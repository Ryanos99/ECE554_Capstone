# pulse_monitor.py
# PS-side controller for Pulse exercise recognition system.
# Runs on PYNQ board ARM Cortex-A53.
#
# Pipeline:
#   USB camera → OpenPose DPU → heatmap decode → 36 features
#   → AXI-Lite registers → MLP classifier PL → rep counter
#
# Usage:
#   python3 pulse_monitor.py
#
# Dependencies on board:
#   pip install pynq opencv-python-headless numpy
#   xmodel: /home/root/openpose/openpose.xmodel
#   bitstream: base.bit + base.hwh

import cv2
import numpy as np
import time
import os
import string

# ── PYNQ / Vitis AI imports ───────────────────────────────────────────────────
try:
    from pynq import Overlay
    from pynq.lib.button import Button
    from pynq.lib.video import *
    import xir
    import vart
    BOARD = True
except ImportError:
    print("[WARN] PYNQ/VART not available — running in simulation mode")
    BOARD = False

# ── Rep counter (same file used on Mac for testing) ───────────────────────────
from rep_counter import RepCounter, CLASS_NAMES

# ── Configuration ─────────────────────────────────────────────────────────────
BITSTREAM_PATH  = "/home/root/base.bit"
XMODEL_PATH     = "/home/root/openpose/openpose.xmodel"
CAMERA_INDEX    = 0
IMG_W           = 256
IMG_H           = 256
HEATMAP_W       = 32
HEATMAP_H       = 32
N_KEYPOINTS     = 18
CONF_THRESHOLD  = 0.1   # minimum heatmap confidence to trust keypoint

# OpenPose body_18 keypoint indices
KP = {
    "nose":            0,
    "neck":            1,
    "right_shoulder":  2,  "left_shoulder":  5,
    "right_elbow":     3,  "left_elbow":     6,
    "right_wrist":     4,  "left_wrist":     7,
    "right_hip":       8,  "left_hip":      11,
    "right_knee":      9,  "left_knee":     12,
    "right_ankle":    10,  "left_ankle":    13,
}

# AXI-Lite register offsets (must match axilite_regs.v)
REG_MLP_DATA_BASE = 0x04   # 36 x 4 bytes = 0x90
REG_DPU_START     = 0x94
REG_REP_COUNT     = 0x98
REG_EXERCISE      = 0x9C

# Buttons
# TODO: Update these
PL_USER_PB0 = 0xAB6
PL_USER_PB1 = 0xAB7
PL_USER_PB2 = 0xAB2
PL_USER_PB3 = 0xAC6

# ── Preprocessing ─────────────────────────────────────────────────────────────
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def preprocess(frame):
    """BGR frame → normalized float32 (1, 3, H, W)"""
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (IMG_W, IMG_H))
    img     = resized.astype(np.float32) / 255.0
    img     = (img - MEAN) / STD
    return img.transpose(2, 0, 1)[np.newaxis]  # (1, 3, H, W)

# ── Heatmap decoder ───────────────────────────────────────────────────────────
def decode_heatmaps(heatmaps):
    """
    Decode OpenPose heatmap output to keypoint coordinates.

    Args:
        heatmaps: np.array (1, 19, 32, 32) — last channel is background

    Returns:
        keypoints: np.array (18, 3) — [y_norm, x_norm, confidence]
                   normalized 0-1, same format as MoveNet output
    """
    keypoints = np.zeros((N_KEYPOINTS, 3), dtype=np.float32)
    for k in range(N_KEYPOINTS):
        hm  = heatmaps[0, k]                          # (32, 32)
        idx = np.argmax(hm)
        y_hm, x_hm = np.unravel_index(idx, hm.shape)
        conf = float(hm[y_hm, x_hm])

        # Apply Gaussian offset for sub-pixel accuracy
        x_f, y_f = float(x_hm), float(y_hm)
        if 0 < x_hm < HEATMAP_W - 1:
            dx = hm[y_hm, x_hm+1] - hm[y_hm, x_hm-1]
            x_f += 0.25 * np.sign(dx)
        if 0 < y_hm < HEATMAP_H - 1:
            dy = hm[y_hm+1, x_hm] - hm[y_hm-1, x_hm]
            y_f += 0.25 * np.sign(dy)

        keypoints[k] = [
            y_f / HEATMAP_H,   # normalized y
            x_f / HEATMAP_W,   # normalized x
            conf
        ]
    return keypoints

# ── Feature extraction ────────────────────────────────────────────────────────
def extract_features(keypoints):
    """
    Extract 36 position features from 18 OpenPose keypoints.
    Returns flat array [y0, x0, y1, x1, ... y17, x17] — 36 values.
    """
    return keypoints[:, :2].flatten()  # (36,)

