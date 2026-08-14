# Data Pipeline

This document is the data card for the leakage-corrected benchmark described
in the study protocol. It records every decision made while
turning the two raw source zips into modeling-ready, leakage-free splits, and
gives exact commands to reproduce every artifact from scratch.

## TL;DR

- Two public sources were inventoried, filtered, deduplicated, and split.
- **The two sources turned out not to be independent**: 44% of the Kaggle
  dataset's images are near-duplicates of Roboflow images (same underlying
  photos, sometimes just rotated). This alone would have broken the original
  plan's idea of using one as an external Split C hold-out for the other.
- The Roboflow source's counterfeit class is **100% unusable**: every
  counterfeit-labeled image in it is an institutional advisory-bulletin
  graphic with the ground-truth label rendered as literal pixel text (e.g.
  the word "COUNTERFEIT" printed on the image), not a product photograph.
  It contributes 2 usable counterfeit images after filtering, against 2695
  authentic ones.
- Given that, **the main modeling pool (Splits A and B) is the Kaggle "Fake
  vs Real Medicine" dataset only**
  — so that Split A vs. Split B is a clean, single-variable, before/after
  leakage comparison, uncontaminated by also changing the underlying data.
- Perceptual-hash clustering (rotation-aware) is used as an operational
  proxy for "product identity" (no ground-truth product labels exist in
  either source). Split B groups on this. The leakage check asserts zero
  product-identity overlap across train/val/test and currently passes.
- A genuinely independent 3rd source was found for an **authentic-only**
  external check (Mendeley, verified non-duplicative via the same pHash
  pipeline) — see "Sources" below. No independent *counterfeit*-labeled
  source was found, so full two-class Split C generalization is still
  untested — see "Open items".

## Directory layout

```
data/
  raw_zips/                     original downloaded zips (kept, untouched)
  raw/roboflow/                 extracted Roboflow zip (train/valid/test + _classes.csv)
  raw/kaggle_fake_real/dataset/ extracted Kaggle zip (Fake/, Real/, + a discarded pre-split)
  metadata/
    inventory.csv                every image, both sources, as shipped
    filtered_pool.csv            inventory.csv + excluded/exclusion_reason columns
    needs_manual_review.csv      retained images still needing a human modality pass
    dedup_clusters.csv           every retained image + pHash + product_identity cluster
    dedup_report.txt             dedup summary stats
    provenance.csv               final per-image metadata table (Part 2.3 of the plan)
  processed/
    roboflow_supplementary_authentic_pool.csv   Roboflow's usable images, kept OUT of
                                                  the main experiment (see below)
splits/
  split_a.csv        naive image-level 70:15:15 split (image_id, split)
  split_b.csv        product-grouped 70:15:15 split (image_id, product_identity, split, cv_fold)
  split_report.txt   counts, class balance, and the leakage self-check
scripts/
  01_inventory.py     walk raw data, one row per image
  02_filter.py        apply documented exclusion rules
  03_dedup.py         rotation-aware pHash clustering -> product_identity
  04_provenance.py    merge filter + dedup decisions into the final provenance table
  05_build_splits.py  build Split A, Split B, 5-fold CV, leakage self-check
  run_all.py          run 01-05 in order
  06_download_mendeley_split_c.py       download the Split C candidate (one-time, ~248MB)
  07_verify_split_c_independence.py     confirm it's not a near-duplicate of the training pool
  08_build_modality_contact_sheets.py   build image grids for the modality review pass
  09_build_manual_review_tool.py        build the local HTML watermark/screenshot tagging tool
  10_apply_manual_review.py             apply the tool's exported CSV back into the pipeline
requirements.txt
```

Scripts 06-07 are not part of `run_all.py` (they're a one-time external
download + check, not a rebuild-from-raw-zips step) — run them separately,
see "Sources" above. Scripts 08-10 are the manual-review workflow — see
"Manual review workflow" below.

## Manual review workflow (scripts 09-12) — completed 2026-07-24

Status: **done**. Both tools below were used for a full, 100%-coverage
human review of the Kaggle pool (not a sample) — results are in
`data/metadata/modality_review_findings.md` and already applied to
`scripts/02_filter.py`'s exclusions. Kept here as a reusable workflow in
case more images need review later (e.g. if a new source is added).

