import streamlit as st

from components.header import show_header
from services.device_service import lock_home
from services.password_service import authenticate
from utils.state import initialize_state
from utils.uploads import save_audio_upload, save_uploaded_wav

st.set_page_config(page_title="Password", page_icon="🔐", layout="wide")

initialize_state()
show_header()

st.title("Smart Home Authentication")
st.write(
    'Say the voice password ("open"). '
    "An enrolled speaker voice is also required to unlock."
)
st.divider()

col_a, col_b = st.columns(2)
with col_a:
    st.metric("Status", "Unlocked" if st.session_state.authenticated else "Locked")
with col_b:
    if st.session_state.authenticated and st.button("Lock home", use_container_width=True):
        lock_home()
        st.rerun()


def _show_auth_result(result) -> None:
    unlocked = getattr(result, "unlocked", st.session_state.get("authenticated"))
    synced = getattr(result, "arduino_synced", st.session_state.get("arduino_synced"))
    if result.password_ok and unlocked:
        st.success(result.message)
        st.info("You can now use Voice Control and Devices.")
        if not synced:
            st.warning(
                "Password accepted in software, but Arduino did not receive "
                "PASSWORD_OK (check USB / ARDUINO_PORT). Offline demo mode is on."
            )
    elif result.password_ok and not unlocked:
        st.error(
            "Password matched, but the home stayed locked because the Arduino "
            "link failed and offline control is disabled."
        )
    else:
        st.error(result.message)
    st.write("**Transcript:**", result.transcript)
    if result.speaker is not None:
        conf = result.speaker_confidence
        conf_txt = f"{conf * 100:.1f}%" if conf is not None else "—"
        st.write(f"**Speaker:** {result.speaker} ({conf_txt})")
    if result.rejected_reason:
        st.caption(f"Reason: {result.rejected_reason}")


st.subheader("Record in browser (recommended)")
st.caption(
    "Uses your browser microphone — works on Streamlit Cloud without PortAudio."
)
audio = st.audio_input("Record password", key="password_audio_input")
if audio is not None and st.button(
    "Verify browser recording", use_container_width=True, type="primary"
):
    with st.spinner("Verifying..."):
        try:
            path = save_audio_upload(audio)
            result = authenticate(audio_path=path)
        except Exception as exc:
            st.error(f"Authentication failed: {exc}")
        else:
            _show_auth_result(result)

st.divider()
st.subheader("Or upload a WAV")
uploaded = st.file_uploader(
    "Password WAV",
    type=["wav"],
    key="password_wav_upload",
)
if uploaded is not None and st.button("Verify uploaded password", use_container_width=True):
    with st.spinner("Verifying..."):
        try:
            path = save_uploaded_wav(uploaded)
            result = authenticate(audio_path=path)
        except Exception as exc:
            st.error(f"Authentication failed: {exc}")
        else:
            _show_auth_result(result)

with st.expander("Advanced: server microphone (local only)"):
    st.caption("Needs PortAudio on the machine running Streamlit (`libportaudio2`).")
    if st.button("Record via server mic", use_container_width=True):
        with st.spinner("Listening..."):
            try:
                result = authenticate()
            except Exception as exc:
                st.error(f"Authentication failed: {exc}")
            else:
                _show_auth_result(result)
