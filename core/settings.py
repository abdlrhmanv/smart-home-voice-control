"""Settings / admin use-case — serial + inference summary + calibration."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.ports import SerialPort


@dataclass(frozen=True)
class SerialStatus:
    port: str | None
    baud_rate: int
    connected: bool
    last_error: str | None = None
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class InferenceSummary:
    whisper_size: str
    device: str
    require_known_speaker: bool
    min_command_confidence: float
    note: str | None = None


class SettingsService:
    def __init__(
        self,
        serial: SerialPort,
        *,
        baud_rate: int,
        project_root: Path,
    ) -> None:
        self.serial = serial
        self.baud_rate = baud_rate
        self.project_root = project_root
        self.ml_dir = project_root / "ml"

    def serial_status(self) -> SerialStatus:
        candidates: tuple[str, ...] = ()
        last_error = None
        if hasattr(self.serial, "list_candidate_ports"):
            try:
                candidates = tuple(self.serial.list_candidate_ports())  # type: ignore[attr-defined]
            except Exception:
                candidates = ()
        if hasattr(self.serial, "last_error"):
            last_error = getattr(self.serial, "last_error", None)
        # Prefer live baud from bridge env if present
        baud = self.baud_rate
        if hasattr(self.serial, "baud_rate"):
            baud = int(getattr(self.serial, "baud_rate") or baud)
        return SerialStatus(
            port=self.serial.resolve_port(),
            baud_rate=baud,
            connected=self.serial.is_connected(),
            last_error=last_error,
            candidates=candidates,
        )

    def connect_serial(self) -> bool:
        return self.serial.connect()

    def disconnect_serial(self) -> None:
        self.serial.disconnect()

    def send_test_password_ok(self) -> bool:
        """Send PASSWORD_OK (Ahmed firmware: buzzer pattern + unlock)."""
        return self.serial.send_command("PASSWORD_OK")

    def send_test_command(self, command: str) -> bool:
        return self.serial.send_command(command)

    def inference_summary(self) -> InferenceSummary:
        try:
            ml = str(self.ml_dir)
            if ml not in sys.path:
                sys.path.insert(0, ml)
            from src.config import InferenceConfig

            cfg = InferenceConfig.from_env()
            return InferenceSummary(
                whisper_size=cfg.whisper_size,
                device=cfg.device,
                require_known_speaker=cfg.require_known_speaker,
                min_command_confidence=cfg.min_command_confidence,
            )
        except Exception as exc:
            import os

            return InferenceSummary(
                whisper_size=os.environ.get("WHISPER_SIZE", "base"),
                device=os.environ.get("WHISPER_DEVICE", "cpu"),
                require_known_speaker=True,
                min_command_confidence=0.55,
                note=str(exc),
            )

    def refresh_calibration(self, task: str) -> tuple[bool, str]:
        proc = subprocess.run(
            [sys.executable, "report_calibration.py", "--task", task],
            cwd=str(self.ml_dir),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or "Calibration report failed")
        return True, (proc.stdout.strip() or "Report updated")

    def load_calibration(self, task: str) -> dict[str, Any] | None:
        from utils.calibration_store import load_calibration_report

        return load_calibration_report(task)
