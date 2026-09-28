# Diagnostics (MDPI) reorganization — revision notes

Written 2026-09-21. **`manuscript.md`** is the complete revised manuscript
(deliverable A); **`supplementary.md`** is the supplement with every
cross-reference into the main text remapped to the new numbering. Both
derive from `paper/paper.md` and `paper/supplementary.md` at v1.4.4
(commit `0714a16`), the source that `ieee-submission-final/01_manuscript.pdf`
was rendered from. `paper/` and `ieee-submission-final/` are untouched.

Every numeric token in the new main text was checked programmatically
against the original; the only non-matches are new section numbers and
merged citation groups. No sample size, count, interval, metric, model,
split, preprocessing step, terminology or interpretation was changed.

## B. Revision summary — structural and writing changes

**Structure (IEEE → Diagnostics).**

| Original | Revised |
|---|---|
| Abstract (unstructured, 240 words) | Structured abstract with Background/Objectives, Methods, Results, Conclusions (~275 words; MDPI asks "around 250") |
| Index Terms | Keywords (8) |
| I. Introduction; I-A; I-B; II. Related Work (A–C) | 1. Introduction with 1.1 screening and the datasets behind it (I + II-A), 1.2 provenance confounding (I-A), 1.3 relation to shortcut learning, dataset bias and leakage (II-B + II-C), 1.4 objectives and contributions (I central result + I-B). Diagnostics has no Related Work section; the field review now sits in the Introduction as the instructions ask. |
| III. Materials and Methods A–G | 2.1 Study design and overview (pipeline determinism, metric conventions, the three evaluations table, the three evidence tiers — gathered from III-B, III-D and the IV preamble); 2.2 data sources, inclusion and exclusion; 2.3 product-identity grouping and de-duplication (split out of III-A); 2.4 provenance metadata audit (III-E, moved before partitioning, plus a new "implementation in this study" paragraph assembled from Table 2's caption and IV-A); 2.5 leakage-controlled partitioning; 2.6 models and training; 2.7 internal evaluation (new subsection, content from III-B, IV-B and the supplement pointers); 2.8 acquisition-shift evaluation; 2.9 balanced external evaluation; 2.10 normalization and region substitution (III-F + III-G); 2.11 statistical analysis (III-B's uncertainty paragraph + interval/test conventions scattered across captions); 2.12 reproducibility, software and use of generative AI (Data-and-Code-Availability environment paragraphs + the GenAI disclosure, which MDPI requires in Methods). |
| IV. Results A–E | 3.1 dataset composition and provenance audit; 3.2 leakage-controlled internal evaluation; **3.3 independent acquisition-shift evaluation; 3.4 balanced external evaluation** (order swapped to follow the experimental sequence you specified; Table 4 = acquisition shift, Table 5 = balanced); 3.5 exploratory normalization (3.5.1) and region analysis (3.5.2); 3.6 additional analyses reported in the supplement (new pointer section). |
| V. Discussion A–D | 4.1 what the audit revealed (V-A/V-B, with the falsifier); 4.2 why the internal results were misleading (new subsection making "leakage-free ≠ provenance-independent" explicit, from III-B and V-A); 4.3 what the external evaluations demonstrate; 4.4 what the normalization and region analyses add (V-B, with the Type A–E taxonomy); 4.5 implications, checklist and next steps (V-C); 4.6 limitations (V-D, with the evidence-status table now Table 7 and each limitation from your list stated once). |
| VI. Conclusion | 5. Conclusions (verbatim apart from section references) |
| Acknowledgment; Ethics; Data and Code Availability | Supplementary Materials (every Figure Sn / Table Sn listed by title); Author Contributions (CRediT); Funding; Institutional Review Board Statement; Informed Consent Statement; Data Availability Statement; Acknowledgments (with MDPI's prescribed GenAI sentence); Conflicts of Interest; References |

**Tables and figures.** All six original main-text tables and Figure 1 are
kept. The uncaptioned three-evaluation table in III-D is now captioned as
Table 1 (MDPI numbers every table). Final numbering: 1 evaluations, 2
acquisition pipelines, 3 audit, 4 acquisition shift, 5 balanced, 6 region
substitution, 7 evidence status. The uncaptioned 2×2 "missing cell" matrix
in V-D is stated as one sentence in 4.6. Equations keep their original
numbers (1)–(9) and order. Supplementary figures are cited as "Figure Sn".

**References.** Renumbered by first appearance (MDPI rule), citations
merged into MDPI form ([1,2], [3–5]) and placed before punctuation, list
rewritten in ACS/MDPI style with full titles. The old→new map is at the end
of this file. All 32 are cited in the main text; the supplement's citations
were remapped with the same table. The italic verification annotations on
the IEEE list were dropped (they are internal apparatus and the build
scripts already strip them); the facts they record are unchanged.

**Supplement.** Text unchanged apart from 103 cross-references into the
main text, remapped occurrence by occurrence (log in
`_supp_remap_log.txt`), the header paragraph that explains the referencing
convention, "Fig. Sn" → "Figure Sn", and citation numbers. Every main-text
section, table and equation the supplement cites exists; every
supplementary item the main text cites exists; every supplementary table
and figure is cited from the main text at least once (S9 only via the
Supplementary Materials listing).

**Writing.** Paragraphs that were already clear were carried over verbatim
(most of 1.2, 1.3, 2.2–2.6, 2.8–2.10, 3.1–3.5, 4.4, 5). New prose is
confined to joins, the overview subsections (2.1, 2.7, 2.11, 3.6), and the
Discussion openings of 4.2 and 4.3. Redundancy removed: the metric
convention and the one-sided rule are stated once in 2.1; the three
evidence tiers once in 2.1; the authentic-labeled caveat is defined once in
2.9, referred to in 3.4 and stated as a limitation once in 4.6; the
Discussion no longer re-narrates Results numbers. Length: 18,500 body words
against 16,600, because the Methods now carry the reproducibility and GenAI
material that was in the back matter, the Supplementary Materials listing
is 540 words by MDPI's format, and the Limitations answer every item in
your list explicitly. Nothing was cut for length.

## C. Issues requiring author verification

1. **Stale supplement reference in the manuscript of record.** III-B says
   "Table S2 gives every partition's class balance", but Table S2 is the
   hyperparameter table and no supplementary table gives per-partition class
   balance (checked by grep). The revised 2.5 says the committed
   split-assignment files record it. Either add a small table to the
   supplement (the split CSVs have the counts) or confirm the new wording.
2. **Abstract length.** ~275 words including the four structured headings.
   MDPI says "around 250". Every number you listed is in it; cutting further
   means dropping the normalization sentence or the balanced-set sentence.
3. **Affiliation address.** MDPI asks for PubMed-style complete addresses.
   The manuscript carries what the IEEE version carried ("Mira Costa High
   School, Manhattan Beach, CA 90266, USA"). Add a street address if you
   want one; I did not invent one.
4. **Reference [3] (Ramos et al., ICCAE 2024).** MDPI's proceedings format
   asks for conference location and date; the record of verification did not
   capture them, so the entry gives venue, year, pages and DOI only. Same for
   [20] and [25]–[28] (ICLR/ICCV/ICML/NeurIPS, old [12]–[16]), which carry arXiv IDs and no DOIs, as
   in the original; add DOIs only after verifying them.
5. **Reference [18] (Öner et al., old [11])** remains a medRxiv preprint and is still
   the sole citation for the patient-level-segregation argument (1.3, 4.2).
   The IEEE list disclosed this in an annotation; MDPI has nowhere to say it
   except the text, and the text does not. Confirm you are content with a
   preprint there, or re-check for a published version.
6. **GenAI disclosure placement.** MDPI requires the details in Materials and
   Methods (now 2.12) and the prescribed sentence in Acknowledgments (done).
   MDPI's template sentence names "[tool name, version information]"; the
   version is stated as not recorded per session, as in the original.
   Confirm that is acceptable to you, and that "the author has reviewed and
   edited the output" is accurate for the eligibility-screen output as well
   as the text.
7. **Newly cited supplementary figures.** The manuscript of record cited
   only Figures S1, S2 and S14 from the main text; the revised text also
   cites S3–S13 (Sections 2.7, 2.10, 3.2, 3.5.1, 3.6) so that every
   supplementary item is reachable. The files exist, but check that those
   captions still match the current numbers — HANDOFF records that
   Figure S1 once carried stale counts, and rendered figure text is
   invisible to every gate.
8. **Journal fit at desk check.** The study has no patients, no diagnostic
   endpoint and no clinical claim, and the manuscript says so (4.5, 4.6,
   Ethics statements). Diagnostics' scope covers AI/ML and medical imaging;
   the cover letter should make the dataset-quality framing explicit.
9. **Limitations bullet dropped on purpose.** An earlier IEEE round carried a
   paragraph explaining why no counterfeit external set under acquisition
   shift was run; it is not in v1.4.4, so it was not reintroduced. If you
   want it back, it needs to be written from the archive inventory, not
   invented.
10. **Kaggle listing figures** (662 downloads, 3 notebooks, no discussion, 13
    September 2026) change over time; refresh at submission.

## D. Final submission checklist

**Diagnostics structure**
- [ ] Title, author list, affiliation (PubMed-style), corresponding author, ORCID
- [ ] Structured abstract (Background/Objectives, Methods, Results, Conclusions), ~250 words
- [ ] 3–10 keywords — 8 present
- [ ] Introduction / Materials and Methods / Results / Discussion / Conclusions — present; no Related Work section
- [ ] Back matter in MDPI order: Supplementary Materials, Author Contributions, Funding, IRB Statement, Informed Consent Statement, Data Availability Statement, Acknowledgments, Conflicts of Interest, References — present
- [ ] Prepare in the MDPI Word (`diagnostics-template.dot`) or LaTeX template; `paper/scripts/build_tex.py` targets the IEEE Access class and needs an MDPI variant
- [ ] Abbreviations defined at first use in abstract, text and first table (CNN, LR, GAP, RGB, ROC-AUC, PNG/JPEG — check the template's abbreviation conventions)

**Main-text / supplement consistency**
- [ ] Every "Section n.m", "Table n", "Figure 1", "Equation (n)" in the supplement resolves (verified by script, 0 unresolved)
- [ ] Every "Section S-…", "Table Sn", "Figure Sn" in the main text exists (verified, 0 missing)
- [ ] Supplementary Materials statement lists every Figure Sn and Table Sn by title (done, S1–S14, S1–S28)
- [ ] Issue C1 (Table S2 class balance) resolved
- [ ] Supplement file renamed/branded for Diagnostics (currently the IEEE PDF build; regenerate from `supplementary.md`)

**Figures and tables**
- [ ] Seven tables, one figure, numbered in order of first citation (verified)
- [ ] Figure 1 supplied as PNG/JPEG/TIFF ≥ 600 dpi in RGB (`paper/figures/fig15_mechanism.png` exists; check resolution)
- [ ] Every table column has a heading (yes); captions explain every symbol (k/n, TN/FP/FN/TP, bold, parenthesized deltas — yes)
- [ ] No caption claims more than the result (Table 7 statuses match the text)
- [ ] Graphical abstract (optional): 560 × 1100 px minimum, not identical to Figure 1 — `ieee-submission-final/05_graphical_abstract.png` needs a size check

**References**
- [ ] Numbered by first appearance, brackets before punctuation (done by script)
- [ ] ACS/MDPI style with full titles (done); add conference locations/dates and verified DOIs where available (issue C4)
- [ ] All 32 cited; supplement citations also appear in the main list (verified)
- [ ] Refresh "accessed on" dates for [1], [21], [22] at submission

**Reproducibility, data and code**
- [ ] Software names and versions in Methods (2.12) — present
- [ ] Data Availability Statement with repository URL and Zenodo concept DOI — present; cut a new release if anything in the repo changes
- [ ] Statement that no images are redistributed and why — present
- [ ] Pre-registration: none; the manuscript says the protocol was fixed in advance and reports evidence tiers — no registration code to add

**Ethics / IRB / consent**
- [ ] IRB: "Not applicable" with the reason (no human or animal subjects, public packaging photographs, no identifiable person) — present
- [ ] Informed consent: "Not applicable" — present
- [ ] No IRB approval, exemption or funding source invented — confirmed

**AI disclosure**
- [ ] Methods 2.12: tool, access route, purposes, the data-producing task, author responsibility — present
- [ ] Acknowledgments: MDPI's prescribed sentence — present
- [ ] GenAI not listed as an author — correct

**Author information**
- [ ] Full first and last name; single-author CRediT statement; "The author has read and agreed…" — present
- [ ] Conflicts of Interest sentence in MDPI wording — present
- [ ] Funding: "This research received no external funding" — present

**Formatting**
- [ ] Convert Markdown to the MDPI template; equations editable (Equation Editor/MathType or LaTeX)
- [ ] Decimal points, no thousands separators inside figures; commas in ≥5-digit numbers in tables (4,007,548, 3,568, 7,283 — present)
- [ ] Section cross-references in the text use "Section n.m" (done)

**Supplementary files**
- [ ] `supplementary.md` rendered to PDF with the same title as the manuscript
- [ ] Table S2 issue resolved; Figure S1 numbers re-checked against the paper
- [ ] Supplement declares that its citations also appear in the main list (they do)

## Reference number map (old IEEE → new MDPI)

1→1, 2→2, 3→3, 26→4, 27→5, 28→6, 4→7, 5→8, 29→9, 6→10, 30→11, 7→12,
8→13, 9→14, 10→15, 31→16, 32→17, 11→18, 23→19, 12→20, 19→21, 21→22,
20→23, 25→24, 13→25, 14→26, 15→27, 16→28, 24→29, 22→30, 17→31, 18→32.

## Section map (old IEEE → new)

I → 1.1/1.4; I-A → 1.2; I-B → 1.4; II-A → 1.1; II-B, II-C → 1.3;
III-A → 2.2 (dataset) and 2.3 (de-duplication); III-B → 2.5 (+ 2.11 for
the uncertainty paragraph); III-C → 2.6; III-D → 2.1 (conventions and
Table 1), 2.8 (acquisition shift), 2.9 (balanced); III-E → 2.4; III-F,
III-G → 2.10; IV preamble → 2.1; IV-A → 3.1; IV-B → 3.2 (+ 2.7); IV-C →
3.4; IV-D → 3.3 (baseline, table) and 3.5.1 (condition D, normalized
columns); IV-E → 3.5; V-A → 4.1/4.2; V-B → 4.1/4.4; V-C → 4.5; V-D → 4.6;
VI → 5. Tables: 1→2, 2→3, 3→5, 4→4, 5→6, 6→7, uncaptioned III-D table → 1.

---

# Editorial pass, 2026-09-22 (writing quality, not science)

A full line-by-line editorial revision was applied to `manuscript.md`. **No
number, sample size, interval, model name, dataset name, statistical test,
definition, equation, citation or claim scope was changed.** Table data was
spliced back verbatim and machine-compared: all 61 table rows are byte-identical
to the pre-edit version, and no numeric token appears in the new body that was
not in the old.

**Measured style change (Abstract through Conclusions):**

| | Before | After |
|---|---|---|
| Em dashes | 86 | 0 |
| Semicolons per 1,000 words | 12.6 | 1.7 |
| Bold runs (whole body) | 211 | 50 |
| Mean sentence length | 30.5 words | 22.5 |
| Median sentence length | 27 words | 21 |
| Sentences over 50 words | 61 | 2 |
| "rather than" | 57 | 43 |
| Prose words (body) | 16,301 | ~13,700 |

**Structural changes.** Introduction cut from 2,707 to ~1,880 words and
reorganized into 1.1 Background, 1.2 Provenance confounding (absorbing the old
1.3 literature subsection), 1.3 Objectives and contributions. The contributions
bullet list became prose. Section 3.6 (a catch-all list of supplementary
analyses) was deleted and its citations moved to the Methods subsections where
each analysis is described, so every supplementary item is still cited. The
six-step audit procedure became four steps, with its interpretive material moved
to Discussion 4.1. Limitations changed from nine bullets plus prose to seven
consolidated paragraphs. Conclusions cut from 479 to ~200 words. References
renumbered again by first appearance after the reorganization, and the
supplement's citations remapped to match.

**Section numbers 1.1, 1.2, 2.2-2.4, 2.6, 2.9-2.11, 3.1, 3.4, 3.5.1, 3.5.2,
4.1, 4.2, 4.5 and 4.6 were held fixed** because the supplement cites them.
Old Section 1.4 is now 1.3 (nothing cited it); Table 7's caption was updated.

**Two precision fixes, both reported to the author rather than made silently:**
(1) "the model with the highest in-distribution accuracy (M4)" was true of the
naive split only, since M3 reaches 0.932 against M4's 0.919 on the
leakage-controlled split. The wording now names the split. (2) The abstract and
Section 1.3 now say "the strongest internally performing model" for the same
reason.

**Open item added to the list below:** Table 7's row for the acquisition-shift
result says "the model reaching 97.4% authentic-class accuracy ... returns 6.0%".
Both M3 and M4 reach 38/39 = 97.4% authentic-class accuracy, and M3 returns
66.7%, so that row should name M4. The table was left untouched pending the
author's decision.
