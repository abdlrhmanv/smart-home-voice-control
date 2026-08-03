"""Waveform augmentation helpers."""

import numpy as np

from src.infrastructure.librosa.augment import (
    add_gaussian_noise,
    augment_waveform,
    random_gain,
)


def test_augment_preserves_length():
    rng = np.random.default_rng(0)
    y = rng.normal(0, 0.1, size=16000).astype(np.float32)
    out = augment_waveform(y, rng)
    assert out.shape == y.shape
    assert np.isfinite(out).all()
    assert float(np.max(np.abs(out))) <= 1.0 + 1e-5


def test_noise_changes_signal():
    rng = np.random.default_rng(1)
    y = np.ones(1000, dtype=np.float32) * 0.5
    noisy = add_gaussian_noise(y, rng, snr_db=10)
    assert not np.allclose(y, noisy)


def test_gain_scales():
    rng = np.random.default_rng(2)
    y = np.ones(100, dtype=np.float32)
    # Force gain by checking magnitude can change before peak-norm in augment_waveform
    g = random_gain(y, rng, low=0.5, high=0.5)
    assert np.allclose(g, 0.5)
