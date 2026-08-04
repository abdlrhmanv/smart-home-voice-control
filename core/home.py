"""Home control use-case — auth, devices, temperature (no Streamlit)."""

from __future__ import annotations

from core.actions import PASSWORD_FAIL_ACTION, PASSWORD_OK_ACTION, arduino_for, known_commands
from core.ports import MusicPlayer, SerialPort, SessionStore


class AuthError(PermissionError):
    """Raised when a locked home is asked to run a control action."""


class HomeControlService:
    """Orchestrates serial + music + session flags for the smart home."""

    def __init__(
        self,
        store: SessionStore,
        serial: SerialPort,
        music: MusicPlayer,
        *,
        allow_offline: bool = True,
    ) -> None:
        self.store = store
        self.serial = serial
        self.music = music
        self.allow_offline = allow_offline

    def require_auth(self) -> None:
        if not self.store.is_authenticated():
            raise AuthError("Home is locked. Authenticate on the Password page first.")

    def _apply_flag(self, setter, value: bool, sent: bool) -> bool:
        if sent or self.allow_offline:
            setter(value)
            return True
        return False

    def unlock(self) -> bool:
        sent = self.serial.send_command(str(PASSWORD_OK_ACTION["arduino"]))
        self.store.set_arduino_synced(bool(sent))
        if sent or self.allow_offline:
            self.store.set_authenticated(True)
        return sent

    def lock(self) -> bool:
        self.music.stop()
        sent = self.serial.send_command(str(PASSWORD_FAIL_ACTION["arduino"]))
        self.store.set_authenticated(False)
        self.store.set_light(False)
        self.store.set_music(False)
        self.store.set_arduino_synced(False)
        return sent

    def turn_light_on(self) -> bool:
        self.require_auth()
        sent = self.serial.send_command(str(arduino_for("light_on")))
        return self._apply_flag(self.store.set_light, True, sent)

    def turn_light_off(self) -> bool:
        self.require_auth()
        sent = self.serial.send_command(str(arduino_for("light_off")))
        return self._apply_flag(self.store.set_light, False, sent)

    def turn_music_on(self) -> bool:
        self.require_auth()
        sent = self.serial.send_command(str(arduino_for("music_on")))
        ok = self._apply_flag(self.store.set_music, True, sent)
        if ok:
            self.music.start()
        return ok

    def turn_music_off(self) -> bool:
        self.require_auth()
        self.music.stop()
        sent = self.serial.send_command(str(arduino_for("music_off")))
        return self._apply_flag(self.store.set_music, False, sent)

    def execute_command(self, command: str) -> bool:
        self.require_auth()
        if command not in known_commands():
            raise ValueError(f"Unknown command: {command}")
        handlers = {
            "light_on": self.turn_light_on,
            "light_off": self.turn_light_off,
            "music_on": self.turn_music_on,
            "music_off": self.turn_music_off,
        }
        # Avoid double require_auth: call private body via mapped arduino + side effects
        return handlers[command]()

    def execute_action(self, action: dict) -> bool:
        """Dispatch from an ML action payload when present."""
        self.require_auth()
        arduino = action.get("arduino") if action else None
        if not arduino:
            return False
        reverse = {arduino_for(c): c for c in known_commands()}
        command = reverse.get(str(arduino))
        if command is None:
            # Password actions are not device commands
            return self.serial.send_command(str(arduino))
        return self.execute_command(command)

    def get_light(self) -> bool:
        return self.store.get_light()

    def get_music(self) -> bool:
        return self.store.get_music()

    def get_temperature(self, *, use_cache_on_failure: bool = False) -> float | None:
        self.require_auth()
        temp = self.serial.request_temperature()
        # USB reopen resets Ahmed's pass_corr — re-arm once if the first read fails.
        if temp is None:
            if self.serial.send_command(str(PASSWORD_OK_ACTION["arduino"])):
                self.store.set_arduino_synced(True)
                temp = self.serial.request_temperature()
        if temp is not None:
            self.store.set_temperature(temp, fresh=True)
            return temp
        # Keep last reading; only mark it as not fresh.
        self.store.set_temperature(self.store.get_temperature(), fresh=False)
        if use_cache_on_failure:
            return self.store.get_temperature()
        return None
