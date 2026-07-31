"""
Tkinter UI for the voice dataset recorder.

Business logic lives in ``RecordingSession``; this class only paints widgets
and forwards button/keyboard events.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from . import config
from .session import RecordingSession
from .storage import DatasetStore


class RecorderApp(tk.Tk):
    """Dark-themed shell bound to a ``RecordingSession``."""

    def __init__(self, speaker_name: str = config.SPEAKER_NAME) -> None:
        super().__init__()
        self.title(f"Voice Dataset Recorder — {speaker_name}")
        self.configure(bg=config.COLORS["bg"])
        self.minsize(900, 640)
        self.geometry("980x700")

        store = DatasetStore(speaker_name=speaker_name)
        store.ensure_layout()
        self.session = RecordingSession(store=store)
        self.session.set_listener(self)

        self._build_styles()
        self._build_ui()
        self._bind_keys()
        self.session.notify_slot()
        self.on_status("Ready. Press Start Session (Enter).")
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

    # ----- SessionListener (marshalled onto Tk thread) ---------------------
    def _ui(self, fn: Callable) -> None:
        self.after(0, fn)

    def on_status(self, text: str) -> None:
        self._ui(lambda: self.status_label.configure(text=text, fg=config.COLORS["fg_muted"]))

    def on_countdown(self, value: str) -> None:
        color = config.COLORS["accent"]
        if value == "GO":
            color = config.COLORS["success"]
        elif value == "❚❚":
            color = config.COLORS["warning"]
        elif value == "—":
            color = config.COLORS["fg_muted"]
        self._ui(lambda: self.timer_label.configure(text=value, fg=color))

    def on_recording_started(self, phrase: str) -> None:
        def _paint() -> None:
            self._set_recording_indicator(True)
            self.timer_label.configure(text="●", fg=config.COLORS["record_red"])
            self.status_label.configure(
                text=f"Recording… speak “{phrase}”",
                fg=config.COLORS["fg"],
            )

        self._ui(_paint)

    def on_recording_ended(self) -> None:
        self._ui(lambda: self._set_recording_indicator(False))

    def on_saved(self, filename: str, message: str, clipped: bool) -> None:
        color = config.COLORS["warning"] if clipped else config.COLORS["success"]

        def _paint() -> None:
            self.timer_label.configure(text="✓", fg=config.COLORS["success"])
            self.status_label.configure(text=f"{filename} — {message}", fg=color)
            self._refresh_progress()

        self._ui(_paint)

    def on_rejected(self, message: str) -> None:
        def _paint() -> None:
            self.timer_label.configure(text="!", fg=config.COLORS["danger"])
            self.status_label.configure(text=message, fg=config.COLORS["danger"])
            self._set_recording_indicator(False)
            self._refresh_progress()

        self._ui(_paint)

    def on_slot_changed(self, cmd_index: int, rec_index: int, phrase: str) -> None:
        def _paint() -> None:
            self.command_label.configure(text=phrase)
            self.counter_label.configure(
                text=f"{rec_index} / {config.RECORDINGS_PER_COMMAND}"
            )
            self._refresh_progress()

        self._ui(_paint)

    def on_complete(self, speaker_name: str) -> None:
        def _paint() -> None:
            self._set_recording_indicator(False)
            self.timer_label.configure(text="🎉", fg=config.COLORS["success"])
            self.command_label.configure(text="All done!")
            msg = (
                f"🎉 Congratulations, {speaker_name}!\n"
                "You have successfully recorded all 100 samples."
            )
            self.status_label.configure(text=msg, fg=config.COLORS["success"])
            self._refresh_progress()
            self.btn_start.configure(state="disabled")
            self.btn_retry.configure(state="disabled")
            self.btn_pause.configure(state="disabled")
            self.btn_resume.configure(state="disabled")
            messagebox.showinfo("Session complete", msg)

        self._ui(_paint)

    def on_error(self, message: str) -> None:
        def _paint() -> None:
            self._set_recording_indicator(False)
            self.status_label.configure(text=message, fg=config.COLORS["danger"])
            self.btn_start.configure(state="normal")
            self.btn_pause.configure(state="disabled")
            messagebox.showerror("Recording error", message)

        self._ui(_paint)

    # ----- UI construction -------------------------------------------------
    def _build_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        c = config.COLORS
        style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor=c["bar_bg"],
            background=c["bar_fill"],
            bordercolor=c["border"],
            lightcolor=c["bar_fill"],
            darkcolor=c["bar_fill"],
            thickness=22,
        )

    def _build_ui(self) -> None:
        c = config.COLORS
        pad = {"padx": 24, "pady": 8}

        header = tk.Frame(self, bg=c["bg"])
        header.pack(fill="x", **pad)
        tk.Label(
            header,
            text=f"Speaker: {self.session.store.speaker_name}",
            font=config.FONTS["title"],
            fg=c["accent"],
            bg=c["bg"],
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Say the command clearly after the beep · 16 kHz mono · 3 s",
            font=config.FONTS["label"],
            fg=c["fg_muted"],
            bg=c["bg"],
        ).pack(anchor="w")

        panel = tk.Frame(
            self, bg=c["panel"], highlightbackground=c["border"], highlightthickness=1
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        self.command_label = tk.Label(
            panel, text="light on", font=config.FONTS["command"], fg=c["fg"], bg=c["panel"], wraplength=860
        )
        self.command_label.pack(pady=(36, 8))

        self.counter_label = tk.Label(
            panel, text="0 / 25", font=config.FONTS["counter"], fg=c["accent"], bg=c["panel"]
        )
        self.counter_label.pack()

        self.timer_label = tk.Label(
            panel, text="—", font=config.FONTS["timer"], fg=c["fg_muted"], bg=c["panel"]
        )
        self.timer_label.pack(pady=12)

        ind_row = tk.Frame(panel, bg=c["panel"])
        ind_row.pack(pady=4)
        self.rec_dot = tk.Canvas(ind_row, width=22, height=22, bg=c["panel"], highlightthickness=0)
        self.rec_dot.pack(side="left", padx=(0, 10))
        self._dot_id = self.rec_dot.create_oval(3, 3, 19, 19, fill=c["bar_bg"], outline="")
        self.rec_text = tk.Label(
            ind_row, text="IDLE", font=config.FONTS["button"], fg=c["fg_muted"], bg=c["panel"]
        )
        self.rec_text.pack(side="left")

        self.status_label = tk.Label(
            panel, text="", font=config.FONTS["status"], fg=c["fg_muted"], bg=c["panel"], wraplength=860, justify="center"
        )
        self.status_label.pack(pady=(16, 24))

        prog = tk.Frame(self, bg=c["bg"])
        prog.pack(fill="x", padx=24)
        self.progress_label = tk.Label(
            prog, text="Overall: 0 / 100  (0%)", font=config.FONTS["label"], fg=c["fg"], bg=c["bg"]
        )
        self.progress_label.pack(anchor="w")
        self.progress = ttk.Progressbar(
            prog, orient="horizontal", mode="determinate", maximum=100, style="Dark.Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x", pady=(6, 4))

        btns = tk.Frame(self, bg=c["bg"])
        btns.pack(fill="x", padx=24, pady=20)
        self.btn_start = self._make_button(btns, "Start Session", self._start, c["accent"])
        self.btn_retry = self._make_button(btns, "Retry Current", self._retry, c["warning"])
        self.btn_pause = self._make_button(btns, "Pause", self._pause, c["panel_alt"])
        self.btn_resume = self._make_button(btns, "Resume", self._resume, c["success"])
        self.btn_exit = self._make_button(btns, "Exit", self._on_exit, c["danger"])
        for b in (self.btn_start, self.btn_retry, self.btn_pause, self.btn_resume, self.btn_exit):
            b.pack(side="left", padx=6)
        self.btn_resume.configure(state="disabled")
        self.btn_retry.configure(state="disabled")
        self.btn_pause.configure(state="disabled")

        tk.Label(
            self,
            text="Shortcuts:  Enter = Start   ·   R = Retry   ·   Esc = Exit",
            font=config.FONTS["label"],
            fg=c["fg_muted"],
            bg=c["bg"],
        ).pack(pady=(0, 16))

    def _make_button(self, parent, text, command, color) -> tk.Button:
        dark_fg = color in (
            config.COLORS["accent"],
            config.COLORS["success"],
            config.COLORS["warning"],
        )
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=config.FONTS["button"],
            bg=color,
            fg="#0d0f14" if dark_fg else config.COLORS["fg"],
            activebackground=config.COLORS["accent_hover"],
            activeforeground="#0d0f14",
            relief="flat",
            padx=16,
            pady=10,
            cursor="hand2",
            borderwidth=0,
        )

    def _bind_keys(self) -> None:
        self.bind("<Return>", lambda _e: self._start())
        self.bind("<r>", lambda _e: self._retry())
        self.bind("<R>", lambda _e: self._retry())
        self.bind("<Escape>", lambda _e: self._on_exit())
        self.focus_set()

    def _set_recording_indicator(self, active: bool) -> None:
        c = config.COLORS
        if active:
            self.rec_dot.itemconfig(self._dot_id, fill=c["record_red"])
            self.rec_text.configure(text="RECORDING", fg=c["record_red"])
        else:
            self.rec_dot.itemconfig(self._dot_id, fill=c["bar_bg"])
            self.rec_text.configure(text="IDLE", fg=c["fg_muted"])

    def _refresh_progress(self) -> None:
        store = self.session.store
        done = store.total_recorded()
        total = store.total_expected()
        pct = int(round(100 * done / total)) if total else 0
        self.progress_label.configure(text=f"Overall: {done} / {total}  ({pct}%)")
        self.progress["value"] = pct

    def _start(self) -> None:
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal")
        self.btn_resume.configure(state="disabled")
        self.btn_retry.configure(state="normal")
        self.session.start()

    def _pause(self) -> None:
        self.session.pause()
        self.btn_pause.configure(state="disabled")
        self.btn_resume.configure(state="normal")

    def _resume(self) -> None:
        self.btn_pause.configure(state="normal")
        self.btn_resume.configure(state="disabled")
        self.session.resume()

    def _retry(self) -> None:
        self.btn_pause.configure(state="normal")
        self.btn_resume.configure(state="disabled")
        self.btn_retry.configure(state="normal")
        self.btn_start.configure(state="disabled")
        self.session.retry_current()

    def _on_exit(self) -> None:
        if self.session.running and not self.session.store.is_complete():
            if not messagebox.askyesno(
                "Exit",
                "Session in progress. Exit anyway?\nSaved recordings will be kept.",
            ):
                return
        self.session.stop()
        self.destroy()


def main(speaker_name: str = config.SPEAKER_NAME) -> None:
    app = RecorderApp(speaker_name=speaker_name)
    app.mainloop()
