# Provenance Confounding in Image Authenticity Classification: Detection and a Counterfeit-Medicine Case Study

**SOPHIE ZHU**<sup>1</sup>

<sup>1</sup>Mira Costa High School, Manhattan Beach, CA 90266 USA (e-mail: sophiezhu2028@gmail.com)

ORCID: 0009-0004-2403-910X

Corresponding author: Sophie Zhu (e-mail: sophiezhu2028@gmail.com).

This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors. The manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic; see the disclosure in the Acknowledgment.

---

**ABSTRACT** In image datasets asking whether an object is genuine, the inauthentic class is scarcer and often obtained differently: screen-captured, scraped, edited, generated. The label then predicts the acquisition process, not the property of interest, and every held-out partition of that pool inherits the confound alike. We call this class-conditional provenance confounding. In a public counterfeit-medicine dataset every counterfeit-labeled file is a PNG screen capture and every authentic one a JPEG photograph. A logistic regression on three acquisition scalars and no pixels reaches 100% on a leakage-free partition. Across four model families, correcting the split changes in-distribution accuracy by at most 6.8 points; external validation on 150 independent authentic photographs drops the strongest model from 97.4% to 3.3%. A label-free normalization of resolution, brightness and compression restores that class to 86% and 81% for two of three models at negligible in-distribution cost, the third's gain inside seed variance, but we report it as a diagnostic, not a remedy: a second capture shift drops the best corrected model to 63% on average across seeds (46% in the run reported), reordering the operators moves external accuracy 50 points while ranking the worst pipeline best in-distribution, and two attention analyses put the recovered accuracy on the background, not the packaging, for one backbone and both models' errors. A correction is itself dataset construction, substituting confounds as readily as removing them. We propose a provenance audit — fitting the intended classifier to acquisition metadata alone — as a pre-training screen, and report where it misfires.

**INDEX TERMS** Data leakage, dataset bias, domain generalization, external validation, hidden stratification, image classification, provenance confounding, shortcut learning.

---

## I. Introduction

Substandard and falsified medical products are a persistent global health problem, concentrated in low- and middle-income countries and in unregulated online supply chains [1], [2]. Because much falsified product is visually imperfect — misprinted cartons, wrong color separations, missing batch information — image-based screening from a consumer smartphone is an attractive triage tool, and a body of work has accordingly applied convolutional networks to photographs of medicine packaging and reported high binary accuracy [3], [26]–[28], alongside a larger literature on pharmaceutical *identification* rather than *authentication* [4], [5].

A property of that body of work motivates this paper's method as much as its subject. There is no shared benchmark for pharmaceutical authentication: every study we could examine in full text built or adopted its own image set, and none audited it for confounds between acquisition and label (Section II-F). Each reported figure therefore rests on the unexamined construction of a single ad hoc collection.

### A. The general problem: asymmetric class sourcing

That condition is not peculiar to pharmaceuticals, and the mechanism it creates is this paper's subject. In any two-class image dataset asking *is this genuine?*, authentic examples are abundant — manufacturers photograph their products, retailers publish catalogs — while the other class is scarce almost by definition, since counterfeit stock is illegal to hold and forged documents are held as evidence. A researcher needing a negative class therefore obtains it *by some other means than the one that produced the positive class*: screen-capturing regulator bulletins, scraping a different corpus, editing authentic images, or generating examples with a model.

Every such substitution introduces a systematic difference between the classes that has nothing to do with the property being labeled. Acquisition method determines file format, encoded size, resolution, noise floor, compression signature, color rendering and often backdrop; a label correlated with acquisition method is correlated with all of them. We call this **class-conditional provenance confounding**, and identify asymmetric class availability as a mechanism by which it can arise — one whose operation is predictable from how a dataset was assembled, rather than an accident particular to any one collection.

Three properties make it damaging. It is **the easiest thing in the data to learn**, since low-level global statistics are easier to extract than the semantics of a printed carton and a shortcut-seeking optimizer [6] finds them first. It is **invisible in-distribution**, because a held-out partition inherits it in the same proportion — we demonstrate this with stratification, cross-validation, bootstrapping and leakage-aware grouping, and find nothing. And it is **silent in the reporting record**, since acquisition method is rarely documented.

The status of that claim should be stated exactly: we demonstrate a mechanism and a case, and make no claim about how often it occurs. A prevalence estimate would require auditing a representative sample of such datasets, which neither this paper nor, as far as we can determine, any other has done. Section S-I-W audits seven datasets across four application areas and finds both a totally confounded case and a clean one — enough to show the audit discriminates, far short of a rate; Section VIII-G says what would falsify the mechanism.

The mechanism is not peculiar to this application area. In generated-image detection, real images are harvested as lossy Joint Photographic Experts Group (JPEG) files at modest resolution while generated images are written as lossless PNGs at native size; Grommelt *et al.* [30] show that on the GenImage benchmark this makes format, compression and size predictive of the label, that detectors partly become JPEG detectors, and that equalizing those factors shifts cross-generator performance by more than 11 points. That work and this share no data, no application area and no method of discovery, and arrive at the same confound — what a structural cause predicts and a coincidence does not.

### B. This paper

The study began as a methodological exercise. The Kaggle *Fake vs Real Medicine* set is small (661 images), freely available, and typical of what this area works with: no data card, no stated acquisition protocol. Under a protocol fixed in advance we set out to establish how much of a reported accuracy survives methodological correction — evaluating identical models under a naive and a product-grouped split, across four model families from a 97-parameter linear baseline to a 4-million-parameter pretrained backbone, and validating on an external source verified independent rather than assumed so.

The result was not the one the design anticipated. Correcting the split changed in-distribution accuracy by at most 6.8 points. What changed the picture was external validation: on 150 authentic photographs from an independent source, two of four models classified *zero* correctly and the strongest in-distribution model 3.3%, despite 97.4% on the authentic class of its own test partition.

Tracing the cause led to the dataset itself. Its two classes were not merely photographed differently, they were *acquired* differently: every counterfeit-labeled file is a screen capture (`Screenshot*.png`) and every authentic-labeled file a downloaded photograph (`images*.jpg`), correlating with the label exactly 1.0 across the pool, and any model — including a 97-parameter linear classifier on a color histogram — has unobstructed access to it. It is the hidden stratification of [7], differing in being total rather than partial (Section II-B).

The contributions are:

1. **A named mechanism and a cheap detector.** We identify asymmetric class sourcing as a mechanism producing provenance confounding, predictable from how a dataset was assembled and distinct from shortcut learning, dataset bias and domain shift (Section II-B), and propose the *provenance audit* — fitting the intended classifier to acquisition metadata alone, under the study's own leakage-free split — as a pre-training screen needing no external data, no annotation and no pixel decoding. It returns **1.000** here (Section VI-A, Table 4). A high score establishes that a provenance shortcut is available, not that a given pixel classifier took it.

2. **Evidence that the detector is necessary but not sufficient.** On a second published dataset it returns only 0.717 although that dataset is confounded at least as severely, because its publisher had normalized every image before release: a tidied dataset is *harder* to audit, and silence is not clearance (Section S-I-W). Across four application areas the audit also exposes a false-positive mode (Section S-I-W, Table S18).

3. **A quantified, previously unreported confound in the case-study dataset**, with effect sizes on brightness, resolution, aspect ratio and file size; an exact Shapley decomposition showing a linear model's decision is dominated by the statistic the confound controls; and a degenerate shipped split whose training folder is a superset of both others (Sections III-A, VI-A).

4. **A demonstration that classical leakage correction is the smaller problem.** Product-level grouping changes accuracy by at most 6.8 points, and a paired experiment that varies leakage alone on a fixed test set moves accuracy by 0.3 points [−1.9, +2.4], whereas the confound accounts for the difference between 97% in-distribution and 3% external accuracy (Sections VI-B–VI-D). The check the field has institutionalized is not the one that mattered.

5. **A label-free correction, ablated per axis, architecture, constant and composition order, and offered as a probe rather than a remedy.** It raises external specificity from 0–3% to 81–86% for two of the three models it is applied to, the third's apparent gain lying inside seed variance. We decline to offer it for use, because three of our own results say what that number is made of (Section VIII-E): operator *order*, normally left implicit, moves external accuracy across a 50-point range under a 2.7-point in-distribution range with the in-distribution ranking inverted; the attribution evidence indicates substantial dependence on the photographic setting; and the repair does not survive a second capture shift for the model it helped most.

This is an empirical critique and a diagnostic method. We propose no new architecture — a 97-parameter linear model and a 4-million-parameter pretrained network are not statistically distinguishable on this test partition — and do not propose the normalization of Section V-D for adoption either. Everything offered for adoption is a check: fit your classifier to acquisition metadata before training it, evaluate on images you did not collect, and audit a correction as you would a dataset.

## II. Related Work

### A. Image-based pharmaceutical authentication and identification

Image classification has been applied to pharmaceutical products for both *identification* (which drug is this?) and *authentication* (is this drug genuine?). Ramos, Samonte and Manlises [3] proposed a convolutional neural network (CNN) authentication system directly comparable in task framing to this work; adjacent identification work addresses look-alike medication errors across 250 blister-packaged drug types [4] and pill-image retrieval [5]. That literature establishes that packaging imagery carries usable signal. As far as this review found, none of it examines *why* reported accuracies are as high as they are, or audits its datasets for confounds between acquisition and label.

### B. Shortcut learning and hidden stratification

Geirhos et al. [6] formalized *shortcut learning*: networks adopt decision rules exploiting superficial, spuriously predictive correlations, scoring well in-distribution while failing wherever the shortcut is absent. That framing describes this paper's central finding precisely.

The failure has a documented precedent in medical imaging. Zech et al. [7] showed that pneumonia detectors trained on chest radiographs from three hospital systems could predict which system an image came from, and used that hospital-identity signal — itself correlated with disease prevalence — as a shortcut for the diagnostic label, degrading substantially on an unseen site. Later audits report the same pattern for scanner-, site- and manufacturer-level signal [8], [9], and early COVID-19 radiograph classifiers were shown to rely on dataset-source confounds rather than radiographic signs [10]. DeGrave et al. [31] put that case most sharply: applying explainable-AI methods to published COVID-19 radiograph detectors, they conclude the systems rely on confounding factors rather than medical pathology, and so "appear accurate, but fail when tested in new hospitals". Of the work we are aware of, that is the closest precedent for the mechanism this paper describes.

