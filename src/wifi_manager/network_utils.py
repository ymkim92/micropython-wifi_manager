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


def url_decode(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i : i + 1] == b"%":
            if i + 2 < len(data) and data[i + 1 : i + 3].isalnum():
                try:
                    result.append(int(data[i + 1 : i + 3], 16))
                    i += 3
                    continue
                except ValueError:
                    pass
        result.append(data[i])
        i += 1
    return bytes(result)
