"""ML pipeline adapter used by password/voice use-cases."""

from __future__ import annotations

from typing import Any

from ai.predict import predict_voice, verify_password


class MlVoiceGateway:
    def verify_password(self, audio_path: str) -> Any:
        return verify_password(audio_path)

    def predict_command(self, audio_path: str) -> dict[str, Any]:
        return predict_voice(audio_path)
