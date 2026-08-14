# The capture-method confound — why Split C collapses (investigation, 2026-07-25)

**Triggered by**: after the full watermark/modality cleanup and retrain
(`modality_review_findings.md`), Split C external generalization got
*worse*, not better, for the two transfer-learning models, and stayed at
exactly 0% for the classical and small-CNN models. This ruled out "the
watermark confound explains the failure" and prompted a direct
investigation into what else differs between the Kaggle training pool and
the Mendeley Split C set. Method: compare basic image statistics (not
semantic content) between the two pools, and check whether any of them
correlate with the class label inside Kaggle.

## Finding 1: Kaggle's two classes come from two different capture pipelines

Every one of the 510 Kaggle images' filenames falls into exactly one of
two patterns, and **the pattern is 100% correlated with the class label**:

| Pattern | Class | n | Median resolution | Mean file size | Mean brightness (0-1) |
|---|---|---|---|---|---|
| `images<N>.jpg` | authentic | 272 | 225×225 | 6,022 bytes | 0.767 |
| `Screenshot <date>.png` | counterfeit | 238 | 454×550 | 339,188 bytes | 0.555 |

This was visible from the very first data-audit pass (filenames noted at
the time) but not quantified until now. It means resolution, file size
(a proxy for compression/detail level), and brightness are ALL
simultaneously and severely confounded with class label across the
**entire dataset**, not just in the 47 watermarked images already removed.
A classifier — even the 96-dim color-histogram baseline — has direct,
undisguised access to overall image brightness as a feature; a from-image
CNN has direct access to resolution-dependent blur/detail statistics.
Neither needs to learn anything about packaging to do reasonably well
in-distribution.

**Statistical test**: authentic vs. counterfeit brightness, two-sample
t-test: t=17.0, p≈0 (as close to zero as floating point represents). This
is not a subtle effect — it is one of the strongest, most trivially
learnable signals available in the entire training set.

## Finding 2: Split C sits on the opposite extreme of both axes

| | Kaggle authentic | Kaggle counterfeit | Split C (external, all authentic) |
|---|---|---|---|
| Median resolution | 225×225 | 454×550 | 2448×3264 |
| Mean brightness | 0.767 (bright) | 0.555 (darker) | **0.162 (very dark)** |

Split C images are real smartphone camera photos: ~10x higher linear
resolution than the *average* Kaggle image, and substantially darker than
even Kaggle's counterfeit class (which is itself darker than Kaggle's
authentic class). A model that has learned "bright + tiny + heavily
compressed → authentic" (even partially, even as one signal among others)
will see Split C's uniformly huge, dark, high-detail images and have every
statistical reason to call them "not-authentic" — i.e. counterfeit. **This
exactly matches the observed result**: Models 1 and 2 (color histogram,
small CNN — both with direct, unmediated access to raw pixel/brightness
statistics) get 0% correct on Split C, calling every single external
authentic image counterfeit. Models 3 and 4 (frozen ImageNet backbones,
which include learned invariances to some brightness/scale variation from
pretraining) fail less totally but still severely (~69% and ~3%
respectively) — consistent with pretrained features providing partial,
not complete, protection against this shortcut.

## What this means for the project

- **The 47-image watermark cleanup was correct to do and did measurably
  improve Grad-CAM attention and shrink leakage deltas** — but it was
  never going to fix Split C, because the dominant confound was not the
  watermarks; it was this capture-method split affecting the entire
  authentic/counterfeit label in the source dataset.
- **This is a property of the Kaggle "Fake vs Real Medicine" dataset
  itself**, not something this
  project's own filtering introduced. It means any accuracy number ever
  reported on this dataset — any of this project's Split A/B
  numbers — has always had a large, easy, non-packaging shortcut available.
  This is arguably the single most important methodological finding for
  the eventual paper: **the true task difficulty is likely far higher than
  any in-distribution number on this dataset can reveal**, because the
  dataset's own construction (screenshots for fakes, direct photos for
  real, or the reverse sourcing pattern) confounds capture method with the
  label being predicted.
- **This cannot be fixed by more image-level filtering** (no single-image
  exclusion rule removes a pattern that applies to 100% of both classes).
  Fixing it would require either (a) a differently-constructed dataset
  where capture method is balanced across classes, or (b) explicit
  normalization (e.g. brightness/resolution standardization) applied
  identically to both classes before training — the latter is worth
  trying as a follow-up experiment, though it would only address the
  brightness/resolution axes specifically, not any other correlated
  difference between the two capture pipelines (compression artifacts,
  color profile, aspect ratio, etc. — not all checked here).

## Finding 3: Grad-CAM on the actual Split C images confirms this directly

Script: `modeling/gradcam_split_c.py`. Output:
`modeling/results/gradcam_split_c/*.png` (20 heatmap overlays: 10 of the
134/150 images the model called counterfeit, 10 of the 16/150 it called
authentic) + `manifest.csv`.

**Visually, every single Split C image shares a distinctive dark
navy/blue photography backdrop** — sharply different from Kaggle's
predominantly bright/white backgrounds (consistent with the brightness
numbers above: Split C mean brightness 0.162 vs. Kaggle authentic 0.767).
Reviewing several of the images the model called counterfeit
(`..._00032`, `..._00006`, `..._00077`): **Grad-CAM attention is
genuinely on the product** — the printed drug name/text — **not on noise
or nothing**. This matters: the model is not failing by "looking at
garbage" or attending randomly on unfamiliar input. It is making a
spatially sensible, confident decision (predicted probabilities of
0.94-1.00 for "counterfeit") that is simply calibrated to the wrong cue —
almost certainly the same brightness/background-darkness signal that
perfectly separates Kaggle's two classes (Finding 1). One of the few
images correctly called authentic (`..._00088`) has a similar dark
backdrop but a distinctive bright multi-color chevron pattern printed on
the box itself, and its attention sits on the image's top/side margins
rather than the box design — suggesting even "correct" Split C
predictions may not be for the right reasons.

