"""Shared fixtures for Project2 tests."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
ML = ROOT / "ml"

for path in (ROOT, ML):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Skip Ahmed PASSWORD_OK buzzer settle delay in unit tests.
import os

os.environ.setdefault("ARDUINO_PASSWORD_SETTLE_S", "0")
os.environ.setdefault("ARDUINO_CONNECT_SETTLE_S", "0")


@pytest.fixture
def tmp_wav(tmp_path: Path) -> Path:
    """1s of low-level noise at 16 kHz (valid but non-speech)."""
    path = tmp_path / "noise.wav"
    y = (np.random.randn(16_000) * 0.01).astype(np.float32)
    sf.write(path, y, 16_000)
    return path


@pytest.fixture
def empty_wav(tmp_path: Path) -> Path:
    path = tmp_path / "empty.wav"
    sf.write(path, np.zeros(100, dtype=np.float32), 16_000)
    return path


@pytest.fixture
def dataset_sample() -> Path:
    samples = list((ML / "data" / "dataset").rglob("*.wav"))
    if not samples:
        pytest.skip("No dataset WAV files available")
    return samples[0]
