# When File Format Predicts the Label: A Case Study of Provenance Confounding in Medicine-Authenticity Image Classification

**Sophie Zhu** <sup>1,\*</sup>

<sup>1</sup> Mira Costa High School, Manhattan Beach, CA 90266, USA

\* Correspondence: sophiezhu2028@gmail.com; ORCID 0009-0004-2403-910X

---

**Abstract:** Image classifiers can reach high held-out accuracy by learning how each class was acquired rather than what distinguishes the objects shown. We examined whether this happens in a public medicine-authenticity image dataset of 510 images, 238 labeled counterfeit and 272 labeled authentic by the uploader, with no independent verification of product status. We audited file-level acquisition properties, trained four image models under image-level and near-duplicate-grouped splits, and tested them on externally acquired photographs. File format alone reproduced all 510 source labels: every counterfeit-labeled file was a PNG named as a screenshot and every authentic-labeled file a JPEG image. The models reached internal accuracies of 0.838 to 0.974, and grouping near-duplicates changed accuracy little. On 150 externally acquired authentic photographs, three of the four models recognized at most 9 as authentic; EfficientNet-B0, with 0.905 internal accuracy, recognized 9. On a balanced external set of regulator-confirmed falsified and authentic-labeled photographs with equalized file formats, balanced accuracy ranged from 0.391 to 0.609. In exploratory analyses, equalizing resolution, brightness and compression improved specificity for two models under one capture condition, but the gain was not stable. Provenance should be audited before internal image-classification accuracy is interpreted as evidence of object-level authentication.

**Keywords:** shortcut learning; dataset bias; provenance confounding; acquisition shift; external validation; image classification; data leakage; falsified medicines

---

## 1. Introduction

An image classifier learns whatever separates the classes in its training data. If the classes also differ in how their images were produced, the classifier can learn that difference instead of the visual property the labels are meant to describe. Deep networks are known to adopt such shortcuts, which work on the data at hand and fail when the incidental regularity changes [@geirhos]. Many of these regularities are introduced when a dataset is assembled. Standard recognition datasets can be identified from their images alone [@torralba], and differences in capture device and environment are a central obstacle to transfer across domains [@zhou]. In medical imaging, pneumonia detectors learned to recognize the hospital that produced a radiograph [@zech], COVID-19 classifiers relied on signals tied to the data source rather than to pathology [@degrave]. Other audits have found performance resting on features other than the target finding [@hill; @seah], and in experiments on 13 medical datasets, hidden acquisition biases frequently inflated performance estimates [@onglyp]. In generated-image detection, detectors trained on datasets in which real images were stored as JPEG and generated images as PNG partly learned to detect JPEG compression [@grommelt].

Acquisition confounding is hardest to avoid when the two classes come from different sources. The usual safeguard against optimistic evaluation, keeping near-duplicate or same-subject images on one side of the train–test split [@oner], does not address it. Grouped splitting prevents a model from being tested on near-copies of its training images. It cannot remove an association that runs through the whole dataset: if every image of one class was captured one way and every image of the other class another way, every partition inherits that difference.

Medicine-authenticity classification is a setting where this problem is likely. Substandard and falsified medical products are a recognized public-health problem [@who; @ozawa], and several groups have trained convolutional neural networks to classify photographs of medicine packaging as authentic or counterfeit, with high reported accuracy [@ramos; @motwani; @thomsonyolo; @thomsonijcrt]. Authentic packaging is easy to photograph, whereas verified counterfeit stock is hard to obtain, so the counterfeit class is often assembled differently, for example by editing authentic images [@motwani] or with a generative model [@thomsonyolo]. None of the four pharmaceutical-authentication studies we located reports whether acquisition conditions predict the class label (Table S26).

Some acquisition differences can be checked before any image model is trained. File format, file size and resolution can be read from a file listing, and a simple classifier fitted to them shows whether the labels can be predicted without looking at the image content. This is an application of existing dataset-bias tests [@torralba] and is closely related to G-AUDIT, which measures how strongly acquisition and patient attributes reveal the label in medical datasets [@drenkow]. Unlike most shortcut diagnostics [@degrave; @trivedi], such a check needs no trained model or attribution map. The task also differs from drug identification, which asks which product is shown rather than whether it is genuine [@ting; @alhussaeni].

