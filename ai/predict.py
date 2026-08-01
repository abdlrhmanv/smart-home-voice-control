import sys
from pathlib import Path

# Add ml folder to Python path
ML_PATH = Path(__file__).resolve().parent.parent / "ml"

if str(ML_PATH) not in sys.path:
    sys.path.append(str(ML_PATH))

from src.application import SmartHomePipeline


# Create one pipeline instance
pipe = SmartHomePipeline.create_default()


def predict_voice(audio_path: str) -> dict:
    """
    Predict speaker and command from an audio file.

    Parameters
    ----------
    audio_path : str
        Path to wav file.

    Returns
    -------
    dict
        {
            "speaker": "...",
            "command": "...",
            "confidence": 98.2
        }
    """

    result = pipe.predict_voice_command(audio_path)

    return {
        "speaker": result.speaker,
        "command": result.command,
        "confidence": round(result.command_confidence * 100, 2)
    }


def verify_password(audio_path: str):
    """
    Verify password using Whisper.
    """

    return pipe.verify_password(audio_path)