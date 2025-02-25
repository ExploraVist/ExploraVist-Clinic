import re
import requests
import os

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", None)

DEEPGRAM_URL = 'https://api.deepgram.com/v1/speak?model=aura-helios-en'
headers = {
    "Authorization": f"Token {DEEPGRAM_API_KEY}",
    "Content-Type": "application/json"
}

input_text = "Our story begins in a peaceful woodland kingdom where a lively squirrel named Frolic made his abode high up within a cedar tree's embrace. He was not a usual woodland creature, for he was blessed with an insatiable curiosity and a heart for adventure. Nearby, a glistening river snaked through the landscape, home to a wonder named Splash - a silver-scaled flying fish whose ability to break free from his water-haven intrigued the woodland onlookers. This magical world moved on a rhythm of its own until an unforeseen circumstance brought Frolic and Splash together. One radiant morning, while Frolic was on his regular excursion, and Splash was making his aerial tours, an unpredictable wave playfully tossed and misplaced Splash onto the riverbank. Despite his initial astonishment, Frolic hurriedly and kindly assisted his new friend back to his watery abode. Touched by Frolic's compassion, Splash expressed his gratitude by inviting his friend to share his world. As Splash perched on Frolic's back, he tasted of the forest's bounty, felt the sun's rays filter through the colors of the trees, experienced the conversations amidst the woods, and while at it, taught the woodland how to blur the lines between earth and water."

def segment_text_by_sentence(text):
    sentence_boundaries = re.finditer(r'(?<=[.!?])\s+', text)
    boundaries_indices = [boundary.start() for boundary in sentence_boundaries]
    
    segments = []
    start = 0
    for boundary_index in boundaries_indices:
        segments.append(text[start:boundary_index + 1].strip())
        start = boundary_index + 1
    segments.append(text[start:].strip())

    return segments

def synthesize_audio(text, output_file):
    payload = {"text": text}
    try:
        response = requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Verify content type is audio
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('audio/'):
            raise ValueError(f"Invalid content type received: {content_type}. Expected audio/*")
            
        # Check if we're getting actual data
        data_received = False
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                data_received = True
                output_file.write(chunk)
                
        if not data_received:
            raise ValueError("No audio data received from the API")
            
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")
        raise
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

def main():
    segments = segment_text_by_sentence(input_text)

    try:
        # Create or truncate the output file
        with open("output.mp3", "wb") as output_file:
            for i, segment_text in enumerate(segments, 1):
                print(f"Processing segment {i}/{len(segments)}")
                synthesize_audio(segment_text, output_file)

        print("Audio file creation completed successfully.")
    except Exception as e:
        print("Failed to create audio file.")
        # Delete partial output file if it exists
        if os.path.exists("output.mp3"):
            os.remove("output.mp3")
        raise

if __name__ == "__main__":
    main()
