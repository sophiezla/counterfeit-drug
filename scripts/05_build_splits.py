"""
Step 5 — Build Split A (naive) and Split B (product-level, leakage-free).

Scope decision (documented in data/README.md "Modeling pool decision"):
Only the Kaggle "Fake vs Real Medicine" pool is used for Splits A/B. The
Roboflow source is EXCLUDED from the main modeling pool because after
filtering it contributes only 2 usable counterfeit images (vs. 2695
authentic) — merging it in would (a) make class imbalance ~12x worse than
Kaggle alone, (b) conflate "how much does leakage explain" with "did we
change the underlying data", which is exactly the confound the primary
research question needs to avoid.
Using the *same* Kaggle pool, split properly, is what makes Split A vs
Split B a clean, direct, before/after leakage comparison. Roboflow's 2695
deduplicated clean authentic photos are written out separately as a
supplementary pool (data/processed/roboflow_supplementary_authentic_pool.csv)
for optional future use (e.g. robustness checks), not used by default.

Split A — naive (replicates the protocol in general use):
  Random 70:15:15 IMAGE-level split, no product grouping, stratified by class.
  Fixed seed = 42.

Split B — corrected (product-level, leakage-free):
  Group all images by product_identity (from perceptual-hash clustering).
  Split at the GROUP level, ~70:15:15, stratified by class-majority label
  per group, so no product/near-duplicate photo-session appears in more than
  one of train/val/test.
  The train partition is additionally assigned 5 stratified group-aware CV
  folds (StratifiedGroupKFold) per the plan's Part 4.1 (report mean +/- std
  across folds, not a single number).
  Fixed seed = 42.

A leakage sanity check is run and asserted for Split B: zero product_identity
overlap between train/val/test.

Outputs:
  splits/split_a.csv          (image_id, split in {train,val,test})
  splits/split_b.csv          (image_id, split in {train,val,test}, cv_fold if train)
  splits/split_report.txt     (counts, class balance, leakage check results)
"""
import csv
from pathlib import Path
from collections import defaultdict, Counter
import random

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parent.parent
PROV = ROOT / "data" / "metadata" / "provenance.csv"
SPLITS_DIR = ROOT / "splits"
SPLITS_DIR.mkdir(exist_ok=True)

SEED = 42
RATIOS = (0.70, 0.15, 0.15)  # train, val, test


def load_kaggle_pool():
    with open(PROV, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["source_dataset"] == "Kaggle - Fake vs Real Medicine"]
    return rows


def write_supplementary_roboflow_pool():
    with open(PROV, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["source_dataset"] != "Kaggle - Fake vs Real Medicine"]
    out = ROOT / "data" / "processed" / "roboflow_supplementary_authentic_pool.csv"
    out.parent.mkdir(exist_ok=True, parents=True)
    if rows:
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return len(rows), out


def build_split_a(rows, report):
    rng = random.Random(SEED)
    by_class = defaultdict(list)
    for r in rows:
        by_class[r["class_label"]].append(r["image_id"])

    assignment = {}
    for label, ids in by_class.items():
        ids = ids[:]
        rng.shuffle(ids)
        n = len(ids)
        n_train = round(n * RATIOS[0])
        n_val = round(n * RATIOS[1])
        train_ids = ids[:n_train]
        val_ids = ids[n_train:n_train + n_val]
        test_ids = ids[n_train + n_val:]
        for i in train_ids:
            assignment[i] = "train"
        for i in val_ids:
            assignment[i] = "val"
        for i in test_ids:
            assignment[i] = "test"

    out = SPLITS_DIR / "split_a.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "split"])
        for image_id, split in assignment.items():
            writer.writerow([image_id, split])

    report.append("=== Split A (naive, image-level, seed=42) ===")
    counts = Counter(assignment.values())
    report.append(f"  train={counts['train']} val={counts['val']} test={counts['test']}")
    for split_name in ("train", "val", "test"):
        ids_in_split = {i for i, s in assignment.items() if s == split_name}
        labels = [r["class_label"] for r in rows if r["image_id"] in ids_in_split]
        report.append(f"  {split_name} class balance: {dict(Counter(labels))}")
    return assignment


