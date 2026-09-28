# Diagnostics (MDPI) submission checklist

Checked on 2026-09-23 against two sources:
- the official *Diagnostics* Instructions for Authors (https://www.mdpi.com/journal/diagnostics/instructions), read in the browser that day;
- the official MDPI LaTeX template (`mdpi_template/MDPI_template.zip`), downloaded from mdpi-res.com the same day.

A final full audit the same day, done with fresh eyes, fixed the items in section D.

## A. Things only you can do before submitting (blocking)

1. **Confirm the paper is not under consideration anywhere else.** The cover letter states that neither the manuscript nor any part of it is under consideration or published elsewhere. `ieee-submission-final/` is a complete IEEE Access package. If it was submitted, withdraw it before submitting here, or do not submit here.
2. **Cover letter:** done. It is dated 23 September 2026 and signed with your typed name. If you submit on a later day, update the date. If you ever submitted this work to another MDPI journal, add that and the manuscript ID.
3. **Read the two new prior-work sentences in Section 1.3.** They cite Ong Ly et al. 2024 (*npj Digital Medicine*) and Drenkow et al. 2025 (G-AUDIT, arXiv). G-AUDIT scores how well dataset attributes, acquisition attributes included, predict the label, which is close to this paper's audit. The text now presents the audit as an adaptation of that idea to image-authenticity data, not as a check nobody has proposed. Both citations were verified against Europe PMC and the arXiv API. Please read them; a reviewer who knows G-AUDIT would have raised this.
4. **In the submission system (SuSy):**
   - enter suggested reviewers (not in the cover letter);
   - link your ORCID;
   - enter funding as "no external funding";
   - check the email address, which published papers display.
5. **APC.** *Diagnostics* charges an article processing charge, and the paper declares no funding. Check the current amount and any waiver before submitting.

## B. Requirements checked in the package

| Requirement (Instructions for Authors) | Status |
|---|---|
| Word or LaTeX template; LaTeX as one ZIP the office can recompile | Done. `02_manuscript_latex_source.zip` holds `manuscript.tex`, `Definitions/` (official class, `diagnostics` option) and `figures/`. It was recompiled from a clean extraction with pdflatex: 0 undefined references, 0 overfull boxes, 0 missing characters. The only warning is fancyhdr's header height, from the MDPI class itself. |
| Title concise; no running title | Done |
| Full author name; affiliation in PubMed format; corresponding author | Done: Mira Costa High School, Manhattan Beach, CA 90266, USA. If you had no formal affiliation for this work, MDPI asks for "Independent Researcher". |
| Structured abstract, about 250 words, with headings Background/Objectives, Methods, Results, Conclusions | Done: 257 words including headings |
| 3–10 keywords | Done: 8 |
| Sections: Introduction, Materials and Methods, Results, Discussion, Conclusions | Done |
| Software named with versions; code availability | Done (Section 2.12) |
| GenAI use disclosed in Methods, and in Acknowledgments with tool name and version | Done (Section 2.12 and Acknowledgments) |
| Preregistration link, if preregistered | Not applicable. The protocol was fixed in advance but not publicly registered. |
| Abbreviations defined at first use in abstract, main text and first table; abbreviation list | Done |
| Equations editable | Done (LaTeX) |
| Figures ≥600 dpi PNG/JPEG/TIFF, RGB, placed after first citation | Done. Figures 1–3 are vector in the PDF; `05_figures.zip` holds Figures 1–3 as 600 dpi RGB PNG and vector PDF. |
| Tables with column headings, ≥8 pt, numbered in order | Done: Tables 1–6 |
| Commas in numbers of five or more digits | Done |
| Supplementary Materials section with "Figure S1: title" and "Table S1: title" | Done: Figures S1–S12, Tables S1–S29 |
| Author Contributions (CRediT); Funding; IRB; Informed Consent; Data Availability; Conflicts of Interest | Done |
| References by first appearance, `[n]` before punctuation, ACS style with full titles | Done: 30 references, order verified by script, 30 `\bibitem`s |
| Supplement citations also in the main reference list | Done. The supplement cites [3–6], [14], [18], [20], [21], [27–30]; all are in the list. |
| Cover letter with the two required statements | Done. Wording is verbatim; dated 23 September 2026; typed signature. |
| Total upload ≤ 120 MB | Done (about 4 MB; see MANIFEST) |
| Graphical abstract (optional) | Included: `06_graphical_abstract.png`, 2400 × 1200 px RGB, original artwork (not a copy of any figure), Arial, no heading |

## C. How it compares with published *Diagnostics* articles

Fifteen recent (2026) *Diagnostics* deep-learning articles were pulled through Europe PMC; the figures below come from the original-research articles among them.

| | Typical *Diagnostics* article | This manuscript |
|---|---|---|
| Body length | about 4,300–11,400 words (median about 7,000) | about 6,500 words |
| References | 26–77 (median about 38) | 30 (24 before this audit) |
| Figures | median about 5 | 3 (1 before this audit) |
| Tables | median about 4 | 6 |
| Abstract | median about 240 words | 257 |

Length and tables are typical. References and figures were below the norm and have been brought into range. What sets this paper apart is its rigor: every number regenerates from committed code, a leakage-controlled paired experiment, pre-specified tiers, and external tests. Most comparable papers report a single held-out split. The main risk is **scope**. Counterfeit-packaging screening is at the edge of a clinical-diagnostics journal. The cover letter argues for fit through dataset quality assurance and validation of diagnostic imaging AI, but desk rejection on fit is possible.

## D. Found and fixed in the final audit (2026-09-23)

- **Figure S13 plotted the superseded archived run** (M3 69.3%, M4 3.3%), while its caption said it plotted Table 4 (66.7%, 6.0%). The values were hard-coded in `paper/scripts/make_figures.py`. They are now read from `table_external_intervals.csv`, and the figure moved to the main text as Figure 3. **The IEEE package `ieee-submission-final/` still contains the old figure.**
- Figure S10 published two Kaggle images (license "Unknown") that the Data Availability Statement says are withheld. It is replaced by a four-panel version with only Mendeley images (CC BY 4.0, attributed) and with "attribution" rather than "attention".
- Figure S12's axis said "Shapley value", which the paper explicitly says this quantity is not. The label now reads "logit contribution".
- Figure S11's caption now says it plots the pre-fix ablation runs of Tables S11 and S13.
- Section 2.9 said the balanced set was "the only evaluation with both classes present". The internal test also has both classes, so it now says "the only external evaluation".
- Section 2.8: a supplement reference was attached to the wrong clause, and condition C was described as "the Mendeley archive" rather than 150 photographs from it. Both fixed.
- Section 3.1 now says where the Roboflow audit comes from (Table S20). This also shows that Table S19's "five scorable datasets" is correct: four from Table S18 plus Roboflow. The earlier flag is withdrawn.
- Four previously verified references were restored:
  - Ting et al. and Al-Hussaeni et al., on drug identification;
  - Hill et al. and Seah et al., on medical-imaging shortcuts.
- Two new references were verified and added: Ong Ly et al. and Drenkow et al.
- Figure S14 moved to the main text as Figure 2.
- Grammar: "data were accessed".
