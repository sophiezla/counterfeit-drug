"""
Step 3 — Perceptual-hash deduplication and product_identity clustering.

This is the mechanism that makes the leakage-free Split B possible: we do not
have ground-truth product identity labels for either source, so we use
near-duplicate clustering as an operational proxy for "same product / same
photo session" per the rewrite plan's explicit allowance (Part 2.4):
    "same product different photo (keep, but group under same
    product_identity for split purposes) vs. true duplicate (remove one copy)"

Method:
  1. Compute a 64-bit pHash (imagehash.phash) for every retained image.
  2. Roboflow's own README states it applies 90-degree-rotation augmentation
     (none / clockwise / counter-clockwise) to create multiple versions of
     each source image. Plain pHash is NOT rotation-invariant, so a rotated
     copy of the same photo would be missed. To catch this, we hash all 4
     rotations (0/90/180/270) of every image and take the numeric minimum as
     a rotation-canonical hash. This is an approximation (canonical-min
     doesn't perfectly preserve pairwise distances) but is adequate for
     near-duplicate *clustering* at a conservative threshold, and is far
     better than ignoring rotation entirely. Documented limitation: mirrored
     (flipped) duplicates would NOT be caught (the plan also avoids flip
     augmentation for the same reason: it would mirror printed text).
  3. Pairwise Hamming distance is computed on the canonical hash, vectorized
     with numpy (all-pairs, exact — dataset is small enough at ~4.7k images).
  4. Union-Find clusters images into connected components using threshold
     HAMMING_THRESHOLD. Any image with 0 neighbors within threshold gets its
     own singleton cluster.
  5. Two thresholds are used and reported separately:
       EXACT (distance == 0): true pixel-identical duplicates -> one is kept,
         others marked is_duplicate_of.
       NEAR (0 < distance <= HAMMING_THRESHOLD): same-product/session photos
         -> all kept, but grouped into the same product_identity for split
         purposes.

Output:
  data/metadata/dedup_clusters.csv — one row per retained image with
    phash_canonical_hex, product_identity (cluster id), cluster_size,
    is_exact_duplicate, duplicate_of (orig_relpath of the kept exact copy, if any)
  data/metadata/dedup_report.txt — summary counts and threshold justification
"""
import csv
from pathlib import Path
import numpy as np
from PIL import Image
import imagehash

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
FILTERED = ROOT / "data" / "metadata" / "filtered_pool.csv"
OUT_CSV = ROOT / "data" / "metadata" / "dedup_clusters.csv"
OUT_REPORT = ROOT / "data" / "metadata" / "dedup_report.txt"

HAMMING_THRESHOLD = 8  # out of 64 bits; conservative near-duplicate cutoff for pHash


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


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def main():
    with open(FILTERED, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["excluded"] == "False"]

    print(f"Hashing {len(rows)} retained images (4 rotations each)...")
    hashes = np.zeros(len(rows), dtype=np.uint64)
    for i, r in enumerate(rows):
        path = RAW / r["orig_relpath"]
        hashes[i] = np.uint64(rotation_canonical_hash(path))
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(rows)}")

    print("Computing all-pairs Hamming distances...")
    a = hashes.reshape(-1, 1)
    b = hashes.reshape(1, -1)
    xor = np.bitwise_xor(a, b)
    dist = np.bitwise_count(xor)  # numpy>=2.0

    n = len(rows)
    uf = UnionFind(n)
    iu, ju = np.triu_indices(n, k=1)
    d_upper = dist[iu, ju]
    match_mask = d_upper <= HAMMING_THRESHOLD
    match_i = iu[match_mask]
    match_j = ju[match_mask]
    exact_mask = d_upper[match_mask] == 0

    exact_of = {}  # index -> index of first-seen exact duplicate
    seen_as_original = set()
    for i, j, is_exact in zip(match_i.tolist(), match_j.tolist(), exact_mask.tolist()):
        uf.union(i, j)
        if is_exact:
            if i not in exact_of and i not in seen_as_original:
                exact_of[j] = i
                seen_as_original.add(i)

    # Assign cluster ids (product_identity) as stable small ints ordered by first occurrence
    root_to_cluster = {}
    cluster_id_of = [None] * n
    for i in range(n):
        root = uf.find(i)
        if root not in root_to_cluster:
            root_to_cluster[root] = len(root_to_cluster)
        cluster_id_of[i] = root_to_cluster[root]

    cluster_sizes = {}
    for cid in cluster_id_of:
        cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1

    out_rows = []
    for i, r in enumerate(rows):
        cid = cluster_id_of[i]
        out_rows.append({
            "source": r["source"],
            "orig_relpath": r["orig_relpath"],
            "class_label": r["class_label"],
            "phash_canonical_hex": format(int(hashes[i]), "016x"),
            "product_identity": f"pid_{cid:05d}",
            "cluster_size": cluster_sizes[cid],
            "is_exact_duplicate": str(i in exact_of),
            "exact_duplicate_of": rows[exact_of[i]]["orig_relpath"] if i in exact_of else "",
        })

    fieldnames = list(out_rows[0].keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    n_clusters = len(root_to_cluster)
    n_exact = sum(1 for r in out_rows if r["is_exact_duplicate"] == "True")
    singleton_clusters = sum(1 for v in cluster_sizes.values() if v == 1)
    multi_clusters = n_clusters - singleton_clusters

    # cross-class cluster check: a cluster mixing authentic + counterfeit would
    # indicate a labeling inconsistency or hash collision worth investigating
    cluster_labels = {}
    for r in out_rows:
        cluster_labels.setdefault(r["product_identity"], set()).add(r["class_label"])
    mixed_label_clusters = [cid for cid, labs in cluster_labels.items() if len(labs) > 1]

    report = [
        f"pHash rotation-canonical dedup report",
        f"Retained images hashed: {n}",
        f"Hamming threshold (near-duplicate): {HAMMING_THRESHOLD} / 64 bits",
        f"Exact duplicates (distance 0) found: {n_exact}",
        f"Total product_identity clusters: {n_clusters}",
        f"  singleton clusters (no duplicate found): {singleton_clusters}",
        f"  multi-image clusters (near/exact dup groups): {multi_clusters}",
        f"Largest cluster size: {max(cluster_sizes.values())}",
        f"Clusters mixing authentic+counterfeit labels: {len(mixed_label_clusters)}"
        + (f" -> {mixed_label_clusters[:20]}" if mixed_label_clusters else ""),
        "",
        "Per-source cluster count (how many distinct product_identity groups per source):",
    ]
    by_source_clusters = {}
    for r in out_rows:
        by_source_clusters.setdefault(r["source"], set()).add(r["product_identity"])
    for src, cids in by_source_clusters.items():
        report.append(f"  {src}: {len(cids)} distinct groups from {sum(1 for r in out_rows if r['source']==src)} images")

    report_text = "\n".join(report)
    OUT_REPORT.write_text(report_text, encoding="utf-8")
    print(report_text)
    print(f"\nWrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
