"""End-to-end service flow with mic/serial/ML mocked via AppContainer."""

from __future__ import annotations

import pytest

from core.container import build_container, reset_container, set_container
from core.home import AuthError
from core.memory_store import InMemorySessionStore
from core.models import AuthResult
from services import password_service, voice_service


class FakeSerial:
    def __init__(self):
        self.sent: list[str] = []

    def send_command(self, cmd: str) -> bool:
        self.sent.append(cmd)
        return True

    def request_temperature(self, timeout_s: float = 2.0):
        return 23.0

    def connect(self, port=None):
        return True

    def disconnect(self):
        return None

    def is_connected(self):
        return True

    def resolve_port(self):
        return "/dev/ttyUSB0"


class FakeMusic:
    def start(self) -> bool:
        return True

    def stop(self) -> None:
        return None


class FakeRecorder:
    def __init__(self, path: str):
        self.path = path
        self.calls = 0

    def record(self) -> str:
        self.calls += 1
        return self.path


class FakeVoice:
    def __init__(self):
        self._password = None
        self._command = None

    def set_password(self, result):
        self._password = result

    def set_command(self, result: dict):
        self._command = result

    def verify_password(self, audio_path: str):
        return self._password

    def predict_command(self, audio_path: str) -> dict:
        return dict(self._command or {})


@pytest.fixture
def harness(tmp_path):
    wav = tmp_path / "input.wav"
    wav.write_bytes(b"RIFF....")
    store = InMemorySessionStore()
    serial = FakeSerial()
    voice = FakeVoice()
    recorder = FakeRecorder(str(wav))
    container = build_container(
        store=store,
        serial=serial,
        music=FakeMusic(),
        voice_gateway=voice,
        recorder=recorder,
        allow_offline=True,
    )
    set_container(container)
    yield {
        "store": store,
        "serial": serial,
        "voice": voice,
        "recorder": recorder,
        "wav": wav,
    }
    reset_container()


def test_e2e_wrong_password_locks(harness):
    class Raw:
        password_ok = False
        transcript = "hello"
        message = "Wrong password"
        speaker = None
        speaker_confidence = None
        rejected_reason = "wrong_password"

    harness["voice"].set_password(Raw())
    result = password_service.authenticate()
    assert isinstance(result, AuthResult)
    assert result.password_ok is False
    assert "PASSWORD_FAIL" in harness["serial"].sent
    assert harness["store"].authenticated is False


def test_e2e_password_then_light_on(harness):
    class Raw:
        password_ok = True
        transcript = "open sesame"
        message = "ok"
        speaker = "ahmed"
        speaker_confidence = 0.93
        rejected_reason = None

    harness["voice"].set_password(Raw())
    harness["voice"].set_command(
        {
            "speaker": "ahmed",
            "command": "light_on",
            "confidence": 96.0,
            "speaker_confidence": 91.0,
            "action": {"arduino": "LIGHT_ON"},
            "message": "Detected ahmed saying 'light on'.",
            "accepted": True,
            "rejected_reason": None,
        }
    )

    gate = password_service.authenticate()
    assert gate.password_ok is True
    assert "PASSWORD_OK" in harness["serial"].sent
    assert harness["store"].authenticated is True

    voice = voice_service.start_listening()
    assert voice["executed"] is True
    assert "LIGHT_ON" in harness["serial"].sent
    assert harness["store"].light is True


def test_e2e_voice_requires_auth(harness):
    harness["voice"].set_command(
        {
            "speaker": "ahmed",
            "command": "light_on",
            "confidence": 96.0,
            "accepted": True,
            "action": {"arduino": "LIGHT_ON"},
        }
    )
    with pytest.raises(AuthError):
        voice_service.start_listening()


def test_e2e_rejected_command_not_sent(harness):
    harness["store"].authenticated = True
    harness["voice"].set_command(
        {
            "speaker": "unknown",
            "command": "unknown",
            "confidence": 30.0,
            "speaker_confidence": 20.0,
            "action": {},
            "message": "Rejected",
            "accepted": False,
            "rejected_reason": "low confidence",
        }
    )
    result = voice_service.start_listening()
    assert result["executed"] is False
    assert "LIGHT_ON" not in harness["serial"].sent
    assert "MUSIC_ON" not in harness["serial"].sent


def test_e2e_injected_wav_skips_mic(harness):
    harness["store"].authenticated = True
    harness["voice"].set_command(
        {
            "speaker": "ahmed",
            "command": "music_on",
            "confidence": 90.0,
            "speaker_confidence": 88.0,
            "action": {"arduino": "MUSIC_ON"},
            "message": "ok",
            "accepted": True,
            "rejected_reason": None,
        }
    )
    result = voice_service.start_listening(audio_path=str(harness["wav"]))
    assert harness["recorder"].calls == 0
    assert result["executed"] is True
    assert "MUSIC_ON" in harness["serial"].sent
    assert harness["store"].music is True
