"""All figures for the MDPI (Diagnostics / J Imaging) manuscript and supplement, in one blue theme.

Reuses the shared builders in paper/scripts/make_figures.py (so the data, and
every number drawn in a figure, come from the same committed tables) and
changes only presentation:

  * color: the shared figures use a categorical palette (blue, orange, aqua,
    violet, plus red/green/amber accents). Here every hue is mapped onto one
    blue ramp. The four models are ordered light -> dark (steps 250/400/550/700,
    validated as an ordinal ramp: monotone lightness, visible step gaps, light
    end >= 2:1 on white), and they stay distinguishable without color through
    the existing line dashes, markers, legends and direct labels;
  * Figure 1: the third box states the condition in words (the Diagnostics
    text does not define I(Y;A) / H(Y|A)), and the second row is moved down so
    that the wrap-around arrow runs through the gap between the rows instead of
    along the tops of the bottom boxes;
  * PNGs are written at 600 dpi, as MDPI asks.

Output: <this folder>/figures/. paper/figures (the IEEE record) is untouched.
Figure S10 (Grad-CAM overlays) is built by make_figure_s10.py.
"""
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "paper" / "scripts" / "make_figures.py"
OUT = HERE / "figures"
src = io.open(SRC, encoding="utf-8").read()


def sub(a, b, n=None):
    global src
    k = src.count(a)
    assert k and (n is None or k == n), (k, a[:70])
    src = src.replace(a, b)


# ---- the four model series: one hue, light -> dark
sub('SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"]   # slots 1,2,3,7',
    'SERIES = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]   # blue 250/400/550/700', 1)

# ---- bar fills: three or four clearly different steps of the same ramp
sub('color="#cde2fb", edgecolor=SERIES[0]', 'color="#cde2fb", edgecolor="#86b6ef"')
sub('color="#fdf3ee", edgecolor=SERIES[1]', 'color="#6da7ec", edgecolor="#3987e5"')
sub('color="#eefaf5", edgecolor=SERIES[2]', 'color="#184f95", edgecolor="#184f95"')
sub('color="#f2f0fa", edgecolor=SERIES[3]', 'color="#0d366b", edgecolor="#0d366b"')

# ---- architecture diagram: M1 takes the lightest series step like everywhere else
sub('97 learned parameters", "#2a78d6"', '97 learned parameters", "#86b6ef"', 1)

# ---- Figure 1 (mechanism): words instead of notation, arrow routed through the gap
sub('r"$I(Y;A)>0$; complete@when $H(Y{\\mid}A)=0$" + "@ "', '"label follows from@file metadata alone@ "', 1)
sub('BLUE, AQUA, RED = "#2a78d6", "#1baf7a", "#d03b3b"', 'BLUE, AQUA, RED = "#2a78d6", "#0d366b", "#104281"', 1)
sub('fig, ax = plt.subplots(figsize=(7.2, 3.75))\n    ax.set_xlim(0, 100)\n    ax.set_ylim(0, 108)',
    'fig, ax = plt.subplots(figsize=(7.2, 4.03))\n    ax.set_xlim(0, 100)\n    ax.set_ylim(-8, 108)', 1)
sub('rows = [(STEPS[:4], 104.0), (STEPS[4:], 46.0)]', 'rows = [(STEPS[:4], 104.0), (STEPS[4:], 40.0)]', 1)
old_arrow = src[src.index("    # the wrap from the end of the first row"):src.index("    ax.text(2 * (w + gap) + w / 2, 104.0 - box_h - note_h + 1.5,")]
src = src.replace(old_arrow,
    "    # the wrap from the end of the first row to the start of the second, routed\n"
    "    # through the empty band between the rows so it never touches a box\n"
    "    _xe, _ys, _yh = 3 * (w + gap) + w / 2, 104.0 - box_h - note_h, 45.0\n"
    "    ax.plot([_xe, _xe, w / 2], [_ys, _yh, _yh], color=MUTED, lw=1.0, zorder=1,\n"
    "            solid_joinstyle='round', solid_capstyle='round')\n"
    "    ax.add_patch(FancyArrowPatch((w / 2, _yh), (w / 2, 40.4), arrowstyle='-|>',\n"
    "                                 mutation_scale=8, linewidth=1.0, color=MUTED, zorder=1))\n")

# ---- ROC / PR curves: with one hue, lightness alone should not carry identity,
# so the curves take the same long-dash patterns the other line charts use
sub('ax.plot(x, y, color=COLOR[tag], lw=1.5,', 'ax.plot(x, y, color=COLOR[tag], lw=1.5, dashes=DASH[tag],', 1)

# ---- remaining accent hues and tints -> the blue ramp (fills stay light so text stays legible)
for a, b in {
    "#eb6834": "#3987e5", "#1baf7a": "#1c5cab", "#4a3aa7": "#0d366b",
    "#d03b3b": "#0d366b", "#0ca30c": "#3987e5", "#eda100": "#256abf", "#fab219": "#6da7ec",
    "#fdf3ee": "#eaf2fd", "#eefaf5": "#dbe9fb", "#f2f0fa": "#e3eefc", "#fdf1f1": "#cde2fb",
    "#fff9ec": "#f4f7fc",
}.items():
    src = src.replace(a, b)
# the RGB channel colors of Figure S12: three blue steps, told apart by the existing line styles
sub('chan_colors = {"R": "#0d366b", "G": "#3987e5", "B": "#2a78d6"}',
    'chan_colors = {"R": "#0d366b", "G": "#6da7ec", "B": "#2a78d6"}', 1)

# ---- 600 dpi PNGs, written to mdpi-diagnostics/figures
sub('dpi=400 if ext == "png" else None', 'dpi=600 if ext == "png" else None', 1)

ns = {"__name__": "make_figures_diagnostics", "__file__": str(SRC)}
exec(compile(src, str(SRC), "exec"), ns)
OUT.mkdir(exist_ok=True)
ns["FIGS"] = OUT
for name, fn in ns["BUILDERS"].items():
    if name == "gradcam":          # Figure S10 has its own builder (external panels only)
        continue
    fn()
print("done ->", OUT)
