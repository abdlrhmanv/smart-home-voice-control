from audio.recorder import record_audio
from ai.predict import verify_password


def authenticate():

    audio_path = record_audio()

    result = verify_password(audio_path)

    return result