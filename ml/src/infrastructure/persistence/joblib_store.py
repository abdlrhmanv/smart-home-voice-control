"""Joblib artifact store — paths come from ClassifierTask.artifact."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from src.domain.models import ClassifierTask
from src.domain.paths import ProjectPaths


class JoblibArtifactStore:
    def __init__(self, paths: ProjectPaths | None = None) -> None:
        self.paths = paths or ProjectPaths.from_package()

    def _path_for(self, task: ClassifierTask) -> Path:
        return self.paths.artifact(task.artifact)

    def save(self, task: ClassifierTask, model: Any) -> Path:
        path = self._path_for(task)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, path)
        return path

    def load(self, task: ClassifierTask) -> Any:
        return joblib.load(self._path_for(task))
