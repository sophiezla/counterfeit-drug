# Editorial review and targeted revision — 2026-09-23

Target: `mdpi-diagnostics/manuscript.md` (the Diagnostics reorganization, after
the 2026-09-22 writing pass). The pre-edit files are kept beside it as
`_pre_2026-09-23_manuscript.md` and `_pre_2026-09-23_supplementary.md`.
Nothing scientific changed. Section 6 lists every place where a claim or a
label moved.

---

## 1. Overall assessment, read straight through

The scientific story is sound, and it is still visible. A reader who gets
through the abstract and Section 3.1 understands the paper: every counterfeit
file is a PNG screenshot and every authentic file a JPEG photograph, so the
labels can be read off the file listing, and the rest follows. That is a
strong, simple, verifiable finding. The external evaluations are designed
with unusual care, the one-sided and two-sided tests are kept apart
correctly, and the limitations are honest. A reviewer at *Diagnostics* would
not doubt the central result.

What slows the reader down is not the density of the methods. It is that the
paper argues with itself. Many paragraphs state a result and then spend two
more sentences on what the result does not mean. Often those sentences repeat
a qualification the reader already has from Methods, a table caption, or the
previous paragraph. Examples of the pattern are "This is not an artifact of
our filtering", "does not establish ...", "not a comparison", "not a remedy",
"which is weaker than ...", and "What this establishes is ...". The
2026-09-22 pass removed the worst of the meta-headings and em dashes, but the
underlying rhythm is still there. It is most noticeable in 1.2, 3.4, 3.5 and
the Discussion.

Organization. The Introduction was doing three jobs: motivating the problem,
defending the novelty of "provenance confounding" against every neighboring
term, and previewing the Results. The seven-archive screen, the 6.8-point
leakage figure, the 9/150 result and the PNG/JPEG finding all appeared in 1.2
and 1.3 before the reader reached Methods. The Discussion had the reverse
problem. Sections 4.3 and 4.4 mostly re-narrated 3.3 to 3.5, and 4.6 restated
limitations already stated in 2.5, 2.9, 2.10 and 2.12.

Contribution hierarchy. The primary contribution (the audit) was stated
clearly, but 1.3 then listed four further findings with section pointers. The
Discussion also introduced a five-type defect taxonomy (Types A–E) that
nothing else in the paper uses. Together these made the secondary analyses
read like separate contributions.

What reads as AI-assisted. Three things, in order of how much they
contribute. (1) Anticipatory qualification: the reader is told what a number
does not mean before being given a reason to think it might. (2) Symmetric
contrast sentences ("X removes a partitioning fault; provenance confounding
is a property of the pool itself"). Each one is fine on its own, but they
make up too much of the text. (3) Over-signposting of the reader's attention:
"carries this paper's second main finding", "deserve comment", "the column to
read first", "More importantly". The formal apparatus in 1.2 ($I(Y;A)>0$,
$H(Y\mid A_{\mathrm{pure}})=0$) also reads as sophistication for its own sake,
because nothing later uses it.

Credibility risks a reviewer would find. There are six small factual or
consistency problems (Section 2, Priority High, and Section 6). The most
visible is in 3.4, where M1 "has never once answered 'authentic'", but its
confusion matrix has FN = 2. Another is Table 7, which called
"correcting one provenance signal can expose another" *demonstrated*, while
3.5.2 itself says the feature inside the outer region is not isolated.

What would most improve it. Keep the numbers and the limitations exactly as
they are, and state each qualification once, in the place where the reader
first needs it. Move the formalism and taxonomy out of the way. Let the
Results end when the finding is clear. The revision in Section 5 does this.

---

## 2. Priority revision table

