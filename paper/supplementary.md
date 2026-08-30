# Supplementary Material

**Provenance Confounding in Image Authenticity Classification: Detection and a
Counterfeit-Medicine Case Study**

Sophie Zhu

This document holds the material the main paper cites but does not reproduce:
the full experimental setup, the complete per-model metric tables and their
figures, the secondary evaluations and ablations, the reproducibility record,
and the appendices. Nothing here is summarized — every section appears as it
did in the full record, and the main paper's claims are traceable to it.

Tables, figures and equations are numbered with an S prefix and are referred
to from the main paper by those numbers. Section references of the form
"Section VI-C" point at the main paper; references of the form
"Section S-III" point within this document.

---

## S-I. Dataset, Method and Experimental Detail

### A. Complete manual quality and modality review

The entire pool was reviewed by a human annotator, image by image, using two purpose-built local tagging tools (a watermark/non-medicine pass and a modality pass), across four rounds. This was a census, not a sample. Fifty-six files were excluded at the filtering stage:

- **47 watermark or stock-photo-overlay images.** Checked rather than assumed: **47/47 (100%) are authentic-labeled**, and they carry overlays from at least six distinct product-catalog or stock-photography sites. This is a second, smaller class-correlated confound, structurally similar to the bulletin-graphic problem of Section III-B.
- **4 non-medicine images**: one literal browser screenshot of another dataset's own web page, and three stock/marketing renders rather than device photographs.
- **5 images with no packaging in frame**: one loose-tablet photograph and four syrup bottles.

The modality census (Table S1) matters for how any result on this pool is described. The dataset is not outer-packaging-only, although its title and the usual framing of this task both suggest it is.

**TABLE S1.**Modality composition of the 510-image modeling pool (complete census, human-annotated).

| Modality | Count | Share |
|---|---|---|
| Blister pack | 223 | 43.7% |
| Outer packaging (carton) | 155 | 30.4% |
| Other (carton + blister together, sachet, mixed) | 132 | 25.9% |

We therefore describe this study's scope as **"packaging and immediate product containers"**. We considered filtering to outer packaging only, which would have removed roughly 57% of the pool and required re-running every split and model; we did not, because the capture-confound finding does not depend on modality composition, and we report the composition explicitly instead. This is a wording correction to the prior claim, not a new experiment.

### B. Synthetic counterfeit proxy

Because no independent counterfeit-labeled source exists (Section III-E), a proxy negative class is constructed by perturbing the *same* 150 external authentic photographs, so that the perturbation is the only systematic difference between classes by construction. Each image receives a deterministically seeded random subset (3–5 of 5) of photographic defects — per-channel color/hue shift, halftone dot-grid overlay, per-channel registration offset, Gaussian blur, contrast reduction — plus text-region tampering (ghosting, thin-strip jitter, or ink dropout) applied to 1 to about half of the text/logo regions located by classical edge-density and connected-component analysis. Parameters are randomized per image specifically to avoid substituting one uniform processing signature for the confound under study.

Two design errors were found and corrected before the set was finalized, both worth recording because both are easy to repeat:

1. **Insufficient severity.** In a first batch, 13% of images were perceptually indistinguishable from their originals (mean per-pixel difference < 5/255 at review resolution) because independent weak parameter draws compounded. Severity ranges were widened, color shift was forced to at least 15% per-channel deviation, halftone spacing was scaled to image size so it survives downscaling, and the number of applied effects was raised from 2–4 to 3–5. After the fix, 0% were imperceptible and the minimum per-pixel difference was 6.0/255.
2. **A reintroduced capture confound.** The first version drew base images from a *different* device subset of the source dataset (iPhone 11 Pro) than the authentic class (Huawei CN). Those subsets differ in mean brightness by more than 2× (0.389 vs. 0.162) because the source dataset deliberately varies lighting across device subsets. This would have recreated exactly the confound this paper is about, via source selection rather than generation. The fix was to generate from the same Huawei CN photographs already serving as the authentic class; the post-fix check gives 0.162 vs. 0.153, and identical median resolution.

All 150 candidates were reviewed by a human annotator side by side with their originals; 150/150 were approved, 0 rejected. The final set is 300 images (150 real authentic + 150 approved synthetic counterfeit). Its remaining class difference in mean file size (1,656 kB vs. 1,018 kB) is a direct causal consequence of the perturbations themselves — blur and contrast reduction lower encoded detail — not an independent acquisition confound.

This set measures robustness to a documented perturbation style. It is **not** a measurement of real-world counterfeit recall, and real counterfeits may differ in ways not modeled at all: absent security features, holograms or tamper seals, wrong packaging substrate, or serial-number and barcode errors. Every reference to it in this paper carries that caveat.

---



> **FIGURE S1.** `paper/figures/fig01_workflow.pdf` — Data provenance, splitting protocol and evaluation design. Sources (top row) pass through source-specific exclusion or verification (second row); the Kaggle and Roboflow pools are de-duplicated into product-identity groups from which the 510-image modeling pool is drawn (third row); the four evaluation partitions (fourth row) feed a single shared training and normalization protocol (bottom band).

> **FIGURE S2.** `paper/figures/fig02_architectures.pdf` — The four model families, with exact parameter counts. Hatched blocks are frozen.

### C. Environment

PyTorch 2.7.1 [17] on CPU only (no CUDA available), scikit-learn 1.9.0 [18]. Seed 42 is set for Python, NumPy and PyTorch before every training run, before every fold, and before every augmented feature-extraction pass. Non-deterministic CUDA kernels are not a factor; `torch.use_deterministic_algorithms` is left off because some CPU operators lack deterministic kernels.

### D. Training protocol

Identical for M2–M4 (Table S2): Adam, batch size 32, class-weighted cross-entropy, maximum 50 epochs, early stopping on validation loss with patience 4 and a minimum improvement threshold. Class weights are inverse-frequency,

$$w_0 = \frac{n}{2 n_0}, \qquad w_1 = \frac{n}{2 n_1}, \qquad \mathcal{L} = -\frac{1}{n}\sum_{m=1}^{n} w_{y_m} \log \hat{p}_{m, y_m} \tag{11}$$

which follows the protocol choice of class weighting over oversampling. The minimum-improvement threshold (1 × 10⁻³) was added after observing a frozen-backbone linear head run for 46+ epochs on noise-level validation-loss "improvements" that a naive patience counter never terminated; with the threshold, patience resets only on a meaningful improvement. The best-validation-loss state is restored at the end of training.

**TABLE S2.**Hyperparameters. The learning-rate grid was searched for 5 epochs per value on Split A train/val only, and the selected value reused for both splits' full runs, following a "document the search range, do not over-search" policy on a dataset this small.

| Setting | Value |
|---|---|
| Optimiser | Adam |
| Batch size | 32 |
| Max epochs / patience / min improvement | 50 / 4 / 1 × 10⁻³ |
| Learning-rate grid | {1 × 10⁻³, 3 × 10⁻⁴, 1 × 10⁻⁴}, 5 epochs each |
| Selected LR (M2 / M3 / M4) | 1 × 10⁻³ / 1 × 10⁻³ / 1 × 10⁻³ |
| Loss | class-weighted cross-entropy, Eq. (S1) |
| Input resolution | 224 × 224, ImageNet mean/std normalization |
| M1 | `LogisticRegression(max_iter=2000, class_weight="balanced")` |
| Cached augmented passes (M3, M4) | K = 3, each seeded with 42 + pass index |
| Seed | 42 |

### E. Frozen-backbone feature caching

For M3 and M4 the backbone is frozen, so its output for a given input never changes during head training, and re-running a full forward pass every epoch on CPU is wasted work. Features are extracted once per partition and the head trained on the cached vectors. To retain the benefit of augmentation despite caching, the training partition is expanded by $K = 3$ independently augmented passes through the backbone, so the head still sees three distinct augmented views of every training image. Validation, test and external partitions use a single deterministic pass.

This is standard linear-probing practice and it is what made M4 tractable at all here: a first attempt at live per-epoch backbone forward passes was terminated by the host before Split A finished. It is nonetheless a fidelity trade-off relative to fresh-every-epoch augmentation, and we record it as such.

### F. Evaluation protocol and metrics

Two kinds of analysis are mixed in this study and the difference matters for how much weight each carries. The split comparison, the four-model roster and the external evaluation were fixed by the protocol before any of them ran, and are confirmatory. Everything about the correction — which axes, which constants, which composition order — was developed after the external failure had been observed, and is exploratory in the strict sense: the axes were nominated by comparing the pool against Split C, and the constants and order were fixed by hand. Three later analyses convert parts of that back into something testable, and each says so where it is used: Section S-I-S re-derives the axes from the training partition alone under a threshold declared in advance, Section S-I-U repeats the production and baseline conditions across five seeds, and the constant and ordering sweeps report every condition they ran rather than the best one. The production constants and the production order were fixed before either sweep existed, which is why Sections VII-B and S-I-R can report that a better setting exists and decline to adopt it.

All metrics use a 0.5 decision threshold unless stated. With TP, FP, FN, TN defined against counterfeit as positive:

$$\mathrm{Sens} = \frac{TP}{TP+FN}, \quad \mathrm{Spec} = \frac{TN}{TN+FP}, \quad \mathrm{BA} = \frac{\mathrm{Sens}+\mathrm{Spec}}{2} \tag{12}$$

$$\mathrm{MCC} = \frac{TP \cdot TN - FP \cdot FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}} \tag{13}$$

ROC-AUC is computed by the Mann–Whitney form with mid-ranks for ties, and PR-AUC as average precision. Uncertainty is a percentile bootstrap over test-set resamples [24]: for $b = 1 \dots 2000$, resample $n$ indices with replacement, recompute the metric, and report the 2.5th and 97.5th percentiles.

Paired model comparison uses McNemar's test [22] on the Split B test predictions. With $n_{01}$ the count of examples model A classifies correctly and model B does not, and $n_{10}$ the converse, we use the exact binomial test when the discordant total is below 25 (which it always is here, 1 ≤ $n_{01}+n_{10}$ ≤ 15):

$$p = 2 \sum_{k=0}^{\min(n_{01}, n_{10})} \binom{n_{01}+n_{10}}{k} 0.5^{\,n_{01}+n_{10}} \tag{14}$$

The external generalization gap for model $m$ is defined on the authentic class only, since Split C has no counterfeit members:

$$\Delta_m = \mathrm{Acc}^{\text{auth}}_{m,\text{Split B test}} - \mathrm{Acc}^{\text{auth}}_{m,\text{Split C}} \tag{15}$$

A negative $\Delta_m$ means the model performs *better* on the external source than on its own in-distribution test partition.

### G. Four reproducibility defects, disclosed

**A non-determinism bug, found and fixed.** The augmented feature-extraction passes of Section S-I-E were originally unseeded, so the augmented views depended on whatever RNG state the process happened to be in — which varies with what ran earlier in the same script and is not reproducible across invocations. This is the mechanism behind a sequence of contradictory readings: the question "does normalization help M3?" was answered positively (+6.0 points), negatively (−21.3 points) and neutrally (−1.3 points) across three runs of nominally the same or closely related conditions before the cause was identified. The fix seeds each pass with 42 + pass index. Determinism was then verified empirically, not assumed: training M3 twice back to back produced byte-identical metric outputs. All production numbers in Section VI postdate the fix. One ablation condition (M3 under two-way normalization, Section S-I-O) was never re-run afterwards and is reported as unverified.

