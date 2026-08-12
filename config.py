"""Load configuration from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _parse_int(value: str | None, default: int = 0) -> int:
    if not value or not value.strip():
        return default
    return int(value.strip())


def _parse_role_ids(value: str | None) -> list[int]:
    if not value or not value.strip():
        return []
    return [int(part.strip()) for part in value.split(",") if part.strip()]


DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
GUILD_ID: int = _parse_int(os.getenv("GUILD_ID"), 0)
ALLOWED_ROLE_IDS: list[int] = _parse_role_ids(os.getenv("ALLOWED_ROLE_IDS"))
