"""Trim, normalize, and quality-gate recorded audio."""

from __future__ import annotations

import numpy as np

from .. import config
from ..models import QualityReport


class AudioQualityGate:
    def __init__(
        self,
        sample_rate: int = config.SAMPLE_RATE,
        silence_top_db: float = config.SILENCE_TOP_DB,
        silence_pad_sec: float = config.SILENCE_PAD_SEC,
        rms_reject: float = config.RMS_REJECT_THRESHOLD,
        clip_threshold: float = config.CLIP_THRESHOLD,
    ) -> None:
        self.sample_rate = sample_rate
        self.silence_top_db = silence_top_db
        self.silence_pad_sec = silence_pad_sec
        self.rms_reject = rms_reject
        self.clip_threshold = clip_threshold

    def trim_silence(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio
        frame = max(1, int(0.02 * self.sample_rate))
        hop = max(1, frame // 2)
        if audio.size < frame:
            return audio

        energies = []
        for start in range(0, audio.size - frame + 1, hop):
            chunk = audio[start : start + frame]
            energies.append(np.sqrt(np.mean(chunk**2)))
        energies = np.asarray(energies, dtype=np.float64)
        peak = float(energies.max()) if energies.size else 0.0
        if peak <= 1e-9:
            return audio

        thresh = peak * (10.0 ** (-self.silence_top_db / 20.0))
        active = np.where(energies >= thresh)[0]
        if active.size == 0:
            return audio

        pad = int(self.silence_pad_sec * self.sample_rate)
        start_sample = max(0, active[0] * hop - pad)
        end_sample = min(audio.size, active[-1] * hop + frame + pad)
        return audio[start_sample:end_sample]

    @staticmethod
    def normalize_peak(audio: np.ndarray, target_peak: float = 0.9) -> np.ndarray:
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak < 1e-9:
            return audio
        return (audio * (target_peak / peak)).astype(np.float32)

    @staticmethod
    def to_int16(audio: np.ndarray) -> np.ndarray:
        clipped = np.clip(audio, -1.0, 1.0)
        return (clipped * 32767.0).astype(np.int16)

    def process(self, raw: np.ndarray) -> QualityReport:
        peak_raw = float(np.max(np.abs(raw))) if raw.size else 0.0
        rms_raw = float(np.sqrt(np.mean(raw**2))) if raw.size else 0.0
        clipped = peak_raw >= self.clip_threshold

        trimmed = self.trim_silence(raw)
        if trimmed.size == 0:
            return QualityReport(
                accepted=False,
                audio_int16=None,
                message="Recording is empty after silence trim. Please retry.",
                clipped=clipped,
                rms=rms_raw,
                peak=peak_raw,
            )

        rms_trim = float(np.sqrt(np.mean(trimmed**2)))
        if rms_trim < self.rms_reject:
            return QualityReport(
                accepted=False,
                audio_int16=None,
                message=(
                    f"Recording too quiet (RMS={rms_trim:.4f}). "
                    "Speak closer / louder, then retry."
                ),
                clipped=clipped,
                rms=rms_trim,
                peak=peak_raw,
            )

        pcm = self.to_int16(self.normalize_peak(trimmed))
        msg = "Saved successfully."
        if clipped:
            msg = (
                "Saved with clipping warning — mic input was too hot. "
                "Lower input gain if this repeats."
            )
        return QualityReport(
            accepted=True,
            audio_int16=pcm,
            message=msg,
            clipped=clipped,
            rms=rms_trim,
            peak=peak_raw,
        )
