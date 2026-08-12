"""Human-readable formatting helpers."""

from datetime import datetime, timezone


def human_bytes(num_bytes: float) -> str:
    """Format bytes as B, KB, MB, GB, or TB."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"


def human_rate(bytes_per_sec: float) -> str:
    """Format a byte rate as B/s, KB/s, etc."""
    return f"{human_bytes(bytes_per_sec)}/s"


def human_duration(seconds: float) -> str:
    """Format seconds as a compact duration string."""
    total = int(seconds)
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def progress_bar(percent: float, width: int = 10) -> str:
    """Unicode progress bar for 0–100 percent."""
    clamped = max(0.0, min(100.0, percent))
    filled = int(round(clamped / 100 * width))
    return "█" * filled + "░" * (width - filled)


def format_boot_time(timestamp: float) -> str:
    """Format boot timestamp as local ISO-like string."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")
