"""Figure S10 for the Diagnostics supplement.

The shared builder (paper/scripts/make_figures.py:fig_gradcam) tiles six
Grad-CAM overlays, two of which show images from the Kaggle archive, whose
license is "Unknown". The Data Availability Statement withholds those
overlays for that reason, so this version keeps only the four external panels,
whose images come from the Mendeley archive (CC BY 4.0). It also says
"attribution" rather than "attention": Grad-CAM is an attribution method, and
neither model has an attention mechanism. Output: mdpi-diagnostics/figures/.
"""
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "paper" / "scripts" / "make_figures.py"
ns = {"__name__": "make_figures_diagnostics", "__file__": str(SRC)}
exec(compile(io.open(SRC, encoding="utf-8").read(), str(SRC), "exec"), ns)
plt, RES, INK, GRID = ns["plt"], ns["RES"], ns["INK"], ns["GRID"]

panels = [
    (RES / "gradcam_split_c" / "wrong_called_counterfeit__mendeley_split_c_00097.png",
     "a  M4, error: authentic photograph called\ncounterfeit (p = 0.79); attribution on\nthe printed name"),
    (RES / "gradcam_split_c" / "correct_called_authentic__mendeley_split_c_00013.png",
     "b  M4, correct: called authentic\n(p = 0.28); attribution on the\nsurround, not the box"),
    (RES / "gradcam_split_c_model3" / "wrong_called_counterfeit__mendeley_split_c_00146.png",
     "c  M3, error: authentic photograph called\ncounterfeit (p = 0.93); attribution on\nthe product"),
    (RES / "gradcam_split_c_model3" / "correct_called_authentic__mendeley_split_c_00148.png",
     "d  M3, correct: called authentic\n(p = 0.002); attribution on the\ndark backdrop"),
]
fig, axes = plt.subplots(2, 2, figsize=(5.2, 5.6))
for ax, (path, cap) in zip(axes.ravel(), panels):
    ax.imshow(plt.imread(path))
    ax.set_title(cap, loc="left", fontsize=7.2, color=INK, pad=4)
    ax.set_xticks([]); ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_edgecolor(GRID)
fig.tight_layout(w_pad=0.9, h_pad=2.2)
out = HERE / "figures"
out.mkdir(exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(out / f"figS10_gradcam_external.{ext}", dpi=600 if ext == "png" else None, facecolor="white")
print("wrote", out / "figS10_gradcam_external.pdf")
