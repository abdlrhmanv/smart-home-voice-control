import streamlit as st

from components.header import show_header
from utils.state import initialize_state

st.set_page_config(page_title="Smart Home AI", page_icon="🏠", layout="wide")

initialize_state()
show_header()

st.title("Smart Home AI")
st.write(
    "Voice-controlled smart home: password unlock → speaker ID → "
    "command classification → Arduino actuation."
)

st.divider()

st.markdown(
    """
### Workflow
1. **Password** — say `open sesame` (Whisper STT). Red LED unlocks the Arduino gate.
2. **Voice Control** — say `light on/off` or `music on/off`.
3. **Devices** — manual toggles and temperature readout.
4. **Activity Log** — session history of recognized commands.
5. **Settings** — serial port connection.
"""
)

col1, col2, col3 = st.columns(3)
col1.metric("Access", "Unlocked" if st.session_state.authenticated else "Locked")
col2.metric("Light", "ON" if st.session_state.light else "OFF")
col3.metric("Music", "ON" if st.session_state.music else "OFF")
