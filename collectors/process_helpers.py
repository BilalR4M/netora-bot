"""Top process helpers used by collectors and slash commands."""

import time

import psutil


def format_process_line(proc: psutil.Process, cpu: float, mem_percent: float) -> str:
    try:
        name = proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        name = "unknown"
    return f"{proc.pid:>6}  {name[:22]:<22}  {cpu:5.1f}%  {mem_percent:5.1f}%"


def format_process_table(
    rows: list[tuple[psutil.Process, float, float]],
) -> str:
    """Render top processes as a monospace code-block table."""
    header = f"{'PID':>6}  {'NAME':<22}  {'CPU':>6}  {'MEM':>6}"
    separator = f"{'-' * 6}  {'-' * 22}  {'-' * 6}  {'-' * 6}"
    if not rows:
        body = "No process data available."
    else:
        body = "\n".join(format_process_line(proc, cpu, mem) for proc, cpu, mem in rows)
    return f"```\n{header}\n{separator}\n{body}\n```"


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
