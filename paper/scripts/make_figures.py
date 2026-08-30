"""
Build every manuscript / poster figure as vector PDF (+ 400 dpi PNG for
embedding in .docx and .pptx, which cannot place PDF natively).

All numbers come from artifacts on disk: paper/tables/*.csv (written by
compute_paper_metrics.py and model1_attribution.py),
data/metadata/capture_method_stats.csv (written by
scripts/18_capture_method_stats.py), and modeling/results/curves/*.csv.

Palette: the dataviz reference instance, light mode, slots 1/2/3/7
(blue / orange / aqua / violet). That four-slot set was validated with
scripts/validate_palette.py against a white print surface under --pairs all
(the correct pairlist for overlapping line and scatter marks): CVD dE 9.2,
normal-vision dE 16.3, both clear. Aqua sits below 3:1 against white, so the
relief rule applies -- every figure using it carries visible direct labels or
a legend with values, and the same numbers appear in a manuscript table.
Sequential encodings (confusion matrices) use the one-hue blue ramp.
"""
import csv
import json
from pathlib import Path

import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "paper" / "tables"
FIGS = ROOT / "paper" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)
RES = ROOT / "modeling" / "results"

# ---------------------------------------------------------------- style
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"]   # slots 1,2,3,7
DASHES = [(None, None), (4, 1.6), (1.4, 1.4), (6, 1.6, 1.4, 1.6)]
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#ffffff", "#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95", "#0d366b"])
GOOD, CRIT, WARN = "#0ca30c", "#d03b3b", "#fab219"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.labelsize": 8.5,
    "axes.titleweight": "600",
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK2,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "figure.dpi": 120,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "pdf.fonttype": 42,          # embed TrueType, keep text editable/selectable
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})

MODEL_TAGS = ["M1", "M2", "M3", "M4"]
MODEL_SHORT = {
    "M1": "M1  Color hist. + LogReg",
    "M2": "M2  Small CNN (GAP)",
    "M3": "M3  MobileNetV3-Small",
    "M4": "M4  EfficientNet-B0",
}
MODEL_TINY = {"M1": "M1 hist+LR", "M2": "M2 CNN", "M3": "M3 MNetV3", "M4": "M4 ENet-B0"}
COLOR = dict(zip(MODEL_TAGS, SERIES))
DASH = dict(zip(MODEL_TAGS, DASHES))


def read(name):
    with open(TABLES / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig, stem):
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{stem}.{ext}", dpi=400 if ext == "png" else None,
                    facecolor="white")
    plt.close(fig)
    print(f"  {stem}.pdf / .png")


def style_axes(ax, xgrid=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="both" if xgrid else "y")
    if not xgrid:
        ax.xaxis.grid(False)


def bar_labels(ax, bars, fmt="{:.1%}", dy=0.012, size=7.2, color=INK):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h),
                ha="center", va="bottom", fontsize=size, color=color)


# ============================================================ Fig 1 workflow
def fig_workflow():
    fig, ax = plt.subplots(figsize=(7.2, 5.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 105)
    ax.axis("off")

    def box(x, w, y, h, text, fc="#f4f7fc", ec="#2a78d6", fs=6.6, weight="normal"):
        # argument order is (x, width, y, height) so the row definitions below
        # can splat the shared COLS entries, which are (x, width) pairs.
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                    linewidth=0.9, edgecolor=ec, facecolor=fc, zorder=2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=INK, zorder=3, linespacing=1.5, fontweight=weight)

    def down(x, y_from, y_to):
        ax.add_patch(FancyArrowPatch((x, y_from), (x, y_to), arrowstyle="-|>",
                                     mutation_scale=7, linewidth=0.85, color=MUTED,
                                     zorder=1))

    def elbow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=7, linewidth=0.85, color=MUTED,
                                     connectionstyle="angle,angleA=-90,angleB=180,rad=2",
                                     zorder=1))

    COLS = [(1, 22), (25.5, 22), (50, 23.5), (76.5, 22.5)]
    ORANGE, BLUE, AQUA, VIOLET = "#eb6834", "#2a78d6", "#1baf7a", "#4a3aa7"

    # ---- row 1: raw sources
    y1, h1 = 84, 14
    box(*COLS[0], y1, h1, "Roboflow\nCounterfeit_med_detection v4\n4 260 images", "#fdf3ee", ORANGE)
    box(*COLS[1], y1, h1, "Kaggle\nFake vs Real Medicine\n661 images", "#f4f7fc", BLUE)
    box(*COLS[2], y1, h1, "Mendeley bjy2svvmn8.1\nMobile-captured packages\n150 photos (Huawei CN)", "#eefaf5", AQUA)
    box(*COLS[3], y1, h1, "Synthetic proxy negatives\n150 perturbed copies of\nthose same 150 photos", "#f2f0fa", VIOLET)

    # ---- row 2: audit / verification
    y2, h2 = 64, 15
    box(1, 22, y2, h2, "Exclusion audit\n180 FDA-bulletin graphics\n52 contradictory labels\n→ 2 usable counterfeits", "#fdf3ee", ORANGE)
    box(25.5, 22, y2, h2, "Exclusion audit (56 files)\n47 watermarked · 4 non-medicine\n5 no packaging in frame\n→ 605 files retained", "#f4f7fc", BLUE)
    box(50, 23.5, y2, h2, "pHash independence check\nrotation-aware, 4 orientations\n0/150 matched the pool\nnearest d = 10/64", "#eefaf5", AQUA)
    box(76.5, 22.5, y2, h2, "Confound re-check\nbrightness 0.162 vs 0.153\nresolution identical\n(same source photos)", "#f2f0fa", VIOLET)

    # ---- row 3: dedup + pool
    y3, h3 = 47, 12
    box(1, 46.5, y3, h3,
        "Rotation-aware pHash de-duplication → product_identity groups\n"
        "229 clusters span both sources (44% of Kaggle ≈ Roboflow)\n"
        "Modeling pool = Kaggle only: 510 images, 480 groups",
        "#f4f7fc", BLUE, weight="normal")

    # ---- row 4: splits
    y4, h4 = 29, 13
    box(1, 22, y4, h4, "Split A\nnaive, image level\n70:15:15\n9/480 groups leak", "#fafaf8", BASELINE)
    box(25.5, 22, y4, h4, "Split B\nproduct-group level\n70:15:15 + 5-fold CV\n0 group overlap", "#f4f7fc", BLUE, weight="600")
    box(50, 23.5, y4, h4, "Split C — real\n150 external authentic\nphotographs\n(specificity)", "#eefaf5", AQUA)
    box(76.5, 22.5, y4, h4, "Split C — synthetic\n150 authentic +\n150 perturbed\n(stress-test proxy)", "#f2f0fa", VIOLET)

    # ---- row 5: models
    y5, h5 = 10, 12
    box(1, 98, y5, h5,
        "Four model families, identical protocol (seed 42, Adam, class-weighted loss, early stopping)\n"
        "M1 color histogram + LogReg   ·   M2 small CNN with GAP head   ·   "
        "M3 MobileNetV3-Small (frozen)   ·   M4 EfficientNet-B0 (frozen)\n"
        "3-way capture normalization (resolution → brightness → JPEG) applied identically to every partition",
        "#fff9ec", "#eda100", fs=6.8)

    for (x, w) in COLS:
        down(x + w / 2, y1, y2 + h2)              # source → audit
    for (x, w) in COLS[:2]:
        down(x + w / 2, y2, y3 + h3)              # audit → dedup/pool
        down(x + w / 2, y3, y4 + h4)              # pool → split A / B
    for (x, w) in COLS[2:]:
        down(x + w / 2, y2, y4 + h4)              # verification → split C
    for (x, w) in COLS:
        down(x + w / 2, y4, y5 + h5)              # split → models / evaluation
    ax.text(50, 104, "Data provenance, splitting protocol, and evaluation design",
            ha="center", va="top", fontsize=9.5, fontweight="600", color=INK)
    save(fig, "fig01_workflow")


