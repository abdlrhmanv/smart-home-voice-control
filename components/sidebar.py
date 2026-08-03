"""Optional custom sidebar (Streamlit multipage nav is used by default)."""

from __future__ import annotations

import streamlit as st


def show_sidebar() -> None:
    with st.sidebar:
        st.title("Smart Home")
        st.markdown("---")
        st.page_link("app.py", label="Home", icon="🏠")
        st.page_link("pages/1_🔐_Password.py", label="Password", icon="🔐")
        st.page_link("pages/2_🎤_Voice_Control.py", label="Voice Control", icon="🎤")
        st.page_link("pages/3_💡_Devices.py", label="Devices", icon="💡")
        st.page_link("pages/4_📜_Activity_Log.py", label="Activity Log", icon="📜")
        st.page_link("pages/5_⚙️_Settings.py", label="Settings", icon="⚙️")
        st.markdown("---")
        unlocked = bool(st.session_state.get("authenticated", False))
        if unlocked:
            st.success("Unlocked")
        else:
            st.warning("Locked")
