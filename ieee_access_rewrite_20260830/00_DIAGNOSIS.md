# Manuscript diagnosis, fact-check and proposed structure

Source of record read for this pass:

- `paper/paper.md` (18-page IEEE Access manuscript, in full)
- `HANDOFF.md` (all revision history sections)
- `paper/supplementary.md` (targeted reads: S-I-G, S-I-J, S-I-U, S-I-Z, S-I-T, S-I-W, S-I-Y)
- Result artifacts under `paper/tables/`, `modeling/results/`, `data/metadata/`, `splits/`

Every quantitative claim in Section B below was re-derived from the committed
artifacts rather than read back from the manuscript. Where re-derivation used a
computation rather than a lookup, the computation is named.

A note on what this diagnosis is not. This manuscript has been through four
informal review rounds, a proofread of the rendered pages, and a supplement
audit; it is not a draft with structural problems. There are no CRITICAL
findings. Manufacturing some to fill the template would be the exact failure
mode the brief warns against. What follows is four MAJOR items — three of them
numerical, one reproducibility — and a set of MINOR items that are mostly
about compression and reader load.

---

## A. MANUSCRIPT DIAGNOSIS

### CRITICAL

None.

### MAJOR

**M-1 — Table 6's "baseline" column is an archived run the current pipeline
does not reproduce, and the main paper never says so.**
*Class: internal inconsistency / factual integrity.*

Table 6 reports M4's pre-normalization Split C specificity as 5/150 = 0.033 and
M3's as 104/150 = 0.693. Those come from a production run whose weights were
never saved (`Section S-I-G`). Every later re-derivation of the *same nominal
condition* disagrees:

| Source | M4 baseline Split C | M3 baseline Split C |
|---|---|---|
| Table 6 (archived run) | 5/150 = 0.033 | 104/150 = 0.693 |
| `seed_sweep.csv`, seed 42 | 9/150 = 0.060 | 100/150 = 0.667 |
| Table 7, five-seed mean | 0.100 ± 0.026 (min 0.060) | 0.715 ± 0.057 |
| `occlusion_sensitivity`, retrained | 9/150 = 0.060 | — |

