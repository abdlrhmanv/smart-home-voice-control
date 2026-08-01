import streamlit as st

from components.header import show_header
from utils.state import initialize_state
from services.password_service import authenticate

st.set_page_config(
    page_title="Password",
    page_icon="🔐",
    layout="wide"
)

initialize_state()

show_header()

st.title("🔐 Smart Home Authentication")

st.write("Please say the password to unlock the Smart Home.")

st.divider()

if st.button(
    "🎙 Record Password",
    use_container_width=True
):

    with st.spinner("Listening..."):

        result = authenticate()

    if result.password_ok:

        st.success(result.message)

        st.session_state.authenticated = True

    else:

        st.error(result.message)

        st.session_state.authenticated = False

    st.write("**Transcript:**", result.transcript)