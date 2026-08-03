"""InferenceConfig environment overlays."""

import os

from src.config import InferenceConfig


def test_from_env_whisper_size(monkeypatch):
    monkeypatch.setenv("WHISPER_SIZE", "tiny")
    monkeypatch.setenv("WHISPER_DEVICE", "cpu")
    cfg = InferenceConfig.from_env(InferenceConfig())
    assert cfg.whisper_size == "tiny"
    assert cfg.device == "cpu"


def test_from_env_require_known_speaker_false(monkeypatch):
    monkeypatch.setenv("REQUIRE_KNOWN_SPEAKER", "0")
    cfg = InferenceConfig.from_env(InferenceConfig(require_known_speaker=True))
    assert cfg.require_known_speaker is False


def test_from_env_confidence(monkeypatch):
    monkeypatch.setenv("MIN_COMMAND_CONFIDENCE", "0.7")
    cfg = InferenceConfig.from_env(InferenceConfig())
    assert cfg.min_command_confidence == 0.7
