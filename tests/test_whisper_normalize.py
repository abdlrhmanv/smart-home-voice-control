"""Whisper adapter unit tests (no model download)."""

from __future__ import annotations

import os

import pytest

from src.infrastructure.whisper.transcriber import FasterWhisperTranscriber


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Open Sesame!", "open sesame"),
        ("  open   sesame  ", "open sesame"),
        ("OPEN-SESAME", "open sesame"),
    ],
)
def test_normalize_text(raw, expected):
    assert FasterWhisperTranscriber.normalize_text(raw) == expected


def test_check_password_matches_normalized_expected(tmp_path, monkeypatch):
    tr = FasterWhisperTranscriber()
    # ``transcribe`` always returns normalized text in production.
    monkeypatch.setattr(tr, "transcribe", lambda path: "open sesame")
    ok, heard = tr.check_password(tmp_path / "x.wav", "Open Sesame!")
    assert ok is True
    assert heard == "open sesame"


def test_check_password_rejects_mismatch(tmp_path, monkeypatch):
    tr = FasterWhisperTranscriber()
    monkeypatch.setattr(tr, "transcribe", lambda path: "hello world")
    ok, heard = tr.check_password(tmp_path / "x.wav", "open sesame")
    assert ok is False
    assert heard == "hello world"


@pytest.mark.skipif(
    os.environ.get("RUN_WHISPER_E2E") != "1",
    reason="Set RUN_WHISPER_E2E=1 to run real Whisper (downloads model)",
)
def test_whisper_e2e_on_dataset_sample():
    from pathlib import Path

    samples = list(Path("ml/data/dataset").rglob("*.wav"))
    if not samples:
        pytest.skip("no dataset wav")
    tr = FasterWhisperTranscriber()
    # Real STT — should return some non-empty normalized string
    text = tr.transcribe(samples[0])
    assert isinstance(text, str)
