"""Classification evaluation — separate from Trainer (SRP)."""

from __future__ import annotations

from typing import Iterable

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.config import TRAINING
from src.domain.labels import LabelMap
from src.domain.models import TrainMetrics, TrainSplit
from src.ports.classifier import Classifier


class ClassificationEvaluator:
    def evaluate(
        self,
        y_true: Iterable[int],
        y_pred: Iterable[int],
        labels: LabelMap | None = None,
    ) -> TrainMetrics:
        y_true_arr = np.asarray(list(y_true))
        y_pred_arr = np.asarray(list(y_pred))
        present = sorted(set(y_true_arr.tolist()))
        target_names = [labels.decode(i) for i in present] if labels else None

        return TrainMetrics(
            accuracy=float(accuracy_score(y_true_arr, y_pred_arr)),
            precision_macro=float(
                precision_score(
                    y_true_arr, y_pred_arr, labels=present, average="macro", zero_division=0
                )
            ),
            recall_macro=float(
                recall_score(
                    y_true_arr, y_pred_arr, labels=present, average="macro", zero_division=0
                )
            ),
            f1_macro=float(
                f1_score(
                    y_true_arr, y_pred_arr, labels=present, average="macro", zero_division=0
                )
            ),
            f1_weighted=float(
                f1_score(
                    y_true_arr, y_pred_arr, labels=present, average="weighted", zero_division=0
                )
            ),
            confusion_matrix=confusion_matrix(
                y_true_arr, y_pred_arr, labels=present
            ).tolist(),
            classification_report=classification_report(
                y_true_arr,
                y_pred_arr,
                labels=present,
                target_names=target_names,
                zero_division=0,
            ),
        )

    def evaluate_split(
        self, split: TrainSplit, labels: LabelMap
    ) -> TrainMetrics:
        y_pred = split.classifier.predict(split.X_test)
        return self.evaluate(split.y_test, y_pred, labels=labels)

    def print_report(self, metrics: TrainMetrics, title: str = "Evaluation") -> None:
        threshold = TRAINING.f1_threshold
        print(f"\n{'=' * 60}")
        print(f" {title}")
        print("=" * 60)
        print(f"  Accuracy          : {metrics.accuracy:.4f}")
        print(f"  Precision (macro) : {metrics.precision_macro:.4f}")
        print(f"  Recall (macro)    : {metrics.recall_macro:.4f}")
        print(f"  F1 (macro)        : {metrics.f1_macro:.4f}")
        print(f"  F1 (weighted)     : {metrics.f1_weighted:.4f}")
        print("\nConfusion matrix:")
        for row in metrics.confusion_matrix:
            print(f"  {row}")
        print("\nClassification report:")
        print(metrics.classification_report)
        if metrics.meets_f1_threshold(threshold):
            print(f"✓  F1 (macro) meets the ≥ {threshold} requirement.")
        else:
            print(f"⚠  F1 (macro) is below the required {threshold} threshold.")
