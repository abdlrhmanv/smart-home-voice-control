"""Sklearn SVM classifier adapter (optional probability calibration)."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
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
        self._model: Any = self._build(
            C=C if C is not None else self.config.svm_c,
            gamma=gamma if gamma is not None else self.config.svm_gamma,
            probability=not self.config.calibrate,
        )

    def _build(
        self, C: float, gamma: str | float, *, probability: bool
    ) -> Pipeline:
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
                        probability=probability,
                        random_state=self.config.random_state,
                    ),
                ),
            ]
        )

    @property
    def pipeline(self) -> Any:
        """Fitted estimator (Pipeline or CalibratedClassifierCV)."""
        return self._model

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._model.fit(X, y)
        if self.config.calibrate:
            self._apply_calibration(X, y)

    def tune(self, X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        cv = StratifiedKFold(
            n_splits=5, shuffle=True, random_state=self.config.random_state
        )
        search = GridSearchCV(
            self._build(
                self.config.svm_c,
                self.config.svm_gamma,
                probability=not self.config.calibrate,
            ),
            param_grid=self.config.param_grid,
            scoring="f1_macro",
            cv=cv,
            n_jobs=-1,
            verbose=1,
        )
        search.fit(X, y)
        self._model = search.best_estimator_
        if self.config.calibrate:
            self._apply_calibration(X, y)
        return {
            "best_params": search.best_params_,
            "best_score": float(search.best_score_),
        }

    def _apply_calibration(self, X: np.ndarray, y: np.ndarray) -> None:
        """Wrap the current estimator with sigmoid CalibratedClassifierCV."""
        n_classes = len(set(y.tolist()))
        # Need enough samples per class for stratified calibration folds.
        _, counts = np.unique(y, return_counts=True)
        max_cv = int(counts.min())
        cv = max(2, min(3, max_cv))
        if max_cv < 2 or n_classes < 2:
            return

        base = clone(self._model)
        if isinstance(base, Pipeline) and "clf" in base.named_steps:
            base.named_steps["clf"].set_params(probability=False)

        calibrated = CalibratedClassifierCV(
            estimator=base, method="sigmoid", cv=cv
        )
        calibrated.fit(X, y)
        self._model = calibrated

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)

    def wrap_fitted_pipeline(self, pipeline: Any) -> None:
        self._model = pipeline

    def exportable(self) -> Any:
        """Object persisted by ArtifactStore."""
        return self._model
