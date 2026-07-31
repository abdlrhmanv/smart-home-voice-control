"""Audio capture and cue tone."""

from __future__ import annotations

import numpy as np
import sounddevice as sd

from .. import config


class AudioCaptureService:
    """SRP: microphone I/O only."""

    def __init__(
        self,
        sample_rate: int = config.SAMPLE_RATE,
        channels: int = config.CHANNELS,
        duration_sec: float = config.DURATION_SEC,
        beep_freq: float = config.BEEP_FREQ_HZ,
        beep_duration: float = config.BEEP_DURATION_SEC,
        beep_amplitude: float = config.BEEP_AMPLITUDE,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.duration_sec = duration_sec
        self.beep_freq = beep_freq
        self.beep_duration = beep_duration
        self.beep_amplitude = beep_amplitude

    def play_beep(self) -> None:
        t = np.linspace(
            0.0,
            self.beep_duration,
            int(self.sample_rate * self.beep_duration),
            endpoint=False,
        )
        envelope = np.ones_like(t)
        fade = max(1, int(0.01 * self.sample_rate))
        envelope[:fade] = np.linspace(0.0, 1.0, fade)
        envelope[-fade:] = np.linspace(1.0, 0.0, fade)
        tone = (
            self.beep_amplitude * np.sin(2 * np.pi * self.beep_freq * t) * envelope
        ).astype(np.float32)
        sd.play(tone, self.sample_rate)
        sd.wait()

    def record(self) -> np.ndarray:
        frames = int(self.duration_sec * self.sample_rate)
        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        )
        sd.wait()
        return np.squeeze(audio).astype(np.float32)