**A learning-rate inconsistency, found and corrected.** Because no checkpoint is persisted, the external-evaluation script re-derives each trained model from scratch, and it hard-coded M2's learning rate at 3 × 10⁻⁴ — a value left over from an earlier retrain. Under the normalized pipeline M2's learning-rate search selects 1 × 10⁻³ (Table S2), so M2's external figures were being produced by a model trained differently from the one supplying its in-distribution numbers.

The hard-coded constant has been replaced by a recorded one: each training script now writes the learning rate it actually used, and every rebuild path reads it back, raising an error rather than guessing if the record is absent. The correction is verifiable — under the recorded rate the rebuild's per-epoch training curve is byte-identical to the training run of record, which the 3 × 10⁻⁴ rebuild demonstrably was not. M2's rows in both external evaluations were then re-measured. Its authentic-only external accuracy moves from 91.3% to **86.0%** and its generalization gap from −6.7 to **−1.4** points; on the synthetic proxy its accuracy moves from 0.623 to 0.633 and its ROC-AUC from 0.788 to 0.794. Every qualitative claim in this paper is unchanged: M2 remains the best-generalizing model and the only one with a negative gap. The superseded values are preserved alongside the current ones in the archived results.

**Checkpoints, and the third divergence they immediately exposed.** The architectural weakness behind both defects above — that no weights were ever saved, so every downstream consumer re-derived "the trained model" by retraining it — has now been removed. Each training run persists the restored best-validation state together with the learning rate, seed, best epoch and epoch count it was produced under, and the loader refuses to return a checkpoint whose recorded learning rate differs from the one the caller expects, which is exactly the mismatch that produced the Model 2 defect.

Persisting checkpoints required re-running the three trainable models, and that re-run disclosed a third discrepancy which we report rather than quietly adopt. M2 and M3 reproduced their recorded Split B test accuracies exactly (0.865 and 0.932). **M4 did not: it now scores 0.919 (68/74) where the previously committed results recorded 0.946 (70/74)** — a two-image difference, with a training trajectory that early-stops at epoch 18 rather than running to 26.

We investigated and can report what is and is not established. The current value is *reproducible*: three consecutive re-runs of M4 produced byte-identical training curves and metric files, so the pipeline is deterministic as it now stands, and the determinism check previously performed on M3 (Finding 13) now holds for M4 as well. The normalization operator is confirmed active in that run (a normalized and an un-normalized tensor for the same image differ by 0.44 in mean absolute value). The split and pool files are unchanged since they were built. What we cannot establish is the *cause* of the difference from the earlier run, because the artifacts that would identify it — that run's weights and cached features — were never saved, which is the very defect being fixed. The most likely explanation is an intermediate code state during the several rounds of normalization and learning-rate work, but we cannot demonstrate it.

We therefore report 0.919 as M4's Split B accuracy of record, since it is the value the committed, deterministic pipeline produces and the one every derived table has been regenerated from. Its consequences are stated where they arise: M4's leakage delta rises from +4.1 to +6.8 points (Table S4), the smallest pairwise *p*-value rises from 0.057 to 0.118 (Table S5), and M4's pooled error count rises from 5 to 7 (Table S7). No qualitative claim in this paper changes — the leakage effect remains small and bounded, no model comparison approaches significance, and the external results are unaffected — but the episode is the clearest possible demonstration of why the checkpoint omission mattered, and of the fact that it was caught only because the omission was finally repaired.

**A fourth defect, in a path that never checked itself.** While building the attention audit of Section S-I-J we found that all three Grad-CAM scripts obtained the backbone by calling its constructor directly, which returns a module in training mode, and set only the classification head to evaluation mode. The backbone's 49 batch-normalization layers therefore ran on batch-of-one statistics and overwrote their running averages on every image. This was invisible for as long as nobody asked the scripts for a number that could be checked: the heatmaps looked plausible. It surfaced immediately once a script printed its external accuracy alongside the heatmaps and that figure read 0.16 against the 0.807 of record. Section S-I-J states the consequence for Fig. S10; the scripts now force evaluation mode and the quantitative audit asserts its accuracy against the value of record before reporting anything.

Two lessons generalize beyond this study, and both are uncomfortable.

The first concerns persistence: a pipeline can be fully seeded, deterministic on re-run, and still fail to reproduce its own published numbers, if nothing durable was saved at the moment those numbers were produced. Determinism is a property of the code; reproducibility of a *result* additionally requires that the artifact be persisted.

The second concerns verification, and is the one we would emphasize. All four defects in this study — a stale learning rate, an unseeded augmentation pass, an unreproducible accuracy, and a backbone in the wrong mode — occurred in code paths that produced an output nobody could check against a known value. The evaluation and training paths, which produce accuracies that are compared against each other constantly, were correct throughout. The generalizable practice is therefore cheap and specific: **any script that rebuilds or reloads a model should compute one metric whose correct value is already known, and refuse to report anything if it disagrees.** Every one of these defects would have been caught on first execution by that single line.

---

### H. In-distribution performance and the leakage comparison

One definition governs everything in this section. "Leakage-free", here and throughout, means free of **product-identity** leakage: Split B guarantees that no perceptual-hash cluster of near-duplicate photographs straddles a partition or a cross-validation fold. It makes no claim about acquisition. Because every counterfeit-labeled image in the pool was produced by one capture pipeline and every authentic-labeled image by another (Section VI-A), *no* partition of this pool can place a capture process on only one side of a fold, and grouped cross-validation inherits the confound in every fold at full strength. The numbers below are therefore the best in-distribution estimates obtainable on this data and are still, in the sense Section VI-A makes precise, measurements of the acquisition process. Readers should not read Split B as a corrected evaluation; it corrects one of the two problems.

Table S3 gives the complete metric set for all four models on both in-distribution test partitions; Fig. S6 gives the corresponding confusion matrices, Fig. S4 the ROC curves and Fig. S5 the precision–recall curves.

**TABLE S3.**In-distribution test performance. Counterfeit is the positive class. Sens = recall. BA = balanced accuracy. Bracketed intervals are 95% percentile bootstrap (2000 resamples).

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

**TABLE S4.**Leakage quantification. Δ is Split A accuracy minus Split B accuracy; a positive Δ is the direction the naive-split-inflates-accuracy hypothesis predicts. Bracketed intervals are 95% percentile bootstrap (2000 resamples), as in Table S3. Split B CV is 5-fold `StratifiedGroupKFold` on the Split B training partition. Throughout this paper "leakage-free" means free of **product-identity** leakage only. The grouping decorrelates which products appear in which fold and nothing else; it cannot decorrelate acquisition, because every counterfeit-labeled image in the pool came from one capture pipeline. Every number in this table is therefore measured under the provenance confound, which is the point of Section VI-A.

| Model | Split A accuracy (95% CI) | Split B accuracy (95% CI) | Split B 5-fold CV | Δ (A − B) |
|---|---|---|---|---|
| M1 hist+LR | 0.842 [0.763, 0.921] | 0.838 [0.743, 0.919] | 0.832 ± 0.049 | +0.004 |
| M2 CNN | 0.868 [0.789, 0.934] | 0.865 [0.784, 0.932] | 0.865 ± 0.036 | +0.004 |
| M3 MobileNetV3 | 0.934 [0.868, 0.987] | 0.932 [0.865, 0.986] | 0.964 ± 0.011 | +0.002 |
| M4 EfficientNet-B0 | 0.987 [0.961, 1.000] | 0.919 [0.851, 0.973] | 0.983 ± 0.011 | **+0.068** |

The leakage effect is real but small, and only M4 shows it at a magnitude worth discussing (Fig. S3). Three of four deltas are within half a percentage point of zero, and even M4's 6.8-point delta sits inside overlapping confidence intervals (Split A [0.961, 1.000] against Split B [0.851, 0.973]). The mechanism is not in doubt — Split B provably eliminates the 9 straddling product groups that Split A permits — but its *magnitude* on this pool is better established by counting and by a paired experiment than by this delta, for the reason the next two paragraphs give.

Counting directly: **7 of the 76 Split A test images belong to a product-identity group that also appears in Split A's training partition**, a direct exposure rate of 9.2%. Those seven are the only images any model could classify correctly by recognizing a training photograph rather than by generalizing, so 9.2 points is the most that *recognition* can contribute. The count follows from the split alone, involving no model and no run, so it is immune to the sampling-variance objection that limits the measured deltas — which duly fall below it (+0.2 to +4.1 points).

It is worth being exact about what that does not cover. Admitting a near-duplicate into training also changes the fitted parameters, and those parameters decide the remaining 69 predictions as well; the count constrains the recognition channel and says nothing about that indirect one, in either direction. The measured delta does not close the gap either, because Split A and Split B do not share a test set. Section S-I-V therefore measures leakage directly, holding the test set fixed and varying only whether the mates are admitted, and finds +0.3 points [−1.9, +2.4] for M2 and no change at all for M3 and M4. On a pool with this duplicate structure, then, image-level leakage is not the dominant inflation mechanism — bounded at 9.2 points by the count, measured at 0.3 with an interval of ±2, against an external collapse worth more than 90. A dataset with heavier duplicate sourcing would raise both the exposure rate and the effect.

> **FIGURE S3.** `paper/figures/fig13_leakage.pdf` — Split A vs. Split B test accuracy per model with 95% bootstrap intervals and the per-model delta.

**No pairwise model difference is statistically significant** (Table S5). Discordant counts are small — for M3 vs. M4 only three test images are classified differently — and the smallest *p*-value is 0.118, for the comparison between the 97-parameter linear baseline and frozen MobileNetV3.

"Not significant" conflates two different situations, and separating them matters, because only one of them is a statement about the models. Since McNemar's exact test depends only on the discordant pairs, the most significant *p*-value *available* at a given discordant total can be computed directly. For five of the six pairs it lies between 0.0001 and 0.002, so those comparisons could have detected a difference had one existed, and their non-significance is genuine evidence that the models perform alike on this partition. The sixth, M3 vs. M4, has a discordant total of 3, for which the most significant *p*-value obtainable is 0.250: **no split of three discordant pairs can reach *p* < 0.05, so that comparison was unresolvable by construction** and is not evidence of equivalence at all.

The power this affords is poor in absolute terms. At the observed discordance levels, reaching *p* < 0.05 requires a net difference of essentially the entire discordant set — 10 of 74 test images at D = 10, 14 at D = 14 — an accuracy gap of 13.5 to 18.9 points. **This design could only have detected between-model differences larger than roughly 13 points.** Every model in the roster sits within 15 points of every other in-distribution, so it was never capable of separating them, and no ranking in this paper should be read as one. That is a property of the dataset's size, not a finding about architectures.

**TABLE S5.**Pairwise McNemar's tests on the Split B test partition (n = 74), exact binomial. $n_{01}$: A correct, B wrong. $n_{10}$: A wrong, B correct.

