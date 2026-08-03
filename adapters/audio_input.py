"""Microphone recording adapter."""

from __future__ import annotations


class MicrophoneRecorder:
    def record(self) -> str:
        from audio.recorder import record_audio

        return record_audio()
