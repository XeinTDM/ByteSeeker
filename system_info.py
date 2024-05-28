from datetime import datetime
import platform
import wmi
import os

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