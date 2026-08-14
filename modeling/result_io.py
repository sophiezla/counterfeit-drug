"""Shared result-writing helpers (predictions + per-model metrics CSV +
the record of which learning rate each model actually trained with)."""
import csv
import json

from common import RESULTS_DIR

CHOSEN_LRS = RESULTS_DIR / "chosen_lrs.json"


def save_chosen_lr(model_name, lr):
    """Record the LR a training run actually used.

    Downstream scripts (eval_split_c.py, eval_split_c_synthetic.py, gradcam*.py)
    rebuild each model from scratch because no checkpoint is persisted, and they
    used to hard-code the LR. That went out of sync twice: once when Model 2 was
    retrained at 3e-4 while the eval script still said 1e-3, and again after the
    3-way-normalisation retrain, when Model 2's LR search selected 1e-3 while the
    eval script had been left at 3e-4. Writing the value here and reading it
    back removes the hand-sync step entirely.
    """
    data = load_all_chosen_lrs()
    data[model_name] = float(lr)
    CHOSEN_LRS.parent.mkdir(parents=True, exist_ok=True)
    with open(CHOSEN_LRS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"  recorded lr={lr} for {model_name} in {CHOSEN_LRS.name}")


def load_all_chosen_lrs():
    if not CHOSEN_LRS.exists():
        return {}
    with open(CHOSEN_LRS, encoding="utf-8") as f:
        return json.load(f)


def load_chosen_lr(model_name):
    """Fail loudly rather than silently rebuilding a model at the wrong LR."""
    data = load_all_chosen_lrs()
    if model_name not in data:
        raise KeyError(
            f"no recorded learning rate for {model_name} in {CHOSEN_LRS}. "
            f"Re-run modeling/train_{model_name.split('_')[0]}*.py, which writes it, "
            f"or add the value by hand from that model's training log."
        )
    return data[model_name]


def save_predictions(model_name, run_name, ids, y_true, y_prob):
    out = RESULTS_DIR / "predictions" / f"{model_name}__{run_name}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "y_true", "y_prob"])
        for i, yt, yp in zip(ids, y_true, y_prob):
            w.writerow([i, yt, yp])


class MetricsAccumulator:
    """Collects rows with heterogeneous columns (e.g. single-fit reports vs.
    5-fold CV summaries) and writes them with a unioned header at the end,
    avoiding misaligned-column bugs from incremental DictWriter appends."""

    def __init__(self, model_name):
        self.model_name = model_name
        self.rows = []

    def add(self, run_name, split_protocol, partition, metrics_dict):
        row = {"model": self.model_name, "run": run_name,
               "split_protocol": split_protocol, "partition": partition, **metrics_dict}
        self.rows.append(row)

    def flush(self):
        out = RESULTS_DIR / f"metrics_{self.model_name}.csv"
        all_keys = []
        for row in self.rows:
            for k in row:
                if k not in all_keys:
                    all_keys.append(k)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=all_keys)
            w.writeheader()
            for row in self.rows:
                w.writerow(row)
        print(f"Wrote {out}")


def checkpoint_path(model_name, run_tag):
    """Where _run_training_loop persists the restored best-validation state."""
    return RESULTS_DIR / "checkpoints" / f"{model_name}__{run_tag}.pt"


def load_checkpoint(model, model_name, run_tag, expected_lr=None):
    """Load persisted weights into `model`, verifying provenance.

    Returns the checkpoint metadata dict. Raises if the file is absent or if it
    was trained at a learning rate other than the one the caller expects --
    the failure mode that produced Model 2's stale-LR divergence. Callers that
    can tolerate a missing checkpoint should catch FileNotFoundError and fall
    back to retraining.
    """
    import torch

    path = checkpoint_path(model_name, run_tag)
    if not path.exists():
        raise FileNotFoundError(
            f"no checkpoint at {path}. Re-run the training script for "
            f"{model_name}, which writes one, or retrain in-process."
        )
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    if expected_lr is not None and abs(ckpt["lr"] - float(expected_lr)) > 1e-12:
        raise ValueError(
            f"{path.name} was trained at lr={ckpt['lr']} but the caller expects "
            f"{expected_lr}. Refusing to load a model trained differently from "
            f"the one being reported."
        )
    model.load_state_dict(ckpt["state_dict"])
    return ckpt
