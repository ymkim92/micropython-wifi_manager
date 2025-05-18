# WiFi Manager

WiFi Manager for ESP32 using MicroPython. It might work in any other board since it only uses standard MicroPython libraries, but that's not tested.

![ESP32](https://img.shields.io/badge/ESP-32-000000.svg?longCache=true&style=flat&colorA=CC101F)
![CI](https://github.com/ymkim92/micropython-wifi_manager/actions/workflows/ci.yml/badge.svg)

## How It Works

- When your device starts up, it will try to connect to a previously saved wifi.
- If there is no saved network or if it fails to connect, it will start an access point;
- By connecting to the access point and going to the address `192.168.4.1` you be able to find your network and input the credentials;
- It will try to connect to the desired network, and if it's successful, it will save the credentials for future usage;
- Be aware that the wifi credentials will be saved in a plain text file, and this can be a security fault depending on your application;

## Installation and Usage
 
### Using mip via mpremote:

```
$ mpremote mip install github:ymkim92/micropython-wifi_manager
```

### Using mip directly on a WiFi capable board:

```
>>> import mip
>>> mip.install("github:ymkim92/micropython-wifi_manager")
```

### justfile

Upload the scripts to a target device:

```sh
$ just upload
```

You may want to use `mount` of `mpremote` for test or debugging:
```sh
$ just mount_and_run
```

## Methods

### .connect()

Tries to connect to a network and if it doesn't work start the configuration portal.

### .disconnect()

Disconnect from network.

### .is_connected()

Returns True if it's connected and False if it's not. It's the simpler way to test the connection inside your code.

### .get_address()

Returns a tuple with the network interface parameters: IP address, subnet mask, gateway and DNS server.

## Notes

- Do not use this library with other ones that works directly with the network interface, since it might have conflicts;

## Thanks To

https://github.com/tayfunulu/WiFiManager/