| Priority | Section | Problem | Why a human reviewer would notice | Recommended action (taken) |
|---|---|---|---|---|
| High | 3.4 | "a classifier that has never once answered 'authentic'" — M1's FN = 2, so it answered "authentic" twice, both wrong | A reviewer checks the confusion matrix beside the sentence | Corrected to "never once answers 'authentic' correctly" |
| High | Table 7 | "Correcting one provenance signal can expose another" marked *Demonstrated*, while 3.5.2 says the feature inside the region is not isolated | Status and text contradict each other | Changed to *Supported on this dataset*, with the reason. **Author to confirm** |
| High | 2.4 / 3.1 / 4.6 | Three different counts of scorable archives: "five scorable datasets" (2.4), "Four of the seven were scorable, including the case study" (3.1), "six further archives …, four of which were scorable" (4.6). The last two contradict each other | Arithmetic a reviewer can do | **Flagged, not changed.** The inconsistent limitation sentence was dropped during consolidation. 2.4 and 3.1 remain; author to reconcile "five" |
| High | 1.2–1.3 | Introduction previews Results (seven-archive screen, 6.8 points, 9/150, PNG/JPEG) | The reader meets the findings twice before Methods | Previews removed; the seven-archive result lives in 3.1 only |
| High | 1.2 ¶4–5 | Two paragraphs distinguishing provenance confounding from every neighboring term | Reads as defending the novelty of a phrase | Merged into one paragraph that keeps the precedents and the single real distinction (cause, hence detectability in advance) |
| High | Discussion | 4.3 and 4.4 re-narrate the Results; taxonomy of Types A–E introduced late | Discussion repeats the tables | 4.3 and 4.4 merged into one interpretive section; taxonomy reduced to one sentence pointing to S-I-T |
| High | 2.9 | The authentic-labeled caveat came in the 5th paragraph of 2.9 | It is the balanced test's main limitation and should come first | Moved to the first paragraph, with "not a gold-standard authentication benchmark" |
| Medium | 3.5.2 | "outside the middle of the frame, which is where the packaging is"; "the models … have not stopped depending on acquisition. Both now depend on a different acquisition-linked cue" | Stronger than region substitution shows, which is the paper's own point in the next paragraph | Softened to "where the packaging is usually placed"; the acquisition interpretation moved to 4.3 as "the most plausible reading" |
| Medium | 4.1 | "the metadata audit, which is not an accuracy at all" | Contradicts 2.4 ("The score is the held-out accuracy …") | Clause removed |
| Medium | Abstract | Methods sentence lists parameter counts and group counts; nothing says the audit measures availability, not use | First-pass readability; key interpretive point missing | Inventory removed; availability-not-use sentence added |
| Medium | 3.2 | "no paired test exists" for Split A − B stated in 2.7, 3.2 ¶1 and 3.2 ¶2; "The internal results stay high because …" in 3.2 and 4.2 | Repetition | Once in 3.2 ¶2; interpretation left to 4.2 |
| Medium | Tables 4, 5 captions | Caption for Table 4 repeated 2.8 and 2.11. Caption for Table 5 editorialized ("the column to read first") | Captions read as argument | Trimmed; the archived-run disclosure kept in full |
| Medium | Limitations | 9 topics across 7 long paragraphs; reproducibility defects and "no partition can decorrelate" repeated from 2.5/2.12 | Length; repetition | 7 paragraphs, each stated once; repeated items point back |
| Medium | 2.10 | Exploratory status qualified again in 3.5, 4.4, 4.6 | Repetition | Stated fully once in 2.10 (including "not a domain-adaptation method" and "specificity ≠ packaging recognition"); later sections point back |
| Low | 1.2 | Information-theoretic notation unused later | Unneeded machinery | Removed; $A_{\mathrm{pure}}$/$A_{\mathrm{mix}}$ kept (used in 2.4, 2.9, 3.1, 4.4) |
| Low | 2.1 | "The technical split labels A to E are retained in this section, in the reproduction appendix and in the supplement" — but Results use Split A/B throughout | Inaccurate signpost | Rewritten: "The split labels A to E follow the code and the supplement" |
| Low | 2.3 | "'product identity' is reserved for the field name in the code", yet the text says "product-identity groups" throughout | Inconsistent terminology rule | Rule dropped; sentence now says the clusters approximate product identity |
| Low | 2.6 | Justifications (GAP vs. flatten, why freeze, why M1 is unaugmented) longer than the definitions | Methods as advocacy | Each cut to one sentence; S-I-Q carries the rest |
| Low | 4.5 bullets / prose | Bold run-in labels, bold used for emphasis | Excess bold | Prose bold 30 → 20 runs (remaining: section structure, model run-ins, the defined term, table/figure labels, abstract headings) |
| Low | 1.2 | "*Hidden stratification* [11]" — [11] is Zech et al.; the term is from Oakden-Rayner et al., and [13] (Seah et al.) uses it in its title | Citation accuracy | Sentence removed during consolidation, so the issue no longer appears; noted in case the author restores it |

