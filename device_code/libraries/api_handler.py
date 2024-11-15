import os
from openai import OpenAI
import base64
import requests
import subprocess
import RPi.GPIO as GPIO
import time
from libraries.metrics import timed

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

	def __init__(self, config, metrics):
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
        self.metrics = metrics
        self.model = "gpt-4o-mini"

	def text_to_speech(self, text, metrics):
    """
    Converts text to speech using the Deepgram TTS API and plays the audio, while tracking metrics.

    Parameters:
        text (str): Text to be converted to speech.
        metrics (Metrics): Metrics object for tracking timings.

    Returns:
        None
    """
    url = "https://api.deepgram.com/v1/speak"
    metrics.start()  # Start tracking the total time for this request

    try:
        # 1. Send the request to Deepgram's TTS API
        step_start = time.time()
        response = self.session.post(url, data=text.encode('utf-8'))  # Encode to UTF-8
        response.raise_for_status()  # Ensure no HTTP errors
        metrics.add_step("TTS API Request", time.time() - step_start)

        # 2. Save the response audio to a temporary file
        step_start = time.time()
        temp_file = "audio/audio.wav"
        with open(temp_file, "wb") as audio_file:
            audio_file.write(response.content)
        metrics.add_step("Save Audio File", time.time() - step_start)

        # 3. Convert the file to a standard WAV format (if needed)
        step_start = time.time()
        converted_file = "audio/converted_response.wav"
        conversion_command = [
            "ffmpeg", "-y", "-i", temp_file, "-ar", "44100", "-ac", "1", converted_file
        ]
        subprocess.run(conversion_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        metrics.add_step("Convert Audio", time.time() - step_start)

        # 4. Play the converted file
        if os.path.exists(converted_file):
            step_start = time.time()
            print("Audio data received successfully. Playing audio...")
            audio_process = subprocess.Popen(["aplay", converted_file])

            # Monitor GPIO to allow user to cancel playback
            while audio_process.poll() is None:
                if GPIO.input(22) == GPIO.LOW or GPIO.input(27) == GPIO.LOW:  # Button pressed
                    print("Button pressed, stopping audio playback.")
                    audio_process.terminate()
                    self.canceled = 1
                    break
                time.sleep(0.1)  # Check every 100ms

            audio_process.wait()  # Wait for playback to complete
            metrics.add_step("Audio Playback", time.time() - step_start)

            # Clean up temporary files
            os.remove(temp_file)
            os.remove(converted_file)
        else:
            print("Error: Converted audio file not saved correctly.")
            metrics.add_step("Error Handling", 0)

    except requests.exceptions.RequestException as e:
        print(f"Error during TTS API request: {e}")
        metrics.add_step("TTS API Error", 0)
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        metrics.add_step("File Error", 0)
    except Exception as e:
        print(f"Unexpected error during text-to-speech process: {e}")
        metrics.add_step("Unexpected Error", 0)

    # Print total time for the TTS process
    total_time = metrics.get_total_time()
    print(f"Total Text-to-Speech Time: {total_time:.2f} seconds")


	@timed(metrics)
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
				model=self.model,
				messages=[
					{"role": "user", "content": transcript}
				]
			)

            # Extract the GPT response content
			response = completion.choices[0].message.content
			print(f"{self.model} Response", response)
			return response
		return None

	@timed(metrics)
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
			model=self.model,
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
		print(f"{self.model} Response: {message_content}")
		return(message_content)

	#@timed(metrics)
	def temp_text_to_speech(self, text):
		start_time = time.time()
        # Convert text to audio as you have done until now
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
	# FFmpeg command to convert the audio stream directly
		ffmpeg_command = [
			"ffmpeg",
			"-y",  # Overwrite output file without asking
			"-i", "pipe:0",  # Input from the pipe
			"-ar", "44100",  # Set audio sample rate
			"-ac", "2",      # Set audio channels
			output_file      # Output file
		]
		try:
			with subprocess.Popen(curl_command, stdout=subprocess.PIPE) as curl_proc:
				ffmpeg_result = subprocess.run(ffmpeg_command, stdin=curl_proc.stdout)
				if ffmpeg_result.returncode == 0:
					print("Audio data received successfully. Playing audio...")
					audio_process = subprocess.Popen(["aplay", output_file])
					print(f"Speech to Text: {time.time() - start_time}")
                # Continuously check GPIO 22 while playing audio
					while audio_process.poll() is None:
						if GPIO.input(22) == GPIO.LOW:  # Button is pressed
							print("Button pressed, stopping audio playback.")
							audio_process.terminate()
							self.canceled = 1
							break
						time.sleep(0.1)  # Check every 100ms
					audio_process.wait()  # Wait for the process to finish or be terminated
					print("Playback finished.")

					if os.path.exists(output_file):
						os.remove(output_file)
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