This paper applies such a check to the public Kaggle *Fake vs Real Medicine* dataset [@kaggle] and follows its result through internal and external evaluation. The contributions are:

1. We identify a complete association between source label and file provenance in a public medicine-authenticity dataset, using a simple provenance audit that can be run before model training.
2. We show that high internal accuracy persists under near-duplicate-grouped splitting but fails under acquisition shift and on a balanced external set.
3. In exploratory analyses, we show that equalizing several obvious acquisition statistics does not remove dependence on capture context.

## 2. Materials and Methods

### 2.1. Study Design and Data

Figure 1 summarizes the study. The primary analyses were the provenance audit, internal evaluation under two partitioning designs, and evaluation on externally acquired photographs (condition C). In this study the audit was run retrospectively, after the condition C result. It uses only file properties that exist before any model is trained, and its result does not depend on any model output, so it is a check that could have been run first. A second acquisition condition (condition D), a paired leakage experiment and a balanced two-class external test were added as follow-up analyses. Provenance normalization and region substitution are exploratory. Section S-X-A gives the full chronology.

> **FIGURE 1.** `figures/fig01_design.pdf` — Study design and main results. Solid boxes are primary analyses; dashed boxes are follow-up or exploratory analyses. The line beneath each box gives its main result.

The Kaggle dataset contains 661 unique files and lists its license as unknown. It has no data card, and its labels are the uploader's. We therefore call its images counterfeit-labeled and authentic-labeled. The audit result does not depend on whether these labels are correct. The bundled train, validation and test folders overlap (the training folder contains all 661 files), so we discarded them. The author reviewed every file by eye and excluded 56: 47 with watermarks or stock-photo overlays (all authentic-labeled), 4 renders or web-page captures, and 5 with no packaging in frame (Section S-I-A, Table S25). Collapsing exact duplicates left a modeling pool of 510 images, 272 authentic-labeled and 238 counterfeit-labeled, showing cartons, blister packs and other immediate containers.

A second public source, Roboflow *Counterfeit_med_detection* [@roboflow], was not used. Its counterfeit-labeled source images are regulatory advisory graphics rather than product photographs, and 42.3% of the Kaggle pool has a near-duplicate in it, so it could serve neither as training data nor as an external test set (Section S-I-T). The external data are described in Section 2.5, and Table 1 summarizes all evaluation sets.

**TABLE 1.** Evaluation sets. The external sets come from archives unrelated to the modeling pool, photographed by different people with different devices.

| Set | Images | What differs from training | How labels are established | Reported |
|---|---|---|---|---|
| Internal test (Split B) | 35 counterfeit-labeled, 39 authentic-labeled | nothing | uploader's labels | accuracy and related metrics |
| Condition C | 150 authentic photographs, one device | device, lighting, backdrop, photographers | archive of retail packages; not verified | specificity |
| Condition D | 149 authentic photographs, another device | as for C; device and lighting also differ from C | as for C | specificity |
| Balanced external test | 46 falsified, 46 authentic-labeled | source archives, products, photographers | falsified: regulator confirmed; authentic-labeled: presumed genuine, not verified | balanced accuracy, recall, specificity |

### 2.2. Provenance Audit

The audit asks whether acquisition variables alone predict the label. We read four variables from each file without decoding the image: container format, encoded file size, short-side resolution and aspect ratio. A logistic regression with balanced class weights was fitted to each variable alone and to the non-format variables together, on the training partition of each split, and scored on its test partition. Mean brightness was fitted separately because it requires decoding the image. We also scored a fixed rule that assigns PNG files to the counterfeit-labeled class.

The variables differ in what a high score means. Container format is fixed by how a file was stored and cannot reflect the object in the picture, so a high score on format is strong evidence of provenance confounding. File size, resolution and brightness depend partly on content, so their scores are weaker evidence. A high audit score is a warning that internal accuracy may not reflect the intended task. A low score does not clear a dataset, because the audit sees only the variables it measures.

### 2.3. Near-Duplicate Grouping, Partitions and Internal Evaluation

