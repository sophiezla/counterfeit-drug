"""Derive supplementary.md (J Imaging) from the Diagnostics supplement.

Only cross-references to the MAIN text change; nothing the supplement reports
changes. Remaps, each applied through placeholders so no chain can collide:
  - citations [n]      : Diagnostics numbering -> J Imaging numbering (refs.py)
  - main tables        : 2->S33, 3->2, 4->3, 5->S31, 6->S34 (main text keeps
                         Tables 1-3; the rest moved to Section S-X)
  - main equation      : (2) -> "the normalization operator (Section 2.6)"
  - main sections      : see SMAP below; 3.5.x -> 3.4
  - header text naming the journal and the title.
Writes _supp_remap_log.txt with every substitution and its line.
Usage: python remap_supplement.py
"""
import io, os, re

import refs

HERE = os.path.dirname(os.path.abspath(__file__))
s = io.open(os.path.join(HERE, "_diagnostics_supplementary.md"), encoding="utf-8").read()
log = []


def line_of(pos, text):
    return text[:pos].count("\n") + 1


# ---- citations
dmap = refs.main()


def recite(m):
    nums = []
    for p in m.group(1).split(","):
        p = p.strip()
        if re.match(r"^\d+[–-]\d+$", p):
            a, b = map(int, re.split("[–-]", p)); nums += range(a, b + 1)
        else:
            nums.append(int(p))
    new = refs.compress(dmap[n] for n in nums)
    log.append(f"L{line_of(m.start(), s)} cite [{m.group(1)}] -> [{new}]")
    return "[" + new + "]"


s = re.sub(r"\[(\d+(?:[–-]\d+)?(?:,\s?\d+(?:[–-]\d+)?)*)\]", recite, s)

# ---- main-text tables (never Table S..)
# Editorial reset (2026-09-27, late): the main text keeps three tables
# (1 evaluation sets, 2 audit, 3 performance). Diagnostics Table 2 (acquisition
# statistics), 5 (balanced test) and 6 (region substitution) now live in the
# supplement's Section S-X as Tables S33, S31 and S34.
TMAP = {"2": "S33", "3": "2", "4": "3", "5": "S31", "6": "S34"}


def retab(m):
    head, nums = m.group(1), m.group(2)
    new = re.sub(r"\b([2-6])\b", lambda k: TMAP[k.group(1)], nums)
    if new != nums:
        log.append(f"L{line_of(m.start(), s)} {head}{nums} -> {head}{new}")
    return head + new


s = re.sub(r"\b(Tables? )(\d(?:(?:, | and | to |–)\d)*)(?![\d.])", retab, s)

# ---- equation
# The main text no longer numbers equations; the normalization operator is
# described in Section 2.6 and specified in Table S35's caption.
n_eq = s.count("Equation (2)")
# "@@NORM@@" is resolved to 2.6 after the section remap, which would otherwise rewrite it.
s = s.replace("The correction of Equation (2) of the main paper", "The normalization of Section @@NORM@@ of the main paper")
s = s.replace("the composed operator of Equation (2)", "the composed normalization operator (Section @@NORM@@)")
s = s.replace("the operator of Equation (2)", "the normalization operator (Section @@NORM@@)")
s = s.replace("Equation (2) of the main paper", "the normalization operator of the main paper (Section @@NORM@@)")
s = s.replace("Equation (2)", "the normalization operator (Section @@NORM@@)")
log.append(f"Equation (2) -> normalization operator (Section 2.6): {n_eq} occurrences")

# Results 3.5.x (exploratory) became part of Section 3.4
n35 = len(re.findall(r"Section 3\.5\.\d", s))
s = re.sub(r"Section 3\.5\.\d", "Section 3.4", s)
log.append(f"Section 3.5.x -> 3.4: {n35} occurrences")

# ---- main-text sections
# Diagnostics section -> J Imaging section (editorial reset, 2026-09-27 late):
# Methods 2.1 design and data / 2.2 audit / 2.3 grouping, partitions, internal
# evaluation / 2.4 models / 2.5 external evaluation / 2.6 exploratory analyses /
# 2.7 statistics; Results 3.1-3.4; Discussion 4.1 main finding / 4.2 why validation
# missed it / 4.3 implications / 4.4 limitations.
SMAP = {"1.1": "1", "1.2": "1", "2.2": "2.1", "2.3": "2.3", "2.4": "2.2", "2.5": "2.3",
        "2.6": "2.4", "2.7": "2.3", "2.8": "2.5", "2.9": "2.5", "2.10": "2.6",
        "2.11": "2.7", "2.12": "2.7", "3.5": "3.4"}


