"""
Quantify probability calibration for all four models on both in-distribution
test partitions.

Gap this closes: a reviewer observed that the manuscript flags overconfident
wrong predictions qualitatively -- Grad-CAM on external images shows
predicted-counterfeit probabilities of 0.94-1.00 on images that are all
authentic -- and plots reliability curves, but never reports a calibration
statistic. For a model proposed (by the literature this paper critiques, not
by this paper) as a triage tool, calibration is the property that decides
whether a score can be thresholded at all.

Reads only the committed per-image predictions in
modeling/results/predictions/, so it needs no images, no model and no
training, and runs in well under a second.

Reported per model and split:

  Brier   mean squared error of the predicted probability. Proper scoring
          rule: rewards being both right and appropriately unsure.
  ECE     expected calibration error, 10 equal-width confidence bins, the
          sample-weighted mean |accuracy - confidence| over bins.
  MCE     maximum calibration error, the worst single bin.
  conf    mean confidence, i.e. mean max(p, 1-p).
  acc     accuracy, for comparison with conf. conf - acc > 0 is overconfidence.

Output: paper/tables/calibration.csv (and a printed table)
"""
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PRED_DIR = ROOT / "modeling" / "results" / "predictions"
OUT = ROOT / "paper" / "tables" / "calibration.csv"

MODELS = [
    ("model1_classical_colorhist_logreg", "M1 hist+LR"),
    ("model2_smallcnn_gap", "M2 CNN"),
    ("model3_mobilenetv3small_frozen", "M3 MobileNetV3"),
    ("model4_efficientnetb0_frozen", "M4 EfficientNet-B0"),
]
N_BINS = 10


def load(tag, split):
    path = PRED_DIR / f"{tag}__{split}.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    y = np.array([int(r["y_true"]) for r in rows])
    p = np.array([float(r["y_prob"]) for r in rows])
    return y, p


def calibration(y, p):
    """Brier, ECE, MCE, mean confidence, accuracy. Positive class = counterfeit."""
    pred = (p >= 0.5).astype(int)
    correct = (pred == y).astype(float)
    conf = np.maximum(p, 1.0 - p)          # confidence in the predicted class

    brier = float(np.mean((p - y) ** 2))

    edges = np.linspace(0.5, 1.0, N_BINS + 1)
    ece, mce = 0.0, 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        in_bin = (conf > lo) & (conf <= hi) if lo > 0.5 else (conf >= lo) & (conf <= hi)
        n = int(in_bin.sum())
        if n == 0:
            continue
        gap = abs(correct[in_bin].mean() - conf[in_bin].mean())
        ece += (n / len(y)) * gap
        mce = max(mce, gap)

    return {"brier": brier, "ece": ece, "mce": mce,
            "conf": float(conf.mean()), "acc": float(correct.mean())}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for tag, label in MODELS:
        for split in ("split_a", "split_b", "split_c", "split_d"):
            if not (PRED_DIR / f"{tag}__{split}.csv").exists():
                continue
            y, p = load(tag, split)
            m = calibration(y, p)
            rows.append({
                "model": label,
                "split": split[-1].upper(),
                "n": len(y),
                "brier": round(m["brier"], 4),
                "ece": round(m["ece"], 4),
                "mce": round(m["mce"], 4),
                "mean_confidence": round(m["conf"], 4),
                "accuracy": round(m["acc"], 4),
                "overconfidence": round(m["conf"] - m["acc"], 4),
            })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    hdr = f"{'model':<22}{'split':<7}{'n':>4}{'Brier':>9}{'ECE':>8}{'MCE':>8}{'conf':>8}{'acc':>8}{'conf-acc':>10}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['model']:<22}{r['split']:<7}{r['n']:>4}{r['brier']:>9.4f}"
              f"{r['ece']:>8.4f}{r['mce']:>8.4f}{r['mean_confidence']:>8.4f}"
              f"{r['accuracy']:>8.4f}{r['overconfidence']:>10.4f}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
