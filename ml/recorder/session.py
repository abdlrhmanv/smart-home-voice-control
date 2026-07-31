"""Recording session state machine (no Tk dependency)."""

from __future__ import annotations

import threading
from typing import Protocol

from . import config
from .services.capture import AudioCaptureService
from .services.quality import AudioQualityGate
from .services.wav_writer import WavWriter
from .storage import DatasetStore


class SessionListener(Protocol):
    """UI (or tests) implement these callbacks — DIP for the session."""

    def on_status(self, text: str) -> None: ...

    def on_countdown(self, value: str) -> None: ...

    def on_recording_started(self, phrase: str) -> None: ...

    def on_recording_ended(self) -> None: ...

    def on_saved(self, filename: str, message: str, clipped: bool) -> None: ...

    def on_rejected(self, message: str) -> None: ...

    def on_slot_changed(self, cmd_index: int, rec_index: int, phrase: str) -> None: ...

    def on_complete(self, speaker_name: str) -> None: ...

    def on_error(self, message: str) -> None: ...


class NullListener:
    def on_status(self, text: str) -> None:
        pass

    def on_countdown(self, value: str) -> None:
        pass

    def on_recording_started(self, phrase: str) -> None:
        pass

    def on_recording_ended(self) -> None:
        pass

    def on_saved(self, filename: str, message: str, clipped: bool) -> None:
        pass

    def on_rejected(self, message: str) -> None:
        pass

    def on_slot_changed(self, cmd_index: int, rec_index: int, phrase: str) -> None:
        pass

    def on_complete(self, speaker_name: str) -> None:
        pass

    def on_error(self, message: str) -> None:
        pass


