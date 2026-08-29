# Handoff — resume here

Rewritten 2026-07-30. Supersedes the previous version entirely, which
described a framing the paper no longer uses. Read this, then `README.md`,
then `paper/paper.md`.

## Submission state, 2026-08-29 — READ THIS FIRST

Everything in the repository is committed and every check passes. Three things
need a human and cannot be done from here; nothing else is outstanding.

**1. DONE — v1.1.0 is released and archived.** Pushed, tagged and published on
2026-08-29; Zenodo minted **doi:10.5281/zenodo.22166543** for it, and the
concept DOI 10.5281/zenodo.21936720 now resolves there. The manuscript cites
the VERSION DOI, deliberately: the concept DOI would silently start pointing at
a later release and the sentence naming v1.1.0 would go stale without anyone
editing it. `CITATION.cff` and `.zenodo.json` carry version 1.1.0 and both
DOIs. One expected and harmless asymmetry: the DOI was minted from the release,
so the archived snapshot's own `paper.md` cites the concept DOI while HEAD
cites the version DOI. The analysis code and every number are identical in
both; only that one sentence differs.

**2. Re-export the two files that need Office.** `build_poster.py` writes the
.pptx but the poster PDF needs a PowerPoint export, so
`PharmaChecked_v2_poster.pdf` still carries the previous subtitle. And the
Word-exported `PharmaChecked_v2_manuscript.pdf` was a stale 22-page file
carrying the OLD TITLE; it has been renamed
`SUPERSEDED_20260828_manuscript_old-title.pdf` so it cannot be submitted by
mistake, and it is gitignored either way. The two current PDFs are
`PharmaChecked_v2_manuscript_IEEEAccess.pdf` (20 pages) and
`PharmaChecked_v2_supplementary_IEEEAccess.pdf` (25 pages), both built by
`compile_pdf.py`; the .docx is current.

**3. Kaggle usage figures are dated, not stale.** Section II-F and reference
[19] quote 3,039 views / 591 downloads / 3 notebooks / 2 votes "as of 28
August 2026". Those counts are rendered by JavaScript and cannot be fetched
programmatically. They are explicitly dated, so they are correct as they
stand; refresh them by hand only if the manuscript sits for months, and note
that the argument depends on the order of magnitude, not the exact count.

**What was verified on the day, not assumed.** The Overleaf zip was extracted
into an empty directory and compiled there: 20 and 25 pages, matching the
local build. Every table-producing analysis script was re-run and the working
tree stayed clean, which means each one reproduced its committed CSV byte for
byte -- including `cross_domain_audit.py`, which re-fetched all seven Kaggle
listings live and returned identical numbers. A geometric check found zero
text blocks past the 177.53 mm text block in either document. `CITATION.cff`
parses and `.zenodo.json` is valid JSON.

**One number to re-check if anything is ever re-run.** Section VI-E's "94.6% on
Split B" was M4's superseded accuracy and is now 91.9%; the value of record
lives in `modeling/results/leakage_table.csv`. Two documents quoted the old
number for weeks after Section S-I-G documented its correction, so treat any
0.946 in this project as suspect unless it is an ordering-sweep or
constant-sweep row, where it is a real result.

## Proofread pass, 2026-08-29 (later the same day)

A fresh read of the RENDERED pages, not the source, on the assumption that
nothing was already correct. Eight defects, four of them visible on the page
and two of them factual. The lesson repeats the one HANDOFF already records:
every check in this repository reads the Markdown or the build log, and the
things found here were invisible to both.

**A set statement was being typeset as a table, in both outputs.** Section
III-A wrote the shipped-split cardinalities as a line beginning with "|", so
the Markdown parser read it as a one-row table and ate the bars as cell
delimiters. The PDF and the .docx both printed "T = 661, V = 453" with no
cardinality notation at all, and the .docx carried an eleventh table that does
not exist. It is now prose. `verify_crossrefs.py` gates the class: every
pipe-led line must belong to a block containing a |---| separator.

**Two stale accuracies for M4.** Section VI-E said "a model at 94.6% on Split
B" and the supplement's Type A entry said "in-distribution 0.946" -- both the
value that Section S-I-G documents as *superseded*, corrected to 0.919 when
checkpointing exposed it. The paper described the correction and then quoted
the old number twice. Now 91.9% and 0.919.

