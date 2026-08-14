# Asymmetric Class Sourcing Creates Provenance Confounds in Authenticity-Classification Image Datasets: Detection, Cost, and Partial Repair

**SOPHIE ZHU**<sup>1</sup>

<sup>1</sup>Mira Costa High School, Manhattan Beach, CA 90266 USA (e-mail: sophiezhu2028@gmail.com)

Corresponding author: Sophie Zhu (e-mail: sophiezhu2028@gmail.com).

This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors. The manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic; see the disclosure in the Ethics section.

---

**ABSTRACT** In binary image tasks that ask whether an object is genuine, the inauthentic class is usually scarcer than the authentic one, so it is obtained differently: screen-captured, scraped, edited, or generated. The label then predicts the acquisition process rather than the property of interest, and no in-distribution evaluation can expose this: every held-out partition inherits the confound in the same proportion. We call this class-conditional provenance confounding. In a public counterfeit-medicine dataset every counterfeit-labeled file is a PNG screen capture and every authentic-labeled file a JPEG photograph, without exception, and the shipped training folder is a superset of its own test folder. A logistic regression on three acquisition scalars and no pixels reaches 100% on a leakage-free partition, bounding what acquisition alone can explain. Across four model families, correcting the split protocol changes in-distribution accuracy by at most 6.8 points, whereas external validation on 150 independent photographs drops the strongest model from 97.4% to 3.3%. A label-free normalization of resolution, brightness and compression restores 77–86% external accuracy for three of four models at negligible in-distribution cost; a second capture shift shows the repair holds for pretrained backbones but not for a small network trained from scratch, which falls from 86% to 46%. Permuting only their order moves external accuracy 50 points and in-distribution accuracy 3, ranking the worst pipeline highest. We propose a provenance audit — fitting the intended classifier to acquisition metadata alone — as a cheap pre-training screen, run it from public listings across four application areas, and report where it misfires.

**INDEX TERMS** Data leakage, dataset bias, domain generalization, external validation, hidden stratification, image classification, provenance confounding, shortcut learning.

---

## I. Introduction

Substandard and falsified medical products are a persistent global health problem, concentrated in low- and middle-income countries and in unregulated online supply chains [1], [2]. Because a large fraction of falsified product is visually imperfect — misprinted cartons, wrong color separations, missing or duplicated batch information — image-based screening from a consumer smartphone is an attractive triage tool: it requires no laboratory access, no chemical assay and no supply-chain instrumentation. A body of work has accordingly applied convolutional neural networks to photographs of medicine packaging and reported high binary classification accuracy [3], [26]–[28], alongside a larger adjacent literature on pharmaceutical *identification* rather than *authentication* [4], [5].

A property of that body of work motivates this paper's method as much as its subject. There is no shared, curated benchmark for pharmaceutical authentication comparable to the standard corpora of adjacent vision tasks. Every study we were able to examine in full text built or adopted its own image set, by a different procedure, and none of them audited that set for confounds between acquisition and label (Section II-F). Accuracy figures in this sub-field are therefore not mutually comparable, and each rests entirely on the unexamined construction of a single private or ad hoc collection.

### A. The general problem: asymmetric class sourcing

That condition is not peculiar to pharmaceutical authentication, and the mechanism it creates is the general subject of this paper. Consider what it takes to assemble a two-class image dataset for any question of the form *is this genuine?* Authentic examples are abundant: manufacturers photograph their own products, retailers publish catalogs, ordinary users can photograph what they own. The other class is scarce almost by definition — counterfeit stock is illegal to hold, forged documents are held as evidence, defective units are discarded, and confirmed instances of any adversarial artifact are rare precisely because someone is trying to prevent them. A researcher who needs a negative class therefore obtains it *by some other means than the one that produced the positive class*: by screen-capturing regulator bulletins, by scraping a different corpus, by digitally editing authentic images, or by generating examples with a model.

Every one of those substitutions introduces a systematic difference between the classes that has nothing to do with the property being labeled. Acquisition method determines file format, encoded size, resolution, noise floor, compression signature, color rendering and often composition and backdrop; a class label that correlates with acquisition method therefore correlates with all of them. We call this **class-conditional provenance confounding**, and the argument of this paper is that asymmetric class availability makes it a *likely* outcome of dataset construction in this family of tasks rather than an occasional lapse.

It is worth being exact about the status of that argument, because the rest of the paper depends on the distinction. What we demonstrate is a mechanism and a case: the case study is confounded totally, the mechanism explains why, and the same signature has been reported independently in an unrelated field. What we do not demonstrate is a *rate*. Establishing that provenance confounding is the default rather than merely a recurring hazard would require auditing a representative sample of datasets in this family and reporting how many fail, and neither this paper nor, as far as we can determine, any other has done that. Section VII-K takes a step in that direction by auditing several further datasets from other application areas, and finds both a totally confounded case and a clean one, which is enough to show that the audit discriminates but far short of a prevalence estimate. Readers should treat the generality claim as a hypothesis with converging support and a stated test, not as a measured fact; Section IX-G says what would falsify it.

Three properties make it particularly damaging. It is **maximally learnable**: low-level global statistics are easier for a network to extract than the semantics of a printed carton, so a shortcut-seeking optimiser [6] finds them first. It is **invisible in-distribution**: a held-out partition drawn from the same pool inherits the confound in the same proportion, so no amount of stratification, cross-validation, bootstrapping or leakage-aware grouping will expose it — we demonstrate this by doing all four and finding nothing. And it is **silent in the reporting record**: acquisition method is rarely documented, so a reader cannot detect it from a paper, and often cannot detect it from the dataset either.

The same signature has been reported independently in a literature with no connection to pharmaceuticals. In generated-image detection, real images are typically harvested from web corpora as lossy JPEGs at modest resolution while generated images are saved as lossless PNGs at the generator's native size; Grommelt *et al.* [30] show that on the standard GenImage benchmark this makes format, compression and size predictive of the label, that detectors trained on it partly become JPEG detectors, and that equalizing those factors changes cross-generator performance by more than 11 points. That work and this one share no data, no application area and no method of discovery, and arrive at the same confound — which is what a structural cause predicts and a coincidence does not.

### B. This paper

This study began as a methodological exercise on a public dataset. The Kaggle *Fake vs Real Medicine* set is small (661 images), freely available, and typical in construction of what this application area works with: a two-class collection of packaging images with no data card and no stated acquisition protocol. Accuracies in the low-to-mid 90s are routinely reported on data of this kind (Section II-F). We set out to establish how much of such a figure survives methodological correction, using a protocol fixed in advance: quantify the train/test leakage contribution by evaluating identical models under a naive image-level split and a product-identity-grouped split; span four model families from a 97-parameter linear baseline to a 4-million-parameter pretrained backbone, so that capacity is a measured variable rather than an assumption; and validate on a genuinely external source, verified independent rather than assumed so.

The result was not the one the design anticipated, and the difference is the contribution of this paper. Correcting the split protocol changed in-distribution accuracy very little — at most 6.8 points, within overlapping bootstrap confidence intervals for every model. What changed the picture completely was external validation. On 150 authentic packaging photographs from an independently collected source, two of four models classified *zero* images correctly, and the strongest in-distribution model classified 3.3% correctly, despite scoring 97.4% on the authentic class of its own in-distribution test partition. That failure is not subtle degradation; it is a near-total inversion.

Tracing its cause led to a property of the dataset itself. The dataset's two classes were not merely photographed differently — they were *acquired* differently. Every counterfeit-labeled file is a screen capture (`Screenshot*.png`); every authentic-labeled file is a downloaded photograph (`images*.jpg`). The correlation with the class label is exactly 1.0 across the entire pool. The two acquisition pipelines differ enormously in brightness, resolution and compression, and none of those differences has anything to do with whether the depicted product is genuine. Any model — including a 97-parameter linear classifier on a color histogram — has direct, unobstructed access to this shortcut. In the terminology of Geirhos et al. [6], the dataset admits a shortcut that is both maximally predictive in-distribution and maximally uninformative out of distribution; in the terminology of the medical-imaging literature, it is a hidden stratification of the same kind as the hospital-of-origin signal that Zech et al. [7] showed pneumonia classifiers exploit, differing only in being total rather than partial [8]–[10].

We then asked whether the failure was correctable. Because the confound is expressed in three measurable low-level image statistics, it can be attacked with preprocessing that uses no label information and could be deployed unchanged at inference time: cap effective resolution, rescale mean brightness to a fixed target, and force every image through a common lossy-compression bottleneck. Applied identically to training, in-distribution test and external partitions, this three-stage normalization raises external authentic accuracy from 0.0% to 86.0% for the small CNN, from 3.3% to 80.7% for EfficientNet-B0, and from 69.3% to 77.3% for MobileNetV3-Small, at an in-distribution cost of between −1.4 and 0.0 points. It is not a complete repair — a 16–20 point gap survives for both transfer-learning models — and it is not universally beneficial: for the color-histogram baseline it destroys in-distribution accuracy (83.8% → 54.1%) while recovering nothing externally, which is itself a diagnosis rather than a disappointment.

The remainder of this section describes how the study reached that framing, which was not the order in which it was designed.

The contributions of this paper are:

1. **A named mechanism and a cheap detector for it.** We identify asymmetric class sourcing as a structural cause of provenance confounding in authenticity-classification datasets (Section I-A), and propose the *provenance audit* — fitting the intended classifier to acquisition metadata alone, under the study's own leakage-free split — as a pre-training screen whose accuracy lower-bounds how much of any pixel-based result the acquisition process can explain (Sections VII-A–VII-B, Tables 7 and 8). It requires no external data, no new annotation and no pixel decoding, and on the case-study dataset it returns 1.000.

2. **Evidence that the detector is necessary but not sufficient, and a diagnosis of when it fails.** Applied to a second, independently published dataset the audit returns only 0.717, although that dataset is confounded at least as severely — 57/57 of its counterfeit-labeled source images carry the ground-truth word rendered in the pixels. Its publisher had normalized every image to a common resolution and format before release, suppressing the acquisition traces without touching the confound (Section VII-B). A dataset that has been tidied for distribution is therefore *harder*, not easier, to audit cheaply, and the audit's silence must not be read as a clearance. We give the taxonomy and the complementary checks in Section IX-F.

3. **A quantified, previously unreported confound in the case-study dataset.** A 100%-separating capture-pipeline/class-label confound, with effect sizes on brightness, resolution, aspect ratio and file size; an exact Shapley decomposition showing a linear model's decision function is dominated by the statistic the confound most directly controls; and a degenerate shipped train/validation/test partition in which the training folder is a superset of both others (Sections III-A and VII-A, Figs. 3 and 12).

4. **A demonstration that classical leakage correction is the smaller of the two problems.** Under a controlled, single-variable comparison, product-level grouping changes accuracy by ≤ 6.8 points on this pool — against an analytic ceiling of 9.2 points derived from the split alone (Section VII-C) — whereas the provenance confound accounts for the difference between 97% in-distribution accuracy and 3% external accuracy (Sections VII-D–VII-F). The methodological check the field has institutionalized is not the one that mattered here.

5. **A complete attention audit showing what the surviving accuracy rests on.** All 62 Grad-CAM maps produced by this study were regenerated from persisted checkpoints and categorized in full. On the external sets the result is without exception across 40 maps and identical for both frozen backbones: evidence for "authentic" comes from the photographic surround, evidence for "counterfeit" from the product (Section VII-G, Fig. 14).

6. **A label-free correction, ablated per axis, per architecture, per constant and per composition order.** We isolate resolution, brightness, compression and white balance, show that the first three are complementary and the fourth is not, report per-architecture outcomes rather than a blanket recommendation, and vary all three constants to show the effect sits on a broad plateau rather than a tuned point (Section VIII). Varying the *order* of the three operators, which a preprocessing description normally leaves implicit, turns out to matter more than any of their magnitudes: it moves external accuracy across a 50-point range, from 0.380 to 0.880, under a 2.7-point in-distribution range, and the ordering that scores highest in-distribution scores lowest externally (Section VIII-F, Table 24).

7. **A synthetic counterfeit-proxy stress test** in the spirit of ImageNet-C [12], used to probe the counterfeit-recall direction that an authentic-only external set cannot address, together with an explicit statement of what such a proxy does and does not measure (Sections V-F and VII-F).

8. **A full accounting of four reproducibility defects found along the way**, every one of them in a code path that rebuilt a model without checking its output against a known value — an unseeded augmentation pass, a stale learning rate, an accuracy that proved unreproducible once checkpoints made the comparison possible, and a backbone left in training mode that invalidated the published attention maps. We give the one-line practice that would have caught all four (Sections VI-E and X).

We deliberately do not propose a new architecture. The most useful thing that can be said about architectures on this dataset is that the pairwise differences between a 97-parameter linear model and a 4-million-parameter pretrained network are not statistically distinguishable on its test partition (Section VII-C), and that the ranking that does emerge in-distribution does not predict the ranking out of distribution.

---

## II. Related Work

### A. Image-based pharmaceutical authentication and identification

Image classification has been applied to pharmaceutical products both for *identification* (which drug is this?) and for *authentication* (is this drug genuine?). Ramos, Samonte and Manlises [3] proposed a CNN-based medicine-authentication system directly comparable in task framing to the present work, classifying pharmaceutical images as authentic or counterfeit. Adjacent work has concentrated on identification: Ting et al. [4] developed a deep learning drug-identification model to address look-alike/sound-alike medication errors, evaluated on 250 blister-packaged drug types at a Taiwanese medical center, and Al-Hussaeni et al. [5] applied CNNs to pill-image retrieval. This body of work establishes that packaging and pill imagery carries usable discriminative signal for pharmaceutical classification tasks. To the extent this review found, however, none of it examines *why* reported accuracies are as high as they are, or audits its benchmark datasets for confounds between the acquisition process and the class label. The present work is methodologically orthogonal to this literature: rather than proposing a new architecture, it audits the acquisition process, the evaluation protocol and the datasets that results of this kind rest on.

### B. Shortcut learning and hidden stratification

Geirhos et al. [6] formalized *shortcut learning*: the tendency of deep networks to adopt decision rules that exploit superficial, spuriously predictive correlations in training data, achieving high in-distribution benchmark performance while failing to transfer to conditions in which the shortcut is absent or reversed. This framing describes the central empirical finding of the present work precisely.

The failure mode has a well-documented precedent in medical imaging. Zech et al. [7] showed that pneumonia-detection models trained on chest radiographs from three hospital systems could predict which system an image originated from at high accuracy, and that this hospital-identity signal — itself correlated with disease prevalence across sites — was usable as a shortcut for the diagnostic label rather than requiring the model to learn disease-relevant features, causing substantially degraded performance on a hospital unseen during training. More recent work continues to document the pattern: [8] and [9] report audits finding that deep models for chest-radiograph interpretation exploit scanner-, site- and manufacturer-level signal rather than the intended pathological finding, and early COVID-19 chest-radiograph classifiers were subsequently shown to rely on dataset-source confounds rather than radiographic signs of disease [10]. The present work's finding is structurally identical to this literature's central concern, applied — as far as this review found, for the first time — to the counterfeit-pharmaceutical image classification literature, and in a more extreme form: the confound here is not a subtle cross-site signal but a complete separation of the two classes by acquisition method.

There is a difference in *cause* worth drawing out, because it determines how far the present finding generalizes. In the medical-imaging cases the confound is an artifact of where data happened to come from: several sites contributed, they differed in equipment and in case mix, and the correlation between site and label was incidental. In the tasks this paper concerns, the correlation is not incidental but produced by the researcher, because the negative class was unobtainable by the procedure that produced the positive class (Section I-A). That makes the confound stronger — total rather than partial — and more predictable, since one can say in advance which datasets are at risk: any in which the two classes were sourced separately.

The closest published analogue outside medicine is in generated-image detection. Grommelt *et al.* [30] audit the GenImage benchmark and find its real and generated classes separated by JPEG compression and image size, because real images are harvested from web corpora as lossy JPEGs while generated images are written as lossless PNGs at the generator's output resolution. They report that detectors trained on the benchmark learn these factors, to the point of partly functioning as JPEG detectors, and that equalizing compression and size shifts cross-generator performance by more than 11 points. The parallel to the present study is close enough to be worth stating precisely: the same three statistics, the same direction (the "genuine" class lossy and small, the "fake" class lossless and large), the same in-distribution invisibility, and a correction of the same shape — yet a completely unrelated application area and cause. Neither study's authors were aware of the other's dataset. Two independent discoveries of one signature is evidence for a shared generating mechanism, which is the argument of Section I-A.

### C. Data leakage and evaluation protocol

A related but distinct methodological concern is train/test leakage from improper partitioning. In medical imaging, splitting at the image level rather than the subject level allows near-duplicate or correlated images of the same underlying entity to appear in both training and test partitions, inflating reported generalization performance [11]. This concern motivated the present work's two-split design — a naive image-level split and a product-identity-level leakage-free split, evaluated in parallel so that the leakage effect's magnitude is directly measured rather than assumed. Notably, on the cleaned dataset used here the measured leakage effect is small (≤ 4.1 points) relative to the capture-pipeline confound of Section II-B, which accounts for the great majority of the gap between in-distribution and external performance. That ordering is itself a finding: auditing acquisition-pipeline confounds deserves at least the attention that image-level leakage currently receives.

### D. Robustness to synthetic corruption

To evaluate robustness under distribution shift without collecting new out-of-distribution data, prior work has used synthetically corrupted versions of clean images as a controlled proxy. Hendrycks and Dietterich [12] introduced ImageNet-C, applying a standardized suite of corruptions at multiple severities to measure classifier robustness independently of any specific real-world out-of-distribution dataset. The present work adopts the same methodological logic: in the absence of a genuine independent counterfeit-labeled external dataset, independent authentic photographs are perturbed with print-quality, color and text-region defects to construct a synthetic counterfeit-proxy evaluation set. Following [12], we state explicitly that such a proxy measures robustness to a specific, documented perturbation style rather than true label-defined class recall.

### E. Architectures and interpretability methods

The four model families evaluated here span a classical color-histogram baseline through modern efficient CNN architectures: MobileNetV3 [13] and EfficientNet-B0 [14], both used as frozen ImageNet-pretrained feature extractors with a linear classification head. Model attention is inspected using Grad-CAM [15], which produces gradient-weighted class activation maps localizing the image regions most responsible for a prediction, without architectural modification or retraining. Feature attribution for the linear baseline uses Shapley values [16]; for a linear model with an independent-feature background these have a closed form and require no sampling (Section V-E). Domain-generalization surveys [23] situate the normalization-based correction of Section V-D within a broader toolkit; the correction used here is closer to hand-designed covariate-shift alignment than to the representation-learning methods that literature mostly covers.

### F. What datasets this sub-field actually uses

Because this paper's contribution is a dataset audit, the datasets on which neighbouring results rest are themselves relevant prior work. We therefore examined, in full text where obtainable, every study we could locate that performs authentic-vs-counterfeit classification of pharmaceutical *images*. Table 1 records what each one trained on. The survey is a best-effort search, not a systematic review, and its negative findings should be read as "not found by this search" rather than "does not exist".

**TABLE 1.** Image sources used by located prior work on pharmaceutical authentication, and the acquisition-audit status of each. "Audit" asks whether the study reports any check that acquisition conditions are balanced across its two classes.

| Study | Image source | Class construction | Reported accuracy | Audit |
|---|---|---|---|---|
| Ramos *et al.* [3] | Self-captured, Raspberry Pi camera; one brand (Biogesic paracetamol) | Physical authentic and counterfeit samples, same rig | 88.75% | none reported |
| Motwani *et al.* [26] | Web-scraped packaging images, 10 manufacturers | Counterfeit class **created by the authors** by altering logo and text on authentic images | not reported per-class | none reported |
| Thomson and Varuna [27] | A Kaggle *pill and vitamin* dataset for training; DrugBank and drugs.com images for testing | Counterfeit class **generated by GAN/cGAN synthesis** | not comparably reported | none reported |
| Thomson and Varuna [28] | drugs.com product images | not specified | 92% | none reported |
| Roboflow *Counterfeit med detection* [21] | Regulator advisory bulletins plus product photographs | Class correlates with document type, not authenticity (Section III-B) | — | — |

Three observations follow, and each bears directly on the finding of Section VII-A.

**No shared benchmark exists, so the confound cannot be inherited — only re-invented.** No two studies in Table 1 evaluate on the same images. The Kaggle set audited here is not a community benchmark in the sense that term usually carries: as of 13 August 2026 its Kaggle listing records 574 downloads, 3 public notebooks and 2 votes, states its license as "Unknown", and a search of the literature found no peer-reviewed study that uses it at all. The claim this paper makes is correspondingly narrow and, we think, more useful: not that a widely-shared benchmark is broken, but that a dataset assembled the way this sub-field routinely assembles datasets contains a total acquisition confound that its own users did not detect.

**The most common class-construction procedures make the confound near-inevitable.** In [26] the counterfeit class is produced by digitally editing authentic images; in [27] it is produced by a generative model. In both cases the two classes are, by construction, outputs of two different image pipelines, exactly as in the dataset audited here — and neither study reports a check that would surface it. A model can score highly on such a set by learning the editing or generation signature, and no in-distribution evaluation would distinguish that from learning authenticity. Where the two classes *were* acquired under a common protocol — [3], which photographs real authentic and real counterfeit samples on one Raspberry Pi rig — the reported accuracy is the lowest in Table 1 (88.75%), which is at least consistent with the confound accounting for part of the spread.

**Studies that do control acquisition say so explicitly.** Outside pharmaceuticals, Garcia-Cotte *et al.* [29] report counterfeit detection on branded garments from smartphone images captured "under natural, weakly controlled conditions" in stores, warehouses and customs checkpoints, at 99.71% after a 3.06% rejection rate. Whatever else separates that work from Table 1, it states its acquisition regime as a property of the result. That is the reporting standard we argue Section IX-D should become routine here.

---

## III. Dataset

### A. Sources considered

Three public sources were inventoried (Table 2). All three were considered for the modeling pool; two were excluded from it for reasons documented below, and one was used as the external evaluation set.

**TABLE 2.** Public sources inventoried, with their role in this study.

