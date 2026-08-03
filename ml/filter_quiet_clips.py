#!/usr/bin/env python3
"""List or quarantine unusually quiet / clipped dataset WAVs.

Default is dry-run (print only). Use --move to relocate into
data/quarantine/ quietly so training can ignore them.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.domain.paths import ProjectPaths
from src.infrastructure.filesystem import FilesystemDatasetRepository


def _stats(path: Path) -> dict:
    y, sr = sf.read(str(path), always_2d=False)
    y = np.asarray(y, dtype=np.float32)
    if y.ndim > 1:
        y = y.mean(axis=1)
    rms = float(np.sqrt(np.mean(y**2))) if y.size else 0.0
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    return {"rms": rms, "peak": peak, "sr": int(sr)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rms-min", type=float, default=0.005)
    p.add_argument("--peak-clip", type=float, default=0.99)
    p.add_argument(
        "--move",
        action="store_true",
        help="Move flagged files into data/quarantine/ mirroring relative paths",
    )
    args = p.parse_args()

    paths = ProjectPaths.from_package()
    repo = FilesystemDatasetRepository()
    quarantine = paths.data_dir / "quarantine"
    flagged: list[tuple[Path, str]] = []

    for sample in repo.discover():
        try:
            st = _stats(sample.path)
        except Exception as exc:
            flagged.append((sample.path, f"unreadable:{exc}"))
            continue
        reasons = []
        if st["rms"] < args.rms_min:
            reasons.append(f"quiet_rms={st['rms']:.4f}")
        if st["peak"] >= args.peak_clip:
            reasons.append(f"clipped_peak={st['peak']:.3f}")
        if reasons:
            flagged.append((sample.path, ",".join(reasons)))

    print(f"Flagged {len(flagged)} / {len(repo.discover())} clips")
    for path, reason in flagged[:50]:
        rel = path.relative_to(repo.root())
        print(f"  {rel}  ({reason})")
    if len(flagged) > 50:
        print(f"  ... and {len(flagged) - 50} more")

    if args.move and flagged:
        for path, _ in flagged:
            rel = path.relative_to(repo.root())
            dest = quarantine / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest))
        print(f"\nMoved {len(flagged)} file(s) → {quarantine}")
    elif flagged:
        print("\nDry-run only. Re-run with --move to quarantine these files.")


if __name__ == "__main__":
    main()
