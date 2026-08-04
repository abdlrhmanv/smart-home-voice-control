"""Home control use-case tests (no Streamlit)."""

from __future__ import annotations

import pytest

from core.home import AuthError, HomeControlService
from core.memory_store import InMemorySessionStore


class FakeSerial:
    def __init__(self, *, ok: bool = True, temperature: float | None = 24.0):
        self.ok = ok
        self.temperature = temperature
        self.sent: list[str] = []

    def send_command(self, command: str) -> bool:
        self.sent.append(command)
        return self.ok

    def request_temperature(self, timeout_s: float = 2.0) -> float | None:
        return self.temperature if self.ok else None

    def connect(self, port=None):
        return self.ok

    def disconnect(self):
        return None

    def is_connected(self):
        return self.ok

    def resolve_port(self):
        return "/dev/ttyUSB0" if self.ok else None


class FakeMusic:
    def __init__(self):
        self.started = 0
        self.stopped = 0

    def start(self) -> bool:
        self.started += 1
        return True

    def stop(self) -> None:
        self.stopped += 1


@pytest.fixture
def home():
    store = InMemorySessionStore()
    store.authenticated = True
    serial = FakeSerial()
    music = FakeMusic()
    svc = HomeControlService(store, serial, music, allow_offline=True)
    return svc, store, serial, music


def test_device_requires_auth():
    store = InMemorySessionStore()
    serial = FakeSerial()
    svc = HomeControlService(store, serial, FakeMusic(), allow_offline=True)
    with pytest.raises(AuthError):
        svc.turn_light_on()
    assert serial.sent == []


def test_device_state_not_updated_when_serial_fails():
    store = InMemorySessionStore()
    store.authenticated = True
    serial = FakeSerial(ok=False)
    svc = HomeControlService(store, serial, FakeMusic(), allow_offline=False)
    assert svc.turn_light_on() is False
    assert store.light is False
    assert "LIGHT_ON" in serial.sent


def test_unlock_sets_arduino_synced():
    store = InMemorySessionStore()
    serial = FakeSerial(ok=True)
    svc = HomeControlService(store, serial, FakeMusic(), allow_offline=True)
    assert svc.unlock() is True
    assert store.authenticated is True
    assert store.arduino_synced is True
    assert "PASSWORD_OK" in serial.sent


def test_get_temperature_does_not_return_stale_as_fresh(home):
    svc, store, serial, _ = home
    store.temperature = 22.5
    serial.temperature = None
    assert svc.get_temperature() is None
    assert svc.get_temperature(use_cache_on_failure=True) == 22.5


def test_music_on_starts_laptop_player(home):
    svc, store, serial, music = home
    assert svc.turn_music_on() is True
    assert music.started == 1
    assert store.music is True
    assert svc.turn_music_off() is True
    assert music.stopped == 1
