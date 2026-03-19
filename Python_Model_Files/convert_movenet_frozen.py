# convert_movenet_frozen.py
# Converts MoveNet Lightning SavedModel to a frozen TF protobuf (.pb)
# that Vitis AI can inspect and quantize.
#
# Run this INSIDE the Vitis AI Docker container on Linux/WSL2:
#   docker run -it -v ~/capstone:/workspace xilinx/vitis-ai-tensorflow2-cpu:latest
#   cd /workspace
#   python convert_movenet_frozen.py
#
# Output: /workspace/movenet_frozen/movenet_frozen.pb
#         /workspace/movenet_frozen/input_output_info.txt
#
# The input_output_info.txt is needed for vai_inspector in the next step.

import os
import numpy as np
import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import (
    convert_variables_to_constants_v2
)

SAVED_MODEL_DIR = "./movenet_savedmodel"
OUTPUT_DIR      = "./movenet_frozen"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"TensorFlow version: {tf.__version__}")
print(f"Loading SavedModel from: {SAVED_MODEL_DIR}")

# ---- Load SavedModel ----
model = tf.saved_model.load(SAVED_MODEL_DIR)
infer = model.signatures["serving_default"]

# ---- Print input/output info ----
print("\n--- Input tensors ---")
for name, tensor in infer.structured_input_signature[1].items():
    print(f"  {name}: shape={tensor.shape}, dtype={tensor.dtype}")

print("\n--- Output tensors ---")
for name, tensor in infer.structured_outputs.items():
    print(f"  {name}: shape={tensor.shape}, dtype={tensor.dtype}")

# Save this info to file — needed for vai_inspector flags
info_path = os.path.join(OUTPUT_DIR, "input_output_info.txt")
with open(info_path, "w") as f:
    f.write("=== MoveNet Lightning Input/Output Info ===\n\n")
    f.write("INPUT TENSORS:\n")
    for name, tensor in infer.structured_input_signature[1].items():
        f.write(f"  name: {name}\n")
        f.write(f"  shape: {tensor.shape}\n")
        f.write(f"  dtype: {tensor.dtype}\n\n")
    f.write("OUTPUT TENSORS:\n")
    for name, tensor in infer.structured_outputs.items():
        f.write(f"  name: {name}\n")
        f.write(f"  shape: {tensor.shape}\n")
        f.write(f"  dtype: {tensor.dtype}\n\n")

print(f"\nInput/output info saved to: {info_path}")

# ---- Convert to frozen graph ----
print("\nConverting to frozen graph (this may take a minute)...")

@tf.function(input_signature=[
    tf.TensorSpec(shape=[1, 192, 192, 3], dtype=tf.uint8, name="input")
])
def serving_fn(input):
    return infer(input)

concrete_func = serving_fn.get_concrete_function()
frozen_func   = convert_variables_to_constants_v2(concrete_func)
frozen_graph  = frozen_func.graph

# Print all ops in the frozen graph — useful to check for unsupported ops
ops_path = os.path.join(OUTPUT_DIR, "graph_ops.txt")
with open(ops_path, "w") as f:
    op_types = sorted(set(op.type for op in frozen_graph.get_operations()))
    f.write("=== Op types in frozen graph ===\n\n")
    for op_type in op_types:
        count = sum(1 for op in frozen_graph.get_operations() if op.type == op_type)
        f.write(f"  {op_type:<40} x{count}\n")

print(f"Op list saved to: {ops_path}")

# Write the frozen .pb file
pb_path = os.path.join(OUTPUT_DIR, "movenet_frozen.pb")
tf.io.write_graph(
    frozen_graph,
    OUTPUT_DIR,
    "movenet_frozen.pb",
    as_text=False
)

print(f"\nFrozen graph saved to: {pb_path}")
print(f"File size: {os.path.getsize(pb_path) / 1e6:.1f} MB")

# ---- Quick sanity check ---- 
print("\nRunning sanity check with dummy input...")
dummy_input  = np.random.randint(0, 255, (1, 192, 192, 3), dtype=np.uint8)
dummy_tensor = tf.constant(dummy_input)
result       = infer(dummy_tensor)

for name, tensor in result.items():
    print(f"  Output '{name}': shape={tensor.shape}, dtype={tensor.dtype}")
    if "keypoint" in name.lower():
        kps = tensor.numpy().reshape(17, 3)
        print(f"  Keypoints (y, x, conf):")
        kp_names = [
            "nose","left_eye","right_eye","left_ear","right_ear",
            "left_shoulder","right_shoulder","left_elbow","right_elbow",
            "left_wrist","right_wrist","left_hip","right_hip",
            "left_knee","right_knee","left_ankle","right_ankle"
        ]
        for i, (y, x, c) in enumerate(kps):
            print(f"    {kp_names[i]:<20} y={y:.3f} x={x:.3f} conf={c:.3f}")

print("\n=== Conversion complete ===")
print("Next step — run the inspector:")
print()
print("  vai_inspector \\")
print("    --model /workspace/movenet_frozen/movenet_frozen.pb \\")
print("    --arch   /workspace/arch.json \\")
print("    --output_dir /workspace/inspect_results/")
print()
print("NOTE: You need arch.json from your DPU bitstream.")
print("If you don't have it yet, see arch_json_placeholder.json for the")
print("B2304 template — results will be approximate until you have the real one.")
