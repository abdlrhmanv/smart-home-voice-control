"""Voice command use-case — classify then actuate."""

from __future__ import annotations

from core.home import HomeControlService
from core.models import VoiceResult
from core.ports import AudioRecorder, VoiceGateway


class VoiceControlService:
    def __init__(
        self,
        voice: VoiceGateway,
        recorder: AudioRecorder,
        home: HomeControlService,
    ) -> None:
        self.voice = voice
        self.recorder = recorder
        self.home = home

    def start_listening(
        self,
        min_confidence: float | None = None,
        audio_path: str | None = None,
    ) -> VoiceResult:
        self.home.require_auth()
        path = audio_path or self.recorder.record()
        raw = self.voice.predict_command(path)

        speaker = str(raw.get("speaker") or "unknown")
        command = str(raw.get("command") or "unknown")
        confidence = float(raw.get("confidence") or 0.0)
        speaker_confidence = float(raw.get("speaker_confidence") or 0.0)
        message = str(raw.get("message") or "")
        rejected = raw.get("rejected_reason")
        action = raw.get("action") or {}

        self.home.store.set_recognition(speaker, command, confidence)

        accepted = bool(raw.get("accepted", True))
        if min_confidence is not None and confidence < min_confidence * 100:
            accepted = False
            rejected = (rejected or "") + f"; override min_confidence {min_confidence:.2f}"

        executed = False
        if accepted and command != "unknown":
            # Prefer ML action payload when it carries an Arduino command.
            if action.get("arduino"):
                self.home.execute_action(action)
            else:
                self.home.execute_command(command)
            executed = True
        else:
            accepted = False

        return VoiceResult(
            speaker=speaker,
            command=command,
            confidence=confidence,
            speaker_confidence=speaker_confidence,
            message=message,
            accepted=accepted,
            executed=executed,
            rejected_reason=None if accepted else (rejected or message or "rejected"),
            action=action,
        )
