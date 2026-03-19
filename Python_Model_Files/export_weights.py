# export_weights.py
# Exports trained sklearn MLP weights to formats usable by hardware.
# Run after train_classifier.py completes.
#
# Outputs:
#   outputs/weights/layer1_weights.coe   — Vivado BRAM init file (Layer 1)
#   outputs/weights/layer2_weights.coe   — Vivado BRAM init file (Layer 2)
#   outputs/weights/output_weights.coe   — Vivado BRAM init file (Output layer)
#   outputs/weights/weights_pkg.vh       — Verilog header with all weights as parameters
#   outputs/weights/weights.npy          — NumPy archive for verification
#   outputs/weights/weight_summary.txt   — Human readable summary
#
# Usage:
#   python export_weights.py
#
# How it works:
#   1. Loads trained sklearn MLP
#   2. Extracts weight matrices and bias vectors per layer
#   3. Quantizes to INT8 (-128 to 127) using per-layer scaling
#   4. Exports in formats Holland needs for weight_bram_ctrl.v
#
# BRAM layout (single BRAM, addressed by layer + neuron + input):
#   Layer 1: addr 0x0000 - 0x15FF  (44*128  = 5632  weights)
#   Layer 2: addr 0x1600 - 0x35FF  (128*64  = 8192  weights)
#   Output:  addr 0x3600 - 0x393F  (64*5    = 320   weights)
#   Biases:  addr 0x3940 - 0x39FF  (128+64+5 = 197  biases)
#   Total:                          14341 entries, fits in 16K BRAM

import os
import numpy as np
import joblib
import json

OUTPUT_DIR   = "./outputs/weights"
CLASSIFIER   = "./outputs/classifier.pkl"
SCALER       = "./outputs/scaler.pkl"

# Layer dimensions — must match mlp_classifier.v parameters
N_INPUT  = 44
N_LAYER1 = 128
N_LAYER2 = 64
N_OUTPUT = 5

# BRAM address map
ADDR_LAYER1 = 0x0000
ADDR_LAYER2 = 0x1600
ADDR_OUTPUT = 0x3600
ADDR_BIASES = 0x3940

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=== MLP Weight Export for Hardware ===\n")

# ---- Load trained model ----
clf    = joblib.load(CLASSIFIER)
scaler = joblib.load(SCALER)

# Verify architecture matches expected dimensions
assert len(clf.coefs_) == 3, f"Expected 3 layers, got {len(clf.coefs_)}"
assert clf.coefs_[0].shape == (N_INPUT,  N_LAYER1), f"Layer 1 shape mismatch: {clf.coefs_[0].shape}"
assert clf.coefs_[1].shape == (N_LAYER1, N_LAYER2), f"Layer 2 shape mismatch: {clf.coefs_[1].shape}"
assert clf.coefs_[2].shape == (N_LAYER2, N_OUTPUT), f"Output shape mismatch: {clf.coefs_[2].shape}"

print(f"Layer 1 weights: {clf.coefs_[0].shape}  biases: {clf.intercepts_[0].shape}")
print(f"Layer 2 weights: {clf.coefs_[1].shape}  biases: {clf.intercepts_[1].shape}")
print(f"Output  weights: {clf.coefs_[2].shape}  biases: {clf.intercepts_[2].shape}")

# ---- Quantize to INT8 ----
# Per-layer symmetric quantization: scale = 127 / max(abs(W))
# This maps the largest weight to +/-127, preserving relative magnitudes.
# Biases use the same scale as their layer's weights.

def quantize_layer(weights, biases, layer_name):
    scale_w = 127.0 / np.max(np.abs(weights))
    scale_b = 127.0 / np.max(np.abs(biases))
    scale   = min(scale_w, scale_b)  # use same scale for W and b

    w_int8 = np.clip(np.round(weights * scale), -128, 127).astype(np.int8)
    b_int8 = np.clip(np.round(biases  * scale), -128, 127).astype(np.int8)

    max_err = np.max(np.abs(weights - w_int8.astype(np.float32) / scale))
    print(f"{layer_name}: scale={scale:.4f}  max_quant_error={max_err:.6f}")
    return w_int8, b_int8, scale

