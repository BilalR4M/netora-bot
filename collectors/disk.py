"""Disk usage stats."""

import psutil

from collectors.base import Collector, register
from utils.formatting import human_bytes, progress_bar

SKIP_FSTYPES = frozenset({"tmpfs", "overlay", "squashfs", "devtmpfs", "devfs"})


def _should_skip_partition(partition) -> bool:
    if partition.fstype in SKIP_FSTYPES:
        return True
    if partition.mountpoint.startswith("/snap"):
        return True
    if partition.device.startswith("/dev/loop"):
        return True
    return False


@register
class DiskCollector(Collector):
    name = "disk"

    def enabled(self) -> bool:
        return True

    def collect(self) -> dict:
        partitions: list[dict] = []
        max_percent = 0.0

        for partition in psutil.disk_partitions(all=False):
            if _should_skip_partition(partition):
                continue
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except (OSError, PermissionError):
                continue

            percent = usage.percent
            max_percent = max(max_percent, percent)
            partitions.append(
                {
                    "mount": partition.mountpoint,
                    "device": partition.device,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": percent,
                }
            )

        partitions.sort(key=lambda p: p["percent"], reverse=True)

        fields: list[dict] = []
        for part in partitions[:8]:
            fields.append(
                {
                    "name": part["mount"],
                    "value": (
                        f"{part['percent']:.1f}% {progress_bar(part['percent'])}\n"
                        f"{human_bytes(part['used'])} / {human_bytes(part['total'])} "
                        f"({human_bytes(part['free'])} free)"
                    ),
                    "inline": False,
                }
            )

        if not fields:
            fields.append(
                {
                    "name": "Disk",
                    "value": "No mount points available.",
                    "inline": False,
                }
            )

        summary = (
            f"Disk peak {max_percent:.1f}% on {partitions[0]['mount']}"
            if partitions
            else "No disk data"
        )

        return {
            "title": "Disk",
            "fields": fields,
            "severity": max_percent,
            "summary": summary,
            "partitions": partitions,
            "max_percent": max_percent,
        }
