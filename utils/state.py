import streamlit as st


def initialize_state() -> None:
    defaults = {
        "light": False,
        "music": False,
        "voice": "Idle",
        "ai": "Ready",
        "last_command": "None",
        "last_user": "Unknown",
        "confidence": 0.0,
        "authenticated": False,
        "temperature": None,
        "activity_log": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Hydrate session log from disk once per session.
    if not st.session_state.activity_log:
        from utils.activity_store import load_activity_log

        st.session_state.activity_log = load_activity_log(limit=50)


def require_auth() -> bool:
    """Return True if unlocked; otherwise show a blocking warning."""
    initialize_state()
    if st.session_state.authenticated:
        return True
    st.warning("Home is locked. Authenticate on the Password page first.")
    st.stop()
    return False


def append_activity(
    user: str,
    command: str,
    confidence: float,
    *,
    executed: bool = True,
) -> None:
    initialize_state()
    from utils.activity_store import append_activity_entry

    entry = append_activity_entry(
        user, command, confidence, executed=executed
    )
    log = list(st.session_state.activity_log)
    log.insert(0, entry)
    st.session_state.activity_log = log[:50]
