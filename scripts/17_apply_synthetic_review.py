"""
Step 17 — Apply the exported synthetic counterfeit review
(16_build_synthetic_review_tool.py + synthetic_counterfeit_review.csv) to
build the final synthetic Split C: real authentic photos (already-verified
Mendeley "Huawei CN" set, data/metadata/split_c_candidate_provenance.csv)
paired with the APPROVED synthetic counterfeit candidates only.

Rows flagged "reject" (looks like a digital artifact, not a believable
counterfeit-style photo) and "unsure" are excluded from the final set --
only "approve" rows are used, per the same "don't auto-include anything
short of a clear-cut human judgment" convention as the earlier watermark/
modality review scripts (10_apply_manual_review.py).

After assembly, runs a Finding-1-style confound check (brightness,
resolution, file size means per class) between the two classes of the new
synthetic Split C set -- the same check that originally surfaced the
capture-method confound in the main Kaggle pool -- to catch it here too if
the perturbation pipeline accidentally introduced one, rather than assume
it didn't.

Usage:
    python scripts/17_apply_synthetic_review.py
      (reads data/metadata/synthetic_counterfeit_review.csv; if not found,
      also checks the user's Downloads folder for a file matching
      synthetic_counterfeit_review*.csv, matching the workflow used for
      earlier manual review rounds in this project)

Output:
  data/metadata/split_c_synthetic_provenance.csv (real authentic + approved
    synthetic counterfeit, combined, ready for eval_split_c_synthetic.py)
"""
import csv
import glob
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
REAL_AUTHENTIC_CSV = ROOT / "data" / "metadata" / "split_c_candidate_provenance.csv"
CANDIDATE_CSV = ROOT / "data" / "metadata" / "synthetic_counterfeit_candidate_provenance.csv"
REVIEW_CSV = ROOT / "data" / "metadata" / "synthetic_counterfeit_review.csv"
OUT_CSV = ROOT / "data" / "metadata" / "split_c_synthetic_provenance.csv"
RAW = ROOT / "data" / "raw"


def find_review_csv():
    if REVIEW_CSV.exists():
        return REVIEW_CSV
    downloads = Path(os.path.expanduser("~")) / "Downloads"
    matches = sorted(glob.glob(str(downloads / "synthetic_counterfeit_review*.csv")),
                      key=os.path.getmtime, reverse=True)
    if matches:
        return Path(matches[0])
    return None


def image_stats(path):
    with Image.open(path) as im:
        w, h = im.size
        arr = np.asarray(im.convert("RGB").resize((64, 64)), dtype=np.float32) / 255.0
        brightness = arr.mean()
    size_bytes = path.stat().st_size
    return brightness, min(w, h), size_bytes


def main():
    review_path = find_review_csv()
    if review_path is None:
        print("ERROR: synthetic_counterfeit_review.csv not found in data/metadata/ or ~/Downloads/.")
        print("Open data/metadata/synthetic_review_tool.html in a browser, review the 150 candidates,")
        print("then click 'Export CSV'.")
        return
    print(f"Reading review from {review_path}")

    with open(review_path, newline="", encoding="utf-8") as f:
        review_rows = {r["image_id"]: r for r in csv.DictReader(f) if r["image_id"] != "_idx"}

    with open(CANDIDATE_CSV, newline="", encoding="utf-8") as f:
        candidates = list(csv.DictReader(f))

    approved = [c for c in candidates if review_rows.get(c["image_id"], {}).get("flag") == "approve"]
    rejected = [c for c in candidates if review_rows.get(c["image_id"], {}).get("flag") == "reject"]
    unsure = [c for c in candidates if review_rows.get(c["image_id"], {}).get("flag") == "unsure"]
    unreviewed = [c for c in candidates if c["image_id"] not in review_rows or not review_rows[c["image_id"]].get("flag")]

    print(f"Candidates: {len(candidates)} | approved: {len(approved)} | "
          f"rejected: {len(rejected)} | unsure: {len(unsure)} | unreviewed: {len(unreviewed)}")
    if unreviewed:
        print(f"WARNING: {len(unreviewed)} candidates have no review flag -- excluded from the final set "
              f"(same 'no action = no inclusion' convention as prior review rounds).")

    with open(REAL_AUTHENTIC_CSV, newline="", encoding="utf-8") as f:
        real_authentic = list(csv.DictReader(f))

    rows = []
    for r in real_authentic:
        rows.append({
            "image_id": r["image_id"],
            "orig_relpath": r["orig_relpath"],
            "class_label": "authentic",
            "data_origin": "real_authentic",
        })
    for c in approved:
        rows.append({
            "image_id": c["image_id"],
            "orig_relpath": c["orig_relpath"],
            "class_label": "counterfeit",
            "data_origin": "synthetic_counterfeit_proxy",
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image_id", "orig_relpath", "class_label", "data_origin"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT_CSV}: {len(real_authentic)} real authentic + {len(approved)} approved synthetic counterfeit "
          f"= {len(rows)} total")

    # Finding-1-style confound check between the two classes
    print("\nConfound check (brightness / min-resolution / file-size, by class):")
    for label, group in (("authentic", real_authentic), ("counterfeit", approved)):
        brightnesses, resolutions, sizes = [], [], []
        for r in group:
            b, res, sz = image_stats(RAW / r["orig_relpath"])
            brightnesses.append(b)
            resolutions.append(res)
            sizes.append(sz)
        print(f"  {label:12s} n={len(group):3d}  "
              f"mean brightness={np.mean(brightnesses):.3f}  "
              f"median min-res={int(np.median(resolutions))}  "
              f"mean file size={int(np.mean(sizes))} bytes")


if __name__ == "__main__":
    main()
