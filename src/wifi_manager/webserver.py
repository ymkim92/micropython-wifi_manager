import re
import socket
import time
import machine
from .network_utils import url_decode, read_credentials, write_credentials


class WebServer:
    def __init__(self, manager, sleep_fn=time.sleep, reset_fn=machine.reset, debug=False):
        self.manager = manager
        self.wlan_ap = manager.wlan_ap
        self.wlan_sta = manager.wlan_sta
        self.ap_ssid = manager.ap_ssid
        self.ap_password = manager.ap_password
        self.ap_authmode = manager.ap_authmode
        self.reboot = manager.reboot
        self.debug = debug
        self.wifi_credentials = manager.wifi_credentials
        self.sleep_fn = sleep_fn  # Dependency injection for time.sleep
        self.reset_fn = reset_fn  # Dependency injection for machine.reset

    def _reboot_device(self):
        """Reboot the device after a delay."""
        if self.reboot:
            print("The device will reboot in 5 seconds.")
            self.sleep_fn(5)
            self.reset_fn()

    def _create_server_socket(self):
        """Create and configure the server socket."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", 80))
        server_socket.listen(1)
        return server_socket

    def _parse_request(self, request):
        """Parse the HTTP request and extract the URL."""
        try:
            url = (
                re.search(b"(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request)
                .group(1)
                .decode("utf-8")
                .rstrip("/")
            )
            return url
        except Exception as error:
            if self.debug:
                print(f"Error parsing request: {error}")
            return None

    def _handle_client(self, client):
        """Handle a single client connection."""
        try:
            client.settimeout(5.0)
            request = b""
            while True:
                chunk = client.recv(128)
                if not chunk:
                    break
                request += chunk
                if b"\r\n\r\n" in request:
                    break

            if self.debug:
                print(f"Request received: {request}")

            url = self._parse_request(request)
            if url == "":
                self.handle_root(client)
            elif url == "configure":
                print(f"##########request {request}")
                self.handle_configure(client, request)
            else:
                self.handle_not_found(client)
        except Exception as error:
            if self.debug:
                print(f"Error handling client: {error}")
        finally:
            client.close()

    def run(self):
        """Start the web server."""
        self.wlan_ap.active(True)
        self.wlan_ap.config(
            essid=self.ap_ssid, password=self.ap_password, authmode=self.ap_authmode
        )
        print(
            f"Connect to {self.ap_ssid} with the password {self.ap_password} "
            f"and access the captive portal at {self.wlan_ap.ifconfig()[0]}"
        )

        server_socket = self._create_server_socket()
        while True:
            if self.wlan_sta.isconnected():
                self.wlan_ap.active(False)
                self._reboot_device()
                return  # just for testing

            client, _ = server_socket.accept()
            self._handle_client(client)

    def send_header(self, client, status_code=200):
        """Send HTTP headers to the client."""
        client.send(f"HTTP/1.1 {status_code} OK\r\n".encode("utf-8"))
        client.send("Content-Type: text/html\r\n".encode("utf-8"))
        client.send("Connection: close\r\n\r\n".encode("utf-8"))

    def send_response(self, client, payload, status_code=200):
        """Send an HTTP response with HTML content."""
        self.send_header(client, status_code)
        client.sendall(
            f"""
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <title>WiFi Manager</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <link rel="icon" href="data:,">
                </head>
                <body>
                    {payload}
                </body>
            </html>
            """.encode("utf-8")
        )
        client.close()

    def handle_root(self, client):
        """Handle the root URL."""
        ssid_options = "".join(
            f"""
            <p><input type="radio" name="ssid" value="{ssid.decode("utf-8")}" id="{ssid.decode("utf-8")}">
            <label for="{ssid.decode("utf-8")}">&nbsp;{ssid.decode("utf-8")}</label></p>
            """
            for ssid, *_ in self.wlan_sta.scan()
        )
        self.send_response(
            client,
            f"""
            <h1>WiFi Manager</h1>
            <form action="/configure" method="post" accept-charset="utf-8">
                {ssid_options}
                <p><label for="password">Password:&nbsp;</label>
                <input type="password" id="password" name="password"></p>
                <p><input type="submit" value="Connect"></p>
            </form>
            """,
        )

    def handle_configure(self, client, request):
        """Handle the configure URL."""
        match = re.search(b"ssid=([^&]*)&password=(.*)", url_decode(request))
        if not match:
            self.send_response(client, "<p>Parameters not found!</p>", 400)
            return

        ssid = match.group(1).decode("utf-8")
        password = match.group(2).decode("utf-8")

        if not ssid:
            self.send_response(
                client, "<p>SSID must be provided!</p><p>Go back and try again!</p>", 400
            )
        elif self.manager.wifi_connect(ssid, password):
            self.send_response(
                client,
                f"<p>Successfully connected to</p><h1>{ssid}</h1><p>IP address: {self.wlan_sta.ifconfig()[0]}</p>",
            )
            profiles = read_credentials(self.wifi_credentials, self.debug)
            profiles[ssid] = password
            write_credentials(self.wifi_credentials, profiles)
            self._reboot_device()
        else:
            self.send_response(
                client, f"<p>Could not connect to</p><h1>{ssid}</h1><p>Go back and try again!</p>"
            )
            self.sleep_fn(5)

    def handle_not_found(self, client):
        """Handle unknown URLs."""
        self.send_response(client, "<p>Page not found!</p>", 404)
