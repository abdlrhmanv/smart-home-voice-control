"""Compatibility re-export — implementation lives in ``adapters.music``."""

from adapters.music import is_playing, start_music, stop_music

__all__ = ["is_playing", "start_music", "stop_music"]
