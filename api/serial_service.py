"""Arduino serial bridge — TX commands and RX temperature replies."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import serial
from serial.tools import list_ports

logger = logging.getLogger(__name__)

DEFAULT_PORT = os.environ.get("ARDUINO_PORT", "")
BAUD_RATE = int(os.environ.get("ARDUINO_BAUD", "9600"))
CONNECT_SETTLE_S = 2.0
READ_TIMEOUT_S = 1.0

_arduino: Optional[serial.Serial] = None


def resolve_port() -> Optional[str]:
    """Prefer ARDUINO_PORT; otherwise pick a common Arduino USB device."""
    if DEFAULT_PORT:
        return DEFAULT_PORT

    keywords = ("arduino", "ch340", "ch341", "usb serial", "usbmodem", "ttyacm", "ttyusb")
    for port in list_ports.comports():
        blob = f"{port.device} {port.description} {port.manufacturer or ''}".lower()
        if any(k in blob for k in keywords):
            return port.device

    ports = list(list_ports.comports())
    return ports[0].device if ports else None


def connect(port: str | None = None) -> bool:
    """Open the serial port. Returns True on success."""
    global _arduino

    if _arduino is not None and _arduino.is_open:
        return True

    target = port or resolve_port()
    if not target:
        logger.warning(
            "No Arduino serial port found. Set ARDUINO_PORT (e.g. /dev/ttyUSB0 or COM11)."
        )
        return False

    try:
        _arduino = serial.Serial(target, BAUD_RATE, timeout=READ_TIMEOUT_S)
        time.sleep(CONNECT_SETTLE_S)
        _arduino.reset_input_buffer()
        logger.info("Arduino connected on %s @ %s", target, BAUD_RATE)
        return True
    except Exception as exc:
        _arduino = None
        logger.error("Arduino connection failed on %s: %s", target, exc)
        return False


def disconnect() -> None:
    global _arduino
    if _arduino is not None:
        try:
            _arduino.close()
        except Exception:
            pass
        _arduino = None


def is_connected() -> bool:
    return _arduino is not None and _arduino.is_open


def send_command(command: str) -> bool:
    """Send a newline-terminated command. Returns True if bytes were written."""
    global _arduino

    if _arduino is None or not _arduino.is_open:
        if not connect():
            return False

    assert _arduino is not None
    try:
        _arduino.write((command.strip() + "\n").encode("ascii"))
        _arduino.flush()
        logger.debug("Sent: %s", command)
        return True
    except Exception as exc:
        logger.error("Failed to send %r: %s", command, exc)
        disconnect()
        return False


def read_line(timeout_s: float = 2.0) -> Optional[str]:
    """Read one line from Arduino (strips whitespace)."""
    if _arduino is None or not _arduino.is_open:
        if not connect():
            return None

    assert _arduino is not None
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            raw = _arduino.readline()
        except Exception as exc:
            logger.error("Serial read failed: %s", exc)
            return None
        if raw:
            return raw.decode("utf-8", errors="replace").strip()
        time.sleep(0.05)
    return None


def request_temperature(timeout_s: float = 2.0) -> Optional[float]:
    """Ask Arduino for temperature and parse 'Temperature: <float> C'."""
    if not send_command("SEND_TEMP"):
        return None

    line = read_line(timeout_s=timeout_s)
    if not line:
        return None

    # Accept both current spelling and older typo from earlier firmware
    for prefix in ("Temperature:", "Tempratute:"):
        if prefix.lower() in line.lower():
            try:
                # "Temperature: 23.50 C"
                token = line.split(":", 1)[1].strip().split()[0]
                return float(token)
            except (IndexError, ValueError):
                return None
    return None
