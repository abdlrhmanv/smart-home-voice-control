"""Voice command façade — returns a plain dict for page compatibility."""

from __future__ import annotations

from core.container import get_container


def start_listening(
    min_confidence: float | None = None,
    audio_path: str | None = None,
) -> dict:
    """
    Run speaker + command models from a live recording or an existing WAV.

    ``audio_path`` lets the UI / Playwright inject fixtures without a mic.
    """
    result = get_container().voice.start_listening(
        min_confidence=min_confidence,
        audio_path=audio_path,
    )
    return result.to_dict()
