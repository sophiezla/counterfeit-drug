# Auditing Provenance Confounding in Image Authenticity Classification: A Counterfeit-Medicine Case Study

**SOPHIE ZHU**<sup>1</sup>

<sup>1</sup>Mira Costa High School, Manhattan Beach, CA 90266 USA (e-mail: sophiezhu2028@gmail.com)

ORCID: 0009-0004-2403-910X

Corresponding author: Sophie Zhu (e-mail: sophiezhu2028@gmail.com).

This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors. The manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic; see the disclosure in the Acknowledgment.

---

**ABSTRACT** In image datasets asking whether an object is genuine, the inauthentic class is scarcer and often obtained differently: screen-captured, scraped, edited, generated. The label then predicts the acquisition process rather than the property of interest, and every held-out partition inherits the confound alike. We call this **class-conditional provenance confounding**, and propose a pre-training **provenance audit**: fit the classifier you intend to use to acquisition metadata alone, under your own leakage-free split, and report the number. In a public counterfeit-medicine dataset every counterfeit file is a PNG screen capture and every authentic one a JPEG photograph; three header fields, no pixel decoded, then reproduce the labels exactly, so no in-distribution result on that pool can establish that a classifier learned packaging rather than provenance. Across four model families, correcting the split changes accuracy by at most 6.8 points, and a fixed-test-set experiment varying leakage alone by 0.3 points; external evaluation on 150 independently captured authentic photographs drops the strongest model's authentic-class specificity from 97.4% to 6.0%. A label-free normalization of resolution, brightness and compression raises that specificity to 86% and 81% for two of three models, the third inside seed variance. We report it as a diagnostic rather than a remedy, because eliminating one provenance signal can expose another: a second capture condition drops the best corrected model to 63% across seeds, reordering the operators moves external specificity 50 points while ranking the worst pipeline best in-distribution, and a region-substitution test locates the recovered specificity on the photographic surround for both corrected backbones — overwriting the outer half of the frame costs 22 to 50 points of specificity, while overwriting an area-matched centre region costs nothing. Removing a confound is itself dataset construction, and preprocessing is therefore an object of provenance auditing in its own right. We report where the audit misfires.

**INDEX TERMS** Data leakage, dataset bias, domain generalization, external validation, hidden stratification, image classification, provenance confounding, shortcut learning.

---

## I. Introduction

Substandard and falsified medical products are a persistent global health problem, concentrated in low- and middle-income countries and in unregulated online supply chains [1], [2]. Because much falsified product is visually imperfect — misprinted cartons, wrong color separations, missing batch information — image-based screening from a consumer smartphone is an attractive triage tool, and a body of work has applied convolutional networks to photographs of medicine packaging and reported high binary accuracy [3], [26]–[28], alongside a larger literature on pharmaceutical *identification* rather than *authentication* [4], [5].

A property of that body of work motivates this paper's method as much as its subject. There is no shared benchmark for pharmaceutical authentication: each study identified through our targeted literature search built or adopted its own image set, and none of them reports an audit for confounds between acquisition and label (Section II-F). Each reported figure therefore rests on the construction of a single ad hoc collection, and that construction is not examined in the paper reporting it.

### A. The general problem: asymmetric class sourcing

That condition is not peculiar to pharmaceuticals, and the mechanism it creates is this paper's subject. In any two-class image dataset asking *is this genuine?*, authentic examples are abundant while the other class is scarce almost by definition: verified counterfeit stock is hard to obtain for research and often restricted, and forged documents are ordinarily held as evidence. A researcher needing a negative class therefore obtains it *by some other means than the one that produced the positive class* — screen-capturing regulator bulletins, scraping a different corpus, editing authentic images, or generating examples with a model.

Each such substitution can introduce a systematic difference between the classes unrelated to the property being labeled, because acquisition method determines file format, encoded size, resolution, noise floor, compression signature, color rendering and often backdrop. We call this **class-conditional provenance confounding**, and identify asymmetric class availability as a mechanism by which it can arise — one predictable from how a dataset was assembled rather than an accident of any one collection.

Let $Y$ be the label, $X$ the image content a correct decision would rest on, and $A$ the acquisition variables a file carries independently of that content — container format, encoder settings, capture device, resolution, illumination, backdrop. The difficulty is not that $A$ exists but that the assembly procedure makes it informative about the label,

$$I(Y; A) > 0$$

for variables $A$ disjoint from the content $X$ on which the task intends its decision to rest. The extreme case, and the one this dataset presents, is

$$H(Y \mid A) = 0$$

— the label a deterministic function of acquisition. Here container format alone leaves no residual entropy: every counterfeit-labeled file is a PNG and every authentic-labeled file a JPEG, across all 510 images. A **provenance audit** measures how close a dataset sits to that extreme by fitting a classifier to $A$ alone and reporting its held-out accuracy — up to sampling error, a lower bound on how well acquisition can predict the label.

> **FIGURE 1.** `paper/figures/fig15_mechanism.pdf` — The mechanism, and where it is detectable. The boxes are general and carry no numbers; the gray line beneath each is this paper's measurement of that step on the case-study dataset. The audit of Section VI-A reads the third box, which is reachable from a file listing before any model exists.

Three properties make the condition damaging. It is **the easiest thing in the data to learn**, low-level global statistics being easier to extract than the semantics of a printed carton, and a shortcut-seeking optimizer [6] finds them first. It is **invisible in-distribution**, because a held-out partition inherits it in the same proportion. And it is **silent in the reporting record**, since acquisition method is rarely documented.

We separate three levels of evidence here and hold to them throughout. **Demonstrated**: the case-study dataset is completely provenance-confounded, container format reproducing the label on all 510 images (Section VI-A). **Supported**: the mechanism is consistent with an independent report in another application area. In generated-image detection, real images are harvested as lossy JPEGs at modest resolution while generated images are written as lossless PNGs at native size, and Grommelt *et al.* [30] show that on GenImage this makes format, compression and size predictive of the label, that detectors partly become JPEG detectors, and that equalizing those factors shifts cross-generator performance by more than 11 points — no shared data, application area or method of discovery, and the same confound, which is what a structural cause predicts and a coincidence does not. **Not established**: how frequently this occurs. A prevalence estimate would require auditing a representative sample of such datasets, which neither this paper nor, as far as we can determine, any other has done; Section VI-A's pilot audit of seven archives finds both a totally confounded case and a clean one, enough to show the audit discriminates and far short of a rate. Table 8 records every claim in this paper against these three levels, and Section VII-G says what would falsify the mechanism.

### B. This paper

The study began as a methodological exercise. The Kaggle *Fake vs Real Medicine* set is small (661 images), freely available, and typical of what this area works with: no data card, no stated acquisition protocol. Under a protocol fixed in advance we set out to establish how much of a reported accuracy survives methodological correction — identical models under a naive and a near-duplicate-grouped split, four model families from a 97-parameter linear baseline to a 4-million-parameter pretrained backbone, and an external source verified independent rather than assumed so.

The result was not the one the design anticipated. Correcting the split changed in-distribution accuracy by at most 6.8 points; external validation changed the picture. On 150 authentic photographs from an independent source, two of four models classified *zero* correctly and the strongest in-distribution model almost none, despite 97.4% on the authentic class of its own test partition. Looking for an explanation led to the dataset itself: its two classes were not merely photographed differently but *acquired* differently, every counterfeit-labeled file being a screen capture (`Screenshot*.png`) and every authentic-labeled file a downloaded photograph (`images*.jpg`), correlating with the label exactly 1.0 across the pool. Any model, including a 97-parameter linear classifier on a color histogram, has unobstructed access to it. It is the hidden stratification of [7], total rather than partial (Section II-B).

The contributions are three, in the order we would defend them:

1. **A pre-training provenance audit, and the mechanism that makes it worth running.** We identify asymmetric class sourcing as a dataset-construction mechanism that can produce provenance confounding — a special case of shortcut learning, dataset bias and domain shift distinguished by being predictable from how the dataset was assembled (Section II-B) — and propose the *provenance audit*, stated as a procedure in Section V-G: fit the intended classifier to acquisition metadata alone, under the study's own leakage-free split. It needs no external data, no annotation and no pixel decoding, and returns **1.000** here from header fields alone. A high score establishes that a provenance shortcut is available, not that a given pixel classifier took it. We also report where it fails: on a second published dataset it returns only 0.717 although that dataset is confounded at least as severely, because its publisher had normalized every image before release — a tidied dataset is *harder* to audit — and across four application areas it exposes a false-positive mode (Table 3).

2. **A case study in which the audit is decisive and the usual checks are not.** We report a previously undocumented confound in a public counterfeit-medicine dataset, with effect sizes on brightness, resolution, aspect ratio and file size; an exact linear logit decomposition showing that a linear model's decision is dominated by the statistic the confound controls; and a degenerate shipped split whose training folder is a superset of both others (Sections III-A, VI-A). Against it, classical leakage correction accounts for far less: near-duplicate grouping changes accuracy by at most 6.8 points, and a paired experiment varying leakage alone on a fixed test set moves it by 0.3 points [−1.9, +2.4], whereas in-distribution accuracy of 97% coincides with an external authentic-class specificity of 6.0%, and intervening on three acquisition statistics recovers most of that gap (Sections VI-B–VI-D, VI-F). In this dataset the acquisition axes are associated with a substantially larger effect than near-duplicate leakage, and are the only one of the two on which an intervention moves the external result.

3. **Evidence that eliminating one provenance signal can expose another, which makes preprocessing itself an object of provenance auditing.** A label-free normalization, ablated per axis, architecture, constant and composition order, and offered as a probe rather than a remedy. It raises external authentic-class specificity from 6.0% to 81–86% for two of the three models it is applied to, the third's apparent gain lying inside seed variance. We decline to offer it for use, because three of our own results say what that number is made of (Section VII-E): operator *order*, a choice a preprocessing description normally leaves implicit, moves external specificity across a 50-point range under a 2.7-point in-distribution range with the in-distribution ranking inverted; region substitution shows both corrected backbones depend on the photographic surround rather than the region holding the packaging; and the recovery does not survive a second capture condition for the model it helped most. The correction removes the confound the audit found and leaves the models resting on an acquisition cue the audit did not test — the same substitution, at one remove, that produced the dataset.

This is an empirical critique and a diagnostic method. We propose no new architecture — a 97-parameter linear model and a 4-million-parameter pretrained network are not statistically distinguishable on this test partition — and do not propose the normalization of Section V-D for adoption either. Everything offered for adoption is a check: fit your classifier to acquisition metadata before training it, evaluate on images you did not collect, and audit a correction as you would a dataset.

## II. Related Work

### A. Image-based pharmaceutical authentication and identification

Image classification has been applied to pharmaceutical products for both *identification* (which drug is this?) and *authentication* (is this drug genuine?). Ramos, Samonte and Manlises [3] proposed a convolutional neural network (CNN) authentication system directly comparable in task framing to this work; adjacent identification work addresses look-alike medication errors across 250 blister-packaged drug types [4] and pill-image retrieval [5]. That literature establishes that packaging imagery carries usable signal. As far as this review found, none of it examines *why* reported accuracies are as high as they are, or audits its datasets for confounds between acquisition and label.

### B. Shortcut learning and hidden stratification

Geirhos *et al.* [6] formalized *shortcut learning*: networks adopt decision rules exploiting superficial, spuriously predictive correlations, scoring well in-distribution while failing wherever the shortcut is absent. That framing describes this paper's central finding precisely.

