"""Settings façade for the Settings page."""

from __future__ import annotations

from core.container import get_container


def serial_status():
    return get_container().settings.serial_status()


def connect_serial() -> bool:
    return get_container().settings.connect_serial()


def disconnect_serial() -> None:
    get_container().settings.disconnect_serial()


def send_test_password_ok() -> bool:
    return get_container().settings.send_test_password_ok()


def send_test_command(command: str) -> bool:
    return get_container().settings.send_test_command(command)


def inference_summary():
    return get_container().settings.inference_summary()


def refresh_calibration(task: str) -> tuple[bool, str]:
    return get_container().settings.refresh_calibration(task)


def load_calibration(task: str):
    return get_container().settings.load_calibration(task)
