"""Discord embed builders for server stats."""

import discord

COLOR_OK = discord.Color.green()
COLOR_WARN = discord.Color.gold()
COLOR_CRITICAL = discord.Color.red()
COLOR_NEUTRAL = discord.Color.blurple()


def severity_color(severity: float | None) -> discord.Color:
    """Map a 0–100 severity value to embed color."""
    if severity is None:
        return COLOR_NEUTRAL
    if severity >= 90:
        return COLOR_CRITICAL
    if severity >= 75:
        return COLOR_WARN
    return COLOR_OK


def build_stats_embed(
    title: str,
    fields: list[dict],
    severity: float | None = None,
    footer: str | None = None,
) -> discord.Embed:
    """Build a single-stats embed from collector field dicts."""
    embed = discord.Embed(title=title, color=severity_color(severity))
    for field in fields:
        embed.add_field(
            name=field["name"],
            value=field["value"],
            inline=field.get("inline", False),
        )
    if footer:
        embed.set_footer(text=footer)
    return embed


def build_overview_embed(
    sections: list[dict],
    hostname: str | None = None,
) -> discord.Embed:
    """Build overview embed from multiple collector results."""
    severities = [s["severity"] for s in sections if s.get("severity") is not None]
    peak = max(severities) if severities else None

    title = "Server Stats"
    if hostname:
        title = f"Server Stats · {hostname}"

    embed = discord.Embed(title=title, color=severity_color(peak))

    for section in sections:
        summary = section.get("summary") or section.get("title", "—")
        embed.add_field(
            name=section.get("title", "Stats"),
            value=summary,
            inline=False,
        )

    embed.set_footer(text="Use /cpu, /mem, /disk, /net, /uptime, /top for details")
    return embed