The dataset has no product-identity labels. As an approximate identity safeguard, images were grouped by a rotation-invariant perceptual hash [@zauner]: images whose 64-bit hashes differed in at most 8 bits were placed in one near-duplicate group. The 510 images form 480 groups. Two dissimilar photographs of the same package would not be grouped, so the groups reduce near-duplicate leakage without establishing product identity (threshold sweep in Table S22).

Two 70:15:15 class-stratified partitions were built. Split A assigns individual images at random. Split B assigns whole near-duplicate groups, so no group appears in more than one partition. The test partitions hold 76 images (Split A) and 74 images (Split B). A paired experiment that varies only whether near-duplicates of the test images are included in training is described in Section S-I-V.

### 2.4. Image Models

Four model families were used to check that the result does not depend on one architecture: a logistic regression on a 96-bin color histogram (M1), a small three-block convolutional network trained from scratch (M2), and linear classifiers on frozen ImageNet features from MobileNetV3-Small (M3) [@mobilenet] and EfficientNet-B0 (M4) [@efficientnet] (Figure S2). Images were resized to 224 × 224. M2 to M4 were trained with the Adam optimizer at a learning rate of 1 × 10⁻³, selected on Split A. Training used batch size 32, class-weighted cross-entropy and early stopping on validation loss. Augmentation consisted of small rotations, brightness and contrast jitter, cropping and blur. The decision threshold was fixed at 0.5. Reported models were trained at seed 42, and results at four further seeds are in Section S-I-U. Full settings are in Table S2.

### 2.5. External Evaluation

By externally acquired we mean images that come from archives unrelated to the modeling pool and were photographed by different people with different devices. Conditions C and D come from the Mendeley *Mobile-Captured Pharmaceutical Medication Packages* archive [@mendeley], which contains photographs of 150 retail packages taken with six devices. Condition C is the 150 images from one device, which we take to be one per package. Condition D is the 149 images from a second device, taken under different lighting. The archive does not map files to packages, so the two conditions cannot be paired image by image. None of the condition C images had a near-duplicate in the modeling pool. Both sets contain authentic images only and yield specificity. They share one backdrop, so condition D changes device and lighting but not surroundings.

The balanced external test adds a two-class measurement. Its falsified class is one photograph from each of 46 WHO and FDA alerts, each confirming a falsified medical product. Its reference class is 46 authentic-labeled photographs of retail medicine packaging from Wikimedia Commons, found mainly with search terms taken from the alerts and chosen to match the falsified photographs in brightness. We labeled these images authentic on the presumption that retail packaging photographed for Commons is genuine. Their authenticity was not verified. An AI assistant made a first pass at the eligibility screens for both classes, using the author's written criteria, and the author then reviewed every decision. The screens removed, for example, frames that did not show a product and frames with captions naming the contents as falsified. Every image then passed through one pipeline: conversion to RGB, resizing of the short side to 448 px and re-encoding as JPEG at a single quality setting. File format and stored resolution are therefore identical across classes. We treat the set as a stress test rather than an authentication benchmark. Construction details and the screening records are in Sections S-VIII and S-IX.

### 2.6. Exploratory Analyses

After the condition C result, we asked whether equalizing the acquisition differences between the modeling pool and condition C would restore transfer. A fixed preprocessing step capped resolution, rescaled mean brightness and re-encoded every image as a low-quality JPEG, and M2 to M4 were retrained with it. Because condition C informed the choice of these three statistics, it was development data for this analysis. To see which part of the image the retrained M3 and M4 used, we overwrote either the central half or the outer half of each external image and measured the change in specificity (region substitution). Settings and ablations are in Section S-X-C and Sections S-I-N to S-I-X; occlusion and Grad-CAM [@gradcam] analyses, and a synthetic counterfeit proxy in the spirit of ImageNet-C [@hendrycks], are reported in Sections S-I-J and S-I-I.

### 2.7. Statistical Analysis

