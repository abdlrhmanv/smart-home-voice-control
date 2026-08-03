"""Streamlit-free application core (use-cases + ports).

Keep this module light: importing ``core.actions`` must not pull in
Streamlit, sounddevice, or the composition root (CI has no PortAudio).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.home import AuthError, HomeControlService
from core.models import AuthResult, VoiceResult

if TYPE_CHECKING:
    from core.container import AppContainer

__all__ = [
    "AppContainer",
    "AuthError",
    "AuthResult",
    "HomeControlService",
    "VoiceResult",
    "get_container",
    "reset_container",
]


def __getattr__(name: str):
    if name in {"AppContainer", "get_container", "reset_container"}:
        from core import container as _container

        return getattr(_container, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
