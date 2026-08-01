import streamlit as st


def initialize_state():

    if "light" not in st.session_state:
        st.session_state.light = False

    if "music" not in st.session_state:
        st.session_state.music = False

    if "voice" not in st.session_state:
        st.session_state.voice = "Idle"

    if "ai" not in st.session_state:
        st.session_state.ai = "Ready"

    if "last_command" not in st.session_state:
        st.session_state.last_command = "None"

    if "last_user" not in st.session_state:
        st.session_state.last_user = "Unknown"

    if "confidence" not in st.session_state:
        st.session_state.confidence = 0.0