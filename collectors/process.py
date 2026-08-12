"""Memory stats and top processes."""

import psutil

from collectors.base import Collector, register
from collectors.process_helpers import format_process_line, top_processes
from utils.formatting import human_bytes, progress_bar


@register
class ProcessCollector(Collector):
    name = "process"

    def enabled(self) -> bool:
        return True

    def collect(self) -> dict:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        mem_fields: list[dict] = [
            {
                "name": "Memory",
                "value": (
                    f"{mem.percent:.1f}% {progress_bar(mem.percent)}\n"
                    f"{human_bytes(mem.used)} / {human_bytes(mem.total)} "
                    f"({human_bytes(mem.available)} available)"
                ),
                "inline": False,
            },
            {
                "name": "Swap",
                "value": (
                    f"{swap.percent:.1f}% {progress_bar(swap.percent)}\n"
                    f"{human_bytes(swap.used)} / {human_bytes(swap.total)}"
                ),
                "inline": False,
            },
        ]

        top_cpu = top_processes("cpu", limit=5)
        top_mem = top_processes("mem", limit=5)

        cpu_lines = [format_process_line(p, c, m) for p, c, m in top_cpu]
        mem_lines = [format_process_line(p, c, m) for p, c, m in top_mem]

        process_fields: list[dict] = [
            {
                "name": "Top CPU",
                "value": "\n".join(cpu_lines) if cpu_lines else "No data",
                "inline": False,
            },
            {
                "name": "Top Memory",
                "value": "\n".join(mem_lines) if mem_lines else "No data",
                "inline": False,
            },
        ]

        summary = f"RAM {mem.percent:.1f}% · swap {swap.percent:.1f}%"

        return {
            "title": "Memory & Processes",
            "fields": mem_fields + process_fields,
            "severity": mem.percent,
            "summary": summary,
            "memory": mem,
            "swap": swap,
            "top_cpu": top_cpu,
            "top_mem": top_mem,
            "mem_fields": mem_fields,
            "process_fields": process_fields,
        }
