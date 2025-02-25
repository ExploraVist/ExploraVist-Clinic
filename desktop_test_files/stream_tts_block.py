import re
import os
import requests
import subprocess

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", None)
if not DEEPGRAM_API_KEY:
    raise ValueError("Please set the DEEPGRAM_API_KEY environment variable.")

# Example TTS endpoint for Deepgram:
DEEPGRAM_URL = "https://api.deepgram.com/v1/speak?model=aura-helios-en"

headers = {
    "Authorization": f"Token {DEEPGRAM_API_KEY}",
    "Content-Type": "application/json"
}

input_text = (
    "Our story begins in a peaceful woodland kingdom where a lively squirrel named Frolic "
    "made his abode high up within a cedar tree's embrace. He was not a usual woodland "
    "creature, for he was blessed with an insatiable curiosity and a heart for adventure. "
    "Nearby, a glistening river snaked through the landscape, home to a wonder named Splash "
    "– a silver-scaled flying fish whose ability to break free from his water-haven intrigued "
    "the woodland onlookers. This magical world moved on a rhythm of its own until an "
    "unforeseen circumstance brought Frolic and Splash together. One radiant morning, while "
    "Frolic was on his regular excursion, and Splash was making his aerial tours, an "
    "unpredictable wave playfully tossed and misplaced Splash onto the riverbank. Despite "
    "his initial astonishment, Frolic hurriedly and kindly assisted his new friend back to "
    "his watery abode."
)

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

def speak_and_play_tts(sentence):
    """
    Sends a single sentence to the Deepgram TTS API and plays the audio
    in real-time by piping it to ffmpeg -> aplay.
    """
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

def main():
    sentences = segment_text_by_sentence(input_text)
    for idx, sentence in enumerate(sentences, start=1):
        print(f"Playing sentence {idx}/{len(sentences)}...")
        speak_and_play_tts(sentence)

if __name__ == "__main__":
    main()
