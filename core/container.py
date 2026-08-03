"""Composition root — wires adapters into application services."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from adapters.audio_input import MicrophoneRecorder
from adapters.ml_gateway import MlVoiceGateway
from adapters.music import _default_player
from adapters.session_store import StreamlitSessionStore
from api.serial_service import BAUD_RATE, get_bridge
from core.home import HomeControlService
from core.password import PasswordService
from core.ports import AudioRecorder, MusicPlayer, SerialPort, SessionStore, VoiceGateway
from core.settings import SettingsService
from core.voice import VoiceControlService


@dataclass
class AppContainer:
    store: SessionStore
    serial: SerialPort
    music: MusicPlayer
    voice_gateway: VoiceGateway
    recorder: AudioRecorder
    home: HomeControlService
    password: PasswordService
    voice: VoiceControlService
    settings: SettingsService


_container: AppContainer | None = None


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def build_container(
    *,
    store: SessionStore | None = None,
    serial: SerialPort | None = None,
    music: MusicPlayer | None = None,
    voice_gateway: VoiceGateway | None = None,
    recorder: AudioRecorder | None = None,
    allow_offline: bool | None = None,
) -> AppContainer:
    offline = (
        os.environ.get("ALLOW_OFFLINE_CONTROL", "1") == "1"
        if allow_offline is None
        else allow_offline
    )
    store = store or StreamlitSessionStore()
    serial = serial or get_bridge()
    music = music or _default_player
    voice_gateway = voice_gateway or MlVoiceGateway()
    recorder = recorder or MicrophoneRecorder()
    home = HomeControlService(
        store=store, serial=serial, music=music, allow_offline=offline
    )
    return AppContainer(
        store=store,
        serial=serial,
        music=music,
        voice_gateway=voice_gateway,
        recorder=recorder,
        home=home,
        password=PasswordService(voice_gateway, recorder, home),
        voice=VoiceControlService(voice_gateway, recorder, home),
        settings=SettingsService(
            serial, baud_rate=BAUD_RATE, project_root=_project_root()
        ),
    )


def get_container() -> AppContainer:
    global _container
    if _container is None:
        _container = build_container()
    return _container


def set_container(container: AppContainer | None) -> None:
    """Replace the process-wide container (tests)."""
    global _container
    _container = container


def reset_container() -> None:
    set_container(None)


def get_home() -> HomeControlService:
    return get_container().home
