# Auditing Provenance Confounding in Image Authenticity Classification: A Counterfeit-Medicine Case Study

**Sophie Zhu** <sup>1,\*</sup>

<sup>1</sup> Mira Costa High School, Manhattan Beach, CA 90266, USA

\* Correspondence: sophiezhu2028@gmail.com; ORCID 0009-0004-2403-910X

---

**Abstract:** **Background/Objectives:** Image-based screening of medicine packaging has been reported to reach high accuracy, but the datasets behind those results are rarely checked for differences in how the two classes were acquired. When the classes are collected by different routes, acquisition metadata alone can predict the label. We describe a provenance audit that tests for this before training and apply it to a public counterfeit-medicine dataset. **Methods:** The audit fits a study's intended classifier to acquisition metadata alone, on the study's own leakage-controlled partition; its score shows whether an acquisition shortcut is available, not whether a model used it. We audited a public dataset of 510 images, trained four model families under a naive and a near-duplicate-grouped split, and evaluated them on two independently acquired external image sets. **Results:** The audit returned 1.000: every counterfeit-labeled file was a PNG screen capture and every authentic-labeled file a JPEG photograph, and three header fields reproduced the labels without decoding a pixel. Internal accuracy reached 0.838 to 0.987, and near-duplicate grouping changed it by at most 6.8 points. Under an acquisition shift, the model with the highest internal accuracy classified 9 of 150 independently sourced authentic photographs correctly (6.0% specificity). On a balanced external set of 46 regulator-confirmed falsified products and 46 authentic-labeled photographs, balanced accuracy ranged from 0.478 to 0.652, and only one model excluded chance. **Conclusions:** Internal accuracy on this dataset does not measure authentication ability. A provenance audit identifies this kind of shortcut cheaply and before training, and belongs alongside external validation, not in place of it.

**Keywords:** counterfeit medicine; provenance confounding; shortcut learning; dataset bias; data leakage; external validation; image classification; medical product screening

---

## 1. Introduction

### 1.1. Background

Substandard and falsified medical products are a persistent global health problem, concentrated in low- and middle-income countries and in unregulated online supply chains [1,2]. Much falsified product is visually imperfect, with misprinted cartons, wrong color separations or missing batch information, so image-based screening from a consumer smartphone is an attractive triage tool. Several groups have applied convolutional neural networks (CNNs) to photographs of medicine packaging and reported high binary accuracy [3–6]. A related clinical literature addresses drug identification, which asks which drug is shown rather than whether the product is genuine [7,8].

Pharmaceutical authentication has no shared benchmark. Each of the five studies located by our targeted search built or adopted its own image set, and none reported a check for confounding between acquisition conditions and label (Table S26, which also gives the search terms and databases). In one study the counterfeit class is produced by digitally editing authentic images [4] and in another by a generative model [5], so the two classes come from two different image pipelines. The one study that captured both classes on a common Raspberry Pi rig [3] reports the lowest accuracy in Table S26, 88.75%, although the studies differ too much in dataset, task and sample size for this to be a comparison. The dataset audited here is not a community benchmark: as of 13 September 2026 its Kaggle listing recorded 662 downloads and 3 public notebooks, and our search located no peer-reviewed study using it.

### 1.2. Provenance Confounding

Datasets that ask whether an object is genuine often cannot obtain both classes by the same route. Authentic examples are abundant, while verified counterfeit stock is hard to obtain for research, so the counterfeit class is often assembled another way: by screen-capturing regulator bulletins, scraping a different corpus, editing authentic images or generating examples with a model. Acquisition method affects file format, encoded size, resolution, compression, color rendering and often backdrop, so such a substitution can make the classes differ in ways unrelated to the property being labeled. We call this **class-conditional provenance confounding**, or provenance confounding for short. Because every partition of a single pool inherits the association, in-distribution validation does not reveal it, and because acquisition is rarely documented, the reporting record is silent (Figure 1).

Acquisition variables are of two kinds. $A_{\mathrm{pure}}$ holds attributes fixed by how the file was produced and stored, which the photographed object cannot influence: container format, encoder settings, filename pattern and embedded timestamps. $A_{\mathrm{mix}}$ holds attributes determined jointly by acquisition and content, such as encoded size, stored dimensions, aspect ratio and mean brightness. A high audit score on $A_{\mathrm{pure}}$ is close to decisive, because storage format is never a property of the photographed object. A high score on $A_{\mathrm{mix}}$ is weaker evidence, because the separation may reflect a real difference between the objects.

> **FIGURE 1.** `figures/fig15_mechanism.pdf` — How asymmetric class sourcing becomes a label-predictive acquisition signal, and where that signal can be detected. The boxes describe the general mechanism; the gray line beneath each reports this study's measurement of that step on the case-study dataset. The audit reads the third box, which is reachable from a file listing before any model exists.

The failure this produces is well documented. Networks readily adopt decision rules that exploit superficial but predictive correlations and then fail where those correlations are absent [9]. Zech et al. [10] showed that pneumonia detectors trained on radiographs from three hospital systems learned to predict the hospital and degraded substantially at an unseen site. Later audits report scanner-, site- and manufacturer-level signal in medical images [11,12], and published COVID-19 radiograph detectors were found to rely on dataset-source confounds rather than pathology [13]. Grommelt et al. [14] report the file-format version of the problem in generated-image detection, where real images are lossy JPEGs and generated images lossless PNGs, so that detectors partly become JPEG detectors. Provenance confounding differs from site confounding mainly in its cause. Because one class could not be obtained by the procedure that produced the other, the association can be complete rather than partial, and datasets at risk can be identified from how their classes were sourced.

### 1.3. Objectives

Most methods for diagnosing a confounded classifier act after training and need both the images and a trained model [13]. Ong Ly et al. [15] showed across 13 medical datasets that shortcut learning of data-acquisition biases frequently leads to overestimated performance, by up to 20% on average, and proposed a bias-corrected estimate of external accuracy. Checks on the data themselves also exist. Fitting a classifier to metadata to test whether it predicts a label is a familiar dataset-bias check [16], and G-AUDIT [17] measures how much patient and acquisition attributes reveal the label in medical datasets. We adapt this idea to image-authenticity data as a provenance audit that runs before training, inside the study's own leakage-controlled partition and with the classifier the study intends to use, and we specify how its score is read. We apply it to the Kaggle *Fake vs Real Medicine* set [18], 661 images distributed with no data card and no stated acquisition protocol. We then ask how much of the dataset's apparent accuracy survives two corrections fixed in advance, a near-duplicate-grouped split [19] and evaluation on independently acquired images, for four model families ranging from a 97-parameter linear baseline to a 4-million-parameter pretrained backbone. An exploratory analysis asks whether removing the audited acquisition statistics removes the shortcut. The audit procedure is the main contribution, and the case study is the evidence for it. How often provenance confounding occurs is not estimated.

## 2. Materials and Methods

### 2.1. Study Design

The study comprises a provenance audit of one public counterfeit-medicine dataset, four model families trained on it under two split designs, one internal and two external evaluations, and an exploratory normalization with probes of what the corrected models use (Figure S1). Counterfeit is the positive class throughout, so recall (sensitivity) is the fraction of counterfeits called counterfeit and specificity the fraction of authentic images called authentic. Accuracy is reported only for sets holding both classes. A set holding one class yields only a specificity or a recall, which cannot distinguish a working decision rule from a shifted operating point. Table 1 summarizes the three evaluations. The split labels A to E follow the code and the supplement.

