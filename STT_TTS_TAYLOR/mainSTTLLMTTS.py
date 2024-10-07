from deepgram_speech_to_text import audio_to_text
from deepgram_text_to_speech_test import text_to_speech  # Import the text-to-speech function
import os
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI()

# Function to process the text with GPT and return the response
def process_text_with_gpt(transcript):
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

def main():
    # Path to your audio file
    audio_file_path = "/Users/taylorlevinson/Downloads/Conference.wav"

    if os.path.exists(audio_file_path):
        print(f"Transcribing audio file: {audio_file_path}")
        transcript = audio_to_text(audio_file_path)
        
        if transcript:
            print("Transcription:", transcript)
            # Process the transcribed text using GPT
            gpt_response = process_text_with_gpt(transcript)
            
            if gpt_response:
                # Convert GPT response to speech using Deepgram TTS
                print(f"Converting GPT response to speech: {gpt_response}")
                text_to_speech(gpt_response)
            else:
                print("No GPT response available.")
        else:
            print("No transcription available.")
    else:
        print(f"Error: Audio file {audio_file_path} does not exist.")

if __name__ == '__main__':
    main()