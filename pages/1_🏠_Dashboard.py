import streamlit as st

from components.header import show_header
from components.card import device_card
from utils.state import initialize_state
from services.device_service import get_light_status, get_music_status

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

initialize_state()
show_header()
st.divider()

light = get_light_status()
music = get_music_status()
unlocked = st.session_state.authenticated

col1, col2, col3, col4 = st.columns(4)

with col1:
    device_card(
        "💡",
        "Lights",
        "ON" if light else "OFF",
        "#22C55E" if light else "#EF4444",
    )

with col2:
    device_card(
        "🎵",
        "Music",
        "ON" if music else "OFF",
        "#22C55E" if music else "#EF4444",
    )

with col3:
    device_card(
        "🔐",
        "Access",
        "Unlocked" if unlocked else "Locked",
        "#22C55E" if unlocked else "#EF4444",
    )

with col4:
    temp = st.session_state.temperature
    device_card(
        "🌡",
        "Temperature",
        f"{temp:.1f}°C" if temp is not None else "—",
        "#3B82F6",
    )

st.divider()

left, right = st.columns([2, 1])

with left:
    st.subheader("Recent Activity")
    st.info(
        f"User: {st.session_state.last_user}\n\n"
        f"Command: {st.session_state.last_command}\n\n"
        f"Confidence: {st.session_state.confidence:.2f}%"
    )

with right:
    st.subheader("System Status")
    st.write("Voice:", st.session_state.voice)
    st.write("AI:", st.session_state.ai)
    if unlocked:
        st.success("Control panel unlocked")
    else:
        st.warning("Authenticate on the Password page to control devices")
