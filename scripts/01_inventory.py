"""
Step 1 — Inventory raw data sources.

Walks the extracted raw data (data/raw/roboflow, data/raw/kaggle_fake_real)
and records one row per image: source, class label, split-as-shipped,
resolution, file format, file size, perceptual hash placeholder.

Roboflow source:
    - Uses train/valid/test/_classes.csv files (columns: filename, authentic, counterfeit)
    - NOTE: Roboflow's own README states it applied 3x augmentation (rotation +
      exposure jitter) per source image, so multiple rows here can share a
      pre-augmentation parent image. This is caught later at the dedup step.

Kaggle "Fake vs Real Medicine" source:
    - Canonical pool is dataset/Fake and dataset/Real ONLY.
    - dataset/train, dataset/val, dataset/test are NOT used: they are a
      pre-bundled split where val/test are subsets of train (see
      data/README.md "Known data-quality issues" for the verification).
      Re-deriving our own leakage-free split from the canonical pool is the
      whole point of this project, so the shipped split is discarded.

Output: data/metadata/inventory.csv
Columns: source, orig_relpath, class_label, shipped_split, width, height,
         format, filesize_bytes
"""
import csv
import os
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "metadata" / "inventory.csv"


def image_meta(path: Path):
    try:
        with Image.open(path) as im:
            return im.width, im.height, im.format
    except Exception as e:
        return None, None, f"ERROR:{e}"


def inventory_roboflow(rows):
    base = RAW / "roboflow"
    for split in ("train", "valid", "test"):
        split_dir = base / split
        classes_csv = split_dir / "_classes.csv"
        labels = {}
        with open(classes_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            reader.fieldnames = [h.strip() for h in reader.fieldnames]
            for row in reader:
                fname = row["filename"].strip()
                authentic = int(row["authentic"].strip())
                counterfeit = int(row["counterfeit"].strip())
                if authentic == 1 and counterfeit == 0:
                    labels[fname] = "authentic"
                elif counterfeit == 1 and authentic == 0:
                    labels[fname] = "counterfeit"
                else:
                    labels[fname] = "ambiguous"  # both/neither flagged - inspect later
        for fname, label in labels.items():
            fpath = split_dir / fname
            if not fpath.exists():
                continue
            w, h, fmt = image_meta(fpath)
            rows.append({
                "source": "roboflow_counterfeit_med_detection",
                "orig_relpath": str(fpath.relative_to(RAW)),
                "class_label": label,
                "shipped_split": split,
                "width": w, "height": h, "format": fmt,
                "filesize_bytes": fpath.stat().st_size,
            })


def inventory_kaggle(rows):
    base = RAW / "kaggle_fake_real" / "dataset"
    label_map = {"Fake": "counterfeit", "Real": "authentic"}
    for folder, label in label_map.items():
        d = base / folder
        for fpath in sorted(d.iterdir()):
            if fpath.name == "desktop.ini" or fpath.is_dir():
                continue
            w, h, fmt = image_meta(fpath)
            rows.append({
                "source": "kaggle_fake_real_medicine",
                "orig_relpath": str(fpath.relative_to(RAW)),
                "class_label": label,
                "shipped_split": "unsplit_pool",  # shipped train/val/test discarded, see docstring
                "width": w, "height": h, "format": fmt,
                "filesize_bytes": fpath.stat().st_size,
            })


def main():
    rows = []
    inventory_roboflow(rows)
    inventory_kaggle(rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["source", "orig_relpath", "class_label", "shipped_split",
                  "width", "height", "format", "filesize_bytes"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT}")
    by_source_class = {}
    for r in rows:
        key = (r["source"], r["class_label"])
        by_source_class[key] = by_source_class.get(key, 0) + 1
    for key, count in sorted(by_source_class.items()):
        print(f"  {key[0]:40s} {key[1]:12s} {count}")


if __name__ == "__main__":
    main()
