import streamlit as st

from components.header import show_header
from utils.state import initialize_state
from services.password_service import authenticate
from services.device_service import lock_home

st.set_page_config(page_title="Password", page_icon="🔐", layout="wide")

initialize_state()
show_header()

st.title("Smart Home Authentication")
st.write(
    'Say the voice password ("open sesame"). '
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

if st.button("Record Password", use_container_width=True):
    with st.spinner("Listening..."):
        try:
            result = authenticate()
        except Exception as exc:
            st.error(f"Authentication failed: {exc}")
        else:
            if result.password_ok:
                st.success(result.message)
                st.session_state.authenticated = True
                if result.speaker:
                    st.session_state.last_user = result.speaker
                st.info("You can now use Voice Control and Devices.")
            else:
                st.error(result.message)
                st.session_state.authenticated = False
            st.write("**Transcript:**", result.transcript)
            if result.speaker is not None:
                conf = result.speaker_confidence
                conf_txt = f"{conf * 100:.1f}%" if conf is not None else "—"
                st.write(f"**Speaker:** {result.speaker} ({conf_txt})")
            if result.rejected_reason:
                st.caption(f"Reason: {result.rejected_reason}")
