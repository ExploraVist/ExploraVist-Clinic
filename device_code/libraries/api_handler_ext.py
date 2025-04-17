# api_handler_ext.py
"""APIHandler subclass that honours the CancelFlag and stops playback /
streaming instantly when cancellation is requested."""
import os, time, threading, subprocess
from cancel_flag import CancelFlag
from libraries.api_handler import APIHandler as BaseHandler

class APIHandler(BaseHandler):
    def __init__(self, *, cancel_flag: CancelFlag, **kwargs):
        super().__init__(**kwargs)
        self.flag = cancel_flag

    # ---- util ------------------------------------------------------------
    def _should_abort(self):
        return self.flag.is_set()

    # ---- synchronous playback (blocking) ---------------------------------
    def play_audio(self, audio_file="audio/converted_response.wav"):
        if not os.path.exists(audio_file):
            print("Missing", audio_file); return
        proc = subprocess.Popen(["aplay", "-q", audio_file])
        while proc.poll() is None:
            if self._should_abort():
                proc.terminate(); proc.wait(); break
            time.sleep(0.05)

    # ---- non‑blocking playback ------------------------------------------
    def play_audio_nonblocking(self, audio_file):
        threading.Thread(target=lambda: self.play_audio(audio_file), daemon=True).start()

    # ---- override chunk player ------------------------------------------
    def _play_chunk(self, wav_path):
        proc = subprocess.Popen(["aplay", "-q", wav_path])
        while proc.poll() is None:
            if self._should_abort():
                proc.terminate(); proc.wait(); break
            time.sleep(0.05)
        proc.wait(); os.remove(wav_path)

    # ---- example of early‑exit wrapper (GPT) -----------------------------
    def gpt_image_request2(self, *args, **kwargs):
        if self._should_abort():
            return ""
        return super().gpt_image_request2(*args, **kwargs)