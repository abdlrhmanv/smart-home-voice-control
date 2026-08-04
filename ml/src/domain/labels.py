"""Label maps for speakers and voice commands (single source of truth)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LabelMap:
    """Bidirectional name ↔ integer encoding for a classification task."""

    name_to_id: dict[str, int]

    @property
    def id_to_name(self) -> dict[int, str]:
        return {v: k for k, v in self.name_to_id.items()}

    def encode(self, name: str) -> int:
        try:
            return self.name_to_id[name]
        except KeyError as exc:
            raise KeyError(f"Unknown label '{name}'. Known: {list(self.name_to_id)}") from exc

    def decode(self, label_id: int) -> str:
        try:
            return self.id_to_name[label_id]
        except KeyError as exc:
            raise KeyError(f"Unknown id {label_id}. Known: {list(self.id_to_name)}") from exc

    def names(self) -> list[str]:
        return list(self.name_to_id.keys())

    def __contains__(self, name: str) -> bool:
        return name in self.name_to_id

    def __iter__(self):
        return iter(self.name_to_id)

    def __len__(self) -> int:
        return len(self.name_to_id)


SPEAKER_LABELS = LabelMap(
    {
        "ahmed": 0,
        "abdullah": 1,
        "Abdlrhman": 2,
    }
)

COMMAND_LABELS = LabelMap(
    {
        "light_on": 0,
        "light_off": 1,
        "music_on": 2,
        "music_off": 3,
    }
)

# folder key → spoken phrase (UI / recorder)
COMMAND_PHRASES: list[tuple[str, str]] = [
    ("light_on", "light on"),
    ("light_off", "light off"),
    ("music_on", "music on"),
    ("music_off", "music off"),
]

# STT variants for live mic (e.g. "lighton" as one word). Off before on.
_COMMAND_STT_VARIANTS: list[tuple[str, tuple[str, ...]]] = [
    ("light_off", ("light off", "lights off", "lightoff")),
    ("music_off", ("music off", "musicoff")),
    ("light_on", ("light on", "lights on", "lighton", "lighten")),
    ("music_on", ("music on", "musicon")),
]


def match_command_phrase(transcript: str) -> str | None:
    """Map a Whisper transcript to a command label, or None if unclear."""
    text = transcript.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    compact = text.replace(" ", "")
    for command, variants in _COMMAND_STT_VARIANTS:
        for variant in variants:
            if variant in text or variant.replace(" ", "") in compact:
                return command
    return None

DEFAULT_PASSWORD = "open"
AUDIO_EXTENSIONS = frozenset({".wav", ".flac", ".ogg", ".mp3", ".m4a"})

# Optional third-level folders: dataset/<speaker>/<command>/<condition>/
RECORDING_CONDITIONS: tuple[str, ...] = (
    "close",
    "distance",
    "noise",
    "rate",
)
DEFAULT_CONDITION = "close"
