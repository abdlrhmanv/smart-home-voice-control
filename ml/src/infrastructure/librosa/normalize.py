"""Per-utterance feature normalization helpers."""

from __future__ import annotations

import numpy as np


def cmvn(x: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Cepstral / feature mean-variance norm over one utterance (or row-wise).

    Removes global level/scale so command models rely less on speaker timbre.
    Do **not** apply this to speaker-ID features.
    """
    arr = np.asarray(x, dtype=np.float32)
    if arr.ndim == 1:
        mu = float(arr.mean())
        sigma = float(arr.std())
        return ((arr - mu) / (sigma + eps)).astype(np.float32)
    if arr.ndim != 2:
        raise ValueError(f"Expected 1-D or 2-D features, got shape {arr.shape}")
    mu = arr.mean(axis=1, keepdims=True)
    sigma = arr.std(axis=1, keepdims=True)
    return ((arr - mu) / (sigma + eps)).astype(np.float32)
