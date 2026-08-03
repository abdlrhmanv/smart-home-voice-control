"""Confidence rejection behaviour."""

from __future__ import annotations

import numpy as np

from src.application.pipeline import SmartHomePipeline
from src.config import InferenceConfig
from src.domain.labels import COMMAND_LABELS, SPEAKER_LABELS


class FakeClf:
    def __init__(self, label_id: int, conf: float, n_classes: int):
        self.label_id = label_id
        self.conf = conf
        self.n_classes = n_classes

    def predict(self, x):
        return np.asarray([self.label_id])

    def predict_proba(self, x):
        probs = np.zeros((1, self.n_classes), dtype=float)
        if self.n_classes == 1:
            probs[0, 0] = 1.0
            return probs
        rem = max(0.0, 1.0 - self.conf)
        other = rem / (self.n_classes - 1)
        probs[0, :] = other
        probs[0, self.label_id] = self.conf
        return probs


class FakeFeatures:
    def extract_from_file(self, path):
        return np.zeros(122, dtype=np.float32)


class FakeTranscriber:
    def check_password(self, audio_path, expected):
        return False, "nope"


def _pipe(speaker_conf: float, command_conf: float, cfg: InferenceConfig) -> SmartHomePipeline:
    return SmartHomePipeline(
        speaker_clf=FakeClf(0, speaker_conf, len(SPEAKER_LABELS)),
        command_clf=FakeClf(0, command_conf, len(COMMAND_LABELS)),
        feature_extractor=FakeFeatures(),
        transcriber=FakeTranscriber(),
        speaker_labels=SPEAKER_LABELS,
        command_labels=COMMAND_LABELS,
        config=cfg,
    )


def test_rejects_low_command_confidence(tmp_path):
    cfg = InferenceConfig(min_command_confidence=0.8, min_speaker_confidence=0.0)
    pipe = _pipe(speaker_conf=0.99, command_conf=0.4, cfg=cfg)
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"")  # path unused by FakeFeatures
    result = pipe.predict_voice_command(wav)
    assert result.accepted is False
    assert result.command == "unknown"
    assert result.action == {}


def test_accepts_high_confidence(tmp_path):
    cfg = InferenceConfig(min_command_confidence=0.5, min_speaker_confidence=0.4)
    pipe = _pipe(speaker_conf=0.9, command_conf=0.9, cfg=cfg)
    result = pipe.predict_voice_command(tmp_path / "x.wav")
    assert result.accepted is True
    assert result.command == "light_on"
    assert result.action.get("arduino") == "LIGHT_ON"


def test_rejects_low_speaker_confidence_clears_action(tmp_path):
    cfg = InferenceConfig(min_command_confidence=0.5, min_speaker_confidence=0.8)
    pipe = _pipe(speaker_conf=0.3, command_conf=0.95, cfg=cfg)
    result = pipe.predict_voice_command(tmp_path / "x.wav")
    assert result.accepted is False
    assert result.speaker == "unknown"
    assert result.command == "light_on"
    assert result.action == {}


def test_run_full_preserves_password_ok(tmp_path):
    class OkTranscriber:
        def check_password(self, audio_path, expected):
            return True, "open sesame"

    cfg = InferenceConfig(
        min_command_confidence=0.5,
        min_speaker_confidence=0.4,
        require_known_speaker=False,
    )
    pipe = _pipe(speaker_conf=0.9, command_conf=0.9, cfg=cfg)
    pipe.transcriber = OkTranscriber()
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"")
    result = pipe.run_full(wav, wav)
    assert result.password_ok is True
    assert result.transcript == "open sesame"
    assert result.accepted is True