**Three claims contradicted the same day's own findings**, left behind when
the occlusion result narrowed them: Future Work still said "both backbones
justify authentic by the surround", S-II still called that the basis of both
backbones' correct predictions, and Section IX asserted "seed-to-seed variance
is itself unmeasured" two sentences after reporting the measurement. When a
finding is read down, grep the whole corpus for the old phrasing.

**Formatting, all confirmed by rendering the page rather than by the log:**
the repository URL was stretched by the justified 85 mm column into
"https : / / github . com / ..." (`\Urlmuskip` cut from 1mu to 0.15mu); the
ethics declarations were emitted as a NUMBERED section, so "XII. ETHICS" sat
between two unnumbered back-matter sections; two sentences began "(8)
composes ..." because IEEEtran style drops the word "Eq." (`build_tex` now
writes "Equation~(8)" sentence-initially); Table 4's "kB = 1000 bytes" note
was stranded a page away from the float it defines, the same defect the
2026-08-28 pass fixed for a different note, and is now inside the caption;
and one leftover British spelling in the main paper plus three in the
supplement survived `americanize.py`.

**Two builder bugs, both of which had been silently producing wrong output.**
`build_tex` stored its own copy of the author biography, so editing `paper.md`
did not reach the PDF -- it now renders the biography from the Markdown. And
the width guard on uncaptioned tables compared against `\textwidth` when such
a table is set inside ONE column, so the new seed-variance table overflowed its
column by 39.6pt while the build reported it fit; the guard now uses
`\linewidth`, which is correct in a float and in running text alike.

**Verification used from here on.** A geometric margin check beats the LaTeX
log: rasterise nothing, just compare every text block's right edge against the
177.53 mm text block. Both documents currently have zero blocks past it, while
the log still reports 43 and 54 "overfull" boxes, of which 41 and 51 are the
class's own page furniture and the rest are under 10pt and invisible.

**Page count.** Still exactly 20, with the `\EOD` mark last on page 20 and no
slack. Every addition in this pass was paid for by cutting duplication, mostly
material the supplement carries in full.

## Reviewer-response pass, 2026-08-29

A reviewer read the compiled PDF and raised twelve items. Nine are done; three
need data or annotation this pass could not produce, and are listed under Open
items with what exists to make them cheap.

**The paper was retitled** to *Provenance Confounding in Image Authenticity
Classification: Detection and a Counterfeit-Medicine Case Study*. "Partial
Repair" was giving the wrong emphasis to a paper whose Section VIII-E argues
the correction is a diagnostic rather than a remedy. The new title is in
`paper.md`, `supplementary.md`, `README.md`, `CITATION.cff`, `.zenodo.json` and
the poster subtitle. **The published Zenodo v1.0.1 record still carries the old
title**; edit that record's metadata if you want them to agree.

**A factual contradiction was removed.** Table 2 described the Kaggle archive
as "the dataset used by [3]", which contradicts Table 1 (Ramos et al.
self-captured on a Raspberry Pi rig) and Section II-F (no located study uses
it). This is the kind of error that makes a reviewer doubt the reference audit,
so it is worth knowing how it survived: nothing checks a claim that resolves.

**Sixteen cross-references pointed at the wrong target**, all of them
resolving, so no existing check saw any of them. `verify_crossrefs.py --map`
is the check that finds them: it prints every Section, Table and Fig.
reference beside the TITLE of what it resolves to, so a wrong target reads as
a mismatch rather than as a number. Run it after any renumbering or
restructuring and read the list. Four were `Table 7` (cross-domain audit)
meaning `Table 8` (external generalization); four were `Section S-I-D`
(Training protocol) meaning `S-I-B` (synthetic proxy); the rest were VI-C/VI-D
for VI-A/VI-E/VI-F, VII-A for VII-B, and Section IX pointing at VII-B for a
derivation that lives in S-I-S.

**A numerical inconsistency is now gated.** The prose said M4 went "5/150 to
122/150" where every table says 121. `verify_crossrefs.py` now derives the
legitimate k/150 and k/149 counts from `external_from_checkpoints.csv`,
`external_intervals.py`'s archived baselines and the border-mass summary, and
fails on any count that is not one of them. Adding a new count means producing
the artefact that justifies it.

**"False-positive rate" was wrong throughout and is now "specificity".**
Counterfeit is the positive class, so accuracy on an authentic-only external
set is the true-negative rate, not the false-positive rate. Section III-E
defines the equivalence once; the four code files that repeated the error were
corrected too.

