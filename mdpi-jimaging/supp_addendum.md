
## S-X. Analysis Chronology, Baseline-Model Analyses and Exploratory Detail

### A. When each analysis was specified

The study was not preregistered. The four model families, the comparison of an image-level partition (Split A) with a near-duplicate-grouped partition (Split B), and specificity on condition C were planned before any external result was available. The original plan also called for recording each source's file formats, resolutions and capture conditions, and the filename patterns that separate the classes were noticed during the first manual review. Whether these acquisition variables predict the label was not quantified until after the baseline models had failed on condition C (`data/metadata/capture_method_confound_findings.md`, 2026-07-25); the header-only audit of Table 2 took its final form later. The audit reads only file properties, so its result cannot depend on any model output, but the variables it examines were chosen with knowledge of the failure. Condition D, the paired leakage experiment, the five-seed repeat and the balanced external test were added after the condition C result. The balanced test was designed after the normalization had been adopted, and its specified target was the normalized models; models, preprocessing, threshold and metrics were fixed before the set was built, and the normalized models were scored on it once. The normalization, attribution and region-substitution analyses are exploratory, and condition C informed the choice of normalization axes.

### B. Baseline-model analyses added in revision

Earlier versions of this study reported the internal metrics (Table S3) and the balanced external test for the normalized models of M2 to M4, because the training code normalizes by default. The main text now treats the baseline (unnormalized) models as primary. `modeling/revision_baseline_analyses.py` (i) scores the persisted seed-42 baseline checkpoints written by the seed sweep on the Split B test partition, conditions C and D and the balanced external set, reproducing the seed sweep's recorded Split B, C and D values exactly; (ii) trains baseline M2 to M4 on Split A at seed 42 with the unchanged training code; and (iii) recomputes every interval from the per-image predictions. No model, threshold or evaluation set was changed. The baseline rows of Table S31 were computed after the normalized rows were known.

**TABLE S30.** Internal test performance, baseline and normalized models. 95% percentile bootstrap, 10,000 resamples, stratified by class, resampling near-duplicate groups. Counterfeit-labeled is the positive class. Confusion counts are TN/FP/FN/TP.

| Model | Condition | Split | n (groups) | Confusion | Accuracy | Balanced accuracy | Sensitivity | Specificity | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|
| M1 hist+LR | baseline | A | 76 (76) | 31/10/2/33 | 0.842 [0.763, 0.921] | 0.850 [0.770, 0.925] | 0.943 [0.857, 1.000] | 0.756 [0.634, 0.878] | 0.893 [0.810, 0.960] |
| M1 hist+LR | baseline | B | 74 (72) | 27/12/0/35 | 0.838 [0.757, 0.909] | 0.846 [0.769, 0.917] | 1.000 [1.000, 1.000] | 0.692 [0.538, 0.833] | 0.897 [0.816, 0.963] |
| M2 CNN | baseline | A | 76 (76) | 36/5/7/28 | 0.842 [0.763, 0.921] | 0.839 [0.753, 0.918] | 0.800 [0.657, 0.914] | 0.878 [0.780, 0.976] | 0.935 [0.877, 0.978] |
| M2 CNN | baseline | B | 74 (72) | 32/7/3/32 | 0.865 [0.781, 0.934] | 0.867 [0.785, 0.938] | 0.914 [0.800, 1.000] | 0.821 [0.684, 0.927] | 0.911 [0.830, 0.974] |
| M2 CNN | normalized | A | 76 (76) | 37/4/6/29 | 0.868 [0.789, 0.934] | 0.866 [0.786, 0.935] | 0.829 [0.686, 0.943] | 0.902 [0.805, 0.976] | 0.951 [0.902, 0.986] |
| M2 CNN | normalized | B | 74 (72) | 33/6/4/31 | 0.865 [0.781, 0.934] | 0.866 [0.783, 0.936] | 0.886 [0.771, 0.971] | 0.846 [0.725, 0.950] | 0.916 [0.844, 0.973] |
| M3 MobileNetV3 | baseline | A | 76 (76) | 37/4/2/33 | 0.921 [0.855, 0.974] | 0.923 [0.858, 0.976] | 0.943 [0.857, 1.000] | 0.902 [0.805, 0.976] | 0.985 [0.960, 0.999] |
| M3 MobileNetV3 | baseline | B | 74 (72) | 38/1/3/32 | 0.946 [0.892, 0.987] | 0.944 [0.887, 0.987] | 0.914 [0.800, 1.000] | 0.974 [0.925, 1.000] | 0.984 [0.955, 1.000] |
| M3 MobileNetV3 | normalized | A | 76 (76) | 40/1/4/31 | 0.934 [0.868, 0.987] | 0.931 [0.866, 0.986] | 0.886 [0.771, 0.971] | 0.976 [0.927, 1.000] | 0.995 [0.983, 1.000] |
| M3 MobileNetV3 | normalized | B | 74 (72) | 38/1/4/31 | 0.932 [0.868, 0.986] | 0.930 [0.863, 0.986] | 0.886 [0.771, 0.971] | 0.974 [0.919, 1.000] | 0.987 [0.963, 1.000] |
| M4 EfficientNet-B0 | baseline | A | 76 (76) | 40/1/1/34 | 0.974 [0.934, 1.000] | 0.974 [0.933, 1.000] | 0.971 [0.914, 1.000] | 0.976 [0.927, 1.000] | 0.991 [0.971, 1.000] |
| M4 EfficientNet-B0 | baseline | B | 74 (72) | 35/4/3/32 | 0.905 [0.836, 0.961] | 0.906 [0.836, 0.963] | 0.914 [0.800, 1.000] | 0.897 [0.795, 0.975] | 0.985 [0.961, 0.999] |
| M4 EfficientNet-B0 | normalized | A | 76 (76) | 41/0/1/34 | 0.987 [0.961, 1.000] | 0.986 [0.957, 1.000] | 0.971 [0.914, 1.000] | 1.000 [1.000, 1.000] | 0.999 [0.993, 1.000] |
| M4 EfficientNet-B0 | normalized | B | 74 (72) | 38/1/5/30 | 0.919 [0.851, 0.973] | 0.916 [0.846, 0.971] | 0.857 [0.743, 0.971] | 0.974 [0.919, 1.000] | 0.988 [0.965, 1.000] |

