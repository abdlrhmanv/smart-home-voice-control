"""MFCC + spectral feature extraction (expects preprocessed waveform)."""

from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

from src.config import AUDIO, AudioConfig
from src.ports.feature_extractor import AudioPreprocessor

from .preprocessor import LibrosaAudioPreprocessor


class LibrosaFeatureExtractor:
    def __init__(
        self,
        config: AudioConfig | None = None,
        preprocessor: AudioPreprocessor | None = None,
        *,
        include_deltas: bool = False,
    ) -> None:
        self.config = config or AUDIO
        self.preprocessor = preprocessor or LibrosaAudioPreprocessor(self.config)
        self.include_deltas = include_deltas

    @staticmethod
    def _stats(feat: np.ndarray) -> np.ndarray:
        return np.concatenate([feat.mean(axis=1), feat.std(axis=1)])

    def extract(self, y: np.ndarray, sr: int) -> np.ndarray:
        if y.size == 0:
            raise ValueError("Empty audio waveform")
        cfg = self.config
        mfcc = librosa.feature.mfcc(
            y=y, sr=sr, n_mfcc=cfg.n_mfcc, n_fft=cfg.n_fft, hop_length=cfg.hop_length
        )
        parts = [
            self._stats(mfcc),
            self._stats(
                librosa.feature.chroma_stft(
                    y=y, sr=sr, n_fft=cfg.n_fft, hop_length=cfg.hop_length
                )
            ),
            self._stats(
                librosa.feature.spectral_contrast(
                    y=y, sr=sr, n_fft=cfg.n_fft, hop_length=cfg.hop_length
                )
            ),
            self._stats(librosa.feature.zero_crossing_rate(y, hop_length=cfg.hop_length)),
            self._stats(
                librosa.feature.rms(
                    y=y, frame_length=cfg.n_fft, hop_length=cfg.hop_length
                )
            ),
        ]
        if self.include_deltas:
            # Dynamics help command content; less useful for raw speaker ID.
            parts.append(self._stats(librosa.feature.delta(mfcc)))
            parts.append(self._stats(librosa.feature.delta(mfcc, order=2)))
        return np.concatenate(parts).astype(np.float32)

    def extract_from_file(self, path: str | Path) -> np.ndarray:
        y, sr = self.preprocessor.prepare(path)
        return self.extract(y, sr)
