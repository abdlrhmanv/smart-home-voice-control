"""Persist activity log entries to disk (JSONL)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "activity_log.jsonl"
MAX_ENTRIES = 200


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_activity_entry(
    user: str,
    command: str,
    confidence: float,
    *,
    executed: bool = True,
    path: Path | None = None,
) -> dict[str, Any]:
    """Append one activity row and return the stored entry."""
    target = path or LOG_PATH
    _ensure_parent(target)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "command": command,
        "confidence": confidence,
        "executed": executed,
    }
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def load_activity_log(
    limit: int = 50,
    *,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load newest-first activity entries (up to ``limit``)."""
    target = path or LOG_PATH
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    with target.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return list(reversed(rows[-MAX_ENTRIES:]))[:limit]


def clear_activity_log(*, path: Path | None = None) -> None:
    target = path or LOG_PATH
    if target.exists():
        target.write_text("", encoding="utf-8")
