from src.actions.command_actions import CommandActionMapper


def test_command_arduino_mapping():
    mapper = CommandActionMapper()
    assert mapper.map("light_on")["arduino"] == "LIGHT_ON"
    assert mapper.map("light_off")["arduino"] == "LIGHT_OFF"
    assert mapper.map("music_on")["arduino"] == "MUSIC_ON"
    assert mapper.map("music_off")["arduino"] == "MUSIC_OFF"


def test_password_actions():
    mapper = CommandActionMapper()
    assert mapper.password_ok()["arduino"] == "PASSWORD_OK"
    assert mapper.password_fail()["arduino"] == "PASSWORD_FAIL"


def test_unknown_command_empty_action():
    assert CommandActionMapper().map("dance") == {}
