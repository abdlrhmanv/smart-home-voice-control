"""Voice command workflow — record → classify → actuate."""

from __future__ import annotations

from audio.recorder import record_audio
from ai.predict import predict_voice
from utils.data import set_recognition_result
from services.device_service import execute_command


def start_listening(min_confidence: float | None = None) -> dict:
    """
    Record audio, run speaker + command models, update UI state,
    and send the matching Arduino command only when accepted.

    ``min_confidence`` (0–1) optionally tightens the command threshold on top
    of the pipeline's configured gate. ``None`` uses pipeline defaults only.
    """
    audio_path = record_audio()
    result = predict_voice(audio_path)

    user = result["speaker"]
    command = result["command"]
    confidence = result["confidence"]

    set_recognition_result(user, command, confidence)

    accepted = bool(result.get("accepted", True))
    if min_confidence is not None and confidence < min_confidence * 100:
        accepted = False
        result["rejected_reason"] = (
            result.get("rejected_reason") or ""
        ) + f"; override min_confidence {min_confidence:.2f}"

    if accepted and command != "unknown":
        execute_command(command)
        result["executed"] = True
    else:
        result["executed"] = False
        result["accepted"] = False

    return result
