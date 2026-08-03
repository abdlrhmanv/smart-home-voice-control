#!/usr/bin/env python3
"""Nested cross-validation + probability calibration for a classifier task.

Outer StratifiedKFold estimates generalization with an honest score.
Inner GridSearchCV (optional) tunes hyperparameters on each outer train fold.
Also reports Brier score and reliability-curve points for predict_proba.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelBinarizer, StandardScaler
from sklearn.svm import SVC

from src.application.tasks import COMMAND_TASK, SPEAKER_TASK
from src.config import TRAINING, TrainingConfig
from src.infrastructure.filesystem.dataset_repo import FilesystemDatasetRepository
from src.infrastructure.librosa.feature_extractor import LibrosaFeatureExtractor
from src.infrastructure.librosa.normalize import cmvn


def _build_xy(task_name: str) -> tuple[np.ndarray, np.ndarray, object]:
    task = SPEAKER_TASK if task_name == "speaker" else COMMAND_TASK
    repo = FilesystemDatasetRepository()
    extractor = LibrosaFeatureExtractor(
        include_deltas=(task.target == "command")
    )
    samples = repo.discover()
    if not samples:
        raise FileNotFoundError(f"No dataset under {repo.root()}")
    X = np.vstack([extractor.extract_from_file(s.path) for s in samples])
    y = np.asarray([task.encode_sample(s) for s in samples])
    if task.target == "command":
        X = cmvn(X)
    return X, y, task


def _svm_pipeline(cfg: TrainingConfig) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                SVC(
                    kernel="rbf",
                    C=cfg.svm_c,
                    gamma=cfg.svm_gamma,
                    class_weight="balanced",
                    probability=True,
                    random_state=cfg.random_state,
                ),
            ),
        ]
    )


def nested_cv(
    task_name: str = "command",
    *,
    outer_splits: int = 5,
    tune: bool = True,
    config: TrainingConfig | None = None,
) -> dict:
    cfg = config or TRAINING
    X, y, task = _build_xy(task_name)
    outer = StratifiedKFold(
        n_splits=outer_splits, shuffle=True, random_state=cfg.random_state
    )

    f1s: list[float] = []
    briers: list[float] = []
    all_y_true: list[int] = []
    all_y_prob: list[np.ndarray] = []

    print(f"\nNested CV — {task.name} ({outer_splits} outer folds, tune={tune})")
    print("=" * 60)

    for fold, (tr, te) in enumerate(outer.split(X, y), start=1):
        X_tr, X_te = X[tr], X[te]
        y_tr, y_te = y[tr], y[te]

        if tune:
            inner = StratifiedKFold(
                n_splits=min(3, len(np.unique(y_tr))),
                shuffle=True,
                random_state=cfg.random_state,
            )
            search = GridSearchCV(
                _svm_pipeline(cfg),
                param_grid=cfg.param_grid,
                scoring="f1_macro",
                cv=inner,
                n_jobs=-1,
            )
            search.fit(X_tr, y_tr)
            model = search.best_estimator_
            best = search.best_params_
        else:
            model = _svm_pipeline(cfg)
            model.fit(X_tr, y_tr)
            best = {"clf__C": cfg.svm_c, "clf__gamma": cfg.svm_gamma}

        y_pred = model.predict(X_te)
        y_proba = model.predict_proba(X_te)
        f1 = float(f1_score(y_te, y_pred, average="macro", zero_division=0))
        f1s.append(f1)

        # Multaclass Brier: mean squared error vs one-hot
        lb = LabelBinarizer()
        lb.fit(y)
        y_te_bin = lb.transform(y_te)
        if y_te_bin.ndim == 1:
            y_te_bin = np.column_stack([1 - y_te_bin, y_te_bin])
        # Align proba columns to lb.classes_
        class_to_idx = {c: i for i, c in enumerate(model.classes_)}
        aligned = np.zeros_like(y_te_bin, dtype=float)
        for j, c in enumerate(lb.classes_):
            if c in class_to_idx:
                aligned[:, j] = y_proba[:, class_to_idx[c]]
        brier = float(np.mean(np.sum((aligned - y_te_bin) ** 2, axis=1)))
        briers.append(brier)

        all_y_true.extend(y_te.tolist())
        # Store max-class confidence for a simple reliability curve
        all_y_prob.extend(y_proba.max(axis=1).tolist())

        print(f"  fold {fold}: f1_macro={f1:.3f}  brier={brier:.3f}  best={best}")

    # Reliability curve for "correct vs max probability"
    y_true_arr = np.asarray(all_y_true)
    # Rebuild correctness using a final refit is awkward; approximate with
    # per-fold max-proba vs whether argmax matched — already have fold metrics.
    # For curve: use one-vs-rest on last collected probs is weak; instead compute
    # from concatenated fold predictions properly by re-running store.

    mean_f1 = float(np.mean(f1s))
    std_f1 = float(np.std(f1s))
    mean_brier = float(np.mean(briers))

    print("-" * 60)
    print(f"  Outer F1 macro : {mean_f1:.4f} ± {std_f1:.4f}")
    print(f"  Mean Brier     : {mean_brier:.4f}  (lower is better)")
    print(
        f"  Spec gate ≥ {cfg.f1_threshold}: "
        f"{'PASS' if mean_f1 >= cfg.f1_threshold else 'FAIL'}"
    )

    result = {
        "task": task.name,
        "outer_splits": outer_splits,
        "tune": tune,
        "fold_f1_macro": f1s,
        "fold_brier": briers,
        "mean_f1_macro": mean_f1,
        "std_f1_macro": std_f1,
        "mean_brier": mean_brier,
    }
    return result


def calibration_report(
    task_name: str = "command",
    *,
    n_bins: int = 8,
    config: TrainingConfig | None = None,
) -> dict:
    """Fit on 80% and plot-ready reliability curve on 20% holdout."""
    from sklearn.model_selection import train_test_split

    cfg = config or TRAINING
    X, y, task = _build_xy(task_name)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=cfg.test_size, random_state=cfg.random_state, stratify=y
    )
    model = _svm_pipeline(cfg)
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)
    pred = model.predict(X_te)
    correct = (pred == y_te).astype(int)
    conf = proba.max(axis=1)
    frac_pos, mean_pred = calibration_curve(
        correct, conf, n_bins=n_bins, strategy="uniform"
    )
    # Binary Brier on correctness vs confidence
    brier = float(brier_score_loss(correct, conf))

    print(f"\nCalibration — {task.name} (holdout)")
    print("=" * 60)
    print(f"  Brier (correct vs max-proba): {brier:.4f}")
    print("  reliability points (mean_predicted_proba → fraction_correct):")
    for mp, fp in zip(mean_pred, frac_pos):
        print(f"    {mp:.3f} → {fp:.3f}")

    return {
        "task": task.name,
        "brier_correct_vs_conf": brier,
        "mean_predicted_proba": mean_pred.tolist(),
        "fraction_correct": frac_pos.tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task", choices=("speaker", "command"), default="command"
    )
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--no-tune", action="store_true")
    parser.add_argument(
        "--calibration-only",
        action="store_true",
        help="Skip nested CV; only emit holdout reliability curve",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write metrics JSON",
    )
    args = parser.parse_args()

    payload: dict = {}
    if not args.calibration_only:
        payload["nested_cv"] = nested_cv(
            args.task,
            outer_splits=args.outer_splits,
            tune=not args.no_tune,
        )
    payload["calibration"] = calibration_report(args.task)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote {args.json_out}")


if __name__ == "__main__":
    main()