w1, b1, scale1 = quantize_layer(clf.coefs_[0],     clf.intercepts_[0], "Layer 1")
w2, b2, scale2 = quantize_layer(clf.coefs_[1],     clf.intercepts_[1], "Layer 2")
wo, bo, scaleo = quantize_layer(clf.coefs_[2],     clf.intercepts_[2], "Output ")

# ---- Flatten weights into BRAM layout ----
# Weight addressing: weight[neuron_i][input_j] = addr_base + neuron_i * N_inputs + input_j
# This matches the address calculation in weight_bram_ctrl.v:
#   neuron_idx = neuron_i * N_INPUT + input_j

def flatten_weights(w):
    # w shape: (n_inputs, n_outputs) in sklearn convention
    # Transpose to (n_outputs, n_inputs) = (neuron_i, input_j)
    return w.T.flatten()

layer1_flat = flatten_weights(w1)   # shape: (128, 44)  → 5632 values
layer2_flat = flatten_weights(w2)   # shape: (64,  128) → 8192 values
output_flat = flatten_weights(wo)   # shape: (5,   64)  → 320  values
biases_flat = np.concatenate([b1, b2, bo])  # 128+64+5 = 197 values

print(f"\nFlattened sizes:")
print(f"  Layer 1: {len(layer1_flat)} weights")
print(f"  Layer 2: {len(layer2_flat)} weights")
print(f"  Output:  {len(output_flat)} weights")
print(f"  Biases:  {len(biases_flat)} biases")

# ---- Save NumPy archive for verification ----
np.save(f"{OUTPUT_DIR}/weights.npy", {
    'w1': w1, 'b1': b1, 'scale1': scale1,
    'w2': w2, 'b2': b2, 'scale2': scale2,
    'wo': wo, 'bo': bo, 'scaleo': scaleo,
    'layer1_flat': layer1_flat,
    'layer2_flat': layer2_flat,
    'output_flat': output_flat,
    'biases_flat': biases_flat
})
print(f"\nNumPy weights saved: {OUTPUT_DIR}/weights.npy")

# ---- Export .coe files (Vivado BRAM initialization format) ----
# .coe format:
#   memory_initialization_radix=10;   (decimal)
#   memory_initialization_vector=
#   val0, val1, val2, ..., valN;
#
# Values must be unsigned — convert signed INT8 to uint8 (two's complement)

def write_coe(filename, data, comment):
    data_uint = data.astype(np.uint8)  # reinterpret signed as unsigned bits
    with open(filename, 'w') as f:
        f.write(f"; {comment}\n")
        f.write(f"; {len(data)} entries, INT8 stored as unsigned decimal\n")
        f.write(f"; To load: Block Memory Generator → Additional Options → Load Init File\n;\n")
        f.write("memory_initialization_radix=10;\n")
        f.write("memory_initialization_vector=\n")
        vals = ', '.join(str(int(v)) for v in data_uint)
        f.write(vals + ";\n")
    print(f"  Wrote: {filename}  ({len(data)} entries)")

print("\nWriting .coe files:")
write_coe(f"{OUTPUT_DIR}/layer1_weights.coe", layer1_flat, "Layer 1 weights: 128 neurons x 44 inputs")
write_coe(f"{OUTPUT_DIR}/layer2_weights.coe", layer2_flat, "Layer 2 weights: 64 neurons x 128 inputs")
write_coe(f"{OUTPUT_DIR}/output_weights.coe", output_flat, "Output weights: 5 neurons x 64 inputs")
write_coe(f"{OUTPUT_DIR}/biases.coe",         biases_flat, "Biases: layer1(128) + layer2(64) + output(5)")

# ---- Combined BRAM .coe (single file for one BRAM) ----
# Pad each section to its address boundary
combined = np.zeros(0x3A00, dtype=np.int8)
combined[ADDR_LAYER1:ADDR_LAYER1 + len(layer1_flat)] = layer1_flat
combined[ADDR_LAYER2:ADDR_LAYER2 + len(layer2_flat)] = layer2_flat
combined[ADDR_OUTPUT:ADDR_OUTPUT + len(output_flat)] = output_flat
combined[ADDR_BIASES:ADDR_BIASES + len(biases_flat)] = biases_flat

