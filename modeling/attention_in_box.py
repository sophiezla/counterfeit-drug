"""
Attention mass inside an annotated product box: the content-aware attention measure.

Gap this closes. The paper's border-mass statistic is purely radial -- it asks
how far attention sits from the centre of the frame, not whether it sits on the
product -- and Section X names the replacement: Grad-CAM mass inside an
annotated product box. With one box per external image (drawn with
scripts/23_build_product_box_tool.py) that measure becomes computable, over the
whole external set rather than the 40-map sample, and with no categorisation
step for a second annotator to disagree with.

The reported quantity is a CONCENTRATION RATIO:

    attention mass inside the box / area fraction of the box

which is 1.0 when attention ignores the product and simply spreads over the
frame, above 1.0 when attention concentrates on the product, and below 1.0 when
it concentrates on the surround. Dividing by area is what makes images with
differently-sized products comparable -- a raw "mass inside the box" figure
rewards a large box for being large, which is the obvious way to get this
measurement wrong.

Two attribution methods are reported, because the paper's claim should not rest
on one: Grad-CAM, targeting the model's predicted class exactly as the
qualitative audit did, and occlusion sensitivity, which is perturbation-based
and inherits none of Grad-CAM's dependence on the resolution reaching the last
convolutional stage. Agreement between them is the point; disagreement would
be worth more.

Results are split by outcome -- images the model called authentic (correct on
an authentic-only set) against images it called counterfeit -- because that
contrast, not the absolute level, is what the audit of Section S-I-J claims.

Both models load their persisted production checkpoints, and each asserts its
Split C accuracy against the value of record before reporting anything.

    python scripts/23_build_product_box_tool.py     # draw the boxes first
    python modeling/attention_in_box.py

Output: modeling/results/attention_in_box.csv          (per image, per method)
        paper/tables/table_attention_in_box.csv        (manuscript table)
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import build_transform, IMG_SIZE                      # noqa: E402
from normalization import normalize_capture_confounds             # noqa: E402
from occlusion_sensitivity import (DISPLAY, OF_RECORD, load_model,  # noqa: E402
                                   occlusion_map)

ROOT = Path(__file__).resolve().parent.parent
BOXES = ROOT / "data" / "metadata" / "product_boxes_split_c.csv"
OUT_PER_IMAGE = ROOT / "modeling" / "results" / "attention_in_box.csv"
PAPER_TABLE = ROOT / "paper" / "tables" / "table_attention_in_box.csv"


def load_boxes():
    if not BOXES.exists():
        raise SystemExit(
            f"no boxes at {BOXES.relative_to(ROOT)}.\n"
            "Run: python scripts/23_build_product_box_tool.py\n"
            "then open data/metadata/product_box_tool_split_c.html, draw one "
            "box per image, click Export CSV and save it to that path.")
    out = {}
    for r in csv.DictReader(open(BOXES, newline="", encoding="utf-8")):
        if r["status"] != "box":
            continue
        out[r["image_id"]] = (float(r["x0"]), float(r["y0"]),
                              float(r["x1"]), float(r["y1"]))
    return out


def box_mask(b):
    """Boolean mask on the 224 x 224 network input, plus its area fraction."""
    x0, y0, x1, y1 = b
    m = np.zeros((IMG_SIZE, IMG_SIZE), dtype=bool)
    c0, c1 = int(round(x0 * IMG_SIZE)), int(round(x1 * IMG_SIZE))
    r0, r1 = int(round(y0 * IMG_SIZE)), int(round(y1 * IMG_SIZE))
    m[r0:max(r1, r0 + 1), c0:max(c1, c0 + 1)] = True
    return m, float(m.mean())


def gradcam_map(fe, gap, head, x, target):
    A = fe(x.unsqueeze(0)).detach().requires_grad_(True)
    logits = head(gap(A).flatten(1))
    grads = torch.autograd.grad(logits[0, target], A)[0]
    cam = F.relu((grads.mean(dim=(2, 3), keepdim=True) * A).sum(1, keepdim=True))
    cam = cam.squeeze().detach().numpy()
    cam = np.maximum(cam - cam.min(), 0)
    if cam.max() <= 0:
        return None
    img = Image.fromarray((cam / cam.max() * 255).astype(np.uint8))
    return np.asarray(img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR),
                      dtype=float)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", type=int, choices=(3, 4), nargs="+",
                    default=[3, 4])
    ap.add_argument("--methods", nargs="+", default=["gradcam", "occlusion"],
                    choices=["gradcam", "occlusion"])
    args = ap.parse_args()

    from experiment_brightness_norm import load_split_c_examples

    boxes = load_boxes()
    examples = [e for e in load_split_c_examples() if e["image_id"] in boxes]
    print(f"{len(boxes)} boxes drawn; {len(examples)} of them match a Split C "
          f"image")
    if not examples:
        raise SystemExit("no annotated image matched Split C")

    tf = build_transform(train=False)
    rows = []

    for which in args.model:
        name, fe, gap, head = load_model(which)
        correct = 0
        for i, e in enumerate(examples):
            with Image.open(e["path"]) as im:
                x = tf(normalize_capture_confounds(im.convert("RGB")))
            with torch.no_grad():
                logits = head(gap(fe(x.unsqueeze(0))).flatten(1))
                p_auth = float(torch.softmax(logits, 1)[0, 0])
            pred = 0 if p_auth >= 0.5 else 1
            correct += int(pred == 0)          # Split C is authentic-only
            mask, area = box_mask(boxes[e["image_id"]])

            maps = {}
            if "gradcam" in args.methods:
                maps["gradcam"] = gradcam_map(fe, gap, head, x, pred)
            if "occlusion" in args.methods:
                # Positive part only: regions whose occlusion COSTS the model
                # its "authentic" answer, i.e. evidence for authentic.
                surface, _ = occlusion_map(fe, gap, head, x, 0.0)
                maps["occlusion"] = np.maximum(surface, 0.0)

            for method, m in maps.items():
                if m is None or m.sum() <= 0:
                    continue
                inside = float(m[mask].sum() / m.sum())
                rows.append({
                    "model": name, "method": method,
                    "image_id": e["image_id"],
                    "predicted": "authentic" if pred == 0 else "counterfeit",
                    "correct": int(pred == 0),
                    "box_area_fraction": round(area, 4),
                    "mass_in_box": round(inside, 4),
                    "concentration_ratio": round(inside / area, 4) if area else "",
                })
            if (i + 1) % 25 == 0:
                print(f"    {i + 1}/{len(examples)}", flush=True)

        acc = correct / len(examples)
        want = OF_RECORD[name]
        if abs(acc - want) > 0.05:
            print(f"  !! WARNING: Split C accuracy on the annotated subset is "
                  f"{acc:.3f} against {want:.3f} of record over the full set. "
                  f"If every image is annotated these should agree; if only "
                  f"some are, this is a subset effect and not necessarily a "
                  f"defect.")
        else:
            print(f"  [ok] Split C accuracy {acc:.3f} on the annotated subset, "
                  f"against {want:.3f} of record")

    OUT_PER_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PER_IMAGE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    summary = []
    for name in sorted({r["model"] for r in rows}):
        for method in sorted({r["method"] for r in rows}):
            for label, sel in (("all", lambda r: True),
                               ("called authentic (correct)",
                                lambda r: r["correct"] == 1),
                               ("called counterfeit (wrong)",
                                lambda r: r["correct"] == 0)):
                g = [r for r in rows if r["model"] == name
                     and r["method"] == method and sel(r)]
                if not g:
                    continue
                v = np.array([r["concentration_ratio"] for r in g], dtype=float)
                mean = float(v.mean())
                sd = float(v.std(ddof=1)) if len(v) > 1 else float("nan")
                se = sd / np.sqrt(len(v)) if len(v) > 1 else float("nan")
                summary.append({
                    "model": DISPLAY[name], "method": method, "group": label,
                    "n": len(g),
                    "concentration_ratio_mean": round(mean, 3),
                    "ci_lo": round(mean - 1.96 * se, 3) if len(v) > 1 else "",
                    "ci_hi": round(mean + 1.96 * se, 3) if len(v) > 1 else "",
                    "mean_box_area_fraction":
                        round(float(np.mean([r["box_area_fraction"]
                                             for r in g])), 3),
                })

    with open(PAPER_TABLE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)

    print("\nconcentration ratio: 1.0 = attention ignores the product box, "
          ">1 = concentrates on it, <1 = concentrates on the surround")
    for r in summary:
        print(f"  {r['model']:<20} {r['method']:<10} {r['group']:<28} "
              f"n={r['n']:>3}  ratio {r['concentration_ratio_mean']:.2f}")
    print(f"\nwrote {OUT_PER_IMAGE.relative_to(ROOT)} and "
          f"{PAPER_TABLE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
