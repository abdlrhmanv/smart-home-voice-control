"""Arduino serial bridge — TX commands and RX temperature replies.

Prefer injecting a ``SerialBridge`` (or a fake) via ``set_bridge()`` in tests.
Module-level helpers remain for the Streamlit app.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional, Protocol

import serial
from serial.tools import list_ports

logger = logging.getLogger(__name__)

DEFAULT_PORT = os.environ.get("ARDUINO_PORT", "")
BAUD_RATE = int(os.environ.get("ARDUINO_BAUD", "9600"))
CONNECT_SETTLE_S = 2.0
READ_TIMEOUT_S = 1.0


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
        self.default_port = DEFAULT_PORT if default_port is None else default_port
        self.baud_rate = BAUD_RATE if baud_rate is None else baud_rate
        self._arduino: Optional[serial.Serial] = None

    def resolve_port(self) -> Optional[str]:
        """Prefer configured port; otherwise pick a common Arduino USB device."""
        if self.default_port:
            return self.default_port

        keywords = (
            "arduino",
            "ch340",
            "ch341",
            "usb serial",
            "usbmodem",
            "ttyacm",
            "ttyusb",
        )
        for port in list_ports.comports():
            blob = f"{port.device} {port.description} {port.manufacturer or ''}".lower()
            if any(k in blob for k in keywords):
                return port.device

        logger.warning(
            "No Arduino-like serial port found. Set ARDUINO_PORT explicitly "
            "(e.g. /dev/ttyUSB0 or COM11)."
        )
        return None

    def connect(self, port: str | None = None) -> bool:
        if self._arduino is not None and self._arduino.is_open:
            return True

        target = port or self.resolve_port()
        if not target:
            logger.warning(
                "No Arduino serial port found. Set ARDUINO_PORT "
                "(e.g. /dev/ttyUSB0 or COM11)."
            )
            return False

        try:
            self._arduino = serial.Serial(
                target, self.baud_rate, timeout=READ_TIMEOUT_S
            )
            time.sleep(CONNECT_SETTLE_S)
            self._arduino.reset_input_buffer()
            logger.info("Arduino connected on %s @ %s", target, self.baud_rate)
            return True
        except Exception as exc:
            self._arduino = None
            logger.error("Arduino connection failed on %s: %s", target, exc)
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
        if self._arduino is None or not self._arduino.is_open:
            if not self.connect():
                return False

        assert self._arduino is not None
        try:
            self._arduino.write((command.strip() + "\n").encode("ascii"))
            self._arduino.flush()
            logger.debug("Sent: %s", command)
            return True
        except Exception as exc:
            logger.error("Failed to send %r: %s", command, exc)
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
                logger.error("Serial read failed: %s", exc)
                return None
            if raw:
                return raw.decode("utf-8", errors="replace").strip()
            time.sleep(0.05)
        return None

    def request_temperature(self, timeout_s: float = 2.0) -> Optional[float]:
        if not self.send_command("SEND_TEMP"):
            return None

        line = self.read_line(timeout_s=timeout_s)
        if not line:
            return None

        for prefix in ("Temperature:", "Tempratute:"):
            if prefix.lower() in line.lower():
                try:
                    token = line.split(":", 1)[1].strip().split()[0]
                    return float(token)
                except (IndexError, ValueError):
                    return None
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
    # Keep env override in sync for callers that patch DEFAULT_PORT in tests.
    _bridge.default_port = DEFAULT_PORT
    return _bridge.resolve_port()


def connect(port: str | None = None) -> bool:
    _bridge.default_port = DEFAULT_PORT
    return _bridge.connect(port)


def disconnect() -> None:
    _bridge.disconnect()


def is_connected() -> bool:
    return _bridge.is_connected()


def send_command(command: str) -> bool:
    _bridge.default_port = DEFAULT_PORT
    return _bridge.send_command(command)


def read_line(timeout_s: float = 2.0) -> Optional[str]:
    _bridge.default_port = DEFAULT_PORT
    return _bridge.read_line(timeout_s=timeout_s)


def request_temperature(timeout_s: float = 2.0) -> Optional[float]:
    _bridge.default_port = DEFAULT_PORT
    return _bridge.request_temperature(timeout_s=timeout_s)
