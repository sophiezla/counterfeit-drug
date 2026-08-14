"""
Step 15 (data) — Generate the full batch of synthetic counterfeit-style
images, using the perturbation pipeline in synthetic_counterfeit.py
(approved after manual preview review — see
data/metadata/synthetic_counterfeit_findings.md for the full methodology,
preview process, and limitations).

Base images: the SAME 150 "Huawei CN" photos already serving as Split C's
real authentic class (data/metadata/split_c_candidate_provenance.csv), NOT
the separately-downloaded "iPhone 11 Pro" subset used in the first version
of this pipeline. That first version was found to have a serious flaw: the
Mendeley dataset's own "controlled lighting-variation protocol" means
different phone subsets were shot under deliberately different lighting,
so the iPhone 11 Pro base photos are ~2.4x brighter on average than the
Huawei CN base photos (0.389 vs. 0.162 mean brightness, pre-perturbation)
-- a large, systematic confound between the two classes that had nothing
to do with the perturbation pipeline, and would have let a model learn
"brighter capture session -> counterfeit" instead of anything resembling a
counterfeit-recognition cue. Using the same base photos for both classes
(one set left as-is for authentic, the same set perturbed for
counterfeit) makes the perturbation the ONLY systematic difference between
classes -- no separate capture session involved. See "Finding: base-image
lighting confound" in data/metadata/synthetic_counterfeit_findings.md.

Each base image gets exactly one synthetic counterfeit version, generated
deterministically from a seed derived from its filename (reproducible, not
re-randomized on rerun). Output images are saved as JPEG at a normal
quality (95) matching a genuine photo export -- NOT pre-degraded in file
size/resolution/format in a way that would recreate the original
capture-method confound; the project's standard 3-way normalization
(modeling/normalization.py) is applied uniformly to both classes at
training/eval time, same as everywhere else in this project, not baked in
here.

This is a PRE-REVIEW candidate pool -- the accompanying HTML review tool
(16_build_synthetic_review_tool.py) lets a human approve/reject each one
before any of them enter an actual split.

Output:
  data/raw/synthetic_counterfeit/*.jpg
  data/metadata/synthetic_counterfeit_candidate_provenance.csv
"""
import csv
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_counterfeit import generate_synthetic_counterfeit

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "data" / "raw" / "mendeley_split_c"
OUT_DIR = ROOT / "data" / "raw" / "synthetic_counterfeit"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = ROOT / "data" / "metadata" / "synthetic_counterfeit_candidate_provenance.csv"

JPEG_EXPORT_QUALITY = 95


def main():
    files = sorted(SRC_DIR.glob("*.jpg"))
    print(f"Generating synthetic counterfeit versions for {len(files)} base images...")

    rows = []
    for i, path in enumerate(files):
        seed = hash(path.stem) % 100000
        image_id = f"synthetic_counterfeit_{i:05d}"
        out_name = f"{image_id}.jpg"
        out_path = OUT_DIR / out_name

        if not out_path.exists():
            # generation is fully deterministic per (path, seed), so it's safe
            # to skip already-written files on a retry after an interrupted run
            with Image.open(path) as im:
                im = im.convert("RGB")
                synth = generate_synthetic_counterfeit(im, seed=seed, include_text_tamper=True)
            synth.save(out_path, format="JPEG", quality=JPEG_EXPORT_QUALITY)

        rows.append({
            "image_id": image_id,
            "orig_relpath": f"synthetic_counterfeit/{out_name}",
            "base_source_relpath": f"mendeley_split_c/{path.name}",
            "class_label": "counterfeit",
            "data_origin": "synthetic_counterfeit_proxy",
            "generation_seed": seed,
        })
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(files)}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Done. {len(rows)} images written to {OUT_DIR}")
    print(f"Provenance: {OUT_CSV}")


if __name__ == "__main__":
    main()
