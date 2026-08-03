"""Unit tests for upload helper and calibration store."""

from pathlib import Path

import pytest

from utils.uploads import UploadValidationError, save_uploaded_wav
from utils.calibration_store import load_calibration_report, reports_dir


class FakeUpload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def test_save_uploaded_wav(tmp_path):
    upload = FakeUpload("demo.wav", b"RIFF....")
    path = save_uploaded_wav(upload, dest_dir=tmp_path)
    assert Path(path).exists()
    assert Path(path).read_bytes() == b"RIFF...."
    assert Path(path).name.startswith("demo_")
    assert Path(path).name.endswith(".wav")


def test_save_uploaded_wav_rejects_non_wav(tmp_path):
    with pytest.raises(UploadValidationError):
        save_uploaded_wav(FakeUpload("bad.bin", b"not-a-wav"), dest_dir=tmp_path)


def test_save_uploaded_wav_rejects_empty(tmp_path):
    with pytest.raises(UploadValidationError):
        save_uploaded_wav(FakeUpload("empty.wav", b""), dest_dir=tmp_path)


def test_calibration_store_missing_ok():
    assert load_calibration_report("does_not_exist_task_xyz") is None
    assert reports_dir().name == "reports"
