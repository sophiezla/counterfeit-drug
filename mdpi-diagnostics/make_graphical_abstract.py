"""Graphical abstract for the Diagnostics submission.

MDPI rules this has to meet: not identical to any figure in the paper (the
IEEE package reused Figure 1, which MDPI does not allow), no "Graphical
Abstract" heading, no large text blocks, readable fonts (Arial), PNG at least
560 x 1100 px (height x width). Numbers are the paper's: 510/510 labels from
container format (Section 3.1); M4 authentic-class accuracy 38/39 in
distribution and 9/150 on condition C (Table 4).
Output: mdpi-diagnostics/figures/graphical_abstract.png (2400 x 1200 px).
"""
from pathlib import Path

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle, Circle

OUT = Path(__file__).resolve().parent / "figures"
L1, L2, L3, L4, L5 = "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"
INK, INK2, MUTED, TINT = "#0b0b0b", "#52514e", "#898781", "#f4f7fc"
mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"]})

fig = plt.figure(figsize=(12, 6), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 120); ax.set_ylim(0, 60); ax.axis("off")


def panel(x, title):
    ax.add_patch(FancyBboxPatch((x, 4), 34, 46, boxstyle="round,pad=0,rounding_size=2.2",
                                facecolor=TINT, edgecolor=L2, linewidth=1.4))
    ax.text(x + 17, 55, title, ha="center", va="center", fontsize=17, fontweight="bold", color=L5)


def arrow(x0, x1, y=27):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=22,
                                 linewidth=2.2, color=L3))


def file_tag(x, y, ext, dark):
    ax.add_patch(FancyBboxPatch((x, y - 2.3), 7.6, 4.6, boxstyle="round,pad=0,rounding_size=0.8",
                                facecolor=L5 if dark else L2, edgecolor="none"))
    ax.text(x + 3.8, y, ext, ha="center", va="center", fontsize=14, fontweight="bold",
            color="white" if dark else L5)


# ---- panel 1: two collection routes
panel(2, "Two collection routes")
# screen (counterfeit class)
ax.add_patch(FancyBboxPatch((6, 32), 11, 8, boxstyle="round,pad=0,rounding_size=0.6",
                            facecolor="white", edgecolor=L5, linewidth=2))
ax.add_patch(Rectangle((10.6, 29.6), 1.8, 2.4, facecolor=L5, edgecolor="none"))
ax.add_patch(Rectangle((8.5, 29), 6, 0.9, facecolor=L5, edgecolor="none"))
ax.text(11.5, 36, "screen\ncapture", ha="center", va="center", fontsize=11, color=L5, linespacing=1.1)
arrow(18.5, 24.5, 35.5)
file_tag(25.5, 35.5, ".png", True)
ax.text(19, 44.3, "counterfeit class", ha="center", va="center", fontsize=13, color=INK2)
# camera (authentic class)
ax.add_patch(FancyBboxPatch((6, 9.5), 11, 7.5, boxstyle="round,pad=0,rounding_size=1.2",
                            facecolor="white", edgecolor=L3, linewidth=2))
ax.add_patch(Rectangle((8.2, 17), 3, 1.4, facecolor=L3, edgecolor="none"))
ax.add_patch(Circle((11.5, 13.25), 2.4, facecolor=L1, edgecolor=L3, linewidth=2))
arrow(18.5, 24.5, 13.25)
file_tag(25.5, 13.25, ".jpg", False)
ax.text(19, 21.3, "authentic class", ha="center", va="center", fontsize=13, color=INK2)

arrow(36.6, 41.4)

# ---- panel 2: the audit
panel(43, "File metadata alone")
ax.text(60, 42.5, "no pixels, no training", ha="center", va="center", fontsize=13, color=INK2)
ax.text(60, 29.5, "510 / 510", ha="center", va="center", fontsize=40, fontweight="bold", color=L5)
ax.text(60, 20.5, "labels predicted\nfrom file format", ha="center", va="center", fontsize=14,
        color=INK, linespacing=1.25)
ax.add_patch(FancyBboxPatch((49, 7.5), 22, 5.5, boxstyle="round,pad=0,rounding_size=1.2",
                            facecolor=L5, edgecolor="none"))
ax.text(60, 10.25, "audit before training", ha="center", va="center", fontsize=13,
        fontweight="bold", color="white")

arrow(77.6, 82.4)

# ---- panel 3: what happens on photographs the authors did not collect
panel(84, "Independent photographs")
ax.text(101, 45.5, "authentic images recognized\n(best internal model)", ha="center", va="center",
        fontsize=12, color=INK2, linespacing=1.2)
base, top = 11, 38
for x, frac, col, lab, val in ((90.5, 38 / 39, L2, "internal\ntest", "97%\n38 / 39"),
                               (103.5, 9 / 150, L5, "new\nphotographs", "6%\n9 / 150")):
    h = (top - base) * frac
    ax.add_patch(FancyBboxPatch((x, base), 8, max(h, 0.4), boxstyle="round,pad=0,rounding_size=0.8",
                                facecolor=col, edgecolor="none"))
    ax.text(x + 4, base + h + 1.2, val, ha="center", va="bottom", fontsize=13, fontweight="bold",
            color=L5, linespacing=1.1)
    ax.text(x + 4, base - 1.2, lab, ha="center", va="top", fontsize=12, color=INK2, linespacing=1.1)
ax.plot([88.5, 113.5], [base, base], color=MUTED, linewidth=1.2)

OUT.mkdir(exist_ok=True)
fig.savefig(OUT / "graphical_abstract.png", dpi=200, facecolor="white")
from PIL import Image  # flatten to 8-bit RGB, as MDPI asks for figures
Image.open(OUT / "graphical_abstract.png").convert("RGB").save(OUT / "graphical_abstract.png", dpi=(200, 200))
print("wrote", OUT / "graphical_abstract.png")
