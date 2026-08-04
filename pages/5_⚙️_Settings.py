import streamlit as st

from components.header import show_header
from services import settings_service
from utils.calibration_store import reports_dir
from utils.state import initialize_state

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

initialize_state()
show_header()

st.title("Settings")
st.write("Serial port, inference config, and model calibration.")
st.divider()

st.subheader("Arduino serial (Ahmed sketch — unchanged)")
st.caption(
    "Buzzer D11 · Light/WHITE D12 (`LIGHT_*`) · Music/GREEN D13 (`MUSIC_*`) · "
    "Temp A0 (`SEND_TEMP`) · 9600 baud. Re-flash after pulling `typo_fix`."
)
status = settings_service.serial_status()
st.write(f"Resolved port: `{status.port or 'none'}`")
st.write(f"Baud rate: `{status.baud_rate}`")
if status.candidates:
    st.write("Candidates:", ", ".join(f"`{p}`" for p in status.candidates))
else:
    st.write("Candidates: none — plug Arduino USB and/or set `ARDUINO_PORT`.")
if status.last_error:
    st.error(status.last_error)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("Connect", use_container_width=True):
        ok = settings_service.connect_serial()
        st.success("Connected") if ok else st.error("Connection failed")
with c2:
    if st.button("Disconnect", use_container_width=True):
        settings_service.disconnect_serial()
        st.info("Disconnected")
with c3:
    if st.button("Test PASSWORD_OK", use_container_width=True):
        with st.spinner("Sending PASSWORD_OK (buzzer ~4.5s)…"):
            ok = settings_service.send_test_password_ok()
        if ok:
            st.success("Sent. Buzzer should beep 3 times.")
        else:
            st.error(status.last_error or "Send failed — set ARDUINO_PORT and reconnect.")
with c4:
    st.metric("Link", "Online" if status.connected else "Offline")

st.caption(
    "Local tip: `export ARDUINO_PORT=/dev/ttyACM0` (or ttyUSB0), then restart Streamlit. "
    "User must be in the `dialout` group on Linux."
)

st.divider()
st.subheader("Inference thresholds")
st.write(
    "Low-confidence predictions are rejected (`unknown`) and not sent to Arduino. "
    "Password requires Whisper phrase match **and** an enrolled speaker. "
    "Configure via `.env` / `InferenceConfig`."
)
summary = settings_service.inference_summary()
st.write(
    f"Whisper: `{summary.whisper_size}` on `{summary.device}` · "
    f"require_known_speaker={summary.require_known_speaker} · "
    f"min_command_confidence={summary.min_command_confidence}"
)
if summary.note:
    st.caption(f"(config load note: {summary.note})")

st.divider()
st.subheader("Calibration monitor")
st.caption(
    "Shows the latest `ml/reports/calibration_*.json` from "
    "`python ml/report_calibration.py`."
)

task = st.selectbox("Task", ["command", "speaker"], index=0)
report = settings_service.load_calibration(task)

col_r1, col_r2 = st.columns([1, 1])
with col_r1:
    if st.button("Refresh calibration report", use_container_width=True):
        with st.spinner(f"Evaluating {task} model…"):
            ok, message = settings_service.refresh_calibration(task)
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)
with col_r2:
    st.write(f"Reports dir: `{reports_dir()}`")

if report is None:
    st.info("No report yet. Click **Refresh calibration report**.")
else:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("F1 macro", f"{report.get('f1_macro', 0):.3f}")
    m2.metric("Accuracy", f"{report.get('accuracy', 0):.3f}")
    m3.metric("Brier", f"{report.get('brier_correct_vs_conf', 0):.3f}")
    m4.metric("Mean conf", f"{report.get('mean_confidence', 0):.3f}")
    st.caption(report.get("note", ""))
    st.caption(f"Generated: {report.get('generated_at', '—')}")
    points = report.get("reliability") or []
    if points:
        st.write("Reliability curve points (predicted confidence → fraction correct)")
        st.dataframe(points, use_container_width=True, hide_index=True)

st.divider()
st.subheader("LED / buzzer wiring (Ahmed `.ino`)")
st.markdown(
    """
| Device | Pin | Sketch command |
|--------|-----|----------------|
| Buzzer | D11 | `PASSWORD_OK` / `PASSWORD_FAIL` |
| WHITE LED | D12 | `LIGHT_ON` / `LIGHT_OFF` |
| GREEN LED | D13 | `MUSIC_ON` / `MUSIC_OFF` |
| TMP sensor | A0 | `SEND_TEMP` → `Temperature: <float> C` |

`SEND_TEMP` only works after `PASSWORD_OK` (`pass_corr`). Re-opening USB resets that flag — use **Test PASSWORD_OK** if temperature times out.
"""
)

st.divider()
st.subheader("Session")
st.write("Authenticated:", st.session_state.authenticated)
st.write("Arduino synced:", st.session_state.get("arduino_synced", False))