| Model A | Model B | $n_{01}$ | $n_{10}$ | Discordant | *p* | Significant (α = 0.05) |
|---|---|---|---|---|---|---|
| M1 | M2 | 5 | 7 | 12 | 0.774 | no |
| M1 | M3 | 4 | 11 | 15 | 0.118 | no |
| M1 | M4 | 5 | 11 | 16 | 0.210 | no |
| M2 | M3 | 3 | 8 | 11 | 0.227 | no |
| M2 | M4 | 4 | 8 | 12 | 0.388 | no |
| M3 | M4 | 2 | 1 | 3 | 1.000 | no |

Six pairwise tests on one partition raises the question of family-wise error, and here it resolves trivially: no comparison is significant before correction, so no correction can make one significant. For completeness, Holm–Bonferroni over the six raises the smallest adjusted *p* from 0.118 to 0.711 and pins the remaining five at 1.000. The conclusion — that this partition cannot distinguish a 97-parameter linear model from a 4-million-parameter pretrained backbone — is therefore robust to the correction and, if anything, understated without it. The reverse risk, that correction masks a real difference, is addressed by the power calculation below rather than by the tests themselves.

Multiplicity is worth a word for the rest of the paper too, because the manuscript reports a great many comparisons. Only Table S5 contains hypothesis tests; every other comparison here — the leakage deltas, the per-axis ablations, the constant sweep, the ordering sweep — is a point estimate reported with its interval where one exists, and none is accompanied by a *p*-value or described as significant. They are not a test family and no correction applies to them. What does apply is the weaker caution stated in Section S-II: they are single realisations, so a difference of a point or two between two conditions should not be read as a difference at all, and we draw conclusions only from separations far larger than that, such as the 28-point gap between the two ordering groups in Section VII-B.

Two further in-distribution observations. First, the training curves (Fig. S7) show the expected pattern: the frozen-backbone heads converge smoothly to near-zero loss, while the from-scratch CNN plateaus with a noisy validation curve and stops at epoch 13, consistent with its 23,938-parameter capacity being the binding constraint rather than overfitting. Second, calibration differs sharply across models (Fig. S8). M1's predicted probabilities are compressed into roughly [0.33, 0.56] — it separates the classes largely by which side of 0.5 a narrow band of scores falls on — whereas M3 and M4 are strongly saturated near 0 and 1. This becomes important in Section S-I-I.

> **FIGURE S4.** `paper/figures/fig04_roc.pdf` — ROC curves, both in-distribution partitions, with AUCs.
> **FIGURE S5.** `paper/figures/fig05_pr.pdf` — Precision–recall curves, both partitions, with average precision.
> **FIGURE S6.** `paper/figures/fig06_confusion_ab.pdf` — Confusion matrices, all four models, both partitions.
> **FIGURE S7.** `paper/figures/fig07_training_curves.pdf` — Split B training and validation loss and accuracy; the filled marker is the restored best-validation-loss epoch.
> **FIGURE S8.** `paper/figures/fig11_calibration.pdf` — (a) Reliability curves on Split B test. (b) Per-model score distributions by true class.

### I. Synthetic counterfeit-proxy stress test

Split C is authentic-only and therefore silent on counterfeit recall. Table S6 reports all four models on the 300-image synthetic proxy of Section S-I-B, and Fig. S9 plots the same confusion counts as matrices. As stated there, this measures robustness to a specific documented perturbation style, not real-world counterfeit recall.

**TABLE S6.**Synthetic counterfeit-proxy Split C (150 authentic + 150 perturbed copies of those same photographs). Confusion counts are exact. PR-AUC is not reported because per-image scores were not persisted by the evaluation script; this is a tooling gap, not a property of the data. 95% intervals, n = 300 with 150 per class — accuracy (Wilson): M1 0.500 [0.444, 0.556], M2 0.633 [0.577, 0.686], M3 0.483 [0.427, 0.540], M4 0.550 [0.493, 0.605]; **M4's row here predates the Split B correction of Section S-I-G** and so describes the superseded 0.946 model rather than the 0.919 one; the two differ by two in-distribution images, and M4's qualitative verdict (weak separation at best, accuracy interval spanning 0.5) does not depend on which is used; ROC-AUC (Hanley–McNeil closed form, used because per-image scores are unavailable for a bootstrap): M1 0.895 [0.859, 0.932], M2 0.794 [0.743, 0.845], M3 0.503 [0.438, 0.569], M4 0.570 [0.505, 0.634].

| Model | TP | FP | FN | TN | Accuracy | Precision | Sens | Spec | F1 | BA | MCC | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 hist+LR | 150 | 150 | 0 | 0 | 0.500 | 0.500 | 1.000 | 0.000 | 0.667 | 0.500 | 0.000 | **0.895** |
| M2 CNN | 61 | 21 | 89 | 129 | 0.633 | 0.744 | 0.407 | 0.860 | 0.526 | 0.633 | 0.299 | 0.794 |
| M3 MobileNetV3 | 29 | 34 | 121 | 116 | 0.483 | 0.460 | 0.193 | 0.773 | 0.272 | 0.483 | −0.041 | 0.503 |
| M4 EfficientNet-B0 | 44 | 29 | 106 | 121 | 0.550 | 0.603 | 0.293 | 0.807 | 0.395 | 0.550 | 0.117 | 0.570 |

Three readings, in decreasing order of interest.

**M1's result is a calibration failure, not an absence of signal.** It labels essentially everything counterfeit (sensitivity 1.000, specificity 0.000, accuracy pinned at exactly 0.500 by the balanced design, MCC exactly 0) — yet it has by far the best ROC-AUC of the four at 0.895. Its raw scores rank perturbed images above clean ones well; its 0.5 threshold, fitted on the very different Kaggle brightness and resolution distribution, is simply in the wrong place for this set. Compare its 0.000 on the authentic-only Split C: the two results together say that M1's color-histogram features carry *some* transferable signal that its decision threshold cannot exploit out of distribution. This is consistent with the compressed score range visible in Fig. S8(b).

**M2 and M4 show modest genuine separation but under-detect.** AUCs of 0.794 and 0.570 with sensitivities of 0.407 and 0.293: at the default threshold both are far more likely to pass a synthetic counterfeit as authentic than the reverse — M2 misses 89 of 150 and M4 misses 106. For a screening application that error direction is the costly one. The two models are not on the same footing, and the intervals in Table S6's caption matter here: M2's AUC interval [0.743, 0.845] is comfortably clear of chance, whereas M4's [0.505, 0.634] excludes 0.5 only barely, and M4's *accuracy* interval [0.493, 0.605] does not exclude it at all. M4 should be described as weakly separating at best, and no ranking between M4 and M3 is supportable on this evidence.

**M3 is at chance (AUC 0.503, 95% CI [0.438, 0.569], MCC −0.041), and this cross-validates the attention finding of Section S-I-J.** M3's comparatively strong authentic-only external accuracy is best explained by a backdrop-matching rule (Section S-I-J); such a rule provides exactly zero signal for separating a photograph from a perturbed copy of *the same photograph*, since the backdrop is identical in both. Chance performance is what that explanation predicts, obtained here from a completely independent evaluation set.

> **FIGURE S9.** `paper/figures/fig09_confusion_synthetic.pdf` — Confusion matrices on the synthetic proxy, with accuracy and ROC-AUC per model.

### J. Attention audit

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

The categorization itself is more robust to that objection than the aggregate statistic is, and the reason is worth stating because the objection is a fair one. The diffuseness result reported below and the caveat that accompanies it — that a 128 px bottleneck degrades activation-based attribution — apply to the *magnitude and sharpness* of these maps. The finding here is not a magnitude but a **contrast**: within one model, one bottleneck and one external set, the maps for correct predictions and the maps for incorrect predictions fall on opposite sides of the frame, 20 out of 20 each, twice over. Degraded attribution adds noise, which would blur that split; it does not manufacture a perfect one that happens to align with the outcome. We therefore continue to report the differential result while declining, below, to interpret the absolute spatial distribution.

**The consequence for Split D.** Section VI-F reported that M3 and M4 hold up on the second external distribution while M2 collapses, and read that as the pretrained backbones transferring across a capture shift. The attention evidence forces a weaker reading. Split C and Split D are the same products photographed against **the same dark backdrop** under different devices and lighting; the surround changes in brightness and color but not in kind. A model predicting "authentic" from the presence of that backdrop would continue to do so on Split D. **Split D therefore does not test the shortcut these heatmaps identify**, and M3's and M4's stability across the two external sets is consistent with the shortcut persisting rather than with genuine packaging recognition. What Split D does establish stands — M2's Split C result was capture-specific — but it cannot be read as evidence that the backbones learned the intended task.

> **FIGURE S10.** `paper/figures/fig14_gradcam.pdf` — Grad-CAM overlays, six of the 62 categorized maps. (a)–(b) M4 in-distribution, one product-focused correct prediction and one error attending to background corners. (c)–(d) M4 external: an authentic photograph called counterfeit with attention on the printed name, and a correct authentic call with attention on the surround. (e)–(f) the same pair for M3. Panels (c)–(f) are representative in the strict sense: on the external sets the split shown here held for all 40 maps. Every heatmap was regenerated from the persisted production checkpoint after the defect described below.

**Coverage, and a defect in how these heatmaps were produced.** Two different things are complete here and it is worth separating them. Every map the study produced was scored: 62 of 62, with no map set aside, and the tags are committed at `modeling/results/gradcam_review_completed.csv`. The *images* those maps were drawn from are a stratified sample rather than a census — in-distribution, all 7 errors plus a seeded sample of 15 correct predictions; externally, a seeded sample of 10 correct and 10 incorrect predictions per model. The audit therefore characterizes the two outcome classes and not the full 150-image external set, and the claim it supports is the contrast between them. It also carries a defect we found only after the fact, and which we report because it bears on how much weight these maps can take.

The three Grad-CAM scripts obtained their backbone by calling the constructor directly, which returns a module in **training mode**, and set only the classification head to evaluation mode. With 49 batch-normalization layers in the backbone and Grad-CAM processing one image at a time, those layers therefore used batch-of-one statistics and overwrote their running averages on every call. Every heatmap produced before the fix consequently described a mis-configured network rather than the trained model. We detected this only when a later script printed a sanity metric — its external accuracy read 0.16 against the 0.807 of record — and confirmed it by checking that, with evaluation mode set, a manually assembled feature path reproduces the production path to within 3 × 10⁻⁶. The scripts now force evaluation mode and load the persisted production head rather than retraining it, every map was regenerated from that path, and the categorization reported above is of the regenerated maps. The quantitative audit below asserts its own accuracy against the value of record before reporting anything, which is the check that would have caught the defect on first execution.

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

**A second attribution method, and the one place it disagrees.** Everything above rests on Grad-CAM: one method, one annotator, forty sampled maps, and a method this subsection has just argued is degraded by the bottleneck it runs behind. `modeling/occlusion_sensitivity.py` puts the same question to a method that shares none of those weaknesses. It slides a 64 px occluder over the network's 224 × 224 input on a 6 × 6 grid and records how far P(authentic) falls when each region is hidden; a region whose occlusion costs the model its "authentic" answer is a region that answer was resting on. The positive part of that surface is normalized to unit mass and summarized with the border statistic used above, so the two methods are comparable by construction. It needs no annotation, no categorization and no sampling, so it runs on all 150 external images for each model, from the persisted production checkpoints — and each model reproduces its Split C accuracy of record, 0.773 and 0.807, before any attention number is reported.

