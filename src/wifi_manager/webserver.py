import re
import socket
import time
import machine
from .network_utils import url_decode, read_credentials, write_credentials

class WebServer:
    def __init__(self, manager):
        self.manager = manager
        self.wlan_ap = manager.wlan_ap
        self.wlan_sta = manager.wlan_sta
        self.ap_ssid = manager.ap_ssid
        self.ap_password = manager.ap_password
        self.ap_authmode = manager.ap_authmode
        self.reboot = manager.reboot
        self.debug = manager.debug
        self.wifi_credentials = manager.wifi_credentials

    def run(self):
        self.wlan_ap.active(True)
        self.wlan_ap.config(
            essid=self.ap_ssid, password=self.ap_password, authmode=self.ap_authmode
        )
        server_socket = socket.socket()
        server_socket.close()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", 80))
        server_socket.listen(1)
        print(
            "Connect to",
            self.ap_ssid,
            "with the password",
            self.ap_password,
            "and access the captive portal at",
            self.wlan_ap.ifconfig()[0],
        )
        while True:
            if self.wlan_sta.isconnected():
                self.wlan_ap.active(False)
                if self.reboot:
                    print("The device will reboot in 5 seconds.")
                    time.sleep(5)
                    machine.reset()
            client, addr = server_socket.accept()
            try:
                client.settimeout(5.0)
                request = b""
                try:
                    while True:
                        if b"\r\n\r\n" in request:
                            request += client.recv(512)
                            break
                        request += client.recv(128)
                except Exception as error:
                    if self.debug:
                        print(error)
                    pass
                if request:
                    if self.debug:
                        print(url_decode(request, self.debug))
                    url = (
                        re.search(b"(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request)
                        .group(1)
                        .decode("utf-8")
                        .rstrip("/")
                    )
                    if url == "":
                        self.handle_root(client)
                    elif url == "configure":
                        self.handle_configure(client, request)
                    else:
                        self.handle_not_found(client)
            except Exception as error:
                if self.debug:
                    print(error)
                return
            finally:
                client.close()

    def send_header(self, client, status_code=200):
        client.send("""HTTP/1.1 {0} OK\r\n""".format(status_code))
        client.send("""Content-Type: text/html\r\n""")
        client.send("""Connection: close\r\n""")

    def send_response(self, client, payload, status_code=200):
        self.send_header(client, status_code)
        client.sendall(
            """
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <title>WiFi Manager</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <link rel="icon" href="data:,">
                </head>
                <body>
                    {0}
                </body>
            </html>
        """.format(payload)
        )
        client.close()

    def handle_root(self, client):
        self.send_header(client)
        client.sendall("""
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <title>WiFi Manager</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <link rel="icon" href="data:,">
                </head>
                <body>
                    <h1>WiFi Manager</h1>
                    <form action="/configure" method="post" accept-charset="utf-8">
        """)
        for ssid, *_ in self.wlan_sta.scan():
            ssid = ssid.decode("utf-8")
            client.sendall(
                """
                        <p><input type="radio" name="ssid" value="{0}" id="{0}">
                        <label for="{0}">&nbsp;{0}</label></p>
            """.format(ssid)
            )
        client.sendall("""
                        <p><label for="password">Password:&nbsp;</label>
                            <input type="password" id="password" name="password"></p>
                        <p><input type="submit" value="Connect"></p>
                    </form>
                </body>
            </html>
        """)
        client.close()

    def handle_configure(self, client, request):
        match = re.search(b"ssid=([^&]*)&password=(.*)", url_decode(request, self.debug))
        if match:
            ssid = match.group(1).decode("utf-8")
            password = match.group(2).decode("utf-8")
            if len(ssid) == 0:
                self.send_response(
                    client,
                    """
                    <p>SSID must be provided!</p>
                    <p>Go back and try again!</p>
                """,
                    400,
                )
            elif self.manager.wifi_connect(ssid, password):
                self.send_response(
                    client,
                    """
                    <p>Successfully connected to</p>
                    <h1>{0}</h1>
                    <p>IP address: {1}</p>
                """.format(ssid, self.wlan_sta.ifconfig()[0])
                )
                profiles = read_credentials(self.wifi_credentials, self.debug)
                profiles[ssid] = password
                write_credentials(self.wifi_credentials, profiles)
                time.sleep(5)
            else:
                self.send_response(
                    client,
                    """
                    <p>Could not connect to</p>
                    <h1>{0}</h1>
                    <p>Go back and try again!</p>
                """.format(ssid)
                )
                time.sleep(5)
        else:
            self.send_response(
                client,
                """
                <p>Parameters not found!</p>
            """,
                400,
            )
            time.sleep(5)

    def handle_not_found(self, client):
        self.send_response(
            client,
            """
            <p>Page not found!</p>
        """,
            404,
        )