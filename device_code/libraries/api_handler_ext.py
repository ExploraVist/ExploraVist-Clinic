# ---------------------------------------------------------------------------
# api_handler_ext.py
"""APIHandler subclass that handles CancelFlag and avoids audio overlap."""
import os, time, threading, subprocess
from libraries.cancel_flag import CancelFlag
from libraries.api_handler import APIHandler as BaseHandler, encode_image

class APIHandler(BaseHandler):
    def __init__(self, *, cancel_flag: CancelFlag, **kwargs):
        super().__init__(**kwargs)
        self.flag = cancel_flag
        self._lock = threading.Lock()
        self._current_proc = None
        self._current_clip = None

    # ---- playback helpers --------------------------------------------------
    def _should_abort(self):
        return self.flag.is_set()

    def _spawn_playback(self, audio_file, blocking):
        with self._lock:
            if self._current_proc and self._current_proc.poll() is None:
                if audio_file == self._current_clip:
                    return  # same clip already playing – ignore
                self._current_proc.terminate(); self._current_proc.wait()
            self._current_clip = audio_file
            self._current_proc = subprocess.Popen(["aplay", "-q", audio_file])

        if blocking:
            self._wait_proc()
        else:
            threading.Thread(target=self._wait_proc, daemon=True).start()

    def _wait_proc(self):
        while True:
            with self._lock:
                proc = self._current_proc
            if proc is None or proc.poll() is not None:
                break
            if self._should_abort():
                proc.terminate(); proc.wait(); break
            time.sleep(0.05)
        with self._lock:
            self._current_proc = None; self._current_clip = None

    # public playback API
    def play_audio(self, audio_file):
        self._spawn_playback(audio_file, blocking=True)

    def play_audio_nonblocking(self, audio_file):
        self._spawn_playback(audio_file, blocking=False)

    # override chunk player
    def _play_chunk(self, wav_path):
        self.play_audio(wav_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

    # GPT image request with cancel polling
    def gpt_image_request2(self, transcript, photo_path="images/temp_image.jpg"):
        if self._should_abort():
            return ""
        resized_path = self.resize_image(photo_path)
        base64_image = encode_image(resized_path)
        messages=[{"role":"user","content":[{"type":"text","text":transcript},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{base64_image}"}}]}]
        response_text=""
        response = self.client.chat.completions.create(model="gpt-4o", messages=messages, stream=True)
        for chunk in response:
            if self._should_abort():
                break
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                print(delta.content, end="", flush=True)
                response_text += delta.content
        print()
        return response_text
