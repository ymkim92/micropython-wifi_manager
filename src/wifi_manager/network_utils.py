def write_credentials(wifi_credentials, profiles):
    lines = []
    for ssid, password in profiles.items():
        lines.append("{0};{1}\n".format(ssid, password))
    with open(wifi_credentials, "w") as file:
        file.write("".join(lines))


def read_credentials(wifi_credentials, debug=False):
    lines = []
    try:
        with open(wifi_credentials) as file:
            lines = file.readlines()
    except Exception as error:
        if debug:
            print(error)
        pass
    profiles = {}
    for line in lines:
        ssid, password = line.strip().split(";")
        profiles[ssid] = password
    return profiles


def url_decode(url_string, debug=False):
    # Source: https://forum.micropython.org/viewtopic.php?t=3076
    # unquote('abc%20def') -> b'abc def'
    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.

    if not url_string:
        return b""

    if isinstance(url_string, str):
        url_string = url_string.encode("utf-8")

    bits = url_string.split(b"%")

    if len(bits) == 1:
        return url_string

    res = [bits[0]]
    appnd = res.append
    hextobyte_cache = {}

    for item in bits[1:]:
        try:
            code = item[:2]
            char = hextobyte_cache.get(code)
            if char is None:
                char = hextobyte_cache[code] = bytes([int(code, 16)])
            appnd(char)
            appnd(item[2:])
        except Exception as error:
            if debug:
                print(error)
            appnd(b"%")
            appnd(item)

    return b"".join(res) 