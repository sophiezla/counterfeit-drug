# Modeling

Status: **all 4 models trained and evaluated under Split A, Split B, and
Split C, TWICE** (2026-07-23 and again 2026-07-24 after a full data
cleanup). McNemar's tests, Grad-CAM (Part 4.5, Model 4), and a cross-model
error analysis (Part 4.6) are done for both rounds. **Read the Split C
section before trusting any headline accuracy number** — it's the most
important finding this modeling pass produced, and it survived the
retrain in a way that makes the whole project's central claim stronger,
not weaker.

**This is the retrain, not the original run.** The first modeling pass
(2026-07-23) was built on a 564-image Kaggle pool that a subsequent full
manual review (`data/metadata/modality_review_findings.md`) found to
contain 47 watermark-confound images (100% authentic-labeled — a real,
checked, class-correlated shortcut), a browser screenshot, several
stock-render images, a loose-pills photo, and 4 syrup-bottle photos with
no packaging in frame. All 54 were removed, landing at **510 images** (a
9.6% reduction) for this retrain. The numbers below are entirely from the
510-image pool; the original run's numbers are preserved in git history /
prior conversation only, not repeated here except where the *comparison
itself* is the finding (see "What changed after cleanup" below).

## Scope of this pass

Per `data/README.md`, Splits A and B use the Kaggle "Fake vs Real Medicine"
pool only (510 images post-dedup and post-manual-review-cleanup — see
`data/metadata/modality_review_findings.md`). **Split C is authentic-only**
(150
images, Mendeley "Mobile-Captured Pharmaceutical Medication Packages",
programmatically verified independent of the training pool — see
`data/metadata/split_c_independence_report.txt`) rather than the plan's
originally-envisioned two-class external test, because no independent
counterfeit-labeled 3rd source was found (see data/README.md "Open items"
and "Split C source" below for what was actually tried). It measures each
model's false-positive rate on authentic packaging from a source it never
trained on — different country, different photographers, different camera
hardware, different backdrop protocol.

## Environment

- PyTorch 2.7.1 (CPU only — no CUDA available in this environment).
- Fixed seed 42 everywhere randomness is used (data shuffling, model init,
  DataLoader shuffling, bootstrap resampling).
- Batch size 32, Adam optimizer, early stopping on val loss (patience 4,
  min_delta=1e-3 — added after Model 3's frozen-backbone linear head was
  observed running 46+ epochs on noise-level, sub-1e-3 val-loss "improvements"
  that never tripped a naive patience counter), documented per-model LR
  search (3-value grid, 5 epochs each, reused for the full run) — plan
  Part 3.2.
- Augmentation (train split only): rotation ±12°, brightness/contrast
  jitter, mild RandomResizedCrop (scale 0.85-1.0), slight Gaussian blur, **no
  flip** (would mirror printed packaging text) — plan Part 2.7. Applied
  identically to Models 2/3/4; Model 1 (color histogram) intentionally
  excluded, see its script docstring for why.
- Class balancing: inverse-frequency class weighting in the loss (plan Part
  2.6: class-weighted, not oversampled).

## Models

| # | Model | Trainable params | Frozen params | Script |
|---|---|---|---|---|
| 1 | Color histogram (96-dim RGB) + Logistic Regression | **97** | — | `train_model1_classical.py` |
| 2 | Small CNN, 3 conv blocks (16→32→64) + GAP head (avoids a flatten→dense(128) head) | **23,938** | — | `train_model2_cnn.py` |
| 3 | MobileNetV3-Small, frozen ImageNet backbone + GAP head | 1,154 | 927,008 | `train_model3_mobilenet.py` |
| 4 | EfficientNet-B0, frozen ImageNet backbone + GAP head | 2,562 | 4,007,548 | `train_model4_efficientnet.py` |

**Two counts in this table were wrong until 2026-07-28 and are now measured,
not estimated** (`paper/scripts/benchmark_cost.py` prints them):

- Model 1 was listed as "~194 (96 features × 2 classes)". scikit-learn's
  *binary* `LogisticRegression` stores a single weight vector, so it is
  96 coefficients + 1 intercept = **97** learned parameters, not 194.
- Model 2 was listed as "~30K". Summing the actual module is **23,938**
  (432+16 / 4,608+32 / 18,432+64 conv weights+biases, 16+16 / 32+32 / 64+64
  BatchNorm, 128+2 head). A flatten→dense(128) head on the same trunk would
  cost roughly 6.4 M parameters, so the GAP head is a **374×** reduction,
  not a 300× one.

## How to reproduce

```bash
cd pharmavision
python modeling/train_model1_classical.py
python modeling/train_model2_cnn.py
python modeling/train_model3_mobilenet.py
python modeling/train_model4_efficientnet.py
python modeling/aggregate_results.py
python modeling/gradcam.py           # Grad-CAM heatmaps for Model 4 (Part 4.5)

# Split C (external generalization, Part 4.3) -- run from the pharmavision/ root:
python scripts/06_download_mendeley_split_c.py       # downloads ~248MB, one-time
python scripts/07_verify_split_c_independence.py     # confirms non-duplication before trusting it
python modeling/eval_split_c.py                      # retrains + evaluates all 4 models on it

# Synthetic counterfeit-proxy Split C (authentic-only Split C has no
# counterfeit class -- see data/metadata/synthetic_counterfeit_findings.md):
python scripts/17_apply_synthetic_review.py          # builds split_c_synthetic_provenance.csv
python modeling/eval_split_c_synthetic.py            # retrains + evaluates all 4 models on it
```

