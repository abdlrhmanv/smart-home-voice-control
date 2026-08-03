"""Laptop music playback adapter for MUSIC_ON / MUSIC_OFF."""

from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_SAMPLE_RATE = 22050


class SoundDeviceMusicPlayer:
    """Looping synthesized melody via sounddevice (no external asset)."""

    def __init__(self) -> None:
        self._play_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    @staticmethod
    def _synthesize_loop(seconds: float = 4.0) -> np.ndarray:
        notes_hz = [523.25, 659.25, 783.99, 659.25, 587.33, 523.25, 392.00, 523.25]
        note_len = seconds / len(notes_hz)
        chunks: list[np.ndarray] = []
        t_note = np.linspace(0, note_len, int(_SAMPLE_RATE * note_len), endpoint=False)
        envelope = np.linspace(0.0, 1.0, 200)
        for freq in notes_hz:
            wave = 0.18 * np.sin(2 * np.pi * freq * t_note)
            wave[:200] *= envelope
            wave[-200:] *= envelope[::-1]
            chunks.append(wave.astype(np.float32))
        return np.concatenate(chunks)

    def _play_loop(self) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:  # pragma: no cover
            logger.warning("Music playback unavailable: %s", exc)
            return

        audio = self._synthesize_loop()
        try:
            while not self._stop_event.is_set():
                sd.play(audio, _SAMPLE_RATE, blocking=True)
                if self._stop_event.is_set():
                    break
        except Exception as exc:
            logger.warning("Music playback failed: %s", exc)
        finally:
            try:
                sd.stop()
            except Exception:
                pass

    def start(self) -> bool:
        with self._lock:
            if self._play_thread is not None and self._play_thread.is_alive():
                return True
            self._stop_event.clear()
            self._play_thread = threading.Thread(
                target=self._play_loop, name="music-loop", daemon=True
            )
            self._play_thread.start()
            return True

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            try:
                import sounddevice as sd

                sd.stop()
            except Exception:
                pass
            thread = self._play_thread
            self._play_thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.5)

    def is_playing(self) -> bool:
        return self._play_thread is not None and self._play_thread.is_alive()


# Process-wide default instance (Streamlit multipage shares the process).
_default_player = SoundDeviceMusicPlayer()


def start_music() -> bool:
    return _default_player.start()


def stop_music() -> None:
    _default_player.stop()


def is_playing() -> bool:
    return _default_player.is_playing()
