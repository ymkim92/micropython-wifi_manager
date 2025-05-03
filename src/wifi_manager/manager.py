import network
import time
from .network_utils import read_credentials
from .webserver import WebServer


class WifiManager:
    def __init__(self, ssid="WifiManager", password="wifimanager", reboot=True, debug=False):
        self.wlan_sta = network.WLAN(network.STA_IF)
        self.wlan_sta.active(True)
        self.wlan_ap = network.WLAN(network.AP_IF)

        if len(ssid) > 32:
            raise Exception("The SSID cannot be longer than 32 characters.")
        else:
            self.ap_ssid = ssid
        if len(password) < 8:
            raise Exception("The password cannot be less than 8 characters long.")
        else:
            self.ap_password = password

        self.ap_authmode = 3
        self.wifi_credentials = "wifi.dat"
        self.wlan_sta.disconnect()
        self.reboot = reboot
        self.debug = debug

    def connect(self):
        if self.wlan_sta.isconnected():
            return
        profiles = read_credentials(self.wifi_credentials, self.debug)
        for ssid, *_ in self.wlan_sta.scan():
            ssid = ssid.decode("utf-8")
            if ssid in profiles:
                password = profiles[ssid]
                if self.wifi_connect(ssid, password):
                    return
        print("Could not connect to any WiFi network. Starting the configuration portal...")
        self.web_server()

    def disconnect(self):
        if self.wlan_sta.isconnected():
            self.wlan_sta.disconnect()

    def is_connected(self):
        return self.wlan_sta.isconnected()

    def get_address(self):
        return self.wlan_sta.ifconfig()

    def wifi_connect(self, ssid, password):
        print("Trying to connect to:", ssid)
        self.wlan_sta.connect(ssid, password)
        for _ in range(100):
            if self.wlan_sta.isconnected():
                print("\nConnected! Network information:", self.wlan_sta.ifconfig())
                return True
            else:
                print(".", end="")
                time.sleep_ms(100)
        print("\nConnection failed!")
        self.wlan_sta.disconnect()
        return False

    def web_server(self):
        server = WebServer(self)
        server.run()