Audit accuracies and single-class proportions carry 95% Wilson score intervals. Other metrics carry 95% percentile bootstrap intervals [@efron] from 10,000 resamples stratified by class. Because related images are not independent, the bootstrap resamples whole near-duplicate groups on the internal test sets. On the balanced set it resamples search-term clusters in the authentic-labeled class, where several images show the same product, and single images in the falsified class, where each image comes from a different alert. Pairwise model comparisons use exact McNemar tests [@mcnemar] with Holm correction. Analyses used PyTorch [@pytorch] and scikit-learn [@sklearn]; software versions are listed in Section S-I-C.

## 3. Results

### 3.1. The Source Labels Were Completely Confounded with File Provenance

File format separates the two classes without exception. All 238 counterfeit-labeled files are PNG files named `Screenshot YYYY-MM-DD HHMMSS.png`, and all 272 authentic-labeled files are small JPEG files named `imagesNN.jpg`. The same holds in the archive as distributed. A rule that reads only the file extension reproduces all 510 labels (Table 2).

The other acquisition statistics also differ sharply between classes (Figure 2; Table S33). Counterfeit-labeled files have a median short side of 405 px against 223 px and a mean size of 339 kB against 6 kB. Fitted to header variables alone, the audit classifier reproduced every test label on both splits. File size alone, or size, resolution and aspect ratio together, also scored 1.000 on Split B, so removing the file extension would not remove the shortcut.

**TABLE 2.** The provenance audit. Held-out accuracy of a logistic regression (LR) fitted only to file-level variables on each split's training partition. The last row uses mean brightness, which requires decoding the image. Intervals are 95% Wilson.

| Classifier | Features | Split A test (n = 76) | Split B test (n = 74) |
|---|---|---|---|
| Rule: PNG → counterfeit-labeled | container format | 510/510 = 1.000 over the whole pool | — |
| LR | container format | 1.000 [0.952, 1.000] | 1.000 [0.951, 1.000] |
| LR | encoded file size | 0.974 [0.909, 0.993] | 1.000 [0.951, 1.000] |
| LR | short-side resolution | 0.947 [0.872, 0.979] | 0.946 [0.869, 0.979] |
| LR | aspect ratio | 0.645 [0.533, 0.743] | 0.595 [0.481, 0.699] |
| LR | size + resolution + aspect ratio | 1.000 [0.952, 1.000] | 1.000 [0.951, 1.000] |
| LR | mean brightness | 0.829 [0.729, 0.897] | 0.716 [0.605, 0.806] |

> **FIGURE 2.** `figures/fig02_acquisition.pdf` — Acquisition statistics of the two source-label classes and of the external condition C photographs. (a) Mean brightness. (b) Short-side resolution. (c) Encoded file size. Each point is one image; lines mark the mean (a, c) or median (b).

### 3.2. High Internal Performance Persisted After Near-Duplicate Control

All four models performed well on held-out data (Table 3). Accuracy was 0.842 to 0.974 on the image-level Split A and 0.838 to 0.946 on the grouped Split B. Split A minus Split B accuracy ranged from −2.5 to +6.8 percentage points. Because the two test sets contain different images, this is only a rough guide, but the paired experiment, which holds the test set fixed, also found little effect of near-duplicate leakage (Section S-I-V). No pair of models differed significantly on Split B (Table S32). Even the color-histogram model, which has no access to spatial structure, reached 0.838 (Section S-I-P).

Near-duplicate leakage therefore did not explain the high scores. The test partitions came from the same two acquisition pipelines as the training data, and grouping could not change that.

**TABLE 3.** Internal and external performance of the four models (without normalization). Split A and Split B accuracy are on the internal test partitions. The next three columns give authentic-class accuracy (specificity): on the 39 authentic-labeled Split B test images and on the external conditions C and D. The last column is balanced accuracy on the balanced external test (46 + 46). Intervals are 95% Wilson for counts and 95% cluster bootstrap for Split B accuracy and balanced external accuracy. Full metrics are in Tables S30 and S31.

