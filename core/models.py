"""Application DTOs — independent of Streamlit and ML dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthResult:
    password_ok: bool
    transcript: str
    message: str
    speaker: str | None = None
    speaker_confidence: float | None = None
    rejected_reason: str | None = None
    arduino_synced: bool = False
    unlocked: bool = False

    @classmethod
    def from_pipeline(cls, result: Any, *, unlocked: bool, arduino_synced: bool) -> AuthResult:
        return cls(
            password_ok=bool(result.password_ok),
            transcript=str(getattr(result, "transcript", "") or ""),
            message=str(getattr(result, "message", "") or ""),
            speaker=getattr(result, "speaker", None),
            speaker_confidence=getattr(result, "speaker_confidence", None),
            rejected_reason=getattr(result, "rejected_reason", None),
            arduino_synced=arduino_synced,
            unlocked=unlocked,
        )


@dataclass
class VoiceResult:
    speaker: str
    command: str
    confidence: float
    speaker_confidence: float
    message: str
    accepted: bool
    executed: bool
    rejected_reason: str | None = None
    action: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaker": self.speaker,
            "command": self.command,
            "confidence": self.confidence,
            "speaker_confidence": self.speaker_confidence,
            "message": self.message,
            "accepted": self.accepted,
            "executed": self.executed,
            "rejected_reason": self.rejected_reason,
            "action": self.action or {},
        }
