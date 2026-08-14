# Manual modality review — findings (plan Part 2.2)

**Status: complete.** This went through two passes:

1. **AI contact-sheet pass** (2026-07-23/24): all images tiled into 19
   labeled grids (`data/metadata/modality_review_sheets/`, built by
   `scripts/08_build_modality_contact_sheets.py`), reviewed qualitatively.
   Produced a composition *estimate* and opportunistically found 11
   watermark cases + 1 confirmed non-medicine image (a browser screenshot).
2. **Full human review** (2026-07-24), by the user, via two purpose-built
   local tools:
   - `data/metadata/manual_review_tool.html` (`scripts/09`/`10`) — every one
     of the then-563 images individually tagged clean / watermark /
     screenshot / unsure. Result: 46 watermark, 4 not-a-real-capture, 0
     unsure.
   - `data/metadata/modality_tagging_tool.html` (`scripts/11`/`12`) — every
     one of the resulting 524 images individually tagged blister / outer
     packaging / other, run on the pool as it stood after the watermark
     cleanup. Also caught 1 additional issue during this second pass (a
     loose-pills stock image miscategorized as "other") and 10 more
     watermark cases the first pass had missed.

All exclusions found across both passes are implemented in
`scripts/02_filter.py`. The numbers below are the final, complete,
human-verified state (510-image Kaggle modeling pool), not an estimate.

## Final modality composition (510 images, complete census)

| Modality | Count | % |
|---|---|---|
| Blister pack | 223 | 43.7% |
| Outer packaging (box) | 155 | 30.4% |
| Other (box+blister combo, sachet, etc.) | 132 | 25.9% |

Class balance at this point: 272 authentic, 238 counterfeit.

Two further correction rounds happened after the two main passes above:
- **Round 3** (2 images): 1 more watermark case + 1 image needing a direct
  "other" tag, both surfaced only because excluding more images changed
  which exact-duplicate copy is retained as the "first-seen"
  representative for a couple of near-duplicate clusters — not a review
  gap. See `scripts/02_filter.py` comments for exactly which.
- **Round 4** (user-requested re-scan for bottles): a targeted re-scan of
  the "other"-tagged images specifically for syrup bottles and any
  remaining loose-pills cases. Found 4 bottle candidates from an AI
  re-scan; 3 confirmed as genuine syrup bottles on full-resolution
  inspection (`images278.jpg`, `images5075.jpg`, `images5114.jpg`) and 1
  (`images5078.jpg`) turned out on closer inspection to be a box+blister
  combo, not a bottle, and was kept. The user then supplied their own
  modality-tool labels identifying a 4th genuine bottle the re-scan had
  missed (`images5079.jpg`) — confirmed on inspection and added. Final:
  4 bottles excluded (`KAGGLE_BOTTLE_FILENAMES`). Same exclusion reasoning
  as the loose-pills case: these are genuine, authentic-labeled medicine
  photos, just out of scope for a packaging/blister classification task.

