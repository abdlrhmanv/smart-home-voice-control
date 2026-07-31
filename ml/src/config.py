"""Central configuration for audio, training, and inference."""

from __future__ import annotations

from dataclasses import dataclass, field


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


# Module-level defaults used by factories
AUDIO = AudioConfig()
TRAINING = TrainingConfig()
INFERENCE = InferenceConfig()
