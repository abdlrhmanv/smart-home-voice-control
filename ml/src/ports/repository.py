"""Dataset and artifact persistence ports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ..domain.models import AudioSample, ClassifierTask


@runtime_checkable
class DatasetRepository(Protocol):
    def discover(self) -> list[AudioSample]: ...

    def root(self) -> Path: ...


@runtime_checkable
class ArtifactStore(Protocol):
    """Persistence keyed by ClassifierTask (store owns path resolution)."""

    def save(self, task: ClassifierTask, model: Any) -> Path: ...

    def load(self, task: ClassifierTask) -> Any: ...