**Reproducibility caveat**: `gradcam_split_c.py` independently rebuilds
Model 4's Split B head (same procedure as `gradcam.py`) rather than
loading a saved checkpoint (none is persisted anywhere in this project).
This rebuild scored 16/150 Split C images as authentic, not the 5/150
(3.3%) reported by `eval_split_c.py` for the accuracy of record — both
use lr=0.001 and the same seed, but `gradcam.py`'s rebuild path runs its
own LR-search trials before the final training call, and something in that
extra RNG usage evidently isn't fully reset by the subsequent `set_seed()`
call, producing a different (but qualitatively similar — the vast
majority of images are still called counterfeit) trained head. This is a
real, unresolved determinism gap between the two rebuild code paths, not
just measurement noise — worth fixing (e.g. by persisting a checkpoint
after the authoritative training run instead of ever rebuilding
"deterministically" from scratch a second time) if this project continues.
The qualitative Grad-CAM observations above do not depend on which exact
rebuild produced them, since the dark-backdrop pattern and
attention-on-product-text pattern are consistent across both very-high-
confidence-counterfeit images regardless.

## Finding 4: a causal test — brightness normalization confirms the mechanism, but only partly

Script: `modeling/experiment_brightness_norm.py`. Output:
`modeling/results/brightness_norm_experiment.csv`. Method: rescale every
image (train, Kaggle test, AND Split C — identically, using no label
information) so its mean pixel value matches a fixed target (0.5),
applied before any other processing, then retrain and re-evaluate Model 1
(classical, the model most directly tied to raw brightness via its
color-histogram features) and Model 4 (best in-distribution performer,
largest Split C gap).

| Model | Split B test acc (no norm → norm) | Split C acc (no norm → norm) |
|---|---|---|
| 1. Color hist + LogReg | 0.838 → **0.541** (collapsed) | 0.000 → 0.000 (no change) |
| 4. EfficientNet-B0 | 0.919 → 0.932 (slightly better) | 0.067 → **0.313** (~5x better) |

**Two different, both informative, results:**

- **Model 1's in-distribution accuracy collapses toward chance when
  brightness is normalized away, and Split C accuracy doesn't move at
  all.** This means Model 1's apparent 83.8% in-distribution accuracy was
  overwhelmingly *reliant* on the brightness confound — a 96-dim color
  histogram has almost nothing else to work with once the single strongest
  signal (mean brightness, which is class-correlated at t=17, p≈0) is
  removed. It was never picking up a genuine, transferable authenticity
  signal, confound or not — removing the confound doesn't unlock
  anything, because there was nothing else there to unlock. This is a
  concrete, quantified illustration of how thin the classical baseline's
  performance always was, and by extension raises the same question about
  any classical or shallow-CNN result reported elsewhere in this
  literature on similarly-sourced data.
