"""Faster-Whisper STT adapter."""

from __future__ import annotations

import re
from pathlib import Path

from src.config import INFERENCE, InferenceConfig


class FasterWhisperTranscriber:
    def __init__(self, config: InferenceConfig | None = None) -> None:
        self.config = config or INFERENCE
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            compute_type = "int8" if self.config.device == "cpu" else "float16"
            self._model = WhisperModel(
                self.config.whisper_size,
                device=self.config.device,
                compute_type=compute_type,
            )
        return self._model

    @staticmethod
    def normalize_text(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def transcribe(self, audio_path: str | Path) -> str:
        model = self._ensure_model()
        segments, _ = model.transcribe(str(audio_path), language=self.config.language)
        return self.normalize_text(" ".join(seg.text for seg in segments))

    def check_password(
        self, audio_path: str | Path, expected: str
    ) -> tuple[bool, str]:
        heard = self.transcribe(audio_path)
        return heard == self.normalize_text(expected), heard
