"""Load cached calibration JSON for the Settings dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def reports_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "ml" / "reports"


def load_calibration_report(task: str = "command") -> dict[str, Any] | None:
    path = reports_dir() / f"calibration_{task}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
