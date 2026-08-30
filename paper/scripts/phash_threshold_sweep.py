"""
Sensitivity of the near-duplicate clustering to its Hamming threshold.

Gap this closes. Section IV-B clusters images at Hamming distance <= 8 on a
64-bit rotation-canonical perceptual hash, and Split B's leakage-freedom is
defined against those clusters. The threshold was fixed before any model ran
and never justified beyond convention, which invites the obvious question:
would a different one have changed the paper's conclusions?

Re-clustering costs nothing. The canonical hashes are already recorded in
data/metadata/dedup_clusters.csv, so no image is decoded here, and the fixed
Split A and Split B assignments can be checked against whatever groups each
threshold produces.

Three quantities are reported per threshold:

  * cluster count and largest cluster -- how coarse the grouping has become;
  * mixed-label clusters -- clusters holding both authentic and counterfeit
    images. The clustering reads no labels, so this is an external check on
    it: once the hash starts merging images the annotations call different,
    it has stopped tracking product identity;
  * clusters straddling a partition of Split A and of Split B -- the countable
    leakage each split design carries at that threshold.

Note on the count at threshold 8. Clustering the 510-image pool alone gives 482
groups where the production pipeline records 480, because production clusters
the Kaggle and Roboflow images together (Section III-C) and two Kaggle pairs
are joined through a Roboflow intermediary. Nothing here turns on it.

Output: paper/tables/table_phash_threshold_sweep.csv
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATS = os.path.join(ROOT, "data", "metadata", "capture_method_stats.csv")
PROV = os.path.join(ROOT, "data", "metadata", "provenance.csv")
DEDUP = os.path.join(ROOT, "data", "metadata", "dedup_clusters.csv")
OUT = os.path.join(ROOT, "paper", "tables", "table_phash_threshold_sweep.csv")

THRESHOLDS = [0, 2, 4, 6, 8, 10, 12, 16]
PRODUCTION = 8


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_pool():
    """The 510 modeling-pool images, with their canonical hash and label."""
    stats = {r["image_id"]: r for r in rows(STATS)}
    prov = {r["image_id"]: r for r in rows(PROV)}
    by_relpath = {r["orig_relpath"]: r for r in rows(DEDUP)}

    ids, hashes, labels = [], [], []
    for image_id, stat in stats.items():
        if stat["pool"] != "kaggle_modeling_pool":
            continue
        relpath = prov[image_id]["orig_relpath"]
        ids.append(image_id)
        hashes.append(int(by_relpath[relpath]["phash_canonical_hex"], 16))
        labels.append(stat["class_label"])
    return ids, hashes, labels


def load_split(name):
    path = os.path.join(ROOT, "splits", "split_%s.csv" % name)
    return {r["image_id"]: r["split"] for r in rows(path)}


def cluster(distances, n, threshold):
    """Union-find over pairs within `threshold`, returning member lists."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if distances[i][j] <= threshold:
                a, b = find(i), find(j)
                if a != b:
                    parent[a] = b

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def main():
    ids, hashes, labels = load_pool()
    n = len(ids)
    print("modeling pool: %d images" % n)

    split_a, split_b = load_split("a"), load_split("b")
    distances = [[bin(hashes[i] ^ hashes[j]).count("1") for j in range(n)]
                 for i in range(n)]

    out = []
    for t in THRESHOLDS:
        groups = cluster(distances, n, t)
        out.append({
            "threshold": t,
            "production": t == PRODUCTION,
            "clusters": len(groups),
            "largest_cluster": max(len(g) for g in groups),
            "mixed_label_clusters":
                sum(1 for g in groups if len({labels[i] for i in g}) > 1),
            "straddles_split_a":
                sum(1 for g in groups if len({split_a[ids[i]] for i in g}) > 1),
            "straddles_split_b":
                sum(1 for g in groups if len({split_b[ids[i]] for i in g}) > 1),
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)

    print("\nthr  clusters  largest  mixed  straddleA  straddleB")
    for r in out:
        print("%3d %9d %8d %6d %10d %10d%s" % (
            r["threshold"], r["clusters"], r["largest_cluster"],
            r["mixed_label_clusters"], r["straddles_split_a"],
            r["straddles_split_b"], "   <- production" if r["production"] else ""))
    print("\nwrote %s" % os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
