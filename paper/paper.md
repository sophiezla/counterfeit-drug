# Asymmetric Class Sourcing Creates Provenance Confounds in Authenticity-Classification Image Datasets: Detection, Cost, and Partial Repair

**SOPHIE ZHU**<sup>1</sup>

<sup>1</sup>Mira Costa High School, Manhattan Beach, CA 90266 USA (e-mail: sophiezhu2028@gmail.com)

ORCID: 0009-0004-2403-910X

Corresponding author: Sophie Zhu (e-mail: sophiezhu2028@gmail.com).

This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors. The manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic; see the disclosure in the Ethics section.

---

**ABSTRACT** In binary image tasks asking whether an object is genuine, the inauthentic class is scarcer, so it is obtained differently: screen-captured, scraped, edited, or generated. The label then predicts the acquisition process, not the property of interest, and no in-distribution evaluation can expose this: every held-out partition inherits the confound in the same proportion. We call this class-conditional provenance confounding. In a public counterfeit-medicine dataset every counterfeit-labeled file is a PNG screen capture and every authentic-labeled file a JPEG photograph, without exception, and the shipped training folder is a superset of its own test folder. A logistic regression on three acquisition scalars and no pixels reaches 100% on a leakage-free partition, bounding what acquisition alone explains. Across four model families, correcting the split changes in-distribution accuracy by at most 6.8 points, whereas external validation on 150 independent photographs drops the strongest model from 97.4% to 3.3%. A label-free normalization of resolution, brightness and compression restores 77–86% external accuracy at negligible in-distribution cost, but we report it as a diagnostic, not a remedy: a second capture shift drops the best corrected model to 46%, permuting only the operators' order moves external accuracy 50 points and ranks the worst pipeline highest in-distribution, and an attention audit finds the recovered accuracy resting on the background in 40 of 40 external maps. A correction is itself dataset construction, and substitutes confounds as readily as it removes them. We propose a provenance audit — fitting the intended classifier to acquisition metadata alone — as a cheap pre-training screen, run it across four application areas, and report where it misfires.

**INDEX TERMS** Data leakage, dataset bias, domain generalization, external validation, hidden stratification, image classification, provenance confounding, shortcut learning.

---

## I. Introduction

Substandard and falsified medical products are a persistent global health problem, concentrated in low- and middle-income countries and in unregulated online supply chains [1], [2]. Because much falsified product is visually imperfect — misprinted cartons, wrong color separations, missing batch information — image-based screening from a consumer smartphone is an attractive triage tool, and a body of work has accordingly applied convolutional networks to photographs of medicine packaging and reported high binary accuracy [3], [26]–[28], alongside a larger literature on pharmaceutical *identification* rather than *authentication* [4], [5].

A property of that body of work motivates this paper's method as much as its subject. There is no shared, curated benchmark for pharmaceutical authentication. Every study we could examine in full text built or adopted its own image set, by a different procedure, and none audited that set for confounds between acquisition and label (Section II-F). Accuracy figures in this sub-field are therefore not mutually comparable, and each rests on the unexamined construction of a single ad hoc collection.

### A. The general problem: asymmetric class sourcing

That condition is not peculiar to pharmaceuticals, and the mechanism it creates is this paper's subject. Consider assembling a two-class image dataset for any question of the form *is this genuine?* Authentic examples are abundant: manufacturers photograph their products, retailers publish catalogs, users can photograph what they own. The other class is scarce almost by definition — counterfeit stock is illegal to hold, forged documents are held as evidence, defective units are discarded. A researcher needing a negative class therefore obtains it *by some other means than the one that produced the positive class*: by screen-capturing regulator bulletins, scraping a different corpus, editing authentic images, or generating examples with a model.

Every such substitution introduces a systematic difference between the classes that has nothing to do with the property being labeled. Acquisition method determines file format, encoded size, resolution, noise floor, compression signature, color rendering and often backdrop; a label correlated with acquisition method is correlated with all of them. We call this **class-conditional provenance confounding**, and argue that asymmetric class availability makes it a *likely* outcome of dataset construction in this family of tasks rather than an occasional lapse.

Three properties make it damaging. It is **maximally learnable**: low-level global statistics are easier to extract than the semantics of a printed carton, so a shortcut-seeking optimizer [6] finds them first. It is **invisible in-distribution**: a held-out partition drawn from the same pool inherits the confound in the same proportion, so no amount of stratification, cross-validation, bootstrapping or leakage-aware grouping exposes it — we demonstrate this by doing all four and finding nothing. And it is **silent in the reporting record**: acquisition method is rarely documented, so a reader cannot detect it from a paper and often cannot detect it from the dataset either.

The status of the general claim should be stated exactly. We demonstrate a mechanism and a case, not a rate. Establishing that provenance confounding is the *default* rather than a recurring hazard would require auditing a representative sample of such datasets and reporting how many fail; neither this paper nor, as far as we can determine, any other has done that. Section VI-C takes a step by auditing seven datasets across four application areas, finding both a totally confounded case and a clean one — enough to show the audit discriminates, far short of a prevalence estimate. The claim is a hypothesis with converging support and a stated test; Section VIII-H says what would falsify it.

Part of that support comes from an unrelated field. In generated-image detection, real images are harvested from web corpora as lossy Joint Photographic Experts Group (JPEG) files at modest resolution while generated images are saved as lossless PNGs at native size; Grommelt *et al.* [30] show that on the standard GenImage benchmark this makes format, compression and size predictive of the label, that detectors partly become JPEG detectors, and that equalizing those factors shifts cross-generator performance by more than 11 points. That work and this share no data, no application area and no method of discovery, and arrive at the same confound — which is what a structural cause predicts and a coincidence does not.

### B. This paper

The study began as a methodological exercise. The Kaggle *Fake vs Real Medicine* set is small (661 images), freely available, and typical of what this area works with: two classes of packaging images, no data card, no stated acquisition protocol. We set out to establish how much of a reported accuracy survives methodological correction, under a protocol fixed in advance — quantify leakage by evaluating identical models under a naive and a product-grouped split, span four model families from a 97-parameter linear baseline to a 4-million-parameter pretrained backbone so capacity is measured rather than assumed, and validate on a genuinely external source verified independent rather than assumed so.

The result was not the one the design anticipated. Correcting the split changed in-distribution accuracy by at most 6.8 points. What changed the picture was external validation: on 150 authentic photographs from an independent source, two of four models classified *zero* correctly and the strongest in-distribution model 3.3%, despite 97.4% on the authentic class of its own test partition. That is not degradation; it is inversion.

Tracing the cause led to the dataset itself. Its two classes were not merely photographed differently, they were *acquired* differently: every counterfeit-labeled file is a screen capture (`Screenshot*.png`), every authentic-labeled file a downloaded photograph (`images*.jpg`), correlating with the label exactly 1.0 across the pool. Any model — including a 97-parameter linear classifier on a color histogram — has unobstructed access to this shortcut. In the terminology of Geirhos et al. [6] the dataset admits a shortcut both maximally predictive in-distribution and maximally uninformative out of it; in that of the medical-imaging literature it is a hidden stratification of the kind Zech et al. [7] found in chest radiographs, differing in being total rather than partial [8]–[10].

The contributions are:

1. **A named mechanism and a cheap detector.** We identify asymmetric class sourcing as a structural cause of provenance confounding (Section I-A) and propose the *provenance audit* — fitting the intended classifier to acquisition metadata alone, under the study's own leakage-free split — as a pre-training screen whose accuracy lower-bounds how much of any pixel-based result acquisition can explain (Section VI-A, Table 5). It needs no external data, no annotation and no pixel decoding, and returns 1.000 here.

2. **Evidence that the detector is necessary but not sufficient, with a diagnosis of when it fails.** On a second published dataset it returns only 0.717 although that dataset is confounded at least as severely — 57/57 of its counterfeit-labeled source images carry the ground-truth word in the pixels — because its publisher had normalized every image to a common resolution and format, suppressing the traces without touching the confound (Section VI-B). A tidied dataset is *harder* to audit, and silence must not be read as clearance. Run across four application areas the audit also exposes a false-positive mode (Section VI-C, Table 9).

3. **A quantified, previously unreported confound in the case-study dataset**, with effect sizes on brightness, resolution, aspect ratio and file size; an exact Shapley decomposition showing a linear model's decision is dominated by the statistic the confound controls; and a degenerate shipped split whose training folder is a superset of both others (Sections III-A, VI-A).

4. **A demonstration that classical leakage correction is the smaller problem.** Product-level grouping changes accuracy by at most 6.8 points against an analytic ceiling of 9.2 derived from the split alone, whereas the confound accounts for the difference between 97% in-distribution and 3% external accuracy (Sections VI-D–VI-F). The check the field has institutionalized is not the one that mattered.

5. **A label-free correction, ablated per axis, per architecture, per constant and per composition order — and reported as a case study in how easily one confound is exchanged for another.** It raises external accuracy from 0–3% to 77–86%, and we still decline to offer it as a remedy, because our own results say what that number is made of (Section VIII-E). Varying the *order* of the three operators — which a preprocessing description normally leaves implicit — matters more than any of their magnitudes: it moves external accuracy across a 50-point range under a 2.7-point in-distribution range, and the ordering scoring highest in-distribution scores lowest externally (Section VII-B, Table 10). A complete attention audit finds the recovered accuracy resting on the background rather than the packaging, in 40 of 40 external maps and identically in both backbones (Section VI-G), and the repair does not survive a second capture shift for the model it helped most (Section VI-F).

This is an empirical critique and a diagnostic method, and should be read as one. We propose no new architecture — the most useful thing to be said about architectures here is that a 97-parameter linear model and a 4-million-parameter pretrained network are not statistically distinguishable on this test partition, and that the in-distribution ranking does not predict the external one — and we do not propose the normalization of Section V-D for adoption either. Everything offered for adoption is a check: fit your classifier to acquisition metadata before training it, evaluate on images you did not collect, and audit a correction as you would a dataset.

## II. Related Work

### A. Image-based pharmaceutical authentication and identification

Image classification has been applied to pharmaceutical products both for *identification* (which drug is this?) and for *authentication* (is this drug genuine?). Ramos, Samonte and Manlises [3] proposed a convolutional neural network (CNN) based authentication system directly comparable in task framing to this work. Adjacent work concentrates on identification: Ting et al. [4] address look-alike/sound-alike medication errors across 250 blister-packaged drug types, and Al-Hussaeni et al. [5] apply CNNs to pill-image retrieval. This literature establishes that packaging and pill imagery carries usable discriminative signal. As far as this review found, none of it examines *why* reported accuracies are as high as they are, or audits its datasets for confounds between acquisition and label. The present work is orthogonal to it: rather than proposing an architecture, it audits the acquisition process, the evaluation protocol and the datasets such results rest on.

