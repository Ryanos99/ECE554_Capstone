# pulse_ps_only.py
# Full PS-only pipeline — no PL MLP classifier.
# Uses sklearn classifier on ARM instead of hardware MLP.
# Use this to verify the full system works correctly before integrating PL.
#
# Pipeline:
#   USB camera → MoveNet TFLite (ARM) → sklearn MLP (ARM) → rep counter → display
#
# Usage:
#   python3 pulse_ps_only.py
#
# Files needed on board:
#   /home/root/base.bit + base.hwh
#   /home/root/movenet_lightning.tflite
#   /home/root/scaler.pkl
#   /home/root/classifier.pkl
#   /home/root/label_encoder.pkl
#   /home/root/pulse_ps_only.py
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
BITSTREAM_PATH  = "/home/root/base.bit"
TFLITE_PATH     = "/home/root/movenet_lightning.tflite"
SCALER_PATH     = "/home/root/scaler.pkl"
CLASSIFIER_PATH = "/home/root/classifier.pkl"
CAMERA_INDEX    = 0
IMAGE_SIZE      = 192
CONF_THRESHOLD  = 0.15

# MoveNet skeleton edges
EDGES = [
    (0,1),(0,2),(1,3),(2,4),
    (5,6),(5,7),(7,9),(6,8),(8,10),
    (5,11),(6,12),(11,12),
    (11,13),(13,15),(12,14),(14,16),
]

# ── Load models ───────────────────────────────────────────────────────────────
print("Loading MoveNet...")
interpreter = make_interpreter(TFLITE_PATH)
interpreter.allocate_tensors()
inp_det = interpreter.get_input_details()
out_det = interpreter.get_output_details()

print("Loading classifier...")
clf    = joblib.load(CLASSIFIER_PATH)
scaler = joblib.load(SCALER_PATH)

# ── Inference ─────────────────────────────────────────────────────────────────
def run_movenet(frame):
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (IMAGE_SIZE, IMAGE_SIZE))
    inp     = np.expand_dims(resized, axis=0).astype(np.uint8)
    interpreter.set_tensor(inp_det[0]['index'], inp)
    interpreter.invoke()
    return interpreter.get_tensor(out_det[0]['index']).reshape(17, 3)

def classify(keypoints):
    features = scaler.transform([keypoints[:, :2].flatten()])[0]
    proba    = clf.predict_proba([features])[0]
    cls      = int(np.argmax(proba))
    return cls, float(proba[cls])

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

    def set_exercise_cnts(self, d):
        self.exercise_cnts = d

    def to_string(self):
        parts = [f"{v} reps in {CLASS_NAMES.get(int(k), 'unknown')}"
                 for k, v in self.exercise_cnts.items()]
        return f"{self.name}: " + ", ".join(parts)

    def copy(self):
        c = Stats(self.name)
        c.set_exercise_cnts(self.exercise_cnts.copy())
        return c

# ── Display ───────────────────────────────────────────────────────────────────
def draw_display(frame, keypoints, exercise, confidence, reps, state, fps,
                 current_stat, prev_stats, ex_max, is_recording):
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

    # Recording indicator
    if is_recording:
        cv2.circle(frame, (w-30, 30), 15, (0,0,255), -1)

    # Top info panel
    cv2.rectangle(frame, (0,0), (320,170), (0,0,0), -1)
    col = (0,255,0) if confidence > 0.7 else (0,165,255) if confidence > 0.4 else (0,0,255)
    cv2.putText(frame, f"{exercise.upper()}",
                (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, col, 2)
    cv2.putText(frame, f"conf: {confidence:.0%}",
                (10,65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)
    cv2.putText(frame, f"REPS: {reps}",
                (10,115), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255,255,255), 3)
    cv2.putText(frame, f"{state}",
                (10,145), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
    cv2.putText(frame, f"FPS: {fps:.1f}  PS-ONLY MODE",
                (10,165), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100,255,100), 1)

    # Bottom stats panel
    ix, iy = 0, 170
    cv2.rectangle(frame, (ix,iy), (ix+320, iy+40+len(ex_max)*40), (0,0,0), -1)
    last = prev_stats[-1].to_string() if prev_stats else "N/A"
    cv2.putText(frame, f"Last: {last}",
                (ix+10, iy+30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
    for i in range(len(ex_max)):
        label = CLASS_NAMES.get(i, "unknown")
        best  = f"{ex_max[i][0]}: {ex_max[i][1]}" if ex_max[i] else "N/A"
        cv2.putText(frame, f"Best {label}: {best}",
                    (ix+10, iy+30+(i+1)*35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)

    return frame

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global previous_stats, exercise_max, player_num

    if BOARD:
        print(f"Loading bitstream: {BITSTREAM_PATH}")
        overlay     = Overlay(BITSTREAM_PATH)
        button_0    = Button(0)   # reset current player
        button_1    = Button(1)   # start/stop recording
        button_2    = Button(2)   # exit
        button_3    = Button(3)   # global reset
        displayport = DisplayPort()
        displayport.configure(VideoMode(1920, 1080, 24), PIXEL_RGB)

    counter      = RepCounter()
    currentStat  = Stats()
    is_recording = False

    cap = cv2.VideoCapture(CAMERA_INDEX)
    time.sleep(1.0)

    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return

    print("Running — PS-only mode (sklearn classifier on ARM)")
    if not BOARD:
        print("Q=quit  R=reset")

    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            # Full inference on ARM
            keypoints              = run_movenet(frame)
            exercise_class, conf   = classify(keypoints)
            reps, state, angle     = counter.update(exercise_class, keypoints, conf)
            exercise               = CLASS_NAMES.get(exercise_class, "unknown")

            # Update stats if recording
            if is_recording:
                currentStat.exercise_cnts[str(exercise_class)] = counter.rep_count

            # FPS
            now = time.time()
            fps = 0.9 * fps + 0.1 / max(now - prev_time, 1e-6)
            prev_time = now

            # Draw
            frame = draw_display(frame, keypoints, exercise, conf, reps, state, fps,
                                 currentStat, previous_stats, exercise_max, is_recording)

            if BOARD:
                dp_frame = displayport.newframe()
                dp_frame[:] = cv2.cvtColor(cv2.resize(frame, (1920,1080)), cv2.COLOR_BGR2RGB)
                displayport.writeframe(dp_frame)

                if button_0.read():
                    counter.reset()
                    currentStat.reset_count()
                    for i in range(len(exercise_max)):
                        if exercise_max[i] and exercise_max[i][0] == currentStat.name:
                            exercise_max[i] = None

                if button_1.read():
                    if not is_recording:
                        is_recording = True
                        counter.reset()
                        time.sleep(0.2)
                    else:
                        previous_stats.append(currentStat.copy())
                        for i in range(len(exercise_max)):
                            cnt = currentStat.exercise_cnts[str(i)]
                            if exercise_max[i] is None or exercise_max[i][1] < cnt:
                                exercise_max[i] = (currentStat.name, cnt)
                        currentStat  = Stats()
                        is_recording = False
                        counter.reset()

                if button_2.read():
                    print("Final stats:")
                    for s in previous_stats:
                        print(s.to_string())
                    break

                if button_3.read():
                    previous_stats = []
                    currentStat    = Stats()
                    exercise_max   = [None] * len(exercise_init)
                    player_num     = 1
                    counter.reset()

            else:
                cv2.imshow("Pulse PS-Only", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    counter.reset()
                    currentStat.reset_count()
                    print("Reset")

    except KeyboardInterrupt:
        print("Stopped")
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