**Conclusion for the paper's scope claim**: "outer packaging only" is NOT
an accurate description of this dataset as used — confirmed by a complete
census, not an estimate. It is closer to "outer packaging, blister packs,
and a substantial tail of combined/other presentations (bottles, sachets,
box+blister shown together)." The paper should either (a) restate its
scope honestly as "packaging and immediate product containers" rather than
"outer packaging only," or (b) actually filter to outer-packaging-only
(the 154 `packaging`-tagged images, or `packaging` + the box-containing
subset of `other`), which would remove roughly 60-70% of the pool and
require re-running Splits A/B/C and all modeling — a real scope decision,
not something to do silently. The "other" category is not further broken down by sub-type in
`provenance.csv` (the tagging tool didn't require notes for speed). Four
confirmed syrup-bottle examples were found across rounds 3-4 (referenced
by filename, since `image_id` numbering shifts on every pipeline rebuild —
see caveat below): `images278.jpg`, `images5075.jpg`, `images5114.jpg`,
`images5079.jpg`. A full sub-type breakdown of "other" would need another
(much faster, since only ~132 images) tagging pass with the notes field
actually used.

**Note on `image_id` stability — found broken, then fixed**: `image_id`
was originally assigned as a sequential counter over whatever was
currently retained, so it was NOT stable across pipeline reruns — every
exclusion renumbered everything after it. This was caught mid-review (an
`image_id` cited earlier for the loose-pills case turned out to point at a
different file after a rebuild) and fixed in `scripts/04_provenance.py`:
`image_id` is now a hash of `(source, orig_relpath)`, stable regardless of
how many other rows are added or removed. **Any `image_id` referenced in
project documentation written before 2026-07-24's fix (e.g. specific IDs
in `modeling/README.md`'s error analysis or Grad-CAM sections, or in this
file's earlier revisions) may point at a different file than when it was
written** — `orig_relpath` is the only reference guaranteed stable across
that boundary. The fix also makes `04_provenance.py` preserve manually-set
`modality` values across reruns (matched by the now-stable `image_id`)
instead of silently resetting them to the placeholder every time the
pipeline runs for an unrelated reason.

## Confirmed exclusions (all applied in `scripts/02_filter.py`)

**Non-medicine / not-a-real-capture (4 images, `KAGGLE_NON_MEDICINE_FILENAMES`)**:
- `Screenshot 2025-09-17 180529.png` — a literal browser screenshot of the
  Roboflow "Counterfeit_med_detection" dataset's own webpage (tabs and URL
  bar visible, reading ".../harshini-t-g-r/counterfeit_...-Advance-
  Buscopan-Kremil-S-and-Loper..."). Found in the AI pass.
- `images4006.jpg`, `images4043.jpg`, `images5012.jpg` — not literal
  screenshots, but stock/marketing-render images (a generic pill icon, a
  graphic-design product ad with a medical-cross background, a small
  low-detail blister icon) rather than an organic device photo of the
  actual product. Found in the full human review.

**Loose pills / bottles, no packaging or blister/box visible (5 images
total)**:
- `KAGGLE_NO_PACKAGING_FILENAMES` (1 image): `Screenshot 2025-09-17
  190956.png` — 7 loose white tablets on a plain background, no packaging
  of any kind. Found during the modality-tagging pass (tagged "other",
  then flagged for exclusion).
- `KAGGLE_BOTTLE_FILENAMES` (4 images): `images278.jpg`, `images5075.jpg`,
  `images5114.jpg`, `images5079.jpg` — syrup bottles, no blister pack or
  outer box in frame. Found via a targeted re-scan of the "other"
  category plus the user's own modality-tool labels, requested
  specifically to catch bottles the first pass had grouped into "other"
  without distinguishing.

All 5 are genuinely medicine photos — they just fail the paper's actual
task (packaging/blister classification) on scope grounds, same reasoning
as `kaggle_fake_real_medicine_00164` / `_00378` flagged as "wrong modality"
in the cross-model error analysis before this pipeline rebuild (see
`modeling/README.md` "Error analysis" — note those specific IDs have since
shifted; see the `image_id` stability note below).

**Watermark / stock-photo confound (47 images, `KAGGLE_WATERMARK_FILENAMES`)**:
found across three passes (11 in the initial AI pass, 35 more in the full
human review, 1 more surfaced by a duplicate-representative shift after
the second cleanup round). **Checked, not assumed: 47/47 (100%) are
authentic-labeled.**
Verified sources spot-checked directly (not just inferred from filenames):
"PharmEasy", "Generic India", "medicaldawa.in", "Crane Medic"
(cranemedic.com), "Wellness Forever", "alamy stock photo", plus several
unbranded/illegible overlays. This is several distinct product-catalog or
stock-photography websites, not one repeated source — i.e. a broad,
structural pattern in how the authentic-class images were sourced, not a
one-off artifact. Same treatment as Roboflow's bulletin-graphic exclusion:
a confirmed, class-correlated confound that a model could exploit as a
shortcut for "authentic" instead of learning genuine packaging cues.
Directly consistent with the Grad-CAM finding (`modeling/README.md`) that
EfficientNet-B0 attends to incidental background/photography-setup cues,
and a plausible contributor to the catastrophic Split C external-
generalization collapse (a model relying on stock-photo/watermark patterns
specific to this dataset's sourcing has no reason to transfer to a new
source with different sourcing conventions).

## Disclosure: modeling artifacts predate this cleanup

**All of `modeling/results/*`** (all 4 models' metrics, Grad-CAM, error
analysis, Split C eval) was generated against Kaggle pools *before* this
cleanup — the largest, at 563 images, still included all confirmed
watermark images, the loose-pills image, the bottle images, and most of
the non-medicine images. The current, final pool is **510 images** (down
from the original 564 — a ~9.6% reduction) that specifically removed every
confirmed class-correlated confound or wrong-modality image found across
four review rounds. **The retrain against this final pool is done** (all
4 models, 2026-07-24) — see `modeling/README.md` "What changed after
cleanup" for results. Headline: leakage deltas shrank and Grad-CAM
attention improved, but Split C (external generalization) got *worse* for
the two transfer-learning models and stayed at 0% for the other two —
ruling out the watermark confound as the primary cause of the
generalization failure.
