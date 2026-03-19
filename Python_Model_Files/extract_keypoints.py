# extract_keypoints.py
# Runs MoveNet Lightning on all dataset images and saves keypoints + angles to CSV.
# Uses TFLite directly — no tensorflow_hub dependency needed.
#
# Usage:
#   python extract_keypoints.py
#
# Output:
#   outputs/keypoints.csv  — one row per image, keypoint positions + angles + label

import tensorflow as tf
import numpy as np
import pandas as pd
import cv2
import os
import urllib.request
from pathlib import Path

# ==============================================================================
# Config
# ==============================================================================
DATASET_DIR  = "./dataset"
OUTPUT_CSV   = "./outputs/keypoints.csv"
IMAGE_SIZE   = 192          # MoveNet Lightning input size
MIN_CONF     = 0.2          # Skip images where mean keypoint confidence is below this

# ==============================================================================
# MoveNet keypoint indices
# ==============================================================================
KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle"
]
KP = {name: i for i, name in enumerate(KEYPOINTS)}

# ==============================================================================
# Load MoveNet Lightning via TFLite (no tensorflow_hub needed)
# ==============================================================================
def load_movenet():
    model_path = "./outputs/movenet_lightning.tflite"
    os.makedirs("./outputs", exist_ok=True)

    if not os.path.exists(model_path):
        print("Downloading MoveNet Lightning (~3MB)...")
        url = "https://storage.googleapis.com/movenet/models/movenet_singlepose_lightning_4.tflite"
        urllib.request.urlretrieve(url, model_path)
        print("Download complete.")

    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    print("MoveNet Lightning loaded.")
    return interpreter

# ==============================================================================
# Run MoveNet on a single image
# Returns: (17, 3) array of [y, x, confidence] normalized 0-1
# ==============================================================================
def get_keypoints(interpreter, img_bgr):
    img_rgb     = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (IMAGE_SIZE, IMAGE_SIZE))
    img_input   = np.expand_dims(img_resized, axis=0).astype(np.uint8)

    input_details  = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]["index"], img_input)
    interpreter.invoke()

    keypoints = interpreter.get_tensor(output_details[0]["index"])[0, 0]  # (17, 3)
    return keypoints

# ==============================================================================
# Calculate angle between 3 points (degrees), B is the vertex
# ==============================================================================
def calc_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))

# ==============================================================================
# Extract feature vector from keypoints
# ==============================================================================
def extract_features(kps):
    """
    kps: (17, 3) array [y, x, conf]
    Returns: list of 34 position values + 10 joint angles = 44 features
    """
    features = []

    # Position features (y, x normalized 0-1 for each of 17 keypoints)
    for i in range(17):
        features.append(float(kps[i, 0]))  # y
        features.append(float(kps[i, 1]))  # x

    # Joint angle features
    def pt(name):
        return (kps[KP[name], 0], kps[KP[name], 1])

    angles = [
        calc_angle(pt("left_shoulder"),  pt("left_elbow"),     pt("left_wrist")),
        calc_angle(pt("right_shoulder"), pt("right_elbow"),    pt("right_wrist")),
        calc_angle(pt("left_elbow"),     pt("left_shoulder"),  pt("left_hip")),
        calc_angle(pt("right_elbow"),    pt("right_shoulder"), pt("right_hip")),
        calc_angle(pt("left_hip"),       pt("left_knee"),      pt("left_ankle")),
        calc_angle(pt("right_hip"),      pt("right_knee"),     pt("right_ankle")),
        calc_angle(pt("left_shoulder"),  pt("left_hip"),       pt("left_knee")),
        calc_angle(pt("right_shoulder"), pt("right_hip"),      pt("right_knee")),
        calc_angle(pt("left_shoulder"),  pt("left_hip"),       pt("right_hip")),
        calc_angle(pt("left_wrist"),     pt("left_shoulder"),  pt("left_hip")),
    ]
    features.extend(angles)
    return features

# ==============================================================================
# Column names for CSV
# ==============================================================================
def get_column_names():
    cols = []
    for name in KEYPOINTS:
        cols.append(f"{name}_y")
        cols.append(f"{name}_x")
    cols += [
        "angle_left_elbow", "angle_right_elbow",
        "angle_left_shoulder", "angle_right_shoulder",
        "angle_left_knee", "angle_right_knee",
        "angle_left_hip", "angle_right_hip",
        "angle_torso", "angle_arm_raise"
    ]
    cols.append("label")
    return cols

# ==============================================================================
# Main extraction loop
# ==============================================================================
def extract_all(dataset_dir, output_csv):
    interpreter  = load_movenet()
    dataset_path = Path(dataset_dir)
    class_dirs   = sorted([d for d in dataset_path.iterdir()
                           if d.is_dir() and d.name != "outputs"])

    if not class_dirs:
        print(f"No class folders found in {dataset_dir}")
        return

    print(f"Found {len(class_dirs)} exercise classes\n")

    rows    = []
    skipped = 0
    total   = 0

    for class_dir in class_dirs:
        label  = class_dir.name
        images = list(class_dir.glob("*.jpg")) + \
                 list(class_dir.glob("*.jpeg")) + \
                 list(class_dir.glob("*.png"))

        print(f"  {label} ({len(images)} images)...", end="", flush=True)
        class_count = 0

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
                features = extract_features(kps)
                features.append(label)
                rows.append(features)
                class_count += 1
                total += 1
            except Exception:
                skipped += 1
                continue

        print(f" {class_count} ok")

    print(f"\nTotal: {total} extracted, {skipped} skipped")

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df = pd.DataFrame(rows, columns=get_column_names())
    df.to_csv(output_csv, index=False)
    print(f"\nSaved to {output_csv}")
    print(df["label"].value_counts().to_string())

# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    extract_all(DATASET_DIR, OUTPUT_CSV)
