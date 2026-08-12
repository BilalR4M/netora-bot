"""Docker container stats (stub for future extension)."""

from pathlib import Path

from collectors.base import Collector, register

DOCKER_SOCKET = Path("/var/run/docker.sock")


@register
class DockerCollector(Collector):
    """
    Placeholder collector for per-container stats.

    To enable later:
      1. pip install docker
      2. Add the service user to the docker group
      3. Implement collect() using docker.from_env().containers.list()
    """

    name = "docker"

    def enabled(self) -> bool:
        return DOCKER_SOCKET.exists()

    def collect(self) -> dict:
        return {
            "title": "Docker",
            "fields": [
                {
                    "name": "Containers",
                    "value": (
                        "Docker socket detected but collector not implemented yet.\n"
                        "See README extension guide to enable container stats."
                    ),
                    "inline": False,
                },
            ],
            "severity": None,
            "summary": "Docker extension pending",
        }
