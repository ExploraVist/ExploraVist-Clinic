# Class will check system configuration files on the Pi Zero 2W

import subprocess

def get_volume():
    """Get the current system volume."""
    result = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True)
    if result.returncode == 0:
        volume_line = result.stdout.split("\n")[0]
        return volume_line.split("/")[1].strip()
    return "Error fetching volume"

def set_volume(volume):
    """Set the system volume (0-100%)."""
    volume = max(0, min(100, volume))  # Ensure volume is in range
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"])

def increase_volume(step=5):
    """Increase volume by a given step."""
    current_volume = int(get_volume().replace("%", ""))
    set_volume(current_volume + step)

def decrease_volume(step=5):
    """Decrease volume by a given step."""
    current_volume = int(get_volume().replace("%", ""))
    set_volume(current_volume - step)

def mute_audio():
    """Toggle mute on/off."""
    subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])

# Example usage
if __name__ == "__main__":
    print(f"Current volume: {get_volume()}")
    increase_volume()
    print(f"New volume after increase: {get_volume()}")


class SystemConfig:
    def __init__(self):
        self.system_read = True
        self.volume = 50
        
    def get_volume(self):
        """Get the current system volume."""
        result = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True)
        if result.returncode == 0:
            volume_line = result.stdout.split("\n")[0]
            return volume_line.split("/")[1].strip()
        return "Error fetching volume"
    
    def set_volume(self, volume):
        """Set the system volume (0-100%)."""
        volume = max(0, min(100, volume))  # Ensure volume is in range
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"])

    def increase_volume(self, step=5):
    
    def check_system_ready(self): 
        #TODO Implement system_read check
        # - Checks for proper system audio config files
        # - Checks for WiFi access
        # - Checks for SystemCTL file changes / settings
        # - Checks for software updates

        return True 