**Two new measurements, both of which changed a claim.** They are the reason
this pass took hours rather than minutes, and both are reproducible:

`modeling/seed_sweep.py` repeats M2, M3 and M4 at five seeds, production and
un-normalized, on Split B/C/D (Section S-I-U, `table_seed_variance.csv`). Seed
42 reproduces all three models' published numbers exactly, which validates the
harness. Findings: the correction's effect on M2 and M4 is an order of
magnitude larger than seed variance, so the headline holds; **M3's is not
distinguishable from seed noise at all** (0.715 +/- 0.057 to 0.724 +/- 0.047),
which converts the paper's cautious refusal to claim a benefit for M3 into a
measurement; and **M2's Split D collapse is overstated by the run of record**
-- 0.627 +/- 0.135 across seeds, with seed 42 the lowest of five, so the mean
drop is 28 points rather than 39.7. Section VI-F now says so.

`modeling/occlusion_sensitivity.py` re-tests the attention claim with a
perturbation method that needs no annotator and covers all 150 external images
per model. It **confirms** the Grad-CAM reading for M3 and for both models'
errors and **contradicts** it for M4's correct answers (border mass 0.614
[0.585, 0.643] against a 0.642 uniform reference; 55 of 121 images above it).
The manuscript's "identical in both backbones, 40 of 40" reading is therefore
withdrawn in Sections VI-G, VI-F, VIII-C, VIII-E, the abstract and the
conclusion. Do not restore it.

**The build had a second copy of the author biography.** `build_tex.py` stored
it as a constant, so editing `paper.md` silently did not reach the PDF. It now
renders the biography from the Markdown, which is what the single-source rule
requires. If you add front matter, check whether a builder hard-codes it.

**Front-matter placeholders are template-owned, and now documented as such.**
`xxxx 00, 0000`, `10.1109/ACCESS.2026.DOI` and `VOLUME 11, 2023` come from
`ieeeaccess.cls`, which is byte-identical to the one in
`ACCESS_latex_template_20240429/`, and from the template's own `access.tex`.
IEEE fills all three at production. `final_sweep.py` now reports them as
expected and separately asserts the nine author-owned fields are filled,
failing on any other placeholder token. **Do not "fix" them.**

**Page count.** The additions pushed the manuscript to 21 pages and it is back
to exactly 20, paid for by condensing material the supplement already carries
in full -- the VIII-G taxonomy, VII-A's ablation summary, the Conclusion's
qualifications, and a funding statement that appeared three times. The
`\EOD` mark is again the last thing on page 20, so **any prose addition needs
a compensating cut**. `compile_pdf.py` reports the page count.

Also done: intervals are no longer described as uniformly bootstrap (two
constructions, each table names its own); the abstract's "no in-distribution
evaluation can expose this" was self-contradicting, since the metadata audit
is in-distribution and does expose it, and now distinguishes conventional
predictive evaluation from the audit; scope claims were narrowed from "any
binary image task" to what the evidence supports; contribution 1 concedes the
general phenomenon to [6]-[10] and claims the mechanism and the screen;
references [3], [23] and [30] were re-verified against Crossref and DBLP and
match exactly.

## Submission-readiness pass, 2026-08-28

A reviewer read the compiled PDF and named four production defects and two
framing recommendations. All six are done. **The manuscript is 20 pages, the
supplement 23, both compile clean, and `overleaf_upload.zip` now compiles
both from an empty directory** — it did not before, and had gone stale.

**Float placement.** One page of the manuscript was four full-width floats
and no text at all, several pages after the text introducing them. Two causes,
both fixed. The preamble now raises `dbltopnumber`, `dbltopfraction` and
`dblfloatpagefraction` so the queue drains onto the tops of text pages instead
of into pages of its own. And three figures were saved much taller than their
`figsize`, because `savefig.bbox: tight` crops the empty *width* away while a
legend anchored outside the axes keeps the height — so `width=\textwidth`
scaled the resulting aspect **up**. Figure 3 reached 4.5 in on the page, half
a page for one bar chart; its legend is now one row above the axes and its
explanatory line moved into the caption. If you add a figure, check its saved
aspect, not its `figsize`. `paper/scripts/compile_pdf.py` compiles both
documents and then reports the float-to-text balance of every page, failing
on a float-only page in the manuscript. Never trust a build report over a
rendered page.

