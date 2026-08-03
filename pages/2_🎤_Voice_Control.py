import streamlit as st

from components.header import show_header
from utils.state import append_activity, initialize_state, require_auth
from services.voice_service import start_listening

st.set_page_config(page_title="Voice Control", page_icon="🎤", layout="wide")

initialize_state()
require_auth()
show_header()

st.title("Voice Assistant")
st.write("Say one of: light on, light off, music on, music off.")
st.divider()

if st.button("Start Listening", use_container_width=True):
    st.session_state.voice = "Listening"
    with st.spinner("Listening..."):
        try:
            result = start_listening()
        except Exception as exc:
            st.session_state.voice = "Error"
            st.session_state.ai = "Error"
            st.error(f"Voice processing failed: {exc}")
        else:
            st.session_state.voice = "Idle"
            st.session_state.ai = "Ready"
            append_activity(
                result["speaker"],
                result["command"],
                result["confidence"],
                executed=bool(result.get("executed", False)),
            )
            if result.get("executed", True):
                st.success(result.get("message") or "Voice processed successfully.")
            else:
                reason = result.get("rejected_reason") or result.get("message")
                st.warning(
                    reason
                    or "Command/speaker rejected (low confidence or unknown)."
                )

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.metric("Speaker", st.session_state.last_user)
    st.metric("Command", st.session_state.last_command)
with col2:
    st.metric("Confidence", f"{st.session_state.confidence:.2f}%")
    st.metric("Status", st.session_state.voice)

st.divider()
st.subheader("Last Action")
st.info(f"Last command: {st.session_state.last_command}")
