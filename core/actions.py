"""Canonical command → hardware/UI action catalog (single source of truth).

Ahmed's sketch (unchanged):
  LIGHT_*  → WHITE_LED on D12
  MUSIC_*  → GREEN_LED on D13
  PASSWORD_* → BUZZER on D11
"""

from __future__ import annotations

from typing import Any

COMMAND_ACTIONS: dict[str, dict[str, Any]] = {
    "light_on": {"arduino": "LIGHT_ON", "music": None, "led": True},
    "light_off": {"arduino": "LIGHT_OFF", "music": None, "led": False},
    "music_on": {"arduino": "MUSIC_ON", "music": "play", "led": True},
    "music_off": {"arduino": "MUSIC_OFF", "music": "stop", "led": False},
}

PASSWORD_OK_ACTION: dict[str, Any] = {"arduino": "PASSWORD_OK", "buzzer": True}
PASSWORD_FAIL_ACTION: dict[str, Any] = {"arduino": "PASSWORD_FAIL", "buzzer": False}


def map_command(command: str) -> dict[str, Any]:
    return COMMAND_ACTIONS.get(command, {}).copy()


def arduino_for(command: str) -> str | None:
    action = COMMAND_ACTIONS.get(command) or {}
    value = action.get("arduino")
    return str(value) if value else None


def known_commands() -> tuple[str, ...]:
    return tuple(COMMAND_ACTIONS.keys())
