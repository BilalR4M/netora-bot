"""Discord embed builders for server stats."""

from datetime import datetime, timezone

import discord

# Palette: purple → magenta → coral → yellow
COLOR_OK = discord.Color(0x672D91)
COLOR_ACCENT = discord.Color(0xA61D8F)
COLOR_CRITICAL = discord.Color(0xF05A5B)
COLOR_WARN = discord.Color(0xFDBB2D)


def severity_label(severity: float | None) -> str | None:
    """Map a 0–100 severity value to a short status label."""
    if severity is None:
        return None
    if severity >= 90:
        return "Critical"
    if severity >= 75:
        return "Elevated"
    return "Healthy"


def severity_color(severity: float | None) -> discord.Color:
    """Map a 0–100 severity value to embed color."""
    if severity is None:
        return COLOR_OK
    if severity >= 90:
        return COLOR_CRITICAL
    if severity >= 75:
        return COLOR_WARN
    return COLOR_OK


def _footer_text(
    hostname: str | None = None,
    requester: str | None = None,
    extra: str | None = None,
) -> str | None:
    parts: list[str] = []
    if hostname:
        parts.append(hostname)
    if requester:
        parts.append(f"requested by {requester}")
    if extra:
        parts.append(extra)
    return " · ".join(parts) if parts else None


def base_embed(
    title: str,
    *,
    description: str | None = None,
    color: discord.Color | None = None,
    severity: float | None = None,
    hostname: str | None = None,
    requester: str | None = None,
    footer_extra: str | None = None,
    author_name: str | None = None,
    author_icon_url: str | None = None,
) -> discord.Embed:
    """Build a branded embed shell with status, timestamp, and footer."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color if color is not None else severity_color(severity),
        timestamp=datetime.now(timezone.utc),
    )

    status = severity_label(severity)
    if status:
        embed.add_field(name="Status", value=f"**{status}**", inline=True)

    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon_url or None)

    footer = _footer_text(hostname=hostname, requester=requester, extra=footer_extra)
    if footer:
        embed.set_footer(text=footer)

    return embed


def build_stats_embed(
    title: str,
    fields: list[dict],
    severity: float | None = None,
    footer: str | None = None,
    *,
    description: str | None = None,
    hostname: str | None = None,
    requester: str | None = None,
    author_name: str | None = None,
    author_icon_url: str | None = None,
    color: discord.Color | None = None,
) -> discord.Embed:
    """Build a single-stats embed from collector field dicts."""
    embed = base_embed(
        title,
        description=description,
        color=color,
        severity=severity,
        hostname=hostname or footer,
        requester=requester,
        author_name=author_name,
        author_icon_url=author_icon_url,
    )
    for field in fields:
        embed.add_field(
            name=field["name"],
            value=field["value"],
            inline=field.get("inline", False),
        )
    return embed


def build_overview_embed(
    sections: list[dict],
    hostname: str | None = None,
    *,
    requester: str | None = None,
    author_name: str | None = None,
    author_icon_url: str | None = None,
) -> discord.Embed:
    """Build overview embed from multiple collector results."""
    severities = [s["severity"] for s in sections if s.get("severity") is not None]
    peak = max(severities) if severities else None

    title = "Server Stats"
    if hostname:
        title = f"Server Stats · {hostname}"

    embed = base_embed(
        title,
        description="Live overview of this host. Use `/help` for all commands.",
        severity=peak,
        hostname=hostname,
        requester=requester,
        author_name=author_name,
        author_icon_url=author_icon_url,
    )

    for section in sections:
        summary = section.get("summary") or section.get("title", "—")
        embed.add_field(
            name=section.get("title", "Stats"),
            value=summary,
            inline=False,
        )

    return embed


def build_help_embed(
    *,
    requester: str | None = None,
    author_name: str | None = None,
    author_icon_url: str | None = None,
) -> discord.Embed:
    """Build the /help command catalog embed."""
    embed = base_embed(
        "Server Stats · Help",
        description=(
            "Reports live metrics from this Ubuntu host via slash commands.\n"
            "Access is restricted to authorized roles on the company server."
        ),
        color=COLOR_ACCENT,
        requester=requester,
        author_name=author_name,
        author_icon_url=author_icon_url,
    )
    embed.add_field(
        name="Overview",
        value="`/stats` — Summary of all enabled collectors",
        inline=False,
    )
    embed.add_field(
        name="Resources",
        value=(
            "`/cpu` — Usage, load average, temperature\n"
            "`/mem` — RAM and swap\n"
            "`/disk` — Usage by mount point\n"
            "`/net` — Throughput and totals"
        ),
        inline=False,
    )
    embed.add_field(
        name="System",
        value=(
            "`/uptime` — Uptime and boot time\n"
            "`/top` — Top processes by CPU or memory\n"
            "`/help` — This command list"
        ),
        inline=False,
    )
    embed.add_field(
        name="Tip",
        value="`/top sort_by:CPU count:10` — change sort metric and row count (1–15).",
        inline=False,
    )
    return embed


def build_message_embed(
    title: str,
    description: str,
    *,
    color: discord.Color | None = None,
    requester: str | None = None,
) -> discord.Embed:
    """Small branded embed for errors and notices."""
    return base_embed(
        title,
        description=description,
        color=color if color is not None else COLOR_ACCENT,
        requester=requester,
    )