---

## 3. Line-level editorial targets

Quotes are from the pre-edit text. The categories are the ones in the brief.

1. **Abstract, Methods:** "…and trained four model families, spanning a 97-parameter logistic regression to frozen ImageNet backbones, under a naive and a near-duplicate-grouped split." — *unnecessary detail, readability*. Drop the inventory. Add that the audit shows availability, not use.
2. **1.1 ¶2:** "The concern is therefore not that a widely shared benchmark is broken, but that a dataset assembled the way this sub-field routinely assembles them…" — *AI-like phrasing, reviewer-proofing, mild overclaim ("routinely")*. Delete. The facts before it make the point.
3. **1.1 ¶2:** "Every study we identified built or adopted its own image set…" — *overclaim risk*. Tie it to "the five studies located by our search" and keep "targeted, not systematic".
4. **1.1 ¶3:** "The way the counterfeit class is usually constructed…" — *overclaim* ("usually", from two studies). Change to "In the located studies…".
5. **1.1 ¶3:** "…so this is a direction worth noting and not a comparison." — *excessive qualification*. Keep the caveat as a subordinate clause.
6. **1.2 ¶2:** "Confounding arises when … $I(Y; A) > 0$. The extreme case … $H(Y \mid A_{\mathrm{pure}}) = 0$" — *terminology, unnecessary detail*. Say it in words. The notation is never used again.
7. **1.2 ¶2:** "That accuracy is a lower bound, up to sampling error…" — *Methods detail*. Move it to 2.4.
8. **1.2 ¶4:** "Related ideas are well established, and provenance confounding is best understood as…" plus the term list "*Hidden stratification* [11], *source confounding* and *metadata leakage* name statistical properties…" — *terminology, reviewer-proofing*. Keep the precedents and drop the taxonomy of names.
9. **1.2 ¶5:** "What distinguishes provenance confounding from these terms is its cause…" — *repetition, defensive novelty*. Fold it into ¶4 as two sentences. The "incidental … but exact" contrast stays in 4.2, where it does work.
10. **1.2 ¶6:** "Two observations place the mechanism outside this dataset without establishing how common it is." — *Results/Discussion boundary*. Keep Grommelt [18], which is literature, and leave the seven-archive result to 3.1.
11. **1.3 ¶2:** "Correcting the split changed in-distribution accuracy by at most 6.8 points. External evaluation was a different matter…" — *repetition (mini-Results)*. Replace with two plain sentences and no numbers.
12. **1.3 ¶3:** "The gap this exposes is procedural rather than architectural. … it is not a new statistical technique. … No new architecture is proposed." — *AI-like not-X-but-Y, excessive qualification*. Keep one sentence: the ingredients are ordinary, and what is specified is when and how.
13. **1.3 ¶4:** "The main contribution is the audit … The case study supplies the rest…" — *unclear hierarchy*. Label the case study explicitly as supporting evidence.
14. **1.3 ¶5:** "Three levels of evidence are separated throughout…" — *apparatus*. The definitions already sit in Table 7's caption. Keep only the prevalence sentence.
15. **2.1 ¶3:** "The technical split labels A to E are retained in this section, in the reproduction appendix (Section S-V) and in the supplement." — *unclear logic (inaccurate)*. Rewrite it.
16. **2.1 ¶3:** "The two external evaluations answer different questions. The balanced test holds both classes…" — *repetition of Table 1*. Delete.
17. **2.3:** "…so the resulting design is called a near-duplicate-grouped split throughout, and 'product identity' is reserved for the field name in the code." — *terminology*. The rule was not followed, so state the limitation and drop the rule.
18. **2.4:** "We publish no threshold, because five scorable datasets…" — *numerical inconsistency* with 3.1. Flagged.
19. **2.5 ¶1:** "This is the protocol in general use on data of this kind, and the only one available…" — *overclaim*. Say "the design available to a study that adopts a shipped partition", and tie it to Table S26.
20. **2.6:** "The GAP head replaces the flatten-then-dense head that small-dataset CNN work commonly uses" / "Freezing also reflects the shortcut as it is available to a practitioner…" / "…acting as label noise rather than as the spatial-filter regularizer they are for a CNN." — *Methods justification*. Cut each to one clause.
21. **2.8 ¶2:** "Content is held approximately fixed while capture varies, so a model that holds its specificity from C to D is stable across…" — *Results/Discussion boundary*. State the design only.
22. **2.9 ¶5:** "The two classes are not established on the same footing…" — *placement*. Move it to the top of 2.9 and add "not a gold-standard authentication benchmark".
23. **2.9 ¶6:** "…and the size and resolution components of $A_{\mathrm{mix}}$ go with them." — *unclear logic*. Encoded size is not standardized (it is the residual axis, 0.598). Changed to "stored resolution, one component of $A_{\mathrm{mix}}$". **Author to confirm.**
24. **2.9 ¶6:** "This is dataset construction, not model preprocessing." — *not-X-but-Y*. Rephrase it positively.
25. **2.10:** "These are attribution analyses, not attention analyses, since neither probe involves an attention mechanism." — *reviewer-proofing*. Delete.
26. **2.11 ¶2:** "Three kinds of uncertainty are kept apart. Sampling uncertainty is … Training-run variability is … Distribution-shift uncertainty is…" — *AI-like triad*. Compress it to three plain sentences.
27. **3.1 ¶4:** "Three of Table 3's rows deserve comment." — *meta-signposting*. Delete and give the rows directly.
28. **3.1 ¶5:** "A screen that fires on every dataset carries no information, so…" and "…and none is made." — *reviewer-proofing*. Start with the procedure and keep the no-prevalence sentence once.
29. **3.2 ¶2:** "Those deltas settle less than they appear to." — *rhetorical*. Replace with a plain topic sentence.
30. **3.2 ¶4:** "The internal results stay high because the internal grouped test inherits…" — *Results/Discussion boundary, repetition with 4.2*. Remove it from Results.
31. **3.3:** "The baseline column carries this paper's second main finding." / "This is a near-complete inversion on the easiest available external case…" / "…has not learned to recognize authentic packaging." — *signposting, mild overclaim*. State the numbers, then "consistent with recognizing this dataset's photography … rather than authentic packaging".
32. **Table 5 caption:** "it is the column to read first, being the one quantity a shifted operating point cannot inflate." — *editorializing*. Delete (2.1 already explains it).
33. **3.4:** "…describes a classifier that has never once answered 'authentic'." — *factual error* (FN = 2). Fix it.
34. **3.4 last ¶:** "Table 5 shows that these models, evaluated on independently sourced photographs…" — *repetition*. Delete.
35. **3.5.1 ¶3:** "They are stable across the device and lighting shift these two conditions represent, which is weaker than generalizing across acquisition… A model applying such a rule would hold its specificity across exactly this shift." — *excessive qualification, forward reference*. Keep one qualifying sentence.
36. **3.5.2:** "…lies outside the middle of the frame, which is where the packaging is." — *overclaim* (the next paragraph says the carton can extend past the center). Soften it.
37. **3.5.2:** "What this establishes is dependence on the outer region, not on the backdrop specifically." — *meta-heading in prose*. Make it a plain topic sentence.
38. **3.5.2 last ¶:** "More importantly, the models corrected by Equation (8) have not stopped depending on acquisition. Both now depend on a different acquisition-linked cue…" — *overclaim, Results/Discussion boundary*. Keep the observation in Results and move the interpretation to 4.3 as "most plausible reading".
39. **4.1 ¶1:** "This does not imply that earlier work in this area was careless." — *defensive*. The Acknowledgments already say it. Delete. Also "the metadata audit, which is not an accuracy at all" contradicts 2.4.
40. **4.4 ¶3:** "That iteration is needed because provenance confounding is not one defect but a small family… **Type A** … **Type E**…" — *terminology, unnecessary detail, inflates secondary work*. Reduce to one sentence and point to S-I-T.
41. **4.5 ¶3:** "Two questions would have been decisive for a reviewer of work using this dataset…" — *reviewer-proofing*. State the practice directly.
42. **4.5 ¶4:** "…fill the cell of the evidence matrix that no experiment here reaches." — *unclear logic*. The matrix was removed in an earlier revision. Say what the set would measure.
43. **4.6:** "Three narrower constraints complete the picture." — *repetition*. "No partition can decorrelate acquisition" duplicates 2.5 and 4.2, and the reproducibility defects duplicate 2.12. Keep frozen backbones and the leakage-free scope.
44. **Conclusions:** "Independently acquired photographs showed the consequence, with the strongest internal model recovering 6.0%…" — *repetition of numbers*. Replace with a statement of what the study shows and add the non-validation sentence.

