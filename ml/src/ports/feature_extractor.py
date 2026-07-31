"""Audio preprocessing and feature extraction ports."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class AudioPreprocessor(Protocol):
    def load(self, path: str | Path) -> tuple[np.ndarray, int]: ...

    def resample(self, y: np.ndarray, orig_sr: int) -> tuple[np.ndarray, int]: ...

    def normalize(self, y: np.ndarray) -> np.ndarray: ...

    def prepare(self, path: str | Path) -> tuple[np.ndarray, int]:
        """Load → resample → normalize."""
        ...


@runtime_checkable
class FeatureExtractor(Protocol):
    def extract(self, y: np.ndarray, sr: int) -> np.ndarray: ...

    def extract_from_file(self, path: str | Path) -> np.ndarray: ...