# ======================================================= Fig 2 architectures
def fig_architectures():
    fig, axes = plt.subplots(4, 1, figsize=(7.2, 5.6))
    specs = [
        ("M1  Color histogram + logistic regression   —   97 learned parameters", "#2a78d6",
         [("input\n224×224×3", 12), ("32-bin RGB\nhistogram", 14), ("L1 normalize\n96-dim", 13),
          ("logistic\nregression", 13), ("softmax\n2 classes", 12)]),
        ("M2  Small CNN with GAP head (trained from scratch)   —   23 938 trainable parameters", "#eb6834",
         [("input\n224×224×3", 12), ("conv3×3-16\nBN·ReLU·pool", 15), ("conv3×3-32\nBN·ReLU·pool", 15),
          ("conv3×3-64\nBN·ReLU·pool", 15), ("GAP\n64-dim", 11), ("dropout 0.5\nlinear 64→2", 14)]),
        ("M3  MobileNetV3-Small, frozen ImageNet backbone   —   1 154 trainable / 927 008 frozen", "#1baf7a",
         [("input\n224×224×3", 12), ("MobileNetV3-Small features   (frozen)", 34),
          ("GAP\n576-dim", 12), ("dropout 0.3\nlinear 576→2", 15)]),
        ("M4  EfficientNet-B0, frozen ImageNet backbone   —   2 562 trainable / 4 007 548 frozen", "#4a3aa7",
         [("input\n224×224×3", 12), ("EfficientNet-B0 features   (frozen)", 34),
          ("GAP\n1280-dim", 12), ("dropout 0.3\nlinear 1280→2", 15)]),
    ]
    for ax, (title, col, blocks) in zip(axes, specs):
        # The boxes run from x=0 to x=100 and their rounded style pads outward
        # beyond that, so limits of exactly (0, 100) clip the first and last
        # block's border. Leave room for the pad and the stroke.
        ax.set_xlim(-1.6, 101.6)
        ax.set_ylim(0, 10)
        ax.axis("off")
        ax.text(0, 9.6, title, fontsize=8.6, fontweight="600", color=INK, va="top")
        x = 0
        total = sum(w for _, w in blocks) + 3 * (len(blocks) - 1)
        scale = 100 / total
        for k, (label, w) in enumerate(blocks):
            ww = w * scale
            frozen = "frozen" in label
            ax.add_patch(FancyBboxPatch((x, 1.1), ww, 5.4,
                                        boxstyle="round,pad=0.15,rounding_size=0.5",
                                        linewidth=0.9, edgecolor=col,
                                        facecolor=col + "1f" if not frozen else "#fafaf8",
                                        hatch="///" if frozen else None, zorder=2))
            ax.text(x + ww / 2, 3.8, label, ha="center", va="center", fontsize=6.9,
                    color=INK, linespacing=1.3, zorder=3,
                    # the hatched (frozen) blocks would otherwise strike through
                    # their own label
                    bbox=dict(facecolor="white", edgecolor="none",
                              boxstyle="square,pad=0.25") if frozen else None)
            if k < len(blocks) - 1:
                ax.add_patch(FancyArrowPatch((x + ww, 3.8), (x + ww + 3 * scale, 3.8),
                                            arrowstyle="-|>", mutation_scale=6,
                                            linewidth=0.8, color=MUTED, zorder=1))
            x += ww + 3 * scale
    fig.suptitle("Model families evaluated", fontsize=9.5, fontweight="600", color=INK, y=1.005)
    fig.tight_layout(h_pad=0.9)
    save(fig, "fig02_architectures")


