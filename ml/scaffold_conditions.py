#!/usr/bin/env python3
"""Create optional multi-condition folders under the dataset tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.domain.labels import COMMAND_LABELS, RECORDING_CONDITIONS, SPEAKER_LABELS
from src.domain.paths import ProjectPaths


def scaffold(speakers: list[str] | None = None, conditions: list[str] | None = None) -> None:
    root = ProjectPaths.from_package().dataset_dir
    speakers = speakers or SPEAKER_LABELS.names()
    conditions = conditions or list(RECORDING_CONDITIONS)
    created = 0
    for speaker in speakers:
        for command in COMMAND_LABELS.names():
            for cond in conditions:
                path = root / speaker / command / cond
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    created += 1
                    print(f"  + {path.relative_to(root)}")
    print(f"\nDone. Created {created} folder(s) under {root}")
    print("Record into a condition by setting RECORDING_CONDITION in ml/recorder/config.py")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--speaker", action="append", help="Limit to speaker(s)")
    p.add_argument("--condition", action="append", help="Limit to condition(s)")
    args = p.parse_args()
    scaffold(speakers=args.speaker, conditions=args.condition)


if __name__ == "__main__":
    main()