| Source | Files as shipped | License | Role |
|---|---|---|---|
| Kaggle *Fake vs Real Medicine* [19] | 661 unique (`Fake/` 240, all `.png`; `Real/` 421, all `.jpg`), re-listed across a bundled `train`/`val`/`test` split | "Unknown" per the Kaggle listing; none stated in the archive | Modeling pool (Splits A and B); the dataset used by [3] |
| Roboflow *Counterfeit_med_detection* v4 [21] | 4,260 (includes the publisher's own 3× rotation/exposure augmentation) | CC BY 4.0 | Excluded from modeling; retained as a supplementary authentic pool |
| Mendeley *Mobile-Captured Pharmaceutical Medication Packages* [20] | 3,900 across six devices; the 150-image "Huawei CN" single-instance-per-product subset was used | CC BY 4.0 | External evaluation (Split C), authentic only |

Two properties of the primary source should be recorded before any result is read, because both are verifiable in seconds by anyone holding the archive and neither appears to have been noted previously.

**Provenance.** The dataset is a single-uploader Kaggle contribution, last updated 13 October 2025, distributed with its license field set to "Unknown". Its counterfeit-class files are named `Screenshot YYYY-MM-DD HHMMSS.png` and their embedded timestamps fall within a small number of capture sessions; its authentic-class files are named `imagesNN.jpg`. The archive contains no data card, no collection protocol and no provenance for any individual image. Nothing about this is unusual for a dataset of this kind, which is the point of Section II-F.

**The bundled split is not a split.** Alongside the `Fake/` and `Real/` class folders, the archive ships `train/`, `val/` and `test/` folders. Counting unique filenames within them:

|T| = 661,  |V| = 453,  |E| = 449,  V ⊂ T,  E ⊂ T,  |V ∩ E| = 286

The training folder contains **every image in the dataset**, and the validation and test folders are proper subsets of it — 453 of 453 and 449 of 449 respectively — with 286 images appearing in all three. A study that adopts this partition as distributed trains on 100% of the data it then reports test accuracy on. We discarded the bundled split entirely and constructed our own (Section IV-C); we record it here because it is a second, independent, fully deterministic defect in the same artifact, and because it is exactly the kind of thing that a reader cannot detect from a reported accuracy figure.

### B. Why the second source was excluded: a label baked into the pixels

The Roboflow source appeared, from its description, to be a second independent authentic/counterfeit dataset and therefore a natural candidate both for pooling and for cross-dataset validation. Direct inspection showed it is neither. Of its counterfeit-labeled images, 57/57 unique source images are institutional public-health advisory graphics — multi-panel comparison collages, typically carrying a regulator's logo, a banner headline, and, critically, **the ground-truth label rendered as literal text inside the image** (captions reading `COUNTERFEIT` or `AUTHENTIC` overlaid on the photograph). Conversely, 263/263 of its plain product photographs are authentic-labeled. A model trained on this source as shipped would learn to distinguish advisory collages from product photography. Two units of count are in play here and are easy to conflate: the source ships each photograph together with the publisher's own 3× rotation/exposure augmentation, so 57 unique counterfeit-labeled *source images* correspond to 180 *files*. Excluding those 180 files (identified by filename pattern, plus explicit manual inspection of every counterfeit-labeled file the pattern left behind — 9 of them) and 52 rows carrying simultaneous `authentic=1` and `counterfeit=1` annotations, the source contributes **2** usable counterfeit images against 2,695 authentic ones. Prior work has attributed this source's unsuitability to class imbalance; the deeper problem is a modality confound.

### C. Why the two sources are not independent

Perceptual-hash clustering (Section IV-B) found that **229 clusters contain images from both the Roboflow and the Kaggle source**, covering 2,900 of 4,027 retained Roboflow images and 290 of 661 Kaggle images — that is, **44% of the Kaggle dataset has a near-duplicate in the Roboflow source**, sometimes differing only by a 90° rotation. Neither source documents its provenance, so we make no claim about which one derives from the other, or whether both draw on a common upstream; the relevant fact is only that they are not independent. This was verified visually on matched pairs, not inferred from hash distance alone. Any study treating these two public datasets as independent sources for cross-dataset generalization testing would therefore be leaking training data into "external" evaluation.

### D. The modeling pool

Given Sections III-B and III-C, **Splits A and B are built from the Kaggle pool alone**. This choice is deliberate and conservative: holding the data fixed makes the split protocol the single manipulated variable in the leakage comparison, rather than confounding "we corrected the split" with "we also changed the data". Adding the Roboflow pool would additionally have pushed the group-level class ratio from 44:56 to roughly 8:92 while contributing essentially no counterfeit signal.

After exclusion and de-duplication the pool contains **510 images in 480 product-identity groups**, 272 authentic and 238 counterfeit.

### E. Complete manual quality and modality review

The entire pool was reviewed by a human annotator, image by image, using two purpose-built local tagging tools (a watermark/non-medicine pass and a modality pass), across four rounds. This was a census, not a sample. Fifty-six files were excluded at the filtering stage:

- **47 watermark or stock-photo-overlay images.** Checked rather than assumed: **47/47 (100%) are authentic-labeled**, and they carry overlays from at least six distinct product-catalog or stock-photography sites. This is a second, smaller class-correlated confound, structurally similar to the bulletin-graphic problem of Section III-B.
- **4 non-medicine images**: one literal browser screenshot of another dataset's own web page, and three stock/marketing renders rather than device photographs.
- **5 images with no packaging in frame**: one loose-tablet photograph and four syrup bottles.

The modality census (Table 3) matters for how any result on this pool is described. The dataset is not outer-packaging-only, although its title and the usual framing of this task both suggest it is.

**TABLE 3.** Modality composition of the 510-image modeling pool (complete census, human-annotated).

| Modality | Count | Share |
|---|---|---|
| Blister pack | 223 | 43.7% |
| Outer packaging (carton) | 155 | 30.4% |
| Other (carton + blister together, sachet, mixed) | 132 | 25.9% |

We therefore describe this study's scope as **"packaging and immediate product containers"**. We considered filtering to outer packaging only, which would have removed roughly 57% of the pool and required re-running every split and model; we did not, because the capture-confound finding does not depend on modality composition, and we report the composition explicitly instead. This is a wording correction to the prior claim, not a new experiment.

### F. External evaluation set (Split C)

The study protocol called for at least one genuinely external source. A search for an independent *two-class* source found none: every candidate identified was either highly likely to share underlying photographs with sources already in the pool (Section III-C) or carried no counterfeit label at all. We therefore use the Mendeley source [20] as an **authentic-only** external check: 150 photographs, one per distinct product, from a different country, different photographers, different camera hardware and a different backdrop protocol. Its independence was verified programmatically rather than assumed (Section IV-B): **0 of 150 images matched anything in the existing pool**, the nearest match sitting at Hamming distance 10/64 against a near-duplicate threshold of 8, with a median distance of 18.

An authentic-only external set measures the false-positive rate on genuine packaging and says nothing about counterfeit recall. Section V-F describes the synthetic proxy built to probe that second direction, and Section X states the limitation that remains.

---

## IV. Data Preprocessing

The full pipeline is deterministic (fixed seed 42 throughout) and idempotent; re-running reproduces byte-identical outputs. Figure 1 summarizes it.

> **FIGURE 1.** `paper/figures/fig01_workflow.pdf` — Data provenance, splitting protocol and evaluation design. Sources (top row) pass through source-specific exclusion or verification (second row); the Kaggle and Roboflow pools are de-duplicated into product-identity groups from which the 510-image modeling pool is drawn (third row); the four evaluation partitions (fourth row) feed a single shared training and normalization protocol (bottom band).

### A. Filtering

Exclusions are rule-based and individually documented in code, in three families: contradictory annotations (52 Roboflow rows), advisory-bulletin graphics (180 Roboflow files, Section III-B), and the 56 human-identified Kaggle files of Section III-E. Every exclusion is recorded with a machine-readable reason in the provenance table, so that any downstream count can be traced to the rule that produced it.

### B. De-duplication and product identity

Neither source carries ground-truth product-identity labels, so near-duplicate photo clustering is used as an operational proxy. A 64-bit perceptual hash [25] is computed at all four cardinal orientations per image and the numeric minimum taken as a rotation-canonical hash:

$$h(x) = \min_{\theta \in \{0°, 90°, 180°, 270°\}} \mathrm{pHash}\big(R_\theta(x)\big) \tag{1}$$

Rotation invariance is necessary rather than decorative: the Roboflow source documents 90°-rotation augmentation, and a plain pHash treats a rotated copy of a photograph as a different image. Pairs at Hamming distance 0 on the canonical hash are treated as true duplicates and one copy is removed; pairs at distance 1–8 are retained but assigned to the same `product_identity` cluster. Zero clusters mix authentic and counterfeit labels, so the clustering never contradicts the original annotations.

The method is not robust to mirroring; mirrored duplicates would be missed. Because the augmentation policy of Section V-C deliberately excludes flips (mirrored printed text is unnatural), this gap is low-risk but not exhaustively verified.

### C. Split construction

Three partitions of the modeling pool are built (Table 4):

- **Split A (naive)** — random 70:15:15, class-stratified, at the **image** level. This is the protocol in general use on data of this kind, and the only one available to a study that adopts a dataset's shipped partition without inspecting it, as Section III-A shows this dataset's shipped partition invites; none of the studies in Table 1 reports a grouped or identity-aware split.
- **Split B (corrected)** — 70:15:15, class-stratified, at the **product-identity group** level, so no near-duplicate photograph of the same product can appear in more than one partition. The training partition additionally carries a `cv_fold` index from `StratifiedGroupKFold`, so 5-fold cross-validation never places the same product in two folds.
- **Split C (external)** — the 150 Mendeley photographs, used only for evaluation.

An assertion in the pipeline verifies zero product-identity overlap between every pair of Split B partitions on every run; it passes. Comparing the two assignments directly, **9 of 480 product-identity groups (1.9%) have members in more than one partition under Split A** — this is the literal, countable leakage that Split B removes — and 230 of 510 images (45.1%) are assigned to a different partition under A than under B.

**TABLE 4.** Partition sizes and class balance. Split B partition sizes differ slightly from Split A's because grouping constrains which images can move together.

| | Split A train | Split A val | Split A test | Split B train | Split B val | Split B test | Split C |
|---|---|---|---|---|---|---|---|
| Images | 357 | 77 | 76 | 357 | 79 | 74 | 150 |
| Product groups | — | — | — | 336 | 72 | 72 | 150 |
| Authentic | 190 | 41 | 41 | 188 | 45 | 39 | 150 |
| Counterfeit | 167 | 36 | 35 | 169 | 34 | 35 | 0 |

The test partitions are small (74–76 images). Every point estimate in Section VII is therefore reported with a 95% bootstrap confidence interval, and comparisons are read against those intervals rather than against point differences.

### D. Capture-method normalization

The three-stage normalization that Sections V-D and VIII evaluate is applied *inside* the dataset class, before augmentation and before the network's input transform, identically for training, validation, in-distribution test and external partitions. It uses no label information at any point and could be shipped unchanged as an inference-time preprocessing step. Section V-D gives its definition.

---

## V. Methodology

### A. Task and label convention

The task is binary image classification. Throughout, authentic = 0 and **counterfeit is the positive class**, so precision, recall, F1, ROC-AUC and PR-AUC are all reported with respect to counterfeit detection. This matches the deployment framing (the cost of interest is a missed counterfeit) and is fixed project-wide in code to prevent accidental polarity inversion between scripts.

### B. Models

Four model families are evaluated (Fig. 2). The roster is deliberately spread across capacity scales so that "does capacity explain the reported accuracy?" is answerable.

> **FIGURE 2.** `paper/figures/fig02_architectures.pdf` — The four model families, with exact parameter counts. Hatched blocks are frozen.

**M1 — Color histogram + logistic regression (97 learned parameters).** Each image is resized to 224×224 and a 32-bin-per-channel RGB intensity histogram computed, giving a 96-dimensional feature vector:

$$\phi(x) = \big[\,\mathbf{h}_R(x) \,\|\, \mathbf{h}_G(x) \,\|\, \mathbf{h}_B(x)\,\big] \in \mathbb{R}^{96}, \qquad \mathbf{h}_{c,b}(x) = \frac{1}{HW}\sum_{i,j} \mathbb{1}\!\left[ x_{ij}^{(c)} \in B_b \right] \tag{2}$$

with the 32 bins $B_b$ uniformly partitioning [0, 256). A logistic regression is fitted on $\phi(x)$:

$$P(y = 1 \mid x) = \sigma\big(\mathbf{w}^\top \phi(x) + b\big), \qquad \sigma(z) = \frac{1}{1 + e^{-z}} \tag{3}$$

with `class_weight="balanced"` and L2 regularization at scikit-learn's default strength. This model exists to answer one question: how much of the reported accuracy on this benchmark is available to a classifier that cannot see spatial structure at all? It is intentionally excluded from the augmentation policy (Section V-C) and from the normalization pipeline (Section V-D) for reasons given in each.

**M2 — Small CNN with a global-average-pooling head (23,938 trainable parameters).** Three convolutional blocks with a conventional channel progression (16 → 32 → 64; each block Conv3×3 → BatchNorm → ReLU → MaxPool2×2), with a global-average-pooling head rather than the `flatten → dense` head that small-dataset CNN work commonly uses:

$$g_k = \frac{1}{H'W'}\sum_{i=1}^{H'}\sum_{j=1}^{W'} a_{ijk}, \qquad \hat{y} = \mathrm{softmax}\big(W_{\!f}\,\mathrm{drop}_{0.5}(\mathbf{g}) + \mathbf{b}_{\!f}\big) \tag{4}$$

The head choice is the point of this model. On a 224 × 224 input this trunk emits a 28 × 28 × 64 feature map, so flattening it into a 128-unit dense layer costs roughly 6.4 M parameters — some 99.7% of such a network's total — on 357 training images. Global average pooling replaces that with 130 parameters and brings the whole network to 23,938, while preserving the trunk exactly. M2 therefore measures what a from-scratch convolutional model achieves on this pool when its capacity is not dominated by a classifier head that the data cannot support.

**M3 — MobileNetV3-Small, frozen (1,154 trainable / 927,008 frozen).** The ImageNet-pretrained feature extractor [13] is frozen; a `Dropout(0.3) → Linear(576, 2)` head is trained on its globally pooled 576-dimensional output.

**M4 — EfficientNet-B0, frozen (2,562 trainable / 4,007,548 frozen).** As M3, with the EfficientNet-B0 feature extractor [14] and a `Dropout(0.3) → Linear(1280, 2)` head.

Freezing both backbones keeps the comparison balanced (both transfer models train exactly one linear layer) and the compute budget bounded on CPU-only hardware. Fine-tuning either backbone is a documented, deliberate omission rather than an oversight; Section XI returns to it.

### C. Augmentation

Training-partition augmentation for M2–M4 is: rotation ±12°, brightness and contrast jitter (±0.25), mild `RandomResizedCrop` (scale 0.85–1.0), and slight Gaussian blur (kernel 3, σ ∈ [0.1, 0.8]). **No horizontal or vertical flip** is used, because mirroring printed packaging text produces images that cannot occur in deployment.

M1 is excluded from augmentation, and this is a considered choice rather than an inconsistency. Rotation and cropping are near-invariances of a color histogram and would contribute nothing; brightness and contrast jitter would directly perturb the only feature this model observes, acting as label noise rather than as the spatial-filter regulariser it is for a CNN. Applying identical augmentation "for fairness" would mechanically handicap this baseline through a mechanism with no counterpart benefit. We note the asymmetry rather than hide it. Section VIII-C shows that this decision does not soften the paper's conclusion about M1 — if anything the opposite.

### D. Capture-method normalization

Three label-free operators are composed in a fixed order. Let $x$ be a decoded RGB image with dimensions $W \times H$.

**Resolution bottleneck.** Cap the short side at $s = 128$ px, chosen to sit below the 10th percentile of the Kaggle pool's own short-side distribution so that the bottleneck binds for nearly every image in both sources rather than only for the high-resolution external set:

$$T_{\mathrm{res}}(x) = \begin{cases} x & \text{if } \min(W, H) \le s \\ \mathrm{resize}\big(x,\; \lambda W,\; \lambda H\big), \;\; \lambda = \dfrac{s}{\min(W,H)} & \text{otherwise} \end{cases} \tag{5}$$

**Brightness rescale.** Scale to a fixed target mean $\mu^\star = 0.5$ and clip:

$$T_{\mathrm{bright}}(x) = \mathrm{clip}\!\left( x \cdot \frac{\mu^\star}{\bar{x}},\; 0,\; 1 \right), \qquad \bar{x} = \frac{1}{3HW}\sum_{c,i,j} x^{(c)}_{ij} \tag{6}$$

**Compression bottleneck.** Re-encode through JPEG at a fixed quality $q = 40$ and decode back, imposing a common quantization-artifact floor:

$$T_{\mathrm{comp}}(x) = \mathrm{decode}_{\mathrm{JPEG}}\big(\mathrm{encode}_{\mathrm{JPEG}}(x,\, q)\big) \tag{7}$$

The composed operator is

$$T(x) = T_{\mathrm{comp}} \circ T_{\mathrm{bright}} \circ T_{\mathrm{res}}\,(x) \tag{8}$$

and is applied identically to every partition. Three properties matter for the interpretation of Section VIII. First, $T$ is label-free — nothing in (5)–(7) references $y$ — so applying it to the external set is not an oracle. Second, $T$ is deployable: it is a fixed preprocessing function, not a train-time-only trick. Third, $T$ is *destructive* by design; it removes information, including information a model might legitimately use, which is why its effect must be measured per architecture rather than assumed (Section VIII-B).

The composition order in (8) is itself a choice, and because two of the three operators destroy information they do not commute: the same three operators reordered move external accuracy by 50 points while moving in-distribution accuracy by under 3. Section VIII-F measures all six orderings and derives the rule that governs them, which is that the compression bottleneck must be applied after the resolution cap rather than before it. The order in (8) satisfies that rule and was fixed before the sweep existed.

M1 reads images directly and never passes through this operator. That exclusion is empirical: normalization collapses M1's in-distribution accuracy toward chance while recovering nothing externally (Section VIII-C), so including it would only obscure the baseline's diagnostic role.

### E. Interpretability and attribution

**Grad-CAM.** For target class $c$, with $A^k$ the activation maps of the last convolutional stage,

$$\alpha^c_k = \frac{1}{HW}\sum_{i,j} \frac{\partial y^c}{\partial A^k_{ij}}, \qquad L^c_{\mathrm{Grad\text{-}CAM}} = \mathrm{ReLU}\!\left(\sum_k \alpha^c_k A^k\right) \tag{9}$$

following [15]. Maps are computed on M4 for the in-distribution audit and directly on the external images for both M3 and M4.

**Exact Shapley values for M1.** For a linear model with an independent-feature background distribution, the Shapley value of feature $i$ for instance $x$ has the closed form [16]

$$\varphi_i(x) = w_i\big(\phi_i(x) - \mathbb{E}[\phi_i]\big) \tag{10}$$

so no sampling approximation is required. We take $\mathbb{E}[\phi_i]$ over the Split B training partition and report $\overline{|\varphi_i|}$ over the Split B test partition as global importance. This is an exact decomposition of M1's decision function, not an estimate.

### F. Synthetic counterfeit proxy

Because no independent counterfeit-labeled source exists (Section III-F), a proxy negative class is constructed by perturbing the *same* 150 external authentic photographs, so that the perturbation is the only systematic difference between classes by construction. Each image receives a deterministically seeded random subset (3–5 of 5) of photographic defects — per-channel color/hue shift, halftone dot-grid overlay, per-channel registration offset, Gaussian blur, contrast reduction — plus text-region tampering (ghosting, thin-strip jitter, or ink dropout) applied to 1 to about half of the text/logo regions located by classical edge-density and connected-component analysis. Parameters are randomized per image specifically to avoid substituting one uniform processing signature for the confound under study.

Two design errors were found and corrected before the set was finalized, both worth recording because both are easy to repeat:

1. **Insufficient severity.** In a first batch, 13% of images were perceptually indistinguishable from their originals (mean per-pixel difference < 5/255 at review resolution) because independent weak parameter draws compounded. Severity ranges were widened, color shift was forced to at least 15% per-channel deviation, halftone spacing was scaled to image size so it survives downscaling, and the number of applied effects was raised from 2–4 to 3–5. After the fix, 0% were imperceptible and the minimum per-pixel difference was 6.0/255.
2. **A reintroduced capture confound.** The first version drew base images from a *different* device subset of the source dataset (iPhone 11 Pro) than the authentic class (Huawei CN). Those subsets differ in mean brightness by more than 2× (0.389 vs. 0.162) because the source dataset deliberately varies lighting across device subsets. This would have recreated exactly the confound this paper is about, via source selection rather than generation. The fix was to generate from the same Huawei CN photographs already serving as the authentic class; the post-fix check gives 0.162 vs. 0.153, and identical median resolution.

All 150 candidates were reviewed by a human annotator side by side with their originals; 150/150 were approved, 0 rejected. The final set is 300 images (150 real authentic + 150 approved synthetic counterfeit). Its remaining class difference in mean file size (1,656 kB vs. 1,018 kB) is a direct causal consequence of the perturbations themselves — blur and contrast reduction lower encoded detail — not an independent acquisition confound.

This set measures robustness to a documented perturbation style. It is **not** a measurement of real-world counterfeit recall, and real counterfeits may differ in ways not modeled at all: absent security features, holograms or tamper seals, wrong packaging substrate, or serial-number and barcode errors. Every reference to it in this paper carries that caveat.

---

## VI. Experimental Setup

### A. Environment

PyTorch 2.7.1 [17] on CPU only (no CUDA available), scikit-learn 1.9.0 [18]. Seed 42 is set for Python, NumPy and PyTorch before every training run, before every fold, and before every augmented feature-extraction pass. Non-deterministic CUDA kernels are not a factor; `torch.use_deterministic_algorithms` is left off because some CPU operators lack deterministic kernels.

### B. Training protocol

Identical for M2–M4 (Table 5): Adam, batch size 32, class-weighted cross-entropy, maximum 50 epochs, early stopping on validation loss with patience 4 and a minimum improvement threshold. Class weights are inverse-frequency,

$$w_0 = \frac{n}{2 n_0}, \qquad w_1 = \frac{n}{2 n_1}, \qquad \mathcal{L} = -\frac{1}{n}\sum_{m=1}^{n} w_{y_m} \log \hat{p}_{m, y_m} \tag{11}$$

which follows the protocol choice of class weighting over oversampling. The minimum-improvement threshold (1 × 10⁻³) was added after observing a frozen-backbone linear head run for 46+ epochs on noise-level validation-loss "improvements" that a naive patience counter never terminated; with the threshold, patience resets only on a meaningful improvement. The best-validation-loss state is restored at the end of training.

**TABLE 5.** Hyperparameters. The learning-rate grid was searched for 5 epochs per value on Split A train/val only, and the selected value reused for both splits' full runs, following a "document the search range, do not over-search" policy on a dataset this small.

| Setting | Value |
|---|---|
| Optimiser | Adam |
| Batch size | 32 |
| Max epochs / patience / min improvement | 50 / 4 / 1 × 10⁻³ |
| Learning-rate grid | {1 × 10⁻³, 3 × 10⁻⁴, 1 × 10⁻⁴}, 5 epochs each |
| Selected LR (M2 / M3 / M4) | 1 × 10⁻³ / 1 × 10⁻³ / 1 × 10⁻³ |
| Loss | class-weighted cross-entropy, Eq. (11) |
| Input resolution | 224 × 224, ImageNet mean/std normalization |
| M1 | `LogisticRegression(max_iter=2000, class_weight="balanced")` |
| Cached augmented passes (M3, M4) | K = 3, each seeded with 42 + pass index |
| Seed | 42 |

### C. Frozen-backbone feature caching

For M3 and M4 the backbone is frozen, so its output for a given input never changes during head training, and re-running a full forward pass every epoch on CPU is wasted work. Features are extracted once per partition and the head trained on the cached vectors. To retain the benefit of augmentation despite caching, the training partition is expanded by $K = 3$ independently augmented passes through the backbone, so the head still sees three distinct augmented views of every training image. Validation, test and external partitions use a single deterministic pass.

This is standard linear-probing practice and it is what made M4 tractable at all here: a first attempt at live per-epoch backbone forward passes was terminated by the host before Split A finished. It is nonetheless a fidelity trade-off relative to fresh-every-epoch augmentation, and we record it as such.

### D. Evaluation protocol and metrics

All metrics use a 0.5 decision threshold unless stated. With TP, FP, FN, TN defined against counterfeit as positive:

$$\mathrm{Sens} = \frac{TP}{TP+FN}, \quad \mathrm{Spec} = \frac{TN}{TN+FP}, \quad \mathrm{BA} = \frac{\mathrm{Sens}+\mathrm{Spec}}{2} \tag{12}$$

$$\mathrm{MCC} = \frac{TP \cdot TN - FP \cdot FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}} \tag{13}$$