The failure has a documented precedent in medical imaging. Zech *et al.* [7] showed that pneumonia detectors trained on chest radiographs from three hospital systems could predict which system an image came from, and used that hospital-identity signal — itself correlated with disease prevalence — as a shortcut for the diagnostic label, degrading substantially on an unseen site. Later audits report the same for scanner-, site- and manufacturer-level signal [8], [9], and early COVID-19 radiograph classifiers were shown to rely on dataset-source confounds rather than radiographic signs [10]. DeGrave *et al.* [31] put the case most sharply: applying explainable-AI methods to published COVID-19 radiograph detectors, they conclude the systems rely on confounding factors rather than pathology, and so "appear accurate, but fail when tested in new hospitals" — the closest precedent we are aware of for the mechanism described here.

The mechanism is worth locating among the terms nearest to it, because the contribution is not the discovery that models learn shortcuts. Shortcut learning [6] names what a model does; dataset bias [32] and spurious correlation name a statistical property of a sample; domain shift names a relation between two distributions, one of them the deployment distribution. Class-conditional provenance confounding rivals none of these. It is a *dataset-construction mechanism* that produces all three, named separately because the cause is what makes it detectable in advance: because one class was unobtainable by the procedure that produced the other, acquisition is correlated with the label *within the training distribution itself*, before any model is fitted and without reference to any deployment distribution.

Three consequences follow that the general terms do not carry. The association can be complete rather than partial — incidental at the three hospital systems of [7], exactly 1.0 across 510 images here. It is predictable from a dataset's construction, so the population at risk is nameable in advance: any collection whose classes were sourced separately. And it survives leakage-aware validation, every partition of one pool inheriting it in the same proportion.

What separates this paper from [31] is level rather than subject. That work diagnoses confounding one dataset at a time, with methods needing the images and a trained classifier; we ask what makes such datasets predictable in advance from how a class was obtained, reduce the diagnosis to a screen that reads file listings before any model exists, and follow the correction through to show that removing a confound is itself dataset construction (Sections VI-F, VII-E). The closest published analogue outside medicine is [30], described in Section I-A.

### C. Data leakage and evaluation protocol

A related but distinct concern is train/test leakage from improper partitioning: splitting at the image rather than the subject level lets near-duplicate images of one entity appear in both partitions, inflating reported performance [11]. That motivated this work's two-split design, evaluated in parallel so the leakage effect is measured rather than assumed. On this pool it is small relative to the capture-pipeline confound (Section VII-B).

### D. Robustness to synthetic corruption

Hendrycks and Dietterich [12] introduced ImageNet-C, applying standardized corruptions to measure robustness without collecting new out-of-distribution data. This work adopts the same logic: lacking a counterfeit-labeled external dataset, independent authentic photographs are perturbed with print-quality, color and text-region defects to build a synthetic proxy. Following [12] we state that such a proxy measures robustness to a documented perturbation style, not label-defined class recall.

### E. Architectures and interpretability methods

The four model families span a classical color-histogram baseline through MobileNetV3 [13] and EfficientNet-B0 [14], both used as frozen ImageNet-pretrained feature extractors with a linear head. Evidence attribution for the convolutional models uses gradient-weighted class activation mapping (Grad-CAM) [15] and occlusion sensitivity; we call these *attribution* rather than *attention* analyses throughout, since neither is an attention mechanism. Attribution for the linear baseline uses an exact logit decomposition, which coincides with the linear SHAP form of [16] under an independent-feature background (Section V-E). Domain-generalization surveys [23] situate the normalization of Section V-D closer to hand-designed covariate-shift alignment than to representation learning.

### F. What datasets this sub-field actually uses

Because this paper's contribution is a dataset audit, the datasets neighboring results rest on are themselves prior work. Table S26 records what each study identified through our targeted literature search trained on, together with whether it reports any check that acquisition conditions are balanced across its two classes; none of the five does. Where the full text was obtainable, it was read in full. The search combined the terms *counterfeit*, *falsified*, *fake* and *authentication* with *medicine*, *drug*, *pharmaceutical*, *packaging* and *blister* across Google Scholar, IEEE Xplore and Scopus, and followed citations forward and backward from each hit. This is a targeted search, not a systematic review: no protocol was registered, no screening was duplicated, and its negative findings mean "not found by this search" rather than "does not exist".

Three observations follow, and each bears on the finding of Section VI-A.

**No shared benchmark exists, so the confound cannot be inherited — only re-invented.** No two studies in Table S26 evaluate on the same images, and the Kaggle set audited here is not a community benchmark: as of 28 August 2026 its listing records 591 downloads, 3 public notebooks and no discussion, and our search located no peer-reviewed study using it. The claim is correspondingly narrow: not that a widely-shared benchmark is broken, but that a dataset assembled the way this sub-field routinely assembles them carries an acquisition confound its own users did not detect.

**The most common class-construction procedures make the confound near-inevitable.** In [26] the counterfeit class is produced by digitally editing authentic images and in [27] by a generative model, so in both the two classes are by construction outputs of two different image pipelines, exactly as in the dataset audited here — and neither reports a check that would surface it. A model can score highly on such a set by learning the editing or generation signature, and no in-distribution evaluation distinguishes that from learning authenticity. Where the classes *were* acquired under a common protocol — [3], on one Raspberry Pi rig — the reported accuracy is the lowest in Table S26 (88.75%). We note the direction and stop there: the studies differ in dataset, task framing, architecture and sample size, and none of that spread can be attributed to acquisition confounding on this evidence.

**Studies that do control acquisition say so explicitly.** Outside pharmaceuticals, Garcia-Cotte *et al.* [29] report counterfeit detection on branded garments from smartphone images captured "under natural, weakly controlled conditions", at 99.71% after a 3.06% rejection rate. Whatever else separates that work from Table S26, it states its acquisition regime as a property of the result — the reporting standard Section VII-D argues should become routine here.

## III. Dataset

### A. Sources considered

Three public sources were inventoried, all considered for the modeling pool: the Kaggle *Fake vs Real Medicine* set [19], 661 unique files re-listed across a bundled split, licence stated as "Unknown"; Roboflow *Counterfeit_med_detection* v4 [21], 4,260 files under CC BY 4.0, including the publisher's own 3× rotation and exposure augmentation; and the Mendeley *Mobile-Captured Pharmaceutical Medication Packages* archive [20], 3,900 files across six devices under CC BY 4.0. Two were excluded from modeling for the reasons below and the third became the external evaluation set; Table S1 gives the full inventory.

Two properties of the primary source should be recorded before any result is read. Both are verifiable in seconds by anyone holding the archive.

**Provenance.** It is a single-uploader Kaggle contribution, last updated 13 October 2025, distributed with its license field set to "Unknown". Counterfeit-class files are named `Screenshot YYYY-MM-DD HHMMSS.png`, with embedded timestamps falling in a small number of capture sessions; authentic-class files are named `imagesNN.jpg`. There is no data card, no collection protocol and no per-image provenance — none of which is unusual for a dataset of this kind, which is the point of Section II-F.

**The bundled split is not a split.** Alongside the class folders the archive ships `train/`, `val/` and `test/`. Counting unique filenames, the training folder lists all 661 while validation (453) and test (449) are proper subsets of it, with 286 filenames common to all three: a study adopting this partition trains on 100% of the data it then reports test accuracy on. We discarded it and built our own (Section IV-C), and record it because it is a second fully deterministic defect in the same artifact, and one no reader could detect from a reported accuracy.

### B. Why the second source was excluded: a label baked into the pixels

The Roboflow source appeared to be a second independent authentic/counterfeit dataset, and therefore a candidate both for pooling and for cross-dataset validation. Inspection showed it is neither. Of its counterfeit-labeled images, 57/57 unique source images are institutional advisory graphics carrying a regulator's logo, a banner headline and, critically, **the ground-truth label rendered as literal text inside the image**, while 263/263 of its plain product photographs are authentic-labeled: a model trained on it as shipped would learn to distinguish advisory collages from product photography. After excluding those, 9 more found by manual inspection and 52 rows carrying simultaneous `authentic=1` and `counterfeit=1` annotations, the source contributes **2** usable counterfeit images against 2,695 authentic. Prior work attributes its unsuitability to class imbalance; the deeper problem is a modality confound (Section S-I-T, Type B).

### C. Why the two sources are not independent

Perceptual-hash clustering (Section IV-B) found **202 clusters containing images from both sources**, covering 2,665 of 4,027 retained Roboflow images and 256 of 605 Kaggle images — **42.3% of the Kaggle pool has a near-duplicate in the Roboflow source**, sometimes differing only by a 90° rotation. This was confirmed visually on matched pairs, not inferred from hash distance alone. The Kaggle denominator here is 605 rather than the 661 files the archive ships, because the clustering artifact of record is written after the 56 manual exclusions of Section S-I-A; an earlier count on the pre-exclusion pool gave 229 clusters over 290 of 661 images, which the committed artifact does not reproduce and which we therefore do not report as the value of record. Neither source documents provenance, so we claim nothing about which derives from which; the relevant fact is that any study treating them as independent sources for cross-dataset testing would be leaking training data into "external" evaluation.

### D. The modeling pool

Given Sections III-B and III-C, **Splits A and B are built from the Kaggle pool alone**, which makes the split protocol the single manipulated variable; adding Roboflow would also have pushed the group-level class ratio from 44:56 to roughly 8:92 while contributing essentially no counterfeit signal. After exclusion and de-duplication the pool contains **510 images in 480 product-identity groups**, 272 authentic and 238 counterfeit. Neither source ships product labels, so these groups are near-duplicate clusters used as an operational proxy for product identity (Section IV-B); two dissimilar photographs of one package would not be grouped, at any threshold (Section S-I-Y). We therefore call the resulting design a **near-duplicate-grouped** split throughout, and reserve "product identity" for the field name in the code.

### E. The first external set (Split C)

The protocol called for a genuinely external source. A search for an independent *two-class* source found none: every candidate was either likely to share photographs with sources already in the pool (Section III-C) or carried no counterfeit label. We therefore use the Mendeley source [20] as an **authentic-only** external check: 150 photographs, one per distinct product, from a different country, photographers, camera hardware and backdrop protocol. Independence was verified rather than assumed (Section IV-B): **0 of 150 images matched anything in the pool**, nearest match at Hamming distance 10/64 against a threshold of 8, median 18.

An authentic-only set measures one quantity only. Because counterfeit is the positive class throughout (Section V-A), that quantity is **external authentic-class specificity**, the rate at which genuine packaging is called genuine; the corresponding false-positive rate is one minus it. We use that term, or "external specificity under acquisition shift", rather than "external accuracy" wherever an authentic-only set is being reported, and reserve *accuracy* for the mixed-class in-distribution partitions. It says nothing about counterfeit recall. Section S-I-B describes the synthetic proxy built to probe that direction, and Section VIII states the limitation that remains.

### F. The second external set (Split D)

One external set cannot distinguish a repair from a coincidence, so a second was built from the same archive's "iphone 11 pro" subset: **149 unique images** (the archive ships one duplicate filename), covering the same 150 packages as Split C on the archive's own account, photographed on different hardware under its deliberately different lighting protocol. Three properties make it the right second test and bound what it can settle.

It is a *different point on the confounded axis* rather than a repeat: mean brightness 0.389, against Split C's 0.162 and the training pool's 0.668, with median short side 2419 px. It is not pixel-interchangeable with Split C: rotation-canonical pHash puts only 1 of 149 images within the near-duplicate threshold of any Split C image, median distance 18. And the correspondence is at the level of the set, not the image — the archive ships no per-image product key and its two device folders do not share a numbering — so the two sets cannot be aligned image by image and are compared as independent proportions.

