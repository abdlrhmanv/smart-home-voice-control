"""Microphone recording adapter."""

from __future__ import annotations

from audio.recorder import record_audio


class MicrophoneRecorder:
    def record(self) -> str:
        return record_audio()
