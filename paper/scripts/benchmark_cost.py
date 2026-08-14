"""
Computational-cost measurements for the manuscript's runtime table.

What is MEASURED here (on the machine the project was developed on, CPU only):
  - exact trainable / frozen parameter counts per model
  - weight memory footprint in MiB (fp32)
  - end-to-end single-image inference latency, split into the preprocessing
    stage (decode + 3-way capture normalisation + resize/tensor) and the
    forward pass, timed over the 74 Split B test images after warm-up

What is NOT measured, and is reported as such in the manuscript rather than
estimated: training wall-clock time. The original training runs were not
instrumented for it, and the host repeatedly killed long-running background
processes during the project, so any retrospective wall-clock figure would be
unreliable. Epochs-to-convergence (paper/tables/table_training_curves.csv) is
reported in its place.

Output: paper/tables/table_cost.csv
"""
import csv
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tvm
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modeling"))
from common import load_examples, build_transform, IMG_SIZE  # noqa: E402
from normalization import normalize_capture_confounds  # noqa: E402
from train_model1_classical import extract_histogram, N_BINS  # noqa: E402
from train_model2_cnn import SmallCNN  # noqa: E402

OUT = ROOT / "paper" / "tables" / "table_cost.csv"
MIB = 1024 ** 2
N_WARMUP = 5


def count(module):
    tr = sum(p.numel() for p in module.parameters() if p.requires_grad)
    fr = sum(p.numel() for p in module.parameters() if not p.requires_grad)
    return tr, fr


def time_stage(fn, items, warmup=N_WARMUP):
    for it in items[:warmup]:
        fn(it)
    t0 = time.perf_counter()
    for it in items:
        fn(it)
    return (time.perf_counter() - t0) / len(items) * 1000.0   # ms/image


def main():
    examples = [e for e in load_examples("split_b") if e["split"] == "test"]
    paths = [e["path"] for e in examples]
    print(f"timing over {len(paths)} Split B test images, CPU, torch {torch.__version__}")

    eval_tf = build_transform(train=False)
    rows = []

    # ---- M1: histogram + logistic regression -------------------------------
    # No PharmaImageDataset, so no capture normalisation, by design.
    pre = time_stage(lambda p: extract_histogram(p), paths)
    feats = [extract_histogram(p) for p in paths]
    rng = np.random.RandomState(0)
    w = rng.normal(size=3 * N_BINS)
    b = 0.1
    fwd = time_stage(lambda x: float(1.0 / (1.0 + np.exp(-(w @ x + b)))), feats)
    rows.append({
        "model": "M1", "model_full": "Colour histogram + LogReg",
        "trainable_params": 3 * N_BINS + 1, "frozen_params": 0,
        "weight_memory_mib": (3 * N_BINS + 1) * 4 / MIB,
        "preprocess_ms_per_image": pre,
        "forward_ms_per_image": fwd,
        "total_ms_per_image": pre + fwd,
        "throughput_images_per_s": 1000.0 / (pre + fwd),
    })
    print(f"  M1 pre {pre:.2f} ms  fwd {fwd:.4f} ms")

    # ---- shared preprocessing for M2/M3/M4 ---------------------------------
    def preprocess(p):
        img = Image.open(p).convert("RGB")
        img = normalize_capture_confounds(img)
        return eval_tf(img).unsqueeze(0)

    pre_nn = time_stage(preprocess, paths)
    tensors = [preprocess(p) for p in paths]
    print(f"  shared preprocessing (decode + 3-way normalisation + resize): {pre_nn:.2f} ms")

    specs = []
    m2 = SmallCNN().eval()
    specs.append(("M2", "Small CNN (GAP head)", m2, m2))

    mn = tvm.mobilenet_v3_small(weights=tvm.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
    mn_features = mn.features.eval()
    for p in mn_features.parameters():
        p.requires_grad = False
    m3 = nn.Sequential(mn_features, nn.AdaptiveAvgPool2d(1), nn.Flatten(),
                       nn.Dropout(0.3), nn.Linear(576, 2)).eval()
    specs.append(("M3", "MobileNetV3-Small (frozen)", m3, m3))

    en = tvm.efficientnet_b0(weights=tvm.EfficientNet_B0_Weights.IMAGENET1K_V1)
    en_features = en.features.eval()
    for p in en_features.parameters():
        p.requires_grad = False
    m4 = nn.Sequential(en_features, nn.AdaptiveAvgPool2d(1), nn.Flatten(),
                       nn.Dropout(0.3), nn.Linear(1280, 2)).eval()
    specs.append(("M4", "EfficientNet-B0 (frozen)", m4, m4))

    for tag, name, model, _ in specs:
        tr, fr = count(model)
        with torch.no_grad():
            fwd = time_stage(lambda t: model(t), tensors)
        total = pre_nn + fwd
        rows.append({
            "model": tag, "model_full": name,
            "trainable_params": tr, "frozen_params": fr,
            "weight_memory_mib": (tr + fr) * 4 / MIB,
            "preprocess_ms_per_image": pre_nn,
            "forward_ms_per_image": fwd,
            "total_ms_per_image": total,
            "throughput_images_per_s": 1000.0 / total,
        })
        print(f"  {tag} params {tr:,} trainable / {fr:,} frozen  fwd {fwd:.1f} ms  "
              f"total {total:.1f} ms  ({1000.0/total:.1f} img/s)")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w_ = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w_.writeheader()
        w_.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
