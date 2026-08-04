from api import serial_service
from api.serial_service import SerialBridge


class _FakePort:
    def __init__(self, device, description="USB", manufacturer="Other"):
        self.device = device
        self.description = description
        self.manufacturer = manufacturer


def test_send_command_without_port_returns_false(monkeypatch):
    bridge = SerialBridge(default_port="")
    monkeypatch.setattr(bridge, "resolve_port", lambda: None)
    serial_service.set_bridge(bridge)
    try:
        assert serial_service.send_command("LIGHT_ON") is False
    finally:
        serial_service.set_bridge(None)


def test_resolve_port_fails_closed_on_unrelated_device(monkeypatch):
    monkeypatch.setattr(serial_service, "DEFAULT_PORT", "")
    monkeypatch.setattr(
        serial_service.list_ports,
        "comports",
        lambda: [_FakePort("/dev/ttyS0", description="UART Bridge")],
    )
    bridge = SerialBridge(default_port="")
    assert bridge.resolve_port() is None


def test_resolve_port_matches_arduino_keyword(monkeypatch):
    monkeypatch.setattr(
        serial_service.list_ports,
        "comports",
        lambda: [_FakePort("/dev/ttyUSB0", description="Arduino Uno")],
    )
    bridge = SerialBridge(default_port="")
    assert bridge.resolve_port() == "/dev/ttyUSB0"


def test_request_temperature_parses_line(monkeypatch):
    bridge = SerialBridge()
    monkeypatch.setattr(bridge, "send_command", lambda cmd: True)
    monkeypatch.setattr(
        bridge, "read_line", lambda timeout_s=2.0: "Temperature: 24.5 C"
    )
    assert bridge.request_temperature() == 24.5


def test_request_temperature_accepts_legacy_typo(monkeypatch):
    bridge = SerialBridge()
    monkeypatch.setattr(bridge, "send_command", lambda cmd: True)
    monkeypatch.setattr(
        bridge, "read_line", lambda timeout_s=2.0: "Tempratute: 21.0 C"
    )
    assert bridge.request_temperature() == 21.0


def test_request_temperature_skips_junk_then_parses(monkeypatch):
    bridge = SerialBridge()
    monkeypatch.setattr(bridge, "send_command", lambda cmd: True)
    lines = iter(["Not a command !!", "Temperature: 19.25 C"])

    def _read(timeout_s=2.0):
        try:
            return next(lines)
        except StopIteration:
            return None

    monkeypatch.setattr(bridge, "read_line", _read)
    assert bridge.request_temperature() == 19.25


def test_set_bridge_injection():
    class Stub:
        def send_command(self, command: str) -> bool:
            return command == "LIGHT_ON"

        def request_temperature(self, timeout_s: float = 2.0):
            return 18.0

        def connect(self, port=None):
            return True

        def disconnect(self):
            return None

        def is_connected(self):
            return True

        def read_line(self, timeout_s: float = 2.0):
            return None

    serial_service.set_bridge(Stub())  # type: ignore[arg-type]
    try:
        assert serial_service.send_command("LIGHT_ON") is True
        assert serial_service.request_temperature() == 18.0
    finally:
        serial_service.set_bridge(None)