`eval_split_c.py` and `eval_split_c_synthetic.py` both checkpoint
incrementally to their respective results CSVs after each model
(re-running skips models already recorded) — useful given retraining 4
models back-to-back can take several minutes. Their output files
(`split_c_eval.csv` vs. `split_c_synthetic_eval.csv`) are kept deliberately
separate and must never be merged in reporting — one measures the
authentic-class false-positive rate on real external photos, the other
measures discrimination against a synthetic perturbation-style proxy for
counterfeit recall.

Error analysis (Part 4.6) reads the already-written prediction CSVs directly
rather than a separate script — see `modeling/results/error_analysis.csv`,
which lists every misclassified image across all 4 models × 2 splits with
its apparent-cause tag (6 of 52 manually reviewed; see "Error analysis"
below for how those 6 were chosen and why the rest weren't).

Each script is self-contained and writes:
- `modeling/results/metrics_<model>.csv` — every metric for every run/partition
- `modeling/results/predictions/<model>__split_a.csv` and `__split_b.csv` — raw
  test-set (y_true, y_prob) for later McNemar's tests / error analysis
- `modeling/results/curves/<model>__<run>.csv` — per-epoch train/val loss & accuracy

`aggregate_results.py` then builds:
- `modeling/results/leakage_table.csv` — the paper's headline table (Split A
  test acc vs. Split B test acc vs. delta, with 95% bootstrap CIs, plus
  Split B's 5-fold CV mean ± std)
- `modeling/results/mcnemar_table.csv` — pairwise McNemar's tests between
  all 4 models' Split B predictions

`gradcam.py` writes `modeling/results/gradcam/*.png` (heatmap overlays) and
`manifest.csv` (per-image categorization).

## What changed after cleanup — read this first

| | Before (564-image pool, 2026-07-23) | After (510-image pool, 2026-07-24) |
|---|---|---|
| Split A→B leakage delta range | 2.6 to 18.0 points | **0.1 to 4.2 points** — much smaller |
| McNemar's significant pairs | 3 of 6 | **0 of 6** — no model pair is statistically distinguishable anymore |
| Grad-CAM: attention on packaging-relevant regions | ~1/3 of reviewed predictions | **~9/15 (60%)** — meaningfully better |
| Split C (external authentic) accuracy, Model 4 | 8.7% | **3.3% — WORSE** |
| Split C (external authentic) accuracy, Model 3 | 77.3% | **69.3% — also worse** |
| Split C, Models 1 & 2 | 0% | **still 0%** |

Removing the confirmed confounds shrank the leakage-quantification deltas,
eliminated every statistically-significant model-vs-model difference, and
visibly improved where Grad-CAM's attention falls. **But it did not fix —
and if anything worsened — the Split C external-generalization collapse.**
That is the single most important finding of this whole project: the
watermark confound was real and worth removing, but it was not the
primary reason these models fail to generalize. Something more
fundamental — likely the overall photography/compression/processing
pipeline distinguishing this dataset's sourcing from an independently
photographed source — is being overfit, and no amount of confound-hunting
inside this one dataset is going to fix that. See "Split C" below.

## Results

### Headline leakage-quantification table (plan Part 4.2)

**Regenerated 2026-07-28 from the current (3-way-normalized) models.** The
table below had been stale since 2026-07-24: `leakage_table.csv` and
`mcnemar_table.csv` were built before Models 2/3/4 were retrained under
normalization, so they described models that no longer exist. Re-running
`aggregate_results.py` refreshed both; the numbers below are the current ones,
and they agree exactly with the independent recomputation in
`paper/tables/table_leakage.csv`.

| Model | Split A test acc (95% CI) | Split B test acc (95% CI) | Split B 5-fold CV acc | Δ (A − B) |
|---|---|---|---|---|
| 1. Color hist + LogReg | 0.842 [0.750, 0.921] | 0.838 [0.743, 0.919] | 0.832 ± 0.049 | +0.004 |
| 2. Small CNN (GAP) | 0.868 [0.789, 0.934] | 0.865 [0.784, 0.932] | 0.865 ± 0.036 | +0.004 |
| 3. MobileNetV3-Small | 0.934 [0.868, 0.987] | 0.932 [0.865, 0.986] | 0.964 ± 0.011 | +0.002 |
| 4. EfficientNet-B0 | 0.987 [0.961, 1.000] | 0.919 [0.851, 0.973] | 0.983 ± 0.011 | +0.068 |

> **Corrected 2026-07-29.** Model 4's Split B row previously read
> 0.946 / 0.975 ± 0.006 / +0.041. Adding checkpoint persistence required
> retraining all three torch models; M2 and M3 reproduced their recorded
> accuracies exactly and **M4 did not**, coming out at 68/74 = 0.919 rather
> than 70/74 = 0.946. Three consecutive re-runs then produced byte-identical
> curves and metric files, normalization is confirmed active in that run,
> and the split/pool files are unchanged — so 0.919 is reproducible and is
> now the value of record. The *cause* of the difference from the earlier
> run could not be identified, because that run's weights and cached
> features were never saved, which is the exact defect the checkpoints fix.
> Every derived table has been regenerated from the current predictions.

(For the record, the superseded pre-normalization readings were M3
0.947/0.946 and M4 0.961/0.919 — normalization moved M3's in-distribution
accuracy down ~1.4 points and left M4's unchanged.)

Full table with precision/recall/F1/ROC-AUC and CIs for every metric:
`modeling/results/leakage_table.csv`; the extended metric set (specificity,
balanced accuracy, MCC, PR-AUC, confusion matrices) is in
`paper/tables/table_performance_full.csv`. All four deltas are small and
all but Model 4's are within noise of zero — Split A and Split B are
essentially statistically indistinguishable at this reduced pool size
(test sets are now ~74-76 images, ~39 of them authentic). Model 4 shows the
(originally hypothesized) positive-delta direction, but the CIs for its
Split A and Split B test accuracy overlap substantially, so this is
suggestive, not conclusive, at this sample size.

### Split C: external generalization (plan Part 4.3) — the most important result in this pass

**Source.** `data/README.md`'s original Split C search came up empty (every
obvious 2nd/3rd counterfeit-labeled source found was either non-independent
of Roboflow/Kaggle, or had no counterfeit label at all). Per the user's
direction, the "Mobile-Captured Pharmaceutical Medication Packages" dataset
(Mendeley, DOI 10.17632/bjy2svvmn8.1, CC BY 4.0, Abdelmaksoud/Gadallah/Asad,
Cairo University) was used as an **authentic-only** external check instead
of a full two-class Split C: 150 images, one per each of its 150 distinct
products, verified programmatically — not just assumed from its
description — to be non-duplicative of the Roboflow/Kaggle training pool
(same rotation-aware pHash method as the main dedup pass; nearest match at
Hamming distance 10/64, comfortably above the 8-bit near-duplicate
threshold; median distance 18). Full check: `scripts/07_verify_split_c_independence.py`,
report at `data/metadata/split_c_independence_report.txt`.

**Method.** Each model, deterministically retrained on Split B's train pool
(same seed/procedure as the original training run), is evaluated on this
external set. Since every image is authentic, the metric is simply: what
fraction does the model correctly call authentic (its recall on the
positive-for-this-check class). Script: `modeling/eval_split_c.py`. Output:
`modeling/results/split_c_eval.csv`.

| Model | Split B test (in-distribution) authentic acc | Split C (external) authentic acc | Gap | vs. pre-cleanup Split C acc |
|---|---|---|---|---|
| 1. Color hist + LogReg | 0.692 | **0.000** | 0.692 | 0.000 (unchanged) |
| 2. Small CNN (GAP) | 0.872 | **0.000** | 0.872 | 0.000 (unchanged) |
| 3. MobileNetV3-Small | 0.974 | 0.693 | 0.281 | 0.773 → 0.693 (**worse**) |
| 4. EfficientNet-B0 | 0.923 | **0.033** | **0.890** | 0.087 → 0.033 (**worse**) |

**This is the headline result of the whole modeling pass, and cleaning up
the data made the finding sharper, not weaker.** Removing every confirmed
watermark/stock-photo confound (47 images, 100% authentic-labeled) and
every wrong-modality image did not close the external-generalization gap —
Models 3 and 4 both got *worse* on Split C after the confound was removed,
and Models 1 and 2 remain at exactly 0%.

**What this rules out and what it implies**: it rules out "the watermark
confound was the main reason these models don't generalize" — if it were,
removing it should have helped, not hurt. What's left is something more
structural: the entire Kaggle pool — regardless of individual-image
confounds — was very likely sourced, photographed, compressed, or
processed in a systematically different way than the independent Mendeley
set (different phones, different lighting protocol, different JPEG
pipeline, different backdrop conventions, etc.), and every model, given
enough capacity, latches onto some correlate of *that* rather than
"authentic packaging" as a general visual concept. A single confound-hunt
inside one dataset cannot fix this; only training on genuinely diverse
sources (multiple independent photography setups in the training pool
itself) is likely to.

- **Models 1 and 2 still misclassify every single external authentic
  image as counterfeit** (0/150, unchanged by the cleanup). Whatever these
  models learn from Kaggle's training images does not transfer even to the
  easiest possible external case (all-authentic packaging), before or
  after removing confounds.
- **EfficientNet-B0 still has the worst external generalization of the two
  transfer-learning models and the single largest gap of all 4 models
  (89.0 points)** — and that gap *grew* after cleanup (81.3 → 89.0 points)
  even though its Split B in-distribution accuracy *dropped* (100% → 92.3%,
  i.e. it got measurably harder to fit the in-distribution data and its
  external performance still fell). This is hard to explain by "it was
  overfitting to the watermark" alone; something else about the frozen
  ImageNet features EfficientNet-B0 extracts from this specific photo
  distribution is source-specific in a way MobileNetV3-Small's features
  are comparatively less so (Model 3 still degrades, 97.4% → 69.3%, but by
  less, both before and after cleanup).

**Bottom line for the paper's abstract/conclusion**: none of the Split
A/Split B accuracy numbers above should be presented without this table
alongside them, and the paper should not claim the watermark cleanup
"fixes" generalization — the data supports the opposite emphasis: even
after removing every confound this project could find and check, external
generalization remains close to zero for the two weakest models and
severely degraded for both transfer-learning models. A 91.9%-on-Split-B
model that gets 3.3% right on plainly-authentic external photos is not
"91.9% accurate at detecting counterfeit pharmaceuticals" — it has barely
learned to recognize Kaggle's specific photography distribution, and nothing
found so far explains why the confound cleanup didn't help more.

**Update (2026-07-25): the "why" has now been found.** See
`data/metadata/capture_method_confound_findings.md` for the full
investigation. Short version: **100% of Kaggle's counterfeit-labeled
images are `Screenshot*.png` files and 100% of its authentic-labeled
images are `images*.jpg` files** — two different capture pipelines,
perfectly confounded with the class label across the *entire* 510-image
pool, not just the 47 already-removed watermarked images. The two groups
differ enormously in brightness (mean 0.77 vs 0.56, t=17.0, p≈0),
resolution (median 225×225 vs 454×550), and file size (mean 6KB vs 339KB).
Split C's external images are ~10x higher resolution than Kaggle's average
and far darker (mean brightness 0.16) than even Kaggle's counterfeit
class — so a model that has learned "darker/bigger/less-compressed →
not-authentic" from Kaggle (a trivially available, dataset-wide shortcut)
will call *every* Split C image counterfeit, which is close to what all 4
models actually do. Direct Grad-CAM on the Split C images
(`modeling/gradcam_split_c.py`) confirms the model's attention is
genuinely on the product in these images, not noise — it is making a
confident, spatially sensible decision calibrated to the wrong cue. This
is a property of the underlying Kaggle "Fake vs Real Medicine" dataset
itself and cannot be fixed by further
single-image filtering — it would need a differently-sourced or
explicitly re-balanced dataset to correct.

**Update 2: causally confirmed, and mostly fixable.**
`modeling/experiment_brightness_norm.py` and
`modeling/experiment_resolution_norm.py` tested this directly with
label-free, deployable normalization (train, Kaggle test, and Split C all
processed identically) for Model 4 (EfficientNet-B0):

| Condition | Split B test acc | Split C acc |
|---|---|---|
| Baseline | 91.9% | 8.7% |
| Resolution norm only | 93.2% | 22.0% |
| Brightness norm only | 91.9% | 27.3% |
| **Both combined** | **95.9%** | **62.7%** |

Combined normalization took Split C from 8.7% to **62.7%** (~7x) while
*also* producing the best in-distribution accuracy of any condition
(95.9%) — a controlled intervention that improved both robustness and
accuracy together, not a trade-off. This is strong causal evidence that
most (not all — a real ~33-point gap remains) of the Split C collapse was
two specific, identifiable, correctable confounds rather than an
irreducible property of the task. For the classical color-histogram
model, brightness normalization alone collapsed in-distribution accuracy
toward chance (83.8% → 54.1%) without helping Split C — that model never
had signal beyond the brightness shortcut.

**Update 3: extending combined normalization to all 4 models shows the
fix is architecture-dependent, not universal — and hurts one model.**
`modeling/experiment_normalization_all_models.py`:

| Model | Baseline Split C | Normalized Split C | Δ |
|---|---|---|---|
| 1. Color hist + LogReg | 0.0% | 0.0% | — |
| 2. Small CNN (GAP) | 0.0% | **84.7%** | **+84.7** (best result in the project) |
| 3. MobileNetV3-Small | **73.3%** (best baseline) | 52.0% | **−21.3** (normalization hurts) |
| 4. EfficientNet-B0 | 8.7% | 62.7% | +54.0 |

Model 3 already generalized far better than any other model *without*
normalization, and imposing normalization made it worse. So "combined
brightness + resolution normalization" is a strong win for Models 2 and
4, a non-effect for Model 1 (no signal to begin with), and actively
counterproductive for Model 3. **Any claim in the paper needs to be
architecture-specific, not a blanket recommendation.**

**Update 4: decomposed why Model 3 regresses, and checked its Grad-CAM
directly — the answer isn't flattering.**
`modeling/experiment_model3_decompose.py` found **brightness**
normalization specifically is what hurts Model 3 (80.0% → 56.0%
Split C); resolution normalization alone is neutral-to-positive (80.0% →
84.7%). `modeling/gradcam_split_c_model3.py` then ran Grad-CAM directly
on Model 3's own (un-normalized) Split C predictions: correct predictions
concentrate attention on the **dark background**, not the product;
reviewed incorrect predictions had attention on the product instead — the
opposite of what "this model genuinely reads packaging better" would
predict. Most likely explanation: Model 3 learned something like "this
consistent dark backdrop → authentic," which scores well on Split C only
because Split C happens to be 100% authentic and 100% sharing that
backdrop — a confound that fits this particular external set well by
chance, not evidence of better packaging understanding. Full results:
`data/metadata/capture_method_confound_findings.md` Findings 4-8. **Not
yet done** (at that point): integrating any normalization into the main
Split A/B/C pipeline, investigating the remaining gap for Models 2/4 after
normalization, and a larger-sample Grad-CAM review of Model 3 (only 5 of
20 images manually reviewed so far).

**Update 5: a third axis (JPEG compression) reverses Model 3's regression
in a standalone experiment, and 3-way normalization is promoted to
production — but Model 3's result doesn't hold up there.**
Color/white-balance normalization was tested and ruled out
(`experiment_colorbalance_norm.py`, Finding 9 — that run was later found
unsound and was redone deterministically as Finding 16, which confirms the
rejection; see Update 7). JPEG compression
normalization was not: combined with resolution+brightness it took Model
4's Split C accuracy to 78.0% in a same-run comparison
(`experiment_compression_norm.py`, Finding 10), and extending the 3-way
combination to all 4 models (`experiment_compression_all_models.py`,
Finding 11) reversed Model 3's earlier regression (75.3%→81.3%, improved
rather than hurt) while still helping Models 2 (0%→91.3% in that
experiment; **0%→86.0% in the corrected production run below** — the
experiment's Model 2 was trained at the stale 0.0003 LR, see "Known
caveats") and 4.

3-way normalization (`modeling/normalization.py`) was then promoted to the
project's **production default** — `common.py`'s `PharmaImageDataset`
applies it automatically now, so `train_model2_cnn.py`,
`train_model3_mobilenet.py`, `train_model4_efficientnet.py`, and
`eval_split_c.py` all pick it up with no experiment-script scaffolding.
Model 1 bypasses `PharmaImageDataset` entirely and is unaffected by
design (Finding 11 showed normalization only hurts it). All 3 affected
models were retrained from scratch and Split C re-evaluated
(`modeling/results/split_c_eval.csv`, Finding 12):

| Model | Split C authentic acc (pre-norm → normalized production) | Split B test authentic acc | Gap |
|---|---|---|---|
| 1. Classical | 0.0% → 0.0% (unaffected by design) | 69.2% | 69.2 |
| 2. Small CNN | 0.0% → **86.0%** | 84.6% | **−1.4 (negative gap)** |
| 3. MobileNetV3-Small | 69.3% → 68.0% (flat) | 94.9% | 26.9 |
| 4. EfficientNet-B0 | 3.3% → 80.7% | 97.4% | 16.8 |

Models 2 and 4 confirm and strengthen in a real production retrain — Model
2 now generalizes to Split C *better* than to its own in-distribution test
set, the first negative gap anywhere in this project. Model 3's first
production run looked flat (68.0% vs. its 69.3% pre-normalization
baseline), contradicting Finding 11's standalone-experiment improvement
(75.3%→81.3%) — reported at the time as unresolved rather than reconciled.

**Update 6: the `k_augment=3` non-determinism was found and fixed, and
Model 3's result resolves back to "normalization helps."**
`modeling/feature_cache.py`'s `extract_features` never seeded its
`k_augment` augmented passes, so results depended on unrelated prior RNG
usage in the same process rather than being reproducible — the root cause
behind every "same condition, different number" gap in Findings 6, 9-12.
Fixed with `set_seed(SEED + pass_idx)` before each pass. Verified
deterministic: ran `train_model3_mobilenet.py` twice back-to-back, `diff`
on the two metrics CSVs shows zero differences. Re-running
`eval_split_c.py` for Model 3 under this fix gives **77.3%** Split C
accuracy (vs. the pre-fix 68.0%) — consistent with (though not identical
to) Finding 11's 81.3%, and the same positive direction as Models 2 and 4.
This is now the accuracy of record; Finding 12's 68.0% and Finding 6's
52.0% (2-way condition, not yet rerun with the fix) are understood as
artifacts of the unseeded bug rather than genuine model behavior. Full
writeup: `data/metadata/capture_method_confound_findings.md` Finding 13.

**Final production Split C table** (deterministic, seeding-fixed):

| Model | Split C authentic acc | Split B test authentic acc | Gap |
|---|---|---|---|
| 1. Classical | 0.0% | 69.2% | 69.2 |
| 2. Small CNN | **86.0%** | 84.6% | −1.4 (negative gap) |
| 3. MobileNetV3-Small | 77.3% | 97.4% | 20.1 |
| 4. EfficientNet-B0 | 80.7% | 97.4% | 16.8 |

**Not yet done**: a larger-sample Grad-CAM review of Model 3 under the
normalized condition to see if its attention pattern changed; the
remaining ~16-20-point gaps for Models 3/4 even after normalization;
rerunning Finding 6's 2-way-only experiment with the seeding fix if that
specific comparison is ever needed again.

### Synthetic counterfeit-proxy Split C (plan Part 4.3 extension) — counterfeit-recall check

The Split C above is authentic-only, so it can only measure the
authentic-class false-positive rate, never counterfeit-class recall. Since
no genuine independent counterfeit-labeled source could be found (`data/README.md`
"Sources"), a synthetic counterfeit proxy was built instead: the same 150
independent Mendeley authentic photos, paired with 150 approved synthetic
"counterfeit-style" perturbations of those SAME photos (print-quality/color
defects + text-region tampering), so the perturbation is the only
systematic difference between classes by construction. Full methodology,
confound checks, and review process: `data/metadata/synthetic_counterfeit_findings.md`.
**This is explicitly a robustness stress-test analogous to ImageNet-C
corruption benchmarks, not a measurement of true real-world
counterfeit-detection recall** — that caveat applies to every number below.

All 4 models deterministically retrained on Split B's train pool (same
seed/procedure as the authentic-only Split C eval above), evaluated on the
full 300-image synthetic set (`modeling/eval_split_c_synthetic.py`,
`modeling/results/split_c_synthetic_eval.csv`):

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| 1. Classical | 0.500 | 0.500 | 1.000 | 0.667 | **0.895** |
| 2. Small CNN | 0.633 | 0.744 | 0.407 | 0.526 | 0.794 |
| 3. MobileNetV3-Small | 0.483 | 0.460 | 0.193 | 0.272 | 0.503 |
| 4. EfficientNet-B0 | 0.550 | 0.603 | 0.293 | 0.395 | 0.570 |

