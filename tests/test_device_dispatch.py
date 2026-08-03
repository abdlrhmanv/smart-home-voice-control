"""Command dispatch validation."""

from __future__ import annotations

import pytest

from core.home import AuthError, HomeControlService
from core.memory_store import InMemorySessionStore


class FakeSerial:
    def send_command(self, command: str) -> bool:
        return True

    def request_temperature(self, timeout_s: float = 2.0):
        return None

    def connect(self, port=None):
        return True

    def disconnect(self):
        return None

    def is_connected(self):
        return True

    def resolve_port(self):
        return None


class FakeMusic:
    def start(self) -> bool:
        return True

    def stop(self) -> None:
        return None


def test_unknown_command_raises():
    store = InMemorySessionStore()
    store.authenticated = True
    home = HomeControlService(store, FakeSerial(), FakeMusic())
    with pytest.raises(ValueError, match="Unknown command"):
        home.execute_command("fly_away")


def test_execute_command_requires_auth():
    home = HomeControlService(InMemorySessionStore(), FakeSerial(), FakeMusic())
    with pytest.raises(AuthError):
        home.execute_command("light_on")
