"""Central configuration for audio, training, and inference."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16_000
    n_mfcc: int = 40
    n_fft: int = 2048
    hop_length: int = 512
    peak_normalize: bool = True


@dataclass(frozen=True)
class TrainingConfig:
    test_size: float = 0.2
    random_state: int = 42
    tune: bool = False
    svm_c: float = 10.0
    svm_gamma: str | float = "scale"
    f1_threshold: float = 0.85
    # Platt/isotonic wrap via CalibratedClassifierCV after fit/tune
    calibrate: bool = True
    # Waveform noise/gain copies while building the training matrix
    augment: bool = False
    augment_copies: int = 1
    param_grid: dict = field(
        default_factory=lambda: {
            "clf__C": [1.0, 10.0, 50.0],
            "clf__gamma": ["scale", 0.01, 0.001],
        }
    )


@dataclass(frozen=True)
class InferenceConfig:
    password: str = "open sesame"
    whisper_size: str = "base"
    device: str = "cpu"
    language: str = "en"
    # Reject predictions below these probabilities (0–1). Set to 0 to disable.
    min_command_confidence: float = 0.55
    min_speaker_confidence: float = 0.45
    unknown_label: str = "unknown"
    # Password must match STT phrase AND a known enrolled speaker.
    require_known_speaker: bool = True
    password_min_speaker_confidence: float = 0.45
    # Apply per-utterance CMVN to command features (improves cross-speaker).
    command_cmvn: bool = True

    @classmethod
    def from_env(cls, base: InferenceConfig | None = None) -> InferenceConfig:
        """Overlay environment variables on defaults.

        Supported:
          WHISPER_SIZE, WHISPER_DEVICE, WHISPER_LANGUAGE
          SMART_HOME_PASSWORD
          MIN_COMMAND_CONFIDENCE, MIN_SPEAKER_CONFIDENCE
          REQUIRE_KNOWN_SPEAKER (=0/1/true/false)
        """
        cfg = base or cls()
        updates: dict = {}

        if size := os.environ.get("WHISPER_SIZE"):
            updates["whisper_size"] = size.strip()
        if device := os.environ.get("WHISPER_DEVICE"):
            updates["device"] = device.strip()
        if lang := os.environ.get("WHISPER_LANGUAGE"):
            updates["language"] = lang.strip()
        if password := os.environ.get("SMART_HOME_PASSWORD"):
            updates["password"] = password.strip()

        if (v := os.environ.get("MIN_COMMAND_CONFIDENCE")) is not None:
            updates["min_command_confidence"] = float(v)
        if (v := os.environ.get("MIN_SPEAKER_CONFIDENCE")) is not None:
            updates["min_speaker_confidence"] = float(v)
        if (v := os.environ.get("PASSWORD_MIN_SPEAKER_CONFIDENCE")) is not None:
            updates["password_min_speaker_confidence"] = float(v)
        if (v := os.environ.get("REQUIRE_KNOWN_SPEAKER")) is not None:
            updates["require_known_speaker"] = v.strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }

        return replace(cfg, **updates) if updates else cfg


# Module-level defaults used by factories
AUDIO = AudioConfig()
TRAINING = TrainingConfig()
INFERENCE = InferenceConfig.from_env()
