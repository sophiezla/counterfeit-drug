"""
Step 4 — Build the final provenance table (Part 2.3 of the rewrite plan).

Merges filtered_pool.csv (quality-filter decisions) with dedup_clusters.csv
(product_identity groups from perceptual-hash clustering) into one row per
*retained, de-duplicated* image.

Exact duplicates (Hamming distance 0 after rotation-canonicalization) are
DROPPED here, keeping only the first-seen copy per the plan's Part 2.4
instruction ("true duplicate -> remove one copy"). Near-duplicates
(distance 1-8, same product/photo-session) are KEPT but share a
product_identity, which is what Split B groups on.

image_id is a STABLE hash of (source, orig_relpath) -- NOT a sequential
counter. An earlier version counted rows as they were processed, which
meant every exclusion added anywhere in the pipeline silently renumbered
every image_id after it, making any image_id cited in prior documentation
(error analysis, Grad-CAM findings, etc.) point at a different file after
the next rebuild. Content-hash IDs stay stable across reruns regardless of
how many other rows are added or removed.

modality and apparent_capture_condition are PRESERVED from the previous
provenance.csv (matched by the stable image_id) if this script has run
before and a human has filled them in (scripts/12_apply_modality_tags.py) --
otherwise this step would silently wipe manual tagging work every time the
pipeline reruns for an unrelated reason (e.g. a new exclusion elsewhere).
New images (not seen in a prior run) get the placeholder default.

Output: data/metadata/provenance.csv with columns:
  image_id, source_dataset, orig_relpath, class_label, product_identity,
  cluster_size, modality, apparent_capture_condition, width, height,
  format, notes
"""
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILTERED = ROOT / "data" / "metadata" / "filtered_pool.csv"
DEDUP = ROOT / "data" / "metadata" / "dedup_clusters.csv"
OUT = ROOT / "data" / "metadata" / "provenance.csv"

SOURCE_DISPLAY = {
    "roboflow_counterfeit_med_detection": "Roboflow - Counterfeit_med_detection (v4)",
    "kaggle_fake_real_medicine": "Kaggle - Fake vs Real Medicine",
}

PLACEHOLDER = "unclassified_needs_manual_review"


def stable_image_id(source: str, relpath: str) -> str:
    h = hashlib.sha1(relpath.encode("utf-8")).hexdigest()[:10]
    return f"{source}_{h}"


def main():
    with open(FILTERED, newline="", encoding="utf-8") as f:
        filtered = {r["orig_relpath"]: r for r in csv.DictReader(f) if r["excluded"] == "False"}

    with open(DEDUP, newline="", encoding="utf-8") as f:
        dedup = {r["orig_relpath"]: r for r in csv.DictReader(f)}

    # Preserve manually-filled fields from a prior run, keyed by the stable
    # image_id (which is a hash of orig_relpath, so this survives reruns
    # even if other rows were added/removed).
    prior_by_id = {}
    if OUT.exists():
        with open(OUT, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                prior_by_id[r["image_id"]] = r

    out_rows = []
    n_dropped_exact = 0
    n_carried_forward = 0
    for relpath, f_row in filtered.items():
        d_row = dedup[relpath]
        if d_row["is_exact_duplicate"] == "True":
            n_dropped_exact += 1
            continue

        source = f_row["source"]
        image_id = stable_image_id(source, relpath)

        default_modality = ("outer_packaging_or_product_photo" if source == "roboflow_counterfeit_med_detection"
                             else PLACEHOLDER)
        modality = default_modality
        apparent_capture_condition = PLACEHOLDER
        prior = prior_by_id.get(image_id)
        if prior:
            if prior.get("modality") and prior["modality"] != PLACEHOLDER and prior["modality"] != default_modality:
                modality = prior["modality"]
                n_carried_forward += 1
            if prior.get("apparent_capture_condition") and prior["apparent_capture_condition"] != PLACEHOLDER:
                apparent_capture_condition = prior["apparent_capture_condition"]

        notes = []
        if int(d_row["cluster_size"]) > 1:
            notes.append(f"member_of_near_duplicate_cluster_size_{d_row['cluster_size']}")
        if f_row["source"] == "roboflow_counterfeit_med_detection" and f_row["class_label"] == "counterfeit":
            notes.append("rare_class_for_this_source_only_3_raw_instances_survived_filtering")

        out_rows.append({
            "image_id": image_id,
            "source_dataset": SOURCE_DISPLAY[source],
            "orig_relpath": relpath,
            "class_label": f_row["class_label"],
            "product_identity": d_row["product_identity"],
            "cluster_size": d_row["cluster_size"],
            "modality": modality,
            "apparent_capture_condition": apparent_capture_condition,
            "width": f_row["width"],
            "height": f_row["height"],
            "format": f_row["format"],
            "notes": "; ".join(notes),
        })

    fieldnames = list(out_rows[0].keys())
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Retained (filtered) images: {len(filtered)}")
    print(f"Dropped as exact duplicates: {n_dropped_exact}")
    print(f"Final provenance rows: {len(out_rows)}")
    print(f"Modality values carried forward from a prior run: {n_carried_forward}")
    from collections import Counter
    print(Counter((r["source_dataset"], r["class_label"]) for r in out_rows))
    n_groups = len(set(r["product_identity"] for r in out_rows))
    print(f"Distinct product_identity groups in final pool: {n_groups}")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
