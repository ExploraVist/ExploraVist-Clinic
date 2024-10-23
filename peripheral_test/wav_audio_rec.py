import pyaudio
import wave

# Define parameters for audio recording
CHUNK = 44100  # buffer size
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1  # mono recording
RATE = 44100  # sample rate
RECORD_SECONDS = 5  # duration of the recording
WAVE_OUTPUT_FILENAME = "output.wav"  # output file name

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
