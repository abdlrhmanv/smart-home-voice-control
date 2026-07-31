"""Persist 16-bit PCM WAV files."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import wavfile

from .. import config


class WavWriter:
    def __init__(self, sample_rate: int = config.SAMPLE_RATE) -> None:
        self.sample_rate = sample_rate

    def write(self, path: Path, audio_int16: np.ndarray) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        wavfile.write(str(path), self.sample_rate, audio_int16)