ROC-AUC is computed by the Mann–Whitney form with mid-ranks for ties, and PR-AUC as average precision. Uncertainty is a percentile bootstrap over test-set resamples [24]: for $b = 1 \dots 2000$, resample $n$ indices with replacement, recompute the metric, and report the 2.5th and 97.5th percentiles.

Paired model comparison uses McNemar's test [22] on the Split B test predictions. With $n_{01}$ the count of examples model A classifies correctly and model B does not, and $n_{10}$ the converse, we use the exact binomial test when the discordant total is below 25 (which it always is here, 1 ≤ $n_{01}+n_{10}$ ≤ 15):

$$p = 2 \sum_{k=0}^{\min(n_{01}, n_{10})} \binom{n_{01}+n_{10}}{k} 0.5^{\,n_{01}+n_{10}} \tag{14}$$

The external generalization gap for model $m$ is defined on the authentic class only, since Split C has no counterfeit members:

$$\Delta_m = \mathrm{Acc}^{\text{auth}}_{m,\text{Split B test}} - \mathrm{Acc}^{\text{auth}}_{m,\text{Split C}} \tag{15}$$

A negative $\Delta_m$ means the model performs *better* on the external source than on its own in-distribution test partition.

### E. Four reproducibility defects, disclosed

**A non-determinism bug, found and fixed.** The augmented feature-extraction passes of Section VI-C were originally unseeded, so the augmented views depended on whatever RNG state the process happened to be in — which varies with what ran earlier in the same script and is not reproducible across invocations. This is the mechanism behind a sequence of contradictory readings: the question "does normalization help M3?" was answered positively (+6.0 points), negatively (−21.3 points) and neutrally (−1.3 points) across three runs of nominally the same or closely related conditions before the cause was identified. The fix seeds each pass with 42 + pass index. Determinism was then verified empirically, not assumed: training M3 twice back to back produced byte-identical metric outputs. All production numbers in Section VII postdate the fix. One ablation condition (M3 under two-way normalization, Section VIII-B) was never re-run afterwards and is reported as unverified.

**A learning-rate inconsistency, found and corrected.** Because no checkpoint is persisted, the external-evaluation script re-derives each trained model from scratch, and it hard-coded M2's learning rate at 3 × 10⁻⁴ — a value left over from an earlier retrain. Under the normalized pipeline M2's learning-rate search selects 1 × 10⁻³ (Table 5), so M2's external figures were being produced by a model trained differently from the one supplying its in-distribution numbers.

The hard-coded constant has been replaced by a recorded one: each training script now writes the learning rate it actually used, and every rebuild path reads it back, raising an error rather than guessing if the record is absent. The correction is verifiable — under the recorded rate the rebuild's per-epoch training curve is byte-identical to the training run of record, which the 3 × 10⁻⁴ rebuild demonstrably was not. M2's rows in both external evaluations were then re-measured. Its authentic-only external accuracy moves from 91.3% to **86.0%** and its generalization gap from −6.7 to **−1.4** points; on the synthetic proxy its accuracy moves from 0.623 to 0.633 and its ROC-AUC from 0.788 to 0.794. Every qualitative claim in this paper is unchanged: M2 remains the best-generalizing model and the only one with a negative gap. The superseded values are preserved alongside the current ones in the archived results.

**Checkpoints, and the third divergence they immediately exposed.** The architectural weakness behind both defects above — that no weights were ever saved, so every downstream consumer re-derived "the trained model" by retraining it — has now been removed. Each training run persists the restored best-validation state together with the learning rate, seed, best epoch and epoch count it was produced under, and the loader refuses to return a checkpoint whose recorded learning rate differs from the one the caller expects, which is exactly the mismatch that produced the Model 2 defect.

Persisting checkpoints required re-running the three trainable models, and that re-run disclosed a third discrepancy which we report rather than quietly adopt. M2 and M3 reproduced their recorded Split B test accuracies exactly (0.865 and 0.932). **M4 did not: it now scores 0.919 (68/74) where the previously committed results recorded 0.946 (70/74)** — a two-image difference, with a training trajectory that early-stops at epoch 18 rather than running to 26.

We investigated and can report what is and is not established. The current value is *reproducible*: three consecutive re-runs of M4 produced byte-identical training curves and metric files, so the pipeline is deterministic as it now stands, and the determinism check previously performed on M3 (Finding 13) now holds for M4 as well. The normalization operator is confirmed active in that run (a normalized and an un-normalized tensor for the same image differ by 0.44 in mean absolute value). The split and pool files are unchanged since they were built. What we cannot establish is the *cause* of the difference from the earlier run, because the artifacts that would identify it — that run's weights and cached features — were never saved, which is the very defect being fixed. The most likely explanation is an intermediate code state during the several rounds of normalization and learning-rate work, but we cannot demonstrate it.

We therefore report 0.919 as M4's Split B accuracy of record, since it is the value the committed, deterministic pipeline produces and the one every derived table has been regenerated from. Its consequences are stated where they arise: M4's leakage delta rises from +4.1 to +6.8 points (Table 10), the smallest pairwise *p*-value rises from 0.057 to 0.118 (Table 11), and M4's pooled error count rises from 5 to 7 (Table 12). No qualitative claim in this paper changes — the leakage effect remains small and bounded, no model comparison approaches significance, and the external results are unaffected — but the episode is the clearest possible demonstration of why the checkpoint omission mattered, and of the fact that it was caught only because the omission was finally repaired.

**A fourth defect, in a path that never checked itself.** While building the attention audit of Section VII-G we found that all three Grad-CAM scripts obtained the backbone by calling its constructor directly, which returns a module in training mode, and set only the classification head to evaluation mode. The backbone's 49 batch-normalization layers therefore ran on batch-of-one statistics and overwrote their running averages on every image. This was invisible for as long as nobody asked the scripts for a number that could be checked: the heatmaps looked plausible. It surfaced immediately once a script printed its external accuracy alongside the heatmaps and that figure read 0.16 against the 0.807 of record. Section VII-G states the consequence for Fig. 14; the scripts now force evaluation mode and the quantitative audit asserts its accuracy against the value of record before reporting anything.

Two lessons generalize beyond this study, and both are uncomfortable.

The first concerns persistence: a pipeline can be fully seeded, deterministic on re-run, and still fail to reproduce its own published numbers, if nothing durable was saved at the moment those numbers were produced. Determinism is a property of the code; reproducibility of a *result* additionally requires that the artifact be persisted.

The second concerns verification, and is the one we would emphasize. All four defects in this study — a stale learning rate, an unseeded augmentation pass, an unreproducible accuracy, and a backbone in the wrong mode — occurred in code paths that produced an output nobody could check against a known value. The evaluation and training paths, which produce accuracies that are compared against each other constantly, were correct throughout. The generalisable practice is therefore cheap and specific: **any script that rebuilds or reloads a model should compute one metric whose correct value is already known, and refuse to report anything if it disagrees.** Every one of these defects would have been caught on first execution by that single line.

---

## VII. Results

All results in this section come from the deterministic, three-way-normalized production pipeline, except where a table explicitly reports a baseline condition for contrast. Complete machine-readable tables are in `paper/tables/`.

### A. The capture-method confound

Every one of the 510 pool filenames falls into exactly one of two patterns, and **the pattern predicts the class label with no exceptions** (Table 6): 272/272 authentic files are `images*.jpg`, 238/238 counterfeit files are `Screenshot*.png`. We recomputed this cross-tabulation independently for this paper from per-image statistics; it is exact, not approximate.

The separation is not an artifact of our filtering. It holds identically in the archive as distributed: all 240 files in `Fake/` are `Screenshot*.png` and all 421 files in `Real/` are `images*.jpg`. Any study using this dataset in any form, filtered or unfiltered, inherits it in full. The consequence is worth stating in its strongest form: a classifier reading nothing but the file extension achieves **100% accuracy** on this dataset, which places the ceiling attributable to acquisition metadata alone at the maximum possible value and makes any pixel-based accuracy figure on this pool uninterpretable without an external check.

**TABLE 6.** The two acquisition pipelines in the Kaggle pool, and the external set's position relative to both. Brightness is the mean RGB value at 64 × 64, on a 0–1 scale.

| Group | n | Capture pattern | Mean brightness | Median short side (px) | Mean file size |
|---|---|---|---|---|---|
| Kaggle authentic | 272 | `images*.jpg` (100%) | 0.767 | 223 | 6.0 kB |
| Kaggle counterfeit | 238 | `Screenshot*.png` (100%) | 0.555 | 405 | 339 kB |
| Split C external (authentic) | 150 | device photograph | **0.162** | **2448** | 1,656 kB |
| Split C synthetic (proxy counterfeit) | 150 | perturbed copy of the above | 0.153 | 2448 | 1,018 kB |

Throughout this paper kB = 1000 bytes.

A two-sample *t*-test on brightness between the two Kaggle classes gives *t* = 17.0, *p* ≈ 0 — not a subtle effect, but one of the strongest and most trivially learnable signals present anywhere in the training data. Figure 3 shows the full distributions and makes the second, equally important point: the external set does not sit *between* the two training classes on these axes, it sits far outside both. It is roughly 10× higher in linear resolution than the average Kaggle image and substantially *darker* than even the Kaggle counterfeit class. A model that has learned "bright, small, heavily compressed → authentic", even partially, has every statistical reason to label every external photograph counterfeit.

> **FIGURE 3.** `paper/figures/fig03_capture_confound.pdf` — Distributions of the three confounded statistics. (a) Brightness: violin plots with group means labeled. (b) Short-side resolution, log scale, with medians. (c) File size, log scale, with means. The external set lies outside the range of both training classes on all three axes.

The confound is directly visible in the decision function of the simplest model. Figure 12(a) plots M1's 96 logistic-regression coefficients: 93 of them lie within ±0.35 of zero, while the top intensity bin (248–255) of each of the three channels carries a large negative weight (β = −2.86, −2.84, −2.95), i.e. "many near-white pixels → authentic". The exact Shapley decomposition of Eq. (10) confirms this is not merely a large coefficient on a rarely varying feature: those same three features have mean |φ| of 0.079–0.082 on the Split B test partition, against ≤ 0.002 for every one of the remaining 93 (Fig. 12(b)). M1's 83.8% in-distribution accuracy is, to a good approximation, a measurement of how much white a photograph contains.

> **FIGURE 12.** `paper/figures/fig12_model1_attribution.pdf` — (a) M1's logistic-regression coefficients across the 32 intensity bins of each RGB channel; the near-white bin dominates all three channels. (b) The eight features with the largest mean |Shapley value| on the Split B test partition. Attribution is exact for this model, not sampled.

**A metadata-only oracle bounds the confound directly.** M1 is a useful diagnostic but an imperfect bound, because a 96-bin color histogram does read pixel intensities and could in principle carry some packaging information. We therefore fitted the same logistic regression to the three acquisition statistics of Table 6 and nothing else — mean brightness, log short-side resolution, log encoded file size — with no pixels, no spatial structure and no color information at all. Three scalars per image, 4 learned parameters, trained on each split's own training partition (Table 7).

**TABLE 7.** Metadata-only oracle. Features are per-image acquisition statistics, not image content; resolution and file size enter as log₁₀. The deterministic rule uses only the filename extension and is not fitted. Intervals are 95% Wilson.

| Classifier | Features | Split A test (n = 76) | Split B test (n = 74) |
|---|---|---|---|
| Deterministic rule: `.png` → counterfeit | file extension | 510/510 = **1.000** [0.993, 1.000] over the whole pool | — |
| Metadata LR | brightness | 0.829 [0.729, 0.897] | 0.716 [0.605, 0.806] |
| Metadata LR | short-side resolution | 0.947 [0.872, 0.979] | 0.946 [0.869, 0.979] |
| Metadata LR | encoded file size | 0.974 [0.909, 0.993] | **1.000** [0.951, 1.000] |
| Metadata LR | all three | 0.974 [0.909, 0.993] | **1.000** [0.951, 1.000] |

Three things follow, and they are stronger than anything the pixel-based models in this study establish.

First, **a single scalar that is not an image classifies this dataset perfectly.** Encoded file size alone reaches 74/74 on the leakage-free Split B test partition. That is above every trained model in this paper, including M4's 0.946 on the same partition (Table 9), and it uses no pixel at all.

Second, **the accuracy ceiling attributable to acquisition alone is 1.000.** The deterministic file-extension rule is correct on all 510 pool images by construction. There is therefore no accuracy figure obtainable on this dataset that requires any packaging information to explain, and no in-distribution result on it — ours or anyone's — can be evidence of packaging-authentication ability. This is the sense in which the dataset is not merely confounded but uninformative for its stated task.

Third, **brightness is the weakest of the three axes, not the strongest.** On its own it reaches only 0.716 on Split B, well below resolution (0.946) and file size (1.000), despite giving the largest *t*-statistic. Large mean separation and high discriminability are different properties: the brightness distributions have very different means but substantial overlap, whereas the file-size distributions barely overlap at all. This resolves what would otherwise look like a tension in Section VIII-A, where compression normalization is the axis with the largest marginal contribution when added last, and it is a caution against ranking candidate confounds by *t*-statistic — the audit should fit a classifier to each candidate statistic, which costs no more than computing the *t*-test does.

### B. The same audit on a second, independently published dataset

One dataset cannot establish a general claim, so we ran the identical procedure against the other public authentic/counterfeit pharmaceutical image dataset we were able to obtain — the Roboflow source of Section III-B, a different publisher, a different country of origin and a different class-construction method. Both are audited **as shipped**, before any filtering of ours, under grouped 5-fold cross-validation on rotation-canonical pHash clusters so that a publisher's own augmented copies cannot straddle a fold. Balanced accuracy is reported because both are heavily imbalanced as distributed; 0.5 means metadata carries nothing about the label (Table 8).

**TABLE 8.** The provenance-confound audit on two independently published datasets, as shipped. Grouped 5-fold cross-validated balanced accuracy of a logistic regression on the named metadata alone — no pixel content. Chance is 0.500.

| Metadata used | Kaggle (661 imgs, 584 groups) | Roboflow v4 (4,207 imgs, 597 groups) |
|---|---|---|
| File format | **1.000** | 0.500 (single-format archive) |
| Encoded file size | 0.994 | 0.717 |
| Short-side resolution | 0.954 | 0.500 (all 640 × 640) |
| Aspect ratio | 0.803 | 0.500 |
| All of the above | **1.000** | 0.717 |

The two columns fail differently, and the contrast is the most transferable result in this paper.

On the Kaggle dataset the audit is decisive on every axis it tests, including one we had not anticipated: **aspect ratio alone reaches 0.803**, because screen captures inherit display proportions that photographs do not. A confound of this kind is not a single leak to be plugged; it is present redundantly in every statistic the acquisition process touches, which is why Section VIII finds three normalization axes each contributing separately.

On the Roboflow dataset the audit largely **fails to fire** — and that dataset is nonetheless catastrophically confounded, in the most extreme way documented in this study: 57/57 of its counterfeit-labeled source images are advisory-bulletin graphics carrying the ground-truth word rendered in the pixels, against 263/263 clean product photographs labeled authentic (Section III-B). Metadata sees only a partial trace of this (0.717 from file size, which registers that bulletin collages compress differently from product photography) and nothing at all from format, resolution or aspect ratio.

The reason it sees so little is worth stating explicitly, because it is a trap rather than a limitation of one dataset. **The Roboflow publisher normalized the archive** — every image was resized to 640 × 640 and re-encoded to a single format before distribution. That normalization destroyed the acquisition *tells* without touching the acquisition *confound*. A dataset that has been tidied for release therefore looks cleaner under this audit than a raw one, while being no less confounded, and the audit's silence on such a dataset is uninformative rather than reassuring.

This is why we present the audit as a **necessary but not sufficient** screen, and pair it with the two checks that did catch the Roboflow problem: a modality/content pass over a sample of each class (Section III-E), and cross-source near-duplicate hashing (Section IV-B). Section IX-F sets out the resulting taxonomy.


### C. In-distribution performance and the leakage comparison

One definition governs everything in this section. "Leakage-free", here and throughout, means free of **product-identity** leakage: Split B guarantees that no perceptual-hash cluster of near-duplicate photographs straddles a partition or a cross-validation fold. It makes no claim about acquisition. Because every counterfeit-labeled image in the pool was produced by one capture pipeline and every authentic-labeled image by another (Section VII-A), *no* partition of this pool can place a capture process on only one side of a fold, and grouped cross-validation inherits the confound in every fold at full strength. The numbers below are therefore the best in-distribution estimates obtainable on this data and are still, in the sense Section VII-D makes precise, measurements of the acquisition process. Readers should not read Split B as a corrected evaluation; it corrects one of the two problems.

Table 9 gives the complete metric set for all four models on both in-distribution test partitions; Fig. 6 gives the corresponding confusion matrices, Fig. 4 the ROC curves and Fig. 5 the precision–recall curves.

**TABLE 9.** In-distribution test performance. Counterfeit is the positive class. Sens = recall. BA = balanced accuracy. Bracketed intervals are 95% percentile bootstrap (2000 resamples).

| Model | Split | n | TP | FP | FN | TN | Accuracy | Precision | Sens | Spec | F1 | BA | MCC | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 hist+LR | A | 76 | 33 | 10 | 2 | 31 | 0.842 [0.763, 0.921] | 0.767 | 0.943 | 0.756 | 0.846 | 0.850 | 0.703 | 0.893 | 0.831 |
| M1 hist+LR | B | 74 | 35 | 12 | 0 | 27 | 0.838 [0.743, 0.919] | 0.745 | 1.000 | 0.692 | 0.854 | 0.846 | 0.718 | 0.897 | 0.864 |
| M2 CNN | A | 76 | 29 | 4 | 6 | 37 | 0.868 [0.789, 0.934] | 0.879 | 0.829 | 0.902 | 0.853 | 0.865 | 0.735 | 0.951 | 0.948 |
| M2 CNN | B | 74 | 31 | 6 | 4 | 33 | 0.865 [0.784, 0.932] | 0.838 | 0.886 | 0.846 | 0.861 | 0.866 | 0.731 | 0.916 | 0.903 |
| M3 MobileNetV3 | A | 76 | 31 | 1 | 4 | 40 | 0.934 [0.868, 0.987] | 0.969 | 0.886 | 0.976 | 0.925 | 0.931 | 0.870 | 0.995 | 0.995 |
| M3 MobileNetV3 | B | 74 | 31 | 1 | 4 | 38 | 0.932 [0.865, 0.986] | 0.969 | 0.886 | 0.974 | 0.925 | 0.930 | 0.867 | 0.987 | 0.987 |
| M4 EfficientNet-B0 | A | 76 | 34 | 0 | 1 | 41 | **0.987** [0.961, 1.000] | 1.000 | 0.971 | 1.000 | 0.986 | 0.986 | 0.974 | 0.998 | 0.998 |
| M4 EfficientNet-B0 | B | 74 | 30 | 1 | 5 | 38 | 0.919 [0.851, 0.973] | 0.968 | 0.857 | 0.974 | 0.909 | 0.916 | 0.841 | 0.988 | 0.986 |

**TABLE 10.** Leakage quantification. Δ is Split A accuracy minus Split B accuracy; a positive Δ is the direction the naive-split-inflates-accuracy hypothesis predicts. Split B CV is 5-fold `StratifiedGroupKFold` on the Split B training partition. Throughout this paper "leakage-free" means free of **product-identity** leakage only. The grouping decorrelates which products appear in which fold and nothing else; it cannot decorrelate acquisition, because every counterfeit-labeled image in the pool came from one capture pipeline. Every number in this table is therefore measured under the provenance confound, which is the point of Section VII-D.

| Model | Split A accuracy (95% CI) | Split B accuracy (95% CI) | Split B 5-fold CV | Δ (A − B) |
|---|---|---|---|---|
| M1 hist+LR | 0.842 [0.763, 0.921] | 0.838 [0.743, 0.919] | 0.832 ± 0.049 | +0.004 |
| M2 CNN | 0.868 [0.789, 0.934] | 0.865 [0.784, 0.932] | 0.865 ± 0.036 | +0.004 |
| M3 MobileNetV3 | 0.934 [0.868, 0.987] | 0.932 [0.865, 0.986] | 0.964 ± 0.011 | +0.002 |
| M4 EfficientNet-B0 | 0.987 [0.961, 1.000] | 0.919 [0.851, 0.973] | 0.983 ± 0.011 | **+0.068** |

The leakage effect is real but small, and only M4 shows it at a magnitude worth discussing (Fig. 13). Three of four deltas are within half a percentage point of zero, and even M4's 6.8-point delta sits inside overlapping confidence intervals (Split A [0.961, 1.000] against Split B [0.851, 0.973]). The mechanism is not in doubt — Split B provably eliminates the 9 straddling product groups that Split A permits — but its *magnitude* on this pool can be bounded exactly, and the bound is more informative than the measurement.

Counting directly: **7 of the 76 Split A test images belong to a product-identity group that also appears in Split A's training partition.** Those seven are the only images any model could classify correctly by recognizing a training photograph rather than by generalizing. No leakage mechanism, for any model, seed or architecture, can therefore inflate Split A test accuracy by more than 7/76 = **9.2 points**. The ceiling follows from the split alone, involving no model and no run, so it is immune to the sampling-variance objection that limits the measured deltas — which duly fall below it (+0.2 to +4.1 points).

The available conclusion is therefore stronger than "we measured a small effect that might be noise": on a pool with this duplicate structure image-level leakage *cannot* be the dominant inflation mechanism, because the arithmetic caps it at 9.2 points while the external collapse of Section VII-D is worth more than 90. A dataset with heavier duplicate sourcing would raise the ceiling and might show a clearer effect; we report the ceiling alongside the measurement so the two are not confused.

> **FIGURE 13.** `paper/figures/fig13_leakage.pdf` — Split A vs. Split B test accuracy per model with 95% bootstrap intervals and the per-model delta.

**No pairwise model difference is statistically significant** (Table 11). Discordant counts are small — for M3 vs. M4 only three test images are classified differently — and the smallest *p*-value is 0.118, for the comparison between the 97-parameter linear baseline and frozen MobileNetV3.

"Not significant" conflates two different situations, and separating them matters, because only one of them is a statement about the models. Since McNemar's exact test depends only on the discordant pairs, the most significant *p*-value *available* at a given discordant total can be computed directly. For five of the six pairs it lies between 0.0001 and 0.002, so those comparisons could have detected a difference had one existed, and their non-significance is genuine evidence that the models perform alike on this partition. The sixth, M3 vs. M4, has a discordant total of 3, for which the most significant *p*-value obtainable is 0.250: **no split of three discordant pairs can reach *p* < 0.05, so that comparison was unresolvable by construction** and is not evidence of equivalence at all.

