import pyaudio 
import wave
import os
import requests




# The API key for Deepgram
DEEPGRAM_API_KEY = ''
# Define parameters for audio recording
CHUNK = 44100  # buffer size
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1  # mono recording
RATE = 44100  # sample rate
RECORD_SECONDS = 5  # duration of the recording
WAVE_OUTPUT_FILENAME = "output.wav"  # output file name

# Function to send audio file to Deepgram for transcription
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
    
    if os.path.exists(WAVE_OUTPUT_FILENAME):
        print(f"Transcribing audio file: {WAVE_OUTPUT_FILENAME}")
        transcript = audio_to_text(WAVE_OUTPUT_FILENAME)
        if transcript:
            print("Transcription:", transcript)
        else:
            print("Failed to get transcription.")
    else:
        print(f"Error: Audio file {WAVE_OUTPUT_FILENAME} does not exist.")

if __name__ == '__main__':
    main()
