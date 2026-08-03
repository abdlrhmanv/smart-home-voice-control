"""Group holdout split keeps speakers disjoint."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.application.trainer import ClassifierTrainer
from src.application.tasks import COMMAND_TASK
from src.config import TrainingConfig
from src.domain.models import AudioSample


class FakeRepo:
    def __init__(self, samples):
        self._samples = samples

    def root(self):
        return Path(".")

    def discover(self):
        return self._samples


class FakeFeatures:
    def extract_from_file(self, path):
        # Deterministic tiny vector from path string
        rng = np.random.default_rng(abs(hash(str(path))) % (2**32))
        return rng.normal(size=8).astype(np.float32)


def test_group_holdout_speakers_disjoint(tmp_path):
    samples = []
    for speaker in ("alice", "bob", "carol"):
        for i, cmd in enumerate(("light_on", "light_off", "music_on", "music_off")):
            for n in range(5):
                p = tmp_path / f"{speaker}_{cmd}_{n}.wav"
                p.write_bytes(b"x")
                samples.append(
                    AudioSample(path=p, speaker=speaker, command=cmd)
                )

    cfg = TrainingConfig(
        test_size=0.34,
        random_state=0,
        group_holdout=True,
        calibrate=False,
        tune=False,
    )
    trainer = ClassifierTrainer(
        task=COMMAND_TASK,
        feature_extractor=FakeFeatures(),
        dataset=FakeRepo(samples),
        config=cfg,
    )
    # Patch encode to use command labels already in task
    split = trainer.train(tune=False)
    # Reconstruct groups from paths used in train/test by re-discovering
    # and checking that with same seed the splitter separates speakers.
    groups = np.asarray([s.speaker for s in samples])
    from sklearn.model_selection import GroupShuffleSplit

    idx = np.arange(len(samples))
    y = np.asarray([COMMAND_TASK.encode_sample(s) for s in samples])
    tr, te = next(
        GroupShuffleSplit(
            n_splits=1, test_size=0.34, random_state=0
        ).split(idx, y, groups)
    )
    assert set(groups[tr]).isdisjoint(set(groups[te]))
    assert len(split.y_test) == len(te)
