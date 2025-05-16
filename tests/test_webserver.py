import sys
import types

if "machine" not in sys.modules:
    sys.modules["machine"] = types.ModuleType("machine")
    sys.modules["machine"].reset = lambda: None

import pytest
from unittest.mock import patch, Mock
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


def test_reboot_device_true(mock_manager):
    mock_sleep = Mock()
    mock_reset = Mock()
    server = WebServer(mock_manager, sleep_fn=mock_sleep, reset_fn=mock_reset)
    server.reboot = True
    server._reboot_device()
    mock_sleep.assert_called_once_with(5)


def test_reboot_device_false(mock_manager):
    mock_sleep = Mock()
    mock_reset = Mock()
    server = WebServer(mock_manager, sleep_fn=mock_sleep, reset_fn=mock_reset)

    server.reboot = False
    server._reboot_device()
    mock_sleep.assert_not_called()


def test_run_no_connection_then_ok(mock_manager):
    server = WebServer(mock_manager)
    mock_socket = Mock()
    server._create_server_socket = Mock(return_value=mock_socket)
    server._handle_client = Mock()
    client = Mock()
    mock_socket.accept.return_value = (client, None)
    mock_manager.wlan_sta.isconnected.side_effect = [False, True]

    server.run()
    mock_socket.accept.assert_called_once()
    server._handle_client.assert_called_once_with(client)


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
    client = Mock()
    server.send_header(client)
    assert client.send.call_count == 3


def test_send_response(mock_manager):
    server = WebServer(mock_manager)
    client = Mock()
    server.send_response(client, "<h1>Hello</h1>")
    client.sendall.assert_called()
    client.close.assert_called()


def test_handle_root(mock_manager):
    server = WebServer(mock_manager)
    client = Mock()
    server.handle_root(client)
    client.sendall.assert_called()


