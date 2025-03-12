import pyaudio
import threading
import wave
import time
from time import sleep
import numpy as np
from picamera2 import Picamera2
from picamera2.previews import QtGlPreview
from libraries.metrics import timed
import os

class MediaDeviceManager:
    def __init__(self):
        # Initialize PyAudio and Picamera2
        self.p = pyaudio.PyAudio()
        self.camera = Picamera2()
        preview_config = self.camera.create_preview_configuration()
        self.camera.configure(preview_config)
        self.camera.set_controls({"AfMode": 2}) # Enable Continuous Autofocus
       # self.camera.start_preview(QtGlPreview())
        self.camera.start()
        
        # Audio parameters
        self.CHUNK = 44100
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.is_recording = False
        self.audio_thread = None
    
    def open(self):
        # Initialize PyAudio and Picamera2 if not already open
        if not self.p:
            self.p = pyaudio.PyAudio()
        if not self.camera:
            self.camera = Picamera2()
            self.camera.start()
        print("Resources opened.")

    def amplify_audio(self, input_filename, output_filename, gain=4):
        """
        Amplifies the audio in `input_filename` by the specified gain and saves it to `output_filename`.
        
        Parameters:
            input_filename (str): Path to the input audio file.
            output_filename (str): Path to save the amplified audio file.
            gain (int): The amplification factor to apply.
        """
        with wave.open(input_filename, "rb") as wav_in, wave.open(output_filename, "wb") as wav_out:
            params = wav_in.getparams()
            wav_out.setparams(params)
            frames = wav_in.readframes(params.nframes)
            audio_data = np.frombuffer(frames, dtype=np.int16)
            
            # Apply the gain and clip to prevent overflow
            audio_data = (audio_data * gain).clip(-32768, 32767).astype(np.int16)
            wav_out.writeframes(audio_data.tobytes())
        
        print(f"Amplified audio saved as {output_filename}")

    def start_recording(self, output_filename="audio/audio.wav"):
        # Ensure only one recording thread is running at a time
        temp_filename = "audio/temp_audio.wav"
        if self.is_recording:
            #print("Already recording!")
            return

        self.is_recording = True

        def record_audio():
            # Start the audio stream
            stream = self.p.open(format=self.FORMAT,
                                 channels=self.CHANNELS,
                                 rate=self.RATE,
                                 input=True,
                                 frames_per_buffer=self.CHUNK)

            frames = []
            print("Recording started...")

            while self.is_recording:
                data = stream.read(self.CHUNK)
                frames.append(data)

            print("Recording stopped.")
            stream.stop_stream()
            stream.close()

            # Save the recorded data as a WAV file
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(frames))
            
            # Amplify the audio after saving the initial recording
            self.amplify_audio(temp_filename, output_filename)

        # Run the audio recording in a separate thread
        self.audio_thread = threading.Thread(target=record_audio)
        self.audio_thread.start()

    def stop_recording(self):
        # Stop the recording and wait for the thread to finish
        self.is_recording = False
        if self.audio_thread:
            self.audio_thread.join()  # Ensure the recording thread completes

    @timed
    def capture_image(self, filename="images/temp_image.jpg"):
        
        # Capture an image with the Picamera2
        self.camera.capture_file(filename)
        print(f"Image captured as {filename}")
    
    def show_image(image_path):
        """Display the captured image using 'eog' (Eye of GNOME)."""
        os.system(f"eog {image_path}")

    def close(self):
        # Clean up resources
        if self.camera:
            self.camera.close()
            self.camera = None
        if self.p:
            self.p.terminate()
            self.p = None
        print("Resources closed.")
