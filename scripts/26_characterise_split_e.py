"""
Step 26 — Acquisition audit of Split E.

This paper's primary contribution is a pre-training provenance audit, and the
rule it argues for is that a dataset earns its place by surviving that audit,
not by being new. Split E is a new source, so it gets the same treatment as
Split D did in step 20, on the same measured axes: brightness, short-side
resolution, and file size.

Two questions.

  (1) Where does Split E sit on the acquisition axis this paper identifies as
      confounded? The training pool is bright and small (brightness 0.668,
      median short side 225 px); Split C is dark and large (0.162, 2448 px);
      Split D sits between them (0.389, 2419 px). If Split E lands somewhere
      distinguishable, it is a third point on that axis. If it lands on top of
      one of the existing sets, it adds no new distribution.

  (2) Is Split E's own class structure confounded? Split E as built is
      falsified-only, so there is no *within-set* class-acquisition confound to
      find and this question is trivially answered. The reason it is asked
      anyway is that it is not trivially answered for the manifest Split E was
      built from: there, the authentic-labelled images are flat vector carton
      artwork and the falsified ones are field photographs, which is the same
      deterministic class-acquisition confound the case-study dataset carries.
      This script measures that gap on the full 57-candidate manifest so the
      claim is a number rather than an assertion, and so the reason the
      eligibility screen threw the authentic class away is on the record.

Writes data/metadata/split_e_stats.csv (per image, all 57 candidates, with the
eligibility decision carried alongside) and prints the comparison.
"""
import csv
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_LOGS = [ROOT / "data" / "metadata" / "split_e_download_log.csv",
                 ROOT / "data" / "metadata" / "split_e_harvest_download_log.csv"]
REVIEWS = [ROOT / "data" / "metadata" / "split_e_eligibility_review.csv",
           ROOT / "data" / "metadata" / "split_e_harvest_eligibility_review.csv"]
PROVENANCE = ROOT / "data" / "metadata" / "split_e_candidate_provenance.csv"
CAPTURE_STATS = ROOT / "data" / "metadata" / "capture_method_stats.csv"
SPLIT_D_STATS = ROOT / "data" / "metadata" / "split_d_stats.csv"
OUT = ROOT / "data" / "metadata" / "split_e_stats.csv"

FIELDNAMES = ["image_id", "manifest_label", "decision", "exclusion_code",
              "in_split_e", "source_organization", "width", "height",
              "min_side", "file_size_bytes", "brightness"]


def image_stats(path):
    """Identical definition to 20_characterise_split_d.py: mean of the RGB
    channels of a 64x64 resize, in [0, 1]. Kept byte-for-byte comparable so the
    numbers can sit in one table."""
    with Image.open(path) as im:
        w, h = im.size
        arr = np.asarray(im.convert("RGB").resize((64, 64)), dtype=np.float32) / 255.0
    return {"width": w, "height": h, "min_side": min(w, h),
            "file_size_bytes": path.stat().st_size,
            "brightness": float(arr.mean())}


def load_csv(path, key=None):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {r[key]: r for r in rows} if key else rows


def summarise(label, rows):
    if not rows:
        return
    br = [r["brightness"] for r in rows]
    ms = [r["min_side"] for r in rows]
    fs = [r["file_size_bytes"] for r in rows]
    print(f"  {label:<34} n={len(rows):<4} brightness {np.mean(br):.3f}   "
          f"median short side {int(np.median(ms)):>4} px   "
          f"mean size {np.mean(fs) / 1000:>5.0f} kB")


def main():
    review = {}
    for path in REVIEWS:
        review.update(load_csv(path, key="image_id"))
    log = {}
    for path in DOWNLOAD_LOGS:
        key = "candidate_id" if "harvest" in path.name else "image_id"
        for iid, r in load_csv(path, key=key).items():
            if r.get("stored_relpath") and r.get("status", "kept") != "dropped":
                log[iid] = {"stored_relpath": r["stored_relpath"],
                            "manifest_label": r.get("manifest_label", "FALSIFIED"),
                            "source_organization": r["source_organization"]}
    in_split_e = {r["image_id"].removeprefix("split_e_")
                  for r in load_csv(PROVENANCE)}

    rows = []
    for iid, entry in sorted(log.items()):
        if not entry["stored_relpath"]:
            continue
        path = ROOT / "data" / "raw" / entry["stored_relpath"]
        st = image_stats(path)
        st.update({
            "image_id": iid,
            "manifest_label": entry["manifest_label"],
            "decision": review[iid]["decision"],
            "exclusion_code": review[iid]["exclusion_code"],
            "in_split_e": str(iid in in_split_e),
            "source_organization": entry["source_organization"],
        })
        rows.append(st)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    print("=== (1) Where Split E sits on the confounded acquisition axis ===")
    summarise("Split E (regulatory alerts)",
              [r for r in rows if r["in_split_e"] == "True"])

    existing = load_csv(CAPTURE_STATS)
    for pool, label in (("kaggle_modeling_pool", "Kaggle pool (train source)"),
                        ("split_c_external", "Split C (huawei cn)")):
        sub = [{"brightness": float(r["brightness"]),
                "min_side": float(r["min_side"]),
                "file_size_bytes": float(r["file_size_bytes"])}
               for r in existing if r["pool"] == pool]
        summarise(label, sub)
    if SPLIT_D_STATS.exists():
        summarise("Split D (iphone 11 pro)",
                  [{"brightness": float(r["brightness"]),
                    "min_side": float(r["min_side"]),
                    "file_size_bytes": float(r["file_size_bytes"])}
                   for r in load_csv(SPLIT_D_STATS)])

    print("\n=== (2) Class-conditional acquisition in the SOURCE MANIFEST ===")
    print("  (all 57 candidates, before the eligibility screen)")
    fal = [r for r in rows if r["manifest_label"] == "FALSIFIED"]
    aut = [r for r in rows if r["manifest_label"] == "AUTHENTIC"]
    summarise("manifest FALSIFIED", fal)
    summarise("manifest AUTHENTIC", aut)
    if fal and aut:
        gap = np.mean([r["brightness"] for r in aut]) - np.mean([r["brightness"] for r in fal])
        print(f"\n  brightness gap (authentic - falsified): {gap:+.3f}")
        art = [r for r in aut if r["exclusion_code"] == "X_NOT_PHOTOGRAPH"]
        print(f"  authentic-labelled images that are flat carton artwork rather "
              f"than photographs: {len(art)}/{len(aut)}")
        print("\n  This is a deterministic class-acquisition confound of the same")
        print("  species Section VI documents in the case-study dataset: the class")
        print("  label is recoverable from how the image was produced, without")
        print("  reference to the product. It is why the eligibility screen")
        print("  discards the authentic class rather than correcting it, and why")
        print("  Split E is reported as a falsified-only recall set.")


if __name__ == "__main__":
    main()