Because content is held approximately fixed and acquisition varies, Split D is a **capture-shift test**: not an independent product sample, and isolating exactly the axis this paper is about. What it can settle is correspondingly narrow. The two sets come from one archive, cover the same packages, and share one dark backdrop; they differ in capture device and lighting protocol and in nothing else we can identify. A model that survives C → D is therefore shown to be stable across **the device and lighting shift these two capture conditions represent**, not across acquisition in general — a distinction that matters because Section VI-E finds the backdrop itself implicated as a cue. The shared backdrop is the study's most consequential gap and is stated again where it bites (Sections VI-E, VIII).

## IV. Data Preprocessing

The full pipeline is deterministic (fixed seed 42 throughout) and idempotent; re-running reproduces byte-identical outputs. Fig. S1 summarizes it.

### A. Filtering

Exclusions are rule-based and documented in code, in three families: contradictory annotations (52 Roboflow rows), advisory-bulletin graphics (180 Roboflow files, Section III-B), and the 56 human-identified Kaggle files of Section S-I-A. Each is recorded with a machine-readable reason in the provenance table, so any downstream count traces to the rule that produced it.

### B. De-duplication and product identity

Neither source carries ground-truth product-identity labels, so near-duplicate photo clustering is used as an operational proxy. A 64-bit perceptual hash [25] is computed at all four cardinal orientations per image and the numeric minimum taken as a rotation-canonical hash:

$$h(x) = \min_{\theta \in \{0°, 90°, 180°, 270°\}} \mathrm{pHash}\big(R_\theta(x)\big) \tag{1}$$

Rotation invariance is necessary rather than decorative: the Roboflow source documents 90°-rotation augmentation, and a plain pHash treats a rotated copy as a different image. Pairs at Hamming distance 0 are treated as true duplicates and one copy removed; pairs at distance 1–8 are retained but assigned to the same `product_identity` cluster.

The threshold of 8 is conventional rather than derived, so Section S-I-Y sweeps it: up to distance 10 no cluster mixes the two class labels, at 12 three do, and at 16 the largest cluster holds 183 of 510 images, so 8 sits inside the range where the clustering still agrees with an external label it never reads. Split A's countable leakage stays between 2 and 18 clusters across that whole range, so nothing this paper concludes from the split comparison turns on the choice. Zero clusters mix authentic and counterfeit labels at the production threshold. The method is not robust to mirroring, a gap kept low-risk by the no-flip augmentation policy of Section V-C but not exhaustively verified.

### C. Split construction

Three partitions of the modeling pool are built:

- **Split A (naive)** — random 70:15:15, class-stratified, at the **image** level. This is the protocol in general use on data of this kind, and the only one available to a study that adopts a dataset's shipped partition without inspecting it, as Section III-A shows this dataset's shipped partition invites; none of the studies in Table S26 reports a grouped or identity-aware split.
- **Split B (near-duplicate-grouped)** — 70:15:15, class-stratified, at the **near-duplicate cluster** level, so no near-duplicate photograph of the same product can appear in more than one partition. The training partition additionally carries a `cv_fold` index from `StratifiedGroupKFold`, so 5-fold cross-validation never places the same product in two folds.
- **Splits C and D (external)** — the Mendeley photographs of Sections III-E and III-F, used only for evaluation.

An assertion in the pipeline verifies zero product-identity overlap between every pair of Split B partitions on every run; it passes. Comparing the two assignments directly, **9 of 480 product-identity groups (1.9%) have members in more than one partition under Split A** — this is the literal, countable leakage that Split B removes — and 230 of 510 images (45.1%) are assigned to a different partition under A than under B.

Split A holds 357/77/76 images and Split B 357/79/74 over 336/72/72 product groups, against Split C's 150 and Split D's 149; Table S2 gives every partition's class balance. The test partitions are small (74–76 images), so every point estimate in Section VI carries a 95% uncertainty interval, and comparisons are read against those intervals rather than against point differences. Two constructions are used — a percentile bootstrap and a Wilson score interval — and each table names the one it reports.

Three kinds of uncertainty are kept apart throughout, because several readings turn on which is being quoted. **Sampling uncertainty** is what a finite evaluation set supports for one trained model, and is what every bracketed interval describes unless a table says otherwise. **Training-run variability** is what a different initialization would have produced, measured separately across five seeds (Table 5). Neither bounds the other, and the difference is not academic: Section VI-C reports an effect clearly outside sampling uncertainty and entirely inside seed variance. **Distribution-shift uncertainty** is not addressed by either; only evaluation on data we did not collect speaks to it, which is why Splits C and D exist.

### D. Capture-method normalization

The three-stage normalization that Sections V-D and VII evaluate is applied *inside* the dataset class, before augmentation and before the network's input transform, identically for training, validation, in-distribution test and external partitions. It uses no label information at any point and could be shipped unchanged as an inference-time preprocessing step. Section V-D gives its definition.

---

## V. Methodology

### A. Task and label convention

The task is binary image classification. Throughout, authentic = 0 and **counterfeit is the positive class**, so precision, recall, F1 score, area under the receiver operating characteristic curve (ROC-AUC) and area under the precision–recall curve (PR-AUC) are reported with respect to counterfeit detection — the deployment framing, in which the costly error is calling a falsified product genuine.

Because a reader in a clinical setting may take "positive" to mean *genuine*, the convention is set out in full here and every later use follows it.

| Term | Meaning in this paper |
|---|---|
| $y = 0$ | Authentic (negative class) |
| $y = 1$ | Counterfeit (positive class) |
| Sensitivity, recall | Counterfeit correctly classified as counterfeit |
| **Specificity** | Authentic correctly classified as authentic |
| Accuracy | Fraction correct over a **mixed-class** partition; used only for Splits A and B |
| External specificity | Specificity on an authentic-only external set (Splits C and D); the only quantity those sets can measure |

Splits C and D contain authentic images only, so nothing computed on them is an accuracy and nothing computed on them estimates counterfeit recall. Where this paper reports an external number it is a specificity, and it is named as one.

### B. Models

Four model families are evaluated (Fig. S2), deliberately spread across capacity scales so that "does capacity explain the reported accuracy?" is answerable.

**M1 — Color histogram + logistic regression (97 learned parameters).** Each image is resized to 224×224 and a 32-bin-per-channel red-green-blue (RGB) intensity histogram computed, giving a 96-dimensional feature vector:

$$\phi(x) = \big[\,\mathbf{h}_R(x) \,\|\, \mathbf{h}_G(x) \,\|\, \mathbf{h}_B(x)\,\big] \in \mathbb{R}^{96}, \qquad \mathbf{h}_{c,b}(x) = \frac{1}{HW}\sum_{i,j} \mathbb{1}\!\left[ x_{ij}^{(c)} \in B_b \right] \tag{2}$$

with the 32 bins $B_b$ uniformly partitioning [0, 256). A logistic regression is fitted on $\phi(x)$:

$$P(y = 1 \mid x) = \sigma\big(\mathbf{w}^\top \phi(x) + b\big), \qquad \sigma(z) = \frac{1}{1 + e^{-z}} \tag{3}$$

with `class_weight="balanced"` and L2 regularization at scikit-learn's default strength. This model answers one question: how much of the reported accuracy is available to a classifier that cannot see spatial structure at all?

**M2 — Small CNN with a global-average-pooling (GAP) head (23,938 trainable parameters).** Three convolutional blocks with a conventional channel progression (16 → 32 → 64; each block Conv3×3 → BatchNorm → ReLU → MaxPool2×2), with a GAP head rather than the flatten-then-dense head small-dataset CNN work commonly uses:

$$g_k = \frac{1}{H'W'}\sum_{i=1}^{H'}\sum_{j=1}^{W'} a_{ijk}, \qquad \hat{y} = \mathrm{softmax}\big(W_{\!f}\,\mathrm{drop}_{0.5}(\mathbf{g}) + \mathbf{b}_{\!f}\big) \tag{4}$$

The head is the point of this model: flattening the trunk's 28 × 28 × 64 output into a 128-unit dense layer would cost roughly 6.4 M parameters, about 99.7% of such a network, on 357 training images, where GAP costs 130 and preserves the trunk exactly (Section S-I-Q).

**M3 — MobileNetV3-Small, frozen (1,154 trainable / 927,008 frozen).** The ImageNet-pretrained feature extractor [13] is frozen; a `Dropout(0.3) → Linear(576, 2)` head is trained on its globally pooled 576-dimensional output.

**M4 — EfficientNet-B0, frozen (2,562 trainable / 4,007,548 frozen).** As M3, with the EfficientNet-B0 extractor [14] and a `Dropout(0.3) → Linear(1280, 2)` head.

Both transfer models are therefore **linear probes on a fixed representation**, which is what this study's question calls for rather than a concession to it: the question is what a change in the *input distribution* does, and a probe holds the representation constant while the input changes, so any movement is attributable to the input, whereas a fine-tuned network confounds the two by re-adapting its features. Freezing also keeps M3 and M4 balanced — both train exactly one linear layer — and the compute budget within central-processing-unit (CPU) only hardware. What a probe cannot say is what fine-tuning would do, in either direction (Section IX).

### C. Augmentation

Training-partition augmentation for M2–M4 is: rotation ±12°, brightness and contrast jitter (±0.25), mild `RandomResizedCrop` (scale 0.85–1.0), and slight Gaussian blur (kernel 3, σ ∈ [0.1, 0.8]). **No horizontal or vertical flip** is used, because mirroring produces printed packaging text that cannot occur in deployment.

M1 is excluded from augmentation by design: rotation and cropping are near-invariances of a color histogram, while brightness and contrast jitter would perturb the only feature this model observes, acting as label noise rather than as the spatial-filter regularizer they are for a CNN. Section VI-F shows the asymmetry does not soften the paper's conclusion about M1.

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

and is applied identically to every partition. Three properties matter. $T$ is **label-free** — nothing in (5)–(7) references $y$ — so applying it to the external set is not an oracle. It is **deployable**: a fixed preprocessing function, not a train-time-only trick. And it is **destructive** by design, removing information a model might legitimately use, which is why its effect must be measured per architecture rather than assumed (Section VI-F).

The order in (8) requires a word, because it is easy to mistake for a designed one. It is not: resolution, then brightness, then compression was the order the operators happened to be written in, it was fixed before any of them was evaluated, and we have no theoretical argument for it. **We therefore treat (8) as one pre-specified experimental operator rather than as a proposed or optimized algorithm**, and Eq. (8) should be read as the arbitrary member of its family that we happened to run. Because two of the three operators impose an information bottleneck rather than an alignment, they do not commute, and Section VI-F measures all six orderings for exactly that reason. The consequence — that the arbitrary choice turns out to matter more than any of the three magnitudes — is a result about preprocessing, not a tuning outcome we are reporting in our own favor.

One choice is not label-free in the sense the operators are: the three axes were selected after Table 1 showed those statistics separating the pool from Split C, which is target-distribution information a practitioner would not hold. Section S-I-S re-derives the same three from the training partition alone under a threshold declared in advance. M1 bypasses the operator, an exclusion that is empirical: normalization collapses its in-distribution accuracy toward chance while recovering nothing externally (Section VI-F).

### E. Interpretability and attribution

**Grad-CAM.** For target class $c$, with $A^k$ the activation maps of the last convolutional stage,

$$\alpha^c_k = \frac{1}{HW}\sum_{i,j} \frac{\partial y^c}{\partial A^k_{ij}}, \qquad L^c_{\mathrm{Grad\text{-}CAM}} = \mathrm{ReLU}\!\left(\sum_k \alpha^c_k A^k\right) \tag{9}$$

following [15]. Maps are computed on M4 for the in-distribution audit and directly on the external images for both M3 and M4.

**An exact linear logit decomposition for M1.** For a linear model, the contribution of feature $i$ to the logit of instance $x$, relative to a background mean, is

