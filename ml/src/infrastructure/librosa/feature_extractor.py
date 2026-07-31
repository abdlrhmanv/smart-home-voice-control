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
    ) -> None:
        self.config = config or AUDIO
        self.preprocessor = preprocessor or LibrosaAudioPreprocessor(self.config)

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
        chroma = librosa.feature.chroma_stft(
            y=y, sr=sr, n_fft=cfg.n_fft, hop_length=cfg.hop_length
        )
        contrast = librosa.feature.spectral_contrast(
            y=y, sr=sr, n_fft=cfg.n_fft, hop_length=cfg.hop_length
        )
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=cfg.hop_length)
        rms = librosa.feature.rms(y=y, frame_length=cfg.n_fft, hop_length=cfg.hop_length)
        return np.concatenate(
            [
                self._stats(mfcc),
                self._stats(chroma),
                self._stats(contrast),
                self._stats(zcr),
                self._stats(rms),
            ]
        ).astype(np.float32)

    def extract_from_file(self, path: str | Path) -> np.ndarray:
        y, sr = self.preprocessor.prepare(path)
        return self.extract(y, sr)
