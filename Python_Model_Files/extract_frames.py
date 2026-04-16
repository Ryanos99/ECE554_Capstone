# extract_frames.py
# Extracts frames from a video file into a dataset folder.
# Works with .mov, .mp4, .avi and most other formats.
#
# Usage:
#   python extract_frames.py --video ~/Desktop/squat.mov --label squat
#   python extract_frames.py --video ~/Desktop/pushup.mov --label "push up"
#   python extract_frames.py --video ~/Desktop/curl.mov --label "barbell biceps curl"

import cv2
import os
import argparse

DATASET_DIR = "./dataset"
FRAME_SKIP  = 3    # save every 3rd frame (~10fps from 30fps video)

def extract_frames(video_path, label, frame_skip=FRAME_SKIP):
    output_dir = os.path.join(DATASET_DIR, label)
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Could not open video: {video_path}")
        return

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps   = cap.get(cv2.CAP_PROP_FPS)
    print(f"Video: {total} frames @ {fps:.0f}fps")
    print(f"Output: {output_dir}")

    # Start numbering after existing files
    existing  = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
    start_idx = len(existing)

    saved     = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_skip == 0:
            filename = f"real_{start_idx + saved:05d}.jpg"
            cv2.imwrite(os.path.join(output_dir, filename), frame)
            saved += 1
        frame_idx += 1

    cap.release()
    print(f"Saved {saved} frames — total in folder: {start_idx + saved}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--skip",  type=int, default=FRAME_SKIP)
    args = parser.parse_args()

    print(f"\nExtracting '{args.label}' from {args.video}...")
    extract_frames(args.video, args.label, args.skip)
    print("\nDone. Next: python extract_keypoints.py")