**Tabular notes.** A note defining a mark used in a table's cells was a plain
paragraph after the table, so the float carried the mark to a page top and
left the note behind in running text. A paragraph opening `\*` immediately
after a table is now folded into the float by both builders.

**Six internal reference notes were printing in the bibliography.** The
stripper matched a whitelist of opening words; notes starting any other way
went through. It is now structural — a trailing italic span of four or more
words ending in a full stop — and `verify_crossrefs.py` gates on the rendered
bibliography containing no known note phrasing. A note ending on a quotation
rather than a period slipped past the first version of that rule, which is
why the predicate strips closing quotes before testing.

**Every reference re-verified against a primary source.** [20]'s author list
(Esraa Abdelmaksoud, Ahmed Gadallah, Ahmed Asad) confirmed on the Mendeley
landing page. [30] upgraded from the arXiv preprint to the published ECCV 2024
Workshops paper. Page ranges and DOIs added to [3], [23], [26]; ISSNs to [26],
[27], [28]. Kaggle usage figures refreshed live (3,039 views, 591 downloads,
2 votes, 3 notebooks, 28 Aug 2026). **A real error was corrected in the audit
trail:** the archive's identity was said to match the listing on 279,596,681
bytes, but that is the sum of uncompressed member sizes; the listing's
`totalBytes` is 279,469,596, which is the zip's own size. Both are now stated
and both check out.

**Four section cross-references pointed at the wrong section** — a VI-C/VI-E
swap in three places and a Section IX self-reference that should have been
Section X. Every reference resolved, so nothing caught them. `verify_crossrefs.py`
now reports references that point at their own enclosing section, which is the
cheapest signature of a stale one. **A stale claim in the supplement was
removed**: Section S-I-J said the attention categorizations were "illustrative
samples, 15 of 24 and 5 of 20", contradicting its own opening and the figure
caption. `modeling/results/gradcam_review_completed.csv` holds 62 of 62 tagged
rows matching every number reported, so the coverage paragraph now separates
the two true statements — every map produced was scored, and the images those
maps came from are a seeded stratified sample.

**Citation ranges were never compressing.** `\cite{ref26}--\cite{ref28}` was
emitted for every range because the en-dash had already become `--` by the
time the citation pattern ran, so its single-character class never matched.
Ranges now emit one `\cite{ref26,ref27,ref28}`.

**The two framing recommendations were adopted.** The frozen backbones are now
introduced as **linear probes on a fixed representation** — the right
instrument for attributing an accuracy change to the input distribution rather
than to features that re-adapt — with the CPU-only constraint stated once
rather than apologized for in four places. The limitation itself is unchanged
and unsoftened: nothing here measures a fine-tuned network. And a new
**Section VIII-E** collects four results already in the paper into the claim
they jointly support, that the three-way normalization exchanges one confound
for another rather than removing it. Nothing in it is a new result. Sections
VIII-E/F/G became F/G/H and every reference was rewritten.

**Watch the page count.** Over 20 pages requires a pre-submission inquiry to
the Editor-in-Chief. The additions above cost about a page and were paid for
by condensing the Conclusion, which was 6,700 characters of restatement, and
by trimming the passages the new Section VIII-E made redundant. The margin is
now one line: the `\EOD` end-mark is the last thing on page 20. Use
`compile_pdf.py` after any prose addition.

## What this project is now

A methods paper about **class-conditional provenance confounding**: in any
binary "is this genuine?" image task, the inauthentic class is scarcer than
the authentic one, so it gets sourced by a different procedure
(screen-captured, scraped, edited, generated). The label then predicts the
*acquisition process*, which is easier to learn than the semantics, and no
in-distribution evaluation can detect it because held-out partitions inherit
the confound in the same proportion.

The Kaggle *Fake vs Real Medicine* dataset is the **case study**, not the
subject. Do not reframe the paper around that dataset being defective —
a deep-research check confirmed no peer-reviewed work cites it, so
"this dataset is bad" has no readership. The mechanism does.

Title: *Provenance Confounding in Image Authenticity Classification:
Detection and a Counterfeit-Medicine Case Study* (retitled 2026-08-29; the
previous title led with the mechanism and ended on "Partial Repair", which
oversold a correction the paper reports as a diagnostic).

## Things that are settled — do not re-litigate

