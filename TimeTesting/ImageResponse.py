import os
import base64
from openai import OpenAI
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import pyaudio
import wave
import numpy as np

# API KEYS
import config


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

PHOTO_PATH = "taylorlevinson/Downloads/EEEEE.jpg"

# Function to process the text with GPT and return the response



def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def process_image(image_path, transcript):
    # Path to your image
    # Getting the base64 string
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": transcript,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":  f"data:image/jpeg;base64,{base64_image}"
                            },
                    },
                ],
            }
        ],
    )

    message_content = response.choices[0].message.content
    return(message_content)


def main():
    while True:  # Run forever
        if GPIO.input(22) == GPIO.LOW:
            image_response = process_image(PHOTO_PATH, "what is in this image?")
            print(image_response)



if __name__ == '__main__':
    main()
