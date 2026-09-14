# Revision notes — reviewer-concern pass and final pass, 2026-09-13

This version of the manuscript (`ieee-submission-final/`) revises the earlier
submission state in `ieee-submission/` in response to a pre-submission review,
followed by a final pass of five targeted changes and a cut pass to 20 pages (both listed at the end). Table numbers below are the final ones: the balanced test is Table 3, the acquisition-shift test Table 4, region substitution Table 5 and the evidence-status table Table 6. Every
number, table, figure and experiment is unchanged; every limitation stated in
the earlier version is still stated. What changed is the framing of the
contribution, the scope of the generalization language, the prominence of
two limitations, the hierarchy between the audit and the exploratory
normalization, and the amount of qualification prose. The list below maps
each concern to the change, in the reviewer's numbering.

## 3. Novelty of the "new method"

The contribution is now stated as *formalizing and operationalizing* a
pre-training provenance audit and demonstrating it through a case study,
not as proposing a new methodology.

- Abstract: "we ... formalize and operationalize a pre-training provenance
  audit ... The audit is deliberately simple; a counterfeit-medicine case
  study shows its value."
- Section I, paragraph 3: the audit's ingredients are ordinary and it is
  not presented as a new statistical technique; what the paper specifies is
  when it runs, on which partition, on which variables, and how the score
  is read.
- Section I-B ("Contributions and scope") is rewritten as a bulleted
  contributions list in descending order of weight, with the audit first
  and the case-study finding second, and closes with a paragraph on what the
  study does *not* establish.
- Section II-C is retitled "Position of this work" and now opens with "The
  audit's ingredients are not new" before stating precisely what is added
  (the specification, and the follow-through showing that removing one
  provenance signal exposes another).
- Section VI opens with the same modest statement.

## 4. Generalization evidence

The generalization language is tightened throughout so that the mechanism is
presented as plausible and supported by examples, not established at
population level.

- Section I-A: "That condition is not peculiar to pharmaceuticals. In any
  two-class image dataset ..." became "There is no reason to expect that
  condition to be peculiar to pharmaceuticals. In a two-class image dataset
  ... typically ..."; "the condition therefore has a nameable population at
  risk, and it is not one collection" became "the same scarcity is plausible
  in other authenticity tasks ... while being clear that the direct
  evidence for the mechanism rests on [the case study]"; "two independent
  lines of evidence support reading it that way" became "two independent
  observations support that reading without establishing its generality".
- Section IV-A: the seven-archive screen is introduced with its sampling
  limitation in the same sentence, and its interpretation paragraph is now
  headed "The screen establishes that the audit discriminates, and nothing
  about prevalence."
- Section V-D: the limitation is restated in the reviewer's own terms —
  "The generality of the mechanism is plausible and supported by examples,
  not established at population level."
- Section VI, final paragraph: "What this study establishes is a case-study
  finding and a procedure, not a prevalence."
- Abstract: "how often the confound occurs is not established."

## 5. The authentic side of the balanced set is not verified

This is now named, in the paper's own words, "the principal limitation of
Table 3", and it is separated from the central audit result.

- Section III-D-1: the authentic-labeled reference class paragraph ends
  with "This is the principal limitation of Table 3" and states that the
  direction of any resulting bias is unknown.
- Section IV-C: the opening paragraph names the two properties that qualify
  the table (unverified authentic class; source rather than acquisition
  shift), and the closing paragraph says the specificity column "measures
  agreement with a label rather than with ground truth".
- Section V-D: a standalone limitation, "The authentic class of the
  balanced set is not verified, and this is the principal limitation of
  Table 3", which states explicitly that the central audit is unaffected
  and the balanced classification experiment is what the limitation
  weakens — the reviewer's own assessment.
- Table 6: the balanced-set row now reads "Demonstrated against an
  authentic-labeled, unverified reference class".

## 6. The missing experiment

Two-class performance under acquisition shift was already acknowledged as
unmeasured; it is now the first limitation in Section V-D and is shown as a
2 × 2 matrix (classes × acquisition) with the unfilled cell marked, so a
reader sees which half of the matrix each experiment occupies. Section I-B
names it among the three things the study does not establish, and Section
V-C's next-steps paragraph points at the matrix.

