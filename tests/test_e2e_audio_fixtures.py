"""End-to-end inference against synthetic audio fixtures + real models."""

from __future__ import annotations

from pathlib import Path

import pytest
import soundfile as sf
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "audio"
ML = ROOT / "ml"


@pytest.fixture(scope="module")
def fixtures_ready():
    FIX.mkdir(parents=True, exist_ok=True)
    if not (FIX / "noise.wav").exists():
        import sys

        sys.path.insert(0, str(ML))
        from make_fixtures import write_fixtures

        write_fixtures(FIX)
    return FIX


@pytest.fixture(scope="module")
def pipeline():
    if not (ML / "models" / "speaker.pkl").exists():
        pytest.skip("models missing")
    import sys

    if str(ML) not in sys.path:
        sys.path.insert(0, str(ML))
    from src.application import SmartHomePipeline

    return SmartHomePipeline.create_default()


def test_fixture_files_exist(fixtures_ready):
    assert (fixtures_ready / "noise.wav").exists()
    assert (fixtures_ready / "silence.wav").exists()


def test_pipeline_handles_noise_fixture(pipeline, fixtures_ready):
    result = pipeline.predict_voice_command(fixtures_ready / "noise.wav")
    assert result.speaker is not None
    assert result.command is not None
    # Noise should usually be rejected by confidence gates
    if not result.accepted:
        assert result.command == "unknown" or result.speaker == "unknown"


def test_pipeline_handles_silence_fixture(pipeline, fixtures_ready):
    result = pipeline.predict_voice_command(fixtures_ready / "silence.wav")
    assert result.command is not None


def test_dataset_sample_still_predicts(pipeline):
    samples = list((ML / "data" / "dataset").rglob("*.wav"))
    if not samples:
        pytest.skip("no dataset")
    sample = samples[0]
    result = pipeline.predict_voice_command(sample)
    assert result.command_confidence is not None
