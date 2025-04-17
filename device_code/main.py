# ---------------------------------------------------------------------------
# main.py
"""Main entry: button logic, GPT/TTS pipeline, instant cancel."""
import time, RPi.GPIO as GPIO
from libraries.cancel_flag import CancelFlag
from libraries.button_watcher import ButtonWatcher
from libraries.api_handler_ext import APIHandler
from libraries.media_device_manager import MediaDeviceManager
from libraries.sys_config import SystemConfig
from libraries.config import config as _cfg

AMP_SD_PIN = 26; THRESHOLD=1.5; MIN_PRESS=0.01
class State: IDLE=0; WAIT_GPT=1; WAIT_TTS=2

def _gpio_setup():
    GPIO.setwarnings(False); GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(AMP_SD_PIN, GPIO.OUT); GPIO.output(AMP_SD_PIN, GPIO.LOW)

def main():
    flag = CancelFlag(); _gpio_setup(); ButtonWatcher(flag).start()
    if not SystemConfig().check_system_ready(): return
    device = MediaDeviceManager(); api = APIHandler(cancel_flag=flag, config=_cfg)
    api.play_audio_nonblocking("audio_files/startup.wav")

    context="Context:\n"; default_prompt="Describe what you see in front of you"; state=State.IDLE

    def cancelled():
        api.play_audio_nonblocking("audio_files/cancelled.wav"); GPIO.output(AMP_SD_PIN, GPIO.LOW); flag.clear()

    while True:
        if flag.is_set(): cancelled(); state=State.IDLE; continue
        if state!=State.IDLE: time.sleep(0.01); continue  # safety

        # wait for any press --------------------------------------------------
        start=btn=None
        while btn is None:
            if GPIO.input(22)==GPIO.LOW:
                btn,start=2,time.time(); device.start_recording()  # begin mic capture immediately
            elif GPIO.input(27)==GPIO.LOW:
                btn,start=1,time.time(); device.start_recording()
            time.sleep(0.01)
        # keep recording until release
        while GPIO.input(22)==GPIO.LOW or GPIO.input(27)==GPIO.LOW:
            time.sleep(0.01)
        device.stop_recording()
        dt=time.time()-start
        if dt<MIN_PRESS:
            continue  # ignore contact bounce
        short=dt<=THRESHOLD

        # quick image default
        if btn==2 and short:
            api.play_audio_nonblocking("audio_files/taking_picture.wav"); device.capture_image()
            flag.monitoring_enabled=True; state=State.WAIT_GPT
            ans=api.gpt_image_request2(context+f"Current Question: {default_prompt}\n"); flag.monitoring_enabled=False
            if flag.is_set(): state=State.IDLE; continue
            context+=f"USER: {default_prompt}\nGPT: {ans}\n"; GPIO.output(AMP_SD_PIN,GPIO.HIGH)
            flag.monitoring_enabled=True; state=State.WAIT_TTS; api.stream_tts_and_play(ans); flag.monitoring_enabled=False
            GPIO.output(AMP_SD_PIN,GPIO.LOW); state=State.IDLE; continue

        # quick mic tap → reminder (no overlap)
        if btn==1 and short:
            api.play_audio_nonblocking("audio_files/hold_button.wav"); continue

        # long holds ------------------------------------------------------
        
        transcript=api.audio_to_text("audio/audio.wav") or ""
        if flag.is_set(): state=State.IDLE; continue
        if btn==2: device.capture_image()
        prompt=context+f"Current Question: {transcript}\n"
        flag.monitoring_enabled=True; state=State.WAIT_GPT
        ans=api.gpt_image_request(prompt) if btn==2 else api.gpt_request(prompt); flag.monitoring_enabled=False
        if flag.is_set(): state=State.IDLE; continue
        context+=f"USER: {transcript}\nGPT: {ans}\n"; GPIO.output(AMP_SD_PIN,GPIO.HIGH)
        flag.monitoring_enabled=True; state=State.WAIT_TTS; api.stream_tts_and_play(ans); flag.monitoring_enabled=False
        GPIO.output(AMP_SD_PIN,GPIO.LOW); state=State.IDLE

if __name__=="__main__":
    try: main()
    finally: GPIO.cleanup()
