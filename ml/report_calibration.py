#!/usr/bin/env python3
"""Write a lightweight calibration / confidence report for Settings UI.

Trains a fresh estimator on the train split only, then scores the held-out
test split — never evaluates a model that already saw the test utterances.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, f1_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.application.tasks import COMMAND_TASK, SPEAKER_TASK
from src.config import TRAINING, TrainingConfig
from src.infrastructure.filesystem.dataset_repo import FilesystemDatasetRepository
from src.infrastructure.librosa.feature_extractor import LibrosaFeatureExtractor
from src.infrastructure.librosa.normalize import cmvn
from src.infrastructure.sklearn.svm_classifier import SklearnSvmClassifier


def _xy(task_name: str):
    task = SPEAKER_TASK if task_name == "speaker" else COMMAND_TASK
    repo = FilesystemDatasetRepository()
    extractor = LibrosaFeatureExtractor(include_deltas=(task.target == "command"))
    samples = repo.discover()
    X = np.vstack([extractor.extract_from_file(s.path) for s in samples])
    y = np.asarray([task.encode_sample(s) for s in samples])
    if task.target == "command":
        X = cmvn(X)
    return X, y, task


def build_report(
    task_name: str = "command",
    n_bins: int = 8,
    *,
    config: TrainingConfig | None = None,
) -> dict:
    cfg = config or TRAINING
    X, y, task = _xy(task_name)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X,
        y,
        test_size=cfg.test_size,
        random_state=cfg.random_state,
        stratify=y,
    )

    # Fit only on train — do not load the shipped artifact (would leak).
    clf = SklearnSvmClassifier(config=cfg)
    clf.fit(X_tr, y_tr)

    y_pred = clf.predict(X_te)
    proba = clf.predict_proba(X_te)
    conf = proba.max(axis=1)
    correct = (y_pred == y_te).astype(int)
    f1 = float(f1_score(y_te, y_pred, average="macro", zero_division=0))
    brier = float(brier_score_loss(correct, conf))
    frac_pos, mean_pred = calibration_curve(
        correct, conf, n_bins=n_bins, strategy="uniform"
    )
    return {
        "task": task.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_train": int(len(y_tr)),
        "n_test": int(len(y_te)),
        "f1_macro": f1,
        "accuracy": float(np.mean(correct)),
        "brier_correct_vs_conf": brier,
        "mean_confidence": float(np.mean(conf)),
        "reliability": [
            {"mean_predicted_proba": float(mp), "fraction_correct": float(fp)}
            for mp, fp in zip(mean_pred, frac_pos)
        ],
        "note": (
            "Fresh model trained on stratified train split only; "
            "metrics/reliability from held-out test utterances (no artifact leak)."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task", choices=("speaker", "command"), default="command")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Defaults to ml/reports/calibration_<task>.json",
    )
    p.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Disable CalibratedClassifierCV for the fresh fit",
    )
    args = p.parse_args()
    out = args.out or (
        Path(__file__).resolve().parent / "reports" / f"calibration_{args.task}.json"
    )
    cfg = TrainingConfig(calibrate=not args.no_calibrate)
    report = build_report(args.task, config=cfg)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(
        f"  f1_macro={report['f1_macro']:.3f}  "
        f"brier={report['brier_correct_vs_conf']:.3f}  "
        f"mean_conf={report['mean_confidence']:.3f}"
    )


if __name__ == "__main__":
    main()
