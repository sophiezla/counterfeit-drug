"""
The provenance-confound audit applied to two independently published datasets.

The point of this script is generality, not the individual numbers. It runs one
fixed, cheap procedure -- fit a classifier to acquisition metadata alone, with
no pixel content, under a leakage-free grouped split -- against both public
authentic/counterfeit pharmaceutical image datasets we could obtain. Neither
was assembled by us; they have different publishers, countries and
class-construction methods.

Statistics used (all readable without decoding an image, except brightness,
which needs one cheap decode):
    file format, encoded file size, short-side resolution, aspect ratio.
Brightness is included only where the committed per-image statistics already
provide it; the audit's value is that it works from metadata alone.

Grouping: rotation-canonical pHash clusters (data/metadata/dedup_clusters.csv),
so the publisher's own augmented copies of one photograph cannot straddle the
split. Without this the Roboflow numbers would be meaningless -- its archive
ships each image three times.

Reported metric is grouped 5-fold cross-validated balanced accuracy, because
both datasets are heavily class-imbalanced as shipped. Balanced accuracy of
0.5 means "metadata carries nothing"; 1.0 means "metadata alone determines the
label".

Writes paper/tables/table_provenance_audit.csv.
"""

import csv
import os
from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INV = os.path.join(ROOT, "data", "metadata", "inventory.csv")
CLUST = os.path.join(ROOT, "data", "metadata", "dedup_clusters.csv")
OUT = os.path.join(ROOT, "paper", "tables", "table_provenance_audit.csv")
SEED = 42

SOURCES = {
    "kaggle_fake_real_medicine": "Kaggle Fake vs Real Medicine",
    "roboflow_counterfeit_med_detection": "Roboflow Counterfeit_med_detection v4",
}

FEATURE_SETS = [
    ("file format only", ["is_png"]),
    ("encoded file size", ["log_size"]),
    ("short-side resolution", ["log_min_side"]),
    ("aspect ratio", ["aspect"]),
    ("all metadata", ["is_png", "log_size", "log_min_side", "aspect"]),
]


def load():
    groups = {}
    for r in csv.DictReader(open(CLUST, newline="", encoding="utf-8")):
        groups[(r["source"], r["orig_relpath"])] = r["product_identity"]

    rows = []
    for r in csv.DictReader(open(INV, newline="", encoding="utf-8")):
        if r["class_label"] not in ("authentic", "counterfeit"):
            continue  # 52 Roboflow rows carry both labels at once
        w, h = float(r["width"]), float(r["height"])
        size = float(r["filesize_bytes"])
        if min(w, h) <= 0 or size <= 0:
            continue
        rows.append({
            "source": r["source"],
            "y": 1 if r["class_label"] == "counterfeit" else 0,
            "group": groups.get((r["source"], r["orig_relpath"]),
                                "ungrouped_" + r["orig_relpath"]),
            "is_png": 1.0 if r["format"].upper() == "PNG" else 0.0,
            "log_size": np.log10(size),
            "log_min_side": np.log10(min(w, h)),
            "aspect": max(w, h) / min(w, h),
        })
    return rows


def audit(rows, cols):
    """Grouped 5-fold CV balanced accuracy of metadata alone."""
    X = np.array([[r[c] for c in cols] for r in rows], dtype=float)
    y = np.array([r["y"] for r in rows])
    g = np.array([r["group"] for r in rows])
    if len(set(y)) < 2:
        return float("nan")
    # A constant feature (e.g. format, when a source is single-format) carries
    # no information; report chance rather than letting the scaler divide by 0.
    if np.allclose(X.std(axis=0), 0):
        return 0.5
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    scores = []
    for tr, te in skf.split(X, y, groups=g):
        if len(set(y[tr])) < 2 or len(set(y[te])) < 2:
            continue
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=5000, class_weight="balanced",
                               random_state=SEED),
        )
        clf.fit(X[tr], y[tr])
        scores.append(balanced_accuracy_score(y[te], clf.predict(X[te])))
    return float(np.mean(scores)) if scores else float("nan")


def main():
    rows = load()
    out = []
    for src, label in SOURCES.items():
        sub = [r for r in rows if r["source"] == src]
        cnt = Counter(r["y"] for r in sub)
        ngroups = len(set(r["group"] for r in sub))
        print(f"\n=== {label} ===")
        print(f"  {len(sub)} images  ({cnt[0]} authentic / {cnt[1]} counterfeit), "
              f"{ngroups} pHash groups")
        for name, cols in FEATURE_SETS:
            ba = audit(sub, cols)
            print(f"  {name:<24} grouped 5-fold balanced acc = {ba:.3f}")
            out.append({
                "dataset": label,
                "n_images": len(sub),
                "n_authentic": cnt[0],
                "n_counterfeit": cnt[1],
                "n_groups": ngroups,
                "features": name,
                "grouped_cv_balanced_accuracy": round(ba, 4),
            })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
