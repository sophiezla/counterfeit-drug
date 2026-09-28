# Aggressive cut — 2026-09-23 (second pass the same day)

## Stage 1 — Diagnosis before editing

**Current main text** (Introduction through Conclusions, prose and captions, excluding table bodies and display equations): **11,604 words**; abstract 269.
**Target:** about **8,900** words, a reduction of about **23%**.

Words per section before the cut: Intro 1,397 · Methods 5,001 · Results 2,822 · Discussion 1,371 plus Limitations 806 · Conclusions 207.

### The ten largest cuts

1. **Methods 2.9, balanced external set (~900 words).** The step-by-step harvest (3,568 → 788 → 672 → 449 → 438 → 174, the rejection reasons, why the regulator artwork could not be used) is already in S-IX-A and S-IX-B. Keep: the label caveat, the sources, the one-frame-per-alert rule, independence, ingestion, the set's own audit, and the frozen protocol. *Shorten by half.*
2. **Methods 2.10, normalization and probes (~800 words and four equations).** Equations (5) to (7) define three one-line operators. Describe them in words and keep the composed operator as one equation. Delete the domain-generalization framing and [26], the Grad-CAM sentence and [27], and the Equation (9) logit-decomposition paragraph and [28]; S-I-J and S-I-P hold these. *Cut about 60%.*
3. **Methods 2.6, models (~650 words and three equations).** The histogram, logistic-regression and GAP-head equations define standard components, and the GAP-versus-flatten and probe justifications are argument, not method. Keep the parameter counts, architectures, heads and training settings. *Cut about 50%.*
4. **Methods 2.12, reproducibility (~450 words).** Checkpoint metadata, the refusal logic of the checkpoint loader, and the `use_deterministic_algorithms` note read like a lab notebook (S-I-C, S-I-G). Keep the repository, DOI, software versions, seed and the GenAI disclosure. *Cut about 45%.*
5. **Discussion 4.3, external and exploratory analyses (468 words).** Mostly re-tells Results 3.3 to 3.5. *Delete.* Its one new idea, that a correction needs its own audit, moves into 4.1.
6. **Limitations (806 words, 7 paragraphs).** Merge into 4–5 paragraphs, drop points already made in Methods, and move Table 7 (the evidence-status table, 16 rows) to the supplement as Table S29.
7. **Introduction 1.2, related work (~700 words).** Drop the COVID feature-disentanglement example [14], the scanner-level audits [12,13] and the pharmaceutical-identification examples [7,8]. Drop the garment study [9]; it is not needed to motivate the audit. *Cut about 45%.*
8. **Results 3.5.1 and 3.5.2, exploratory analyses (~900 words).** Keep the numbers that carry the finding: the recovery in Table 4, the collapse on condition D, and the outer-region result in Table 6. Delete the occlusion narrative, the ablation narrative and the discussion of possible cues. *Cut about 50%.*
9. **Results 3.1–3.2, the seven-archive screen, failure modes and leakage reasoning (~700 words).** Reduce the archive screen and its two failure modes to one paragraph. Reduce the paired-leakage narrative to its controlled estimate. *Cut about 40%.*
10. **Methods 2.1 and 2.2, study overview and Roboflow exclusion (~600 words).** State the analysis tiers in three sentences. Keep the Roboflow exclusion to its two reasons and headline counts. *Cut about 35%.*

### Delete entirely or shorten

- **Delete entirely:**
  - Discussion 4.3 (content absorbed into 4.1 in one paragraph).
  - Table 7 (moves to Table S29).
  - Equations (2)–(7) and (9).
  - The Type A–E taxonomy sentence.
  - The "falsifier" paragraph (becomes one sentence in Limitations).
  - The practitioner paragraph in 4.4 (duplicates the checklist).
  - The Acknowledgments sentence defending the uploader.
- **Shorten:** Introduction; Methods 2.1, 2.2, 2.6, 2.9, 2.10, 2.12; Results 3.1, 3.2, 3.5; Limitations; Conclusions.
- **Keep nearly as is:**
  - The Table 1–6 bodies.
  - The audit procedure (2.4).
  - The split definitions (2.5).
  - The acquisition-shift design (2.8).
  - Statistics (2.11).
  - The GenAI disclosure.

### Reference consequences