---

## 4. Section-level restructuring plan (as carried out)

**Abstract.** Keep the problem, the audit, the four headline results and the conclusion. Remove the model and group inventory. Add that the audit measures availability. 276 → 269 words.

**1 Introduction.** Keep 1.1 and 1.2's definition, the Figure 1 paragraph and the precedents. Shorten the 1.2 formalism to words. Combine 1.2 ¶4 and ¶5 into one paragraph. Delete the seven-archive preview (it stays in 3.1) and the 1.3 Results preview. Move the three evidence levels to Table 7's caption. 1,840 → 1,397 words.

**2 Methods.** Keep all counts, rules, model definitions, equations, splits, external-set construction, statistics and the AI disclosure verbatim. Shorten justifications in 2.3, 2.6, 2.8, 2.10 and 2.11. Reorder 2.9 so that the label caveat comes first. Make 2.10's exploratory paragraph the single full statement of the normalization's status. Nothing moved to the supplement, because the supplement already holds the longer justifications (S-I-Q, S-IX-A, S-I-S). 5,163 → 5,001 words.

**3 Results.** Keep every table row unchanged. Trim the captions of Tables 4 and 5. Delete meta-sentences, the repeated caveats, and the interpretive endings of 3.2, 3.4 and 3.5.2. Fix the M1 sentence. 3,193 → 2,822 words.