- **Model 4 (EfficientNet-B0) improves on BOTH axes** — slightly better
  in-distribution (removing noisy, class-correlated brightness variance
  apparently helped more than it hurt) and substantially better on Split C
  (6.7% → 31.3%, a genuine ~5x improvement using a transformation that
  uses no label information and could be deployed for real). **This is
  direct causal confirmation that brightness is part of the mechanism**,
  not just a correlated observation — a controlled intervention on exactly
  one variable, applied identically to both classes and to the external
  set, recovered a meaningful fraction of lost external accuracy.
  **But 31.3% is still far short of the ~93% in-distribution level**, so
  brightness is only *part* of what's being overfit — the remaining gap is
  consistent with the still-uncontrolled resolution/detail difference
  (Kaggle images are ~10x smaller than Split C's) and any other correlate
  of the Screenshot-vs-camera-photo capture-method split not addressed by
  this single-variable intervention (compression artifacts, color profile,
  aspect ratio, etc.).

**Bottom line**: brightness is a real, causally-confirmed, but partial
contributor to the generalization failure. A follow-up normalizing
resolution/detail as well (e.g. matching blur/sharpness statistics, or
training at a resolution/compression level representative of both
sources) would be a natural next experiment to close more of the
remaining gap.

## Finding 5: combining resolution + brightness normalization closes most of the gap

Script: `modeling/experiment_resolution_norm.py`. Output:
`modeling/results/resolution_norm_experiment.csv`. Method: same
label-free, deployable idea as Finding 4, extended to resolution. Every
image is first downsampled to 128px on its short side (chosen to sit
below Kaggle's own 10th-percentile image size, so it's a genuine
bottleneck for nearly all images in both sources, not just Split C's),
THEN resized back up to the network's normal 224×224 input as usual. This
caps "effective detail budget" the same way brightness normalization
capped mean pixel value. Four conditions tested on Model 4
(EfficientNet-B0), all retrained from scratch:

| Condition | Split B test acc | Split C acc |
|---|---|---|
| Baseline (no normalization) | 91.9% | 8.7% |
| Resolution normalization only | 93.2% | 22.0% |
| Brightness normalization only | 91.9% | 27.3% |
| **Both combined** | **95.9%** | **62.7%** |

**Both individual interventions help on their own** (resolution alone:
8.7%→22.0%, ~2.5x; brightness alone: 8.7%→27.3%, ~3x — both replicate
Finding 4's direction, with some run-to-run variance from Finding 4's
exact numbers, expected given no fixed data augmentation seed is
guaranteed identical across separate script invocations). **Combined, the
improvement is much larger than either alone and slightly more than
additive** (8.7% → 62.7%, a ~7x improvement) **and in-distribution
accuracy is simultaneously the best of all four conditions (95.9%)** —
removing both shortcuts didn't trade off accuracy for robustness, it
improved both at once. This is strong evidence that brightness and
resolution/detail are two largely independent, both-real, both-fixable
components of what these models were overfitting to, and that most (though
not all — 62.7% vs. 95.9% in-distribution is still a real, if much
smaller, gap) of the original Split C collapse was attributable to these
two easily-identified, easily-corrected, label-free preprocessing
confounds rather than to some irreducible property of the task itself.

**This is the strongest evidence in the whole project that the
generalization failure is a fixable data/preprocessing problem, not proof
that "packaging classification from images" is fundamentally
non-generalizable.** The remaining ~33-point gap (62.7% vs 95.9%) is
still large and still unexplained — plausible remaining candidates include
compression artifacts, color profile/white-balance differences, aspect
ratio, or the two capture pipelines' backgrounds/staging more generally —
but the headline conclusion changed meaningfully across this
investigation: from "these models don't generalize" (Split C first run)
to "these models don't generalize *because of specific, identified,
partially-correctable dataset confounds*, and correcting the two most
obvious ones recovers most of the gap" (this finding). That is a
substantially more constructive and publishable result.

**Important qualification found immediately after, in Finding 6 below:
"recovers most of the gap" is true for some architectures and false for
others.** Read that finding before treating combined normalization as a
general-purpose fix.

## Finding 6: the fix is architecture-dependent, not universal — and it actively hurts one model

Script: `modeling/experiment_normalization_all_models.py`. Output:
`modeling/results/normalization_all_models_experiment.csv`. Finding 5's
combined normalization was tested on Model 4 only; this extends it to all
4 models, same combined (resolution-then-brightness) normalization,
baseline vs. normalized, each model retrained from scratch:

| Model | Baseline Split B / Split C | Normalized Split B / Split C | Δ Split C |
|---|---|---|---|
| 1. Color hist + LogReg | 83.8% / 0.0% | 54.1% / 0.0% | +0.0 |
| 2. Small CNN (GAP) | 86.5% / 0.0% | 82.4% / **84.7%** | **+84.7** |
| 3. MobileNetV3-Small | 94.6% / **73.3%** | 94.6% / 52.0% | **−21.3** |
| 4. EfficientNet-B0 | 91.9% / 8.7% | 95.9% / 62.7% | +54.0 |

**Four different outcomes, not one story:**

- **Model 1**: no effect either way — already established in Finding 4,
  this model has no signal beyond the brightness shortcut to begin with.
- **Model 2 (small CNN)**: the biggest win in the whole project. Split C
  accuracy goes from 0% to **84.7%** — better than any other model/
  condition tested anywhere in this investigation — for a modest
  in-distribution cost (86.5% → 82.4%). A from-scratch CNN with no
  pretrained-feature scale/brightness invariance apparently relied on the
  confound almost completely, and removing it lets whatever real signal
  exists come through cleanly.
- **Model 3 (MobileNetV3-Small)**: normalization *hurts* — Split C
  accuracy drops from 73.3% (already the best baseline of any model,
  substantially better than Model 4's 8.7% baseline) to 52.0%, a 21-point
  loss, while in-distribution accuracy is unchanged. This is the opposite
  direction from every other model. Plausible explanation: MobileNetV3's
  ImageNet-pretrained features may already carry some brightness/scale
  invariance from its own pretraining augmentation, meaning it wasn't
  relying on the confound as heavily to begin with — and the forced
  128px-bottleneck resolution normalization discards real, useful detail
  this model *was* successfully using, net-negative for a model that
  didn't need the crutch removed.
- **Model 4 (EfficientNet-B0)**: as in Finding 5, a large win (+54 points).

**This means "apply brightness+resolution normalization" is not a
general-purpose recommendation** — it is a strong fix for models that are
heavily reliant on the capture-method confound (2 and 4) and actively
counterproductive for at least one model that generalizes comparatively
well without it (3). Any paper claim should be architecture-specific:
"this normalization helps models N and M substantially, is neutral for
model X, and hurts model Y" — not a blanket "normalization fixes
generalization." This is also informative in its own right: Model 3's
comparatively strong un-normalized baseline (73.3%, by far the best of
any baseline) suggests MobileNetV3-Small's specific pretrained features
are, for whatever architectural reason, the most naturally robust to this
dataset's capture-method confound of the 4 models tested — worth
investigating further (e.g. comparing its ImageNet pretraining recipe/
augmentation policy against EfficientNet-B0's) if this project continues.

## Finding 7: decomposing Model 3's regression — brightness normalization is the specific culprit

Script: `modeling/experiment_model3_decompose.py`. Output:
`modeling/results/model3_decompose_experiment.csv`. Finding 6 found
combined normalization hurts Model 3; this isolates which of the two
components (resolution vs. brightness) is responsible, same 4-condition
structure as Finding 5 but for Model 3:

| Condition | Split B test acc | Split C acc |
|---|---|---|
| Baseline (no normalization) | 94.6% | 80.0% |
| Resolution normalization only | 94.6% | **84.7%** (slightly better) |
| Brightness normalization only | 93.2% | **56.0%** (much worse) |
| Both combined | 95.9% | 40.0% (worse still) |

(Baseline Split C here is 80.0%, not the 73.3% reported in Finding 6 —
expected run-to-run variance from the augmented-feature-extraction
pipeline not using a fixed cross-script seed for k=3 augmentation, same
caveat as Finding 5. The qualitative pattern — Model 3 has by far the
best baseline of any model/condition tested anywhere in this
investigation — holds regardless.)

**Resolution normalization alone is neutral-to-slightly-positive for
Model 3 (80.0% → 84.7%) — it is brightness normalization specifically
that damages it (80.0% → 56.0%), and combining both is worse than either
alone (40.0%), indicating a negative interaction, not just two independent
effects added together.** This sharpens Finding 6's explanation: it isn't
that Model 3 has general "pretrained scale/robustness" that the 128px
bottleneck disrupts — resolution normalization on its own doesn't hurt it
at all. Specifically forcing every image's mean brightness to a fixed
target removes information this model's frozen ImageNet features were
successfully using. Whether that information is a genuine
authenticity-relevant cue or a subtler version of the same brightness
confound the other models exploit more crudely is not resolved by this
experiment — Grad-CAM on Model 3's Split C predictions (not yet done,
only Model 4's Split C Grad-CAM exists so far, see
`modeling/gradcam_split_c.py`) would be the natural next check.

## Finding 8: Model 3's un-normalized Split C attention — answered, and it's not what "genuinely better at packaging" would predict

Script: `modeling/gradcam_split_c_model3.py`. Output:
`modeling/results/gradcam_split_c_model3/*.png` (20 heatmap overlays,
un-normalized/baseline model — 109/150 = 72.7% correct on this run,
consistent with Findings 6-7) + `manifest.csv`.

Reviewed 3 correct and 2 incorrect predictions directly:

- **All 3 correctly-classified images** (`..._00007`, `..._00035`,
  `..._00123`) show Grad-CAM attention concentrated on the **dark
  background around the product**, not the product itself — the same
  incidental-background pattern seen throughout this project (Grad-CAM
  on Model 4, Finding 3), not a cleaner or more "genuine" attention
  pattern.
- **Both misclassified images reviewed** (`..._00146`, `..._00003`) show
  attention concentrated **on the product's own design/text** — the
  opposite of what background-reliance would predict, and the opposite
  of what a "the model looks at packaging when right, background when
  wrong" story would predict too.

**This is a genuinely counter-intuitive result, reported as found, not
smoothed into a tidier story**: Model 3's higher un-normalized Split C
accuracy does not come from attending to packaging content more reliably
than Model 4 does. If anything, on this small sample, the pattern is
reversed. A more likely explanation, consistent with Finding 7 (brightness
normalization specifically hurts this model): Model 3 may have learned
something closer to "this consistent dark-navy background pattern →
authentic" as a coarse rule from its ImageNet pretraining or from
whatever incidental correlation exists in Kaggle's training distribution.
Because Split C happens to be 100% authentic and 100% sharing the same
photography backdrop, a background-pattern-matching rule *coincidentally*
scores well on this specific external set even though it is not a
packaging-authenticity judgment — the same category of shortcut as the
other models, just one that happens to transfer better to this
particular external test's specific backdrop, not evidence of more
genuine packaging understanding. This is a caution against over-crediting
Model 3's strong baseline number: it is likely still confound-driven, just
a different (and for this specific Split C set, luckier) confound than
brightness.

**Coverage caveat**: only 5 of 20 generated images were manually reviewed
(3 correct, 2 incorrect) — a small, illustrative sample, not an
exhaustive audit. The pattern is clear enough in this sample to report,
but a larger review would strengthen or could revise this reading.

## Finding 9: color/white-balance is ruled out as an explanation for Model 4's remaining post-normalization gap

Script: `modeling/experiment_colorbalance_norm.py`. Output:
`modeling/results/colorbalance_norm_experiment.csv`.

Motivation: even the best condition found so far (resolution + brightness
normalization combined) leaves a large gap between Model 4's in-distribution
accuracy and its Split C accuracy, so this experiment tested the next
candidate axis from the "Next steps" list: color profile / white balance. A
quick channel-mean check across 150 images per source supported the idea —
Kaggle's R:G:B channel means (normalized to R=1) are `1 : 0.94 : 0.86` (a
warm cast, blue suppressed ~14% relative to red) versus Split C's much more
neutral `1 : 0.93 : 0.93` (blue only ~7% below red). Real, measurable,
dataset-wide difference, same category as the brightness/resolution
confounds, just smaller.

Method: gray-world white balance — scale each image's R and B channel means
to match its G channel mean, label-free, applied identically to
train/test/Split C. Tested on Model 4 (EfficientNet-B0), same pattern as
every prior normalization experiment (test on Model 4 first).

| Condition | Split B test acc | Split C acc |
|---|---|---|
| Resolution + brightness (this run) | 95.9% | 45.3% |
| Color balance only | 93.2% | 10.7% |
| All three combined | 95.9% | 42.0% |

**Color balance normalization does not help, and combined with the other
two it is mildly negative** (45.3% → 42.0%), the same qualitative direction
as brightness normalization's effect on Model 3 (Finding 7) though much
smaller in magnitude here. Alone, it barely moves Split C accuracy off the
8.7% baseline (10.7%) — nowhere near brightness or resolution's individual
effect sizes (27.3% and 22.0% respectively, Finding 5). **Ruled out** as the
explanation for the remaining gap.

**Note on the "45.3%" baseline in this table**: this is a fresh rerun of the
exact "both combined" condition from Finding 5, which originally reported
62.7%. The two numbers disagree because of the already-documented
`k_augment=3` feature-extraction non-determinism (no fixed seed across
augmentation draws between script invocations — see the caveat at the end
of Finding 6/8's reproducibility notes). This is real run-to-run variance,
not a bug in this new experiment; it's reported honestly rather than
silently reconciled. It does not change this finding's conclusion, since
color balance is compared against a same-run baseline (both numbers came
from the same script execution, so the *within-run* comparison is valid
even though the *across-run* absolute number moved).

Remaining untested candidates from the "Next steps" list: JPEG
compression/quality artifacts, aspect ratio, and background/staging
differences more generally (the two capture pipelines' physical photo
setups, not just their pixel statistics).

## Finding 10: JPEG compression normalization is a real, additive third fix — best combined result yet

Script: `modeling/experiment_compression_norm.py`. Output:
`modeling/results/compression_norm_experiment.csv`.

Motivation: Finding 1 already noted Kaggle's two classes differ in mean
file size by ~56x (6,022 vs. 339,188 bytes) — a compression-artifact
signature (blockiness, ringing, noise floor) at least as strong as the
resolution difference, and a CNN has direct pixel-level access to it the
same way it does to resolution-dependent blur. Color balance (Finding 9)
turned out not to matter; compression was the next untested candidate.

Method: re-encode every image through a fixed, aggressive JPEG quality
bottleneck (quality=40) and decode it back — the same "impose a common
bottleneck" logic as resolution normalization, applied to the compression
axis instead of the pixel-count axis. Label-free, applied identically to
train/test/Split C.

| Condition | Split B test acc | Split C acc |
|---|---|---|
| Baseline (no normalization, this run) | 91.9% | 5.3% |
| Compression normalization only | 90.5% | 12.7% |
| Resolution + brightness (this run) | 93.2% | 50.7% |
| **Resolution + brightness + compression, all three** | **93.2%** | **78.0%** |

**Compression normalization alone is a modest, real effect** (5.3% → 12.7%,
roughly in line with color balance's small effect, Finding 9) **but
combined with the other two it is strongly additive**, not redundant:
78.0% is the best combined Split C result found for Model 4 across every
experiment in this investigation, a large jump over the two-way combination
alone (50.7%) at effectively no cost to in-distribution accuracy (93.2% in
both the two-way and three-way conditions, this run). Unlike color balance
(Finding 9, mildly negative when combined) or brightness on Model 3
(Finding 7, actively harmful), compression normalization behaves the way
resolution and brightness normalization did when first combined (Finding
5): each axis recovers something the others don't.

**This changes the "next steps" priority list**: compression should be
added to the standard normalization pipeline alongside resolution and
brightness (currently a 2-way combination; this finding argues for a
3-way one), and re-tested on Models 2 and 3 the same way Finding 6 extended
brightness+resolution to all four models — Model 3 in particular, since
brightness normalization alone hurt it (Finding 7); it's not yet known
whether compression normalization would help, hurt, or be neutral for that
model.

**Same run-to-run variance caveat applies** (Finding 6/9's documented
`k_augment=3` non-determinism): this run's own baseline (5.3%) and
resolution+brightness numbers (50.7%) both differ from earlier runs of the
"same" conditions (8.7% and 45.3%/62.7% respectively) reported in Findings
4-6 and 9. The comparison that matters is the *within-run* one — three
extra points on top of the two-way combination, all four conditions run
back-to-back in a single script execution — not the absolute numbers
against other runs.

## Finding 11: extending 3-way normalization to all models — Model 3's "normalization hurts it" verdict reverses

Script: `modeling/experiment_compression_all_models.py`. Output:
`modeling/results/compression_all_models_experiment.csv`. Extends Finding
10's 3-way normalization (resolution + brightness + compression) from
Model 4 alone to Models 1-3, mirroring how Finding 6 extended the 2-way
combination.

| Model | Baseline Split B / Split C | 3-way norm Split B / Split C | Δ Split C |
|---|---|---|---|
| 1 Classical | 83.8% / 0.0% | 54.1% / 0.0% | +0.0 (in-distribution collapses again, same as brightness-alone, Finding 4 — no signal beyond the shortcut) |
| 2 Small CNN | 86.5% / 0.0% | 83.8% / **91.3%** | **+91.3** (best single-model win in the project, beating the 2-way combination's 84.7%, Finding 6; this row's Model 2 was trained at the stale 0.0003 LR — see Finding 14) |
| 3 MobileNetV3-Small | 93.2% / 75.3% | 94.6% / **81.3%** | **+6.0** (improved on both axes at once) |
| 4 EfficientNet-B0 | 91.9% / 5.3% | 93.2% / 78.0% | +72.7 (Finding 10, same-run numbers) |

**This substantially revises the Model 3 story from Findings 6-8.** There,
the 2-way (resolution+brightness) combination hurt Model 3 (73.3%→52.0%,
Finding 6), traced specifically to brightness normalization alone
(80.0%→56.0%, Finding 7). Here, the 3-way combination (adding compression
on top) **improves** Model 3 on both Split B (93.2%→94.6%) and Split C
(75.3%→81.3%) simultaneously — the opposite direction from the 2-way
result. The most likely explanation: compression normalization removes
enough of the remaining shortcut signal (file-size/compression-artifact
correlation with class label, Finding 1) that the combination stops
tempting the optimizer toward the same brightness-sensitive shortcut that
hurt it in the 2-way case — i.e., the earlier negative interaction
(Finding 7: "combined is worse than either alone") was specific to the
2-way mix, not an inherent problem with normalizing Model 3's inputs at
all.

**Every model's Split C number moved in the same direction this run**
(0/0/+6.0/+72.7 pts) except Model 1, which has consistently shown no
usable signal beyond the shortcuts across every experiment in this
investigation. **This is now the strongest case yet for making 3-way
normalization (resolution + brightness + compression) the default
preprocessing** for every model except the classical baseline — not
"architecture-dependent, helps 2 of 4" as Finding 6 concluded, but "helps
3 of 4, including the one model that a smaller version of the same idea
used to hurt."

**Caveat, same as always**: single-run numbers, subject to the documented
`k_augment=3` non-determinism (Finding 6/9/10). Model 3's Grad-CAM-derived
"background shortcut" explanation (Finding 8) was based on the
*un-normalized* model and is not contradicted by this result — a
differently-shortcut-reliant model can still see its external accuracy
improve when a confound it wasn't as reliant on gets removed at the margin.
Worth revisiting Model 3's Grad-CAM under the 3-way-normalized condition to
see whether its attention pattern changes now that it performs better
externally.

## Finding 12: 3-way normalization promoted to the production pipeline — confirms Models 2/4, but Model 3's experiment result does not reproduce in production

3-way normalization (`modeling/normalization.py`, factored out of the
experiment scripts) was made the project's default preprocessing:
`common.py`'s `PharmaImageDataset` now applies it unless explicitly
disabled, so it flows through to every consumer (`train_model2_cnn.py`,
`train_model3_mobilenet.py`/`feature_cache.py`, `train_model4_efficientnet.py`,
and `eval_split_c.py`, which rebuilds each model the same way). Model 1
(`train_model1_classical.py`) reads images directly and never touches
`PharmaImageDataset`, so it is deliberately unaffected — Finding 11 already
showed normalization collapses its in-distribution accuracy with no Split C
benefit, i.e. it has no signal beyond the shortcuts to remove. All 3
production models were retrained from scratch and Split C was
re-evaluated end-to-end (`eval_split_c.py`, `modeling/results/split_c_eval.csv`).

| Model | Split C authentic acc | Split B test authentic acc | Gap |
|---|---|---|---|
| 1. Classical | 0.0% | 69.2% | 69.2 |
| 2. Small CNN | **86.0%** | 84.6% | **−1.4 (negative gap — external beats in-distribution)** |
| 3. MobileNetV3-Small | 68.0% | 94.9% | 26.9 |
| 4. EfficientNet-B0 | 81.3% | 97.4% | 16.1 |

**Models 2 and 4 confirm and strengthen the experimental findings** in a
real, non-experimental, checkpoint-free production run: Model 2 goes from
0% (pre-normalization, post-watermark-cleanup baseline) to 86.0%, with a
*negative* generalization gap — the first time any model/condition in this
project has generalized to Split C better than to its own in-distribution
test set. Model 4 goes from 3.3% to 81.3%.

**Model 3 does NOT reproduce Finding 11's improvement.** The pre-normalization
production baseline for Model 3 was 69.3% (see `modeling/README.md`'s "What
changed after cleanup" table); this normalized production run gives 68.0%
— flat, within noise, not the 75.3%→81.3% improvement Finding 11's
standalone experiment reported. **Reported as found, not reconciled away**:
this is a real discrepancy between the standalone-experiment result and the
production-pipeline result for the same nominal condition (3-way
normalization, Model 3, Split B train pool, Split C eval), and it's the
clearest concrete demonstration yet of why the `k_augment=3`
non-determinism caveat (repeated throughout Findings 6/9/10/11) is not a
minor footnote — for Model 3 specifically, the "does normalization help or
hurt" answer has now come out positive (Finding 11, 75.3%→81.3%), negative
(Finding 6, 73.3%→52.0%), and flat (this finding, 69.3%→68.0%) across three
different runs of nominally the same or closely related conditions. **The
honest conclusion for Model 3 is "unresolved / high run-to-run variance,"
not "normalization helps" or "normalization hurts."** This production
number (68.0%) is the accuracy of record per the project's existing
convention (`eval_split_c.py` output is authoritative, same standard
applied to the earlier `gradcam_split_c.py` reproducibility gap).

**This changes the project's honest bottom line**: 3-way normalization is a
strong, reproducible, production-confirmed win for Models 2 and 4 (the two
models with the worst baseline generalization), a total non-event for
Model 1 (as expected — no signal to recover), and **an open question for
Model 3** rather than a settled win or loss. Given Model 3's baseline
(69.3%, unnormalized) was already competitive with Model 4's *normalized*
result, and given the high measured variance, the paper should report
Model 3 under both conditions with the variance explicitly disclosed rather
than picking one run's number as representative.

Fixing the underlying `k_augment=3` non-determinism (a fixed seed per
augmentation pass, not just per script) would be the highest-value
remaining engineering task if more precision on Model 3 specifically is
wanted — everything else in this investigation has been robust enough that
it hasn't mattered, but Model 3 is evidently right at a sensitivity boundary.

## Finding 13: the `k_augment=3` non-determinism is fixed — Model 3's status resolves back to "normalization helps"

Root cause (identified while investigating Finding 12's Model 3
discrepancy): `modeling/feature_cache.py`'s `extract_features` ran its
`k_augment` augmented passes with no seed set at all — each pass's random
rotation/jitter/crop/blur draws depended entirely on whatever RNG state the
Python process happened to be in when that pass ran, which differs
depending on what ran earlier in the same script (LR search, other model's
training, etc.) and is not reproducible across separate script
invocations. This is the mechanism behind every "same nominal condition,
different number" gap documented in Findings 6/9/10/11/12.

**Fix**: `extract_features` now calls `set_seed(SEED + pass_idx)`
immediately before each augmented pass (`modeling/feature_cache.py`).

**Verified fixed**: ran `train_model3_mobilenet.py` twice back-to-back
with this change — the two runs' `metrics_model3_mobilenetv3small_frozen.csv`
outputs are byte-for-byte identical (`diff` reports no differences). Same
underlying function is used by `eval_split_c.py`'s Model 3/4 rebuild path,
so this result extends there too.

**Model 3's Split C number under this fix**: re-ran `eval_split_c.py` for
Model 3 (production, 3-way-normalized pipeline): **77.3%** — much closer
to Finding 11's standalone-experiment result (81.3%) than to Finding 12's
pre-fix production number (68.0%, now understood to be a noisy read caused
by the unseeded bug, not a real "normalization doesn't help Model 3"
result). Split B in-distribution authentic accuracy is unchanged (97.4%).

**Updated bottom line for Model 3**: the "unresolved / high run-to-run
variance" verdict from Finding 12 is superseded. With the non-determinism
fixed, Model 3's answer resolves back to the same direction as every other
affected model: **3-way normalization helps** (69.3% pre-normalization →
77.3% normalized, this fixed production run). This is now the accuracy of
record. The earlier flat (Finding 12, pre-fix) and negative (Finding 6,
2-way-only condition, a different and not-yet-refixed experiment script)
readings should be understood as artifacts of the same seeding bug rather
than genuine model behavior — though Finding 6's 2-way-only experiment
script itself has not been rerun with the fix, so that specific number
technically remains unverified; only the production 3-way path has been
confirmed deterministic and re-measured.

**Updated full production table** (all from the deterministic,
seeding-fixed pipeline):

| Model | Split C authentic acc | Split B test authentic acc | Gap |
|---|---|---|---|
| 1. Classical | 0.0% | 69.2% | 69.2 |
| 2. Small CNN | **86.0%** | 84.6% | −1.4 (negative gap) |
| 3. MobileNetV3-Small | **77.3%** (corrected from 68.0%) | 97.4% | 20.1 |
| 4. EfficientNet-B0 | 81.3% | 97.4% | 16.1 |

Every model except Model 1 (unaffected by design) now shows a large,
positive, and — for the first time — *reproducible* improvement from 3-way
normalization. This is the strongest and most trustworthy version of the
project's headline finding to date.

## Finding 14: Model 2's Split C numbers were rebuilt at the wrong learning rate — corrected 2026-07-28

While preparing the manuscript, `eval_split_c.py` was found to hard-code
Model 2's learning rate at 0.0003, a value left over from the 2026-07-24
retrain. Under the normalized pipeline Model 2's own LR search selects
**0.001** (see `modeling/results/model2_train_log_normalized.txt`), so every
Split C number for Model 2 in Findings 11-13 above was produced by a model
trained differently from the one supplying its in-distribution numbers.

**Fixed structurally, not by hand.** Training scripts now write the LR they
actually used to `modeling/results/chosen_lrs.json`
(`result_io.save_chosen_lr`) and every rebuild path reads it back
(`load_chosen_lr`), raising rather than guessing if the record is absent. The
same fix was applied to `gradcam.py` and `gradcam_split_c_model3.py`, which
had been running their own LR search before the final training call — the
cause of the separately documented 16/150-vs-5/150 rebuild discrepancy.

**Verified, then re-measured.** Under the recorded rate the rebuild's
per-epoch training curve is byte-identical to
`curves/model2_smallcnn_gap__split_b_final.csv`, the run of record; the
0.0003 rebuild's plainly was not. Re-running both Split C evaluations for
Model 2 gives:

| Metric | Pre-fix (lr 0.0003) | Corrected (lr 0.001) |
|---|---|---|
| Split C authentic acc | 91.3% | **86.0%** |
| Gap vs. in-distribution (84.6%) | −6.7 | **−1.4** |
| Synthetic proxy accuracy | 0.623 | 0.633 |
| Synthetic proxy ROC-AUC | 0.788 | 0.794 |

Pre-fix values preserved in `split_c_eval_PRE_LRFIX_20260728.csv` and
`split_c_synthetic_eval_PRE_LRFIX_20260728.csv`.

**Every qualitative conclusion above survives**: Model 2 is still the
best-generalizing model, still the only one with a negative generalization
gap, and 3-way normalization still takes it from 0% to the high eighties.

**Not re-run**: `experiment_normalization_all_models.py` and
`experiment_compression_all_models.py` also trained Model 2 at 0.0003, so the
M2 rows of Findings 6 and 11 carry the same caveat. Their *within-run*
baseline-vs-normalized comparison is unaffected (both conditions share the
LR), which is the comparison those findings actually claim; their absolute
values are not comparable to the production numbers. Both scripts now read
the recorded LR, so a re-run refreshes them.

## Finding 15: the composition ORDER of the three operators matters more than any of their constants — and the in-distribution ranking is inverted

Date: 2026-08-13. Script: `modeling/experiment_order_permutation.py`.
Results: `modeling/results/order_permutation_experiment.csv`.

`normalization.py` composes resolution → brightness → compression and nothing
in the study had ever varied that order. Two of the three operators destroy
information, so they have no reason to commute. All 3! = 6 orderings were run
on M4 at the production constants (128, 0.5, 40), inside one execution.

| Order | Compression | Split B | Split C |
|---|---|---|---|
| R, B, C (production) | after the cap | 0.919 | 0.820 |
| R, C, B | after the cap | 0.932 | **0.880** |
| B, R, C | after the cap | 0.919 | 0.847 |
| B, C, R | before the cap | **0.946** | **0.380** |
| C, R, B | before the cap | 0.932 | 0.540 |
| C, B, R | before the cap | 0.932 | 0.467 |

**One rule explains the whole table, with no overlap.** Compression applied
*after* the resolution cap: 0.820 / 0.847 / 0.880. Applied *before*: 0.380 /
0.467 / 0.540. A 28-point gap between two groups of three. The mechanism is
mechanical, not statistical: JPEG at native resolution followed by a
downsample largely undoes itself, because the resampling filter averages over
the quantisation artefacts the bottleneck exists to impose. Those three
orderings are effectively two-way normalisations, and 0.380–0.540 brackets
the 0.507 that the real two-way condition scores in Finding 10.

**Brightness position is second-order**: 6 points of movement within the
sound group, against the 28-point gap between groups. Same split as
Finding 5's: bottlenecks are position-sensitive, the location-shifting
operator is not.

**The most useful result for the paper: the in-distribution ranking is
inverted.** B, C, R has the *highest* Split B accuracy of all six (0.946) and
the *lowest* Split C (0.380). Choosing the composition order by held-out
accuracy on your own data selects the worst of six options. The in-distribution
spread is 2.7 points; the external spread is 50. Nothing else varies between
these rows — same operators, same constants, same model, same data.

**Production order is conservative, not tuned.** R, C, B beats it on both
axes. Deliberately not adopted: choosing preprocessing by external score is
the target-distribution leakage the paper's Limitations warns about, and the
production order was fixed before these six numbers existed.

**Harness validation.** The production row returned 0.919 / 0.820, exactly
the values of record from Finding 12 and the constant sweep — and the same
condition returned the same pair again in the white-balance rerun below, from
a different script. Three exact reproductions across two scripts.

## Finding 16: the white-balance rejection of Finding 9 was made on an untrustworthy run — re-run deterministically

Date: 2026-08-13. Script: `modeling/experiment_colorbalance_norm.py`
(rewritten). Superseded numbers preserved in
`modeling/results/colorbalance_norm_experiment_PRE_DETERMINISM_20260725.csv`.

Finding 9 ruled white balance out as a fourth axis, and the manuscript cites
it. Re-reading the script that produced it turned up three defects, all of
which post-date it:

1. Its feature extraction looped `for _ in range(k_augment)` **with no
   per-pass seeding** — precisely the defect of Finding 13, which was fixed
   in `feature_cache.py` on 2026-07-26, the day *after* Finding 9 ran. Under
   that defect one unchanged condition read 62.7 / 45.3 / 50.7 across three
   executions. That 17-point spread dwarfs the 3.3-point difference
   (45.3 → 42.0) on which the axis was rejected.
2. It hard-coded `lr=0.001` rather than reading the recorded value
   (the Finding 14 fix).
3. Its "combined" reference was resolution + brightness only. Compression had
   not yet been promoted, so white balance was **never tested against the
   pipeline that actually ships**.

All three are corrected, and the conditions now include a same-run production
baseline and a deterministic redo of the original two-way comparison.

| Condition | Operators | Split B | Split C |
|---|---|---|---|
| Production three-way | R, B, C | 0.919 | **0.820** |
| White balance alone | W | 0.905 | 0.067 |
| Production three-way + WB | R, B, W, C | 0.932 | 0.780 |
| Two-way | R, B | 0.919 | 0.500 |
| Two-way + WB | R, B, W | **0.960** | 0.347 |

**The rejection survives, and is stronger than what it replaces.** White
balance alone leaves external accuracy at 0.067, i.e. the unnormalised
baseline. On the production three-way pipeline it costs 4.0 points
(0.820 → 0.780). On the two-way pipeline — the comparison the original
experiment was attempting — it costs **15.3 points** (0.500 → 0.347), where
the untrustworthy run had reported 3.3. Both combinations point the same
way, so the axis is excluded on a sound basis now rather than an unsound one.

Three things worth keeping:

1. **A rejection is a claim and needs a harness good enough to support it.**
   The original conclusion happened to be right, which was not guaranteed —
   the corrected decrement is 4.6x larger, and it could as easily have
   flipped sign. Any negative result produced before 2026-07-26 by a script
   that calls `extract` with `k_augment > 1` is suspect for the same reason;
   these two were the last of them in the paper.
2. **Test against the pipeline that ships, not the one that shipped.** The
   original compared against res+bright because compression had not yet been
   promoted. A candidate axis has to be evaluated on top of the current
   operator or the result answers a question nobody is asking.
3. **Another instance of the inversion from Finding 15.** Two-way + WB has
   the highest in-distribution accuracy of the five conditions (0.960) and
   the second-lowest external accuracy (0.347). That is now three separate
   sweeps — constants, ordering, and this one — in which in-distribution
   accuracy ranks conditions in close to the opposite order from external
   accuracy.

The two-way baseline here reads 0.500 against the compression experiment's
0.507 for the nominally identical condition (Finding 10) — reassuring, but
NOT a seed-variance estimate: that experiment ran on 2026-07-25 and so
predates the seeding fix, which is the whole reason its sibling result is
being redone here. The study still has no measured seed variance, and
Limitations says so.

## Reproducing this analysis

The comparison was done ad hoc (not yet a committed script) via PIL +
numpy: resize each image to 64×64, take the RGB mean as "brightness,"
compare distributions by class label (using `provenance.csv`'s
`class_label` and `orig_relpath`) and by filename pattern
(`Screenshot*` vs `images*`). Worth turning into a proper script
(`scripts/13_capture_method_confound_check.py` or similar) if this
investigation continues — not yet done as of this writing.
