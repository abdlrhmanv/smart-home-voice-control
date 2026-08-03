"""In-memory SessionStore for unit tests (no Streamlit)."""

from __future__ import annotations


class InMemorySessionStore:
    def __init__(self) -> None:
        self.authenticated = False
        self.arduino_synced = False
        self.light = False
        self.music = False
        self.temperature: float | None = None
        self.temperature_fresh = False
        self.last_user = "Unknown"
        self.last_command = "None"
        self.confidence = 0.0
        self.recognition_result: dict | None = None

    def is_authenticated(self) -> bool:
        return self.authenticated

    def set_authenticated(self, value: bool) -> None:
        self.authenticated = value

    def get_arduino_synced(self) -> bool:
        return self.arduino_synced

    def set_arduino_synced(self, value: bool) -> None:
        self.arduino_synced = value

    def get_light(self) -> bool:
        return self.light

    def set_light(self, value: bool) -> None:
        self.light = value

    def get_music(self) -> bool:
        return self.music

    def set_music(self, value: bool) -> None:
        self.music = value

    def get_temperature(self) -> float | None:
        return self.temperature

    def set_temperature(self, value: float | None, *, fresh: bool) -> None:
        if value is not None or fresh:
            self.temperature = value
        self.temperature_fresh = fresh

    def set_recognition(self, user: str, command: str, confidence: float) -> None:
        self.last_user = user
        self.last_command = command
        self.confidence = confidence
        self.recognition_result = {
            "user": user,
            "command": command,
            "confidence": confidence,
        }

    def get_last_user(self) -> str:
        return self.last_user

    def set_last_user(self, user: str) -> None:
        self.last_user = user

    def get_last_command(self) -> str:
        return self.last_command

    def get_confidence(self) -> float:
        return float(self.confidence)
