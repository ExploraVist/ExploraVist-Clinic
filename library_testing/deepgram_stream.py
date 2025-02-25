import re
import requests
import subprocess

DEEPGRAM_URL = 'https://api.deepgram.com/v1/speak?model=aura-helios-en'
headers = {
    "Authorization": "Token DEEPGRAM_API_KEY",
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

def synthesize_audio(text):
    payload = {"text": text}
    with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
        # Open a subprocess to pipe audio data to aplay with specified format
        aplay_process = subprocess.Popen(
            ['aplay', '-f', 'S16_LE', '-r', '16000', '-c', '1', '-'],
            stdin=subprocess.PIPE
        )
        try:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    # Write the audio chunk to aplay's stdin
                    aplay_process.stdin.write(chunk)
        finally:
            # Ensure the aplay process is properly terminated
            aplay_process.stdin.close()
            aplay_process.wait()

def main():
    segments = segment_text_by_sentence(input_text)

    for segment_text in segments:
        synthesize_audio(segment_text)

    print("Audio playback completed.")

if __name__ == "__main__":
    main()
