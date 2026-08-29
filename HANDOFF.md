# Handoff — resume here

Rewritten 2026-07-30. Supersedes the previous version entirely, which
described a framing the paper no longer uses. Read this, then `README.md`,
then `paper/paper.md`.

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

Title: *Asymmetric Class Sourcing Creates Provenance Confounds in
Authenticity-Classification Image Datasets: Detection, Cost, and Partial
Repair.*

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

**One item still needs the author and cannot be done here:** a public
DOI-bearing repository (a placeholder in Data and Code Availability says so).
The project is not yet a git repository at all. A second annotator for the
attention audit also remains open; `scripts/21_build_gradcam_review.py`
already produces the tool, so a second pass is cheap.

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
