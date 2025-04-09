import os
import threading
import subprocess  # Using arecord via subprocess
import wave
import time
from time import sleep
import numpy as np
from picamera2 import Picamera2
from picamera2.previews import QtGlPreview
from libraries.metrics import timed

class MediaDeviceManager:
    def __init__(self):
        # Initialize Picamera2
        self.camera = Picamera2()
        preview_config = self.camera.create_preview_configuration()
        self.camera.configure(preview_config)
        self.camera.set_controls({"AfMode": 2})  # Enable Continuous Autofocus
        # self.camera.start_preview(QtGlPreview())
        self.camera.start()
        
        # Audio parameters for arecord:
        self.CHUNK = 44100      # Not used by arecord, kept for compatibility
        self.FORMAT = "S32_LE"   # Using S32_LE (32-bit) as per your working command
        self.CHANNELS = 1       # Mono recording
        self.RATE = 48000       # Sample rate: 48000 Hz
        self.is_recording = False
        self.audio_thread = None
        self.audio_process = None  # Will hold the subprocess.Popen instance

    def open(self):
        # Initialize resources if not already open
        if not self.camera:
            self.camera = Picamera2()
            self.camera.start()
        print("Resources opened.")

    def amplify_audio(self, input_filename, output_filename, gain=4):
        """
        Amplifies the audio in `input_filename` by the specified gain and saves it to `output_filename`.
        """
        with wave.open(input_filename, "rb") as wav_in, wave.open(output_filename, "wb") as wav_out:
            params = wav_in.getparams()
            wav_out.setparams(params)
            frames = wav_in.readframes(params.nframes)
            # Choose correct numpy dtype based on sample width:
            if params.sampwidth == 2:
                dtype = np.int16
            elif params.sampwidth == 4:
                dtype = np.int32
            else:
                dtype = np.int16
            audio_data = np.frombuffer(frames, dtype=dtype)
            
            # Calculate limits based on sample width
            max_val = 2 ** (8 * params.sampwidth - 1) - 1
            min_val = -2 ** (8 * params.sampwidth - 1)
            audio_data = (audio_data * gain).clip(min_val, max_val).astype(dtype)
            wav_out.writeframes(audio_data.tobytes())
        
        print(f"Amplified audio saved as {output_filename}")

    def start_recording(self, output_filename="audio/audio.wav"):
        """
        Starts recording audio using the arecord command.
        Audio is temporarily saved to 'audio/temp_audio.wav', then amplified and saved to output_filename.
        """
        os.makedirs("audio", exist_ok=True)
        temp_filename = "audio/temp_audio.wav"
        if self.is_recording:
            return

        self.is_recording = True

        def record_audio():
            # The following are the parameters that worked for you:
            # arecord -D plughw:0 -c1 -r 48000 -f S32_LE -t wav -V mono -v file.wav
            cmd = [
                "arecord",
                "-D", "plughw:0",
                "-c", str(self.CHANNELS),
                "-r", str(self.RATE),
                "-f", self.FORMAT,
                "-t", "wav",
                "-V", "mono",
                "-v",
                temp_filename
            ]
            print("Recording started using arecord...")
            self.audio_process = subprocess.Popen(cmd)
            while self.is_recording:
                sleep(0.1)
            self.audio_process.terminate()
            self.audio_process.wait()
            print("Recording stopped.")
            if not os.path.exists(temp_filename):
                print(f"Error: {temp_filename} was not created.")
                return
            self.amplify_audio(temp_filename, output_filename)

        self.audio_thread = threading.Thread(target=record_audio)
        self.audio_thread.start()

    def stop_recording(self):
        # Stop the recording and wait for the thread to finish.
        self.is_recording = False
        if self.audio_thread:
            self.audio_thread.join()

    @timed
    def capture_image(self, filename="images/temp_image.jpg"):
        # Capture an image with the Picamera2
        self.camera.capture_file(filename)
        print(f"Image captured as {filename}")

    def close(self):
        # Clean up resources
        if self.camera:
            self.camera.close()
            self.camera = None
        print("Resources closed.")