## 7. Outer-region vs backdrop

The cautious terminology is retained and made explicit. Section IV-E-2's
interpretation paragraph is now headed "What this establishes is
outer-region dependence, not backdrop dependence." Table 6's row reads
"depend on the outer region of the frame ... which property of that region
is not isolated" (previously "the photographic surround"). In the
supplement, "a backdrop-matching rule" became "a surround-based rule".

## 8. The normalization experiment as a distraction

The normalization is subordinated to the audit textually and structurally.

- The 86% / 81% figures are removed from the abstract; the abstract states
  only that the normalization "removes the audited statistics and leaves
  both corrected backbones depending on the outer region of the frame".
- Section I-B's exploratory bullet gives no percentages and states the
  normalization's role: to show that a correction is itself dataset
  construction.
- Section IV-E opens by saying both exploratory analyses "serve the audit",
  and Section IV-E-1 is cut from six paragraphs to three, with the
  composition-order and in-distribution-cost discussion reduced to one
  sentence each and the ablation detail left to the supplement.
- Section V-B is retitled "What the audit settles, and what it does not"
  and now opens with the audit; the normalization discussion is one
  paragraph within it.
- Section III-F's exploratory-status paragraph states that the operator is
  "an instrument rather than a proposal".

## 9. Defensive prose

Qualification language was cut wherever the same limitation was stated in
more than one place, with each limitation kept once — in Section V-D or
Table 6 — and stated plainly there. Examples of cuts: the one-sided-rule
paragraph in III-D, the fine-tuning discussion in III-C (now two sentences,
with the full statement in V-D), the monotonicity paragraph in III-E, the
exploratory-status paragraph in III-F, the tier discussion at the head of
IV, the "not a survey" paragraphs in IV-A, "What Table 3 does and does not
establish" in IV-C, the seed-42 paragraph in IV-D, three of the six
paragraphs of IV-E-1, the first two paragraphs of V-B, the "No published
two-class set" paragraph of V-D (background restated from III-D), and the
"What the external evidence establishes is correspondingly narrow"
paragraph of V-D (restated from IV-C/IV-D). The manuscript is about 600
words shorter than the earlier version at the same page count, with the
contributions list, the organization paragraph and the matrix added.

## 10. Size relative to the central contribution

The introduction now carries the five-step argument in order (Section I-B:
acquisition pipelines → metadata predicts the label → in-distribution
accuracy cannot establish authentication → external failure → removing one
confound reveals another), a contributions list, and an organization
paragraph. The exploratory material is shorter in the main text (see 8) and
its detail remains in the supplement.

## 11. Statistical power and ranking language

