from src.domain.labels import COMMAND_LABELS, COMMAND_PHRASES, SPEAKER_LABELS


def test_speaker_labels_roundtrip():
    for name in SPEAKER_LABELS.names():
        assert SPEAKER_LABELS.decode(SPEAKER_LABELS.encode(name)) == name


def test_command_labels_match_phrases():
    keys = {k for k, _ in COMMAND_PHRASES}
    assert keys == set(COMMAND_LABELS.names())


def test_unknown_label_raises():
    try:
        SPEAKER_LABELS.encode("unknown_person")
        assert False, "expected KeyError"
    except KeyError:
        pass
