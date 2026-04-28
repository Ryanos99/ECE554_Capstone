# pulse_monitor.py
# PS-side controller for Pulse exercise recognition system.
# Runs on PYNQ board ARM Cortex-A53.
#
# Pipeline:
#   USB camera → MoveNet TFLite (ARM) → 34 features
#   → StandardScaler → INT8 quantize
#   → AXI-Lite registers → MLP classifier PL → rep counter
#
# Usage:
#   python3 pulse_monitor.py
#
# Files needed on board:
#   /home/root/base.bit + base.hwh
#   /home/root/movenet_lightning.tflite
#   /home/root/scaler.pkl
#   /home/root/pulse_monitor.py
#   /home/root/rep_counter.py

import cv2
import numpy as np
import time
import joblib

# ── PYNQ imports ──────────────────────────────────────────────────────────────
try:
    from pynq import Overlay
    from pynq.lib.button import Button
    from pynq.lib.video import *
    BOARD = True
except ImportError:
    print("[WARN] PYNQ not available — running in simulation mode")
    BOARD = False

try:
    import tflite_runtime.interpreter as tflite_mod
    def make_interpreter(path):
        return tflite_mod.Interpreter(path)
except ImportError:
    import tensorflow as tf
    def make_interpreter(path):
        return tf.lite.Interpreter(model_path=path)

from rep_counter import RepCounter, CLASS_NAMES

# ── Configuration ─────────────────────────────────────────────────────────────
BITSTREAM_PATH = "/home/xilinx/jupyter_notebooks/final_with_buttons/workout_classifier.bit"
TFLITE_PATH    = "/home/xilinx/jupyter_notebooks/final_with_buttons/movenet_lightning.tflite"
SCALER_PATH    = "/home/xilinx/jupyter_notebooks/final_with_buttons/scaler.pkl"
CAMERA_INDEX   = 0
IMAGE_SIZE     = 192
N_KEYPOINTS    = 17
N_FEATURES     = 34
CONF_THRESHOLD = 0.15

# AXI-Lite register offsets (must match axilite_regs.v)
REG_MLP_DATA_BASE = 0x04   # 34 x 4 bytes = 0x88
REG_MLP_START     = 0x8C
REG_DONE_PULSE    = 0x90
REG_EXERCISE      = 0x94

# INT8 scale factor — maps StandardScaler output (~[-3,+3]) to [-127,+127]
INT8_SCALE = 42.0

# Debounce time (ms)
DEBOUNCE_TIME = 50
NUM_BUTTONS = 4

# MoveNet skeleton edges
EDGES = [
    (0,1),(0,2),(1,3),(2,4),
    (5,6),(5,7),(7,9),(6,8),(8,10),
    (5,11),(6,12),(11,12),
    (11,13),(13,15),(12,14),(14,16),
]

# ── Load scaler ───────────────────────────────────────────────────────────────
print(f"Loading scaler from {SCALER_PATH}...")
scaler = joblib.load(SCALER_PATH)

# ── MoveNet ───────────────────────────────────────────────────────────────────
def load_movenet():
    print(f"Loading MoveNet from {TFLITE_PATH}...")
    interp = make_interpreter(TFLITE_PATH)
    interp.allocate_tensors()
    return interp

def run_movenet(interp, frame):
    """BGR frame → (17, 3) keypoints [y, x, confidence]"""
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (IMAGE_SIZE, IMAGE_SIZE))
    inp     = np.expand_dims(resized, axis=0).astype(np.uint8)
    inp_det = interp.get_input_details()
    out_det = interp.get_output_details()
    interp.set_tensor(inp_det[0]['index'], inp)
    interp.invoke()
    return interp.get_tensor(out_det[0]['index']).reshape(17, 3)

# ── Feature pipeline ──────────────────────────────────────────────────────────
def keypoints_to_int8(keypoints):
    """
    MoveNet keypoints → signed INT8 features for MLP hardware.
      1. Extract 34 raw position features (y, x per keypoint)
      2. Apply StandardScaler (zero-center, unit variance)
      3. Quantize to INT8 [-128, 127]
    """
    raw       = keypoints[:, :2].flatten().reshape(1, -1)  # (1, 34)
    scaled    = scaler.transform(raw)[0]                    # (34,) float
    quantized = np.clip(np.round(scaled * INT8_SCALE), -128, 127).astype(np.int8)
    return quantized  # (34,) int8