- **No earlier draft is mentioned anywhere**, in the manuscript or in this
  public repository. It was never published and is to stay unmentioned, not
  merely uncited: no citation, no figures quoted from it, no architecture or
  accuracy numbers attributed to it, and no account of its review history.
  The references were renumbered accordingly and every motivation that once
  leaned on it now stands on the dataset and the mechanism instead. If you
  are tempted to reintroduce any of it for context, don't.
- **Split C is authentic-only** and no independent counterfeit-labelled
  source exists; an extensive search ruled this out. The synthetic proxy is
  a perturbation-robustness probe, never a recall measurement.
- Scope is "packaging and immediate containers", not outer cartons only.
- Model 1 is reported as a clean negative result.
- Citation style is IEEE numbered.

## IEEE Access conversion, 2026-08-13

Decisions taken while putting the manuscript into the journal's format, so
they are not re-argued:

- **The abstract was cut from ~1,150 words to 244.** Access allows one
  paragraph of about 250. The five-paragraph version is preserved verbatim in
  `paper/abstract_long_superseded.md`; nothing in it is unique, every claim
  also appears in the body. `**Keywords:**` became `**INDEX TERMS**`,
  alphabetised.
- **Back matter reordered** to Access order: appendixes, acknowledgment, data
  availability, references, biographies. "Acknowledgements" became the IEEE
  house singular "Acknowledgment".
- **Author biographies added as placeholders.** Access requires one per
  author. They are unfilled, like the author block, and the two must still be
  completed together so blind review is not broken.
- **The internal apparatus is excluded from the built artefacts, not from the
  source**: the "Reference verification status" note and the trailing italic
  verification annotation on each reference stay in `paper.md` as the audit
  trail, and both builders drop them. Set `KEEP_INTERNAL_NOTES = True` in
  either builder to render them.
- **British spelling was deliberately left alone.** IEEE house style is
  American, so "normalisation", "colour" and "generalisation" are a real
  remaining deviation. It was not changed because the same words appear in
  figure labels generated by `make_figures.py`, in committed CSVs and in the
  poster, and a prose-only pass would make those disagree. It is a mechanical
  pass whenever it is wanted -- it just has to cover all four.
- Two genuine defects surfaced by the new checker and fixed: reference [25]
  (the pHash thesis) was in the bibliography but cited nowhere, and Table 23
  was never referred to in the text.

## Peer review, 2026-08-13: accept with minor revision

A review came back recommending **accept with minor revision**, praising the
composition-order sweep (Section VIII-F) as one of the paper's most compelling
results. All four substantive actions are done:

1. **Domain adaptation.** Eq. (8) is now framed explicitly as a
   *zero-target-sample baseline*, with Deep CORAL, MMD matching and an
   adversarial confusion head named as what a practitioner holding unlabelled
   target data should benchmark against it. We say we expect them to win.
   Still no empirical comparison — that is the honest gap and it is stated.
2. **Grad-CAM diffuseness.** Section VII-G no longer claims anything about
   *what the normalised models see*. A 128 px bottleneck degrades
   activation-based attribution as well as the input, so the near-uniform maps
   are reported as a limitation of the method under a spatial bottleneck. The
   40-of-40 differential result survives, and the paper now says why: it is a
   contrast between correct and incorrect predictions within one model and one
   bottleneck, and degraded attribution adds noise rather than manufacturing a
   perfect outcome-aligned split. The border-mass/categorisation "independent
   agreement" claim was read down to weak corroboration — 0.655 against a
   uniform 0.642 is in the predicted direction but indistinguishable from
   uniform.
3. **Frozen backbones.** Future Work now leads with fine-tuning as the
   top GPU-enabled item and states outright that the frozen-backbone results
   are not an upper bound in either direction.
4. **Grouped CV.** Section VII-C opens with, and Table 10's caption repeats,
   that "leakage-free" means *product-identity* leakage only and never
   acquisition leakage — no partition of this pool can put a capture process
   on one side of a fold.

Minor items: Kaggle usage metrics refreshed against the live API (downloads
540 → 574 between 29 Jul and 13 Aug 2026; votes, notebooks, licence and
last-updated unchanged, `totalBytes` still matching the local archive), and
every script path cited in the paper verified to exist (32/32).

**The author block and biographies are still placeholders on purpose.** The
reviewer asks for them to be filled before publication; that remains the
author's call and they must be completed together so blind review is not
broken.