| Model, by outcome | Images | Border mass (95% CI) | Images above the 0.642 uniform reference |
|---|---|---|---|
| M3, called authentic (correct) | 116 | 0.760 [0.738, 0.782] | 96/116 |
| M3, called counterfeit (wrong) | 34 | **0.856** [0.826, 0.886] | 33/34 |
| M4, called authentic (correct) | 121 | 0.614 [0.585, 0.643] | 55/121 |
| M4, called counterfeit (wrong) | 29 | **0.803** [0.738, 0.868] | 24/29 |

Three readings, and the third one changes a claim.

**The error pattern is confirmed, for both models.** On external images each model calls counterfeit, the evidence for "authentic" sits in the surround — 0.856 and 0.803 against a uniform 0.642, and 33 of 34 and 24 of 29 individual images above that reference. For a two-class model, evidence for "authentic" concentrated away from the product is the same statement as evidence for "counterfeit" concentrated on it, which is what the categorization reported.

**M3's correct answers are confirmed too.** 0.760 [0.738, 0.782], with 96 of 116 images above the uniform reference: when M3 gets an external image right, it is responding to the surround. An independent method, over the whole set rather than ten sampled maps, agrees with the categorization.

**M4's correct answers are not.** Its border mass over the 121 images it calls authentic is 0.614 [0.585, 0.643], which does not separate from the 0.642 uniform reference, and 55 of 121 individual images exceed it — half of them. Occlusion does not find M4's correct external answers resting on the background, and the categorization of ten sampled maps said it did.

We report the disagreement rather than choose a winner, and we read the paper's claim down to what both methods support. Three things bear on which to weight. The occlusion measurement covers every external image rather than a seeded sample of ten, and it is causal rather than gradient-based, which are reasons to prefer it. Grad-CAM here runs behind the 128 px bottleneck this subsection has already argued degrades it, which is a reason to distrust the maps. And the two do not measure the same quantity: Grad-CAM weights a feature map by the gradient of the predicted-class logit, occlusion measures what removing a region actually costs, and a model can carry a gradient signature over the surround without a causal dependence on it. What we will not do is keep the stronger claim because one of the two methods supports it. Section VI-G states the consequence: the surround dependence stands for M3 and for both models' errors, and does not stand for M4's correct external answers, so the reading that the two backbones behave identically is withdrawn.

The content-aware measure that would settle it is still the one Section X names — attention mass inside an annotated product box rather than inside a radial ring, which distinguishes "away from the center" from "not on the product" for images whose product is off-center. `scripts/23_build_product_box_tool.py` and `modeling/attention_in_box.py` implement it end to end and are committed; what they need is the annotation pass, which has not been done.

### K. Error analysis

**TABLE S7.**Error counts pooled over both in-distribution test partitions (each model contributes 76 + 74 = 150 predictions).

| Model | Predictions | Errors | Error rate |
|---|---|---|---|
| M1 hist+LR | 150 | 24 | 16.0% |
| M2 CNN | 150 | 20 | 13.3% |
| M3 MobileNetV3 | 150 | 10 | 6.7% |
| M4 EfficientNet-B0 | 150 | 7 | 4.7% |
| Pooled | 600 | 61 | 10.2% |

Thirty-six distinct images account for all 61 errors, and six are misclassified by three or more independent model/split combinations. Three of those six were examined individually in an earlier round of this project, and their diagnoses are informative: one is the recurring carton whose Grad-CAM attention falls on background corners (a confound case); one is a sachet, well lit and legible with no visible defect, whose attention *does* fall on the product's regulatory logo (a genuine visual-similarity case, i.e. real task difficulty rather than a shortcut artifact); and one is a blister image on which the model attends to the tablets themselves. A fourth image examined in that round is a 100 × 100 px thumbnail, far below the pool's typical resolution, misclassified only by the two weakest models — a resolution/detail failure rather than an ambiguity.

The qualitative diagnoses above were made on the pre-normalization models; the counts in Table S7 are recomputed from the current models of record. Six of 36 error images is a deliberate, non-exhaustive sample selected for cross-model agreement, not a random one.

The shape of Table S7 is worth stating plainly against Section VI-E. In-distribution, these models make few errors and most of those errors are explicable. Externally, two of them were wrong on every single image. Both statements are true simultaneously, and a study reporting only the first would be describing a system that does not work as one that works well.

### L. Computational cost

**TABLE S8.**Measured cost, single image, CPU only (PyTorch 2.7.1, batch size 1, mean over the 74 Split B test images after warm-up). Preprocessing for M2–M4 is decode + three-way normalization + resize + tensor conversion; for M1 it is decode + resize + histogram. Weight memory is fp32 parameter storage.

| Model | Trainable params | Frozen params | Weight memory | Preprocess | Forward | Total | Throughput |
|---|---|---|---|---|---|---|---|
| M1 hist+LR | 97 | 0 | < 0.01 MiB | 18.2 ms | 0.01 ms | 18.2 ms | 54.9 img/s |
| M2 CNN | 23,938 | 0 | 0.09 MiB | 16.8 ms | 17.4 ms | 34.3 ms | 29.2 img/s |
| M3 MobileNetV3 | 1,154 | 927,008 | 3.54 MiB | 16.8 ms | 71.9 ms | 88.7 ms | 11.3 img/s |
| M4 EfficientNet-B0 | 2,562 | 4,007,548 | 15.30 MiB | 16.8 ms | 154.4 ms | 171.2 ms | 5.8 img/s |

Two points bear on deployment. First, preprocessing — including the entire three-way normalization — costs under 17 ms per image and is negligible relative to any CNN forward pass; the correction proposed in this paper is essentially free at inference time. Second, the accuracy/cost ordering is unhelpful for a field deployment: M4 costs 5× M2's total latency and 166× its weight memory for an in-distribution difference that Table S5 cannot distinguish statistically, while M2 is the model with the best external accuracy (Table 9).

**Training wall-clock time is not reported.** The original runs were not instrumented for it and the host repeatedly terminated long-running background processes during the project, so any retrospective figure would be unreliable. Epochs to convergence are reported instead (Table S9); every model trains on CPU in minutes, not hours, and the frozen-backbone models train on cached features so that an "epoch" involves no image decoding and no convolution.

**TABLE S9.**Epochs run and best-validation-loss epoch (M1 is a convex fit with a deterministic solver and no epoch structure).

| Model | Split | Epochs run | Best epoch | Best val loss | Best val accuracy |
|---|---|---|---|---|---|
| M2 CNN | A | 10 | 5 | 0.336 | 0.870 |
| M2 CNN | B | 13 | 8 | 0.259 | 0.924 |
| M3 MobileNetV3 | A | 15 | 10 | 0.073 | 0.974 |
| M3 MobileNetV3 | B | 37 | 36 | 0.057 | 0.962 |
| M4 EfficientNet-B0 | A | 13 | 8 | 0.099 | 0.974 |
| M4 EfficientNet-B0 | B | 26 | 23 | 0.031 | 1.000 |

### M. Calibration of the probability outputs

Everything above treats the models as decision rules at a fixed threshold. Any deployment as a triage tool would instead read the probability, so calibration is the property that decides whether the score can be thresholded at all. Table S10 quantifies it from the persisted per-image scores, on all four partitions, with no retraining.

**TABLE S10.**Calibration on all four partitions, computed from the persisted per-image scores. Brier is the mean squared error of the predicted probability. ECE is expected calibration error over ten equal-width confidence bins; MCE is the worst single bin. Conf is mean confidence in the predicted class; conf − acc is positive for overconfidence. Splits C and D are authentic-only, so their accuracy is a specificity and their calibration is measured against one class; see the caveat below.

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

**M1 fails in an unusual and diagnostic direction.** In-distribution it is markedly *under*confident — mean confidence 0.561 against accuracy 0.838, an ECE of 0.277 driven entirely by scores that hug the decision boundary. Externally the same hugging behavior becomes maximal overconfidence, because it is wrong on 150 of 150 and 149 of 149 images while still reporting confidences of 0.54–0.56. This is the same object as the synthetic-proxy result of Section S-I-I, where M1's ROC-AUC of 0.895 coexisted with accuracy pinned at exactly 0.500: its ranking carries some signal and its threshold carries none.

**M4 is the only model whose calibration survives both capture shifts** (0.061 → 0.098 → 0.055), which is consistent with its accuracy behavior in Table 10 and, like that result, says nothing about whether it is reading packaging — Section S-I-J applies unchanged.

One caveat bounds all of this. Splits C and D contain only authentic images, so accuracy on them is a specificity and the calibration statistics are measured against a single class; ECE and accuracy are therefore not independent quantities there in the way they are on Splits A and B, and the external rows should be read as a description of how confidently each model commits its false positives rather than as a full calibration curve. A counterfeit-labeled external set, which Section IX lists as the outstanding acquisition, is what would make external calibration measurable in the ordinary sense.

### N. Which axes matter, and are they complementary?

Table S11 and Fig. S11(a) ablate four axes on M4 within single runs.

**TABLE S11.**Per-axis ablation on M4 (EfficientNet-B0). Rows are grouped by the script execution that produced them; compare only within a group. ✓ = axis applied. All three groups predate the seeding fix of Section S-I-G, so their absolute values carry the caveat stated in the text; group (ii)'s white-balance rows are additionally superseded by the deterministic rerun in Table S12, and are retained here only so that the two can be read against each other. The two comparisons this table is used for — that the axes are complementary, and that white balance is not one of them — are both reproduced post-fix in Table S12.

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

Every group in Table S11 predates the seeding fix of Section S-I-G, which matters more for this claim than for the others because it is the one the correction rests on. It is reproduced post-fix, and by a script written for a different purpose: the white-balance rerun of Table S12 contains both a two-way and a production three-way condition in one deterministic execution, and returns 0.500 against 0.820. The third axis adds 32 points there against the 27 recorded here, so the complementarity conclusion does not depend on the compromised runs even though the exact decimals do.

**White balance is ruled out, and the test was repeated to make sure of it.** It was a plausible fourth axis: the Kaggle pool has a measurably warm cast (channel means R:G:B ≈ 1 : 0.94 : 0.86) against the external set's more neutral 1 : 0.93 : 0.93. The original test of it, however, was run before the per-pass seeding defect of Section S-I-G was fixed, and it compared against a two-way pipeline that compression had not yet joined — so it rejected the axis on a difference of 3.3 points using a harness whose spread on an unchanged condition was 17. That is not a basis for excluding anything, so the experiment was rebuilt with per-pass seeding and the recorded learning rate, and rerun against the pipeline that actually ships, with its own same-run baselines (Table S12).

