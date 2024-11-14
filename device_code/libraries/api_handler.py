import os
from openai import OpenAI
import base64
import requests
import subprocess
from metrics import timed

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

    @timed
    def audio_to_text(self, file_path="/audio/audio.wav"):
        """
        Transcribes audio to text using Deepgram's API.
        
        Parameters:
            file_path (str): Path to the audio file.

        Returns:
            str: The transcribed text if successful, None otherwise.
        """

        url = "https://api.deepgram.com/v1/listen"

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
    
    @timed
    def gpt_image_request(self, transcript, photo_path="/images/temp_image.jpg"):
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

    @timed
    def text_to_speech(self, text):
        """
        Converts text to speech using the Deepgram TTS API and plays the audio.

        Parameters:
            text (str): Text to be converted to speech.

        Returns:
            None
        """

        # The URL for Deepgram TTS
        url = "https://api.deepgram.com/v1/speak"

        # Construct the payload as plain text
        payload = text  # Plain text with no encoding

        # Construct the curl command
        curl_command = [
            "curl",
            "-X", "POST", url,
            "-H", f"Authorization: Token {self.DEEPGRAM_API_KEY}",
            "-H", "Content-Type: text/plain",  # Set Content-Type to text/plain
            "--data", payload  # Use --data for plain text
        ]
        
        # Run the curl command and capture the binary response
        try:
            # Run the curl command and capture binary data without decoding
            result = subprocess.run(curl_command, capture_output=True)
            
            if result.returncode == 0:
                # Save the response to a temporary file for playback
                temp_file = "/audio/audio.wav"
                with open(temp_file, "wb") as audio_file:
                    audio_file.write(result.stdout)

                # Check if the file was saved properly
                if os.path.getsize(temp_file) > 0:
                    print("Audio data received successfully. Playing audio...")
            # Play the audio file using afplay
                    converted_file = "converted_response.wav"
                    conversion_command = [
                            "ffmpeg","-y",
                            "-i", temp_file,
                            "-ar", "44100",
                            "-ac", "2",
                            converted_file
                    ]
                    #TODO: Figure out how to play Audio on Pi Zero 2W
                    subprocess.run(conversion_command)

                    subprocess.run(["aplay", converted_file])
                    print("Playback finished.")
                    
                    # Optionally delete the temp file after playing
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                else:
                    print("Error: The audio file is empty or not saved correctly.")
            else:
                print(f"Error: {result.stderr.decode('utf-8', errors='ignore')}")
                
        except Exception as e:
            print(f"Error running curl command: {e}")
            
    
    class MemoryManager:
        def __init__(self):
            # Current context window
            # Selected list of 
            self.context_window = ""
        
        def top_k_embedding(self, curr_embedding):
            return 0