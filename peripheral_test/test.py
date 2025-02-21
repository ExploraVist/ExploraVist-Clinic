import websockets
import json
import pyaudio
from pydub import AudioSegment
import io

async def play_audio_stream(ws):
    p = pyaudio.PyAudio()

    while True:
        response = await ws.recv()
        
        # Log the response to see what's coming from the WebSocket
        if response:
            
                # Attempt to parse the JSON response
                audio_data = json.loads(response)


                # Extract the audio chunk
                audio_chunk = audio_data.get("audio", None)
                if audio_chunk:

                    
                    # Convert audio chunk to in-memory file
                    audio_bytes = io.BytesIO(audio_chunk)
                    
                    # Attempt to load the audio from the bytes
                    audio = AudioSegment.from_wav(audio_bytes)
                    

                    # Play the audio
                    stream = p.open(format=pyaudio.paInt16,
                                    channels=1,
                                    rate=audio.frame_rate,
                                    output=True)
                    
                    stream.write(audio.raw_data)
                    stream.stop_stream()
                    stream.close()
               
                    
    p.terminate()



async def stream_tts(text, api_key, model="aura-asteria-en"):

                url = f"wss://api.deepgram.com/v1/listen?model={model}"
                headers = {
                        "Authorization": f"Token {api_key}",
                        "Content-Type": "application/json"
                }

                try:
                        async with websockets.connect(url, extra_headers=headers) as ws:
                                
                                # Send the text to be converted to speech
                                request = json.dumps({"text": text})
                                await ws.send(request)
                                print("Sent text to Deepgram API")  # Debugging output
                                
                                # Start playing the audio stream
                                await play_audio_stream(ws)

                except Exception as e:
                        print(f"Error in stream_tts: {e}")


    

api_key = "eb4f92cc97e5bb2057fc4bcb4d8ea1ddccb7b1ed"

text = "Deepgram is an advanced speech recognition platform that leverages deep learning technologies to provide high-quality, real-time transcription and voice recognition services. Designed for developers and businesses, Deepgram offers a range of features, including automatic speech recognition (ASR), natural language processing (NLP), and customizable models that can be tailored to specific industries or applications. Its API allows users to integrate speech recognition capabilities into various applications, such as customer support, content creation, and voice interfaces."

stream_tts(api_key, text)