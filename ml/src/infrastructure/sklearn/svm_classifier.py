"""Sklearn SVM classifier adapter."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src.config import TRAINING, TrainingConfig


class SklearnSvmClassifier:
    """Generic Classifier — no label decoding (application layer owns that)."""

    def __init__(
        self,
        config: TrainingConfig | None = None,
        C: float | None = None,
        gamma: str | float | None = None,
    ) -> None:
        self.config = config or TRAINING
        self._pipeline = self._build(
            C=C if C is not None else self.config.svm_c,
            gamma=gamma if gamma is not None else self.config.svm_gamma,
        )

    def _build(self, C: float, gamma: str | float) -> Pipeline:
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "clf",
                    SVC(
                        kernel="rbf",
                        C=C,
                        gamma=gamma,
                        class_weight="balanced",
                        probability=True,
                        random_state=self.config.random_state,
                    ),
                ),
            ]
        )

    @property
    def pipeline(self) -> Pipeline:
        return self._pipeline

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._pipeline.fit(X, y)

    def tune(self, X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        cv = StratifiedKFold(
            n_splits=5, shuffle=True, random_state=self.config.random_state
        )
        search = GridSearchCV(
            self._build(self.config.svm_c, self.config.svm_gamma),
            param_grid=self.config.param_grid,
            scoring="f1_macro",
            cv=cv,
            n_jobs=-1,
            verbose=1,
        )
        search.fit(X, y)
        self._pipeline = search.best_estimator_
        return {
            "best_params": search.best_params_,
            "best_score": float(search.best_score_),
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._pipeline.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._pipeline.predict_proba(X)

    def wrap_fitted_pipeline(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline

    def exportable(self) -> Pipeline:
        """Object persisted by ArtifactStore."""
        return self._pipeline
