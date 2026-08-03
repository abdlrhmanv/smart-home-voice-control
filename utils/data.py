"""Recognition-result helpers (delegate to the session store)."""

from __future__ import annotations

from core.container import get_container


def set_recognition_result(user, command, confidence):
    get_container().store.set_recognition(user, command, confidence)


def get_recognition_result():
    store = get_container().store
    return {
        "user": store.get_last_user(),
        "command": store.get_last_command(),
        "confidence": store.get_confidence(),
    }
