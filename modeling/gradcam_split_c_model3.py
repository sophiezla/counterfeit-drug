"""
Grad-CAM on Split C (external) images for Model 3 (MobileNetV3-Small),
mirroring gradcam_split_c.py but for the model whose pretrained features
turned out to be unusually robust to the capture-method confound (Finding
6-7 in data/metadata/capture_method_confound_findings.md). Question: does
Model 3's much-better (80% vs Model 4's 8.7%) un-normalized Split C
accuracy come from genuinely attending to the product, or from a
different, still-incidental cue it happens to have learned that merely
transfers better?

Output: modeling/results/gradcam_split_c_model3/*.png + manifest.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, RAW
from train_model3_mobilenet import build_backbone, build_head, get_features, MODEL_NAME
from result_io import load_chosen_lr
from torch_utils import train_model_on_features, evaluate_model_on_features
from feature_cache import extract_features
from gradcam import compute_gradcam, overlay_heatmap

ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_PROV = ROOT / "data" / "metadata" / "split_c_candidate_provenance.csv"
OUT_DIR = Path(__file__).resolve().parent / "results" / "gradcam_split_c_model3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
N_SAMPLE_EACH = 10


def rebuild_split_b_model3():
    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}
    X_train, y_train, _ = get_features(by_split["train"], train=True, k_augment=3)
    X_val, y_val, _ = get_features(by_split["val"], train=False, k_augment=1)
    # Recorded LR, not a fresh search -- same fix as gradcam.py, so this
    # rebuild matches eval_split_c.py's trained head exactly.
    # Load the persisted production head instead of retraining it. Before
    # checkpoints existed this path retrained, which is what produced the
    # 16/150-vs-5/150 divergence recorded in modeling/README.md; loading makes
    # the model shown in these heatmaps provably the model of record.
    from result_io import load_checkpoint
    head = build_head()
    load_checkpoint(head, MODEL_NAME, "split_b_final",
                    expected_lr=load_chosen_lr(MODEL_NAME))
    head.eval()
    head.eval()
    return head


def load_split_c_examples():
    with open(CANDIDATE_PROV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [{"image_id": r["image_id"], "path": RAW / r["orig_relpath"]} for r in rows]


def main():
    print("Rebuilding Split B final-fit Model 3...")
    head = rebuild_split_b_model3()
    feature_extractor, gap = build_backbone()
    # eval() is required: build_backbone() returns a FRESH module in training
    # mode (get_features caches and eval()s a different instance), so without
    # this the 49 BatchNorm layers use batch-of-1 statistics and overwrite
    # their running averages on every Grad-CAM call. Found 2026-07-30.
    feature_extractor.eval()

    examples = load_split_c_examples()
    fake_examples = [{"image_id": e["image_id"], "path": e["path"], "label": 0,
                       "split": "split_c", "product_identity": e["image_id"], "cv_fold": None}
                      for e in examples]
    print(f"Scoring all {len(examples)} Split C images...")
    X, y, ids = extract_features(feature_extractor, gap, fake_examples, train=False, k_augment=1)
    with torch.no_grad():
        logits = head(torch.as_tensor(X, dtype=torch.float32))
        probs = torch.softmax(logits, dim=1)[:, 1].numpy()

    id_to_path = {e["image_id"]: e["path"] for e in examples}
    scored = list(zip(ids, probs))
    wrong = [(i, p) for i, p in scored if p >= 0.5]
    correct = [(i, p) for i, p in scored if p < 0.5]
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
