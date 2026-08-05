"""Arduino serial bridge — TX commands and RX temperature replies.

Matches Ahmed's firmware protocol (9600 baud, newline-terminated):
  PASSWORD_OK | PASSWORD_FAIL | LIGHT_ON | LIGHT_OFF | MUSIC_ON | MUSIC_OFF | SEND_TEMP
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional, Protocol

import serial
from serial.tools import list_ports

logger = logging.getLogger(__name__)

# Ahmed's PASSWORD_OK blocks ~4.5s (3× beep with delays). Wait before next TX.
PASSWORD_OK_SETTLE_S = float(os.environ.get("ARDUINO_PASSWORD_SETTLE_S", "4.6"))
CONNECT_SETTLE_S = float(os.environ.get("ARDUINO_CONNECT_SETTLE_S", "2.0"))
READ_TIMEOUT_S = 1.0
TEMP_LINE_RE = re.compile(
    r"(?:temperature|tempratute)\s*:\s*([-+]?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def env_port() -> str:
    return (os.environ.get("ARDUINO_PORT") or "").strip()


def env_baud() -> int:
    return int(os.environ.get("ARDUINO_BAUD", "9600"))


# Back-compat for tests that patch these names.
DEFAULT_PORT = env_port()
BAUD_RATE = env_baud()


class SerialPort(Protocol):
    """Minimal surface used by device services."""

    def connect(self, port: str | None = None) -> bool: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...
    def send_command(self, command: str) -> bool: ...
    def read_line(self, timeout_s: float = 2.0) -> Optional[str]: ...
    def request_temperature(self, timeout_s: float = 2.0) -> Optional[float]: ...


class SerialBridge:
    """Stateful Arduino USB serial client (injectable)."""

    def __init__(
        self,
        *,
        default_port: str | None = None,
        baud_rate: int | None = None,
    ) -> None:
        self.default_port = env_port() if default_port is None else default_port
        self.baud_rate = env_baud() if baud_rate is None else baud_rate
        self._arduino: Optional[serial.Serial] = None
        self.last_error: str | None = None
        self.last_port: str | None = None

    def refresh_from_env(self) -> None:
        """Pick up ARDUINO_PORT / baud changed after process start."""
        self.default_port = env_port()
        self.baud_rate = env_baud()

    def list_candidate_ports(self) -> list[str]:
        found: list[str] = []
        for port in list_ports.comports():
            blob = f"{port.device} {port.description} {port.manufacturer or ''}".lower()
            dev = port.device.lower()
            if (
                any(
                    k in blob
                    for k in ("arduino", "ch340", "ch341", "usb serial", "usbmodem")
                )
                or "ttyacm" in dev
                or "ttyusb" in dev
                or "cu.usb" in dev
            ):
                found.append(port.device)
        return found

    def resolve_port(self) -> Optional[str]:
        """Prefer configured port; otherwise pick a common Arduino USB device."""
        self.refresh_from_env()
        if self.default_port:
            return self.default_port

        found = self.list_candidate_ports()
        if found:
            return found[0]

        self.last_error = (
            "No Arduino-like serial port found. "
            "Plug in USB and set ARDUINO_PORT (e.g. /dev/ttyACM0 or /dev/ttyUSB0)."
        )
        logger.warning("%s", self.last_error)
        return None

    def connect(self, port: str | None = None) -> bool:
        if self._arduino is not None and self._arduino.is_open:
            return True

        self.refresh_from_env()
        target = port or self.resolve_port()
        if not target:
            return False

        try:
            self._arduino = serial.Serial(
                target, self.baud_rate, timeout=READ_TIMEOUT_S
            )
            # Opening the port resets most Uno/Nano boards — wait for reboot.
            time.sleep(CONNECT_SETTLE_S)
            self._arduino.reset_input_buffer()
            self.last_port = target
            self.last_error = None
            logger.info("Arduino connected on %s @ %s", target, self.baud_rate)
            return True
        except Exception as exc:
            self._arduino = None
            self.last_error = f"Connection failed on {target}: {exc}"
            logger.error("%s", self.last_error)
            return False

    def disconnect(self) -> None:
        if self._arduino is not None:
            try:
                self._arduino.close()
            except Exception:
                pass
            self._arduino = None

    def is_connected(self) -> bool:
        return self._arduino is not None and self._arduino.is_open

    def send_command(self, command: str) -> bool:
        self.refresh_from_env()
        if self._arduino is None or not self._arduino.is_open:
            if not self.connect():
                return False

        assert self._arduino is not None
        try:
            payload = (command.strip() + "\n").encode("ascii")
            self._arduino.write(payload)
            self._arduino.flush()
            logger.info("Sent to Arduino: %s", command.strip())
            # Ahmed's sketch blocks in delay() during PASSWORD_OK beeps.
            if command.strip() == "PASSWORD_OK" and PASSWORD_OK_SETTLE_S > 0:
                time.sleep(PASSWORD_OK_SETTLE_S)
            self.last_error = None
            return True
        except Exception as exc:
            self.last_error = f"Failed to send {command!r}: {exc}"
            logger.error("%s", self.last_error)
            self.disconnect()
            return False

    def read_line(self, timeout_s: float = 2.0) -> Optional[str]:
        if self._arduino is None or not self._arduino.is_open:
            if not self.connect():
                return None

        assert self._arduino is not None
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                raw = self._arduino.readline()
            except Exception as exc:
                self.last_error = f"Serial read failed: {exc}"
                logger.error("%s", self.last_error)
                return None
            if raw:
                return raw.decode("utf-8", errors="replace").strip()
            time.sleep(0.05)
        return None

    def request_temperature(self, timeout_s: float = 3.0) -> Optional[float]:
        if self._arduino is not None and self._arduino.is_open:
            try:
                self._arduino.reset_input_buffer()
            except Exception:
                pass

        if not self.send_command("SEND_TEMP"):
            return None

        # Ahmed replies "Temperature: <float> C" (older builds: "Tempratute:").
        # Keep reading until we see that line or the deadline hits (skip junk).
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            remaining = max(0.05, deadline - time.time())
            line = self.read_line(timeout_s=min(1.0, remaining))
            if not line:
                continue
            match = TEMP_LINE_RE.search(line)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
            logger.debug("Ignoring non-temp serial line: %r", line)
        self.last_error = (
            "Timed out waiting for Temperature: reply (is PASSWORD_OK set?)"
        )
        logger.warning("%s", self.last_error)
        return None


_bridge: SerialBridge = SerialBridge()


def get_bridge() -> SerialBridge:
    return _bridge


def set_bridge(bridge: SerialBridge | None = None) -> SerialBridge:
    """Replace the process-wide bridge (tests). Pass ``None`` to reset."""
    global _bridge
    _bridge = bridge if bridge is not None else SerialBridge()
    return _bridge


def resolve_port() -> Optional[str]:
    global DEFAULT_PORT
    DEFAULT_PORT = env_port()
    if hasattr(_bridge, "refresh_from_env"):
        _bridge.refresh_from_env()
    return _bridge.resolve_port()


def connect(port: str | None = None) -> bool:
    if hasattr(_bridge, "refresh_from_env"):
        _bridge.refresh_from_env()
    return _bridge.connect(port)


def disconnect() -> None:
    _bridge.disconnect()


def is_connected() -> bool:
    return _bridge.is_connected()


def send_command(command: str) -> bool:
    if hasattr(_bridge, "refresh_from_env"):
        _bridge.refresh_from_env()
    return _bridge.send_command(command)


def read_line(timeout_s: float = 2.0) -> Optional[str]:
    if hasattr(_bridge, "refresh_from_env"):
        _bridge.refresh_from_env()
    return _bridge.read_line(timeout_s=timeout_s)


def request_temperature(timeout_s: float = 2.0) -> Optional[float]:
    if hasattr(_bridge, "refresh_from_env"):
        _bridge.refresh_from_env()
    return _bridge.request_temperature(timeout_s=timeout_s)