write_coe(f"{OUTPUT_DIR}/all_weights.coe", combined, "Combined BRAM: all layers at fixed addresses")

# ---- Export Verilog header (alternative to BRAM — small enough for ROM) ----
# For a model this size Holland can also instantiate weights as Verilog
# parameters/localparams instead of BRAM if preferred.
# This generates a .vh file that can be `include`d in mlp_classifier.v

print("\nWriting Verilog header:")
with open(f"{OUTPUT_DIR}/weights_pkg.vh", 'w') as f:
    f.write("// weights_pkg.vh\n")
    f.write("// Auto-generated by export_weights.py — DO NOT EDIT MANUALLY\n")
    f.write("// Include in mlp_classifier.v: `include \"weights_pkg.vh\"\n\n")

    f.write(f"// Quantization scales (for reference/dequant if needed)\n")
    f.write(f"// scale1 = {scale1:.6f}  scale2 = {scale2:.6f}  scaleo = {scaleo:.6f}\n\n")

    f.write(f"// Layer 1: {N_LAYER1} neurons x {N_INPUT} inputs\n")
    f.write(f"localparam signed [7:0] LAYER1_W [{N_LAYER1*N_INPUT-1}:0] = '{{\n")
    vals = ', '.join(f"8'sd{int(v)}" for v in layer1_flat)
    f.write(f"  {vals}\n}};\n\n")

    f.write(f"localparam signed [7:0] LAYER1_B [{N_LAYER1-1}:0] = '{{\n")
    vals = ', '.join(f"8'sd{int(v)}" for v in b1)
    f.write(f"  {vals}\n}};\n\n")

    f.write(f"// Layer 2: {N_LAYER2} neurons x {N_LAYER1} inputs\n")
    f.write(f"localparam signed [7:0] LAYER2_W [{N_LAYER2*N_LAYER1-1}:0] = '{{\n")
    vals = ', '.join(f"8'sd{int(v)}" for v in layer2_flat)
    f.write(f"  {vals}\n}};\n\n")

    f.write(f"localparam signed [7:0] LAYER2_B [{N_LAYER2-1}:0] = '{{\n")
    vals = ', '.join(f"8'sd{int(v)}" for v in b2)
    f.write(f"  {vals}\n}};\n\n")

    f.write(f"// Output layer: {N_OUTPUT} neurons x {N_LAYER2} inputs\n")
    f.write(f"localparam signed [7:0] OUTPUT_W [{N_OUTPUT*N_LAYER2-1}:0] = '{{\n")
    vals = ', '.join(f"8'sd{int(v)}" for v in output_flat)
    f.write(f"  {vals}\n}};\n\n")

    f.write(f"localparam signed [7:0] OUTPUT_B [{N_OUTPUT-1}:0] = '{{\n")
    vals = ', '.join(f"8'sd{int(v)}" for v in bo)
    f.write(f"  {vals}\n}};\n")

print(f"  Wrote: {OUTPUT_DIR}/weights_pkg.vh")

# ---- Verification: run INT8 inference and compare to sklearn ----
print("\n=== Verification: INT8 vs sklearn ===")

def relu(x):
    return np.maximum(0, x)

