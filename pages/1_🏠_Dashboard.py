import streamlit as st

from components.header import show_header
from components.card import device_card

from utils.state import initialize_state

from services.device_service import (
    get_light_status,
    get_music_status
)

st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

initialize_state()

show_header()

st.divider()

# ==========================
# Read Device Status
# ==========================

light = get_light_status()
music = get_music_status()

# ==========================
# Cards
# ==========================

col1, col2, col3, col4 = st.columns(4)

with col1:

    device_card(
        "💡",
        "Lights",
        "ON" if light else "OFF",
        "#22C55E" if light else "#EF4444"
    )

with col2:

    device_card(
        "🎵",
        "Music",
        "ON" if music else "OFF",
        "#22C55E" if music else "#EF4444"
    )

with col3:

    device_card(
        "🎤",
        "Voice",
        st.session_state.voice,
        "#3B82F6"
    )

with col4:

    device_card(
        "🤖",
        "AI",
        st.session_state.ai,
        "#3B82F6"
    )

st.divider()

left, right = st.columns([2, 1])

with left:

    st.subheader("📋 Recent Activity")

    st.info(
        f"""
👤 User : {st.session_state.last_user}

🎯 Command : {st.session_state.last_command}
"""
    )

with right:

    st.subheader("📊 System Status")

    st.progress(100)

    st.success("All Systems Running")