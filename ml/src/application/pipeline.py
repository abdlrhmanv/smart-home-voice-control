"""Smart Home inference — depends only on ports, never sklearn."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from src.actions.command_actions import CommandActionMapper
from src.application.tasks import COMMAND_TASK, SPEAKER_TASK
from src.config import INFERENCE, InferenceConfig
from src.domain.labels import LabelMap
from src.domain.models import InferenceResult, Prediction
from src.infrastructure.librosa.feature_extractor import LibrosaFeatureExtractor
from src.infrastructure.persistence.model_loader import JoblibModelLoader
from src.infrastructure.whisper.transcriber import FasterWhisperTranscriber
from src.ports.classifier import Classifier
from src.ports.feature_extractor import FeatureExtractor
from src.ports.model_loader import ModelLoader
from src.ports.transcriber import SpeechTranscriber


def _predict_labeled(
    clf: Classifier, features: np.ndarray, labels: LabelMap
) -> Prediction:
    x = np.asarray(features, dtype=np.float32).reshape(1, -1)
    label_id = int(clf.predict(x)[0])
    conf = float(clf.predict_proba(x).max())
    return Prediction(name=labels.decode(label_id), label_id=label_id, confidence=conf)


class SmartHomePipeline:
    """
    Password STT → speaker → command → action mapping.

    Constructor takes ports only. ``create_default()`` is the composition root.
    """

    def __init__(
        self,
        speaker_clf: Classifier,
        command_clf: Classifier,
        feature_extractor: FeatureExtractor,
        transcriber: SpeechTranscriber,
        speaker_labels: LabelMap,
        command_labels: LabelMap,
        action_mapper: CommandActionMapper | None = None,
        password: str | None = None,
    ) -> None:
        self.speaker_clf = speaker_clf
        self.command_clf = command_clf
        self.features = feature_extractor
        self.transcriber = transcriber
        self.speaker_labels = speaker_labels
        self.command_labels = command_labels
        self.actions = action_mapper or CommandActionMapper()
        self.password = password if password is not None else INFERENCE.password

    @classmethod
    def create_default(
        cls,
        config: InferenceConfig | None = None,
        model_loader: ModelLoader | None = None,
    ) -> SmartHomePipeline:
        """Composition root — wires infrastructure adapters into this use-case."""
        cfg = config or INFERENCE
        loader = model_loader or JoblibModelLoader()
        return cls(
            speaker_clf=loader.load(SPEAKER_TASK),
            command_clf=loader.load(COMMAND_TASK),
            feature_extractor=LibrosaFeatureExtractor(),
            transcriber=FasterWhisperTranscriber(cfg),
            speaker_labels=SPEAKER_TASK.labels,
            command_labels=COMMAND_TASK.labels,
            password=cfg.password,
        )

    def reload(self, model_loader: ModelLoader | None = None) -> None:
        loader = model_loader or JoblibModelLoader()
        self.speaker_clf = loader.load(SPEAKER_TASK)
        self.command_clf = loader.load(COMMAND_TASK)

    def verify_password(self, audio_path: str | Path) -> InferenceResult:
        ok, transcript = self.transcriber.check_password(audio_path, self.password)
        if ok:
            return InferenceResult(
                password_ok=True,
                transcript=transcript,
                message="Password accepted. Red LED should turn ON.",
                action=self.actions.password_ok(),
            )
        return InferenceResult(
            password_ok=False,
            transcript=transcript,
            message="Wrong password. Please record again.",
            action=self.actions.password_fail(),
        )

    def predict_voice_command(self, audio_path: str | Path) -> InferenceResult:
        features = self.features.extract_from_file(audio_path)
        speaker = _predict_labeled(self.speaker_clf, features, self.speaker_labels)
        command = _predict_labeled(self.command_clf, features, self.command_labels)
        return InferenceResult(
            password_ok=True,
            transcript="",
            speaker=speaker.name,
            speaker_confidence=speaker.confidence,
            command=command.name,
            command_confidence=command.confidence,
            action=self.actions.map(command.name),
            message=(
                f"Detected {speaker.name} saying "
                f"'{command.name.replace('_', ' ')}'."
            ),
        )

    def run_full(
        self,
        password_audio: str | Path,
        command_audio: str | Path | None = None,
    ) -> InferenceResult:
        gate = self.verify_password(password_audio)
        if not gate.password_ok or command_audio is None:
            return gate
        result = self.predict_voice_command(command_audio)
        result.transcript = gate.transcript
        return result
