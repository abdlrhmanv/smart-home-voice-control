import serial
import time

SERIAL_PORT = "COM3"
BAUD_RATE = 9600

arduino = None


def connect():
    global arduino

    try:
        arduino = serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=1
        )

        time.sleep(2)

        print("Arduino Connected")

    except Exception as e:
        print("Connection Error:", e)


def send_command(command):
    global arduino

    if arduino is None:
        connect()

    if arduino is not None:
        arduino.write((command + "\n").encode())
        print("Sent:", command)