**TABLE 1.** The three evaluations, and what each can measure. ROC-AUC = area under the receiver operating characteristic curve.

| | Internal grouped test | External acquisition-shift test | Balanced external test |
|---|---|---|---|
| Classes held | both (35 counterfeit, 39 authentic) | authentic only (150; 149) | both (46 and 46) |
| What shifts from training | nothing | capture: device, lighting, backdrop, country | source: two archives unrelated to the pool |
| What is standardized | — | — | file-level acquisition (format, encoder, resolution), by construction |
| How labels are established | dataset's own labels, which the confound tracks | archive's own labels, authentic only | counterfeit: regulator confirmed; authentic: labeled, not verified |
| Quantity it can measure | accuracy | specificity only | accuracy, balanced accuracy, recall, specificity, F1, ROC-AUC |

The provenance audit, the split comparison with its paired leakage experiment and the baseline evaluation on the first acquisition-shift condition were fixed by protocol before any of them ran. The balanced external evaluation was designed after the one-sided results, but models, preprocessing, threshold and metrics were settled before the set was built, and it was scored once. The normalization, the attribution and region-substitution analyses and the second acquisition-shift condition were developed after the external failure was observed and are exploratory (Section S-I-F).

### 2.2. Data Sources, Inclusion and Exclusion

Three public sources were inventoried (Table S1). The Kaggle *Fake vs Real Medicine* set [18] holds 661 unique files, with its license stated as "Unknown". Roboflow *Counterfeit_med_detection* v4 [20] holds 4,260 files under CC BY 4.0, including the publisher's own 3× rotation and exposure augmentation. The Mendeley *Mobile-Captured Pharmaceutical Medication Packages* archive [21] holds 3,900 files across six devices under CC BY 4.0.

The primary source is a single-uploader Kaggle contribution, last updated 13 October 2025, with no data card, no collection protocol and no per-image provenance. Counterfeit-labeled files are named `Screenshot YYYY-MM-DD HHMMSS.png`, with embedded timestamps falling in a small number of capture sessions, while authentic-labeled files are named `imagesNN.jpg`. The bundled split does not partition the data: counting unique filenames, the `train/` folder lists all 661 while `val/` (453) and `test/` (449) are proper subsets of it, with 286 filenames common to all three. We discarded it and built our own (Section 2.5).

The Roboflow source was excluded for two reasons. First, 57 of its 57 unique counterfeit source images are institutional advisory graphics carrying a regulator's logo and the ground-truth label as literal text, while 263 of its 263 plain product photographs are authentic-labeled, a modality confound that metadata alone does not detect (Section S-I-T). Second, the two sources are not independent. Perceptual-hash clustering, confirmed visually, found 202 clusters containing images from both, so 42.3% of the Kaggle pool has a near-duplicate in the Roboflow source, sometimes differing only by a 90° rotation. Treating them as independent sources would leak training data into an ostensibly external evaluation.

The modeling pool is therefore built from the Kaggle pool alone. After rule-based exclusion and de-duplication it contains 510 images in 480 product-identity groups, 272 authentic and 238 counterfeit (Sections S-I-A and S-IV; Table S25).

### 2.3. Product-Identity Grouping and De-duplication

Neither the Kaggle nor the Roboflow source carries product-identity labels, so near-duplicate clustering was used as a proxy. A 64-bit perceptual hash [22] is computed at all four cardinal orientations of each image and the numeric minimum taken as a rotation-canonical hash:

$$h(x) = \min_{\theta \in \{0°, 90°, 180°, 270°\}} \mathrm{pHash}\big(R_\theta(x)\big) \tag{1}$$

Pairs at Hamming distance 0 are treated as true duplicates, and one copy is removed. Pairs at distance 1 to 8 are assigned to the same cluster. Section S-I-Y sweeps the threshold (Table S22): no cluster mixes the two class labels up to distance 10, and no conclusion drawn from the split comparison turns on the choice. Two dissimilar photographs of one package would not be grouped at any threshold, so the clusters approximate product identity rather than establish it.

### 2.4. The Provenance Metadata Audit

The audit asks whether acquisition variables alone predict the label. It needs a labeled image dataset, the partition the study will use and the classifier family the study intends to use. No external data, annotation, training run or pixel decoding is involved, and on this dataset it runs from a file listing in seconds. The procedure has four steps.

1. Enumerate the acquisition variables obtainable without decoding an image: container format, encoded file size, stored dimensions and the aspect ratio they imply. Filename patterns and embedded timestamps are recorded separately, because they are trivially removable and their absence proves nothing.
2. Partition the data exactly as the study will, inside its own leakage-controlled split, so that the audit inherits the grouping the models receive.
3. Fit the intended classifier to those variables alone, once per variable and once on all of them jointly. Report held-out accuracy with an interval, against chance, using balanced accuracy where the classes are imbalanced.
4. Read $A_{\mathrm{pure}}$ and $A_{\mathrm{mix}}$ separately. Report pixel-derived statistics such as mean brightness in a separate row, since they require decoding and depend partly on content.

The score is the held-out accuracy of the acquisition-only classifier. It shows that a provenance shortcut is available, not that any model used it, and no threshold is proposed (Table S19 records how the values measured here were read). In this study the audit classifier is a logistic regression (LR) fitted on each split's own training partition to container format, log₁₀ encoded file size, log₁₀ short-side resolution and aspect ratio, singly and jointly, with 95% Wilson intervals. Mean brightness, the mean RGB value at 64 × 64 on a 0–1 scale, is fitted separately as a pixel-derived proxy. A deterministic rule assigning `.png` to counterfeit is evaluated over the whole pool without fitting. The same procedure was applied to six further archives from their public file listings (Tables S18 and S20; Section S-I-W) and to the finished balanced external set (Section 2.9).

### 2.5. Leakage-Controlled Partitioning

Two partitions of the modeling pool were built so that the leakage effect could be measured. Split A is a naive random 70:15:15 class-stratified partition at the image level; none of the studies in Table S26 reports a grouped or identity-aware split. Split B is a 70:15:15 class-stratified partition at the near-duplicate cluster level, so that no near-duplicate photograph of the same product appears in more than one partition, and its training partition carries `StratifiedGroupKFold` indices for 5-fold cross-validation. An assertion verifies zero product-identity overlap between Split B partitions on every run. Under Split A, 9 of 480 product-identity groups (1.9%) have members in more than one partition, and 230 of 510 images (45.1%) are assigned differently under the two designs. Split A holds 357/77/76 images and Split B 357/79/74 over 336/72/72 product groups.

"Leakage-free" in this paper means free of product-identity leakage. It says nothing about acquisition, which no partition of this pool can separate from class (Section 4.2).

### 2.6. Model Architectures and Training

