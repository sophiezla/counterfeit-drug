# IEEE Access rewrite — build folder

A self-contained mirror of the project's `paper/` tree carrying the rewritten
manuscript. It builds with the project's own scripts, unmodified except for
one gate extension noted below, and passes every gate the original passes.

## What is here

The rewrite has been **promoted into `paper/`**, which is now the single build
tree and the state the v1.2.0 release archives. What remains in this folder is
the working record of the rewrite:

```
00_DIAGNOSIS.md          diagnosis, fact-check table, proposed structure
MANUSCRIPT_rewritten.md  the authored human-readable copy, generated from
                         paper/paper.md by paper/scripts/mirror_authored_copy.py
REVIEWER_AUDIT.md        simulated IEEE Access review of the rewrite
README.md                this file
```

`paper/paper.md` and `paper/supplementary.md` are the single sources of truth.
Every other artifact, including `MANUSCRIPT_rewritten.md`, is generated from
them and none may be hand-edited.

## Rebuilding

Run from the repository root, in this order:

```
python paper/scripts/build_tex.py         # manuscript LaTeX
python paper/scripts/build_supplement.py  # supplement LaTeX
python paper/scripts/build_docx.py        # .docx
python paper/scripts/verify_crossrefs.py  # gate: refs, cites, labels, counts
python paper/scripts/compile_pdf.py       # both PDFs
python paper/scripts/final_sweep.py       # gate: rendered pages
python paper/scripts/make_overleaf_zip.py
python paper/scripts/mirror_authored_copy.py  # this folder's authored copy
```

Edit `paper/paper.md`, never `MANUSCRIPT_rewritten.md`: the authored copy is
generated from the build source by the last script above, and hand-editing it
is how the two drifted apart before.

## Verification state

| Gate | Result |
|---|---|
| `verify_crossrefs.py` | all checks passed |
| `final_sweep.py` | all checks passed, 4 notes (all carried over from the original) |
| `compile_pdf.py` | 19 and 32 pages, no float-only pages in either |
| Rendered-page section letters | 24 manuscript references and 16 supplement→manuscript references all resolve against the letters LaTeX actually printed |
| Geometric margin check | widest text block 178.64 mm against the original's 178.67 mm; zero real overflows in either document |

The last two are the checks `HANDOFF.md` records as invisible to every gate in
the repository, and were run by hand. The margin figure is the class's own
footer rule, identical in the original.

## Differences from the original build tree, in full

1. **The manuscript text**, per `00_DIAGNOSIS.md`. Section VII folded into
   VI-F, VIII–XI renumbered VII–X, Split D's description moved to III-F,
   Table 4's columns reordered, prose compressed, four editorial flags added
   inline where a number is disputed.

2. **`paper/supplementary.md` cross-references renumbered.** Sixteen
   references into the manuscript's sections were remapped (X→IX, IX→VIII,
   VIII-x→VII-x, VII→VI-F). Nothing else in the supplement was touched; it was
   not rewritten and is carried over as-is.

3. **`paper/scripts/verify_crossrefs.py` extended by one block.**
   `check_external_counts` derives the set of legitimate k/150 and k/149
   counts from committed artifacts, and did not read `seed_sweep.csv`. Table
   6's caption note quotes two per-seed counts (20/150 and 100/150) that are
   on record there, so a true statement failed the gate. The fix reads the
   artifact rather than whitelisting the numbers, which keeps the rule the
   gate exists to enforce: a new count still requires the artifact that
   justifies it. Both counts were confirmed against `seed_sweep.csv`
   (M4 baseline Split C: 9, 15, 16, 15, 20; M3 baseline seed 42: 100).

4. **One editorial note reworded for typesetting, not for content.** The
   pre-submission note in Data and Code Availability originally carried a full
   DOI string and two script paths; in an 85 mm justified column those are
   unbreakable and overflowed the right column by 13.6 mm. The note now names
   the two scripts in prose. This was caught by the geometric margin check and
   by nothing else.

## Not included, deliberately

- **The poster** (`PharmaChecked_v2_poster.pptx/pdf`). It carries the previous
  manuscript's subtitle and rebuilding it needs a PowerPoint export, which
  cannot be done from here. `HANDOFF.md` already tracks it.
- **`related_work.md`, `section_related_work.md`,
  `abstract_long_superseded.md`** and the `_pre_*_backup` directories. These
  are the original tree's working notes and superseded drafts, not build
  inputs.
- **Images, checkpoints and the raw data pipeline.** Only the result CSVs the
  gates read were copied.

## Conflict flags: all four resolved, 2026-08-31

No `[CONFLICT FLAG]` or `[INFORMATION NEEDED]` note remains in either
document. Each was resolved against the committed artifacts, not by judgement:

| Item | Resolution | Evidence |
|---|---|---|
| **M-1** Table 6/7 baseline disagreement | The **archived run is retained as the historical value of record** and labelled as such in the caption of what is now Table 7; the five-seed re-derivation of Table 8 is the value used for every sensitivity statement. 3.3% is quoted throughout and the stray "6%" in Section VI-E is gone. | `table_external_intervals.csv` re-derives 104/150 and 5/150 exactly; `seed_sweep.csv` gives the five-seed 0.715 +/- 0.057 and 0.100 +/- 0.026 that the caption now names |
| **M-2** M4's Split B baseline | **0.905 confirmed.** The stray 0.919 came from a superseded pre-seeding-fix ablation the paper itself declares non-comparable. | `seed_sweep.csv`: 0.9054 at every one of seeds 42-46, sd 0.000 |
| **M-3** "at most 1.4 points" | **Scoped in both places.** Section VII-E and the Conclusion now read "no more than 1.4 points at seed 42; -3.0 to +3.0 across five seeds". | recomputed from `seed_sweep.csv`: M2 0.8541 -> 0.8243, M4 0.9054 -> 0.9351 |
| **M-4** cross-source overlap | **Committed figures adopted**: 202 clusters, 2,665 of 4,027 Roboflow, 256 of 605 Kaggle, 42.3%. The pre-exclusion count is named in the text and explicitly not reported as the value of record. | recomputed from `data/metadata/dedup_clusters.csv` |

## Still outstanding

Nothing blocking. The v1.2.0 release is cut and `README.md`, `CITATION.cff`
and the availability statement name it.
