from libraries.media_device_manager import MediaDeviceManager
from libraries.api_handler import APIHandler
from libraries.sys_config import SystemConfig
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
from libraries.config import config
import libraries.config
import time
import os


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

    restart = 0 #TODO implement an exit/restart mechanism
    default_prompt = "Describe what you see in front of you"
    context_window = "Context: \n"

    while(not restart):
        # In case of an interrupt, give some room so you don't immediately take another picture
        if api_handler.canceled == 1:
            time.sleep(1)
        api_handler.canceled = 0
        button_pressed = 0

        api_handler.text_to_speech("Press the front button")
        button_time = time.time()
        while GPIO.input(22) == GPIO.HIGH and (button_time - time.time() < 5):
            button_pressed = 0
        
        if GPIO.input(22) == GPIO.LOW:
            api_handler.text_to_speech("front button is working")
            print("front button is working")
        else:
            api_handler.text_to_speech("front button was not working")
            print("front button is not working")
           
        api_handler.text_to_speech("Press the back button")
        while GPIO.input(27) == GPIO.HIGH and (button_time - time.time() < 5):
            button_pressed = 0
        
        if GPIO.input(27) == GPIO.LOW:
            print("back button is working")
            api_handler.text_to_speech("back button is working")
        else:
            api_handler.text_to_speech("back button was not working")
            print("back button is not working")

        output_file = "audio/audio.wav"
        
        if os.path.exists(output_file):
            os.remove(output_file)
        
        api_handler.text_to_speech("speak for up to five second")
        recording_time = time.time()
        device.start_recording(output_file)
        time.sleep(5)
        device.stop_recording()
        if os.path.exists(output_file):
            api_handler.text_to_speech("recording is working")
            print("recording is working")
        else:
            api_handler.text_to_speech("recording is not working")
            print("recording is not working")
        
        output_image = "images/temp_image.jpg"

        if os.path.exists(output_image):
            os.remove(output_image)
        
        device.capture_image(output_image)
        time.sleep(1)

        if os.path.exists(output_image):
            api_handler.text_to_speech("camera is working")
            print("camera is working")
        else:
            api_handler.text_to_speech("camera is not working")
            print("camera is not working")

        temp_prompt = "What is the result of 2+2"
        response = api_handler.gpt_request(temp_prompt)
        if response is not None:
            api_handler.text_to_speech("GPT text is working")
            print("GPT text is working")
        else:
            api_handler.text_to_speech("GPT text is working")
            print("GPT text is working")
        if response == "the result of 2 + 2 is 4":
            print ("accuracy?")
        
        photo_path = "images/temp_image.jpg"
        response = api_handler.gpt_image_request("Describe this image", photo_path)

        if response is not None:
            api_handler.text_to_speech("GPT image request was successful")
            print("GPT image request was successful")
        else:
            api_handler.text_to_speech("GPT image request was not successful")
            print("GPT image request not successful")
        
    # Clean up resources
    device.close()

if __name__ == '__main__':
    main()