class RecordingSession:
    """
    Owns countdown → beep → record → quality → save → advance.

    Runs the worker thread; notifies a ``SessionListener`` for UI updates.
    """

    def __init__(
        self,
        store: DatasetStore,
        capture: AudioCaptureService | None = None,
        quality: AudioQualityGate | None = None,
        writer: WavWriter | None = None,
        listener: SessionListener | None = None,
    ) -> None:
        self.store = store
        self.capture = capture or AudioCaptureService()
        self.quality = quality or AudioQualityGate()
        self.writer = writer or WavWriter()
        self.listener: SessionListener = listener or NullListener()

        self.cmd_index = 0
        self.rec_index = 1
        self.running = False
        self.paused = False
        self._worker: threading.Thread | None = None
        self._cancel_take = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._generation = 0

        self._resume_from_disk()

    def set_listener(self, listener: SessionListener) -> None:
        self.listener = listener

    def _resume_from_disk(self) -> None:
        if self.store.is_complete():
            self.cmd_index = len(self.store.commands) - 1
            self.rec_index = self.store.recordings_per_command
        else:
            self.cmd_index, self.rec_index = self.store.find_resume_position()

    def current_command(self) -> tuple[str, str]:
        return self.store.commands[self.cmd_index]

    def notify_slot(self) -> None:
        _key, phrase = self.current_command()
        self.listener.on_slot_changed(self.cmd_index, self.rec_index, phrase)

    def start(self) -> None:
        if self.running and not self.paused:
            return
        if self.store.is_complete():
            self.listener.on_complete(self.store.speaker_name)
            return

        self.paused = False
        self._pause_event.set()
        self._cancel_take.clear()
        self.running = True
        self._generation += 1
        gen = self._generation
        self.listener.on_status("Session started…")
        self._spawn(gen)

    def pause(self) -> None:
        if not self.running or self.paused:
            return
        self.paused = True
        self._pause_event.clear()
        self._cancel_take.set()
        self.listener.on_countdown("❚❚")
        self.listener.on_recording_ended()
        self.listener.on_status("Paused. Press Resume to continue.")

    def resume(self) -> None:
        if not self.running or not self.paused:
            return
        self.paused = False
        self._cancel_take.clear()
        self._pause_event.set()
        self.listener.on_countdown("—")
        self.listener.on_status("Resuming…")
        self._generation += 1
        self._spawn(self._generation)

    def retry_current(self) -> None:
        key, _ = self.current_command()
        path = self.store.wav_path(key, self.rec_index)
        if path.exists():
            path.unlink()

        if not self.running:
            self.start()
            return

        self._cancel_take.set()
        self.paused = False
        self._pause_event.set()
        self._generation += 1
        gen = self._generation
        self._cancel_take.clear()
        self.listener.on_status(f"Retrying {key}_{self.rec_index:03d}…")
        self._spawn(gen)

    def stop(self) -> None:
        self.running = False
        self._cancel_take.set()
        self._pause_event.set()

    def _spawn(self, generation: int) -> None:
        self._worker = threading.Thread(
            target=self._loop, args=(generation,), daemon=True
        )
        self._worker.start()

    def _loop(self, generation: int) -> None:
        while (
            self.running
            and generation == self._generation
            and not self.store.is_complete()
        ):
            self._pause_event.wait()
            if generation != self._generation or not self.running:
                return

            key, phrase = self.current_command()
            while (
                self.rec_index <= self.store.recordings_per_command
                and self.store.wav_path(key, self.rec_index).exists()
            ):
                self.rec_index += 1
            if self.rec_index > self.store.recordings_per_command:
                if not self._advance_command():
                    break
                continue

            self.notify_slot()
            self.listener.on_status(f"Get ready: “{phrase}”")

            if not self._countdown(generation):
                if self.paused:
                    return
                continue

            if generation != self._generation or not self.running:
                return

            self.listener.on_status("Beep…")
            try:
                self.capture.play_beep()
            except Exception as exc:  # noqa: BLE001
                self.listener.on_error(f"Beep failed: {exc}")

            if self._cancel_take.is_set() or generation != self._generation:
                self._cancel_take.clear()
                if self.paused:
                    return
                continue

            self.listener.on_recording_started(phrase)
            try:
                raw = self.capture.record()
            except Exception as exc:  # noqa: BLE001
                self.running = False
                self.listener.on_recording_ended()
                self.listener.on_error(f"Mic error: {exc}")
                return

            self.listener.on_recording_ended()

            if self._cancel_take.is_set() or generation != self._generation:
                self._cancel_take.clear()
                if self.paused:
                    return
                continue

            report = self.quality.process(raw)
            if not report.accepted:
                self.listener.on_rejected(report.message)
                if not self._sleep(1.2, generation):
                    if self.paused:
                        return
                continue

            path = self.store.wav_path(key, self.rec_index)
            assert report.audio_int16 is not None
            self.writer.write(path, report.audio_int16)
            self.listener.on_saved(path.name, report.message, report.clipped)

            self.rec_index += 1
            if self.rec_index > self.store.recordings_per_command:
                if not self._advance_command():
                    break
            else:
                self.notify_slot()

            if not self._sleep(0.45, generation):
                if self.paused:
                    return

        if self.store.is_complete() and generation == self._generation:
            self.running = False
            self.listener.on_complete(self.store.speaker_name)

    def _advance_command(self) -> bool:
        if self.cmd_index >= len(self.store.commands) - 1:
            return False
        self.cmd_index += 1
        self.rec_index = 1
        key, phrase = self.current_command()
        self.notify_slot()
        self.listener.on_status(f"Next command: “{phrase}” ({key})")
        return True

    def _countdown(self, generation: int) -> bool:
        for remaining in range(config.COUNTDOWN_SEC, 0, -1):
            if (
                not self.running
                or generation != self._generation
                or self._cancel_take.is_set()
            ):
                return False
            self.listener.on_countdown(str(remaining))
            if not self._sleep(1.0, generation):
                return False
        self.listener.on_countdown("GO")
        return True

    def _sleep(self, seconds: float, generation: int) -> bool:
        steps = max(1, int(seconds / 0.05))
        for _ in range(steps):
            if (
                not self.running
                or generation != self._generation
                or self._cancel_take.is_set()
            ):
                return False
            if not self._pause_event.wait(timeout=0.05):
                return False
        return True
