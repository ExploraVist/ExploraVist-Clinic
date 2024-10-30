import subprocess
import os
import config # Includes DEEPGRAM_API_KEY

# The API key for Deepgram
DEEPGRAM_API_KEY = config.DEEPGRAM_API_KEY

# Function to send text to Deepgram and play audio response
def text_to_speech(text):
    # The URL for Deepgram TTS
    url = "https://api.deepgram.com/v1/speak"

    # Construct the payload as plain text
    payload = text  # Plain text with no encoding

    # Construct the curl command
    curl_command = [
        "curl",
        "-X", "POST", url,
        "-H", f"Authorization: Token {DEEPGRAM_API_KEY}",
        "-H", "Content-Type: text/plain",  # Set Content-Type to text/plain
        "--data", payload  # Use --data for plain text
    ]
    
    # Run the curl command and capture the binary response
    try:
        # Run the curl command and capture binary data without decoding
        result = subprocess.run(curl_command, capture_output=True)
        
        if result.returncode == 0:
            # Save the response to a temporary file for playback
            temp_file = "temp_response.wav"
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

def main():
    # Test strings for text-to-speech conversion
    test_strings = [
        "Hello, this is a test of Deepgram's text-to-speech functionality.",
        "How are you doing today?",
        "This is a third example to check different string inputs."
    ]

    for text in test_strings:
        print(f"Converting text: {text}")
        text_to_speech(text)

if __name__ == '__main__':
    main()
