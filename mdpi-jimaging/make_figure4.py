"""Figure 4 (J Imaging): the region-substitution intervention, shown on one image.

Uses the production code path of modeling/region_substitution.py unchanged:
the image goes through PharmaImageDataset(normalize=True) (three-way
normalization, 224x224, ImageNet standardization), and the regions are
overwritten by region_substitution.substitute with half_frame_masks. The
tensors are then de-standardized for display only. No model is run; the
numbers belong to Table 8 and are not drawn here.

The photograph is from the Mendeley archive (CC BY 4.0), condition C.
Usage: python make_figure4.py [index]   (index into split_c_examples, default 0)
Output: figures/fig16_region_substitution.{pdf,png}
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "modeling"))
from common import PharmaImageDataset, IMAGENET_MEAN, IMAGENET_STD, IMG_SIZE, SEED  # noqa: E402
from eval_external_from_checkpoints import split_c_examples                     # noqa: E402
from region_substitution import half_frame_masks, substitute                     # noqa: E402

idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
ex = split_c_examples()
x = PharmaImageDataset([ex[idx]], train=False, normalize=True)[0][0].unsqueeze(0)
outer, inner = half_frame_masks()


def show(t):
    m = torch.tensor(IMAGENET_MEAN).view(3, 1, 1); s = torch.tensor(IMAGENET_STD).view(3, 1, 1)
    return (t[0] * s + m).clamp(0, 1).permute(1, 2, 0).numpy()


def sub(mask, fill):
    g = torch.Generator(); g.manual_seed(SEED)
    return substitute(x, mask, fill, g)


panels = [("(a) Intact", x), ("(b) Outer → mean", sub(outer, "mean")), ("(c) Outer → noise", sub(outer, "noise")),
          ("(d) Inner → mean", sub(inner, "mean")), ("(e) Inner → noise", sub(inner, "noise"))]
side = int(round(IMG_SIZE * np.sqrt(0.5))); off = (IMG_SIZE - side) // 2
plt.rcParams.update({"font.family": "Arial", "font.size": 9})
fig, axes = plt.subplots(1, 5, figsize=(7.2, 1.85))
for ax, (title, t) in zip(axes, panels):
    ax.imshow(show(t), interpolation="nearest")
    ax.add_patch(plt.Rectangle((off - 0.5, off - 0.5), side, side, fill=False, ls="--", lw=0.9, ec="#f4f7fc"))
    ax.add_patch(plt.Rectangle((off - 0.5, off - 0.5), side, side, fill=False, ls=(4, (4, 4)), lw=0.9, ec="#0d366b"))
    ax.set_title(title, fontsize=9, pad=4)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#b0b8c4"); sp.set_linewidth(0.6)
fig.tight_layout(pad=0.4, w_pad=0.6)
out = HERE / "figures" / "fig16_region_substitution"
fig.savefig(str(out) + ".pdf", bbox_inches="tight")
fig.savefig(str(out) + ".png", dpi=600, bbox_inches="tight")
print("wrote", out, "from", ex[idx])
