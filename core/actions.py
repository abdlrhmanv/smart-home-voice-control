"""Canonical command → hardware/UI action catalog (single source of truth)."""

from __future__ import annotations

from typing import Any

# Rich payloads used by ML InferenceResult.action and by HomeControlService.
COMMAND_ACTIONS: dict[str, dict[str, Any]] = {
    "light_on": {"arduino": "LIGHT_ON", "music": None, "white_led": True},
    "light_off": {"arduino": "LIGHT_OFF", "music": None, "white_led": False},
    "music_on": {"arduino": "MUSIC_ON", "music": "play", "green_led": True},
    "music_off": {"arduino": "MUSIC_OFF", "music": "stop", "green_led": False},
}

PASSWORD_OK_ACTION: dict[str, Any] = {"arduino": "PASSWORD_OK", "red_led": True}
PASSWORD_FAIL_ACTION: dict[str, Any] = {"arduino": "PASSWORD_FAIL", "red_led": False}


def map_command(command: str) -> dict[str, Any]:
    return COMMAND_ACTIONS.get(command, {}).copy()


def arduino_for(command: str) -> str | None:
    action = COMMAND_ACTIONS.get(command) or {}
    value = action.get("arduino")
    return str(value) if value else None


def known_commands() -> tuple[str, ...]:
    return tuple(COMMAND_ACTIONS.keys())
