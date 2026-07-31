"""Librosa audio preprocessor — load, resample, normalize."""

from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

from src.config import AUDIO, AudioConfig


class LibrosaAudioPreprocessor:
    def __init__(self, config: AudioConfig | None = None) -> None:
        self.config = config or AUDIO

    def load(self, path: str | Path) -> tuple[np.ndarray, int]:
        y, sr = librosa.load(path, sr=None, mono=True)
        return y.astype(np.float32), int(sr)

    def resample(self, y: np.ndarray, orig_sr: int) -> tuple[np.ndarray, int]:
        target = self.config.sample_rate
        if orig_sr == target:
            return y.astype(np.float32), target
        y_rs = librosa.resample(y, orig_sr=orig_sr, target_sr=target)
        return y_rs.astype(np.float32), target

    def normalize(self, y: np.ndarray) -> np.ndarray:
        if not self.config.peak_normalize or y.size == 0:
            return y
        peak = float(np.max(np.abs(y)))
        if peak <= 0:
            return y
        return (y / peak).astype(np.float32)

    def prepare(self, path: str | Path) -> tuple[np.ndarray, int]:
        y, sr = self.load(path)
        y, sr = self.resample(y, sr)
        return self.normalize(y), sr
