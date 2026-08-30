"""
Metadata-only oracle: how much of the reported accuracy on the Kaggle pool is
available to a classifier that never looks at a pixel's spatial arrangement?

Two feature families are reported separately, because they cost different
things to obtain. Header metadata -- container format, encoded file size, pixel
dimensions and the aspect ratio derived from them -- is readable from a file
listing and a header parse, with no pixel decoding at all. Mean brightness is a
low-level acquisition proxy and does require decoding the image, so it is
reported apart from the metadata-only rows rather than inside them.

This bounds the confound-attributable accuracy directly, rather than inferring
it from M1's 96-dimensional colour histogram (which does see pixel intensities).
A deterministic file-extension rule is reported alongside it as the exact
ceiling.

Writes paper/tables/table_metadata_oracle.csv.
"""

import csv
import json
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATS = os.path.join(ROOT, "data", "metadata", "capture_method_stats.csv")
OUT = os.path.join(ROOT, "paper", "tables", "table_metadata_oracle.csv")
SEED = 42

# Feature sets. Values are column names in capture_method_stats.csv; the
# transform column says how each is fed to the model.
FEATURE_SETS = [
    ("format", ["is_png"]),
    ("encoded file size", ["file_size_bytes"]),
    ("short-side resolution", ["min_side"]),
    ("aspect ratio", ["aspect"]),
    ("header metadata, all four", ["is_png", "file_size_bytes", "min_side",
                                   "aspect"]),
    ("header metadata minus format", ["file_size_bytes", "min_side", "aspect"]),
    ("mean brightness (pixel-derived)", ["brightness"]),
    ("header metadata minus format, plus brightness",
     ["file_size_bytes", "min_side", "aspect", "brightness"]),
]


def load():
    rows = list(csv.DictReader(open(STATS, newline="", encoding="utf-8")))
    by_id = {}
    for r in rows:
        by_id[r["image_id"]] = {
            "y": 1 if r["class_label"] == "counterfeit" else 0,
            "pool": r["pool"],
            "pattern": r["capture_pattern"],
            "brightness": float(r["brightness"]),
            # log-scaled: both span orders of magnitude across the two pipelines
            "min_side": np.log10(float(r["min_side"])),
            "file_size_bytes": np.log10(float(r["file_size_bytes"])),
            "aspect": float(r["width"]) / float(r["height"]),
            "is_png": 1.0 if r["capture_pattern"].endswith(".png") else 0.0,
        }
    return by_id


def load_split(name):
    path = os.path.join(ROOT, "splits", f"split_{name}.csv")
    out = {}
    for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
        out.setdefault(r["split"], []).append(r["image_id"])
    return out


def matrix(by_id, ids, cols):
    X = np.array([[by_id[i][c] for c in cols] for i in ids], dtype=float)
    y = np.array([by_id[i]["y"] for i in ids], dtype=int)
    return X, y


def wilson(k, n, z=1.959963985):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    by_id = load()
    results = []

    # ---- the deterministic ceiling: capture pattern alone ----------------
    pool = [i for i, r in by_id.items() if r["pool"] == "kaggle_modeling_pool"]
    rule_correct = sum(
        1
        for i in pool
        if (by_id[i]["pattern"].endswith(".png")) == (by_id[i]["y"] == 1)
    )
    lo, hi = wilson(rule_correct, len(pool))
    results.append(
        {
            "model": "capture pattern (file extension), deterministic rule",
            "split": "whole pool",
            "n": len(pool),
            "accuracy": rule_correct / len(pool),
            "ci_lo": lo,
            "ci_hi": hi,
        }
    )

    # ---- learned metadata-only classifiers ------------------------------
    for split_name in ("a", "b"):
        sp = load_split(split_name)
        for label, cols in FEATURE_SETS:
            Xtr, ytr = matrix(by_id, sp["train"], cols)
            Xte, yte = matrix(by_id, sp["test"], cols)
            clf = make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=2000, class_weight="balanced", random_state=SEED
                ),
            )
            clf.fit(Xtr, ytr)
            pred = clf.predict(Xte)
            k = int((pred == yte).sum())
            lo, hi = wilson(k, len(yte))
            results.append(
                {
                    "model": f"metadata LR ({label}, {len(cols)} feature"
                    f"{'s' if len(cols) > 1 else ''})",
                    "split": f"Split {split_name.upper()} test",
                    "n": len(yte),
                    "accuracy": k / len(yte),
                    "ci_lo": lo,
                    "ci_hi": hi,
                }
            )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["model", "split", "n", "accuracy", "ci_lo", "ci_hi"]
        )
        w.writeheader()
        for r in results:
            w.writerow(r)

    for r in results:
        print(
            f"{r['model']:<58} {r['split']:<14} n={r['n']:<4} "
            f"acc={r['accuracy']:.3f} [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]"
        )
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
