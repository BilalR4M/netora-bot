"""Collector base class and registry."""

from abc import ABC, abstractmethod
from typing import Any

REGISTRY: dict[str, "Collector"] = {}


class Collector(ABC):
    """Gather one category of server stats for Discord embeds."""

    name: str

    @abstractmethod
    def enabled(self) -> bool:
        """Return False when this collector cannot run (e.g. Docker not installed)."""

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """
        Return embed-ready data:
          - title: str — section heading for /stats overview
          - fields: list[dict] — embed fields (name, value, inline optional)
          - severity: float | None — 0–100 for color coding (optional)
        """


def register(collector_cls: type[Collector]) -> type[Collector]:
    """Decorator that registers a collector instance in REGISTRY."""
    instance = collector_cls()
    REGISTRY[instance.name] = instance
    return collector_cls


def get_enabled_collectors() -> list[Collector]:
    """Return collectors that are currently enabled."""
    return [c for c in REGISTRY.values() if c.enabled()]


def get_collector(name: str) -> Collector | None:
    """Return a collector by name if it exists and is enabled."""
    collector = REGISTRY.get(name)
    if collector is None or not collector.enabled():
        return None
    return collector
