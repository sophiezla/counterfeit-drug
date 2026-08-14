# Synthetic counterfeit Split C — methodology, review, and limitations

## Motivation

Split C has been authentic-only throughout this project (see
`data/README.md` "Sources" for the search for a genuine independent
counterfeit-labeled external source, which came up empty). This means
every Split C number reported so far (`modeling/results/split_c_eval.csv`)
measures only the authentic-class false-positive rate on external data —
it says nothing about counterfeit-class recall (whether the models can
correctly flag a genuinely different-looking package as counterfeit at
all, on data they've never seen).

Since no real independent counterfeit-labeled dataset could be found, this
builds a **synthetic counterfeit proxy**: independent, never-before-used
authentic photos, perturbed with degradation modes commonly cited in
pharma anti-counterfeiting literature (print-quality defects, color/ink
mismatch, print misregistration, text/logo tampering), used as a stand-in
negative class.

**This is explicitly analogous to ImageNet-C-style synthetic corruption
benchmarks in the robustness literature** — a well-precedented practice
for exactly this "no real OOD negative class available" situation. It
measures recall against a specific, documented set of simulated defects,
**not** true real-world counterfeit-detection recall. Real counterfeits
may differ in ways not modeled here at all: security-feature omission
(holograms, tamper seals), packaging material/texture, barcode or serial
number errors, or subtler design differences than the print/color defects
simulated here. Every reference to this dataset in any future writeup
(paper included) must carry this caveat — it is a stress test, not a
ground-truth measurement.

## Source images

**First attempt (superseded) and why it was wrong.** The first version of
this pipeline used the Mendeley "iPhone 11 Pro" subset — 149 usable base
images (150 nominally; see below), same 150 products as the existing
"Huawei CN" authentic Split C set but different photos, never used
anywhere else in this project (`scripts/13_download_mendeley_iphone11pro.py`).
The reasoning at the time: using the same products (different photos)
rather than new products keeps product identity constant, isolating the
perturbation as the only systematic difference between classes.

**This reasoning was wrong in a way that mattered a lot.** After the full
149-image batch was generated and reviewed, a routine confound check
(brightness/resolution/file-size by class, the same check used throughout
this project since Finding 1) found the two classes differed in mean
brightness by **more than 2x** (authentic 0.162 vs. synthetic-counterfeit
0.359). Investigating further: the *un-perturbed base photos themselves*
already differed by roughly this much (Huawei CN 0.162 vs. iPhone 11 Pro
0.389, measured directly, before any perturbation). The Mendeley dataset's
own documentation describes a "controlled lighting-variation protocol"
across its phone subsets — different phone subsets were deliberately shot
under different lighting setups as part of the source dataset's own OCR-
robustness research design. Using a different phone subset as the
counterfeit-class base therefore reintroduced a large, systematic,
class-correlated confound **structurally identical to Finding 1** (the
original Kaggle capture-method confound this entire project has been
built around removing) — just via source *selection* this time, not
generation. A model could have learned "brighter capture session ->
counterfeit" and scored well on this synthetic Split C without learning
anything resembling a counterfeit-recognition cue, making any resulting
recall number meaningless.

**Fix**: generate synthetic counterfeits from the SAME 150 "Huawei CN"
photos already serving as the real authentic Split C class, not a
different phone subset. This makes the perturbation the only systematic
difference between classes — both classes come from the exact same
capture session/lighting setup, no separate phone/lighting confound
possible. Re-checked immediately after switching: authentic 0.162 vs.
synthetic-counterfeit 0.153 mean brightness — no longer a meaningful gap.
`scripts/15_generate_synthetic_counterfeit.py` was updated to source from
`data/raw/mendeley_split_c` (Huawei CN) instead of
`data/raw/mendeley_iphone11pro`; the iPhone 11 Pro download and first
generated batch were discarded. The lesson generalizes: whenever a
"negative class" is built by drawing from a *different* source/subset
than the positive class, check for confounds in the source photos
themselves, not just in whatever processing is deliberately applied on
top — this project has now been burned by exactly this pattern twice
(Finding 1, and this one).

**149, not 150, base images in the first (superseded) attempt**: the
source dataset's own file listing had a duplicate filename entry
(`iphone 11 pro (159).JPG` appears twice in the Mendeley API's file list),
which collided on download since both mapped to the same normalized
output filename — a quirk in the source dataset, not a bug in the
download script. Moot now that generation uses the Huawei CN subset
instead (all 150 of those files are already known-good, already used for
the existing Split C authentic class).

## Perturbation pipeline (`scripts/synthetic_counterfeit.py`)

Each base image gets a **randomly-chosen subset and severity** of the
following, seeded deterministically per image (reproducible on rerun, not
re-randomized):

**Photographic defects** (3-5 of 5 chosen per image; see "Severity fix"
below for why this is 3-5, not the original 2-4):
- Color/hue shift — per-channel intensity scaling (ink/pigment mismatch)
- Halftone overlay — faint dot-grid pattern (cheap offset-print screening)
- Print-registration warp — per-channel pixel offset (color-plate
  misregistration / fringing)
- Gaussian blur — randomized radius (out-of-focus/smudged print)
- Contrast reduction (low-grade paper/ink)

**Severity fix**: the first full batch (149 images, since-superseded base
source) was checked for perceptibility after generation — ~13% of images
landed on weak random parameter draws that were nearly imperceptible (mean
per-pixel diff <5/255 at review-display resolution), and the user
confirmed by eye that they could not reliably tell the synthetic images
apart from the originals. Root cause: each effect's severity range allowed
draws close enough to a no-op (e.g. a color-shift factor near 1.0, a
halftone spacing too fine to survive downscaling to a normal browser
review size) that a run of bad luck across 2-4 randomly chosen effects
could compound into an overall negligible change. Fixed by: widening every
effect's severity range and biasing color-shift away from a 1.0-centered
window (guaranteed >=15% per-channel deviation), scaling halftone dot
spacing to image size instead of a fixed small px count so it survives
downscaling, and requiring 3-5 (not 2-4) of the 5 effects per image.
Re-verified across all images before regenerating the full batch: 0%
imperceptible (previously 13%), minimum per-pixel diff 6.0/255 (previously
some were ~1.0/255).

**Text/logo tampering** (applied to 1 to ~half of detected text/logo
regions per image):
- Region detection: classical CV only (no OpenCV/Tesseract available in
  this environment) — edge-density thresholding + connected-component
  blob detection + text-line-shaped aspect-ratio filtering, applied
  directly on the image (no OCR, doesn't read or understand the text).
- Ghosting — region duplicated with a small shift, alpha-blended (print
  misregistration/double-strike)
- Scramble — 1-2 thin strips shifted a few px, alpha-blended (mimics
  slight print jitter). **An earlier version reordered many strips across
  the whole region**, which read as an obvious digital glitch rather than
  a believable print defect during preview review — toned down to a much
  smaller, subtler shift after the user reviewed a preview batch and
  flagged it.
- Dropout — random patches lightened (faded/incomplete ink)

## Anti-shortcut design

Every perturbation draws parameters randomly per image, and each image
gets a randomly-chosen subset of effects, not a uniform fixed filter —
this is specifically to avoid recreating the project's original
capture-method confound (Finding 1,
`data/metadata/capture_method_confound_findings.md`) in a new form, where
a model could learn to detect "this exact processing signature" instead
of anything resembling a counterfeit-recognition cue. Output images are
saved as normal-quality JPEGs (quality=95, matching a genuine photo
export), not pre-degraded in file size/resolution/format in a
class-correlated way — the project's standard 3-way normalization
(`modeling/normalization.py`) is applied uniformly to both classes at
eval time, same as everywhere else in this project, not baked into
generation.

## Preview review process

Before generating the full batch, two 12-image preview grids
(`data/metadata/synthetic_counterfeit_preview/preview_grid.png`, two
random samples) were generated and visually reviewed (by the assistant,
then reported to the user) at both thumbnail and full resolution. This
caught the scramble-op issue described above: on the "Minalax" box's
"CROWN" logo, the original scramble implementation reordered many strips
across the whole region, producing unreadable, visibly-glitched text
rather than a believable print defect. After toning it down to a 1-2
thin-strip small shift, a second preview batch (different random sample,
14 more products) showed no comparable issues — text tampering was subtle
and plausible throughout, and photographic defects (color shift, halftone,
blur, contrast) gave a convincing "cheap counterfeit print" look without
looking artificial.

## Manual review (user-driven)

All 149 synthetic candidates were then generated
(`scripts/15_generate_synthetic_counterfeit.py`,
`data/raw/synthetic_counterfeit/*.jpg`,
`data/metadata/synthetic_counterfeit_candidate_provenance.csv`) and
reviewed by the user via a side-by-side HTML tool
(`scripts/16_build_synthetic_review_tool.py` →
`data/metadata/synthetic_review_tool.html`, same fast keyboard-driven
pattern as the earlier watermark/modality review tools) — original photo
next to its synthetic counterfeit candidate, tagged approve / reject /
unsure. Only **approved** rows are included in the final set; rejected and
unsure rows are excluded (same "no action = no inclusion" convention as
the earlier manual review rounds — see `modality_review_findings.md`).

**Review completed 2026-07-28**: all 150 synthetic candidates reviewed via the tool, exported to `~/Downloads/synthetic_counterfeit_review.csv`. Result: **150/150 approved, 0 rejected, 0 unsure** — no rejection-reason patterns to report, since none were rejected.

## Final assembly and confound check

`scripts/17_apply_synthetic_review.py` combines the 150 real authentic
photos (existing, verified-independent Split C) with the approved
synthetic counterfeit candidates into
`data/metadata/split_c_synthetic_provenance.csv`, and re-runs a
Finding-1-style confound check (mean brightness, median resolution, mean
file size, per class) between the two classes — the same check that
originally surfaced the capture-method confound in the main Kaggle pool —
specifically to catch it here too rather than assume the perturbation
pipeline didn't introduce one.

**Confound check results 2026-07-28** (`scripts/17_apply_synthetic_review.py`, 150 authentic vs. 150 approved synthetic counterfeit): mean brightness 0.162 (authentic) vs. 0.153 (counterfeit) — no meaningful gap, as expected since both classes share the same Huawei CN source photos. Median min-resolution identical (2448 both classes, also expected — resolution isn't touched by the perturbation pipeline). Mean file size differs (authentic 1,655,915 bytes vs. counterfeit 1,017,839 bytes) — expected and not a confound to control for: it's a direct, causal consequence of the perturbation pipeline itself (blur/halftone/contrast changes reduce JPEG-encoded detail), unlike Finding 1's file-size gap which came from two totally different, class-confounded capture pipelines. Splits C's final dataset written to `data/metadata/split_c_synthetic_provenance.csv` (300 rows: 150 authentic + 150 synthetic counterfeit).

## Evaluation

**Evaluation completed 2026-07-28** (`modeling/eval_split_c_synthetic.py`, all 4 models deterministically retrained on Split B's train pool, same seeds/LRs as `eval_split_c.py`, evaluated on the full 300-image synthetic Split C set). Results (`modeling/results/split_c_synthetic_eval.csv`):

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Model 1 (classical color-hist + LogReg) | 0.500 | 0.500 | 1.000 | 0.667 | **0.895** |
| Model 2 (small CNN, GAP head) | 0.633 | 0.744 | 0.407 | 0.526 | 0.794 |
| Model 3 (MobileNetV3-Small, frozen) | 0.483 | 0.460 | 0.193 | 0.272 | 0.503 |
| Model 4 (EfficientNet-B0, frozen) | 0.550 | 0.603 | 0.293 | 0.395 | 0.570 |

**Key finding — Model 1's miscalibration, not lack of signal, dominates its result.** Model 1 predicts "counterfeit" for essentially every image (recall=1.0, accuracy pinned at exactly 0.5 by construction), yet has by far the best ROC-AUC of the four models (0.895) — meaning its raw scores rank synthetic-counterfeit images above authentic ones quite well, but its 0.5 decision threshold (fit on the very different real-Kaggle brightness/resolution distribution) is badly wrong for this set. This is a genuinely different failure mode from Split C's authentic-only result (where Model 1 scored 0% — see `split_c_eval.csv` and the main README), and together the two suggest Model 1's classical color-histogram features do carry *some* transferable signal, but its LogReg threshold is calibrated in a way that only works in-distribution.

**Models 2 and 4 show modest, genuine separation** (AUC 0.794 and 0.570 respectively) but both trade off toward low recall at the default 0.5 threshold — both are far more likely to call a synthetic counterfeit "authentic" than vice versa (Model 2 misses 89/150; Model 4 misses 106/150).

**Model 2's row was re-measured 2026-07-28** after the learning-rate defect described in `modeling/README.md` "Known caveats" was fixed (its rebuild had been trained at 0.0003 while the model of record used 0.001). Pre-fix values: accuracy 0.623, precision 0.794, recall 0.333, F1 0.469, ROC-AUC 0.788 — preserved in `split_c_synthetic_eval_PRE_LRFIX_20260728.csv`. Every qualitative reading in this file is unchanged.

**Model 3 is at chance (AUC 0.503)** — this is the most interpretable result of the four, and it corroborates rather than contradicts the earlier Grad-CAM finding (`capture_method_confound_findings.md` Finding 8) that Model 3's strong *authentic-only* Split C performance was driven by a background/backdrop-matching shortcut specific to the real Mendeley photos' consistent backdrop, not a genuine understanding of packaging authenticity. That shortcut provides zero signal for distinguishing an authentic photo from a perturbed version of the *same* photo (same backdrop in both), so chance-level performance here is exactly what the earlier finding would predict, and directly cross-validates it using a completely different eval set.

**Overall interpretation for the paper**: none of the 4 models show strong, well-calibrated counterfeit-recall against this synthetic perturbation-style proxy, reinforcing (via an entirely different route than the authentic-only Split C or the confound-normalization experiments) that high in-distribution accuracy in this project has not reflected robust, transferable counterfeit-detection ability. As always: this measures robustness to the specific print/color/text defects simulated here, not true real-world counterfeit recall — that caveat must accompany every reference to this table.
