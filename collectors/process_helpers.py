"""Top process helpers used by collectors and slash commands."""

import time

import psutil


def format_process_line(proc: psutil.Process, cpu: float, mem_percent: float) -> str:
    try:
        name = proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        name = "unknown"
    return f"`{proc.pid:>6}` {name[:24]:<24} CPU {cpu:5.1f}% MEM {mem_percent:5.1f}%"


def top_processes(
    by: str,
    limit: int = 5,
    sample_interval: float = 0.0,
) -> list[tuple[psutil.Process, float, float]]:
    """Return (process, cpu_percent, mem_percent) sorted by CPU or memory."""
    procs = list(psutil.process_iter(["pid", "name"]))

    if sample_interval > 0:
        for proc in procs:
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        time.sleep(sample_interval)

    results: list[tuple[psutil.Process, float, float]] = []
    for proc in procs:
        try:
            cpu = proc.cpu_percent(interval=None)
            mem_percent = proc.memory_percent()
            results.append((proc, cpu, mem_percent))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    key_index = 1 if by == "cpu" else 2
    results.sort(key=lambda item: item[key_index], reverse=True)
    return results[:limit]