**TABLE S31.** Balanced external test with two interval constructions: resampling images (each falsified frame is a separate regulatory alert) and resampling the 29 authentic search-term clusters. Both are stratified by class, 10,000 resamples. Falsified is the positive class.

| Model | Condition | Metric | Point | Image-level interval | Cluster-level interval |
|---|---|---|---|---|---|
| M1 hist+LR | baseline | balanced accuracy | 0.478 | [0.446, 0.500] | [0.446, 0.500] |
| M1 hist+LR | baseline | recall | 0.957 | [0.891, 1.000] | [0.891, 1.000] |
| M1 hist+LR | baseline | specificity | 0.000 | [0.000, 0.000] | [0.000, 0.000] |
| M1 hist+LR | baseline | precision | 0.489 | [0.471, 0.500] | [0.435, 0.542] |
| M1 hist+LR | baseline | F1 | 0.647 | [0.617, 0.667] | [0.593, 0.698] |
| M1 hist+LR | baseline | ROC-AUC | 0.422 | [0.307, 0.541] | [0.315, 0.533] |
| M2 CNN | baseline | balanced accuracy | 0.391 | [0.304, 0.478] | [0.307, 0.472] |
| M2 CNN | baseline | recall | 0.652 | [0.500, 0.783] | [0.500, 0.783] |
| M2 CNN | baseline | specificity | 0.130 | [0.043, 0.239] | [0.029, 0.218] |
| M2 CNN | baseline | precision | 0.429 | [0.365, 0.485] | [0.361, 0.492] |
| M2 CNN | baseline | F1 | 0.517 | [0.429, 0.595] | [0.426, 0.598] |
| M2 CNN | baseline | ROC-AUC | 0.379 | [0.268, 0.497] | [0.260, 0.502] |
| M2 CNN | normalized | balanced accuracy | 0.478 | [0.380, 0.576] | [0.369, 0.582] |
| M2 CNN | normalized | recall | 0.652 | [0.522, 0.783] | [0.522, 0.783] |
| M2 CNN | normalized | specificity | 0.304 | [0.174, 0.435] | [0.136, 0.462] |
| M2 CNN | normalized | precision | 0.484 | [0.411, 0.556] | [0.410, 0.557] |
| M2 CNN | normalized | F1 | 0.556 | [0.460, 0.642] | [0.462, 0.643] |
| M2 CNN | normalized | ROC-AUC | 0.403 | [0.289, 0.523] | [0.273, 0.533] |
| M3 MobileNetV3 | baseline | balanced accuracy | 0.609 | [0.511, 0.707] | [0.509, 0.700] |
| M3 MobileNetV3 | baseline | recall | 0.652 | [0.522, 0.783] | [0.522, 0.783] |
| M3 MobileNetV3 | baseline | specificity | 0.565 | [0.413, 0.717] | [0.417, 0.689] |
| M3 MobileNetV3 | baseline | precision | 0.600 | [0.509, 0.702] | [0.518, 0.688] |
| M3 MobileNetV3 | baseline | F1 | 0.625 | [0.517, 0.722] | [0.522, 0.716] |
| M3 MobileNetV3 | baseline | ROC-AUC | 0.645 | [0.526, 0.758] | [0.530, 0.750] |
| M3 MobileNetV3 | normalized | balanced accuracy | 0.543 | [0.446, 0.641] | [0.443, 0.639] |
| M3 MobileNetV3 | normalized | recall | 0.435 | [0.283, 0.587] | [0.283, 0.587] |
| M3 MobileNetV3 | normalized | specificity | 0.652 | [0.522, 0.783] | [0.510, 0.783] |
| M3 MobileNetV3 | normalized | precision | 0.556 | [0.424, 0.690] | [0.424, 0.692] |
| M3 MobileNetV3 | normalized | F1 | 0.488 | [0.354, 0.612] | [0.351, 0.608] |
| M3 MobileNetV3 | normalized | ROC-AUC | 0.641 | [0.523, 0.755] | [0.521, 0.749] |
| M4 EfficientNet-B0 | baseline | balanced accuracy | 0.587 | [0.489, 0.685] | [0.484, 0.683] |
| M4 EfficientNet-B0 | baseline | recall | 0.609 | [0.478, 0.739] | [0.457, 0.739] |
| M4 EfficientNet-B0 | baseline | specificity | 0.565 | [0.413, 0.717] | [0.421, 0.700] |
| M4 EfficientNet-B0 | baseline | precision | 0.583 | [0.488, 0.686] | [0.481, 0.688] |
| M4 EfficientNet-B0 | baseline | F1 | 0.596 | [0.483, 0.695] | [0.483, 0.699] |
| M4 EfficientNet-B0 | baseline | ROC-AUC | 0.607 | [0.490, 0.720] | [0.492, 0.716] |
| M4 EfficientNet-B0 | normalized | balanced accuracy | 0.652 | [0.554, 0.750] | [0.557, 0.744] |
| M4 EfficientNet-B0 | normalized | recall | 0.587 | [0.435, 0.717] | [0.435, 0.717] |
| M4 EfficientNet-B0 | normalized | specificity | 0.717 | [0.587, 0.848] | [0.583, 0.833] |
| M4 EfficientNet-B0 | normalized | precision | 0.675 | [0.564, 0.795] | [0.571, 0.784] |
| M4 EfficientNet-B0 | normalized | F1 | 0.628 | [0.506, 0.736] | [0.506, 0.733] |
| M4 EfficientNet-B0 | normalized | ROC-AUC | 0.713 | [0.603, 0.816] | [0.598, 0.809] |

