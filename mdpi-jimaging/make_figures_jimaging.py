"""Figures 1-3 of the J. Imaging manuscript (revision of 2026-09-27).

Figure 1  study design, with each analysis marked as planned at the outset or
          added after the condition C result was known.
Figure 2  the three acquisition statistics for the two source-label classes
          and condition C (data/metadata/capture_method_stats.csv).
Figure 3  baseline models: internal authentic-class accuracy against external
          specificity (conditions C, D), and balanced external accuracy for the
          baseline and normalized models with cluster-bootstrap intervals
          (modeling/results/revision_*.csv, written by
          modeling/revision_baseline_analyses.py).

Figure 4 (region substitution) is unchanged and built by make_figure4.py.
Output: figures/fig01_design.{pdf,png}, figures/fig02_acquisition.{pdf,png},
        figures/fig03_external.{pdf,png}
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "figures"
RES = ROOT / "modeling" / "results"

INK, MUTED, GRID = "#1f2937", "#6b7280", "#d1d5db"
RAMP = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------ Figure 1

def fig_design():
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")
    PLAN, LATE = "#eaf2fd", "#ffffff"
    boxes = [
        # x, y, w, h, title, body, planned
        (0, 31, 18, 27, "Source data",
         "510 Kaggle images\n(272 authentic-,\n238 counterfeit-\nlabeled); 480 near-\nduplicate groups", True),
        (20.5, 31, 18, 27, "Provenance audit",
         "classifier on file\nmetadata only, on\nthe study's own\npartitions", True),
        (41, 31, 18, 27, "Internal test",
         "four image models\nSplit A: by image\nSplit B: by near-\nduplicate group", True),
        (61.5, 31, 18, 27, "Acquisition shift",
         "authentic only\nC: 150 photographs\nD: 149 photographs,\nother device", True),
        (82, 31, 18, 27, "Balanced test",
         "46 regulator-\nconfirmed falsified\n+ 46 authentic-\nlabeled reference\nphotographs", False),
        (39, 2, 42.5, 16, "Exploratory: provenance normalization",
         "resolution, brightness and compression\nequalized; M2-M4 retrained; region substitution", False),
    ]
    notes = [(9, "format alone:\n510/510 labels"), (29.5, "file metadata\nLR: 1.000"),
             (50, "internal accuracy\n0.838–0.974"), (70.5, "EfficientNet-B0:\n9/150 correct"),
             (91, "balanced accuracy\n0.391–0.609")]
    for xc, t in notes:
        ax.text(xc, 29.3, t, ha="center", va="top", fontsize=6.4, color=RAMP[3],
                fontweight="bold", linespacing=1.25)
    for x, y, w, h, t, b, planned in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                    fc=PLAN if planned else LATE,
                                    ec=RAMP[2], lw=1.1, ls="-" if planned else (0, (3, 2))))
        ax.text(x + w / 2, y + h - 3.2, t, ha="center", va="center", fontsize=7.1,
                fontweight="bold", color=INK)
        ax.text(x + w / 2, y + h - 6.8, b, ha="center", va="top", fontsize=6.5,
                color=INK, linespacing=1.3)
    for x0, x1 in [(18, 20.5), (38.5, 41), (59, 61.5), (79.5, 82)]:
        ax.add_patch(FancyArrowPatch((x0 + 0.2, 44.5), (x1 - 0.2, 44.5), arrowstyle="-|>",
                                     mutation_scale=7, lw=0.9, color=MUTED))
    # legend
    ax.add_patch(FancyBboxPatch((0, 12), 4, 3, boxstyle="round,pad=0,rounding_size=0.5",
                                fc=PLAN, ec=RAMP[2], lw=1.1))
    ax.text(5.2, 13.5, "primary analysis", va="center", fontsize=7.1, color=INK)
    ax.add_patch(FancyBboxPatch((0, 5.5), 4, 3, boxstyle="round,pad=0,rounding_size=0.5",
                                fc=LATE, ec=RAMP[2], lw=1.1, ls=(0, (3, 2))))
    ax.text(5.2, 7, "follow-up or exploratory analysis", va="center", fontsize=7.1, color=INK)
    save(fig, "fig01_design")


# ------------------------------------------------------------------ Figure 2

def fig_acquisition():
    d = pd.read_csv(ROOT / "data" / "metadata" / "capture_method_stats.csv")
    groups = [("authentic-\nlabeled", d[(d.pool == "kaggle_modeling_pool") & (d.class_label == "authentic")]),
              ("counterfeit-\nlabeled", d[(d.pool == "kaggle_modeling_pool") & (d.class_label == "counterfeit")]),
              ("condition C", d[d.pool == "split_c_external"])]
    cols = [RAMP[0], RAMP[1], RAMP[3]]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.6))
    rng = np.random.default_rng(0)
    panels = [("brightness", "mean brightness (0-1)", False, np.mean, "{:.3f}", "a"),
              ("min_side", "short side (px, log scale)", True, np.median, "{:.0f}", "b"),
              ("file_size_bytes", "encoded file size (kB, log scale)", True, np.mean, "{:,.0f}", "c")]
    for ax, (col, lab, logy, stat, fmt, tag) in zip(axes, panels):
        for i, ((name, g), c) in enumerate(zip(groups, cols)):
            v = g[col].to_numpy(float)
            if col == "file_size_bytes":
                v = v / 1000
            x = i + rng.uniform(-0.22, 0.22, len(v))
            ax.scatter(x, v, s=4, color=c, alpha=0.55, lw=0)
            s = stat(v)
            ax.plot([i - 0.3, i + 0.3], [s, s], color=INK, lw=1.4)
            ax.text(i + 0.33, s, fmt.format(s), va="center", fontsize=7, color=INK)
        ax.set_xticks(range(3)); ax.set_xticklabels([n for n, _ in groups], fontsize=6.3)
        ax.set_xlim(-0.5, 2.9)
        if logy:
            ax.set_yscale("log")
        ax.set_ylabel(lab, fontsize=7.5)
        ax.yaxis.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)
        ax.set_title(tag, loc="left", fontweight="bold", fontsize=9)
    fig.tight_layout()
    save(fig, "fig02_acquisition")


# ------------------------------------------------------------------ Figure 3

def fig_external():
    spec = pd.read_csv(RES / "revision_external_specificity.csv")
    bal = pd.read_csv(RES / "revision_balanced_external.csv")
    models = ["M1 hist+LR", "M2 CNN", "M3 MobileNetV3", "M4 EfficientNet-B0"]
    short = ["M1", "M2", "M3", "M4"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.35, 1]})

    sets = [("split_b_test", "internal (Split B, n = 39)"), ("split_c", "condition C (n = 150)"),
            ("split_d", "condition D (n = 149)")]
    w = 0.26
    for j, (s, lab) in enumerate(sets):
        for i, m in enumerate(models):
            r = spec[(spec.model == m) & (spec.condition == "baseline") & (spec.set == s)].iloc[0]
            x = i + (j - 1) * w
            a.bar(x, r.specificity, w * 0.92, color=[RAMP[0], RAMP[2], RAMP[3]][j],
                  label=lab if i == 0 else None)
            a.plot([x, x], [r.lo, r.hi], color=INK, lw=0.7)
            a.text(x, r.hi + 0.02, f"{r.k}", ha="center", fontsize=6, color=INK)
    a.set_xticks(range(4)); a.set_xticklabels(short)
    a.set_ylim(0, 1.12); a.set_ylabel("authentic-class accuracy (specificity)")
    a.yaxis.grid(True, color=GRID, lw=0.5); a.set_axisbelow(True)
    a.legend(frameon=False, fontsize=6.4, loc="lower left", ncol=3, bbox_to_anchor=(0, 1.02), handlelength=1.2, columnspacing=0.8)
    a.text(-0.12, 1.1, "a", transform=a.transAxes, fontweight="bold", fontsize=9)

    for i, m in enumerate(models):
        conds = ["baseline"] if m == "M1 hist+LR" else ["baseline", "normalized"]
        for c in conds:
            r = bal[(bal.model == m) & (bal.condition == c)].iloc[0]
            x = i - 0.12 if c == "baseline" else i + 0.12
            if m == "M1 hist+LR":
                x = i
            mk = "o" if c == "baseline" else "s"
            b.plot([x, x], [r.balanced_accuracy_clu_lo, r.balanced_accuracy_clu_hi],
                   color=RAMP[3] if c == "baseline" else RAMP[1], lw=1.2)
            b.plot(x, r.balanced_accuracy, mk, ms=5.5, color=RAMP[3] if c == "baseline" else RAMP[1],
                   mec="white", mew=0.8,
                   label=({"baseline": "baseline", "normalized": "normalized (exploratory)"}[c]
                          if i == 1 else None))
    b.axhline(0.5, color=MUTED, lw=0.8, ls=(0, (4, 3)))
    b.text(-0.45, 0.505, "chance", fontsize=6.6, color=MUTED, va="bottom", ha="left")
    b.set_xticks(range(4)); b.set_xticklabels(short); b.set_xlim(-0.5, 3.5)
    b.set_ylim(0.2, 0.85); b.set_ylabel("balanced accuracy, 46 + 46 images")
    b.yaxis.grid(True, color=GRID, lw=0.5); b.set_axisbelow(True)
    b.legend(frameon=False, fontsize=6.4, loc="lower left", ncol=2, bbox_to_anchor=(0, 1.02), handlelength=1.2)
    b.text(-0.16, 1.1, "b", transform=b.transAxes, fontweight="bold", fontsize=9)
    fig.tight_layout()
    save(fig, "fig03_external")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig_design(); fig_acquisition()
    if (RES / "revision_balanced_external.csv").exists():
        fig_external()
