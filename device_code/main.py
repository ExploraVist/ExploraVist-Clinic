from libraries.media_device_manager import MediaDeviceManager
from libraries.api_handler import APIHandler
from libraries.sys_config import SystemConfig
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
from libraries.config import config
import libraries.config
import time
import threading
import pyttsx3

def check_gpio_state(expected_state, AMP_SD):
    """Checks if GPIO state matches the expected state."""
    actual_state = GPIO.input(AMP_SD)
    if actual_state == expected_state:
        print(f"✅ GPIO {AMP_SD} is {'HIGH (ON)' if actual_state else 'LOW (OFF)'} as expected.")
    else:
        print(f"❌ ERROR: GPIO {AMP_SD} is {'HIGH (ON)' if actual_state else 'LOW (OFF)'} but expected {'HIGH (ON)' if expected_state else 'LOW (OFF)'}!")



def main():
    # Initialize GPIO first
    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BCM)  # Use physical pin numbering

    # Set pin 22 to pull up (normally closed)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Set pin 27 to pul up (normally closed)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Shutdown Pin on Amplifier
    AMP_SD_PIN = 26
    GPIO.setup(AMP_SD_PIN, GPIO.OUT)
    GPIO.output(AMP_SD_PIN, GPIO.LOW)

    check_gpio_state(GPIO.LOW, AMP_SD_PIN)  # Verify if the pin is LOW

    # Initialize classes
    sys_config = SystemConfig()
    if not sys_config.check_system_ready():
        print("System not ready. Exiting.")
        GPIO.cleanup()  # Clean up GPIO before exiting
        return
    print(config)
    device = MediaDeviceManager()
    api_handler = APIHandler(config=config) 

    restart = 0 #TODO implement an exit/restart mechanism
    default_prompt = "Describe what you see in front of you"
    context_window = "Context: \n"

    while(not restart):
        # In case of an interrupt, give some room so you don't immediately take another picture
        if api_handler.canceled == 1:
            time.sleep(1)
        api_handler.canceled = 0
        button_pressed = 0

        start_time = time.time()
        while GPIO.input(22) == GPIO.LOW or GPIO.input(27) == GPIO.LOW:
            #api_handler.live_transcription_from_mic()
            #api_handler.stream_live_recording_to_deepgram()
            device.start_recording()
            if GPIO.input(22) == GPIO.LOW:
                button_pressed = 2
            elif GPIO.input(27) == GPIO.LOW:
                button_pressed = 1

        device.stop_recording()
        time_pressed = time.time() - start_time

        if time_pressed <= 1.6 and time_pressed >= 0.1: # Image Description Using Default Prompt
            
            # Image Response
            if button_pressed == 2:
                # Take image
                device.capture_image()
                temp_prompt = context_window + f"Current Question: {default_prompt} \n"

                # Play Starting Sound
                api_handler.play_audio("audio_files/start_sound.wav")

                # Make LLM API Call
                begin = time.time()
                text_response = api_handler.gpt_image_request2(temp_prompt)
                context_window += f"USER: {default_prompt} \n GPT: {text_response} \n"

                # Check that pin is low
                check_gpio_state(GPIO.LOW,AMP_SD_PIN)

                # Turn On Speaker
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)

                # Check that pin is low
                check_gpio_state(GPIO.HIGH,AMP_SD_PIN)
                time.sleep(0.1) 

                # Convert LLM Response to Audio

                end = time.time()
                #api_handler.stream_tts(text_response)
                api_handler.stream_tts_and_play(text_response)
                print ("text to speech")
                print (end, begin, end-begin)
                
                #api_handler.play_audio()

                


        elif time_pressed > 1.5:
            if button_pressed == 2:   # Image with Custom Prompt
                # Take image
                device.capture_image()
                api_handler.play_audio("audio_files/start_sound.wav")
                # Speech to Text
                #transcript = api_handler.stream_wav_file_to_deepgram("audio/audio.wav")
                transcript =  api_handler.audio_to_text("audio/audio.wav")
                temp_prompt = context_window + f"Current Question: {transcript} \n"


                # Play Starting Sound


                # Make LLM API Call with Custom Prompt
                begin = time.time()
                text_response = api_handler.gpt_image_request_word_by_word(temp_prompt)
                context_window += f"USER: {transcript} \n GPT: {text_response} \n"

                # Check that pin is low
                check_gpio_state(GPIO.LOW,AMP_SD_PIN)

                # Turn On Speaker
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)
                

                # Check that pin is low
                check_gpio_state(GPIO.HIGH,AMP_SD_PIN)
                time.sleep(2) 

                # Convert LLM Response to Audio
                end = time.time()
                #api_handler.stream_tts(text_response)
                #api_handler.stream_tts_and_play(text_response)
                print ("text to speech")
                print (end, begin, end-begin)
                
                #api_handler.play_audio()


            elif button_pressed == 1: # Custom Prompt Only
                # Speech to Text
                transcript = api_handler.audio_to_text()
                temp_prompt = context_window + f"Current Question: {transcript} \n"

                # Make LLM API Call with Custom Prompt
                text_response = api_handler.gpt_request2(temp_prompt)
                context_window += f"USER: {transcript} \n GPT: {text_response} \n"

                # Check that pin is low
                check_gpio_state(GPIO.LOW,AMP_SD_PIN)

                # Turn On Speaker
                GPIO.output(AMP_SD_PIN, GPIO.HIGH)

                # Check that pin is low
                check_gpio_state(GPIO.HIGH,AMP_SD_PIN)
                time.sleep(0.1) 

                # Convert LLM Response to Audio

                begin = time.time()
                api_handler.stream_tts_and_play(text_response)
                end = time.time()
                print (end-begin)

                
            else:
                continue
                #print("waiting for input")
            

    # Clean up resources
    device.close()
    GPIO.cleanup()  # Clean up GPIO before exiting

if __name__ == '__main__':
    main()
