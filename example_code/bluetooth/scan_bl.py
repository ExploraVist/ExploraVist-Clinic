import subprocess
import time

def run_bluetoothctl_cmd(cmd):
    """
    Runs a single command in bluetoothctl and returns the output as a list of lines.
    """
    process = subprocess.Popen(
        ['bluetoothctl'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = process.communicate(cmd)
    return out.split('\n')

def scan_devices(timeout=5):
    """
    Scans for bluetooth devices by using bluetoothctl. Returns a list of (MAC, NAME).
    """
    # Start scanning
    run_bluetoothctl_cmd('scan on\n')
    print("Scanning for devices...")
    time.sleep(timeout)
    # Stop scanning
    run_bluetoothctl_cmd('scan off\n')

    # Get list of devices
    output = run_bluetoothctl_cmd('devices\n')
    devices = []
    for line in output:
        # Typical line format: "Device AA:BB:CC:DD:EE:FF DeviceName"
        if "Device" in line:
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                mac = parts[1]
                name = parts[2]
                devices.append((mac, name))
    return devices

def pair_and_connect(mac_address):
    """
    Pair and connect to a device with the given MAC address.
    """
    # Pair
    run_bluetoothctl_cmd(f'pair {mac_address}\n')
    # Trust
    run_bluetoothctl_cmd(f'trust {mac_address}\n')
    # Connect
    run_bluetoothctl_cmd(f'connect {mac_address}\n')

if __name__ == '__main__':
    found = scan_devices()
    for mac, name in found:
        print(f"{mac} - {name}")

    # Suppose we see a device we want to connect to:
    target_mac = "AA:BB:CC:DD:EE:FF"
    pair_and_connect(target_mac)
