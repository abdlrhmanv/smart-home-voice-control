"""Load/save Classifier instances via ArtifactStore (no sklearn in pipeline)."""

from __future__ import annotations

from src.domain.models import ClassifierTask
from src.infrastructure.persistence.joblib_store import JoblibArtifactStore
from src.infrastructure.sklearn.svm_classifier import SklearnSvmClassifier
from src.ports.classifier import Classifier
from src.ports.repository import ArtifactStore


class JoblibModelLoader:
    """
    Reconstructs SklearnSvmClassifier wrappers around persisted pipelines.

    Swap this class for ONNX/Torch loaders later without touching Pipeline.
    """

    def __init__(self, store: ArtifactStore | None = None) -> None:
        self.store = store or JoblibArtifactStore()

    def load(self, task: ClassifierTask) -> Classifier:
        raw = self.store.load(task)
        clf = SklearnSvmClassifier()
        clf.wrap_fitted_pipeline(raw)
        return clf

    def save(self, task: ClassifierTask, classifier: Classifier) -> None:
        exportable = getattr(classifier, "exportable", None)
        payload = exportable() if callable(exportable) else classifier
        self.store.save(task, payload)
