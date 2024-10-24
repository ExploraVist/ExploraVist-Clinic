from deepgram_speech_to_text import audio_to_text
from deepgram_text_to_speech_test import text_to_speech  # Import the text-to-speech function
import os
import base64
from openai import OpenAI
from picamera2 import Picamera2

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

def process_image(image_path):
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
            "text": "What is in this image?",
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
    # Path to your audio file
    audio_file_path = "sample-3s.wav"
    picam2 = Picamera2()
    picam2.start()
    picam2.capture_file(PHOTO_PATH)
    picam2.close()
    if os.path.exists(audio_file_path):
        #print(f"Transcribing audio file: {audio_file_path}")
        #transcript = audio_to_text(audio_file_path)
        transcript = "hello, have a nice day!"
        if transcript:
            print("Transcription:", transcript)
            # Process the transcribed text using GPT
            gpt_response = process_text_with_gpt(transcript)
            
            if gpt_response:
                # Convert GPT response to speech using Deepgram TTS
                print(f"Converting GPT response to speech: {gpt_response}")
                text_to_speech(gpt_response)
                print(f"Processing Image:")
                image_response = process_image(PHOTO_PATH)
                print(image_response)
                print(f"Converting image response to speech:")
                text_to_speech(image_response)
            else:
                print("No GPT response available.")
        else:
            print("No transcription available.")
    else:
        print(f"Error: Audio file {audio_file_path} does not exist.")

if __name__ == '__main__':
    main()