### B. Shortcut learning and hidden stratification

Geirhos et al. [6] formalized *shortcut learning*: networks adopt decision rules exploiting superficial, spuriously predictive correlations, scoring well in-distribution while failing wherever the shortcut is absent. That framing describes this paper's central finding precisely.

The failure has a documented precedent in medical imaging. Zech et al. [7] showed that pneumonia detectors trained on chest radiographs from three hospital systems could predict which system an image came from, and used that hospital-identity signal — itself correlated with disease prevalence — as a shortcut for the diagnostic label, degrading substantially on an unseen site. Later audits report the same pattern for scanner-, site- and manufacturer-level signal [8], [9], and early COVID-19 radiograph classifiers were shown to rely on dataset-source confounds rather than radiographic signs [10].

A difference in *cause* determines how far the present finding generalizes. In those cases the confound is an artifact of where data happened to come from: several sites contributed, differing in equipment and case mix, and the site–label correlation was incidental. In the tasks this paper concerns it is not incidental but produced by the researcher, because the negative class was unobtainable by the procedure that produced the positive one (Section I-A). That makes the confound total rather than partial, and predictable in advance: any dataset whose two classes were sourced separately is at risk.

The closest published analogue outside medicine is Grommelt et al. [30], who audit the GenImage benchmark and find its real and generated classes separated by JPEG compression and image size, because real images are harvested as lossy JPEGs while generated images are written as lossless PNGs at native resolution. Detectors trained on it partly function as JPEG detectors, and equalizing those factors shifts cross-generator performance by over 11 points. The parallel is worth stating precisely: the same three statistics, the same direction, the same in-distribution invisibility, and a correction of the same shape — in an unrelated application area, discovered independently.

### C. Data leakage and evaluation protocol

A related but distinct concern is train/test leakage from improper partitioning: splitting at the image rather than the subject level lets near-duplicate images of one entity appear in both partitions, inflating reported performance [11]. That motivated this work's two-split design — naive image-level and product-identity-level, evaluated in parallel so the leakage effect is measured rather than assumed. On this pool the measured effect is small relative to the capture-pipeline confound, which accounts for the great majority of the in-distribution/external gap. That ordering is itself a finding: acquisition-pipeline confounds deserve at least the attention image-level leakage currently receives.

### D. Robustness to synthetic corruption

Hendrycks and Dietterich [12] introduced ImageNet-C, applying standardized corruptions at multiple severities to measure robustness without collecting new out-of-distribution data. This work adopts the same logic: lacking a genuine counterfeit-labeled external dataset, independent authentic photographs are perturbed with print-quality, color and text-region defects to build a synthetic counterfeit proxy. Following [12] we state explicitly that such a proxy measures robustness to a documented perturbation style, not label-defined class recall.

### E. Architectures and interpretability methods

The four model families span a classical color-histogram baseline through MobileNetV3 [13] and EfficientNet-B0 [14], both used as frozen ImageNet-pretrained feature extractors with a linear head. Attention is inspected with gradient-weighted class activation mapping (Grad-CAM) [15]; attribution for the linear baseline uses Shapley values [16], which have a closed form for a linear model with an independent-feature background and need no sampling. Domain-generalization surveys [23] situate the normalization of Section V-D in a broader toolkit; it is closer to hand-designed covariate-shift alignment than to the representation-learning methods that literature mostly covers.

### F. What datasets this sub-field actually uses

Because this paper's contribution is a dataset audit, the datasets neighbouring results rest on are themselves prior work. We examined in full text, where obtainable, every study we could locate performing authentic-vs-counterfeit classification of pharmaceutical *images*; Table 1 records what each trained on. The survey is a best-effort search, not a systematic review, and its negative findings should be read as "not found by this search".

**TABLE 1.**Image sources used by located prior work on pharmaceutical authentication, and the acquisition-audit status of each. "Audit" asks whether the study reports any check that acquisition conditions are balanced across its two classes.

| Study | Image source | Class construction | Reported accuracy | Audit |
|---|---|---|---|---|
| Ramos *et al.* [3] | Self-captured, Raspberry Pi camera; one brand (Biogesic paracetamol) | Physical authentic and counterfeit samples, same rig | 88.75% | none reported |
| Motwani *et al.* [26] | Web-scraped packaging images, 10 manufacturers | Counterfeit class **created by the authors** by altering logo and text on authentic images | not reported per-class | none reported |
| Thomson and Varuna [27] | A Kaggle *pill and vitamin* dataset for training; DrugBank and drugs.com images for testing | Counterfeit class **generated by generative adversarial network (GAN) synthesis** | not comparably reported | none reported |
| Thomson and Varuna [28] | drugs.com product images | not specified | 92% | none reported |
| Roboflow *Counterfeit med detection* [21] | Regulator advisory bulletins plus product photographs | Class correlates with document type, not authenticity (Section III-B) | — | — |

Three observations follow, and each bears directly on the finding of Section VI-A.

**No shared benchmark exists, so the confound cannot be inherited — only re-invented.** No two studies in Table 1 evaluate on the same images. The Kaggle set audited here is not a community benchmark in the sense that term usually carries: as of 28 August 2026 its Kaggle listing records 3,039 views, 591 downloads, 3 public notebooks, 2 votes and no discussion, states its license as "Unknown", and a search of the literature found no peer-reviewed study that uses it at all. The claim this paper makes is correspondingly narrow and, we think, more useful: not that a widely-shared benchmark is broken, but that a dataset assembled the way this sub-field routinely assembles datasets contains a total acquisition confound that its own users did not detect.

**The most common class-construction procedures make the confound near-inevitable.** In [26] the counterfeit class is produced by digitally editing authentic images; in [27] it is produced by a generative model. In both cases the two classes are, by construction, outputs of two different image pipelines, exactly as in the dataset audited here — and neither study reports a check that would surface it. A model can score highly on such a set by learning the editing or generation signature, and no in-distribution evaluation would distinguish that from learning authenticity. Where the two classes *were* acquired under a common protocol — [3], which photographs real authentic and real counterfeit samples on one Raspberry Pi rig — the reported accuracy is the lowest in Table 1 (88.75%), which is at least consistent with the confound accounting for part of the spread.

**Studies that do control acquisition say so explicitly.** Outside pharmaceuticals, Garcia-Cotte *et al.* [29] report counterfeit detection on branded garments from smartphone images captured "under natural, weakly controlled conditions" in stores, warehouses and customs checkpoints, at 99.71% after a 3.06% rejection rate. Whatever else separates that work from Table 1, it states its acquisition regime as a property of the result. That is the reporting standard we argue Section VIII-D should become routine here.

## III. Dataset

### A. Sources considered

Three public sources were inventoried (Table 2). All were considered for the modeling pool; two were excluded for reasons below, and one became the external evaluation set.

**TABLE 2.**Public sources inventoried, with their role in this study.

