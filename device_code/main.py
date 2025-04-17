from libraries.media_device_manager import MediaDeviceManager
from libraries.api_handler import APIHandler
from libraries.sys_config import SystemConfig
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
from libraries.config import config
import libraries.config
import time
import pyttsx3

def check_gpio_state(expected_state, AMP_SD):
    """Checks if GPIO state matches the expected state."""
    actual_state = GPIO.input(AMP_SD)
    if actual_state == expected_state:
        print(f"✅ GPIO {AMP_SD} is {'HIGH (ON)' if actual_state else 'LOW (OFF)'} as expected.")
    else:
        print(
            f"❌ ERROR: GPIO {AMP_SD} is {'HIGH (ON)' if actual_state else 'LOW (OFF)'} "
            f"but expected {'HIGH (ON)' if expected_state else 'LOW (OFF)'}!"
        )

def main():
    # Initialize GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Input buttons (pulled up)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Image button
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Mic button

    # Amplifier shutdown control
    AMP_SD_PIN = 26
    GPIO.setup(AMP_SD_PIN, GPIO.OUT)
    GPIO.output(AMP_SD_PIN, GPIO.LOW)
    check_gpio_state(GPIO.LOW, AMP_SD_PIN)

    # System readiness
    sys_config = SystemConfig()
    if not sys_config.check_system_ready():
        print("System not ready. Exiting.")
        GPIO.cleanup()
        return

    device = MediaDeviceManager()
    api_handler = APIHandler(config=config)

    # Startup sound
    api_handler.play_audio("audio_files/startup.wav")

    restart = False
    default_prompt = "Describe what you see in front of you"
    context_window = "Context:\n"

    # Timing thresholds
    THRESHOLD = 1.5    # seconds to distinguish tap vs. hold
    MIN_PRESS  = 0.01  # ignore very quick blips

    while not restart:
        # Debounce if last TTS was canceled
        if api_handler.canceled:
            time.sleep(1)
        api_handler.canceled = 0

        # Wait for button press
        button_pressed = None
        start_time = None

        while True:
            if GPIO.input(22) == GPIO.LOW:
                button_pressed = 2
                start_time = time.time()
                device.start_recording()
                break
            if GPIO.input(27) == GPIO.LOW:
                button_pressed = 1
                start_time = time.time()
                device.start_recording()
                break
            time.sleep(0.01)

        # Wait for release
        while GPIO.input(22) == GPIO.LOW or GPIO.input(27) == GPIO.LOW:
            time.sleep(0.01)
        device.stop_recording()

        time_pressed = time.time() - start_time

        # Ignore very short presses
        if time_pressed < MIN_PRESS:
            continue

        # SHORT TAP (<= THRESHOLD)
        if time_pressed <= THRESHOLD:
            if button_pressed == 2:
                # Image with default prompt
                test_time = time.time()
                api_handler.play_audio_nonblocking("audio_files/taking_picture.wav")
                print(f"Time taken to play audio: {time.time() - test_time:.2f}s") # This is for testing purposes
                device.capture_image()
                

                prompt = context_window + f"Current Question: {default_prompt}\n"
                begin = time.time()
                text_response = api_handler.gpt_image_request2(prompt)
                end = time.time()

                context_window += f"USER: {default_prompt}\nGPT: {text_response}\n"

                check_gpio_state(GPIO.LOW, AMP_SD_PIN)
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)
                check_gpio_state(GPIO.HIGH, AMP_SD_PIN)

                api_handler.stream_tts_and_play(text_response)
                print(f"⏱ LLM call took {end - begin:.2f}s")

            elif button_pressed == 1:
                # Mic button tapped too quickly
                api_handler.play_audio("audio_files/hold_button.wav")

        # LONG HOLD (> THRESHOLD)
        else:
            if button_pressed == 2:
                # Image + custom speech prompt
                device.capture_image()
                api_handler.play_audio("audio_files/start_sound.wav")

                transcript = api_handler.audio_to_text("audio/audio.wav")
                prompt = context_window + f"Current Question: {transcript}\n"
                begin = time.time()
                text_response = api_handler.gpt_image_request2(prompt)
                end = time.time()

                context_window += f"USER: {transcript}\nGPT: {text_response}\n"

                check_gpio_state(GPIO.LOW, AMP_SD_PIN)
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)
                check_gpio_state(GPIO.HIGH, AMP_SD_PIN)

                api_handler.stream_tts_and_play(text_response)
                print(f"⏱ LLM call took {end - begin:.2f}s")

            elif button_pressed == 1:
                # Mic-only Q&A
                transcript = api_handler.audio_to_text("audio/audio.wav")
                prompt = context_window + f"Current Question: {transcript}\n"
                begin = time.time()
                text_response = api_handler.gpt_image_request2(prompt)
                end = time.time()

                context_window += f"USER: {transcript}\nGPT: {text_response}\n"

                check_gpio_state(GPIO.LOW, AMP_SD_PIN)
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)
                check_gpio_state(GPIO.HIGH, AMP_SD_PIN)

                api_handler.stream_tts_and_play(text_response)
                print(f"⏱ LLM call took {end - begin:.2f}s")

    # Cleanup
    device.close()
    GPIO.cleanup()

if __name__ == "__main__":
    main()
