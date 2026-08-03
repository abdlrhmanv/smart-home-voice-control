"""Tests for speaker-bound password and CMVN helpers."""

from __future__ import annotations

import numpy as np

from src.application.pipeline import SmartHomePipeline
from src.config import InferenceConfig
from src.domain.labels import COMMAND_LABELS, SPEAKER_LABELS
from src.infrastructure.librosa.normalize import cmvn


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
        return np.arange(122, dtype=np.float32)


class FakeTranscriber:
    def __init__(self, ok: bool = True, text: str = "open sesame"):
        self.ok = ok
        self.text = text

    def check_password(self, audio_path, expected):
        return self.ok, self.text


def _pipe(
    *,
    phrase_ok: bool,
    speaker_conf: float,
    cfg: InferenceConfig,
) -> SmartHomePipeline:
    return SmartHomePipeline(
        speaker_clf=FakeClf(0, speaker_conf, len(SPEAKER_LABELS)),
        command_clf=FakeClf(0, 0.9, len(COMMAND_LABELS)),
        feature_extractor=FakeFeatures(),
        transcriber=FakeTranscriber(ok=phrase_ok),
        speaker_labels=SPEAKER_LABELS,
        command_labels=COMMAND_LABELS,
        config=cfg,
    )


def test_cmvn_zero_mean_unit_std():
    x = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    y = cmvn(x)
    assert abs(float(y.mean())) < 1e-5
    assert abs(float(y.std()) - 1.0) < 1e-4


def test_password_rejects_unknown_speaker(tmp_path):
    cfg = InferenceConfig(
        require_known_speaker=True,
        password_min_speaker_confidence=0.7,
    )
    pipe = _pipe(phrase_ok=True, speaker_conf=0.2, cfg=cfg)
    result = pipe.verify_password(tmp_path / "p.wav")
    assert result.password_ok is False
    assert result.action["arduino"] == "PASSWORD_FAIL"
    assert "speaker" in (result.rejected_reason or "")


def test_password_accepts_enrolled_speaker(tmp_path):
    cfg = InferenceConfig(
        require_known_speaker=True,
        password_min_speaker_confidence=0.4,
    )
    pipe = _pipe(phrase_ok=True, speaker_conf=0.95, cfg=cfg)
    result = pipe.verify_password(tmp_path / "p.wav")
    assert result.password_ok is True
    assert result.speaker == "ahmed"
    assert result.action["arduino"] == "PASSWORD_OK"


def test_password_phrase_still_required(tmp_path):
    cfg = InferenceConfig(require_known_speaker=True)
    pipe = _pipe(phrase_ok=False, speaker_conf=0.99, cfg=cfg)
    result = pipe.verify_password(tmp_path / "p.wav")
    assert result.password_ok is False
    assert result.rejected_reason == "wrong_password"
