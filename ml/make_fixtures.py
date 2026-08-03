#!/usr/bin/env python3
"""Generate synthetic WAV fixtures for offline e2e tests (no mic needed)."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 16_000


def tone(freq: float, seconds: float = 1.0, amp: float = 0.3) -> np.ndarray:
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def noise(seconds: float = 1.0, amp: float = 0.05) -> np.ndarray:
    rng = np.random.default_rng(0)
    return (amp * rng.normal(0, 1, int(SR * seconds))).astype(np.float32)


def write_fixtures(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "tone_440.wav": tone(440.0, 1.0),
        "tone_880.wav": tone(880.0, 1.0),
        "noise.wav": noise(1.0, 0.08),
        "silence.wav": np.zeros(SR, dtype=np.float32),
        "short_blip.wav": tone(520.0, 0.25, amp=0.4),
    }
    paths = []
    for name, y in files.items():
        path = out_dir / name
        sf.write(path, y, SR)
        paths.append(path)
        print(f"  wrote {path}")
    return paths


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "audio",
    )
    args = p.parse_args()
    print(f"Fixtures → {args.out}")
    write_fixtures(args.out)


if __name__ == "__main__":
    main()