The conclusion survives, more firmly than before. Gray-world normalization applied alone leaves external accuracy at 0.067, essentially the unnormalized baseline. Added to the production three-way operator it moves external accuracy from 0.820 to 0.780. Added to the two-way operator — the comparison the original experiment attempted — it moves 0.500 to 0.347, a decrement four times larger than the one originally reported. Both combinations point the same way, and the axis buys nothing in either.

**TABLE S12.**Gray-world white balance as a fourth axis. M4 (EfficientNet-B0), all five conditions from one script execution after the seeding fix, so all rows are directly comparable. WB is composed with the other photometric operator, before the compression bottleneck.

| Condition | Operators | Split B test accuracy | Split C accuracy |
|---|---|---|---|
| Production three-way | R, B, C | 0.919 | **0.820** |
| White balance alone | W | 0.905 | 0.067 |
| Production three-way + WB | R, B, W, C | 0.932 | 0.780 |
| Two-way | R, B | 0.919 | 0.500 |
| Two-way + WB | R, B, W | **0.960** | 0.347 |

Three things are worth taking from this beyond the axis itself. A real, measurable, dataset-wide difference between the sources need not be part of the mechanism, which is an argument for testing candidate axes rather than reasoning about them. A rejection is a claim and needs a harness good enough to support it; this one did not have one until it was rerun, and the corrected numbers happen to agree, which was not guaranteed. And the two-way-plus-WB condition is a third instance of the inversion documented in Section VII-B: it has the highest in-distribution accuracy of the five (0.960) and the second-lowest external accuracy (0.347).

**Robustness and in-distribution accuracy are not in tension here.** The best external condition in group (i) is also the best in-distribution condition in that group (0.959), and in group (iii) the three-way condition matches the two-way condition in-distribution (0.932 both) while adding 27 points externally. Removing shortcut access did not force a trade-off; on this data it improved both, presumably because the removed variance was class-correlated noise with respect to the intended task.

> **FIGURE S11.** `paper/figures/fig10_ablation.pdf` — (a) M4 within-run ablation of the three retained axes. (b) Change in external accuracy under two-way and three-way normalization, per model.

### O. Is the correction architecture-dependent?

Yes, and the answer changed twice during this study, which is itself the methodological lesson.

**TABLE S13.**Normalization extended to all four models. Two-way = resolution + brightness; three-way adds compression. Each row's baseline and normalized numbers come from the same script execution. M4's three-way row comes from the single-model experiment that introduced the axis (group (iii) of Table S11). Both the two-way and the three-way executions predate the seeding fix of Section S-I-G, so every number in this table carries that caveat; each row's within-run baseline-to-normalized comparison, which is what the table is used for, is unaffected.

| Model | Two-way Δ external | Three-way Δ external | Three-way normalized: Split B / Split C |
|---|---|---|---|
| M1 hist+LR | +0.000 (0.000 → 0.000) | +0.000 (0.000 → 0.000) | 0.541 / 0.000 |
| M2 CNN | +0.847 (0.000 → 0.847) | **+0.913** (0.000 → 0.913) | 0.838 / 0.913 |
| M3 MobileNetV3 | −0.213 (0.733 → 0.520)\* | +0.060 (0.753 → 0.813) | 0.946 / 0.813 |
| M4 EfficientNet-B0 | +0.540 (0.087 → 0.627) | +0.727 (0.053 → 0.780) | 0.932 / 0.780 |

\* Every condition in this table predates the seeding fix of Section S-I-G, but this is the one whose *sign* the fix later reversed, so treat its magnitude as unverified rather than merely imprecise.

The final column of Table S13 does not reproduce Table 9, and the difference is expected rather than a discrepancy to reconcile: Table 9 reports the production pipeline, Table S13 reports standalone single-run ablation scripts. For M3 the two read 0.773 and 0.813 externally, for M4 0.813 and 0.780, and for M2 0.860 and 0.913. Only Table 9's column is the result of record. We report both rather than silently dropping the ablation's absolute values, because the within-run deltas those runs measure are the ablation's actual claim and are unaffected.

Two further caveats attach to the M2 rows specifically. Both ablation scripts trained M2 at 3 × 10⁻⁴ — the same stale constant described in Section S-I-G — so their absolute values are not comparable to M2's production numbers in Table 9 (which use the recorded 1 × 10⁻³). Because baseline and normalized conditions within a single run share that learning rate, the *within-run* comparison each row reports is unaffected, which is the claim the ablation makes; the scripts now read the recorded rate, so a re-run would refresh the absolute values.

Under two-way normalization, M3 was the sole model the correction appeared to *harm*, and a decomposition run isolated the responsible axis: brightness normalization alone took M3 from 0.800 to 0.560 externally, while resolution normalization alone was neutral-to-positive (0.800 → 0.847), and the combination (0.400) was worse than either alone — a negative interaction rather than two additive effects. On the strength of that, an earlier version of this analysis concluded that the correction was "architecture-dependent, helps two of four, harms one".

Adding the compression axis reversed the sign for M3 (+0.060, improving on both axes simultaneously), and the production pipeline — after the seeding fix — puts M3 at 0.773 externally against a 0.693 pre-normalization baseline (Table 9). The most likely reading is that the harmful interaction was specific to the two-way mixture rather than intrinsic to normalizing this model's inputs. But we note that M3's answer to "does normalization help?" came out positive, negative and flat across three runs before the seeding bug was diagnosed, and that only the three-way production path has been verified deterministic. **M3 is the one model for which we would want an independent replication before treating the sign as settled**, and Section S-I-U now supplies one: across five seeds the normalized and un-normalized conditions differ by 0.9 points against standard deviations of about 5, so there is no sign to settle.

### P. The baseline that has nothing else: M1

M1 is unaffected by normalization externally (0.000 either way) and its in-distribution accuracy *collapses* under it, from 0.838 to 0.541 — barely above the 0.527 majority-class rate of its test partition. This is the cleanest single result in the study.

A 96-dimensional color histogram has almost nothing to work with once mean brightness is standardized away, because — per the exact Shapley decomposition of Section VI-A — mean brightness, expressed through the near-white bin, *was* essentially its entire decision function. Fig. S12 shows both halves of that decomposition: 93 of the 96 coefficients lie within ±0.35 of zero, and the three near-white bins carry mean |φ| of 0.079–0.082 on the Split B test partition against ≤ 0.002 for the remaining 93.

> **FIGURE S12.** `paper/figures/fig12_model1_attribution.pdf` — (a) M1's logistic-regression coefficients across the 32 intensity bins of each RGB channel; the near-white bin dominates all three channels. (b) The eight features with the largest mean |Shapley value| on the Split B test partition. Attribution is exact for this model, not sampled. Removing the confound does not unlock latent signal in this model, because there was no latent signal to unlock. We therefore report M1 as a clean negative result: **on this benchmark, a classical color-statistics baseline is structurally incapable of the intended task, and its 83.8% accuracy is a measurement of the confound rather than of packaging authenticity.** We considered enlarging its feature set (texture descriptors, color moments, edge statistics) and decided against it: the model shows zero external signal across every condition tested in this study, in both external evaluations, and a larger hand-crafted feature set is unlikely to overturn a pattern that consistent. The negative result is the useful finding.

This has an uncomfortable implication, and it is worth being precise about its reach. On *this* dataset it is direct, and the metadata-only oracle of Table 5 makes it exact rather than suggestive: three acquisition scalars with no pixel input reach 100% on the leakage-free partition, and a color histogram reaches 83.8%. There is no residual on this pool that a convolutional network is needed to explain. M1's 83.8% is the more conservative statement of the same point and the one we would defend if the oracle were disputed, but the oracle is the tighter bound. Beyond this dataset the implication is conditional rather than established: it applies to any collection in which the two classes were produced by different pipelines, which Section II-F finds is the majority of the located prior work — [26] edits authentic images to create its counterfeit class, [27] generates it — but we have not audited those collections and do not claim their reported figures are confounded. We claim they are unaudited, and that the audit is cheap.

### Q. The architectural ablation implicit in M2

M2 carries an architectural observation that is worth separating from the confound results. It scores 0.865 on the leakage-free split — statistically indistinguishable from every other model in the roster (Table S3) — and it is the *best* model externally after correction (0.860, Table 9), with the only negative generalization gap anywhere in this study. It reaches that with 23,938 parameters and no pretraining.

The comparison this licenses is a narrow one, and we state it narrowly. A `flatten → dense(128)` head on this trunk would add roughly 6.4 M parameters, some 267 times the rest of the network, trained on 357 images. Nothing in these results suggests that capacity would buy anything: the accuracy ceiling on this pool is set by the confound (Section VI-A), not by model capacity. Parameter count is the wrong axis on data like this.

What we no longer claim is that M2 generalizes best. On Split C alone it does, by a clear margin. On the second external distribution of Section VI-F it collapses to 0.463 while both frozen backbones hold, which makes its Split C advantage a property of that particular capture condition rather than of the model. The defensible version of the architectural observation is therefore weaker and more interesting: a 23,938-parameter network from scratch can match far larger pretrained models in-distribution and on one external set, and still fail to carry that to a second — so neither in-distribution accuracy nor a single external evaluation predicts which model to deploy.

### R. Are the three constants load-bearing?

Eqs. (5)–(7) of the main paper fix three constants: a 128 px short side, a target mean of 0.5 and JPEG quality 40. Only the first has a justification derived from the training distribution alone. A reviewer may reasonably suspect that a recovery from 3.3% to 80.7% rests on three fortunate choices, so we varied each one around its production value, on M4, inside a single script execution (Table S14).

**TABLE S14.**Sensitivity of the three-way normalization to its constants. M4 (EfficientNet-B0), all nine conditions from one script execution, so all rows are directly comparable. The production triple is (128, 0.5, 40).

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

**The production constants are conservative, not tuned.** A 96 px short side beats the 128 px we report (0.873 vs. 0.820), and JPEG quality 25 is level with quality 40. The headline figure therefore understates what the method achieves; we have not re-run the paper around the better value, because choosing constants by their external score is precisely the target-distribution leakage that Section S-II warns about. The 128 px threshold retains a defense the 96 px one does not: it was set from the training pool's own 10th percentile without consulting Split C.

**The two axes that behave monotonically are the two that impose an information bottleneck.** Capping resolution and forcing a lossy re-encode both destroy information, and doing more of either helps externally until in-distribution detail starts to matter. Rescaling brightness only shifts a location parameter, destroys nothing, and correspondingly has a flat optimum. That distinction predicts which future candidate axes are worth sweeping and which need only be applied: bottlenecks have a tunable strength, alignments do not.

One reading of the diffuse attention reported in Section S-I-J is that the bottleneck simply destroys the fine spatial structure a genuine packaging classifier would need, leaving a model that cannot localize anything. This sweep is the direct test of that reading, and it does not support it. If the 128 px cap were already past the point where authentication-relevant detail survives, tightening it to 96 px should cost external accuracy; instead 96 px is the best external condition in this sweep (0.873), for 1.4 points of in-distribution accuracy. Detail is being removed, and removing more of it continues to help up to the limit tested. What the sweep cannot settle is the complementary possibility — that the intended task needs detail this pipeline never had access to, in which case both the confound and the signal are being suppressed together and only the confound is being missed. Distinguishing those requires a source whose two classes share an acquisition pipeline, which Section IX lists as the outstanding acquisition.

