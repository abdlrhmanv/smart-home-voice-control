"""Filesystem dataset repository."""

from __future__ import annotations

from pathlib import Path

from src.domain.labels import AUDIO_EXTENSIONS, COMMAND_LABELS, SPEAKER_LABELS
from src.domain.models import AudioSample
from src.domain.paths import ProjectPaths


class FilesystemDatasetRepository:
    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root else ProjectPaths.from_package().dataset_dir

    def root(self) -> Path:
        return self._root

    def list_audio_files(self, directory: Path) -> list[Path]:
        if not directory.is_dir():
            return []
        return sorted(
            p for p in directory.rglob("*") if p.suffix.lower() in AUDIO_EXTENSIONS
        )

    def discover(self) -> list[AudioSample]:
        samples: list[AudioSample] = []
        for speaker in SPEAKER_LABELS.names():
            for command in COMMAND_LABELS.names():
                folder = self._root / speaker / command
                for path in self.list_audio_files(folder):
                    samples.append(
                        AudioSample(path=path, speaker=speaker, command=command)
                    )
        return samples
