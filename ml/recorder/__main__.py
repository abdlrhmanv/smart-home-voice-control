"""python -m recorder"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .app import main
from .config import SPEAKER_NAME


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Voice dataset recorder")
    p.add_argument("--speaker", default=SPEAKER_NAME)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse()
    main(speaker_name=args.speaker)
