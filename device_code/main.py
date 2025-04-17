# main.py
"""Entry point stitching together devices, API, and cancellation logic."""
import time, RPi.GPIO as GPIO
from libraries.cancel_flag import CancelFlag
from libraries.button_watcher import ButtonWatcher
from libraries.api_handler_ext import APIHandler
from libraries.media_device_manager import MediaDeviceManager
from libraries.sys_config import SystemConfig
from libraries.config import config as _cfg

AMP_SD_PIN = 26  # amplifier shutdown
THRESHOLD = 1.5
MIN_PRESS  = 0.01

class State: IDLE=0; WAIT_GPT=1; WAIT_TTS=2

def _gpio_setup():
    GPIO.setwarnings(False); GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(AMP_SD_PIN, GPIO.OUT); GPIO.output(AMP_SD_PIN, GPIO.LOW)

def main():
    flag = CancelFlag(); _gpio_setup(); ButtonWatcher(flag).start()
    if not SystemConfig().check_system_ready(): return
    device = MediaDeviceManager()
    api = APIHandler(cancel_flag=flag, config=_cfg)
    api.play_audio_nonblocking("audio_files/startup.wav")

    state, context = State.IDLE, "Context:\n"; default_prompt = "Describe what you see in front of you"

    def cancel_feedback():
        api.play_audio_nonblocking("audio_files/cancelled.wav")
        GPIO.output(AMP_SD_PIN, GPIO.LOW)
        flag.clear()

    while True:
        if flag.is_set(): cancel_feedback(); state = State.IDLE; continue

        if state == State.IDLE:
            # --- wait for button ---
            start = btn = None
            while btn is None:
                if GPIO.input(22)==GPIO.LOW: btn,start=2,time.time()
                elif GPIO.input(27)==GPIO.LOW: btn,start=1,time.time()
                time.sleep(0.01)
            while GPIO.input(22)==GPIO.LOW or GPIO.input(27)==GPIO.LOW: time.sleep(0.01)
            dt = time.time()-start
            if dt < MIN_PRESS: continue

            short = dt<=THRESHOLD
            if btn==2 and short:
                api.play_audio_nonblocking("audio_files/taking_picture.wav")
                device.capture_image()
                flag.monitoring_enabled=True; state=State.WAIT_GPT
                answer = api.gpt_image_request2(context+f"Current Question: {default_prompt}\n")
                flag.monitoring_enabled=False
                if flag.is_set(): continue
                context+=f"USER: {default_prompt}\nGPT: {answer}\n"
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)
                flag.monitoring_enabled=True; state=State.WAIT_TTS
                api.stream_tts_and_play(answer)
                flag.monitoring_enabled=False; GPIO.output(AMP_SD_PIN, GPIO.LOW); state=State.IDLE
            elif btn==1 and short:
                flag.monitoring_enabled=True; state=State.WAIT_TTS
                api.play_audio_nonblocking("audio_files/hold_button.wav")
                flag.monitoring_enabled=False; GPIO.output(AMP_SD_PIN, GPIO.LOW); state=State.IDLE
                
            else:
                device.start_recording();
                while GPIO.input(22)==GPIO.LOW or GPIO.input(27)==GPIO.LOW: time.sleep(0.05)
                device.stop_recording();
                transcript = api.audio_to_text("audio/audio.wav") or ""
                if flag.is_set(): continue
                if btn==2: device.capture_image();
                prompt=context+f"Current Question: {transcript}\n"
                flag.monitoring_enabled=True; state=State.WAIT_GPT
                answer = api.gpt_image_request2(prompt) if btn==2 else api.gpt_request(prompt)
                flag.monitoring_enabled=False
                if flag.is_set(): continue
                context+=f"USER: {transcript}\nGPT: {answer}\n"
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)
                flag.monitoring_enabled=True; state=State.WAIT_TTS
                api.stream_tts_and_play(answer)
                flag.monitoring_enabled=False; GPIO.output(AMP_SD_PIN, GPIO.LOW); state=State.IDLE

if __name__=="__main__":
    try: main()
    finally: GPIO.cleanup()
