import streamlit as st

from utils.env_loader import load_dotenv

# Must run before serial/ML config is read.
load_dotenv(".env")

from components.header import show_header
from utils.state import initialize_state
from ai.predict import get_pipeline

st.set_page_config(page_title="Smart Home AI", page_icon="🏠", layout="wide")

initialize_state()
show_header()

# Warm SVM load (and register Streamlit cache). Whisper stays lazy until password.
with st.spinner("Loading AI models…"):
    get_pipeline()

st.title("Smart Home AI")
st.write(
    "Voice-controlled smart home: password unlock → speaker ID → "
    "command classification → Arduino actuation."
)

st.divider()

st.markdown(
    """
### Workflow
1. **Settings** — Connect Arduino (set `ARDUINO_PORT`, click **Test PASSWORD_OK**).
2. **Password** — say `open` (Whisper STT + enrolled speaker). Buzzer beeps on unlock.
3. **Voice Control** — say `light on/off` or `music on/off`.
4. **Devices** — manual toggles and temperature readout.
5. **Activity Log** — persisted history of recognized commands.
"""
)

col1, col2, col3 = st.columns(3)
col1.metric("Access", "Unlocked" if st.session_state.authenticated else "Locked")
col2.metric("Light", "ON" if st.session_state.light else "OFF")
col3.metric("Music", "ON" if st.session_state.music else "OFF")
