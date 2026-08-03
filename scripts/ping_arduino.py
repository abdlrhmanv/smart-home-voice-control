#!/usr/bin/env python3
"""Quick hardware check against Ahmed's Arduino sketch."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.env_loader import load_dotenv

load_dotenv(ROOT / ".env")

from api.serial_service import get_bridge


def main() -> int:
    bridge = get_bridge()
    bridge.refresh_from_env()
    print("ARDUINO_PORT =", os.environ.get("ARDUINO_PORT") or "(auto)")
    print("candidates  =", bridge.list_candidate_ports())
    print("resolved    =", bridge.resolve_port())
    if not bridge.connect():
        print("FAIL:", bridge.last_error)
        print("Hint: export ARDUINO_PORT=/dev/ttyACM0   # or /dev/ttyUSB0")
        print("      sudo usermod -aG dialout $USER && re-login")
        return 1
    print("connected on", bridge.last_port)
    print("Sending PASSWORD_OK (expect 3 buzzer beeps, ~4.5s)…")
    if not bridge.send_command("PASSWORD_OK"):
        print("FAIL send:", bridge.last_error)
        return 1
    print("Sending LIGHT_ON…")
    bridge.send_command("LIGHT_ON")
    print("Sending MUSIC_ON…")
    bridge.send_command("MUSIC_ON")
    print("Sending SEND_TEMP…")
    temp = bridge.request_temperature()
    print("temperature =", temp)
    print("OK — if hardware silent, re-flash arduino/arduino.ino and check wiring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