**TABLE S32.** (a) Exact McNemar tests between baseline models on the Split B test partition (n = 74), with Holm correction over six pairs. (b) Specificity on condition C minus condition D, with Newcombe hybrid-score intervals for independent proportions; the two conditions draw on one package collection but cannot be paired image by image.

| Model A | Model B | Only A correct | Only B correct | *p* | Holm *p* |
|---|---|---|---|---|---|
| M1 hist+LR | M3 MobileNetV3 | 4 | 12 | 0.077 | 0.461 |
| M2 CNN | M3 MobileNetV3 | 3 | 9 | 0.146 | 0.730 |
| M3 MobileNetV3 | M4 EfficientNet-B0 | 3 | 0 | 0.250 | 1.000 |
| M1 hist+LR | M4 EfficientNet-B0 | 6 | 11 | 0.332 | 1.000 |
| M2 CNN | M4 EfficientNet-B0 | 5 | 8 | 0.581 | 1.000 |
| M1 hist+LR | M2 CNN | 4 | 6 | 0.754 | 1.000 |

| Model | Condition | C − D (percentage points) | 95% interval |
|---|---|---|---|
| M1 hist+LR | baseline | +0.0 | [−2.5, +2.5] |
| M2 CNN | baseline | −10.1 | [−16.0, −5.5] |
| M2 CNN | normalized | +39.7 | [+29.4, +48.8] |
| M3 MobileNetV3 | baseline | +6.3 | [−4.6, +16.9] |
| M3 MobileNetV3 | normalized | +4.9 | [−5.0, +14.6] |
| M4 EfficientNet-B0 | baseline | −10.1 | [−17.4, −3.0] |
| M4 EfficientNet-B0 | normalized | −2.5 | [−11.3, +6.2] |

### C. Exploratory and descriptive detail moved from the main text

