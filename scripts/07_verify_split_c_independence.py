"""
Step 7 — Verify the Mendeley Split C candidate is genuinely independent of
the existing Roboflow/Kaggle pool, using the SAME rotation-aware pHash
method as 03_dedup.py. This is not optional: the whole reason Split C
exists is to test generalization to a truly held-out source, and the data
audit already found that two superficially "independent" sources (Roboflow,
Kaggle) turned out to share 44% of their images. A new candidate source
gets the same scrutiny before being trusted.

Method: compute each Mendeley image's rotation-canonical pHash (min hash
over 0/90/180/270 degree rotations, identical to 03_dedup.py), then find its
nearest neighbor (minimum Hamming distance) against every image already in
data/metadata/dedup_clusters.csv (the full deduplicated Roboflow+Kaggle
pool). Any match at or below HAMMING_THRESHOLD=8 is flagged as a likely
duplicate/near-duplicate and excluded from the Split C pool.

Output:
  data/metadata/split_c_independence_report.txt
  data/metadata/split_c_candidate_provenance.csv (only images that passed
    the independence check)
"""
import csv
from pathlib import Path

import numpy as np
from PIL import Image
import imagehash

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
EXISTING_DEDUP = ROOT / "data" / "metadata" / "dedup_clusters.csv"
CANDIDATE_DIR = RAW / "mendeley_split_c"
REPORT_OUT = ROOT / "data" / "metadata" / "split_c_independence_report.txt"
PROVENANCE_OUT = ROOT / "data" / "metadata" / "split_c_candidate_provenance.csv"

HAMMING_THRESHOLD = 8  # same threshold as 03_dedup.py


def rotation_canonical_hash(path: Path) -> int:
    with Image.open(path) as im:
        im = im.convert("RGB")
        best = None
        for angle in (0, 90, 180, 270):
            rotated = im.rotate(angle, expand=True)
            h = imagehash.phash(rotated)
            hint = int(str(h), 16)
            if best is None or hint < best:
                best = hint
        return best


def main():
    print("Loading existing pool hashes...")
    with open(EXISTING_DEDUP, newline="", encoding="utf-8") as f:
        existing_rows = list(csv.DictReader(f))
    existing_hashes = np.array([int(r["phash_canonical_hex"], 16) for r in existing_rows], dtype=np.uint64)
    existing_paths = [r["orig_relpath"] for r in existing_rows]

    candidate_paths = sorted(CANDIDATE_DIR.glob("*.jpg"))
    print(f"Hashing {len(candidate_paths)} Split C candidate images...")

    results = []
    for i, path in enumerate(candidate_paths):
        h = np.uint64(rotation_canonical_hash(path))
        dist = np.bitwise_count(np.bitwise_xor(existing_hashes, h))
        min_idx = int(np.argmin(dist))
        min_dist = int(dist[min_idx])
        results.append({
            "candidate_file": path.name,
            "min_hamming_distance": min_dist,
            "nearest_existing_match": existing_paths[min_idx],
            "flagged_duplicate": min_dist <= HAMMING_THRESHOLD,
        })
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(candidate_paths)}")

    n_flagged = sum(1 for r in results if r["flagged_duplicate"])
    dists = [r["min_hamming_distance"] for r in results]

    report = [
        "Split C independence check (Mendeley 'Mobile-Captured Pharmaceutical",
        "Medication Packages', huawei-cn subset, 150 images) vs. existing",
        f"Roboflow+Kaggle dedup pool ({len(existing_rows)} images)",
        "",
        f"Hamming threshold (same as main dedup pass): {HAMMING_THRESHOLD}/64 bits",
        f"Candidate images flagged as likely duplicates: {n_flagged}/{len(results)}",
        f"Nearest-neighbor distance distribution: min={min(dists)}, "
        f"median={int(np.median(dists))}, max={max(dists)}",
        "",
    ]
    if n_flagged:
        report.append("Flagged images:")
        for r in results:
            if r["flagged_duplicate"]:
                report.append(f"  {r['candidate_file']} (dist={r['min_hamming_distance']}) "
                              f"~= {r['nearest_existing_match']}")
    else:
        report.append("No candidate image matched any existing pool image within threshold.")
        report.append("VERDICT: independent source, confirmed programmatically (not just by")
        report.append("description) -- safe to use as Split C / external generalization pool.")

    report_text = "\n".join(report)
    REPORT_OUT.write_text(report_text, encoding="utf-8")
    print(report_text)

    # write provenance for images that passed
    passed = [r for r in results if not r["flagged_duplicate"]]
    with open(PROVENANCE_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "source_dataset", "orig_relpath", "class_label", "min_hamming_distance_to_existing_pool"])
        for i, r in enumerate(passed):
            w.writerow([f"mendeley_split_c_{i:05d}", "Mendeley - Mobile-Captured Pharmaceutical Medication Packages",
                        f"mendeley_split_c/{r['candidate_file']}", "authentic", r["min_hamming_distance"]])
    print(f"\nWrote {REPORT_OUT}")
    print(f"Wrote {PROVENANCE_OUT} ({len(passed)} images)")


if __name__ == "__main__":
    main()