## Second review round, 2026-08-13: "major revision" — what was done

**A figure-rendering defect was found and fixed, and it had been silently
shipping.** `Normal` sets EXACT 12 pt line spacing, which IEEE Access's 10/12
body requires — and Word clips an inline image to the exact line height, so
**every figure in every .docx built before this fix was cropped to a 12 pt
sliver of its own bottom edge.** Only the axis labels showed. It was caught by
rasterising a page and looking, not by any check the build prints; page count
went 43 → 49 once fixed. `render_figure` now sets
`line_spacing_rule = SINGLE`. Never trust a build report over a rendered page.

New analyses, both committed and both cheap to re-run:

- `paper/scripts/calibration_analysis.py` (Table 18) — Brier, ECE, MCE and
  over/under-confidence for all four models on all four partitions, from the
  persisted per-image scores. Required teaching
  `eval_external_from_checkpoints.py` to persist the probabilities it had
  been computing and discarding; that re-run reproduced all eight external
  accuracies byte-identically. Headline: in-distribution ECE looks fine
  (M3 0.064, M4 0.061) for models that are confidently wrong externally, so
  **calibration is as blind to the confound as accuracy is**. MCE is the
  revealing statistic, not ECE — M2 has ECE 0.118 and MCE 0.962 on Split C.
- `paper/scripts/cross_domain_audit.py` (Table 19) — the provenance audit run
  on seven datasets in four application areas **from Kaggle's public file
  listings, downloading nothing**. The listing gives path (class folder) and
  encoded size, which is two of the four audit features. Results: the
  case-study dataset returns 1.000 by this independent route (positive
  control); one generated-image dataset returns 1.000; a second in the same
  area returns 0.577; and the **signature negative control returns format
  0.500 but size 0.843** — a false-positive mode, almost certainly ink
  coverage rather than acquisition. That produced a new Type E in the
  Section IX-F taxonomy and a rule for reading the audit: **format is
  near-decisive because storage format is never a property of the object;
  size, resolution and aspect ratio mix acquisition with content.**

Also done: Holm–Bonferroni over the six McNemar tests (smallest adjusted
*p* 0.118 → 0.711; nothing was significant uncorrected so nothing changes)
plus a paragraph on why the ablations are not a test family; generality
claims rescoped in abstract, Section I-A and the conclusion as a hypothesis
with a stated test rather than a measured rate; Eq. (8) framed as a
zero-target-sample baseline; an Ethics/COI/Data-Provenance section added;
the Kaggle usage metrics refreshed (574 downloads).

**Authorship, declarations and spelling completed 2026-08-13.** The author
block, corresponding author, affiliation and biography are filled from the
earlier Overleaf draft (Sophie Zhu, Mira Costa High School); the photograph is
committed at `paper/figures/author_photo.jpeg` and `paper/latex/figures/`, and
the LaTeX build uses `IEEEbiography` with it. Funding: none received, stated
in three places consistently. COI: none declared. **A generative-AI
disclosure states that the manuscript and code were prepared with the
assistance of Claude**, itemises what that covered, and states that the design
decisions, interpretations and the decision to report negative results are the
author's, and that every number is produced by committed code and verified by
re-execution.

`paper/scripts/americanize.py` converted the prose to American spelling
(283 substitutions in `paper.md`, plus the figure and poster generators so
their labels agree with the body). It skips fenced code, inline code spans,
URLs and filenames, and is idempotent. Two things it deliberately did not
touch, both verified afterwards: the figure filename
`fig08_external_generalisation.pdf` (the leading underscore blocks the word
boundary, so the name stayed consistent across paper.md, the generator and
disk) and the cited author name "Manlises". Figures and poster were
regenerated; the poster's four columns still report positive slack.

**Both items in this paragraph are now done** and it is kept for the record:
the repository is public and archived (doi:10.5281/zenodo.22151840), and the
attention audit gained a second, annotation-free opinion on 2026-08-29 (see
the reviewer-response pass above). A second human annotator is still open;
`scripts/21_build_gradcam_review.py` already produces the tool.

## Current headline results

