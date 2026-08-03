"""Unit tests for persisted activity log."""

from utils.activity_store import (
    append_activity_entry,
    clear_activity_log,
    load_activity_log,
)


def test_activity_roundtrip(tmp_path):
    path = tmp_path / "activity.jsonl"
    append_activity_entry("ahmed", "light_on", 91.2, path=path)
    append_activity_entry("abdullah", "music_off", 88.0, executed=False, path=path)
    rows = load_activity_log(path=path)
    assert len(rows) == 2
    assert rows[0]["command"] == "music_off"  # newest first
    assert rows[1]["user"] == "ahmed"
    clear_activity_log(path=path)
    assert load_activity_log(path=path) == []
