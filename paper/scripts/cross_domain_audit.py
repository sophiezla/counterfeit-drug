"""
Cross-domain provenance audit: does the confound appear outside pharmaceuticals?

Gap this closes: the manuscript argues that class-conditional provenance
confounding is the default outcome of asymmetric class sourcing, and supports
that with one case study plus one independently published analogous finding
[30]. Two data points motivate a hypothesis; they do not measure a prevalence.
Reviewers have correctly identified this as the paper's largest evidentiary
gap, and the paper's own Future Work proposes the fix: run the metadata audit
across datasets in other application areas.

This script does a partial version of that survey, and it does it without
downloading a single image.

METHOD. Kaggle's public dataset-file listing endpoint,

    https://www.kaggle.com/api/v1/datasets/list/{owner}/{slug}

returns, without authentication, one record per file giving its full path and
its encoded size in bytes. The path's leading directory carries the class
label in the folder-per-class layout these datasets use, and the extension
carries the storage format. That is enough to fit two of the four audit
features of Table 8 -- format and encoded size -- on the dataset exactly as
its publisher shipped it, with no pixel access at all.

For each dataset we report, under stratified 5-fold cross-validation with
balanced accuracy (chance = 0.500, matching Table 8):

    format      one-hot file extension
    size        log10 encoded bytes
    both        the two together
    ext-rule    accuracy of the single deterministic rule "extension predicts
                class", the strongest form of the claim (1.000 means a
                one-line script separates the classes perfectly)

THREE LIMITATIONS, all of which make this a conservative screen:

 1. Resolution and aspect ratio cannot be computed from a listing, so this
    audit uses half the feature set of Table 8. A dataset that scores low here
    may still be confounded on the axes not measured.
 2. There is no near-duplicate grouping. The paper's own audit groups folds on
    rotation-canonical pHash clusters so a publisher's augmented copies cannot
    straddle a fold; that needs pixels. Scores here are therefore upper bounds
    on what a grouped audit would return, and datasets shipping augmented
    copies will be flattered.
 3. Large datasets are sampled, not enumerated: the listing is paginated 20
    files at a time and we stop at MAX_PAGES. Sampling follows listing order,
    which is usually folder order, so a dataset whose sample never reaches its
    second class is reported as NOT AUDITABLE rather than scored.

Output: paper/tables/cross_domain_audit.csv
"""
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "tables" / "cross_domain_audit.csv"

API = "https://www.kaggle.com/api/v1/datasets/list/{}"
UA = {"User-Agent": "Mozilla/5.0"}
MAX_PAGES = 200            # 20 files per page
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".gif"}

# (kaggle ref, application area, regexes matching the two class folders).
# Class regexes are matched case-insensitively against every path component.
DATASETS = [
    ("rhythmghai/ai-vs-real-images-dataset", "Generated images",
     ("ai_generated", "real_dataset")),
    ("kshitizbhargava/deepfake-face-images", "Deepfake faces",
     ("fake", "real")),
    ("shahzaibshazoo/detect-ai-generated-faces-high-quality-dataset",
     "Generated faces", ("ai", "real")),
    ("cashbowman/ai-generated-images-vs-real-images", "Generated images",
     ("ai|fake", "real")),
    ("prosperchuks/fakereal-logo-detection-dataset", "Brand logos",
     ("genlogo|fake", "real|original|genuine")),
    # Negative control. Genuine and forged signatures are normally written and
    # scanned by the same procedure, so asymmetric class sourcing does not
    # apply and the audit should return close to chance. A screen that fires
    # everywhere is worthless; this is the case that should not fire.
    ("ishanikathuria/handwritten-signature-datasets", "Signatures (control)",
     ("file:-f-", "file:-g-")),
    # Positive control: the paper's own case study, where the answer is known.
    ("surajkumarjha1/fake-vs-real-medicine-datasets-images", "Medicines",
     ("fake", "real")),
]


def fetch_files(ref, verbose=True):
    """Paginate the public listing endpoint. Returns [(path, bytes), ...]."""
    files, token, pages = [], None, 0
    while pages < MAX_PAGES:
        url = API.format(ref)
        if token:
            url += "?pageToken=" + urllib.parse.quote(token)
        try:
            data = json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=60))
        except Exception as exc:
            print(f"    fetch error on page {pages}: {exc}")
            break
        batch = data.get("datasetFiles") or []
        for f in batch:
            name = f.get("name") or ""
            size = f.get("totalBytes")
            if name and size:
                files.append((name, int(size)))
        token = data.get("nextPageToken") or None
        pages += 1
        if not batch or not token:
            break
        time.sleep(0.15)                     # be polite to the endpoint
    if verbose:
        print(f"    {len(files)} files listed over {pages} page(s)"
              f"{' (page budget reached)' if pages >= MAX_PAGES else ''}")
    return files