# ========================================================== Fig 3 confound
def fig_confound():
    rows = []
    with open(ROOT / "data" / "metadata" / "capture_method_stats.csv",
              newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    kaggle = [r for r in rows if r["pool"] == "kaggle_modeling_pool"]
    auth = [r for r in kaggle if r["class_label"] == "authentic"]
    cft = [r for r in kaggle if r["class_label"] == "counterfeit"]
    ext = [r for r in rows if r["pool"] == "split_c_external"]

    groups = [
        ("Kaggle authentic\n(images*.jpg, n=272)", auth, SERIES[0]),
        ("Kaggle counterfeit\n(Screenshot*.png, n=238)", cft, SERIES[1]),
        ("Split C external\n(photographs, n=150)", ext, SERIES[2]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.25))   # float budget, see fig12

    # panel a: brightness
    ax = axes[0]
    for i, (lab, g, c) in enumerate(groups):
        v = np.array([float(r["brightness"]) for r in g])
        parts = ax.violinplot([v], positions=[i], widths=0.72, showextrema=False)
        for b in parts["bodies"]:
            b.set_facecolor(c); b.set_alpha(0.30); b.set_edgecolor(c); b.set_linewidth(0.9)
        ax.plot([i], [v.mean()], marker="o", ms=4.5, color=c, mec="white", mew=0.9, zorder=5)
        ax.text(i, v.mean() + 0.055, f"{v.mean():.3f}", ha="center", fontsize=7.2, color=INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["authentic", "counterfeit", "Split C"], fontsize=7.5)
    ax.set_ylabel("mean pixel value (0–1)")
    ax.set_title("a  Brightness", loc="left")
    ax.set_ylim(0, 1.02)
    style_axes(ax)

    # panel b: resolution (log)
    ax = axes[1]
    for i, (lab, g, c) in enumerate(groups):
        v = np.array([float(r["min_side"]) for r in g])
        ax.scatter(np.random.RandomState(42 + i).normal(i, 0.075, len(v)), v, s=4,
                   color=c, alpha=0.45, linewidths=0, zorder=3)
        med = np.median(v)
        ax.plot([i - 0.3, i + 0.3], [med, med], color=c, lw=2, zorder=5,
                solid_capstyle="round")
        ax.text(i + 0.34, med, f"{med:.0f}", fontsize=7.2, color=INK, va="center")
    ax.set_yscale("log")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["authentic", "counterfeit", "Split C"], fontsize=7.5)
    ax.set_ylabel("shorter image side (px, log)")
    ax.set_title("b  Resolution", loc="left")
    ax.set_xlim(-0.55, 2.75)
    style_axes(ax)

    # panel c: file size (log)
    ax = axes[2]
    for i, (lab, g, c) in enumerate(groups):
        # kB = 1000 bytes throughout the manuscript, so figure and tables agree
        v = np.array([float(r["file_size_bytes"]) for r in g]) / 1000
        ax.scatter(np.random.RandomState(7 + i).normal(i, 0.075, len(v)), v, s=4,
                   color=c, alpha=0.45, linewidths=0, zorder=3)
        m = v.mean()
        ax.plot([i - 0.3, i + 0.3], [m, m], color=c, lw=2, zorder=5, solid_capstyle="round")
        ax.text(i + 0.34, m, f"{m:,.0f} kB", fontsize=7.2, color=INK, va="center")
    ax.set_yscale("log")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["authentic", "counterfeit", "Split C"], fontsize=7.5)
    ax.set_ylabel("file size (kB, log)")
    ax.set_title("c  Compression proxy", loc="left")
    ax.set_xlim(-0.55, 2.95)
    style_axes(ax)

    fig.tight_layout(w_pad=1.6)
    save(fig, "fig03_capture_confound")


# ============================================================== Fig 4 ROC
def _curves():
    return json.loads((TABLES / "curve_data.json").read_text(encoding="utf-8"))


def fig_roc_pr():
    cd = _curves()
    for kind, stem, title in (("roc", "fig04_roc", "Receiver operating characteristic"),
                              ("pr", "fig05_pr", "Precision–recall")):
        fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7), sharey=True)
        for ax, split, sname in zip(axes, ("split_a", "split_b"),
                                    ("Split A (naive, image-level)",
                                     "Split B (product-grouped)")):
            for tag in MODEL_TAGS:
                d = cd[f"{tag}__{split}"]
                if kind == "roc":
                    x, y, auc = d["fpr"], d["tpr"], d["roc_auc"]
                else:
                    x, y, auc = d["recall"], d["precision"], d["pr_auc"]
                # Solid, not dashed. These curves are step functions over 74
                # test images, and a dashed or dotted staircase reads as a
                # scribble at print size. Colour alone separates them; the
                # palette is the validated colour-blind-safe set.
                ax.plot(x, y, color=COLOR[tag], lw=1.5,
                        label=MODEL_TINY[tag],
                        solid_capstyle="butt", solid_joinstyle="miter",
                        zorder=3)
            if kind == "roc":
                ax.plot([0, 1], [0, 1], color=BASELINE, lw=0.9, dashes=(2, 2), zorder=1)
                ax.set_xlabel("false positive rate")
            else:
                ax.set_xlabel("recall (counterfeit)")
            ax.set_title(sname, loc="left", fontsize=8.6)
            ax.set_xlim(-0.01, 1.01)
            ax.set_ylim(0.0 if kind == "pr" else -0.01, 1.02)
            ax.set_aspect("equal")
            style_axes(ax, xgrid=True)
            # The per-panel metric values go in the corner the curves never
            # reach, as plain text. An in-axes legend sat on top of the data.
            label = "AUC" if kind == "roc" else "AP"
            lines = [f"{label}"] + [
                f"{MODEL_TINY[t]}  "
                f"{cd[f'{t}__{split}']['roc_auc' if kind == 'roc' else 'pr_auc']:.3f}"
                for t in MODEL_TAGS]
            ax.text(0.985, 0.03, "\n".join(lines), transform=ax.transAxes,
                    ha="right", va="bottom", fontsize=6.9, color=INK2,
                    linespacing=1.45,
                    bbox=dict(boxstyle="round,pad=0.34", facecolor="white",
                              edgecolor="#DDDCD6", linewidth=0.6, alpha=0.94))
        axes[0].set_ylabel("true positive rate" if kind == "roc" else "precision")
        # One shared legend under both panels, so neither panel loses space.
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
                   handlelength=1.9, columnspacing=1.9, fontsize=8,
                   bbox_to_anchor=(0.5, -0.055))
        fig.suptitle(title + "  ·  counterfeit = positive class",
                     fontsize=9.5, fontweight="600", color=INK, y=1.02)
        fig.tight_layout(w_pad=1.2)
        save(fig, stem)


