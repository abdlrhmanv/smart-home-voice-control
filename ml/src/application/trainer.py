"""ClassifierTrainer — fit only; evaluation is a separate service."""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from src.config import TRAINING, TrainingConfig
from src.domain.models import ClassifierTask, TrainSplit
from src.infrastructure.filesystem.dataset_repo import FilesystemDatasetRepository
from src.infrastructure.librosa.augment import augment_waveform
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
        if feature_extractor is not None:
            self.features = feature_extractor
        elif task.target == "command":
            self.features = LibrosaFeatureExtractor(include_deltas=True)
        else:
            self.features = LibrosaFeatureExtractor()
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
        if self.task.target == "command":
            from src.infrastructure.librosa.normalize import cmvn

            X = cmvn(X)
        return X, y

    def train(self, tune: bool | None = None) -> TrainSplit:
        cfg = self.config
        do_tune = cfg.tune if tune is None else tune
        samples = self.dataset.discover()
        if not samples:
            raise FileNotFoundError(
                f"No audio under {self.dataset.root()}/<speaker>/<command>/."
            )

        # Clean features for honest holdout
        X = np.vstack([self.features.extract_from_file(s.path) for s in samples])
        y = np.asarray([self.task.encode_sample(s) for s in samples])
        if self.task.target == "command":
            from src.infrastructure.librosa.normalize import cmvn

            X = cmvn(X)

        n_classes = len(set(y.tolist()))
        required = 2
        if n_classes < required:
            raise ValueError(
                f"{self.task.name} needs ≥{required} classes; found {n_classes}."
            )

        _, counts = np.unique(y, return_counts=True)
        min_per_class = int(counts.min())
        min_needed = max(2, int(1 / cfg.test_size) if cfg.test_size else 2)
        if min_per_class < min_needed:
            raise ValueError(
                f"{self.task.name}: class with only {min_per_class} sample(s); "
                f"need ≥{min_needed} per class for a stratified "
                f"{cfg.test_size:.0%} holdout."
            )

        idx = np.arange(len(samples))
        idx_train, idx_test = train_test_split(
            idx,
            test_size=cfg.test_size,
            random_state=cfg.random_state,
            stratify=y,
        )

        X_test, y_test = X[idx_test], y[idx_test]
        X_train, y_train = X[idx_train], y[idx_train]

        if cfg.augment and self.task.target == "command":
            X_train, y_train = self._augment_train(
                [samples[i] for i in idx_train], X_train, y_train
            )
            print(
                f"Augmented train set → {len(y_train)} rows "
                f"({cfg.augment_copies} copy/copies per clip)."
            )

        clf = SklearnSvmClassifier(config=cfg)
        if do_tune:
            info = clf.tune(X_train, y_train)
            print(f"Best {self.task.name} params: {info['best_params']}")
            print(f"Best CV F1 (macro): {info['best_score']:.4f}")
        else:
            clf.fit(X_train, y_train)

        if cfg.calibrate:
            print(f"Applied probability calibration ({self.task.name}).")

        return TrainSplit(classifier=clf, X_test=X_test, y_test=y_test)

    def _augment_train(self, train_samples, X_train, y_train):
        """Waveform noise/gain on train clips only; CMVN after stacking."""
        from src.infrastructure.librosa.normalize import cmvn

        rng = np.random.default_rng(self.config.random_state)
        copies = max(0, int(self.config.augment_copies))
        xs = [X_train]
        ys = [y_train]
        prep = getattr(self.features, "preprocessor", None)

        if prep is not None and copies > 0:
            for sample, label in zip(train_samples, y_train):
                y_wave, sr = prep.prepare(sample.path)
                for _ in range(copies):
                    feat = self.features.extract(augment_waveform(y_wave, rng), sr)
                    xs.append(feat.reshape(1, -1))
                    ys.append(np.asarray([label]))
        elif copies > 0:
            # Feature-space jitter fallback
            for _ in range(copies):
                noise = rng.normal(0.0, 0.05, size=X_train.shape).astype(np.float32)
                xs.append(X_train + noise)
                ys.append(y_train)

        X_out = np.vstack(xs)
        y_out = np.concatenate(ys)
        if self.task.target == "command":
            # Clean train rows already CMVN'd; re-CMVN whole matrix for consistency
            X_out = cmvn(X_out)
        return X_out, y_out
