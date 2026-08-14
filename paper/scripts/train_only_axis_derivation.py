"""
Can the normalisation axes be derived WITHOUT looking at the external set?

This closes the paper's most serious self-disclosed gap. The three axes of the
correction (resolution, brightness, compression) were originally chosen after
comparing the Kaggle pool against external Split C, which is target-distribution
information a real practitioner would not have. Section 10 conceded that the
train-only version of the procedure "was not tested". This script tests it.

Protocol, and the point is what it never touches:
  * Split B TRAINING partition only (357 images, 336 product groups).
  * Grouped 5-fold CV *inside* that partition, so the ranking is estimated
    without the validation partition, the test partition, or Split C.
  * One candidate acquisition statistic at a time, ranked by how well it alone
    predicts the training label.

A practitioner runs this before training anything and normalises every axis
whose balanced accuracy clears a pre-declared threshold. If the axes it
nominates are the axes the paper actually used, the correction is derivable
without target knowledge and the leak is closed.

Writes paper/tables/table_train_only_axes.csv.
"""

import csv
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATS = os.path.join(ROOT, "data", "metadata", "capture_method_stats.csv")
SPLIT_B = os.path.join(ROOT, "splits", "split_b.csv")
OUT = os.path.join(ROOT, "paper", "tables", "table_train_only_axes.csv")
SEED = 42

# Every acquisition statistic a practitioner could compute from the training
# files alone, with the normalisation each one implies if it fires.
CANDIDATES = [
    ("file format (PNG vs JPEG)", "is_png",
     "not normalisable by preprocessing — re-encode all inputs (implies the compression axis)"),
    ("encoded file size", "log_size",
     "fixed-quality re-encode  ->  COMPRESSION axis"),
    ("short-side resolution", "log_min_side",
     "short-side cap  ->  RESOLUTION axis"),
    ("aspect ratio", "aspect",
     "already removed by the square 224x224 input resize"),
    ("mean brightness", "brightness",
     "rescale to fixed target mean  ->  BRIGHTNESS axis"),
    ("colour balance (R:G ratio)", "rg_ratio",
     "gray-world white balance"),
    ("colour balance (R:B ratio)", "rb_ratio",
     "gray-world white balance"),
]

THRESHOLD = 0.65  # declared in advance: normalise any axis above this


def load_train_rows():
    keep = {}
    for r in csv.DictReader(open(SPLIT_B, newline="", encoding="utf-8")):
        if r["split"] == "train":
            keep[r["image_id"]] = r["product_identity"]

    rows = []
    for r in csv.DictReader(open(STATS, newline="", encoding="utf-8")):
        if r["image_id"] not in keep:
            continue
        mr, mg, mb = float(r["mean_r"]), float(r["mean_g"]), float(r["mean_b"])
        rows.append({
            "y": 1 if r["class_label"] == "counterfeit" else 0,
            "group": keep[r["image_id"]],
            "is_png": 1.0 if "png" in r["capture_pattern"].lower() else 0.0,
            "log_size": np.log10(float(r["file_size_bytes"])),
            "log_min_side": np.log10(float(r["min_side"])),
            "aspect": max(float(r["width"]), float(r["height"]))
                      / min(float(r["width"]), float(r["height"])),
            "brightness": float(r["brightness"]),
            "rg_ratio": mr / mg if mg > 1e-6 else 1.0,
            "rb_ratio": mr / mb if mb > 1e-6 else 1.0,
        })
    return rows


def grouped_cv_ba(rows, col):
    X = np.array([[r[col]] for r in rows], dtype=float)
    y = np.array([r["y"] for r in rows])
    g = np.array([r["group"] for r in rows])
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    scores = []
    for tr, te in skf.split(X, y, groups=g):
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=5000, class_weight="balanced",
                               random_state=SEED),
        )
        clf.fit(X[tr], y[tr])
        scores.append(balanced_accuracy_score(y[te], clf.predict(X[te])))
    return float(np.mean(scores)), float(np.std(scores))


def main():
    rows = load_train_rows()
    print(f"Split B training partition only: {len(rows)} images, "
          f"{len({r['group'] for r in rows})} product groups")
    print(f"Pre-declared threshold: normalise any axis above "
          f"{THRESHOLD:.2f} balanced accuracy\n")

    out = []
    for label, col, implication in CANDIDATES:
        ba, sd = grouped_cv_ba(rows, col)
        fires = ba >= THRESHOLD
        out.append({"statistic": label, "grouped_cv_balanced_accuracy": round(ba, 4),
                    "sd_across_folds": round(sd, 4),
                    "fires_at_threshold": "yes" if fires else "no",
                    "implied_normalisation": implication})
        print(f"{'FIRES ' if fires else '  --  '} {label:<28} "
              f"BA = {ba:.3f} (sd {sd:.3f})   {implication}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
