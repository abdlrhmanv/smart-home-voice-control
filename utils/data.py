import streamlit as st


def set_recognition_result(user, command, confidence):
    """
    Save recognition result in Session State.
    """

    st.session_state.last_user = user
    st.session_state.last_command = command
    st.session_state.confidence = confidence

    st.session_state.recognition_result = {
        "user": user,
        "command": command,
        "confidence": confidence
    }


def get_recognition_result():
    """
    Return last recognition result.
    """

    return {
        "user": st.session_state.last_user,
        "command": st.session_state.last_command,
        "confidence": st.session_state.confidence
    }