| Claim | Value |
|---|---|
| Capture pattern predicts label | 100% (240/240 PNG counterfeit, 421/421 JPEG authentic, as shipped) |
| Metadata-only oracle (3 scalars, no pixels) | 1.000 on the leakage-free test partition; file size alone suffices |
| Shipped train/val/test split | `train` = all 661 images; `val` and `test` are subsets of it |
| Leakage effect | ≤ 6.8 points, against a 9.2-point analytic ceiling (7/76 test images) |
| Pairwise model differences | none significant, all p ≥ 0.118; M3-vs-M4 unresolvable by construction |
| External, Split C, after correction | M2 86.0%, M3 77.3%, M4 80.7% |
| External, Split D (2nd capture shift) | M2 **46.3%**, M3 72.5%, M4 **83.2%** |
| Seed variance, 5 seeds (Section S-I-U) | correction >> noise for M2/M4; M3 0.715±0.057 → 0.724±0.047, i.e. no effect; M2 Split D 0.627±0.135 |
| Occlusion vs Grad-CAM on external attention | agree for M3 and for both models' errors; disagree for M4's correct answers |

**Two findings dominate the current draft.** First, Model 2's Split C lead
was specific to that capture condition (Split D), so the correction transfers
for frozen backbones and not for the from-scratch CNN. Second, and more
important: the completed attention audit found that on external images
**both backbones take their evidence for "authentic" from the background and
for "counterfeit" from the product** — 40 of 40 maps, no exceptions, both
models identical. Split C and Split D share one backdrop, so neither tests
that cue. The paper therefore reports that accuracy survives a change of
camera and explicitly does **not** claim any model recognises packaging.

## Reproducibility state

Checkpoints are now persisted (`modeling/results/checkpoints/`, 27 files)
with the LR, seed, best epoch and epoch count each was trained under;
`result_io.load_checkpoint` **raises** if the recorded LR differs from the
caller's expectation. `modeling/eval_external_from_checkpoints.py` is the
template for any new external evaluation — it loads rather than retrains,
which is the difference between finishing in minutes and being killed by
this host.

Adding checkpoints immediately exposed a real error: **Model 4's Split B
accuracy is 0.919, not the 0.946 previously committed.** The new value is
deterministic across three re-runs; the cause of the old value could not be
identified because that run's artefacts were never saved. Every derived
table was regenerated. See `modeling/README.md` for the full note.

Lesson worth keeping: a pipeline can be fully seeded, deterministic on
re-run, and still fail to reproduce its own published numbers if nothing
durable was saved when those numbers were produced.

## Build discipline

`paper/paper.md` and `paper/supplementary.md` are the single sources of truth.
Every artefact is generated from them and none may be hand-edited. Run in this
order:

```
python paper/scripts/build_tex.py        # IEEE Access LaTeX, manuscript
python paper/scripts/build_supplement.py # IEEE Access LaTeX, supplement
python paper/scripts/build_docx.py       # IEEE Access .docx
python paper/scripts/verify_crossrefs.py # gate: refs, cites, labels, S-refs,
                                         #   and no internal note in the bib
python paper/scripts/compile_pdf.py      # both PDFs + per-page float audit
python paper/scripts/final_sweep.py      # page count, docx/pdf agreement
python paper/scripts/make_overleaf_zip.py
python paper/scripts/build_poster.py     # then export PDF via PowerPoint COM
```

**The manuscript is in IEEE Access format as of 2026-08-13.** Both builders
implement the metrics in `ieeeaccess.cls` rather than an impression of a
published PDF: two columns of 85.29 mm with a 6.95 mm gutter on a
203.2 x 276.2 mm page, Times 10/12 body, sans headings in Access blue,
7 pt captions, 7.61 pt references. `build_docx.py` documents the mapping.

Traps, all of them hit during this project:

1. **Poster text boxes are fixed-height with hard-coded `y +=` advances.**
   Added prose silently overflows into the next section. The layout report
   printed by the build script will NOT catch it. Always export a PNG via
   PowerPoint COM and *look at it*. The same applies to the manuscript:
   export it to PDF via Word COM and rasterise a page before believing it.
2. **Table numerals are literal Arabic text in `paper.md`** (Access sets
   `\thetable = \@arabic`; Roman is JTEHM-only, which is why they were
   renumbered from I-XXI to 1-23 on 2026-08-13). Inserting a table still
   means a scripted shift of every later caption *and* every in-text
   reference -- `verify_crossrefs.py` is now that check, and it fails
   non-zero, so run it after any renumbering.
