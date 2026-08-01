import streamlit as st


def show_sidebar():

    with st.sidebar:

        st.image(
            "https://img.icons8.com/fluency/96/home.png",
            width=70
        )

        st.title("Smart Home")

        st.markdown("---")

        st.page_link(
            "app.py",
            label="Dashboard",
            icon="🏠"
        )

        st.page_link(
            "pages/Voice_Control.py",
            label="Voice Control",
            icon="🎤"
        )

        st.page_link(
            "pages/Devices.py",
            label="Devices",
            icon="💡"
        )

        st.page_link(
            "pages/Activity_Log.py",
            label="Activity Log",
            icon="📜"
        )

        st.page_link(
            "pages/Settings.py",
            label="Settings",
            icon="⚙️"
        )

        st.markdown("---")

        st.success("System Online")