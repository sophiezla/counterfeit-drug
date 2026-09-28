"""Write Section S-X of the J. Imaging supplement (supp_addendum.md) from the
revision CSVs produced by modeling/revision_baseline_analyses.py.

Every number in the section is read from those files, none is typed by hand.
remap_supplement.py appends the output to supplementary.md.
"""
import io
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "modeling" / "results"


def ci(r, k, tag=""):
    return f"{r[k]:.3f} [{r[f'{k}{tag}_lo']:.3f}, {r[f'{k}{tag}_hi']:.3f}]"


def main():
    it = pd.read_csv(RES / "revision_internal.csv")
    bal = pd.read_csv(RES / "revision_balanced_external.csv")
    mc = pd.read_csv(RES / "revision_mcnemar_baseline.csv")
    cd = pd.read_csv(RES / "revision_c_minus_d.csv")

    out = ["", "## S-X. Analysis Chronology, Baseline-Model Analyses and Exploratory Detail", "",
           "### A. When each analysis was specified", "",
           "The study was not preregistered. The four model families, the comparison of an "
           "image-level partition (Split A) with a near-duplicate-grouped partition (Split B), "
           "and specificity on condition C were planned before any external result was "
           "available. The original plan also called for recording each source's file formats, "
           "resolutions and capture conditions, and the filename patterns that separate the "
           "classes were noticed during the first manual review. Whether these acquisition "
           "variables predict the label was not quantified until after the baseline models "
           "had failed on condition C (`data/metadata/capture_method_confound_findings.md`, "
           "2026-07-25); the header-only audit of Table 2 took its final form later. The audit "
           "reads only file properties, so its result cannot depend on any model output, but "
           "the variables it examines were chosen with knowledge of the failure. Condition D, "
           "the paired leakage experiment, the five-seed repeat and the balanced external test "
           "were added after the condition C result. The balanced test was designed after the "
           "normalization had been adopted, and its specified target was the normalized models; "
           "models, preprocessing, threshold and metrics were fixed before the set was built, "
           "and the normalized models were scored on it once. The normalization, attribution and "
           "region-substitution analyses are exploratory, and condition C informed the choice of "
           "normalization axes.", "",
           "### B. Baseline-model analyses added in revision", "",
           "Earlier versions of this study reported the internal metrics (Table S3) and the "
           "balanced external test for the normalized models of M2 to M4, because the "
           "training code normalizes by default. The main text now treats the baseline "
           "(unnormalized) models as primary. `modeling/revision_baseline_analyses.py` "
           "(i) scores the persisted seed-42 baseline checkpoints written by the seed sweep "
           "on the Split B test partition, conditions C and D and the balanced external set, "
           "reproducing the seed sweep's recorded Split B, C and D values exactly; (ii) trains "
           "baseline M2 to M4 on Split A at seed 42 with the unchanged training code; and "
           "(iii) recomputes every interval from the per-image predictions. No model, "
           "threshold or evaluation set was changed. The baseline rows of Table S31 were "
           "computed after the normalized rows were known.",
           "",
           "**TABLE S30.** Internal test performance, baseline and normalized models. "
           "95% percentile bootstrap, 10,000 resamples, stratified by class, resampling "
           "near-duplicate groups. Counterfeit-labeled is the positive class. Confusion "
           "counts are TN/FP/FN/TP.", "",
           "| Model | Condition | Split | n (groups) | Confusion | Accuracy | Balanced accuracy | Sensitivity | Specificity | ROC-AUC |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in it.iterrows():
        out.append(f"| {r.model} | {r.condition} | {r.split} | {r.n} ({r.n_groups}) | "
                   f"{r.tn}/{r.fp}/{r.fn}/{r.tp} | {ci(r, 'accuracy')} | "
                   f"{ci(r, 'balanced_accuracy')} | {ci(r, 'recall')} | "
                   f"{ci(r, 'specificity')} | {ci(r, 'roc_auc')} |")
    out += ["", "**TABLE S31.** Balanced external test with two interval constructions: "
            "resampling images (each falsified frame is a separate regulatory alert) and "
            "resampling the 29 authentic search-term clusters. Both are stratified by class, "
            "10,000 resamples. Falsified is the positive class.", "",
            "| Model | Condition | Metric | Point | Image-level interval | Cluster-level interval |",
            "|---|---|---|---|---|---|"]
    for _, r in bal.iterrows():
        for k, name in [("balanced_accuracy", "balanced accuracy"), ("recall", "recall"),
                        ("specificity", "specificity"), ("precision", "precision"),
                        ("f1", "F1"), ("roc_auc", "ROC-AUC")]:
            out.append(f"| {r.model} | {r.condition} | {name} | {r[k]:.3f} | "
                       f"[{r[k + '_img_lo']:.3f}, {r[k + '_img_hi']:.3f}] | "
                       f"[{r[k + '_clu_lo']:.3f}, {r[k + '_clu_hi']:.3f}] |")
    out += ["", "**TABLE S32.** (a) Exact McNemar tests between baseline models on the "
            "Split B test partition (n = 74), with Holm correction over six pairs. "
            "(b) Specificity on condition C minus condition D, with Newcombe hybrid-score "
            "intervals for independent proportions; the two conditions draw on one package "
            "collection but cannot be paired image by image.", "",
            "| Model A | Model B | Only A correct | Only B correct | *p* | Holm *p* |",
            "|---|---|---|---|---|---|"]
    for _, r in mc.iterrows():
        out.append(f"| {r.model_a} | {r.model_b} | {r.a_only_correct} | {r.b_only_correct} | "
                   f"{r.p_exact:.3f} | {r.p_holm:.3f} |")
    out += ["", "| Model | Condition | C − D (percentage points) | 95% interval |", "|---|---|---|---|"]
    for _, r in cd.iterrows():
        out.append(f"| {r.model} | {r.condition} | {100 * r.c_minus_d:+.1f} | "
                   f"[{100 * r.lo:+.1f}, {100 * r.hi:+.1f}] |")
    # ---- Table S33: acquisition statistics (formerly a main-text table)
    st = pd.read_csv(HERE.parent / "data" / "metadata" / "capture_method_stats.csv")
    groups = [("Kaggle authentic-labeled", st[(st.pool == "kaggle_modeling_pool") & (st.class_label == "authentic")]),
              ("Kaggle counterfeit-labeled", st[(st.pool == "kaggle_modeling_pool") & (st.class_label == "counterfeit")]),
              ("Condition C (external, authentic)", st[st.pool == "split_c_external"])]
    out += ["", "### C. Exploratory and descriptive detail moved from the main text", "",
            "**TABLE S33.** Acquisition statistics of the two source-label classes and of "
            "condition C (plotted in Figure 2 of the main text). Median short side and file "
            "size are header fields; mean brightness is the mean RGB value at 64 × 64 on a 0–1 "
            "scale. kB = 1000 bytes.", "",
            "| Group | n | File pattern | Median short side (px) | Mean file size (kB) | Mean brightness |",
            "|---|---|---|---|---|---|"]
    for name, g in groups:
        pats = g.capture_pattern.value_counts()
        pat = f"`{pats.index[0]}` ({100 * pats.iloc[0] / len(g):.0f}%)" if "Kaggle" in name else "device photograph (JPEG)"
        out.append(f"| {name} | {len(g)} | {pat} | {g.min_side.median():.0f} | "
                   f"{g.file_size_bytes.mean() / 1000:,.1f} | {g.brightness.mean():.3f} |")

    # ---- Table S34: region substitution (formerly a main-text table)
    rs = pd.read_csv(RES / "region_substitution.csv")
    short = {"model3_mobilenetv3small_frozen": "M3", "model4_efficientnetb0_frozen": "M4"}
    cols = [("model3_mobilenetv3small_frozen", "split_c"), ("model3_mobilenetv3small_frozen", "split_d"),
            ("model4_efficientnetb0_frozen", "split_c"), ("model4_efficientnetb0_frozen", "split_d")]
    out += ["", "Region substitution overwrote one region of each normalized external image "
            "after resizing to 224 × 224 and before the forward pass. The inner region is a "
            "centered square of 158 × 158 px (0.4975 of the frame); the outer region is its "
            "complement (0.5025). Fills are the ImageNet channel mean or standard Gaussian noise "
            "in standardized space. Because any substitution is itself a distribution shift, only "
            "the asymmetry between the two area-matched regions is interpreted. The border ring "
            "and center box of the occlusion analysis (Section S-I-J) are not area-matched and are "
            "shown for comparison. Figure S13 illustrates the intervention.", "",
            "**TABLE S34.** Region substitution on conditions C and D for the exploratory "
            "normalized M3 and M4. Each cell is specificity after overwriting one region "
            "(area fraction in parentheses after the region name); the intact row reproduces "
            "the value of record. Parentheses in cells: change from intact, in percentage points.", "",
            "| Region overwritten | Fill | " + " | ".join(f"{short[m]}, cond. {s[-1].upper()}" for m, s in cols) + " |",
            "|---|---|---|---|---|---|"]
    order = rs[(rs.model == cols[0][0]) & (rs.split == cols[0][1])][["region", "fill", "area_fraction"]].values.tolist()
    for region, fill, area in order:
        cells = []
        for m, s in cols:
            r = rs[(rs.model == m) & (rs.split == s) & (rs.region == region) & (rs.fill == fill)].iloc[0]
            cells.append(f"{r.specificity:.3f}" if region == "intact"
                         else f"{r.specificity:.3f} ({100 * r.delta_vs_intact:+.1f})")
        label = ("— (intact)" if region == "intact" else
                 region if "(" in region else f"{region} ({float(area):.4f})")
        out.append(f"| {label} | {'—' if fill == '-' else fill} | " + " | ".join(cells) + " |")
    out += ["", "> **FIGURE S13.** `figures/fig16_region_substitution.pdf` — The region-substitution "
            "intervention on one condition C photograph, after normalization and resizing to the "
            "224 × 224 model input. (a) Intact. (b, c) Outer region overwritten with the ImageNet "
            "channel mean or Gaussian noise. (d, e) Inner region overwritten in the same two ways. "
            "Photograph from the Mendeley *Mobile-Captured Pharmaceutical Medication Packages* "
            "archive, CC BY 4.0."]

    # ---- Table S35: normalized models at seed 42 (formerly main-text columns)
    sp = pd.read_csv(RES / "revision_external_specificity.csv")
    out += ["", "**TABLE S35.** Exploratory normalized models of M2 to M4 at seed 42: Split B "
            "test accuracy and specificity on conditions C and D, beside the baseline values. "
            "Intervals are 95% Wilson on k/n. The normalization caps the short side at 128 px, "
            "rescales mean brightness to 0.5 and re-encodes as JPEG at quality 40, in that order, "
            "for every image; its axes were chosen after the condition C result.", "",
            "| Model | Condition | Split B accuracy | Condition C | Condition D |", "|---|---|---|---|---|"]
    for m in ["M2 CNN", "M3 MobileNetV3", "M4 EfficientNet-B0"]:
        for c in ["baseline", "normalized"]:
            acc = it[(it.model == m) & (it.condition == c) & (it.split == "B")].iloc[0].accuracy
            cells = []
            for s in ("split_c", "split_d"):
                r = sp[(sp.model == m) & (sp.condition == c) & (sp.set == s)].iloc[0]
                cells.append(f"{r.k}/{r.n} = {r.specificity:.3f} [{r.lo:.3f}, {r.hi:.3f}]")
            out.append(f"| {m} | {c} | {acc:.3f} | " + " | ".join(cells) + " |")
    import re
    text = "\n".join(out) + "\n"
    text = re.sub(r"(?<=[\s(\[,|])-(?=\d)", "−", text)   # typographic minus in table numbers
    text = text.replace("centre box", "center box")        # CSV label uses British spelling
    io.open(HERE / "supp_addendum.md", "w", encoding="utf-8", newline="\n").write(text)
    print("wrote supp_addendum.md")


if __name__ == "__main__":
    main()