The power this affords is poor in absolute terms. At the observed discordance levels, reaching *p* < 0.05 requires a net difference of essentially the entire discordant set — 10 of 74 test images at D = 10, 14 at D = 14 — an accuracy gap of 13.5 to 18.9 points. **This design could only have detected between-model differences larger than roughly 13 points.** Every model in the roster sits within 15 points of every other in-distribution, so it was never capable of separating them, and no ranking in this paper should be read as one. That is a property of the dataset's size, not a finding about architectures.

**TABLE 11.** Pairwise McNemar's tests on the Split B test partition (n = 74), exact binomial. $n_{01}$: A correct, B wrong. $n_{10}$: A wrong, B correct.

| Model A | Model B | $n_{01}$ | $n_{10}$ | Discordant | *p* | Significant (α = 0.05) |
|---|---|---|---|---|---|---|
| M1 | M2 | 5 | 7 | 12 | 0.774 | no |
| M1 | M3 | 4 | 11 | 15 | 0.118 | no |
| M1 | M4 | 5 | 11 | 16 | 0.210 | no |
| M2 | M3 | 3 | 8 | 11 | 0.227 | no |
| M2 | M4 | 4 | 8 | 12 | 0.388 | no |
| M3 | M4 | 2 | 1 | 3 | 1.000 | no |

Six pairwise tests on one partition raises the question of family-wise error, and here it resolves trivially: no comparison is significant before correction, so no correction can make one significant. For completeness, Holm–Bonferroni over the six raises the smallest adjusted *p* from 0.118 to 0.711 and pins the remaining five at 1.000. The conclusion — that this partition cannot distinguish a 97-parameter linear model from a 4-million-parameter pretrained backbone — is therefore robust to the correction and, if anything, understated without it. The reverse risk, that correction masks a real difference, is addressed by the power calculation below rather than by the tests themselves.

Multiplicity is worth a word for the rest of the paper too, because the manuscript reports a great many comparisons. Only Table 11 contains hypothesis tests; every other comparison here — the leakage deltas, the per-axis ablations, the constant sweep, the ordering sweep — is a point estimate reported with its interval where one exists, and none is accompanied by a *p*-value or described as significant. They are not a test family and no correction applies to them. What does apply is the weaker caution stated in Section X: they are single realisations, so a difference of a point or two between two conditions should not be read as a difference at all, and we draw conclusions only from separations far larger than that, such as the 28-point gap between the two ordering groups in Section VIII-F.

Two further in-distribution observations. First, the training curves (Fig. 7) show the expected pattern: the frozen-backbone heads converge smoothly to near-zero loss, while the from-scratch CNN plateaus with a noisy validation curve and stops at epoch 13, consistent with its 23,938-parameter capacity being the binding constraint rather than overfitting. Second, calibration differs sharply across models (Fig. 11). M1's predicted probabilities are compressed into roughly [0.33, 0.56] — it separates the classes largely by which side of 0.5 a narrow band of scores falls on — whereas M3 and M4 are strongly saturated near 0 and 1. This becomes important in Section VII-F.

> **FIGURE 4.** `paper/figures/fig04_roc.pdf` — ROC curves, both in-distribution partitions, with AUCs.
> **FIGURE 5.** `paper/figures/fig05_pr.pdf` — Precision–recall curves, both partitions, with average precision.
> **FIGURE 6.** `paper/figures/fig06_confusion_ab.pdf` — Confusion matrices, all four models, both partitions.
> **FIGURE 7.** `paper/figures/fig07_training_curves.pdf` — Split B training and validation loss and accuracy; the filled marker is the restored best-validation-loss epoch.
> **FIGURE 11.** `paper/figures/fig11_calibration.pdf` — (a) Reliability curves on Split B test. (b) Per-model score distributions by true class.

### D. External generalization: the result that matters

Table 12 and Fig. 8 give the central result of this paper.

**TABLE 12.** External generalization on 150 independently captured authentic photographs. "Baseline" is the production run immediately before three-way normalization became the default; "normalized" is the current pipeline. In-distribution reference is authentic-class accuracy on each model's own Split B test partition (n = 39 authentic). Δ follows Eq. (15). M1 does not pass through the normalization operator in the production pipeline; that exclusion was decided empirically after the fact, not a priori, and Section VIII-C reports what happens when the operator is applied to it anyway (Table 22). Bracketed intervals are 95% Wilson score intervals on the underlying counts, given as k/n; they quantify sampling uncertainty on a fixed trained model and not training-run variance, which would require repeated seeds.

| Model | In-distribution authentic accuracy (k = 39) | Split C, baseline (n = 150) | Split C, 3-way normalized (n = 150) | Δ (normalized) |
|---|---|---|---|---|
| M1 hist+LR | 27/39 = 0.692 [0.536, 0.814] | 0/150 = 0.000 [0.000, 0.025] | 0/150 = 0.000 [0.000, 0.025] | +0.692 |
| M2 CNN | 33/39 = 0.846 [0.703, 0.928] | 0/150 = 0.000 [0.000, 0.025] | 129/150 = **0.860** [0.795, 0.907] | **−0.014** |
| M3 MobileNetV3 | 38/39 = 0.974 [0.868, 0.995] | 104/150 = 0.693 [0.615, 0.762] | 116/150 = 0.773 [0.700, 0.833] | +0.201 |
| M4 EfficientNet-B0 | 38/39 = 0.974 [0.868, 0.995] | 5/150 = 0.033 [0.014, 0.076] | 121/150 = 0.807 [0.736, 0.862] | +0.167 |

Read the baseline column first. Two of the four models classified **zero of 150** external authentic photographs correctly, and the model with the best in-distribution accuracy in the entire study (M4, 0.987 on Split A) classified **3.3%** correctly. These are not degradations; they are near-complete inversions on the easiest possible external case, a test set containing only the class the models were most accurate on in-distribution. A model at 94.6% on Split B that recovers 3.3% of plainly authentic external photographs has not learned to recognize authentic packaging. It has learned to recognize this dataset's photography.

Now read the normalized column. The same models, retrained on the same images with the same seeds and hyperparameters, differing only by the label-free operator of Eq. (8), recover 86.0%, 77.3% and 80.7%. The in-distribution price is negligible: over the same transition, Split B test accuracy moves 0.865 → 0.865 (M2), 0.946 → 0.932 (M3) and 0.919 → 0.919 (M4), i.e. between −1.4 and 0.0 points. Two of the three models are unchanged to three decimal places and the third loses 1.4 points, well inside its bootstrap interval. The correction is close to free in-distribution while being worth 77 to 86 points externally. M2's external accuracy exceeds its own in-distribution accuracy, giving the only negative generalization gap anywhere in this study — which is intelligible rather than paradoxical: with the shortcut suppressed, its in-distribution test partition (mixed classes, small, adversarially hard for a 23,938-parameter model) is simply a harder problem than "is this well-lit photograph of an intact carton authentic?". M1, which never passes through the operator, is unchanged at 0.000 — and Section VIII-C shows that applying the operator to it does not help either.

The intervals separate the models' claims sharply, and one of them should be read down. M2's and M4's gains are far outside sampling uncertainty — 0/150 to 129/150 and 5/150 to 122/150, with non-overlapping intervals in both cases — so those two results are secure against the objection that Split C is only 150 images. M3's are not: 104/150 [0.615, 0.762] to 116/150 [0.700, 0.833] is a 12-image difference whose intervals overlap substantially, and it is consistent with no effect. Combined with Section VIII-B's finding that M3's answer to this question changed sign twice across runs, **we do not claim a normalization benefit for M3**; the honest statement is that it is the one model where the effect is neither established nor excluded. The paper's headline claim rests on M2 and M4.

> **FIGURE 8.** `paper/figures/fig08_external_generalisation.pdf` — In-distribution authentic accuracy against external accuracy before and after three-way normalization, per model.

### E. A second external distribution, and what it costs the headline

Section IX-C warns that a shortcut coinciding with one external distribution is indistinguishable from robustness until a second, differently constructed evaluation disagrees. We made that warning testable. Split D is the same source's "iphone 11 pro" subset — 149 unique images (the archive ships one duplicate filename), the **same 150 products** as Split C, photographed on different hardware under the source's deliberately different lighting protocol. Measured: mean brightness 0.389 against Split C's 0.162 and the training pool's 0.668, so it is a different point on the confounded axis rather than a repeat; median short side 2419 px; and rotation-canonical pHash puts only 1 of 149 within the near-duplicate threshold of any Split C image (median distance 18), so despite depicting the same products the two sets are not pixel-interchangeable.

Because content is held fixed and only acquisition varies, this is a **paired capture-shift test**. It is not an independent product sample and says nothing about generalization across products; it isolates exactly the axis this paper is about. Both sets are authentic-only, so both measure the false-positive rate. All four models were evaluated from their persisted Split B checkpoints (Section VI-E), so the model tested here is provably the one that produced the in-distribution numbers; Table 13 gives the result.

**TABLE 13.** The same corrected models on two external distributions. Both authentic-only; accuracy is the fraction correctly called authentic, with 95% Wilson intervals. Split C and Split D photograph the same products under different capture conditions.

| Model | Split C (n = 150) | Split D (n = 149) | Change |
|---|---|---|---|
| M1 hist+LR | 0/150 = 0.000 [0.000, 0.025] | 0/149 = 0.000 [0.000, 0.025] | 0.0 |
| M2 CNN | 129/150 = **0.860** [0.795, 0.907] | 69/149 = **0.463** [0.385, 0.543] | **−39.7** |
| M3 MobileNetV3 | 116/150 = 0.773 [0.700, 0.833] | 108/149 = 0.725 [0.648, 0.790] | −4.9 |
| M4 EfficientNet-B0 | 121/150 = 0.807 [0.736, 0.862] | 124/149 = 0.832 [0.764, 0.884] | +2.6 |

Two of the three findings here are uncomfortable for the rest of this paper, and we state them before the reassuring one.

**The correction does not transfer uniformly across capture shifts, and the model it fails for is the one we had called the best generaliser.** M2 loses 39.7 points between the two external sets — from 0.860, the highest external accuracy in the study, to 0.463, barely above the rate obtained by calling everything counterfeit. Its two intervals do not come close to overlapping. Whatever M2 learned that let it succeed on Split C after correction did not survive a change of camera, even with the same products, the same normalization and the same authentic label.

**The paper's own caution about M3 applies to M2.** Section IX-C argues that M3's strong *uncorrected* external accuracy was a backdrop-matching rule that happened to fit Split C. The same argument now applies, on this evidence, to M2's strong *corrected* external accuracy: a single external distribution could not distinguish a general repair from one that fits Split C in particular, and the second distribution says it was substantially the latter. We had the right diagnostic and did not apply it to our own headline until now.

**The two pretrained backbones hold their accuracy across the shift.** M3 moves −4.9 points and M4 +2.6, both with comfortably overlapping intervals, so neither change is distinguishable from sampling noise at these sample sizes. Across both external distributions M4 is the most stable model (0.807 and 0.832) and M3 the next (0.773 and 0.725).

We deliberately do not describe this as the backbones generalizing. Section VII-G's attention audit finds that on external images both models take their evidence for "authentic" from the background rather than the product, without exception in 40 heatmaps — and Split C and Split D share the same dark backdrop, differing in device and lighting but not in staging. A model applying a backdrop rule would hold its accuracy across exactly this shift. **Split D tests the capture-pipeline confound and leaves the backdrop cue untouched**, so the right reading of these two rows is that the backbones' accuracy survives a change of camera, not that it rests on packaging content.

The net effect on this paper's claim is a real narrowing. The correction of Section V-D demonstrably repairs external generalization **for frozen pretrained backbones across two capture shifts**, and demonstrably fails to do so for a small from-scratch CNN on the second shift. The earlier framing — that normalization recovers 77–86% externally — was measured on one distribution and does not hold as a general statement. Section X records what remains unmeasured: two capture conditions from one archive is still a narrow basis, and nothing here tests generalization across products, sources or countries.

### F. Synthetic counterfeit-proxy stress test

Split C is authentic-only and therefore silent on counterfeit recall. Table 14 reports all four models on the 300-image synthetic proxy of Section V-F. As stated there, this measures robustness to a specific documented perturbation style, not real-world counterfeit recall.

**TABLE 14.** Synthetic counterfeit-proxy Split C (150 authentic + 150 perturbed copies of those same photographs). Confusion counts are exact. PR-AUC is not reported because per-image scores were not persisted by the evaluation script; this is a tooling gap, not a property of the data. 95% intervals, n = 300 with 150 per class — accuracy (Wilson): M1 0.500 [0.444, 0.556], M2 0.633 [0.577, 0.686], M3 0.483 [0.427, 0.540], M4 0.550 [0.493, 0.605]; **M4's row here predates the Split B correction of Section VI-E** and so describes the superseded 0.946 model rather than the 0.919 one; the two differ by two in-distribution images, and M4's qualitative verdict (weak separation at best, accuracy interval spanning 0.5) does not depend on which is used; ROC-AUC (Hanley–McNeil closed form, used because per-image scores are unavailable for a bootstrap): M1 0.895 [0.859, 0.932], M2 0.794 [0.743, 0.845], M3 0.503 [0.438, 0.569], M4 0.570 [0.505, 0.634].

| Model | TP | FP | FN | TN | Accuracy | Precision | Sens | Spec | F1 | BA | MCC | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 hist+LR | 150 | 150 | 0 | 0 | 0.500 | 0.500 | 1.000 | 0.000 | 0.667 | 0.500 | 0.000 | **0.895** |
| M2 CNN | 61 | 21 | 89 | 129 | 0.633 | 0.744 | 0.407 | 0.860 | 0.526 | 0.633 | 0.299 | 0.794 |
| M3 MobileNetV3 | 29 | 34 | 121 | 116 | 0.483 | 0.460 | 0.193 | 0.773 | 0.272 | 0.483 | −0.041 | 0.503 |
| M4 EfficientNet-B0 | 44 | 29 | 106 | 121 | 0.550 | 0.603 | 0.293 | 0.807 | 0.395 | 0.550 | 0.117 | 0.570 |

Three readings, in decreasing order of interest.

**M1's result is a calibration failure, not an absence of signal.** It labels essentially everything counterfeit (sensitivity 1.000, specificity 0.000, accuracy pinned at exactly 0.500 by the balanced design, MCC exactly 0) — yet it has by far the best ROC-AUC of the four at 0.895. Its raw scores rank perturbed images above clean ones well; its 0.5 threshold, fitted on the very different Kaggle brightness and resolution distribution, is simply in the wrong place for this set. Compare its 0.000 on the authentic-only Split C: the two results together say that M1's color-histogram features carry *some* transferable signal that its decision threshold cannot exploit out of distribution. This is consistent with the compressed score range visible in Fig. 11(b).

**M2 and M4 show modest genuine separation but under-detect.** AUCs of 0.794 and 0.570 with sensitivities of 0.407 and 0.293: at the default threshold both are far more likely to pass a synthetic counterfeit as authentic than the reverse — M2 misses 89 of 150 and M4 misses 106. For a screening application that error direction is the costly one. The two models are not on the same footing, and the intervals in Table 14's caption matter here: M2's AUC interval [0.743, 0.845] is comfortably clear of chance, whereas M4's [0.505, 0.634] excludes 0.5 only barely, and M4's *accuracy* interval [0.493, 0.605] does not exclude it at all. M4 should be described as weakly separating at best, and no ranking between M4 and M3 is supportable on this evidence.

**M3 is at chance (AUC 0.503, 95% CI [0.438, 0.569], MCC −0.041), and this cross-validates the attention finding of Section VII-G.** M3's comparatively strong authentic-only external accuracy is best explained by a backdrop-matching rule (Section VII-G); such a rule provides exactly zero signal for separating a photograph from a perturbed copy of *the same photograph*, since the backdrop is identical in both. Chance performance is what that explanation predicts, obtained here from a completely independent evaluation set.

> **FIGURE 9.** `paper/figures/fig09_confusion_synthetic.pdf` — Confusion matrices on the synthetic proxy, with accuracy and ROC-AUC per model.

### G. Attention audit

**All heatmaps in this section were regenerated after a defect described below, and categorized by a human annotator over the complete set — 62 of 62, not a sample.** Each map targets the model's *predicted* class, so a map on an image called counterfeit shows the evidence for "counterfeit", and a map on an image called authentic shows the evidence for "authentic". That distinction turns out to carry the result.

**In-distribution (M4, Split B), n = 22.** Nine of 22 (41%) place attention on packaging-relevant regions — logo, brand header, printed text — seven (32%) on incidental regions such as background, corners or backdrop, and six (27%) are mixed. Split by outcome, the pattern is mild but in the expected direction: of 15 correct predictions, 7 attend to the product and 3 to incidental regions; of 7 errors, 4 attend to incidental regions and 2 to the product. In-distribution, then, attention is unremarkable — mostly on the product, more often incidental when the model is wrong.

**External (M4 and M3, Split C), n = 20 each.** The external sets behave completely differently, and the two models behave *identically*:

| | attends to product | attends to background |
|---|---|---|
| M4, called authentic (correct) | 0/10 | **10/10** |
| M4, called counterfeit (wrong) | **10/10** | 0/10 |
| M3, called authentic (correct) | 0/10 | **10/10** |
| M3, called counterfeit (wrong) | **10/10** | 0/10 |

The separation is total, in both models, with no exceptions in 40 heatmaps. Read with the target-class convention above, it says something specific and damaging: **on external images these models take their evidence for "authentic" from the background, and their evidence for "counterfeit" from the product.** When either model gets an external image right, it is not because it recognized authentic packaging; it is responding to the photographic surround. When it gets one wrong, it is looking straight at the printed carton and concluding "counterfeit".

This supersedes and generalizes an earlier reading. A previous version of this analysis made a similar argument about M3 alone, from five heatmaps, and treated M4's external attention as evidence that the model was making a "spatially sensible decision calibrated to the wrong cue". With the complete set and corrected heatmaps, the finding is not specific to M3 and is not a point in M4's favor: both frozen backbones do the same thing, and the product-focused attention on M4's errors is the *failure* half of the pattern, not a redeeming feature.

It is consistent with the quantitative result of the previous subsection, though we put that more weakly than an earlier version of this paper did. Split C is 100% authentic, so the model predicts "authentic" on most of it, and a surround-driven prediction should push attention mass away from the center; the normalized model's border mass is 0.655 against a uniform reference of 0.642. That is in the predicted direction but it is also, in absolute terms, indistinguishable from uniform, so it corroborates the categorization only weakly and cannot be offered as independent confirmation of it.

The categorization itself is more robust to that objection than the aggregate statistic is, and the reason is worth stating because the objection is a fair one. Section VII-G's diffuseness result and the caveat that accompanies it — that a 128 px bottleneck degrades activation-based attribution — apply to the *magnitude and sharpness* of these maps. The finding here is not a magnitude but a **contrast**: within one model, one bottleneck and one external set, the maps for correct predictions and the maps for incorrect predictions fall on opposite sides of the frame, 20 out of 20 each, twice over. Degraded attribution adds noise, which would blur that split; it does not manufacture a perfect one that happens to align with the outcome. We therefore continue to report the differential result while declining, in the previous subsection, to interpret the absolute spatial distribution.

**The consequence for Split D.** Section VII-E reported that M3 and M4 hold up on the second external distribution while M2 collapses, and read that as the pretrained backbones transferring across a capture shift. The attention evidence forces a weaker reading. Split C and Split D are the same products photographed against **the same dark backdrop** under different devices and lighting; the surround changes in brightness and color but not in kind. A model predicting "authentic" from the presence of that backdrop would continue to do so on Split D. **Split D therefore does not test the shortcut these heatmaps identify**, and M3's and M4's stability across the two external sets is consistent with the shortcut persisting rather than with genuine packaging recognition. What Split D does establish stands — M2's Split C result was capture-specific — but it cannot be read as evidence that the backbones learned the intended task.

> **FIGURE 14.** `paper/figures/fig14_gradcam.pdf` — Grad-CAM overlays, six of the 62 categorized maps. (a)–(b) M4 in-distribution, one product-focused correct prediction and one error attending to background corners. (c)–(d) M4 external: an authentic photograph called counterfeit with attention on the printed name, and a correct authentic call with attention on the surround. (e)–(f) the same pair for M3. Panels (c)–(f) are representative in the strict sense: on the external sets the split shown here held for all 40 maps. Every heatmap was regenerated from the persisted production checkpoint after the defect described below.

**Coverage, and a defect in how these heatmaps were produced.** The categorisations above are illustrative samples, not exhaustive audits: 15 of 24 in-distribution heatmaps and 5 of 20 per external model, scored by a human. They also carry a defect we found only after the fact, and which we report because it bears on how much weight they can take.

The three Grad-CAM scripts obtained their backbone by calling the constructor directly, which returns a module in **training mode**, and set only the classification head to evaluation mode. With 49 batch-normalization layers in the backbone and Grad-CAM processing one image at a time, those layers therefore used batch-of-one statistics and overwrote their running averages on every call. The heatmaps in Fig. 14 consequently describe a mis-configured network rather than the trained model. We detected this only when a later script printed a sanity metric — its external accuracy read 0.16 against the 0.807 of record — and confirmed it by checking that, with evaluation mode set, a manually assembled feature path reproduces the production path to within 3 × 10⁻⁶. The scripts are fixed; the qualitative categorisations above are not re-run, because re-running them would require the human review again, and they are superseded for quantitative purposes by the audit below.

**A quantitative attention audit.** To replace a human judgement on a small sample with a measurement over the whole set, we compute the **border mass fraction** of each Grad-CAM map: the share of total attention mass falling in an outer frame occupying the outer 20% of each side. It requires no bounding-box annotation, which is what makes it runnable on all 150 external images, and it targets the specific failure the qualitative audit diagnosed — attention on backdrop, margins and corners rather than on the product. The border ring covers 0.642 of the frame, so 0.642 is the value for spatially uniform attention; below it means center-concentrated, above it means the surround is favored. Both conditions run on the same images with matching preprocessing, and the normalized condition loads the production checkpoint, so its Split C accuracy reproduces the 0.807 of record exactly (the un-normalized baseline has no checkpoint and is retrained, giving 9/150 against the archived 5/150).

| Condition | Border mass (95% CI) | Center mass | Split C accuracy |
|---|---|---|---|
| Uniform attention (reference) | 0.642 | 0.161 | — |
| Baseline, un-normalized | 0.182 [0.155, 0.209] | 0.563 | 0.060 |
| Three-way normalized | 0.655 [0.613, 0.697] | 0.165 | 0.807 |
| Paired change | **+0.473 [+0.422, +0.524]** | −0.398 | — |

The result does not flatter the correction, and is the more interesting for it. **Normalization does not move attention onto the product; it makes attention diffuse.** The un-normalized model is strongly center-concentrated — 0.563 of its attention mass in a center box covering 0.161 of the frame, a 3.5-fold over-representation on exactly the region where a centered product sits — and it classifies 6% of external images correctly. The normalized model distributes attention almost exactly uniformly (border 0.655 against a uniform 0.642; center 0.165 against 0.161) and classifies 80.7% correctly. Across these two conditions, spatial concentration of attention **anti-correlates** with external accuracy.

