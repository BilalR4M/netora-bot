"""Network I/O stats with per-interval rates."""

import time

import psutil

from collectors.base import Collector, register
from utils.formatting import human_bytes, human_rate

_prev_counters = None
_prev_time: float | None = None


def _sample_rates() -> tuple[float, float]:
    """Return (bytes_sent_per_sec, bytes_recv_per_sec) since last sample."""
    global _prev_counters, _prev_time

    counters = psutil.net_io_counters()
    now = time.monotonic()

    if _prev_counters is None or _prev_time is None:
        _prev_counters = counters
        _prev_time = now
        return 0.0, 0.0

    elapsed = now - _prev_time
    if elapsed <= 0:
        return 0.0, 0.0

    sent_rate = (counters.bytes_sent - _prev_counters.bytes_sent) / elapsed
    recv_rate = (counters.bytes_recv - _prev_counters.bytes_recv) / elapsed

    _prev_counters = counters
    _prev_time = now

    return sent_rate, recv_rate


@register
class NetworkCollector(Collector):
    name = "network"

    def enabled(self) -> bool:
        return True

    def collect(self) -> dict:
        counters = psutil.net_io_counters()
        sent_rate, recv_rate = _sample_rates()

        fields: list[dict] = [
            {
                "name": "Throughput",
                "value": (
                    f"↑ {human_rate(sent_rate)}\n"
                    f"↓ {human_rate(recv_rate)}"
                ),
                "inline": True,
            },
            {
                "name": "Totals",
                "value": (
                    f"Sent: {human_bytes(counters.bytes_sent)}\n"
                    f"Recv: {human_bytes(counters.bytes_recv)}"
                ),
                "inline": True,
            },
            {
                "name": "Packets",
                "value": (
                    f"Sent: {counters.packets_sent:,}\n"
                    f"Recv: {counters.packets_recv:,}"
                ),
                "inline": True,
            },
        ]

        if counters.errin or counters.errout:
            fields.append(
                {
                    "name": "Errors",
                    "value": f"In: {counters.errin:,} · Out: {counters.errout:,}",
                    "inline": True,
                }
            )

        summary = f"Net ↑{human_rate(sent_rate)} ↓{human_rate(recv_rate)}"

        return {
            "title": "Network",
            "fields": fields,
            "severity": None,
            "summary": summary,
            "bytes_sent": counters.bytes_sent,
            "bytes_recv": counters.bytes_recv,
            "sent_rate": sent_rate,
            "recv_rate": recv_rate,
            "packets_sent": counters.packets_sent,
            "packets_recv": counters.packets_recv,
        }
