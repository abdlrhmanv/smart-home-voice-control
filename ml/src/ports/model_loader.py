"""Model loading port — swap Joblib/ONNX/Torch behind this."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..domain.models import ClassifierTask
from .classifier import Classifier


@runtime_checkable
class ModelLoader(Protocol):
    def load(self, task: ClassifierTask) -> Classifier: ...

    def save(self, task: ClassifierTask, classifier: Classifier) -> None: ...
