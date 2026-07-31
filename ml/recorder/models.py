"""Local quality report — recorder must not import ML domain models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class QualityReport:
    accepted: bool
    audio_int16: np.ndarray | None
    message: str
    clipped: bool = False
    rms: float = 0.0
    peak: float = 0.0
