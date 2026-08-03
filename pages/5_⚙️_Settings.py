import os

import streamlit as st

from components.header import show_header
from utils.state import initialize_state
from api.serial_service import BAUD_RATE, connect, disconnect, is_connected, resolve_port

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

initialize_state()
show_header()

st.title("Settings")
st.write("Serial port and session options.")
st.divider()

st.subheader("Arduino serial")
detected = resolve_port()
st.write(f"Detected / configured port: `{detected or 'none'}`")
st.write(f"Baud rate: `{BAUD_RATE}`")
st.caption("Override with environment variable `ARDUINO_PORT` (e.g. `/dev/ttyUSB0` or `COM11`).")

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Connect", use_container_width=True):
        ok = connect()
        st.success("Connected") if ok else st.error("Connection failed")
with c2:
    if st.button("Disconnect", use_container_width=True):
        disconnect()
        st.info("Disconnected")
with c3:
    st.metric("Link", "Online" if is_connected() else "Offline")

st.divider()
st.subheader("Inference thresholds")
st.write(
    "Low-confidence predictions are rejected (`unknown`) and not sent to Arduino. "
    "Configure in `ml/src/config.py` → `InferenceConfig.min_command_confidence` "
    f"/ `min_speaker_confidence`."
)

st.divider()
st.subheader("LED wiring")
st.markdown(
    """
| LED | Pin | Role |
|-----|-----|------|
| Red | D11 | Password unlock |
| Green | D12 | Music |
| White | D10 | Light (optional on 2-LED boards) |
| Buzzer | D13 | Beeps |

If you only wired red + green, leave D10 empty — `LIGHT_ON`/`OFF` still send, but no white LED will light.
"""
)

st.divider()
st.subheader("Session")
st.write("Authenticated:", st.session_state.authenticated)
st.write("Password phrase is configured in `ml/src/config.py` (`InferenceConfig.password`).")
st.write("Whisper model:", os.environ.get("WHISPER_SIZE", "base (default)"))