Four model families were evaluated, from 97 learned parameters to a 4-million-parameter pretrained backbone (Figure S2). **M1** (97 learned parameters) is a logistic regression with balanced class weights on a 96-dimensional red-green-blue (RGB) histogram (32 bins per channel) of the image resized to 224 × 224. It cannot see spatial structure. **M2** (23,938 trainable parameters) is a small CNN with three convolutional blocks of 16, 32 and 64 channels (Conv3×3, BatchNorm, ReLU, MaxPool2×2) and a global-average-pooling head with dropout 0.5 (Section S-I-Q). **M3** (1,154 trainable and 927,008 frozen parameters) is an ImageNet-pretrained MobileNetV3-Small [23] with a frozen feature extractor and a `Dropout(0.3) → Linear(576, 2)` head. **M4** (2,562 trainable and 4,007,548 frozen parameters) is the same design with EfficientNet-B0 [24] and a `Dropout(0.3) → Linear(1280, 2)` head. M3 and M4 are therefore linear probes on a fixed representation.

M2 to M4 were trained with Adam at 1 × 10⁻³ (selected on the Split A training and validation partitions alone), batch size 32, class-weighted cross-entropy, a 50-epoch cap with early stopping on validation loss, and the best-validation-loss checkpoint retained (Tables S2 and S9). Training augmentation is rotation ±12°, brightness and contrast jitter of ±0.25, `RandomResizedCrop` at scale 0.85–1.0 and Gaussian blur with kernel 3 and σ ∈ [0.1, 0.8]. No flip is used, because mirrored packaging text cannot occur in deployment. M1 is fitted by `LogisticRegression(max_iter=2000, class_weight="balanced")` without augmentation. The decision threshold is 0.5 throughout. Seed sensitivity was assessed at seeds 42 to 46 (Section S-I-U).

### 2.7. Internal Evaluation

Each model was evaluated on the held-out test partition of both splits, with n = 76 for Split A and n = 74 for Split B. Reported quantities are accuracy, balanced accuracy, sensitivity, specificity, precision, F1 and area under the receiver operating characteristic curve (ROC-AUC) with 95% percentile bootstrap intervals (Table S3), with curves, confusion matrices, error counts, calibration and CPU cost in the supplement (Figures S4 to S6; Tables S7, S8 and S10). The Split B test partition, 35 counterfeit and 39 authentic images, is the internal grouped test. Its authentic-class accuracy, reported as k of 39, is the in-distribution reference for external specificity.

Because Split A and Split B do not share a test set, their difference mixes leakage with the effect of testing on different images (Table S4). A paired design separates the two (Section S-I-V, Tables S16 and S17). One test set is held fixed and two training sets are built around it that differ only in whether the near-duplicate mates of the test images are admitted, with everything else identical. This design was run across five seeds.

### 2.8. Independent Acquisition-Shift Evaluation

Condition C (Split C) is 150 photographs from the Mendeley archive [21], one per distinct product, taken in a different country by different photographers using different camera hardware and a different backdrop protocol from the modeling pool. None of the 150 images matched anything in the pool within the near-duplicate threshold. Condition D (Split D) is the same archive's "iphone 11 pro" subset: 149 unique images covering the same 150 packages, photographed on different hardware under a deliberately different lighting protocol, with mean brightness 0.389 against condition C's 0.162 and the training pool's 0.668. The two conditions are not pixel-interchangeable (Section S-I-Y). The two conditions share one archive, one set of packages and one dark backdrop. Both hold authentic images only, so they measure specificity, and they are compared as independent proportions rather than pooled. Condition C is confirmatory and condition D exploratory. A synthetic counterfeit proxy of 150 perturbed copies of the condition C photographs, a corruption-robustness test in the spirit of ImageNet-C [25], is reported in the supplement only (Sections S-I-B and S-I-I).

### 2.9. Balanced External Evaluation

This set holds 92 photographs, 46 counterfeit and 46 authentic, from two independent sources. It is the only external evaluation in the study with both classes present. The counterfeit class is regulator-confirmed. The authentic class was not independently verified for authenticity, since a photograph of a carton labeled *Drug X* does not establish that its contents were made by the named manufacturer. We therefore call it the authentic-labeled reference class, and the set serves as a two-class external stress test rather than a gold-standard authentication benchmark.

The counterfeit class is one photograph from each of 46 U.S. Food and Drug Administration (FDA) and World Health Organization (WHO) medical-product alerts confirming a falsified product (Split E). Several frames per alert show one seizure, so one frame per alert was chosen by a rule that consults no model (the within-case median-brightness frame), making the alert the unit of independence. The eligibility screen that reduced 202 candidates to the 150-image regulatory source was one reviewer's single pass (Section S-VIII, Table S28).

The authentic class could not come from any source already in the study without reproducing the confound: the regulators' authentic-labeled images are mostly flat carton artwork, a mean-brightness gap of +0.233 against the falsified photographs (Section S-IX-A). It was therefore sourced from Wikimedia Commons, which carries per-file license and authorship, and product-matched to the 46 alerts. Of 3,568 candidates, automated screens on title, resolution, flatness, brightness and duplication and a recorded subject-matter review left 174 photographs of current retail medicine packages (Section S-IX-B). The final 46 were chosen by nearest-neighbour brightness matching to the counterfeit frames, spread over 29 distinct products. The subject-matter review was performed by the generative-AI assistant described in Section 2.12, working to the author's protocol; it assigned no class label. Neither class had any near-duplicate in the project's raw image tree.

Both classes then pass through one identical ingestion pipeline: conversion to RGB, short side resampled to 448 px, and re-encoding at one JPEG quality with metadata stripped. This holds container format, encoder, encoder settings and stored resolution constant across the classes by construction. Because the counterfeit frames are re-encoded, their recall here is not numerically comparable to recall in their native encodings (Section S-IX-D). The finished set was audited by the procedure of Section 2.4 and locked. It returns a balanced accuracy of 0.598 on encoded file size, 0.435 on aspect ratio, 0.413 on mean brightness and 0.620 on all three jointly, against 1.000 for the case-study pool, and the between-class brightness gap is +0.005 (Section S-IX-E). Models were loaded from the same persisted Split B checkpoints as every other table, at the 0.5 threshold, and the set was scored once (Section S-IX-F).

### 2.10. Exploratory Normalization and Region-Substitution Analysis

The audit names three acquisition statistics on which the modeling pool and condition C separate: resolution, brightness and compression. To test whether intervening on them changes the external result, three label-free operators were composed. $T_{\mathrm{res}}$ caps the short side at $s = 128$ px, below the 10th percentile of the Kaggle pool's short-side distribution. $T_{\mathrm{bright}}$ rescales the image to mean $\mu^\star = 0.5$ and clips to [0, 1]. $T_{\mathrm{comp}}$ re-encodes through JPEG at quality $q = 40$ and decodes back. The composed operator

$$T(x) = T_{\mathrm{comp}} \circ T_{\mathrm{bright}} \circ T_{\mathrm{res}}\,(x) \tag{2}$$

is applied before augmentation, identically to training, validation, test and external images. It never references the label. M2 to M4 were retrained with it under otherwise identical settings. M1 bypasses it, because normalization collapses its in-distribution accuracy toward chance while recovering nothing externally (Section S-I-O).

The axes were chosen after Table 2 showed those statistics separating the training pool from condition C, so for this experiment condition C is development data rather than an untouched external set. Equation (2) is an experimental probe, not a proposed method. As a sensitivity analysis, a rule confined to the Split B training partition was used to re-derive the axes (Section S-I-S, Table S15), and the operator it nominates was run end to end (Section S-VII, Table S27). Ablations are in Sections S-I-N to S-I-X.

