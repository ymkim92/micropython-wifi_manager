from wifi_manager.manager import WifiManager
import utime

# Example of usage

wm = WifiManager()
wm.connect()

while True:
    if wm.is_connected():
        print("Connected!")
    else:
        print("Disconnected!")
    utime.sleep(10)
