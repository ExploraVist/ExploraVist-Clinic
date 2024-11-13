from libraries.media_device_manager import MediaDeviceManager
from libraries.api_handler import APIHandler
from libraries.config_checker import ConfigurationChecker
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import config
import time

end = 0
default_prompt = "Describe what you see in front of you."

def main():
    # Initialize classes
    config_checker = ConfigurationChecker()
    if not config_checker.check_system_ready():
        print("System not ready. Exiting.")
        return

    device = MediaDeviceManager()
    api_handler = APIHandler(config=config) 

    while(not end):
        start_time = time.time()
        while GPIO.input(22) == GPIO.LOW:
            device.start_recording()

        device.stop_recording()
        time_pressed = time.time() - start_time

        if time_pressed <= 1.5:
            # Image Description Using Default Prompt


            # Take image
            device.capture_image(default_prompt)
            # Make LLM API Call
            text_response = api_handler.gpt_image_request()
            # Convert LLM Response to Audio
            api_handler.text_to_speech(text_response)
        
        else:
            
        


    # Clean up resources
    device.close()

if __name__ == '__main__':
    main()