Region substitution tests which part of the frame the corrected models need. One region of each external image is overwritten before the forward pass, either a center square covering half the frame or its complement, which is area-matched to within half a point. Two fills are used, the ImageNet channel mean and Gaussian noise. Only the asymmetry between the two regions is interpretable, since any substitution is itself a distribution shift. Occlusion sensitivity and a qualitative Grad-CAM [26] categorization are reported in Section S-I-J.

### 2.11. Statistical Analysis

The test partitions are small, at 74 to 76 images, so every point estimate carries a 95% interval: a percentile bootstrap [27], stratified by class on the balanced set, or a Wilson score interval on counts. Pairwise model comparisons on the shared Split B test partition use exact McNemar tests [28] with Holm–Bonferroni correction over the six pairs (power analysis in Section S-I-H and Table S5). The paired leakage experiment reports a paired bootstrap difference across five seeds with a McNemar test. Group differences in brightness are described with a two-sample *t*-test. Intervals describe sampling uncertainty for one trained model. Training-run variability was assessed across five seeds (Section S-I-U, Table S23), and only separations much larger than the seed spread are treated as findings.

### 2.12. Reproducibility, Software and Use of Generative AI

All code and derived artifacts are available at `https://github.com/sophiezla/counterfeit-drug`, archived at the concept DOI 10.5281/zenodo.21936720. Software versions are pinned in the committed `requirements.txt`: PyTorch 2.7.1 [29] and torchvision 0.22.1 (CPU builds), scikit-learn 1.9.0 [30], NumPy 2.3.2, pandas 3.0.3, SciPy 1.18.0, Pillow 11.3.0 and imagehash 4.3.2. All runs are CPU-only and deterministic at seed 42. The external evaluations are scored from the persisted checkpoints rather than from retrained copies, and Section S-V lists the command that regenerates each table and figure. Four reproducibility defects in earlier versions of the pipeline were fixed and every affected analysis re-run (Sections S-I-G and S-I-U).

Claude, an AI assistant developed by Anthropic and accessed through the Claude Code command-line interface, was used over the course of the project to assist in drafting and revising the text and in writing and debugging the analysis and figure-generation code. The specific model version varied across that period and is not recorded per session; the final editorial revision used Claude Opus 5.5. The assistant performed one task that produced data rather than text: the per-image subject-matter eligibility screen of the balanced external test's authentic candidates (Section 2.9), carried out to the author's protocol and published in full per image (Section S-IX-B). That screen decided whether a candidate was a photograph of a retail medicine package. It assigned no class label and made no authenticity judgement. All experimental design decisions and interpretations are the author's. Every number reported here was produced by committed code from committed data and verified by re-execution, and no result, citation or reference was generated by a language model without verification against a primary source.

## 3. Results

### 3.1. Acquisition Metadata Reproduces the Labels

All 510 labels are predictable from container format alone: 272 of 272 authentic files are `.jpg` photographs and 238 of 238 counterfeit files are `.png` screenshots. This holds in the archive as distributed, where all 240 files in `Fake/` are `Screenshot*.png` and all 421 in `Real/` are `images*.jpg`, so any study using this dataset inherits it, and a classifier reading nothing but the file extension achieves 100% accuracy.

The two classes differ on every axis a file header exposes (Table 2). Brightness also differs (*t* = 17.0 on 508 degrees of freedom, *p* < 10⁻¹⁵). The external acquisition-shift set lies far outside both training classes, roughly 10 times higher in linear resolution and darker than even the counterfeit class (Figure 2).

**TABLE 2.** The two acquisition pipelines in the Kaggle pool, and the external acquisition-shift set's position relative to both. Median short side and file size are header fields. Mean brightness is the mean RGB value at 64 × 64 on a 0–1 scale and requires decoding the image. kB = 1000 bytes.

| Group | n | Capture pattern | Median short side (px) | Mean file size | Mean brightness |
|---|---|---|---|---|---|
| Kaggle authentic | 272 | `images*.jpg` (100%) | 223 | 6.0 kB | 0.767 |
| Kaggle counterfeit | 238 | `Screenshot*.png` (100%) | 405 | 339 kB | 0.555 |
| Condition C external (authentic) | 150 | device photograph | **2448** | 1,656 kB | **0.162** |
| Condition C synthetic (proxy counterfeit) | 150 | perturbed copy of the above | 2448 | 1,018 kB | 0.153 |

Fitted to header fields alone, the audit classifier reproduces the labels (Table 3). Container format reaches 1.000 on both splits. Encoded file size alone classifies the leakage-controlled test partition perfectly, 74 of 74, above every trained model (Table S3), and size, resolution and aspect ratio together reach 1.000 without the file extension. Brightness, the pixel-derived proxy, is the weakest candidate at 0.716 on Split B despite having the largest *t*-statistic, because its class distributions overlap while the file-size distributions barely do.

> **FIGURE 2.** `figures/fig03_capture_confound.pdf` — Distributions of the three acquisition statistics that separate the classes, for the two Kaggle classes and the external acquisition-shift set (Split C, condition C). (a) Mean brightness, with group means. (b) Short-side resolution, log scale, with medians. (c) Encoded file size, log scale, with means. The external set lies outside the range of both training classes on all three axes.

**TABLE 3.** The provenance audit on the case-study pool. LR = logistic regression, fitted on each split's own training partition. Every row but the last reads only what a file listing and a header parse provide; the last is a pixel-derived proxy. Resolution and file size enter as log₁₀. The deterministic rule is not fitted. Intervals are 95% Wilson.

| Classifier | Features | Split A test (n = 76) | Split B test (n = 74) |
|---|---|---|---|
| Deterministic rule: `.png` → counterfeit | container format | 510/510 = **1.000** [0.993, 1.000] over the whole pool | — |
| Header LR | container format | **1.000** [0.952, 1.000] | **1.000** [0.951, 1.000] |
| Header LR | encoded file size | 0.974 [0.909, 0.993] | **1.000** [0.951, 1.000] |
| Header LR | short-side resolution | 0.947 [0.872, 0.979] | 0.946 [0.869, 0.979] |
| Header LR | aspect ratio | 0.645 [0.533, 0.743] | 0.595 [0.481, 0.699] |
| Header LR | size + resolution + aspect ratio | **1.000** [0.952, 1.000] | **1.000** [0.951, 1.000] |
| Pixel-derived proxy LR | mean brightness | 0.829 [0.729, 0.897] | 0.716 [0.605, 0.806] |

The simplest model's decision function shows the same thing. The near-white bin (248–255) of each channel carries M1's three largest coefficients, at β = −2.86, −2.84 and −2.95, while 93 of the remaining coefficients lie within ±0.35 of zero (Section S-I-P, Figure S12). M1's accuracy of 83.8% therefore appears to be driven by the prevalence of near-white pixels rather than by packaging.

As supporting evidence outside the case study, the audit was run from public file listings on six further archives across four application areas, chosen for accessibility rather than by any sampling frame (Table S18; Section S-I-W), and on the Roboflow archive as shipped (Table S20). Four of the seven were scorable, including the case study; two return 1.000 on format and two sit at or near chance. Two generated-image datasets built for the same task by different people return 1.000 and 0.577. These runs also showed two failure modes. The Roboflow archive, although severely confounded, returns 0.500 on format and 0.717 on the full feature set, because the publisher resized to 640 × 640 and re-encoded before release. Genuine and forged signatures in BHSig260, digitized by one procedure, return exactly 0.500 on format but 0.843 on encoded size, most likely because forged signatures differ in ink coverage. These results support no estimate of how often provenance confounding occurs.

