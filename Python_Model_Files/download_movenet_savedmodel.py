# download_movenet_savedmodel.py
# Downloads MoveNet Lightning as a TensorFlow SavedModel.
# Run this on Mac in your capstone environment.
# Output: ~/Desktop/capstone/movenet_savedmodel/
#
# Usage:
#   python download_movenet_savedmodel.py

import os
import urllib.request
import tarfile

SAVE_DIR = os.path.expanduser("~/Desktop/capstone/movenet_savedmodel")
os.makedirs(SAVE_DIR, exist_ok=True)

# MoveNet Lightning v4 SavedModel from TF Hub (float16)
# This is the full SavedModel — not TFLite — needed for Vitis AI conversion
URL = "https://tfhub.dev/google/movenet/singlepose/lightning/4?tf-hub-format=compressed"
TAR_PATH = os.path.join(SAVE_DIR, "movenet_lightning.tar.gz")

print("Downloading MoveNet Lightning SavedModel (~25MB)...")
print("URL:", URL)

try:
    urllib.request.urlretrieve(URL, TAR_PATH)
    print("Download complete.")
except Exception as e:
    print(f"Auto-download failed: {e}")
    print("\nManual download instead:")
    print("1. Go to: https://tfhub.dev/google/movenet/singlepose/lightning/4")
    print("2. Click 'Download' → save as movenet_lightning.tar.gz")
    print(f"3. Move to: {TAR_PATH}")
    print("4. Re-run this script")
    exit(1)

print("Extracting...")
with tarfile.open(TAR_PATH, "r:gz") as tar:
    tar.extractall(SAVE_DIR)

print(f"\nSavedModel extracted to: {SAVE_DIR}")
print("Contents:")
for f in os.listdir(SAVE_DIR):
    print(f"  {f}")

print("\nNext step: copy this folder to your Linux/WSL2 machine")
print(f"  scp -r {SAVE_DIR} user@linux-machine:~/capstone/")
