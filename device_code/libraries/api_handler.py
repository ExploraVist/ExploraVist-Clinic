import os
from openai import OpenAI
import base64
import requests
import subprocess
import RPi.GPIO as GPIO
import time
import re
from pathlib import Path

def encode_image(image_path):
        with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

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
         
        def stream_tts(self, text):
                url = "https://api.deepgram.com/v1/speak"
                headers = {
                        "Authorization": f"Token {self.DEEPGRAM_API_KEY}",
                        "Accept": "audio/mpeg"  # Deepgram will return MP3 audio
                }

                chunks = self.split_text(text)
                Path("audio").mkdir(exist_ok=True)
                wav_files = []

                for i, chunk in enumerate(chunks):
                        mp3_path = f"audio/chunk_{i}.mp3"
                        wav_path = f"audio/chunk_{i}.wav"

                        try:
                                with self.session.post(url, headers=headers, data=chunk.encode("utf-8"), stream=True) as response:
                                        response.raise_for_status()
                                        with open(mp3_path, "wb") as f:
                                                for audio_chunk in response.iter_content(chunk_size=4096):
                                                        if audio_chunk:
                                                                f.write(audio_chunk)

            # Convert MP3 to WAV
                                subprocess.run([
                                        "ffmpeg", "-y", "-i", mp3_path, wav_path
                                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                                wav_files.append(wav_path)
                                os.remove(mp3_path)

                        except requests.RequestException as e:
                                print(f"Chunk {i} failed: {e}")
                                continue

    # Create a file list for ffmpeg concat
                concat_list_path = "audio/concat_list.txt"
                with open(concat_list_path, "w") as f:
                        for wav_file in wav_files:
                                f.write(f"file '{os.path.abspath(wav_file)}'\n")

                final_wav = "audio/converted_response.wav"

    # Use ffmpeg to concatenate all .wav files
                subprocess.run([
                        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
                        "-c", "copy", final_wav
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Cleanup
                for wav in wav_files:
                        os.remove(wav)
                        os.remove(concat_list_path)

                return final_wav

        def play_audio(self, audio_file="audio/converted_response.wav"):
                """
                Plays the converted audio file and monitors for cancellation.

                Parameters:
                        audio_file (str): Path to the audio file to play
                """
                if not os.path.exists(audio_file):
                        print("Error: Audio file not found.")
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

                # Clean up the converted file
                os.remove(audio_file)


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

        

        class MemoryManager:
                def __init__(self):
            # Current context window
            # Selected list of
                        self.context_window = ""

        def top_k_embedding(self, curr_embedding):
                return 0