# =================================================== Fig 6 confusion matrices
def _cm_panel(ax, cm, title, vmax):
    ax.imshow(cm, cmap=SEQ_BLUE, vmin=0, vmax=vmax)
    for i in range(2):
        for j in range(2):
            v = cm[i, j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=9.5,
                    color="white" if v > 0.55 * vmax else INK, fontweight="600")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["auth.", "counterf."], fontsize=7.2)
    ax.set_yticklabels(["auth.", "counterf."], fontsize=7.2, rotation=90, va="center")
    ax.set_title(title, loc="left", fontsize=8.2)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)


def fig_confusion():
    perf = read("table_performance_full.csv")
    # Taller than wide-enough: the two rows need real vertical separation or
    # the Split B titles collide with the bottom edge of the Split A matrices.
    fig, axes = plt.subplots(2, 4, figsize=(7.2, 3.35),
                             gridspec_kw={"hspace": 0.26, "wspace": 0.30})
    vmax = max(max(int(r[k]) for k in ("tp", "fp", "fn", "tn")) for r in perf)
    for row, split in enumerate(("A (naive)", "B (product-grouped)")):
        for col, tag in enumerate(MODEL_TAGS):
            r = next(x for x in perf if x["model"] == tag and x["split"] == split)
            cm = np.array([[int(r["tn"]), int(r["fp"])], [int(r["fn"]), int(r["tp"])]])
            _cm_panel(axes[row, col], cm,
                      f"{MODEL_TINY[tag]}   acc {float(r['accuracy']):.3f}", vmax)
            if row == 0:                        # avoid colliding with row 2 titles
                axes[row, col].set_xticklabels([])
        axes[row, 0].set_ylabel(f"Split {split.split(' ')[0]}\ntrue label", fontsize=8,
                                color=INK2)
    for col in range(4):
        axes[1, col].set_xlabel("predicted", fontsize=7.6)
    fig.suptitle("Confusion matrices, in-distribution test partitions",
                 fontsize=9.5, fontweight="600", color=INK, y=1.02)
    fig.tight_layout(w_pad=1.2, h_pad=2.4)
    save(fig, "fig06_confusion_ab")


def fig_confusion_synthetic():
    syn = read("table_split_c_synthetic.csv")
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.15))
    vmax = max(max(int(r[k]) for k in ("tp", "fp", "fn", "tn")) for r in syn)
    for ax, tag in zip(axes, MODEL_TAGS):
        r = next(x for x in syn if x["model"] == tag)
        cm = np.array([[int(r["tn"]), int(r["fp"])], [int(r["fn"]), int(r["tp"])]])
        _cm_panel(ax, cm, f"{MODEL_TINY[tag]}\nacc {float(r['accuracy']):.3f} · "
                          f"AUC {float(r['roc_auc']):.3f}", vmax)
        ax.set_xlabel("predicted", fontsize=7.6)
    axes[0].set_ylabel("true label", fontsize=8, color=INK2)
    fig.suptitle("Confusion matrices, synthetic counterfeit-proxy Split C "
                 "(150 authentic / 150 perturbed)",
                 fontsize=9.2, fontweight="600", color=INK, y=1.04)
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig09_confusion_synthetic")