$$\varphi_i(x) = w_i\big(\phi_i(x) - \mathbb{E}[\phi_i]\big) \tag{10}$$

so no sampling approximation is needed. We take $\mathbb{E}[\phi_i]$ over the Split B training partition and report $\overline{|\varphi_i|}$ over its test partition as global importance.

The terminology is worth fixing once. Eq. (10) coincides with the linear SHAP form of [16] under an independent-feature background, but histogram bins are not independent — the 32 bins of a channel sum to one by construction — so we do not call it a Shapley value. What (10) computes exactly, and all we use it for, is the additive decomposition of the model's logit relative to the training mean, $\sum_i \varphi_i(x) = \mathbf{w}^\top(\phi(x) - \mathbb{E}[\phi])$, an identity that holds whether or not the features are independent. We call it an **exact linear logit decomposition** throughout, and report the raw coefficients alongside it (Section S-I-P) so that the reading does not rest on the decomposition alone.

### F. Training protocol

Table S2 gives every setting in one place. Nothing in it varies by split, condition or experiment: every training run reported here uses the same values — Adam at 1 × 10⁻³ for M2–M4, selected from {1 × 10⁻³, 3 × 10⁻⁴, 1 × 10⁻⁴} on Split A train/val alone; batch 32; class-weighted cross-entropy; a 50-epoch cap with early stopping on validation loss at patience 4 and minimum improvement 1 × 10⁻³; best-validation-loss state persisted as a checkpoint; a 0.5 decision threshold; and seed 42 fixed before every run, fold and augmented extraction pass, with sensitivity at 42–46 (Table 5). M1 is fitted by `LogisticRegression(max_iter=2000, class_weight="balanced")` with neither augmentation nor the normalization operator. The ablations of Section VI-F vary the *input* operator alone. All runs are CPU-only.

### G. The provenance audit, stated as a procedure

Because the audit is what this paper offers for adoption, we state it as a procedure rather than leave it to be reconstructed from the experiments. It needs no external data, no annotation, no training run and no pixel decoding, and here it runs from a file listing in seconds. **Inputs:** a labelled image dataset, a partition free of whatever leakage the study already controls for, and the classifier family the study intends to use.

1. **Enumerate the acquisition variables the files carry** — every attribute obtainable without decoding an image: container format, encoded size, stored dimensions, and the aspect ratio they imply. Filename patterns and embedded timestamps belong here too, reported separately because they are trivially removable and their absence proves nothing.
2. **Partition exactly as the study will**, inside its own leakage-free split, so the audit inherits the grouping the models do. A different partition measures a different quantity.
3. **Fit the intended classifier to those variables alone**: one fit per variable, then one on all jointly, reporting held-out accuracy with an interval and using balanced accuracy where the classes are imbalanced. Chance is the reference, not zero.
4. **Read container format on its own.** Storage format is never a property of the photographed object, so a high score on it is close to decisive, whereas encoded size, resolution and aspect ratio mix acquisition with content; Section VI-A's negative control separates along exactly this line.
5. **Report pixel-derived proxies separately if at all** — statistics such as mean brightness require decoding and are not independent of content, so they belong in their own row, as in Table 2.
6. **Interpret against what the score licenses, not a threshold.** It establishes the *availability* of a provenance shortcut, not that any model took it, and we publish no threshold because five scorable datasets cannot support a false-positive rate.

**Outputs.** A score at chance says these features found no acquisition asymmetry — not that the dataset is clean, since a publisher who normalized the archive before release destroys the traces without touching the confound. A middling score on the ambiguous axes is a reason to investigate and may reflect a content difference. A high score on format means acquisition determines the label, and from there no in-distribution accuracy on that dataset can distinguish the intended task from provenance recognition.

**Two companion checks the audit does not replace**, each having caught something it missed on our own data: a content pass over a sample of each class (Section S-I-A), which identified the modality confound of Section III-B, and cross-source near-duplicate hashing (Section IV-B), which established that two sources treated as independent were not. Section VII-F gives the taxonomy these three checks jointly cover.

## VI. Results

All results in this section come from the deterministic, three-way-normalized production pipeline, except where a table explicitly reports a baseline condition for contrast. Complete machine-readable tables are in `paper/tables/`.

**Two tiers of evidence are reported here, and the distinction governs how each result should be weighted.** Everything in the first tier was fixed by the protocol before any of it ran. Everything in the second was developed after the external failure was observed, and Section S-I-F sets out the sense in which it is exploratory. We do not present the two as equivalent, and no claim in Sections VII–X rests on the second tier alone.

| Tier | What it covers | Where |
|---|---|---|
| **Confirmatory** (pre-specified) | The provenance audit; the Split A vs. Split B comparison and the paired leakage experiment; the baseline external evaluation of the four models on Split C | Sections VI-A, VI-B, and the baseline column of Table 4 |
| **Exploratory** (post-hoc) | The normalization itself; the selection of its three axes; the choice of its constants; the operator ordering; the resolution sweep; the attribution investigations; Split D | Sections VI-C–VI-F |

The second tier is where the strongest-looking numbers in this paper live, and it is also where Split C stops being an untouched external set: the three normalization axes were nominated *because* Table 1 showed those statistics separating the training pool from Split C, which makes Split C target-informed development data for that experiment and for nothing else (Sections V-D, VI-C, VIII). The 86% and 81% figures are therefore not clean external-validation results, and we do not report them as such. Section S-I-S re-derives the same three axes from the training partition alone, under a threshold declared in advance, which is the closest this study comes to repairing that.

### A. The capture-method confound

The strongest result in this study needs four learned parameters and no decoded pixels: a logistic regression on three header fields separates the two classes perfectly on the leakage-free partition (Table 2). This subsection builds to it.

Every one of the 510 pool filenames falls into exactly one of two patterns, and **the pattern predicts the class label with no exceptions**: 272/272 authentic files are `images*.jpg` and 238/238 counterfeit files `Screenshot*.png`. This is not an artifact of our filtering — it holds in the archive as distributed, where all 240 files in `Fake/` are `Screenshot*.png` and all 421 in `Real/` are `images*.jpg` — so any study using this dataset inherits it in full, and a classifier reading nothing but the file extension achieves **100% accuracy**. Table 1 gives what the two pipelines look like in the file, and where the external set sits beside them.

**TABLE 1.** The two acquisition pipelines in the Kaggle pool, and the external sets' position relative to both. Median short side and file size are header fields; mean brightness is the mean RGB value at 64 × 64 on a 0–1 scale, and is listed last because it requires decoding the image. Throughout this paper kB = 1000 bytes.

| Group | n | Capture pattern | Median short side (px) | Mean file size | Mean brightness |
|---|---|---|---|---|---|
| Kaggle authentic | 272 | `images*.jpg` (100%) | 223 | 6.0 kB | 0.767 |
| Kaggle counterfeit | 238 | `Screenshot*.png` (100%) | 405 | 339 kB | 0.555 |
| Split C external (authentic) | 150 | device photograph | **2448** | 1,656 kB | **0.162** |
| Split C synthetic (proxy counterfeit) | 150 | perturbed copy of the above | 2448 | 1,018 kB | 0.153 |

A two-sample *t*-test on brightness between the classes gives *t* = 17.0 on 508 degrees of freedom, *p* < 10⁻¹⁵. Table 1 makes a second point, plotted by Fig. S14: the external set does not sit *between* the two training classes on these axes but far outside both, roughly 10× higher in linear resolution and darker than even the counterfeit class. A model that had learned "bright, small, heavily compressed → authentic" would have every statistical reason to call every external photograph counterfeit — a prediction the external results are consistent with, not an observation about any model's internals, and Sections VI-E and VI-F are where it is tested.

The confound is visible in the simplest model's decision function. Of M1's 96 coefficients, 93 lie within ±0.35 of zero while the top intensity bin (248–255) of each channel carries a large negative weight (β = −2.86, −2.84, −2.95) — "many near-white pixels → authentic" — and the logit decomposition of Eq. (10) puts those three bins in the top three positions by mean |φ|, at 0.079–0.082 against 0.002 for the fourth (Section S-I-P). M1's 83.8% accuracy therefore appears driven largely by near-white pixel prevalence rather than by packaging.

**A header-only oracle shows acquisition alone suffices.** A 96-bin color histogram still reads pixel intensities and could in principle carry packaging information, so we fitted the same logistic regression to what a file listing and a header parse supply — container format, log encoded size, log short-side resolution, and the implied aspect ratio — decoding no pixel (Table 2). Mean brightness is not metadata but a **low-level acquisition proxy**, cheap yet needing the image decoded, so it sits in Table 2's last row rather than among the header rows.

**TABLE 2.** The provenance audit on the case-study pool. LR = logistic regression, fitted on each split's own training partition. Every row but the last reads only what a file listing and a header parse provide, with no pixel decoding; the last is a pixel-derived acquisition proxy and is separated for that reason. Resolution and file size enter as log₁₀. The deterministic rule is not fitted. Intervals are 95% Wilson.

| Classifier | Features | Split A test (n = 76) | Split B test (n = 74) |
|---|---|---|---|
| Deterministic rule: `.png` → counterfeit | container format | 510/510 = **1.000** [0.993, 1.000] over the whole pool | — |
| Header LR | container format | **1.000** [0.952, 1.000] | **1.000** [0.951, 1.000] |
| Header LR | encoded file size | 0.974 [0.909, 0.993] | **1.000** [0.951, 1.000] |
| Header LR | short-side resolution | 0.947 [0.872, 0.979] | 0.946 [0.869, 0.979] |
| Header LR | aspect ratio | 0.645 [0.533, 0.743] | 0.595 [0.481, 0.699] |
| Header LR | size + resolution + aspect ratio | **1.000** [0.952, 1.000] | **1.000** [0.951, 1.000] |
| Pixel-derived proxy LR | mean brightness | 0.829 [0.729, 0.897] | 0.716 [0.605, 0.806] |

Three things follow, stronger than anything the pixel-based models here establish. First, **a single scalar that is not an image classifies this dataset perfectly**: encoded file size alone reaches 74/74 on the leakage-free partition, above every trained model here including M4 (Table S3), using no pixel at all. Second, **acquisition variables alone reproduce the labels with accuracy 1.000**, three header fields doing it without even the file extension. What that licenses has to be stated exactly, because it is the most misreadable result in this paper.

> **What an audit score means.** A high audit score establishes that $A \to Y$ is predictable: a provenance shortcut is *available* in the dataset. It does not establish that any given pixel classifier took it. The audit is a **diagnostic on the dataset**, not an attribution of model behavior, and no result in this paper treats it as the latter.

The consequence needs no attribution: because provenance predicts the label perfectly here, in-distribution accuracy cannot distinguish a classifier that learned packaging semantics from one that learned provenance-associated cues, whichever it did. In-distribution evaluation on this pool is therefore uninformative about the stated task, ours as much as anyone's; what a particular model actually used is a separate question, and Section VI-E is our attempt at it. Third, **the pixel-derived proxy is the weakest candidate here, not the strongest.** Brightness alone reaches 0.716 on Split B, below resolution (0.946) and file size (1.000), despite having the largest *t*-statistic: the brightness distributions differ in mean but overlap substantially, whereas the file-size distributions barely overlap. Rank candidate confounds by fitting a classifier to each, not by *t*-statistic — it costs no more, and it is why the audit starts at the header.

**The audit on datasets other than the case study.** A screen that fires on every dataset carries no information, so the same procedure was run on six further public archives across four application areas (Table 3; Section S-I-W gives the full record). Four of the seven were scorable alongside the case study, and they separate into the three outcomes the method admits.