3. **An uncaptioned Markdown table must not become a LaTeX float.**
   `\caption` advances the table counter, which would silently shift every
   number after it away from the manuscript's own. `build_tex.py` emits
   those three as plain `center`ed tabulars.
4. **Word holding the .docx** makes `build_docx.py` fail with PermissionError.
   Don't kill WINWORD (unsaved work); build to a temp path by patching the
   module-level `OUT`, then re-run the canonical build.

Section numbering is Roman with lettered subsections (`Section VII-D`) and is
literal text in `paper.md`, rewritten by `paper/scripts/ieee_conventions.py`.
That script is the one-shot migration, kept for the record. Every pattern it
matches is a pre-migration form, so re-running it on converted source is a
no-op; the pre-migration text is in `paper/_pre_ieee_backup_20260813/`.

The poster's two result tables now read from CSV (they were hard-coded and
had silently drifted). If you add numbers to the poster, wire them to the
CSVs rather than typing them.

## Open items

1. **An external set that varies the photographic setting.** This is now the
   most valuable missing evaluation, ahead of the counterfeit-labelled set,
   and it is cheaper. The completed attention audit shows both frozen
   backbones justify "authentic" by the *background*, and Split C and Split D
   share one dark backdrop — so neither existing external set disturbs that
   cue. Photographs against varied surfaces, in hand, or in uncontrolled
   conditions would test it directly.
2. A content-aware attention measure — Grad-CAM mass inside an annotated
   product box — would separate the two readings Section VI-G leaves open.
   The border-mass metric there is complete but purely radial.
3. Re-running the two `experiment_*_all_models.py` ablations would make
   their absolute values comparable to production (their within-run
   comparisons are already valid, and the paper says so). These are now the
   only remaining conditions in the paper that predate the seeding fix.

**Do not re-tune the pipeline on external score.** Two sweeps have now found
settings that beat production on Split C — a 96 px short side (0.873 vs
0.820, Table S14) and the R, C, B composition order (0.880 vs 0.820,
Table 10). Both were deliberately left unadopted, and the paper says why in
Sections VII-A and VII-B: selecting preprocessing by its external score is
exactly the target-distribution leakage the Limitations section warns about,
and the production settings were fixed before either sweep existed. Adopting
them would trade a defensible claim for a bigger number.
4. A counterfeit-labelled external set remains the single most valuable
   addition, and would change what can be claimed.
5. A second annotator for the attention audit. Section IX discloses the
   single-annotator limitation, and `scripts/21_build_gradcam_review.py`
   already produces the tool, so a second pass is cheap.
6. **The product-box annotation pass, which is the cheapest open item and
   settles a live disagreement.** Grad-CAM and occlusion disagree about
   whether M4's correct external answers rest on the background (Section
   VI-G), and the border-mass statistic cannot referee it because it is
   radial: it measures distance from the centre of the frame, not from the
   product. `scripts/23_build_product_box_tool.py` builds a drag-one-box-
   per-image HTML tool over the 150 Split C images (one drag, saves and
   advances; about five minutes), and `modeling/attention_in_box.py` turns
   the exported CSV into an area-normalised concentration ratio for both
   attribution methods, split by outcome. Nothing else is needed.
7. Re-running the ordering and per-axis ablations across seeds. Section
   S-I-U measures seed variance for the production and baseline conditions
   only; the ablations remain single executions, which is defensible while
   their separations stay an order of magnitude above the variance measured
   there, and is worth revisiting if any of them is ever pressed.

The author block and biography were filled on 2026-08-13 and the poster's on
2026-08-28; the item that used to stand here saying otherwise was stale. The
`xxxx 00, 0000` publication date and the `10.1109/ACCESS.2026.DOI` on page 1
are the template's own fields, which IEEE fills at acceptance — leave them.

## Verify before submitting

```
python paper/scripts/metadata_oracle.py            # Table 5
python paper/scripts/provenance_audit_multi.py     # Table 6
python paper/scripts/cross_domain_audit.py         # Table 7
python paper/scripts/train_only_axis_derivation.py # Section VII-B's axes
python paper/scripts/power_and_leakage_bound.py    # the 9.2-point ceiling
python paper/scripts/external_intervals.py         # Tables 8 and 9
```

All are fast, read committed artefacts only, and reproduce the numbers of
record. The table numbers above replace the Roman ones this section used to
list, which predated the 2026-08-13 renumbering and no longer resolved.
Re-run and confirmed 2026-08-28.
