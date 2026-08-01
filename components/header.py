import streamlit as st
from pathlib import Path


def load_css():
    css_file = Path("assets/style.css")

    with open(css_file) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


def show_header():

    load_css()

    col1, col2 = st.columns([6, 1])

    with col1:
        st.title("🏠 Smart Home Dashboard")
        st.caption("Voice Controlled Smart Home System")

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.success("🟢 Online")