# Split E — external counterfeit-recall set: audit findings

Date: 2026-09-07. Sources: the delivered package
`PharmaChecked_200_license_audited_2026-09-07.zip` plus its manifest CSV at the
repo root, and a harvest of the wider FDA/WHO alert archive (steps 27–28).

Scripts: `scripts/24_download_split_e.py`,
`scripts/27_harvest_split_e_candidates.py`,
`scripts/28_download_harvested_candidates.py`,
`scripts/25_verify_split_e_independence.py`,
`scripts/26_characterise_split_e.py`, `modeling/eval_split_e.py`,
`modeling/split_e_screen_sensitivity.py`.

**Split E is 150 photographs from 46 regulatory cases, counterfeit class only.**

---

## 0. The duplicate question, answered first

**No candidate overlaps anything this project has ever trained or evaluated on.**

Rotation-canonical pHash, the same procedure and the same 8/64 Hamming threshold
used by `03_dedup.py` and by Split C's independence check in step 07. The
reference set is deliberately wider than Split C's was: **all 7,081 images under
`data/raw`** — the Roboflow and Kaggle modelling pool, Mendeley Split C, Mendeley
Split D, the iphone11pro archive and the synthetic counterfeits.

| | |
|---|---|
| Candidates checked | 202 |
| Flagged as near-duplicate | **0 / 202** |
| Nearest-neighbour distance | min 10, median 18, max 20 |
| Threshold | 8 |

Closest approach is distance 10, the same as Split C's closest approach to the
training pool. Byte-level SHA-256 finds **0 exact duplicate groups** among the
survivors. Four harvested images *were* caught as pool near-duplicates during
step 28 (filter `F4_POOL_DUP`) and deleted before they reached the screen, which
is the filter doing its job rather than a defect.

**Within the candidate set**, 8 near-duplicate pairs exist, all among
`PC_000007`–`PC_000014` and all from one case. Every one of those is excluded by
the eligibility screen for an independent reason, so **0 near-duplicate pairs
survive into Split E**. Step 28 additionally removed 27 byte-identical repeats
and 6 template assets before the screen ran: the alert archive genuinely re-uses
photographs across related alerts (the 2013 and 2014 Coartem alerts, the two
Defitelio alerts), so this is a real risk, not a hypothetical one.

---

## 1. What the delivered package actually contained

A **rights-audited candidate manifest, not an image dataset** — its own
`documentation/CURRENT_VERIFICATION.md` says so, and `images/`, `hashes/`,
`splits/` and `replacements/` inside the zip are empty directories.

- 188 manifest rows, of which **131 are `source_photo_queue` records with no
  image URL and no label**.
- **57 rows are `direct_image_reference`s.** All 57 fetch. These were the entire
  usable content of the delivery.
- 27 FDA-hosted and public domain; 30 WHO-hosted and
  `metadata_only_permission_required`, i.e. **not redistributable**.

### Defects found in the package

1. **The two record counts disagree.** `metadata/metadata.csv` has 200 rows;
   `candidate_manifest_200.csv` has **188**. The 12 missing rows are
   `PC_000189`–`PC_000200`, queue records under `CASE_0033`/`CASE_0034` with no
   URL. `COUNTS_LICENSE_AUDIT.txt` reports `total_records=200` and
   `queue_records=143`, matching `metadata.csv` and not the manifest.
2. **`COUNTS_LICENSE_AUDIT.txt` is internally inconsistent.** `metadata_only=173`
   holds against a 200 denominator but not against the manifest's 188, and the
   file does not say which it means.
3. **`PC_000055` is the World Health Organization corporate logo**, labeled
   `FALSIFIED`. A labeling error, not a borderline call.
4. **`PC_000048`, `PC_000050` contain no product** — rendered data tables of
   product name, lot and expiry.
