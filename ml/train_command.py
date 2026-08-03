#!/usr/bin/env python3
"""Train command model: Trainer → Evaluator → ModelLoader.save."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.application import (
    COMMAND_TASK,
    ClassificationEvaluator,
    ClassifierTrainer,
)
from src.config import TRAINING, TrainingConfig
from src.infrastructure.filesystem import FilesystemDatasetRepository
from src.infrastructure.persistence import JoblibModelLoader


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train command recognition model")
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--test-size", type=float, default=TRAINING.test_size)
    p.add_argument("--tune", action="store_true")
    p.add_argument("--seed", type=int, default=TRAINING.random_state)
    p.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Disable CalibratedClassifierCV (default: on)",
    )
    p.add_argument(
        "--augment",
        action="store_true",
        help="Add noise/gain copies of train waveforms only",
    )
    p.add_argument("--augment-copies", type=int, default=1)
    p.add_argument(
        "--group-holdout",
        action="store_true",
        help="Hold out entire speakers (GroupShuffleSplit) for a harder test",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = TrainingConfig(
        test_size=args.test_size,
        random_state=args.seed,
        tune=args.tune,
        calibrate=not args.no_calibrate,
        augment=args.augment,
        augment_copies=args.augment_copies,
        group_holdout=args.group_holdout,
    )
    dataset = FilesystemDatasetRepository(args.data)
    print(f"Dataset : {dataset.root()}")

    trainer = ClassifierTrainer(task=COMMAND_TASK, dataset=dataset, config=cfg)
    split = trainer.train(tune=args.tune)

    evaluator = ClassificationEvaluator()
    metrics = evaluator.evaluate_split(split, COMMAND_TASK.labels)
    evaluator.print_report(metrics, title="Command Recognition — Test Set")

    loader = JoblibModelLoader()
    loader.save(COMMAND_TASK, split.classifier)
    print(f"\nSaved → {COMMAND_TASK.artifact}")
    print(f"Test F1 (macro) = {metrics.f1_macro:.4f}")


if __name__ == "__main__":
    main()