| Source | Files as shipped | License | Role |
|---|---|---|---|
| Kaggle *Fake vs Real Medicine* [19] | 661 unique (`Fake/` 240, all `.png`; `Real/` 421, all `.jpg`), re-listed across a bundled `train`/`val`/`test` split | "Unknown" per the Kaggle listing; none stated in the archive | Modeling pool (Splits A and B); the dataset used by [3] |
| Roboflow *Counterfeit_med_detection* v4 [21] | 4,260 (includes the publisher's own 3× rotation/exposure augmentation) | CC BY 4.0 | Excluded from modeling; retained as a supplementary authentic pool |
| Mendeley *Mobile-Captured Pharmaceutical Medication Packages* [20] | 3,900 across six devices; the 150-image "Huawei CN" single-instance-per-product subset was used | CC BY 4.0 | External evaluation (Split C), authentic only |

Two properties of the primary source should be recorded before any result is read: both are verifiable in seconds by anyone holding the archive, and neither appears to have been noted previously.

**Provenance.** It is a single-uploader Kaggle contribution, last updated 13 October 2025, distributed with its license field set to "Unknown". Counterfeit-class files are named `Screenshot YYYY-MM-DD HHMMSS.png`, with embedded timestamps falling in a small number of capture sessions; authentic-class files are named `imagesNN.jpg`. There is no data card, no collection protocol and no provenance for any individual image — none of which is unusual for a dataset of this kind, which is the point of Section II-F.

**The bundled split is not a split.** Alongside the class folders the archive ships `train/`, `val/` and `test/`. Counting unique filenames:

|T| = 661,  |V| = 453,  |E| = 449,  V ⊂ T,  E ⊂ T,  |V ∩ E| = 286

The training folder contains **every image in the dataset**, and validation and test are proper subsets of it — 453 of 453 and 449 of 449 — with 286 images in all three. A study adopting this partition trains on 100% of the data it then reports test accuracy on. We discarded it and built our own (Section IV-C), and record it here because it is a second, independent, fully deterministic defect in the same artifact, and one no reader could detect from a reported accuracy.

### B. Why the second source was excluded: a label baked into the pixels

The Roboflow source appeared to be a second independent authentic/counterfeit dataset, and therefore a candidate both for pooling and for cross-dataset validation. Inspection showed it is neither. Of its counterfeit-labeled images, 57/57 unique source images are institutional advisory graphics — multi-panel collages carrying a regulator's logo, a banner headline and, critically, **the ground-truth label rendered as literal text inside the image** (`COUNTERFEIT` or `AUTHENTIC` overlaid on the photograph) — while 263/263 of its plain product photographs are authentic-labeled. A model trained on it as shipped would learn to distinguish advisory collages from product photography. Two units of count are easy to conflate here: the publisher ships each photograph with its own 3× augmentation, so 57 unique counterfeit-labeled *source images* correspond to 180 *files*. Excluding those, plus 9 more found by manual inspection and 52 rows carrying simultaneous `authentic=1` and `counterfeit=1` annotations, the source contributes **2** usable counterfeit images against 2,695 authentic. Prior work attributes its unsuitability to class imbalance; the deeper problem is a modality confound.

### C. Why the two sources are not independent

Perceptual-hash clustering (Section IV-B) found **229 clusters containing images from both sources**, covering 2,900 of 4,027 retained Roboflow images and 290 of 661 Kaggle images — **44% of the Kaggle dataset has a near-duplicate in the Roboflow source**, sometimes differing only by a 90° rotation. This was confirmed visually on matched pairs, not inferred from hash distance alone. Neither source documents provenance, so we claim nothing about which derives from which; the relevant fact is that any study treating them as independent sources for cross-dataset testing would be leaking training data into "external" evaluation.

### D. The modeling pool

Given Sections III-B and III-C, **Splits A and B are built from the Kaggle pool alone**. Holding the data fixed makes the split protocol the single manipulated variable, rather than confounding "we corrected the split" with "we also changed the data"; adding Roboflow would also have pushed the group-level class ratio from 44:56 to roughly 8:92 while contributing essentially no counterfeit signal. After exclusion and de-duplication the pool contains **510 images in 480 product-identity groups**, 272 authentic and 238 counterfeit.

### E. External evaluation set (Split C)

The protocol called for a genuinely external source. A search for an independent *two-class* source found none: every candidate was either likely to share photographs with sources already in the pool (Section III-C) or carried no counterfeit label. We therefore use the Mendeley source [20] as an **authentic-only** external check: 150 photographs, one per distinct product, from a different country, photographers, camera hardware and backdrop protocol. Independence was verified rather than assumed (Section IV-B): **0 of 150 images matched anything in the pool**, nearest match at Hamming distance 10/64 against a threshold of 8, median 18.

An authentic-only set measures the false-positive rate on genuine packaging and says nothing about counterfeit recall. Section S-I-D describes the synthetic proxy built to probe that direction, and Section IX states the limitation that remains.

## IV. Data Preprocessing

The full pipeline is deterministic (fixed seed 42 throughout) and idempotent; re-running reproduces byte-identical outputs. Fig. S1 summarizes it.

### A. Filtering

Exclusions are rule-based and individually documented in code, in three families: contradictory annotations (52 Roboflow rows), advisory-bulletin graphics (180 Roboflow files, Section III-B), and the 56 human-identified Kaggle files of Section III-E. Every exclusion is recorded with a machine-readable reason in the provenance table, so that any downstream count can be traced to the rule that produced it.

### B. De-duplication and product identity

Neither source carries ground-truth product-identity labels, so near-duplicate photo clustering is used as an operational proxy. A 64-bit perceptual hash [25] is computed at all four cardinal orientations per image and the numeric minimum taken as a rotation-canonical hash:

$$h(x) = \min_{\theta \in \{0°, 90°, 180°, 270°\}} \mathrm{pHash}\big(R_\theta(x)\big) \tag{1}$$

Rotation invariance is necessary rather than decorative: the Roboflow source documents 90°-rotation augmentation, and a plain pHash treats a rotated copy of a photograph as a different image. Pairs at Hamming distance 0 on the canonical hash are treated as true duplicates and one copy is removed; pairs at distance 1–8 are retained but assigned to the same `product_identity` cluster. Zero clusters mix authentic and counterfeit labels, so the clustering never contradicts the original annotations.

The method is not robust to mirroring; mirrored duplicates would be missed. Because the augmentation policy of Section V-C deliberately excludes flips (mirrored printed text is unnatural), this gap is low-risk but not exhaustively verified.

### C. Split construction

Three partitions of the modeling pool are built (Table 3):

- **Split A (naive)** — random 70:15:15, class-stratified, at the **image** level. This is the protocol in general use on data of this kind, and the only one available to a study that adopts a dataset's shipped partition without inspecting it, as Section III-A shows this dataset's shipped partition invites; none of the studies in Table 1 reports a grouped or identity-aware split.
- **Split B (corrected)** — 70:15:15, class-stratified, at the **product-identity group** level, so no near-duplicate photograph of the same product can appear in more than one partition. The training partition additionally carries a `cv_fold` index from `StratifiedGroupKFold`, so 5-fold cross-validation never places the same product in two folds.
- **Split C (external)** — the 150 Mendeley photographs, used only for evaluation.

An assertion in the pipeline verifies zero product-identity overlap between every pair of Split B partitions on every run; it passes. Comparing the two assignments directly, **9 of 480 product-identity groups (1.9%) have members in more than one partition under Split A** — this is the literal, countable leakage that Split B removes — and 230 of 510 images (45.1%) are assigned to a different partition under A than under B.

**TABLE 3.**Partition sizes and class balance. Split B partition sizes differ slightly from Split A's because grouping constrains which images can move together.

| | Split A train | Split A val | Split A test | Split B train | Split B val | Split B test | Split C |
|---|---|---|---|---|---|---|---|
| Images | 357 | 77 | 76 | 357 | 79 | 74 | 150 |
| Product groups | — | — | — | 336 | 72 | 72 | 150 |
| Authentic | 190 | 41 | 41 | 188 | 45 | 39 | 150 |
| Counterfeit | 167 | 36 | 35 | 169 | 34 | 35 | 0 |

The test partitions are small (74–76 images). Every point estimate in Section VI is therefore reported with a 95% bootstrap confidence interval, and comparisons are read against those intervals rather than against point differences.

### D. Capture-method normalization

The three-stage normalization that Sections V-D and VIII evaluate is applied *inside* the dataset class, before augmentation and before the network's input transform, identically for training, validation, in-distribution test and external partitions. It uses no label information at any point and could be shipped unchanged as an inference-time preprocessing step. Section V-D gives its definition.

---

## V. Methodology

### A. Task and label convention

The task is binary image classification. Throughout, authentic = 0 and **counterfeit is the positive class**, so precision, recall, F1 score, area under the receiver operating characteristic curve (ROC-AUC) and area under the precision–recall curve (PR-AUC) are all reported with respect to counterfeit detection. This matches the deployment framing, in which the costly error is calling a falsified product genuine.

### B. Models

Four model families are evaluated (Fig. S2), deliberately spread across capacity scales so that "does capacity explain the reported accuracy?" is answerable.

**M1 — Color histogram + logistic regression (97 learned parameters).** Each image is resized to 224×224 and a 32-bin-per-channel red-green-blue (RGB) intensity histogram computed, giving a 96-dimensional feature vector:

$$\phi(x) = \big[\,\mathbf{h}_R(x) \,\|\, \mathbf{h}_G(x) \,\|\, \mathbf{h}_B(x)\,\big] \in \mathbb{R}^{96}, \qquad \mathbf{h}_{c,b}(x) = \frac{1}{HW}\sum_{i,j} \mathbb{1}\!\left[ x_{ij}^{(c)} \in B_b \right] \tag{2}$$

with the 32 bins $B_b$ uniformly partitioning [0, 256). A logistic regression is fitted on $\phi(x)$:

$$P(y = 1 \mid x) = \sigma\big(\mathbf{w}^\top \phi(x) + b\big), \qquad \sigma(z) = \frac{1}{1 + e^{-z}} \tag{3}$$

with `class_weight="balanced"` and L2 regularization at scikit-learn's default strength. This model answers one question: how much of the reported accuracy is available to a classifier that cannot see spatial structure at all?

**M2 — Small CNN with a global-average-pooling (GAP) head (23,938 trainable parameters).** Three convolutional blocks with a conventional channel progression (16 → 32 → 64; each block Conv3×3 → BatchNorm → ReLU → MaxPool2×2), with a GAP head rather than the flatten-then-dense head small-dataset CNN work commonly uses:

$$g_k = \frac{1}{H'W'}\sum_{i=1}^{H'}\sum_{j=1}^{W'} a_{ijk}, \qquad \hat{y} = \mathrm{softmax}\big(W_{\!f}\,\mathrm{drop}_{0.5}(\mathbf{g}) + \mathbf{b}_{\!f}\big) \tag{4}$$

The head is the point of this model. On a 224 × 224 input the trunk emits a 28 × 28 × 64 feature map, so flattening it into a 128-unit dense layer would cost roughly 6.4 M parameters — about 99.7% of such a network — on 357 training images. GAP replaces that with 130 parameters while preserving the trunk exactly, so M2 measures what a from-scratch CNN achieves when its capacity is not dominated by a head the data cannot support.

**M3 — MobileNetV3-Small, frozen (1,154 trainable / 927,008 frozen).** The ImageNet-pretrained feature extractor [13] is frozen; a `Dropout(0.3) → Linear(576, 2)` head is trained on its globally pooled 576-dimensional output.

**M4 — EfficientNet-B0, frozen (2,562 trainable / 4,007,548 frozen).** As M3, with the EfficientNet-B0 extractor [14] and a `Dropout(0.3) → Linear(1280, 2)` head.

Both transfer models are therefore **linear probes on a fixed representation**, which is the instrument this study's question calls for rather than a concession to it. The question is what a change in the *input distribution* does, since the normalization of Section V-D removes acquisition signal and nothing else; a probe holds the representation constant while the input changes, so any movement in accuracy is attributable to the input, whereas a fine-tuned network confounds the two by re-adapting its features to whatever the new input affords. Freezing also keeps M3 and M4 balanced — both train exactly one linear layer — and the compute budget within central-processing-unit (CPU) only hardware. What a probe cannot say is what fine-tuning would do, in either direction; Section X states both outcomes it leaves open.

### C. Augmentation

Training-partition augmentation for M2–M4 is: rotation ±12°, brightness and contrast jitter (±0.25), mild `RandomResizedCrop` (scale 0.85–1.0), and slight Gaussian blur (kernel 3, σ ∈ [0.1, 0.8]). **No horizontal or vertical flip** is used, because mirroring produces printed packaging text that cannot occur in deployment.

M1 is excluded from augmentation by design: rotation and cropping are near-invariances of a color histogram and would contribute nothing, while brightness and contrast jitter would perturb the only feature this model observes, acting as label noise rather than as the spatial-filter regularizer they are for a CNN. We note the asymmetry rather than hide it; Section VII-A shows it does not soften the paper's conclusion about M1.

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

and is applied identically to every partition. Three properties matter. $T$ is **label-free** — nothing in (5)–(7) references $y$ — so applying it to the external set is not an oracle. It is **deployable**: a fixed preprocessing function, not a train-time-only trick. And it is **destructive** by design, removing information a model might legitimately use, which is why its effect must be measured per architecture rather than assumed (Section VII-A). The composition order in (8) is itself a free choice, and because two of the three operators destroy information they do not commute; Section VII-B measures all six orderings.

M1 reads images directly and never passes through this operator, an exclusion that is empirical: normalization collapses M1's in-distribution accuracy toward chance while recovering nothing externally (Section VII-A).

### E. Interpretability and attribution

**Grad-CAM.** For target class $c$, with $A^k$ the activation maps of the last convolutional stage,

$$\alpha^c_k = \frac{1}{HW}\sum_{i,j} \frac{\partial y^c}{\partial A^k_{ij}}, \qquad L^c_{\mathrm{Grad\text{-}CAM}} = \mathrm{ReLU}\!\left(\sum_k \alpha^c_k A^k\right) \tag{9}$$

following [15]. Maps are computed on M4 for the in-distribution audit and directly on the external images for both M3 and M4.

**Exact Shapley values for M1.** For a linear model with an independent-feature background, the Shapley value of feature $i$ for instance $x$ has the closed form [16]

$$\varphi_i(x) = w_i\big(\phi_i(x) - \mathbb{E}[\phi_i]\big) \tag{10}$$

so no sampling approximation is needed. We take $\mathbb{E}[\phi_i]$ over the Split B training partition and report $\overline{|\varphi_i|}$ over its test partition as global importance — an exact decomposition of M1's decision function, not an estimate of it.

## VI. Results

All results in this section come from the deterministic, three-way-normalized production pipeline, except where a table explicitly reports a baseline condition for contrast. Complete machine-readable tables are in `paper/tables/`.

### A. The capture-method confound

Every one of the 510 pool filenames falls into exactly one of two patterns, and **the pattern predicts the class label with no exceptions** (Table 4): 272/272 authentic files are `images*.jpg`, 238/238 counterfeit files are `Screenshot*.png`. We recomputed this cross-tabulation independently for this paper from per-image statistics; it is exact, not approximate.

The separation is not an artifact of our filtering: it holds identically in the archive as distributed, where all 240 files in `Fake/` are `Screenshot*.png` and all 421 in `Real/` are `images*.jpg`. Any study using this dataset, filtered or not, inherits it in full — and a classifier reading nothing but the file extension achieves **100% accuracy** on it.

**TABLE 4.**The two acquisition pipelines in the Kaggle pool, and the external set's position relative to both. Brightness is the mean RGB value at 64 × 64, on a 0–1 scale.

| Group | n | Capture pattern | Mean brightness | Median short side (px) | Mean file size |
|---|---|---|---|---|---|
| Kaggle authentic | 272 | `images*.jpg` (100%) | 0.767 | 223 | 6.0 kB |
| Kaggle counterfeit | 238 | `Screenshot*.png` (100%) | 0.555 | 405 | 339 kB |
| Split C external (authentic) | 150 | device photograph | **0.162** | **2448** | 1,656 kB |
| Split C synthetic (proxy counterfeit) | 150 | perturbed copy of the above | 0.153 | 2448 | 1,018 kB |

Throughout this paper kB = 1000 bytes.

A two-sample *t*-test on brightness between the two classes gives *t* = 17.0, *p* ≈ 0 — one of the strongest and most trivially learnable signals anywhere in the training data. Fig. 1 makes the second, equally important point: the external set does not sit *between* the two training classes on these axes but far outside both, roughly 10× higher in linear resolution and darker than even the counterfeit class. A model that has learned "bright, small, heavily compressed → authentic", even partially, has every statistical reason to call every external photograph counterfeit.

> **FIGURE 1.** `paper/figures/fig03_capture_confound.pdf` — Distributions of the three confounded statistics. (a) Brightness: violin plots with group means labeled. (b) Short-side resolution, log scale, with medians. (c) File size, log scale, with means. The external set lies outside the range of both training classes on all three axes.

The confound is visible in the decision function of the simplest model. Fig. 2(a) plots M1's 96 coefficients: 93 lie within ±0.35 of zero, while the top intensity bin (248–255) of each channel carries a large negative weight (β = −2.86, −2.84, −2.95) — "many near-white pixels → authentic". The exact Shapley decomposition of Eq. (10) confirms this is not a large coefficient on a rarely varying feature: those three have mean |φ| of 0.079–0.082 on the Split B test partition against ≤ 0.002 for the remaining 93 (Fig. 2(b)). M1's 83.8% accuracy is, to a good approximation, a measurement of how much white a photograph contains.

> **FIGURE 2.** `paper/figures/fig12_model1_attribution.pdf` — (a) M1's logistic-regression coefficients across the 32 intensity bins of each RGB channel; the near-white bin dominates all three channels. (b) The eight features with the largest mean |Shapley value| on the Split B test partition. Attribution is exact for this model, not sampled.

**A metadata-only oracle bounds the confound directly.** M1 is a useful diagnostic but an imperfect bound, because a 96-bin color histogram does read pixel intensities and could in principle carry some packaging information. We therefore fitted the same logistic regression to the three acquisition statistics of Table 4 and nothing else — mean brightness, log short-side resolution, log encoded file size — with no pixels, no spatial structure and no color information at all. Three scalars per image, 4 learned parameters, trained on each split's own training partition (Table 5).

**TABLE 5.**Metadata-only oracle; LR = logistic regression. Features are per-image acquisition statistics, not image content; resolution and file size enter as log₁₀. The deterministic rule uses only the filename extension and is not fitted. Intervals are 95% Wilson.

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

### B. The same audit on a second, independently published dataset

One dataset cannot establish a general claim, so we ran the identical procedure against the other public authentic/counterfeit pharmaceutical image dataset we were able to obtain — the Roboflow source of Section III-B, a different publisher, a different country of origin and a different class-construction method. Both are audited **as shipped**, before any filtering of ours, under grouped 5-fold cross-validation on rotation-canonical pHash clusters so that a publisher's own augmented copies cannot straddle a fold. Balanced accuracy is reported because both are heavily imbalanced as distributed; 0.5 means metadata carries nothing about the label (Table 6).

**TABLE 6.**The provenance-confound audit on two independently published datasets, as shipped. Grouped 5-fold cross-validated balanced accuracy of a logistic regression on the named metadata alone — no pixel content. Chance is 0.500.

| Metadata used | Kaggle (661 imgs, 584 groups) | Roboflow v4 (4,207 imgs, 597 groups) |
|---|---|---|
| File format | **1.000** | 0.500 (single-format archive) |
| Encoded file size | 0.994 | 0.717 |
| Short-side resolution | 0.954 | 0.500 (all 640 × 640) |
| Aspect ratio | 0.803 | 0.500 |
| All of the above | **1.000** | 0.717 |

The two columns fail differently, and the contrast is the most transferable result in this paper.

On the Kaggle dataset the audit is decisive on every axis, including one we had not anticipated: **aspect ratio alone reaches 0.803**, because screen captures inherit display proportions that photographs do not. Such a confound is not a single leak to be plugged; it is present redundantly in every statistic acquisition touches, which is why Section VII finds three normalization axes each contributing separately.

On the Roboflow dataset the audit largely **fails to fire** — and that dataset is nonetheless confounded in the most extreme way documented here: 57/57 of its counterfeit-labeled source images are advisory-bulletin graphics carrying the ground-truth word rendered in the pixels, against 263/263 clean product photographs labeled authentic (Section III-B). Metadata registers only a partial trace (0.717 from file size, which sees that bulletin collages compress differently) and nothing from format, resolution or aspect ratio.

The reason is a trap rather than a limitation of one dataset. **The publisher normalized the archive**, resizing every image to 640 × 640 and re-encoding to a single format before release, which destroyed the acquisition *tells* without touching the acquisition *confound*. A dataset tidied for distribution therefore looks cleaner under this audit than a raw one while being no less confounded, and its silence is uninformative rather than reassuring. We therefore present the audit as a **necessary but not sufficient** screen, paired with the two checks that did catch this: a content pass over a sample of each class (Section III-E) and cross-source near-duplicate hashing (Section IV-B).


### C. The audit across application areas

Section VI-B establishes that the audit is not tuned to one archive, but says nothing about the wider claim. This subsection takes the first step of the survey that would test it, and it costs nothing to run: Kaggle's public file-listing endpoint returns, without authentication, the path and encoded size of every file in a dataset. The path carries the class in the folder-per-class layout these archives use and the extension carries the format, so two of the four audit features can be fitted **as the publisher shipped it, without downloading a single image** (Table 7).

**TABLE 7.**The provenance audit run from public file listings alone, no images downloaded. Balanced accuracy under stratified 5-fold cross-validation; chance is 0.500. Format is the one-hot file extension, size is log encoded bytes. Ext-rule is the accuracy of the single deterministic rule "extension predicts class". Listings are paginated and the endpoint stops at 2,400 files, so large archives are sampled in listing order.

| Dataset | Area | n | Format | Size | Both | Ext-rule |
|---|---|---|---|---|---|---|
| Kaggle *Fake vs Real Medicine* [19] | Medicines (positive control) | 2224 | **1.000** | 0.999 | **1.000** | **1.000** |
| `rhythmghai/ai-vs-real-images-dataset` | Generated images | 995 | **1.000** | 0.812 | **1.000** | **1.000** |
| `cashbowman/ai-generated-images-vs-real-images` | Generated images | 974 | 0.577 | 0.553 | 0.562 | 0.554 |
| `ishanikathuria/handwritten-signature-datasets` | Signatures (negative control) | 2400 | 0.500 | **0.843** | 0.845 | 0.560 |
| `kshitizbhargava/deepfake-face-images` | Deepfake faces | — | \* | \* | \* | \* |
| `shahzaibshazoo/detect-ai-generated-faces...` | Generated faces | — | \* | \* | \* | \* |
| `prosperchuks/fakereal-logo-detection-dataset` | Brand logos | — | \* | \* | \* | \* |

\* Not auditable from a listing, and no sample size (—) is reported: the sample reached only one class before the endpoint's file limit, so there is nothing to compare within the dataset and no score of any kind is defined. This is a property of the sampling method, not a finding about the dataset; it is not a low score, and it must not be read as one.

Four things follow, and the last two are the useful ones.

**The positive control passes, by an independent route.** The case-study dataset returns 1.000 on format and 1.000 on the deterministic extension rule from its *public listing metadata alone* — no pixels, no download, no local pipeline. Section VI-A reached the same conclusion from the archive on disk. That the two agree is a check on this paper's central empirical claim using entirely different inputs.

**The confound appears in another application area, at full strength.** One of the two generated-image datasets is perfectly separable by file format, exactly as the medicine dataset is, and exactly as [30] reports for the GenImage benchmark. This is a third independent instance of the mechanism and the first this paper measured itself.

**But it does not appear everywhere, which is what makes the audit worth running.** The second generated-image dataset, in the same application area, returns 0.577 on format and 0.562 overall — near chance on these axes. A screen that fired on every dataset would carry no information; this one does not. It is also a caution against reading the mechanism as a law: two archives built for the same task by different people differ completely in whether they exhibit it.

**The negative control reveals a false-positive mode, and it changes how the audit's output should be read.** Genuine and forged signatures in the BHSig260 corpus are written on the same paper and digitized by one procedure, so there is no acquisition asymmetry to find, and format duly returns exactly 0.500. Encoded size returns **0.843**. The likely explanation is not provenance but content: forged signatures differ in stroke complexity and ink coverage, and ink coverage drives the compressed size of a bitonal scan. The audit therefore answers a narrower question than "is this dataset confounded" — it answers "can a trivial statistic separate your classes", and the researcher must then establish whether that statistic is an acquisition artifact or a property of the objects. A high score is a reason to investigate, not a verdict, and format is the more specific axis because storage format is never a property of the photographed object (Section VIII-G, Type E).

---

### D. In-distribution performance, and why leakage is the smaller problem

One definition governs what follows. "Leakage-free", here and throughout, means free of **product-identity** leakage: Split B guarantees that no perceptual-hash cluster of near-duplicate photographs straddles a partition or a fold. It makes no claim about acquisition. Because every counterfeit-labeled image in the pool was produced by one capture pipeline and every authentic-labeled image by another, *no* partition of this pool can place a capture process on one side of a fold, and grouped cross-validation inherits the confound at full strength in every fold. Split B corrects one of the two problems, not both.

In-distribution, the four models reach 0.842, 0.868, 0.934 and 0.987 on the naive split and 0.838, 0.865, 0.932 and 0.919 on the leakage-free one — deltas of +0.004, +0.004, +0.002 and +0.068, three of them within half a point of zero. No pairwise McNemar's test is significant, and Holm–Bonferroni over the six raises the smallest adjusted *p* from 0.118 to 0.711, so the correction is robust to multiplicity and, if anything, understated without it. The full metric set, the tests and their power analysis are Table S3–S5 and Section S-I-H.

The measured deltas can be bounded rather than merely observed. Exactly 7 of the 76 Split A test images belong to a product group that also appears in Split A's training partition, so image-level leakage cannot inflate Split A test accuracy by more than 7/76 = **9.2 points** for any model, seed or architecture. The observed deltas fall below that ceiling, and the ceiling is itself small. This is the paper's first substantive result: on this pool the methodological check the field has institutionalized moves accuracy by at most 6.8 points, while the confound described next accounts for the difference between 97% in-distribution accuracy and 3% external accuracy.

### E. External generalization: the result that matters

Table 8 and Fig. 3 give the central result of this paper.

**TABLE 8.**External generalization on 150 independently captured authentic photographs. "Baseline" is the production run immediately before three-way normalization became the default; "normalized" is the current pipeline. In-distribution reference is authentic-class accuracy on each model's own Split B test partition (n = 39 authentic). Δ follows Eq. (S5) of the supplement. M1 does not pass through the normalization operator in the production pipeline; that exclusion was decided empirically after the fact, not a priori, and Section S-I-P reports what happens when the operator is applied to it anyway (Table S13). Bracketed intervals are 95% Wilson score intervals on the underlying counts, given as k/n; they quantify sampling uncertainty on a fixed trained model and not training-run variance, which would require repeated seeds.

| Model | In-distribution authentic accuracy (k = 39) | Split C, baseline (n = 150) | Split C, 3-way normalized (n = 150) | Δ (normalized) |
|---|---|---|---|---|
| M1 hist+LR | 27/39 = 0.692 [0.536, 0.814] | 0/150 = 0.000 [0.000, 0.025] | 0/150 = 0.000 [0.000, 0.025] | +0.692 |
| M2 CNN | 33/39 = 0.846 [0.703, 0.928] | 0/150 = 0.000 [0.000, 0.025] | 129/150 = **0.860** [0.795, 0.907] | **−0.014** |
| M3 MobileNetV3 | 38/39 = 0.974 [0.868, 0.995] | 104/150 = 0.693 [0.615, 0.762] | 116/150 = 0.773 [0.700, 0.833] | +0.201 |
| M4 EfficientNet-B0 | 38/39 = 0.974 [0.868, 0.995] | 5/150 = 0.033 [0.014, 0.076] | 121/150 = 0.807 [0.736, 0.862] | +0.167 |

Read the baseline column first. Two of the four models classified **zero of 150** external authentic photographs correctly, and the model with the best in-distribution accuracy in the entire study (M4, 0.987 on Split A) classified **3.3%** correctly. These are not degradations; they are near-complete inversions on the easiest possible external case, a test set containing only the class the models were most accurate on in-distribution. A model at 94.6% on Split B that recovers 3.3% of plainly authentic external photographs has not learned to recognize authentic packaging. It has learned to recognize this dataset's photography.

Now read the normalized column. The same models, retrained on the same images with the same seeds and hyperparameters, differing only by the label-free operator of Eq. (8), recover 86.0%, 77.3% and 80.7%. The in-distribution price is negligible: over the same transition, Split B test accuracy moves 0.865 → 0.865 (M2), 0.946 → 0.932 (M3) and 0.919 → 0.919 (M4), i.e. between −1.4 and 0.0 points. Two of the three models are unchanged to three decimal places and the third loses 1.4 points, well inside its bootstrap interval. The correction is close to free in-distribution while being worth 77 to 86 points externally. M2's external accuracy exceeds its own in-distribution accuracy, giving the only negative generalization gap anywhere in this study — which is intelligible rather than paradoxical: with the shortcut suppressed, its in-distribution test partition (mixed classes, small, adversarially hard for a 23,938-parameter model) is simply a harder problem than "is this well-lit photograph of an intact carton authentic?". M1, which never passes through the operator, is unchanged at 0.000 — and Section S-I-P shows that applying the operator to it does not help either.

The intervals separate the models' claims sharply, and one of them should be read down. M2's and M4's gains are far outside sampling uncertainty — 0/150 to 129/150 and 5/150 to 122/150, with non-overlapping intervals in both cases — so those two results are secure against the objection that Split C is only 150 images. M3's are not: 104/150 [0.615, 0.762] to 116/150 [0.700, 0.833] is a 12-image difference whose intervals overlap substantially, and it is consistent with no effect. Combined with Section S-I-O's finding that M3's answer to this question changed sign twice across runs, **we do not claim a normalization benefit for M3**; the honest statement is that it is the one model where the effect is neither established nor excluded. The paper's headline claim rests on M2 and M4.

> **FIGURE 3.** `paper/figures/fig08_external_generalisation.pdf` — In-distribution authentic accuracy against external accuracy before and after three-way normalization, per model. M1 bypasses the normalized pipeline by design, so its two Split C bars are the same 0.0% measurement shown twice.

### F. A second external distribution, and what it costs the headline

Section VIII-C warns that a shortcut coinciding with one external distribution is indistinguishable from robustness until a second, differently constructed evaluation disagrees. We made that warning testable. Split D is the same source's "iphone 11 pro" subset — 149 unique images (the archive ships one duplicate filename), the **same 150 products** as Split C, photographed on different hardware under the source's deliberately different lighting protocol. Measured: mean brightness 0.389 against Split C's 0.162 and the training pool's 0.668, so it is a different point on the confounded axis rather than a repeat; median short side 2419 px; and rotation-canonical pHash puts only 1 of 149 within the near-duplicate threshold of any Split C image (median distance 18), so despite depicting the same products the two sets are not pixel-interchangeable.

Because content is held fixed and only acquisition varies, this is a **paired capture-shift test**. It is not an independent product sample and says nothing about generalization across products; it isolates exactly the axis this paper is about. Both sets are authentic-only, so both measure the false-positive rate. All four models were evaluated from their persisted Split B checkpoints (Section S-I-G), so the model tested here is provably the one that produced the in-distribution numbers; Table 9 gives the result.

**TABLE 9.**The same corrected models on two external distributions. Both authentic-only; accuracy is the fraction correctly called authentic, with 95% Wilson intervals. Split C and Split D photograph the same products under different capture conditions.

| Model | Split C (n = 150) | Split D (n = 149) | Change |
|---|---|---|---|
| M1 hist+LR | 0/150 = 0.000 [0.000, 0.025] | 0/149 = 0.000 [0.000, 0.025] | 0.0 |
| M2 CNN | 129/150 = **0.860** [0.795, 0.907] | 69/149 = **0.463** [0.385, 0.543] | **−39.7** |
| M3 MobileNetV3 | 116/150 = 0.773 [0.700, 0.833] | 108/149 = 0.725 [0.648, 0.790] | −4.9 |
| M4 EfficientNet-B0 | 121/150 = 0.807 [0.736, 0.862] | 124/149 = 0.832 [0.764, 0.884] | +2.6 |

Two of the three findings are uncomfortable for the rest of this paper; we state them before the reassuring one.

**The correction does not transfer uniformly across capture shifts, and the model it fails for is the one we had called the best generalizer.** M2 loses 39.7 points between the two external sets — from 0.860, the highest external accuracy in the study, to 0.463, barely above the rate obtained by calling everything counterfeit. Its two intervals do not come close to overlapping. Whatever M2 learned that let it succeed on Split C after correction did not survive a change of camera, even with the same products, the same normalization and the same authentic label.

**The paper's own caution about M3 applies to M2.** Section VIII-C argues that M3's strong *uncorrected* external accuracy was a backdrop-matching rule that happened to fit Split C. The same argument now applies, on this evidence, to M2's strong *corrected* external accuracy: a single external distribution could not distinguish a general repair from one that fits Split C in particular, and the second distribution says it was substantially the latter. We had the right diagnostic and did not apply it to our own headline until now.

**The two pretrained backbones hold their accuracy across the shift.** M3 moves −4.9 points and M4 +2.6, both with comfortably overlapping intervals, so neither change is distinguishable from sampling noise at these sample sizes. Across both external distributions M4 is the most stable model (0.807 and 0.832) and M3 the next (0.773 and 0.725).

We do not describe this as the backbones generalizing. The attention audit of Section VI-G finds that on external images both take their evidence for "authentic" from the background rather than the product, without exception in 40 maps — and Split C and Split D share the same dark backdrop, differing in device and lighting but not in staging. A model applying a backdrop rule would hold its accuracy across exactly this shift. **Split D tests the capture-pipeline confound and leaves the backdrop cue untouched**, so the right reading of these two rows is that the backbones' accuracy survives a change of camera, not that it rests on packaging content.

The net effect is a real narrowing. The correction of Section V-D repairs external generalization **for frozen pretrained backbones across two capture shifts** and fails to do so for a small from-scratch CNN on the second, so "normalization recovers 77–86% externally" holds of one distribution and not as a general statement. Two capture conditions from one archive is still a narrow basis, and nothing here tests generalization across products, sources or countries (Section S-II).


### G. What the surviving accuracy attends to

Accuracy that survives a capture shift still has to be shown to rest on the intended cue, and here it does not. All 62 Grad-CAM maps this study produced were regenerated from the persisted checkpoints and categorized in full; the procedure, the four-way scheme and the maps themselves are Section S-I-J and Fig. S10.

On the external sets the result is without exception across 40 maps, and identical for both frozen backbones: **maps for correct "authentic" predictions attend to the background, and maps for incorrect "counterfeit" predictions attend to the product** — 10 of 10 each way, twice over. Because each map targets the predicted class, this says that on external images both models take their evidence for "authentic" from the photographic surround and their evidence for "counterfeit" from the packaging. Their correct external answers are therefore not packaging recognition.

Two consequences follow, and both narrow the paper's claims. Split C and Split D are the same products on the same dark backdrop, differing in device and lighting only, so neither disturbs the cue the audit identifies: M3 and M4 holding up across that shift (Section VI-F) is consistent with the backdrop cue persisting, not with genuine robustness. And we make no claim about *what the normalized models see* in aggregate: a border-mass audit over all 150 external images finds attention essentially uniform after normalization (0.655 against a uniform reference of 0.642) where it had been sharply product-centered before (0.182), but a 128 px bottleneck degrades activation-based attribution as much as it degrades the input, so the diffuse maps are a limitation of the method rather than evidence of distributed reasoning. The differential result above survives that objection where the aggregate does not: degraded attribution adds noise, and noise does not manufacture a perfect outcome-aligned split.

One conclusion survives under either reading, and it cautions against a common practice. **A visually convincing, product-centered Grad-CAM map is not evidence that a model learned the intended task.** That claim rests on the un-normalized model, whose input is unaltered and whose attribution is not in question: it is strongly product-centered, and it classifies 6% of external images correctly.

## VII. Ablation Study

Section VI-E established that the composed operator of Eq. (8) works. This section decomposes it: which axes matter, whether they are complementary, whether the effect is architecture-dependent, what happens to a model that has nothing but the shortcut, and whether the result depends on the two things the operator's definition leaves free — the magnitudes of its three constants and the order of composition.

A caveat applies throughout. These ablations are **single-run** standalone experiments; each compares conditions executed within one script invocation, so the within-run comparison is valid even where absolute numbers differ from the production pipeline's. Cross-run absolute comparisons should not be made: the same nominal condition read 62.7%, 45.3% and 50.7% across three runs before the seeding bug of Section S-I-G was found. Directional conclusions held in every run; specific decimals did not.

### A. Which axes matter, and how much

The correction is decomposed in full in Sections S-I-J to S-I-N; this subsection states what those ablations establish, because the ordering result below is only interpretable against them.

**The three axes are complementary, not redundant.** Individually they take M4's external accuracy from 5–9% to 22.0% (resolution), 27.3% (brightness) and 12.7% (compression); resolution and brightness together give 62.7%, and adding compression takes 50.7% to 78.0% in the same run (Table S11). Each recovers something the others do not, which is what one expects if the confound is a *capture pipeline* expressed through several correlated statistics rather than a single one. Every group in that table predates the augmentation-seeding fix of Section S-I-G, so its absolute values carry that caveat; the conclusion is reproduced post-fix, by a script written for another purpose, in Table S12's two-way and production three-way conditions (0.500 against 0.820).

**A fourth plausible axis is not part of the mechanism.** Gray-world white balance was motivated by a real, measurable difference — the pool has a warm cast, R:G:B ≈ 1 : 0.94 : 0.86, against the external set's 1 : 0.93 : 0.93 — and it recovers nothing: 0.067 alone, and −4.0 points added to the production operator (Table S12). The original test of that axis was itself unsound, and redoing it properly is a small methodological lesson in its own right (Section S-I-M).

**The effect is architecture-dependent, and one model gains nothing.** The correction helps the small CNN and both frozen backbones and does nothing for the color-histogram baseline, whose in-distribution accuracy instead collapses from 0.838 to 0.541 — barely above its majority-class rate. Removing the confound does not unlock latent signal there because there was none: that model's entire decision function was the shortcut (Table S13).

**The constants are conservative rather than tuned.** Sweeping all three around their production values moves external accuracy across 0.480–0.873 while in-distribution accuracy stays within 0.905–0.946, with no knife edge; a 96 px short side would in fact beat the 128 px we report (Table S14). We have not re-tuned around it, because choosing preprocessing by its external score is precisely the target-distribution leakage Section IX warns about. The same sweep answers a natural objection to the diffuse attention maps above: if the bottleneck had already destroyed the detail authentication needs, tightening it should hurt, and instead it helps.

### B. Does the order of composition matter?

Eq. (8) composes the three operators in one fixed order — resolution, then brightness, then compression — and Section S-I-R varied their magnitudes while holding that order constant. The order is a free parameter of the same method, it was never justified, and two of the three operators impose an information bottleneck rather than an alignment, so there is no reason to expect them to commute. Concretely: a JPEG re-encode applied to an image already capped at 128 px quantizes 8×8 blocks covering a large fraction of the frame, whereas the same re-encode applied at a 2400 px native size produces artifacts that the subsequent downsample averages away. We therefore ran all 3! = 6 orderings at the production constants, on M4, inside a single execution (Table 10).

**TABLE 10.**Composition order of the three normalization operators. M4 (EfficientNet-B0), production constants (128, 0.5, 40), all six orderings from one script execution, so all rows are directly comparable. R = resolution bottleneck (Eq. 5), B = brightness rescale (Eq. 6), C = compression bottleneck (Eq. 7). The production order of Eq. (8) is R, B, C.

| Order | Compression applied | Split B test accuracy | Split C accuracy |
|---|---|---|---|
| R, B, C (production) | after the cap | 0.919 | 0.820 |
| R, C, B | after the cap | 0.932 | **0.880** |
| B, R, C | after the cap | 0.919 | 0.847 |
| B, C, R | before the cap | **0.946** | **0.380** |
| C, R, B | before the cap | 0.932 | 0.540 |
| C, B, R | before the cap | 0.932 | 0.467 |

Order matters more than any of the three constants does, and it separates the six conditions perfectly along the axis the mechanism predicts.

**Compression must follow the resolution cap, and that one rule accounts for the entire spread.** The three orderings applying the JPEG bottleneck *after* the short side has been capped score 0.820, 0.847 and 0.880 externally; the three applying it before score 0.380, 0.467 and 0.540. The groups do not overlap and are separated by 28 points. The reading is mechanical rather than statistical: compressing at native resolution and then downsampling largely undoes the compression, because the resampling filter averages over precisely the quantization artifacts the bottleneck exists to impose. Those three conditions are in effect two-way normalizations that pay for a third operator without obtaining it, and 0.380–0.540 brackets the 0.500 that the genuine two-way condition reaches in Table S12.

**Brightness placement is a second-order effect.** Within the three sound orderings, moving the brightness rescale changes external accuracy by 6 points (0.820 → 0.880), against the 28-point gap between the groups. This is the distinction of Section S-I-R in another guise: the two bottleneck operators are load-bearing and position-sensitive, the location-shifting operator is neither.

**The in-distribution ranking is not merely uninformative here; it is inverted.** The ordering with the highest Split B accuracy of all six — B, C, R at 0.946 — is the ordering with the lowest external accuracy of all six, 0.380. A practitioner selecting the composition order the ordinary way, by held-out accuracy on their own data, would have chosen the worst of the six available options, and would have watched a 2.7-point in-distribution spread (0.919–0.946) conceal a 50-point external one (0.380–0.880). This is the sharpest demonstration in the study of what a confounded in-distribution partition is worth, precisely because nothing else varies: the same three operators, the same constants, the same model, the same data, reordered.

**The reported order is again conservative rather than tuned.** R, C, B beats production on both axes (0.880 vs. 0.820 externally, 0.932 vs. 0.919 in-distribution). As in Section S-I-R we have not re-run the paper around the better value, for the same reason: selecting a preprocessing choice by its external score is the target-distribution leakage Section S-II warns about, and the production order was fixed before any of these six numbers existed. The headline figures continue to understate the method.

The practical consequence generalizes past this pipeline. Composition order is normally left implicit in a preprocessing description; on this evidence it deserves the treatment of a hyperparameter — it must be reported, and it cannot be chosen in-distribution. Any pipeline composing two or more information-destroying operators should expect the same sensitivity, since the argument is about resampling and quantization rather than anything specific to this dataset.


## VIII. Discussion

### A. What the reported accuracies on this dataset actually measure

Four results constrain interpretation, in decreasing order of force. A classifier reading three acquisition scalars and no pixels reaches 100% on the leakage-free partition, and the filename extension alone is correct on all 510 images. A 97-parameter linear model on color histograms reaches 83.8%. Its decision function is dominated by a single brightness proxy. And that in-distribution accuracy falls to 54.1% once brightness is standardized. The first is not a floor but a ceiling already reached: everything an in-distribution evaluation on this dataset can measure is available without looking at the packaging at all.

This does not imply prior work here is careless. It implies the dataset is defective in a way a standard held-out evaluation cannot reveal, and that the field's prevailing construction practice (Section II-F) makes such defects likely to recur and unlikely to be caught. Held-out partitions from the same pool inherit the confound exactly, so no in-distribution methodology — stratification, cross-validation, bootstrap intervals, even the product-level grouping we introduce — will expose it. Only evaluation on independently acquired data does.

### B. Why leakage turned out to be the smaller problem

We expected image-level leakage to dominate, because that is what the surrounding methodological literature emphasizes [11] and what a methodologically-minded reader raises first. It did not: at most 6.8 points, against an analytic ceiling of 9.2 and a confound worth more than 90.

The generalizable point concerns the ordering of audits. Leakage checks are cheap, well known and increasingly routine. Acquisition audits are equally cheap — reading image metadata and cross-tabulating it against the label — but are not routine at all, and on this dataset the second was worth an order of magnitude more than the first. We do not argue that leakage checks are unimportant; we argue that a field which performs one and not the other is auditing the smaller risk.

### C. Why the models behave differently, and why capacity is the wrong axis

External behavior is not ordered by capacity. It is better explained by *what kind of access* each model has to the confound.

M1 sees the confound directly and nothing else: brightness *is* a color-histogram feature, so the shortcut and the model's feature space coincide. It exploits the shortcut maximally in-distribution, transfers nothing, and gains nothing from correction because there was no other signal to unlock. M2 reaches resolution-dependent blur and detail statistics through filters learned from scratch on 357 images; it relies on the shortcut almost completely at baseline yet recovers strongly once the shortcut is removed. M3 and M4 inherit ImageNet invariances affording partial protection: both degrade severely at baseline, neither collapses to zero the way the models with unmediated pixel-statistic access do.

**Both frozen backbones deserve the caution once reserved for M3.** The attention audit (Section VI-G) finds them behaving identically on external images, and the most probable account is that neither learned to recognize packaging: both learned something about the photographic setting, which suffices on external sets that are entirely authentic, uniformly staged, and share a backdrop across both capture conditions. Capacity is the wrong axis on which to compare them; access to the confound, and what the evaluation happens to vary, are the right ones. Section VIII-E takes up what that implies for the correction itself.

### D. Practical implications

**For practitioners.** Read the three-way normalization as a zero-target-sample baseline, not a best available correction and not something to deploy on this evidence (Section VIII-E): anyone holding unlabeled target-domain images should expect representation-level alignment to do better.

**For dataset publishers.** Document the acquisition procedure for each class, and state whether the two classes were produced by the same one. That single sentence would have made this study's central finding visible without any of its analysis. Publishing a raw archive rather than a normalized one also preserves the traces a cheap audit reads.

**For reviewers.** Ask two questions of any authenticity-classification result: how was each class obtained, and was the model evaluated on data the authors did not collect. Neither requires expertise in the application area, and on this dataset either would have been decisive.

### E. The correction is a case study in substituting one confound for another

The normalization of Eq. (8) does what it was designed to do: label-free, under 17 ms, and worth 77.3 to 86.0 external points for three of four models at an in-distribution cost of at most 1.4. We nevertheless report it as an instrument and not a remedy, and four results already given are the reason. Separately each reads as a caveat; together they make a different point. *The recovered accuracy does not rest on the packaging*: across 40 external maps, without exception in either backbone, the evidence for "authentic" comes from the background and for "counterfeit" from the product (Section VI-G), and both external sets share one dark backdrop. *The exchange is not stable*: M2, the best corrected model on Split C, falls to 0.463 on a second capture of the same products (Section VI-F), which a correction that had truly removed the dependence on acquisition would not do. *The pipeline is under-determined by its own description*: permuting operator order alone moves external accuracy 50 points under a 2.7-point in-distribution range, and the ordering scoring highest in-distribution scores lowest externally (Section VII-B), so a detail a methods section leaves implicit decides most of the result and the usual way of settling it picks the worst option. *Removing more information keeps helping*: tightening the resolution bottleneck from 128 px to 96 px raises external accuracy to 0.873 (Section VII-A, Table S14), which is what a coarse distribution match predicts and not what restored reading of printed detail predicts.

None of this makes the operator useless; it fixes what it is for. Being label-free and a fixed function of one image, the change in external accuracy when it is applied is a measurement, bounding how much of the observed failure the three acquisition axes account for — here 77 to 86 points of the roughly 94 lost. Read instead as something to deploy, it trades an audited cue for an unaudited one: the same move, at one remove, that produced the dataset this paper is about. **A correction is itself dataset construction, and is owed the same audit as a dataset**, to which Section VIII-G's taxonomy applies exactly as it does to a raw archive.

### F. Relation to the wider shortcut-learning literature

This study contributes a stronger form of a known failure and a different cause for it. Where the medical-imaging cases document a partial, incidental correlation between site and label [7]–[10], the confound here is total and is produced by the researcher, because the negative class was unobtainable by the procedure that produced the positive one. That makes the population at risk nameable in advance — any dataset whose classes were sourced separately — which is what turns a cautionary tale into a screening rule.

### G. A taxonomy of provenance defects, and what detects each

The datasets audited here failed in different ways, and a third near-failure was caught while building our own evaluation set. "Provenance confound" is not one defect but a small family, each member needing a different check. Section S-I-T gives the full treatment with instances and costs; the members are:

**Type A, acquisition-statistic confound.** The classes differ in format, resolution, compression or brightness because they were captured by different processes. *Detected by* the metadata audit of Section VI-A. *Instance:* the Kaggle pool, audit accuracy 1.000. *Partially repaired by* the operator of Section V-D.

**Type B, content or modality confound.** The classes differ in what kind of document they are — product photography against bulletin graphics or screenshots, in the worst case with the label rendered in the pixels. *Detected by* human inspection; metadata may be silent. *Instance:* the Roboflow archive, 57/57, audit accuracy only 0.717.

**Type C, confound reintroduced by source selection.** The dataset is clean but a *derived* partition is drawn from a differently-acquired part of the source. *Detected by* re-running the Type A statistics on every partition after construction. *Instance:* our own first synthetic proxy, caught before use.

**Type D, degenerate shipped split.** The dataset's own partition files do not partition. *Detected by* intersecting the filename sets. *Instance:* the Kaggle archive, whose training folder contains all 661 images.

**Type E, a real content difference the audit reads as a confound.** This is the audit's false-positive mode. *Detected by* comparing the audit's axes against each other: storage format is never a property of the photographed object, whereas size, resolution and aspect ratio mix acquisition with content. *Instance:* the signature corpus of Section VI-C, format 0.500 and size 0.843, where the size signal is most likely ink coverage.

Two cross-cutting lessons follow. **Publisher-side tidying suppresses the symptom, not the disease**: the Roboflow archive had been resized to a uniform resolution and format before release, which erased exactly the traces the cheap audit reads while leaving a total Type B confound untouched — so a curated dataset is *harder* to audit than a raw one, and a clean audit on a normalized archive carries almost no information. And **the audit's output is not a verdict**: it says a trivial statistic separates your classes, and establishing that the statistic is an acquisition artifact rather than a property of the objects is a second step.

### H. What would falsify the general claim

The claim of Section I-A is causal — asymmetric class availability *produces* provenance confounding — and we state what evidence would count against it. Datasets in which the scarce class was obtained by the same procedure as the abundant one should show no Type A confound; [3], which photographed authentic and counterfeit samples on one Raspberry Pi rig, is the one study in Table 1 that plausibly meets this condition, and it also reports the lowest accuracy in that table. Conversely, a survey of authenticity datasets that found the audit firing no more often on separately-sourced collections than on jointly-sourced ones would refute the mechanism. That survey is the natural next study and we have not performed it: two datasets in one application area, plus one corroborating report from another [30], is enough to motivate the mechanism and not enough to establish its prevalence.

## IX. Limitations

Section S-II states each of these in full, with the evidence for and against; the list here is complete but compressed.

**The external evaluation is authentic-only**, so every external number is a false-positive rate and nothing else. The synthetic proxy probes the counterfeit direction by perturbing genuine photographs and is a corruption-robustness test in the spirit of ImageNet-C [12], never a recall measurement.

**Both external sets share one backdrop.** They vary device and lighting on the same products, so the surround cue of Section VI-G is untested. This is the study's most consequential gap, and it qualifies every claim that the correction "holds" across a capture shift.

**"Leakage-free" means product-identity leakage only.** No partition of this pool can decorrelate acquisition, because the counterfeit class exists in exactly one capture pipeline. Cross-validating across sources — the strongest available answer — fails for the same reason: the only other public authentic/counterfeit pharmaceutical dataset has a counterfeit class unusable at any position in a fold, so a source-held-out fold would contain no negatives.

**The correction is a preprocessing bottleneck, not a domain-adaptation method, and is not compared against one.** Eq. (8) is a *zero-target-sample baseline*: the performance recoverable when nothing is known about the deployment distribution. Anyone holding even unlabeled target images should benchmark second-order alignment, distribution matching or an adversarial confusion head against it. We expect those to win; the margin is unmeasured here, because every such method consumes target data, which would forfeit Split C as an external evaluation.

**The normalization axes were chosen with knowledge of the external set**, which is target-distribution information a practitioner would not have. Section VII-B removes that dependency by nominating the same axes from the training partition alone, so the objection is answered on this dataset; it is not answered in general, because no training-set procedure can nominate an axis confounded only in deployment.

**The generality claim is a hypothesis with a stated test, not a measured rate.** Two datasets in one application area, seven audited across four, and one convergent report from an unrelated field [30] motivate the mechanism; they do not establish how often it occurs. Section X names the survey that would.

**Statistical power is thin throughout.** In-distribution test partitions hold 74–76 images, every pairwise comparison is underpowered, and the ablations are single executions rather than distributions over seeds — so a difference of a point or two should not be read as a difference. The pipeline is deterministic, each ablation re-runs its own baseline in the same execution, and the production condition reproduces exactly across three post-fix scripts, but seed-to-seed variance is itself unmeasured. Results predating the augmentation-seeding fix are identified in the captions where they appear.

**Both transfer models are frozen backbones**, which Section V-B argues is the right instrument for isolating an input-distribution effect and which CPU-only hardware also required; the two coincided, and we would not claim the second did not make the first easier to adopt. The limitation is unaffected by that argument: **nothing here measures a fine-tuned network**, so no result of ours bounds what transfer learning can do here in either direction (Section X). The attention audit is a further limit — 62 maps scored by a single annotator, with no inter-rater agreement to report. Finally, some numbers predate checkpoint persistence and cannot be re-derived: an earlier M4 accuracy of 0.946 could not be explained once the checkpointed pipeline deterministically produced 0.919, because the original run's artifacts no longer exist. The newer value is the one reported, and the older one is unrecoverable rather than refuted.

## X. Future Work

**Acquire an external set that varies the photographic setting, and one that is counterfeit-labeled.** These are the two evaluations this study most needs and could not build. The attention audit shows both backbones justify "authentic" by the surround, and both external sets here share one backdrop, so neither disturbs that cue; photographs against varied surfaces, in hand, or in uncontrolled conditions would test it directly, and are far cheaper to obtain than the counterfeit-labeled set. That set remains the single addition that would most change what can be claimed, and its requirements are specific: independently photographed, verified rather than assumed by the pHash procedure of Section IV-B, and with acquisition method balanced across its two classes so that it does not import the confound it is meant to test.

**Build a training set with acquisition balanced across classes.** Because the confound cannot be filtered away, the durable fix is at collection time: several independent photography setups, each contributing both classes. Such a pool would also let the leakage question be re-asked where the effect is not swamped by sampling variance.

**Fine-tune the backbones — the highest-priority item for anyone with a graphics processing unit (GPU).** Section V-B defends the linear probe as the instrument for separating an input-distribution effect from a representation-learning one, and the CPU-only hardware required it in any case; whichever reason the reader weights, no result here describes a fine-tuned network. **The frozen-backbone numbers are therefore not an upper bound on what transfer learning can do on this task, in either direction.** The two outcomes are equally informative and opposite: adaptable features may discard the confound once the head can no longer profit from it, or the extra capacity may specialize onto residual acquisition artifacts more aggressively than a frozen trunk does — in which case fine-tuning would worsen external generalization while improving every in-distribution number, and Section VII-A's inversion suggests that would be invisible to anyone evaluating in-distribution.

**Survey the mechanism across application areas.** The most valuable extension is not another model but a measurement. Section VI-C applies the audit to seven datasets in four areas, enough to show that it discriminates and to expose one false-positive mode, and nothing like enough to estimate how often the confound occurs. A survey designed for that — a defined sampling frame of authenticity datasets, a pre-registered scoring rule, and enumeration rather than listing-order sampling — would convert this paper's central claim from a motivated hypothesis into a measured prevalence, and needs no training runs at all. Section VIII-H states what result would refute it.

**Test further acquisition axes, and finish the reproducibility substrate.** Aspect ratio, sensor noise, and staging conventions remain untested; the white-balance result shows that a real dataset-wide difference need not be part of the mechanism, that a candidate must be judged against the current operator, and that the harness must be quieter than the effect being measured. Any new axis should be swept for composition position, not only for inclusion. Separately, a content-aware attention measure — Grad-CAM mass inside an annotated product box — would separate the two readings the border-mass metric leaves open, and one remaining ablation condition still predates the seeding fix and is flagged as unverified where it appears.

## XI. Conclusion

We set out to measure how much of a reported accuracy on a small public counterfeit-medicine dataset survives methodological correction, expecting train/test leakage to be the mechanism at issue. Leakage accounted for very little: at most 6.8 points against an arithmetic ceiling of 9.2, and under half a point for three of four models. Almost all of the inflation is something else, and that something else has a structural cause reaching well beyond the dataset we started from.

In any binary image task asking whether something is genuine, the inauthentic class is harder to obtain, so it is obtained differently — screen-captured, scraped, edited or generated. The label then predicts the acquisition process, which is easier to learn than the semantics, and no in-distribution evaluation can tell the difference, because a held-out partition from the same pool inherits the confound in the same proportion. We ran stratification, grouped cross-validation, bootstrap intervals and a leakage-free product-level split; none saw anything wrong. Here every counterfeit-labeled file is a screen capture and every authentic-labeled file a downloaded photograph, without exception across 510 images; a classifier given three acquisition scalars and no pixels then scores 100% on the leakage-free partition, encoded size alone suffices, and the filename extension separates the classes perfectly. The dataset's stated task is not merely hard to measure on it; it is unmeasurable on it.

The consequence is severe. On 150 authentic photographs from an independent source, two of four models were correct on zero images and the best in-distribution model on 3.3%, while scoring 97.4% on the authentic class of its own test partition. A label-free three-stage normalization raises external accuracy to 86.0%, 80.7% and 77.3% at an in-distribution cost between −1.4 and 0.0 points — and that number is not the repair it looks like. Rephotographing the same products on different hardware leaves the two frozen backbones intact but drops the from-scratch CNN to 0.463. Permuting only the order of the three operators, with the same constants, model and data, moves external accuracy from 0.380 to 0.880 under a 2.7-point in-distribution range, and the ordering scoring highest in-distribution scores lowest externally; a practitioner tuning this preprocessing the ordinary way would have chosen the worst of six with no way to know. And categorizing all 62 attention maps — after finding that the ones previously inspected came from a mis-configured network — gives a result without exception across 40 external maps: both backbones justify "authentic" by the background and "counterfeit" by the product, and both external sets share one dark backdrop. The models that look robust are the ones whose shortcut our evaluations happened not to vary. What the correction measures is how much of the failure the acquisition axes account for. It is not a remedy, because removing a confound from the input is itself dataset construction, and installs new ones as readily as the original construction did.

Gaps of 16 to 20 points also remain for both transfer models, no model achieves well-calibrated counterfeit recall against a synthetic proxy, and the counterfeit-recall direction is untested against real counterfeits. We would not deploy any of these models.

The methodological claim we would most like carried forward is cheap to act on. Before training anything, fit the classifier you intend to use to acquisition metadata alone — format, encoded size, resolution, aspect ratio — under your own leakage-free split, and report the number. It costs seconds, needs no data you do not already have, and lower-bounds how much of your eventual result the acquisition process can explain. Here it is 1.000, which settles the interpretation of every accuracy ever reported on this dataset before a single network is trained.

Three qualifications keep that recommendation honest. First, we can offer no validated threshold: eight datasets, five of them scorable, is far too few for a false-positive or false-negative rate. What the scores support is narrower — a high score on **format** is close to decisive, because storage format is never a property of the photographed object, while size, resolution and aspect ratio mix acquisition with content. Our signature negative control returns 0.500 on format and 0.843 on size, and that size signal is most likely ink coverage, a real difference between genuine and forged writing. The number is a reason to look; the axis it comes from says where. Second, the audit is necessary but not sufficient: on a second pharmaceutical dataset it returned 0.717 while that dataset was confounded at least as badly, because its publisher had normalized the acquisition traces away without removing the confound. Third, it says nothing about whether a model generalizes; only data someone else acquired does that.

The same signature has been documented independently in generated-image detection [30] — genuine class lossy and small, synthetic class lossless and large, detectors partly reduced to compression detectors. Two unconnected literatures arriving at one confound is what a structural cause predicts, and we would expect it wherever a scarce class must be manufactured or harvested separately from an abundant one.

## Acknowledgment

This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors, and was carried out on a single consumer laptop; the CPU-only constraint that shapes several of this paper's design decisions is a direct consequence.

We thank the maintainers of the three public datasets used here [19], [20], [21]. The Mendeley and Roboflow datasets are distributed under CC BY 4.0; the Kaggle dataset carries no license in its archive and its listing states its license as "Unknown", so it is attributed to its uploader and no image from it is redistributed here — only derived per-image statistics, split assignments and filenames. Readers reproducing the pool must obtain that archive from the original listing themselves.

This paper is critical of the construction of a dataset whose uploader made it freely available and made no research claim about it. That criticism is directed at a property of the artifact and at the practice of adopting such artifacts without auditing them; it is not directed at the uploader, and nothing here suggests bad faith on anyone's part. The same applies to the prior studies surveyed in Section II-F, whose reported accuracies we do not dispute and have not attempted to re-derive.

## Ethics, Conflicts of Interest, and Data Provenance

**Human and animal subjects.** This study involves neither. All images are photographs of pharmaceutical packaging obtained from public archives; none depicts an identifiable person, and no personal or patient data was accessed at any stage.

**Data provenance and permissions.** Every image originates from a third-party public archive, used within its stated terms: Mendeley Data and Roboflow under CC BY 4.0 with attribution, and the Kaggle archive under no stated license, from which nothing is redistributed. No data was scraped or purchased, and no counterfeit product was acquired, handled or imaged by the author.

**Intended use and misuse.** No model examined here is fit to authenticate medicine, and this paper should not be read as validating any of them for that purpose. A falsely reassuring authentication tool is more dangerous than no tool: a consumer told a falsified product is genuine is worse off than one who remains uncertain.

**Conflicts of interest.** The author declares none, has no affiliation with the maintainers of any dataset examined here, and no commercial interest in any pharmaceutical-authentication product.

**Funding.** This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Generative-AI disclosure.** This manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic, covering drafting and revising the text, writing and debugging the analysis and figure-generation code, and identifying several defects in earlier versions of the pipeline that are disclosed in Section S-I-G. All experimental design decisions, all interpretations, and the decision to report each negative and superseded result rather than remove it are the author's. Every number reported here is produced by committed code from committed data and was verified by re-execution, and no result, citation or reference was generated by a language model without verification against a primary source. The author takes full responsibility for the content.

---

## Data and Code Availability

**Repository.** All code and derived artifacts are at `https://github.com/sophiezla/counterfeit-drug`, archived at **doi:10.5281/zenodo.21936721** (release v1.0.0, 14 August 2026), the exact state of the code that produced every number reported here; doi:10.5281/zenodo.21936720 resolves to the most recent release. It holds the data pipeline, the four model implementations, every analysis and figure script, the per-image statistics and split assignments, the persisted checkpoints, and the sources of this manuscript and its supplement.

It deliberately contains **no images**. The Kaggle archive carries no license grant, so nothing from it is redistributed — only derived per-image statistics, split assignments and filenames. Grad-CAM overlays and the manual-review contact sheets are excluded for the same reason, since they reproduce image content rather than describe it; both are regenerated by committed scripts from a reader's own copy of the archives.

Five analysis scripts read only committed artifacts, need no image data and no training, and reproduce their results in seconds: `metadata_oracle.py` (Table 5), `provenance_audit_multi.py` (Table 6), `cross_domain_audit.py` (Table 7), `power_and_leakage_bound.py` (the analytic leakage ceiling) and `external_intervals.py` (the external intervals). Together they cover the paper's two central quantitative claims without requiring a reader to obtain the images or run a model.

Two caveats on exact reproduction. Checkpoints are persisted for the production models with the learning rate, seed, best epoch and epoch count each was trained under, and `load_checkpoint` refuses one whose recorded rate differs from the caller's expectation; the external evaluations load these rather than retraining. The ablation scripts predate that mechanism and rebuild instead, so their absolute values are comparable within a run and not across runs. Results produced before the augmentation-seeding fix are identified in the captions where they appear, and superseded results are archived alongside the current ones rather than deleted.

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

[21] Harshini T. G. R., "Counterfeit_med_detection," Roboflow Universe, version 4 (multiclass export), Nov. 2022, CC BY 4.0. Accessed: Aug. 28, 2026. [Online]. Available: https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection. *Contributor name, license, version count and year confirmed in a browser on 28 Aug. 2026 against the publisher's own suggested citation; the landing page rejects automated requests, which is why an earlier note deferred this. The version date, the 4,260-image count and the "resize to 640x640 (stretch)" preprocessing that Section VI-B attributes to the publisher are read from `README.roboflow.txt` inside the export archive held locally.*

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

## Author Biographies

![Sophie Zhu](paper/figures/author_photo.jpeg)

**SOPHIE ZHU** is a student at Mira Costa High School, in Manhattan Beach, CA, USA. Her research interests include artificial intelligence, healthcare technology, computer vision, and machine learning applications in public health. Her work focuses on the development of accessible and scalable artificial intelligence systems for healthcare challenges, with an emphasis on low-cost technologies for resource-constrained environments. Her current research examines how dataset construction shapes what image classifiers actually learn, and what evaluation protocols are needed before such systems can be trusted in public-health settings.