### Watermark / screenshot flagging (scripts 09-10)

For flagging watermarks, screenshots/non-medicine images, and anything
uncertain, by hand, faster than opening 564 files one at a time:

```bash
python scripts/09_build_manual_review_tool.py
# then open data/metadata/manual_review_tool.html directly in a browser
# (double-click it, or `start`/`open` from the shell) -- no server needed.
```

The tool shows one image at a time, large, with keyboard shortcuts:
**Space**/**→** = clean, **W** = watermark, **S** = screenshot/not-medicine,
**U** = unsure, **←** = go back. Each key press auto-advances to the next
image. Progress auto-saves to the browser's localStorage (keyed to the
file), so closing and reopening resumes where you left off. It comes
pre-seeded with 13 AI-flagged suggestions from the earlier contact-sheet
pass (shown as a colored banner, e.g. "Suggested: WATERMARK -- ...") —
these are starting points to confirm or override, not settled answers.

When done (or partway through — export any time), click **Export CSV**,
which downloads `manual_watermark_review.csv`. Save/move it to
`data/metadata/manual_watermark_review.csv`, then:

```bash
python scripts/10_apply_manual_review.py            # dry run: reports counts,
                                                       # prints filenames, no changes
python scripts/10_apply_manual_review.py --apply     # edits scripts/02_filter.py's
                                                       # exclusion sets and re-runs
                                                       # the full data pipeline
```

`--apply` excludes `watermark`- and `screenshot`-flagged images (same
treatment as the Roboflow bulletin-graphic exclusion — a confirmed,
class-correlated confound; see `modality_review_findings.md`). `unsure`
rows are NOT auto-excluded — they're written to
`data/metadata/manual_review_unsure_queue.csv` for a separate judgment
call, since "unsure" isn't a clear-cut exclusion by definition.

**After running `--apply`**: Splits A/B/C will differ from whatever the 4
models in `modeling/` were last trained on until a retrain is run — as of
2026-07-24, all 4 models have been retrained on the final 510-image pool
and `modeling/README.md` is up to date. If you add further exclusions via
this workflow, `modeling/results/*` will again predate the data until
retrained (`python modeling/train_model{1,2,3,4}_*.py`, then
`aggregate_results.py`, `gradcam.py`, and `eval_split_c.py`).

### Modality tagging (scripts 11-12)

Same interface pattern, for classifying blister pack / outer packaging /
other, run on the pool as it stands *after* the watermark/screenshot
cleanup above (so results aren't invalidated by that data change):

```bash
python scripts/11_build_modality_tagging_tool.py
# open data/metadata/modality_tagging_tool.html in a browser
```

Keyboard: **B** = blister pack, **P** = outer packaging, **O** = other
(use the notes field for what kind — loose pills / syrup / sachet /
box+blister combo), **←** = back. Export → save as
`data/metadata/manual_modality_tags.csv`, then:

```bash
python scripts/12_apply_modality_tags.py
```

This only writes into `provenance.csv`'s `modality` column — no
exclusions happen here (deciding whether to filter to outer-packaging-only
is a separate, much bigger decision — see `modality_review_findings.md`).
`04_provenance.py` now preserves these values across pipeline reruns
(matched by `image_id`, which is a content hash — stable across reruns
even when other rows are added/removed, unlike an earlier version of this
script).

## Reproducing from scratch

```bash
cd pharmavision
pip install -r requirements.txt

# 1. Extract the raw zips (one-time, not scripted — see paths below)
unzip -q "data/raw_zips/Counterfeit_med_detection.v4i.multiclass (1).zip" -d data/raw/roboflow
unzip -q "data/raw_zips/archive (1).zip" -d data/raw/kaggle_fake_real

# 2. Run the pipeline
python scripts/run_all.py
```

All five steps are deterministic (fixed seed = 42 everywhere randomness is
used) and idempotent — re-running overwrites the CSVs with byte-identical
results. Total runtime is ~35 seconds on the machine this was built on (the
pHash step, hashing ~4,700 images at 4 rotations each, dominates).

## Sources

| Source | Raw zip | Images (as shipped) | License | Notes |
|---|---|---|---|---|
| Roboflow `Counterfeit_med_detection` v4 | `Counterfeit_med_detection.v4i.multiclass (1).zip` | 4,260 (train/valid/test, includes Roboflow's own 3x rotation+exposure augmentation) | CC BY 4.0 | See findings below — counterfeit class unusable |
| Kaggle "Fake vs Real Medicine" | `archive (1).zip` | 661 (`dataset/Fake` + `dataset/Real`) | Not stated in the zip; attribute to Kaggle uploader | Primary modeling pool (Splits A and B) |
| Mendeley "Mobile-Captured Pharmaceutical Medication Packages" (DOI 10.17632/bjy2svvmn8.1, Abdelmaksoud/Gadallah/Asad, Cairo University) | downloaded via `scripts/06_download_mendeley_split_c.py` into `data/raw/mendeley_split_c/` | 150 (one per each of 150 distinct products; full dataset is 3,900 across 6 devices, only the "huawei cn" subset was pulled) | CC BY 4.0 | **Authentic-only** (no counterfeit label) — used as Split C, see below |

The plan's Part 2.1 calls for "at least 1 additional public source" to serve
as a genuinely external Split C hold-out. A two-class (authentic +
counterfeit) independent source was searched for and **not found** — every
candidate identified (mostly Roboflow "authentic vs counterfeit" datasets
for the same drug brands — Biogesic, Neozep, Buscopan — that appear in the
bulletin images already excluded above) was either highly likely to share
the same underlying photos as sources already in this pool, or turned out
to have no counterfeit label at all. Per the user's direction, the Mendeley
dataset above is used instead as an **authentic-only external
generalization check** — not a full Split C. Its independence from the
Roboflow+Kaggle pool was verified programmatically (not just assumed from
its description) using the same rotation-aware pHash pipeline as the main
dedup step: `scripts/07_verify_split_c_independence.py`, report at
`data/metadata/split_c_independence_report.txt` (0/150 candidate images
matched anything in the existing pool; nearest match at Hamming distance
10/64, comfortably above the 8-bit near-duplicate threshold used
throughout this project). See `modeling/README.md` "Split C" for what this
found when the trained models were evaluated on it — it is the single most
important result of the modeling pass.

## Filtering decisions (script `02_filter.py`)

Filtering was informed by a manual visual audit (not exhaustive pixel-by-pixel
review of all 4,920 images — see "What manual review still needs to happen"
below for what remains).

1. **52 Roboflow rows with contradictory labels** (`authentic=1` AND
   `counterfeit=1` simultaneously in `_classes.csv`) — excluded outright as
   corrupted annotations.

2. **180 Roboflow images identified as "bulletin graphics"** — excluded.
   These are Philippine FDA public-health-advisory graphics and social-media
   reposts of the same: multi-panel comparison collages, often with an FDA
   logo, a banner headline like *"Public Health Warning Against the Purchase
   and Use of the Following Unregistered Drug Products"*, and — critically —
   **the ground-truth label rendered as literal text in the image**, e.g. a
   caption reading `COUNTERFEIT` or `AUTHENTIC` directly overlaid on the
   photo. Example files viewed and confirmed during the audit:
   `FDA-Advisory-No-2022-0611-4...jpg`, `109956533_...jpg`,
   `2020-1348_33-1-_...jpg`, `Authentic-vs-fake-Medicol-Advance-...jpg`,
   `1877_...jpg`, `1434-2020_...jpg`.

   These were identified via a filename-pattern regex (`FDA-Advisory*`,
   numeric Facebook-photo-ID prefixes, dated `20XX-*` doc scans, `fake-*`,
   `authentic-vs-fake*`, `how-to*`, `maxresdefault*`) plus two explicit
   overrides (`1877`, `1434-2020`) found by directly viewing every
   remaining counterfeit-labeled Roboflow image after the regex pass, since
   there were few enough (9) left to check by hand.

   **This is class-correlated, not incidental**: cross-tabulating by unique
   source image, **100% of Roboflow's counterfeit-labeled images (57/57
   pre-override) were bulletin graphics**, while **100% of its "clean"
   product photos (263/263) were authentic-labeled**. A model trained on
   this data as shipped would learn to distinguish institutional bulletin
   collages from plain product photography — not counterfeit packaging.
   This is a more severe and more decisive problem than the class imbalance
   that has been flagged before as a reason for dropping this dataset.
   That earlier account attributed the problem to imbalance; the deeper
   issue is this modality confound.

   Net effect: after filtering, Roboflow contributes **2 usable counterfeit
   images** (post-dedup) against thousands of authentic ones.

3. **What was NOT filtered here**: the plan's Part 2.2 "outer packaging vs.
   blister-pack vs. loose-pills vs. label-close-up" modality classification.
   Both sources visually mix modalities (confirmed by the source paper
   description of the Kaggle set, and by spot-checking — e.g. Kaggle
   contains both boxed products and loose sachets/blister-adjacent shots).
   Doing this exhaustively by eye for ~3,300 retained images was out of
   scope for this pass. `data/metadata/needs_manual_review.csv` is a queue
   (image path + a coarse automated guess + empty `reviewer_modality` /
   `reviewer_notes` columns) ready for a human pass — this is Week 1,
   Days 2-3 in the plan's timeline and still needs to happen before the
   "outer packaging only" scope claim in the paper is literally true.

## Deduplication & product identity (script `03_dedup.py`)

No ground-truth product-identity labels exist in either source, so
near-duplicate photo clustering is used as the operational proxy, exactly as
the plan's Part 2.4 anticipates ("group under same product_identity for
split purposes").

- **Method**: 64-bit pHash (`imagehash.phash`) computed at all 4
  orientations (0/90/180/270) per image; the numeric minimum across
  orientations is used as a rotation-canonical hash. This was necessary
  because Roboflow's own README documents 90-degree-rotation augmentation,
  and a plain (non-rotation-aware) pHash would treat a rotated copy of the
  same photo as a different image. **Verified**: `images4110_jpg.rf....jpg`
  (Roboflow, rotated 90°) and `images4110.jpg` (Kaggle, unrotated) hash into
  the same cluster and are visually confirmed to be the same underlying
  photo.
- **Known limitation**: this is not robust to horizontal/vertical *flips*
  (mirrored duplicates would be missed). The plan itself avoids flip
  augmentation for a related reason (mirrored printed text looks wrong), so
  this is a low-risk gap, but it is not exhaustively verified.
- **Thresholds**: exact duplicates (Hamming distance 0 on the canonical
  hash) are treated as true duplicates and **removed**, keeping only the
  first-seen copy (plan's Part 2.4: "true duplicate — remove one copy").
  Near-duplicates (distance 1-8 / 64 bits) are **kept** but grouped into the
  same `product_identity` cluster (plan's Part 2.4: "same product different
  photo — keep, but group").
- **Sanity check**: zero clusters mix `authentic` and `counterfeit` labels
  — i.e. the clustering never contradicts the original annotations.

**Major finding — cross-source overlap**: 229 clusters contain images from
*both* Roboflow and Kaggle. That's 2,900/4,027 retained Roboflow images and
290/661 Kaggle images (44% of the entire Kaggle dataset) — meaning these two
"independent" public datasets substantially share the same underlying photo
pool. This was spot-verified visually (see `images4110` example above) and
is not a hash-collision artifact. Anyone treating Roboflow and Kaggle as
independent sources for cross-dataset generalization testing (as the
original plan's Split C sketch assumed one could) would be leaking test
data into "external" evaluation without deduplication first.

Full numbers are in `data/metadata/dedup_report.txt`, regenerated on every
pipeline run.

## Modeling pool decision

The plan's model roster and split protocol assume one coherent pool. Given
the findings above, **Splits A and B are built from the Kaggle pool only**
(564 images post-dedup, 530 product_identity groups, 232 counterfeit / 298
authentic groups). Reasoning:

- Roboflow contributes ~0 usable counterfeit signal, so including it would
  push class imbalance from Kaggle's already-lean 44:56 ratio (at the group
  level) to roughly 8:92 — actively harmful given the plan already relies on
  class-weighted loss rather than oversampling specifically because
  counterfeit counts are small.
- Since prior work has trained on this exact Kaggle dataset, using the
  same pool for Split A/B isolates the single variable the paper's primary
  research question is actually about: *does correcting the split protocol
  change the measured accuracy*. Mixing in a second, differently-sourced,
  single-class pool would confound "we fixed the split" with "we also
  changed the data," undermining the headline comparison.

Roboflow's 2,697 filtered, deduplicated images (nearly all authentic) are
preserved at `data/processed/roboflow_supplementary_authentic_pool.csv` for
optional future use (e.g., a robustness/generalization check on unseen
authentic packaging), but are **not** used by any split by default.

## Split protocol (script `05_build_splits.py`)

- **Split A (naive)** — random 70:15:15, stratified by class, at the
  **image** level, fixed seed 42. This reproduces the mistake the plan
  attributes to the field generally.
- **Split B (corrected)** — 70:15:15, stratified by class, at the
  **product_identity group** level, fixed seed 42, so no near-duplicate
  photo/product can appear in more than one of train/val/test. The `train`
  partition additionally carries a `cv_fold` column (0-4) from
  `StratifiedGroupKFold`, so 5-fold CV never puts the same product in two
  folds either.
- **Leakage self-check**: the script asserts zero product_identity overlap
  between every pair of {train, val, test} in Split B. This currently
  passes and is re-verified on every run (`run_all.py` will raise
  `AssertionError` if it ever doesn't).
- **Quantified leakage in the naive split**: comparing Split A and Split B
  group assignments directly, 14 of 530 product_identity groups (2.6%) have
  members placed in more than one partition under Split A — this is the
  literal, countable leakage that Split B eliminates, and gives a first
  concrete number for the paper's headline "how much did leakage matter"
  question (Part 4.2 of the plan) once accuracy is measured under both
  protocols.
- **Split C (external)**: built as an authentic-only check (150 Mendeley
  images, verified independent) — see "Sources" above and
  `modeling/README.md` "Split C" for results. Not the two-class benchmark
  the plan originally envisioned (see Open Items below).

## Open items / what's still needed before modeling starts

1. **A counterfeit-labeled independent Split C source.** The authentic-only
   Mendeley check (above) resolves the "is there sampling/generalization
   bias" question for the authentic class, but says nothing about whether
   counterfeit-detection recall generalizes externally — that remains
   untested. A genuinely independent source that also has a counterfeit
   label would still need the same pHash independence verification before
   being trusted (Roboflow, the obvious second source, turned out to
   overlap with Kaggle by 44% despite looking independent by description).
2. **Manual modality review — DONE and complete for the Kaggle modeling
   pool (2026-07-24), still open for Roboflow's supplementary pool.**
   Three rounds: an AI contact-sheet pass (composition estimate + 11
   opportunistic finds), then a full human review of every image via two
   purpose-built local tools (`data/metadata/manual_review_tool.html` for
   watermark/screenshot flagging, `data/metadata/modality_tagging_tool.html`
   for blister/packaging/other classification) — see "Manual review
   workflow" below and full findings in
   `data/metadata/modality_review_findings.md`. **Final census, 514 images,
   100% coverage, not an estimate**: 223 blister pack (43.4%), 155 outer
   packaging box (30.2%), 136 other/combo (26.5%). Confirms this dataset is
   NOT outer-packaging-only — the paper's scope claim needs correcting, or
   the data needs an actual outer-packaging-only filter (a bigger
   undertaking requiring re-running Splits A/B/C and all modeling). The
   review also found and excluded: 4 non-medicine images (1 literal browser
   screenshot + 3 stock/marketing-render images), 1 loose-pills image (no
   packaging visible at all), and **47 watermark/stock-photo-overlay
   images — checked, not assumed: 47/47 (100%) are authentic-labeled**,
   sourced from at least 6 distinct catalog/stock-photo websites
   (PharmEasy, Generic India, medicaldawa.in, Crane Medic, Wellness
   Forever, alamy). Roboflow's 2,697-image supplementary pool (not used in
   modeling by default) still has only a coarse automated guess, not a
   human pass.
3. **`apparent_capture_condition`** (studio/field/unclear) in
   `provenance.csv` is a placeholder (`unclassified_needs_manual_review`)
   for every row — this field genuinely requires human judgment per image
   and was out of scope for this automated pass.
4. Augmentation (Part 2.7 of the plan) and all of Part 3 (modeling) haven't
   started; this data pipeline only covers Part 2.