Two readings are available and this metric cannot separate them. The mechanical one: the resolution bottleneck caps the short side at 128 px before the 224 × 224 resize, so the normalized model's input carries little fine spatial structure for Grad-CAM to localize, and diffuseness is an artifact of the operator rather than a property of the decision. The substantive one: the model's evidence for "authentic packaging" is genuinely distributed across the image rather than concentrated in one region.

We take the mechanical reading to be the more likely of the two, and its consequence is a restriction on what this subsection may be used for. Grad-CAM localizes by weighting a convolutional feature map with gradients computed on it, so its spatial resolution is bounded by the spatial information that reaches that layer; an operator that deliberately removes high-frequency structure before the network sees anything therefore degrades the attribution as well as the input. **We accordingly make no claim about *what the normalized models see*.** The honest statement is narrower and negative: after normalization, activation-based attribution on these models carries little diagnostic signal, and the near-uniform maps should be read as a limitation of the method under an aggressive spatial bottleneck rather than as evidence of distributed reasoning. This generalizes past our pipeline — any preprocessing or architectural bottleneck that caps effective resolution should be expected to reduce the interpretability of Grad-CAM and its relatives, and reporting such maps without noting the bottleneck invites over-reading them.

One conclusion survives under either reading, and it is a caution against a common practice: **a visually convincing, product-centered Grad-CAM map is not evidence that a model has learned the intended task.** That claim rests on the *un-normalized* model, whose input is unaltered and whose attribution is therefore not in question — it is strongly product-centered, and it classifies 6% of external images correctly. The model whose attention looks most like it is reading the product is the one that fails externally.

### H. Error analysis

**TABLE 15.** Error counts pooled over both in-distribution test partitions (each model contributes 76 + 74 = 150 predictions).

| Model | Predictions | Errors | Error rate |
|---|---|---|---|
| M1 hist+LR | 150 | 24 | 16.0% |
| M2 CNN | 150 | 20 | 13.3% |
| M3 MobileNetV3 | 150 | 10 | 6.7% |
| M4 EfficientNet-B0 | 150 | 7 | 4.7% |
| Pooled | 600 | 61 | 10.2% |

Thirty-six distinct images account for all 61 errors, and six are misclassified by three or more independent model/split combinations. Three of those six were examined individually in an earlier round of this project, and their diagnoses are informative: one is the recurring carton whose Grad-CAM attention falls on background corners (a confound case); one is a sachet, well lit and legible with no visible defect, whose attention *does* fall on the product's regulatory logo (a genuine visual-similarity case, i.e. real task difficulty rather than a shortcut artifact); and one is a blister image on which the model attends to the tablets themselves. A fourth image examined in that round is a 100 × 100 px thumbnail, far below the pool's typical resolution, misclassified only by the two weakest models — a resolution/detail failure rather than an ambiguity.

The qualitative diagnoses above were made on the pre-normalization models; the counts in Table 15 are recomputed from the current models of record. Six of 36 error images is a deliberate, non-exhaustive sample selected for cross-model agreement, not a random one.

The shape of Table 15 is worth stating plainly against Section VII-D. In-distribution, these models make few errors and most of those errors are explicable. Externally, two of them were wrong on every single image. Both statements are true simultaneously, and a study reporting only the first would be describing a system that does not work as one that works well.

### I. Computational cost

**TABLE 16.** Measured cost, single image, CPU only (PyTorch 2.7.1, batch size 1, mean over the 74 Split B test images after warm-up). Preprocessing for M2–M4 is decode + three-way normalization + resize + tensor conversion; for M1 it is decode + resize + histogram. Weight memory is fp32 parameter storage.

| Model | Trainable params | Frozen params | Weight memory | Preprocess | Forward | Total | Throughput |
|---|---|---|---|---|---|---|---|
| M1 hist+LR | 97 | 0 | < 0.01 MiB | 18.2 ms | 0.01 ms | 18.2 ms | 54.9 img/s |
| M2 CNN | 23,938 | 0 | 0.09 MiB | 16.8 ms | 17.4 ms | 34.3 ms | 29.2 img/s |
| M3 MobileNetV3 | 1,154 | 927,008 | 3.54 MiB | 16.8 ms | 71.9 ms | 88.7 ms | 11.3 img/s |
| M4 EfficientNet-B0 | 2,562 | 4,007,548 | 15.30 MiB | 16.8 ms | 154.4 ms | 171.2 ms | 5.8 img/s |

Two points bear on deployment. First, preprocessing — including the entire three-way normalization — costs under 17 ms per image and is negligible relative to any CNN forward pass; the correction proposed in this paper is essentially free at inference time. Second, the accuracy/cost ordering is unhelpful for a field deployment: M4 costs 5× M2's total latency and 166× its weight memory for an in-distribution difference that Table 11 cannot distinguish statistically, while M2 is the model with the best external accuracy (Table 12).

**Training wall-clock time is not reported.** The original runs were not instrumented for it and the host repeatedly terminated long-running background processes during the project, so any retrospective figure would be unreliable. Epochs to convergence are reported instead (Table 17); every model trains on CPU in minutes, not hours, and the frozen-backbone models train on cached features so that an "epoch" involves no image decoding and no convolution.

**TABLE 17.** Epochs run and best-validation-loss epoch (M1 is a closed-form convex fit with no epochs).

| Model | Split | Epochs run | Best epoch | Best val loss | Best val accuracy |
|---|---|---|---|---|---|
| M2 CNN | A | 10 | 5 | 0.336 | 0.870 |
| M2 CNN | B | 13 | 8 | 0.259 | 0.924 |
| M3 MobileNetV3 | A | 15 | 10 | 0.073 | 0.974 |
| M3 MobileNetV3 | B | 37 | 36 | 0.057 | 0.962 |
| M4 EfficientNet-B0 | A | 13 | 8 | 0.099 | 0.974 |
| M4 EfficientNet-B0 | B | 26 | 23 | 0.031 | 1.000 |

### J. Calibration of the probability outputs

Everything above treats the models as decision rules at a fixed threshold. Any deployment as a triage tool would instead read the probability, so calibration is the property that decides whether the score can be thresholded at all — and Section VII-D reported, qualitatively, that the external errors arrive at predicted counterfeit probabilities of 0.94–1.00. Table 18 quantifies that from the persisted per-image scores, on all four partitions, with no retraining.

**TABLE 18.** Calibration on all four partitions, computed from the persisted per-image scores. Brier is the mean squared error of the predicted probability. ECE is expected calibration error over ten equal-width confidence bins; MCE is the worst single bin. Conf is mean confidence in the predicted class; conf − acc is positive for overconfidence. Splits C and D are authentic-only, so their accuracy is a false-positive rate and their calibration is measured against one class; see the caveat below.

| Model | Split | n | Brier | ECE | MCE | Conf | Acc | Conf − acc |
|---|---|---|---|---|---|---|---|---|
| M1 hist+LR | B | 74 | 0.207 | 0.277 | 0.372 | 0.561 | 0.838 | −0.277 |
| M1 hist+LR | C | 150 | 0.295 | **0.543** | 0.552 | 0.543 | 0.000 | **+0.543** |
| M1 hist+LR | D | 149 | 0.310 | **0.556** | 0.556 | 0.556 | 0.000 | **+0.556** |
| M2 CNN | B | 74 | 0.118 | 0.122 | 0.427 | 0.837 | 0.865 | −0.028 |
| M2 CNN | C | 150 | 0.112 | 0.118 | **0.962** | 0.790 | 0.860 | −0.070 |
| M2 CNN | D | 149 | **0.356** | **0.226** | **0.976** | 0.666 | 0.463 | **+0.203** |
| M3 MobileNetV3 | B | 74 | 0.052 | 0.064 | **0.852** | 0.960 | 0.932 | +0.028 |
| M3 MobileNetV3 | C | 150 | 0.149 | 0.083 | 0.292 | 0.809 | 0.773 | +0.036 |
| M3 MobileNetV3 | D | 149 | 0.183 | 0.117 | 0.228 | 0.801 | 0.725 | +0.076 |
| M4 EfficientNet-B0 | B | 74 | 0.053 | 0.061 | 0.748 | 0.956 | 0.919 | +0.037 |
| M4 EfficientNet-B0 | C | 150 | 0.132 | 0.098 | 0.381 | 0.781 | 0.807 | −0.025 |
| M4 EfficientNet-B0 | D | 149 | 0.113 | 0.055 | 0.166 | 0.815 | 0.832 | −0.018 |

Four readings, and the first is the one that matters.

**In-distribution calibration is as blind to the confound as in-distribution accuracy.** M3 and M4 return in-distribution ECEs of 0.064 and 0.061 — numbers a practitioner would read as a usably calibrated model — and M2 returns 0.122. Those same models are then wrong, at high confidence, on external data: M2's ECE triples to 0.226 on Split D with a Brier score three times its in-distribution value. Nothing measurable on the confounded partition anticipates this. Calibration is not an escape route from the paper's central problem; it is another quantity that the confound corrupts and that in-distribution evaluation cannot audit.

**Averages conceal the failure that matters; the worst bin does not.** M3's in-distribution ECE of 0.064 sits alongside an MCE of 0.852, and M2's excellent-looking Split C ECE of 0.118 alongside an MCE of 0.962. In both cases there exists a confidence bin in which the model is almost maximally confident and almost entirely wrong. Reporting ECE alone would hide exactly the behavior that makes an authentication tool dangerous, which is a confident false negative rather than an average miscalibration.

**M1 fails in an unusual and diagnostic direction.** In-distribution it is markedly *under*confident — mean confidence 0.561 against accuracy 0.838, an ECE of 0.277 driven entirely by scores that hug the decision boundary. Externally the same hugging behavior becomes maximal overconfidence, because it is wrong on 150 of 150 and 149 of 149 images while still reporting confidences of 0.54–0.56. This is the same object as the synthetic-proxy result of Section VII-F, where M1's ROC-AUC of 0.895 coexisted with accuracy pinned at exactly 0.500: its ranking carries some signal and its threshold carries none.

**M4 is the only model whose calibration survives both capture shifts** (0.061 → 0.098 → 0.055), which is consistent with its accuracy behavior in Table 14 and, like that result, says nothing about whether it is reading packaging — Section VII-G applies unchanged.

One caveat bounds all of this. Splits C and D contain only authentic images, so accuracy on them is a false-positive rate and the calibration statistics are measured against a single class; ECE and accuracy are therefore not independent quantities there in the way they are on Splits A and B, and the external rows should be read as a description of how confidently each model commits its false positives rather than as a full calibration curve. A counterfeit-labeled external set, which Section XI lists as the outstanding acquisition, is what would make external calibration measurable in the ordinary sense.

### K. The audit across application areas

Section VII-B applied the provenance audit to a second pharmaceutical dataset. That establishes the audit is not tuned to one archive, but it says nothing about the paper's wider claim, and Section I-A is explicit that the claim is a hypothesis rather than a measured rate. This subsection takes the first step of the survey that would test it, and it costs nothing to run: Kaggle's public dataset-file listing endpoint returns, without authentication, the path and encoded size of every file in a dataset. The path carries the class in the folder-per-class layout these archives use, and the extension carries the storage format, so two of the four audit features can be fitted on a dataset **as its publisher shipped it, without downloading a single image**. Table 19 reports the result for seven datasets spanning four application areas.

**TABLE 19.** The provenance audit run from public file listings alone, no images downloaded. Balanced accuracy under stratified 5-fold cross-validation; chance is 0.500. Format is the one-hot file extension, size is log encoded bytes. Ext-rule is the accuracy of the single deterministic rule "extension predicts class". Listings are paginated and the endpoint stops at 2,400 files, so large archives are sampled in listing order; a dataset whose sample never reaches its second class is reported as not auditable rather than scored.

| Dataset | Area | n | Format | Size | Both | Ext-rule |
|---|---|---|---|---|---|---|
| Kaggle *Fake vs Real Medicine* [19] | Medicines (positive control) | 2224 | **1.000** | 0.999 | **1.000** | **1.000** |
| `rhythmghai/ai-vs-real-images-dataset` | Generated images | 995 | **1.000** | 0.812 | **1.000** | **1.000** |
| `cashbowman/ai-generated-images-vs-real-images` | Generated images | 974 | 0.577 | 0.553 | 0.562 | 0.554 |
| `ishanikathuria/handwritten-signature-datasets` | Signatures (negative control) | 2400 | 0.500 | **0.843** | 0.845 | 0.560 |
| `kshitizbhargava/deepfake-face-images` | Deepfake faces | — | \* | \* | \* | \* |
| `shahzaibshazoo/detect-ai-generated-faces...` | Generated faces | — | \* | \* | \* | \* |
| `prosperchuks/fakereal-logo-detection-dataset` | Brand logos | — | \* | \* | \* | \* |

\* Not auditable from a listing: the sample reached only one class before the endpoint's file limit, so no within-dataset comparison is possible. This is a limitation of the sampling method, not a finding about the dataset.

Four things follow, and the last two are the useful ones.

**The positive control passes, by an independent route.** The case-study dataset returns 1.000 on format and 1.000 on the deterministic extension rule from its *public listing metadata alone* — no pixels, no download, no local pipeline. Section VII-A reached the same conclusion from the archive on disk. That the two agree is a check on this paper's central empirical claim using entirely different inputs.

**The confound appears in another application area, at full strength.** One of the two generated-image datasets is perfectly separable by file format, exactly as the medicine dataset is, and exactly as [30] reports for the GenImage benchmark. This is a third independent instance of the mechanism and the first this paper measured itself.

**But it does not appear everywhere, which is what makes the audit worth running.** The second generated-image dataset, in the same application area, returns 0.577 on format and 0.562 overall — near chance on these axes. A screen that fired on every dataset would carry no information; this one does not. It is also a caution against reading the mechanism as a law: two archives built for the same task by different people differ completely in whether they exhibit it.

**The negative control reveals a false-positive mode we had not anticipated, and it changes how the audit's output should be read.** Genuine and forged signatures in the BHSig260 corpus are written on the same paper and digitized by the same procedure, so there is no acquisition asymmetry to find, and the format axis duly returns exactly 0.500. Encoded size, however, returns **0.843**. The most plausible explanation is not provenance at all but content: forged signatures differ from genuine ones in stroke complexity and ink coverage, and ink coverage drives the compressed size of a bitonal scan. The audit is therefore answering a narrower question than "is this dataset confounded". It answers "can a trivial low-level statistic separate your classes", and the researcher must then determine whether that statistic is an acquisition artifact or a real property of the objects. Section IX-F's taxonomy gains a fourth entry accordingly, and the practical recommendation in Section XII is stated in those terms: a high score is a reason to investigate, not a verdict, and the format axis is the more specific of the two because storage format is never a property of the object being photographed.

---

## VIII. Ablation Study

Section VII-D established that the composed operator of Eq. (8) works. This section decomposes it: which axes matter, whether they are complementary, whether the effect is architecture-dependent, what happens to a model that has nothing but the shortcut, and whether the result depends on the two things the operator's definition leaves free — the magnitudes of its three constants and the order in which its three parts are composed.

An important caveat applies throughout. These ablations are **single-run** standalone experiments, and each compares conditions executed within one script invocation so that the within-run comparison is valid even where absolute numbers differ from the production pipeline's. Cross-run absolute comparisons should not be made: the same nominal condition read 62.7%, 45.3% and 50.7% across three runs before the seeding bug of Section VI-E was found. Directional conclusions held in every run; specific decimals did not.

### A. Which axes matter, and are they complementary?

Table 20 and Fig. 10(a) ablate four axes on M4 within single runs.

**TABLE 20.** Per-axis ablation on M4 (EfficientNet-B0). Rows are grouped by the script execution that produced them; compare only within a group. ✓ = axis applied. All three groups predate the seeding fix of Section VI-E, so their absolute values carry the caveat stated in the text; group (ii)'s white-balance rows are additionally superseded by the deterministic rerun in Table 21, and are retained here only so that the two can be read against each other. The two comparisons this table is used for — that the axes are complementary, and that white balance is not one of them — are both reproduced post-fix in Table 21.

| Group | Res. | Bright. | Comp. | White bal. | Split B accuracy | Split C accuracy |
|---|---|---|---|---|---|---|
| **(i)** | | | | | 0.919 | 0.087 |
| (i) | ✓ | | | | 0.932 | 0.220 |
| (i) | | ✓ | | | 0.919 | 0.273 |
| (i) | ✓ | ✓ | | | **0.959** | 0.627 |
| **(ii)** | ✓ | ✓ | | | 0.959 | 0.453 |
| (ii) | | | | ✓ | 0.932 | 0.107 |
| (ii) | ✓ | ✓ | | ✓ | 0.959 | 0.420 |
| **(iii)** | | | | | 0.919 | 0.053 |
| (iii) | | | ✓ | | 0.905 | 0.127 |
| (iii) | ✓ | ✓ | | | 0.932 | 0.507 |
| (iii) | ✓ | ✓ | ✓ | | 0.932 | **0.780** |

Four conclusions.

**Each of resolution, brightness and compression helps alone, and each helps modestly.** Individually they take external accuracy from 5–9% to 22.0%, 27.3% and 12.7% respectively — real effects, none sufficient.

**They are strongly complementary, not redundant.** Resolution and brightness together give 62.7% in group (i) against 22.0% and 27.3% alone: slightly more than additive. Adding compression in group (iii) takes 50.7% to 78.0%. Each axis recovers something the others do not, which is what one expects if the underlying confound is a *capture pipeline* expressed simultaneously through several correlated statistics rather than a single one.

Every group in Table 20 predates the seeding fix of Section VI-E, which matters more for this claim than for the others because it is the one the correction rests on. It is reproduced post-fix, and by a script written for a different purpose: the white-balance rerun of Table 21 contains both a two-way and a production three-way condition in one deterministic execution, and returns 0.500 against 0.820. The third axis adds 32 points there against the 27 recorded here, so the complementarity conclusion does not depend on the compromised runs even though the exact decimals do.

**White balance is ruled out, and the test was repeated to make sure of it.** It was a plausible fourth axis: the Kaggle pool has a measurably warm cast (channel means R:G:B ≈ 1 : 0.94 : 0.86) against the external set's more neutral 1 : 0.93 : 0.93. The original test of it, however, was run before the per-pass seeding defect of Section VI-E was fixed, and it compared against a two-way pipeline that compression had not yet joined — so it rejected the axis on a difference of 3.3 points using a harness whose spread on an unchanged condition was 17. That is not a basis for excluding anything, so the experiment was rebuilt with per-pass seeding and the recorded learning rate, and rerun against the pipeline that actually ships, with its own same-run baselines (Table 21).

The conclusion survives, more firmly than before. Gray-world normalization applied alone leaves external accuracy at 0.067, essentially the unnormalized baseline. Added to the production three-way operator it moves external accuracy from 0.820 to 0.780. Added to the two-way operator — the comparison the original experiment attempted — it moves 0.500 to 0.347, a decrement four times larger than the one originally reported. Both combinations point the same way, and the axis buys nothing in either.

**TABLE 21.** Gray-world white balance as a fourth axis. M4 (EfficientNet-B0), all five conditions from one script execution after the seeding fix, so all rows are directly comparable. WB is composed with the other photometric operator, before the compression bottleneck.

| Condition | Operators | Split B test accuracy | Split C accuracy |
|---|---|---|---|
| Production three-way | R, B, C | 0.919 | **0.820** |
| White balance alone | W | 0.905 | 0.067 |
| Production three-way + WB | R, B, W, C | 0.932 | 0.780 |
| Two-way | R, B | 0.919 | 0.500 |
| Two-way + WB | R, B, W | **0.960** | 0.347 |

Three things are worth taking from this beyond the axis itself. A real, measurable, dataset-wide difference between the sources need not be part of the mechanism, which is an argument for testing candidate axes rather than reasoning about them. A rejection is a claim and needs a harness good enough to support it; this one did not have one until it was rerun, and the corrected numbers happen to agree, which was not guaranteed. And the two-way-plus-WB condition is a third instance of the inversion documented in Section VIII-F: it has the highest in-distribution accuracy of the five (0.960) and the second-lowest external accuracy (0.347).

**Robustness and in-distribution accuracy are not in tension here.** The best external condition in group (i) is also the best in-distribution condition in that group (0.959), and in group (iii) the three-way condition matches the two-way condition in-distribution (0.932 both) while adding 27 points externally. Removing shortcut access did not force a trade-off; on this data it improved both, presumably because the removed variance was class-correlated noise with respect to the intended task.

> **FIGURE 10.** `paper/figures/fig10_ablation.pdf` — (a) M4 within-run ablation of the three retained axes. (b) Change in external accuracy under two-way and three-way normalization, per model.

### B. Is the correction architecture-dependent?

Yes, and the answer changed twice during this study, which is itself the methodological lesson.

**TABLE 22.** Normalization extended to all four models. Two-way = resolution + brightness; three-way adds compression. Each row's baseline and normalized numbers come from the same script execution. M4's three-way row comes from the single-model experiment that introduced the axis (group (iii) of Table 20). Both the two-way and the three-way executions predate the seeding fix of Section VI-E, so every number in this table carries that caveat; each row's within-run baseline-to-normalized comparison, which is what the table is used for, is unaffected.

| Model | Two-way Δ external | Three-way Δ external | Three-way normalized: Split B / Split C |
|---|---|---|---|
| M1 hist+LR | +0.000 (0.000 → 0.000) | +0.000 (0.000 → 0.000) | 0.541 / 0.000 |
| M2 CNN | +0.847 (0.000 → 0.847) | **+0.913** (0.000 → 0.913) | 0.838 / 0.913 |
| M3 MobileNetV3 | −0.213 (0.733 → 0.520)\* | +0.060 (0.753 → 0.813) | 0.946 / 0.813 |
| M4 EfficientNet-B0 | +0.540 (0.087 → 0.627) | +0.727 (0.053 → 0.780) | 0.932 / 0.780 |

\* Every condition in this table predates the seeding fix of Section VI-E, but this is the one whose *sign* the fix later reversed, so treat its magnitude as unverified rather than merely imprecise.

The final column of Table 22 does not reproduce Table 12, and the difference is expected rather than a discrepancy to reconcile: Table 12 reports the production pipeline, Table 22 reports standalone single-run ablation scripts. For M3 the two read 0.773 and 0.813 externally, for M4 0.813 and 0.780, and for M2 0.860 and 0.913. Only Table 12's column is the result of record. We report both rather than silently dropping the ablation's absolute values, because the within-run deltas those runs measure are the ablation's actual claim and are unaffected.

Two further caveats attach to the M2 rows specifically. Both ablation scripts trained M2 at 3 × 10⁻⁴ — the same stale constant described in Section VI-E — so their absolute values are not comparable to M2's production numbers in Table 12 (which use the recorded 1 × 10⁻³). Because baseline and normalized conditions within a single run share that learning rate, the *within-run* comparison each row reports is unaffected, which is the claim the ablation makes; the scripts now read the recorded rate, so a re-run would refresh the absolute values.

