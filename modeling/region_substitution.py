"""
Which region carries the corrected models' external "authentic" verdict?

Gap this closes. Section VI-E leaves M4's recovered external specificity
unexplained: the occlusion analysis returns a border mass of 0.614 [0.585,
0.643] on its correct answers, indistinguishable from the 0.642 uniform
reference, so it cannot say whether the decision rests on the photographic
surround or on the product. Occlusion asks a local question -- how much does
hiding *this patch* move the score -- and a decision distributed over a large
region answers it weakly no matter where that region is. This script asks the
global question instead: destroy one region outright and see whether the
verdict survives.

Design. Every Split C and Split D image is authentic, so accuracy here is
specificity throughout. Each image is put through the production pipeline
exactly as eval_external_from_checkpoints does -- three-way normalization,
224x224, ImageNet standardization -- and then one region of the resulting
tensor is overwritten before the forward pass:

    intact          control; must reproduce the specificity of record
    outer -> mean   everything outside a centre square, set to the ImageNet
                    channel mean (zero in standardized space)
    inner -> mean   the centre square itself, set to the same value
    outer -> noise  the same region, set to standard normal noise
    inner -> noise  likewise

The centre square covers half the frame (158 of 224 px per side, 0.4975 of
the area), so "outer" and "inner" are area-matched to within half a point.
That matters: substituting a region is itself a distribution shift, and a
model whose specificity fell under *any* large substitution would tell us
nothing. Only the asymmetry between the two directions is interpretable, and
an area-matched pair is what makes the asymmetry readable. The 0.642/0.161
border ring of gradcam_quantitative.ring_masks is reported alongside for
continuity with the occlusion analysis, but it is not area-matched and the
half-frame pair is the one to read.

Two fills rather than one because they fail differently. The channel mean is
the fill the occlusion analysis uses and is a flat, low-entropy region; noise
is high-entropy. A model keying on the *texture* of the dark backdrop and one
keying on its *level* would respond differently to the two.

What this can and cannot establish. It identifies the region a decision needs,
not the feature within it, and it cannot distinguish "the model reads the
surround" from "the model reads a product cue that the substitution disturbs
at the boundary". It is evidence about locality, which is exactly what
Section VI-E is missing, and it needs no annotation, which is what the
content-aware measure of Section IX still waits on.

The intact condition is asserted against the value of record before anything
is reported, per the practice Section S-I-G argues for.

    python modeling/region_substitution.py

Output: modeling/results/region_substitution.csv
"""
import csv
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import PharmaImageDataset, IMG_SIZE, set_seed, SEED   # noqa: E402
from eval_external_from_checkpoints import (split_c_examples,      # noqa: E402
                                            split_d_examples)
from gradcam_quantitative import ring_masks                        # noqa: E402
from occlusion_sensitivity import load_model, prob_authentic       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "modeling" / "results" / "region_substitution.csv"

# Specificity of record, production pipeline, seed 42 (Table 7 of the paper).
OF_RECORD = {
    ("model3_mobilenetv3small_frozen", "split_c"): 116,
    ("model4_efficientnetb0_frozen", "split_c"): 121,
    ("model3_mobilenetv3small_frozen", "split_d"): 108,
    ("model4_efficientnetb0_frozen", "split_d"): 124,
}

FIELDS = ["model", "split", "region", "fill", "area_fraction",
          "k_authentic", "n", "specificity", "delta_vs_intact"]


def half_frame_masks(n=IMG_SIZE):
    """A centre square covering half the frame, and its complement."""
    side = int(round(n * np.sqrt(0.5)))
    off = (n - side) // 2
    inner = np.zeros((n, n), dtype=bool)
    inner[off:off + side, off:off + side] = True
    return ~inner, inner            # outer, inner


def substitute(x, mask, fill, generator):
    """Overwrite the masked region of a standardized image batch."""
    out = x.clone()
    m = torch.as_tensor(mask)
    if fill == "mean":
        # Zero in ImageNet-standardized space *is* the channel mean.
        out[:, :, m] = 0.0
    elif fill == "noise":
        noise = torch.randn(out.shape[0], out.shape[1], int(m.sum()),
                            generator=generator)
        out[:, :, m] = noise
    else:
        raise ValueError(fill)
    return out


