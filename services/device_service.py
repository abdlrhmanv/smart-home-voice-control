import streamlit as st
from api.serial_service import send_command


# ==========================
# Lights
# ==========================

def turn_light_on():
    st.session_state.light = True
    send_command("LIGHT_ON")


def turn_light_off():
    st.session_state.light = False
    send_command("LIGHT_OFF")


# ==========================
# Music
# ==========================

def turn_music_on():
    st.session_state.music = True
    send_command("MUSIC_ON")


def turn_music_off():
    st.session_state.music = False
    send_command("MUSIC_OFF")


# ==========================
# Status
# ==========================

def get_light_status():
    return st.session_state.light


def get_music_status():
    return st.session_state.music