Under two-way normalization, M3 was the sole model the correction appeared to *harm*, and a decomposition run isolated the responsible axis: brightness normalization alone took M3 from 0.800 to 0.560 externally, while resolution normalization alone was neutral-to-positive (0.800 → 0.847), and the combination (0.400) was worse than either alone — a negative interaction rather than two additive effects. On the strength of that, an earlier version of this analysis concluded that the correction was "architecture-dependent, helps two of four, harms one".

Adding the compression axis reversed the sign for M3 (+0.060, improving on both axes simultaneously), and the production pipeline — after the seeding fix — puts M3 at 0.773 externally against a 0.693 pre-normalization baseline (Table 12). The most likely reading is that the harmful interaction was specific to the two-way mixture rather than intrinsic to normalizing this model's inputs. But we note that M3's answer to "does normalization help?" came out positive, negative and flat across three runs before the seeding bug was diagnosed, and that only the three-way production path has been verified deterministic. **M3 is the one model for which we would want an independent replication before treating the sign as settled.**

### C. The baseline that has nothing else: M1

M1 is unaffected by normalization externally (0.000 either way) and its in-distribution accuracy *collapses* under it, from 0.838 to 0.541 — barely above the 0.527 majority-class rate of its test partition. This is the cleanest single result in the study.

A 96-dimensional color histogram has almost nothing to work with once mean brightness is standardized away, because — per the exact Shapley decomposition of Section VII-A — mean brightness, expressed through the near-white bin, *was* essentially its entire decision function. Removing the confound does not unlock latent signal in this model, because there was no latent signal to unlock. We therefore report M1 as a clean negative result: **on this benchmark, a classical color-statistics baseline is structurally incapable of the intended task, and its 83.8% accuracy is a measurement of the confound rather than of packaging authenticity.** We considered enlarging its feature set (texture descriptors, color moments, edge statistics) and decided against it: the model shows zero external signal across every condition tested in this study, in both external evaluations, and a larger hand-crafted feature set is unlikely to overturn a pattern that consistent. The negative result is the useful finding.

This has an uncomfortable implication, and it is worth being precise about its reach. On *this* dataset it is direct, and the metadata-only oracle of Table 7 makes it exact rather than suggestive: three acquisition scalars with no pixel input reach 100% on the leakage-free partition, and a color histogram reaches 83.8%. There is no residual on this pool that a convolutional network is needed to explain. M1's 83.8% is the more conservative statement of the same point and the one we would defend if the oracle were disputed, but the oracle is the tighter bound. Beyond this dataset the implication is conditional rather than established: it applies to any collection in which the two classes were produced by different pipelines, which Section II-F finds is the majority of the located prior work — [26] edits authentic images to create its counterfeit class, [27] generates it — but we have not audited those collections and do not claim their reported figures are confounded. We claim they are unaudited, and that the audit is cheap.

### D. The architectural ablation implicit in M2

M2 carries an architectural observation that is worth separating from the confound results. It scores 0.865 on the leakage-free split — statistically indistinguishable from every other model in the roster (Table 9) — and it is the *best* model externally after correction (0.860, Table 12), with the only negative generalization gap anywhere in this study. It reaches that with 23,938 parameters and no pretraining.

The comparison this licenses is a narrow one, and we state it narrowly. A `flatten → dense(128)` head on this trunk would add roughly 6.4 M parameters, some 267 times the rest of the network, trained on 357 images. Nothing in these results suggests that capacity would buy anything: the accuracy ceiling on this pool is set by the confound (Section VII-A), not by model capacity. Parameter count is the wrong axis on data like this.

What we no longer claim is that M2 generalizes best. On Split C alone it does, by a clear margin. On the second external distribution of Section VII-E it collapses to 0.463 while both frozen backbones hold, which makes its Split C advantage a property of that particular capture condition rather than of the model. The defensible version of the architectural observation is therefore weaker and more interesting: a 23,938-parameter network from scratch can match far larger pretrained models in-distribution and on one external set, and still fail to carry that to a second — so neither in-distribution accuracy nor a single external evaluation predicts which model to deploy.

### E. Are the three constants load-bearing?

Eq. (5)–(7) fix three constants: a 128 px short side, a target mean of 0.5 and JPEG quality 40. Only the first has a justification derived from the training distribution alone. A reviewer may reasonably suspect that a recovery from 3.3% to 80.7% rests on three fortunate choices, so we varied each one around its production value, on M4, inside a single script execution (Table 23).

**TABLE 23.** Sensitivity of the three-way normalization to its constants. M4 (EfficientNet-B0), all nine conditions from one script execution, so all rows are directly comparable. The production triple is (128, 0.5, 40).

| Varied | Value | Split B test accuracy | Split C accuracy |
|---|---|---|---|
| — (production) | (128, 0.5, 40) | 0.919 | 0.820 |
| Short side | 96 | 0.905 | **0.873** |
| Short side | 192 | 0.932 | 0.620 |
| Short side | 256 | 0.905 | 0.480 |
| Brightness target | 0.4 | 0.932 | 0.727 |
| Brightness target | 0.6 | 0.932 | 0.773 |
| JPEG quality | 25 | 0.946 | 0.807 |
| JPEG quality | 60 | 0.932 | 0.747 |
| JPEG quality | 85 | 0.932 | 0.660 |

Four conclusions, and they largely defuse the objection.

**Nothing here is a knife edge.** Every axis varies smoothly. External accuracy moves monotonically with the short side (0.873 → 0.820 → 0.620 → 0.480 across 96–256 px) and monotonically with JPEG quality (0.807 → 0.820 → 0.747 → 0.660 across 25–85), and shallowly and non-monotonically with the brightness target (0.727 / 0.820 / 0.773 across 0.4–0.6). There is no narrow window in which the correction works; the reported result sits on a broad plateau.

**In-distribution accuracy is insensitive to all three.** Split B accuracy stays within 0.905–0.946 across every condition, against an external range of 0.480–0.873. The constants trade almost nothing in-distribution while moving external accuracy by nearly 40 points — which is the same asymmetry, now measured across a hyperparameter sweep rather than across an architecture, that makes in-distribution evaluation on a confounded dataset uninformative.

**The production constants are conservative, not tuned.** A 96 px short side beats the 128 px we report (0.873 vs. 0.820), and JPEG quality 25 is level with quality 40. The headline figure therefore understates what the method achieves; we have not re-run the paper around the better value, because choosing constants by their external score is precisely the target-distribution leakage that Section X warns about. The 128 px threshold retains a defense the 96 px one does not: it was set from the training pool's own 10th percentile without consulting Split C.

**The two axes that behave monotonically are the two that impose an information bottleneck.** Capping resolution and forcing a lossy re-encode both destroy information, and doing more of either helps externally until in-distribution detail starts to matter. Rescaling brightness only shifts a location parameter, destroys nothing, and correspondingly has a flat optimum. That distinction predicts which future candidate axes are worth sweeping and which need only be applied: bottlenecks have a tunable strength, alignments do not.

One reading of the diffuse attention reported in Section VII-G is that the bottleneck simply destroys the fine spatial structure a genuine packaging classifier would need, leaving a model that cannot localize anything. This sweep is the direct test of that reading, and it does not support it. If the 128 px cap were already past the point where authentication-relevant detail survives, tightening it to 96 px should cost external accuracy; instead 96 px is the best external condition in this sweep (0.873), for 1.4 points of in-distribution accuracy. Detail is being removed, and removing more of it continues to help up to the limit tested. What the sweep cannot settle is the complementary possibility — that the intended task needs detail this pipeline never had access to, in which case both the confound and the signal are being suppressed together and only the confound is being missed. Distinguishing those requires a source whose two classes share an acquisition pipeline, which Section XI lists as the outstanding acquisition.

### F. Does the order of composition matter?

Eq. (8) composes the three operators in one fixed order — resolution, then brightness, then compression — and Section VIII-E varied their magnitudes while holding that order constant. The order is a free parameter of the same method, it was never justified, and two of the three operators impose an information bottleneck rather than an alignment, so there is no reason to expect them to commute. Concretely: a JPEG re-encode applied to an image already capped at 128 px quantizes 8×8 blocks covering a large fraction of the frame, whereas the same re-encode applied at a 2400 px native size produces artifacts that the subsequent downsample averages away. We therefore ran all 3! = 6 orderings at the production constants, on M4, inside a single execution (Table 24).

**TABLE 24.** Composition order of the three normalization operators. M4 (EfficientNet-B0), production constants (128, 0.5, 40), all six orderings from one script execution, so all rows are directly comparable. R = resolution bottleneck (Eq. 5), B = brightness rescale (Eq. 6), C = compression bottleneck (Eq. 7). The production order of Eq. (8) is R, B, C.

| Order | Compression applied | Split B test accuracy | Split C accuracy |
|---|---|---|---|
| R, B, C (production) | after the cap | 0.919 | 0.820 |
| R, C, B | after the cap | 0.932 | **0.880** |
| B, R, C | after the cap | 0.919 | 0.847 |
| B, C, R | before the cap | **0.946** | **0.380** |
| C, R, B | before the cap | 0.932 | 0.540 |
| C, B, R | before the cap | 0.932 | 0.467 |

Order matters more than any of the three constants does, and it separates the six conditions perfectly along the axis the mechanism predicts.

**Compression must follow the resolution cap, and that one rule accounts for the entire spread.** The three orderings applying the JPEG bottleneck *after* the short side has been capped score 0.820, 0.847 and 0.880 externally; the three applying it before score 0.380, 0.467 and 0.540. The groups do not overlap and are separated by 28 points. The reading is mechanical rather than statistical: compressing at native resolution and then downsampling largely undoes the compression, because the resampling filter averages over precisely the quantization artifacts the bottleneck exists to impose. Those three conditions are in effect two-way normalizations that pay for a third operator without obtaining it, and 0.380–0.540 brackets the 0.500 that the genuine two-way condition reaches in Table 21.

**Brightness placement is a second-order effect.** Within the three sound orderings, moving the brightness rescale changes external accuracy by 6 points (0.820 → 0.880), against the 28-point gap between the groups. This is the distinction of Section VIII-E in another guise: the two bottleneck operators are load-bearing and position-sensitive, the location-shifting operator is neither.

**The in-distribution ranking is not merely uninformative here; it is inverted.** The ordering with the highest Split B accuracy of all six — B, C, R at 0.946 — is the ordering with the lowest external accuracy of all six, 0.380. A practitioner selecting the composition order the ordinary way, by held-out accuracy on their own data, would have chosen the worst of the six available options, and would have watched a 2.7-point in-distribution spread (0.919–0.946) conceal a 50-point external one (0.380–0.880). This is the sharpest demonstration in the study of what a confounded in-distribution partition is worth, precisely because nothing else varies: the same three operators, the same constants, the same model, the same data, reordered.

**The reported order is again conservative rather than tuned.** R, C, B beats production on both axes (0.880 vs. 0.820 externally, 0.932 vs. 0.919 in-distribution). As in Section VIII-E we have not re-run the paper around the better value, for the same reason: selecting a preprocessing choice by its external score is the target-distribution leakage Section X warns about, and the production order was fixed before any of these six numbers existed. The headline figures continue to understate the method.

The practical consequence generalizes past this pipeline. Composition order is normally left implicit in a preprocessing description; on this evidence it deserves the treatment of a hyperparameter — it must be reported, and it cannot be chosen in-distribution. Any pipeline composing two or more information-destroying operators should expect the same sensitivity, since the argument is about resampling and quantization rather than anything specific to this dataset.

### G. Deriving the axes without the external set

Sections VIII-A–VIII-F establish that the correction works, is robust to its constants and is sensitive to its composition order, but not that it could have been *found* without the external set. The axes were originally identified by comparing the Kaggle pool against Split C (Table 6), which is target-distribution information no practitioner deploying a model would possess. This section removes that dependency, because it is the most serious objection to the correction and, until now, an untested one.

The procedure is the audit of Section VII-A turned into an axis-selection rule and confined to the training data. Using the **Split B training partition alone** — 357 images, 336 product groups, with grouped 5-fold cross-validation *inside* that partition so that neither the validation partition nor the test partition nor Split C is consulted at any point — we fit a one-feature classifier to each acquisition statistic a practitioner could compute from their own files, and normalize every axis whose balanced accuracy clears a threshold declared in advance (0.65). Table 25 gives the result.

**TABLE 25.** Train-only axis derivation. Grouped 5-fold cross-validated balanced accuracy of a one-feature classifier fitted inside the Split B training partition only. No validation, test or external data is used. Chance is 0.500; the pre-declared normalization threshold is 0.650.

| Acquisition statistic | Balanced accuracy (sd) | Fires? | Normalization it implies |
|---|---|---|---|
| File format (PNG vs. JPEG) | 1.000 (0.000) | yes | re-encode all inputs → compression axis |
| Encoded file size | 0.985 (0.019) | yes | fixed-quality re-encode → **compression axis** |
| Short-side resolution | 0.958 (0.018) | yes | short-side cap → **resolution axis** |
| Aspect ratio | 0.809 (0.019) | yes | already removed by the square 224 × 224 input resize |
| Mean brightness | 0.777 (0.067) | yes | rescale to fixed target → **brightness axis** |
| Color balance (R:B) | 0.684 (0.051) | yes (marginal) | gray-world white balance |
| Color balance (R:G) | 0.610 (0.044) | no | — |

**The train-only procedure nominates the axes we used.** Resolution, brightness and compression are all selected, and they are selected in an order that matches their measured contribution in Section VIII-A rather than their *t*-statistics. Nothing in this table required knowing that Split C exists, let alone what it looks like. The correction of Eq. (8) is therefore derivable from the training set alone, and the concession this paper previously made — that the train-only variant was untested — no longer holds.

**Its two extra nominations are both informative rather than embarrassing.** Aspect ratio fires at 0.809, and is already neutralized by the square input resize that this and essentially every comparable pipeline applies before the first convolution; the audit flags a real confound that standard practice happens to remove for unrelated reasons, which is worth knowing but implies no new operator. Color balance fires marginally on one of its two ratios (0.684 against a 0.650 threshold) — and white balance is precisely the axis Section VIII-A tested and **ruled out**, finding it useless alone (0.107 external) and mildly harmful in combination. The one false positive the train-only rule produces is thus a candidate we independently showed does no good, at the cost of one ablation run.

Two honest qualifications remain. The threshold of 0.65 is a judgement, not a derived quantity; a stricter 0.75 would have excluded color balance and retained all three axes used, and a looser 0.55 would have admitted both color ratios. And this demonstrates *derivability on one dataset*, not that a train-only audit will nominate the right axes generally — in particular it cannot nominate an axis that is confounded in the deployment distribution but not in the training distribution, which is a real blind spot and not one any training-set procedure can address. What it does establish is that on this dataset the correction required no target knowledge, so the reported recovery is not an artifact of having seen the answer.

---

## IX. Discussion

### A. What the reported accuracies on this dataset actually measure

Four results constrain interpretation, in decreasing order of force. A classifier reading three acquisition scalars and no pixels reaches 100% on the leakage-free test partition, and the filename extension alone is correct on all 510 images (Table 7). A 97-parameter linear model on color histograms reaches 83.8% (Table 10). That model's decision function is dominated by a single brightness-proxy feature (Fig. 12). And its in-distribution accuracy falls to 54.1% when brightness is standardized (Section VIII-C). The first result is not a floor but a ceiling already reached: everything an in-distribution evaluation on this dataset can measure is available without looking at the packaging at all.

This does not imply prior work in this area is fraudulent or careless; it implies the dataset is defective in a way that a standard held-out evaluation cannot reveal, and that the field's prevailing dataset-construction practice (Section II-F) makes such defects likely to recur and unlikely to be caught. Held-out test partitions drawn from the same pool inherit the confound exactly, so no amount of careful in-distribution methodology — stratification, cross-validation, bootstrap intervals, even the product-level grouping we introduce here — will expose it. Only evaluation on independently acquired data does. That is the practical lesson we would want carried forward: in this application area, an external evaluation set from a different acquisition pipeline is not an optional strengthening, it is the only measurement that distinguishes the intended task from its shortcut.

### B. Why leakage turned out to be the smaller problem

We designed this study expecting image-level leakage to be the dominant inflation mechanism, because that is the mechanism the surrounding methodological literature emphasizes [11], and the one a methodologically-minded reader of work on this kind of dataset raises first. It was not, and the reason is quantitative rather than conceptual: only 9 of 480 product groups actually straddle partitions under the naive split, so the mechanism is real but its leverage is small at this pool size, and it competes against sampling variance in 74–76-image test partitions. The naive split remains indefensible — nothing here argues for using it — but on this dataset it inflates accuracy by single-digit fractions of a point for three of four models, while the acquisition confound is worth the difference between 97% and 3%.

The generalisable point is about ordering of audits. Leakage checks are cheap, well known and increasingly routine. Acquisition-pipeline audits are equally cheap — the analysis in Table 6 requires reading image metadata and computing three summary statistics — and on this dataset would have been vastly more informative. A dataset audit that checks whether any low-level acquisition statistic predicts the label should be a default step, performed before any model is trained. We would state it as a concrete procedure: for each candidate statistic — file format, encoded size, resolution, mean brightness — fit the same classifier you intend to use on that statistic alone and report its accuracy on your own leakage-free partition. On this dataset that procedure takes seconds and returns 1.000 (Table 7), which is the entire finding of this paper available before any network is trained. Ranking candidates by *t*-statistic is not a substitute: brightness has the largest *t* here and is the weakest of the three predictors.

### C. Why the models behave differently, and why capacity is the wrong axis

The four models' external behavior is not ordered by capacity, and their differences are better explained by *what kind of access* each has to the confound.

M1 sees the confound directly and nothing else: brightness *is* a color-histogram feature, so the shortcut and the model's entire feature space coincide. Consequently it exploits the shortcut maximally in-distribution, transfers nothing, and gains nothing from correction.

M2 has access to resolution-dependent blur and detail statistics through its own convolutional filters, learned from scratch on 357 images. It relies on the shortcut almost completely at baseline (0.000 externally) but, unlike M1, it has the representational capacity to learn something else when the shortcut is removed — and does, more successfully than any other model on Split C (0.860). The pairing is instructive: heavy shortcut reliance and good post-correction generalization are compatible, and the first does not predict the second. What it learned instead, however, is itself capture-specific: on a second external distribution it falls to 0.463 (Section VII-E). Removing one shortcut from a small from-scratch network appears to have let it acquire another rather than the intended concept.

M3 and M4 inherit ImageNet-pretrained invariances that afford partial, incomplete protection: both degrade severely at baseline but neither collapses to zero the way the two models with unmediated pixel-statistic access do. Their frozen features cannot adapt, so the head can only reweight whatever the backbone reports — which is why correction, which changes what the backbone reports, moves them substantially (+0.161, +0.201).

**Both frozen backbones deserve the caution that was previously reserved for M3.** The complete attention audit (Section VII-G) found that on external images M3 and M4 behave identically and without exception across 40 heatmaps: every correct prediction — that is, every "authentic" call — takes its evidence from the background, and every incorrect one takes its evidence from the product. Three further results are consistent with a backdrop cue being load-bearing: M3's baseline external accuracy is by far the best of any uncorrected model, which is what a backdrop rule would produce on a set that is 100% authentic and uniformly staged; brightness normalization specifically damages M3, which is what one expects if a brightness-linked surround cue matters (Section VIII-B); and M3 performs at chance on the synthetic proxy, where both classes share that backdrop and the cue is therefore uninformative (Section VII-F).

The most probable account is that neither backbone learned to recognize packaging. Both learned something about the photographic setting, which suffices on external sets that are entirely authentic and uniformly staged, and which the synthetic proxy — the one evaluation where both classes share the setting — reduces to chance. This is a general hazard of single-external-set evaluation: a shortcut that coincidentally aligns with one external distribution is indistinguishable from robustness until a second, differently constructed evaluation disagrees. We built that second evaluation (Section VII-E), and it disagreed — not about M3, which held, but about M2, the model this paper had been calling its best generaliser.

The hazard has a second edge, which we also walked into. A second external set only tests a shortcut if it *varies the thing the shortcut keys on*. Split D varies device and lighting but keeps the same products against the same backdrop, so it probes the capture-pipeline confound this paper is about and leaves the backdrop cue of Section VII-G entirely intact. Building it was worthwhile and it overturned a claim; it nonetheless cannot license the conclusion that the backbones generalize. Choosing an external set requires knowing which shortcut you are trying to break, and we only learned that after building this one.

### D. Practical implications

**For practitioners building screening tools.** Three-way normalization costs under 17 ms per image (Table 16) and is a fixed function of the input, so it can ship unchanged in an inference pipeline. On this data it improved external accuracy substantially for every model with usable signal, at an in-distribution cost between −1.4 and 0.0 points — i.e. unchanged for two of three models and within noise for the third. We would nonetheless not deploy any model in this study: after correction, external authentic accuracy is 0.773–0.860, i.e. between 14% and 23% of genuine packages would be flagged as suspect, and the counterfeit-recall direction is untested against real counterfeits and weak against a synthetic proxy (Table 14). A tool with those characteristics would generate false alarms at a rate that erodes trust, while providing unquantified protection against the thing it is for.

**For deciding what to collect.** The single highest-value action for this application area is not a better architecture; it is a training set in which acquisition method is *balanced across classes*, ideally with multiple independent photography setups per class. The confound documented here cannot be removed by any per-image filtering rule, because it applies to 100% of both classes; it is a property of how the dataset was assembled.

**For reviewers and readers.** A claimed accuracy on a small authentic/counterfeit image dataset should be read alongside three specific questions: what does a classifier fitted to the acquisition statistics alone — no pixels — score on the same partition; what does a trivial color-statistics baseline score; and what is the accuracy on data acquired by someone else. The first question is the cheapest and the most decisive, and on this dataset it alone settles the matter: the answer is 1.000, which makes the reported headline number uninterpretable without the third.

### E. Relation to the wider shortcut-learning literature

The mechanism here is the same as the hospital-of-origin confound in chest radiography [7] and the dataset-source confound in early COVID-19 radiograph classifiers [10], with two differences worth noting. First, it is *total* rather than partial: acquisition method predicts the label perfectly, which makes the shortcut both maximally attractive during training and maximally misleading, and means the confound cannot be diluted by pooling within the dataset. Second, it is expressed in low-level global statistics rather than in semantic content, which is what makes it correctable by fixed preprocessing at all — the correction of Section V-D works precisely because the confounded quantities are simple enough to standardize. Confounds carried by scene composition, staging or subject selection would not yield to this treatment, and we would not expect the approach here to generalize to those cases. Relative to the domain-generalization literature [23], the correction used here is deliberately unambitious: hand-designed covariate alignment on three identified axes, not learned invariance. Its advantage is that it is auditable and free at inference; its limit is that it requires knowing which axes to align, which required the audit of Section VII-A.

---

### F. A taxonomy of provenance defects, and what to check for each

The two datasets audited here failed in different ways, and a third near-failure was caught during construction of our own evaluation set. Taken together they suggest that "provenance confound" is not one defect but a small family, each member requiring a different check. We set out the four we encountered, with the cheapest test that detects each, in the order we would run them.

