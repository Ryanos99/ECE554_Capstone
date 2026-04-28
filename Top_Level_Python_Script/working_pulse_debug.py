# pulse_debug.py
# Debug script — shows MoveNet skeleton and raw MLP classifier output.
# No rep counter, no buttons, no stats tracking.
# Use this to verify MLP classification is correct before full integration.
#
# Usage:
#   python3 pulse_debug.py
 
import cv2
import numpy as np
import time
import joblib
 
# ── PYNQ imports ──────────────────────────────────────────────────────────────
try:
    from pynq import Overlay
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
 
# ── Configuration ─────────────────────────────────────────────────────────────
BITSTREAM_PATH = "/home/xilinx/jupyter_notebooks/final/workout_classifier.bit"
TFLITE_PATH    = "/home/xilinx/jupyter_notebooks/final/movenet_lightning.tflite"
SCALER_PATH    = "/home/xilinx/jupyter_notebooks/final/scaler.pkl"
CAMERA_INDEX   = 0
IMAGE_SIZE     = 192
CONF_THRESHOLD = 0.15
INT8_SCALE     = 42.0
 
# AXI-Lite register offsets
REG_MLP_DATA_BASE = 0x04
REG_MLP_START     = 0x8C
REG_DONE_PULSE    = 0x90
REG_EXERCISE      = 0x94
 
# Class names — must match label_encoder.pkl
CLASS_NAMES = {
    0: "bench",
    1: "pushup",
    2: "squat",
    3: "unknown",
}
 
CLASS_COLORS = {
    0: (255, 165, 0),   # bench  — orange
    1: (0, 255, 0),     # pushup — green
    2: (0, 0, 255),     # squat  — blue
    3: (128, 128, 128), # unknown — gray
}
 
# MoveNet skeleton edges
EDGES = [
    (0,1),(0,2),(1,3),(2,4),
    (5,6),(5,7),(7,9),(6,8),(8,10),
    (5,11),(6,12),(11,12),
    (11,13),(13,15),(12,14),(14,16),
]
 
# ── Load scaler ───────────────────────────────────────────────────────────────
print(f"Loading scaler...")
scaler = joblib.load(SCALER_PATH)
 
# ── MoveNet ───────────────────────────────────────────────────────────────────
def load_movenet():
    print(f"Loading MoveNet...")
    interp = make_interpreter(TFLITE_PATH)
    interp.allocate_tensors()
    return interp
 
def run_movenet(interp, frame):
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (IMAGE_SIZE, IMAGE_SIZE))
    inp     = np.expand_dims(resized, axis=0).astype(np.uint8)
    inp_det = interp.get_input_details()
    out_det = interp.get_output_details()
    interp.set_tensor(inp_det[0]['index'], inp)
    interp.invoke()
    return interp.get_tensor(out_det[0]['index']).reshape(17, 3)
 
def keypoints_to_int8(keypoints):
    raw       = keypoints[:, :2].flatten().reshape(1, -1)
    scaled    = scaler.transform(raw)[0]
    quantized = np.clip(np.round(scaled * INT8_SCALE), -128, 127).astype(np.int8)
    return quantized
 
# ── AXI-Lite interface ────────────────────────────────────────────────────────
class PLInterface:
    def __init__(self, overlay):
        self.ip = overlay.mlp_controller_0
 
    def write_features(self, features_int8):
        for i, val in enumerate(features_int8):
            self.ip.write(REG_MLP_DATA_BASE + i * 4, int(val) & 0xFF)
 
    def trigger_inference(self):
        self.ip.write(REG_DONE_PULSE, 0)
        self.ip.write(REG_MLP_START, 1)
        time.sleep(0.001)
        self.ip.write(REG_MLP_START, 0)
 
    def read_results(self):
        return self.ip.read(REG_EXERCISE)
 
# ── Display ───────────────────────────────────────────────────────────────────
def draw_display(frame, keypoints, exercise_class, fps):
    h, w = frame.shape[:2]
    exercise = CLASS_NAMES.get(exercise_class, "unknown")
    color    = CLASS_COLORS.get(exercise_class, (128,128,128))
 
    # Skeleton
    for a, b in EDGES:
        if keypoints[a,2] > CONF_THRESHOLD and keypoints[b,2] > CONF_THRESHOLD:
            cv2.line(frame,
                     (int(keypoints[a,1]*w), int(keypoints[a,0]*h)),
                     (int(keypoints[b,1]*w), int(keypoints[b,0]*h)),
                     (0,255,0), 2)
    for k in keypoints:
        if k[2] > CONF_THRESHOLD:
            cv2.circle(frame, (int(k[1]*w), int(k[0]*h)), 5, (0,255,255), -1)
 
    # Info panel
    cv2.rectangle(frame, (0,0), (400,120), (0,0,0), -1)
    cv2.putText(frame, f"CLASS: {exercise.upper()}",
                (10,45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    cv2.putText(frame, f"RAW IDX: {exercise_class}",
                (10,80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
    cv2.putText(frame, f"FPS: {fps:.1f}",
                (10,108), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150,150,150), 1)
 
    # Keypoint confidence bar
    confs = keypoints[:, 2]
    cv2.putText(frame, f"KP conf avg: {confs.mean():.2f}  min: {confs.min():.2f}",
                (10, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150,150,150), 1)
 
    return frame
 
# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    interpreter = load_movenet()
 
    if BOARD:
        print(f"Loading bitstream: {BITSTREAM_PATH}")
        overlay  = Overlay(BITSTREAM_PATH)
        pl_iface = PLInterface(overlay)
        displayport = DisplayPort()
        displayport.configure(VideoMode(1920, 1080, 24), PIXEL_RGB)
    else:
        pl_iface = None
 
    cap = cv2.VideoCapture(CAMERA_INDEX)
    time.sleep(1.0)
 
    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return
 
    print("Running — Q to quit")
    prev_time = time.time()
    fps = 0.0
 
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue
 
            # MoveNet inference
            keypoints     = run_movenet(interpreter, frame)
            features_int8 = keypoints_to_int8(keypoints)
 
            # MLP classification
            if BOARD and pl_iface is not None:
                pl_iface.write_features(features_int8)
                pl_iface.trigger_inference()
                exercise_class = pl_iface.read_results()
            else:
                exercise_class = 3  # unknown in sim mode
 
            # FPS
            now = time.time()
            fps = 0.9 * fps + 0.1 / max(now - prev_time, 1e-6)
            prev_time = now
 
            # Draw
            frame = draw_display(frame, keypoints, exercise_class, fps)
 
            if BOARD:
                dp_frame = displayport.newframe()
                # dp_frame[:] = cv2.cvtColor(cv2.resize(frame, (1920,1080)), cv2.COLOR_BGR2RGB)
                dp_frame[:] = cv2.resize(frame, (1920,1080))
                displayport.writeframe(dp_frame)
            else:
                cv2.imshow("Pulse Debug", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
 
    except KeyboardInterrupt:
        print("Stopped")
    finally:
        cap.release()
        if BOARD:
            displayport.close()
        cv2.destroyAllWindows()
 
if __name__ == "__main__":
    main()