| Model | Split A accuracy | Split B accuracy | Internal authentic (of 39) | Condition C (of 150) | Condition D (of 149) | Balanced external |
|---|---|---|---|---|---|---|
| M1 histogram + LR | 0.842 | 0.838 [0.757, 0.909] | 27 (0.692) | 0 (0.000) [0.000, 0.025] | 0 (0.000) [0.000, 0.025] | 0.478 [0.446, 0.500] |
| M2 small CNN | 0.842 | 0.865 [0.781, 0.934] | 32 (0.821) | 0 (0.000) [0.000, 0.025] | 15 (0.101) [0.062, 0.160] | 0.391 [0.307, 0.472] |
| M3 MobileNetV3 | 0.921 | 0.946 [0.892, 0.987] | 38 (0.974) | 100 (0.667) [0.588, 0.737] | 90 (0.604) [0.524, 0.679] | 0.609 [0.510, 0.700] |
| M4 EfficientNet-B0 | 0.974 | 0.905 [0.836, 0.961] | 35 (0.897) | 9 (0.060) [0.032, 0.110] | 24 (0.161) [0.111, 0.229] | 0.587 [0.484, 0.684] |

### 3.3. Acquisition Shift Exposed Poor Transfer

The internal results did not carry over to externally acquired photographs (Table 3; Figure 3a). EfficientNet-B0 illustrates the gap: it classified 90.5% of the grouped internal test set correctly, including 35 of its 39 authentic-labeled images, but recognized only 9 of 150 authentic photographs in condition C. The histogram model and the small CNN recognized none. Three of the four models called almost every external authentic photograph counterfeit. This pattern is consistent with a decision rule tied to the training pool's authentic-class acquisition pipeline rather than to the packaging. MobileNetV3 was the partial exception, at 0.667.

Condition D, a different device and lighting on packages from the same archive, gave the same pattern, with specificities of 0.000 to 0.604. Results at four further training seeds were similar (Section S-I-U).

> **FIGURE 3.** `figures/fig03_external.pdf` — Internal versus external performance. (a) Authentic-class accuracy on the internal Split B test set and specificity on conditions C and D, for the models trained without normalization; bars are labeled with the number of images called authentic, and whiskers are 95% Wilson intervals. (b) Balanced accuracy on the balanced external test, without normalization (circles) and with the exploratory normalization (squares), with 95% bootstrap intervals; the dashed line marks chance.

### 3.4. Balanced External Test and Exploratory Normalization

Conditions C and D contain one class, so they cannot show whether the models separate the two classes. The balanced test can. Its own audit scored 0.620 on file size, aspect ratio and brightness combined, against 1.000 for the modeling pool. Format and resolution carry no information because they are identical across classes (Section S-IX-E). On this set the models did not separate the falsified from the authentic-labeled images reliably (Table 3; Figure 3b). Balanced accuracy was 0.478, 0.391, 0.609 and 0.587 for M1 to M4. M1 called 90 of 92 images counterfeit, so its high recall (0.957) came with a specificity of 0.000. M2 was below chance. Only MobileNetV3's interval lay above 0.500, and only narrowly, on a set whose residual acquisition variables alone reached 0.620.

In the exploratory analysis, equalizing resolution, brightness and compression raised condition C specificity for M2 (from 0.000 to 0.860) and M4 (from 0.060 to 0.807), with similar internal accuracy (Table S35). The gain did not hold consistently: M2's specificity fell to 0.463 on condition D, the result was sensitive to details of the preprocessing (Table S21), and on the balanced set the normalized models scored 0.478 to 0.652. When the outer half of each external image was overwritten, the normalized models' specificity fell sharply, whereas overwriting the central half changed it little (Table S34). The outer region holds backdrop, lighting and staging, and sometimes part of the package. This result is consistent with continued reliance on capture context but does not identify the feature used.

## 4. Discussion

### 4.1. Main Finding

In this dataset the source label is a function of how each file was produced. Every counterfeit-labeled image is a PNG named as a screenshot and every authentic-labeled image a small JPEG, and file metadata reproduces all 510 labels without any pixel being examined. Four quite different image models reached high internal accuracy on these data, and the same models failed on photographs acquired elsewhere: three of the four recognized almost none of 150 authentic photographs, and none reliably separated falsified from authentic-labeled images on a balanced external set. Internal accuracy on this dataset therefore does not establish object-level authentication.

The audit establishes that acquisition variables alone predict the source labels. The external failures are consistent with the models relying on acquisition cues, but they do not show which features any model used.

### 4.2. Why Conventional Validation Missed It

