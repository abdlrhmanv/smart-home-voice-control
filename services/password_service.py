"""Voice password authentication — STT gate + Arduino unlock."""

from __future__ import annotations

from audio.recorder import record_audio
from ai.predict import verify_password
from services.device_service import lock_home, unlock_home


def authenticate():
    """
    Record speech, verify against the configured password via Whisper,
    and notify Arduino (PASSWORD_OK / PASSWORD_FAIL).
    """
    audio_path = record_audio()
    result = verify_password(audio_path)

    if result.password_ok:
        unlock_home()
    else:
        lock_home()

    return result