### 3.2. Internal Evaluation Stays High Under Leakage Control

In-distribution, the four models reach 0.842, 0.868, 0.934 and 0.987 on the naive split and 0.838, 0.865, 0.932 and 0.919 on the leakage-controlled one. The deltas are +0.004, +0.004, +0.002 and +0.068. No pairwise McNemar test between models is significant; Holm–Bonferroni correction raises the smallest adjusted *p* from 0.118 to 0.711 (Tables S3 to S5).

The paired leakage experiment gives the controlled estimate. Of the 74 test images, 28 are exposed to a near-duplicate mate. Across five seeds, admitting the mates moves M2 by +0.3 points [−1.9, +2.4] by paired bootstrap, with McNemar *p* = 1.000, and M3 and M4 are unchanged at every seed, though both sit at ceiling, at 1.000 and 0.987 (Table S17). Near-duplicate leakage is therefore a small effect on this dataset.

### 3.3. Independent Acquisition-Shift Evaluation

Both acquisition-shift conditions hold authentic images only, so every figure in Table 4 is an external authentic-class specificity.

**TABLE 4.** The acquisition-shift experiment: authentic-class specificity under two capture conditions on approximately the same products. Both model conditions come from the current deterministic pipeline at seed 42, so the baseline and normalized columns differ only by the operator of Equation (2); Section S-I-U gives both across five seeds. An archived run predating three-way normalization (104/150 for M3, 5/150 for M4) came from a pipeline carrying two defects since fixed and is superseded (Section S-I-G). The in-distribution reference is authentic-class accuracy on each model's own Split B test partition (n = 39). Intervals are 95% Wilson on the counts given as k/n.

| Model | In-distribution authentic accuracy (k of 39) | Condition C, baseline (n = 150) | Condition C, normalized (n = 150) | Condition D, normalized (n = 149) | C → D change (points) |
|---|---|---|---|---|---|
| M1 hist+LR | 27/39 = 0.692 [0.536, 0.814] | 0/150 = 0.000 [0.000, 0.025] | 0/150 = 0.000 [0.000, 0.025] | 0/149 = 0.000 [0.000, 0.025] | 0.0 |
| M2 CNN | 33/39 = 0.846 [0.703, 0.928] | 0/150 = 0.000 [0.000, 0.025] | 129/150 = **0.860** [0.795, 0.907] | 69/149 = **0.463** [0.385, 0.543] | **−39.7** |
| M3 MobileNetV3 | 38/39 = 0.974 [0.868, 0.995] | 100/150 = 0.667 [0.588, 0.737] | 116/150 = 0.773 [0.700, 0.833] | 108/149 = 0.725 [0.648, 0.790] | −4.9 |
| M4 EfficientNet-B0 | 38/39 = 0.974 [0.868, 0.995] | 9/150 = 0.060 [0.032, 0.110] | 121/150 = 0.807 [0.736, 0.862] | 124/149 = 0.832 [0.764, 0.884] | +2.6 |

Two of the four models classified none of the 150 external authentic photographs correctly (Figure 3). M4, whose 0.987 on the naive split is the highest internal accuracy in the study, classified 9 of 150 correctly, a specificity of 6.0%, although it classified 38 of 39 authentic images in its internal test partition correctly. Its behavior is consistent with recognizing this dataset's photography, which Section 3.1 shows was available to it, rather than authentic packaging. Seed 42 is not a central draw: its condition C value is the lowest of five seeds for M2 and M4 and the highest for M3 (Section S-I-U).

> **FIGURE 3.** `figures/fig08_external_generalisation.pdf` — Authentic-class accuracy in distribution (Split B test partition, n = 39) against external specificity on condition C (Split C, n = 150), before and after the normalization of Equation (2), per model. The values are those of Table 4. M1 bypasses the normalization, so its two external bars show the same 0.0% measurement.

### 3.4. Balanced External Evaluation

The balanced set pairs 46 regulator-confirmed falsified products with 46 authentic-labeled photographs (Section 2.9). It audits at 0.620 against 1.000 for the case-study pool.

**TABLE 5.** The balanced external test: 92 photographs, 46 authentic-labeled and 46 regulator-confirmed counterfeit, scored once from the persisted Split B checkpoints at a decision threshold of 0.5 fixed before the set was built. Counterfeit is the positive class. Because the set is balanced, accuracy and balanced accuracy coincide. Intervals are 95% stratified bootstrap percentiles. The confusion matrix is given as TN / FP / FN / TP.

| Model | Confusion (TN/FP/FN/TP) | Balanced external accuracy | Counterfeit recall | Authentic specificity | Precision | F1 | ROC-AUC |
|---|---|---|---|---|---|---|---|
| M1 hist+LR | 0 / 46 / 2 / 44 | 0.478 [0.446, 0.500] | **0.957** [0.891, 1.000] | **0.000** [0.000, 0.000] | 0.489 [0.471, 0.500] | 0.647 [0.617, 0.667] | 0.422 [0.307, 0.541] |
| M2 CNN | 14 / 32 / 16 / 30 | 0.478 [0.380, 0.576] | 0.652 [0.522, 0.783] | 0.304 [0.174, 0.435] | 0.484 [0.411, 0.556] | 0.556 [0.460, 0.642] | 0.403 [0.289, 0.523] |
| M3 MobileNetV3 | 30 / 16 / 26 / 20 | 0.543 [0.446, 0.641] | 0.435 [0.283, 0.587] | 0.652 [0.522, 0.783] | 0.556 [0.424, 0.690] | 0.488 [0.354, 0.612] | 0.641 [0.523, 0.755] |
| M4 EfficientNet-B0 | 33 / 13 / 19 / 27 | **0.652** [0.554, 0.750] | 0.587 [0.435, 0.717] | 0.717 [0.587, 0.848] | 0.675 [0.564, 0.795] | 0.628 [0.506, 0.736] | **0.713** [0.603, 0.816] |

Three of the four models are indistinguishable from chance. Balanced accuracy runs 0.478, 0.478, 0.543 and 0.652, and only M4's interval excludes 0.500. M1 and M2 have ROC-AUC point estimates below 0.5, at 0.422 and 0.403. No pair of models is separated by more than sampling noise. M1 is a degenerate classifier: it calls 90 of 92 images counterfeit, for 0.957 recall at 0.000 specificity and an F1 of 0.647, a figure that looks respectable in isolation. Performance on the acquisition-shift test did not predict performance here. M2, which has the highest external specificity after normalization (0.860 on condition C, Table 4), returns balanced accuracy 0.478 and ROC-AUC 0.403.

### 3.5. Exploratory Normalization and Region Analysis

#### 3.5.1. Exploratory Normalization

Retrained with the operator of Equation (2), M2, M3 and M4 recover 86.0%, 77.3% and 80.7% external specificity on condition C (Table 4), at an in-distribution cost within 1.4 points. Across five seeds the paired gain is +85.9 points [+81.7, +89.7] for M2, +76.0 [+69.9, +81.5] for M4 and +0.9 [−6.9, +8.8] for M3, so no benefit is claimed for M3 (Section S-I-Z, Table S23). The train-only rule nominates the same three axes, and its operator averages 0.842 external specificity against the reported operator's 0.818 (Table S27).

