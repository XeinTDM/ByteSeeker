import subprocess
import socket
import psutil

def get_saved_wifi():
    wifi_list = []
    try:
        result = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True)
        profiles = [line.split(":")[1].strip() for line in result.stdout.split("\n") if "All User Profile" in line]
        for profile in profiles:
            result = subprocess.run(["netsh", "wlan", "show", "profile", profile, "key=clear"], capture_output=True, text=True)
            ssid = profile
            key_content = None
            for line in result.stdout.split("\n"):
                if "Key Content" in line:
                    key_content = line.split(":")[1].strip()
                    break
            wifi_list.append({"SSID": ssid, "Password": key_content})
    except Exception as e:
        wifi_list.append({"Error": str(e)})
    return wifi_list

def get_network_adapters():
    network_adapters = psutil.net_if_addrs()
    ip_info = {}
    for interface, addrs in network_adapters.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip_info[interface] = addr.address
    return ip_info