# ============================================== Fig 7 training/validation curves
def fig_training_curves():
    files = {
        "M2": "model2_smallcnn_gap__split_b_final.csv",
        "M3": "model3_mobilenetv3small_frozen__split_b_final.csv",
        "M4": "model4_efficientnetb0_frozen__split_b_final.csv",
    }
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7))
    for tag, fname in files.items():
        with open(RES / "curves" / fname, newline="", encoding="utf-8") as f:
            hist = list(csv.DictReader(f))
        ep = [int(r["epoch"]) for r in hist]
        axes[0].plot(ep, [float(r["train_loss"]) for r in hist], color=COLOR[tag],
                     lw=1.5, label=f"{MODEL_TINY[tag]} train", solid_capstyle="round")
        axes[0].plot(ep, [float(r["val_loss"]) for r in hist], color=COLOR[tag],
                     lw=1.5, dashes=(3, 1.6), label=f"{MODEL_TINY[tag]} val")
        axes[1].plot(ep, [float(r["train_acc"]) for r in hist], color=COLOR[tag],
                     lw=1.5, solid_capstyle="round")
        axes[1].plot(ep, [float(r["val_acc"]) for r in hist], color=COLOR[tag],
                     lw=1.5, dashes=(3, 1.6))
        best = min(hist, key=lambda r: float(r["val_loss"]))
        axes[0].scatter([int(best["epoch"])], [float(best["val_loss"])], s=18,
                        color=COLOR[tag], edgecolor="white", linewidth=0.8, zorder=6)
    axes[0].set_xlabel("epoch"); axes[0].set_ylabel("weighted cross-entropy")
    axes[0].set_title("a  Loss (solid = train, dashed = val)", loc="left")
    axes[0].legend(handlelength=2.2, labelspacing=0.28, ncol=1, fontsize=7)
    axes[1].set_xlabel("epoch"); axes[1].set_ylabel("accuracy")
    axes[1].set_title("b  Accuracy", loc="left")
    axes[1].set_ylim(0.4, 1.02)
    for ax in axes:
        style_axes(ax, xgrid=True)
    fig.suptitle("Split B training dynamics · filled marker = best validation loss "
                 "(restored checkpoint)", fontsize=9, fontweight="600", color=INK, y=1.03)
    fig.tight_layout(w_pad=1.4)
    save(fig, "fig07_training_curves")


# ================================================ Fig 8 external generalization
def fig_generalisation():
    sc = read("table_split_c_authentic.csv")
    # pre-normalization Split C numbers, from modeling/README.md's production
    # baseline table (the run immediately before 3-way normalization).
    pre = {"M1": 0.0, "M2": 0.0, "M3": 0.693, "M4": 0.033}
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    x = np.arange(4)
    w = 0.26
    idacc = [float(next(r for r in sc if r["model"] == t)["split_b_authentic_acc"]) for t in MODEL_TAGS]
    prev = [pre[t] for t in MODEL_TAGS]
    post = [float(next(r for r in sc if r["model"] == t)["split_c_authentic_acc"]) for t in MODEL_TAGS]

    b1 = ax.bar(x - w, idacc, w, color="#cde2fb", edgecolor=SERIES[0], linewidth=0.9,
                label="in-distribution (Split B test, authentic class)")
    b2 = ax.bar(x, prev, w, color="#fdf3ee", edgecolor=SERIES[1], linewidth=0.9,
                label="external Split C, no normalization")
    b3 = ax.bar(x + w, post, w, color="#eefaf5", edgecolor=SERIES[2], linewidth=0.9,
                label="external Split C, 3-way normalization")
    for bars in (b1, b2, b3):
        bar_labels(ax, bars, dy=0.015)
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_TINY[t] for t in MODEL_TAGS])
    ax.set_ylabel("accuracy on authentic images")
    ax.set_ylim(0, 1.13)
    # A three-row legend stacked above the axes, plus an explanatory line
    # below them, doubled this figure's height once "savefig.bbox: tight"
    # cropped the empty width away: it reached 4.5 in when set to the text
    # block, half a page for one bar chart. One legend row sits flush above
    # the axes instead, and the explanatory line moved into the caption,
    # where a caption's own type size applies to it.
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=3,
              labelspacing=0.3, columnspacing=1.4, handlelength=1.4,
              fontsize=7.5, frameon=False, borderaxespad=0)
    style_axes(ax)
    save(fig, "fig08_external_generalisation")


# ================================================== Fig 10 ablation of the axes
def fig_ablation():
    abl = read("table_ablation_axes.csv")
    cross = read("table_ablation_all_models.csv")

    # Panel (b) sat with a wide empty gap to its left. Closing the gap and
    # giving it a larger share lets its bars fill the space.
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.95),
                             gridspec_kw={"width_ratios": [1.18, 1],
                                          "wspace": 0.26})

    # panel a: M4, the four-condition within-run comparison (compression run)
    src = [r for r in abl if r["source"] == "compression_norm_experiment.csv"]
    order = ["baseline_no_norm_rerun", "compression_norm_only",
             "resolution_brightness_combined_rerun", "all_three_combined"]
    names = ["none", "compression\nonly", "resolution +\nbrightness",
             "all three\n(res + bright + comp)"]
    ax = axes[0]
    x = np.arange(len(order))
    w = 0.36
    bsplit = [float(next(r for r in src if r["condition"] == c)["split_b_acc"]) for c in order]
    csplit = [float(next(r for r in src if r["condition"] == c)["split_c_acc"]) for c in order]
    b1 = ax.bar(x - w / 2, bsplit, w, color="#cde2fb", edgecolor=SERIES[0], linewidth=0.9,
                label="Split B test accuracy (in-distribution)")
    b2 = ax.bar(x + w / 2, csplit, w, color="#eefaf5", edgecolor=SERIES[2], linewidth=0.9,
                label="Split C accuracy (external)")
    bar_labels(ax, b1, dy=0.015); bar_labels(ax, b2, dy=0.015)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=6.8)
    ax.set_xlabel("normalization axes applied")
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, 1.42)
    ax.set_title("a  M4 EfficientNet-B0, single-run ablation", loc="left")
    ax.legend(loc="upper center", labelspacing=0.28)
    style_axes(ax)

    # panel b: 2-way vs 3-way, all models, Split C delta
    ax = axes[1]
    x = np.arange(4)
    w = 0.36
    d2 = []
    d3 = []
    for t in MODEL_TAGS:
        r2 = next((r for r in cross if r["model"] == t and r["experiment"].startswith("2-way")), None)
        r3 = next((r for r in cross if r["model"] == t and r["experiment"].startswith("3-way")), None)
        d2.append(float(r2["delta_split_c"]) if r2 else np.nan)
        d3.append(float(r3["delta_split_c"]) if r3 else np.nan)
    b1 = ax.bar(x - w / 2, d2, w, color="#fdf3ee", edgecolor=SERIES[1], linewidth=0.9,
                label="2-way (res + bright)")
    b2 = ax.bar(x + w / 2, d3, w, color="#f2f0fa", edgecolor=SERIES[3], linewidth=0.9,
                label="3-way (+ compression)")
    for bi, bars in enumerate((b1, b2)):
        for b in bars:
            h = b.get_height()
            if np.isnan(h):
                continue
            # both series read exactly 0 for M1; stagger so the two labels
            # cannot land on top of each other
            dy = 0.02 + (0.075 if abs(h) < 1e-9 and bi == 1 else 0.0)
            ax.text(b.get_x() + b.get_width() / 2, h + (dy if h >= 0 else -0.02),
                    f"{h:+.1%}", ha="center", va="bottom" if h >= 0 else "top",
                    fontsize=7, color=INK)
    ax.axhline(0, color=BASELINE, lw=0.9)
    ax.set_xticks(x); ax.set_xticklabels([MODEL_TINY[t] for t in MODEL_TAGS], fontsize=7.1)
    ax.set_ylabel("change in Split C accuracy")
    ax.set_ylim(-0.35, 1.42)
    ax.set_title("b  Which axes help which architecture", loc="left")
    ax.legend(loc="upper left", labelspacing=0.28)
    style_axes(ax)
    fig.text(0.53, -0.06, "M3's 2-way regression predates the k_augment seeding fix and is "
                          "reported as unverified; M1 bypasses the normalized pipeline by design.",
             fontsize=6.6, color=MUTED, ha="left", va="bottom")

    fig.tight_layout(w_pad=0.7)
    save(fig, "fig10_ablation")