@torch.no_grad()
def evaluate(fe, gap, head, tensors, mask, fill, generator):
    """Count images called authentic under one substitution."""
    k, n = 0, 0
    for start in range(0, len(tensors), 32):
        x = tensors[start:start + 32]
        if mask is not None:
            x = substitute(x, mask, fill, generator)
        p = prob_authentic(fe, gap, head, x)
        k += int((p >= 0.5).sum())
        n += x.shape[0]
    return k, n


def normalized_tensors(examples):
    """The production pipeline's input tensors, computed once per split.

    The three-way operator re-encodes every image through JPEG, which dominates
    the runtime; every condition below sees the same tensors, so deriving them
    once is both faster and a guarantee that two conditions cannot differ by
    anything other than the substitution.
    """
    ds = PharmaImageDataset(examples, train=False, normalize=True)
    return torch.stack([ds[i][0] for i in range(len(ds))])


def load_done():
    if not OUT.exists():
        return []
    with open(OUT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(rows):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def main():
    outer_half, inner_half = half_frame_masks()
    border_ring, centre_box = ring_masks()

    conditions = [
        ("intact", None, "-"),
        ("outer half-frame", outer_half, "mean"),
        ("inner half-frame", inner_half, "mean"),
        ("outer half-frame", outer_half, "noise"),
        ("inner half-frame", inner_half, "noise"),
        ("border ring (0.642)", border_ring, "mean"),
        ("centre box (0.161)", centre_box, "mean"),
    ]

    splits = {"split_c": split_c_examples(), "split_d": split_d_examples()}
    print("normalizing both external sets once ...")
    tensors = {k: normalized_tensors(v) for k, v in splits.items()}
    for k, v in tensors.items():
        print(f"  {k}: {tuple(v.shape)}")

    rows = load_done()
    done = {(r["model"], r["split"], r["region"], r["fill"]) for r in rows}

    for which in (3, 4):
        name, fe, gap, head = load_model(which)
        for split_name in splits:
            intact_spec = None
            for region, mask, fill in conditions:
                if region != "intact" and intact_spec is None:
                    prior = [r for r in rows if r["model"] == name
                             and r["split"] == split_name
                             and r["region"] == "intact"]
                    if prior:
                        intact_spec = float(prior[0]["specificity"])
                if (name, split_name, region, fill) in done:
                    print(f"      skip {region} {fill} (recorded)")
                    continue
                # Fixed generator per condition: the noise fill must not depend
                # on what ran before it, which is the defect of Section S-I-G.
                g = torch.Generator()
                g.manual_seed(SEED)
                set_seed(SEED)
                k, n = evaluate(fe, gap, head, tensors[split_name], mask, fill, g)
                spec = k / n

                if region == "intact":
                    intact_spec = spec
                    expected = OF_RECORD.get((name, split_name))
                    if expected is not None and k != expected:
                        raise SystemExit(
                            f"ABORT: {name} {split_name} intact returned {k}/{n}, "
                            f"expected {expected}/{n} of record. Nothing is "
                            f"reported from a pipeline that does not reproduce "
                            f"its own published number.")
                    print(f"  [ok] {name} {split_name} intact reproduces "
                          f"{k}/{n} of record")

                area = "-" if mask is None else round(float(mask.mean()), 4)
                rows.append({
                    "model": name, "split": split_name, "region": region,
                    "fill": fill, "area_fraction": area,
                    "k_authentic": k, "n": n,
                    "specificity": round(spec, 4),
                    "delta_vs_intact": round(spec - intact_spec, 4),
                })
                save(rows)
                print(f"      {region:22s} {fill:6s} "
                      f"{k:3d}/{n}  {spec:.4f}  "
                      f"({spec - intact_spec:+.4f})")

    print(f"\nwrote {OUT.relative_to(ROOT)}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