# ── AXI-Lite interface ────────────────────────────────────────────────────────
class PLInterface:
    def __init__(self, overlay):
        self.ip = overlay.mlp_controller_0  # must match Vivado IP name
        print(dir(overlay))

    def write_features(self, features_int8):
        """Write 34 signed INT8 features to AXI-Lite registers."""
        for i, val in enumerate(features_int8):
            # & 0xFF handles two's complement for negative values over AXI-Lite
            self.ip.write(REG_MLP_DATA_BASE + i * 4, int(val) & 0xFF)

    def trigger_inference(self):
        self.ip.write(REG_MLP_START, 1)
        time.sleep(0.001)
        self.ip.write(REG_MLP_START, 0)

    def read_results(self):
        exercise_class = self.ip.read(REG_EXERCISE)
        return exercise_class

# ── Stats tracking ────────────────────────────────────────────────────────────
exercise_init = {str(i): 0 for i in range(len(CLASS_NAMES))}
previous_stats = []
exercise_max   = [None] * len(exercise_init)
player_num     = 1

class Stats:
    def __init__(self, name=""):
        global player_num
        self.name = f"Player {player_num}" if name == "" else name
        player_num += 1
        self.exercise_cnts = exercise_init.copy()

    def reset_count(self):
        self.exercise_cnts = exercise_init.copy()

    def set_name(self, new_name):
        self.name = new_name

    def set_exercise_cnts(self, exercise_to_set):
        self.exercise_cnts = exercise_to_set

    def to_string(self):
        parts = [f"{v} reps in {CLASS_NAMES.get(int(k), 'unknown')}"
                 for k, v in self.exercise_cnts.items()]
        return f"{self.name}: " + ", ".join(parts)

    def copy(self):
        a_copy = Stats(self.name)
        a_copy.set_exercise_cnts(self.exercise_cnts.copy())
        return a_copy