# ========================================================= Fig 11 calibration
def fig_calibration():
    cd = _curves()
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9),
                             gridspec_kw={"width_ratios": [1, 1]})
    ax = axes[0]
    bins = np.linspace(0, 1, 6)
    for tag in MODEL_TAGS:
        d = cd[f"{tag}__split_b"]
        y = np.array(d["y_true"]); p = np.array(d["y_prob"])
        idx = np.digitize(p, bins) - 1
        xs, ys = [], []
        for b in range(len(bins) - 1):
            m = idx == b
            if m.sum() >= 3:
                xs.append(p[m].mean()); ys.append(y[m].mean())
        ax.plot(xs, ys, marker="o", ms=4.5, lw=1.5, color=COLOR[tag], dashes=DASH[tag],
                label=MODEL_TINY[tag], mec="white", mew=0.8)
    ax.plot([0, 1], [0, 1], color=BASELINE, lw=0.9, dashes=(2, 2))
    ax.set_xlabel("mean predicted P(counterfeit)")
    ax.set_ylabel("observed counterfeit fraction")
    ax.set_title("a  Reliability, Split B test", loc="left")
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    ax.legend(loc="upper left", handlelength=2.2, labelspacing=0.28)
    style_axes(ax, xgrid=True)

    ax = axes[1]
    for i, tag in enumerate(MODEL_TAGS):
        d = cd[f"{tag}__split_b"]
        y = np.array(d["y_true"]); p = np.array(d["y_prob"])
        for lab, marker, alpha in ((0, "o", 0.5), (1, "s", 0.5)):
            v = p[y == lab]
            ax.scatter(np.random.RandomState(3 + i + lab).normal(i + (-0.16 if lab == 0 else 0.16),
                                                                 0.05, len(v)),
                       v, s=7, marker=marker, color=COLOR[tag], alpha=alpha, linewidths=0)
    ax.axhline(0.5, color=BASELINE, lw=0.9, dashes=(2, 2))
    ax.set_xticks(range(4)); ax.set_xticklabels([MODEL_TINY[t] for t in MODEL_TAGS], fontsize=7.1)
    ax.set_ylabel("predicted P(counterfeit)")
    ax.set_title("b  Score separation (○ authentic, □ counterfeit)", loc="left")
    ax.set_ylim(-0.03, 1.03)
    style_axes(ax)
    fig.tight_layout(w_pad=1.5)
    save(fig, "fig11_calibration")