**4 Discussion.** Now five subsections:
4.1 main finding (with the falsifier);
4.2 why internal validation failed;
4.3 what the external and exploratory analyses show (old 4.3 + 4.4, taxonomy reduced to one sentence);
4.4 implications (old 4.5; bullets unbolded; future-work paragraph clarified);
4.5 limitations (old 4.6, 7 paragraphs).
Limitations stays its own subsection rather than being folded into 4.4, so that the supplement's six pointers to it still land on a heading. 2,714 → 2,177 words.

**5 Conclusions.** Three short paragraphs: what was shown, what the audit contributes, what remains unknown. 193 → 207 words. The previous version was already short. The added length is the non-validation sentence and the "what remains unknown" paragraph the brief asked for.

**Supplement.** Only cross-references changed: main-text Section 4.5 → 4.4 (1 place), 4.6 → 4.5 (5 places), and one pointer in the normalization-ablation discussion (the "outstanding acquisition" sentence) re-aimed at 4.4, where the future-work paragraph now sits. It was diff-verified: no other byte changed.

---

## 6. Final quality-control audit

**Changed substantially.** Introduction 1.2 and 1.3; 2.9 (order); Results 3.2, 3.4, 3.5.2 (endings); Discussion 4.1 to 4.4 (merged and compressed); Limitations; Conclusions.

**Left mostly unchanged on purpose.** 1.1 ¶1; 2.1 (except two sentences); 2.2; 2.4 procedure; 2.5 ¶2–3; 2.6 model definitions and training; 2.7; 2.12 (reproducibility and AI disclosure, verbatim); 3.1 ¶1–3 and ¶6; 3.3 seed paragraph; 3.5.1 ¶1, ¶2, ¶4; all equations; all table bodies except three Table 7 cells; back matter.

**Consolidated (now stated once).**
- "Leakage-free" means near-duplicate only: 2.5, with a one-clause reminder in Limitations.
- Split A and B do not share a test set: 3.2.
- The exploratory status of the normalization, "not a domain-adaptation method", and "specificity ≠ packaging recognition": 2.10.
- Authentic class labeled, not verified: 2.9 opening, with a one-clause pointer in 3.4 and the full limitation in 4.5.
- No prevalence estimate: 3.1 and 1.3.
- The internal grouped test inherits the confound: 4.2.
- Reproducibility defects: 2.12.
- Outer region ≠ backdrop: 3.5.2.