A difference in *cause* determines how far the present finding generalizes, and the mechanism is worth separating from the terms nearest to it, because the contribution is not that models learn shortcuts. Shortcut learning [6] names what a model does. Dataset bias [32] and spurious correlation name a statistical property of a sample. Domain shift names a relation between two distributions, one of them the deployment distribution. What we describe is none of those but a property of how a dataset was assembled: because one class was unobtainable by the procedure that produced the other, acquisition is correlated with the label *within the training distribution itself*, before any model is fitted and without reference to any deployment distribution. Three consequences follow that the neighboring terms do not carry. The association can be complete rather than partial — at the three hospital systems of [7] it was incidental and partial; here it is exactly 1.0 across 510 images. It is predictable from a dataset's construction, so the population at risk is nameable in advance: any collection whose two classes were sourced separately. And it survives leakage-aware validation, because every partition of one pool inherits it in the same proportion, which is why the check this field has institutionalized does not see it. What separates this paper from [31] is level rather than subject. That work diagnoses confounding in datasets it examines one at a time, with methods that require the images and a trained classifier; we ask what makes such datasets predictable in advance from how a class was obtained, reduce the diagnosis to a screen that reads file listings before any model exists, and then follow the correction through to show that removing the confound is itself dataset construction (Sections VII, VIII-E).

The closest published analogue outside medicine is the GenImage audit of Grommelt et al. [30], described in Section I-A. The parallel is worth stating precisely: the same three statistics, the same direction, the same in-distribution invisibility, and a correction of the same shape — in an unrelated application area, discovered independently.

### C. Data leakage and evaluation protocol

A related but distinct concern is train/test leakage from improper partitioning: splitting at the image rather than the subject level lets near-duplicate images of one entity appear in both partitions, inflating reported performance [11]. That motivated this work's two-split design, evaluated in parallel so the leakage effect is measured rather than assumed. On this pool it is small relative to the capture-pipeline confound (Section VIII-B).

### D. Robustness to synthetic corruption

Hendrycks and Dietterich [12] introduced ImageNet-C, applying standardized corruptions to measure robustness without collecting new out-of-distribution data. This work adopts the same logic: lacking a counterfeit-labeled external dataset, independent authentic photographs are perturbed with print-quality, color and text-region defects to build a synthetic proxy. Following [12] we state that such a proxy measures robustness to a documented perturbation style, not label-defined class recall.

### E. Architectures and interpretability methods

The four model families span a classical color-histogram baseline through MobileNetV3 [13] and EfficientNet-B0 [14], both used as frozen ImageNet-pretrained feature extractors with a linear head. Attention is inspected with gradient-weighted class activation mapping (Grad-CAM) [15]; attribution for the linear baseline uses Shapley values [16], which have a closed form here and need no sampling. Domain-generalization surveys [23] situate the normalization of Section V-D closer to hand-designed covariate-shift alignment than to representation learning.

### F. What datasets this sub-field actually uses

Because this paper's contribution is a dataset audit, the datasets neighboring results rest on are themselves prior work. We examined in full text, where obtainable, every study we could locate performing authentic-vs-counterfeit classification of pharmaceutical *images*; Table 1 records what each trained on. This is a best-effort search, not a systematic review, and its negative findings mean "not found by this search".

**TABLE 1.**Image sources used by located prior work on pharmaceutical authentication. "Audit" asks whether the study reports any check that acquisition conditions are balanced across its two classes.

| Study | Image source | Class construction | Reported accuracy | Audit |
|---|---|---|---|---|
| Ramos *et al.* [3] | Self-captured, Raspberry Pi camera; one brand | Real authentic and counterfeit samples, same rig | 88.75% | none |
| Motwani *et al.* [26] | Web-scraped packaging, 10 manufacturers | Counterfeit class **created by the authors** by altering logo and text | not per-class | none |
| Thomson and Varuna [27] | Kaggle pill set for training; DrugBank and drugs.com for testing | Counterfeit class **GAN-synthesized** | not comparable | none |
| Thomson and Varuna [28] | drugs.com product images | not specified | 92% | none |
| Roboflow *Counterfeit_med_detection* [21] | Advisory bulletins plus product photographs | Class tracks document type, not authenticity (Section III-B) | — | — |

Three observations follow, and each bears directly on the finding of Section VI-A.

**No shared benchmark exists, so the confound cannot be inherited — only re-invented.** No two studies in Table 1 evaluate on the same images, and the Kaggle set audited here is not a community benchmark: as of 28 August 2026 its listing records 591 downloads, 3 public notebooks and no discussion, and our search located no peer-reviewed study that uses it. The claim this paper makes is correspondingly narrow: not that a widely-shared benchmark is broken, but that a dataset assembled the way this sub-field routinely assembles datasets contains a total acquisition confound that its own users did not detect.

**The most common class-construction procedures make the confound near-inevitable.** In [26] the counterfeit class is produced by digitally editing authentic images and in [27] by a generative model, so in both the two classes are by construction outputs of two different image pipelines, exactly as in the dataset audited here — and neither reports a check that would surface it. A model can score highly on such a set by learning the editing or generation signature, and no in-distribution evaluation distinguishes that from learning authenticity. Where the classes *were* acquired under a common protocol — [3], on one Raspberry Pi rig — the reported accuracy is the lowest in Table 1 (88.75%), consistent with the confound accounting for part of the spread.

**Studies that do control acquisition say so explicitly.** Outside pharmaceuticals, Garcia-Cotte *et al.* [29] report counterfeit detection on branded garments from smartphone images captured "under natural, weakly controlled conditions", at 99.71% after a 3.06% rejection rate. Whatever else separates that work from Table 1, it states its acquisition regime as a property of the result — the reporting standard Section VIII-D argues should become routine here.

## III. Dataset

### A. Sources considered

Three public sources were inventoried (Table 2). All were considered for the modeling pool; two were excluded for reasons below, and one became the external evaluation set.

**TABLE 2.**Public sources inventoried, with their role in this study.

