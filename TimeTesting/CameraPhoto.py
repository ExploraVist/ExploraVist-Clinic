
import os
import base64
from openai import OpenAI
from picamera2 import Picamera2
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import pyaudio
import wave
import numpy as np

# API KEYS
import config


# Define parameters for audio recording
CHUNK = 44100  # buffer size
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1  # mono recording
RATE = 44100  # sample rate
RECORD_SECONDS = 5  # duration of the recording
WAVE_OUTPUT_FILENAME = "output.wav"  # output file name


# Set an environment variable
os.environ["OPENAI_API_KEY"] = config.GPT_API_KEY


def button_callback(channel):
    print("Button was pushed!")


GPIO.setwarnings(False)  # Ignore warning for now
GPIO.setmode(GPIO.BCM)  # Use physical pin numbering

# Set pin 22 to pull up (normally closed)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Set pin 27 to pull up (normally closed)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Initialize the OpenAI client
client = OpenAI()

PHOTO_PATH = "new_image.jpg"

# Function to process the text with GPT and return the response


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



def main():
    while True:  # Run forever
        if GPIO.input(22) == GPIO.LOW:
            picam2 = Picamera2()
            picam2.start()
            picam2.capture_file(PHOTO_PATH)
            picam2.close()


if __name__ == '__main__':
    main()
