# button_watcher.py
"""Edge‑detected GPIO listener that
1) plays *popClick.wav* on every press (async);
2) sets the shared CancelFlag whenever monitoring is enabled."""
import time, subprocess, threading
import RPi.GPIO as GPIO
from libraries.cancel_flag import CancelFlag

POP_CLICK_WAV = "audio_files/popClick.wav"

class ButtonWatcher(threading.Thread):
    def __init__(self, cancel_flag: CancelFlag, pins=(22, 27)):
        super().__init__(daemon=True)
        self.flag = cancel_flag
        self.pins = pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for p in pins:
            GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(p, GPIO.FALLING, self._callback, bouncetime=120)

    def _callback(self, channel):
        subprocess.Popen(["aplay", "-q", POP_CLICK_WAV])  # fire & forget
        self.flag.set()

    def run(self):
        while True:
            time.sleep(10)