5. **`PC_000033`, `PC_000036`, `PC_000037` are single frames containing both
   classes** — regulator comparison figures captioned "Authentic Ozempic Images |
   Counterfeit Images" and similar. The package's own
   `LICENSE_REVIEW_2026-09-07.md` anticipates this ("Mixed comparison
   photographs must be segmented before binary labeling") but ships them
   unsegmented.
6. **`PC_000034`, `PC_000035` carry regulator markup** — ellipses drawn onto the
   image to indicate discrepant fields.
7. **Eight images carry a burned-in caption naming the contents as falsified.**
8. **`CASE_0033` is correctly marked substandard rather than falsified.**
   Confirmed; no action needed. The rule is now encoded in step 27, which
   refuses to harvest from an alert whose title says *substandard*.

### The defect that determines the design

9. **The manifest carries a deterministic class–acquisition confound of exactly
   the species this paper documents.** Of the 9 `AUTHENTIC`-labelled images,
   **8 are flat vector carton artwork** — manufacturer reference renderings of
   the genuine label — while **every `FALSIFIED` image is a field photograph**.
   Measured across all 192 labelled candidates (step 26):

   | | n | brightness | median short side |
   |---|---|---|---|
   | `FALSIFIED` | 183 | 0.588 | 447 px |
   | `AUTHENTIC` | 9 | **0.821** | 328 px |

   A **+0.233 brightness gap** between classes, driven by artwork-versus-
   photograph rather than by anything about the products. A two-class Split E
   built without screening would have reproduced, inside this paper's own
   external validation, the precise defect the paper exists to expose. That is
   why the authentic class is discarded rather than corrected.

---

## 2. Reaching a usable size

28 images from 8 cases was too small to evaluate on: the case-clustered interval
for M2 ran [0.214, 0.821]. The 143 queue records could not close the gap —
**all 143 carry the same generic index URL** rather than a specific alert, and
22 of the 34 cases name a product with no alert page at all. The queue is a
to-do list, not a download.

Steps 27–28 therefore locate the alerts themselves: WHO's full-alert index and
FDA's counterfeit-medicine index, filtered to alerts asserting falsification,
then every image resource on each. **WHO changed how it publishes around 2022** —
older alerts embed photographs inline, newer ones carry only boilerplate and
link a PDF with the photographs inside. Harvesting inline images alone returned
42 distinct URLs across 48 alerts, nearly all page furniture; adding PDF raster
extraction (`pymupdf`) is what made the recent archive usable at all.

Attrition, all recorded in `split_e_harvest_download_log.csv`:

| filter | n |
|---|---|
| `F0_PDF_NO_RASTER` | 7 |
| `F1_CHROME` (asset on 3+ alert pages) | 6 |
| `F2_TOO_SMALL` (< 120 px) | 3 |
| `F3_BYTE_DUP` | 27 |
| `F4_POOL_DUP` / `F4_HARVEST_DUP` | 4 |
| **kept** | **145** |

---

## 3. The eligibility screen

Recorded in `split_e_eligibility_review.csv` (the 57 manifest images) and
`split_e_harvest_eligibility_review.csv` (the 145 harvested), one row per
candidate with a decision, an exclusion code and a written reason. Step 25
applies it; it does not decide it. **Both passes are a single first pass by one
reviewer, marked as such in the `reviewer` column, and neither has been
adjudicated by a second.**

| code | n | what it catches |
|---|---|---|
| `X_BANNER_COMPOSITE` | 16 | burned-in caption naming the contents as falsified |
| `X_NOT_PRODUCT` | 8 | WHO logo, WHO emblem line art, laboratory TLC plates, a chromatogram |
| `X_TEXT_ONLY` | 8 | rendered tables with no photographic content |
| `X_NOT_PHOTOGRAPH` | 8 | flat carton artwork rather than a photograph |
| `X_ANNOTATED` | 5 | regulator markup drawn onto the image |
| `X_MIXED_CLASS` | 3 | both classes in one frame |
| `X_LABEL_UNVERIFIED` | 3 | the manifest does not assert a class |
| `X_CLASS_TOO_SMALL` | 1 | the last surviving authentic image |
| **include** | **150** | |

`PC_000015` is a genuine photograph of an authentic vial and the only authentic
image to survive the other screens. One image is not a class, so it is excluded
and Split E is reported honestly as falsified-only.

**One earlier call was reversed for consistency.** `PC_000019` was first
excluded as `X_TEXT_ONLY`; it is a photographic close-up of a printed carton
panel, and the harvest screen keeps ten frames of exactly that kind. The code
covers *rendered* tables with no photographic content, so keeping the original
call would have applied two different rules to the same thing. It is now
included and flagged `label_crop`.

---

## 4. What Split E is

**150 photographs, 46 regulatory cases, counterfeit class only.**
10 FDA public domain, 140 WHO metadata-only. Bytes live under `data/raw`, which
is gitignored; the repository ships the manifests and the scripts, never the WHO
bytes. Composition: 22 multi-panel montages, 12 label crops, 116 single
whole-product photographs. Images per case run 1–8 (median 3).

It measures **external counterfeit recall** and nothing else — the exact
complement of Splits C and D, which are authentic-only and measure specificity.
The Section V-A terminology rule applies: this is not an accuracy.

### It is still not an acquisition-shift set

| | brightness | median short side |
|---|---|---|
| Kaggle pool (training source) | 0.668 | 225 px |
| **Split E (regulatory alerts)** | **0.558** | **439 px** |
| Split D (iphone 11 pro) | 0.389 | 2419 px |
| Split C (huawei cn) | 0.162 | 2448 px |

Split E sits **next to the training pool**, not out with Splits C and D. It
shifts the product, the source and the photographer; it does not meaningfully
shift the acquisition statistics this paper is about. It does **not** close
Table 8's "counterfeit recall under acquisition shift" row — it narrows it.
Recall under *source* shift is now measured; under *acquisition* shift it is
not.

### 150 images but 46 cases

Several images per case are photographs of one seizure of one product, sharing
lighting, camera and packaging. `eval_split_e.py` reports a **case-clustered
bootstrap interval** (resampling whole cases, 10,000 draws) alongside the Wilson
interval, and the clustered one is the one to quote.

---

## 5. Result

Checkpoints `split_b_final`, seed 42 — the same objects that produced the
in-distribution and Split C/D numbers.

| model | Split E recall | clustered 95% CI | Split C spec. | Split D spec. |
|---|---|---|---|---|
| M1 classical colour-histogram | **0.967** | [0.93, 0.99] | **0.000** | **0.000** |
| M2 small CNN | 0.593 | [0.50, 0.69] | 0.860 | 0.463 |
| M3 MobileNetV3-Small frozen | 0.553 | [0.46, 0.64] | 0.773 | 0.725 |
| M4 EfficientNet-B0 frozen | 0.607 | [0.49, 0.72] | 0.807 | 0.832 |

**M1 is the degenerate classifier the paper hypothesised, now observed.**
Section VII says: "A degenerate classifier calling every image counterfeit would
score 0.000 here and 1.000 on counterfeit recall, and nothing in our external
data separates such a model from one applying a real decision rule at a shifted
operating point." M1 scores 0.000 / 0.000 / 0.967. The sentence was written as a
hypothetical about what the data could not rule out; it is now a measurement of
what one of the four reported models actually does.

**M2–M4 sit near chance on confirmed counterfeits** — 0.553–0.607 — while
holding 0.725–0.860 specificity on Splits C and D (M2's Split D 0.463 excepted).
M3's interval [0.46, 0.64] excludes both 0.35 and 0.75; M2's and M4's lower
bounds sit at 0.50 and 0.49. The models that survive external specificity
testing do not thereby demonstrate counterfeit recall.

Read the columns together; neither half is the finding on its own.

### The screen does not drive the result

`modeling/split_e_screen_sensitivity.py` scores every FALSIFIED-labelled
candidate once and re-reads the same predictions under five screen settings,
from whole-product photographs only to no screen at all:

| condition | n | cases | M1 | M2 | M3 | M4 |
|---|---|---|---|---|---|---|
| S1 whole-product photographs only | 117 | 34 | 0.991 | 0.573 | 0.513 | 0.573 |
| S2 minus multi-panel montages | 128 | 36 | 0.992 | 0.594 | 0.555 | 0.609 |
| **S0 as built (reported)** | **150** | **46** | **0.967** | **0.593** | **0.553** | **0.607** |
| S3 plus banner composites | 166 | 53 | 0.886 | 0.584 | 0.524 | 0.578 |
| S4 no screen at all | 183 | 56 | 0.836 | 0.590 | 0.552 | 0.601 |

M2–M4 move by at most 0.06 across the whole range; M1 stays between 0.84 and
0.99. The screen removes frames that should not be scored; it does not
manufacture the number. This table should ship with any reported Split E result.

---

## 6. What is still open

1. **Second-reviewer adjudication.** Both screens are a single first pass. The
   project's modality review used two purpose-built tools and a full human pass;
   this has had neither.
2. **Counterfeit recall under acquisition shift** remains unmeasured. Split E
   shifts source, not acquisition.
3. **The authentic side of an external two-class set** still does not exist, and
   the regulatory archive cannot supply one: regulators publish photographs of
   seized falsified product, and their authentic reference imagery is
   manufacturer artwork. This is a property of the source, not of the harvest.
4. **Only 10 of 150 images are redistributable.** The set is reproducible from
   the manifests but not publishable as a dataset.
5. **Per-image FDA rights exceptions are unchecked.** FDA's blanket policy
   carries an "unless otherwise noted" exception, and `PC_000007`–`PC_000014`
   are manufacturer-supplied Allergan/AbbVie artwork — the most likely place for
   a third-party credit. They are excluded from Split E on other grounds.
6. **Case sizes are uneven** (1–8 images, median 3). The clustered bootstrap
   handles this correctly, but a per-case-balanced subsample would be a cleaner
   headline figure if one is ever needed.
