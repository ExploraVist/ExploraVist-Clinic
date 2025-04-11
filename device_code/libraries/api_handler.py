import os
from openai import OpenAI
import base64
import requests
import subprocess
import RPi.GPIO as GPIO
import time

import re
from pathlib import Path
import threading
import queue
import time
import random

from libraries.metrics import timed
import re
import sounddevice as sd
import numpy as np
import websocket
import json
import threading
import time
from scipy.signal import resample

from PIL import Image
from functools import lru_cache


def encode_image(image_path):
        with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')



def segment_text_by_sentence(text):
    """
    Splits `text` into segments (sentences) by looking for punctuation followed by whitespace.
    """
    sentence_boundaries = re.finditer(r'(?<=[.!?])\s+', text)
    boundaries_indices = [boundary.start() for boundary in sentence_boundaries]
    
    segments = []
    start = 0
    for boundary_index in boundaries_indices:
        segments.append(text[start:boundary_index + 1].strip())
        start = boundary_index + 1
    # Append the last segment
    segments.append(text[start:].strip())

    return segments


class APIHandler:
    #TODO incorporate a requests.Session() for Keep-Alive, Ex:
    # self.session = requests.Session()  # Use a session for keep-alive
    #   self.session.headers.update({
    #       "Authorization": f"Token {self.DEEPGRAM_API_KEY}",
    #       "Content-Type": "audio/wav"  # Set content type for the session
    #   })
    # self.url = "https://api.deepgram.com/v1/listen"

        def __init__(self, config):
                self.DEEPGRAM_API_KEY = config["DEEPGRAM_API_KEY"]
        # Set an environment variable
                os.environ["OPENAI_API_KEY"] = config["GPT_API_KEY"]
                self.client = OpenAI()
                self.canceled = 0
                self.session = requests.Session()
                self.session.headers.update({
                        "Authorization": f"Token {self.DEEPGRAM_API_KEY}",
                        "Content-Type": "text/plain"
                })
        
        def stream_wav_file_to_deepgram(self, wav_path="audio/audio.wav"):

                DG_URL = "wss://api.deepgram.com/v1/listen?punctuate=true"
                header = [f"Authorization: Token {self.DEEPGRAM_API_KEY}"]

                def on_open(ws):
                        print("Streaming WAV file...")
                        wf = wave.open(wav_path, 'rb')

                        def send_chunks():
                                try:
                                        chunk_size = 1024
                                        frame_rate = wf.getframerate()

                                        while True:
                                                data = wf.readframes(chunk_size)
                                                if not data:
                                                        break
                                                ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

                                                if simulate_realtime:
                                                        time.sleep(chunk_size / frame_rate)

                                        print("✅ Finished streaming WAV file")
                                        ws.close()

                                except Exception as e:
                                        print("Error sending audio:", e)

                        threading.Thread(target=send_chunks, daemon=True).start()

                def on_message(ws, message):
                        try:
                                msg = json.loads(message)
                                transcript = msg.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                                if transcript:
                                        print("🗣️", transcript)
                        except Exception as e:
                                print("Error parsing transcript:", e)


                def on_close(ws, code, reason):
                        print("Connection closed")

                websocket.enableTrace(False)
                ws = websocket.WebSocketApp(
                        DG_URL,
                        header=header,
                        on_open=on_open,
                        on_message=on_message,
                        on_close=on_close
                )
                ws.run_forever()

        def text_to_speech(self, text):
                """
                Converts text to speech using the Deepgram TTS API and saves the audio file.

                Parameters:
                        text (str): Text to be converted to speech.
                Returns:
                        str: Path to the converted audio file, or None if conversion fails
                """
                temp_time = time.time()
                start_time = time.time()
                url = "https://api.deepgram.com/v1/speak"

                try:
                        # Send the request to Deepgram's TTS API
                        response = self.session.post(url, data=text.encode('utf-8'))
                        response.raise_for_status()

                        # print(f"API Request Time: {time.time() - temp_time:.2f} seconds")
                        # temp_time = time.time()

                        # Save the response audio to a file
                        temp_file = "audio/audio.wav"
                        with open(temp_file, "wb") as audio_file:
                                audio_file.write(response.content)

                        # print(f"File Save Time: {time.time() - temp_time:.2f} seconds")
                        # temp_time = time.time()

                        # Convert and amplify the audio file
                        converted_file = "audio/converted_response.wav"
                        temp_amplified_file = "audio/temp_amplified.wav"
                        conversion_command = [
                                "ffmpeg", "-y", "-i", temp_file, "-ar", "44100", "-ac", "1", converted_file
                        ]
                        amplification_command = [
                                "ffmpeg", "-y", "-i", converted_file, "-filter:a", "volume=3", temp_amplified_file
                        ]

                        try:
                                subprocess.run(conversion_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True) # Convert the audio file
                                
                                # print(f"Audio Conversion Time: {time.time() - temp_time:.2f} seconds")
                                # temp_time = time.time()

                                subprocess.run(amplification_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True) # Amplify the audio file
                                os.replace(temp_amplified_file, converted_file) # Rename the amplified file to the converted file

                                os.remove(temp_file) # Remove the temporary file
                                return converted_file

                        except subprocess.CalledProcessError as e:
                                print(f"Error during audio processing: {e}")
                                return None

                except requests.exceptions.RequestException as e:
                        print(f"Error during request: {e}")
                        return None
        
        @staticmethod
        def split_text(text, max_length=200):
        # Naive sentence-based splitter with length control
                sentences = re.split(r'(?<=[.!?])\s+', text)
                chunks = []
                current_chunk = ""

                for sentence in sentences:
                        if len(current_chunk) + len(sentence) <= max_length:
                                current_chunk += " " + sentence
                        else:
                                if current_chunk:
                                        chunks.append(current_chunk.strip())
                                        current_chunk = sentence
                if current_chunk:
                        chunks.append(current_chunk.strip())
                return chunks 

        def play_audio(self, audio_file="audio/converted_response.wav"):
                """
                Plays the converted audio file and monitors for cancellation.

                Parameters:
                        audio_file (str): Path to the audio file to play
                """
                if not os.path.exists(audio_file):
                        print(f"Error: Audio file not found: {audio_file}")
                        return

                print("Audio data received successfully. Playing audio...")
                # temp_time = time.time()
                
                audio_process = subprocess.Popen(["aplay", audio_file])

                # Monitor GPIO 22 to cancel playback
                while audio_process.poll() is None:
                        if GPIO.input(22) == GPIO.LOW or GPIO.input(27) == GPIO.LOW:  # Button is pressed
                                print("Button pressed, stopping audio playback.")
                                audio_process.terminate()
                                self.canceled = 1
                                break
                        time.sleep(0.1)  # Check every 100ms
                audio_process.wait()

                # print(f"Playback Time: {time.time() - temp_time:.2f} seconds")
                # print("Playback finished.")

                # Only delete the file if it's a temporary response file
                if "converted_response.wav" in audio_file:
                    os.remove(audio_file)
        
        def stream_tts_and_play(self, text):
                url = "https://api.deepgram.com/v1/speak"
                headers = {
                "Authorization": f"Token {self.DEEPGRAM_API_KEY}",
                "Accept": "audio/mpeg"
                }

                if len(text) <= 200:  # or adjust threshold based on performance        
                        self._process_and_play_single_chunk(text)
                        return
                chunks = self.split_text(text)
                Path("audio").mkdir(exist_ok=True)
                q = queue.Queue()
                self.canceled = 0

                intro_choices = {
                        1: "audio_files/thinking.wav",
                        2: "audio_files/letssee.wav",
                        3: "audio_files/almostthere.wav"
                }

                choice = random.choice([1, 2, 3, 4, 5, 6])
                if choice in intro_choices:
                        threading.Thread(
                        target=self.play_audio,
                        args=(intro_choices[choice],),
                        daemon=True
                ).start()

                def producer():
                        for i, chunk in enumerate(chunks):
                                if self.canceled:
                                        break
                                wav_path = f"audio/chunk_{i}.wav"
                                try:
                                        with self.session.post(url, headers=headers, data=chunk.encode("utf-8"), stream=True) as response:
                                                response.raise_for_status()
                                                ffmpeg_process = subprocess.Popen([
                                                        "ffmpeg", "-y", "-threads", "1",
                                                        "-f", "mp3", "-i", "pipe:0",
                                                        wav_path
                                                ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                                                for audio_chunk in response.iter_content(chunk_size=2048):
                                                        if audio_chunk:
                                                                ffmpeg_process.stdin.write(audio_chunk)

                                                ffmpeg_process.stdin.close()
                                                ffmpeg_process.wait()

                                        q.put(wav_path)
                                except requests.RequestException as e:
                                        print(f"Chunk {i} failed: {e}")
                                        continue

                        q.put(None)  # Sentinel

                def consumer():
                        while True:
                                wav_path = q.get()
                                if wav_path is None:
                                        break
                                self._play_chunk(wav_path)

                threading.Thread(target=producer, daemon=True).start()
                consumer()  # This stays in the main thread so it can monitor GPIO

        def _play_chunk(self, wav_path):
                print(f"Playing {wav_path}...")
                if not os.path.exists(wav_path):
                        print(f"Error: {wav_path} not found.")
                        return

                audio_process = subprocess.Popen(["aplay", "-q", wav_path])
                while audio_process.poll() is None:
                        # GPIO cancel check could be added here
                        time.sleep(0.1)
                audio_process.wait()
                os.remove(wav_path)

        def _process_and_play_single_chunk(self, text):
                if not text.strip():
                        print("⚠️ Skipping empty TTS chunk")
                        return
                url = "https://api.deepgram.com/v1/speak"
                headers = {
                        "Authorization": f"Token {self.DEEPGRAM_API_KEY}",
                        "Content-Type": "text/plain",
                        "Accept": "audio/mpeg"
                }

                wav_path = "audio/quick_response.wav"
                try:
                        with self.session.post(url, headers=headers, data=text.encode("utf-8"), stream=True) as response:
                                response.raise_for_status()

                                ffmpeg_process = subprocess.Popen([
                                        "ffmpeg", "-y", "-threads", "1",
                                        "-f", "mp3", "-i", "pipe:0",
                                        wav_path
                                ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                                for audio_chunk in response.iter_content(chunk_size=2048):
                                        if audio_chunk:
                                                ffmpeg_process.stdin.write(audio_chunk)

                                ffmpeg_process.stdin.close()
                                ffmpeg_process.wait()

                        self._play_chunk(wav_path)

                except requests.RequestException as e:
                        print(f"Single chunk failed: {e}")


        @timed
        def audio_to_text(self, file_path="audio/audio.wav"):
                """
                        Transcribes audio to text using Deepgram's API.

                        Parameters:
                        file_path (str): Path to the audio file.

                        Returns:
                        str: The transcribed text if successful, None otherwise.
                """

                url = "https://api.deepgram.com/v1/listen"
                print(self.DEEPGRAM_API_KEY)
        # Open the audio file in binary mode
                with open(file_path, "rb") as audio_file:
            # Send the file for transcription
                        response = requests.post(
                                url,
                                headers={
                                "Authorization": f"Token {self.DEEPGRAM_API_KEY}",
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
                                        print(f"Speech to Text: {transcript}")
                                        return transcript
                                else:
                                        print("Error: No transcription found in the response.")
                                        return None
                        else:
                                print(f"Error: {response.status_code} - {response.text}")
                                return None


        def gpt_request(self, transcript):
                """
                        Performs GPT API Request with a custom prompt returning text response

                        Parameters:
                        transcript (str): User prompt / transcript of user speech

                        Returns:
                        str: GPT text response if successful, None otherwise.
                """
                if transcript:
            # Send the transcript to OpenAI GPT model
                        completion = self.client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                        {"role": "user", "content": transcript}
                                ]
                        )

            # Extract the GPT response content
                        response = completion.choices[0].message.content
                        print("GPT-4o-mini Response: ", response)
                        return response
                return None


        def gpt_image_request(self, transcript, photo_path="images/temp_image.jpg"):
                """
                Sends an image and a text prompt to the GPT API and returns the text response.

                Parameters:
                        photo_path (str): Path to the image file to be sent.
                        transcript (str): Text prompt or description for the image.

                Returns:
                str: The GPT model's response text.
                """
        # Path to your image
        # Getting the base64 string
                base64_image = encode_image(photo_path)

                response = self.client.chat.completions.create(
                        model="gpt-4o",
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
                print(f"GPT-4o-mini Response: {message_content}")
                return(message_content)
        
        def resize_image(self, image_path, max_size=512):
                """
                Resizes the image to fit within max_size (pixels) and returns new path.
                """
                os.makedirs("images", exist_ok=True)
                resized_path = "images/resized_temp.jpg"
                img = Image.open(image_path)
                img.thumbnail((max_size, max_size))
                img.save(resized_path, "JPEG")
                return resized_path
        

        def gpt_image_request2(self, transcript, photo_path="images/temp_image.jpg"):
                """
                Sends an image and a text prompt to the GPT API and returns the text response.

                Parameters:
                        photo_path (str): Path to the image file to be sent.
                        transcript (str): Text prompt or description for the image.

                Returns:
                str: The GPT model's response text.
                """
        # Path to # ✅ Resize image for performance
                resized_path = self.resize_image(photo_path)
                

    # ✅ Encode resized image using cached method
                base64_image = encode_image(resized_path)
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
                        ]
                
                print("Streaming GPT-4o response...")

                response_text = ""
                response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        stream=True
                )

                for chunk in response:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content"):
                                content = delta.content
                                if content:
                                        print(content, end="", flush=True)
                                        response_text += content

                print()  # new line after stream
                return response_text
        
        def gpt_image_request3(self, transcript, photo_path="images/temp_image.jpg"):
                """
                Sends an image and a text prompt to the GPT API and returns the text response.

                Parameters:
                        photo_path (str): Path to the image file to be sent.
                        transcript (str): Text prompt or description for the image.

                Returns:
                str: The GPT model's response text.
                """
                if not hasattr(self, "audio_queue"):
                        self.audio_queue = queue.Queue()

                        def audio_worker():
                                while True:
                                        text = self.audio_queue.get()
                                        if text:
                                                self._process_and_play_single_chunk(text)
                                        self.audio_queue.task_done()
                
                        threading.Thread(target=audio_worker, daemon=True).start()

                resized_path = self.resize_image(photo_path)
                base64_image = encode_image_cached(resized_path)

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
                        ]
                
                print("Streaming GPT-4o response...")

                response_text = ""
                buffer = ""

                response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        stream=True
                )

                for chunk in response:
                        delta = chunk.choices[0].delta
                        content = getattr(delta, "content", None)
                        
                        if content and content.strip(): 
                                print(content, end="", flush=True)
                                response_text += content
                                buffer += content

                                if any(p in content for p in ".!?") or len(buffer) > 199:
                                        print(f"\n🎤 Queueing for TTS: {buffer.strip()}")
                                        self.audio_queue.put(buffer.strip())
                                        buffer = ""
                if buffer.strip():
                        print(f"\n🎤 Final speaking chunk: {buffer.strip()}")
                        self.audio_queue.put(buffer.strip())

                print()  # new line after stream
                return response_text
        
        def gpt_image_request_word_by_word(self, transcript, photo_path="images/temp_image.jpg"):
                """
                Streams GPT-4o word-by-word and speaks each word using Deepgram TTS.
                """
                # Start audio queue system if not already running
                self.audio_queue = queue.Queue()

                def audio_worker():
                        while True:
                                word = self.audio_queue.get()
                                if word and len(word.strip()) > 1:  # avoid 1-char like "a"
                                        self._process_and_play_single_chunk(word)
                                self.audio_queue.task_done()

                threading.Thread(target=audio_worker, daemon=True).start()

    # Prepare image and prompt
                resized_path = self.resize_image(photo_path)
                base64_image = encode_image_cached(resized_path)

                messages = [
                        {
                                "role": "user",
                                "content": [
                                        {"type": "text", "text": transcript},
                                        {
                                                "type": "image_url",
                                                "image_url": {
                                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                                },
                                        },
                                ],
                        }
                ]

                print("Streaming GPT-4o response word-by-word...")
                response_text = ""

                response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        stream=True
                )

                word_buffer = ""
                for chunk in response:
                        delta = chunk.choices[0].delta
                        content = getattr(delta, "content", None)

                        if content and content.strip():
                                print(content, end="", flush=True)
                                response_text += content
                                word_buffer += content

            # Check for a space = end of word
                                if " " in word_buffer:
                                        words = word_buffer.strip().split()
                                        for word in words[:-1]:
                                                self.audio_queue.put(word.strip())
                                        word_buffer = words[-1] if words else ""

    # Final word
                if word_buffer.strip():
                        self.audio_queue.put(word_buffer.strip())

                print()  # newline
                return response_text
        class MemoryManager:
                def __init__(self):
            # Current context window
            # Selected list of
                        self.context_window = ""

        def top_k_embedding(self, curr_embedding):
                return 0















