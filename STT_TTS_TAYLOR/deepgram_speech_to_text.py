# deepgram_speech_to_text.py
import pyaudio 
import wave
import os
import requests
import numpy as np
import config
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

# The API key for Deepgram
DEEPGRAM_API_KEY = config.DEEPGRAM_API_KEY
# Define parameters for audio recording
CHUNK = 44100  # buffer size
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1  # mono recording
RATE = 44100  # sample rate
#CHANNELS = 2
#RATE = 48000
RECORD_SECONDS = 5  # duration of the recording
WAVE_OUTPUT_FILENAME = "/home/pi/Desktop/ExploraVist-Clinic/STT_TTS_TAYLOR/output.wav"  # output file name
WAVE_INPUT_FILENAME = "/home/pi/Desktop/ExploraVist-Clinic/STT_TTS_TAYLOR/output_louder.wav"
# Function to send audio file to Deepgram for transcription
def audio_to_text(file_path):
    url = "https://api.deepgram.com/v1/listen"

    # Open the audio file in binary mode
    with open(file_path, "rb") as audio_file:
        # Send the file for transcription
        response = requests.post(
            url,
            headers={
                "Authorization": "Token {DEEPGRAM_API_KEY}",
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
            print("Error: {response.status_code} - {response.text}")
            return None

def speech_to_text():
    # Initialize pyaudio
    p = pyaudio.PyAudio()
    #device_index = 1	
    # Start the audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
		#    input_device_index=device_index,
                    frames_per_buffer=CHUNK)

    print("Recording...")

    # Store audio data in frames
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
#print("File saved as {WAVE_OUTPUT_FILENAME}")

    try:
        while GPIO.input(22) == GPIO.LOW:  # Record while button is pressed
            data = stream.read(CHUNK)
            frames.append(data)
            print("recording")
    except Exception as e:
        print("Recording error:", e)
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


    with wave.open(WAVE_OUTPUT_FILENAME, "rb") as wav_in, wave.open(WAVE_INPUT_FILENAME, "wb") as wav_out:
    	params = wav_in.getparams()
    	wav_out.setparams(params)
    	frames = wav_in.readframes(params.nframes)
    	audio_data = np.frombuffer(frames, dtype=np.int16)
    	audio_data = (audio_data * 4).clip(-32768, 32767).astype(np.int16)  # Adjust multiplier for gain
    	wav_out.writeframes(audio_data.tobytes())


    if os.path.exists(WAVE_INPUT_FILENAME):
        print("Transcribing audio file: {WAVE_INPUT_FILENAME}")
        transcript = audio_to_text(WAVE_INPUT_FILENAME)
        if transcript:
            print("Transcription:", transcript)
        else:
            print("Failed to get transcription.")
    else:
        print("Error: Audio file {WAVE_INPUT_FILENAME} does not exist.")

    return transcript

def main():

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

    print("File saved as {WAVE_OUTPUT_FILENAME}")
    
    with wave.open(WAVE_OUTPUT_FILENAME, "rb") as wav_in, wave.open(WAVE_INPUT_FILENAME, "wb") as wav_out:
    	params = wav_in.getparams()
    	wav_out.setparams(params)
    	frames = wav_in.readframes(params.nframes)
    	audio_data = np.frombuffer(frames, dtype=np.int16)
    	audio_data = (audio_data * 4).clip(-32768, 32767).astype(np.int16)  # Adjust multiplier for gain
    	wav_out.writeframes(audio_data.tobytes())


    if os.path.exists(WAVE_INPUT_FILENAME):
        print("Transcribing audio file: {WAVE_INPUT_FILENAME}")
        transcript = audio_to_text(WAVE_INPUT_FILENAME)
        if transcript:
            print("Transcription:", transcript)
        else:
            print("Failed to get transcription.")
    else:
        print("Error: Audio file {WAVE_INPUT_FILENAME} does not exist.")

if __name__ == '__main__':
    main()
