#!/usr/bin/env python3
"""Leave-one-speaker-out evaluation for the command classifier.

Trains on all speakers except one, tests on the held-out speaker's clips.
This measures whether command recognition generalizes to an unseen voice
(stricter than a random stratified split).
"""

from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np

from src.application.evaluator import ClassificationEvaluator
from src.application.tasks import COMMAND_TASK
from src.config import TRAINING, TrainingConfig
from src.domain.labels import SPEAKER_LABELS
from src.infrastructure.filesystem.dataset_repo import FilesystemDatasetRepository
from src.infrastructure.librosa.feature_extractor import LibrosaFeatureExtractor
from src.infrastructure.librosa.normalize import cmvn
from src.infrastructure.sklearn.svm_classifier import SklearnSvmClassifier


def build_xy_by_speaker(
    extractor: LibrosaFeatureExtractor,
    repo: FilesystemDatasetRepository,
    *,
    apply_cmvn: bool = True,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    buckets: dict[str, list[tuple[np.ndarray, int]]] = defaultdict(list)
    for sample in repo.discover():
        x = extractor.extract_from_file(sample.path)
        if apply_cmvn:
            x = cmvn(x)
        y = COMMAND_TASK.encode_sample(sample)
        buckets[sample.speaker].append((x, y))

    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for speaker, pairs in buckets.items():
        X = np.vstack([p[0] for p in pairs])
        y = np.asarray([p[1] for p in pairs], dtype=int)
        out[speaker] = (X, y)
    return out


def evaluate_loso(
    tune: bool = False,
    config: TrainingConfig | None = None,
    *,
    apply_cmvn: bool = True,
    include_deltas: bool = True,
) -> dict:
    cfg = config or TRAINING
    repo = FilesystemDatasetRepository()
    extractor = LibrosaFeatureExtractor(include_deltas=include_deltas)
    by_speaker = build_xy_by_speaker(extractor, repo, apply_cmvn=apply_cmvn)
    speakers = [s for s in SPEAKER_LABELS.names() if s in by_speaker]
    if len(speakers) < 2:
        raise RuntimeError("Need ≥2 speakers for leave-one-speaker-out.")

    evaluator = ClassificationEvaluator()
    fold_scores: list[dict] = []

    print("\nLeave-one-speaker-out — Command classifier")
    print(f"  utterance CMVN: {apply_cmvn}  |  MFCC deltas: {include_deltas}")
    print("=" * 60)

    for held_out in speakers:
        train_X, train_y = [], []
        for spk in speakers:
            if spk == held_out:
                continue
            X, y = by_speaker[spk]
            train_X.append(X)
            train_y.append(y)
        X_train = np.vstack(train_X)
        y_train = np.concatenate(train_y)
        X_test, y_test = by_speaker[held_out]

        clf = SklearnSvmClassifier(config=cfg)
        if tune:
            info = clf.tune(X_train, y_train)
            print(f"  [{held_out}] best params: {info['best_params']}")
        else:
            clf.fit(X_train, y_train)

        metrics = evaluator.evaluate(y_test, clf.predict(X_test), labels=COMMAND_TASK.labels)
        fold_scores.append(
            {
                "held_out": held_out,
                "n_test": int(len(y_test)),
                "f1_macro": metrics.f1_macro,
                "accuracy": metrics.accuracy,
            }
        )
        print(
            f"  held-out={held_out:12s}  n={len(y_test):3d}  "
            f"acc={metrics.accuracy:.3f}  f1_macro={metrics.f1_macro:.3f}"
        )

    mean_f1 = float(np.mean([f["f1_macro"] for f in fold_scores]))
    mean_acc = float(np.mean([f["accuracy"] for f in fold_scores]))
    print("-" * 60)
    print(f"  Mean accuracy : {mean_acc:.4f}")
    print(f"  Mean F1 macro : {mean_f1:.4f}")
    print(f"  Spec gate ≥ {cfg.f1_threshold}: {'PASS' if mean_f1 >= cfg.f1_threshold else 'FAIL'}")
    return {"folds": fold_scores, "mean_f1_macro": mean_f1, "mean_accuracy": mean_acc}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tune", action="store_true", help="Grid-search on each train fold")
    parser.add_argument(
        "--no-cmvn",
        action="store_true",
        help="Disable per-utterance CMVN (legacy comparison)",
    )
    parser.add_argument(
        "--no-deltas",
        action="store_true",
        help="Disable MFCC delta / delta-delta features",
    )
    args = parser.parse_args()
    evaluate_loso(
        tune=args.tune,
        apply_cmvn=not args.no_cmvn,
        include_deltas=not args.no_deltas,
    )


if __name__ == "__main__":
    main()
