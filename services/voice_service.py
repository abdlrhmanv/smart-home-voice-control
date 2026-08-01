from audio.recorder import record_audio

from ai.predict import predict_voice

from utils.data import set_recognition_result

from services.device_service import (
    turn_light_on,
    turn_light_off,
    turn_music_on,
    turn_music_off
)


def start_listening():
    """
    Main Voice Workflow
    """

    # ============================
    # Step 1 : Record Audio
    # ============================

    audio_path = record_audio()

    # ============================
    # Step 2 : AI Prediction
    # ============================

    result = predict_voice(audio_path)

    user = result["speaker"]
    command = result["command"]
    confidence = result["confidence"]

    # ============================
    # Step 3 : Save Result
    # ============================

    set_recognition_result(
        user,
        command,
        confidence
    )

    # ============================
    # Step 4 : Execute Command
    # ============================

    if command == "light_on":
        turn_light_on()

    elif command == "light_off":
        turn_light_off()

    elif command == "music_on":
        turn_music_on()

    elif command == "music_off":
        turn_music_off()

    # ============================
    # Step 5 : Return Result
    # ============================

    return result