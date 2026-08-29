"""
Shared PyTorch training harness for Models 2, 3, 4 — common training
protocol per plan Part 3.2: fixed seed, Adam, early stopping on val loss
(patience 4), track both train and val loss/accuracy every epoch, documented
batch size.

Two training paths share the same core loop (`_run_training_loop`):
  - `train_model`: end-to-end on raw images (used by Model 2, which trains
    the whole network from scratch and needs fresh per-epoch augmentation
    reaching real conv filters).
  - `train_model_on_features`: on pre-extracted, cached backbone features
    (used by Models 3/4). Their backbones are frozen, so re-running a full
    MobileNetV3/EfficientNet-B0 forward pass every epoch on CPU is pure
    waste — the backbone output for a given (possibly augmented) input never
    changes during head-only training. Features are extracted once (see
    `extract_features` in each model's script, which builds a small
    augmented cache — e.g. 3 augmented passes per training image — instead
    of re-augmenting+re-extracting every epoch). This is standard "linear
    probing" practice for frozen-backbone transfer learning and is what
    made Model 4 (EfficientNet-B0) tractable at all on CPU-only hardware:
    the first attempt at real-time backbone forward passes every epoch was
    killed by the environment's runtime limit before Split A even finished.
"""
import csv
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from common import PharmaImageDataset, RESULTS_DIR, SEED

DEVICE = torch.device("cpu")  # no CUDA available in this environment
BATCH_SIZE = 32
MAX_EPOCHS = 50
PATIENCE = 4
# Frozen-backbone linear probing (Models 3/4) converges very smoothly, with
# per-epoch val-loss improvements of ~1e-4 to 1e-3 that never trip a naive
# patience counter -- observed empirically as a 46+ epoch run that never
# early-stopped. MIN_DELTA requires a *meaningful* improvement to reset
# patience, so training stops once gains are noise-level, not just nonzero.
MIN_DELTA = 1e-3


def make_loader(examples, train: bool, batch_size: int = BATCH_SIZE,
                 normalize: bool = True):
    # normalize=False is the un-normalized baseline condition; the default is
    # the production pipeline and is unchanged. feature_cache.extract_features
    # carries the same flag for the frozen-backbone path.
    ds = PharmaImageDataset(examples, train=train, normalize=normalize)
    g = torch.Generator()
    g.manual_seed(SEED)
    return DataLoader(ds, batch_size=batch_size, shuffle=train, generator=g if train else None,
                       num_workers=0)


def make_feature_loader(X, y, train: bool, batch_size: int = BATCH_SIZE):
    ds = TensorDataset(torch.as_tensor(X, dtype=torch.float32),
                        torch.as_tensor(y, dtype=torch.long))
    g = torch.Generator()
    g.manual_seed(SEED)
    return DataLoader(ds, batch_size=batch_size, shuffle=train, generator=g if train else None,
                       num_workers=0)


def compute_class_weights_from_labels(labels: np.ndarray):
    n = len(labels)
    n_pos = int(labels.sum())
    n_neg = n - n_pos
    w0 = n / (2 * n_neg) if n_neg > 0 else 1.0
    w1 = n / (2 * n_pos) if n_pos > 0 else 1.0
    return torch.tensor([w0, w1], dtype=torch.float32)


def compute_class_weights(examples):
    labels = np.array([e["label"] for e in examples])
    return compute_class_weights_from_labels(labels)


