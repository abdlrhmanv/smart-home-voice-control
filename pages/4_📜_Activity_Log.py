import streamlit as st

from components.header import show_header
from utils.state import initialize_state, require_auth
from utils.activity_store import clear_activity_log

st.set_page_config(page_title="Activity Log", page_icon="📜", layout="wide")

initialize_state()
require_auth()
show_header()

st.title("Activity Log")
st.write("Recent voice commands (persisted under `data/activity_log.jsonl`).")
st.divider()

log = st.session_state.activity_log
if not log:
    st.info("No activity yet. Use Voice Control to issue a command.")
else:
    st.dataframe(
        [
            {
                "Time (UTC)": e.get("ts", "—"),
                "Speaker": e.get("user", "—"),
                "Command": e.get("command", "—"),
                "Confidence %": e.get("confidence", 0),
                "Executed": e.get("executed", True),
            }
            for e in log
        ],
        use_container_width=True,
        hide_index=True,
    )

if st.button("Clear log"):
    clear_activity_log()
    st.session_state.activity_log = []
    st.rerun()