**TABLE 3.** The provenance audit outside the case study, summarized from Tables S18 and S20. Balanced accuracy of a logistic regression on the named metadata alone under cross-validation; chance is 0.500. Format is the one-hot container format, the axis nearest to isolating acquisition, because storage format is never a property of the photographed object. Feature sets differ between the two source tables: the four listing-audited rows supply format and encoded size, the Roboflow row adds resolution and aspect ratio, and the Kaggle row returns 1.000 under both. Three further archives returned only one class before the listing endpoint's file limit and admit no score at all; that is a property of the sampling method, not a finding about them (Section S-I-W). A pilot audit of archives chosen for accessibility, not a prevalence estimate over a defined sampling frame.

| Dataset | Area | Provenance issue | Format | All features audited | Outcome |
|---|---|---|---|---|---|
| Kaggle *Fake vs Real Medicine* [19] | Medicines (positive control) | Type A: acquisition determines the label | **1.000** | **1.000** | Detects |
| `rhythmghai/ai-vs-real-images-dataset` | Generated images | Type A, independently arising | **1.000** | **1.000** | Detects |
| `cashbowman/ai-generated-images-vs-real...` | Generated images | None these features find | 0.577 | 0.562 | Near chance |
| Roboflow *Counterfeit_med_detection* [21] | Medicines | Type B: a modality confound, acquisition traces erased by the publisher | 0.500 | 0.717 | Partially detects |
| `ishanikathuria/handwritten-signature...` | Signatures (negative control) | None; one acquisition procedure for both classes | 0.500 | 0.845 | False positive on size |

Three readings follow, and the last two bear on whether the audit is a method or a trick.

**It discriminates.** Two archives return 1.000 on format and two at or near chance. The generated-image pair is the sharper case: two datasets built for the same task by different people return 1.000 and 0.577, which is also a caution against reading the mechanism as a law.

**It has a false-negative mode, and publisher-side tidying causes it.** The Roboflow archive is confounded at least as severely as the case study — 57/57 of its counterfeit-labeled source images are advisory graphics carrying the ground-truth word in the pixels (Section III-B) — yet format returns 0.500 and the full set 0.717, because the publisher resized to 640 × 640 and re-encoded before release. A tidied dataset is *harder* to audit than a raw one, so a middling score is a reason to investigate, not a clearance.

**Its false-positive mode is on the ambiguous axes.** Genuine and forged signatures in BHSig260 are written on one paper and digitized by one procedure, so format returns exactly 0.500 while encoded size returns 0.843, most likely because forged signatures differ in stroke complexity and so in ink coverage. Encoded size, resolution and aspect ratio mix acquisition with content; container format does not. We publish no threshold: five scorable datasets cannot support a false-positive rate.

### B. In-distribution performance, and the size of the leakage effect

One definition governs what follows. "Leakage-free" here means free of **product-identity** leakage: Split B guarantees that no perceptual-hash cluster of near-duplicate photographs straddles a partition or a fold. It makes no claim about acquisition. Because every counterfeit-labeled image was produced by one capture pipeline and every authentic-labeled image by another, *no* partition of this pool can place a capture process on one side of a fold, and grouped cross-validation inherits the confound at full strength. Split B corrects one of the two problems, not both.

In-distribution, the four models reach 0.842, 0.868, 0.934 and 0.987 on the naive split and 0.838, 0.865, 0.932 and 0.919 on the leakage-free one — deltas of +0.004, +0.004, +0.002 and +0.068, three of them within half a point of zero. Six pairwise McNemar tests compare *models against each other* on one shared test partition; none is significant, and Holm–Bonferroni over the six raises the smallest adjusted *p* from 0.118 to 0.711. They do not test the Split A − Split B difference, whose two partitions hold different images and for which no paired test exists; that comparison is made properly below. The full metric set, the tests and their power analysis are Tables S3–S5 and Section S-I-H.

Two things limit what those deltas settle. First, exactly 7 of the 76 Split A test images belong to a product group also in Split A's training partition, a **direct exposure rate of 9.2%**, so at most seven predictions can be got right by recognizing a training photograph — but that bounds one channel only, since admitting a near-duplicate also changes the fitted parameters, which decide the other 69. Second, Split A and Split B do not share a test set: 230 of 510 images are assigned differently, so their difference mixes leakage with the effect of testing on different images.

A paired design separates the two. One test set is held fixed and two training sets are built around it differing in exactly one respect — whether the near-duplicate mates of the test images are admitted — with size, class balance, validation set, architecture and learning rate identical, the 30 mates balanced by class-matched substitutes (Section S-I-V). Of the 74 test images, 28 are *exposed*, which is every exposed image the pool admits; on the other 46 any difference is the indirect channel. Across five seeds, admitting the mates moves M2 by **+0.3 points [−1.9, +2.4]** (paired bootstrap; McNemar *p* = 1.000), by +0.0 [−2.9, +2.9] on the exposed subset and +0.4 [−2.2, +3.5] on the unexposed. M3 and M4 are unchanged at every seed, though both sit at ceiling (1.000 and 0.987), which leaves an effect almost no room to appear — itself a consequence of the confound, an in-distribution partition of this pool being close to trivial.

This is the paper's first substantive result. Near-duplicate leakage moves accuracy by at most 6.8 points across split designs, and by 0.3 points when it is varied alone on a fixed test set, while the external gap described next runs from 97% in-distribution accuracy to an authentic-class specificity of 6.0%.

### C. External evaluation: authentic-class specificity

Table 4 gives the central result of this paper, under the convention of Section V-A. Split C holds authentic images only, so every number in it is an **external authentic-class specificity**, and what it records is a false-positive collapse under acquisition shift — not a demonstration that counterfeit *detection* generalizes poorly, since counterfeit sensitivity, F1 and balanced accuracy under shift are measured nowhere in this study (Section III-E). The finding is that these models fail to recognize independently acquired authentic products as authentic: disqualifying for an authentication system, and narrower than "the models fail externally".

**TABLE 4.** External authentic-class specificity on 150 independently captured authentic photographs; every figure is a true-negative rate and none estimates counterfeit recall. **Both conditions come from the current deterministic pipeline at seed 42**, so the two columns differ only by the operator of Eq. (8) and the comparison is within-run; Table 5 gives both across five seeds. An earlier archived run, made before three-way normalization became the default, returned 104/150 for M3 and 5/150 for M4. That run was produced by a pipeline carrying the two defects of Section S-I-G — a hard-coded learning rate for M2 and unseeded augmented feature passes for M3 and M4, both since fixed — and Section S-I-U diagnoses the divergence and supersedes it; it is not quoted as a result anywhere in this paper. The in-distribution reference is authentic-class accuracy on each model's own Split B test partition (n = 39). The last column is the in-distribution-minus-external gap of the normalized model, Eq. (S5) of the supplement — not the effect of normalization, which is the difference between the two preceding columns. M1 bypasses the operator in the production pipeline, an exclusion decided empirically rather than a priori (Table S13). Intervals are 95% Wilson on the counts given as k/n, and quantify sampling uncertainty on a fixed trained model, not training-run variance.

| Model | In-distribution authentic accuracy (k = 39) | Split C, baseline (n = 150) | Split C, 3-way normalized (n = 150) | Generalization gap, normalized |
|---|---|---|---|---|
| M1 hist+LR | 27/39 = 0.692 [0.536, 0.814] | 0/150 = 0.000 [0.000, 0.025] | 0/150 = 0.000 [0.000, 0.025] | +0.692 |
| M2 CNN | 33/39 = 0.846 [0.703, 0.928] | 0/150 = 0.000 [0.000, 0.025] | 129/150 = **0.860** [0.795, 0.907] | **−0.014** |
| M3 MobileNetV3 | 38/39 = 0.974 [0.868, 0.995] | 100/150 = 0.667 [0.588, 0.737] | 116/150 = 0.773 [0.700, 0.833] | +0.201 |
| M4 EfficientNet-B0 | 38/39 = 0.974 [0.868, 0.995] | 9/150 = 0.060 [0.032, 0.110] | 121/150 = 0.807 [0.736, 0.862] | +0.167 |

Read the baseline column first. Two of the four models classified **zero of 150** external authentic photographs correctly, and the best in-distribution model in the study (M4, 0.987 on Split A) reached 9/150 = 6.0%. This is a near-complete inversion on the easiest possible external case — a test set holding only the class the models were most accurate on in-distribution. A model at 91.9% on Split B that recovers nine of 150 plainly authentic photographs has not learned to recognize authentic packaging; what it has learned is consistent with recognizing this dataset's photography, which Section VI-A establishes was available to it.

The normalized column carries the qualification of the tier table above. **Split C was not an untouched validation set for the normalization experiment**: its acquisition statistics nominated the three axes (Section V-D), so for that experiment alone Split C is target-informed development data and the column is exploratory in a way the baseline column, measured before any operator existed, is not. Section VI-F reports what an operator nominated from the training partition alone achieves instead, and Section VII-E what the experiment can establish.

The same models, retrained on the same images with the same seeds and hyperparameters and differing only by the label-free operator of Eq. (8), recover 86.0%, 77.3% and 80.7%. The in-distribution price at seed 42 is small — Split B accuracy moves 0.865 → 0.865 (M2), 0.946 → 0.932 (M3) and 0.905 → 0.919 (M4), one loss of 1.4 points well inside its bootstrap interval and one gain of the same size — but that describes the run of record, not the five-seed record, which is larger and signed both ways: M2 loses 3.0 points and M4 gains 3.0 (Table 5). Both forms are reported wherever this claim appears. M2's external specificity exceeds its own in-distribution accuracy, the only negative gap here, because with the shortcut suppressed its mixed-class test partition is the harder problem. M1 bypasses the operator and is unchanged at 0.000.

Two Wilson intervals are the wrong instrument for that comparison: both conditions are evaluated on the same 150 images, so it is paired. Section S-I-Z runs it as one across all five seeds, resampling images so both arms' verdicts move together: **+85.9 points [+81.7, +89.7]** for M2, **+76.0 [+69.9, +81.5]** for M4, **+0.9 [−6.9, +8.8]** for M3 (Table S23). Read unpaired, Table 4 agrees — M2's and M4's intervals do not overlap between conditions, M3's 16-image difference overlaps substantially.

Repeating both conditions at five seeds settles which movement is a finding and which is initialization (Table 5). M2 and M4 separate by 86 and 76 points against standard deviations of three to ten, the worst normalized seed far above the best baseline seed in both; M3 moves 0.715 ± 0.057 to 0.724 ± 0.047, the two sets of five interleaved. **We therefore claim no normalization benefit for M3**, as a measurement rather than a caution, and rest the headline claim on M2 and M4. Only separations of this size are read as findings anywhere in this paper: a point or two between models, orderings or seeds is inside what 74 to 150 images and five runs can resolve. Five seeds bound seed sensitivity rather than estimating it precisely, and what makes these readings safe is that each turns on a separation far larger than the quantity being estimated.

**TABLE 5.** Five-seed sensitivity analysis, seeds 42–46, mean ± sample standard deviation. Every other number in this paper comes from one run at seed 42; this table says how much of it is initialization. Split assignments, preprocessing and learning rates are fixed across seeds, so the training seed is the only thing that moves. The baseline rows are re-derivations from the current harness, not the archived run of Table 4's baseline column; the two differ for M3 and M4, and the discrepancy is recorded in Section S-I-U. Splits C and D are authentic-only, so those columns are specificities. M1 is a convex fit with a deterministic solver and no augmentation, so its accuracy is identical under every seed and it is omitted. Per-seed values are in Section S-I-U.

