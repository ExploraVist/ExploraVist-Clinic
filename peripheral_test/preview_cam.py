from picamzero import Camera
from time import sleep

cam = Camera()
print("initialized camera")
cam.start_preview()
print("initialized preview")
sleep(5)
print("exiting")
