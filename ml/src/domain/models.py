"""Domain dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .labels import LabelMap


@dataclass(frozen=True)
class AudioSample:
    path: Path
    speaker: str
    command: str


@dataclass
class InferenceResult:
    password_ok: bool
    transcript: str
    speaker: str | None = None
    speaker_confidence: float | None = None
    command: str | None = None
    command_confidence: float | None = None
    action: dict[str, Any] | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrainMetrics:
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    f1_weighted: float
    confusion_matrix: list[list[int]]
    classification_report: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def meets_f1_threshold(self, threshold: float = 0.85) -> bool:
        return self.f1_macro >= threshold


@dataclass(frozen=True)
class ClassifierTask:
    """Speaker vs command — includes artifact filename for persistence."""

    name: str
    labels: LabelMap
    artifact: str
    target: str  # "speaker" | "command"

    def encode_sample(self, sample: AudioSample) -> int:
        if self.target == "speaker":
            return self.labels.encode(sample.speaker)
        if self.target == "command":
            return self.labels.encode(sample.command)
        raise ValueError(f"Unknown target '{self.target}'")


@dataclass
class Prediction:
    name: str
    label_id: int
    confidence: float = 0.0


@dataclass
class TrainSplit:
    """Output of Trainer — fitted model + held-out split for Evaluator."""

    classifier: Any  # Classifier protocol
    X_test: np.ndarray
    y_test: np.ndarray
