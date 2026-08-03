"""Helpers for persisting uploaded WAV files for offline testing."""

from __future__ import annotations

import uuid
from pathlib import Path

# 10 MiB — enough for multi-second 16 kHz WAV, blocks abuse.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_WAV_MAGIC = b"RIFF"


class UploadValidationError(ValueError):
    """Raised when an uploaded file is not a plausible WAV."""


def save_uploaded_wav(upload, dest_dir: str | Path = "temp") -> str:
    """Write a Streamlit UploadedFile (or file-like) to a unique path; return it."""
    folder = Path(dest_dir)
    folder.mkdir(parents=True, exist_ok=True)

    data = upload.getvalue() if hasattr(upload, "getvalue") else upload.read()
    if not isinstance(data, (bytes, bytearray)):
        raise UploadValidationError("Upload payload must be bytes.")
    if len(data) == 0:
        raise UploadValidationError("Empty upload.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadValidationError(
            f"Upload exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MiB limit."
        )
    if not data.startswith(_WAV_MAGIC):
        raise UploadValidationError("File does not look like a WAV (missing RIFF header).")

    original = getattr(upload, "name", None) or "upload.wav"
    stem = Path(original).stem or "upload"
    # Unique name avoids cross-session overwrite in a shared Streamlit process.
    path = folder / f"{stem}_{uuid.uuid4().hex[:10]}.wav"
    path.write_bytes(data)
    return str(path)
