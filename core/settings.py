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
        return SerialStatus(
            port=self.serial.resolve_port(),
            baud_rate=self.baud_rate,
            connected=self.serial.is_connected(),
        )

    def connect_serial(self) -> bool:
        return self.serial.connect()

    def disconnect_serial(self) -> None:
        self.serial.disconnect()

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