# ================================================= Fig 12 Model 1 attribution
def fig_attribution():
    rows = read("model1_attribution.csv")
    # Height, here and in fig03, is set against a float budget rather than by
    # eye: these two and their two neighbouring tables are declared within one
    # subsection, all four are full-width, and at their previous heights the
    # four together filled a page exactly, so LaTeX gave them a page of their
    # own with no text on it. Both are wide panels; the trim comes out of
    # vertical white space, not out of the marks.
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.35),
                             gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    chan_colors = {"R": "#d03b3b", "G": "#0ca30c", "B": "#2a78d6"}
    # Channels are encoded by their own color, which is the one place in this
    # figure set where a non-palette hue is the correct choice. Red vs green is
    # exactly the pair CVD readers lose, so each channel also carries a distinct
    # dash pattern and every bar in panel b is directly labeled with its channel.
    chan_dashes = {"R": (None, None), "G": (3.5, 1.5), "B": (1.3, 1.3)}
    for ch in ("R", "G", "B"):
        sel = [r for r in rows if r["channel"] == ch]
        ax.plot([int(r["bin"]) for r in sel], [float(r["coefficient"]) for r in sel],
                marker="o", ms=2.6, lw=1.3, color=chan_colors[ch], label=f"{ch} channel",
                dashes=chan_dashes[ch], solid_capstyle="round")
    ax.axhline(0, color=BASELINE, lw=0.9)
    ax.annotate("top intensity bin (248–255):\n$\\beta$ = −2.86 / −2.84 / −2.95",
                xy=(31, -2.9), xytext=(20.5, -1.75), fontsize=7,
                color=INK, ha="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.8, color=MUTED))
    ax.set_xlabel("32-bin RGB histogram bin (0 = darkest, 31 = brightest)")
    ax.set_ylabel("logistic-regression coefficient")
    ax.set_title("a  M1 decision function is one feature", loc="left")
    ax.legend(labelspacing=0.28, ncol=1, loc="lower left", handlelength=2.4)
    style_axes(ax, xgrid=True)

    ax = axes[1]
    sel = sorted(rows, key=lambda r: -float(r["mean_abs_shap"]))[:8]
    labels = [f"{r['channel']} {r['bin_low']}–{r['bin_high']}" for r in sel][::-1]
    vals = [float(r["mean_abs_shap"]) for r in sel][::-1]
    cols = [chan_colors[r["channel"]] for r in sel][::-1]
    bars = ax.barh(range(len(vals)), vals, color=cols, height=0.62, linewidth=0)
    for b, v in zip(bars, vals):
        ax.text(v + 0.0025, b.get_y() + b.get_height() / 2, f"{v:.3f}",
                va="center", fontsize=7, color=INK)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=7.2)
    ax.set_xlabel("mean |Shapley value| (exact, linear model)")
    ax.set_title("b  Attribution, Split B test", loc="left")
    ax.set_xlim(0, max(vals) * 1.22)
    ax.grid(axis="x"); ax.yaxis.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig12_model1_attribution")


# ================================================== Fig 13 leakage deltas
def fig_leakage():
    leak = read("table_leakage.csv")
    fig, ax = plt.subplots(figsize=(6.6, 2.5))
    x = np.arange(4)
    w = 0.3
    a = [float(r["split_a_acc"]) for r in leak]
    b = [float(r["split_b_acc"]) for r in leak]
    aci = [r["split_a_ci"] for r in leak]
    bci = [r["split_b_ci"] for r in leak]

    def err(cis, vals):
        lo, hi = [], []
        for c, v in zip(cis, vals):
            l, h = [float(t) for t in c.strip("[]").split(",")]
            lo.append(v - l); hi.append(h - v)
        return [lo, hi]

    ax.bar(x - w / 2, a, w, color="#fafaf8", edgecolor=BASELINE, linewidth=0.9,
           label="Split A (naive, image-level)",
           yerr=err(aci, a), capsize=2.5, ecolor=MUTED, error_kw={"lw": 0.9})
    ax.bar(x + w / 2, b, w, color="#cde2fb", edgecolor=SERIES[0], linewidth=0.9,
           label="Split B (product-grouped, leakage-free)",
           yerr=err(bci, b), capsize=2.5, ecolor=SERIES[0], error_kw={"lw": 0.9})
    for i, r in enumerate(leak):
        d = float(r["delta_a_minus_b"])
        ax.text(i, 1.075, f"Δ {d:+.3f}", ha="center", fontsize=7.2,
                color=INK if abs(d) > 0.02 else MUTED)
    ax.set_xticks(x); ax.set_xticklabels([MODEL_TINY[r["model"]] for r in leak])
    ax.set_ylabel("test accuracy")
    ax.set_ylim(0, 1.16)
    # Legend below the axes. Every bar reaches at least 0.83, so an in-axes
    # legend sat on top of the data wherever it was placed.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2,
              frameon=False, labelspacing=0.3, columnspacing=2.2,
              handlelength=1.5, fontsize=7.6)
    style_axes(ax)
    fig.suptitle("Leakage quantification: naive vs product-grouped partitioning "
                 "(error bars = 95% bootstrap CI)",
                 fontsize=8.8, fontweight="600", color=INK, y=1.03)
    save(fig, "fig13_leakage")


