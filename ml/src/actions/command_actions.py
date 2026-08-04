"""Map predicted commands to Arduino / UI actions (separate from ML).

Canonical catalog lives in ``core.actions`` so the Streamlit app and the ML
package share one source of truth.
"""

from __future__ import annotations

from typing import Any

try:
    from core.actions import (
        COMMAND_ACTIONS,
        PASSWORD_FAIL_ACTION,
        PASSWORD_OK_ACTION,
    )
except ImportError:  # pragma: no cover - ml-only PYTHONPATH
    # Keep in sync with core.actions (Ahmed sketch token names).
    COMMAND_ACTIONS = {
        "light_on": {"arduino": "LIGHT_ON", "music": None, "led": True},
        "light_off": {"arduino": "LIGHT_OFF", "music": None, "led": False},
        "music_on": {"arduino": "MUSIC_ON", "music": "play", "led": True},
        "music_off": {"arduino": "MUSIC_OFF", "music": "stop", "led": False},
    }
    PASSWORD_OK_ACTION = {"arduino": "PASSWORD_OK", "buzzer": True}
    PASSWORD_FAIL_ACTION = {"arduino": "PASSWORD_FAIL", "buzzer": False}


class CommandActionMapper:
    """SRP: hardware/UI policy lives here, not inside classifiers."""

    DEFAULT_ACTIONS: dict[str, dict[str, Any]] = dict(COMMAND_ACTIONS)

    def __init__(self, actions: dict[str, dict[str, Any]] | None = None) -> None:
        self._actions = actions or dict(self.DEFAULT_ACTIONS)

    def map(self, command: str) -> dict[str, Any]:
        return self._actions.get(command, {}).copy()

    def password_ok(self) -> dict[str, Any]:
        return dict(PASSWORD_OK_ACTION)

    def password_fail(self) -> dict[str, Any]:
        return dict(PASSWORD_FAIL_ACTION)