### S. Deriving the axes without the external set

Sections VII-A and VII-B establish that the correction works, is robust to its constants and is sensitive to its composition order, but not that it could have been *found* without the external set. The axes were originally identified by comparing the Kaggle pool against Split C (Table 4), which is target-distribution information no practitioner deploying a model would possess. This section removes that dependency, because it is the most serious objection to the correction and, until now, an untested one.

The procedure is the audit of Section VI-A turned into an axis-selection rule and confined to the training data. Using the **Split B training partition alone** — 357 images, 336 product groups, with grouped 5-fold cross-validation *inside* that partition so that neither the validation partition nor the test partition nor Split C is consulted at any point — we fit a one-feature classifier to each acquisition statistic a practitioner could compute from their own files, and normalize every axis whose balanced accuracy clears a threshold declared in advance (0.65). Table S15 gives the result.

**TABLE S15.**Train-only axis derivation. Grouped 5-fold cross-validated balanced accuracy of a one-feature classifier fitted inside the Split B training partition only. No validation, test or external data is used. Chance is 0.500; the pre-declared normalization threshold is 0.650.

| Acquisition statistic | Balanced accuracy (sd) | Fires? | Normalization it implies |
|---|---|---|---|
| File format (PNG vs. JPEG) | 1.000 (0.000) | yes | re-encode all inputs → compression axis |
| Encoded file size | 0.985 (0.019) | yes | fixed-quality re-encode → **compression axis** |
| Short-side resolution | 0.958 (0.018) | yes | short-side cap → **resolution axis** |
| Aspect ratio | 0.809 (0.019) | yes | already removed by the square 224 × 224 input resize |
| Mean brightness | 0.777 (0.067) | yes | rescale to fixed target → **brightness axis** |
| Color balance (R:B) | 0.684 (0.051) | yes (marginal) | gray-world white balance |
| Color balance (R:G) | 0.610 (0.044) | no | — |

**The train-only procedure nominates the axes we used.** Resolution, brightness and compression are all selected, and they are selected in an order that matches their measured contribution in Section S-I-N rather than their *t*-statistics. Nothing in this table required knowing that Split C exists, let alone what it looks like. The correction of Eq. (8) of the main paper is therefore derivable from the training set alone, and the concession this paper previously made — that the train-only variant was untested — no longer holds.

**Its two extra nominations are both informative rather than embarrassing.** Aspect ratio fires at 0.809, and is already neutralized by the square input resize that this and essentially every comparable pipeline applies before the first convolution; the audit flags a real confound that standard practice happens to remove for unrelated reasons, which is worth knowing but implies no new operator. Color balance fires marginally on one of its two ratios (0.684 against a 0.650 threshold) — and white balance is precisely the axis Section S-I-N tested and **ruled out**, finding it useless alone (0.107 external) and mildly harmful in combination. The one false positive the train-only rule produces is thus a candidate we independently showed does no good, at the cost of one ablation run.

Two honest qualifications remain. The threshold of 0.65 is a judgement, not a derived quantity; a stricter 0.75 would have excluded color balance and retained all three axes used, and a looser 0.55 would have admitted both color ratios. And this demonstrates *derivability on one dataset*, not that a train-only audit will nominate the right axes generally — in particular it cannot nominate an axis that is confounded in the deployment distribution but not in the training distribution, which is a real blind spot and not one any training-set procedure can address. What it does establish is that on this dataset the correction required no target knowledge, so the reported recovery is not an artifact of having seen the answer.

---

### T. A taxonomy of provenance defects, and what to check for each

The two datasets audited here failed in different ways, and a third near-failure was caught during construction of our own evaluation set. Taken together they suggest that "provenance confound" is not one defect but a small family, each member requiring a different check. We set out the four we encountered, with the cheapest test that detects each, in the order we would run them.

**Type A — acquisition-statistic confound.** The classes differ in format, resolution, compression, brightness or aspect ratio because they were captured or encoded by different processes. *Detection:* the provenance audit of Section VI-A — fit the intended classifier to metadata alone. *Instance:* the Kaggle dataset, audit accuracy 1.000, with even aspect ratio alone at 0.803. *Cost when undetected:* in-distribution 0.919, external 0.033. *Partial repair:* the label-free normalization of Section V-D, architecture-dependent.

**Type B — content or modality confound.** The classes differ in what kind of *document* they are, not in the labeled property: one class is product photography and the other is bulletin graphics, screenshots, catalog renders or marketing material — in the worst case with the ground-truth label rendered as text in the pixels. *Detection:* human inspection of a sample of each class, and of the extremes of any metadata distribution. Metadata may be silent, and normalizing a dataset for release makes it more so. *Instance:* the Roboflow dataset, 57/57 against 263/263, audit accuracy only 0.717. Also, in smaller degree, the 47 watermarked stock-catalog images in the Kaggle pool, 47/47 authentic-labeled. *Cost when undetected:* unbounded — a model can reach 100% by reading the printed label. *Repair:* exclusion; no preprocessing helps.

**Type C — confound reintroduced by source selection.** The dataset is clean, but a *derived* set — an external test set, a synthetic negative class, an augmented subset — is drawn from a differently-acquired part of the source. *Detection:* recompute the Type A statistics on every partition after construction, not only on the training pool. *Instance:* our own first synthetic proxy drew its base images from a different device subset of the external source, differing more than twofold in brightness (Section S-I-B), which would have reproduced the confound under study via selection rather than generation. It was caught by re-running our own audit and fixed before use. *Cost when undetected:* a fabricated positive result, published as a validation of the very method under test.

**Type D — degenerate shipped evaluation protocol.** The dataset's own partition files do not partition. *Detection:* intersect the filename sets. *Instance:* the Kaggle archive, whose `train` folder contains all 661 images while `val` and `test` are proper subsets of it (Section III-A). *Cost when undetected:* test accuracy is training accuracy. *Repair:* build your own split; treat a shipped split as a claim to be verified, not a service.

**Type E — a real content difference that the audit reads as a confound.** This is the audit's false-positive mode rather than a defect of the dataset, and we add it because the cross-domain survey produced one. The classes differ in a low-level statistic for reasons intrinsic to the objects, not to how they were acquired. *Detection:* compare the audit's axes against each other. Storage format is never a property of the photographed object, so a high score on format is specific to acquisition; encoded size, resolution and aspect ratio all mix acquisition with content and are correspondingly ambiguous. *Instance:* the BHSig260 signature corpus (Section VI-C), where both classes are written on the same paper and scanned by one procedure — format returns exactly 0.500, as it should, while encoded size returns 0.843, almost certainly because forged signatures differ from genuine ones in stroke complexity and therefore in ink coverage, which drives the compressed size of a bitonal scan. *Consequence:* the audit's output is not a verdict. It says a trivial statistic separates the classes; establishing that the statistic is an *acquisition* artifact is a second step, and the format axis is the one that most nearly settles it on its own.

Two cross-cutting lessons follow, and they are the ones we would most want carried into other application areas.

**Publisher-side tidying suppresses the symptom, not the disease.** The Roboflow archive had been resized to a uniform 640 × 640 and re-encoded to a single format before release. Those are ordinary, well-intentioned preparation steps, and their effect is to erase exactly the traces the cheap audit reads while leaving a total Type B confound untouched. A curated dataset is therefore *harder* to audit than a raw one, and a clean audit result on a normalized dataset carries almost no information. Where an archive has been normalized, the audit should be treated as inapplicable rather than as passed.

**Rank confounds by discriminability, not by effect size.** Brightness gave the largest *t*-statistic in the case-study dataset (*t* = 17.0) and was the *weakest* single predictor of the label (0.716 balanced accuracy, against 1.000 for format and 0.994 for file size). A large difference in means with overlapping distributions is less dangerous than a small difference with none. Since fitting a one-feature classifier costs no more than a *t*-test, there is no reason to use the *t*-test for this purpose.

### U. Seed-to-seed variance

Every number reported elsewhere in this study comes from one training run at seed 42, and earlier versions of this document listed seed-to-seed variance as unmeasured. It is now measured, for the conditions the paper's argument rests on. `modeling/seed_sweep.py` re-runs M2, M3 and M4 at five seeds (42–46), under the production pipeline and under the un-normalized baseline, and evaluates each on the Split B test partition and on both external sets. Each seed runs in its own process with the seed fixed before any module derives from it, so no run inherits another's RNG state — the defect of Section S-I-G in a new form. M1 is excluded: it is a convex fit with a deterministic solver, no random initialization and no augmentation, so its accuracy is identical under every seed.

The harness reproduces the values of record. At seed 42 the normalized condition returns M2 0.865 / 0.860 / 0.463, M3 0.932 / 0.773 / 0.725 and M4 0.919 / 0.807 / 0.832 on Split B, C and D — the published numbers exactly, from the pipeline as it now stands. Mean ± sample standard deviation across the five seeds:

| Model | Condition | Split B test | Split C | Split D |
|---|---|---|---|---|
| M2 CNN | baseline | 0.854 ± 0.018 | 0.051 ± 0.103 | 0.176 ± 0.201 |
| M2 CNN | normalized | 0.824 ± 0.042 | **0.909 ± 0.038** | 0.627 ± 0.135 |
| M3 MobileNetV3 | baseline | 0.941 ± 0.007 | 0.715 ± 0.057 | 0.644 ± 0.043 |
| M3 MobileNetV3 | normalized | 0.938 ± 0.007 | 0.724 ± 0.047 | 0.685 ± 0.044 |
| M4 EfficientNet-B0 | baseline | 0.905 ± 0.000 | 0.100 ± 0.026 | 0.240 ± 0.048 |
| M4 EfficientNet-B0 | normalized | 0.935 ± 0.011 | **0.860 ± 0.034** | 0.878 ± 0.031 |

Four readings, and the third and fourth are the ones that change how a claim should be stated.

**The correction's effect on M2 and M4 is an order of magnitude larger than seed variance.** M2's external accuracy moves from 0.051 ± 0.103 to 0.909 ± 0.038 and M4's from 0.100 ± 0.026 to 0.860 ± 0.034. Those are 86- and 76-point shifts against standard deviations of three to ten points, and the two distributions do not come close to touching: the worst normalized seed beats the best baseline seed by a wide margin in both models. The paper's central quantitative claim does not depend on a fortunate initialization.

**M3's does not separate from seed variance at all, which settles a question this study left open.** Its baseline is 0.715 ± 0.057 and its normalized condition 0.724 ± 0.047 — a difference of 0.9 points against standard deviations five times that. The five normalized values are 0.773, 0.733, 0.647, 0.733, 0.733 and the five baseline values 0.667, 0.773, 0.673, 0.780, 0.680; the two sets interleave. Section VI-E declines to claim a normalization benefit for M3 on the strength of overlapping Wilson intervals and a history of sign changes. That decision is now supported by a direct measurement rather than by caution, and the honest statement is stronger than the one it replaces: for M3 the correction has no effect this design can detect, and the sign changes recorded in Section S-I-O are what a 5-point standard deviation produces when it is read as signal.