def label_of(path, class_patterns):
    # Substring match on each directory component. Folder names in the wild
    # are things like "Ai_generated_dataset" and "real_dataset", where word
    # boundaries do not fall where a \b would put them (underscores are word
    # characters). A path matching BOTH patterns is discarded, which also
    # handles ambiguous names such as "fakereal".
    #
    # A "file:" prefix matches the FILENAME instead of the directories, for
    # the archives that encode the class in the name: the BHSig260 signature
    # corpus, for instance, puts the signer in the folder and the genuine or
    # forged status in the filename (B-S-12-G-04 vs B-S-12-F-04).
    neg, pos = class_patterns
    if neg.startswith("file:") or pos.startswith("file:"):
        neg, pos = neg.removeprefix("file:"), pos.removeprefix("file:")
        parts = [Path(path).name.lower()]
    else:
        parts = [p.lower() for p in re.split(r"[/\\]", path)[:-1]]
    hit_neg = any(re.search(neg, p) for p in parts)
    hit_pos = any(re.search(pos, p) for p in parts)
    if hit_neg and not hit_pos:
        return 1                              # "inauthentic" class
    if hit_pos and not hit_neg:
        return 0
    return None


def audit(files, class_patterns):
    ext, size, y = [], [], []
    for path, nbytes in files:
        suffix = Path(path).suffix.lower()
        if suffix not in IMAGE_EXT:
            continue
        lab = label_of(path, class_patterns)
        if lab is None:
            continue
        ext.append(suffix)
        size.append(nbytes)
        y.append(lab)

    y = np.array(y)
    if len(y) < 40 or len(set(y)) < 2:
        return None, {"n": len(y), "classes": len(set(y))}

    enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    X_ext = enc.fit_transform(np.array(ext).reshape(-1, 1))
    X_size = np.log10(np.array(size, dtype=float)).reshape(-1, 1)

    def cv(X):
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = []
        for tr, te in skf.split(X, y):
            clf = LogisticRegression(max_iter=2000, class_weight="balanced")
            clf.fit(X[tr], y[tr])
            scores.append(balanced_accuracy_score(y[te], clf.predict(X[te])))
        return float(np.mean(scores))

    # deterministic single rule: majority class per extension
    rule = {}
    for e, lab in zip(ext, y):
        rule.setdefault(e, Counter())[lab] += 1
    pred = np.array([rule[e].most_common(1)[0][0] for e in ext])
    ext_rule = float((pred == y).mean())

    counts = Counter(y)
    return {
        "n_images": int(len(y)),
        "n_inauthentic": int(counts[1]),
        "n_authentic": int(counts[0]),
        "formats": "|".join(sorted(set(ext))),
        "audit_format": round(cv(X_ext), 3),
        "audit_size": round(cv(X_size), 3),
        "audit_both": round(cv(np.hstack([X_ext, X_size])), 3),
        "ext_rule_accuracy": round(ext_rule, 3),
    }, None


def main():
    rows = []
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for ref, area, patterns in DATASETS:
        if only and only not in ref:
            continue
        print(f"=== {ref}  ({area}) ===", flush=True)
        files = fetch_files(ref)
        if not files:
            print("    no listing; skipped")
            continue
        res, why = audit(files, patterns)
        if res is None:
            print(f"    NOT AUDITABLE: {why['n']} labelled images, "
                  f"{why['classes']} class(es) found in sample")
            rows.append({"dataset": ref, "area": area, "status": "not auditable",
                         "n_images": why["n"]})
            continue
        print(f"    n={res['n_images']} ({res['n_authentic']} authentic / "
              f"{res['n_inauthentic']} inauthentic)  formats={res['formats']}")
        print(f"    format {res['audit_format']:.3f}   size "
              f"{res['audit_size']:.3f}   both {res['audit_both']:.3f}   "
              f"ext-rule {res['ext_rule_accuracy']:.3f}", flush=True)
        rows.append({"dataset": ref, "area": area, "status": "audited", **res})

    if not rows:
        return
    fields = ["dataset", "area", "status", "n_images", "n_authentic",
              "n_inauthentic", "formats", "audit_format", "audit_size",
              "audit_both", "ext_rule_accuracy"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
