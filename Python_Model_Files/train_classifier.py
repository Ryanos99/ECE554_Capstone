# train_classifier.py
# Trains a small MLP on the keypoints CSV extracted by extract_keypoints.py.
# Takes ~1 minute to train. Outputs a small model file for use on the board.
#
# Usage:
#   python train_classifier.py
#
# Outputs:
#   outputs/classifier.pkl      — trained sklearn MLP
#   outputs/label_encoder.pkl   — label encoder (index → exercise name)
#   outputs/scaler.pkl          — feature scaler (must match inference)

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ==============================================================================
# Config
# ==============================================================================
CSV_PATH    = "./outputs/keypoints.csv"
OUTPUT_DIR  = "./outputs"
TEST_SPLIT  = 0.2
RANDOM_SEED = 42

# ==============================================================================
# Load data
# ==============================================================================
print("Loading keypoints CSV...")
df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} samples, {len(df.columns)-1} features, {df['label'].nunique()} classes")

X = df.drop(columns=["label"]).values.astype(np.float32)
y = df["label"].values

# ==============================================================================
# Encode labels
# ==============================================================================
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print(f"Classes: {list(le.classes_)}")

# ==============================================================================
# Scale features
# ==============================================================================
scaler  = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==============================================================================
# Train/val split
# ==============================================================================
X_train, X_val, y_train, y_val = train_test_split(
    X_scaled, y_encoded, test_size=TEST_SPLIT,
    random_state=RANDOM_SEED, stratify=y_encoded
)
print(f"\nTrain: {len(X_train)} samples | Val: {len(X_val)} samples")

# ==============================================================================
# Train MLP
# Hidden layers: 256 → 128 → 64
# Small enough to run fast on ARM, big enough to distinguish 22 exercises
# ==============================================================================
print("\nTraining MLP classifier...")
clf = MLPClassifier(
    hidden_layer_sizes = (256, 128, 64),
    activation         = "relu",
    solver             = "adam",
    max_iter           = 500,
    early_stopping     = True,
    validation_fraction= 0.1,
    n_iter_no_change   = 20,
    random_state       = RANDOM_SEED,
    verbose            = True
)
clf.fit(X_train, y_train)

# ==============================================================================
# Evaluate
# ==============================================================================
print("\n" + "="*60)
val_acc = clf.score(X_val, y_val)
print(f"Validation accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")

y_pred = clf.predict(X_val)
print("\nPer-class report:")
print(classification_report(y_val, y_pred, target_names=le.classes_))

# ==============================================================================
# Save model, scaler, encoder
# ==============================================================================
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(f"{OUTPUT_DIR}/classifier.pkl", "wb") as f:
    pickle.dump(clf, f)

with open(f"{OUTPUT_DIR}/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

with open(f"{OUTPUT_DIR}/label_encoder.pkl", "wb") as f:
    pickle.dump(le, f)

print(f"\nSaved:")
print(f"  {OUTPUT_DIR}/classifier.pkl")
print(f"  {OUTPUT_DIR}/scaler.pkl")
print(f"  {OUTPUT_DIR}/label_encoder.pkl")
print("\nDone! Run rep_counter_pose.py to test live.")