**M2's collapse on the second capture shift is real in direction and overstated in magnitude by the reported run.** Across seeds M2 falls from 0.909 on Split C to 0.627 ± 0.135 on Split D, a mean drop of 28 points, while M3 moves −3.9 and M4 +1.8. The qualitative finding of Section VI-F therefore holds across seeds: the from-scratch CNN does not carry its corrected external accuracy to a second capture condition and the two frozen backbones do. But the specific 39.7-point drop the paper reports is the largest of the five, because seed 42 returns M2's lowest Split D value of the five (0.463, against 0.738, 0.792, 0.584 and 0.557), and M2's Split D standard deviation of 0.135 is by far the largest in the table. The drop should be read as tens of points with wide run-to-run spread, not as 39.7.

**Seed 42 is not a central draw, and in different directions for different models.** Its Split C values are the *minimum* of five for M2 (0.860 against a mean of 0.909) and for M4 (0.807 against 0.860), and the *maximum* of five for M3 (0.773 against 0.724). The reported figures therefore understate the correction for the two models it demonstrably helps and flatter it for the model where it cannot be shown to help at all. We have not restated the paper around the means: seed 42 was fixed before any of this existed, every artifact and checkpoint of record was produced under it, and re-centering the manuscript on a five-seed mean would trade a reproducible number for a slightly better one. The variance is reported here so that the single-run figures can be read with it.

Two limits on this table. It covers the production and baseline conditions only, not the per-axis, constant or ordering ablations, which remain single executions — six orderings at five seeds is thirty further training runs, and the claim they support is a 28-point separation between two groups, an order of magnitude beyond anything in this table. And five seeds give a standard deviation with roughly 50% relative uncertainty of its own, so these figures bound the variance rather than estimate it precisely. Neither limit affects the readings above, all of which turn on separations far larger than the quantities being estimated.

The baseline rows are re-derivations, not the archived pre-normalization run that Table 9's baseline column reports. That column is an artifact of a run whose weights were never saved (Section S-I-G), and it records 0/150 for M2 and 5/150 for M4, against 0.051 ± 0.103 and 0.100 ± 0.026 here. The archived M4 figure sits below every seed measured, which is consistent with what Section S-I-J already reports for the same condition — the border-mass audit, retraining the same baseline, returned 9/150 rather than the archived 5/150. Nothing in this paper's argument depends on the exact baseline value, which is why the discrepancy is recorded rather than reconciled: what the argument needs is that the baseline is near zero and the corrected pipeline is not, and every measurement of both agrees on that.


### V. A paired measurement of near-duplicate leakage

Section S-I-H bounds the recognition channel by counting and notes what the count leaves open. This section is the experiment that closes it, its design and its full output. `modeling/leakage_paired.py` builds the partition, runs it and writes the table.

**What has to be held fixed.** The quantity of interest is the effect of admitting a near-duplicate of a test image into training, and it is not what the Split A − Split B delta measures: those two splits assign 230 of 510 images differently, so their difference mixes leakage with a change of test images. Holding the test set fixed and varying nothing but the mates isolates it. Two further controls matter. The arms must be the same size, or the comparison confounds leakage with training-set size; and they must carry the same class balance, or it confounds leakage with the class prior. Both are enforced by construction and asserted at run time (Table S16), together with the property that gives the design its name: the clean arm shares no product group with the test set, and the leaky arm's overlap with it is exactly the mates.

**TABLE S16.**The paired leakage design. Built under a fixed design seed (20260829) independent of the training seed, so every training seed sees the identical partition and the pairing is exact. The pool has 480 product-identity groups over 510 images — 26 of size 2 and 2 of size 3 — so the 28 exposed test images are not a sample of the exposed images but all of them.

| Partition | n | Counterfeit | Held by |
|---|---|---|---|
| Test — exposed | 28 | 8 | neither arm |
| Test — unexposed | 46 | 27 | neither arm |
| Mates | 30 | 8 | leaky arm only |
| Substitutes | 30 | 8 | clean arm only |
| Base train | 320 | 159 | both arms |
| Validation | 56 | 28 | both arms |
| **Clean train total** | **350** | **167** | — |
| **Leaky train total** | **350** | **167** | — |

M1 is excluded, for a different reason than in Section S-I-U: 97 parameters over a 96-bin color histogram cannot memorize an individual photograph, so the channel under test does not exist for it.

**TABLE S17.**Leaky minus clean, five seeds (42–46), production pipeline. Accuracies are mean ± sample standard deviation across seeds; the difference and its 95% interval come from a bootstrap over test images, resampling images rather than predictions so that both arms' verdicts on an image move together. McNemar is computed on the pooled discordant pairs.

| Model | Subset | n | Clean | Leaky | Difference (percentage points) | McNemar *p* |
|---|---|---|---|---|---|---|
| M2 CNN | all | 74 | 0.865 ± 0.029 | 0.868 ± 0.018 | **+0.3 [−1.9, +2.4]** | 1.000 |
| M2 CNN | exposed | 28 | 0.936 ± 0.039 | 0.936 ± 0.016 | +0.0 [−2.9, +2.9] | 1.000 |
| M2 CNN | unexposed | 46 | 0.822 ± 0.032 | 0.826 ± 0.027 | +0.4 [−2.2, +3.5] | 1.000 |
| M3 MobileNetV3 | all | 74 | 1.000 ± 0.000 | 1.000 ± 0.000 | +0.0 [+0.0, +0.0] | 1.000 |
| M4 EfficientNet-B0 | all | 74 | 0.987 ± 0.000 | 0.987 ± 0.000 | +0.0 [+0.0, +0.0] | 1.000 |

**What this establishes, and what it does not.** For M2, Table S17 establishes an effect indistinguishable from zero with an interval of roughly ±2 points, on the whole test set and on both subsets separately — so neither the recognition channel nor the indirect one is doing appreciable work. The two subsets are the point of the design: a difference confined to the exposed images would be recognition, and a difference on the unexposed ones would be the indirect channel that no counting argument can bound. Neither appears.

For M3 and M4 the null is weaker than it looks, and we would rather say so than bank it. Both sit at or beside ceiling on this test set — 1.000 and 0.987, at every seed and in both arms — so the design has almost no room in which an effect could show. That ceiling is not a flaw in the experiment so much as a restatement of the paper's subject: on a pool where the label is perfectly predicted by acquisition, an in-distribution test partition is close to trivial, and there is little left for leakage to add. The interpretable measurement is M2's, which is also the only model here that learns its features rather than inheriting them.

Two further limits are worth stating. The exposed subset is 28 images, which is every one the pool offers and still small; the ±2.9-point interval on that subset is what the data support and no tighter statement should be read into the point estimate of 0.0. And this measures near-duplicate leakage as `pHash` clustering defines it (Section IV-B). Two dissimilar photographs of the same physical package would not be grouped, so both the exposure count and this experiment address near-duplicate leakage specifically, not every sense in which two images might share a product.

## S-II. Limitations

**The external evaluation is authentic-only, so counterfeit recall is unmeasured.** Every external image in this study is genuine packaging, so every external number is a specificity — equivalently, one minus the false-positive rate — and nothing else. We state the resulting non-claim as plainly as we can: **this paper does not report, estimate or bound the rate at which any of these models would detect a real counterfeit.** No independent counterfeit-labeled source could be found (Section III-E), and the synthetic proxy of Section S-I-B does not substitute for one.

The proxy's limitation is worth enumerating, because Table S6 could otherwise be mistaken for a recall measurement. It perturbs genuine photographs, so it can only measure sensitivity to *degradation of a genuine image*. Real falsified packaging differs along axes it does not model at all: absent or imitated security features, holograms and tamper seals; wrong substrate, board weight or surface finish; serial numbers, batch codes and barcodes that are legible but incorrect; and — most importantly — competently produced counterfeits whose printing is not degraded in any visible way, which are precisely the cases a screening tool exists to catch. A model could score well on the proxy and fail on all of these; it could also fail the proxy and catch real counterfeits, since the perturbations are not drawn from any counterfeit distribution. The proxy supports only a weak, one-directional inference: a model that cannot separate a photograph from a visibly perturbed copy of *that same photograph* is unlikely to separate genuine from falsified packaging, and three of four models here fail that test.

**The general claim rests on a narrow evidence base.** Section I-A argues that asymmetric class sourcing makes provenance confounding the default. The direct evidence here is two datasets in one application area, plus a structurally matching report from generated-image detection [30] that we did not produce. That is enough to motivate the mechanism, to justify the audit as a routine precaution, and to explain two independent observations of one signature; it is not enough to quantify how often the mechanism fires, and no number in this paper should be read as a prevalence estimate. Section VIII-G states what would falsify the claim.

**The correction's axes were originally chosen with knowledge of the external set, though they need not have been.** Eq. (8) of the main paper uses no label information, which is what licenses applying it to Split C; but the *choice* of resolution, brightness and compression was made after Table 4 showed those statistics separating the Kaggle pool from Split C, and that is target-distribution information a practitioner would not have. Section S-I-S addresses this directly: a train-only audit, confined to the Split B training partition with grouped cross-validation inside it, nominates all three axes without consulting any external data. The objection is therefore answered on this dataset. Two residual weaknesses remain. The selection threshold (0.65 balanced accuracy) is a judgement rather than a derived quantity. More fundamentally, no training-set procedure can nominate an axis that is confounded in the deployment distribution but not in the training distribution, so a train-only audit is a safeguard against the confound you have, not a guarantee against the one you have not seen.

**The correction is a preprocessing bottleneck, not a domain-adaptation method, and is not compared against one.** The natural alternative to suppressing a confounded statistic is to align the distributions in feature space — second-order alignment such as CORAL, importance reweighting, or an adversarial domain-confusion objective — and we report no such comparison. The omission is a design constraint rather than an oversight, and the constraint is worth stating because it also limits what the comparison would mean. Every method in that family requires samples from the deployment distribution at training time, and consumes them to fit an alignment; Eq. (8) of the main paper is a fixed function of a single image that uses neither labels nor target data, which is what licenses applying it unchanged to Split C, to Split D, and to an image captured after deployment. A study that fitted CORAL on Split C could not then report Split C as an external evaluation. The honest statement of the trade is therefore that we chose the weaker intervention because it is the one that survives its own evaluation protocol, and that a practitioner who does hold target-domain data should expect to do better than Eq. (8) of the main paper — how much better is unmeasured here.

We accordingly ask that Eq. (8) of the main paper be read as a **zero-target-sample baseline**: the performance recoverable when nothing whatsoever is known about the deployment distribution, not the best available correction. Anyone holding even unlabeled target-domain images is in a strictly stronger position and should evaluate second-order feature alignment (Deep CORAL), distribution matching (MMD-based adaptation) or an adversarial domain-confusion head against this baseline before adopting it. We would expect those methods to win, and the quantity of interest — how much accuracy a rigid per-image bottleneck leaves on the table relative to representation-level alignment — is exactly what such a comparison would measure, and is not measured here.

