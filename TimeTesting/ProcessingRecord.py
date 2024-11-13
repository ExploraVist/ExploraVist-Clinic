import pyaudio 
import wave
import os
import requests
import numpy as np
import config


# The API key for Deepgram
DEEPGRAM_API_KEY = config.DEEPGRAM_API_KEY
FILE_PATH = "FIGUREITOUTTOMORROW"

def audio_to_text(file_path):
    url = "https://api.deepgram.com/v1/listen"

    # Open the audio file in binary mode
    with open(file_path, "rb") as audio_file:
        # Send the file for transcription
        response = requests.post(
            url,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav"  # Use "audio/mp3" for MP3 files
            },
            data=audio_file
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            if "results" in result and result["results"]["channels"][0]["alternatives"]:
                # Extract the transcript
                transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
                return transcript
            else:
                print("Error: No transcription found in the response.")
                return None
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

def main():

    # Initialize pyaudio
    p = pyaudio.PyAudio()
    audio_to_text()

if __name__ == '__main__':
    main()