"""CPU, load average, uptime, and temperature stats."""

import os
import platform
import time

import psutil

from collectors.base import Collector, register
from utils.formatting import human_duration, progress_bar


def _load_average() -> str | None:
    if hasattr(os, "getloadavg"):
        one, five, fifteen = os.getloadavg()
        return f"{one:.2f} / {five:.2f} / {fifteen:.2f}"
    return None


def _temperature() -> str | None:
    if not hasattr(psutil, "sensors_temperatures"):
        return None
    try:
        temps = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return None
    if not temps:
        return None

    lines: list[str] = []
    for sensor_name, entries in temps.items():
        for entry in entries[:2]:
            label = entry.label or sensor_name
            lines.append(f"{label}: {entry.current:.1f}°C")
    return "\n".join(lines[:4]) if lines else None


@register
class SystemCollector(Collector):
    name = "system"

    def enabled(self) -> bool:
        return True

    def collect(self) -> dict:
        cpu_percent = psutil.cpu_percent(interval=None)
        logical = psutil.cpu_count(logical=True) or 0
        physical = psutil.cpu_count(logical=False) or logical
        boot = psutil.boot_time()
        uptime_seconds = time.time() - boot

        fields: list[dict] = [
            {
                "name": "CPU",
                "value": f"{cpu_percent:.1f}% {progress_bar(cpu_percent)}\n"
                f"{physical} physical / {logical} logical cores",
                "inline": False,
            },
        ]

        load = _load_average()
        if load:
            fields.append({"name": "Load average", "value": load, "inline": True})

        fields.append(
            {
                "name": "Uptime",
                "value": human_duration(uptime_seconds),
                "inline": True,
            }
        )

        temp = _temperature()
        if temp:
            fields.append({"name": "Temperature", "value": temp, "inline": False})

        hostname = platform.node() or "unknown"
        fields.append({"name": "Host", "value": hostname, "inline": True})

        summary = f"CPU {cpu_percent:.1f}% · uptime {human_duration(uptime_seconds)}"

        return {
            "title": "System",
            "fields": fields,
            "severity": cpu_percent,
            "summary": summary,
            "cpu_percent": cpu_percent,
            "uptime_seconds": uptime_seconds,
            "boot_time": boot,
            "load_average": load,
            "temperature": temp,
            "hostname": hostname,
            "logical_cores": logical,
            "physical_cores": physical,
        }