**Cross-validating across sources or capture hardware is not possible on this data.** The strongest answer to a provenance confound would be a grouped cross-validation whose folds are acquisition pipelines rather than products, so that every fold is evaluated on a capture process it never saw. That design cannot be built here, and the reason is the confound itself: the counterfeit class exists in exactly one usable source. The only other public authentic/counterfeit pharmaceutical dataset we could obtain has a counterfeit class that is 57/57 advisory graphics carrying the ground-truth word in the pixels (Section VI-B), which is unusable at any position in a fold, and both external sets are authentic-only. A source-held-out fold would therefore contain no negatives. The grouped cross-validation we do run decorrelates product identity and nothing else, and we do not claim otherwise; Section VIII-A states the consequence, which is that in-distribution machinery of any kind cannot see this defect.

**Split D does not vary the backdrop.** Section S-I-J identifies a surround-based cue as the basis of M3's correct external predictions, and of both backbones' errors, and Split C and Split D share the same staging. The second external set therefore cannot test that cue, and the stability of M3 and M4 across the two sets should not be read as evidence against it. An external set that varies the photographic setting — different surfaces, in-hand or in-shelf photography, uncontrolled backgrounds — is the evaluation this study most obviously lacks, and is a different requirement from the counterfeit-labeled set discussed above.

**Two capture conditions, one archive, one product set.** This limitation was stated in an earlier version as a caution and has since been partly measured. Section VI-F adds a second external distribution, and it changed a headline claim: M2's post-correction accuracy proved specific to Split C (0.860 → 0.463) while both frozen backbones held. What remains unmeasured is still substantial. Both external sets come from the same archive, the same 150 products and the same laboratory protocol, differing only in device and lighting — so the evidence supports "the correction transfers across a change of camera for pretrained backbones" and not "the correction transfers." Nothing here tests generalization across products, across sources, across countries, or to photographs taken by end users in the conditions a screening tool would actually face. No number in this paper should be read as establishing a generalization *rate*.

**Small test partitions.** In-distribution test partitions contain 74–76 images. Bootstrap intervals are correspondingly wide (Table S3), all pairwise model comparisons are underpowered (Table S5, discordant counts 1–15), and the leakage delta of Section S-I-H is measured against variance that a larger pool would suppress. Point differences of a few percentage points between models on this data should not be interpreted.

**Some numbers predate checkpoint persistence and cannot be re-derived.** For most of this study no script saved a trained model, and every downstream consumer — external evaluation, Grad-CAM, the synthetic proxy — re-derived "the trained model" from scratch. That design produced both defects of Section S-I-G: the learning-rate divergence in M2's external evaluation, and a discrepancy in which two rebuild paths of the same nominal M4 model classified 16/150 versus 5/150 external images as authentic. Training now persists a checkpoint with the learning rate, seed, best epoch and epoch count it was trained under, `load_checkpoint` raises if the recorded learning rate differs from the caller's expectation, and the external evaluations of Table 9 load rather than retrain — which independently reproduced M2's and M3's recorded Split C accuracies exactly. Two residual weaknesses follow from the change arriving late. M4's earlier Split B accuracy of 0.946 could not be explained when the checkpointed pipeline deterministically produced 0.919, because the artifacts of the original run no longer exist; the newer value is the one reported, and the older one is unrecoverable rather than refuted. And the two `experiment_*_all_models.py` ablations still rebuild rather than load, so their absolute values are not directly comparable with the production tables — the within-run comparisons they actually make are unaffected, and Section VII says so where they are used.

**Single-run ablations.** Every ablation in Section VII is one execution per condition, not a distribution over seeds, so none of them carries an interval. The reason this is tolerable is that the pipeline is now deterministic: the per-pass seeding defect of Section S-I-G, under which nominally identical conditions moved by up to 17 points, was fixed partway through, and each ablation re-runs its own baseline inside the same execution so that every comparison it makes is within-run. Three checks support the harness rather than merely asserting it: the production condition returns 0.919 in-distribution and 0.820 externally in each of the three post-fix scripts that contain it (Tables S12, S14 and 10), and the external evaluation from persisted checkpoints reproduced M2's and M3's recorded Split C counts exactly, byte for byte, on a re-run. Seed-to-seed variance is no longer unmeasured for the production and baseline conditions — Section S-I-U repeats those at five seeds and finds standard deviations of 0.03 to 0.14 on the external sets — but it remains unmeasured for the ablations themselves, which is why a condition differing from its baseline by a point or two is not read here as a difference. The ablations that predate the fix are identified in their captions — all of Table S11, all of Table S13, and the superseded white-balance rows retained in Table S18; Tables S12, S14 and 10 are post-fix — and the two conclusions Table S11 is used for are separately reproduced post-fix in Table S12.

**Frozen backbones only.** Neither transfer model was fine-tuned; each trained a single linear head on cached features, a scope decision forced by CPU-only hardware — an early attempt at live per-epoch backbone passes was terminated by the host before one split finished (Section S-I-E). Whether end-to-end fine-tuning would reduce or amplify the shortcut reliance documented here is genuinely open, and the possibilities are opposite: adaptable features could discard the confounded statistics, or specialize onto them more aggressively than a frozen representation can.

One data point here bears on the question without settling it. M2 *is* trained end to end from scratch with no frozen component, and it is simultaneously the model that relies on the shortcut most completely at baseline (0/150 external) and the one that generalizes best after correction (0.860, the only negative gap). End-to-end training therefore conferred no protection against the confound, but also did not prevent the model from learning something transferable once the confound was suppressed. That is consistent with fine-tuning being neutral-to-helpful rather than harmful, but M2 differs from M3 and M4 in scale, initialization and capacity, so it is weak evidence and we do not lean on it.

**The attention audit is complete but small, one annotator produced it, and a second method contradicts part of it.** All 62 heatmaps were regenerated from the persisted production checkpoint after the training-mode defect of Section S-I-G and categorized in full, so the audit is no longer a non-random sample of a mis-configured model. It remains 62 images scored by a single human against a four-way scheme, with no second annotator and therefore no inter-rater agreement to report. An earlier version of this paragraph argued that the external result was stark enough — 40 of 40 maps splitting cleanly by outcome — that a second opinion would not overturn it. A second opinion partly has: the occlusion analysis of Section S-I-J, which needs no annotator and covers every external image rather than ten per group, corroborates the categorization on both models' errors and on M3's correct answers and does not corroborate it on M4's, and Section VI-G now claims only what both methods support. The categories are also coarse: "attends to the background" does not identify *which* property of the background a model is using, and both quantitative measures reported here are purely radial — they distinguish center from surround, not product from not-product. The content-aware measure that would is implemented and committed (`scripts/23_build_product_box_tool.py`, `modeling/attention_in_box.py`) and awaits an annotation pass.

**Product identity is a proxy.** Split B groups on perceptual-hash clusters, not ground-truth product labels, which do not exist in this source. The clustering is not robust to mirroring, and while no cluster mixes class labels, the grouping could be coarser or finer than true product identity in ways that would slightly change the measured leakage rate.

**Scope of the modality claim.** The pool is 43.7% blister packs and 25.9% mixed presentations (Table S1). Results characterize "packaging and immediate product containers", and should not be read as results on outer cartons.

**Single-machine cost measurements.** Table S8 is one CPU on one machine at batch size 1. Absolute latencies will differ elsewhere; the relative ordering and the conclusion that normalization is negligible relative to a forward pass should be stable.

---

## S-III. Appendix A — Complete Per-Axis Ablation Record

Table S18 reproduces every normalization condition executed in this study, annotated with the script execution that produced it, so that valid within-run comparisons are identifiable. Absolute values are not comparable across groups; see Section VII's caveat.

**TABLE S18.**All normalization conditions. Res = resolution bottleneck (Eq. 5); Bright = brightness rescale (Eq. 6); Comp = JPEG bottleneck (Eq. 7); WB = gray-world white balance.

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

Only the last two groups — the ordering sweep and the white-balance rerun — were produced after the seeding fix of Section S-I-G, by scripts that seed each augmentation pass and read the recorded learning rate. Every other group in this table was executed on 2026-07-25, the day before the fix, and its absolute values carry the caveat of Section VII; the within-run comparisons each group was built to make are unaffected. The superseded white-balance group is retained only so that the rerun beneath it can be read against what it replaces. The production condition appears in both post-fix groups and returns 0.919 / 0.820 in each, matching its value in Table S14 — three exact reproductions across two scripts.

## S-IV. Appendix B — Exclusion Rules Applied to the Modeling Pool

Table S19 records every exclusion rule applied to the modeling pool, with the number of files each removed.

**TABLE S19.**Every exclusion rule, with counts. Roboflow exclusions are listed for completeness; that source contributes to no split used in this paper's results.

| Source | Rule | Files excluded |
|---|---|---|
| Roboflow | simultaneous `authentic=1` and `counterfeit=1` annotation | 52 |
| Roboflow | advisory-bulletin graphic (label rendered as pixel text) | 180 |
| Kaggle | watermark / stock-photo overlay (47/47 authentic-labeled) | 47 |
| Kaggle | not a device photograph of a product (1 browser screenshot, 3 marketing renders) | 4 |
| Kaggle | no packaging in frame (1 loose tablets, 4 syrup bottles) | 5 |
| Kaggle | exact duplicate on the rotation-canonical hash (one copy retained) | — (applied after the above; 605 filtered files → 510 pool images) |

## S-V. Appendix C — Reproduction
```bash
# 1. Data pipeline (deterministic; ~35 s)
python scripts/run_all.py                          # inventory → filter → dedup → provenance → splits
python scripts/06_download_mendeley_split_c.py     # external set, one-time (~248 MB)
python scripts/07_verify_split_c_independence.py   # pHash independence check
python scripts/17_apply_synthetic_review.py        # assemble the synthetic proxy set
python scripts/18_capture_method_stats.py          # per-image capture statistics (Table 6, Fig. S5)

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
python modeling/gradcam_quantitative.py            # border mass, all 150 external
python modeling/occlusion_sensitivity.py           # second attribution method
python modeling/eval_external_from_checkpoints.py  # Split C and D from checkpoints

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

# 5. Seed variance (Section S-I-U) and paired leakage (Section S-I-V); ~25 min per seed
python modeling/seed_sweep.py                      # 5 seeds, resumable
python modeling/seed_sweep.py --summary            # mean +/- sd tables
python modeling/leakage_paired.py                  # paired leakage, 5 seeds, resumable
python modeling/leakage_paired.py --design         # print the partition and its assertions

# 6. Manuscript tables and figures
python paper/scripts/compute_paper_metrics.py
python paper/scripts/metadata_oracle.py
python paper/scripts/provenance_audit_multi.py
python paper/scripts/cross_domain_audit.py         # Table 7; fetches Kaggle listings
python paper/scripts/power_and_leakage_bound.py
python paper/scripts/train_only_axis_derivation.py
python paper/scripts/external_intervals.py
python paper/scripts/calibration_analysis.py       # Table S10
python paper/scripts/model1_attribution.py
python paper/scripts/benchmark_cost.py
python paper/scripts/make_figures.py

# 7. Manuscript and supplement
python paper/scripts/build_tex.py
python paper/scripts/build_supplement.py
python paper/scripts/build_docx.py
python paper/scripts/verify_crossrefs.py           # gates the build
python paper/scripts/compile_pdf.py
python paper/scripts/final_sweep.py```
