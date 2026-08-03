"""End-to-end service flow with mic/serial/ML mocked."""

from __future__ import annotations

import pytest


@pytest.fixture
def mock_audio(tmp_path, monkeypatch):
    wav = tmp_path / "input.wav"
    wav.write_bytes(b"RIFF")

    def _record():
        return str(wav)

    monkeypatch.setattr("audio.recorder.record_audio", _record)
    monkeypatch.setattr("services.password_service.record_audio", _record)
    monkeypatch.setattr("services.voice_service.record_audio", _record)
    return wav


@pytest.fixture
def mock_serial(monkeypatch):
    sent: list[str] = []

    monkeypatch.setattr(
        "api.serial_service.send_command",
        lambda cmd: sent.append(cmd) or True,
    )
    monkeypatch.setattr(
        "services.device_service.send_command",
        lambda cmd: sent.append(cmd) or True,
    )
    return sent


@pytest.fixture
def mock_streamlit_state(monkeypatch):
    """Minimal stand-in so device_service can set session flags."""
    state = {
        "light": False,
        "music": False,
        "authenticated": False,
        "last_user": "Unknown",
        "last_command": "None",
        "confidence": 0.0,
        "activity_log": [],
    }

    class FakeSession(dict):
        def __getattr__(self, item):
            return self[item]

        def __setattr__(self, key, value):
            self[key] = value

    session = FakeSession(state)

    class FakeSt:
        session_state = session

    monkeypatch.setattr("services.device_service.st", FakeSt)
    monkeypatch.setattr("utils.data.st", FakeSt)
    return session


def test_e2e_wrong_password_locks(mock_audio, mock_serial, mock_streamlit_state, monkeypatch):
    from src.domain.models import InferenceResult

    monkeypatch.setattr(
        "services.password_service.verify_password",
        lambda path: InferenceResult(
            password_ok=False,
            transcript="hello",
            message="Wrong password",
            action={"arduino": "PASSWORD_FAIL"},
            accepted=False,
            rejected_reason="wrong_password",
        ),
    )

    from services.password_service import authenticate

    result = authenticate()
    assert result.password_ok is False
    assert "PASSWORD_FAIL" in mock_serial
    assert mock_streamlit_state["authenticated"] is False


def test_e2e_password_then_light_on(
    mock_audio, mock_serial, mock_streamlit_state, monkeypatch
):
    from src.domain.models import InferenceResult

    monkeypatch.setattr(
        "services.password_service.verify_password",
        lambda path: InferenceResult(
            password_ok=True,
            transcript="open sesame",
            speaker="ahmed",
            speaker_confidence=0.93,
            message="ok",
            action={"arduino": "PASSWORD_OK"},
            accepted=True,
        ),
    )
    monkeypatch.setattr(
        "services.voice_service.predict_voice",
        lambda path: {
            "speaker": "ahmed",
            "command": "light_on",
            "confidence": 96.0,
            "speaker_confidence": 91.0,
            "action": {"arduino": "LIGHT_ON"},
            "message": "Detected ahmed saying 'light on'.",
            "accepted": True,
            "rejected_reason": None,
        },
    )

    from services.password_service import authenticate
    from services.voice_service import start_listening

    gate = authenticate()
    assert gate.password_ok is True
    assert "PASSWORD_OK" in mock_serial
    assert mock_streamlit_state["authenticated"] is True

    voice = start_listening()
    assert voice["executed"] is True
    assert "LIGHT_ON" in mock_serial
    assert mock_streamlit_state["light"] is True


def test_e2e_rejected_command_not_sent(
    mock_audio, mock_serial, mock_streamlit_state, monkeypatch
):
    monkeypatch.setattr(
        "services.voice_service.predict_voice",
        lambda path: {
            "speaker": "unknown",
            "command": "unknown",
            "confidence": 30.0,
            "speaker_confidence": 20.0,
            "action": {},
            "message": "Rejected",
            "accepted": False,
            "rejected_reason": "low confidence",
        },
    )

    from services.voice_service import start_listening

    result = start_listening()
    assert result["executed"] is False
    assert "LIGHT_ON" not in mock_serial
    assert "MUSIC_ON" not in mock_serial
