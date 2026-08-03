"""Device control façade — pages keep importing from here."""

from __future__ import annotations

import os

from core.container import get_container, get_home, set_container, build_container
from core.home import AuthError

# Re-export for older tests / callers
ALLOW_OFFLINE_CONTROL = os.environ.get("ALLOW_OFFLINE_CONTROL", "1") == "1"

__all__ = [
    "ALLOW_OFFLINE_CONTROL",
    "AuthError",
    "execute_command",
    "get_light_status",
    "get_music_status",
    "get_temperature",
    "lock_home",
    "set_serial_bridge",
    "turn_light_off",
    "turn_light_on",
    "turn_music_off",
    "turn_music_on",
    "unlock_home",
]


def set_serial_bridge(bridge) -> None:
    """Inject a serial client for tests (rebuilds the process container)."""
    from adapters.music import _default_player
    from adapters.session_store import StreamlitSessionStore
    from core.memory_store import InMemorySessionStore

    # Prefer keeping the current store type when possible.
    current = None
    try:
        current = get_container().store
    except Exception:
        current = None
    store = current if current is not None else StreamlitSessionStore()
    # If tests already patched Streamlit away, fall back to memory store.
    try:
        store.is_authenticated()
    except Exception:
        store = InMemorySessionStore()

    set_container(
        build_container(
            store=store,
            serial=bridge,
            music=_default_player,
            allow_offline=ALLOW_OFFLINE_CONTROL,
        )
    )


def turn_light_on() -> bool:
    return get_home().turn_light_on()


def turn_light_off() -> bool:
    return get_home().turn_light_off()


def turn_music_on() -> bool:
    return get_home().turn_music_on()


def turn_music_off() -> bool:
    return get_home().turn_music_off()


def unlock_home() -> bool:
    return get_home().unlock()


def lock_home() -> bool:
    return get_home().lock()


def execute_command(command: str) -> bool:
    return get_home().execute_command(command)


def get_light_status() -> bool:
    return get_home().get_light()


def get_music_status() -> bool:
    return get_home().get_music()


def get_temperature(*, use_cache_on_failure: bool = False) -> float | None:
    return get_home().get_temperature(use_cache_on_failure=use_cache_on_failure)
