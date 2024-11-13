import pyaudio
import wave
import numpy as np
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
with wave.open("output.wav", "rb") as wav_in, wave.open("output_louder.wav", "wb") as wav_out:
    params = wav_in.getparams()
    wav_out.setparams(params)
    frames = wav_in.readframes(params.nframes)
    audio_data = np.frombuffer(frames, dtype=np.int16)
    audio_data = (audio_data * 4).clip(-32768, 32767).astype(np.int16)  # Adjust multiplier for gain
    wav_out.writeframes(audio_data.tobytes())