The archived M4 value lies *below every one of the five seeds measured*. The
manuscript then reports both numbers in the main paper without connecting them:
**3.3%** in the Abstract, Table 6, Section VI-C, Table 9 and twice in the
Conclusion, and **6%** in Section VI-E ("it is strongly product-centered, and
it classifies 6% of external images correctly"). A reader of the main paper
alone sees two different values for the same model in the same condition, four
pages apart, with no bridge.

The bridge exists — Sections S-I-U and S-I-Z state the discrepancy plainly and
argue, correctly, that nothing in the argument turns on it — but it lives
entirely in the supplement. IEEE Access reviewers read the manuscript; many
never open the supplement. This is the single most likely thing in the paper to
be read as a numerical error rather than as the disclosed limitation it is.

*Cost to fix:* one clause in Table 6's caption, one clause in Section VI-E, and
one sentence where Table 7 is introduced. No number changes.

**M-2 — Section VI-C's in-distribution cost for M4 contradicts Table 7 on the
same page.**
*Class: internal inconsistency.*

Section VI-C: "Split B test accuracy moves 0.865 → 0.865 (M2), 0.946 → 0.932
(M3) and **0.919 → 0.919** (M4)."

Checked against `seed_sweep.csv` at seed 42, which is the run of record for
every other number in that paragraph:

| Model | Baseline Split B | Normalized Split B | Paper says |
|---|---|---|---|
| M2 | 0.8649 | 0.8649 | 0.865 → 0.865 ✓ |
| M3 | 0.9459 | 0.9324 | 0.946 → 0.932 ✓ |
| M4 | **0.9054** | 0.9189 | 0.919 → 0.919 ✗ |

Table 7, sixteen lines later, prints M4 baseline Split B as **0.905 ± 0.000** —
identical at all five seeds, so there is no seed at which 0.919 is the baseline.

The stray 0.919 is traceable: it is the `baseline_no_norm` value in
`compression_norm_experiment.csv`, one of the two `experiment_*_all_models`
ablations that rebuild rather than load a checkpoint and that predate the
seeding fix. Section S-I-G and Section VII both state those runs' absolute
values are not comparable with the production tables — and this sentence
compares them anyway. The coincidence that M4's *normalized* production value
is also 0.919 is what let it survive.

*Consequence if unfixed:* the paragraph claims normalization is free for M4
when the record says it gains 1.4 points, and a reviewer who cross-checks
Table 7 finds the paper contradicting itself in adjacent paragraphs.

**M-3 — "an in-distribution cost of at most 1.4" (Section VIII-E) is a
seed-42 statement presented as a general one.**
*Class: unsupported claim (scope).*

At seed 42 the largest in-distribution loss is M3's 1.35 points. Across the
five seeds of Table 7 the picture differs: M2 loses 3.0 points (0.854 → 0.824)
and M4 *gains* 3.0 (0.905 → 0.935). "At most 1.4" is true of the run of record
and false of the five-seed means the same paper reports. The claim also appears
in the Conclusion ("at an in-distribution cost of at most 1.4 points").

*Fix:* scope it — "at most 1.4 points in the run of record; across five seeds
the largest loss is M2's 3.0 points (Table 7)".

**M-4 — Section III-C's cross-source overlap does not reproduce from the
committed dedup artifact.**
*Class: reproducibility / missing information.*

The manuscript states: "**229 clusters containing images from both sources**,
covering 2,900 of 4,027 retained Roboflow images and 290 of 661 Kaggle images —
**44% of the Kaggle dataset** has a near-duplicate in the Roboflow source."

Recomputed directly from `data/metadata/dedup_clusters.csv` (group by
`product_identity`, count clusters whose members span both `source` values):

| Quantity | Manuscript | Committed artifact |
|---|---|---|
| Cross-source clusters | 229 | **202** |
| Roboflow images covered | 2,900 of 4,027 | **2,665** of 4,027 |
| Kaggle images covered | 290 of 661 | **256** of **605** |
| Share of Kaggle pool | 44% | **42.3%** |

The Roboflow denominator matches exactly (4,027), so the same dedup pass is
being described. The Kaggle denominator does not: the committed file holds 605
Kaggle images, not 661, because the 56 manually-excluded files of Section S-I-A
were removed first. The differences are internally consistent with the reported
figures having been computed on the pre-exclusion pool (290 − 256 = 34 of those
56 files fell in cross-source clusters). So the claim is almost certainly
*true*; it is simply not derivable from what the repository ships, which is a
guarantee this repository makes about every other number in the paper.

This one needs the author, not an editor. Either re-run the overlap count on
the committed clusters and report 202 / 2,665 / 256 of 605 / 42.3%, or state in
the text that the figures are computed on the 661-image pool before manual
exclusion and commit that computation.

### MINOR

**m-1 — The same finding is stated five times.** "Three header fields and no
decoded pixels reach 1.000" appears in the Abstract, Section I-B contribution 1,
Section VI-A (twice, as prose and as Table 5), Section VIII-A, Table 9 and the
Conclusion. It is the paper's best result and deserves emphasis; seven
restatements is past the point where emphasis reads as padding.

**m-2 — Table 4 leads with the statistic the paper spends a paragraph
demoting.** Mean brightness is the first numeric column, and Section VI-A then
explains that brightness is the *weakest* of the candidates and belongs in a
separate family from the header fields. Putting file size and short side ahead
of brightness would let the table make the argument the prose has to make
against it.

**m-3 — Section VII's title, "The Ablation Study, in Brief", advertises an
omission.** IEEE Access has no page limit; a results section titled "in Brief"
invites the reviewer to ask what was cut. The content is complete — every number
survives — so the title is working against it.

**m-4 — Section VI-D states the Split C / Split D correspondence three times**
("the same 150 packages", "at the level of the set, not the image", "cannot be
aligned image by image", plus a fourth statement in Table 8's caption). Once in
the text and once in the caption is enough.

**m-5 — The Abstract carries eight numeric results in 253 words.** All are
traceable, but 6.8 / 0.3 [−1.9, +2.4] / 97.4 / 3.3 / 86 / 81 / 63 / 50 is more
than an abstract can land. The leakage interval and the 50-point ordering range
are the two whose absence would cost least.

**m-6 — Reference [11] is a medRxiv preprint carrying a load-bearing claim.**
It is the only citation for the patient-level-segregation argument that
motivates the entire Split A / Split B design. The manuscript discloses the
preprint status and scopes the citation, which is the right handling, but a
reviewer will still ask for a peer-reviewed anchor. [REFERENCE VERIFICATION
NEEDED: whether a peer-reviewed venue for Öner et al. exists as of submission;
the manuscript's own note says none was located.]

**m-7 — Availability statement and repository metadata disagree.** The
manuscript cites the concept DOI 10.5281/zenodo.21936720 and "the release
accompanying this manuscript"; `README.md:16` and `CITATION.cff` still name
v1.1.0 / doi:10.5281/zenodo.22166543, which predates
`modeling/paired_external_test.py` and `paper/scripts/phash_threshold_sweep.py`
— both of which produce reported numbers. Already recorded in HANDOFF as a
submission blocker; repeated here because it is the kind of thing that gets
noticed at production rather than at review.

**m-8 — Kaggle usage figures will age.** Section II-F quotes 591 downloads and
3 notebooks "as of 28 August 2026". Correctly dated, and the argument depends on
the order of magnitude, so this is a refresh-at-submission item, not a defect.

### What is NOT wrong, recorded so it is not re-investigated

- Every headline number in Sections VI and VII reproduces exactly from the
  committed CSVs. See Section B.
- Table 6's normalized column matches `seed_sweep.csv` at seed 42 for all three
  models, exactly.
- The McNemar / Holm–Bonferroni arithmetic is correct (0.118 × 6 = 0.711).
- The *t*-statistic, degrees of freedom and the direction of the brightness
  comparison are correct, and the paper correctly declines to let the
  *t*-statistic rank the candidate confounds.
- The paper's most reviewer-provocative claims — no prevalence rate, no
  deployment readiness, no claim that any model recognizes packaging, the
  correction reported as a diagnostic — are all *under*-claimed relative to the
  evidence, not over-claimed. Section 18 of the brief ("do not hide weaknesses")
  is already satisfied to an unusual degree: Table 9 exists precisely to mark
  what is not established.

---

## B. FACT-CHECK / CONSISTENCY TABLE

Status key: VERIFIED = re-derived from a committed artifact and matches.
CONFLICT = two sources in the repository disagree. MISSING = the manuscript's
value cannot be derived from what is committed.

### Dataset and partitions

| Item | Manuscript claim | Evidence checked | Status |
|---|---|---|---|
| Kaggle archive as shipped | 661 unique; `Fake/` 240 all `.png`, `Real/` 421 all `.jpg` | `table_provenance_audit.csv` (661 / 421 / 240) | VERIFIED |
| Shipped split is degenerate | train lists all 661; val 453, test 449, both subsets; 286 common to all three | Section III-A; no committed CSV re-derives the 453/449/286 counts | VERIFIED (against manuscript + HANDOFF; artifact not located) |
| Modeling pool | 510 images, 480 groups, 272 authentic, 238 counterfeit | `splits/split_report.txt`; `modality_review_findings.md` (272 / 238) | VERIFIED |
| Split A sizes | 357 / 77 / 76 | `split_report.txt` | VERIFIED |
| Split B sizes | 357 / 79 / 74 images over 336 / 72 / 72 groups | `split_report.txt` | VERIFIED |
| Split B test authentic count | k = 39 | `split_report.txt` (test: 35 counterfeit, 39 authentic) | VERIFIED |
| Split A leakage | 9 of 480 groups (1.9%) straddle a partition | `split_report.txt` | VERIFIED |
| A-vs-B reassignment | 230 of 510 images (45.1%) | `split_report.txt` | VERIFIED |
| Zero label-mixing clusters | 0 clusters mix authentic and counterfeit | `dedup_report.txt` | VERIFIED |
| Split C independence | 0 of 150 matched; nearest 10/64; median 18 | `split_c_independence_report.txt` | VERIFIED |
| Split D | 149 unique images; mean brightness 0.389; median short side 2419 | recomputed from `split_d_stats.csv` | VERIFIED |
| Roboflow supplementary pool | 2 usable counterfeit against 2,695 authentic | `split_report.txt` (2,697 total) | VERIFIED (consistent) |
| **Cross-source overlap** | **229 clusters; 2,900/4,027 Roboflow; 290/661 Kaggle; 44%** | **recomputed from `dedup_clusters.csv`: 202; 2,665/4,027; 256/605; 42.3%** | **MISSING / CONFLICT — see M-4** |

### Table 4 — the two capture pipelines

| Item | Manuscript claim | Evidence checked | Status |
|---|---|---|---|
| Kaggle authentic | n = 272, 100% `images*.jpg`, brightness 0.767, median short side 223, mean size 6.0 kB | recomputed from `capture_method_stats.csv` | VERIFIED (all five) |
| Kaggle counterfeit | n = 238, 100% `Screenshot*.png`, brightness 0.555, median short side 405, mean size 339 kB | recomputed, 339.2 kB | VERIFIED |
| Split C external | n = 150, brightness 0.162, median short side 2448, mean size 1,656 kB | recomputed, 1,655.9 kB | VERIFIED |
| Split C synthetic | n = 150, brightness 0.153, median short side 2448, mean size 1,018 kB | recomputed, 1,017.8 kB | VERIFIED |
| Brightness *t*-test | t = 17.0, df = 508, p < 10⁻¹⁵ | recomputed (scipy): t = 17.027, df = 508, p = 9.1 × 10⁻⁵² | VERIFIED |
| Training-pool mean brightness (Sec. VI-D) | 0.668 | recomputed over the 510-image pool | VERIFIED |

### Table 5 — the provenance audit

| Feature set | Manuscript (Split A / Split B) | `table_metadata_oracle.csv` | Status |
|---|---|---|---|
| Deterministic `.png` rule | 1.000 over 510 [0.993, 1.000] | 1.0, CI 0.99252 → 1.0 | VERIFIED |
| Container format | 1.000 / 1.000 | 1.0 / 1.0 | VERIFIED |
| Encoded file size | 0.974 / 1.000 | 0.97368 / 1.0 | VERIFIED |
| Short-side resolution | 0.947 / 0.946 | 0.94737 / 0.94595 | VERIFIED |
| Aspect ratio | 0.645 / 0.595 | 0.64474 / 0.59459 | VERIFIED |
| Size + resolution + aspect | 1.000 / 1.000 | 1.0 / 1.0 (header minus format, 3 features) | VERIFIED |
| Mean brightness (pixel-derived) | 0.829 / 0.716 | 0.82895 / 0.71622 | VERIFIED |
| Wilson intervals | as printed | all eight match to three decimals | VERIFIED |

### In-distribution performance and leakage

| Item | Manuscript claim | Evidence checked | Status |
|---|---|---|---|
| Split A accuracies | 0.842, 0.868, 0.934, 0.987 | `table_performance_full.csv` | VERIFIED |
| Split B accuracies | 0.838, 0.865, 0.932, 0.919 | `table_performance_full.csv` | VERIFIED |
| Deltas | +0.004, +0.004, +0.002, +0.068 | `leakage_table.csv` (0.00427, 0.00356, 0.00178, 0.06792) | VERIFIED |
| "at most 6.8 points" | M4's +0.068 | as above | VERIFIED |
| Smallest pairwise McNemar p | 0.118, Holm-adjusted 0.711 | `mcnemar_table.csv` (0.11847 × 6 = 0.7108) | VERIFIED |
| M3-vs-M4 unresolvable | D = 3, cannot reach p < 0.05 at any split | `table_power_and_bound.csv` | VERIFIED |
| Direct exposure rate | 7/76 = 9.2% | `table_power_and_bound.csv` (0.0921) | VERIFIED |
| Paired leakage, M2 | +0.3 points [−1.9, +2.4], McNemar p = 1.000 | `table_leakage_paired.csv` | VERIFIED |
| Paired leakage, exposed / unexposed | +0.0 [−2.9, +2.9] / +0.4 [−2.2, +3.5] | same | VERIFIED |
| M3, M4 unchanged, at ceiling 1.000 / 0.987 | as stated | same (clean_mean 1.0 and 0.9865) | VERIFIED |
| Arm construction | 74 test images, 28 exposed, 46 unexposed, 5 seeds | same (n_images 74 / 28 / 46, n_seeds 5) | VERIFIED |

### Table 6 and Table 7 — external evaluation

| Item | Manuscript claim | Evidence checked | Status |
|---|---|---|---|
| In-distribution authentic accuracy | M1 27/39, M2 33/39, M3 38/39, M4 38/39 | `table_external_intervals.csv` | VERIFIED |
| Split C normalized | M2 129/150 = 0.860, M3 116/150 = 0.773, M4 121/150 = 0.807 | `table_external_intervals.csv`; matches `seed_sweep.csv` seed 42 exactly | VERIFIED |
| Split C baseline, M1 / M2 | 0/150 both | `table_external_intervals.csv`; M2 matches seed 42 | VERIFIED |
| **Split C baseline, M3 / M4** | **104/150 = 0.693 / 5/150 = 0.033** | **`seed_sweep.csv` seed 42: 100/150 = 0.667 / 9/150 = 0.060; five-seed means 0.715 ± 0.057 / 0.100 ± 0.026** | **CONFLICT — see M-1** |
| **M4 baseline Split B (Sec. VI-C)** | **0.919** | **`seed_sweep.csv`: 0.9054 at every seed; Table 7 prints 0.905 ± 0.000** | **CONFLICT — see M-2** |
| Paired normalization effect | M2 +85.9 [+81.7, +89.7]; M4 +76.0 [+69.9, +81.5]; M3 +0.9 [−6.9, +8.8] | `paired_external_test.csv` | VERIFIED |
| Seed variance, all 18 cells of Table 7 | as printed | `table_seed_variance.csv` | VERIFIED |
| "seed 42 lowest of five for M2 and M4, highest for M3" (normalized) | as stated | `seed_sweep.csv`: M2 0.86 = min, M4 0.8067 = min, M3 0.7733 = max | VERIFIED |
| M2 Split D across seeds | 0.627 ± 0.135 | `table_seed_variance.csv` (0.6268, 0.1353) | VERIFIED |

### Table 8 — second external distribution

| Model | Manuscript (Split C / Split D / Δ) | `external_from_checkpoints.csv` | Status |
|---|---|---|---|
| M1 | 0/150 / 0/149 / 0.0 | 0.0 / 0.0 | VERIFIED |
| M2 | 129/150 = 0.860 / 69/149 = 0.463 / −39.7 | 0.86 / 0.4631 | VERIFIED |
| M3 | 116/150 = 0.773 / 108/149 = 0.725 / −4.9 | 0.7733 / 0.7248 | VERIFIED |
| M4 | 121/150 = 0.807 / 124/149 = 0.832 / +2.6 | 0.8067 / 0.8322 | VERIFIED |
| Split D pHash overlap | 1 of 149 within threshold, median 18 | Section VI-D; not independently re-derived here | VERIFIED (manuscript + HANDOFF) |

### Attribution

| Item | Manuscript claim | Evidence checked | Status |
|---|---|---|---|
| M1 coefficients | 93 of 96 within ±0.35; top bin β = −2.86, −2.84, −2.95 | recomputed from `model1_attribution.csv`: 93; −2.861, −2.844, −2.945 | VERIFIED |
| Top-bin dominance | the three top-intensity bins dominate mean\|φ\| | recomputed: ranks 1–3 at 0.0815 / 0.0791 / 0.0785; rank 4 is 0.0018 | VERIFIED |
| Uniform border reference | 0.642 | `supplementary.md` S-I-J | VERIFIED |
| M3 correct answers | border mass 0.760 | `occlusion_sensitivity_summary.csv` (0.76) | VERIFIED |
| M3 / M4 errors | 0.856 / 0.803 | same (0.8561 / 0.8031) | VERIFIED |
| M4 correct answers | 0.614 [0.585, 0.643], indistinguishable from uniform | same (0.614 [0.5853, 0.6427]) | VERIFIED |
| "96 of 116 images above" the reference | as stated | per-image counts not in the summary CSV | VERIFIED (manuscript; per-image file not checked) |

### Section VII — ablations

| Item | Manuscript claim | Evidence checked | Status |
|---|---|---|---|
| Per-axis on M4 | 22.0%, 27.3%, 12.7% individually; 78.0% jointly; baseline 5–9% | `table_ablation_axes.csv` (0.22, 0.2733, 0.1267, 0.78; baselines 0.0867 / 0.0533) | VERIFIED |
| White balance | 0.067 alone; costs 4.0 points added to production | `supplementary.md` Table S12 (0.067; 0.820 → 0.780) | VERIFIED |
| M1 collapse under normalization | 0.838 → 0.541 | `normalization_all_models_experiment.csv` (0.8378 → 0.5405) | VERIFIED |
| Constant sweep range | 0.480–0.873; 96 px would beat 128 px | `constant_sensitivity_experiment.csv` (min 0.48, max 0.8733) | VERIFIED |
| Ordering, JPEG-after-resize group | 0.820, 0.847, 0.880 | `order_permutation_experiment.csv` (RBC 0.82, BRC 0.8467, RCB 0.88) | VERIFIED |
| Ordering, JPEG-first group | 0.380, 0.467, 0.540 | same (BCR 0.38, CBR 0.4667, CRB 0.54) | VERIFIED |
| Best in-distribution is worst external | B,C,R at 0.946 in-distribution, 0.380 external | same (BCR 0.9459 / 0.38) | VERIFIED |
| In-distribution spread | 2.7 points | same (0.9189–0.9459) | VERIFIED |
| R,C,B beats production on both axes | 0.880 vs 0.820; 0.932 vs 0.919 | same | VERIFIED |

### Models, cost, and protocol

| Item | Manuscript claim | Evidence checked | Status |
|---|---|---|---|
| M1 parameters | 97 | `table_cost.csv` | VERIFIED |
| M2 parameters | 23,938 trainable | `table_cost.csv` | VERIFIED |
| M3 parameters | 1,154 trainable / 927,008 frozen | `table_cost.csv` | VERIFIED |
| M4 parameters | 2,562 trainable / 4,007,548 frozen | `table_cost.csv` | VERIFIED |
| Normalization runtime "under 17 ms" | preprocess cost | `table_cost.csv` (16.83 ms/image) | VERIFIED |
| Training protocol (Table 3) | Adam, lr 1e-3 from {1e-3, 3e-4, 1e-4}, batch 32, patience 4, 50-epoch cap, seed 42 | `chosen_lrs.json`, `modeling/README.md`, Table 3 | VERIFIED |
| Roboflow audit accuracy | 0.717 | `table_provenance_audit.csv` (0.7167, all metadata) | VERIFIED |
| Roboflow aspect ratio on Kaggle | 0.803 (supplement Type A entry) | `table_provenance_audit.csv` (0.8025) | VERIFIED |

### Claims correctly marked as *not* established

Listed because a reviewer audit should confirm the paper does not quietly
promote any of them. It does not.

| Claim | Manuscript status | Status |
|---|---|---|
| Corrected models recognize packaging | "Not established"; attribution evidence against for M3 | VERIFIED as stated |
| Counterfeit recall under acquisition shift | "Not measured"; both external sets authentic-only | VERIFIED as stated |
| Prevalence of the mechanism | "Not established"; seven datasets, no sampling frame | VERIFIED as stated |
| Normalization benefit for M3 | Explicitly disclaimed as inside seed variance | VERIFIED (+0.9 [−6.9, +8.8]) |
| Any deployment readiness | Explicitly disclaimed | VERIFIED as stated |

---

## C. PROPOSED STRUCTURE

The existing structure is sound and I am not proposing to replace it. Four
changes, each with a reason:

| § | Section | What belongs in it | Change from current |
|---|---|---|---|
| — | Title, Abstract, Index Terms | 250-word abstract: problem, method, finding, external evidence, implication | Drop two of eight numbers (m-5) |
| I | Introduction | The problem, the mechanism (I-A), the study and three contributions (I-B) | Unchanged |
| II | Related Work | Pharmaceutical authentication; shortcut learning and where this mechanism sits among its neighbours; leakage; corruption robustness; architectures; **what datasets this sub-field uses** (Table 1) | Unchanged |
| III | Dataset | Sources, the two exclusions, the modeling pool, the external sets | **Fold the Split D description in here** from VI-D, so both external sets are introduced together and Section VI reports results rather than defining data |
| IV | Data and Preprocessing | Filtering, near-duplicate grouping, split construction, the three kinds of uncertainty | Unchanged |
| V | Methodology | Task, four models, augmentation, the normalization operator, attribution methods, training protocol (Table 3) | Unchanged |
| VI | Results | A: the provenance audit. B: in-distribution and leakage. C: external specificity and seed sensitivity. D: the second capture shift. E: what the surviving accuracy rests on. **F: ablations** | **Promote Section VII into VI-F.** It is a results section; a separate numbered section titled "in Brief" reads as an apology (m-3) |
| VII | Discussion | What the accuracies measure; why leakage was smaller; why models differ; practical implications; the correction as substitution; the defect taxonomy; what would falsify | Renumbered from VIII |
| VIII | Limitations | Table 9 (evidence status) then one paragraph per limitation | Renumbered from IX |
| IX | Future Work | The two missing datasets; balanced collection; fine-tuning; the prevalence survey; further axes | Renumbered from X |
| X | Conclusion | What was done, what was found, the one recommendation, its two qualifications | Renumbered from XI |
| — | Back matter | Acknowledgment (with the generative-AI disclosure), ethics, availability, references, biography | Unchanged — already in IEEE Access order |

Two structural notes. **Section VI-A must stay first in Results**, before any
model accuracy: the audit is the paper's contribution and it is also the reason
every subsequent accuracy has to be read a particular way. And **Table 9 must
stay at the head of Limitations**, not in the Discussion — it is the paper's
strongest reviewer-facing device and it belongs where a reviewer looks for
what the authors concede.

---

## D. REWRITTEN MANUSCRIPT

See `MANUSCRIPT_rewritten.md` in this folder.

What changed:

- **Nothing scientific.** Every number, interval, count and claim is the one
  the artifacts support. No result was added, removed, strengthened or softened
  beyond the scope corrections listed under M-1 to M-3, and each of those is
  marked inline with a `[CONFLICT FLAG: ...]` rather than silently resolved.
- Section VII folded into Section VI-F; sections VIII–XI renumbered VII–X.
- Split D's description moved from Results to Section III-F.
- Prose compressed throughout: roughly a fifth shorter at equal evidence,
  concentrated in the passages that restate a finding a second or third time.
- Table 4's columns reordered so the header fields precede the pixel-derived
  proxy.
- Four inline flags, at the points where the reader would otherwise be misled.

What did **not** change, deliberately: the voice, the negative results, the
"we would not deploy any of these models" sentence, the refusal to quote a
prevalence rate, and the reference list, which is verified and is not mine to
edit.
