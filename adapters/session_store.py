"""Streamlit-backed SessionStore adapter."""

from __future__ import annotations

import streamlit as st


class StreamlitSessionStore:
    """Reads/writes the shared Streamlit session schema."""

    def is_authenticated(self) -> bool:
        return bool(st.session_state.get("authenticated", False))

    def set_authenticated(self, value: bool) -> None:
        st.session_state.authenticated = value

    def get_arduino_synced(self) -> bool:
        return bool(st.session_state.get("arduino_synced", False))

    def set_arduino_synced(self, value: bool) -> None:
        st.session_state.arduino_synced = value

    def get_light(self) -> bool:
        return bool(st.session_state.get("light", False))

    def set_light(self, value: bool) -> None:
        st.session_state.light = value

    def get_music(self) -> bool:
        return bool(st.session_state.get("music", False))

    def set_music(self, value: bool) -> None:
        st.session_state.music = value

    def get_temperature(self) -> float | None:
        return st.session_state.get("temperature")

    def set_temperature(self, value: float | None, *, fresh: bool) -> None:
        if value is not None or fresh:
            st.session_state.temperature = value
        st.session_state.temperature_fresh = fresh

    def set_recognition(self, user: str, command: str, confidence: float) -> None:
        st.session_state.last_user = user
        st.session_state.last_command = command
        st.session_state.confidence = confidence
        st.session_state.recognition_result = {
            "user": user,
            "command": command,
            "confidence": confidence,
        }

    def get_last_user(self) -> str:
        return str(st.session_state.get("last_user", "Unknown"))

    def set_last_user(self, user: str) -> None:
        st.session_state.last_user = user

    def get_last_command(self) -> str:
        return str(st.session_state.get("last_command", "None"))

    def get_confidence(self) -> float:
        return float(st.session_state.get("confidence", 0.0) or 0.0)
