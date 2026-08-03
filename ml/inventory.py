#!/usr/bin/env python3
"""Print dataset inventory (including recording conditions)."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.domain.labels import COMMAND_LABELS, RECORDING_CONDITIONS, SPEAKER_LABELS
from src.infrastructure.filesystem import FilesystemDatasetRepository


def main() -> None:
    repo = FilesystemDatasetRepository()
    samples = repo.discover()
    print(f"Dataset root: {repo.root()}")
    print(f"Total clips : {len(samples)}\n")

    by_speaker = Counter(s.speaker for s in samples)
    by_command = Counter(s.command for s in samples)
    by_pair = Counter((s.speaker, s.command) for s in samples)
    by_cond = Counter(s.condition for s in samples)

    print("Per speaker")
    for name in SPEAKER_LABELS.names():
        n = by_speaker.get(name, 0)
        status = "✓" if n >= 100 else ("·" if n == 0 else "⚠")
        print(f"  {status} {name:14s} {n:4d}")

    print("\nPer command")
    for name in COMMAND_LABELS.names():
        print(f"  {name:12s} {by_command.get(name, 0):4d}")

    print("\nPer condition")
    for name in RECORDING_CONDITIONS:
        print(f"  {name:12s} {by_cond.get(name, 0):4d}")
    extras = [k for k in by_cond if k not in RECORDING_CONDITIONS]
    for name in extras:
        print(f"  {name:12s} {by_cond.get(name, 0):4d}")

    print("\nSpeaker × command")
    print(f"  {'':14s}", end="")
    for cmd in COMMAND_LABELS.names():
        print(f"{cmd:>12s}", end="")
    print()
    for speaker in SPEAKER_LABELS.names():
        print(f"  {speaker:14s}", end="")
        for cmd in COMMAND_LABELS.names():
            print(f"{by_pair.get((speaker, cmd), 0):12d}", end="")
        print()

    missing = [
        (s, c)
        for s in SPEAKER_LABELS.names()
        for c in COMMAND_LABELS.names()
        if by_pair.get((s, c), 0) == 0
    ]
    if missing:
        print("\nMissing folders / empty:")
        for s, c in missing:
            print(f"  - {s}/{c}")
    else:
        print("\n✓ All speaker/command folders have at least one clip.")

    n_conds = sum(1 for c in RECORDING_CONDITIONS if by_cond.get(c, 0) > 0)
    if n_conds < 2:
        print(
            "\n⚠ Tip: only one recording condition detected. "
            "Use scaffold_conditions.py + recorder RECORDING_CONDITION "
            "to add distance/noise/rate takes for stronger LOSO."
        )


if __name__ == "__main__":
    main()