| Model | Condition | Split B test | Split C | Split D |
|---|---|---|---|---|
| M2 CNN | baseline | 0.854 ± 0.018 | 0.051 ± 0.103 | 0.176 ± 0.201 |
| M2 CNN | normalized | 0.824 ± 0.042 | **0.909 ± 0.038** | 0.627 ± 0.135 |
| M3 MobileNetV3 | baseline | 0.941 ± 0.007 | 0.715 ± 0.057 | 0.644 ± 0.043 |
| M3 MobileNetV3 | normalized | 0.938 ± 0.007 | 0.724 ± 0.047 | 0.685 ± 0.044 |
| M4 EfficientNet-B0 | baseline | 0.905 ± 0.000 | 0.100 ± 0.026 | 0.240 ± 0.048 |
| M4 EfficientNet-B0 | normalized | 0.935 ± 0.011 | **0.860 ± 0.034** | 0.878 ± 0.031 |

Seed 42 is not a central draw, and not in one direction: its Split C value is the lowest of five for M2 and M4 and the highest for M3, so the single-run figures understate the correction where it works and flatter it where it does not. We report the spread rather than restate the paper around the means, seed 42 having been fixed before any of this existed and every artifact of record produced under it.

### D. A second capture shift, and what it costs the headline

Section VII-C warns that a shortcut coinciding with one external distribution is indistinguishable from robustness until a second, differently constructed evaluation disagrees. Split D (Section III-F) makes that warning testable. All four models were evaluated from their persisted Split B checkpoints (Section S-I-G), so the model tested is provably the one that produced the in-distribution numbers; Table 6 gives the result.

**TABLE 6.** The same corrected models on two external distributions. Both authentic-only; accuracy is the fraction correctly called authentic, with 95% Wilson intervals. The two sets cover the same packages under different capture conditions but cannot be aligned image by image (Section III-F), so the columns are compared as independent proportions.

| Model | Split C (n = 150) | Split D (n = 149) | Change (percentage points) |
|---|---|---|---|
| M1 hist+LR | 0/150 = 0.000 [0.000, 0.025] | 0/149 = 0.000 [0.000, 0.025] | 0.0 |
| M2 CNN | 129/150 = **0.860** [0.795, 0.907] | 69/149 = **0.463** [0.385, 0.543] | **−39.7** |
| M3 MobileNetV3 | 116/150 = 0.773 [0.700, 0.833] | 108/149 = 0.725 [0.648, 0.790] | −4.9 |
| M4 EfficientNet-B0 | 121/150 = 0.807 [0.736, 0.862] | 124/149 = 0.832 [0.764, 0.884] | +2.6 |

Two of the three findings narrow claims made elsewhere in this paper; we state those first.

**The correction does not transfer uniformly across capture shifts, and the model it fails for is the one we had called the best generalizer.** M2 loses 39.7 points between the two external sets, from 0.860 — the highest in the study — to 0.463, marginally below the 0.500 a coin flip would return, with intervals nowhere near overlapping. Read that with Table 5: M2's Split D specificity is the most seed-sensitive quantity in the study (0.627 ± 0.135) and the run of record is the lowest of five, so the mean drop is 28 points rather than 39.7. The direction, and the contrast with the backbones' −3.9 and +1.8 at five seeds, hold at every seed. One external distribution cannot distinguish a general repair from one fitting Split C in particular; the second says it was substantially the latter.

**The two pretrained backbones hold their specificity across the shift.** M3 moves −4.9 points and M4 +2.6, both with comfortably overlapping intervals, so neither change is distinguishable from sampling noise. M4 is the most stable model across both external sets (0.807 and 0.832) and M3 the next (0.773 and 0.725). What that establishes is bounded by what separates the two sets: they come from one archive, cover the same packages and share one backdrop, and differ in capture device and lighting protocol. The backbones are therefore shown to be **stable across the device and lighting shift these two capture conditions represent**, and not to generalize across acquisition.

We do not describe this as the backbones generalizing. Section VI-E finds both taking their evidence for "authentic" from the surround, while Split C and Split D share one dark backdrop — and a model applying a backdrop rule would hold its specificity across exactly this shift. **Split D tests the capture-pipeline confound and leaves the backdrop cue untouched.** The net effect is a narrowing: the correction remains stable for frozen backbones across the device and lighting shift two capture conditions from one archive represent, and fails for a small from-scratch CNN on the second, so "normalization recovers 81–86% external specificity" is a statement about one distribution (Section S-II).

### E. What the surviving accuracy rests on

Specificity that survives a capture shift still has to be shown to rest on the intended cue, and here it is not. Two attribution methods were run on the corrected models and Section S-I-J reports both in full. They differ in evidential weight, and we weight them accordingly.

**The occlusion analysis is the primary evidence.** It is annotation-free, runs over every external image rather than a sample, produces a continuous statistic — the fraction of decision-relevant mass falling in a border ring, against a 0.642 uniform reference — and reproduces each model's Split C specificity of record before reporting anything. It finds M3 taking its evidence for "authentic" from the photographic surround (border mass 0.760, 96 of 116 images above the uniform reference) and both backbones taking their evidence for "counterfeit" from the product on the images they get wrong (0.856 and 0.803). For M4's correct external answers it returns 0.614 [0.585, 0.643], indistinguishable from uniform.

**The Grad-CAM categorization is corroborating evidence only, and we do not rest anything on it alone.** It covers the 62 maps this study produced, and each was placed in one of two categories by a single annotator with no second rater and no scoring rubric written in advance, so "background-driven" against "product-driven" is not a reproducible measurement (Section VIII). It agrees with the occlusion analysis on three of the four groups above and disagrees on the fourth, reading M4's correct external answers as surround-driven where occlusion cannot distinguish them from uniform. Where the two disagree we report the occlusion result and record the disagreement.

Occlusion asks a local question — how far does hiding *this patch* move the score — which a decision spread over a large region answers weakly wherever that region is. The M4 result is therefore uninformative rather than negative, and a global test settles it.

**Region substitution identifies the region, and it is the surround for both backbones.** One region of each external image's production-pipeline input is overwritten before the forward pass: a centre square covering half the frame, or its complement. The two are area-matched to within half a point, which is what makes the comparison readable, since substituting a region is itself a distribution shift and only the asymmetry between the two directions is interpretable. Two fills are used because they fail differently: the ImageNet channel mean, flat, and Gaussian noise, high-entropy. The intact condition reproduces each model's specificity of record before anything is reported (Table 7).

**TABLE 7.** Region substitution on both external sets. Each cell is authentic-class specificity after overwriting one region of the model's input; the intact row is the unmodified production pipeline and reproduces the value of record exactly. "Outer" is everything outside a centre square covering half the frame and "inner" is the square itself, so the two are area-matched (0.5025 against 0.4975) and the asymmetry is not an artifact of how much was destroyed. The last two rows use the occlusion analysis's 0.642 border ring and 0.161 centre box, which are *not* area-matched, for continuity with it. Both sets are authentic-only, so every figure is a specificity; parenthesized values are changes from intact, in points.

| Region overwritten | Fill | M3, Split C | M3, Split D | M4, Split C | M4, Split D |
|---|---|---|---|---|---|
| — (intact) | — | 0.773 | 0.725 | 0.807 | 0.832 |
| Outer half-frame | mean | **0.280** (−49.3) | **0.275** (−45.0) | **0.487** (−32.0) | **0.611** (−22.2) |
| Inner half-frame | mean | 0.800 (+2.7) | 0.738 (+1.3) | 0.807 (0.0) | 0.859 (+2.7) |
| Outer half-frame | noise | **0.273** (−50.0) | 0.483 (−24.2) | **0.373** (−43.3) | 0.530 (−30.2) |
| Inner half-frame | noise | 0.713 (−6.0) | 0.785 (+6.0) | 0.853 (+4.7) | 0.906 (+7.4) |
| Border ring (0.642) | mean | 0.233 (−54.0) | 0.201 (−52.4) | 0.260 (−54.7) | 0.396 (−43.6) |
| Centre box (0.161) | mean | 0.887 (+11.3) | 0.852 (+12.8) | 0.853 (+4.7) | 0.920 (+8.7) |

The result holds in all eight model-by-split-by-fill combinations and is large in every one. **Destroying the surround costs 22 to 50 points of external specificity; destroying an area-matched centre region costs nothing and more often helps**, and removing the occlusion analysis's small centre box raises specificity by 5 to 13 points. Whatever these models read in order to call an external photograph authentic lies outside the middle of the frame, and the middle of the frame is where the packaging is. This settles M4, the case occlusion could not resolve, in the same direction as M3 and in Grad-CAM's; we record that reversal rather than quietly adopting it, and note that the local and global tests asked different questions rather than answering one differently.

Three limits. Substitution identifies the *region* a decision needs, not the feature inside it — the outer region holds the dark backdrop but also whatever of the carton extends past the centre square, and this design does not separate them. It speaks to the external sets only. And each condition is a single deterministic pass, so the small positive deltas on the inner rows are not a benefit; what carries the finding is the sign and size of the outer rows, an order of magnitude larger than anything else in the table.

**The reading we take forward** is that neither corrected backbone is shown to recognize packaging and both depend on the photographic surround, which both external sets hold fixed. We withdraw the earlier reading that the two behave differently on their correct answers.

Two consequences follow. Split C and Split D are the same products on one dark backdrop, so neither disturbs the cue identified here: both backbones holding up across that shift is what a surround-dependent rule predicts, not evidence of robustness. And we make no claim about what the normalized models see in aggregate, because a 128 px bottleneck degrades activation-based attribution as much as it degrades the input (Section S-I-J). **The models corrected by Eq. (8) have not stopped depending on acquisition; both now depend on a different acquisition-linked cue — the photographic surround — which the audit of Section VI-A does not test and which both external sets hold constant.** That is the finding Section VII-E develops.

One further conclusion cautions against a common practice. **A visually convincing, product-centered Grad-CAM map is not evidence that a model learned the intended task.** That rests on the un-normalized model, whose input is unaltered and whose attribution is not in question: it is strongly product-centered, 0.563 of its mass in a centre box covering 0.161 of the frame, and it classifies almost no external image correctly (Table 4). Across the two conditions, spatial concentration of attribution *anti-correlates* with external specificity.

### F. Ablating the correction

Sections S-I-N to S-I-X ablate the correction per axis, per architecture, per constant and per composition order. Five conclusions carry into the discussion.

**The three axes are complementary, not redundant.** Individually they take M4's external specificity from 5–9% to 22.0%, 27.3% and 12.7%, and jointly to 78.0% in the same run (Table S11) — what one expects if the confound is a *capture pipeline* expressed through several correlated statistics rather than one. A fourth plausible axis, gray-world white balance, recovers 0.067 alone and costs M4 4.0 points added to the production operator; that was the evidence on which earlier versions of this paper ruled it out, and it was M4's evidence only.

**A practitioner using no target information would have done at least as well.** Section S-I-S re-derives the three axes inside the Split B training partition alone, under a threshold fixed in advance, which removes the target dependency in principle. It does not report what the rule *yields*, because the operator it nominates is not the one we report: it also fires, marginally, on gray-world colour balance. Table S27 runs that nominated operator end to end for all three models and both external sets; nothing in its construction consulted an external image.

**The recovery is therefore not an artifact of having seen the external set.** The operator selected with no target information raises external specificity by 6.7 points for M2 and 4.7 for M3 and lowers it by 4.0 for M4, averaging 0.842 against the reported operator's 0.818: a practitioner who never saw Split C would have measured the same effect, and slightly more of it. The in-distribution decoupling reappears here too — M2 loses 8.1 points of Split B accuracy while gaining 6.7 externally, M4 gains 1.4 while losing 4.0 — so choosing between these two operators the ordinary way would have chosen wrongly for both, the same inversion the ordering permutation produces, reached by varying something else.

