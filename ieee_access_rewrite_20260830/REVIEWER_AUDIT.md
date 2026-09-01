# Simulated IEEE Access peer review of the rewritten manuscript

Run against `MANUSCRIPT_rewritten.md` as an Associate Editor would read it,
without the supplement, then a second pass with it.

## Verdict a reviewer would likely reach

**Minor revision**, conditional on the three inline conflict flags being
resolved rather than shipped. The paper's evidence is unusually well
documented and its claims are consistently weaker than its data would allow.
The risk to it is not overstatement; it is that a reviewer trips on an
internal numerical disagreement and starts doubting the rest.

## Scientific validity

| Question | Finding |
|---|---|
| Are conclusions supported by results? | Yes. The central claim (acquisition alone reproduces the labels) is a measurement, not an inference, and is reproduced from committed artifacts. |
| Unsupported causal claims? | None found. Section I-A states the mechanism as one that "can arise", Section VII-G supplies a falsifier, and Table 9 marks the generality claim "not established". |
| Are statistical claims justified? | Yes, with one caveat the paper itself raises: five seeds give a standard deviation with ~50% relative uncertainty, and the paper says so before relying on it. The paired bootstrap is correctly preferred over the pooled McNemar in Section S-I-Z. |
| Are comparisons fair? | Yes. The one unfair-looking comparison — Split A vs Split B, whose test sets differ — is identified as such and replaced by a proper fixed-test-set design. |
| Reproducible? | Yes for everything except Section III-C's cross-source counts (M-4) and the archived baseline column (M-1), both now flagged in the text. |

## Consistency

Checked after the rewrite:

- The three flagged disagreements (M-1, M-2, M-3) are the only ones found across
  Abstract → Introduction → Methods → Results → Discussion → Limitations →
  Conclusion → Tables. All three are marked inline; none is silently resolved.
- Every number appearing in more than one section now appears at the same value
  and in the same units. The 3.3% / 6% pair, which was the worst offender, is
  replaced by a qualitative phrase pending the author's decision on M-1.
- Terminology is consistent: *specificity* not false-positive rate,
  *attribution* not attention, *near-duplicate-grouped* not product-level,
  *header fields* not metadata scalars.
- Table/figure references were not renumbered except where sections moved
  (VII → VI-F, VIII–XI → VII–X); every `Section S-*` pointer is unchanged and
  still resolves to the supplement's own numbering.

## Writing

- Roughly 18% shorter than the source at identical evidence. The cuts fall
  almost entirely on third and fourth restatements of a finding.
- Longest remaining paragraph is Section VI-B's paired-design description,
  which is dense because it has to be: it defines an experiment.
- No sentence was found that exists only to sound academic. The source did not
  have many.

## What a real reviewer is most likely to ask for

In descending order of likelihood, and none of these is new — the project's
own notes predict the first three:

1. **A fine-tuning experiment.** Asked for by three consecutive informal
   reviews. Declined on hardware; Sections V-B, VIII and IX state the
   limitation and both directions it leaves open. This is the most likely
   single request, and the answer is a response letter, not new text.
2. **A counterfeit-labeled external set.** Not obtainable; the search is
   documented in Section III-E and the gap is named in Table 9 and Section IX.
3. **An external set with a different backdrop.** The paper calls this its most
   consequential gap itself, which is the right way to be asked for it.
4. **Why the archived baseline is retained at all** (M-1). Resolve it before
   submission and this does not get asked.
5. **The ablations at multiple seeds.** Thirty training runs; the claims they
   support are separations an order of magnitude past the measured seed
   variance, and the paper says so. Defensible as it stands.
6. **A validated threshold for the audit score.** Deliberately not supplied,
   because five scorable datasets cannot support a false-positive rate. The
   refusal is itself an argument the paper makes; do not soften it under
   review pressure.

## What would weaken the paper if changed

Recorded so a later revision does not undo them:

- The refusal to quote a prevalence rate.
- Table 9. It is the cheapest reviewer-facing device in the paper and the one
  most likely to be cut for space.
- The negative results: M1 as a clean negative, the M3 non-effect, the M2
  Split D collapse, the Grad-CAM/occlusion disagreement, and the
  unreproducible archived numbers. Every one of them makes the paper more
  credible, not less.
- "None of these models should be deployed."
