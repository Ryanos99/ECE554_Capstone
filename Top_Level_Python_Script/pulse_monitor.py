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

import cv2
import numpy as np
import time
import joblib

# ── PYNQ imports ──────────────────────────────────────────────────────────────
try:
    from pynq import Overlay
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
        interp = tf.lite.Interpreter(model_path=path)
        return interp

# ── Rep counter ───────────────────────────────────────────────────────────────
from rep_counter import RepCounter, CLASS_NAMES

# ── Configuration ─────────────────────────────────────────────────────────────
BITSTREAM_PATH = "/home/root/base.bit"
TFLITE_PATH    = "/home/root/movenet_lightning.tflite"
SCALER_PATH    = "/home/root/scaler.pkl"
CAMERA_INDEX   = 0
IMAGE_SIZE     = 192
N_KEYPOINTS    = 17
N_FEATURES     = 34

# AXI-Lite register offsets (must match axilite_regs.v)
REG_MLP_DATA_BASE = 0x04   # 34 x 4 bytes = 0x88
REG_MLP_START     = 0x8C
REG_DONE_PULSE    = 0x90
REG_EXERCISE      = 0x94

# Confidence threshold for skeleton display
CONF_THRESHOLD = 0.15

# INT8 scale factor — maps StandardScaler output (~[-3,+3]) to [-127,+127]
INT8_SCALE = 42.0

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
      1. Extract 34 raw position features (y,x per keypoint)
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
        self.ip = overlay.workout_classifier  # must match Vivado IP name

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

# ── Display ───────────────────────────────────────────────────────────────────
def draw_display(frame, keypoints, exercise, reps, state, fps):
    h, w = frame.shape[:2]

    for a, b in EDGES:
        if keypoints[a,2] > CONF_THRESHOLD and keypoints[b,2] > CONF_THRESHOLD:
            cv2.line(frame,
                     (int(keypoints[a,1]*w), int(keypoints[a,0]*h)),
                     (int(keypoints[b,1]*w), int(keypoints[b,0]*h)),
                     (0,255,0), 2)
    for k in keypoints:
        if k[2] > CONF_THRESHOLD:
            cv2.circle(frame, (int(k[1]*w), int(k[0]*h)), 4, (0,255,255), -1)

    cv2.rectangle(frame, (0,0), (300,170), (0,0,0), -1)
    cv2.putText(frame, f"{exercise.upper()}",
                (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)
    cv2.putText(frame, f"REPS: {reps}",
                (10,90), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255,255,255), 3)
    cv2.putText(frame, f"{state}",
                (10,125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
    cv2.putText(frame, f"FPS: {fps:.1f}",
                (10,155), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150,150,150), 1)
    return frame

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    interpreter = load_movenet()

    if BOARD:
        print(f"Loading bitstream: {BITSTREAM_PATH}")
        overlay  = Overlay(BITSTREAM_PATH)
        pl_iface = PLInterface(overlay)
    else:
        pl_iface = None

    counter = RepCounter()
    cap     = cv2.VideoCapture(CAMERA_INDEX)
    time.sleep(1.0)

    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return

    print("Running — Q=quit  R=reset")
    prev_time = time.time()
    fps = 0.0

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

        # FPS
        now = time.time()
        fps = 0.9 * fps + 0.1 / max(now - prev_time, 1e-6)
        prev_time = now

        frame = draw_display(frame, keypoints, exercise, reps, state, fps)
        cv2.imshow("Pulse", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            counter.reset()
            print("Reset")

    cap.release()
    cv2.destroyAllWindows()
    print(f"Session ended. Total reps: {counter.rep_count}")

if __name__ == "__main__":
    main()
