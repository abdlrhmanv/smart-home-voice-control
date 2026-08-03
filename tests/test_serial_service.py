from api import serial_service


def test_send_command_without_port_returns_false(monkeypatch):
    monkeypatch.setattr(serial_service, "DEFAULT_PORT", "")
    monkeypatch.setattr(serial_service, "_arduino", None)
    monkeypatch.setattr(serial_service, "resolve_port", lambda: None)
    assert serial_service.send_command("LIGHT_ON") is False


def test_request_temperature_parses_line(monkeypatch):
    monkeypatch.setattr(serial_service, "send_command", lambda cmd: True)
    monkeypatch.setattr(
        serial_service, "read_line", lambda timeout_s=2.0: "Temperature: 24.5 C"
    )
    assert serial_service.request_temperature() == 24.5


def test_request_temperature_accepts_legacy_typo(monkeypatch):
    monkeypatch.setattr(serial_service, "send_command", lambda cmd: True)
    monkeypatch.setattr(
        serial_service, "read_line", lambda timeout_s=2.0: "Tempratute: 21.0 C"
    )
    assert serial_service.request_temperature() == 21.0