**Claims softened (each is a single statement, and no result changed).**
- Table 7, "Correcting one provenance signal can expose another": *Demonstrated → Supported on this dataset*. **Author to confirm.**
- 3.5.2: the outer-region finding is no longer described as "a different acquisition-linked cue" in Results. In 4.3 it is "the most plausible reading".
- "where the packaging is" → "where the packaging is usually placed".
- 1.1: "usually constructed" → "in the located studies"; "routinely assembles" deleted.
- 2.5: "the protocol in general use" → "the design available to a study that adopts a shipped partition".
- 1.3: "typical of what this area works with" → "not unusual for data in this area".
- 3.3: "has not learned to recognize authentic packaging" → "consistent with recognizing this dataset's photography … rather than authentic packaging".
- 3.4: "their scores carry no usable information about the label" → "show no evidence of ranking counterfeit images above authentic ones".
- 4.4: "almost by necessity" → "often … by necessity".
- 4.4: "disqualifies any in-distribution claim" → "rules out any in-distribution claim" (same strength, plainer).

**Factual corrections made (flagged, not silent).**
- M1 "never once answered 'authentic'" → "… correctly" (FN = 2).
- 4.1: "which is not an accuracy at all" removed (it contradicted 2.4).
- 2.9: "size and resolution components of $A_{\mathrm{mix}}$" → "stored resolution". Encoded size is the residual audit axis on this set, so it is not held constant. **Author to confirm.**
- 2.1: the split-label signpost corrected.
- Table 7: "the model reaching 97.4%" → "M4, reaching 97.4%". M3 is also 38/39, so the old wording was ambiguous. This is the ambiguity HANDOFF flagged on 2026-09-22.

**Inconsistencies flagged and not fixed.**
- Scorable-archive count: 2.4 says "five scorable datasets", and 3.1 says "Four of the seven were scorable, including the case study". The old Limitations sentence ("six further archives …, four of which were scorable") contradicted 3.1 and is gone. The author should check whether "five" counts the Roboflow archive scored as shipped (Table S20), and state it.
- "Hidden stratification [11]": [11] is Zech et al. The sentence is no longer in the text.
- Carried over from 2026-09-22: "highest in-distribution accuracy" for M4 holds on the naive split only. The abstract now says "the model with the highest internal accuracy", and with 0.987 in the preceding sentence that is exact.

**Important limitations preserved.** All seven: single small dataset; extreme provenance and no prevalence estimate; unverified authentic class, with unknown bias direction and the residual 0.620 audit; AI-assisted and single-reviewer screening; no two-class evaluation under acquisition shift and limited acquisition diversity; exploratory normalization and region analyses, including target-informed axes, no domain-adaptation comparison, and region ≠ feature; frozen backbones and the leakage-free scope. Also kept: the archived-run disclosure in Table 4, the Table 5 caption's threshold and interval definitions, and the whole AI disclosure in 2.12 and the Acknowledgments.

**Numbers and experimental facts.** None changed. This was checked programmatically against the pre-edit file.
- Every numeric token in the new body occurs in the old one. The only new tokens are the merged citation "[14,15]" and "74," from reordered punctuation.
- 61 of 61 table rows are present. 58 are byte-identical. The 3 edited rows are Table 7 text cells with no number changed.
- Citations 1–32 are all cited, and their first appearances are still in order 1…32.
- Every supplementary table, figure and section cited before is still cited.
- Equations (1)–(9) are unchanged.
- The only old numeric token absent from the new text is the section number "4.6", which was renumbered.

**Uncertainty accidentally strengthened?** No instance found. Every change of certainty is a softening.

**Remaining AI-like patterns.** Some remain, deliberately, where the distinction matters to interpretation: availability vs. use (abstract, 2.4, 5); region vs. feature (3.5.2, 4.3); regulator-confirmed vs. authentic-labeled (2.9); "not a domain-adaptation method" (2.10). Counts: "not" 111 → 97, sentences 590 → 517, prose bold runs 30 → 20, body words 14,472 → 12,963 (−10%). The Methods remain long. That is a length question, not a style one: most of what is left is reproducibility detail the brief said to keep.

**Not done.** MDPI template build; the author's decisions on the three "Author to confirm" items and the scorable-archive count.