**Type A — acquisition-statistic confound.** The classes differ in format, resolution, compression, brightness or aspect ratio because they were captured or encoded by different processes. *Detection:* the provenance audit of Section VII-A — fit the intended classifier to metadata alone. *Instance:* the Kaggle dataset, audit accuracy 1.000, with even aspect ratio alone at 0.803. *Cost when undetected:* in-distribution 0.946, external 0.033. *Partial repair:* the label-free normalization of Section V-D, architecture-dependent.

**Type B — content or modality confound.** The classes differ in what kind of *document* they are, not in the labeled property: one class is product photography and the other is bulletin graphics, screenshots, catalog renders or marketing material — in the worst case with the ground-truth label rendered as text in the pixels. *Detection:* human inspection of a sample of each class, and of the extremes of any metadata distribution. Metadata may be silent, and normalizing a dataset for release makes it more so. *Instance:* the Roboflow dataset, 57/57 against 263/263, audit accuracy only 0.717. Also, in smaller degree, the 47 watermarked stock-catalog images in the Kaggle pool, 47/47 authentic-labeled. *Cost when undetected:* unbounded — a model can reach 100% by reading the printed label. *Repair:* exclusion; no preprocessing helps.

**Type C — confound reintroduced by source selection.** The dataset is clean, but a *derived* set — an external test set, a synthetic negative class, an augmented subset — is drawn from a differently-acquired part of the source. *Detection:* recompute the Type A statistics on every partition after construction, not only on the training pool. *Instance:* our own first synthetic proxy drew its base images from a different device subset of the external source, differing more than twofold in brightness (Section V-F), which would have reproduced the confound under study via selection rather than generation. It was caught by re-running our own audit and fixed before use. *Cost when undetected:* a fabricated positive result, published as a validation of the very method under test.

**Type D — degenerate shipped evaluation protocol.** The dataset's own partition files do not partition. *Detection:* intersect the filename sets. *Instance:* the Kaggle archive, whose `train` folder contains all 661 images while `val` and `test` are proper subsets of it (Section III-A). *Cost when undetected:* test accuracy is training accuracy. *Repair:* build your own split; treat a shipped split as a claim to be verified, not a service.

**Type E — a real content difference that the audit reads as a confound.** This is the audit's false-positive mode rather than a defect of the dataset, and we add it because the cross-domain survey produced one. The classes differ in a low-level statistic for reasons intrinsic to the objects, not to how they were acquired. *Detection:* compare the audit's axes against each other. Storage format is never a property of the photographed object, so a high score on format is specific to acquisition; encoded size, resolution and aspect ratio all mix acquisition with content and are correspondingly ambiguous. *Instance:* the BHSig260 signature corpus (Section VII-K), where both classes are written on the same paper and scanned by one procedure — format returns exactly 0.500, as it should, while encoded size returns 0.843, almost certainly because forged signatures differ from genuine ones in stroke complexity and therefore in ink coverage, which drives the compressed size of a bitonal scan. *Consequence:* the audit's output is not a verdict. It says a trivial statistic separates the classes; establishing that the statistic is an *acquisition* artifact is a second step, and the format axis is the one that most nearly settles it on its own.

Two cross-cutting lessons follow, and they are the ones we would most want carried into other application areas.

**Publisher-side tidying suppresses the symptom, not the disease.** The Roboflow archive had been resized to a uniform 640 × 640 and re-encoded to a single format before release. Those are ordinary, well-intentioned preparation steps, and their effect is to erase exactly the traces the cheap audit reads while leaving a total Type B confound untouched. A curated dataset is therefore *harder* to audit than a raw one, and a clean audit result on a normalized dataset carries almost no information. Where an archive has been normalized, the audit should be treated as inapplicable rather than as passed.

**Rank confounds by discriminability, not by effect size.** Brightness gave the largest *t*-statistic in the case-study dataset (*t* = 17.0) and was the *weakest* single predictor of the label (0.716 balanced accuracy, against 1.000 for format and 0.994 for file size). A large difference in means with overlapping distributions is less dangerous than a small difference with none. Since fitting a one-feature classifier costs no more than a *t*-test, there is no reason to use the *t*-test for this purpose.

### G. What would falsify the general claim

The claim of Section I-A is causal — asymmetric class availability *produces* provenance confounding — and we state what evidence would count against it. Datasets in which the scarce class was obtained by the same procedure as the abundant one should show no Type A confound; [3], which photographed authentic and counterfeit samples on one Raspberry Pi rig, is the one study in Table 1 that plausibly meets this condition, and it also reports the lowest accuracy in that table. Conversely, a survey of authenticity datasets that found the audit firing no more often on separately-sourced collections than on jointly-sourced ones would refute the mechanism. That survey is the natural next study and we have not performed it: two datasets in one application area, plus one corroborating report from another [30], is enough to motivate the mechanism and not enough to establish its prevalence.

## X. Limitations

**The external evaluation is authentic-only, so counterfeit recall is unmeasured.** Every external image in this study is genuine packaging, so every external number is a false-positive rate and nothing else. We state the resulting non-claim as plainly as we can: **this paper does not report, estimate or bound the rate at which any of these models would detect a real counterfeit.** No independent counterfeit-labeled source could be found (Section III-F), and the synthetic proxy of Section V-F does not substitute for one.

The proxy's limitation is worth enumerating, because Table 14 could otherwise be mistaken for a recall measurement. It perturbs genuine photographs, so it can only measure sensitivity to *degradation of a genuine image*. Real falsified packaging differs along axes it does not model at all: absent or imitated security features, holograms and tamper seals; wrong substrate, board weight or surface finish; serial numbers, batch codes and barcodes that are legible but incorrect; and — most importantly — competently produced counterfeits whose printing is not degraded in any visible way, which are precisely the cases a screening tool exists to catch. A model could score well on the proxy and fail on all of these; it could also fail the proxy and catch real counterfeits, since the perturbations are not drawn from any counterfeit distribution. The proxy supports only a weak, one-directional inference: a model that cannot separate a photograph from a visibly perturbed copy of *that same photograph* is unlikely to separate genuine from falsified packaging, and three of four models here fail that test.

**The general claim rests on a narrow evidence base.** Section I-A argues that asymmetric class sourcing makes provenance confounding the default. The direct evidence here is two datasets in one application area, plus a structurally matching report from generated-image detection [30] that we did not produce. That is enough to motivate the mechanism, to justify the audit as a routine precaution, and to explain two independent observations of one signature; it is not enough to quantify how often the mechanism fires, and no number in this paper should be read as a prevalence estimate. Section IX-G states what would falsify the claim.

**The correction's axes were originally chosen with knowledge of the external set, though they need not have been.** Eq. (8) uses no label information, which is what licenses applying it to Split C; but the *choice* of resolution, brightness and compression was made after Table 6 showed those statistics separating the Kaggle pool from Split C, and that is target-distribution information a practitioner would not have. Section VIII-G addresses this directly: a train-only audit, confined to the Split B training partition with grouped cross-validation inside it, nominates all three axes without consulting any external data. The objection is therefore answered on this dataset. Two residual weaknesses remain. The selection threshold (0.65 balanced accuracy) is a judgement rather than a derived quantity. More fundamentally, no training-set procedure can nominate an axis that is confounded in the deployment distribution but not in the training distribution, so a train-only audit is a safeguard against the confound you have, not a guarantee against the one you have not seen.

**The correction is a preprocessing bottleneck, not a domain-adaptation method, and is not compared against one.** The natural alternative to suppressing a confounded statistic is to align the distributions in feature space — second-order alignment such as CORAL, importance reweighting, or an adversarial domain-confusion objective — and we report no such comparison. The omission is a design constraint rather than an oversight, and the constraint is worth stating because it also limits what the comparison would mean. Every method in that family requires samples from the deployment distribution at training time, and consumes them to fit an alignment; Eq. (8) is a fixed function of a single image that uses neither labels nor target data, which is what licenses applying it unchanged to Split C, to Split D, and to an image captured after deployment. A study that fitted CORAL on Split C could not then report Split C as an external evaluation. The honest statement of the trade is therefore that we chose the weaker intervention because it is the one that survives its own evaluation protocol, and that a practitioner who does hold target-domain data should expect to do better than Eq. (8) — how much better is unmeasured here.

We accordingly ask that Eq. (8) be read as a **zero-target-sample baseline**: the performance recoverable when nothing whatsoever is known about the deployment distribution, not the best available correction. Anyone holding even unlabelled target-domain images is in a strictly stronger position and should evaluate second-order feature alignment (Deep CORAL), distribution matching (MMD-based adaptation) or an adversarial domain-confusion head against this baseline before adopting it. We would expect those methods to win, and the quantity of interest — how much accuracy a rigid per-image bottleneck leaves on the table relative to representation-level alignment — is exactly what such a comparison would measure, and is not measured here.

**Cross-validating across sources or capture hardware is not possible on this data.** The strongest answer to a provenance confound would be a grouped cross-validation whose folds are acquisition pipelines rather than products, so that every fold is evaluated on a capture process it never saw. That design cannot be built here, and the reason is the confound itself: the counterfeit class exists in exactly one usable source. The only other public authentic/counterfeit pharmaceutical dataset we could obtain has a counterfeit class that is 57/57 advisory graphics carrying the ground-truth word in the pixels (Section VII-B), which is unusable at any position in a fold, and both external sets are authentic-only. A source-held-out fold would therefore contain no negatives. The grouped cross-validation we do run decorrelates product identity and nothing else, and we do not claim otherwise; Section IX-A states the consequence, which is that in-distribution machinery of any kind cannot see this defect.

**Split D does not vary the backdrop.** Section VII-G identifies a surround-based cue as the basis of both backbones' correct external predictions, and Split C and Split D share the same staging. The second external set therefore cannot test that cue, and the stability of M3 and M4 across the two sets should not be read as evidence against it. An external set that varies the photographic setting — different surfaces, in-hand or in-shelf photography, uncontrolled backgrounds — is the evaluation this study most obviously lacks, and is a different requirement from the counterfeit-labeled set discussed above.

**Two capture conditions, one archive, one product set.** This limitation was stated in an earlier version as a caution and has since been partly measured. Section VII-E adds a second external distribution, and it changed a headline claim: M2's post-correction accuracy proved specific to Split C (0.860 → 0.463) while both frozen backbones held. What remains unmeasured is still substantial. Both external sets come from the same archive, the same 150 products and the same laboratory protocol, differing only in device and lighting — so the evidence supports "the correction transfers across a change of camera for pretrained backbones" and not "the correction transfers." Nothing here tests generalization across products, across sources, across countries, or to photographs taken by end users in the conditions a screening tool would actually face. No number in this paper should be read as establishing a generalization *rate*.

**Small test partitions.** In-distribution test partitions contain 74–76 images. Bootstrap intervals are correspondingly wide (Table 9), all pairwise model comparisons are underpowered (Table 11, discordant counts 1–15), and the leakage delta of Section VII-C is measured against variance that a larger pool would suppress. Point differences of a few percentage points between models on this data should not be interpreted.

**Some numbers predate checkpoint persistence and cannot be re-derived.** For most of this study no script saved a trained model, and every downstream consumer — external evaluation, Grad-CAM, the synthetic proxy — re-derived "the trained model" from scratch. That design produced both defects of Section VI-E: the learning-rate divergence in M2's external evaluation, and a discrepancy in which two rebuild paths of the same nominal M4 model classified 16/150 versus 5/150 external images as authentic. Training now persists a checkpoint with the learning rate, seed, best epoch and epoch count it was trained under, `load_checkpoint` raises if the recorded learning rate differs from the caller's expectation, and the external evaluations of Table 13 load rather than retrain — which independently reproduced M2's and M3's recorded Split C accuracies exactly. Two residual weaknesses follow from the change arriving late. M4's earlier Split B accuracy of 0.946 could not be explained when the checkpointed pipeline deterministically produced 0.919, because the artifacts of the original run no longer exist; the newer value is the one reported, and the older one is unrecoverable rather than refuted. And the two `experiment_*_all_models.py` ablations still rebuild rather than load, so their absolute values are not directly comparable with the production tables — the within-run comparisons they actually make are unaffected, and Section VIII says so where they are used.

**Single-run ablations.** Every ablation in Section VIII is one execution per condition, not a distribution over seeds, so none of them carries an interval. The reason this is tolerable is that the pipeline is now deterministic: the per-pass seeding defect of Section VI-E, under which nominally identical conditions moved by up to 17 points, was fixed partway through, and each ablation re-runs its own baseline inside the same execution so that every comparison it makes is within-run. Three checks support the harness rather than merely asserting it: the production condition returns 0.919 in-distribution and 0.820 externally in each of the three post-fix scripts that contain it (Tables 21, 23 and 24), and the external evaluation from persisted checkpoints reproduced M2's and M3's recorded Split C counts exactly, byte for byte, on a re-run. What remains unmeasured is seed-to-seed variance itself; a condition differing from its baseline by a point or two should not be read as a difference, and we do not read any such difference. The ablations that predate the fix are identified in their captions — all of Table 20, all of Table 22, and the superseded white-balance rows retained in Table 26; Tables 21, 23 and 24 are post-fix — and the two conclusions Table 18 is used for are separately reproduced post-fix in Table 21.

**Frozen backbones only.** Neither transfer model was fine-tuned; each trained a single linear head on cached features, a scope decision forced by CPU-only hardware — an early attempt at live per-epoch backbone passes was terminated by the host before one split finished (Section VI-C). Whether end-to-end fine-tuning would reduce or amplify the shortcut reliance documented here is genuinely open, and the possibilities are opposite: adaptable features could discard the confounded statistics, or specialize onto them more aggressively than a frozen representation can.

One data point here bears on the question without settling it. M2 *is* trained end to end from scratch with no frozen component, and it is simultaneously the model that relies on the shortcut most completely at baseline (0/150 external) and the one that generalizes best after correction (0.860, the only negative gap). End-to-end training therefore conferred no protection against the confound, but also did not prevent the model from learning something transferable once the confound was suppressed. That is consistent with fine-tuning being neutral-to-helpful rather than harmful, but M2 differs from M3 and M4 in scale, initialization and capacity, so it is weak evidence and we do not lean on it.

**The attention audit is complete but small, and one annotator produced it.** All 62 heatmaps were regenerated from the persisted production checkpoint after the training-mode defect of Section VI-E and categorized in full, so the audit is no longer a non-random sample of a mis-configured model. It remains 62 images scored by a single human against a four-way scheme, with no second annotator and therefore no inter-rater agreement to report. The external result is stark enough — 40 of 40 maps splitting cleanly by outcome — that we do not think a second annotator would overturn it, but we cannot demonstrate that. The categories themselves are also coarse: "attends to the background" does not identify *which* property of the background the model is using, and the quantitative border-mass measure that accompanies it is purely radial.

**Product identity is a proxy.** Split B groups on perceptual-hash clusters, not ground-truth product labels, which do not exist in this source. The clustering is not robust to mirroring, and while no cluster mixes class labels, the grouping could be coarser or finer than true product identity in ways that would slightly change the measured leakage rate.

**Scope of the modality claim.** The pool is 43.7% blister packs and 25.9% mixed presentations (Table 3). Results characterize "packaging and immediate product containers", and should not be read as results on outer cartons.

**Single-machine cost measurements.** Table 16 is one CPU on one machine at batch size 1. Absolute latencies will differ elsewhere; the relative ordering and the conclusion that normalization is negligible relative to a forward pass should be stable.

---

## XI. Future Work

**Finish fixing the reproducibility substrate.** Persist a checkpoint from each authoritative training run and have every downstream consumer load it rather than re-derive it. Recording the learning rate (Section VI-E) removed the immediate cause of both observed divergences, but it does not *verify* that a rebuild reproduces the model of record; loading a checkpoint would.

**Re-run the one ablation condition (M3, two-way normalization) that predates the seeding fix.** It is not expected to change a directional conclusion, but its magnitude is currently unverified, and Table 22 flags it as such.

**Vary the photographic setting in an external set.** The attention audit shows both backbones justify "authentic" by the surround, and both external sets here share one backdrop, so neither disturbs that cue. An external set photographed against varied surfaces — in hand, on shelves, in uncontrolled conditions — would test it directly, and is a different and cheaper requirement than the counterfeit-labeled set above.

**Acquire a counterfeit-labeled external set.** This is the single most valuable addition and the one that would most change what can be claimed. The requirements are specific: independently photographed (verified, not assumed, by the pHash procedure of Section IV-B), and with acquisition method balanced across its two classes so that it does not import the confound it is meant to test.

**Build a training set with acquisition balanced across classes.** Since the confound cannot be filtered away, the durable fix is at collection time: multiple independent photography setups, each contributing both classes. This would also permit the leakage question of Section VII-C to be re-asked on a pool where the effect is not swamped by sampling variance.

**Fine-tune the backbones — the highest-priority item for anyone with a GPU.** Both transfer models here train a single linear head on cached features because the hardware available was CPU-only (Section VI-A), and that constraint, not a scientific judgement, is why no result in this paper describes a fine-tuned network. **The frozen-backbone numbers should therefore not be read as an upper bound on what transfer learning can do on this task, in either direction.** With external evaluation now in place the experiment is well-posed rather than merely expensive, and the two outcomes are both informative and opposite: adaptable features may discard the capture confound once the classification head can no longer profit from it, or the additional capacity may specialize onto residual low-level acquisition artifacts more aggressively than a frozen ImageNet trunk does, in which case fine-tuning would make external generalization worse while improving every in-distribution number. Section VIII-F's inversion suggests the second outcome would be invisible to anyone evaluating in-distribution. This is the single cheapest way for a better-equipped group to extend the study.

**Test further acquisition axes.** Aspect ratio, sensor noise characteristics and — harder — staging and backdrop conventions remain untested. The white-balance result (Section VIII-A) shows that a measurable dataset-wide difference need not be part of the mechanism, so each candidate needs testing rather than reasoning; it also shows that a candidate must be tested on top of the current operator and with a harness whose run-to-run spread is smaller than the effect being judged, neither of which was true the first time that axis was rejected. Any new axis should additionally be swept for composition position, not only for inclusion, on the evidence of Section VIII-F.

**Extend the attention audit to a content-aware measure.** Section VII-G replaces the human categorization with a border-mass fraction over all external images, which is automatic and complete but purely radial. Annotating product bounding boxes would allow the fraction of Grad-CAM mass falling on the product itself to be measured, which is the quantity the qualitative audit was reaching for and the one that would distinguish this section's mechanical and substantive readings.

**Test the mechanism across application areas.** The most valuable extension is not another model but a survey: apply the audit of Section VII-A to a corpus of authenticity-classification datasets — counterfeit goods, document forgery, generated-image detection, industrial defect inspection — recording for each whether the two classes were sourced by the same procedure. The mechanism of Section I-A predicts that audit accuracy tracks sourcing asymmetry, and Section IX-G states what result would refute it. Such a survey needs no training runs, only metadata, and would convert this paper's mechanism from a motivated hypothesis into a measured prevalence.

**Audit sibling datasets in this application area.** The audit performed here is inexpensive and mechanical: cross-tabulate file format, resolution, brightness and file size against the class label, then fit a classifier to each statistic alone (Table 7) rather than only testing means. Section II-F establishes that no two located studies share an image set, so the audit has to be applied per study rather than once per benchmark; doing so across the collections behind the reported accuracies in Table 1 would establish whether this dataset is an outlier or an example. Section VII-K begins this outside the application area rather than inside it, because public listings made that possible without downloads, and the datasets behind Table 1 are mostly private. Extending it properly is the single highest-value piece of work this paper leaves undone: what Section VII-K delivers is four scored datasets across four areas, enough to show the audit discriminates and to expose one false-positive mode, and nothing like enough to estimate how often the confound occurs. A survey designed for that — a defined sampling frame of authenticity datasets, a pre-registered scoring rule, and enumeration rather than listing-order sampling — would convert this paper's central generality claim from a hypothesis into a measurement, and needs no training runs at all.

---

## XII. Conclusion

We set out to determine how much of a reported accuracy on a small public counterfeit-medicine image dataset survives methodological correction, expecting train/test leakage to be the mechanism at issue. Leakage turned out to account for very little — at most 6.8 points against an arithmetic ceiling of 9.2, and under half a point for three of four models. Almost all of the inflation is something else, and that something else has a structural cause that reaches well beyond the dataset we started from.

In any binary image task asking whether something is genuine, the inauthentic class is harder to obtain than the authentic one, so it gets obtained differently — screen-captured, scraped, edited or generated. The label then predicts the acquisition process, the acquisition process is easier to learn than the semantics, and no in-distribution evaluation can tell the difference, because a held-out partition drawn from the same pool inherits the confound in the same proportion. We ran stratification, 5-fold grouped cross-validation, bootstrap intervals and a leakage-free product-level split, and none of them saw anything wrong. The dataset's two classes were acquired by two different methods — screen captures for counterfeits, downloaded photographs for authentics — with no exceptions across 510 images, and those methods differ by a factor of 17 in *t*-statistic on brightness, roughly 2× in median resolution and 56× in file size. A 97-parameter linear model on color histograms scores 83.8% on this data, and an exact Shapley decomposition shows it does so by counting near-white pixels. A classifier given three acquisition scalars and no pixels scores 100% on the leakage-free test partition — encoded file size alone is sufficient — and the filename extension separates the classes perfectly across all 510 images. The dataset's stated task is therefore not merely hard to measure on it; it is unmeasurable on it.

The consequence is measurable and severe. On 150 authentic packaging photographs from an independent source, two of four models were correct on zero images and the best in-distribution model was correct on 3.3%, while scoring 97.4% on the authentic class of its own test partition. Grad-CAM on those images shows attention on the printed product name at predicted counterfeit probabilities of 0.94–1.00: confident, spatially sensible decisions calibrated to the wrong cue.

The failure is substantially correctable, and cheaply. A label-free three-stage normalization — a resolution bottleneck, a brightness rescale and a fixed-quality JPEG re-encode, together costing under 17 ms per image — raises external authentic accuracy from 0.0% to 86.0%, from 3.3% to 80.7% and from 69.3% to 77.3% for the three models with usable signal, with in-distribution accuracy moving only between −1.4 and 0.0 points. Whether that repair is general, however, depends on the model: on a second external distribution built by rephotographing the same products with different hardware, the two frozen pretrained backbones held (0.725 and 0.832) while the from-scratch CNN fell to 0.463. One external set was not enough to tell those cases apart, and we had written the warning about exactly that hazard before we ran the test that caught us out by it.

Nor is the surviving accuracy what it appears to be. Categorizing every one of the 62 attention maps produced by this study — after discovering that the ones we had previously inspected were generated with the network in the wrong mode — gives a result with no exceptions across 40 external maps: both frozen backbones justify "authentic" by the background and "counterfeit" by the product. Both external sets share a single dark backdrop, so neither disturbs that cue. The models that look robust here are the ones whose shortcut our evaluations happened not to vary. Ablation shows the three axes are complementary rather than redundant, and that a fourth plausible axis, white balance, is not part of the mechanism. The one model that gains nothing is the one whose entire decision function was the shortcut.

The ablations also produced the study's most compact statement of its own thesis, and it was not one we set out to make. Permuting the order of the three operators — nothing else: same operators, same constants, same model, same data — moves external accuracy from 0.380 to 0.880 while moving in-distribution accuracy by 2.7 points, and the ordering that scores highest in-distribution is the one that scores lowest externally. A practitioner tuning this preprocessing the ordinary way, on held-out data drawn from their own pool, would have selected the worst of the six available options and would have had no way to know. That is the whole argument of this paper reproduced inside a single hyperparameter.

