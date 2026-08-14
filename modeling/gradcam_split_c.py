"""
Grad-CAM on Split C (external) images for Model 4 (EfficientNet-B0).

Follow-up to the capture-method confound investigation
(data/metadata/capture_method_confound_findings.md): if the model is
failing on Split C because its high resolution/dark brightness don't match
anything learned from Kaggle's bright/tiny/heavily-compressed images
(rather than because it's "looking at the wrong part of the packaging"),
Grad-CAM on these specific external images should show either diffuse,
unfocused attention or attention on regions that make no packaging sense
(since the input distribution itself is unfamiliar) -- as opposed to a
crisp, wrong-but-confident focus on some analogous confound.

Rebuilds the same Split B final-fit Model 4 as gradcam.py (deterministic,
same seed/procedure), then runs Grad-CAM on a sample of Split C images:
several the model got wrong (called counterfeit) and the few it got right
(called authentic).

Output: modeling/results/gradcam_split_c/*.png + manifest.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import build_transform, IMG_SIZE, RAW
from train_model4_efficientnet import build_backbone
from gradcam import rebuild_split_b_model, compute_gradcam, overlay_heatmap

ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_PROV = ROOT / "data" / "metadata" / "split_c_candidate_provenance.csv"
OUT_DIR = Path(__file__).resolve().parent / "results" / "gradcam_split_c"
OUT_DIR.mkdir(parents=True, exist_ok=True)
N_SAMPLE_EACH = 10


def load_split_c_examples():
    with open(CANDIDATE_PROV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [{"image_id": r["image_id"], "path": RAW / r["orig_relpath"]} for r in rows]


def main():
    print("Rebuilding Split B final-fit Model 4...")
    head, _ = rebuild_split_b_model()
    feature_extractor, gap = build_backbone()
    # eval() is required: build_backbone() returns a FRESH module in training
    # mode (get_features caches and eval()s a different instance), so without
    # this the 49 BatchNorm layers use batch-of-1 statistics and overwrite
    # their running averages on every Grad-CAM call. Found 2026-07-30.
    feature_extractor.eval()

    examples = load_split_c_examples()

    from feature_cache import extract_features
    print(f"Scoring all {len(examples)} Split C images...")
    fake_examples = [{"image_id": e["image_id"], "path": e["path"], "label": 0,
                       "split": "split_c", "product_identity": e["image_id"], "cv_fold": None}
                      for e in examples]
    X, y, ids = extract_features(feature_extractor, gap, fake_examples, train=False, k_augment=1)
    with torch.no_grad():
        logits = head(torch.as_tensor(X, dtype=torch.float32))
        probs = torch.softmax(logits, dim=1)[:, 1].numpy()

    id_to_path = {e["image_id"]: e["path"] for e in examples}
    scored = list(zip(ids, probs))
    wrong = [(i, p) for i, p in scored if p >= 0.5]   # predicted counterfeit (wrong, since all are authentic)
    correct = [(i, p) for i, p in scored if p < 0.5]  # predicted authentic (correct)
    print(f"Predicted counterfeit (wrong): {len(wrong)} / {len(scored)}")
    print(f"Predicted authentic (correct): {len(correct)} / {len(scored)}")

    import random
    rng = random.Random(42)
    wrong_sample = rng.sample(wrong, min(N_SAMPLE_EACH, len(wrong)))
    correct_sample = rng.sample(correct, min(N_SAMPLE_EACH, len(correct)))

    manifest = []
    for group_name, sample in (("wrong_called_counterfeit", wrong_sample),
                                ("correct_called_authentic", correct_sample)):
        for image_id, prob in sample:
            path = id_to_path[image_id]
            pred_class = 1 if prob >= 0.5 else 0
            base_img, cam_img = compute_gradcam(feature_extractor, gap, head, path, pred_class)
            overlay = overlay_heatmap(base_img, cam_img)
            fname = f"{group_name}__{image_id}.png"
            overlay.save(OUT_DIR / fname)
            manifest.append({"group": group_name, "image_id": image_id, "y_prob_counterfeit": prob,
                              "file": fname, "attention_pattern": "", "notes": ""})
            print(f"  saved {fname} (p_counterfeit={prob:.3f})")

    manifest_path = OUT_DIR / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    print(f"\nWrote {manifest_path} ({len(manifest)} images)")


if __name__ == "__main__":
    main()
