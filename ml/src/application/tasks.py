"""Preconfigured classifier tasks."""

from __future__ import annotations

from src.domain.labels import COMMAND_LABELS, SPEAKER_LABELS
from src.domain.models import ClassifierTask

SPEAKER_TASK = ClassifierTask(
    name="speaker",
    labels=SPEAKER_LABELS,
    artifact="speaker.pkl",
    target="speaker",
)

COMMAND_TASK = ClassifierTask(
    name="command",
    labels=COMMAND_LABELS,
    artifact="command.pkl",
    target="command",
)
