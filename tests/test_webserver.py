import sys
import types

if "machine" not in sys.modules:
    sys.modules["machine"] = types.ModuleType("machine")
    sys.modules["machine"].reset = lambda: None

import pytest
from unittest.mock import MagicMock, patch
from wifi_manager.webserver import WebServer


class DummyManager:
    def __init__(self):
        self.wlan_ap = MagicMock()
        self.wlan_sta = MagicMock()
        self.ap_ssid = "TestSSID"
        self.ap_password = "TestPass123"
        self.ap_authmode = 3
        self.reboot = False
        self.debug = False
        self.wifi_credentials = "wifi.dat"

    def wifi_connect(self, ssid, password):
        return ssid == "ssid1" and password == "pass1"


@pytest.fixture
def webserver():
    manager = DummyManager()
    return WebServer(manager)


def test_send_header_and_response(webserver):
    client = MagicMock()
    webserver.send_header(client, status_code=201)
    assert client.send.call_count == 3
    client.reset_mock()
    webserver.send_response(client, "<p>hello</p>", status_code=202)
    assert client.sendall.called


def test_handle_not_found(webserver):
    client = MagicMock()
    webserver.handle_not_found(client)
    assert client.sendall.called


def test_handle_root(webserver):
    client = MagicMock()
    # Mock scan to return two SSIDs
    webserver.wlan_sta.scan.return_value = [(b"ssid1",), (b"ssid2",)]
    webserver.handle_root(client)
    assert client.sendall.called


def test_handle_configure_success(monkeypatch, webserver):
    client = MagicMock()
    # Patch url_decode to simulate a valid POST
    with patch("wifi_manager.webserver.url_decode", return_value=b"ssid=ssid1&password=pass1"):
        with patch("time.sleep", return_value=None):
            webserver.handle_configure(client, b"dummy")
    assert client.sendall.called


def test_handle_configure_failure(monkeypatch, webserver):
    client = MagicMock()
    # Patch url_decode to simulate a missing SSID
    with patch("wifi_manager.webserver.url_decode", return_value=b"ssid=&password=pass1"):
        with patch("time.sleep", return_value=None):
            webserver.handle_configure(client, b"dummy")
    assert client.sendall.called
    # Patch url_decode to simulate missing parameters
    with patch("wifi_manager.webserver.url_decode", return_value=b""):
        with patch("time.sleep", return_value=None):
            webserver.handle_configure(client, b"dummy")
    assert client.sendall.called
