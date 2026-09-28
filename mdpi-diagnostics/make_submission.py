"""Assemble the Diagnostics (MDPI) submission folder.

Usage: python make_submission.py <MDPI template Definitions dir>
Output: mdpi-diagnostics/submission_diagnostics/
  01_manuscript.pdf                 MDPI LaTeX template build
  02_manuscript_latex_source.zip    manuscript.tex + Definitions/ + figures/ (recompilable; no PDF inside)
  03_supplementary_materials.pdf    supplement with Figures S1-S12 and Tables S1-S29
  04_supplementary_materials.zip    the supplement PDF + Figures S1-S12 (600 dpi PNG and vector PDF)
  05_figures.zip                    Figures 1-3 (600 dpi PNG and vector PDF)
  06_graphical_abstract.png         graphical abstract, 2400 x 1200 px RGB (not a copy of any figure)
  07_cover_letter.pdf / .md         cover letter
  08_SUBMISSION_CHECKLIST.md        requirements vs. status (copied)
  MANIFEST.md                       SHA-256 of every file
"""
import hashlib, io, os, shutil, subprocess, sys, zipfile

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
DEFS = sys.argv[1]
OUT = os.path.join(HERE, "submission_diagnostics")
BUILD = os.path.join(HERE, "_latex_build")
FIG = os.path.join(HERE, "figures")

# Main-text and supplementary figure numbers -> source files (see the FIGURE lines in the .md files)
MAIN_FIGS = {1: "fig15_mechanism", 2: "fig03_capture_confound", 3: "fig08_external_generalisation"}
SUPP_FIGS = {1: "fig01_workflow", 2: "fig02_architectures", 3: "fig13_leakage", 4: "fig04_roc",
             5: "fig05_pr", 6: "fig06_confusion_ab", 7: "fig07_training_curves", 8: "fig11_calibration",
             9: "fig09_confusion_synthetic", 10: "figS10_gradcam_external", 11: "fig10_ablation",
             12: "fig12_model1_attribution"}


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    print(r.stdout.strip()[-800:])
    if r.returncode:
        print(r.stderr[-3000:]); sys.exit(f"failed: {cmd}")


def png600(stem):
    """600 dpi RGB PNG rasterized from the vector PDF (MDPI asks for >= 600 dpi)."""
    pix = pymupdf.open(os.path.join(FIG, stem + ".pdf"))[0].get_pixmap(dpi=600, alpha=False)
    pix.set_dpi(600, 600)
    return pix.tobytes("png")


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

# ---- figures first, so every PDF below embeds the current ones
run([sys.executable, os.path.join(HERE, "make_figures_diagnostics.py")])
run([sys.executable, os.path.join(HERE, "make_figure_s10.py")])
run([sys.executable, os.path.join(HERE, "make_graphical_abstract.py")])

# ---- manuscript: template PDF, LaTeX source ZIP, plain reading copy
run([sys.executable, os.path.join(HERE, "build_mdpi_tex.py"), BUILD, DEFS])
run([sys.executable, os.path.join(HERE, "build_pdf.py"), "manuscript"])
shutil.copy(os.path.join(BUILD, "manuscript.pdf"), os.path.join(OUT, "01_manuscript.pdf"))
with zipfile.ZipFile(os.path.join(OUT, "02_manuscript_latex_source.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    # Source only: no compiled PDF (uploaded separately; SuSy reads any extra PDF
    # in the archive as supplementary material) and no build artifacts.
    z.write(os.path.join(BUILD, "manuscript.tex"), "manuscript.tex")
    for sub in ("Definitions", "figures"):
        for root, _, files in os.walk(os.path.join(BUILD, sub)):
            for f in files:
                if f.endswith("-eps-converted-to.pdf"):
                    continue
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, BUILD))

# ---- supplement: PDF, and a ZIP of the PDF plus its figures
run([sys.executable, os.path.join(HERE, "build_pdf.py"), "supplementary"])
shutil.copy(os.path.join(HERE, "supplementary.pdf"), os.path.join(OUT, "03_supplementary_materials.pdf"))
with zipfile.ZipFile(os.path.join(OUT, "04_supplementary_materials.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(HERE, "supplementary.pdf"), "Supplementary_Materials.pdf")
    for n, stem in SUPP_FIGS.items():
        z.writestr(f"Figure_S{n}.png", png600(stem))
        z.write(os.path.join(FIG, stem + ".pdf"), f"Figure_S{n}.pdf")

# ---- main-text figures
with zipfile.ZipFile(os.path.join(OUT, "05_figures.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for n, stem in MAIN_FIGS.items():
        z.writestr(f"Figure_{n}.png", png600(stem))
        z.write(os.path.join(FIG, stem + ".pdf"), f"Figure_{n}.pdf")

# ---- graphical abstract, cover letter, checklist
shutil.copy(os.path.join(FIG, "graphical_abstract.png"), os.path.join(OUT, "06_graphical_abstract.png"))
shutil.copy(os.path.join(HERE, "cover_letter.md"), os.path.join(OUT, "07_cover_letter.md"))
run(["pandoc", os.path.join(HERE, "cover_letter.md"), "-o", os.path.join(OUT, "07_cover_letter.pdf"),
     "--pdf-engine=xelatex", "-V", "mainfont=Cambria", "-V", "geometry:margin=2.5cm", "-V", "fontsize=11pt"])
shutil.copy(os.path.join(HERE, "SUBMISSION_CHECKLIST.md"), os.path.join(OUT, "08_SUBMISSION_CHECKLIST.md"))

rows = []
for f in sorted(os.listdir(OUT)):
    h = hashlib.sha256(open(os.path.join(OUT, f), "rb").read()).hexdigest()
    rows.append(f"| `{f}` | {os.path.getsize(os.path.join(OUT, f)):,} | `{h}` |")
io.open(os.path.join(OUT, "MANIFEST.md"), "w", encoding="utf-8").write(
    "# Diagnostics submission package\n\nBuilt by `mdpi-diagnostics/make_submission.py` from `manuscript.md` "
    "and `supplementary.md`.\n\n| File | Bytes | SHA-256 |\n|---|---|---|\n" + "\n".join(rows) + "\n")
print("\n".join(rows))
