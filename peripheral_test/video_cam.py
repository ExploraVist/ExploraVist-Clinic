from picamzero import Camera

cam = Camera()
#cam.start_preview()
print("recording")
cam.record_video("new_video.mp4", duration=20)
#cam.stop_preview()
print("Finished")