**The effect is architecture-dependent, and the constants are conservative rather than tuned.** The correction does nothing for the color-histogram baseline, whose in-distribution accuracy instead collapses from 0.838 to 0.541 (Table S13). Sweeping all three constants moves external specificity across 0.480–0.873 with no knife edge, and 96 px would beat the 128 px we report (Table S14); we have not re-tuned, because choosing preprocessing by its external score is the target-distribution leakage Section VIII warns about.

**And composition order matters more than any of the three magnitudes.** Eq. (8) fixes one order — resolution, then brightness, then compression — which was the order the operators were written in, fixed before evaluation and never theoretically justified (Section V-D), and two of the three operators impose an information bottleneck rather than an alignment, so there is no reason to expect them to commute. Running all 3! = 6 orderings at the production constants on M4 inside one execution (Table S21) separates them along the axis the mechanism predicts: the three applying the JPEG bottleneck *after* the resolution cap score 0.820, 0.847 and 0.880 externally, the three applying it before score 0.380, 0.467 and 0.540, and the groups are 28 points apart with no overlap. Compressing at native resolution then downsampling largely undoes the compression, because the resampling filter averages over the quantization artifacts the bottleneck exists to impose.

Two consequences bear on how any such pipeline should be reported. **In-distribution ranking is not merely uninformative here; it is inverted** — the ordering with the highest Split B accuracy of all six (brightness, compression, resolution, at 0.946) has the lowest external accuracy of all six, 0.380, so a practitioner selecting the order the ordinary way would have chosen the worst of six while watching a 2.7-point in-distribution spread conceal a 50-point external one. And **the reported order is again conservative**: resolution, compression, brightness beats production on both axes (0.880 against 0.820 externally, 0.932 against 0.919 in-distribution), and we have not re-run the paper around it, for the reason just given. Composition order is normally left implicit in a preprocessing description; on this evidence it deserves the treatment of a hyperparameter — reported, and not chosen in-distribution.

## VII. Discussion

### A. What the reported accuracies on this dataset actually measure

Everything an in-distribution evaluation on this dataset can measure is available without looking at the packaging: three header fields reach 100% on the leakage-free partition, container format alone is correct on all 510 images, and M1's 83.8% rests on a brightness proxy, falling to 54.1% once brightness is standardized. This does not imply prior work here is careless. It indicates a defect no in-distribution measure surfaces — not stratification, cross-validation, bootstrap intervals or near-duplicate grouping. Two checks do surface it, and neither is an accuracy: the metadata audit of Section VI-A, and evaluation on data someone else acquired.

### B. Why the leakage effect was smaller than the confound

We expected image-level leakage to dominate, because that is what the surrounding methodological literature emphasizes [11]. It did not: at most 6.8 points across split designs and 0.3 [−1.9, +2.4] when varied alone, against an external gap of more than 90 points that coincides with the acquisition confound and that intervening on the acquisition axes largely closes. The generalizable point concerns the ordering of audits: both checks are cheap, only the leakage one is routine, and here the other identified a substantially larger effect — an argument for running both, not for replacing one with the other.

### C. Why the models behave differently

External behavior is not ordered by capacity but by *what kind of access* each model has to the confound: M1's feature space *is* the shortcut, so correction unlocks nothing; M2 reaches the same statistics through learned filters and recovers strongly once they are suppressed; and the two backbones inherit ImageNet invariances that afford partial protection, degrading severely at baseline without collapsing to zero. Section S-I-Q develops this. Since Section VI-E leaves neither backbone shown to recognize packaging, access to the confound and what the evaluation happens to vary are the axes that explain these rows; capacity is not.

### D. Practical implications

**For dataset publishers.** Document the acquisition procedure for each class and state whether both came from the same one — a single sentence that would have made this study's central finding visible without any of its analysis. Publishing a raw archive rather than a normalized one also preserves the traces a cheap audit reads.

**For reviewers.** Ask how each class was obtained, and whether the model was evaluated on data the authors did not collect. On this dataset either question would have been decisive.

### E. Eliminating one provenance signal exposes another

The normalization of Eq. (8) does what it was designed to do: label-free, under 17 ms per image, and worth 80.7 to 86.0 points of external authentic-class specificity for two of the three models it is applied to — M3's apparent gain lies inside seed variance. Its in-distribution cost should be quoted with its scope: **at seed 42, the run of record, normalization changed Split B accuracy by no more than 1.4 points in either direction; across the five seeds of Table 5 the changes were −3.0 points for M2 and +3.0 for M4.** We nevertheless report the operator as an instrument and not a remedy, and four results already given are the reason.

*The recovered specificity rests on the photographic surround rather than the packaging* (Section VI-E): overwriting the outer half of the frame costs both backbones 22 to 50 points, while overwriting an area-matched centre region costs neither anything, and both external sets share one dark backdrop. *The exchange is not stable*: M2, the best corrected model on Split C, falls to 0.463 on a second capture of the same products and to 0.627 ± 0.135 across five seeds, which a correction that had truly removed the dependence on acquisition would not do. *The pipeline is under-determined by its own description*: permuting operator order alone moves external specificity 50 points under a 2.7-point in-distribution range with the ranking inverted, so a detail methods sections leave implicit decides most of the result and the usual way of settling it picks the worst option. *Removing more information keeps helping*: tightening the resolution bottleneck from 128 px to 96 px raises external specificity to 0.873, which is what a coarse distribution match predicts and not what restored reading of printed detail predicts.

None of this makes the operator useless; it fixes what it is for. One objection has to be met first: the axes were chosen because Table 1 showed them separating the pool from Split C, so intervening on them might seem guaranteed to help. It is not — a bottleneck that removed the discrepancy while destroying the signal would have driven in-distribution accuracy to chance, as it does for M1 (Table S13). What the experiment supports is therefore an *interventional* claim about three named statistics and nothing wider: removing the discrepancy on resolution, brightness and compression recovers 81 to 86 of the roughly 94 points lost. Two things it does not establish should be said in the same breath. It does not identify *which* of the three, or what within them, the models were responding to, since the axes are correlated and were removed together. And it is not evidence that the corrected models learned to recognize packaging — Section VI-E indicates the opposite for M3.

The conclusion we would defend is accordingly not that a preprocessing solution was developed. It is the narrower and, we think, more useful one: **eliminating one provenance signal can expose another, so a correction is itself dataset construction and is owed the same audit as a dataset.** The evidence is measured rather than argued. The audit of Section VI-A named three acquisition statistics and Eq. (8) removed them; region substitution then shows that what the corrected models read in order to call an external photograph authentic lies outside the middle of the frame, for both backbones and on both external sets, and the middle of the frame is where the packaging is (Table 7). The surround is an acquisition property — backdrop, staging and lighting are chosen by whoever took the photograph, not by the manufacturer — and one the audit does not test, because it leaves no trace in a file header. A practitioner who ran the audit, applied the correction and reported the resulting external number would have reported a real improvement produced by a mechanism they had not audited.

### F. A taxonomy of provenance defects, and what detects each

"Provenance confound" is not one defect but a small family, each needing a different check, and the datasets audited here failed in different ways. **Type A** is the acquisition-statistic confound this paper is mostly about (the Kaggle pool, 1.000). **Type B** is a content or modality confound, on which metadata may be silent (the Roboflow archive, 57/57 advisory graphics against 0.717). **Type C** is one reintroduced when a *derived* set is drawn from a differently-acquired part of a clean source, which is how our own first synthetic proxy failed before use. **Type D** is a shipped split whose partitions do not partition. **Type E** is the audit's false-positive mode (the signature corpus, format 0.500 against size 0.843). Section S-I-T gives each its detector, its cost when undetected and its repair, and the two lessons cutting across them: publisher-side tidying suppresses the symptom rather than the disease, and the audit's output is not a verdict, since establishing that the separating statistic is an acquisition artifact rather than a property of the objects is a second step.

### G. What would falsify the general claim

The claim of Section I-A is a causal mechanism — asymmetric class availability can create class-conditional acquisition differences that confound the intended task — and we state what would count against it. Datasets whose scarce class was obtained by the same procedure as the abundant one should show no Type A confound; [3], which photographed both classes on one Raspberry Pi rig, is the one study in Table S26 plausibly meeting that condition, and it also reports the lowest accuracy there — a single observation across heterogeneous studies, suggestive and not evidence. Conversely, a survey finding the audit firing no more often on separately-sourced collections than on jointly-sourced ones would refute the mechanism. That survey is the natural next study and we have not performed it.

## VIII. Limitations

Table 8 separates what this study demonstrates from what it hypothesizes or leaves unmeasured; the paragraphs after it state each limitation in turn, and Section S-II gives the evidence for and against each. The list is complete but compressed.

**TABLE 8.** Evidence status of the claims in this paper, on the three levels set out in Section I-A. "Demonstrated" means measured here on the data named; "supported" means consistent with evidence reported here or elsewhere but not measured as a claim in its own right; "not established" means the paper argues for it without measuring it; "not measured" means the quantity was never estimated at all.

| Claim | Status | Where |
|---|---|---|
| The case-study dataset is provenance-confounded | Demonstrated: container format predicts the label on 510/510 images | Section VI-A |
| Acquisition variables alone reproduce its labels | Demonstrated: 1.000 on the leakage-free partition, no pixels decoded | Table 2 |
| In-distribution validation does not surface the confound | Demonstrated on this dataset: stratification, grouped cross-validation, bootstrap intervals and near-duplicate grouping all pass | Sections VI-A, VI-B |
| Near-duplicate leakage is the smaller effect here | Demonstrated: +0.3 points [−1.9, +2.4] on a fixed test set | Section VI-B |
| External acquisition shift exposes the failure | Demonstrated for authentic-class specificity: 97.4% in-distribution against 6.0% externally | Table 4 |
| Normalization removes much of the acquisition signal | Demonstrated for M2 and M4; not demonstrated for M3 | Tables 4 and 5 |
| The corrected models recognize packaging | Demonstrated against: overwriting the centre of the frame costs neither backbone anything | Table 7 |
| The corrected models depend on the photographic surround | Demonstrated on both external sets: overwriting the outer half costs 22–50 points | Table 7 |
| Correcting one provenance signal can expose another | Demonstrated on this dataset: the corrected models' recovered specificity localizes to the photographic surround, an acquisition property the audit does not test | Table 7, Section VII-E |
| The corrected models generalize across acquisition | Not established: both external sets come from one archive and share one backdrop, so only a device and lighting shift was tested | Sections III-F, VI-D |
| Counterfeit recall under acquisition shift | Not measured: both external sets are authentic-only | Section III-E |
| Asymmetric sourcing produces this confound in general | Not established: a mechanism with a stated falsifier | Section VII-G |
| How often the confound occurs across image datasets | Not established: seven datasets audited, no sampling frame | Section S-I-W |

**The external evaluation is authentic-only**, so every external number is a specificity; the synthetic proxy is a corruption-robustness test in the spirit of ImageNet-C [12], never a recall measurement. Counterfeit sensitivity, counterfeit F1 and balanced accuracy under acquisition shift, and end-to-end authentication performance, are **not measured anywhere in this study**. A degenerate classifier calling every image counterfeit would score 0.000 here and 1.000 on counterfeit recall, and nothing in our external data separates such a model from one applying a real decision rule at a shifted operating point. What the external sets establish is narrow: **these models fail to recognize independently acquired authentic products as authentic** — disqualifying for deployment, but not evidence that the counterfeit side survives the same shift.

