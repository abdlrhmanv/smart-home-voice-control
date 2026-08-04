"""Command phrase matching + STT override over SVM."""

from __future__ import annotations

import numpy as np
import pytest

from src.application.pipeline import SmartHomePipeline
from src.config import InferenceConfig
from src.domain.labels import COMMAND_LABELS, SPEAKER_LABELS, match_command_phrase
from tests.test_confidence_reject import FakeClf, FakeFeatures


@pytest.mark.parametrize(
    "transcript,expected",
    [
        ("light on", "light_on"),
        ("lighton", "light_on"),
        ("Light On!", "light_on"),
        ("please light on now", "light_on"),
        ("music off", "music_off"),
        ("musicoff", "music_off"),
        ("light off", "light_off"),
        ("music on", "music_on"),
        ("hello world", None),
        ("", None),
    ],
)
def test_match_command_phrase(transcript, expected):
    assert match_command_phrase(transcript) == expected


def test_stt_overrides_wrong_svm_command(tmp_path):
    class SttTranscriber:
        def check_password(self, audio_path, expected):
            return False, ""

        def transcribe(self, audio_path):
            return "lighton"

    cfg = InferenceConfig(
        min_command_confidence=0.5,
        min_speaker_confidence=0.4,
        command_stt_override=True,
    )
    # SVM wrongly predicts music_off (id 3)
    pipe = SmartHomePipeline(
        speaker_clf=FakeClf(0, 0.9, len(SPEAKER_LABELS)),
        command_clf=FakeClf(3, 0.92, len(COMMAND_LABELS)),
        feature_extractor=FakeFeatures(),
        transcriber=SttTranscriber(),
        speaker_labels=SPEAKER_LABELS,
        command_labels=COMMAND_LABELS,
        config=cfg,
    )
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"")
    result = pipe.predict_voice_command(wav)
    assert result.accepted is True
    assert result.command == "light_on"
    assert result.transcript == "lighton"
    assert "light on" in result.message


def test_stt_override_can_be_disabled(tmp_path):
    class SttTranscriber:
        def check_password(self, audio_path, expected):
            return False, ""

        def transcribe(self, audio_path):
            return "light on"

    cfg = InferenceConfig(
        min_command_confidence=0.5,
        min_speaker_confidence=0.4,
        command_stt_override=False,
    )
    pipe = SmartHomePipeline(
        speaker_clf=FakeClf(0, 0.9, len(SPEAKER_LABELS)),
        command_clf=FakeClf(3, 0.92, len(COMMAND_LABELS)),
        feature_extractor=FakeFeatures(),
        transcriber=SttTranscriber(),
        speaker_labels=SPEAKER_LABELS,
        command_labels=COMMAND_LABELS,
        config=cfg,
    )
    result = pipe.predict_voice_command(tmp_path / "x.wav")
    assert result.command == "music_off"