The recovery did not hold for M2 on the second capture condition: its specificity falls 39.7 points from condition C to D, from 0.860 to 0.463 (a mean drop of 28 points across seeds). The two backbones hold theirs, with M3 moving −4.9 points and M4 +2.6. Because both conditions share one dark backdrop, this is stability across a device and lighting shift only. Composition order alone moves external specificity by 50 points while moving in-distribution accuracy by 2.7 (Table S21).

#### 3.5.2. Residual Dependence on the Outer Region

Region substitution shows what the corrected backbones need in order to call an external photograph authentic (Table 6). In all eight model-by-condition-by-fill combinations, overwriting the outer region costs 22 to 50 points of specificity, while overwriting the area-matched center region costs at most 6.0 points and more often helps. The decisive evidence therefore lies outside the center of the frame, where the packaging is usually placed. The outer region contains the backdrop, lighting, staging and any part of the carton that extends past the center square, and this experiment does not separate them.

**TABLE 6.** Region substitution on the two acquisition-shift conditions. Each cell is authentic-class specificity after overwriting one region of the model's input; the intact row reproduces the value of record. "Outer" is everything outside a center square covering half the frame and "inner" is the square itself, so the two are area-matched (0.5025 against 0.4975). The last two rows reuse the occlusion analysis's 0.642 border ring and 0.161 center box, which are *not* area-matched. Parenthesized values are changes from intact, in points.

| Region overwritten | Fill | M3, cond. C | M3, cond. D | M4, cond. C | M4, cond. D |
|---|---|---|---|---|---|
| — (intact) | — | 0.773 | 0.725 | 0.807 | 0.832 |
| Outer half-frame | mean | **0.280** (−49.3) | **0.275** (−45.0) | **0.487** (−32.0) | **0.611** (−22.2) |
| Inner half-frame | mean | 0.800 (+2.7) | 0.738 (+1.3) | 0.807 (0.0) | 0.859 (+2.7) |
| Outer half-frame | noise | **0.273** (−50.0) | 0.483 (−24.2) | **0.373** (−43.3) | 0.530 (−30.2) |
| Inner half-frame | noise | 0.713 (−6.0) | 0.785 (+6.0) | 0.853 (+4.7) | 0.906 (+7.4) |
| Border ring (0.642) | mean | 0.233 (−54.0) | 0.201 (−52.4) | 0.260 (−54.7) | 0.396 (−43.6) |
| Center box (0.161) | mean | 0.887 (+11.3) | 0.852 (+12.8) | 0.853 (+4.7) | 0.920 (+8.7) |

## 4. Discussion

### 4.1. Main Finding

On this dataset the label is a function of how each file was acquired. A classifier can reach high in-distribution accuracy without looking at the packaging, and the audit detects this from a file listing before any model is trained. The external evaluations show the consequence. The audit shows that a shortcut is available, not that a model used it; the external results supply that evidence. A low audit score does not clear a dataset, since publisher-side resizing and re-encoding erase the traces the audit reads without removing the confound, as the Roboflow archive shows.

The exploratory analysis adds one caution. Removing the three audited statistics raised external specificity for two models, but the corrected backbones then depended on the outer region of the frame, which in these photographs is largely set by whoever took the picture rather than by the manufacturer, and the gain did not hold for M2 on a second capture. Removing one acquisition signal can leave another in place, so a correction to the data needs the same audit as the original data.

### 4.2. Why Internal Validation Failed

Every counterfeit-labeled image was produced by one capture pipeline and every authentic-labeled image by another, so any partition of the pool places the same class–acquisition relationship on both sides of the split in the same proportion. The grouped split kept near-duplicate photographs of one product out of both training and test sets on every run, but it could not make the dataset provenance-independent. Near-duplicate leakage [19] is the fault image-based studies most often correct, and here its controlled effect was 0.3 points against an external collapse to 6.0% specificity. In the hospital-level confounding reported in radiology [10,13], the association between site and label was partial. Here it is exact across all 510 images, which is why it can be detected before training rather than only after an external failure.

### 4.3. Implications for Dataset Construction and Evaluation

Provenance auditing is useful before training any image classifier whose classes were assembled from different sources, and medical-product screening datasets are often assembled that way by necessity. Stating how each class was acquired, and whether both came from the same procedure, is a single sentence that would have made this study's central finding visible without any analysis. Each item below would have surfaced a defect reported here, and none requires a model.

- *Acquisition-source balance.* Every capture condition, including camera, operator, location and lighting, should contribute both classes.
- *Format and encoding parity.* Store both classes in one container format at one encoder setting, with neutral filenames.
- *Report the audit score before the model score.* Publish the $A_{\mathrm{pure}}$ result, container format at minimum, and the partition on which it was computed.
- *Ship a raw archive and document the collection protocol*, since publisher-side re-encoding hides the confound from a cheap audit.
- *Verify the shipped split.* One archive audited here ships a training folder that is a superset of both others.

External evaluation should include both classes wherever possible, and the audit should be re-run after any correction. The evaluation this study most needs is a two-class external set in which both classes are photographed against varied surfaces, with varied cameras and lighting, by people unconnected to the training data. It would test the outer-region cue directly and measure two-class performance under acquisition shift. Other directions are fine-tuning the backbones, a survey of authenticity datasets with a defined sampling frame, and attribution measured inside annotated product boxes.

### 4.4. Limitations

The study rests on one small counterfeit-medicine dataset whose confound is total. The modeling pool holds 510 images, the internal test partitions 74 to 76 and the balanced set 92, so every interval is wide, no pair of models is separated, and the ablations and region substitutions are single executions. The further archives support no prevalence estimate, and the mechanism proposed in Section 1.2 would be refuted by a survey finding confounds no more often in separately sourced collections than in jointly sourced ones; that survey has not been done.

The balanced external set's authentic class is labeled, not verified. A counterfeit among the 46 would be scored as a false positive when a model calls it counterfeit; the number of such cases cannot be bounded, and the direction of the resulting bias in any one model's row is unknown. The set's own audit is 0.620 rather than 0.500, with encoded file size the residual axis, and both classes are convenience samples of what regulators release and volunteers upload. The authentic class's subject-matter screen was performed by an AI assistant rather than a second human reviewer, and the counterfeit side's screen by one reviewer, without inter-rater agreement; the per-image records are published, and Table S28 bounds the counterfeit screen's effect at 0.06 of recall.

Acquisition diversity is limited. The two acquisition-shift conditions share one backdrop and contain no counterfeit image, and the balanced set shifts source rather than capture, so two-class performance under acquisition shift is not measured, and nothing here estimates field performance on medicines a patient might be handed.

The normalization and region analyses are exploratory. The axes were chosen with knowledge of condition C, the operator was not compared against domain-adaptation methods, which would consume target data, and region substitution identifies which region a decision requires, not which feature inside it. Both transfer models are frozen backbones, so nothing here measures a fine-tuned network. Table S29 records the evidence status of each claim.

## 5. Conclusions

