"""Dataset condition folder inference."""

from pathlib import Path

from src.infrastructure.filesystem.dataset_repo import FilesystemDatasetRepository


def test_condition_from_nested_folder(tmp_path):
    cmd = tmp_path / "ahmed" / "light_on"
    nested = cmd / "noise" / "light_on_001.wav"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"x")
    assert FilesystemDatasetRepository._condition_for(nested, cmd) == "noise"


def test_condition_default_for_flat_layout(tmp_path):
    cmd = tmp_path / "ahmed" / "light_on"
    flat = cmd / "light_on_001.wav"
    flat.parent.mkdir(parents=True)
    flat.write_bytes(b"x")
    assert FilesystemDatasetRepository._condition_for(flat, cmd) == "close"
