# test_model.py
# Validates best_model.pth by running inference on images or webcam.
# Run this on your Mac before handing off to Vitis AI quantization.
#
# Usage:
#   python test_model.py --image path/to/image.jpg   (test single image)
#   python test_model.py --webcam                     (live webcam test)
#   python test_model.py --folder path/to/folder      (test whole folder)

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import json
import argparse
import os

# ==============================================================================
# Config — must match train_resnet50.py exactly
# ==============================================================================
WEIGHTS_PATH = "./outputs/best_model.pth"
LABELS_PATH  = "./outputs/class_labels.json"
IMAGE_SIZE   = 224
DEVICE       = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# ==============================================================================
# Load model
# ==============================================================================
def load_model(weights_path, num_classes):
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(torch.load(weights_path, map_location=DEVICE))
    model.eval()
    model.to(DEVICE)
    print(f"Model loaded from {weights_path}")
    return model

# ==============================================================================
# Preprocessing — must match train_resnet50.py val transform
# ==============================================================================
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

def preprocess(img_rgb):
    """Input: PIL Image. Output: tensor ready for model."""
    return transform(img_rgb).unsqueeze(0).to(DEVICE)

# ==============================================================================
# Inference
# ==============================================================================
def predict(model, tensor, class_labels):
    with torch.no_grad():
        outputs = model(tensor)
        probs   = torch.softmax(outputs, dim=1)[0]
        top5    = torch.topk(probs, 5)

    results = []
    for prob, idx in zip(top5.values, top5.indices):
        results.append((class_labels[idx.item()], prob.item()))
    return results

def print_results(results):
    print("\n  Top 5 predictions:")
    for i, (label, conf) in enumerate(results):
        bar = "█" * int(conf * 30)
        print(f"  {i+1}. {label:<30s} {conf:.1%}  {bar}")
    print()

# ==============================================================================
# Test modes
# ==============================================================================
def test_image(model, image_path, class_labels):
    img = Image.open(image_path).convert("RGB")
    tensor = preprocess(img)
    results = predict(model, tensor, class_labels)
    print(f"\nImage: {image_path}")
    print_results(results)

def test_folder(model, folder_path, class_labels):
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    files = [f for f in os.listdir(folder_path)
             if os.path.splitext(f)[1].lower() in exts]

    if not files:
        print(f"No images found in {folder_path}")
        return

    correct = 0
    total   = len(files)
    print(f"\nTesting {total} images in {folder_path}...\n")

    for fname in sorted(files):
        path = os.path.join(folder_path, fname)
        img  = Image.open(path).convert("RGB")
        tensor = preprocess(img)
        results = predict(model, tensor, class_labels)
        top_label, top_conf = results[0]
        print(f"  {fname:<40s} → {top_label:<30s} ({top_conf:.1%})")

def test_webcam(model, class_labels):
    try:
        import cv2
    except ImportError:
        print("opencv-python not installed. Run: pip install opencv-python")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    print("Webcam test running. Press Q to quit, SPACE to freeze a prediction.")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break

        # Convert BGR → RGB → PIL
        frame_rgb = frame_bgr[:, :, ::-1].copy()
        img = Image.fromarray(frame_rgb)
        tensor = preprocess(img)
        results = predict(model, tensor, class_labels)
        top_label, top_conf = results[0]

        # Overlay prediction on frame
        text = f"{top_label} ({top_conf:.0%})"
        cv2.putText(frame_bgr, text, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        # Show top 3 below
        for i, (label, conf) in enumerate(results[:3]):
            small = f"{i+1}. {label} {conf:.0%}"
            cv2.putText(frame_bgr, small, (10, 80 + i*30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Exercise Recognition - Press Q to quit", frame_bgr)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test exercise recognition model")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image",  type=str, help="Path to a single image file")
    group.add_argument("--folder", type=str, help="Path to folder of images")
    group.add_argument("--webcam", action="store_true", help="Use webcam")
    args = parser.parse_args()

    # Load labels
    with open(LABELS_PATH) as f:
        class_labels = json.load(f)
    print(f"Loaded {len(class_labels)} classes")

    # Load model
    model = load_model(WEIGHTS_PATH, len(class_labels))
    print(f"Running on: {DEVICE}\n")

    if args.image:
        test_image(model, args.image, class_labels)
    elif args.folder:
        test_folder(model, args.folder, class_labels)
    elif args.webcam:
        test_webcam(model, class_labels)