import requests
import os

# The API key for Deepgram
DEEPGRAM_API_KEY = ''

# Function to send audio file to Deepgram for transcription
def audio_to_text(file_path):
    url = "https://api.deepgram.com/v1/listen"

    # Open the audio file in binary mode
    with open(file_path, "rb") as audio_file:
        # Send the file for transcription
        response = requests.post(
            url,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
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

def main():
    # Example audio file for transcription
    audio_file_path = "/Users/taylorlevinson/Downloads/Conference.wav"  # Use .mp3 if needed

    if os.path.exists(audio_file_path):
        print(f"Transcribing audio file: {audio_file_path}")
        transcript = audio_to_text(audio_file_path)
        if transcript:
            print("Transcription:", transcript)
        else:
            print("Failed to get transcription.")
    else:
        print(f"Error: Audio file {audio_file_path} does not exist.")

if __name__ == '__main__':
    main()