def resec(m):
    head, nums = m.group(1), m.group(2)
    new = re.sub(r"(?<![\d.])(\d\.\d+)(?![\d.])", lambda k: SMAP.get(k.group(1), k.group(1)), nums)
    if new != nums:
        log.append(f"L{line_of(m.start(), s)} {head}{nums} -> {head}{new}")
    return head + new


s = re.sub(r"\b(Sections? )(\d\.\d+(?:(?:, | and )\d\.\d+)*)(?![\d.])", resec, s)
s = s.replace("@@NORM@@", "2.6")

# ---- header
reps = [
    ("*Supplementary Materials for the manuscript submitted to* Diagnostics.",
     "*Supplementary Materials for the manuscript submitted to* Journal of Imaging."),
    ("**Auditing Provenance Confounding in Image Authenticity\nClassification: A Counterfeit-Medicine Case Study**",
     "**When File Format Predicts the Label: A Case Study of Provenance\nConfounding in Medicine-Authenticity Image Classification**"),
    ("**TABLE S3.**In-distribution test performance. Counterfeit is the positive class. Sens = recall. BA = balanced accuracy. Bracketed intervals are 95% percentile bootstrap (2000 resamples).",
     "**TABLE S3.**In-distribution test performance of the normalized models of M2 to M4 (M1 is never normalized); the baseline models, which the main text treats as primary, are in Table S30. Counterfeit is the positive class. Sens = recall. BA = balanced accuracy. Bracketed intervals are 95% percentile bootstrap over images (1,000 resamples); Table S30 recomputes them over near-duplicate groups."),
    ("**TABLE S5.**Pairwise McNemar's tests on the Split B test partition (n = 74), exact binomial.",
     "**TABLE S5.**Pairwise McNemar's tests on the Split B test partition (n = 74), exact binomial, normalized models of M2 to M4 (baseline models: Table S32)."),
    ("made by one\nreviewer looking at each image,",
     "made in a first pass by the AI assistant named in the Acknowledgments, working to the codes below and looking at each image, and then reviewed in full by the author,"),
    ("What the table does not do is substitute for a second reviewer.",
     "What the table does not do is substitute for an independent second rater."),
    ("author's protocol; it is not a human reviewer's pass and no inter-rater\nagreement was measured.",
     "author's protocol, and every decision was then reviewed by the author against\nthe images. That review checked the first pass rather than rating independently,\nso no inter-rater agreement was computed."),
    ("Section and\ntable numbers follow the *Diagnostics* manuscript; the manuscript has two numbered equations, (1) and (2).",
     "Section and\ntable numbers follow the *Journal of Imaging* manuscript, which has no numbered equations.\n"
     "**Terminology.** Sections S-I to S-IX use \"production\" for the pipeline with the exploratory\n"
     "provenance normalization (main text Section 2.6), which was the training default in the code.\n"
     "The main text calls these the normalized models and treats the models trained without it, called\n"
     "baseline here, as primary; Section S-X reports the baseline models in full. \"Counterfeit\" and\n"
     "\"authentic\" applied to the Kaggle pool mean the uploader's labels, which were not verified."),
    ("The split comparison, the four-model roster and the external evaluation were fixed by the protocol before any of them ran, and are confirmatory.",
     "The split comparison, the four-model roster and the condition C evaluation were planned before any external result was available (Section S-X-A gives the full chronology)."),
    ("Bracketed intervals are 95% percentile bootstrap (2000 resamples), as in Table S3.",
     "Bracketed intervals are 95% percentile bootstrap over images (1,000 resamples), as in Table S3; M2 to M4 are the normalized models, and Table S30 gives the baseline models."),
    ("de-duplicated into product-identity groups", "de-duplicated into near-duplicate groups"),
    ("free of **product-identity** leakage", "free of **near-duplicate** leakage"),
    ("belong to a product-identity group", "belong to a near-duplicate group"),
    ("The pool has 480 product-identity groups", "The pool has 480 near-duplicate groups"),
    ("decorrelates product identity and nothing else", "separates near-duplicate groups and nothing else"),
    # normalized-model values moved from the old acquisition-shift table to Table S35
    ("does not reproduce Table 3, and the difference is expected rather than a discrepancy to reconcile: Table 3 reports the production pipeline",
     "does not reproduce Table S35, and the difference is expected rather than a discrepancy to reconcile: Table S35 reports the production pipeline"),
    ("Only Table 3's column is the result of record.", "Only Table S35 is the result of record."),
    ("comparable to M2's production numbers in Table 3", "comparable to M2's production numbers in Table S35"),
    ("0.667 pre-normalization baseline (Table 3)", "0.667 pre-normalization baseline (Table S35)"),
    ("(0.860, Table 3)", "(0.860, Table S35)"),
    ("the main paper's Table 3 is this table's seed-42 draw", "the main paper's Tables 3 and S35 give this table's seed-42 draw"),
    ("the main paper's Table 3 reports both of its columns", "the main paper's Tables 3 and S35 report the baseline and normalized columns"),
    ("against the 0.807 of Table 3", "against the 0.807 of Table S35"),
    ("(the un-normalized baseline has no checkpoint and is retrained, giving 9/150 against the archived 5/150)",
     "(when this analysis was run the un-normalized baseline had no persisted checkpoint and was retrained, giving 9/150, the same value as the persisted seed-42 baseline checkpoint of Section S-X, against the superseded archived 5/150)"),
    ("the region-substitution experiment of the main paper's Table S34 does", "the region-substitution experiment (Table S34) does"),
    ("behind Table S33 of the main paper are plotted in its Figure 2", "in Table S33 are plotted in Figure 2 of the main paper"),
    ('"Figure 1", "the normalization operator (Section 2.6)" and "Section 3.1"', '"Figure 1" and "Section 3.1"'),
    ("M4, reaching 97.4% authentic-class accuracy on its own internal test partition, returns 6.0% authentic-class specificity",
     "the baseline M4, reaching 89.7% (35 of 39) authentic-class accuracy on its own internal test partition, returns 6.0% authentic-class specificity"),
    ("| Normalization removes much of the acquisition signal | Demonstrated for M2 and M4; not demonstrated for M3 | Table 3, Section S-I-U |",
     "| Normalization raises condition C specificity | Demonstrated for M2 and M4 in an exploratory analysis whose axes condition C informed; not demonstrated for M3 | Table S35, Section S-I-U |"),
    ("Demonstrated against an authentic-labeled, unverified reference class: balanced accuracy 0.478, 0.478, 0.543 and 0.652, only M4's interval excluding chance; ROC-AUC 0.403 to 0.713",
     "Measured against an authentic-labeled, unverified reference class: balanced accuracy 0.478, 0.391, 0.609 and 0.587 for the baseline models, only M3's interval lying above chance; 0.478 to 0.652 for the normalized models"),
    ("| Asymmetric sourcing produces this confound in general | Not established: a mechanism with a stated falsifier | Section 4.4 |",
     "| Asymmetric sourcing produces this confound in general | Not established: argued, not measured | Section 4.3 |"),
    ("which is largely set by acquisition and which the audit does not test; the feature inside that region is not isolated | Table S34, Section 4.1 |",
     "which is largely set by acquisition and which the audit does not test; the feature inside that region is not isolated | Table S34, Section 4.2 |"),
    ("need not have been.** the normalization operator", "need not have been.** The normalization operator"),
    ("a different publisher, a different country of origin and a different class-construction method",
     "a different publisher and a different class-construction method"),
    ("**aspect ratio alone reaches 0.803**, because screen captures inherit",
     "**aspect ratio alone reaches 0.803**, most likely because screen captures inherit"),
    ("The headline figure therefore understates what the method achieves;",
     "The reported figure therefore understates what the normalization achieves on condition C;"),
    ]
for a, b in reps:
    if a in s:
        s = s.replace(a, b); log.append(f"header: {a[:50]!r}")
    else:
        log.append(f"HEADER NOT FOUND: {a[:60]!r}")

import make_supp_addendum
make_supp_addendum.main()
s = s.rstrip() + "\n" + io.open(os.path.join(HERE, "supp_addendum.md"), encoding="utf-8").read()
log.append("appended supp_addendum.md (Section S-X, Tables S30-S32)")

io.open(os.path.join(HERE, "supplementary.md"), "w", encoding="utf-8", newline="\n").write(s)
io.open(os.path.join(HERE, "_supp_remap_log.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
print(len(log), "log lines")
