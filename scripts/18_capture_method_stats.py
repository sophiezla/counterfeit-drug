"""
Per-image capture-method statistics for the Kaggle modelling pool and the
external Mendeley Split C set.

This turns the ad-hoc PIL+numpy comparison described at the end of
`data/metadata/capture_method_confound_findings.md` ("worth turning into a
proper script ... not yet done as of this writing") into a committed,
reproducible artifact, so the manuscript's confound figures are built from
per-image data rather than from the four summary numbers quoted in that
document.

Definitions match the original ad-hoc analysis:
  brightness  mean RGB value over the image after resizing to 64x64, on a
              0-1 scale (resize first so the statistic is not dominated by
              the ~10x resolution difference between sources)
  resolution  min(width, height) of the file as stored, plus width/height
  file_size   bytes on disk (a proxy for compression/detail level)
  capture_pattern  'images*.jpg' vs 'Screenshot*.png' for the Kaggle pool
                   (Finding 1's two capture pipelines), 'external_photo'
                   for Mendeley

Output: data/metadata/capture_method_stats.csv (one row per image)
"""
import csv
import re
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
META = ROOT / "data" / "metadata"
SPLITS = ROOT / "splits"
OUT = META / "capture_method_stats.csv"

THUMB = 64


def brightness(path: Path) -> float:
    with Image.open(path) as im:
        im = im.convert("RGB").resize((THUMB, THUMB))
        arr = np.asarray(im).astype(np.float32) / 255.0
    return float(arr.mean())


def channel_means(path: Path):
    with Image.open(path) as im:
        im = im.convert("RGB").resize((THUMB, THUMB))
        arr = np.asarray(im).astype(np.float32) / 255.0
    return [float(arr[:, :, c].mean()) for c in range(3)]


def capture_pattern(relpath: str) -> str:
    name = Path(relpath).name
    if re.match(r"(?i)^screenshot", name):
        return "Screenshot*.png"
    if re.match(r"(?i)^images\d", name):
        return "images*.jpg"
    return "other"


def main():
    # The modelling pool: Kaggle rows that Split A actually uses.
    with open(SPLITS / "split_a.csv", newline="", encoding="utf-8") as f:
        pool_ids = {r["image_id"] for r in csv.DictReader(f)}
    with open(META / "provenance.csv", newline="", encoding="utf-8") as f:
        prov = [r for r in csv.DictReader(f) if r["image_id"] in pool_ids]

    rows = []
    for r in prov:
        p = RAW / r["orig_relpath"]
        with Image.open(p) as im:
            w, h = im.size
        rmeans = channel_means(p)
        rows.append({
            "image_id": r["image_id"],
            "pool": "kaggle_modeling_pool",
            "class_label": r["class_label"],
            "capture_pattern": capture_pattern(r["orig_relpath"]),
            "modality": r["modality"],
            "width": w, "height": h, "min_side": min(w, h),
            "file_size_bytes": p.stat().st_size,
            "brightness": brightness(p),
            "mean_r": rmeans[0], "mean_g": rmeans[1], "mean_b": rmeans[2],
        })

    # External Split C (real authentic photographs).
    with open(META / "split_c_candidate_provenance.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = RAW / r["orig_relpath"]
            with Image.open(p) as im:
                w, h = im.size
            rmeans = channel_means(p)
            rows.append({
                "image_id": r["image_id"], "pool": "split_c_external",
                "class_label": r["class_label"], "capture_pattern": "external_photo",
                "modality": "", "width": w, "height": h, "min_side": min(w, h),
                "file_size_bytes": p.stat().st_size, "brightness": brightness(p),
                "mean_r": rmeans[0], "mean_g": rmeans[1], "mean_b": rmeans[2],
            })

    # Synthetic counterfeit proxy (Split C stress-test negatives only).
    with open(META / "split_c_synthetic_provenance.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["data_origin"] == "real_authentic":
                continue
            p = RAW / r["orig_relpath"]
            with Image.open(p) as im:
                w, h = im.size
            rmeans = channel_means(p)
            rows.append({
                "image_id": r["image_id"] + "__synth", "pool": "split_c_synthetic",
                "class_label": r["class_label"], "capture_pattern": "synthetic_perturbed",
                "modality": "", "width": w, "height": h, "min_side": min(w, h),
                "file_size_bytes": p.stat().st_size, "brightness": brightness(p),
                "mean_r": rmeans[0], "mean_g": rmeans[1], "mean_b": rmeans[2],
            })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} rows)")

    # Print the same summary Finding 1 / Finding 2 report, for cross-checking.
    import statistics as st
    def summarise(sel, name):
        if not sel:
            return
        print(f"  {name:26s} n={len(sel):4d}  "
              f"brightness={st.mean(x['brightness'] for x in sel):.3f}  "
              f"median min_side={st.median(x['min_side'] for x in sel):.0f}  "
              f"mean bytes={st.mean(x['file_size_bytes'] for x in sel):,.0f}")
    k = [r for r in rows if r["pool"] == "kaggle_modeling_pool"]
    summarise([r for r in k if r["class_label"] == "authentic"], "Kaggle authentic")
    summarise([r for r in k if r["class_label"] == "counterfeit"], "Kaggle counterfeit")
    summarise([r for r in k if r["capture_pattern"] == "images*.jpg"], "Kaggle images*.jpg")
    summarise([r for r in k if r["capture_pattern"] == "Screenshot*.png"], "Kaggle Screenshot*.png")
    summarise([r for r in rows if r["pool"] == "split_c_external"], "Split C external")
    summarise([r for r in rows if r["pool"] == "split_c_synthetic"], "Split C synthetic")

    # Cross-tab: capture pattern vs class label (Finding 1's 100% claim).
    from collections import Counter
    ct = Counter((r["capture_pattern"], r["class_label"]) for r in k)
    print("  capture_pattern x class_label:", dict(ct))


if __name__ == "__main__":
    main()