**TABLE S33.** Acquisition statistics of the two source-label classes and of condition C (plotted in Figure 2 of the main text). Median short side and file size are header fields; mean brightness is the mean RGB value at 64 × 64 on a 0–1 scale. kB = 1000 bytes.

| Group | n | File pattern | Median short side (px) | Mean file size (kB) | Mean brightness |
|---|---|---|---|---|---|
| Kaggle authentic-labeled | 272 | `images*.jpg` (100%) | 223 | 6.0 | 0.767 |
| Kaggle counterfeit-labeled | 238 | `Screenshot*.png` (100%) | 405 | 339.2 | 0.555 |
| Condition C (external, authentic) | 150 | device photograph (JPEG) | 2448 | 1,655.9 | 0.162 |

Region substitution overwrote one region of each normalized external image after resizing to 224 × 224 and before the forward pass. The inner region is a centered square of 158 × 158 px (0.4975 of the frame); the outer region is its complement (0.5025). Fills are the ImageNet channel mean or standard Gaussian noise in standardized space. Because any substitution is itself a distribution shift, only the asymmetry between the two area-matched regions is interpreted. The border ring and center box of the occlusion analysis (Section S-I-J) are not area-matched and are shown for comparison. Figure S13 illustrates the intervention.

**TABLE S34.** Region substitution on conditions C and D for the exploratory normalized M3 and M4. Each cell is specificity after overwriting one region (area fraction in parentheses after the region name); the intact row reproduces the value of record. Parentheses in cells: change from intact, in percentage points.

| Region overwritten | Fill | M3, cond. C | M3, cond. D | M4, cond. C | M4, cond. D |
|---|---|---|---|---|---|
| — (intact) | — | 0.773 | 0.725 | 0.807 | 0.832 |
| outer half-frame (0.5025) | mean | 0.280 (−49.3) | 0.275 (−45.0) | 0.487 (−32.0) | 0.611 (−22.1) |
| inner half-frame (0.4975) | mean | 0.800 (+2.7) | 0.738 (+1.3) | 0.807 (+0.0) | 0.859 (+2.7) |
| outer half-frame (0.5025) | noise | 0.273 (−50.0) | 0.483 (−24.2) | 0.373 (−43.3) | 0.530 (−30.2) |
| inner half-frame (0.4975) | noise | 0.713 (−6.0) | 0.785 (+6.0) | 0.853 (+4.7) | 0.906 (+7.4) |
| border ring (0.642) | mean | 0.233 (−54.0) | 0.201 (−52.3) | 0.260 (−54.7) | 0.396 (−43.6) |
| center box (0.161) | mean | 0.887 (+11.3) | 0.852 (+12.8) | 0.853 (+4.7) | 0.919 (+8.7) |

> **FIGURE S13.** `figures/fig16_region_substitution.pdf` — The region-substitution intervention on one condition C photograph, after normalization and resizing to the 224 × 224 model input. (a) Intact. (b, c) Outer region overwritten with the ImageNet channel mean or Gaussian noise. (d, e) Inner region overwritten in the same two ways. Photograph from the Mendeley *Mobile-Captured Pharmaceutical Medication Packages* archive, CC BY 4.0.

**TABLE S35.** Exploratory normalized models of M2 to M4 at seed 42: Split B test accuracy and specificity on conditions C and D, beside the baseline values. Intervals are 95% Wilson on k/n. The normalization caps the short side at 128 px, rescales mean brightness to 0.5 and re-encodes as JPEG at quality 40, in that order, for every image; its axes were chosen after the condition C result.

| Model | Condition | Split B accuracy | Condition C | Condition D |
|---|---|---|---|---|
| M2 CNN | baseline | 0.865 | 0/150 = 0.000 [0.000, 0.025] | 15/149 = 0.101 [0.062, 0.160] |
| M2 CNN | normalized | 0.865 | 129/150 = 0.860 [0.795, 0.907] | 69/149 = 0.463 [0.385, 0.543] |
| M3 MobileNetV3 | baseline | 0.946 | 100/150 = 0.667 [0.588, 0.737] | 90/149 = 0.604 [0.524, 0.679] |
| M3 MobileNetV3 | normalized | 0.932 | 116/150 = 0.773 [0.700, 0.833] | 108/149 = 0.725 [0.648, 0.790] |
| M4 EfficientNet-B0 | baseline | 0.905 | 9/150 = 0.060 [0.032, 0.110] | 24/149 = 0.161 [0.111, 0.229] |
| M4 EfficientNet-B0 | normalized | 0.919 | 121/150 = 0.807 [0.736, 0.862] | 124/149 = 0.832 [0.764, 0.884] |
