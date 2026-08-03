from core.actions import (
    PASSWORD_FAIL_ACTION,
    PASSWORD_OK_ACTION,
    map_command,
)
from src.actions.command_actions import CommandActionMapper


def test_core_command_arduino_mapping():
    assert map_command("light_on")["arduino"] == "LIGHT_ON"
    assert map_command("light_off")["arduino"] == "LIGHT_OFF"
    assert map_command("music_on")["arduino"] == "MUSIC_ON"
    assert map_command("music_off")["arduino"] == "MUSIC_OFF"


def test_ml_mapper_shares_core_catalog():
    mapper = CommandActionMapper()
    assert mapper.map("light_on")["arduino"] == "LIGHT_ON"
    assert mapper.password_ok() == PASSWORD_OK_ACTION
    assert mapper.password_fail() == PASSWORD_FAIL_ACTION


def test_unknown_command_empty_action():
    assert map_command("dance") == {}
    assert CommandActionMapper().map("dance") == {}
