# Handoff — resume here

Rewritten 2026-07-30. Supersedes the previous version entirely, which
described a framing the paper no longer uses. Read this, then `README.md`,
then `paper/paper.md`.

## Sixth review round, 2026-09-01 -- two new experiments, reproducibility resolved

**The M-1 "reproducibility problem" was never a reproducibility problem, and
the pre-rewrite manuscript simply did not disclose it.** Its Table 6 caption
said only "Baseline is the production run immediately before three-way
normalization became the default"; the disagreement with the re-derivation
lived in S-I-U alone. The rewrite pulled it into the caption. Do not "restore"
the old caption -- the defect is older than the rewrite, only its visibility
was new.

**Two things were found while checking that, and both are fixed.**

  1. `paper/scripts/external_intervals.py` carried the archived counts as a
     **hardcoded `BASELINE_K` dict**. They were the only figures in the paper
     with no derivation from an artifact. The artifact existed all along:
     `modeling/results/split_c_eval_log.txt`, committed since the first commit
     and present in every Zenodo archive, records the full per-epoch curves and
     the four Split C accuracies. The script now parses it. `verify_crossrefs`
     was validating those counts by scraping that same dict -- i.e. against a
     transcription of themselves -- and now reads the log too.
  2. **The archived/current divergence now has an identified cause, per model.**
     Comparing epoch-0 trajectories under nominally identical seeds: M2 diverges
     large (0.6157 vs 0.5777) and is the one model whose LR the pre-fix script
     hard-coded at 3e-4; M3 and M4 diverge an order of magnitude less (0.4661 vs
     0.4680; 0.3821 vs 0.3788) and are the two models using the K=3 cached
     augmented passes, unseeded before the fix. The groups are disjoint and each
     shows exactly its own defect's signature. Also explains why M4's archived
     5/150 sits *outside* the 9-20/150 training-seed spread: the seed sweep does
     not vary the augmentation scheme. The archived run is now **superseded**,
     and Table 7 reports both columns from the current pipeline at seed 42
     (M3 100/150, M4 9/150). Headline moved 3.3% -> 6.0%.

**Two new experiments, both approved by the author, both in `modeling/`:**

  * **`region_substitution.py` -> Table 10.** Overwrite one region of the input
    and re-evaluate. Area-matched halves (0.5025 vs 0.4975), two fills.
    **Destroying the outer half costs 22-50 points of external specificity;
    destroying the area-matched centre costs nothing or helps** -- in all eight
    model x split x fill combinations. This **identifies M4's cue**, which
    occlusion could not, resolves the Grad-CAM/occlusion disagreement in
    Grad-CAM's favour, and turns "eliminating one provenance signal can expose
    another" from Supported into Demonstrated. Intact rows reproduce the values
    of record exactly.
  * **`experiment_train_only_operator.py` -> Table 11.** The operator the
    train-only rule of S-I-S actually nominates (R->B->W->C, including the
    marginal colour-balance axis) run for all three models. **External
    specificity is higher than the reported operator's for M2 (+6.7) and M3
    (+4.7), lower for M4 (-4.0); mean 0.842 vs 0.818.** So the recovery is not
    an artifact of having seen Split C. It also **corrects a claim that had
    rested on M4 alone** -- white balance was ruled out on M4's -4.0, and it
    helps the other two. M4's rows reproduce the committed colour-balance
    ablation exactly, which validates the new harness.

**Also fixed: a real error.** Section VI-D said M2's 0.463 on Split D was
"barely above the rate obtained by calling everything counterfeit". On an
authentic-only set that rate is 0.000. It now reads "marginally below the 0.500
a coin flip would return".

**Other reviewer items:** causal language softened throughout (association +
intervention, never the full chain); an explicit bound on what an authentic-only
design can support, including that a degenerate always-counterfeit classifier is
indistinguishable from a shifted-threshold one on this data; and **Section V-G,
the audit stated as a numbered procedure** with inputs, six steps, and what each
output licenses.

**Manuscript is 23 pages** (was 21); `final_sweep`'s page gate was raised 21 ->
23 with the reason recorded in the script. Note the IEEE Access overlength
charge applies per page beyond the tenth.

## Fifth review round, 2026-08-31 — all four conflict flags resolved, v1.2.0 cut

