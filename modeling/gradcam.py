"""
Grad-CAM bias audit for Model 4 (EfficientNet-B0), Split B (plan Part 4.5).

Rebuilds the exact Split B final-fit model (deterministic given fixed seed,
same procedure as train_model4_efficientnet.py) since that script does not
persist the trained head to disk. Then, for a sample of correct and
incorrect predictions on the val+test partitions, computes a standard
Grad-CAM heatmap (Selvaraju et al. 2017) targeting each image's PREDICTED
class, and saves an overlay PNG for manual visual categorization: does the
model's attention fall on packaging-relevant regions (logo, seal, text
block) or incidental regions (background, edges, watermark)?

Sample size note: at this model's accuracy (99% test, 95% val), there are
only 5 misclassified images total across val+test (1 test + 4 val) — the
plan's "~10-15 incorrect predictions" target assumed a less accurate model.
All 5 available errors are used rather than padding the count artificially.
~15 correct predictions are sampled for contrast.

Output: modeling/results/gradcam/*.png + modeling/results/gradcam/manifest.csv
"""
import csv
import random
from pathlib import Path
import sys

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, build_transform, IMG_SIZE
from train_model4_efficientnet import get_features, build_head, build_backbone
from torch_utils import train_model_on_features, evaluate_model_on_features
from result_io import load_chosen_lr

OUT_DIR = Path(__file__).resolve().parent / "results" / "gradcam"
OUT_DIR.mkdir(parents=True, exist_ok=True)
N_CORRECT_SAMPLE = 15


def rebuild_split_b_model():
    """Deterministically reproduces the trained Split B final-fit model
    from train_model4_efficientnet.py (same seed, same call sequence)."""
    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}

    # Training features are no longer extracted: this path loads the persisted
    # head rather than retraining, so the 1,071 augmented forward passes over
    # the training partition were pure waste (and the main reason a re-run of
    # this script used to exceed the host's tolerance for long processes).
    X_val, y_val, val_ids = get_features(by_split["val"], train=False, k_augment=1)
    X_test, y_test, test_ids = get_features(by_split["test"], train=False, k_augment=1)
    # Load the persisted production head instead of retraining it. Before
    # checkpoints existed this path retrained, which is what produced the
    # 16/150-vs-5/150 divergence recorded in modeling/README.md; loading makes
    # the model shown in these heatmaps provably the model of record.
    from result_io import load_checkpoint
    head = build_head()
    load_checkpoint(head, "model4_efficientnetb0_frozen", "split_b_final",
                    expected_lr=load_chosen_lr("model4_efficientnetb0_frozen"))
    head.eval()

    val_ids2, val_true, val_prob = evaluate_model_on_features(head, X_val, y_val, val_ids)
    test_ids2, test_true, test_prob = evaluate_model_on_features(head, X_test, y_test, test_ids)

    example_by_id = {e["image_id"]: e for e in examples}
    records = []
    for ids, ytrue, yprob, part in ((val_ids2, val_true, val_prob, "val"),
                                     (test_ids2, test_true, test_prob, "test")):
        for iid, yt, yp in zip(ids, ytrue, yprob):
            records.append({"image_id": iid, "y_true": yt, "y_prob": yp,
                             "y_pred": int(yp >= 0.5), "partition": part,
                             "path": example_by_id[iid]["path"]})
    return head, records


def compute_gradcam(feature_extractor, gap, head, image_path, target_class):
    transform = build_transform(train=False)
    img = Image.open(image_path).convert("RGB")
    x = transform(img).unsqueeze(0)

    A = feature_extractor(x)
    A = A.detach().requires_grad_(True)
    pooled = gap(A).flatten(1)
    logits = head(pooled)
    score = logits[0, target_class]
    grads = torch.autograd.grad(score, A)[0]

    weights = grads.mean(dim=(2, 3), keepdim=True)
    cam = F.relu((weights * A).sum(dim=1, keepdim=True))
    cam = cam.squeeze().detach().numpy()
    cam = cam - cam.min()
    if cam.max() > 0:
        cam = cam / cam.max()

    cam_img = Image.fromarray((cam * 255).astype(np.uint8)).resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    return img.resize((IMG_SIZE, IMG_SIZE)), cam_img


def overlay_heatmap(base_img: Image.Image, cam_img: Image.Image) -> Image.Image:
    heat = np.array(cam_img).astype(np.float32) / 255.0
    # simple red-channel heatmap overlay (no matplotlib dependency)
    heat_rgb = np.zeros((*heat.shape, 3), dtype=np.uint8)
    heat_rgb[..., 0] = (heat * 255).astype(np.uint8)          # red = high activation
    heat_rgb[..., 2] = ((1 - heat) * 255).astype(np.uint8)    # blue = low activation
    heat_img = Image.fromarray(heat_rgb).convert("RGB")
    return Image.blend(base_img.convert("RGB"), heat_img, alpha=0.45)


def main():
    print("Rebuilding Split B final-fit Model 4...")
    head, records = rebuild_split_b_model()
    feature_extractor, gap = build_backbone()
    # eval() is required: build_backbone() returns a FRESH module in training
    # mode (get_features caches and eval()s a different instance), so without
    # this the 49 BatchNorm layers use batch-of-1 statistics and overwrite
    # their running averages on every Grad-CAM call. Found 2026-07-30.
    feature_extractor.eval()

    incorrect = [r for r in records if r["y_pred"] != r["y_true"]]
    correct = [r for r in records if r["y_pred"] == r["y_true"]]
    print(f"Errors available: {len(incorrect)} (using all). Correct pool: {len(correct)}.")

    rng = random.Random(SEED)
    correct_sample = rng.sample(correct, min(N_CORRECT_SAMPLE, len(correct)))

    manifest = []
    for group_name, recs in (("incorrect", incorrect), ("correct", correct_sample)):
        for r in recs:
            base_img, cam_img = compute_gradcam(feature_extractor, gap, head, r["path"], r["y_pred"])
            overlay = overlay_heatmap(base_img, cam_img)
            fname = f"{group_name}__{r['image_id']}.png"
            overlay.save(OUT_DIR / fname)
            manifest.append({
                "group": group_name, "image_id": r["image_id"], "partition": r["partition"],
                "y_true": r["y_true"], "y_pred": r["y_pred"], "y_prob": r["y_prob"],
                "gradcam_target_class": r["y_pred"], "file": fname,
                "packaging_relevant": "",  # filled in by manual visual review
                "notes": "",
            })
            print(f"  saved {fname}")

    manifest_path = OUT_DIR / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    print(f"\nWrote {manifest_path} ({len(manifest)} images)")


if __name__ == "__main__":
    main()
