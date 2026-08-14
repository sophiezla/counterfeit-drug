"""
Characterise Split D (second external set) and establish what it is and is not.

Two questions, both of which the paper must answer before using it:

  (1) How does Split D differ from Split C on the confounded acquisition axes?
      If it does not differ, it is not a second distribution and tests nothing.

  (2) Is any Split D image a near-duplicate of a Split C image or of a training
      image? Split C and Split D photograph the SAME 150 products, so a pixel
      near-duplicate would mean the two sets are interchangeable and the test is
      vacuous. Rotation-canonical pHash, the same procedure used for Split C's
      independence check, answers this at the pixel level.

Writes data/metadata/split_d_stats.csv (per image) and prints the comparison
that Section 7 reports.
"""
import csv
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SPLIT_D_DIR = ROOT / "data" / "raw" / "mendeley_split_d"
SPLIT_C_DIR = ROOT / "data" / "raw" / "mendeley_split_c"
STATS_CSV = ROOT / "data" / "metadata" / "capture_method_stats.csv"
OUT = ROOT / "data" / "metadata" / "split_d_stats.csv"
NEAR_DUP_THRESHOLD = 8   # same threshold as the Split C independence check


def rotation_canonical_hash(path):
    with Image.open(path) as im:
        im = im.convert("RGB")
        vals = []
        for angle in (0, 90, 180, 270):
            vals.append(int(str(imagehash.phash(im.rotate(angle, expand=True))), 16))
    return min(vals)


def image_stats(path):
    with Image.open(path) as im:
        w, h = im.size
        small = im.convert("RGB").resize((64, 64))
        arr = np.asarray(small, dtype=np.float32) / 255.0
    return {
        "width": w, "height": h, "min_side": min(w, h),
        "file_size_bytes": path.stat().st_size,
        "brightness": float(arr.mean()),
    }


def main():
    d_paths = sorted(p for p in SPLIT_D_DIR.iterdir()
                     if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    c_paths = sorted(p for p in SPLIT_C_DIR.iterdir()
                     if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    print(f"Split D: {len(d_paths)} images    Split C: {len(c_paths)} images")

    rows = []
    for p in d_paths:
        st = image_stats(p)
        st["filename"] = p.name
        rows.append(st)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["filename", "width", "height",
                                           "min_side", "file_size_bytes",
                                           "brightness"])
        w.writeheader()
        w.writerows(rows)

    def summarise(label, br, ms, fs):
        print(f"  {label:<28} brightness {np.mean(br):.3f}   "
              f"median short side {int(np.median(ms))} px   "
              f"mean size {np.mean(fs) / 1000:.0f} kB")

    print("\n=== (1) Acquisition statistics ===")
    summarise("Split D (iphone 11 pro)",
              [r["brightness"] for r in rows],
              [r["min_side"] for r in rows],
              [r["file_size_bytes"] for r in rows])

    existing = list(csv.DictReader(open(STATS_CSV, newline="", encoding="utf-8")))
    for pool, label in (("split_c_external", "Split C (huawei cn)"),
                        ("kaggle_modeling_pool", "Kaggle pool (train source)")):
        sub = [r for r in existing if r["pool"] == pool]
        if sub:
            summarise(label,
                      [float(r["brightness"]) for r in sub],
                      [float(r["min_side"]) for r in sub],
                      [float(r["file_size_bytes"]) for r in sub])

    print("\n=== (2) Pixel-level relationship (rotation-canonical pHash) ===")
    d_hashes = {p.name: rotation_canonical_hash(p) for p in d_paths}
    c_hashes = {p.name: rotation_canonical_hash(p) for p in c_paths}

    def hamming(a, b):
        return bin(a ^ b).count("1")

    nearest = []
    for dn, dh in d_hashes.items():
        best = min(hamming(dh, ch) for ch in c_hashes.values())
        nearest.append(best)
    matches = sum(1 for x in nearest if x <= NEAR_DUP_THRESHOLD)
    print(f"  Split D vs Split C: {matches}/{len(nearest)} within Hamming "
          f"{NEAR_DUP_THRESHOLD} (near-duplicate threshold)")
    print(f"    nearest distance {min(nearest)}, median {int(np.median(nearest))}")
    print("  Interpretation: the two sets photograph the same products, so a low "
          "count here means\n  a change of camera and lighting alone makes the "
          "images not near-duplicates at the pixel level.")


if __name__ == "__main__":
    main()