No architecture is ranked. "The best in-distribution model", "the strongest
model", "M2 leads", "M4 leads" and "the one that looked best" are replaced
with point-estimate statements ("the model with the highest in-distribution
accuracy", "has the highest point estimate here"). Section IV-C now states
that no pair of models in Table 3 is separated by more than sampling noise,
"so the table supports statements about point estimates and about chance,
not a ranking of architectures". Section V-D's power limitation says which
statement forms are supported and which are not. The supplement's three
ranking phrases were changed the same way.

## 12. AI-assisted screening

Section V-D now carries a limitation headed "AI-assisted eligibility
screening is not ground-truth labeling", stating that the screen decided one
thing only (is this a photograph, of a medicine package, of a current retail
product), that every class label comes from its source, that selection bias
from the screen could act only through which photographs survive and not
through their labels, that the brightness matching after the screen removes
the one acquisition statistic it could shift, and that the audit on the
finished set (0.620) bounds what remains. The counterfeit side's
corresponding single-reviewer screen is stated in the same paragraph. The
Acknowledgment disclosure adds: "That screen decided whether a candidate was
a photograph of a retail medicine package; it assigned no class label and
made no authenticity judgement." Section S-IX-B of the supplement says the
same.

## 13. Title

Unchanged: "Auditing Provenance Confounding in Image Authenticity
Classification: A Counterfeit-Medicine Case Study".

## Style

The introduction follows the IEEE Access convention of a contributions list
and an "organized as follows" paragraph; section openers state what a
section establishes before the evidence; results paragraphs lead with the
finding and follow with the qualification once. No text from any other
article was used.

## Verification

Both gates (`verify_crossrefs.py`, `final_sweep.py`) pass; the abstract is
246 words; the manuscript is 22 pages and the supplement 37; the LaTeX
source in this folder compiles standalone to text-identical PDFs.

## Final pass (five targeted changes)

1. **Novelty claim.** Already stated as *formalize and operationalize*; no
   sentence in the paper now presents the audit as a new ML technique.
2. **Central result impossible to miss.** A bold paragraph in Section I
   ("The central result is easily stated. ... all 510 labels are
   predictable from container format alone ... High internal classifier
   performance on this dataset therefore cannot be interpreted as evidence
   of object-level authentication") and the same two sentences open
   Section IV-A.
3. **External-validation limitations explicit.** Section III-D now carries a
   side-by-side table of the three evaluations — classes held, what shifts,
   what is standardized, how labels are established (regulator-confirmed
   vs labeled-not-verified vs authentic-only), and what each can measure —
   followed by one sentence stating that the balanced test and the
   acquisition-shift test are not two versions of one experiment.
4. **Defensive language.** A further round of cuts: the seed-sensitivity
   caveat is stated once (IV-D) rather than in III-B as well; the leakage
   summary in IV-B no longer restates the previous paragraph; V-B no
   longer restates the outer-region finding of IV-E; V-D no longer has two
   "most consequential" gaps; a duplicated "not a property of the
   photographed object" was removed from the cross-domain table's caption (that table has since moved to the supplement). The manuscript
   is about 1,200 words shorter than the original submission state at the
   same page count.
5. **Normalization and Grad-CAM secondary.** The Grad-CAM equation and its
   description were moved out of Section III-G (one sentence remains,
   pointing to Section S-I-J), the Grad-CAM paragraph closing Section IV-E
   was removed (its content is in Section S-I-J), and the exact-logit
   decomposition is now Eq. (9). Nothing in the main text presents the
   normalization as a proposed solution; Sections III-F, IV-E and V-B each
   say it is an instrument.

The whole manuscript was then read once more in its rendered form; two
slips found in that read (a dangling "It" in the availability statement and
one remaining "photographic surround" in Table 6) were fixed. Both gates
pass; 22 pages; abstract 247 words.

## Cut pass to 20 pages (final)

Requested edits applied verbatim or nearly so: the two abstract sentences;
"This literature's methodology motivates our approach"; "Missing is a
pre-training check, run solely on the files..."; the "organized as follows"
paragraph removed; "This asymmetric class availability is not peculiar to
pharmaceuticals"; "Let $A$ represent file acquisition variables, divided into
two types"; the narrative opening of I-B replaced by "We evaluated how much
reported accuracy survives methodological correction using..."; "Two
verifiable properties of the primary source must be noted"; the Roboflow
paragraph condensed to the modality-confound finding; the IV-A opener
"All 510 labels are predictable from container format alone: 272/272
authentic files are .jpg photographs and 238/238 counterfeit files are .png
screenshots"; the Table 4 reading conventions moved into its caption;
Section V-D rewritten as a bulleted list in active voice ("This study does
not measure two-class performance under acquisition shift"), absorbing the
caveats that had been in V-B.

Structural cuts that paid for the pages: the cross-domain summary table
(formerly Table 3) left the main text — its numbers are quoted in prose and
it lives in the supplement as Tables S18 and S20; the five-seed table
(formerly Table 6) moved to Section S-I-U; the metric-terms table and the
evidence-tier table became prose. Prose trims of restatement in II-A, II-B,
II-C, III-C, III-D, III-E, IV-A, IV-B, IV-D, IV-E, V-A, the Acknowledgment
and the availability statement. The manuscript is 20 pages (17,700 rendered
words, from 19,900 at v1.4.1); a 19th page would require removing Fig. 1 or
the practitioner checklist, or about 600 further words of substantive text.

