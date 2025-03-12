import os
from openai import OpenAI
import base64
import requests
import subprocess
import RPi.GPIO as GPIO
import time
from libraries.metrics import timed
import re

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


DEEPGRAM_API_KEY = "3d85ba05e27a54d04228f61d2b231c97d00b926a"
if not DEEPGRAM_API_KEY:
    raise ValueError("Please set the DEEPGRAM_API_KEY environment variable.")


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
        @timed
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

        @timed
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

        def speak_and_play_tts(self, sentence):
                """
                Sends a single sentence to the Deepgram TTS API and plays the audio
                in real-time by piping it to ffmpeg -> aplay.
                """

                DEEPGRAM_URL = "https://api.deepgram.com/v1/speak?model=aura-helios-en"

                headers = {
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "application/json"}
                
                payload = {"text": sentence}

                # Make a streaming POST request
                response = requests.post(DEEPGRAM_URL, headers=headers, json=payload, stream=True)
                response.raise_for_status()

                # Validate we are getting audio data
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith("audio/"):
                        raise ValueError(f"Expected audio data but got content-type={content_type}")

                # Start ffmpeg to read from STDIN (pipe:0), decode to WAV (-f wav -),
                # and output the raw WAV data to STDOUT.
                ffmpeg_proc = subprocess.Popen(
                        [
                        "ffmpeg",
                        "-loglevel", "error",  # Suppress verbose logs
                        "-i", "pipe:0",        # Take input from stdin
                        "-f", "wav",           # Output format: WAV
                        "-"
                        ],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE
                )

                # Pipe ffmpeg's decoded WAV data directly into aplay for playback
                aplay_proc = subprocess.Popen(
                        ["aplay", "-D", "default"],
                        stdin=ffmpeg_proc.stdout
                )

                # Stream chunks from the TTS response into ffmpeg's stdin
                try:
                        for chunk in response.iter_content(chunk_size=4096):
                                if chunk:
                                        ffmpeg_proc.stdin.write(chunk)
                finally:
                        # Close ffmpeg's stdin to signal end of input
                        ffmpeg_proc.stdin.close()

                        # Wait for ffmpeg to finish decoding
                        ffmpeg_proc.wait()

                        # Terminate aplay after ffmpeg completes
                        aplay_proc.terminate()
                        aplay_proc.wait()

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

        @timed
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
        
        def gpt_stream_request(self, transcript):
                """
                Performs GPT API Request with a custom prompt returning text response

                Parameters:
                        transcript (str): User prompt / transcript of user speech

                Returns:
                str: GPT text response if successful, None otherwise.
                """

        @timed
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















