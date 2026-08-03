"""Auth façade — delegates to the wired HomeControlService."""

from __future__ import annotations

from core.container import get_home
from core.home import AuthError

__all__ = ["AuthError", "is_authenticated", "require_authenticated"]


def is_authenticated() -> bool:
    return get_home().store.is_authenticated()


def require_authenticated() -> None:
    get_home().require_auth()
