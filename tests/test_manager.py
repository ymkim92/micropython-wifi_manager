import sys
import types

if "machine" not in sys.modules:
    sys.modules["machine"] = types.ModuleType("machine")
    sys.modules["machine"].reset = lambda: None
if "network" not in sys.modules:
    sys.modules["network"] = types.ModuleType("network")
    sys.modules["network"].WLAN = lambda iface: None

import pytest
from unittest.mock import patch, MagicMock
from wifi_manager.manager import WifiManager
from wifi_manager.network_utils import write_credentials


@pytest.fixture(autouse=True)
def patch_network(monkeypatch):
    import wifi_manager.manager as manager_mod

    # Create mock WLAN class
    mock_wlan = MagicMock()
    mock_wlan._connected = False
    mock_wlan.isconnected.side_effect = lambda: mock_wlan._connected
    mock_wlan.scan.return_value = [(b"ssid1",), (b"ssid2",)]
    mock_wlan.ifconfig.return_value = ("192.168.1.2", "255.255.255.0", "192.168.1.1", "8.8.8.8")
    mock_wlan.connect.side_effect = lambda ssid, password: setattr(
        mock_wlan, "_connected", ssid == "ssid1" and password == "pass1"
    )
    mock_wlan.disconnect.side_effect = lambda: setattr(mock_wlan, "_connected", False)

    # Mock the network module
    sys.modules["network"] = types.ModuleType("network")
    sys.modules["network"].STA_IF = 0
    sys.modules["network"].AP_IF = 1
    sys.modules["network"].WLAN = lambda iface: mock_wlan

    # Patch the network module
    monkeypatch.setattr(manager_mod, "network", sys.modules["network"])
    yield


def test_wifi_manager_init():
    wm = WifiManager(ssid="TestSSID", password="TestPass123")
    assert wm.ap_ssid == "TestSSID"
    assert wm.ap_password == "TestPass123"
    assert wm.reboot is True


def test_wifi_manager_ssid_length():
    with pytest.raises(Exception):
        WifiManager(ssid="x" * 33)


def test_wifi_manager_password_length():
    with pytest.raises(Exception):
        WifiManager(password="short")


def test_wifi_manager_connect(tmp_path):
    wm = WifiManager(ssid="TestSSID", password="TestPass123")
    wm.wifi_credentials = str(tmp_path / "wifi.dat")

    # Save credentials for ssid1
    write_credentials(wm.wifi_credentials, {"ssid1": "pass1"})
    wm.connect()
    assert wm.is_connected()


@patch("wifi_manager.manager.read_credentials", return_value={})
def test_wifi_manager_connected_already(mock_read_credentials):
    wm = WifiManager(ssid="TestSSID", password="TestPass123")
    wm.wlan_sta._connected = True  # Simulate already connected
    wm.connect()
    mock_read_credentials.assert_not_called()


@patch("wifi_manager.manager.WebServer")
def test_wifi_manager_connect_not_connected_and_no_credentials(mock_webserver, tmp_path):
    mock_instance = MagicMock()
    mock_webserver.return_value = mock_instance
    wm = WifiManager(ssid="TestSSID", password="TestPass123")
    wm.wifi_credentials = str(tmp_path / "wifi.dat")

    write_credentials(wm.wifi_credentials, {"ssid3": "pass3"})
    wm.connect()
    assert not wm.is_connected()
    mock_webserver.assert_called_once_with(wm)
    mock_instance.run.assert_called_once()


def test_wifi_manager_disconnect():
    wm = WifiManager(ssid="TestSSID", password="TestPass123")
    wm.wlan_sta._connected = True
    wm.disconnect()
    assert wm.is_connected() is False


# def test_manager_wifi_connect():
#     wm = WifiManager(ssid="TestSSID", password="TestPass123")
#     wm.wlan_sta._connected = True
#     wm.disconnect()
#     assert wm.is_connected() is False