def build_split_b(rows, report):
    groups = defaultdict(list)
    for r in rows:
        groups[r["product_identity"]].append(r)

    group_ids = sorted(groups.keys())
    # majority class label per group (product_identity groups are same-class in this
    # pool per the dedup script's mixed-label check, so this is really just "the" label)
    group_label = {}
    for gid in group_ids:
        labels = [r["class_label"] for r in groups[gid]]
        group_label[gid] = Counter(labels).most_common(1)[0][0]

    rng = random.Random(SEED)
    by_class_groups = defaultdict(list)
    for gid in group_ids:
        by_class_groups[group_label[gid]].append(gid)

    group_assignment = {}
    for label, gids in by_class_groups.items():
        gids = gids[:]
        rng.shuffle(gids)
        n = len(gids)
        n_train = round(n * RATIOS[0])
        n_val = round(n * RATIOS[1])
        for gid in gids[:n_train]:
            group_assignment[gid] = "train"
        for gid in gids[n_train:n_train + n_val]:
            group_assignment[gid] = "val"
        for gid in gids[n_train + n_val:]:
            group_assignment[gid] = "test"

    image_assignment = {}
    for gid, members in groups.items():
        for r in members:
            image_assignment[r["image_id"]] = group_assignment[gid]

    # 5-fold stratified group CV on the train partition only
    train_rows = [r for r in rows if image_assignment[r["image_id"]] == "train"]
    X = np.zeros(len(train_rows))
    y = np.array([r["class_label"] for r in train_rows])
    g = np.array([r["product_identity"] for r in train_rows])
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    fold_of_image = {}
    for fold_idx, (_, val_idx) in enumerate(sgkf.split(X, y, g)):
        for i in val_idx:
            fold_of_image[train_rows[i]["image_id"]] = fold_idx

    out = SPLITS_DIR / "split_b.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "product_identity", "split", "cv_fold"])
        for r in rows:
            iid = r["image_id"]
            writer.writerow([iid, r["product_identity"], image_assignment[iid],
                              fold_of_image.get(iid, "")])

    report.append("=== Split B (product-level grouped, seed=42) ===")
    counts = Counter(image_assignment.values())
    report.append(f"  images: train={counts['train']} val={counts['val']} test={counts['test']}")
    gcounts = Counter(group_assignment.values())
    report.append(f"  product_identity groups: train={gcounts['train']} val={gcounts['val']} test={gcounts['test']}")
    for split_name in ("train", "val", "test"):
        ids_in_split = {i for i, s in image_assignment.items() if s == split_name}
        labels = [r["class_label"] for r in rows if r["image_id"] in ids_in_split]
        report.append(f"  {split_name} class balance: {dict(Counter(labels))}")

    fold_counts = Counter(fold_of_image.values())
    report.append(f"  CV fold sizes (train partition only): {dict(sorted(fold_counts.items()))}")

    # --- leakage sanity check ---
    train_groups = {gid for gid, s in group_assignment.items() if s == "train"}
    val_groups = {gid for gid, s in group_assignment.items() if s == "val"}
    test_groups = {gid for gid, s in group_assignment.items() if s == "test"}
    overlap_tv = train_groups & val_groups
    overlap_tt = train_groups & test_groups
    overlap_vt = val_groups & test_groups
    report.append(f"  LEAKAGE CHECK: train&val group overlap={len(overlap_tv)}, "
                  f"train&test group overlap={len(overlap_tt)}, val&test group overlap={len(overlap_vt)}")
    assert not overlap_tv and not overlap_tt and not overlap_vt, "LEAKAGE DETECTED IN SPLIT B"
    report.append("  PASS: zero product_identity overlap across train/val/test.")

    return image_assignment


def compare_a_vs_b(rows, split_a, split_b, report):
    # How many images changed which "bucket" they'd be in between A and B —
    # illustrative of how much naive splitting scrambles product grouping.
    disagree = sum(1 for r in rows if split_a.get(r["image_id"]) != split_b.get(r["image_id"]))
    report.append("=== Split A vs Split B assignment disagreement ===")
    report.append(f"  {disagree}/{len(rows)} images assigned to a different partition under A vs B "
                  f"({disagree/len(rows)*100:.1f}%)")

    # Under split A, how many product_identity groups get split across partitions?
    group_to_a_splits = defaultdict(set)
    for r in rows:
        group_to_a_splits[r["product_identity"]].add(split_a[r["image_id"]])
    leaky_groups_in_a = sum(1 for splits in group_to_a_splits.values() if len(splits) > 1)
    report.append(f"  Under naive Split A, {leaky_groups_in_a}/{len(group_to_a_splits)} product_identity "
                  f"groups have members in more than one partition (this IS the leakage Split B eliminates).")


def main():
    rows = load_kaggle_pool()
    n_supp, supp_path = write_supplementary_roboflow_pool()

    report = [
        f"Split construction report",
        f"Modeling pool: Kaggle - Fake vs Real Medicine only ({len(rows)} images, "
        f"{len(set(r['product_identity'] for r in rows))} product_identity groups)",
        f"Roboflow supplementary pool written separately: {n_supp} images -> {supp_path.relative_to(ROOT)}",
        "",
    ]

    split_a = build_split_a(rows, report)
    report.append("")
    split_b = build_split_b(rows, report)
    report.append("")
    compare_a_vs_b(rows, split_a, split_b, report)

    report_text = "\n".join(report)
    (SPLITS_DIR / "split_report.txt").write_text(report_text, encoding="utf-8")
    print(report_text)
    print(f"\nWrote splits/split_a.csv, splits/split_b.csv, splits/split_report.txt")


if __name__ == "__main__":
    main()
