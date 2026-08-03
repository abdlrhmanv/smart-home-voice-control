"""Microphone capture for password / command utterances."""

from __future__ import annotations

import uuid
from pathlib import Path

from scipy.io.wavfile import write

SAMPLE_RATE = 16000
DURATION = 3


class MicrophoneUnavailableError(RuntimeError):
    """Raised when PortAudio / sounddevice cannot open a mic."""


def record_audio(dest_dir: str | Path = "temp") -> str:
    """
    Record audio from the microphone and save a unique WAV under ``temp/``.

    ``sounddevice`` is imported lazily so unit tests / CI / Streamlit Cloud
    can import the package without PortAudio. Prefer ``st.audio_input`` in
    the UI so recording happens in the browser instead.
    """
    try:
        import sounddevice as sd
    except OSError as exc:
        raise MicrophoneUnavailableError(
            "Server microphone unavailable (PortAudio not found). "
            "Use the browser mic recorder or upload a WAV instead."
        ) from exc

    output_folder = Path(dest_dir)
    output_folder.mkdir(parents=True, exist_ok=True)
    filename = output_folder / f"input_{uuid.uuid4().hex[:10]}.wav"

    try:
        recording = sd.rec(
            int(DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()
    except Exception as exc:
        raise MicrophoneUnavailableError(
            f"Could not record from server microphone: {exc}. "
            "Use the browser mic recorder or upload a WAV instead."
        ) from exc

    write(filename, SAMPLE_RATE, recording)
    return str(filename)
