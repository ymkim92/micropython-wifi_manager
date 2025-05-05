import sys
import types

if "machine" not in sys.modules:
    sys.modules["machine"] = types.ModuleType("machine")
    sys.modules["machine"].reset = lambda: None

import pytest
from unittest.mock import MagicMock, patch, Mock
from wifi_manager.webserver import WebServer


@pytest.fixture
def mock_manager():
    mock = Mock()
    mock.wlan_ap.ifconfig.return_value = ["192.168.4.1"]
    mock.wlan_sta.isconnected.return_value = False
    mock.wlan_sta.scan.return_value = [(b"TestSSID",)]
    mock.ap_ssid = "MyAP"
    mock.ap_password = "password123"
    mock.ap_authmode = 3
    mock.reboot = False
    mock.wifi_credentials = "wifi.dat"
    mock.wifi_connect.return_value = True
    return mock


# def test_reboot_device(mock_manager):
#     server = WebServer(mock_manager)
#     url = server._reboot_device(request)
#     assert url == "configure"


def test_parse_request_valid(mock_manager):
    server = WebServer(mock_manager)
    request = b"GET /configure HTTP/1.1\r\n\r\n"
    url = server._parse_request(request)
    assert url == "configure"


def test_parse_request_invalid(mock_manager, capsys):
    server = WebServer(mock_manager, debug=True)
    request = b"BAD REQUEST"
    url = server._parse_request(request)
    captured = capsys.readouterr()
    assert url is None
    assert "Error parsing request" in captured.out


def test_send_header(mock_manager):
    server = WebServer(mock_manager)
    client = MagicMock()
    server.send_header(client)
    assert client.send.call_count == 3


def test_send_response(mock_manager):
    server = WebServer(mock_manager)
    client = MagicMock()
    server.send_response(client, "<h1>Hello</h1>")
    client.sendall.assert_called()
    client.close.assert_called()


def test_handle_root(mock_manager):
    server = WebServer(mock_manager)
    client = MagicMock()
    server.handle_root(client)
    client.sendall.assert_called()


@patch("wifi_manager.webserver.url_decode")
@patch("wifi_manager.webserver.read_credentials", return_value={})
@patch("wifi_manager.webserver.write_credentials")
def test_handle_configure_success(mock_write, mock_read, mock_decode, mock_manager):
    mock_decode.return_value = b"ssid=TestSSID&password=abc123"
    server = WebServer(mock_manager, sleep_fn=lambda x: None, reset_fn=lambda: None)
    client = MagicMock()
    mock_manager.wlan_sta.ifconfig.return_value = ["192.168.4.1"]
    server.handle_configure(client, b"dummy request")
    client.sendall.assert_called()
    mock_write.assert_called()


def test_handle_not_found(mock_manager):
    server = WebServer(mock_manager)
    client = MagicMock()
    server.handle_not_found(client)
    client.sendall.assert_called()
