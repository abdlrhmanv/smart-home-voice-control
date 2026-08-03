#!/usr/bin/env python3
"""Validate dataset quality and multi-condition coverage.

Checks:
  - speaker × command counts
  - optional condition folders (close/distance/noise/rate)
  - duration, peak, RMS (flag silent / clipped files)
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.domain.labels import (
    COMMAND_LABELS,
    DEFAULT_CONDITION,
    RECORDING_CONDITIONS,
    SPEAKER_LABELS,
)
from src.infrastructure.filesystem import FilesystemDatasetRepository


def _audio_stats(path: Path) -> dict:
    y, sr = sf.read(str(path), always_2d=False)
    y = np.asarray(y, dtype=np.float32)
    if y.ndim > 1:
        y = y.mean(axis=1)
    dur = float(y.size / sr) if sr else 0.0
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    rms = float(np.sqrt(np.mean(y**2))) if y.size else 0.0
    return {"duration": dur, "peak": peak, "rms": rms, "sr": int(sr)}


def validate(
    *,
    min_per_pair: int = 20,
    min_conditions: int = 1,
    min_duration: float = 0.4,
    max_duration: float = 6.0,
    rms_min: float = 0.005,
    peak_clip: float = 0.99,
) -> int:
    repo = FilesystemDatasetRepository()
    samples = repo.discover()
    print(f"Dataset root: {repo.root()}")
    print(f"Total clips : {len(samples)}\n")

    by_pair = Counter((s.speaker, s.command) for s in samples)
    by_cond = Counter(s.condition for s in samples)
    by_pair_cond = Counter((s.speaker, s.command, s.condition) for s in samples)

    print("Conditions present")
    for cond in RECORDING_CONDITIONS:
        print(f"  {cond:10s} {by_cond.get(cond, 0):4d}")
    other = sum(v for k, v in by_cond.items() if k not in RECORDING_CONDITIONS)
    if other:
        print(f"  {'(other)':10s} {other:4d}")

    errors = 0
    warnings = 0

    print("\nCoverage (speaker × command)")
    for speaker in SPEAKER_LABELS.names():
        for cmd in COMMAND_LABELS.names():
            n = by_pair.get((speaker, cmd), 0)
            conds = {
                c
                for c in RECORDING_CONDITIONS
                if by_pair_cond.get((speaker, cmd, c), 0) > 0
            }
            # Flat legacy layout counts as DEFAULT_CONDITION
            if by_pair_cond.get((speaker, cmd, DEFAULT_CONDITION), 0) > 0:
                conds.add(DEFAULT_CONDITION)
            flag = "✓" if n >= min_per_pair else "⚠"
            if n < min_per_pair:
                warnings += 1
            if len(conds) < min_conditions:
                warnings += 1
                flag = "⚠"
            print(
                f"  {flag} {speaker:12s} {cmd:12s} n={n:3d}  "
                f"conditions={sorted(conds) or ['—']}"
            )

    print("\nAudio quality scan")
    bad: list[str] = []
    for s in samples:
        try:
            st = _audio_stats(s.path)
        except Exception as exc:
            bad.append(f"{s.path}: unreadable ({exc})")
            errors += 1
            continue
        issues = []
        if st["duration"] < min_duration or st["duration"] > max_duration:
            issues.append(f"duration={st['duration']:.2f}s")
        if st["rms"] < rms_min:
            issues.append(f"silent rms={st['rms']:.4f}")
        if st["peak"] >= peak_clip:
            issues.append(f"clipped peak={st['peak']:.3f}")
        if issues:
            bad.append(f"{s.path.relative_to(repo.root())}: {', '.join(issues)}")
            warnings += 1

    if bad:
        print(f"  Flagged {len(bad)} file(s) (showing up to 20):")
        for line in bad[:20]:
            print(f"    - {line}")
    else:
        print("  ✓ No duration/silence/clipping issues found.")

    print(
        f"\nSummary: {errors} error(s), {warnings} warning(s). "
        f"Target ≥{min_per_pair}/pair and ≥{min_conditions} condition(s)."
    )
    return 1 if errors else 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--min-per-pair", type=int, default=20)
    p.add_argument(
        "--min-conditions",
        type=int,
        default=1,
        help="Warn if fewer recording conditions seen per pair",
    )
    args = p.parse_args()
    raise SystemExit(
        validate(min_per_pair=args.min_per_pair, min_conditions=args.min_conditions)
    )


if __name__ == "__main__":
    main()
