"""Configuration for the voice dataset recorder (UI + audio only).

Does not import ML domain packages — keeps Tkinter isolated.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
SPEAKER_NAME = "Abdlrhman"

# Multi-condition sessions: close | distance | noise | rate
# Files go to data/dataset/<speaker>/<command>/<RECORDING_CONDITION>/
RECORDING_CONDITION = "close"

COMMANDS: list[tuple[str, str]] = [
    ("light_on", "light on"),
    ("light_off", "light off"),
    ("music_on", "music on"),
    ("music_off", "music off"),
]

RECORDINGS_PER_COMMAND = 25

SAMPLE_RATE = 16_000
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2
DURATION_SEC = 3.0
COUNTDOWN_SEC = 3

BEEP_FREQ_HZ = 880.0
BEEP_DURATION_SEC = 0.18
BEEP_AMPLITUDE = 0.35

SILENCE_TOP_DB = 30.0
SILENCE_PAD_SEC = 0.05
RMS_REJECT_THRESHOLD = 0.008
CLIP_THRESHOLD = 0.99

RECORDER_DIR = Path(__file__).resolve().parent
ML_ROOT = RECORDER_DIR.parent
DATASET_ROOT = ML_ROOT / "data" / "dataset"

COLORS = {
    "bg": "#12141a",
    "panel": "#1c1f29",
    "panel_alt": "#252a38",
    "fg": "#e8eaef",
    "fg_muted": "#9aa3b5",
    "accent": "#5b8cff",
    "accent_hover": "#7aa2ff",
    "success": "#3ecf8e",
    "warning": "#f0b429",
    "danger": "#ff5c5c",
    "record_red": "#e63946",
    "bar_bg": "#2a3040",
    "bar_fill": "#5b8cff",
    "border": "#343b4f",
}

FONTS = {
    "command": ("DejaVu Sans", 48, "bold"),
    "counter": ("DejaVu Sans", 28, "bold"),
    "timer": ("DejaVu Sans", 64, "bold"),
    "status": ("DejaVu Sans", 14),
    "label": ("DejaVu Sans", 12),
    "button": ("DejaVu Sans", 12, "bold"),
    "title": ("DejaVu Sans", 18, "bold"),
}
