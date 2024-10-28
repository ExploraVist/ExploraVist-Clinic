import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

def button_callback(channel):
	print("Button was pushed!")

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BCM) # Use physical pin numbering

GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 22 to pull up (normally closed)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 27 to pull up (normally closed)

i=0
while True: # Run forever
    if GPIO.input(22) == GPIO.LOW:
        i+=1
        print("Back button was pushed!" + str(i))
    if GPIO.input(27) == GPIO.LOW:
        print("Front button was pushed!")

#GPIO.add_event_detect(22,GPIO.RISING,callback=button_callback) # Setup event on pin 13 rising edge

#message = input("Press enter to quit\n\n") # Run until someone presses enter

#GPIO.cleanup() # Clean up
