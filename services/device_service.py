"""Device control — session state + Arduino serial commands."""

from __future__ import annotations

import streamlit as st

from api.serial_service import request_temperature, send_command


def turn_light_on() -> None:
    st.session_state.light = True
    send_command("LIGHT_ON")


def turn_light_off() -> None:
    st.session_state.light = False
    send_command("LIGHT_OFF")


def turn_music_on() -> None:
    st.session_state.music = True
    send_command("MUSIC_ON")


def turn_music_off() -> None:
    st.session_state.music = False
    send_command("MUSIC_OFF")


def unlock_home() -> bool:
    """Signal password success to Arduino (red LED / unlock gate)."""
    st.session_state.authenticated = True
    return send_command("PASSWORD_OK")


def lock_home() -> bool:
    """Signal password failure / logout to Arduino."""
    st.session_state.authenticated = False
    st.session_state.light = False
    st.session_state.music = False
    return send_command("PASSWORD_FAIL")


def execute_command(command: str) -> None:
    """Dispatch a predicted command label to the matching device action."""
    actions = {
        "light_on": turn_light_on,
        "light_off": turn_light_off,
        "music_on": turn_music_on,
        "music_off": turn_music_off,
    }
    handler = actions.get(command)
    if handler is None:
        raise ValueError(f"Unknown command: {command}")
    handler()


def get_light_status() -> bool:
    return bool(st.session_state.get("light", False))


def get_music_status() -> bool:
    return bool(st.session_state.get("music", False))


def get_temperature() -> float | None:
    """Request live temperature from Arduino; cache last good reading."""
    temp = request_temperature()
    if temp is not None:
        st.session_state.temperature = temp
    return st.session_state.get("temperature")
