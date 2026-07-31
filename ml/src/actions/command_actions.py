"""Map predicted commands to Arduino / UI actions (separate from ML)."""

from __future__ import annotations

from typing import Any


class CommandActionMapper:
    """SRP: hardware/UI policy lives here, not inside classifiers."""

    DEFAULT_ACTIONS: dict[str, dict[str, Any]] = {
        "light_on": {"arduino": "LIGHT_ON", "music": None, "white_led": True},
        "light_off": {"arduino": "LIGHT_OFF", "music": None, "white_led": False},
        "music_on": {"arduino": "MUSIC_ON", "music": "play", "green_led": True},
        "music_off": {"arduino": "MUSIC_OFF", "music": "stop", "green_led": False},
    }

    def __init__(self, actions: dict[str, dict[str, Any]] | None = None) -> None:
        self._actions = actions or dict(self.DEFAULT_ACTIONS)

    def map(self, command: str) -> dict[str, Any]:
        return self._actions.get(command, {}).copy()

    def password_ok(self) -> dict[str, Any]:
        return {"arduino": "PASSWORD_OK", "red_led": True}

    def password_fail(self) -> dict[str, Any]:
        return {"arduino": "PASSWORD_FAIL", "red_led": False}
