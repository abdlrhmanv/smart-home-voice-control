"""
Minimal Streamlit integration example.

    streamlit run examples/streamlit_hook_example.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from src.application import SmartHomePipeline  # noqa: E402
from src.infrastructure.whisper import FasterWhisperTranscriber  # noqa: E402

st.set_page_config(page_title="Smart Home AI Hook", page_icon="🏠")
st.title("Smart Home — ML Integration Hook")
st.caption("Example only. Replace with the real Streamlit app.")

tab_pw, tab_cmd = st.tabs(["Password (STT)", "Speaker + Command"])

with tab_pw:
    st.subheader("Voice password")
    pw_file = st.file_uploader("Upload password WAV", type=["wav"], key="pw")
    if pw_file is not None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(pw_file.read())
            tmp_path = tmp.name
        stt = FasterWhisperTranscriber()
        ok, text = stt.check_password(tmp_path, expected="open sesame")
        st.write(f"Heard: `{text}`")
        st.success("Password OK") if ok else st.error("Wrong password")

with tab_cmd:
    st.subheader("Identify speaker & command")
    st.info("Requires trained `models/speaker.pkl` and `models/command.pkl`.")
    cmd_file = st.file_uploader("Upload command WAV", type=["wav"], key="cmd")
    if cmd_file is not None and st.button("Run models"):
        pipe = SmartHomePipeline.create_default()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(cmd_file.read())
            tmp_path = tmp.name
        result = pipe.predict_voice_command(tmp_path)
        st.json(result.to_dict())
