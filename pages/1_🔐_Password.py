import streamlit as st

from components.header import show_header
from utils.state import initialize_state
from services.password_service import authenticate
from services.device_service import lock_home

st.set_page_config(page_title="Password", page_icon="🔐", layout="wide")

initialize_state()
show_header()

st.title("Smart Home Authentication")
st.write('Say the voice password ("open sesame") to unlock the control panel.')
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
                st.info("You can now use Voice Control and Devices.")
            else:
                st.error(result.message)
                st.session_state.authenticated = False
            st.write("**Transcript:**", result.transcript)