@patch("wifi_manager.webserver.write_credentials")
def test_handle_configure_success(mock_write, mock_manager):
    server = WebServer(mock_manager, sleep_fn=lambda x: None, reset_fn=lambda: None)
    client = Mock()
    mock_manager.wlan_sta.ifconfig.return_value = ["192.168.4.1"]
    test_request = (
        b"POST /configure HTTP/1.1\r\n"
        b"Host: 192.168.4.1\r\nConnection: keep-alive\r\n"
        b"Content-Length: 26\r\nCache-Control: max-age=0\r\n"
        b"Origin: http://192.168.4.1\r\nContent-Type: application/x-www-form-urlencoded\r\n"
        b"Upgrade-Insecure-Requests: 1\r\n"
        b"User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        b"(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36\r\n"
        b"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,"
        b"image/avif,image/webp,image/apng,*/*;q=0.8\r\nSec-GPC: 1\r\n"
        b"Referer: http://192.168.4.1/\r\nAccept-Encoding: gzip, deflate\r\n"
        b"Accept-Language: en-GB,en-US;q=0.9,en;q=0.8,ko;q=0.7\r\n\r\nssid=Kimmies&password=1234"
    )
    server.handle_configure(client, test_request)
    client.sendall.assert_called()
    mock_write.assert_called()


@patch("wifi_manager.webserver.socket")
def test_create_server_socket(mock_socket, mock_manager):
    mock_socket.socket.return_value = mock_socket
    mock_socket.bind = Mock()
    mock_socket.listen = Mock()
    mock_socket.setsockopt = Mock()

    server = WebServer(mock_manager)
    server._create_server_socket()

    assert mock_socket.socket.call_count == 1
    assert mock_socket.bind.call_count == 1
    assert mock_socket.listen.call_count == 1
    assert mock_socket.setsockopt.call_count == 1
    assert mock_socket.bind.call_args[0][0] == ("", 80)
    assert mock_socket.listen.call_args[0][0] == 1


def test_handle_client_root(mock_manager):
    """Test handling a client request for the root URL."""
    mock_client = Mock()
    mock_client.recv.side_effect = [
        b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n",  # Simulate HTTP GET request
    ]
    server = WebServer(mock_manager, debug=True)

    with patch.object(server, "handle_root") as mock_handle_root:
        server._handle_client(mock_client)

        # Verify the root handler was called
        mock_handle_root.assert_called_once_with(mock_client)

    # Verify the client connection was closed
    mock_client.close.assert_called_once()


def test_handle_client_connection_closed(mock_manager):
    server = WebServer(mock_manager)
    mock_client = Mock()
    # Empty chunk simulates closed connection
    mock_client.recv.side_effect = [b"GET /", b"", b"more data"]

    server._handle_client(mock_client)

    # Should stop after receiving empty chunk
    assert mock_client.recv.call_count == 2
    # from handle_not_found
    mock_client.sendall.assert_called_once()
    mock_client.close.assert_called()
    assert mock_client.close.call_count == 2


def test_handle_client_configure(mock_manager):
    """Test handling a client request for the configure URL."""
    mock_client = Mock()
    mock_client.recv.side_effect = [
        b"POST /configure HTTP/1.1\r\nHost: localhost\r\n\r\nssid=TestSSID&password=TestPass123",
        b"",
    ]
    server = WebServer(mock_manager, debug=True)

    with patch.object(server, "handle_configure") as mock_handle_configure:
        server._handle_client(mock_client)

        # Verify the configure handler was called
        mock_handle_configure.assert_called_once_with(
            mock_client,
            b"POST /configure HTTP/1.1\r\nHost: localhost\r\n\r\nssid=TestSSID&password=TestPass123",
        )

    # Verify the client connection was closed
    mock_client.close.assert_called_once()


def test_handle_client_not_found(mock_manager):
    """Test handling a client request for an unknown URL."""
    mock_client = Mock()
    mock_client.recv.side_effect = [
        b"GET /unknown HTTP/1.1\r\nHost: localhost\r\n\r\n",
        b"",
    ]
    server = WebServer(mock_manager, debug=True)

    with patch.object(server, "handle_not_found") as mock_handle_not_found:
        server._handle_client(mock_client)

        # Verify the not found handler was called
        mock_handle_not_found.assert_called_once_with(mock_client)

    # Verify the client connection was closed
    mock_client.close.assert_called_once()


def test_handle_client_timeout(mock_manager):
    """Test handling a client request with a timeout."""
    mock_client = Mock()
    mock_client.recv.side_effect = TimeoutError  # Simulate a timeout
    server = WebServer(mock_manager, debug=True)

    server._handle_client(mock_client)

    # Verify the client connection was closed even on timeout
    mock_client.close.assert_called_once()


def test_handle_configure_missing_ssid(mock_manager):
    """Test handle_configure when SSID is empty"""
    server = WebServer(mock_manager)
    mock_client = Mock()

    # Test with empty SSID
    with patch("wifi_manager.webserver.url_decode", return_value=b"ssid=&password=test123"):
        server.handle_configure(mock_client, b"")
        mock_client.sendall.assert_called()
        # from send_header
        assert mock_client.send.call_count == 3
        assert b"HTTP/1.1 400" in mock_client.send.call_args_list[0][0][0]
        # Verify error message was sent
        assert b"SSID must be provided!" in mock_client.sendall.call_args[0][0]


def test_handle_configure_missing_parameters(mock_manager):
    """Test handle_configure when parameters are missing from the request"""
    server = WebServer(mock_manager)
    mock_client = Mock()

    # Test with empty request
    with patch("wifi_manager.webserver.url_decode", return_value=b""):
        server.handle_configure(mock_client, b"")
        mock_client.sendall.assert_called()
        # from send_header
        assert mock_client.send.call_count == 3
        assert b"HTTP/1.1 400" in mock_client.send.call_args_list[0][0][0]
        # Verify error message was sent
        assert b"Parameters not found!" in mock_client.sendall.call_args[0][0]