# ── VART DPU runner ───────────────────────────────────────────────────────────
class OpenPoseDPU:
    def __init__(self, xmodel_path):
        print(f"Loading xmodel: {xmodel_path}")
        graph    = xir.Graph.deserialize(xmodel_path)
        subgraphs = [s for s in graph.get_root_subgraph().toposort_child_subgraph()
                     if s.has_attr("device") and s.get_attr("device").upper() == "DPU"]
        assert len(subgraphs) > 0, "No DPU subgraph found"
        self.runner = vart.Runner.create_runner(subgraphs[0], "run")

        self.input_tensors  = self.runner.get_input_tensors()
        self.output_tensors = self.runner.get_output_tensors()
        print(f"DPU runner ready")
        print(f"  Input:  {[t.name for t in self.input_tensors]}")
        print(f"  Output: {[t.name for t in self.output_tensors]}")

    def run(self, img_nchw):
        """
        Run OpenPose inference.
        img_nchw: np.array (1, 3, H, W) float32 normalized

        Returns heatmaps: np.array (1, 19, 32, 32)
        """
        # Convert NCHW → NHWC for DPU
        img_nhwc = img_nchw.transpose(0, 2, 3, 1)

        inputData  = [np.empty(t.dims, dtype=np.float32, order="C")
                      for t in self.input_tensors]
        outputData = [np.empty(t.dims, dtype=np.float32, order="C")
                      for t in self.output_tensors]

        inputData[0][...] = img_nhwc

        job_id = self.runner.execute_async(inputData, outputData)
        self.runner.wait(job_id)

        # Find the heatmap output (shape should be (1, H, W, 19))
        # Convert back to (1, 19, H, W)
        for out in outputData:
            if out.shape[-1] == 19:
                return out.transpose(0, 3, 1, 2)  # NHWC → NCHW

        # Fallback — return first output
        return outputData[0].transpose(0, 3, 1, 2)


# ── AXI-Lite interface ────────────────────────────────────────────────────────
class PLInterface:
    """Writes keypoint features to AXI-Lite registers and reads back results."""

    def __init__(self, overlay):
        # Get the AXI-Lite IP from the overlay
        # Name depends on how Prateek named it in Vivado block design
        self.ip = overlay.mlp_controller  # adjust name if needed

    def write_features(self, features_36):
        """Write 36 normalized features as fixed-point integers."""
        for i, val in enumerate(features_36):
            # Scale to 0-255 range
            scaled = int(np.clip(val * 255.0, 0, 255))
            self.ip.write(REG_MLP_DATA_BASE + i * 4, scaled)

    def trigger_inference(self):
        self.ip.write(REG_DPU_START, 1)
        time.sleep(0.001)  # wait for PL to process
        self.ip.write(REG_DPU_START, 0)

    def read_results(self):
        rep_count     = self.ip.read(REG_REP_COUNT)
        exercise_class = self.ip.read(REG_EXERCISE)
        return rep_count, exercise_class


