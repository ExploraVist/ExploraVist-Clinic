# from deepgram_speech_to_text import speech_to_text
from deepgram_speech_to_text import audio_to_text
# Import the text-to-speech function
from deepgram_text_to_speech_test import text_to_speech
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


def processAudio():
    # Initialize pyaudio
    p = pyaudio.PyAudio()

# Start the audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")

# Store audio data in frames
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete")

# Stop and close the audio stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the audio data as a .wav file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"File saved as {WAVE_OUTPUT_FILENAME}")
    with wave.open("output.wav", "rb") as wav_in, wave.open("output_louder.wav", "wb") as wav_out:
        params = wav_in.getparams()
        wav_out.setparams(params)
        frames = wav_in.readframes(params.nframes)
        audio_data = np.frombuffer(frames, dtype=np.int16)
        # Adjust multiplier for gain
        audio_data = (audio_data * 4).clip(-32768, 32767).astype(np.int16)
        wav_out.writeframes(audio_data.tobytes())


def main():
    while True:  # Run forever
        if GPIO.input(22) == GPIO.LOW:
            processAudio()
            picam2 = Picamera2()
            picam2.start()
            picam2.capture_file(PHOTO_PATH)
            picam2.close()
          #print(f"Transcribing audio file: {audio_file_path}")
          #transcript = audio_to_text(audio_file_path)
          # transcript = "what is shown in this image?"
            transcript = audio_to_text(WAVE_OUTPUT_FILENAME)
        # transcript = deepgram_speech_to_text.speech_to_text()
        # transcript = ""
        # transcript = deepgram_speech_to_text.speech_to_text()
            if transcript:
                print("Transcription:", transcript)
                # Process the transcribed text using GPT
                #gpt_response = process_text_with_gpt(transcript)
                # if gpt_response:
                  # Convert GPT response to speech using Deepgram TTS
                #print(f"Converting GPT response to speech: {gpt_response}")
                # text_to_speech(gpt_response)
                #print(f"Processing Image:")
                #image_response = process_image(PHOTO_PATH)
                # print(image_response)
                #print(f"Converting image response to speech:")
                # text_to_speech(image_response)
                # else:
                #print("No GPT response available.")
                image_response = process_image(PHOTO_PATH, transcript)
                print(f"Converting image response to speech:")
                text_to_speech(image_response)
            else:
                print("No transcription available.")


if __name__ == '__main__':
    main()