**Both external sets share one backdrop.** They vary device and lighting on the same products, so the surround cue Section VI-E identifies is untested — the study's most consequential gap, and it qualifies every claim that the correction "holds" across a capture shift.

**"Leakage-free" means near-duplicate leakage only**, at Hamming distance ≤ 8 (Section S-I-Y). No partition of this pool can decorrelate acquisition, because the counterfeit class exists in exactly one capture pipeline; cross-validation across sources fails for the same reason.

**The correction is a preprocessing bottleneck, not a domain-adaptation method, and is not compared against one.** Eq. (8) is a *zero-target-sample baseline*; anyone holding even unlabeled target images should benchmark representation-level alignment against it and expect to win. The margin is unmeasured because every such method consumes target data, which would forfeit Split C as an external evaluation.

**The normalization axes were chosen with knowledge of the external set**, making Split C target-informed development data for that one experiment. Two results bound the cost: the operator consumes no target data at inference, and the train-only rule of Section S-I-S nominates the same axes from the training partition alone, with the operator it nominates recovering at least as much external specificity for two of three models (Table S27). That answers the objection on this dataset and not in general, since no training-set procedure can nominate an axis confounded only in deployment.

**The generality claim is a mechanism with a stated test, not a measured rate**, resting on seven audited datasets (Section S-I-W) and one convergent report [30]; Section IX names the survey that would measure it.

**Statistical power is thin throughout.** Test partitions hold 74–76 images, every pairwise comparison is underpowered, and the ablations and region substitutions are single executions, so a difference of a point or two should not be read as one. Table 5 repeats the production and baseline conditions at five seeds; the ablations' own seed variance is unmeasured.

**Both transfer models are frozen backbones**, which Section V-B argues is the right instrument and which CPU-only hardware also required: **nothing here measures a fine-tuned network** (Section IX).

**The Grad-CAM categorization rests on 62 maps scored by a single annotator**, with no inter-rater agreement and no rubric fixed in advance, so it is not a reproducible measurement and Section VI-E rests on the two annotation-free analyses instead. **Region substitution establishes which region a decision requires, not which feature inside it** — the outer region holds the dark backdrop and also whatever of the carton extends past the centre square — and it speaks to the external sets only.

**Every number reported here comes from the current deterministic pipeline and its persisted checkpoints**, with two superseded measurements kept as an audit trail rather than reported: an earlier M4 Split B accuracy of 0.946, unexplained once the checkpointed pipeline deterministically produced 0.919, and an archived pre-normalization external run returning 104/150 for M3 and 5/150 for M4 where the current harness returns 100/150 and 9/150. The second divergence is traced to the two defects of Section S-I-G by comparing per-epoch trajectories, which separate along model class exactly as those defects predict (Section S-I-U). Both runs' logs are committed and neither is quoted as a result. The limitation is that two historical measurements cannot be re-executed, not that any reported figure is in doubt.

## IX. Future Work

**Acquire an external set that varies the photographic setting, and one that is counterfeit-labeled.** These are the two evaluations this study most needs and could not build. Both external sets share one backdrop, so neither disturbs the surround cue of Section VI-E, and photographs against varied surfaces would test it directly at a fraction of the cost. The counterfeit-labeled set would change most; its requirements are specific — independently photographed, verified by the pHash procedure of Section IV-B, and with acquisition balanced across classes so it does not import the confound it exists to test.

**Build a training set with acquisition balanced across classes.** The confound cannot be filtered away, so the durable fix is at collection time: several independent photography setups, each contributing both classes.

**Fine-tune the backbones — the highest-priority item for anyone with a GPU.** No result here describes a fine-tuned network, and **the frozen-backbone numbers bound it in neither direction.** Adaptable features may discard the confound once the head can no longer profit from it, or the extra capacity may specialize onto residual acquisition artifacts more aggressively than a frozen trunk — in which case fine-tuning would worsen external specificity while improving every in-distribution number, which Section VI-F's inversion suggests would be invisible to anyone evaluating in-distribution.

**Survey the mechanism across application areas.** The most valuable extension is a measurement, not another model: a survey with a defined sampling frame, a pre-registered scoring rule and enumeration rather than listing-order sampling would convert the central claim from a motivated hypothesis into a measured prevalence, and needs no training runs.

**Test further acquisition axes, and separate the surround from the product.** Sensor noise and staging conventions remain untested, and any new axis should be swept for composition position, not only for inclusion. The most valuable single addition is a content-aware attribution measure — mass inside an annotated product box rather than a fixed geometric region — which would separate the two things the outer region of Table 7 confounds, the backdrop and the part of the carton that extends past the centre square. It is implemented and committed, and needs an annotation pass using rotated boxes. Photographs of the same products against varied surfaces would test the same question from the data side.

## X. Conclusion

We set out to measure how much of a reported accuracy on a small public counterfeit-medicine dataset survives methodological correction, expecting leakage to be the mechanism at issue. It accounted for very little: at most 6.8 points across split designs, and 0.3 points [−1.9, +2.4] when varied alone on a fixed test set.

Where a binary image task asks whether something is genuine, the inauthentic class is often harder to obtain and liable to be obtained differently; where it is, the label can come to predict the acquisition process, which is easier to learn than the semantics and which no partition of the same pool can expose. Stratification, grouped cross-validation, bootstrap intervals and a near-duplicate-grouped split all failed to surface it here, where every counterfeit-labeled file is a screen capture and every authentic-labeled file a downloaded photograph across all 510 images, and three header fields with no decoded pixels score 100% on the leakage-free partition. In-distribution accuracy on this dataset therefore cannot distinguish packaging authentication from provenance recognition.

The consequence is severe. On 150 authentic photographs from an independent source, two of four models were correct on zero images and the best in-distribution model on nine of 150, while scoring 97.4% on the authentic class of its own test partition. A label-free three-stage normalization raises external *authentic-class specificity* to 86.0% and 80.7% for two of the three, costing no more than 1.4 points in-distribution at seed 42 and −3.0 to +3.0 across five seeds — and that is not the repair it looks like. Rephotographing the same packages on different hardware drops the from-scratch CNN to 0.627 ± 0.135 while the frozen backbones stay stable across that device and lighting shift; permuting only the operator order moves external specificity from 0.380 to 0.880 under a 2.7-point in-distribution range with the ranking inverted, so a practitioner tuning this preprocessing the ordinary way would have chosen the worst of six; and overwriting the outer half of the frame costs both corrected backbones 22 to 50 points while overwriting an area-matched centre region costs them nothing, which puts their "authentic" verdicts on the photographic surround rather than the packaging. What the correction measures is how much of the external failure the three acquisition axes account for. It is not a remedy, for the paper's most transferable reason: **eliminating one provenance signal can expose another**, so removing a confound from the input is itself dataset construction and needs auditing on the same terms.

Gaps of 16 to 20 points remain for both transfer models, counterfeit recall under acquisition shift is untested against real counterfeits, and none of these models should be deployed.

The methodological claim we would most like carried forward is cheap to act on. Before training anything, fit the classifier you intend to use to acquisition metadata alone — format, encoded size, resolution, aspect ratio — under your own leakage-free split, and report the number. It is a diagnostic on the dataset: it tells you whether a provenance shortcut is *available*, not whether your model takes it. But where it is high, no in-distribution accuracy on that dataset can distinguish the two. Here it is 1.000.

Two qualifications keep that recommendation honest. The audit is necessary but not sufficient: on a second pharmaceutical dataset it returned 0.717 while that dataset was confounded at least as badly, its publisher having normalized the acquisition traces away without removing the confound. And it says nothing about whether a model generalizes; only data someone else acquired does that. That the same signature is documented independently in generated-image detection [30], and appears in a third archive in our own pilot audit, is what a structural cause predicts — a mechanism we would expect wherever a scarce class must be manufactured or harvested separately from an abundant one, and not a rate we have measured.

## Acknowledgment

This work was carried out on a single consumer laptop, and the CPU-only constraint that shapes several of this paper's design decisions follows from that. We thank the maintainers of the three public datasets used here [19], [20], [21]. The Mendeley and Roboflow datasets are distributed under CC BY 4.0; the Kaggle dataset carries no license, so it is attributed to its uploader, nothing from it is redistributed, and readers reproducing the pool must obtain it from the original listing.

This paper is critical of the construction of a dataset whose uploader made it freely available and made no research claim about it. That criticism is directed at a property of the artifact and at the practice of adopting such artifacts unaudited; it is not directed at the uploader, and nothing here suggests bad faith. The same applies to the prior studies of Section II-F, whose reported accuracies we do not dispute and have not re-derived.

**Generative-AI disclosure.** This manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic, accessed through the Claude Code command-line interface over the course of the project; the specific model version varied across that period and is not recorded per session. Its use covered drafting and revising the text of every section, writing and debugging the analysis and figure-generation code, and identifying several defects in earlier versions of the pipeline that are disclosed in Section S-I-G. All experimental design decisions, all interpretations, and the decision to report each negative and superseded result rather than remove it are the author's. Every number reported here is produced by committed code from committed data and was verified by re-execution, and no result, citation or reference was generated by a language model without verification against a primary source. The author takes full responsibility for the content.

## Ethics, Conflicts of Interest, and Data Provenance

**Human and animal subjects.** This study involves neither. All images are photographs of pharmaceutical packaging from public archives; none depicts an identifiable person, and no personal or patient data was accessed.

**Data provenance and permissions.** Every image originates from a third-party public archive, used within its stated terms: Mendeley Data and Roboflow under CC BY 4.0 with attribution, and the Kaggle archive under no stated license, from which nothing is redistributed. No data was scraped or purchased.

**Intended use and misuse.** No model examined here is fit to authenticate medicine, and a falsely reassuring authentication tool is more dangerous than no tool.

**Conflicts of interest.** The author declares none, has no affiliation with the maintainers of any dataset examined here, and no commercial interest in any authentication product.

**Funding.** This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Generative-AI disclosure.** Stated in full in the Acknowledgment, as IEEE Access directs.

---

## Data and Code Availability

**Repository.** All code and derived artifacts are at `https://github.com/sophiezla/counterfeit-drug`, archived at the concept DOI **10.5281/zenodo.21936720**, which resolves to the most recent release. The release accompanying this manuscript is **v1.3.1**, archived at doi:10.5281/zenodo.22239515, and it is the exact state of the code that produced every number reported here; `README.md` and `CITATION.cff` name it, and the earlier releases they list are marked superseded. It holds the data pipeline, the four model implementations, every analysis and figure script, the per-image statistics and split assignments, the persisted checkpoints, and the sources of this manuscript and its supplement.

It deliberately contains **no images**: the Kaggle archive carries no license grant, so only derived per-image statistics, split assignments and filenames are redistributed. Grad-CAM overlays and the manual-review contact sheets are excluded for the same reason, and are regenerated by committed scripts from a reader's own copy of the archives.

Six analysis scripts read only committed artifacts, need no image data and no training, and reproduce Table 2, Tables S18, S20 and S22, the direct exposure count and the external intervals in seconds — covering the paper's two central quantitative claims without requiring a reader to obtain the images or run a model. Section S-V names them.

## References

This list is shared with the supplementary material, which cites it by the same numbers; references [17], [18], [22] and [24] are cited there rather than here.

> **Reference verification status.** Every reference has been verified against a primary source: full author lists, venues, volume/issue and DOIs were read from the publisher or indexed record rather than from an aggregator page or from recollection. Where a detail could not be confirmed it is omitted rather than guessed, and said so. Two carried-forward notes for the reviewer audit: reference [11] is a medRxiv preprint and is the sole citation for the patient-level-segregation argument, disclosed and scoped to that argument alone; reference [31] is cited only for what its abstract states, because the published full text is paywalled.


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
