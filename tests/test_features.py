import numpy as np

from src.infrastructure.librosa.feature_extractor import LibrosaFeatureExtractor


def test_feature_vector_shape(tmp_wav):
    feats = LibrosaFeatureExtractor().extract_from_file(tmp_wav)
    assert feats.ndim == 1
    # 40 MFCC + 12 chroma + 7 contrast + 1 zcr + 1 rms → mean+std = 122
    assert feats.shape[0] == 122
    assert np.isfinite(feats).all()


def test_command_features_include_deltas(tmp_wav):
    feats = LibrosaFeatureExtractor(include_deltas=True).extract_from_file(tmp_wav)
    # base 122 + delta MFCC 80 + delta-delta 80
    assert feats.shape[0] == 282
    assert np.isfinite(feats).all()


def test_empty_audio_returns_zeros(empty_wav):
    feats = LibrosaFeatureExtractor().extract_from_file(empty_wav)
    assert feats.shape[0] == 122
