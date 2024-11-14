from libraries.media_device_manager import MediaDeviceManager
from libraries.api_handler import APIHandler
from libraries.sys_config import SystemConfig
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
from libraries.config import config
import libraries.config
import time

restart = 0 #TODO implement an exit/restart mechanism
default_prompt = "Describe what you see in front of you."

def main():
    # Initialize classes
    sys_config = SystemConfig()
    if not sys_config.check_system_ready():
        print("System not ready. Exiting.")
        return
    print(config)
    device = MediaDeviceManager()
    api_handler = APIHandler(config=config) 
    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BCM)  # Use physical pin numbering

    # Set pin 22 to pull up (normally closed)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Set pin 27 to pul up (normally closed)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while(not restart):
        # In case of an interrupt, give some room so you don't immediately take another picture
        if api_handler.canceled == 1:
            time.sleep(1)
        api_handler.canceled = 0

        start_time = time.time()
        while GPIO.input(22) == GPIO.LOW:
            device.start_recording()


        device.stop_recording()
        time_pressed = time.time() - start_time

        if time_pressed <= 1.5 and time_pressed >= 0.1: # Image Description Using Default Prompt
            # Take image
            device.capture_image()

            # Make LLM API Call
            text_response = api_handler.gpt_image_request(default_prompt)

            # Convert LLM Response to Audio
            api_handler.text_to_speech(text_response)

        elif time_pressed > 1.5:
            # Take image
            device.capture_image()

            # Speech to Text
            transcript = api_handler.audio_to_text()

            # Make LLM API Call with Custom Prompt
            text_response = api_handler.gpt_image_request(transcript)

            # Convert LLM Response to Audio
            api_handler.text_to_speech(text_response)
        else:
            continue
            #print("waiting for input")

        


    # Clean up resources
    device.close()

if __name__ == '__main__':
    main()
