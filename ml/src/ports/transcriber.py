"""Speech-to-text port."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class SpeechTranscriber(Protocol):
    def transcribe(self, audio_path: str | Path) -> str: ...

    def check_password(
        self, audio_path: str | Path, expected: str
    ) -> tuple[bool, str]: ...
