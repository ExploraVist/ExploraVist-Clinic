## config.py Format:

config = {
    "DEEPGRAM_API_KEY": config.DEEPGRAM_API_KEY
    "GPT_API_KEY": config.GPT_API_KEY,
}

## Folder Structure:

```
project_root/
│
├── main.py               # The main entry point for your application
│
├── config.py             # Configuration file (API keys, constants, etc.)
│
├── libraries/            # Folder for reusable libraries or classes
│   ├── media_device_manager.py   # The class handling PyAudio, Picamera2, and audio playback
│   ├── api_handler.py            # Class for handling API interactions (e.g., OpenAI, Deepgram)
│   └── sys_config.py             # Class for checking system configurations on the Pi Zero 2 W
│
├── audio/                # Folder to store recorded audio files
│   └── output.wav
│
├── images/               # Folder to store captured images
│   └── captured_image.jpg
│
└── requirements.txt      # Dependencies for the project
```
