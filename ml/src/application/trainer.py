"""ClassifierTrainer — fit only; evaluation is a separate service."""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from src.config import TRAINING, TrainingConfig
from src.domain.models import ClassifierTask, TrainSplit
from src.infrastructure.filesystem.dataset_repo import FilesystemDatasetRepository
from src.infrastructure.librosa.feature_extractor import LibrosaFeatureExtractor
from src.infrastructure.sklearn.svm_classifier import SklearnSvmClassifier
from src.ports.feature_extractor import FeatureExtractor
from src.ports.repository import DatasetRepository


class ClassifierTrainer:
    """Build features → split → fit Classifier. Does not compute metrics."""

    def __init__(
        self,
        task: ClassifierTask,
        feature_extractor: FeatureExtractor | None = None,
        dataset: DatasetRepository | None = None,
        config: TrainingConfig | None = None,
    ) -> None:
        self.task = task
        self.features = feature_extractor or LibrosaFeatureExtractor()
        self.dataset = dataset or FilesystemDatasetRepository()
        self.config = config or TRAINING

    def build_xy(self) -> tuple[np.ndarray, np.ndarray]:
        samples = self.dataset.discover()
        if not samples:
            raise FileNotFoundError(
                f"No audio under {self.dataset.root()}/<speaker>/<command>/."
            )
        X = np.vstack([self.features.extract_from_file(s.path) for s in samples])
        y = np.asarray([self.task.encode_sample(s) for s in samples])
        return X, y

    def train(self, tune: bool | None = None) -> TrainSplit:
        cfg = self.config
        do_tune = cfg.tune if tune is None else tune
        X, y = self.build_xy()

        n_classes = len(set(y.tolist()))
        # Both tasks are multi-class; require at least 2 distinct labels so SVM
        # and stratified splitting are well-defined.
        required = 2
        if n_classes < required:
            raise ValueError(
                f"{self.task.name} needs ≥{required} classes; found {n_classes}."
            )

        # Stratified split / 5-fold tune need enough samples per class.
        _, counts = np.unique(y, return_counts=True)
        min_per_class = int(counts.min())
        min_needed = max(2, int(1 / self.config.test_size) if self.config.test_size else 2)
        if min_per_class < min_needed:
            raise ValueError(
                f"{self.task.name}: class with only {min_per_class} sample(s); "
                f"need ≥{min_needed} per class for a stratified "
                f"{self.config.test_size:.0%} holdout."
            )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=cfg.test_size,
            random_state=cfg.random_state,
            stratify=y,
        )

        clf = SklearnSvmClassifier(config=cfg)
        if do_tune:
            info = clf.tune(X_train, y_train)
            print(f"Best {self.task.name} params: {info['best_params']}")
            print(f"Best CV F1 (macro): {info['best_score']:.4f}")
        else:
            clf.fit(X_train, y_train)

        return TrainSplit(classifier=clf, X_test=X_test, y_test=y_test)
