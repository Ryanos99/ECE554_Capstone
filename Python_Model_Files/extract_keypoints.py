# extract_keypoints.py
# Runs MoveNet on all dataset images and saves 34 position features to CSV.
# Uses TFLite runtime (works on Apple Silicon).
#
# Usage:
#   python extract_keypoints.py
#
# Output:
#   outputs/keypoints.csv — 34 position features + label per image

import tensorflow as tf
import numpy as np
import pandas as pd
import cv2
import os
from pathlib import Path

DATASET_DIR = "./dataset"
OUTPUT_CSV  = "./outputs/keypoints.csv"
TFLITE_PATH = "./outputs/movenet_lightning.tflite"
IMAGE_SIZE  = 192
MIN_CONF    = 0.2   # skip images where average keypoint confidence is below this

KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle"
]

def load_movenet():
    print(f"Loading MoveNet from {TFLITE_PATH}...")
    interpreter = tf.lite.Interpreter(TFLITE_PATH)
    interpreter.allocate_tensors()
    return interpreter

def get_keypoints(interpreter, img_bgr):
    rgb     = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (IMAGE_SIZE, IMAGE_SIZE))
    inp     = np.expand_dims(resized, axis=0).astype(np.uint8)
    interpreter.set_tensor(interpreter.get_input_details()[0]['index'], inp)
    interpreter.invoke()
    kps = interpreter.get_tensor(interpreter.get_output_details()[0]['index'])
    return kps.reshape(17, 3)  # [y, x, confidence]

def extract_features(kps):
    # Only position features — 17 joints * (y, x) = 34 values
    features = []
    for i in range(17):
        features.append(float(kps[i, 0]))  # y
        features.append(float(kps[i, 1]))  # x
    return features

def get_column_names():
    cols = []
    for name in KEYPOINTS:
        cols.append(f"{name}_y")
        cols.append(f"{name}_x")
    cols.append("label")
    return cols

def main():
    interpreter  = load_movenet()
    dataset_path = Path(DATASET_DIR)
    class_dirs   = sorted([d for d in dataset_path.iterdir() if d.is_dir()])

    if not class_dirs:
        print(f"ERROR: No folders found in {DATASET_DIR}")
        return

    print(f"Found {len(class_dirs)} exercise classes\n")

    rows    = []
    skipped = 0
    total   = 0

    for class_dir in class_dirs:
        label  = class_dir.name
        images = sorted(list(class_dir.glob("*.jpg")) +
                        list(class_dir.glob("*.jpeg")) +
                        list(class_dir.glob("*.png")))

        print(f"  {label} ({len(images)} images)...", end="", flush=True)
        count = 0

        for img_path in images:
            img = cv2.imread(str(img_path))
            if img is None:
                skipped += 1
                continue
            try:
                kps = get_keypoints(interpreter, img)
                if np.mean(kps[:, 2]) < MIN_CONF:
                    skipped += 1
                    continue
                row = extract_features(kps)
                row.append(label)
                rows.append(row)
                count += 1
                total += 1
            except Exception:
                skipped += 1

        print(f" {count} ok")

    print(f"\nTotal: {total} extracted, {skipped} skipped")

    os.makedirs("./outputs", exist_ok=True)
    df = pd.DataFrame(rows, columns=get_column_names())
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved to {OUTPUT_CSV}")
    print(df["label"].value_counts())

if __name__ == "__main__":
    main()