What survives correction is also worth stating. Gaps of 16 to 20 points remain for both transfer models on Split C; no model achieves well-calibrated counterfeit recall against a synthetic perturbation proxy; the model with the best uncorrected external accuracy turns out on inspection to be relying on a backdrop cue that happens to suit that particular external set; the model with the best corrected external accuracy on Split C turns out to lose 40 points on a second capture condition; both surviving models justify their correct external answers by the photographic surround rather than the packaging; and the counterfeit-recall direction remains untested against real counterfeits. We would not deploy any of these models.

The methodological claim we would most like carried forward is cheap to act on and, we think, general. Before training anything, fit the classifier you intend to use to acquisition metadata alone — format, encoded size, resolution, aspect ratio — under your own leakage-free split, and report the number. It costs seconds, needs no data you do not already have, and it lower-bounds how much of your eventual result the acquisition process can explain. On the dataset studied here that number is 1.000, which settles the interpretation of every accuracy figure ever reported on it before a single network is trained.

Three qualifications keep that recommendation honest, and the first is a limit on how the number may be read. We can offer no validated decision threshold: the audit has been run on eight distinct datasets in total, of which five could be scored, and that is far too few to establish a false-positive or false-negative rate. What the scores support is a weaker and more specific reading. A high score on **format** is close to decisive, because storage format is never a property of the object being photographed — the two datasets scoring 1.000 there are separable by a one-line script that reads no pixels. A high score on encoded size, resolution or aspect ratio is ambiguous, because those mix acquisition with content: our signature negative control returns 0.500 on format and 0.843 on size, and the size signal there is most likely ink coverage, a real difference between genuine and forged writing (Section IX-F, Type E). The number is a reason to look, and the axis it comes from tells you where.

The second qualification is that the audit is necessary but not sufficient in the other direction too: on a second pharmaceutical dataset it returned 0.717 while that dataset was confounded at least as badly, because its publisher had normalized away the acquisition traces without removing the confound — so a clean audit on a curated archive means very little, and content inspection remains irreplaceable. And the third is that the audit tells you nothing about whether your model generalizes; only data someone else acquired does that. What the audit buys is the ability to find out before you have built anything on the answer.

The same signature has now been documented independently in generated-image detection [30], with the genuine class lossy and small, the synthetic class lossless and large, and detectors partly reduced to compression detectors. Two unconnected literatures arriving at one confound is what a structural cause predicts. We would expect the same to be found wherever a scarce class had to be manufactured or harvested separately from an abundant one — forged documents, defect detection, any adversarial artifact rare enough that it cannot be collected the ordinary way — and we would expect a metadata audit to be the cheapest thing anyone in those fields could add to their protocol.

---

## Appendix A — Complete Per-Axis Ablation Record

Table 26 reproduces every normalization condition executed in this study, annotated with the script execution that produced it, so that valid within-run comparisons are identifiable. Absolute values are not comparable across groups; see Section VIII's caveat.

**TABLE 26.** All normalization conditions. Res = resolution bottleneck (Eq. 5); Bright = brightness rescale (Eq. 6); Comp = JPEG bottleneck (Eq. 7); WB = gray-world white balance.

| Run group | Model | Condition | Res | Bright | Comp | WB | Split B | Split C |
|---|---|---|---|---|---|---|---|---|
| resolution experiment | M4 | baseline | | | | | 0.919 | 0.087 |
| resolution experiment | M4 | resolution only | ✓ | | | | 0.932 | 0.220 |
| resolution experiment | M4 | brightness only | | ✓ | | | 0.919 | 0.273 |
| resolution experiment | M4 | both | ✓ | ✓ | | | 0.959 | 0.627 |
| brightness experiment | M1 | baseline | | | | | 0.838 | 0.000 |
| brightness experiment | M1 | brightness | | ✓ | | | 0.541 | 0.000 |
| brightness experiment | M4 | baseline | | | | | 0.919 | 0.067 |
| brightness experiment | M4 | brightness | | ✓ | | | 0.932 | 0.313 |
| white balance, superseded | M4 | res + bright | ✓ | ✓ | | | 0.959 | 0.453 |
| white balance, superseded | M4 | white balance only | | | | ✓ | 0.932 | 0.107 |
| white balance, superseded | M4 | res + bright + WB | ✓ | ✓ | | ✓ | 0.959 | 0.420 |
| white balance, rerun | M4 | production three-way | ✓ | ✓ | ✓ | | 0.919 | 0.820 |
| white balance, rerun | M4 | white balance only | | | | ✓ | 0.905 | 0.067 |
| white balance, rerun | M4 | three-way + WB | ✓ | ✓ | ✓ | ✓ | 0.932 | 0.780 |
| white balance, rerun | M4 | two-way | ✓ | ✓ | | | 0.919 | 0.500 |
| white balance, rerun | M4 | two-way + WB | ✓ | ✓ | | ✓ | 0.960 | 0.347 |
| compression experiment | M4 | baseline (rerun) | | | | | 0.919 | 0.053 |
| compression experiment | M4 | compression only | | | ✓ | | 0.905 | 0.127 |
| compression experiment | M4 | res + bright (rerun) | ✓ | ✓ | | | 0.932 | 0.507 |
| compression experiment | M4 | all three | ✓ | ✓ | ✓ | | 0.932 | 0.780 |
| M3 decomposition | M3 | baseline | | | | | 0.946 | 0.800 |
| M3 decomposition | M3 | resolution only | ✓ | | | | 0.946 | 0.847 |
| M3 decomposition | M3 | brightness only | | ✓ | | | 0.932 | 0.560 |
| M3 decomposition | M3 | both | ✓ | ✓ | | | 0.959 | 0.400 |
| two-way, all models | M1 | baseline / normalized | ✓ | ✓ | | | 0.838 → 0.541 | 0.000 → 0.000 |
| two-way, all models | M2 | baseline / normalized | ✓ | ✓ | | | 0.865 → 0.824 | 0.000 → 0.847 |
| two-way, all models | M3 | baseline / normalized | ✓ | ✓ | | | 0.946 → 0.946 | 0.733 → 0.520 |
| two-way, all models | M4 | baseline / normalized | ✓ | ✓ | | | 0.919 → 0.959 | 0.087 → 0.627 |
| three-way, all models | M1 | baseline / normalized | ✓ | ✓ | ✓ | | 0.838 → 0.541 | 0.000 → 0.000 |
| three-way, all models | M2 | baseline / normalized | ✓ | ✓ | ✓ | | 0.865 → 0.838 | 0.000 → 0.913 |
| three-way, all models | M3 | baseline / normalized | ✓ | ✓ | ✓ | | 0.932 → 0.946 | 0.753 → 0.813 |
| ordering sweep | M4 | R, B, C (production) | ✓ | ✓ | ✓ | | 0.919 | 0.820 |
| ordering sweep | M4 | R, C, B | ✓ | ✓ | ✓ | | 0.932 | 0.880 |
| ordering sweep | M4 | B, R, C | ✓ | ✓ | ✓ | | 0.919 | 0.847 |
| ordering sweep | M4 | B, C, R | ✓ | ✓ | ✓ | | 0.946 | 0.380 |
| ordering sweep | M4 | C, R, B | ✓ | ✓ | ✓ | | 0.932 | 0.540 |
| ordering sweep | M4 | C, B, R | ✓ | ✓ | ✓ | | 0.932 | 0.467 |

Only the last two groups — the ordering sweep and the white-balance rerun — were produced after the seeding fix of Section VI-E, by scripts that seed each augmentation pass and read the recorded learning rate. Every other group in this table was executed on 2026-07-25, the day before the fix, and its absolute values carry the caveat of Section VIII; the within-run comparisons each group was built to make are unaffected. The superseded white-balance group is retained only so that the rerun beneath it can be read against what it replaces. The production condition appears in both post-fix groups and returns 0.919 / 0.820 in each, matching its value in Table 23 — three exact reproductions across two scripts.

## Appendix B — Exclusion Rules Applied to the Modeling Pool

Table 27 records every exclusion rule applied to the modeling pool, with the number of files each removed.

**TABLE 27.** Every exclusion rule, with counts. Roboflow exclusions are listed for completeness; that source contributes to no split used in this paper's results.

| Source | Rule | Files excluded |
|---|---|---|
| Roboflow | simultaneous `authentic=1` and `counterfeit=1` annotation | 52 |
| Roboflow | advisory-bulletin graphic (label rendered as pixel text) | 180 |
| Kaggle | watermark / stock-photo overlay (47/47 authentic-labeled) | 47 |
| Kaggle | not a device photograph of a product (1 browser screenshot, 3 marketing renders) | 4 |
| Kaggle | no packaging in frame (1 loose tablets, 4 syrup bottles) | 5 |
| Kaggle | exact duplicate on the rotation-canonical hash (one copy retained) | — (applied after the above; 605 filtered files → 510 pool images) |

## Appendix C — Reproduction

```bash
# 1. Data pipeline (deterministic; ~35 s)
python scripts/run_all.py                          # inventory → filter → dedup → provenance → splits
python scripts/06_download_mendeley_split_c.py     # external set, one-time (~248 MB)
python scripts/07_verify_split_c_independence.py   # pHash independence check
python scripts/17_apply_synthetic_review.py        # assemble the synthetic proxy set
python scripts/18_capture_method_stats.py          # per-image capture statistics (Table 6, Fig. 3)

# 2. Models
python modeling/train_model1_classical.py
python modeling/train_model2_cnn.py
python modeling/train_model3_mobilenet.py
python modeling/train_model4_efficientnet.py

# 3. Evaluation
python modeling/eval_split_c.py                    # external, authentic-only
python modeling/eval_split_c_synthetic.py          # synthetic proxy
python modeling/gradcam.py                         # in-distribution attention audit
python modeling/gradcam_split_c.py                 # external attention audit, M4
python modeling/gradcam_split_c_model3.py          # external attention audit, M3

# 4. Ablations
python modeling/experiment_resolution_norm.py
python modeling/experiment_brightness_norm.py
python modeling/experiment_colorbalance_norm.py
python modeling/experiment_compression_norm.py
python modeling/experiment_normalization_all_models.py
python modeling/experiment_compression_all_models.py
python modeling/experiment_model3_decompose.py
python modeling/experiment_constant_sensitivity.py
python modeling/experiment_order_permutation.py

# 5. Manuscript tables and figures
python paper/scripts/compute_paper_metrics.py
python paper/scripts/metadata_oracle.py
python paper/scripts/provenance_audit_multi.py
python paper/scripts/power_and_leakage_bound.py
python paper/scripts/train_only_axis_derivation.py
python paper/scripts/external_intervals.py
python paper/scripts/model1_attribution.py
python paper/scripts/benchmark_cost.py
python paper/scripts/make_figures.py
```
## Acknowledgment

This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors, and was carried out on a single consumer laptop; the CPU-only constraint that shapes several of this paper's design decisions is a direct consequence.

We thank the maintainers of the three public datasets used here [19], [20], [21]. The Mendeley and Roboflow datasets are distributed under CC BY 4.0. The Kaggle dataset carries no license in its archive and its Kaggle listing states its license as "Unknown"; it is attributed to its uploader. Because no license grant is on record, this study redistributes no image from that source — only derived per-image statistics, split assignments and filenames — and readers wishing to reproduce the pool must obtain the archive from the original listing themselves.

This paper is critical of the construction of a dataset whose uploader made it freely available and made no research claim about it. That criticism is directed at a property of the artifact and at the practice of adopting such artifacts without auditing them; it is not directed at the uploader, and nothing here suggests bad faith on anyone's part. The same applies to the prior studies surveyed in Section II-F, whose reported accuracies we do not dispute and have not attempted to re-derive.

## Ethics, Conflicts of Interest, and Data Provenance

**Human and animal subjects.** This study involves neither. All images are photographs of pharmaceutical packaging and its printed surfaces, obtained from public archives. No image in any partition depicts an identifiable person, and no personal or patient data was accessed, stored or processed at any stage.

**Data provenance and permissions.** Every image originates from a third-party public archive, used within its stated terms: Mendeley Data and Roboflow under CC BY 4.0 with attribution, and the Kaggle archive under no stated license, from which nothing is redistributed for the reason given above. No data was scraped, purchased, or obtained under any agreement restricting publication, and no counterfeit pharmaceutical product was acquired, handled or imaged by the authors.

**Intended use and misuse.** The paper reports that no model examined here is fit to authenticate medicine, and it should not be read as validating any of them for that purpose. We state this explicitly because a falsely reassuring authentication tool is more dangerous in this application than no tool: a consumer told a falsified product is genuine is worse off than one who remains uncertain. The paper's own conclusion is that the reported accuracies in this area measure acquisition rather than authenticity, and that the deployment case therefore remains unproven.

**Conflicts of interest.** The author declares no conflict of interest. The author has no affiliation with, and received no consideration from, the maintainers or uploaders of any dataset examined here, and no commercial interest in any pharmaceutical-authentication product or service.

**Funding.** This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Generative-AI disclosure.** This manuscript and the accompanying code were prepared with the assistance of Claude, an AI assistant developed by Anthropic. Its assistance covered drafting and revising the text, writing and debugging the analysis and figure-generation code, and, in the course of that work, identifying several defects in earlier versions of the analysis pipeline that are disclosed in Section VI-E. All experimental design decisions, all interpretations of results, and the decision to report each negative and superseded result rather than remove it are the author's. Every number reported in this paper is produced by committed code from committed data and was verified by re-execution; no result, citation, or reference in this manuscript was generated by a language model without such verification against a primary source. The author takes full responsibility for the content.

---

## Data and Code Availability

**Repository.** All code and derived artifacts described below are available at `https://github.com/sophiezla/counterfeit-drug`. [Before submission, archive a release of that repository to obtain a citable DOI — Zenodo's GitHub integration does this in one step — and cite the DOI here alongside the URL.] The repository contains the data pipeline, the four model implementations, every analysis and figure-generation script, the per-image statistics and split assignments, the persisted model checkpoints, and the manuscript source from which this document is built.

It deliberately contains **no images**. The Kaggle archive carries no license grant, so no image from it is redistributed — only derived per-image statistics, split assignments and filenames, as stated in the Acknowledgment. Grad-CAM overlays and the manual-review contact sheets are excluded for the same reason, since they reproduce image content rather than describe it; both are regenerated by committed scripts from a reader's own copy of the archives. The five analysis scripts named below need no images at all.

All derived artifacts referenced in this paper are reproducible from the archived pipeline. The data pipeline (inventory → filtering → de-duplication → provenance → splits) runs deterministically from the raw archives; the four models, the external evaluations, the ablation experiments, the attention audits and every table and figure in this paper are produced by committed scripts. Per-image capture statistics (`data/metadata/capture_method_stats.csv`), all manuscript tables (`paper/tables/*.csv`) and all figures in vector form (`paper/figures/*.pdf`) accompany this manuscript. Five analysis scripts read only committed artifacts, need no image data and no training, and reproduce their results in seconds: `paper/scripts/metadata_oracle.py` (Table 7), `paper/scripts/provenance_audit_multi.py` (Table 8), `paper/scripts/power_and_leakage_bound.py` (the analytic leakage ceiling of Section VII-C), `paper/scripts/train_only_axis_derivation.py` (Table 25) and `paper/scripts/external_intervals.py` (the external and synthetic-proxy intervals). Together they cover the paper's two central quantitative claims — the acquisition-attributable accuracy ceiling and the audit's behavior on a second dataset — without requiring a reader to obtain the images or run a model.

Two caveats on exact reproduction, both stated in Sections VI-E and X. Model checkpoints are persisted for the production models, with the learning rate, seed, best epoch and epoch count each was trained under, and `result_io.load_checkpoint` refuses to return a checkpoint whose recorded learning rate differs from the caller's expectation; the external evaluations load these rather than retraining. The ablation scripts predate that mechanism and rebuild instead, so their absolute values are comparable within a run and not across runs. Results produced before the augmentation-seeding fix of 2026-07-26 are identified as such in the captions of Tables 20, 22 and 26, and superseded results are archived alongside the current ones rather than deleted.

---

## References

> **Reference verification status.** Every reference has been verified against a primary source: full author lists, venues, volume/issue and DOIs were read from the publisher or indexed record rather than from an aggregator page or from recollection. Where a detail could not be confirmed it is omitted rather than guessed, and said so. Two additional sources encountered during the literature search — a graph-neural-network counterfeit detector operating on chemical structure, and a GAN + CNN + blockchain authentication system — were deliberately **excluded** because no primary source could be located for either; they should be added only if one is found, and never cited from an aggregator summary.

[1] World Health Organization, "Substandard and falsified medical products," WHO fact sheet, 3 Dec. 2024. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/substandard-and-falsified-medical-products. *Verified against the primary source; states "at least 1 in 10 medicines in low- and middle-income countries are substandard or falsified". Fact sheets are revised in place, so the access date should be refreshed at submission.*

[2] S. Ozawa, D. R. Evans, S. Bessias, D. G. Haynie, T. T. Yemeke, S. K. Laing, and J. E. Herrington, "Prevalence and estimated economic burden of substandard and falsified medicines in low- and middle-income countries: A systematic review and meta-analysis," *JAMA Network Open*, vol. 1, no. 4, e181662, 2018, doi: 10.1001/jamanetworkopen.2018.1662. *Verified against the primary record; replaces the unsourced industry market-size estimate carried over from [3].*

[3] R. R. T. Ramos, K. R. B. Samonte, and C. O. Manlises, "Medicine authentication based on image processing using convolutional neural networks," in *Proc. 16th Int. Conf. Computer and Automation Engineering (ICCAE)*, 2024.

[4] H.-W. Ting, S.-L. Chung, C.-F. Chen, H.-Y. Chiu, and Y.-W. Hsieh, "A drug identification model developed using deep learning technologies: Experience of a medical center in Taiwan," *BMC Health Services Research*, vol. 20, art. 312, 2020, doi: 10.1186/s12913-020-05166-w.

[5] K. Al-Hussaeni, I. Karamitsos, E. Adewumi, and R. M. Amawi, "CNN-based pill image recognition for retrieval systems," *Applied Sciences*, 2023.

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

[19] S. K. Jha, "Fake vs Real Medicine Dataset (images)," Kaggle, dataset `surajkumarjha1/fake-vs-real-medicine-datasets-images`, last updated 13 Oct. 2025, license stated as "Unknown". [Online]. Available: https://www.kaggle.com/datasets/surajkumarjha1/fake-vs-real-medicine-datasets-images. *Identity confirmed by matching the archive's total size (279,596,681 bytes) against the listing metadata, re-verified 13 Aug. 2026. Usage figures quoted in Section II-F (574 downloads, 3 public notebooks, 2 votes) were read from the Kaggle dataset API on 13 Aug. 2026 and should be refreshed again at submission, since they change; between 29 Jul. and 13 Aug. 2026 downloads moved 540 → 574 while notebooks, votes, license and last-updated date did not change. The paper's argument depends on the order of magnitude, not the exact count.*

[20] M. Abdelmaksoud, H. Gadallah, and M. Asad, "Mobile-captured pharmaceutical medication packages," Mendeley Data, V1, doi: 10.17632/bjy2svvmn8.1, CC BY 4.0. *Author list and affiliation as recorded in the project's data card; confirm spelling and initials against the dataset landing page before submission.*

[21] Harshini T. G. R., "Counterfeit_med_detection," Roboflow Universe, version 4 (multiclass export), CC BY 4.0. [Online]. Available: https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection. *Workspace identified from the Roboflow Universe listing; the landing page rejects automated requests, so the license line and access date should be confirmed in a browser before submission.*

[22] Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," *Psychometrika*, vol. 12, no. 2, pp. 153–157, 1947.

[23] K. Zhou, Z. Liu, Y. Qiao, T. Xiang, and C. C. Loy, "Domain generalization: A survey," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 45, no. 4, 2023, doi: 10.1109/TPAMI.2022.3195549, arXiv:2103.02503. *Author list and volume/issue verified against the indexed record; the page range was not confirmed and is omitted rather than guessed.*

[24] B. Efron and R. J. Tibshirani, *An Introduction to the Bootstrap*. New York, NY, USA: Chapman & Hall, 1993.

[25] C. Zauner, "Implementation and benchmarking of perceptual image hash functions," M.Sc. thesis, Upper Austria University of Applied Sciences Hagenberg, Jul. 2010. [Online]. Available: https://www.phash.org/docs/pubs/thesis_zauner.pdf. *Verified: institution, year and title confirmed against the thesis PDF hosted by phash.org.*

[26] K. Motwani, R. Dsouza, R. Dsouza, and J. Jose, "Counterfeit medicine detection using deep learning," *International Journal of Innovative Research in Technology (IJIRT)*, vol. 9, no. 3, Aug. 2022. *Full text read; the counterfeit class is constructed by the authors by altering logos and text on web-scraped authentic packaging images.*

[27] B. S. Thomson and W. R. Varuna, "An intelligent counterfeit medicine classification prediction system using modified YOLO: A single stage object detector," *TPM (Testing, Psychometrics, Methodology in Applied Psychology)*, vol. 32, no. S2, pp. 1073–1088, 2025. *Full text read; trains on GAN-synthesized counterfeit images derived from a Kaggle pharmaceutical pill dataset and tests against DrugBank and drugs.com imagery.*

[28] B. S. Thomson and W. R. Varuna, "Detecting counterfeit medicines utilizing artificial intelligence technique," *International Journal of Creative Research Thoughts (IJCRT)*, vol. 13, no. 4, pp. i322–i329, Apr. 2025, ISSN 2320-2882. *Full text read; reports 92% accuracy over an image set cited only as a drugs.com URL, with no image count or partition protocol stated.*

[29] H. Garcia-Cotte, D. Mellouli, A. Rehman, L. Wang, and D. G. Stork, "Deep neural network-based detection of counterfeit products from smartphone images," arXiv:2410.05969, 2024.

[30] P. Grommelt, L. Weiss, F.-J. Pfreundt, and J. Keuper, "Fake or JPEG? Revealing common biases in generated image detection datasets," arXiv:2403.17608, 2024. *Verified against the arXiv record. Cited as the closest independent analogue of this paper's finding: real/generated separation by JPEG compression and image size on the GenImage benchmark, detectors partly reducible to JPEG detectors, and >11-point cross-generator shifts after equalization.*

> **Note on [26]–[28].** These are cited as evidence about dataset-construction practice in this application area, which required reading them in full text; they are not cited as authoritative results, and two of the three appear in venues without visible peer-review records. That distribution of venues is itself part of the observation made in Section II-F.

---


---

## Author Biographies

![Sophie Zhu](paper/figures/author_photo.jpeg)

**SOPHIE ZHU** is a student at Mira Costa High School, in Manhattan Beach, CA, USA. Her research interests include artificial intelligence, healthcare technology, computer vision, and machine learning applications in public health. Her work focuses on the development of accessible and scalable artificial intelligence systems for healthcare challenges, with an emphasis on low-cost technologies for resource-constrained environments. Her current research examines how dataset construction shapes what image classifiers actually learn, and what evaluation protocols are needed before such systems can be trusted in public-health settings.