**Model 1's result is a calibration failure, not a lack of signal.** It
predicts "counterfeit" for essentially every image (recall=1.0, accuracy
pinned at exactly 0.5), yet has by far the best ROC-AUC (0.895) — its raw
scores separate the two classes well, but its 0.5 threshold (fit on the
very different real-Kaggle brightness/resolution distribution) is
badly wrong here. This is a different failure mode than its 0% on the
authentic-only Split C above, and together the two results suggest its
color-histogram features do carry some transferable signal that its
threshold doesn't exploit correctly out of distribution.

**Models 2 and 4 show modest, genuine separation** (AUC 0.788 and 0.570)
but under-predict counterfeit at the default threshold (both miss the
majority of synthetic counterfeits).

**Model 3 is at chance (AUC 0.503) — this corroborates, not contradicts,
the earlier Grad-CAM finding** (Finding 8 above) that its strong
authentic-only Split C performance was a background/backdrop-matching
shortcut specific to the real photos' shared backdrop, not genuine
packaging understanding. That shortcut gives zero signal for
distinguishing an authentic photo from a perturbed version of the exact
same photo (identical backdrop in both), so chance performance is exactly
what that finding would predict — cross-validated here via a completely
independent eval set.

**Overall**: none of the 4 models show strong, well-calibrated
counterfeit-recall against this specific perturbation-style proxy — a
result reached via a different route than the authentic-only Split C or
the normalization experiments, but pointing the same direction: high
in-distribution accuracy in this project has not been evidence of robust,
transferable counterfeit-detection ability.