On the public counterfeit-medicine dataset audited here, container format alone predicts all 510 labels, and internal accuracy of up to 0.987 therefore does not measure authentication ability. A leakage-controlled split does not correct this, and independently acquired photographs exposed the failure. The results do not support interpreting the evaluated models as counterfeit-medicine authentication systems. A provenance audit asks, cheaply and before training, whether acquisition variables alone can predict the label. It should be run before training and again after any correction, alongside external evaluation on data the authors did not collect, with both classes present.

## Supplementary Materials

The following supporting information can be downloaded at the journal's website and is archived with the code at the release named in the Data Availability Statement. Section S-I: dataset, method and experimental detail, comprising S-I-A complete manual quality and modality review; S-I-B synthetic counterfeit proxy; S-I-C environment; S-I-D training protocol; S-I-E frozen-backbone feature caching; S-I-F evaluation protocol and metrics; S-I-G four reproducibility defects, disclosed; S-I-H in-distribution performance and the leakage comparison; S-I-I synthetic counterfeit-proxy stress test; S-I-J attribution audit; S-I-K error analysis; S-I-L computational cost; S-I-M calibration; S-I-N to S-I-R and S-I-X normalization ablations; S-I-S deriving the axes without the external set; S-I-T a taxonomy of provenance defects; S-I-U seed-to-seed variance; S-I-V a paired measurement of near-duplicate leakage; S-I-W the provenance audit on datasets other than the case study; S-I-Y the near-duplicate threshold; and S-I-Z a paired comparison of the baseline and normalized conditions. Section S-II: limitations, with the evidence for and against each. Section S-III: complete per-axis ablation record. Section S-IV: exclusion rules applied to the modeling pool. Section S-V: reproduction commands, table by table. Section S-VI: image sources used by prior work. Section S-VII: the operator a train-only audit nominates. Section S-VIII: the counterfeit source's eligibility screen. Section S-IX: the balanced external test's construction, screen and audit.

Figure S1: data provenance, splitting protocol and evaluation design; Figure S2: the four model families, with exact parameter counts; Figure S3: Split A versus Split B leakage comparison; Figure S4: ROC curves, both in-distribution partitions; Figure S5: precision–recall curves, both partitions; Figure S6: confusion matrices, all four models, both partitions; Figure S7: Split B training and validation curves; Figure S8: reliability curves and calibration; Figure S9: confusion matrices on the synthetic proxy; Figure S10: Grad-CAM attribution maps on external images; Figure S11: normalization ablations; Figure S12: M1 logistic-regression coefficients and logit decomposition.

Table S1: modality composition of the 510-image modeling pool; Table S2: hyperparameters; Table S3: in-distribution test performance; Table S4: leakage quantification; Table S5: pairwise McNemar tests; Table S6: synthetic counterfeit-proxy results; Table S7: error counts pooled over both internal test partitions; Table S8: measured single-image CPU cost; Table S9: epochs run and best-validation-loss epoch; Table S10: calibration; Table S11: per-axis ablation on M4; Table S12: gray-world white balance as a fourth axis; Table S13: normalization extended to all four models; Table S14: sensitivity of the normalization to its constants; Table S15: train-only axis derivation; Table S16: the paired leakage design; Table S17: leaky minus clean across five seeds; Table S18: the provenance audit run from public file listings; Table S19: how to read an audit score; Table S20: the audit on two independently published datasets as shipped; Table S21: composition order of the three operators; Table S22: sensitivity of the near-duplicate clustering to its Hamming threshold; Table S23: normalized minus baseline on the two external conditions across five seeds; Table S24: all normalization conditions; Table S25: every exclusion rule, with counts; Table S26: image sources used by located prior work; Table S27: the reported operator against the one a train-only audit nominates; Table S28: external counterfeit recall on the full regulatory source under five screen settings; Table S29: evidence status of the claims in the paper.

## Author Contributions

Conceptualization, S.Z.; methodology, S.Z.; software, S.Z.; validation, S.Z.; formal analysis, S.Z.; investigation, S.Z.; data curation, S.Z.; writing—original draft preparation, S.Z.; writing—review and editing, S.Z.; visualization, S.Z. The author has read and agreed to the published version of the manuscript.

## Funding

This research received no external funding.

## Institutional Review Board Statement

Not applicable. This study involves neither human nor animal subjects. All images are photographs of pharmaceutical packaging from public archives, none depicts an identifiable person, and no personal or patient data were accessed.

## Informed Consent Statement

Not applicable.

## Data Availability Statement

All code and derived artifacts are publicly available at `https://github.com/sophiezla/counterfeit-drug` and archived at Zenodo under the concept DOI 10.5281/zenodo.21936720, which resolves to the most recent release; `README.md` and `CITATION.cff` name the release accompanying this manuscript, with earlier releases marked superseded. The release holds the data pipeline, the four model implementations, every analysis and figure script, the per-image statistics and split assignments, the persisted checkpoints, and the sources of this manuscript and its supplement. The repository contains no images. The Kaggle archive [18] carries no license grant, so only derived per-image statistics, split assignments and filenames are redistributed, and readers reproducing the pool must obtain it from the original listing. The Mendeley [21] and Roboflow [20] datasets are distributed under CC BY 4.0. Grad-CAM overlays of Kaggle images and the manual-review contact sheets are excluded for the same licensing reason and are regenerated by committed scripts from a reader's own copy of the archives. The balanced external test is a reproducible recipe rather than a publishable dataset, because 140 of the 150 regulatory photographs are held under metadata-only permission and the Wikimedia Commons files carry per-file license terms. What is published is the candidate manifest with every license and source URL, the per-image screen record, the per-image predictions, and the five scripts that rebuild it (Section S-V). Six analysis scripts read only committed artifacts and reproduce Table 3, Tables S18, S20 and S22, the direct exposure count and the external intervals in seconds, without image data or training.

## Acknowledgments

The author thanks the maintainers of the three public datasets used here [18,20,21]. During the preparation of this manuscript and study, the author used Claude (Anthropic), accessed through the Claude Code command-line interface (model versions varied over the project and were not recorded per session; the final editorial revision used Claude Opus 5.5), for the purposes of drafting and revising text, writing and debugging analysis and figure-generation code, and performing the per-image subject-matter eligibility screen of the balanced external test's authentic candidates described in Sections 2.9 and 2.12. The author has reviewed and edited the output and takes full responsibility for the content of this publication.

## Conflicts of Interest

The author declares no conflict of interest. The author has no affiliation with the maintainers of any dataset examined here and no commercial interest in any authentication product.

## References