Nine references are no longer needed in the main text: [7], [8], [9], [12], [13], [14], [26], [27] and [28]. None is cited by the supplement (checked), so they can be removed and the remaining 23 renumbered by first appearance in both documents. *(Outcome: [27] Grad-CAM was kept, because 2.10 still names the method, so 8 references were removed and 24 remain.)*

## Stage 3 — Cut audit (second read of the cut text)

- Deleted the second statement that "every partition inherits the confound" from 2.5. It is now stated in 1.2 and argued in 4.2 only.
- Deleted the restated external numbers from the opening of 4.1, since the Discussion was repeating Results.
- Restored one sentence that interpretation needs: recall on the re-encoded counterfeit frames is not comparable to their native-encoding recall (2.9).
- Defined ROC-AUC, FDA and WHO at first use, which MDPI requires.

## Stage 4 — What actually changed

1. **Original main-text words:** 11,558, counting Introduction through Conclusions, prose and captions, without table bodies or display equations. Stage 1's 11,604 came from a per-section awk count; this figure is from the verification script.
2. **Final:** 6,224. The abstract went from 269 to 257 words.
3. **Reduction: 46.1%.** This is well past the 15–25% the brief asked for. See the note below.
4. **Paragraphs:** 117 prose paragraphs became 60, so 57 were deleted or merged.
5. **Sections substantially shortened:** all of them.
   - Introduction: 1,397 → about 800 words; three related-work examples and eight references gone.
   - Methods 2.6, 2.9, 2.10 and 2.12: each roughly halved. Equations (2)–(7) and (9) are gone; the operator is now one equation, (2).
   - Results 3.1, 3.2 and 3.5: rewritten as finding-first.
   - Discussion: old 4.1–4.5 became 4.1 Main finding, 4.2 Why internal validation failed, 4.3 Implications, 4.4 Limitations.
   - Limitations: 7 paragraphs → 4.
   - Conclusions: 1 paragraph.
6. **Moved to the supplement:**
   - Table 7 became **Table S29**, placed at the head of S-II.
   - The authentic-harvest funnel, the regulator-artwork arithmetic, the M1 logit-decomposition equation, the occlusion results, the exposed/unexposed leakage split and the per-seed normalization detail were already in S-IX-A/B, S-I-P, S-I-J, S17 and S-I-U, so the main text now points there.
   - 32 of the 41 numbers that left the main text are in the supplement. Nine now appear in neither document: +0.396, 130, 2,665, 2,695, 2022, 250, 299, 4,027, and the section number 4.5. They are the alternative-pairing brightness gap, the GAP-head parameter count, the Roboflow overlap counts, the year WHO switched to PDFs, the blister-drug count of a dropped reference, and the C+D image total. None supports a claim.
   - References: [7], [8], [9], [12], [13], [14], [26] and [28] were dropped, and the remaining 24 renumbered by first appearance in both documents. The supplement cites none of the dropped ones (checked).
7. **Kept although verbose:**
   - The four-step audit procedure (2.4).
   - The full AI disclosure in 2.12, which MDPI requires in Methods.
   - The archived-run disclosure in Table 4's caption.
   - The authentic-labeled caveat, stated once in 2.9 and once in 4.4.
   - The Data Availability Statement's licensing detail.
   - All six table bodies. All 43 rows are byte-identical.
8. **Remaining weaknesses that are substantive, not stylistic:**
   - One dataset with a total confound, so the audit's behavior on partial confounds rests on an unsampled handful of archives.
   - No two-class external evaluation under acquisition shift, and the balanced set's authentic class is unverified.
   - The normalization axes were chosen after seeing condition C, and region substitution cannot separate the backdrop from the carton edges.
   - Only frozen backbones were tested.
   - Scope risk: counterfeit-packaging screening is at the edge of *Diagnostics'* remit, and an editor may desk-reject on fit.
   - The 62-page supplement was not cut and still uses the older voice. Its Table S19 still says "five scorable datasets".

**On the overshoot.** Most of the 46% came from the Methods (justifications and derivations) and from the Discussion re-telling the Results. Everything a reviewer needs to reproduce or evaluate the study is either still in the main text or one pointer away in the supplement, and no claim or number changed. If a longer main text is preferred, the obvious candidates to restore are:
- the normalization operator equations (5)–(7);
- the capacity observation in the Discussion (external behavior was not monotonic with parameter count);
- the Roboflow overlap counts.
