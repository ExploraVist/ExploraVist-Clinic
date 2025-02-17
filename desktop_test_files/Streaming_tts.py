import json
import os
import threading
import asyncio
import queue
import time
import signal

import websockets
from websockets.sync.client import connect

import pyaudio

from openai import OpenAI

client = OpenAI()

TIMEOUT = 0.050
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 8000

DEFAULT_URL = f"wss://api.deepgram.com/v1/speak?encoding=linear16&sample_rate={RATE}"
DEFAULT_TOKEN = os.environ.get("DEEPGRAM_API_KEY", None)

class Speaker:
    """Handles audio playback for streaming text-to-speech output."""
    def __init__(self, rate: int = RATE, chunk: int = CHUNK, channels: int = CHANNELS, output_device_index: int = None):
        self._exit = threading.Event()
        self._queue = queue.Queue()
        self._audio = pyaudio.PyAudio()
        self._chunk = chunk
        self._rate = rate
        self._format = FORMAT
        self._channels = channels
        self._output_device_index = output_device_index

    def start(self) -> bool:
        """Starts the audio playback stream and processing thread."""
        self._stream = self._audio.open(
            format=self._format,
            channels=self._channels,
            rate=self._rate,
            input=False,
            output=True,
            frames_per_buffer=self._chunk,
            output_device_index=self._output_device_index,
        )
        self._exit.clear()
        self._thread = threading.Thread(target=self._play, daemon=True)
        self._thread.start()
        self._stream.start_stream()
        return True

    def stop(self):
        """Stops the audio playback and cleans up resources."""
        self._exit.set()
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        self._thread.join()
        self._thread = None
        self._queue = None

    def play(self, data):
        """Enqueues audio data for playback."""
        self._queue.put(data)

    def _play(self):
        """Continuously plays audio from the queue while the thread is running."""
        while not self._exit.is_set():
            try:
                data = self._queue.get(timeout=TIMEOUT)
                self._stream.write(data)
            except queue.Empty:
                pass  # Nothing to play right now
            except Exception as e:
                print(f"Speaker error: {e}")

def main():
    print(f"Connecting to {DEFAULT_URL}")
    _socket = connect(DEFAULT_URL, additional_headers={"Authorization": f"Token {DEFAULT_TOKEN}"})
    _exit = threading.Event()
    char_count = 0
    last_flush_time = 0

    # Graceful exit function
    def shutdown(signum, frame):
        print("\nShutting down gracefully...")
        _exit.set()
        try:
            _socket.send(json.dumps({"type": "Close"}))
            _socket.close()
        except Exception:
            pass
        exit(0)

    # Attach signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, shutdown)    # Handle termination signals

    # Wait for the user to press 's' to start the request (so we don't include setup time in the measurement)
    start_input = input("Press 's' to start the request: ")
    while start_input.lower() != 's':
        start_input = input("Press 's' to start the request: ")

    # Record start time and begin the TTS request now that the user is ready
    start_time = time.time()
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Can you tell me about the complete history of the Ottoman Empire?"}],
        stream=True,
    )

    async def receiver():
        """Receives and plays audio data from the WebSocket."""
        speaker = Speaker()
        speaker.start()
        try:
            while not _exit.is_set():
                if _socket is None:
                    break
                message = _socket.recv()
                if message is None:
                    continue
                if isinstance(message, str):
                    print(message)
                elif isinstance(message, bytes):
                    speaker.play(message)
        except Exception as e:
            print(f"Receiver error: {e}")
        finally:
            speaker.stop()

    _receiver_thread = threading.Thread(target=asyncio.run, args=(receiver(),))
    _receiver_thread.start()

    try:
        for chunk in stream:
            if _exit.is_set():
                break

            if chunk.choices[0].delta.content is not None:
                text = chunk.choices[0].delta.content

                # If the text exceeds 2000 characters, split it up.
                if len(text) > 2000:
                    parts = [text[i:i+2000] for i in range(0, len(text), 2000)]
                else:
                    parts = [text]

                for part in parts:
                    char_count += len(part)
                    # Reset character count every 2 minutes
                    if time.time() - start_time > 120:
                        char_count = 0
                        start_time = time.time()
                    # Prevent exceeding 12k characters per 2 minutes
                    if char_count > 12000:
                        print("Character limit reached, pausing...")
                        time.sleep(5)
                    print(f"Sending: {part}")
                    _socket.send(json.dumps({"type": "Speak", "text": part}))
                    time.sleep(0.05)  # Throttle sending

                    # Only flush if at least 5 seconds have passed
                    if time.time() - last_flush_time >= 5:
                        _socket.send(json.dumps({"type": "Flush"}))
                        print("Flushed.")
                        last_flush_time = time.time()

    except KeyboardInterrupt:
        shutdown(None, None)

    print("Final Flush...")
    _socket.send(json.dumps({"type": "Flush"}))
    _exit.set()
    _socket.send(json.dumps({"type": "Close"}))
    _socket.close()
    _receiver_thread.join()

if __name__ == "__main__":
    main()
