from picamera2 import Picamera2
from picamera2.previews import QtGlPreview

# initialize the camera
picam2 = Picamera2()

# Configure camera for preview
config = picam2.create_preview_configuration()
picam2.configure(config)

# Use a Qt-based preview window
picam2.start_preview(QtGlPreview())

# Enable continuous autofocus
picam2.set_controls({"AfMode": 2}) # 2 = Continuous Autofocus

# Starte the camera
picam2.start()

print("Autofocus enabled. Live preview active. Press CtrlC to stop.")
try:
    while True:
        pass # Keep running preview
except KeyboardInterrupt:
    print("Stopping preview...")
    picam2.stop_preview()
    picam2.stop()
