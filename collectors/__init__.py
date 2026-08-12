"""Stat collectors; importing submodules registers them in REGISTRY."""

from collectors.base import REGISTRY, Collector, register

# Import collectors so @register runs at import time.
from collectors import disk, docker, network, process, system  # noqa: F401

__all__ = ["REGISTRY", "Collector", "register"]