Grouping images by near-duplicate cluster did what it is designed to do: no test image had a near-copy in training, and near-duplicate leakage turned out to be small. It could not address the larger problem. Every counterfeit-labeled image came from one pipeline and every authentic-labeled image from another, so every partition of the pool contained the same class–acquisition relationship, and a held-out test set could reward a model that had learned it. In pneumonia detection the association between hospital and label was partial [@zech]. In COVID-19 radiograph datasets that drew the two classes from different sources it was close to complete, but it was diagnosed from trained models [@degrave]. Here the association is complete and can be seen in a file listing before any model is trained.

The two external evaluations answered different questions. The acquisition-shift sets kept the task and removed the training pool's acquisition pipeline, exposing the collapse of specificity. The balanced set added the second class under a change of source. They did not agree on which model transferred best: the normalized M2 had the highest specificity on condition C and was at chance on the balanced set. Robustness to one shift did not imply robustness to another, and neither result could have been predicted from internal accuracy. The exploratory normalization points the same way: removing three measured acquisition statistics improved one external result, but the models' decisions still appeared to depend on capture context.

### 4.3. Practical Implications

The risk is not specific to medicines. When one class is easy to collect and the other is scarce, the scarce class may be assembled by a different route, such as screenshots, web scraping, digital editing or generation. The same PNG-versus-JPEG split has been reported in datasets for generated-image detection [@grommelt], and dataset-level audits such as G-AUDIT address the equivalent question for patient and acquisition attributes in medical imaging [@drenkow]. What this case adds is a complete instance, followed from the file listing through leakage-controlled testing to external failure, in an application where a misleading accuracy figure could be read as evidence of a working safety tool.

For image-classification studies whose classes may have been collected by different routes, the following steps would each have exposed the problem described here. The first three need no trained model.

- *Report how each class was acquired and stored.* A statement that the two classes came from different procedures would by itself have revealed the central finding.
- *Audit file-level properties on the partitions actually used.* Treat a high score, especially on file format, as a warning that internal accuracy may reflect provenance. Treat a low score as uninformative rather than as clearance, since spatial cues such as a background, and datasets re-encoded by their publisher, escape the audit.
- *Balance acquisition across classes.* Each camera, operator, location and background should contribute images of both classes, and both classes should be stored with the same format and encoder settings.
- *Evaluate on externally acquired images of both classes.* Repeat the audit after any correction, because a correction changes the pipeline.

### 4.4. Limitations and Next Steps

This is a case study of one small dataset whose confound is total. It shows what can happen, not how often it happens across datasets. The Kaggle labels are the uploader's and were not verified, so internal accuracy measures agreement with those labels. The authentic-labeled class of the balanced external set was presumed genuine rather than verified, and a falsified product among those images would be scored as an error whenever a model called it counterfeit. The external data are limited: the two acquisition-shift conditions come from one archive, share one backdrop and contain no counterfeit images. Two-class performance under a controlled acquisition shift was therefore not measured, and nothing here estimates field performance. The normalization and region analyses are exploratory and used condition C for development.

The evaluation this problem most needs is a two-class external set in which both classes are photographed by people unconnected to the training data, with varied cameras, lighting and backgrounds, and with authenticity established by laboratory analysis or chain of custody.

## 5. Conclusions

In the public medicine-authenticity dataset examined here, file format alone reproduces every source label. Because this association runs through the whole dataset, it survives both conventional and near-duplicate-grouped splitting, and image models reach high held-out accuracy without demonstrating object-level authentication. Externally acquired photographs exposed the failure. A simple provenance audit can reveal such a problem before model training, but it is a warning diagnostic, not a guarantee that a dataset is free of shortcuts, and validation on externally acquired images of both classes remains necessary.

## Supplementary Materials