# ── Display overlay ───────────────────────────────────────────────────────────
def draw_display(frame, keypoints, exercise, reps, state, fps):
    h, w = frame.shape[:2]

    # Skeleton edges (OpenPose body_18 connections)
    EDGES = [
        (0,1),(1,2),(2,3),(3,4),      # right arm
        (1,5),(5,6),(6,7),             # left arm
        (1,8),(8,9),(9,10),            # right leg
        (1,11),(11,12),(12,13),        # left leg
        (0,14),(14,16),(0,15),(15,17), # face
    ]

    for a, b in EDGES:
        if keypoints[a,2] > CONF_THRESHOLD and keypoints[b,2] > CONF_THRESHOLD:
            y1,x1 = int(keypoints[a,0]*h), int(keypoints[a,1]*w)
            y2,x2 = int(keypoints[b,0]*h), int(keypoints[b,1]*w)
            cv2.line(frame, (x1,y1), (x2,y2), (0,255,0), 2)

    for k in range(N_KEYPOINTS):
        if keypoints[k,2] > CONF_THRESHOLD:
            y,x = int(keypoints[k,0]*h), int(keypoints[k,1]*w)
            cv2.circle(frame, (x,y), 4, (0,255,255), -1)

    # Info panel
    cv2.rectangle(frame, (0,0), (300,160), (0,0,0), -1)
    cv2.putText(frame, f"{exercise.upper()}",
                (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)
    cv2.putText(frame, f"REPS: {reps}",
                (10,90), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255,255,255), 3)
    cv2.putText(frame, f"{state}",
                (10,120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
    cv2.putText(frame, f"FPS: {fps:.1f}",
                (10,145), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150,150,150), 1)
    
    initial_x = 0
    initial_y = 160
    x_size = 300
    y_size = 320
    cv2.rectangle(frame, (initial_x, initial_y), (initial_x + x_size, initial_y + y_size), (0, 0, 0), -1)
    cv2.putText(frame, f"most recent player: {previous_stats[-1].to_string() if len(previous_stats) > 0 else 'N/A'}",
            (initial_x + 10, initial_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 1)
    
    for i in range(len(exercise_max)):
        cv2.putText(frame, f"Current best in {CLASS_NAMES.get(str(i), 'unknown')}: " + (f"{exercise_max[i][0]} with {exercise_max[i][1]}" if exercise_max[i] is not None else 'N/A'),
                    (initial_x + 10, initial_y + (i + 2) * 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    return frame

player_num = 1
class Stats:
    def __init__(self, name=""):
        global player_num
        self.name = ("Player " + str(player_num)) if name == "" else name
        player_num += 1
        self.exercise_cnts = exercise_init.copy()
    
    def reset_count(self):
        self.exercise_cnts = exercise_init.copy()

    def set_name(self, new_name):
        self.name = new_name
    
    def set_exercise_cnts(self, exercise_to_set):
        self.exercise_cnts = exercise_to_set

    def to_string(self):
        the_string = self.name + ": "
        for key, value in self.exercise_cnts.items():
            the_string += f"{value} reps in " + CLASS_NAMES.get(key, "unknown") + ", "
        return the_string[:-2] # remove the trailing , 
    
    def copy(self):
        a_copy = Stats(self.name)
        a_copy.set_exercise_cnts(self.exercise_cnts)
        return a_copy
    
exercise_init = {'0': 0, '1': 0, '2': 0, '3': 0}
previous_stats = []
currentStat = Stats()
exercise_max = [None] * len(exercise_init.keys())

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    # Load overlay
    if BOARD:
        print(f"Loading bitstream: {BITSTREAM_PATH}")
        overlay  = Overlay(BITSTREAM_PATH)
        dpu      = OpenPoseDPU(XMODEL_PATH)
        pl_iface = PLInterface(overlay)
    else:
        print("Simulation mode — no DPU or PL")
        dpu = pl_iface = None

    counter = RepCounter()
    cap     = cv2.VideoCapture(CAMERA_INDEX)
    button_0 = Button(0)
    button_1 = Button(1)
    button_2 = Button(2)
    button_3 = Button(3)
    displayport = DisplayPort()
    displayport.configure(VideoMode(1920, 1080, 24), PIXEL_RGB)

    text = ""
    is_typing = False
    is_recording = False

    # TODO: Change name as needed
    workout_machine = overlay.workout_statemachine

    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return

    prev_time = time.time()
    fps       = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # ── Inference ──
            img = preprocess(frame)

            if BOARD and dpu is not None:
                heatmaps  = dpu.run(img)
                keypoints = decode_heatmaps(heatmaps)
                features  = extract_features(keypoints)

                # Send features to PL MLP classifier
                pl_iface.write_features(features)
                pl_iface.trigger_inference()
                rep_count, exercise_class = pl_iface.read_results()

                # Also run rep counter on PS for robustness
                reps, state, angle = counter.update(exercise_class, keypoints)
                exercise = CLASS_NAMES.get(exercise_class, "unknown")

            else:
                # Simulation — just show camera feed
                keypoints     = np.zeros((N_KEYPOINTS, 3), dtype=np.float32)
                reps          = 0
                state         = "IDLE"
                exercise      = "none"
                exercise_class = 0

            # ── FPS ──
            now      = time.time()
            fps      = 0.9 * fps + 0.1 * (1.0 / max(now - prev_time, 1e-6))
            prev_time = now

            # ── Display ──
            frame = draw_display(frame, keypoints, exercise, reps, state, fps)

            dp_frame = displayport.newframe()
            to_dp_frame = cv2.cvtColor(cv2.resize(frame, (1920, 1080)), cv2.COLOR_BGR2RGB)
            dp_frame[:] = to_dp_frame
            displayport.writeframe(dp_frame)

            if (button_0.read()):
                # Current person reset
                currentStat.reset_count()
                for i in range(len(exercise_max)):
                    if exercise_max[i] is not None and exercise_max[i][0] == currentStat.name:
                        exercise_max[i] = None

            if (button_3.read()):
                # Global reset
                previous_stats = []
                currentStat = Stats()
                exercise_max = [None] * len(exercise_init.keys())

            if (button_1.read()):
                if not(is_recording):
                    is_recording = True
                    time.sleep(0.2)
                    # Start the process
                else:
                    previous_stats.append(currentStat.copy())
                    for i in range(len(exercise_max)):
                        if exercise_max[i] is None or exercise_max[i][1] < currentStat.exercise_cnts[str(i)]:
                            exercise_max[i] = (currentStat.name, currentStat.exercise_cnts[str(i)])

                    currentStat = Stats()
                    is_recording = False
            
            if is_recording:
                currentStat.exercise_cnts[str(exercise_class)] = rep_count


            if (button_2.read()):
                # Exiting....
                print("STATS...")
                for element in previous_stats:
                    print(element.to_string())
                break

    except KeyboardInterrupt:
        print("Keyboard Interrupt")

    finally:
        cap.release()
        displayport.close()
        cv2.destroyAllWindows()
        print(f"Session ended. Total reps: {counter.rep_count}")


if __name__ == "__main__":
    main()
