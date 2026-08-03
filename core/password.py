"""Password authentication use-case."""

from __future__ import annotations

from core.home import HomeControlService
from core.models import AuthResult
from core.ports import AudioRecorder, VoiceGateway


class PasswordService:
    def __init__(
        self,
        voice: VoiceGateway,
        recorder: AudioRecorder,
        home: HomeControlService,
    ) -> None:
        self.voice = voice
        self.recorder = recorder
        self.home = home

    def authenticate(self, audio_path: str | None = None) -> AuthResult:
        path = audio_path or self.recorder.record()
        raw = self.voice.verify_password(path)
        if raw.password_ok:
            synced = self.home.unlock()
        else:
            self.home.lock()
            synced = False
        unlocked = self.home.store.is_authenticated()
        result = AuthResult.from_pipeline(
            raw, unlocked=unlocked, arduino_synced=synced
        )
        if result.unlocked and result.speaker:
            self.home.store.set_last_user(result.speaker)
        return result
