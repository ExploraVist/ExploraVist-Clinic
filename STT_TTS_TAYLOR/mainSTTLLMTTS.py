# mainSTTLLMTTS.py

# from deepgram_speech_to_text import speech_to_text
import deepgram_speech_to_text
from deepgram_text_to_speech_test import text_to_speech  # Import the text-to-speech function
import os
import base64
from openai import OpenAI
from picamera2 import Picamera2
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

# API KEYS
import config


# Set an environment variable
os.environ["OPENAI_API_KEY"] = config.GPT_API_KEY


def button_callback(channel):
	print("Button was pushed!")

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BCM) # Use physical pin numbering

GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 22 to pull up (normally closed)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 27 to pull up (normally closed)
# Initialize the OpenAI client
client = OpenAI()

PHOTO_PATH = "new_image.jpg"

# Function to process the text with GPT and return the response
def process_text_with_gpt(transcript):
    if transcript:
        # Send the transcript to OpenAI GPT model
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": transcript}
            ]
        )

        # Extract the GPT response content
        response = completion.choices[0].message.content
        print("GPT-4 Response:", response)
        return response
    return None

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
	while True: # Run forever
	    if GPIO.input(22) == GPIO.LOW:
		    # Path to your audio file
		    picam2 = Picamera2()
		    picam2.start()
		    picam2.capture_file(PHOTO_PATH)
		    picam2.close()
		    #print(f"Transcribing audio file: {audio_file_path}")
		    #transcript = audio_to_text(audio_file_path)
		    transcript = "what do you see in front of me?"
		    #transcript = deepgram_speech_to_text.speech_to_text()
            # transcript = deepgram_speech_to_text.speech_to_text()
            # transcript = ""
            # transcript = deepgram_speech_to_text.speech_to_text()
		    if transcript:
		        print("Transcription:", transcript)
		        # Process the transcribed text using GPT
		        #gpt_response = process_text_with_gpt(transcript)    
		        #if gpt_response:
		                # Convert GPT response to speech using Deepgram TTS
		            #print(f"Converting GPT response to speech: {gpt_response}")
		            #text_to_speech(gpt_response)
		            #print(f"Processing Image:")
		            #image_response = process_image(PHOTO_PATH)
		            #print(image_response)
		            #print(f"Converting image response to speech:")
		            #text_to_speech(image_response)
		        #else:
		            #print("No GPT response available.")
		        image_response = process_image(PHOTO_PATH, transcript)
		        print(image_response)
		        print(f"Converting image response to speech:")
		        text_to_speech(image_response)
		    else:
		        print("No transcription available.")
if __name__ == '__main__':
    main()
