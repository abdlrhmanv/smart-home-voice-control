"""Recorder-facing dataset repository (no ML domain imports)."""

from __future__ import annotations

from pathlib import Path

from . import config


class RecordingDatasetRepository:
    """
    UI → RecordingSession → RecordingDatasetRepository.

    Owns paths under ``data/dataset/<speaker>/<command>/``.
    """

    def __init__(
        self,
        speaker_name: str = config.SPEAKER_NAME,
        root: Path | None = None,
        recordings_per_command: int = config.RECORDINGS_PER_COMMAND,
        commands: list[tuple[str, str]] | None = None,
    ) -> None:
        self.speaker_name = speaker_name
        self.root = Path(root) if root else config.DATASET_ROOT
        self.recordings_per_command = recordings_per_command
        self.commands = commands or list(config.COMMANDS)
        self.speaker_dir = self.root / self.speaker_name

    def ensure_layout(self) -> None:
        for folder_name, _phrase in self.commands:
            (self.speaker_dir / folder_name).mkdir(parents=True, exist_ok=True)

    def command_dir(self, command_key: str) -> Path:
        return self.speaker_dir / command_key

    def wav_path(self, command_key: str, index: int) -> Path:
        return self.command_dir(command_key) / f"{command_key}_{index:03d}.wav"

    def existing_count(self, command_key: str) -> int:
        folder = self.command_dir(command_key)
        if not folder.is_dir():
            return 0
        return len(list(folder.glob(f"{command_key}_*.wav")))

    def total_expected(self) -> int:
        return len(self.commands) * self.recordings_per_command

    def total_recorded(self) -> int:
        return sum(self.existing_count(key) for key, _ in self.commands)

    def find_resume_position(self) -> tuple[int, int]:
        for cmd_i, (key, _) in enumerate(self.commands):
            count = self.existing_count(key)
            if count < self.recordings_per_command:
                return cmd_i, count + 1
        last = len(self.commands) - 1
        return last, self.recordings_per_command

    def is_complete(self) -> bool:
        return all(
            self.existing_count(key) >= self.recordings_per_command
            for key, _ in self.commands
        )


# Backwards-friendly alias used by session/app
DatasetStore = RecordingDatasetRepository