The following supporting information can be downloaded at the journal's website and is archived with the code at the release named in the Data Availability Statement. Section S-I: dataset, method and experimental detail (S-I-A manual quality and modality review; S-I-B synthetic counterfeit proxy; S-I-C environment and software versions; S-I-D training protocol; S-I-E frozen-backbone feature caching; S-I-F evaluation protocol; S-I-G four reproducibility defects; S-I-H internal performance and leakage comparison; S-I-I synthetic proxy stress test; S-I-J attribution audit; S-I-K error analysis; S-I-L computational cost; S-I-M calibration; S-I-N to S-I-R and S-I-X normalization ablations; S-I-S train-only axis derivation; S-I-T taxonomy of provenance defects; S-I-U seed-to-seed variance; S-I-V paired leakage experiment; S-I-W audit of other datasets; S-I-Y near-duplicate threshold; S-I-Z baseline versus normalized comparison). Section S-II: limitations. Section S-III: per-axis ablation record. Section S-IV: exclusion rules. Section S-V: reproduction commands. Section S-VI: image sources used by prior work. Section S-VII: the train-only operator. Section S-VIII: falsified-class eligibility screen. Section S-IX: construction and audit of the balanced external test. Section S-X: analysis chronology, baseline-model analyses and exploratory detail.

Figures S1–S13: evaluation design; model families; leakage comparison; ROC and precision–recall curves; confusion matrices; training curves; calibration; synthetic proxy; Grad-CAM maps; normalization ablations; M1 coefficients; region-substitution illustration. Tables S1–S35: modality composition; hyperparameters; internal performance of the normalized models; leakage quantification; McNemar tests; synthetic proxy; error counts; computational cost; training epochs; calibration; normalization ablations (S11–S14, S21, S24); train-only axis derivation; paired leakage design and results (S16, S17); audits of other datasets (S18–S20); threshold sweep; seed comparison; exclusion rules; prior work; train-only operator; screen sensitivity; evidence status; full internal metrics (S30); balanced external test (S31); McNemar tests and condition C–D differences (S32); acquisition statistics (S33); region substitution (S34); normalized models (S35).

## Author Contributions

Conceptualization, S.Z.; methodology, S.Z.; software, S.Z.; validation, S.Z.; formal analysis, S.Z.; investigation, S.Z.; data curation, S.Z.; writing—original draft preparation, S.Z.; writing—review and editing, S.Z.; visualization, S.Z. The author has read and agreed to the published version of the manuscript.

## Funding

This research received no external funding.

## Institutional Review Board Statement

Not applicable. The study involves no human or animal subjects. All images are photographs of pharmaceutical packaging from public archives, and no personal or patient data were accessed.

## Informed Consent Statement

Not applicable.

## Data Availability Statement

Code and derived artifacts are available at `https://github.com/sophiezla/counterfeit-drug` and archived at Zenodo under the concept DOI 10.5281/zenodo.21936720; `README.md` and `CITATION.cff` name the release that accompanies this manuscript. The release contains the data pipeline, model code, every analysis and figure script, per-image statistics, split assignments, per-image predictions, persisted checkpoints, and the sources of this manuscript and its supplement. It redistributes no dataset images apart from the CC BY 4.0 Mendeley photographs shown, with attribution, in Figures S10 and S13. The Kaggle archive [@kaggle] carries no license grant, so only derived per-image statistics, split assignments and filenames are redistributed. The Mendeley [@mendeley] and Roboflow [@roboflow] datasets are distributed under CC BY 4.0. The balanced external test is distributed as a recipe, because most regulatory photographs are held under metadata-only permission and the Wikimedia Commons files carry per-file licenses; the release contains the candidate manifest with licenses and source URLs, the per-image screening records, the per-image predictions and the scripts that rebuild the set (Section S-V).

## Acknowledgments

The author thanks the maintainers of the public datasets used here [@kaggle; @roboflow; @mendeley]. During the preparation of this study and manuscript, the author used Claude (Anthropic), accessed through the Claude Code command-line interface (model versions varied and were not recorded per session; the final revision used Claude Opus 5.5), to draft and revise text, to write and debug analysis and figure code, to pre-flag possible watermarks during the manual review of the source dataset, and to make a first pass at the eligibility screens of the balanced external test's candidate images according to criteria defined by the author. The author reviewed every screening decision. The assistant did not assign any authenticity label, which came from the regulators and the image sources. The author made all scientific decisions, reviewed and edited all output, and takes full responsibility for the content of this publication.

## Conflicts of Interest

The author declares no conflicts of interest.

## References
