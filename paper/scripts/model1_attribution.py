"""
Feature attribution for Model 1 (96-dim RGB colour histogram + logistic
regression), refit deterministically on Split B's train partition exactly as
`modeling/train_model1_classical.py` does (same features, same
class_weight='balanced', same seed), then attributed two ways:

  1. Signed logistic-regression coefficients per histogram bin.
  2. Exact Shapley values. For a linear model the Shapley value of feature i
     for instance x is phi_i(x) = beta_i * (x_i - E[x_i]) (Lundberg & Lee's
     LinearExplainer with an independent-feature background). No sampling or
     approximation is involved, so no `shap` package is needed; the reported
     global importance is mean_x |phi_i(x)| over the Split B test partition,
     with E[x] taken over the train partition.

This is the paper's feature-importance / attribution figure for the one model
whose decision function is small enough to read directly. Models 2-4 are
attributed with Grad-CAM instead (modeling/gradcam*.py) -- gradient-based
saliency, not Shapley -- because a 1280-dim frozen-backbone embedding has no
human-interpretable per-feature axis to attribute to.

Output: paper/tables/model1_attribution.csv
"""
import csv
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modeling"))
from common import load_examples, set_seed, SEED  # noqa: E402
from train_model1_classical import extract_histogram, N_BINS  # noqa: E402

OUT = ROOT / "paper" / "tables" / "model1_attribution.csv"


def main():
    examples = load_examples("split_b")
    train = [e for e in examples if e["split"] == "train"]
    test = [e for e in examples if e["split"] == "test"]

    X_tr = np.stack([extract_histogram(e["path"]) for e in train])
    y_tr = np.array([e["label"] for e in train])
    X_te = np.stack([extract_histogram(e["path"]) for e in test])

    set_seed(SEED)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
    clf.fit(X_tr, y_tr)

    beta = clf.coef_[0]
    baseline = X_tr.mean(axis=0)
    phi = (X_te - baseline) * beta            # exact per-instance Shapley values
    mean_abs_phi = np.abs(phi).mean(axis=0)
    mean_phi = phi.mean(axis=0)

    channels = ["R", "G", "B"]
    rows = []
    for i in range(len(beta)):
        ch = channels[i // N_BINS]
        b = i % N_BINS
        rows.append({
            "feature_index": i,
            "channel": ch,
            "bin": b,
            "bin_low": int(b * 256 / N_BINS),
            "bin_high": int((b + 1) * 256 / N_BINS) - 1,
            "coefficient": float(beta[i]),
            "baseline_mean_density": float(baseline[i]),
            "mean_abs_shap": float(mean_abs_phi[i]),
            "mean_signed_shap": float(mean_phi[i]),
        })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(rows)} features)")

    # Channel-level aggregate, and the dark/bright half split -- the quantity
    # Finding 1 predicts should dominate if the model is using overall
    # brightness as its shortcut.
    for c, name in enumerate(channels):
        sl = slice(c * N_BINS, (c + 1) * N_BINS)
        print(f"  {name}: sum|SHAP|={mean_abs_phi[sl].sum():.4f}  "
              f"signed={mean_phi[sl].sum():+.4f}")
    dark = np.concatenate([mean_phi[c * N_BINS:c * N_BINS + N_BINS // 2] for c in range(3)])
    bright = np.concatenate([mean_phi[c * N_BINS + N_BINS // 2:(c + 1) * N_BINS] for c in range(3)])
    print(f"  signed SHAP, dark bins (0-127):   {dark.sum():+.4f}")
    print(f"  signed SHAP, bright bins (128-255): {bright.sum():+.4f}")
    print("  (positive pushes toward the counterfeit class)")
    top = sorted(rows, key=lambda r: -r["mean_abs_shap"])[:10]
    print("  top-10 features by mean |SHAP|:")
    for r in top:
        print(f"    {r['channel']} bin {r['bin']:2d} [{r['bin_low']:3d}-{r['bin_high']:3d}]  "
              f"beta={r['coefficient']:+.3f}  mean|phi|={r['mean_abs_shap']:.4f}  "
              f"signed={r['mean_signed_shap']:+.4f}")


if __name__ == "__main__":
    main()