# ============================================================ Fig 14 Grad-CAM
def fig_gradcam():
    """Tile Grad-CAM overlays selected from the completed human review.

    The heatmaps were regenerated 2026-07-30 after the batch-normalization
    defect (the Grad-CAM scripts ran the backbone in training mode) and come
    from the persisted production checkpoint. Panels are chosen to show the
    pattern the review found rather than to flatter it: on external images
    every correct call attended to the surround and every error attended to
    the product. Captions state the annotator's category.
    """
    panels = [
        (RES / "gradcam" / "correct__kaggle_fake_real_medicine_d850d8b22d.png",
         "a  M4, in-distribution, correct\nattention on the product; 9 of 22\nin-distribution maps were product-focused"),
        (RES / "gradcam" / "incorrect__kaggle_fake_real_medicine_82c705d9a3.png",
         "b  M4, in-distribution, error\ncounterfeit blister called authentic\n(p = 0.19); attention on background corners"),
        (RES / "gradcam_split_c" / "wrong_called_counterfeit__mendeley_split_c_00097.png",
         "c  M4, external, error\nauthentic photo called counterfeit\n(p = 0.79); attention on the printed name"),
        (RES / "gradcam_split_c" / "correct_called_authentic__mendeley_split_c_00013.png",
         "d  M4, external, correct\ncalled authentic (p = 0.28);\nattention on the surround, not the box"),
        (RES / "gradcam_split_c_model3" / "wrong_called_counterfeit__mendeley_split_c_00146.png",
         "e  M3, external, error\nauthentic photo called counterfeit\n(p = 0.93); attention on the product"),
        (RES / "gradcam_split_c_model3" / "correct_called_authentic__mendeley_split_c_00148.png",
         "f  M3, external, correct\ncalled authentic (p = 0.002);\nattention on the dark backdrop"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(6.6, 5.5))
    for ax, (path, cap) in zip(axes.ravel(), panels):
        ax.imshow(plt.imread(path))
        ax.set_title(cap, loc="left", fontsize=6.9, color=INK, pad=4)
        ax.set_xticks([]); ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_edgecolor(GRID)
    fig.suptitle("Grad-CAM attention audit", fontsize=9.5, fontweight="600",
                 color=INK, y=1.0)
    fig.tight_layout(w_pad=0.9, h_pad=3.4)
    save(fig, "fig14_gradcam")


# ========================================================= Fig 15 mechanism
def fig_mechanism():
    """The chain from class-conditional sourcing to external failure.

    Laid out 4 + 3 across the page rather than as a vertical column: every
    figure is emitted full-width, so a tall narrow diagram is scaled up until
    it cannot be placed.  The boxes are the general mechanism; the grey line
    under each is this paper's measurement of that step on the case study.
    """
    fig, ax = plt.subplots(figsize=(7.2, 2.62))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.grid(False)

    BLUE, AQUA, RED = "#2a78d6", "#1baf7a", "#d03b3b"
    STEPS = [
        ("Class-conditional@sourcing", "the two classes are@obtained by "
         "different@procedures", BLUE, "#f4f7fc",
         "counterfeit = screen capture,@authentic = downloaded photo"),
        ("Two acquisition@pipelines", "format, encoder, resolution,@lighting "
         "and backdrop differ@by class", BLUE, "#f4f7fc",
         "PNG vs JPEG; 405 vs 223 px;@339 vs 6 kB"),
        ("Acquisition predicts@the label",
         r"$I(Y;A)>0$; complete@when $H(Y{\mid}A)=0$" + "@ ", AQUA, "#eefaf5",
         "format alone: 510/510;@header model: 1.000"),
        ("Every partition@inherits it", "stratified, grouped and@cross-"
         "validated alike@ ", BLUE, "#f4f7fc",
         "9/480 groups leak; removing@them moves accuracy 0.3 pt"),
        ("High in-distribution@accuracy", "which cannot separate@packaging "
         "semantics from@provenance", BLUE, "#f4f7fc",
         "0.919 on the leakage-free@test partition"),
        ("A new acquisition@pipeline", "evaluation on images the@authors did "
         "not collect@ ", RED, "#fdf1f1",
         "150 external authentic@photographs (Split C)"),
        ("Failure", "the shortcut the model@relies on is absent@ ", RED,
         "#fdf1f1", "3.3% correct"),
    ]

    w, gap = 22.0, 4.0
    rows = [(STEPS[:4], 96.0), (STEPS[4:], 45.0)]
    box_h, note_h = 26.0, 15.0
    for group, top in rows:
        for i, (title, sub, ec, fc, note) in enumerate(group):
            x = i * (w + gap)
            y = top - box_h
            ax.add_patch(FancyBboxPatch((x, y), w, box_h,
                                        boxstyle="round,pad=0,rounding_size=2",
                                        linewidth=1.4 if ec == AQUA else 0.9,
                                        edgecolor=ec, facecolor=fc, zorder=2))
            ax.text(x + w / 2, y + box_h * 0.70, title.replace("@", chr(10)),
                    ha="center", va="center", fontsize=6.6, fontweight="600",
                    color=INK, zorder=3, linespacing=1.3)
            ax.text(x + w / 2, y + box_h * 0.26, sub.replace("@", chr(10)),
                    ha="center", va="center", fontsize=5.4, color=INK2,
                    zorder=3, linespacing=1.35)
            ax.text(x + w / 2, y - 2.0, note.replace("@", chr(10)), ha="center",
                    va="top", fontsize=5.3, color=MUTED, linespacing=1.35,
                    zorder=3)
            if i < len(group) - 1:
                ax.add_patch(FancyArrowPatch((x + w, y + box_h / 2),
                                             (x + w + gap, y + box_h / 2),
                                             arrowstyle="-|>", mutation_scale=6,
                                             linewidth=0.85, color=MUTED,
                                             zorder=1))

    # the wrap from the end of the first row to the start of the second
    ax.add_patch(FancyArrowPatch((3 * (w + gap) + w / 2, 96.0 - box_h - note_h),
                                 (w / 2, 45.0),
                                 arrowstyle="-|>", mutation_scale=6,
                                 linewidth=0.85, color=MUTED, zorder=1,
                                 connectionstyle="angle,angleA=-90,angleB=0,"
                                                 "rad=6"))
    ax.text(2 * (w + gap) + w / 2, 96.0 - box_h - note_h + 2.0,
            "detectable here," + chr(10) + "before any model is trained",
            ha="center", va="top", fontsize=5.6, color=AQUA, fontweight="600",
            linespacing=1.35, zorder=4)
    save(fig, "fig15_mechanism")


BUILDERS = {
    "mechanism": fig_mechanism,
    "gradcam": fig_gradcam,
    "workflow": fig_workflow,
    "architectures": fig_architectures,
    "confound": fig_confound,
    "roc_pr": fig_roc_pr,
    "confusion": fig_confusion,
    "confusion_synthetic": fig_confusion_synthetic,
    "training_curves": fig_training_curves,
    "generalization": fig_generalisation,
    "ablation": fig_ablation,
    "calibration": fig_calibration,
    "attribution": fig_attribution,
    "leakage": fig_leakage,
}

if __name__ == "__main__":
    import sys
    wanted = sys.argv[1:] or list(BUILDERS)
    print("building figures")
    for name in wanted:
        BUILDERS[name]()
    print("done ->", FIGS)
