"""Password authentication façade."""

from __future__ import annotations

from core.container import get_container
from core.models import AuthResult


def authenticate(audio_path: str | None = None) -> AuthResult:
    """
    Verify password from a live recording or an existing WAV path
    (useful for uploads / Playwright without a microphone).
    """
    return get_container().password.authenticate(audio_path=audio_path)
