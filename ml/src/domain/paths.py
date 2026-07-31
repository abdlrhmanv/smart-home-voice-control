"""Filesystem layout for the ML package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Resolves dataset / models directories relative to ``Project2/ml``."""

    root: Path

    @classmethod
    def from_package(cls) -> ProjectPaths:
        # src/domain/paths.py → parents: domain, src, ml
        ml_root = Path(__file__).resolve().parents[2]
        return cls(root=ml_root)

    @property
    def dataset_dir(self) -> Path:
        return self.root / "data" / "dataset"

    @property
    def models_dir(self) -> Path:
        return self.root / "models"

    def artifact(self, filename: str) -> Path:
        return self.models_dir / filename
