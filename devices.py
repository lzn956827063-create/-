import subprocess


def scan_network(base_ip="192.168.1.", start=1, end=20, timeout_ms=200):
    online_devices = []

    for i in range(start, end + 1):
        ip = base_ip + str(i)
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), ip],
            stdout=subprocess.DEVNULL
        )
        if result.returncode == 0:
            online_devices.append(ip)

    return online_devices
