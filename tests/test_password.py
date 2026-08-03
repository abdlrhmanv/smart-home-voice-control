from src.infrastructure.whisper.transcriber import FasterWhisperTranscriber


def test_normalize_strips_punctuation():
    assert FasterWhisperTranscriber.normalize_text("  Open, Sesame!! ") == "open sesame"


def test_normalize_collapses_whitespace():
    assert FasterWhisperTranscriber.normalize_text("open   sesame") == "open sesame"


class FakeTranscriber:
    def __init__(self, text: str):
        self.text = text

    def check_password(self, audio_path, expected):
        heard = FasterWhisperTranscriber.normalize_text(self.text)
        return heard == FasterWhisperTranscriber.normalize_text(expected), heard


def test_wrong_password_fails():
    t = FakeTranscriber("wrong phrase")
    ok, heard = t.check_password("x.wav", "open sesame")
    assert ok is False
    assert heard == "wrong phrase"


def test_correct_password_passes():
    t = FakeTranscriber("Open Sesame.")
    ok, heard = t.check_password("x.wav", "open sesame")
    assert ok is True
    assert heard == "open sesame"
