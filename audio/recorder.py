"""Microphone capture for password / command utterances."""

from __future__ import annotations

import uuid
from pathlib import Path

from scipy.io.wavfile import write

SAMPLE_RATE = 16000
DURATION = 3


def record_audio(dest_dir: str | Path = "temp") -> str:
    """
    Record audio from the microphone and save a unique WAV under ``temp/``.

    ``sounddevice`` is imported lazily so unit tests / CI can import the
    package without PortAudio installed.
    """
    import sounddevice as sd

    output_folder = Path(dest_dir)
    output_folder.mkdir(parents=True, exist_ok=True)
    filename = output_folder / f"input_{uuid.uuid4().hex[:10]}.wav"

    recording = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    write(filename, SAMPLE_RATE, recording)
    return str(filename)