| Source | Files as shipped | License | Role |
|---|---|---|---|
| Kaggle *Fake vs Real Medicine* [19] | 661 unique (`Fake/` 240, all `.png`; `Real/` 421, all `.jpg`), re-listed across a bundled `train`/`val`/`test` split | "Unknown" per the Kaggle listing; none stated in the archive | Modeling pool (Splits A and B) |
| Roboflow *Counterfeit_med_detection* v4 [21] | 4,260 (includes the publisher's own 3× rotation/exposure augmentation) | CC BY 4.0 | Excluded from modeling; retained as a supplementary authentic pool |
| Mendeley *Mobile-Captured Pharmaceutical Medication Packages* [20] | 3,900 across six devices; the 150-image "Huawei CN" single-instance-per-product subset was used | CC BY 4.0 | External evaluation (Split C), authentic only |

Two properties of the primary source should be recorded before any result is read. Both are verifiable in seconds by anyone holding the archive.

**Provenance.** It is a single-uploader Kaggle contribution, last updated 13 October 2025, distributed with its license field set to "Unknown". Counterfeit-class files are named `Screenshot YYYY-MM-DD HHMMSS.png`, with embedded timestamps falling in a small number of capture sessions; authentic-class files are named `imagesNN.jpg`. There is no data card, no collection protocol and no per-image provenance — none of which is unusual for a dataset of this kind, which is the point of Section II-F.

**The bundled split is not a split.** Alongside the class folders the archive ships `train/`, `val/` and `test/`. Counting unique filenames, the training folder lists all 661 while validation (453) and test (449) are proper subsets of it, with 286 filenames common to all three: a study adopting this partition trains on 100% of the data it then reports test accuracy on. We discarded it and built our own (Section IV-C), and record it because it is a second fully deterministic defect in the same artifact, and one no reader could detect from a reported accuracy.

### B. Why the second source was excluded: a label baked into the pixels

The Roboflow source appeared to be a second independent authentic/counterfeit dataset, and therefore a candidate both for pooling and for cross-dataset validation. Inspection showed it is neither. Of its counterfeit-labeled images, 57/57 unique source images are institutional advisory graphics carrying a regulator's logo, a banner headline and, critically, **the ground-truth label rendered as literal text inside the image**, while 263/263 of its plain product photographs are authentic-labeled: a model trained on it as shipped would learn to distinguish advisory collages from product photography. After excluding those, 9 more found by manual inspection and 52 rows carrying simultaneous `authentic=1` and `counterfeit=1` annotations, the source contributes **2** usable counterfeit images against 2,695 authentic. Prior work attributes its unsuitability to class imbalance; the deeper problem is a modality confound (Section S-I-T, Type B).

### C. Why the two sources are not independent

Perceptual-hash clustering (Section IV-B) found **229 clusters containing images from both sources**, covering 2,900 of 4,027 retained Roboflow images and 290 of 661 Kaggle images — **44% of the Kaggle dataset has a near-duplicate in the Roboflow source**, sometimes differing only by a 90° rotation. This was confirmed visually on matched pairs, not inferred from hash distance alone. Neither source documents provenance, so we claim nothing about which derives from which; the relevant fact is that any study treating them as independent sources for cross-dataset testing would be leaking training data into "external" evaluation.

### D. The modeling pool

Given Sections III-B and III-C, **Splits A and B are built from the Kaggle pool alone**, which makes the split protocol the single manipulated variable; adding Roboflow would also have pushed the group-level class ratio from 44:56 to roughly 8:92 while contributing essentially no counterfeit signal. After exclusion and de-duplication the pool contains **510 images in 480 product-identity groups**, 272 authentic and 238 counterfeit. Neither source ships product labels, so these groups are near-duplicate clusters used as an operational proxy for product identity (Section IV-B); two dissimilar photographs of one package would not be grouped.

### E. External evaluation set (Split C)

The protocol called for a genuinely external source. A search for an independent *two-class* source found none: every candidate was either likely to share photographs with sources already in the pool (Section III-C) or carried no counterfeit label. We therefore use the Mendeley source [20] as an **authentic-only** external check: 150 photographs, one per distinct product, from a different country, photographers, camera hardware and backdrop protocol. Independence was verified rather than assumed (Section IV-B): **0 of 150 images matched anything in the pool**, nearest match at Hamming distance 10/64 against a threshold of 8, median 18.

An authentic-only set measures external authentic accuracy. Because counterfeit is the positive class throughout (Section V-A), that quantity is specificity, the true-negative rate; the corresponding false-positive rate is one minus it. It says nothing about counterfeit recall. Section S-I-B describes the synthetic proxy built to probe that direction, and Section IX states the limitation that remains.

## IV. Data Preprocessing

The full pipeline is deterministic (fixed seed 42 throughout) and idempotent; re-running reproduces byte-identical outputs. Fig. S1 summarizes it.

### A. Filtering

Exclusions are rule-based and documented in code, in three families: contradictory annotations (52 Roboflow rows), advisory-bulletin graphics (180 Roboflow files, Section III-B), and the 56 human-identified Kaggle files of Section S-I-A. Each is recorded with a machine-readable reason in the provenance table, so any downstream count traces to the rule that produced it.

### B. De-duplication and product identity

Neither source carries ground-truth product-identity labels, so near-duplicate photo clustering is used as an operational proxy. A 64-bit perceptual hash [25] is computed at all four cardinal orientations per image and the numeric minimum taken as a rotation-canonical hash:

$$h(x) = \min_{\theta \in \{0°, 90°, 180°, 270°\}} \mathrm{pHash}\big(R_\theta(x)\big) \tag{1}$$

Rotation invariance is necessary rather than decorative: the Roboflow source documents 90°-rotation augmentation, and a plain pHash treats a rotated copy as a different image. Pairs at Hamming distance 0 are treated as true duplicates and one copy removed; pairs at distance 1–8 are retained but assigned to the same `product_identity` cluster. Zero clusters mix authentic and counterfeit labels, so the clustering never contradicts the original annotations. The method is not robust to mirroring, a gap kept low-risk by the no-flip augmentation policy of Section V-C but not exhaustively verified.

### C. Split construction

Three partitions of the modeling pool are built (Table 3):

- **Split A (naive)** — random 70:15:15, class-stratified, at the **image** level. This is the protocol in general use on data of this kind, and the only one available to a study that adopts a dataset's shipped partition without inspecting it, as Section III-A shows this dataset's shipped partition invites; none of the studies in Table 1 reports a grouped or identity-aware split.
- **Split B (corrected)** — 70:15:15, class-stratified, at the **product-identity group** level, so no near-duplicate photograph of the same product can appear in more than one partition. The training partition additionally carries a `cv_fold` index from `StratifiedGroupKFold`, so 5-fold cross-validation never places the same product in two folds.
- **Split C (external)** — the 150 Mendeley photographs, used only for evaluation.

An assertion in the pipeline verifies zero product-identity overlap between every pair of Split B partitions on every run; it passes. Comparing the two assignments directly, **9 of 480 product-identity groups (1.9%) have members in more than one partition under Split A** — this is the literal, countable leakage that Split B removes — and 230 of 510 images (45.1%) are assigned to a different partition under A than under B.

Split A holds 357/77/76 images and Split B 357/79/74 over 336/72/72 product groups, against Split C's 150; Table S2 gives every partition's class balance. The test partitions are small (74–76 images), so every point estimate in Section VI carries a 95% uncertainty interval, and comparisons are read against those intervals rather than against point differences. Two constructions are used — a percentile bootstrap and a Wilson score interval — and each table names the one it reports. Both describe sampling uncertainty for one trained model; training-run variance is reported separately in Section S-I-U.

### D. Capture-method normalization

The three-stage normalization that Sections V-D and VIII evaluate is applied *inside* the dataset class, before augmentation and before the network's input transform, identically for training, validation, in-distribution test and external partitions. It uses no label information at any point and could be shipped unchanged as an inference-time preprocessing step. Section V-D gives its definition.

---

## V. Methodology

### A. Task and label convention

The task is binary image classification. Throughout, authentic = 0 and **counterfeit is the positive class**, so precision, recall, F1 score, area under the receiver operating characteristic curve (ROC-AUC) and area under the precision–recall curve (PR-AUC) are reported with respect to counterfeit detection — the deployment framing, in which the costly error is calling a falsified product genuine.

### B. Models

Four model families are evaluated (Fig. S2), deliberately spread across capacity scales so that "does capacity explain the reported accuracy?" is answerable.

**M1 — Color histogram + logistic regression (97 learned parameters).** Each image is resized to 224×224 and a 32-bin-per-channel red-green-blue (RGB) intensity histogram computed, giving a 96-dimensional feature vector:

$$\phi(x) = \big[\,\mathbf{h}_R(x) \,\|\, \mathbf{h}_G(x) \,\|\, \mathbf{h}_B(x)\,\big] \in \mathbb{R}^{96}, \qquad \mathbf{h}_{c,b}(x) = \frac{1}{HW}\sum_{i,j} \mathbb{1}\!\left[ x_{ij}^{(c)} \in B_b \right] \tag{2}$$

with the 32 bins $B_b$ uniformly partitioning [0, 256). A logistic regression is fitted on $\phi(x)$:

$$P(y = 1 \mid x) = \sigma\big(\mathbf{w}^\top \phi(x) + b\big), \qquad \sigma(z) = \frac{1}{1 + e^{-z}} \tag{3}$$

with `class_weight="balanced"` and L2 regularization at scikit-learn's default strength. This model answers one question: how much of the reported accuracy is available to a classifier that cannot see spatial structure at all?

**M2 — Small CNN with a global-average-pooling (GAP) head (23,938 trainable parameters).** Three convolutional blocks with a conventional channel progression (16 → 32 → 64; each block Conv3×3 → BatchNorm → ReLU → MaxPool2×2), with a GAP head rather than the flatten-then-dense head small-dataset CNN work commonly uses:

$$g_k = \frac{1}{H'W'}\sum_{i=1}^{H'}\sum_{j=1}^{W'} a_{ijk}, \qquad \hat{y} = \mathrm{softmax}\big(W_{\!f}\,\mathrm{drop}_{0.5}(\mathbf{g}) + \mathbf{b}_{\!f}\big) \tag{4}$$

The head is the point of this model. Flattening the trunk's 28 × 28 × 64 output into a 128-unit dense layer would cost roughly 6.4 M parameters — about 99.7% of such a network — on 357 training images; GAP replaces that with 130 while preserving the trunk exactly (Section S-I-Q).

**M3 — MobileNetV3-Small, frozen (1,154 trainable / 927,008 frozen).** The ImageNet-pretrained feature extractor [13] is frozen; a `Dropout(0.3) → Linear(576, 2)` head is trained on its globally pooled 576-dimensional output.

**M4 — EfficientNet-B0, frozen (2,562 trainable / 4,007,548 frozen).** As M3, with the EfficientNet-B0 extractor [14] and a `Dropout(0.3) → Linear(1280, 2)` head.

Both transfer models are therefore **linear probes on a fixed representation**, which is the instrument this study's question calls for rather than a concession to it. The question is what a change in the *input distribution* does; a probe holds the representation constant while the input changes, so any movement in accuracy is attributable to the input, whereas a fine-tuned network confounds the two by re-adapting its features to whatever the new input affords. Freezing also keeps M3 and M4 balanced — both train exactly one linear layer — and the compute budget within central-processing-unit (CPU) only hardware. What a probe cannot say is what fine-tuning would do, in either direction (Section X).

### C. Augmentation

Training-partition augmentation for M2–M4 is: rotation ±12°, brightness and contrast jitter (±0.25), mild `RandomResizedCrop` (scale 0.85–1.0), and slight Gaussian blur (kernel 3, σ ∈ [0.1, 0.8]). **No horizontal or vertical flip** is used, because mirroring produces printed packaging text that cannot occur in deployment.

M1 is excluded from augmentation by design: rotation and cropping are near-invariances of a color histogram, while brightness and contrast jitter would perturb the only feature this model observes, acting as label noise rather than as the spatial-filter regularizer they are for a CNN. Section VII shows the asymmetry does not soften the paper's conclusion about M1.

### D. Capture-method normalization

Three label-free operators are composed in a fixed order. Let $x$ be a decoded RGB image with dimensions $W \times H$.

**Resolution bottleneck.** Cap the short side at $s = 128$ px, chosen to sit below the 10th percentile of the Kaggle pool's own short-side distribution so the bottleneck binds for nearly every image in both sources rather than only for the high-resolution external set:

$$T_{\mathrm{res}}(x) = \begin{cases} x & \text{if } \min(W, H) \le s \\ \mathrm{resize}\big(x,\; \lambda W,\; \lambda H\big), \;\; \lambda = \dfrac{s}{\min(W,H)} & \text{otherwise} \end{cases} \tag{5}$$

**Brightness rescale.** Scale to a fixed target mean $\mu^\star = 0.5$ and clip:

$$T_{\mathrm{bright}}(x) = \mathrm{clip}\!\left( x \cdot \frac{\mu^\star}{\bar{x}},\; 0,\; 1 \right), \qquad \bar{x} = \frac{1}{3HW}\sum_{c,i,j} x^{(c)}_{ij} \tag{6}$$

**Compression bottleneck.** Re-encode through JPEG compression at fixed quality $q = 40$ and decode back, imposing a common quantization-artifact floor:

$$T_{\mathrm{comp}}(x) = \mathrm{decode}_{\mathrm{JPEG}}\big(\mathrm{encode}_{\mathrm{JPEG}}(x,\, q)\big) \tag{7}$$

The composed operator is

$$T(x) = T_{\mathrm{comp}} \circ T_{\mathrm{bright}} \circ T_{\mathrm{res}}\,(x) \tag{8}$$

and is applied identically to every partition. Three properties matter. $T$ is **label-free** — nothing in (5)–(7) references $y$ — so applying it to the external set is not an oracle. It is **deployable**: a fixed preprocessing function, not a train-time-only trick. And it is **destructive** by design, removing information a model might legitimately use, which is why its effect must be measured per architecture rather than assumed (Section VII). The composition order in (8) is itself a free choice, and because two of the three operators destroy information they do not commute; Section VII measures all six orderings.

One choice is not label-free in the sense the operators are: the three axes were selected after Table 3 showed those statistics separating the pool from Split C, which is target-distribution information a practitioner would not hold. Section S-I-S re-derives the same three from the training partition alone, under a threshold declared in advance. M1 reads images directly and never passes through this operator, an exclusion that is empirical: normalization collapses M1's in-distribution accuracy toward chance while recovering nothing externally (Section VII).

### E. Interpretability and attribution

**Grad-CAM.** For target class $c$, with $A^k$ the activation maps of the last convolutional stage,

$$\alpha^c_k = \frac{1}{HW}\sum_{i,j} \frac{\partial y^c}{\partial A^k_{ij}}, \qquad L^c_{\mathrm{Grad\text{-}CAM}} = \mathrm{ReLU}\!\left(\sum_k \alpha^c_k A^k\right) \tag{9}$$

following [15]. Maps are computed on M4 for the in-distribution audit and directly on the external images for both M3 and M4.

**Exact Shapley values for M1.** For a linear model with an independent-feature background, the Shapley value of feature $i$ for instance $x$ has the closed form [16]

$$\varphi_i(x) = w_i\big(\phi_i(x) - \mathbb{E}[\phi_i]\big) \tag{10}$$

so no sampling approximation is needed. We take $\mathbb{E}[\phi_i]$ over the Split B training partition and report $\overline{|\varphi_i|}$ over its test partition as global importance — an exact decomposition of M1's decision function, not an estimate of it.

## VI. Results

All results in this section come from the deterministic, three-way-normalized production pipeline, except where a table explicitly reports a baseline condition for contrast. Complete machine-readable tables are in `paper/tables/`. The split comparison, the model roster and the external evaluation were fixed by the protocol before any of them ran; everything about the correction was developed after the external failure was observed and is exploratory in the sense Section S-I-F sets out.

### A. The capture-method confound

The strongest result in this study needs four learned parameters and no pixels: a logistic regression on three acquisition statistics separates the two classes perfectly on the leakage-free partition (Table 4). This subsection builds to it.

Every one of the 510 pool filenames falls into exactly one of two patterns, and **the pattern predicts the class label with no exceptions** (Table 3): 272/272 authentic files are `images*.jpg`, 238/238 counterfeit files are `Screenshot*.png`. We recomputed this cross-tabulation independently for this paper from per-image statistics; it is exact, not approximate.

This is not an artifact of our filtering: it holds in the archive as distributed, where all 240 files in `Fake/` are `Screenshot*.png` and all 421 in `Real/` are `images*.jpg`. Any study using this dataset, filtered or not, inherits it in full, and a classifier reading nothing but the file extension achieves **100% accuracy**.

**TABLE 3.**The two acquisition pipelines in the Kaggle pool, and the external set's position relative to both. Brightness is the mean RGB value at 64 × 64, on a 0–1 scale; throughout this paper kB = 1000 bytes.

| Group | n | Capture pattern | Mean brightness | Median short side (px) | Mean file size |
|---|---|---|---|---|---|
| Kaggle authentic | 272 | `images*.jpg` (100%) | 0.767 | 223 | 6.0 kB |
| Kaggle counterfeit | 238 | `Screenshot*.png` (100%) | 0.555 | 405 | 339 kB |
| Split C external (authentic) | 150 | device photograph | **0.162** | **2448** | 1,656 kB |
| Split C synthetic (proxy counterfeit) | 150 | perturbed copy of the above | 0.153 | 2448 | 1,018 kB |

A two-sample *t*-test on brightness between the two classes gives *t* = 17.0 on 508 degrees of freedom, *p* < 10⁻¹⁵ — one of the strongest and most trivially learnable signals anywhere in the training data. Table 3 makes the second, equally important point, and Fig. S13 plots the full distributions: the external set does not sit *between* the two training classes on these axes but far outside both, roughly 10× higher in linear resolution and darker than even the counterfeit class. A model that has learned "bright, small, heavily compressed → authentic", even partially, has every statistical reason to call every external photograph counterfeit.

The confound is visible in the decision function of the simplest model. Of M1's 96 coefficients, 93 lie within ±0.35 of zero while the top intensity bin (248–255) of each channel carries a large negative weight (β = −2.86, −2.84, −2.95) — "many near-white pixels → authentic" — and the exact Shapley decomposition of Eq. (10) confirms this is not a large coefficient on a rarely varying feature (Section S-I-P, Fig. S12). M1's 83.8% accuracy is, to a good approximation, a measurement of how much white a photograph contains.

**A metadata-only oracle shows acquisition alone suffices.** M1 is a useful diagnostic but an ambiguous one, because a 96-bin color histogram does read pixel intensities and could in principle carry some packaging information. We therefore fitted the same logistic regression to the three acquisition statistics of Table 3 and nothing else — mean brightness, log short-side resolution, log encoded file size — with no pixels, no spatial structure and no color information at all. Three scalars per image, 4 learned parameters, trained on each split's own training partition (Table 4).

**TABLE 4.**Metadata-only oracle; LR = logistic regression. Features are per-image acquisition statistics, not image content; resolution and file size enter as log₁₀. The deterministic rule uses only the filename extension and is not fitted. Intervals are 95% Wilson.

| Classifier | Features | Split A test (n = 76) | Split B test (n = 74) |
|---|---|---|---|
| Deterministic rule: `.png` → counterfeit | file extension | 510/510 = **1.000** [0.993, 1.000] over the whole pool | — |
| Metadata LR | brightness | 0.829 [0.729, 0.897] | 0.716 [0.605, 0.806] |
| Metadata LR | short-side resolution | 0.947 [0.872, 0.979] | 0.946 [0.869, 0.979] |
| Metadata LR | encoded file size | 0.974 [0.909, 0.993] | **1.000** [0.951, 1.000] |
| Metadata LR | all three | 0.974 [0.909, 0.993] | **1.000** [0.951, 1.000] |

Three things follow, and they are stronger than anything the pixel-based models in this study establish.

First, **a single scalar that is not an image classifies this dataset perfectly.** Encoded file size alone reaches 74/74 on the leakage-free partition — above every trained model here, including M4 (Table S3), using no pixel at all.

Second, **the accuracy ceiling attributable to acquisition alone is 1.000.** The deterministic file-extension rule is correct on all 510 pool images by construction. There is therefore no accuracy figure obtainable on this dataset that requires any packaging information to explain, and no in-distribution result on it — ours or anyone's — can be evidence of packaging-authentication ability. This is the sense in which the dataset is not merely confounded but uninformative for its stated task.

Third, **brightness is the weakest of the three axes, not the strongest.** Alone it reaches 0.716 on Split B, below resolution (0.946) and file size (1.000), despite the largest *t*-statistic. Large mean separation and high discriminability are different properties: the brightness distributions have very different means but substantial overlap, whereas the file-size distributions barely overlap. This is a caution against ranking candidate confounds by *t*-statistic — fit a classifier to each candidate instead, which costs no more than the *t*-test.

### B. In-distribution performance, and why leakage is the smaller problem

One definition governs what follows. "Leakage-free", here and throughout, means free of **product-identity** leakage: Split B guarantees that no perceptual-hash cluster of near-duplicate photographs straddles a partition or a fold. It makes no claim about acquisition. Because every counterfeit-labeled image in the pool was produced by one capture pipeline and every authentic-labeled image by another, *no* partition of this pool can place a capture process on one side of a fold, and grouped cross-validation inherits the confound at full strength in every fold. Split B corrects one of the two problems, not both.

In-distribution, the four models reach 0.842, 0.868, 0.934 and 0.987 on the naive split and 0.838, 0.865, 0.932 and 0.919 on the leakage-free one — deltas of +0.004, +0.004, +0.002 and +0.068, three of them within half a point of zero. No pairwise McNemar's test is significant, and Holm–Bonferroni over the six raises the smallest adjusted *p* from 0.118 to 0.711, so the correction is robust to multiplicity and, if anything, understated without it. The full metric set, the tests and their power analysis are Table S3–S5 and Section S-I-H.

Two things limit what those deltas settle. First, they can be checked against a count: exactly 7 of the 76 Split A test images belong to a product group also represented in Split A's training partition, a **direct exposure rate of 9.2%**, so at most seven predictions can be got right by recognizing a training photograph. But that bounds one channel only — admitting a near-duplicate into training also changes the fitted parameters, and those decide the other 69 predictions, in either direction. Second, Split A and Split B do not share a test set: 230 of 510 images are assigned differently, so their difference mixes leakage with the effect of testing on different images. We therefore measured leakage directly as well.

A paired design separates the two. One test set is held fixed and two training sets are built around it differing in exactly one respect — whether the near-duplicate mates of the test images are admitted — with size, class balance, validation set, architecture and learning rate identical, the 30 mates balanced by class-matched substitutes so the arms differ in which images they hold and not how many (Section S-I-V). Of the 74 test images, 28 are *exposed*: a mate exists and the leaky arm has seen it, and these are every exposed image the pool admits. On the other 46, any difference is the indirect channel. Across five seeds, admitting the mates moves M2 by **+0.3 points [−1.9, +2.4]** (paired bootstrap over images; McNemar *p* = 1.000), by +0.0 [−2.9, +2.9] on the exposed subset and +0.4 [−2.2, +3.5] on the unexposed. M3 and M4 are unchanged at every seed, though both sit at ceiling here (1.000 and 0.987), which leaves an effect almost no room to appear — itself a consequence of the confound, since an in-distribution partition of this pool is close to trivial.

This is the paper's first substantive result. The methodological check the field has institutionalized moves accuracy by at most 6.8 points across split designs, and by 0.3 points [−1.9, +2.4] when leakage alone is varied, while the confound described next accounts for the difference between 97% in-distribution accuracy and 3% external accuracy.

### C. External generalization: the result that matters

Table 5 and Fig. 1 give the central result of this paper.

**TABLE 5.**External generalization on 150 independently captured authentic photographs. "Baseline" is the production run immediately before three-way normalization became the default; "normalized" is the current pipeline. In-distribution reference is authentic-class accuracy on each model's own Split B test partition (n = 39 authentic). The last column is the in-distribution-minus-external gap of the normalized model, Eq. (S5) of the supplement — not the effect of normalization, which is the difference between the two preceding columns. M1 does not pass through the normalization operator in the production pipeline; that exclusion was decided empirically after the fact, not a priori, and Section S-I-P reports what happens when the operator is applied to it anyway (Table S13). Bracketed intervals are 95% Wilson score intervals on the underlying counts, given as k/n; they quantify sampling uncertainty on a fixed trained model and not training-run variance, which would require repeated seeds.

| Model | In-distribution authentic accuracy (k = 39) | Split C, baseline (n = 150) | Split C, 3-way normalized (n = 150) | Generalization gap, normalized |
|---|---|---|---|---|
| M1 hist+LR | 27/39 = 0.692 [0.536, 0.814] | 0/150 = 0.000 [0.000, 0.025] | 0/150 = 0.000 [0.000, 0.025] | +0.692 |
| M2 CNN | 33/39 = 0.846 [0.703, 0.928] | 0/150 = 0.000 [0.000, 0.025] | 129/150 = **0.860** [0.795, 0.907] | **−0.014** |
| M3 MobileNetV3 | 38/39 = 0.974 [0.868, 0.995] | 104/150 = 0.693 [0.615, 0.762] | 116/150 = 0.773 [0.700, 0.833] | +0.201 |
| M4 EfficientNet-B0 | 38/39 = 0.974 [0.868, 0.995] | 5/150 = 0.033 [0.014, 0.076] | 121/150 = 0.807 [0.736, 0.862] | +0.167 |

Read the baseline column first. Two of the four models classified **zero of 150** external authentic photographs correctly, and the model with the best in-distribution accuracy in the entire study (M4, 0.987 on Split A) classified **3.3%** correctly. This is a near-complete inversion on the easiest possible external case, a test set holding only the class the models were most accurate on in-distribution: a model at 91.9% on Split B that recovers 3.3% of plainly authentic external photographs has not learned to recognize authentic packaging, but to recognize this dataset's photography.

Now read the normalized column. The same models, retrained on the same images with the same seeds and hyperparameters and differing only by the label-free operator of Eq. (8), recover 86.0%, 77.3% and 80.7%. The in-distribution price is negligible: Split B test accuracy moves 0.865 → 0.865 (M2), 0.946 → 0.932 (M3) and 0.919 → 0.919 (M4), between −1.4 and 0.0 points, the one loss well inside its bootstrap interval. The correction is close to free in-distribution while being worth tens of points externally, subject to the reading-down of the next paragraph. M2's external accuracy exceeds its own in-distribution accuracy, the only negative generalization gap in this study, because with the shortcut suppressed its mixed-class test partition is a harder problem than "is this well-lit photograph of an intact carton authentic?". M1, which never passes through the operator, is unchanged at 0.000.

The intervals separate the models' claims sharply, and one should be read down. M2's and M4's gains are far outside sampling uncertainty — 0/150 to 129/150 and 5/150 to 121/150, non-overlapping in both cases — so neither turns on Split C being only 150 images. M3's does: 104/150 [0.615, 0.762] to 116/150 [0.700, 0.833] is a 12-image difference whose intervals overlap substantially, consistent with no effect. Five seeds settle it: M3 moves 0.715 ± 0.057 → 0.724 ± 0.047, a difference five times smaller than either standard deviation, while M2 moves 0.051 → 0.909 and M4 0.100 → 0.860, both with normalized standard deviations under 0.04 (Section S-I-U). **We therefore claim no normalization benefit for M3**, as a measurement rather than a caution; the headline claim rests on M2 and M4.

> **FIGURE 1.** `paper/figures/fig08_external_generalisation.pdf` — In-distribution authentic accuracy against external accuracy before and after three-way normalization, per model. M1 bypasses the normalized pipeline by design, so its two Split C bars are the same 0.0% measurement shown twice.

### D. A second external distribution, and what it costs the headline

Section VIII-C warns that a shortcut coinciding with one external distribution is indistinguishable from robustness until a second, differently constructed evaluation disagrees. We made that warning testable. Split D is the same source's "iphone 11 pro" subset — 149 unique images (the archive ships one duplicate filename), the **same 150 products** as Split C, photographed on different hardware under the source's deliberately different lighting protocol. Measured: mean brightness 0.389 against Split C's 0.162 and the training pool's 0.668, so it is a different point on the confounded axis rather than a repeat; median short side 2419 px; and rotation-canonical pHash puts only 1 of 149 within the near-duplicate threshold of any Split C image (median distance 18), so despite depicting the same products the two sets are not pixel-interchangeable.

Because content is held fixed and only acquisition varies, this is a **paired capture-shift test**: it is not an independent product sample and isolates exactly the axis this paper is about. Both sets are authentic-only, so both measure specificity. All four models were evaluated from their persisted Split B checkpoints (Section S-I-G), so the model tested is provably the one that produced the in-distribution numbers; Table 6 gives the result.

**TABLE 6.**The same corrected models on two external distributions. Both authentic-only; accuracy is the fraction correctly called authentic, with 95% Wilson intervals. Split C and Split D photograph the same products under different capture conditions.

| Model | Split C (n = 150) | Split D (n = 149) | Change (percentage points) |
|---|---|---|---|
| M1 hist+LR | 0/150 = 0.000 [0.000, 0.025] | 0/149 = 0.000 [0.000, 0.025] | 0.0 |
| M2 CNN | 129/150 = **0.860** [0.795, 0.907] | 69/149 = **0.463** [0.385, 0.543] | **−39.7** |
| M3 MobileNetV3 | 116/150 = 0.773 [0.700, 0.833] | 108/149 = 0.725 [0.648, 0.790] | −4.9 |
| M4 EfficientNet-B0 | 121/150 = 0.807 [0.736, 0.862] | 124/149 = 0.832 [0.764, 0.884] | +2.6 |

Two of the three findings narrow claims made elsewhere in this paper; we state those first.

**The correction does not transfer uniformly across capture shifts, and the model it fails for is the one we had called the best generalizer.** M2 loses 39.7 points between the two external sets, from 0.860 — the highest in the study — to 0.463, barely above the rate obtained by calling everything counterfeit, with intervals nowhere near overlapping. Read that size with Section S-I-U: across five seeds M2's Split D accuracy is the most seed-sensitive quantity in the study (0.627 ± 0.135) and the run of record is the lowest of the five, so the mean drop is 28 points rather than 39.7. The direction, and the contrast with the backbones' −3.9 and +1.8, hold at every seed. Whatever let M2 succeed on Split C after correction did not survive a change of camera.

The same caution Section VIII-C raises about M3's uncorrected accuracy therefore applies to M2's corrected accuracy: one external distribution cannot distinguish a general repair from one that fits Split C in particular, and the second says it was substantially the latter.

**The two pretrained backbones hold their accuracy across the shift.** M3 moves −4.9 points and M4 +2.6, both with comfortably overlapping intervals, so neither change is distinguishable from sampling noise. M4 is the most stable model across both external distributions (0.807 and 0.832) and M3 the next (0.773 and 0.725).

We do not describe this as the backbones generalizing. Section VI-E finds M3 taking its evidence for "authentic" from the background, and both models doing so on the images they get wrong, while Split C and Split D share the same dark backdrop — and a model applying a backdrop rule would hold its accuracy across exactly this shift. **Split D tests the capture-pipeline confound and leaves the backdrop cue untouched**, so these two rows say the backbones' accuracy survives a change of camera, not that it rests on packaging content.

The net effect is a narrowing: the correction holds **for frozen pretrained backbones across two capture shifts** and fails for a small from-scratch CNN on the second, so "normalization recovers 81–86% external specificity" is a statement about one distribution. Two capture conditions from one archive remains a narrow basis (Section S-II).


### E. What the surviving accuracy attends to

Accuracy that survives a capture shift still has to be shown to rest on the intended cue, and here it is not. Two attribution methods were run on the corrected models and Section S-I-J reports both in full: a categorization of all 62 Grad-CAM maps this study produced, and an annotation-free occlusion analysis over every external image, which reproduces each model's Split C accuracy of record before reporting anything.

They agree on three of four groups and disagree on the fourth. Both put the evidence for "authentic" on the photographic surround for M3 (occlusion border mass 0.760 against a 0.642 uniform reference, 96 of 116 images above it) and both put the evidence for "counterfeit" on the product for both backbones' errors (0.856 and 0.803). For M4's correct external answers they part: Grad-CAM reads them as surround-driven, occlusion returns 0.614 [0.585, 0.643], indistinguishable from uniform. **The evidence therefore supports substantial surround dependence for M3 and for both models' errors, and not for M4's correct external answers**, and we withdraw the reading that the two backbones behave identically. Neither is shown to recognize packaging; for M4 what its correct answers rest on is unidentified.

Two consequences narrow the paper's claims. Split C and Split D are the same products on the same dark backdrop, so neither disturbs the cue the audit identifies: M3 holding up across that shift (Section VI-D) is consistent with the backdrop cue persisting rather than with robustness, and M4 holding up is consistent with a cue this audit has not identified. And we make no claim about what the normalized models see in aggregate, because a 128 px bottleneck degrades activation-based attribution as much as it degrades the input (Section S-I-J).

One conclusion survives under either reading, and it cautions against a common practice. **A visually convincing, product-centered Grad-CAM map is not evidence that a model learned the intended task.** That claim rests on the un-normalized model, whose input is unaltered and whose attribution is not in question: it is strongly product-centered, and it classifies 6% of external images correctly.

## VII. The Ablation Study, in Brief

Sections S-I-N to S-I-X ablate the correction per axis, per architecture, per constant and per composition order. Five conclusions carry into the discussion; Section S-I-X gives the experiment behind the last of them.

**The three axes are complementary, not redundant.** Individually they take M4's external accuracy from 5–9% to 22.0%, 27.3% and 12.7%, and jointly to 78.0% in the same run (Table S11) — what one expects if the confound is a *capture pipeline* expressed through several correlated statistics rather than one. **A fourth plausible axis is not part of the mechanism:** gray-world white balance recovers 0.067 alone and costs 4.0 points added to the production operator, despite a real warm cast in the pool. **The effect is architecture-dependent:** the correction does nothing for the color-histogram baseline, whose in-distribution accuracy instead collapses from 0.838 to 0.541 (Table S13), because that model's entire decision function was the shortcut. **The constants are conservative rather than tuned:** sweeping all three moves external accuracy across 0.480–0.873 with no knife edge, and a 96 px short side would beat the 128 px we report (Table S14). We have not re-tuned around it, because choosing preprocessing by its external score is the target-distribution leakage Section IX warns about.

**And composition order matters more than any of the three magnitudes.** Eq. (8) fixes one order — resolution, then brightness, then compression — which was never justified, and two of the three operators impose an information bottleneck rather than an alignment, so there is no reason to expect them to commute. Running all 3! = 6 orderings at the production constants on M4, inside one execution (Table S21), separates them perfectly along the axis the mechanism predicts: the three that apply the JPEG bottleneck *after* the resolution cap score 0.820, 0.847 and 0.880 externally, the three that apply it before score 0.380, 0.467 and 0.540, and the groups are 28 points apart with no overlap. Compressing at native resolution and then downsampling largely undoes the compression, because the resampling filter averages over the quantization artifacts the bottleneck exists to impose.

Two consequences bear on how any such pipeline should be reported. **In-distribution ranking is not merely uninformative here; it is inverted** — the ordering with the highest Split B accuracy of all six (B, C, R at 0.946) has the lowest external accuracy of all six, 0.380, so a practitioner selecting the order the ordinary way would have chosen the worst of six while watching a 2.7-point in-distribution spread conceal a 50-point external one. And **the reported order is again conservative**: R, C, B beats production on both axes (0.880 against 0.820 externally, 0.932 against 0.919 in-distribution), and we have not re-run the paper around it, for the reason just given. Composition order is normally left implicit in a preprocessing description; on this evidence it deserves the treatment of a hyperparameter — reported, and not chosen in-distribution.

## VIII. Discussion

### A. What the reported accuracies on this dataset actually measure

Four results constrain interpretation, in decreasing order of force. A classifier reading three acquisition scalars and no pixels reaches 100% on the leakage-free partition, and the filename extension alone is correct on all 510 images. A 97-parameter linear model on color histograms reaches 83.8%, its decision function dominated by a single brightness proxy, and that accuracy falls to 54.1% once brightness is standardized. The first is a ceiling already reached: everything an in-distribution evaluation on this dataset can measure is available without looking at the packaging at all.

This does not imply prior work here is careless. It implies the dataset is defective in a way no in-distribution measure can reveal — not stratification, cross-validation, bootstrap intervals or the product-level grouping we introduce. Two things do, and neither is an accuracy: the metadata audit of Section VI-A, which asks how the images were acquired rather than how well they are classified, and evaluation on data someone else acquired.

### B. Why leakage turned out to be the smaller problem

We expected image-level leakage to dominate, because that is what the surrounding methodological literature emphasizes [11] and what a methodologically-minded reader raises first. It did not: at most 6.8 points across split designs, 0.3 [−1.9, +2.4] when varied on its own, against a confound worth more than 90.

The generalizable point concerns the ordering of audits. Leakage checks are cheap and increasingly routine; acquisition audits are equally cheap — read the metadata, cross-tabulate it against the label — and are not routine at all, and here the second was worth an order of magnitude more than the first. A field that performs one and not the other is auditing the smaller risk.

### C. Why the models behave differently

External behavior is not ordered by capacity but by *what kind of access* each model has to the confound: M1's feature space *is* the shortcut, so correction unlocks nothing; M2 reaches the same statistics through learned filters and recovers strongly once they are suppressed; and the two backbones inherit ImageNet invariances that afford partial protection, degrading severely at baseline without collapsing to zero. Section S-I-Q develops this. Since Section VI-E leaves neither backbone shown to recognize packaging, access to the confound and what the evaluation happens to vary are the axes that explain these rows; capacity is not.

### D. Practical implications

**For dataset publishers.** Document the acquisition procedure for each class and state whether both came from the same one — a single sentence that would have made this study's central finding visible without any of its analysis. Publishing a raw archive rather than a normalized one also preserves the traces a cheap audit reads. **For reviewers.** Ask how each class was obtained, and whether the model was evaluated on data the authors did not collect. On this dataset either question would have been decisive.

### E. The correction is a case study in substituting one confound for another

The normalization of Eq. (8) does what it was designed to do: label-free, under 17 ms, and worth 80.7 to 86.0 points of external specificity for two of the three models it is applied to — M3's apparent gain lies inside seed variance (Section VI-C) — at an in-distribution cost of at most 1.4. We nevertheless report it as an instrument and not a remedy, and four results already given are the reason. *The recovered accuracy is not shown to rest on the packaging* (Section VI-E), while both external sets share one dark backdrop. *The exchange is not stable*: M2, the best corrected model on Split C, falls to 0.463 on a second capture of the same products, and to 0.627 ± 0.135 across five seeds (Section VI-D), which a correction that had truly removed the dependence on acquisition would not do. *The pipeline is under-determined by its own description*: permuting operator order alone moves external accuracy 50 points under a 2.7-point in-distribution range, with the in-distribution ranking inverted (Section VII), so a detail a methods section leaves implicit decides most of the result and the usual way of settling it picks the worst option. *Removing more information keeps helping*: tightening the resolution bottleneck from 128 px to 96 px raises external accuracy to 0.873 (Section VII, Table S14), which is what a coarse distribution match predicts and not what restored reading of printed detail predicts.

None of this makes the operator useless; it fixes what it is for. One objection has to be met first: the axes were chosen because Table 3 showed them separating the pool from Split C, so an intervention on those axes might seem guaranteed to help. It is not — a bottleneck that removed the discrepancy while destroying the signal would have driven in-distribution accuracy to chance, as it does for M1 (Table S13). What the experiment establishes is causal with respect to those three discrepancies and nothing more: how much of the observed failure they account for, here 81 to 86 points of the roughly 94 lost. It is not evidence that the corrected models learned to recognize packaging, which Section VI-E addresses and does not establish. Read instead as something to deploy, it trades an audited cue for an unaudited one: the same move, at one remove, that produced the dataset this paper is about. **A correction is itself dataset construction, and is owed the same audit as a dataset**, to which Section VIII-F's taxonomy applies exactly as it does to a raw archive.

### F. A taxonomy of provenance defects, and what detects each

"Provenance confound" is not one defect but a small family, each member needing a different check, and the datasets audited here failed in different ways. **Type A** is the acquisition-statistic confound this paper is mostly about (the Kaggle pool, audit accuracy 1.000). **Type B** is a content or modality confound, on which metadata may be silent (the Roboflow archive, 57/57 against an audit accuracy of 0.717, Section S-I-W). **Type C** is one reintroduced when a *derived* set is drawn from a differently-acquired part of a clean source, which is how our own first synthetic proxy failed before use. **Type D** is a shipped split whose partitions do not partition. **Type E** is the audit's false-positive mode, a real difference between the objects registering as an acquisition one (the signature corpus of Section S-I-W, format 0.500 against size 0.843). This study therefore contributes a stronger form of a known failure and a different cause for it, and because the population at risk is nameable before any data is collected, a screening rule rather than a cautionary tale. Section S-I-T gives each type its detector, its cost when undetected and its repair, and develops the two lessons that cut across them: publisher-side tidying suppresses the symptom rather than the disease, so a curated dataset is *harder* to audit than a raw one; and the audit's output is not a verdict, since establishing that the separating statistic is an acquisition artifact rather than a property of the objects is a second step.

### G. What would falsify the general claim

The claim of Section I-A is causal — asymmetric class availability *produces* provenance confounding — and we state what evidence would count against it. Datasets in which the scarce class was obtained by the same procedure as the abundant one should show no Type A confound; [3], which photographed authentic and counterfeit samples on one Raspberry Pi rig, is the one study in Table 1 that plausibly meets this condition, and it also reports the lowest accuracy in that table. Conversely, a survey of authenticity datasets that found the audit firing no more often on separately-sourced collections than on jointly-sourced ones would refute the mechanism. That survey is the natural next study and we have not performed it: two datasets in one application area, plus one corroborating report from another [30], is enough to motivate the mechanism and not enough to establish its prevalence.

## IX. Limitations

Section S-II states each of these in full, with the evidence for and against; the list here is complete but compressed.

**The external evaluation is authentic-only**, so every external number is a specificity — the rate at which genuine packaging is called genuine — and nothing else. The synthetic proxy perturbs genuine photographs and is a corruption-robustness test in the spirit of ImageNet-C [12], never a recall measurement.

**Both external sets share one backdrop.** They vary device and lighting on the same products, so the surround cue of Section VI-E is untested — the study's most consequential gap, qualifying every claim that the correction "holds" across a capture shift.

**"Leakage-free" means product-identity leakage only.** No partition of this pool can decorrelate acquisition, because the counterfeit class exists in exactly one capture pipeline. Cross-validating across sources fails for the same reason: the only other public authentic/counterfeit pharmaceutical dataset has a counterfeit class unusable at any position in a fold, so a source-held-out fold would hold no negatives.

**The correction is a preprocessing bottleneck, not a domain-adaptation method, and is not compared against one.** Eq. (8) is a *zero-target-sample baseline*. Anyone holding even unlabeled target images should benchmark representation-level alignment against it and expect to win; the margin is unmeasured because every such method consumes target data, which would forfeit Split C as an external evaluation.

**The normalization axes were chosen with knowledge of the external set.** The operator itself consumes no target data, and Section S-I-S nominates the same three axes from the training partition alone under a threshold declared in advance. That answers the objection on this dataset and not in general, because no training-set procedure can nominate an axis confounded only in deployment.

**The generality claim is a mechanism with a stated test, not a measured rate.** Two datasets in one application area, seven audited across four (Section S-I-W) and one convergent report from another field [30] motivate the mechanism without establishing how often it occurs; Section X names the survey that would.

**Statistical power is thin throughout.** Test partitions hold 74–76 images, every pairwise comparison is underpowered, and the ablations are single executions, so a difference of a point or two should not be read as one. Section S-I-U repeats the production and baseline conditions at five seeds: the correction's effect on M2 and M4 is an order of magnitude beyond seed variance, M3's is inside it, and M2's Split D accuracy varies by ±0.135. The seed variance of the ablations themselves is unmeasured.

**Both transfer models are frozen backbones**, which Section V-B argues is the right instrument here and which CPU-only hardware also required: **nothing here measures a fine-tuned network**, so no result of ours bounds what transfer learning can do (Section X).

**The attention audit rests on 62 maps scored by a single annotator**, with no inter-rater agreement to report. An annotation-free occlusion analysis over every external image corroborates three of its four groups and contradicts the fourth; the content-aware measure that would settle the disagreement needs an annotation pass this study has not run.

**Some numbers predate checkpoint persistence and cannot be re-derived.** An earlier M4 accuracy of 0.946 could not be explained once the checkpointed pipeline deterministically produced 0.919, the original run's artifacts no longer existing. The newer value is reported; the older is unrecoverable rather than refuted.

## X. Future Work

**Acquire an external set that varies the photographic setting, and one that is counterfeit-labeled.** These are the two evaluations this study most needs and could not build. Both external sets share one backdrop, so neither disturbs the surround cue of Section VI-E; photographs against varied surfaces would test it directly, and are far cheaper than the counterfeit-labeled set. That set would most change what can be claimed, and its requirements are specific: independently photographed, verified by the pHash procedure of Section IV-B, and with acquisition balanced across its classes so that it does not import the confound it is meant to test.

**Build a training set with acquisition balanced across classes.** The confound cannot be filtered away, so the durable fix is at collection time: several independent photography setups, each contributing both classes.

**Fine-tune the backbones — the highest-priority item for anyone with a graphics processing unit (GPU).** No result here describes a fine-tuned network (Section IX), and **the frozen-backbone numbers are not an upper bound on what transfer learning can do here, in either direction.** The two outcomes are equally informative and opposite: adaptable features may discard the confound once the head can no longer profit from it, or the extra capacity may specialize onto residual acquisition artifacts more aggressively than a frozen trunk does — in which case fine-tuning would worsen external generalization while improving every in-distribution number, and Section VII's inversion suggests that would be invisible to anyone evaluating in-distribution.

**Survey the mechanism across application areas.** The most valuable extension is a measurement, not another model. A survey with a defined sampling frame, a pre-registered scoring rule and enumeration rather than listing-order sampling would convert the central claim from a motivated hypothesis into a measured prevalence, and needs no training runs. Section VIII-G states what would refute it.

**Test further acquisition axes, and settle the attribution disagreement.** Aspect ratio, sensor noise and staging conventions remain untested, and any new axis should be swept for composition position, not only for inclusion. A content-aware attention measure — attention mass inside an annotated product box rather than a radial ring — would settle where the two attribution methods of Section VI-E disagree; it is implemented and committed, and needs an annotation pass using rotated boxes, since many of these products sit diagonally.

## XI. Conclusion

We set out to measure how much of a reported accuracy on a small public counterfeit-medicine dataset survives methodological correction, expecting leakage to be the mechanism at issue. It accounted for very little: at most 6.8 points across split designs, and 0.3 points [−1.9, +2.4] when varied alone on a fixed test set. Almost all of the inflation is something else, with a structural cause reaching beyond the dataset we started from.

Wherever a binary image task asks whether something is genuine, the inauthentic class is harder to obtain and liable to be obtained differently, so the label comes to predict the acquisition process — which is easier to learn than the semantics, and which no partition of the same pool can expose. We ran stratification, grouped cross-validation, bootstrap intervals and a leakage-free product-level split; none saw anything wrong. Here every counterfeit-labeled file is a screen capture and every authentic-labeled file a downloaded photograph, without exception across 510 images; three acquisition scalars and no pixels then score 100% on the leakage-free partition. No in-distribution accuracy on this dataset can distinguish packaging authentication from provenance recognition.

The consequence is severe. On 150 authentic photographs from an independent source, two of four models were correct on zero images and the best in-distribution model on 3.3%, while scoring 97.4% on the authentic class of its own test partition. A label-free three-stage normalization raises external *specificity* to 86.0% and 80.7% for two of the three, at an in-distribution cost between −1.4 and 0.0 points — and that is not the repair it looks like. Rephotographing the same products on different hardware drops the from-scratch CNN to 0.463 in the run reported and to 0.627 ± 0.135 across five seeds, while the frozen backbones hold. Permuting only the order of the three operators moves external accuracy from 0.380 to 0.880 under a 2.7-point in-distribution range, with the in-distribution ranking inverted, so a practitioner tuning this preprocessing the ordinary way would have chosen the worst of six with no way to know. And the attribution evidence puts MobileNetV3's "authentic" verdicts on the background and leaves EfficientNet's unresolved. What the correction measures is how much of the failure the acquisition axes account for. It is not a remedy, because removing a confound from the input is itself dataset construction, and installs new ones as readily as the original construction did.

Gaps of 16 to 20 points remain for both transfer models, counterfeit recall is untested against real counterfeits, and none of these models should be deployed.

The methodological claim we would most like carried forward is cheap to act on. Before training anything, fit the classifier you intend to use to acquisition metadata alone — format, encoded size, resolution, aspect ratio — under your own leakage-free split, and report the number. It tells you whether a provenance shortcut is available, not whether your model takes it; but where it is high, no in-distribution accuracy on that dataset can distinguish the two. Here it is 1.000.

Two qualifications keep that recommendation honest, beyond the reading guide of Table S19. The audit is necessary but not sufficient: on a second pharmaceutical dataset it returned 0.717 while that dataset was confounded at least as badly (Section S-I-W), because its publisher had normalized the acquisition traces away without removing the confound. And it says nothing about whether a model generalizes; only data someone else acquired does that.

That the same signature has been documented independently in generated-image detection [30] is what a structural cause predicts, and we would expect it wherever a scarce class must be manufactured or harvested separately from an abundant one.

## Acknowledgment

This work was carried out on a single consumer laptop, and the CPU-only constraint that shapes several of this paper's design decisions follows from that. We thank the maintainers of the three public datasets used here [19], [20], [21]. The Mendeley and Roboflow datasets are distributed under CC BY 4.0; the Kaggle dataset carries no license, so it is attributed to its uploader, nothing from it is redistributed, and readers reproducing the pool must obtain it from the original listing.

This paper is critical of the construction of a dataset whose uploader made it freely available and made no research claim about it. That criticism is directed at a property of the artifact and at the practice of adopting such artifacts unaudited; it is not directed at the uploader, and nothing here suggests bad faith. The same applies to the prior studies of Section II-F, whose reported accuracies we do not dispute and have not re-derived.

**Generative-AI disclosure.** This manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic. Its use covered drafting and revising the text of every section, writing and debugging the analysis and figure-generation code, and identifying several defects in earlier versions of the pipeline that are disclosed in Section S-I-G. All experimental design decisions, all interpretations, and the decision to report each negative and superseded result rather than remove it are the author's. Every number reported here is produced by committed code from committed data and was verified by re-execution, and no result, citation or reference was generated by a language model without verification against a primary source. The author takes full responsibility for the content.

## Ethics, Conflicts of Interest, and Data Provenance

**Human and animal subjects.** This study involves neither. All images are photographs of pharmaceutical packaging from public archives; none depicts an identifiable person, and no personal or patient data was accessed.

**Data provenance and permissions.** Every image originates from a third-party public archive, used within its stated terms: Mendeley Data and Roboflow under CC BY 4.0 with attribution, and the Kaggle archive under no stated license, from which nothing is redistributed. No data was scraped or purchased.

**Intended use and misuse.** No model examined here is fit to authenticate medicine, and a falsely reassuring authentication tool is more dangerous than no tool.

**Conflicts of interest.** The author declares none, has no affiliation with the maintainers of any dataset examined here, and no commercial interest in any authentication product.

**Funding.** This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Generative-AI disclosure.** Stated in full in the Acknowledgment, as IEEE Access directs.

---

## Data and Code Availability

**Repository.** All code and derived artifacts are at `https://github.com/sophiezla/counterfeit-drug`, archived at **doi:10.5281/zenodo.22166543** (release v1.1.0), the exact state of the code that produced every number reported here; doi:10.5281/zenodo.21936720 resolves to the most recent release. It holds the data pipeline, the four model implementations, every analysis and figure script, the per-image statistics and split assignments, the persisted checkpoints, and the sources of this manuscript and its supplement.

It deliberately contains **no images**: the Kaggle archive carries no license grant, so only derived per-image statistics, split assignments and filenames are redistributed. Grad-CAM overlays and the manual-review contact sheets are excluded for the same reason, and are regenerated by committed scripts from a reader's own copy of the archives.

Five analysis scripts read only committed artifacts, need no image data and no training, and reproduce Table 4, Tables S18 and S20, the direct exposure count and the external intervals in seconds — covering the paper's two central quantitative claims without requiring a reader to obtain the images or run a model. Section S-V names them.

## References

This list is shared with the supplementary material, which cites it by the same numbers; references [17], [18], [22] and [24] are cited there rather than here.

> **Reference verification status.** Every reference has been verified against a primary source: full author lists, venues, volume/issue and DOIs were read from the publisher or indexed record rather than from an aggregator page or from recollection. Where a detail could not be confirmed it is omitted rather than guessed, and said so. Two additional sources encountered during the literature search — a graph-neural-network counterfeit detector operating on chemical structure, and a GAN + CNN + blockchain authentication system — were deliberately **excluded** because no primary source could be located for either; they should be added only if one is found, and never cited from an aggregator summary.

[1] World Health Organization, "Substandard and falsified medical products," WHO fact sheet, 3 Dec. 2024. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/substandard-and-falsified-medical-products. *Verified against the primary source; states "at least 1 in 10 medicines in low- and middle-income countries are substandard or falsified". Fact sheets are revised in place, so the access date should be refreshed at submission.*

[2] S. Ozawa, D. R. Evans, S. Bessias, D. G. Haynie, T. T. Yemeke, S. K. Laing, and J. E. Herrington, "Prevalence and estimated economic burden of substandard and falsified medicines in low- and middle-income countries: A systematic review and meta-analysis," *JAMA Network Open*, vol. 1, no. 4, e181662, 2018, doi: 10.1001/jamanetworkopen.2018.1662. *Verified against the primary record; replaces the unsourced industry market-size estimate carried over from [3].*

[3] R. R. T. Ramos, K. R. B. Samonte, and C. O. Manlises, "Medicine authentication based on image processing using convolutional neural networks," in *Proc. 16th Int. Conf. Computer and Automation Engineering (ICCAE)*, 2024, pp. 278–282, doi: 10.1109/ICCAE59995.2024.10569752. *Author list, venue, page range and DOI verified 2026-08-28 against the indexed conference record; the page range and DOI were added then.*

[4] H.-W. Ting, S.-L. Chung, C.-F. Chen, H.-Y. Chiu, and Y.-W. Hsieh, "A drug identification model developed using deep learning technologies: Experience of a medical center in Taiwan," *BMC Health Services Research*, vol. 20, art. 312, 2020, doi: 10.1186/s12913-020-05166-w.

[5] K. Al-Hussaeni, I. Karamitsos, E. Adewumi, and R. M. Amawi, "CNN-based pill image recognition for retrieval systems," *Applied Sciences*, vol. 13, no. 8, art. 5050, 2023, doi: 10.3390/app13085050.

[6] R. Geirhos, J.-H. Jacobsen, C. Michaelis, R. Zemel, W. Brendel, M. Bethge, and F. A. Wichmann, "Shortcut learning in deep neural networks," *Nature Machine Intelligence*, vol. 2, pp. 665–673, 2020, arXiv:2004.07780.

[7] J. R. Zech, M. A. Badgeley, M. Liu, A. B. Costa, J. J. Titano, and E. K. Oermann, "Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs: A cross-sectional study," *PLOS Medicine*, vol. 15, no. 11, e1002683, 2018, doi: 10.1371/journal.pmed.1002683.

[8] B. G. Hill, F. L. Koback, and P. L. Schilling, "The risk of shortcutting in deep learning algorithms for medical imaging research," *Scientific Reports*, vol. 14, no. 1, art. 29224, 2024, doi: 10.1038/s41598-024-79838-6.

[9] J. Seah, C. Tang, Q. D. Buchlak, M. Milne, X. Holt, H. Ahmad, J. F. Lambert, N. Esmaili, L. Oakden-Rayner, P. Brotchie, and C. M. Jones, "Do comprehensive deep learning algorithms suffer from hidden stratification? A retrospective study on pneumothorax detection in chest radiography," *BMJ Open*, vol. 11, no. 12, e053024, 2021, doi: 10.1136/bmjopen-2021-053024.

[10] A. Trivedi, C. Robinson, M. Blazes, A. Ortiz, J. Desbiens, S. Gupta, R. Dodhia, P. K. Bhatraju, W. C. Liles, J. Kalpathy-Cramer, A. Lee, and J. Lavista Ferres, "Deep learning models for COVID-19 chest x-ray classification: Preventing shortcut learning using feature disentanglement," *PLOS ONE*, vol. 17, no. 10, e0274098, 2022, doi: 10.1371/journal.pone.0274098.

[11] M. Ü. Öner, Y.-C. Cheng, H. K. Lee, and W.-K. Sung, "Training machine learning models on patient level data segregation is crucial in practical clinical applications," medRxiv preprint, 2020, doi: 10.1101/2020.04.23.20076406. *Preprint; no peer-reviewed version was located, and it is cited here for the patient-level-segregation argument only.*

[12] D. Hendrycks and T. Dietterich, "Benchmarking neural network robustness to common corruptions and perturbations," in *Proc. Int. Conf. Learning Representations (ICLR)*, 2019, arXiv:1903.12261.

[13] A. Howard, M. Sandler, G. Chu, L.-C. Chen, B. Chen, M. Tan, W. Wang, Y. Zhu, R. Pang, V. Vasudevan, Q. V. Le, and H. Adam, "Searching for MobileNetV3," in *Proc. IEEE Int. Conf. Computer Vision (ICCV)*, 2019, pp. 1314–1324, arXiv:1905.02244.

[14] M. Tan and Q. V. Le, "EfficientNet: Rethinking model scaling for convolutional neural networks," in *Proc. Int. Conf. Machine Learning (ICML)*, 2019, arXiv:1905.11946.

[15] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, "Grad-CAM: Visual explanations from deep networks via gradient-based localization," in *Proc. IEEE Int. Conf. Computer Vision (ICCV)*, 2017, arXiv:1610.02391.

[16] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2017, arXiv:1705.07874.

[17] A. Paszke, S. Gross, F. Massa, et al., "PyTorch: An imperative style, high-performance deep learning library," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2019.

[18] F. Pedregosa, G. Varoquaux, A. Gramfort, et al., "Scikit-learn: Machine learning in Python," *Journal of Machine Learning Research*, vol. 12, pp. 2825–2830, 2011.

[19] S. K. Jha, "Fake vs Real Medicine Dataset (images)," Kaggle, dataset `surajkumarjha1/fake-vs-real-medicine-datasets-images`, last updated 13 Oct. 2025, license stated as "Unknown". [Online]. Available: https://www.kaggle.com/datasets/surajkumarjha1/fake-vs-real-medicine-datasets-images. *Identity re-confirmed 28 Aug. 2026 against the local archive on two independent byte totals: the downloaded zip is 279,469,596 bytes, which matches the listing's `totalBytes` exactly, and its 2,228 members sum to 279,596,681 bytes uncompressed. Earlier notes quoted the second figure as though it were the listing value; they are different quantities and both are now stated. Usage figures quoted in Section II-F (3,039 views, 591 downloads, 3 public notebooks, 2 votes, no discussion) were read from the live listing on 28 Aug. 2026; downloads moved 540 → 574 → 591 between 29 Jul. and 28 Aug. 2026 while notebooks, votes, license and last-updated date did not change. They change, so refresh them if the manuscript is held; the argument depends on the order of magnitude, not the exact count.*

[20] E. Abdelmaksoud, A. Gadallah, and A. Asad, "Mobile-captured pharmaceutical medication packages," Mendeley Data, V1, doi: 10.17632/bjy2svvmn8.1, CC BY 4.0. *Author list corrected 2026-08-28 after re-checking against the dataset landing page and DOI resolution: the given names are Esraa, Ahmed and Ahmed, not the initials M./H./M. previously carried over from an earlier note.*

[21] Harshini T. G. R., "Counterfeit_med_detection," Roboflow Universe, version 4 (multiclass export), Nov. 2022, CC BY 4.0. Accessed: Aug. 28, 2026. [Online]. Available: https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection. *Contributor name, license, version count and year confirmed in a browser on 28 Aug. 2026 against the publisher's own suggested citation; the landing page rejects automated requests, which is why an earlier note deferred this. The version date, the 4,260-image count and the "resize to 640x640 (stretch)" preprocessing that Section S-I-W attributes to the publisher are read from `README.roboflow.txt` inside the export archive held locally.*

[22] Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," *Psychometrika*, vol. 12, no. 2, pp. 153–157, 1947.

[23] K. Zhou, Z. Liu, Y. Qiao, T. Xiang, and C. C. Loy, "Domain generalization: A survey," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 45, no. 4, pp. 4396–4415, 2023, doi: 10.1109/TPAMI.2022.3195549, arXiv:2103.02503. *Author list, volume, issue and page range verified 2026-08-28 against the publisher-of-record listing; Crossref still carries the early-access record (pp. 1–20, 2022), so the final pagination was taken from the issue record instead.*

[24] B. Efron and R. J. Tibshirani, *An Introduction to the Bootstrap*. New York, NY, USA: Chapman & Hall, 1993.

[25] C. Zauner, "Implementation and benchmarking of perceptual image hash functions," M.Sc. thesis, Upper Austria University of Applied Sciences Hagenberg, Jul. 2010. [Online]. Available: https://www.phash.org/docs/pubs/thesis_zauner.pdf. *Verified: institution, year and title confirmed against the thesis PDF hosted by phash.org.*

[26] K. Motwani, R. Dsouza, R. Dsouza, and J. Jose, "Counterfeit medicine detection using deep learning," *International Journal of Innovative Research in Technology (IJIRT)*, vol. 9, no. 3, pp. 818–821, Aug. 2022, ISSN 2349-6002. *Full text re-read 2026-08-28; volume, issue, page range and ISSN taken from the article's own running head, and the page range added then. The counterfeit class is constructed by the authors by altering logos and text on web-scraped authentic packaging images: "we scraped medicines of 10 manufacturers ... due to the lack of availability of fake images, we ourselves created by altering the logo and text on the package."*

[27] B. S. Thomson and W. R. Varuna, "An intelligent counterfeit medicine classification prediction system using modified YOLO: A single stage object detector," *TPM (Testing, Psychometrics, Methodology in Applied Psychology)*, vol. 32, no. S2, pp. 1073–1088, 2025, ISSN 1972-6325. *Full text re-read 2026-08-28; volume, issue, page range and ISSN confirmed against the article's own running head. trains on GAN-synthesized counterfeit images derived from a Kaggle pharmaceutical pill dataset and tests against DrugBank and drugs.com imagery.*

[28] B. S. Thomson and W. R. Varuna, "Detecting counterfeit medicines utilizing artificial intelligence technique," *International Journal of Creative Research Thoughts (IJCRT)*, vol. 13, no. 4, pp. i322–i329, Apr. 2025, ISSN 2320-2882. *Full text re-read 2026-08-28, volume, issue, page range and ISSN confirmed against the running head; reports 92% accuracy over an image set cited only as a drugs.com URL, with no image count stated, though the paper does state an 80/10/10 train/test/validation split.*

[29] H. Garcia-Cotte, D. Mellouli, A. Rehman, L. Wang, and D. G. Stork, "Deep neural network-based detection of counterfeit products from smartphone images," arXiv:2410.05969, 2024.

[30] P. Grommelt, L. Weiss, F.-J. Pfreundt, and J. Keuper, "Fake or JPEG? Revealing common biases in generated image detection datasets," in *Computer Vision – ECCV 2024 Workshops*, Lecture Notes in Computer Science. Cham, Switzerland: Springer, 2025, pp. 80–95, doi: 10.1007/978-3-031-92089-9_6, arXiv:2403.17608. *Verified 2026-08-28 against both the arXiv record and the Crossref record for the published version; this reference was upgraded from the preprint to the peer-reviewed proceedings entry then. Cited as the closest independent analogue of this paper's finding: real/generated separation by JPEG compression and image size on the GenImage benchmark, detectors partly reducible to JPEG detectors, and >11-point cross-generator shifts after equalization, all four claims checked against the abstract of record.*

---


---

[31] A. J. DeGrave, J. D. Janizek, and S.-I. Lee, "AI for radiographic COVID-19 detection selects shortcuts over signal," *Nature Machine Intelligence*, vol. 3, no. 7, pp. 610–619, 2021, doi: 10.1038/s42256-021-00338-7. *Authors, journal, volume, issue, page range and year verified 2026-08-29 against the Crossref record; the quoted phrase is from the abstract of the preprint of the same title and authors (Europe PMC PPR213715). The published full text is paywalled, so nothing is claimed here about its methods or datasets beyond what that abstract states.*

[32] A. Torralba and A. A. Efros, "Unbiased look at dataset bias," in *Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)*, 2011, pp. 1521–1528, doi: 10.1109/CVPR.2011.5995347. *Title, authors, venue, year and page range verified 2026-08-29 against the Crossref record. Cited for the dataset-bias framing itself, not for a specific numerical result.*

## Author Biographies

![Sophie Zhu](paper/figures/author_photo.jpeg)

**SOPHIE ZHU** is a student at Mira Costa High School, in Manhattan Beach, CA, USA. Her research interests include computer vision and machine learning applications in public health, with an emphasis on low-cost systems for resource-constrained environments. Her current work examines how dataset construction shapes what image classifiers learn.
