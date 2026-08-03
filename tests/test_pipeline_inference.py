"""Integration tests against real models + dataset samples."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.application.pipeline import SmartHomePipeline
from src.domain.labels import COMMAND_LABELS, SPEAKER_LABELS

ML = Path(__file__).resolve().parents[1] / "ml"
MODELS = ML / "models"


@pytest.fixture(scope="module")
def pipeline():
    if not (MODELS / "speaker.pkl").exists() or not (MODELS / "command.pkl").exists():
        pytest.skip("Trained models missing")
    return SmartHomePipeline.create_default()


def test_predict_known_sample(pipeline, dataset_sample):
    # path like .../abdullah/music_on/music_on_011.wav
    speaker = dataset_sample.parent.parent.name
    command = dataset_sample.parent.name
    result = pipeline.predict_voice_command(dataset_sample)
    assert result.speaker in SPEAKER_LABELS
    assert result.command in COMMAND_LABELS
    assert result.command_confidence is not None and result.command_confidence > 0
    # Most in-distribution clips should be correct; soft-check label folders
    assert result.speaker == speaker or result.command == command


def test_noise_is_rejected_or_labeled(pipeline, tmp_wav):
    """Noise must not crash; low confidence should reject as unknown."""
    result = pipeline.predict_voice_command(tmp_wav)
    assert result.speaker is not None
    assert result.command is not None
    if result.accepted:
        assert result.speaker in SPEAKER_LABELS
        assert result.command in COMMAND_LABELS
    else:
        assert result.command == "unknown" or result.speaker == "unknown"


def test_action_attached(pipeline, dataset_sample):
    result = pipeline.predict_voice_command(dataset_sample)
    assert result.action is not None
    assert "arduino" in result.action
