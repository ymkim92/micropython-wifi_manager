from wifi_manager.network_utils import write_credentials, read_credentials, url_decode


def test_write_and_read_credentials(tmp_path):
    file_path = tmp_path / "wifi.dat"
    profiles = {"ssid1": "pass1", "ssid2": "pass2"}
    write_credentials(str(file_path), profiles)
    loaded = read_credentials(str(file_path))
    assert loaded == profiles


def test_write_and_read_credentials_exception(tmp_path):
    file_path = tmp_path / "wifi.dat"
    loaded = read_credentials(str(file_path), debug=True)
    assert loaded == {}


def test_write_and_read_empty_credentials(tmp_path):
    file_path = tmp_path / "wifi.dat"
    profiles = {}
    write_credentials(str(file_path), profiles)
    loaded = read_credentials(str(file_path))
    assert loaded == profiles


def test_url_decode_basic():
    assert url_decode("abc%20def") == b"abc def"
    assert url_decode(b"abc%20def") == b"abc def"
    assert url_decode("") == b""


def test_url_decode_non_encoded():
    assert url_decode("plainstring") == b"plainstring"
    assert url_decode(b"plainstring") == b"plainstring"


def test_url_decode_partial_percent():
    # Should not raise, just return as-is
    assert url_decode("abc%2") == b"abc%2"
    assert url_decode(b"abc%2") == b"abc%2"


def test_url_decode_invalid_percent():
    # Should not raise, just return as-is
    assert url_decode("abc%zz") == b"abc%zz"
    assert url_decode(b"abc%zz") == b"abc%zz"