### The finding is not what the plan's working hypothesis expected — and that's reported as-is

The working hypothesis (plan Part 1, and the reason this rewrite exists) was
that Split A (naive, leaky) accuracy would come in **higher** than Split B
(leakage-corrected) accuracy — i.e. Δ (A − B) positive — because near-
duplicate product photos leaking from train into test should make the test
set artificially easy under Split A.

On the cleaned 510-image pool, the deltas are now tiny (+0.1 to +4.2
points) and mostly within noise — Split A and Split B are close to
indistinguishable at this sample size, with only Model 4 showing a
delta (+4.2 points) that leans toward the originally-hypothesized
direction, and even that one's CIs overlap substantially between splits.
(On the original 564-image pool, before cleanup, all four models had
shown the *opposite* sign, by 2.6 to 18.0 points — that finding is now
superseded by the retrain, not still current; see "What changed after
cleanup" above.)

Plausible explanation for why the delta is small either way: only 9 of 484
product_identity groups (1.9%, see `splits/split_report.txt`) actually
straddle partitions under the naive split at the current pool size. That
is a real but small amount of leakage given a ~39-image test set — small
enough that ordinary sampling variance in *which* images happen to land in
each split's test set dominates the leakage effect. This doesn't
contradict the mechanism Split B is designed to fix; it bounds how much
that mechanism matters *for this specific, now-cleaned data at this scale*.
A dataset with more duplicate-heavy sourcing, or a larger naive-split
leakage rate, would be expected to show a clearer effect.

This is exactly the kind of result plan Part 7 ("Notes on scope honesty")
anticipated: "this plan is designed so that the paper is publishable
regardless of which way the results go... write the Discussion section to
reflect whatever the data actually shows."

### Model ranking under Split B (leakage-corrected)

Complexity still tracks with in-distribution accuracy: classical (0.838) <
small CNN (0.865) < EfficientNet-B0 (0.919) < MobileNetV3-Small (0.932) —
though note Model 4 ranks *below* Model 3 on Split B test accuracy
(it has a higher 5-fold CV mean, 0.983 vs 0.964, so this is close and
partly a small-test-set artifact — n=74, and no pairwise McNemar test
separates any two models, all p ≥ 0.118). This in-distribution
ranking is exactly the picture Split C complicates: MobileNetV3-Small's
in-distribution edge over EfficientNet-B0 here does *not* predict which
one generalizes better externally (both degrade severely; Model 3
degrades somewhat less — see Split C above). In-distribution ranking and
external robustness are simply different questions, and this project's
data only answers the second one convincingly.

### Pairwise McNemar's tests (Split B test set, plan Part 4.4)

Full table: `modeling/results/mcnemar_table.csv`.

Regenerated 2026-07-28 alongside the leakage table above (the previous
version described the pre-normalization models). Discordant pair counts are
in `paper/tables/table_mcnemar.csv`.

| Model A | Model B | Discordant | p-value | Significant (α=0.05) |
|---|---|---|---|---|
| Classical | Small CNN | 12 | 0.774 | no |
| Classical | MobileNetV3-Small | 15 | 0.118 | no |
| Classical | EfficientNet-B0 | 14 | 0.057 | no |
| Small CNN | MobileNetV3-Small | 11 | 0.227 | no |
| Small CNN | EfficientNet-B0 | 10 | 0.109 | no |
| MobileNetV3-Small | EfficientNet-B0 | 1 | 1.000 | no |

**No pairwise comparison is significant anymore** (before cleanup, 3 of 6
were, including EfficientNet-B0 vs. both weaker models). At this reduced
test-set size (~39 images per split) and with the confound-driven
performance boosts removed, none of the 4 models can be confidently said
to outperform any other on Split B test accuracy alone — a materially
more cautious conclusion than the pre-cleanup run supported, and the more
defensible one to put in a paper.

### Grad-CAM bias audit (plan Part 4.5)

Ran on Model 4 (EfficientNet-B0), Split B, on the cleaned 510-image pool.
Script: `gradcam.py`. Output: `modeling/results/gradcam/*.png` (24 heatmap
overlays) + `manifest.csv`.

**Sample size note**: the plan asks for "~10-15 incorrect predictions."
Model 4 now misclassifies 9 images across val+test (up from 5 pre-cleanup,
consistent with its Split B test accuracy dropping from 98.8% to 91.9%) —
all 9 are used. 15 correct predictions are sampled for contrast; 15 of the
24 total images were manually reviewed and categorized (9/9 incorrect,
6/15 correct — the remaining 9 correct images are generated but not yet
manually tagged, `packaging_relevant=not_reviewed` in the manifest).

**Finding — attention is meaningfully more often on packaging cues than
before the cleanup, but a specific recurring confound persists.** Of the
15 manually reviewed:

| Category | Count | Meaning |
|---|---|---|
| `packaging_relevant` | 9 (60%) | Attention on logo, brand header, printed text, or the product itself |
| `incidental` | 4 (27%) | Attention on background, image corners, or cloth backdrop — not on the product |
| `mixed` | 2 (13%) | Attention partly on the product, partly on background |

Compare to the pre-cleanup pass: ~33% packaging-relevant, ~40% incidental.
Removing the watermark confound visibly shifted attention toward the
product on this sample — but it did not eliminate incidental reliance,
and one specific pattern recurs even after cleanup:

- **Two separate "Ecosprin" box photos** (`..._70c0c79496`, an Ecosprin-75
  box, and `..._1c2176cbfd`, an Ecosprin-150 box) both show attention
  concentrated on the **background corners around the box**, not the box
  itself — the same failure mode on two different images of visually
  similar packaging from what is very likely the same photography
  session/backdrop. This is a smaller-scale echo of the original
  patterned-cloth-backdrop finding (pre-cleanup: `..._00538`) and is
  consistent with the Split C result above: whatever the model is keying
  on for these images is tied to *this dataset's specific photography
  conventions*, not the product, and that is exactly the kind of thing
  that would fail to transfer to an external source.
- `..._378059a366`: a genuinely good sign — attention lands squarely on
  the pills themselves for a blister-pack image, one of several cases in
  this pass where the model attends to the actual product rather than
  its surroundings.

**Honest read**: cleanup measurably improved where this model's attention
falls, but the Split C result (above) shows that "attends to the product
more often on this internal sample" and "generalizes to new photography
setups" are not the same thing — the model's remaining reliance on
dataset-specific incidental cues (even at a reduced rate) is enough to
produce a near-total external generalization failure. Both findings should
be reported together, not the improvement alone.

### Error analysis (plan Part 4.6)

Pooled predictions from all 4 models across both Split A and Split B test
sets on the cleaned pool (600 predictions total: 4 models × 2 splits × ~75
test images).

**Error rate by model** (out of 150 test predictions each). Recomputed
2026-07-28 from the current predictions — `modeling/results/error_analysis.csv`
still holds the pre-normalization counts for Models 3/4 plus the manual
cause tags, which is why it is kept rather than overwritten; the current
counts are in `paper/tables/table_error_analysis.csv`:

| Model | Errors | Rate | (pre-normalization) |
|---|---|---|---|
| Color hist + LogReg | 24 | 16.0% | 24 / 16.0% |
| Small CNN (GAP) | 20 | 13.3% | 20 / 13.3% |
| MobileNetV3-Small | 10 | 6.7% | 8 / 5.3% |
| EfficientNet-B0 | 5 | 3.3% | 9 / 6.0% |

34 distinct images account for all 59 pooled errors, and 6 are wrong in
three or more model/split combinations
(`paper/tables/table_error_consensus.csv`); three of those six are the same
images the manual review below examined, so those diagnoses carry over.

Similar shape to the pre-cleanup pass (classical/small-CNN much worse than
the transfer-learning models), though EfficientNet-B0's error rate ticked
up slightly (5.3% → 6.0%) consistent with its Split B test accuracy drop.
36 distinct images have at least one error (down from 52 pre-cleanup,
tracking the smaller pool); 4 are misclassified by **3 or more**
model/split combinations independently — manually inspected:

| Image | True label | Wrong in | Apparent cause |
|---|---|---|---|
| `..._02169db735` | authentic | 4/8 (M3 both splits, M4 both splits) | **Mixed/incidental confound** — Grad-CAM (this is the recurring "Paracetamol STADA box" case) shows attention on background corners, not the print |
| `..._378059a366` | authentic | 4/8 (M2 both splits, M3 split A, M4 split A) | **Genuine visual similarity, correctly attributed** — Grad-CAM shows this model's attention *does* land on the actual pills; this looks like a genuinely hard example rather than a shortcut artifact |
| `..._6a0d82961a` | authentic | 3/4 (M2, M3, M4, split B) | **Genuine visual similarity** — the sachet packet case, well-lit and legible with no visible defect; Grad-CAM shows attention near the product's OTC logo, not background |
| `..._f57956b7d9` | authentic | 4/8 (M1 both splits, M2 both splits) | **Image quality** — this image is a 100×100px thumbnail, far lower resolution than the rest of the pool; only the two weaker models (classical, small CNN) are fooled by it, the two transfer-learning models handle it fine, consistent with a resolution/detail problem rather than a genuine ambiguity |

**Coverage note, stated plainly**: these 4 images (of 36 with at least one
error) are the ones with the strongest cross-model agreement signal —
not a random or exhaustive sample of all 36. Two of the four causes here
(mixed/incidental, image quality) match categories already seen in the
pre-cleanup pass; two others (genuine visual similarity, now with Grad-CAM
evidence that the model's attention is actually reasonable on those
specific images) suggest that at least some of what looked like "hard
examples" are cases where the model is doing something defensible and
simply meeting the real difficulty of the task.

**Takeaway**: the post-cleanup error pattern is consistent with, not
contradictory to, the Split C finding above — these models make relatively
few and often explicable in-distribution errors (image quality, genuinely
hard examples), while their catastrophic failure is specifically on
external data, which this pooled in-distribution error analysis cannot
surface by construction (Split A and Split B are both drawn from the same
underlying Kaggle photography distribution). Read this section as "the
models are reasonably competent on data like their training data" and the
Split C section as "and that competence does not transfer" — both are
true simultaneously and the paper needs both to tell an honest story.

**Update 7 (2026-08-13): the composition ORDER of the three operators is
the most load-bearing free parameter in the pipeline, and the white-balance
rejection was redone on a sound harness.** Two experiments, both M4, both
single-execution with same-run baselines, both post-seeding-fix.

`experiment_order_permutation.py` (Finding 15) ran all 3! = 6 orderings of
resolution/brightness/compression at the production constants. External
accuracy ranges **0.380 to 0.880** while Split B ranges 0.919 to 0.946. One
rule separates the six with no overlap: applying the JPEG bottleneck *after*
the resolution cap gives 0.820 / 0.847 / 0.880, applying it before gives
0.380 / 0.467 / 0.540. Compressing at native resolution and then downsampling
undoes the compression, because the resampling filter averages over the
quantisation artefacts the bottleneck exists to impose. Most usefully for the
paper: the ordering with the **highest** in-distribution accuracy (0.946) has
the **lowest** external accuracy (0.380), so choosing the order by held-out
accuracy picks the worst of six. Production order (R, B, C) is sound but not
optimal — R, C, B beats it on both axes and was deliberately **not** adopted,
because choosing preprocessing by external score is target-distribution
leakage.

`experiment_colorbalance_norm.py` was rewritten and rerun (Finding 16) after
its original 2026-07-25 run was found to predate the seeding fix, hard-code
the learning rate, and compare against a superseded two-way pipeline. The
rejection holds and hardens: 0.067 alone, −4.0 points on the production
three-way, −15.3 points on the two-way (against the 3.3 originally reported).

Harness validation from both: the production condition returned 0.919 / 0.820
in each script, matching the constant sweep exactly — three exact
reproductions across two scripts.

## Known caveats for this pass

- Test partitions are now small (~39 images per split, down from ~84-85
  pre-cleanup), so point-estimate deltas between Split A and Split B for
  any single model carry wide bootstrap CIs — read the CIs, not just the
  point accuracy, before concluding anything about leakage magnitude.
- Models 3 and 4 (frozen pretrained backbones) train on features extracted
  ONCE per split rather than re-running the backbone every epoch (see
  `feature_cache.py`) — necessary for CPU tractability (an initial
  live-backbone-forward-pass-per-epoch attempt at Model 4 was killed by
  the environment's runtime limit before Split A finished). Augmentation
  variety is preserved via 3 independently-augmented cached passes per
  training image rather than fresh-every-epoch augmentation; documented
  as a deliberate speed/fidelity trade-off, not a silent shortcut.
- Model 4's "optional fine-tune" (plan Part 3.1) was not run — frozen
  backbone only, to keep CPU training time bounded and comparable across
  models. Documented as a future extension, not silently skipped.
- Split C is authentic-only (150 images), not the plan's originally-envisioned
  two-class external benchmark — no independent counterfeit-labeled 3rd
  source was found (every candidate checked was either non-independent of
  Roboflow/Kaggle or lacked a counterfeit label; see data/README.md). This
  means Split C measures false-positive rate on authentic packaging only;
  it says nothing about whether counterfeit-detection *recall* generalizes
  externally, which remains untested and should be stated as a limitation
  in the paper, not implied to be covered.
- ~~`eval_split_c.py`'s Model 2 retraining reuses a hardcoded LR that has to
  be kept in sync by hand.~~ **Fixed 2026-07-28.** The hand-sync went wrong
  twice: once during the 2026-07-24 retrain (training used 0.0003 via the
  `PHARMAVISION_MODEL2_LR` override while the eval script still said 0.001),
  and again after the normalization retrain, when Model 2's LR search
  selected 0.001 while the eval script had been left at 0.0003 from that
  first fix. Training scripts now record the LR they actually used to
  `modeling/results/chosen_lrs.json` (`result_io.save_chosen_lr`) and every
  rebuild path reads it back (`load_chosen_lr`), raising rather than guessing
  if the record is missing. `eval_split_c.py`, `eval_split_c_synthetic.py`,
  `gradcam.py` and `gradcam_split_c_model3.py` all use it. Model 2's Split C
  and synthetic-Split-C rows were re-measured under the corrected LR; the
  rebuild's training curve is now byte-identical to the run of record, which
  the 0.0003 rebuild plainly was not. Pre-fix values are preserved in
  `split_c_eval_PRE_LRFIX_20260728.csv` and
  `split_c_synthetic_eval_PRE_LRFIX_20260728.csv`.
- Modality/quality review of the Kaggle pool is complete (100% human
  reviewed, not sampled) as of this retrain — see
  `data/metadata/modality_review_findings.md`. Roboflow's supplementary
  pool (not used by default) still only has a coarse automated guess.
- Environment note: background training runs were killed unpredictably by
  the host environment multiple times during this retrain (not a fixed
  timeout — sometimes <2 minutes, sometimes 15+); each kill lost at most
  the in-progress model thanks to per-model result files, and Model 2's
  LR search was cached via an env var after the pattern became clear, to
  shrink the window between checkpoints. If reproducing this from scratch,
  expect to possibly need 2-3 attempts for Model 2 specifically.
