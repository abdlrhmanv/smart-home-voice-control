"""Simple waveform augmentations for more robust training."""

from __future__ import annotations

import numpy as np


def add_gaussian_noise(
    y: np.ndarray, rng: np.random.Generator, snr_db: float = 20.0
) -> np.ndarray:
    """Add noise at approximately ``snr_db`` relative to signal RMS."""
    y = np.asarray(y, dtype=np.float32)
    if y.size == 0:
        return y
    rms = float(np.sqrt(np.mean(y**2)) + 1e-8)
    noise_rms = rms / (10 ** (snr_db / 20.0))
    noise = rng.normal(0.0, noise_rms, size=y.shape).astype(np.float32)
    return y + noise


def random_gain(
    y: np.ndarray, rng: np.random.Generator, low: float = 0.7, high: float = 1.3
) -> np.ndarray:
    gain = float(rng.uniform(low, high))
    return (np.asarray(y, dtype=np.float32) * gain).astype(np.float32)


def augment_waveform(
    y: np.ndarray,
    rng: np.random.Generator,
    *,
    snr_db_range: tuple[float, float] = (12.0, 25.0),
) -> np.ndarray:
    """Gain + noise; peak-normalize afterward for stable features."""
    out = random_gain(y, rng)
    snr = float(rng.uniform(*snr_db_range))
    out = add_gaussian_noise(out, rng, snr_db=snr)
    peak = float(np.max(np.abs(out)))
    if peak > 0:
        out = (out / peak).astype(np.float32)
    return out