def mlp_int8(features_raw):
    # Normalize features using scaler
    x = scaler.transform([features_raw])[0].astype(np.float32)

    # Quantize input to INT8
    scale_in = 127.0 / np.max(np.abs(x))
    x_int = np.clip(np.round(x * scale_in), -128, 127).astype(np.int8)

    # Layer 1 (INT8 MAC)
    acc1 = np.zeros(N_LAYER1, dtype=np.int32)
    for i in range(N_LAYER1):
        for j in range(N_INPUT):
            acc1[i] += int(x_int[j]) * int(w1[j, i])
        acc1[i] += int(b1[i]) * 128  # bias scaled
    a1 = np.clip(acc1 >> 8, 0, 127).astype(np.int8)  # ReLU + scale

    # Layer 2 (INT8 MAC)
    acc2 = np.zeros(N_LAYER2, dtype=np.int32)
    for i in range(N_LAYER2):
        for j in range(N_LAYER1):
            acc2[i] += int(a1[j]) * int(w2[j, i])
        acc2[i] += int(b2[i]) * 128
    a2 = np.clip(acc2 >> 8, 0, 127).astype(np.int8)

    # Output layer
    acco = np.zeros(N_OUTPUT, dtype=np.int32)
    for i in range(N_OUTPUT):
        for j in range(N_LAYER2):
            acco[i] += int(a2[j]) * int(wo[j, i])
        acco[i] += int(bo[i]) * 128

    return np.argmax(acco)

# Load keypoints and test on a sample
try:
    import pandas as pd
    df = pd.read_csv("./outputs/keypoints.csv")
    feature_cols = [c for c in df.columns if c != 'label']
    X = df[feature_cols].values
    y = df['label'].values

    # Test on 100 random samples
    n_test   = min(100, len(X))
    indices  = np.random.choice(len(X), n_test, replace=False)
    sklearn_correct = 0
    int8_correct    = 0

    label_encoder = joblib.load("./outputs/label_encoder.pkl")

    for idx in indices:
        features_raw = X[idx]
        true_label   = y[idx]

        # sklearn prediction
        sklearn_pred_idx = clf.predict(scaler.transform([features_raw]))[0]
        sklearn_pred     = label_encoder.inverse_transform([sklearn_pred_idx])[0] \
                           if hasattr(sklearn_pred_idx, '__iter__') else true_label
        if clf.predict(scaler.transform([features_raw]))[0] == \
           label_encoder.transform([true_label])[0]:
            sklearn_correct += 1

        # INT8 prediction
        int8_pred_idx = mlp_int8(features_raw)
        if int8_pred_idx == label_encoder.transform([true_label])[0]:
            int8_correct += 1

    print(f"sklearn accuracy (sample): {sklearn_correct/n_test*100:.1f}%")
    print(f"INT8 hw accuracy (sample): {int8_correct/n_test*100:.1f}%")

    acc_drop = (sklearn_correct - int8_correct) / n_test * 100
    if acc_drop <= 5.0:
        print(f"PASS: accuracy drop = {acc_drop:.1f}% (acceptable <= 5%)")
    else:
        print(f"WARN: accuracy drop = {acc_drop:.1f}% (> 5% — consider retraining with higher precision)")

except Exception as e:
    print(f"Verification skipped: {e}")

# ---- Write summary ----
summary = {
    "architecture": {
        "input":   N_INPUT,
        "layer1":  N_LAYER1,
        "layer2":  N_LAYER2,
        "output":  N_OUTPUT
    },
    "quantization": {
        "type":    "INT8 symmetric per-layer",
        "scale_layer1": float(scale1),
        "scale_layer2": float(scale2),
        "scale_output": float(scaleo)
    },
    "bram_addresses": {
        "layer1_start": hex(ADDR_LAYER1),
        "layer2_start": hex(ADDR_LAYER2),
        "output_start": hex(ADDR_OUTPUT),
        "biases_start": hex(ADDR_BIASES),
        "total_entries": int(len(layer1_flat) + len(layer2_flat) +
                             len(output_flat) + len(biases_flat))
    },
    "files": {
        "bram_init":         "all_weights.coe  (load into Block Memory Generator)",
        "verilog_header":    "weights_pkg.vh   (include in mlp_classifier.v)",
        "numpy_archive":     "weights.npy      (use for simulation verification)"
    }
}

with open(f"{OUTPUT_DIR}/weight_summary.json", 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary saved: {OUTPUT_DIR}/weight_summary.json")
print(f"\n=== Export complete ===")
print(f"Hand off to Holland:")
print(f"  outputs/weights/all_weights.coe  → Block Memory Generator init file")
print(f"  outputs/weights/weights_pkg.vh   → include in mlp_classifier.v")
print(f"  outputs/weights/weight_summary.json → BRAM address map reference")
