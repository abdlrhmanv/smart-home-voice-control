import numpy as np
import pytest

from src.application.tasks import COMMAND_TASK
from src.application.trainer import ClassifierTrainer
from src.domain.models import AudioSample


class OneClassRepo:
    def discover(self):
        return [
            AudioSample(path=f"/tmp/{i}.wav", speaker="ahmed", command="light_on")
            for i in range(10)
        ]

    def root(self):
        return "/tmp"


class FakeExtractor:
    def extract_from_file(self, path):
        return np.zeros(122, dtype=np.float32)


def test_command_trainer_rejects_single_class():
    trainer = ClassifierTrainer(
        task=COMMAND_TASK,
        feature_extractor=FakeExtractor(),
        dataset=OneClassRepo(),
    )
    with pytest.raises(ValueError, match="needs ≥2 classes"):
        trainer.train(tune=False)