The rewrite in `ieee_access_rewrite_20260830/` was **promoted into `paper/`**,
which is again the single build tree. That folder now holds only the working
record: the diagnosis, the reviewer audit, and `MANUSCRIPT_rewritten.md`, which
is *generated* by `paper/scripts/mirror_authored_copy.py` and must not be
hand-edited — hand-editing it is how it drifted 18 pages behind.

**The four conflict flags are gone, each resolved against a committed artifact:**

  * **M-1** (Table 6 vs. Table 7 baselines). The **archived run is retained as
    the historical value of record**, labelled as such in the caption of what
    is now Table 7, and quoted as 3.3% throughout; the five-seed re-derivation
    of Table 8 is the value used for every sensitivity statement. The stray
    "6%" in Section VI-E is gone. `table_external_intervals.csv` re-derives
    104/150 and 5/150 exactly, so the archived column is still reproducible
    from a committed artifact — which is what settled the choice.
  * **M-2** (M4's Split B baseline). **0.905 confirmed**: `seed_sweep.csv`
    gives 0.9054 at every one of seeds 42–46, sd exactly 0.000. The stray
    0.919 came from a pre-seeding-fix ablation the paper itself declares
    non-comparable.
  * **M-3** ("at most 1.4 points"). **Scoped in both places** — Section VII-E
    and the Conclusion now give the seed-42 figure and the five-seed range
    (−3.0 for M2, +3.0 for M4) together.
  * **M-4** (cross-source overlap). **Committed figures adopted**: 202
    clusters, 2,665 of 4,027 Roboflow, 256 of 605 Kaggle, 42.3%, recomputed
    from `data/metadata/dedup_clusters.csv`. The old 229 / 2,900 / 290-of-661
    was computed on the pre-exclusion pool, which the repository does not ship;
    it is now named in the text and explicitly *not* the value of record.

**Also implemented, from a simulated reviewer pass.** Title shortened (the term
is now defined in Section I-A, not carried in the title). Specificity discipline
enforced: authentic-only sets are "external authentic-class specificity", never
"accuracy" or "external failure". A confirmatory/exploratory tier table opens
Section VI, and the normalization is characterised as one pre-specified operator
rather than a proposed algorithm. Split C→D is now "the device and lighting
shift these two capture conditions represent", never "generalizes across
acquisition". Section VI-E promotes occlusion to primary evidence and demotes
the single-annotator Grad-CAM categorization to corroboration. A five-row
summary of the multi-dataset audit came **back into the main paper as Table 6**
(reversing the 2026-08-29 cut of Section S-I-W, which stays in the supplement as
the full record) — this is the renumbering that moved Tables 6–9 to 7–10 in both
documents. "Shapley" is retired for "exact linear logit decomposition". A
notation box fixes y=0/y=1 in Section V-A, and a set-off statement in VI-A fixes
that the audit measures shortcut *availability*, not model behaviour. Prose
neutralised throughout per the reviewer's ~15–20% request.

**Template.** `ol{14}` and `\year{2026}` are now set in both build scripts;
the footer read "VOLUME 11, 2023" from the class default before. `\history` and
`\doi` remain the template's own placeholders, which IEEE fills at production.

**Manuscript is 21 pages** (was 19), supplement 32. All gates pass; the
geometric margin check gives a widest block of 178.06 mm against the class's
178.67 mm rule.

**Release.** v1.2.0 cut from this state. `README.md`, `CITATION.cff` and the
availability statement name it; earlier releases are marked superseded.

## Cut to 16 pages, 2026-08-29 (author instruction: at least four pages)

20 -> 16. What moved, and where it went:

  * **Section VI-B** (audit on the Roboflow archive) and **Section VI-C** (the
    seven-dataset pilot audit) are now **Section S-I-W**, in that reading
    order. Author called VI-C removable; VI-B followed because the two are one
    argument and splitting them across documents read worse than moving both.
  * **Section VII** (ablation study) is now **Section S-I-X**, and the main
    paper carries "VII. The Ablation Study, in Brief" -- every number retained,
    including the full ordering result; only the six-row table left.
  * **Figure 1** (distributions of the three confounded statistics) is now
    **Fig. S13**; Table 3 already carried its numbers.
  * **Table 3** (partition sizes) became a sentence pointing at Table S2.
  * The reproduction caveats left the availability statement for Appendix C.

**The trap this round: LaTeX auto-letters subsections.** Removing VI-B and VI-C
silently renumbered the rest of Section VI in the PDF (old VI-D..VI-G became
VI-B..VI-E) while the markdown headings and 25 cross-references still said
D..G. `verify_crossrefs` passed throughout, because it resolves references
against the markdown headings, not the rendered letters. Both were realigned by
hand. **If you relocate a subsection again, re-letter the remaining ones in the
markdown and re-check every `Section X-y` reference in BOTH files against the
compiled PDF.** A direct check is in this session's transcript: extract the
PDF text, collect `^[A-H]\. ` headings under each `^[IVX]+\. ` section, and
confirm every `Section X-y` reference resolves. Both documents return zero
dangling.

Main paper is now Tables 1-6 and Figure 1; the supplement is Tables S1-S23 and
Figures S1-S13, 30 pages.

## Supplement audit, 2026-08-29 — six defects found by reading it fresh

The supplement had drifted behind the manuscript. Nothing here was caught by
verify_crossrefs or final_sweep, which check reference resolution and float
numbering, not whether a sentence is still true.

  1. **A superseded number quoted as current.** Section S-I-S said gray-world
     white balance was "useless alone (0.107 external)". 0.107 is the
     pre-seeding-fix value that Section S-I-N itself supersedes; the corrected
     value is 0.067 (Table S12), which is what the main paper cites. Fixed,
     with the table named.
  2. **A broken cross-reference the gate cannot see.** Section S-II referred
     twice to "Tables S12, S14 and 10", meaning the ordering-permutation table.
     That table became Table 11 when Table 8 was inserted. The reference reads
     "and 10", so neither the shift nor the gate's `Table Sn` pattern touched
     it. Both fixed. **Watch for this shape whenever a main table is
     renumbered.**
  3. **An internal contradiction about M2.** Section S-I-G still said "M2
     remains the best-generalizing model" while Section S-I-Q says "what we no
     longer claim is that M2 generalizes best". S-I-G predates Split D. Reworded
     to say what the learning-rate correction actually did and does not.
  4. **A withdrawn claim stated as fact before its withdrawal.** Section S-I-J
     asserted the two backbones behave "identically" three times in the
     Grad-CAM subsection, and only narrowed it in the occlusion subsection
     further down. A reader in order gets the withdrawn claim. The three now
     mark it as the Grad-CAM reading and point forward.
  5. **A claim attributed to Section I-A that Section I-A no longer makes.**
     S-II said "Section I-A argues that asymmetric class sourcing makes
     provenance confounding the default". That was narrowed this same day.
  6. **A literal code fence in the PDF.** Appendix C's closing ``` was glued to
     the last command, so page 27 rendered "final_sweep.py```".

Also: Appendix C annotated 18_capture_method_stats.py as producing "Table 6,
Fig. S5"; it produces the brightness/resolution/file-size statistics behind
Table 4 and Fig. 1. And the manuscript said M2 and M4 move "at standard
deviations under 0.04" when M2's baseline sd is 0.103 -- it is the normalized
sds that are under 0.04.

## Third informal review, 2026-08-29 — shortened, claims narrowed

Implemented: the length cut (21 -> 20 pages), the prevalence narrowing, the
specificity discipline, the attribution softening, the normalization-as-probe
framing, and an explicit answer to the circularity objection. Details are in
commit 696bd56.

**Declined, with reasons** -- do not re-add without deciding these again:

  * **A heuristic audit-threshold table** (~0.5 / 0.6-0.8 / >0.9). The paper
    argues from its own data that no validated threshold exists: five scorable
    datasets is far too few for a false-positive rate. Printing invented
    numbers would contradict that and hand a reviewer a soft target. The
    operational guidance the reviewer wanted is already in Section VI-C and
    the Conclusion, and it is grounded: a high score on FORMAT is close to
    decisive because storage format is never a property of the photographed
    object, while size, resolution and aspect ratio mix acquisition with
    content -- which is exactly what the signature negative control shows at
    0.500 on format against 0.843 on size.
  * **A causal-story summary figure.** Costs a figure and roughly a third of a
    page in a round whose main purpose was cutting. Section I-A already states
    the chain in four sentences.
  * **A separate "Threats to Validity" subsection.** Section IX plus S-II is
    that section. Adding a third home for caveats is the repetition the same
    review objected to.
  * **A fine-tuning experiment.** Two consecutive informal reviews now ask for
    it, so expect a real reviewer to. It remains declined on the author's
    earlier decision and on CPU-only hardware; Sections V-B, IX and X state
    the limitation and both directions it leaves open. This is the most likely
    thing a submitted version gets asked for.
  * **Neutralising the remaining voice.** The review wanted phrases like "the
    check the field has institutionalized" made neutral. Repetition of those
    phrases was cut; the phrases themselves stay, per the author's standing
    instruction on writing style.

**Going below 20 pages means deleting evidence, not prose.** Everything
duplicative has now been cut across two rounds. The only remaining block of
the right size is Section VI-B, the audit's false-negative mode on the
Roboflow archive -- which is a contribution, not filler. Author's call.

**Zenodo is still unreleased and the manuscript still names v1.1.0.** Unchanged
from the previous section: cut v1.2.0 and update both DOI mentions before
submitting.

## Second informal review (ChatGPT), 2026-08-29 — leakage measured, prior art closed

A second informal review was run against the 20-page version. Three of its
claims were wrong on the facts and are recorded here so nobody re-investigates
them:

  * It said `README.md` reports v1.0.1 / doi:10.5281/zenodo.22151840 against
    the manuscript's v1.1.0. It does not; the README has said v1.1.0 /
    22166543 since the release was cut, with v1.0.1 marked superseded.
  * It said the footer's "VOLUME 11, 2023" is a stale template. It is
    hard-coded in `ieeeaccess.cls:525`, the class file is byte-identical to
    ACCESS_latex_template_20240429, and IEEE substitutes it at production.
    `final_sweep.py` already asserts it as an expected placeholder.
  * It said the normalization cannot be called zero-target-sample because
    Split C informed the axis choice. Section S-I-S already re-derives the
    same three axes from the training partition alone under a pre-declared
    threshold. A pointer to S-I-S was added at the point of use.

What was actually wrong, and what was done:

**1. The 9.2-point "analytic ceiling" over-reached, and is now a measurement.**
The old claim was that leakage "cannot inflate Split A test accuracy by more
than 7/76 for any model, seed or architecture". That bounds the recognition
channel only: admitting a mate into training also moves the parameters that
decide the other 69 predictions. And Split A and Split B do not share a test
set (230 of 510 images differ), so their delta was never a clean estimate.

`modeling/leakage_paired.py` (new) measures it instead. One fixed test set of
74 images; two training sets differing only in whether the 30 near-duplicate
mates are admitted, balanced by class-matched substitutes so both arms are 350
images with 167 counterfeit; identical validation set, architecture, learning
rate and augmentation. 28 test images are exposed (every one the pool admits),
46 unexposed, so the recognition and indirect channels are separated. Five
seeds, M2/M3/M4. Result: **M2 +0.3 points [-1.9, +2.4]**, +0.0 [-2.9, +2.9]
exposed, +0.4 [-2.2, +3.5] unexposed, McNemar p = 1.000; M3 and M4 unchanged
at every seed, but both at ceiling here (1.000, 0.987) so their null is weak
and Section S-I-V says so. The count survives as the "direct exposure rate";
`power_and_leakage_bound.py` was reworded to match. New Section S-I-V, Tables
S16 and S17 (the appendix tables shifted to S18/S19).

**2. DeGrave et al. was missing, and it is close prior work.** Added as [31]
(Nature Machine Intelligence 3:610-619, 2021) in Section II-B, with Torralba
and Efros as [32] for the dataset-bias framing. Both verified against
Crossref. NOTE: the review characterised DeGrave as combining positive and
negative classes from different source repositories. That could not be
verified -- the published full text is paywalled and Europe PMC serves no full
text for PPR213715 -- so the citation claims only what the abstract states
(reliance on confounding factors rather than pathology; failure at new
hospitals). Do not strengthen it without reading the paper.

**3. The abstract contradicted the body, twice.** It claimed normalization
restores the class to "77-86%", but Section VI-E concludes "we therefore claim
no normalization benefit for M3" and 77.3% is M3's. And it reported the 46%
Split D drop, which S-I-U identifies as the lowest of five seeds (0.627 +/-
0.135). Both fixed, and every downstream restatement (contributions 1 and 5,
VI-E, VIII-E, Conclusion) now agrees. Abstract is 250 words.

Smaller items: Table 8's last column relabelled a generalization gap, not a
normalization effect; Table 9's Change column labelled percentage points;
`p` was a bound rather than "approx 0"; Table 7's caption explains 2,224
listing entries against 661 unique images and calls itself a pilot audit;
product-identity groups named as a pHash proxy at first use; the
generative-AI disclosure moved into the Acknowledgment where IEEE Access asks
for it, with a pointer left in Ethics; "maximally learnable" and "bounds the
confound directly" softened.

**The paper is 21 pages, deliberately.** IEEE Access sets no page limit and
recommends under 20. The duplication that could go without losing an argument
already went this round: VIII-G reduced to a pointer at S-I-T, Future Work's
re-defence of the frozen probe removed (Section IX carries it), the
Conclusion's retelling of VI-E/F/G and VII-B compressed. What remains is
load-bearing. `final_sweep.py`'s gate was moved to 21 with the reason recorded
in the source, so it still catches unintended growth. Getting to 20 now means
deleting a results section -- Section VI-B, the audit's false-negative mode,
is the only candidate of the right size -- and that is a worse paper.

**Zenodo was deliberately NOT updated.** `modeling/leakage_paired.py` is new
code that produces a reported number, so v1.1.0 is no longer the exact state
of the code behind every number. Cut a v1.2.0 release and repoint the version
DOI before submitting, or at acceptance. The manuscript still names
doi:10.5281/zenodo.22166543 -- FIX THAT WHEN THE RELEASE IS CUT.

## Informal-review revision, 2026-08-29

An informal reviewer returned a Major Revision with eight major and five minor
concerns. Five of the eight were things the manuscript already stated, often in
the reviewer's own words -- generality conceded as a mechanism and not a rate
(I-A, VIII-H, IX, X), the external set as specificity rather than recall
(III-E, IX), power and single-run ablations (S-I-H, S-I-U), attribution as
suggestive (answered by the occlusion analysis, which contradicted part of the
Grad-CAM reading), and the shared backdrop (already the study's most
consequential gap). Those were left alone: the fix is a response letter, not
new text. Four things were actionable and are done.

**The mechanism is now separated from its neighbours in Section II-B**, which
is where novelty gets judged. The paragraph that used to say only "a difference
in cause" now says what shortcut learning, dataset bias and domain shift each
name, and what this is instead: a property of how a dataset was assembled, in
which acquisition correlates with the label WITHIN the training distribution,
before a model is fitted and without reference to a deployment distribution.
Three consequences follow that the neighbouring terms do not carry -- the
association can be complete rather than partial (1.0 here against incidental
and partial at [7]'s three hospitals), it is predictable from construction so
the population at risk is nameable in advance, and it survives leakage-aware
validation because every partition of one pool inherits it. Section VIII-F was
cut back to what only it says, since it had been repeating this.

**The target-distribution objection is answered where it arises.** Section V-D
now states, at the point the axes are introduced, that they were chosen after
Table 4 and that Section S-I-S re-derives the same three from the training
partition alone under a threshold declared in advance. It was previously only
in Limitations and the supplement, which is not where the doubt occurs.

**Exploratory and confirmatory analyses are now labelled.** Section VI says
which parts were fixed by the protocol before running and which were developed
after the external failure; Section S-I-F gives the full statement, including
which later analyses convert exploratory choices back into testable ones.

**Two rhetorical phrasings were neutralised**, and no more: the voice is
deliberate and "we would not deploy any of these models" is a substantive
claim, not a flourish.

**The title was kept.** The reviewer's objection is not to the words but to the
risk that a coined term invites "how is this different?" -- which Section II-B
now answers directly. Changing it again would also desynchronise the published
Zenodo record for no scientific gain.

**Page count.** The additions cost about 1,400 characters and were paid for by
consolidating what the supplement already carries in full: Section VII-A's four
headed paragraphs became two, Section VI-C's two middle readings became one
(which also answers the reviewer's minor point that secondary analyses crowd
the central one), and the no-redistribution statement stopped appearing in both
the Acknowledgment and the availability statement. Back to exactly 20 pages.

**No new Zenodo release was cut for this.** Nothing in `modeling/`, `scripts/`
or `paper/tables/` changed, so v1.1.0 remains the exact state of the code that
produced every number, which is what the manuscript claims of it. The
manuscript text has moved on in git; archive the accepted version at
acceptance, which is the normal point to do it.

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

## The fourth informal review, 2026-08-30

Thirty-nine numbered items, worked in the order the review itself proposed:
positioning, then methodological validity, then statistics, then transparency,
then language and compliance. Two new experiments, three new main tables, one
new main figure and two new supplement sections. The manuscript went 16 -> 20
pages with the additions and back to **18** by compression; nothing was
deleted to get there, only tightened.

### The one real internal contradiction, and what fixing it bought

The audit was described as needing "no pixel decoding" while its feature set
included **mean brightness**, which requires decoding the image. That is a
contradiction a reviewer would have caught, and the fix made the result
stronger rather than weaker. `paper/scripts/metadata_oracle.py` now fits two
families separately:

  * **header metadata** -- container format, encoded file size, stored
    dimensions and the aspect ratio implied by them. Readable from a listing
    and a header parse, no pixel decoded.
  * **low-level acquisition proxies** -- mean brightness, reported apart.

Measured, and now Table 5: format alone 1.000 / 1.000 (Split A / Split B),
encoded size 0.974 / 1.000, short side 0.947 / 0.946, aspect ratio 0.645 /
0.595, and **size + resolution + aspect ratio 1.000 / 1.000** -- so three
header fields, without even the file extension, reproduce the labels exactly.
Brightness alone is 0.829 / 0.716, the weakest candidate of the three despite
the largest t-statistic. Every "three acquisition scalars and no pixels" in
both documents is now "three header fields and no decoded pixels".

This also aligns the case-study audit with Table S20, which was already
header-only.

### New experiment 1 -- the paired baseline-vs-normalized test (review item 10)

`modeling/paired_external_test.py`, Section S-I-Z, Table S23. Table 6 reported
the correction as the distance between two Wilson intervals; the two conditions
are evaluated on the *same* 150 images, so the comparison is paired. The script
replays the persisted baseline and normalized checkpoints at all five seeds,
keeps the per-image verdict, and bootstraps over **images** so both arms move
together -- the construction of `leakage_paired.py`. It asserts every replayed
accuracy against `seed_sweep.csv` before writing anything.

    M2  Split C  0.051 -> 0.909   +85.9 [+81.7, +89.7]
    M2  Split D  0.176 -> 0.627   +45.1 [+39.9, +50.3]
    M3  Split C  0.715 -> 0.724    +0.9 [-6.9, +8.8]
    M3  Split D  0.644 -> 0.685    +4.0 [-2.7, +11.3]
    M4  Split C  0.100 -> 0.860   +76.0 [+69.9, +81.5]
    M4  Split D  0.240 -> 0.878   +63.8 [+56.9, +70.5]

**Do not quote the McNemar column as the primary statistic.** It pools
discordant pairs across five seeds, treating 745 verdicts as independent when
they are 150 images seen five times by correlated runs, so it deflates every
p. M3 on Split D is where that shows: McNemar 0.028 against a bootstrap
interval containing zero. The bootstrap is the one whose resampling unit
matches the design. Section S-I-Z says so in the text.

Also worth knowing: a seed-42-only version of this test returns +10.7 pp,
p = 0.023 for M3 on Split C -- a "significant" result that vanishes at five
seeds. That is the whole argument for keeping sampling uncertainty and
training-run variability apart, which Section IV-C now states explicitly as
three kinds of uncertainty.

### New experiment 2 -- the pHash threshold sweep (review item 15)

`paper/scripts/phash_threshold_sweep.py`, Section S-I-Y, Table S22. Costs
nothing: the canonical hashes are already in `dedup_clusters.csv`, so no image
is decoded. Re-clusters the 510-image pool at thresholds 0-16 and checks the
fixed Split A and Split B assignments against the result.

The justification for 8 that came out of it is an external one: **up to
distance 10 no cluster mixes the two class labels, at 12 three do, and at 16
the largest cluster holds 183 of 510 images.** The clustering never reads
labels, so that is evidence it does not use. Split A's countable leakage stays
between 2 and 18 clusters across the whole range, so nothing the split
comparison concludes turns on the threshold. And the honest limitation: at 10
six clusters would straddle a Split B partition and at 12 seventeen would, so
Split B's guarantee is a statement about distance <= 8, not about product
identity.

Clustering the pool alone gives 482 groups at threshold 8 where production
records 480, because production clusters Kaggle and Roboflow together and two
Kaggle pairs are joined through a Roboflow intermediary. Stated in the caption.

### Main-paper additions

* **Figure 1**, the mechanism diagram (`fig_mechanism` in `make_figures.py`),
  replacing the external-generalisation bar chart, which duplicated Table 6
  entirely and is now Fig. S13.
* **Table 3**, the complete training protocol, so reproducing Section VI needs
  no trip to the supplement. Table S2 is retitled as the same settings in the
  code's own names.
* **Table 7**, five-seed sensitivity, promoted from Section S-I-U.
* **Table 9**, evidence status: ten claims, each marked demonstrated, not
  established, or not measured, with a pointer. This is the cheapest thing in
  the round and probably the most reviewer-friendly.
* A formal statement in Section I-A: I(Y;A) > 0, complete when H(Y|A) = 0,
  with the case study as the complete case. Both equations are **unnumbered**
  on purpose -- numbering them would have shifted Eq. (1)-(10) and every
  reference to them.

### Language and claim strength

"Every such substitution introduces" -> "can introduce". "Wherever a binary
image task asks" -> "Where ... often ... where it is, the label can". Section
VIII-G no longer says the claim is causal in a way Section I-A had already
narrowed. "counterfeit stock is illegal to hold" -> difficult to obtain and in
many jurisdictions restricted. Table 1's audit column reads "not reported"
rather than "none", which is a statement about the paper and not about what
its authors did -- and is a regression the 16-page cut introduced. The
Raspberry Pi comparison no longer attributes any of the accuracy spread to
acquisition confounding. "The accuracy ceiling attributable to acquisition
alone is 1.000" is now the precise form: provenance alone predicts the label,
so in-distribution accuracy cannot establish that a classifier learned
packaging semantics -- sufficiency, not attribution.

Terminology: **attention -> attribution** everywhere (Grad-CAM and occlusion
are not attention mechanisms); **product-level -> near-duplicate-grouped**;
**external generalization -> external authentic-class specificity** in the
Section VI-C heading and Table 6's caption. The Shapley closed form is now
named for what it is -- an exact linear attribution decomposition -- with the
independent-feature assumption stated and the simplex constraint on histogram
bins acknowledged.

Title is now *Auditing Class-Conditional Provenance Confounding in Image
Authenticity Classification: A Counterfeit-Medicine Case Study*. Abstract
restructured to problem / method / finding / external evidence / implication,
253 words. Contributions reduced from five to three.

### What the review asked for and did not get, and why

1. **A genuinely untouched external dataset**, ideally two-class (items 6, 8).
   Not obtainable; Section III-E already documents the search. This remains
   the single most valuable missing experiment and Section X says so.
2. **Fine-tuning** (asked for by three consecutive reviews now). Declined on
   the author's earlier decision and CPU-only hardware. Flagged again as the
   most likely thing a real reviewer asks for.
3. **The operator-order ablation at 3-5 seeds** (item 13). Thirty training
   runs. The claim it supports is a 28-point separation between two groups of
   three, an order of magnitude past anything in Table 7. Recorded as a known
   limitation in Section S-I-U rather than run.
4. **Split C vs Split D as a paired comparison** (item 10, second half). The
   Mendeley archive ships no per-image product key and its two device folders
   do not share a numbering -- checked: Split C's indices run to 162 and Split
   D's to 226, with different gaps. The two sets cover the same 150 packages
   on the archive's own account, but cannot be aligned image by image. Section
   VI-D now says exactly that instead of "the same 150 products".
5. **The IEEE template artefacts** (item 35). `VOLUME 11, 2023` and
   `xxxx 00, 0000` are hard-coded in `ieeeaccess.cls`, which is byte-identical
   to the official template; `final_sweep.py` already asserts them as expected.
   Not a defect.

### Traps confirmed again this round

* **LaTeX auto-letters subsections.** Adding Section V-F was safe because it
  appends, but the check was run anyway: extract the compiled PDF's text,
  collect the `^[A-H]\. ` headings under each `^[IVX]+\. ` section, and
  resolve every `Section X-y` reference against *those*. Zero dangling in
  both directions (22 references from the manuscript, 15 from the supplement).
  `verify_crossrefs` still cannot see this class of defect.
* **Every figure is emitted as a full-width `figure*` at `width=\textwidth`.**
  The mechanism diagram was drafted as a tall 3.45-inch column, which LaTeX
  scaled up until it could not place the float and **dropped it silently** --
  no error, no caption, and `verify_crossrefs` passed. It was caught only by
  `final_sweep`'s docx-vs-pdf figure-numbering check. Re-laid 4 + 3 across the
  page at 7.2 x 2.62 in. The note in `build_tex.render_figure` says this;
  believe it.
* **Supplement float order.** Fig. S14 was inserted into Section S-I-U, which
  precedes Section S-I-W where Fig. S13 lived, so the captions ran 12, 14, 13.
  `final_sweep` catches it; `verify_crossrefs` does not.
* Heredocs in this environment mangle backslash escapes. Write patch scripts
  to the scratchpad with the Write tool. This bit twice again today, once
  turning `\n` inside a Python string literal into a real newline and
  breaking the file.

### Still blocking submission

**Cut a Zenodo v1.2.0 release.** `modeling/paired_external_test.py` and
`paper/scripts/phash_threshold_sweep.py` are new code behind reported numbers,
so v1.1.0 no longer matches. The manuscript's availability statement was
rewritten to cite the concept DOI (10.5281/zenodo.21936720) and "the release
accompanying this manuscript", which is true rather than misleading in the
meantime, but **README.md:16 and CITATION.cff still name v1.1.0 and
doi:10.5281/zenodo.22166543** and must be updated when the release is cut. The
author asked that Zenodo not be touched this round.

The poster PDF still shows the old subtitle; re-export from
`PharmaChecked_v2_poster.pptx`.

### Two supplement defects found by reading the compiled PDF, 2026-08-30

Both were invisible to every gate and had been shipping for some time.

**Every reference from the supplement to a main-paper table resolved to the
wrong table.** `crossrefs()` is shared between the two builders, so a bare
"Table 6" in `supplementary.md` -- which means *the manuscript's* Table 6,
since this document's own floats are written "Table S6" and pass through as
literal text -- became `\\ref{tab:6}`. The supplement labels its own tables
`tab:1..tab:25`, so the reference resolved inside the supplement and printed
**"Table S6"**: wrong number, wrong table, no error, and nothing in
`verify_crossrefs` or `final_sweep` looks at it. Twenty references were
affected, including the one opening the new Section S-I-Z. Equations already
had `resolve_dangling_eqrefs`; tables and figures did not.

Fixed in `build_supplement.py`, which now rewrites `\\ref{tab:n}` and
`\\ref{fig:n}` to literal numbers, and gated in `verify_crossrefs.py`
("no cross-document float refs survive as LaTeX refs"). The supplement's intro
now states the convention explicitly: unprefixed numbers point at the
manuscript, S-prefixed ones point within the supplement.

**The supplement's LaTeX title was two titles out of date.** `PREAMBLE` in
`build_supplement.py` still read *Asymmetric Class Sourcing Creates Provenance
Confounds in Authenticity-Classification Image Datasets* -- older than the
2026-08-29 retitle, and asserting the causal "Creates" the manuscript has
since narrowed to a mechanism. The markdown's own title line was stale too.
Both now match the manuscript. **The title lives in three places** --
`paper.md` line 1, `supplementary.md` line 3, and `build_supplement.py`'s
`PREAMBLE` -- and `final_sweep` checks only the first against the compiled
PDF. Change all three together.
