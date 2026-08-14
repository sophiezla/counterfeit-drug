"""
Step 2 — Apply data-quality filters discovered during manual visual audit.

This script does NOT do full manual "outer-packaging vs blister-pack vs pill"
modality classification (Part 2.2 of the rewrite plan) — that step still
needs a human pass and is left as a queue (see data/metadata/needs_manual_review.csv).

What this script DOES remove, based on a visual audit of stratified samples
(documented in data/README.md, section "Filtering decisions"):

1. Roboflow dual-labeled rows (authentic=1 AND counterfeit=1 simultaneously)
   — 52 rows, internally contradictory annotation, unusable.

2. Roboflow "bulletin" images — filename-pattern-identified institutional
   advisory graphics (FDA Advisory bulletins, Facebook-style numeric-ID
   reposts of the same bulletins, dated comparison docs, "authentic-vs-fake"
   collages). Visual inspection of every matched pattern confirmed these are
   NOT product photographs: they are multi-panel comparison graphics with
   the ground-truth class WRITTEN AS TEXT directly in the image (e.g. the
   word "COUNTERFEIT" or "AUTHENTIC" rendered as a pixel caption), often
   with FDA logos/branding, sometimes showing both classes in one frame.
   This is a severe label-leakage-via-OCR confound, not a legitimate visual
   cue, and it is *class-correlated*: 100% of Roboflow's unique counterfeit-
   labeled images (57/57) are bulletin graphics, while its "clean" product
   photos (263/263) are all authentic-labeled. In other words the Roboflow
   source's counterfeit class and authentic class differ systematically in
   *image modality* (bulletin graphic vs. plain product photo), not just in
   product authenticity — a model trained on it would learn to distinguish
   graphic-design collages from product photos, not counterfeit packaging.
   Consequence: Roboflow contributes ZERO usable counterfeit images. Its
   263 unique clean authentic photos are retained as supplementary
   authentic-class examples only.

3. One Kaggle image (`Screenshot 2025-09-17 180529.png`, counterfeit-
   labeled) is not a medicine photo at all: it is a screenshot of a web
   browser showing the Roboflow "counterfeit_med_detection" dataset page
   itself (tabs and URL bar reading ".../harshini-t-g-r/counterfeit_...-
   Advance-Buscopan-Kremil-S-and-Loper...' visible in the crop). Found
   during the initial AI contact-sheet pass (see
   `data/metadata/modality_review_sheets/`), not by the earlier
   filename-pattern audit — this is a per-image visual find, not something
   a regex could catch. Excluded outright: it is not an image of a
   pharmaceutical product under any modality.

4. A full human review of all 563 Kaggle images (`data/metadata/
   manual_review_tool.html`, 2026-07-24 — see "Manual review workflow" in
   data/README.md) found and confirmed:
     - 36 more images with a visible watermark or stock-photo overlay
       (KAGGLE_WATERMARK_FILENAMES). Checked, not assumed: 36/36 (100%)
       are authentic-labeled — a real, class-correlated confound, same
       kind of issue as item 2 above though smaller in degree. The earlier
       AI pass had only opportunistically spotted 11 of these 36.
     - 2 more non-medicine images (KAGGLE_NON_MEDICINE_FILENAMES) — not
       literal browser screenshots like the one above, but stock/
       marketing-render images (a generic product icon, a graphic-design
       ad) rather than an organic device photo of the actual product.
     - Zero images marked "unsure" — the human reviewer resolved every
       image to a definite tag.

   NOTE: exclusions in items 3-4 were added AFTER Splits A/B/C and all 4
   models were already built and trained on data that included these
   images. The combined effect (1 + 3 + 36 = 40 images, ~7% of the
   564-image Kaggle pool) is large enough that model retraining is
   recommended once the data pipeline stabilizes — this is disclosed in
   both READMEs rather than silently left inconsistent; see
   data/README.md "Open items" for current status.

Output: data/metadata/filtered_pool.csv (superset of inventory.csv columns
plus `excluded` bool and `exclusion_reason`), and
data/metadata/needs_manual_review.csv (retained images still needing a human
outer-packaging/blister/pill modality pass).
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "metadata" / "inventory.csv"
OUT = ROOT / "data" / "metadata" / "filtered_pool.csv"
REVIEW_OUT = ROOT / "data" / "metadata" / "needs_manual_review.csv"

BULLETIN_STEM_RE = re.compile(
    r'^(fda-advisory|how-to|maxresdefault|\d{5,}_|(2019|2020|2021)-|fake-|authentic-vs-fake)',
    re.IGNORECASE,
)
ROBOFLOW_FNAME_RE = re.compile(r'(.+?)_(jpg|png|jpeg)\.rf\.', re.IGNORECASE)

# Stems that don't match the generic bulletin regex but were confirmed by direct
# visual inspection to be the same FDA-advisory-bulletin type (multi-panel
# comparison graphic, ground-truth label rendered as pixel text). Found by
# manually viewing every remaining counterfeit-labeled image after the regex
# pass (see data/README.md "Filtering decisions").
BULLETIN_STEM_OVERRIDES = {"1877", "1434-2020"}

# kaggle_fake_real_medicine_00055 (Screenshot 2025-09-17 180529.png): found
# during the initial AI contact-sheet pass -- a literal browser screenshot
# of the Roboflow dataset's own webpage, not a medicine photo at all.
# images4006/4043/5012.jpg: flagged "screenshot" during the full human
# review via manual_review_tool.html -- not literal browser screenshots,
# but stock/marketing-render style images (generic product icons, a
# graphic-design product ad) rather than an organic device photo, i.e. not
# a real capture of the specific product either.
KAGGLE_NON_MEDICINE_FILENAMES = {"Screenshot 2025-09-17 180529.png", "images4006.jpg", "images4043.jpg", "images5012.jpg"}

# Full human review (data/metadata/manual_review_tool.html, all 563 images,
# 2026-07-24) confirmed 36 watermark/stock-photo-overlay images, then a
# second human review pass over the modality-tagging tool's images found
# 10 more (46 total) -- 46/46 (100%) are authentic-labeled, a confirmed
# class-correlated confound (same treatment as Roboflow's bulletin
# graphics). The AI contact-sheet pass had only opportunistically found 11
# of these 46 as suggestions. Spot-verified sources include "PharmEasy",
# "Generic India", "medicaldawa.in", "Crane Medic" (cranemedic.com),
# "Wellness Forever", and "alamy stock photo" -- i.e. this is several
# distinct product-catalog/stock-photo websites, not one repeated source.
KAGGLE_WATERMARK_FILENAMES = {
    "images31.jpg",
    "images311.jpg",
    "images336.jpg",
    "images340.jpg",
    "images4015.jpg",
    "images4028.jpg",
    "images4035.jpg",
    "images4036.jpg",
    "images4038.jpg",
    "images4053.jpg",
    "images4071.jpg",
    "images4080.jpg",
    "images4083.jpg",
    "images4089.jpg",
    "images4093.jpg",
    "images4095.jpg",
    "images4122.jpg",
    "images50.jpg",
    "images5001.jpg",
    "images5003.jpg",
    "images5007.jpg",
    "images5025.jpg",
    "images5028.jpg",
    "images5035.jpg",
    "images5040.jpg",
    "images5043.jpg",
    "images5045.jpg",
    "images5058.jpg",
    "images5065.jpg",
    "images5083.jpg",
    "images5085.jpg",
    "images5088.jpg",
    "images5090.jpg",
    "images5105.jpg",
    "images5115.jpg",
    "images5118.jpg",
    "images12.jpg",
    "images213.jpg",
    "images215.jpg",
    "images22.jpg",
    "images241.jpg",
    "images246.jpg",
    "images339.jpg",
    "images4024.jpg",
    "images4092.jpg",
    "images5026.jpg",
    "images256.jpg",
}

# (images256.jpg was found afterward: excluding more images shifted which
# exact-duplicate copy is "first-seen" and retained, surfacing a
# not-previously-reviewed copy that also carries the same kind of
# watermark. Spot-checked directly, confirmed "maddisonpharma"-style
# overlay, authentic-labeled -- consistent with the pattern above.)

# Found during the modality-tagging pass (data/metadata/
# modality_tagging_tool.html, tagged "other", 2026-07-24): a stock image of
# 7 loose pills with no packaging of any kind visible. Unlike the
# KAGGLE_NON_MEDICINE_FILENAMES cases, this genuinely is a photo of
# medicine -- it just fails the paper's actual task (packaging
# classification) on scope grounds, the same reason
# kaggle_fake_real_medicine_00164 / _00378 were flagged as "wrong modality"
# in the cross-model error analysis before this pipeline rebuild (see
# modeling/README.md "Error analysis" -- note those specific IDs have since
# shifted due to renumbering after this and earlier exclusions; the
# underlying issue is the same).
KAGGLE_NO_PACKAGING_FILENAMES = {"Screenshot 2025-09-17 190956.png"}

# Found via a targeted re-scan of the "other"-tagged images (2026-07-24,
# user request): syrup bottles, no blister pack or outer box in frame.
# Same reasoning as KAGGLE_NO_PACKAGING_FILENAMES -- genuinely medicine,
# genuinely authentic-labeled, but out of scope for a packaging/blister
# classification task. Each spot-verified directly (not inferred from a
# thumbnail alone -- an initial 4th candidate, images5078.jpg, turned out
# on full-resolution inspection to be a box+blister combo, not a bottle,
# and was excluded from this set).
KAGGLE_BOTTLE_FILENAMES = {"images278.jpg", "images5075.jpg", "images5114.jpg", "images5079.jpg"}


def roboflow_stem(orig_relpath: str) -> str:
    fname = Path(orig_relpath).name
    m = ROBOFLOW_FNAME_RE.match(fname)
    return m.group(1) if m else fname


def main():
    with open(INV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["excluded"] = "False"
        r["exclusion_reason"] = ""
        r["source_stem"] = ""

        if r["source"] == "roboflow_counterfeit_med_detection":
            stem = roboflow_stem(r["orig_relpath"])
            r["source_stem"] = stem
            if r["class_label"] == "ambiguous":
                r["excluded"] = "True"
                r["exclusion_reason"] = "dual_label_contradiction"
            elif BULLETIN_STEM_RE.match(stem) or stem in BULLETIN_STEM_OVERRIDES:
                r["excluded"] = "True"
                r["exclusion_reason"] = "bulletin_graphic_with_baked_in_label_text"
        else:
            # kaggle_fake_real_medicine: use filename (no roboflow suffix) as stem
            r["source_stem"] = Path(r["orig_relpath"]).stem
            if Path(r["orig_relpath"]).name in KAGGLE_NON_MEDICINE_FILENAMES:
                r["excluded"] = "True"
                r["exclusion_reason"] = "not_a_medicine_photo_browser_screenshot"
            elif Path(r["orig_relpath"]).name in KAGGLE_WATERMARK_FILENAMES:
                r["excluded"] = "True"
                r["exclusion_reason"] = "watermark_stock_photo_confound"
            elif Path(r["orig_relpath"]).name in KAGGLE_NO_PACKAGING_FILENAMES:
                r["excluded"] = "True"
                r["exclusion_reason"] = "loose_pills_no_packaging_visible"
            elif Path(r["orig_relpath"]).name in KAGGLE_BOTTLE_FILENAMES:
                r["excluded"] = "True"
                r["exclusion_reason"] = "syrup_bottle_wrong_modality"

    fieldnames = list(rows[0].keys())
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    retained = [r for r in rows if r["excluded"] == "False"]
    with open(REVIEW_OUT, "w", newline="", encoding="utf-8") as f:
        fn = ["source", "orig_relpath", "class_label", "modality_guess", "reviewer_modality", "reviewer_notes"]
        writer = csv.DictWriter(f, fieldnames=fn)
        writer.writeheader()
        for r in retained:
            guess = "outer_packaging_or_product_photo" if r["source"] == "roboflow_counterfeit_med_detection" else "unclassified"
            writer.writerow({
                "source": r["source"],
                "orig_relpath": r["orig_relpath"],
                "class_label": r["class_label"],
                "modality_guess": guess,
                "reviewer_modality": "",
                "reviewer_notes": "",
            })

    print(f"Total rows: {len(rows)}")
    excluded = [r for r in rows if r["excluded"] == "True"]
    print(f"Excluded: {len(excluded)}")
    from collections import Counter
    print(Counter(r["exclusion_reason"] for r in excluded))
    print(f"Retained: {len(retained)}")
    print(Counter((r["source"], r["class_label"]) for r in retained))
    print(f"\nWrote {OUT}")
    print(f"Wrote {REVIEW_OUT} ({len(retained)} rows queued for human modality review)")


if __name__ == "__main__":
    main()