# ── Display ───────────────────────────────────────────────────────────────────
def draw_display(frame, keypoints, exercise, reps, state, fps, current_stat, prev_stats, ex_max, is_recording=False):
    h, w = frame.shape[:2]

    # Skeleton
    for a, b in EDGES:
        if keypoints[a,2] > CONF_THRESHOLD and keypoints[b,2] > CONF_THRESHOLD:
            cv2.line(frame,
                     (int(keypoints[a,1]*w), int(keypoints[a,0]*h)),
                     (int(keypoints[b,1]*w), int(keypoints[b,0]*h)),
                     (0,255,0), 2)
    for k in keypoints:
        if k[2] > CONF_THRESHOLD:
            cv2.circle(frame, (int(k[1]*w), int(k[0]*h)), 4, (0,255,255), -1)

    # Top info panel
    cv2.rectangle(frame, (0,0), (300,160), (0,0,0), -1)
    cv2.putText(frame, f"{exercise.upper()}",
                (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)
    cv2.putText(frame, f"REPS: {reps}",
                (10,90), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255,255,255), 3)
    cv2.putText(frame, f"{state}",
                (10,120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
    cv2.putText(frame, f"FPS: {fps:.1f}",
                (10,145), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150,150,150), 1)
    if is_recording:
        cv2.putText(frame, f"RECORDING",
                (10,160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)
    # Bottom stats panel
    ix, iy, xsz, ysz = 0, 160, 300, 320
    cv2.rectangle(frame, (ix, iy), (ix+xsz, iy+ysz), (0,0,0), -1)
    last = prev_stats[-1].to_string() if len(prev_stats) > 0 else "N/A"
    cv2.putText(frame, f"Last: {last}",
                (ix+10, iy+40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    for i in range(len(ex_max)):
        label = CLASS_NAMES.get(i, "unknown")
        best  = f"{ex_max[i][0]}: {ex_max[i][1]}" if ex_max[i] is not None else "N/A"
        cv2.putText(frame, f"Best {label}: {best}",
                    (ix+10, iy+(i+2)*40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    return frame

def get_time_ms():
    return time.time_ns() // 1_000_000

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global previous_stats, exercise_max, player_num

    interpreter = load_movenet()

    if BOARD:
        print(f"Loading bitstream: {BITSTREAM_PATH}")
        overlay  = Overlay(BITSTREAM_PATH)
        pl_iface = PLInterface(overlay)
        
        gpio = overlay.axi_gpio_0
        buttons = gpio.channel1

        # Code taken from https://digilent.com/reference/learn/microprocessor/tutorials/debouncing-via-software/start?srsltid=AfmBOopyAjinABd9VAqmMSGY8QmHhWQSOWYKDYIcPH9McAYU_J87vzom
        from enum import Enum

        global DEBOUNCE_TIME, NUM_BUTTONS

        class Button(Enum):
            LOW = 0
            HIGH = 1

        currentBtnState = [Button.LOW] * NUM_BUTTONS
        prevBtnState = [Button.LOW] * NUM_BUTTONS
        currentActiveState = [Button.LOW] * NUM_BUTTONS
        prevActiveState = [Button.LOW] * NUM_BUTTONS

        lastDebounceTime = [get_time_ms()] * NUM_BUTTONS

        def get_button(i):

            currentBtnState[i] = Button.HIGH if ((buttons.read() >> i) & 1 == 1) else Button.LOW
            if (currentBtnState[i] != prevBtnState[i]):
                lastDebounceTime[i] = get_time_ms()
            if (get_time_ms() - lastDebounceTime[i]) > DEBOUNCE_TIME:
                currentActiveState[i] = currentBtnState[i]
            temp_return = (prevActiveState[i] == Button.LOW and currentActiveState[i] == Button.HIGH)
            prevBtnState[i] = currentBtnState[i]
            prevActiveState[i] = currentActiveState[i]
            return temp_return
    
        displayport = DisplayPort()
        displayport.configure(VideoMode(1920, 1080, 24), PIXEL_RGB)
    else:
        pl_iface = None

    counter     = RepCounter()
    currentStat = Stats()
    is_recording = False

    cap = cv2.VideoCapture(CAMERA_INDEX)
    time.sleep(1.0)

    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return

    print("Running — Q=quit")
    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            # Run MoveNet on ARM
            keypoints = run_movenet(interpreter, frame)

            # Quantize to signed INT8 for MLP hardware
            features_int8 = keypoints_to_int8(keypoints)

            if BOARD and pl_iface is not None:
                pl_iface.write_features(features_int8)
                pl_iface.trigger_inference()
                exercise_class = pl_iface.read_results()
            else:
                exercise_class = 0

            # Rep counter on PS
            reps, state, angle = counter.update(exercise_class, keypoints)
            exercise = CLASS_NAMES.get(exercise_class, "unknown")

            # Update stats if recording
            if is_recording:
                currentStat.exercise_cnts[str(exercise_class)] = counter.rep_count

            # FPS
            now = time.time()
            fps = 0.9 * fps + 0.1 / max(now - prev_time, 1e-6)
            prev_time = now

            # Draw
            frame = draw_display(frame, keypoints, exercise, reps, state, fps,
                                 currentStat, previous_stats, exercise_max, is_recording)

            if BOARD:
                dp_frame = displayport.newframe()
                dp_frame[:] = cv2.cvtColor(cv2.resize(frame, (1920,1080)), cv2.COLOR_BGR2RGB)
                displayport.writeframe(dp_frame)

                # Button 0 — reset current player
                if get_button(0):
                    counter.reset()
                    currentStat.reset_count()
                    for i in range(len(exercise_max)):
                        if exercise_max[i] is not None and exercise_max[i][0] == currentStat.name:
                            exercise_max[i] = None

                # Button 1 — start/stop recording
                if get_button(1):
                    if not is_recording:
                        is_recording = True
                        counter.reset()
                    else:
                        previous_stats.append(currentStat.copy())
                        for i in range(len(exercise_max)):
                            cnt = currentStat.exercise_cnts[str(i)]
                            if exercise_max[i] is None or exercise_max[i][1] < cnt:
                                exercise_max[i] = (currentStat.name, cnt)
                        currentStat = Stats()
                        is_recording = False
                        counter.reset()

                # Button 2 — exit
                if get_button(2):
                    print("Final stats:")
                    for s in previous_stats:
                        print(s.to_string())
                    break

                # Button 3 — global reset
                if get_button(3):
                    previous_stats = []
                    currentStat    = Stats()
                    exercise_max   = [None] * len(exercise_init)
                    player_num     = 1
                    counter.reset()

            else:
                cv2.imshow("Pulse", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    counter.reset()
                    currentStat.reset_count()

    except KeyboardInterrupt:
        print("Keyboard interrupt")
    finally:
        cap.release()
        if BOARD:
            displayport.close()
        cv2.destroyAllWindows()
        print(f"Session ended. Total reps: {counter.rep_count}")
        print("Final stats:")
        for s in previous_stats:
            print(s.to_string())

if __name__ == "__main__":
    main()