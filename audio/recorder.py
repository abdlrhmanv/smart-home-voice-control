import sounddevice as sd
from scipy.io.wavfile import write
from pathlib import Path

SAMPLE_RATE = 16000
DURATION = 3


def record_audio():
    """
    Record audio from microphone and save it as temp/input.wav
    """

    output_folder = Path("temp")
    output_folder.mkdir(exist_ok=True)

    filename = output_folder / "input.wav"

    print("Recording...")

    recording = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(filename, SAMPLE_RATE, recording)

    print("Recording Finished.")

    return str(filename)