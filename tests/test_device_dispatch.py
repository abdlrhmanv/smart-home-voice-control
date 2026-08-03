"""Unit tests for device command dispatch (no Streamlit session required for mapper)."""

from services.device_service import execute_command


def test_unknown_command_raises():
    try:
        execute_command("fly_away")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Unknown command" in str(exc)
