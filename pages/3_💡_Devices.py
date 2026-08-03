import streamlit as st

from components.header import show_header
from utils.state import initialize_state, require_auth
from services.device_service import (
    get_light_status,
    get_music_status,
    get_temperature,
    turn_light_off,
    turn_light_on,
    turn_music_off,
    turn_music_on,
)

st.set_page_config(page_title="Devices", page_icon="💡", layout="wide")

initialize_state()
require_auth()
show_header()

st.title("Devices")
st.write("Manual control and temperature monitoring.")
st.divider()

light = get_light_status()
music = get_music_status()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Light (white LED)")
    st.write("Status:", "ON" if light else "OFF")
    c1, c2 = st.columns(2)
    if c1.button("Light ON", use_container_width=True):
        turn_light_on()
        st.rerun()
    if c2.button("Light OFF", use_container_width=True):
        turn_light_off()
        st.rerun()

with col2:
    st.subheader("Music (green LED + laptop audio)")
    st.write("Status:", "ON" if music else "OFF")
    st.caption("MUSIC_ON plays a loop on the laptop and lights the green LED.")
    c1, c2 = st.columns(2)
    if c1.button("Music ON", use_container_width=True):
        if not turn_music_on():
            st.error("Could not start music (serial failed and offline mode off).")
        st.rerun()
    if c2.button("Music OFF", use_container_width=True):
        turn_music_off()
        st.rerun()

with col3:
    st.subheader("Temperature")
    if st.button("Read temperature", use_container_width=True):
        with st.spinner("Requesting from Arduino..."):
            temp = get_temperature()
        if temp is None:
            st.error(
                "No fresh reading. Check the USB cable and ARDUINO_PORT, "
                "and unlock with PASSWORD_OK first."
            )
            if st.session_state.temperature is not None:
                st.caption(
                    f"Last successful reading was "
                    f"{st.session_state.temperature:.2f} °C (not refreshed)."
                )
        else:
            st.success(f"{temp:.2f} °C")
    elif st.session_state.temperature is not None:
        st.metric("Last reading", f"{st.session_state.temperature:.2f} °C")
    else:
        st.caption("No temperature reading yet.")
