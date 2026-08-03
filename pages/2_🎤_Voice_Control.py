import streamlit as st

from components.header import show_header
from services.voice_service import start_listening
from utils.state import append_activity, initialize_state, require_auth
from utils.uploads import save_audio_upload, save_uploaded_wav

st.set_page_config(page_title="Voice Control", page_icon="🎤", layout="wide")

initialize_state()
require_auth()
show_header()

st.title("Voice Assistant")
st.write("Say one of: light on, light off, music on, music off.")
st.divider()


def _handle_voice_result(result: dict) -> None:
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
            reason or "Command/speaker rejected (low confidence or unknown)."
        )


st.subheader("Record in browser (recommended)")
st.caption("Browser mic — no PortAudio required on the server.")
audio = st.audio_input("Record command", key="command_audio_input")
if audio is not None and st.button(
    "Run browser recording", use_container_width=True, type="primary"
):
    st.session_state.voice = "Listening"
    with st.spinner("Processing..."):
        try:
            path = save_audio_upload(audio)
            result = start_listening(audio_path=path)
        except Exception as exc:
            st.session_state.voice = "Error"
            st.session_state.ai = "Error"
            st.error(f"Voice processing failed: {exc}")
        else:
            _handle_voice_result(result)

st.divider()
st.subheader("Or upload a WAV")
uploaded = st.file_uploader(
    "Command WAV",
    type=["wav"],
    key="command_wav_upload",
)
if uploaded is not None and st.button("Run uploaded command", use_container_width=True):
    st.session_state.voice = "Listening"
    with st.spinner("Processing..."):
        try:
            path = save_uploaded_wav(uploaded)
            result = start_listening(audio_path=path)
        except Exception as exc:
            st.session_state.voice = "Error"
            st.session_state.ai = "Error"
            st.error(f"Voice processing failed: {exc}")
        else:
            _handle_voice_result(result)

with st.expander("Advanced: server microphone (local only)"):
    if st.button("Start Listening (server mic)", use_container_width=True):
        st.session_state.voice = "Listening"
        with st.spinner("Listening..."):
            try:
                result = start_listening()
            except Exception as exc:
                st.session_state.voice = "Error"
                st.session_state.ai = "Error"
                st.error(f"Voice processing failed: {exc}")
            else:
                _handle_voice_result(result)

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Speaker", st.session_state.last_user)
    st.metric("Command", st.session_state.last_command)
with col2:
    st.metric("Confidence", f"{st.session_state.confidence:.2f}%")
    st.metric("Status", st.session_state.voice)
with col3:
    from pathlib import Path

    speaker = str(st.session_state.last_user or "")
    avatar = Path("assets/speakers") / f"{speaker}.png"
    if avatar.is_file():
        st.image(str(avatar), caption=speaker, width=120)
    else:
        st.caption(f"No photo for '{speaker}'. Add assets/speakers/{speaker}.png")

st.divider()
st.subheader("Last Action")
st.info(f"Last command: {st.session_state.last_command}")
