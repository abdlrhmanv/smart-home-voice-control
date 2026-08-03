"""Thin façade from the Streamlit app into the ML Clean Architecture package."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

ML_PATH = Path(__file__).resolve().parent.parent / "ml"
if str(ML_PATH) not in sys.path:
    sys.path.insert(0, str(ML_PATH))

from src.application import SmartHomePipeline


def _create_pipeline() -> SmartHomePipeline:
    return SmartHomePipeline.create_default()


# Process-wide fallback (tests / CLI). Survives Streamlit reruns via sys.modules.
_lru_pipeline = lru_cache(maxsize=1)(_create_pipeline)

# Prefer Streamlit's resource cache when available (stable function object).
try:
    import streamlit as st

    _st_pipeline = st.cache_resource(_create_pipeline)
except Exception:  # pragma: no cover - streamlit always installed in app env
    _st_pipeline = _lru_pipeline


def get_pipeline() -> SmartHomePipeline:
    """Return a cached SmartHomePipeline (SVM + lazy Whisper)."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is not None:
            return _st_pipeline()
    except Exception:
        pass
    return _lru_pipeline()


def predict_voice(audio_path: str) -> dict:
    """Predict speaker and command from an audio file."""
    result = get_pipeline().predict_voice_command(audio_path)
    return {
        "speaker": result.speaker,
        "command": result.command,
        "confidence": round((result.command_confidence or 0.0) * 100, 2),
        "speaker_confidence": round((result.speaker_confidence or 0.0) * 100, 2),
        "action": result.action or {},
        "message": result.message,
        "accepted": result.accepted,
        "rejected_reason": result.rejected_reason,
    }


def verify_password(audio_path: str):
    """Verify the spoken password using Whisper STT."""
    return get_pipeline().verify_password(audio_path)