1. World Health Organization. Substandard and Falsified Medical Products. Available online: https://www.who.int/news-room/fact-sheets/detail/substandard-and-falsified-medical-products (accessed on 13 September 2026).
2. Ozawa, S.; Evans, D.R.; Bessias, S.; Haynie, D.G.; Yemeke, T.T.; Laing, S.K.; Herrington, J.E. Prevalence and Estimated Economic Burden of Substandard and Falsified Medicines in Low- and Middle-Income Countries: A Systematic Review and Meta-analysis. *JAMA Netw. Open* **2018**, *1*, e181662. https://doi.org/10.1001/jamanetworkopen.2018.1662
3. Ramos, R.R.T.; Samonte, K.R.B.; Manlises, C.O. Medicine Authentication Based on Image Processing Using Convolutional Neural Networks. In Proceedings of the 16th International Conference on Computer and Automation Engineering (ICCAE), 2024; pp. 278–282. https://doi.org/10.1109/ICCAE59995.2024.10569752
4. Motwani, K.; Dsouza, R.; Dsouza, R.; Jose, J. Counterfeit Medicine Detection Using Deep Learning. *Int. J. Innov. Res. Technol.* **2022**, *9*, 818–821.
5. Thomson, B.S.; Varuna, W.R. An Intelligent Counterfeit Medicine Classification Prediction System Using Modified YOLO: A Single Stage Object Detector. *TPM Test. Psychom. Methodol. Appl. Psychol.* **2025**, *32*, 1073–1088.
6. Thomson, B.S.; Varuna, W.R. Detecting Counterfeit Medicines Utilizing Artificial Intelligence Technique. *Int. J. Creat. Res. Thoughts* **2025**, *13*, i322–i329.
7. Ting, H.-W.; Chung, S.-L.; Chen, C.-F.; Chiu, H.-Y.; Hsieh, Y.-W. A Drug Identification Model Developed Using Deep Learning Technologies: Experience of a Medical Center in Taiwan. *BMC Health Serv. Res.* **2020**, *20*, 312. https://doi.org/10.1186/s12913-020-05166-w
8. Al-Hussaeni, K.; Karamitsos, I.; Adewumi, E.; Amawi, R.M. CNN-Based Pill Image Recognition for Retrieval Systems. *Appl. Sci.* **2023**, *13*, 5050. https://doi.org/10.3390/app13085050
9. Geirhos, R.; Jacobsen, J.-H.; Michaelis, C.; Zemel, R.; Brendel, W.; Bethge, M.; Wichmann, F.A. Shortcut Learning in Deep Neural Networks. *Nat. Mach. Intell.* **2020**, *2*, 665–673. arXiv:2004.07780.
10. Zech, J.R.; Badgeley, M.A.; Liu, M.; Costa, A.B.; Titano, J.J.; Oermann, E.K. Variable Generalization Performance of a Deep Learning Model to Detect Pneumonia in Chest Radiographs: A Cross-Sectional Study. *PLoS Med.* **2018**, *15*, e1002683. https://doi.org/10.1371/journal.pmed.1002683
11. Hill, B.G.; Koback, F.L.; Schilling, P.L. The Risk of Shortcutting in Deep Learning Algorithms for Medical Imaging Research. *Sci. Rep.* **2024**, *14*, 29224. https://doi.org/10.1038/s41598-024-79838-6
12. Seah, J.; Tang, C.; Buchlak, Q.D.; Milne, M.R.; Holt, X.; Ahmad, H.; Lambert, J.; Esmaili, N.; Oakden-Rayner, L.; Brotchie, P.; Jones, C.M. Do Comprehensive Deep Learning Algorithms Suffer from Hidden Stratification? A Retrospective Study on Pneumothorax Detection in Chest Radiography. *BMJ Open* **2021**, *11*, e053024. https://doi.org/10.1136/bmjopen-2021-053024
13. DeGrave, A.J.; Janizek, J.D.; Lee, S.-I. AI for Radiographic COVID-19 Detection Selects Shortcuts over Signal. *Nat. Mach. Intell.* **2021**, *3*, 610–619. https://doi.org/10.1038/s42256-021-00338-7
14. Grommelt, P.; Weiss, L.; Pfreundt, F.-J.; Keuper, J. Fake or JPEG? Revealing Common Biases in Generated Image Detection Datasets. In *Computer Vision – ECCV 2024 Workshops*; Lecture Notes in Computer Science; Springer: Cham, Switzerland, 2025; pp. 80–95. https://doi.org/10.1007/978-3-031-92089-9_6
15. Ong Ly, C.; Unnikrishnan, B.; Tadic, T.; Patel, T.; Duhamel, J.; Kandel, S.; Moayedi, Y.; Brudno, M.; Hope, A.; Ross, H.; McIntosh, C. Shortcut Learning in Medical AI Hinders Generalization: Method for Estimating AI Model Generalization without External Data. *npj Digit. Med.* **2024**, *7*, 124. https://doi.org/10.1038/s41746-024-01118-4
16. Torralba, A.; Efros, A.A. Unbiased Look at Dataset Bias. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2011; pp. 1521–1528. https://doi.org/10.1109/CVPR.2011.5995347
17. Drenkow, N.; Pavlak, M.; Harrigian, K.; Zirikly, A.; Subbaswamy, A.; Farhangi, M.M.; Petrick, N.; Unberath, M. Detecting Dataset Bias in Medical AI: A Generalized and Modality-Agnostic Auditing Framework. *arXiv* **2025**, arXiv:2503.09969.
18. Jha, S.K. Fake vs Real Medicine Dataset (Images). Kaggle. Available online: https://www.kaggle.com/datasets/surajkumarjha1/fake-vs-real-medicine-datasets-images (accessed on 13 September 2026).
19. Öner, M.Ü.; Cheng, Y.-C.; Lee, H.K.; Sung, W.-K. Training Machine Learning Models on Patient Level Data Segregation Is Crucial in Practical Clinical Applications. *medRxiv* **2020**, preprint. https://doi.org/10.1101/2020.04.23.20076406
20. Harshini, T.G.R. Counterfeit_med_detection, Version 4 (Multiclass Export). Roboflow Universe, November 2022. Available online: https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection (accessed on 28 August 2026).
21. Abdelmaksoud, E.; Gadallah, A.; Asad, A. Mobile-Captured Pharmaceutical Medication Packages. Mendeley Data, V1, 2022. https://doi.org/10.17632/bjy2svvmn8.1
22. Zauner, C. Implementation and Benchmarking of Perceptual Image Hash Functions. M.Sc. Thesis, Upper Austria University of Applied Sciences, Hagenberg, Austria, July 2010.
23. Howard, A.; Sandler, M.; Chu, G.; Chen, L.-C.; Chen, B.; Tan, M.; Wang, W.; Zhu, Y.; Pang, R.; Vasudevan, V.; Le, Q.V.; Adam, H. Searching for MobileNetV3. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), 2019; pp. 1314–1324. arXiv:1905.02244.
24. Tan, M.; Le, Q.V. EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks. In Proceedings of the International Conference on Machine Learning (ICML), 2019. arXiv:1905.11946.
25. Hendrycks, D.; Dietterich, T. Benchmarking Neural Network Robustness to Common Corruptions and Perturbations. In Proceedings of the International Conference on Learning Representations (ICLR), 2019. arXiv:1903.12261.
26. Selvaraju, R.R.; Cogswell, M.; Das, A.; Vedantam, R.; Parikh, D.; Batra, D. Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization. In Proceedings of the IEEE International Conference on Computer Vision (ICCV), 2017. arXiv:1610.02391.
27. Efron, B.; Tibshirani, R.J. *An Introduction to the Bootstrap*; Chapman & Hall: New York, NY, USA, 1993.
28. McNemar, Q. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. *Psychometrika* **1947**, *12*, 153–157.
29. Paszke, A.; Gross, S.; Massa, F.; et al. PyTorch: An Imperative Style, High-Performance Deep Learning Library. In Advances in Neural Information Processing Systems (NeurIPS), 2019.
30. Pedregosa, F.; Varoquaux, G.; Gramfort, A.; et al. Scikit-learn: Machine Learning in Python. *J. Mach. Learn. Res.* **2011**, *12*, 2825–2830.