def _run_training_loop(model, train_loader, val_loader, lr, class_weights,
                        model_tag, run_tag, max_epochs, patience, has_ids):
    torch.manual_seed(SEED)
    model = model.to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(DEVICE))
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.Adam(trainable_params, lr=lr)

    history = []
    best_val_loss = float("inf")
    best_state = None
    epochs_no_improve = 0

    for epoch in range(max_epochs):
        model.train()
        train_loss, train_correct, train_n = 0.0, 0, 0
        for batch in train_loader:
            x, y = batch[0], batch[1]
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * x.size(0)
            train_correct += (logits.argmax(1) == y).sum().item()
            train_n += x.size(0)
        train_loss /= train_n
        train_acc = train_correct / train_n

        model.eval()
        val_loss, val_correct, val_n = 0.0, 0, 0
        with torch.no_grad():
            for batch in val_loader:
                x, y = batch[0], batch[1]
                x, y = x.to(DEVICE), y.to(DEVICE)
                logits = model(x)
                loss = criterion(logits, y)
                val_loss += loss.item() * x.size(0)
                val_correct += (logits.argmax(1) == y).sum().item()
                val_n += x.size(0)
        val_loss /= val_n
        val_acc = val_correct / val_n

        history.append({"epoch": epoch, "train_loss": train_loss, "train_acc": train_acc,
                         "val_loss": val_loss, "val_acc": val_acc})
        print(f"  epoch {epoch:2d}  train_loss={train_loss:.4f} train_acc={train_acc:.3f}  "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.3f}")

        if val_loss < best_val_loss - MIN_DELTA:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"  early stopping at epoch {epoch} (patience={patience})")
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    # Persist the restored best state. Until 2026-07-29 nothing in this project
    # saved weights, so every downstream consumer (eval_split_c, the synthetic
    # proxy, Grad-CAM) re-derived "the trained model" by retraining it. That is
    # what produced both reproducibility defects documented in the paper's
    # Section 6.5. Writing the checkpoint here makes the rebuild optional, and
    # storing lr/seed/best-epoch alongside it makes a mismatch detectable rather
    # than silent.
    ckpt_dir = RESULTS_DIR / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ckpt_dir / f"{model_tag}__{run_tag}.pt"
    torch.save({
        "state_dict": model.state_dict(),
        "model_tag": model_tag,
        "run_tag": run_tag,
        "lr": float(lr),
        "seed": SEED,
        "best_val_loss": float(best_val_loss),
        "best_epoch": int(min(range(len(history)),
                             key=lambda i: history[i]["val_loss"])) if history else -1,
        "epochs_run": len(history),
    }, ckpt_path)
    print(f"  saved checkpoint {ckpt_path.name}")

    curve_path = RESULTS_DIR / "curves" / f"{model_tag}__{run_tag}.csv"
    with open(curve_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "train_acc", "val_loss", "val_acc"])
        w.writeheader()
        w.writerows(history)

    return model, history


def train_model(model, train_examples, val_examples, lr, model_tag, run_tag,
                 max_epochs=MAX_EPOCHS, patience=PATIENCE, batch_size=BATCH_SIZE,
                 normalize: bool = True):
    train_loader = make_loader(train_examples, train=True, batch_size=batch_size,
                                normalize=normalize)
    val_loader = make_loader(val_examples, train=False, batch_size=batch_size,
                              normalize=normalize)
    class_weights = compute_class_weights(train_examples)
    return _run_training_loop(model, train_loader, val_loader, lr, class_weights,
                               model_tag, run_tag, max_epochs, patience, has_ids=True)


def train_model_on_features(model, X_train, y_train, X_val, y_val, lr, model_tag, run_tag,
                             max_epochs=MAX_EPOCHS, patience=PATIENCE, batch_size=BATCH_SIZE):
    train_loader = make_feature_loader(X_train, y_train, train=True, batch_size=batch_size)
    val_loader = make_feature_loader(X_val, y_val, train=False, batch_size=batch_size)
    class_weights = compute_class_weights_from_labels(y_train)
    return _run_training_loop(model, train_loader, val_loader, lr, class_weights,
                               model_tag, run_tag, max_epochs, patience, has_ids=False)


@torch.no_grad()
def evaluate_model(model, examples, batch_size: int = BATCH_SIZE,
                    normalize: bool = True):
    model.eval()
    model = model.to(DEVICE)
    loader = make_loader(examples, train=False, batch_size=batch_size,
                          normalize=normalize)
    all_ids, all_true, all_prob = [], [], []
    for x, y, ids in loader:
        x = x.to(DEVICE)
        logits = model(x)
        prob = torch.softmax(logits, dim=1)[:, 1]
        all_ids.extend(ids)
        all_true.extend(y.tolist())
        all_prob.extend(prob.cpu().tolist())
    return all_ids, all_true, all_prob


@torch.no_grad()
def evaluate_model_on_features(model, X, y, ids, batch_size: int = BATCH_SIZE):
    model.eval()
    model = model.to(DEVICE)
    loader = make_feature_loader(X, y, train=False, batch_size=batch_size)
    all_true, all_prob = [], []
    for x, yb in loader:
        x = x.to(DEVICE)
        logits = model(x)
        prob = torch.softmax(logits, dim=1)[:, 1]
        all_true.extend(yb.tolist())
        all_prob.extend(prob.cpu().tolist())
    return list(ids), all_true, all_prob
