"""Discord slash commands for server stats."""

import discord
from discord import app_commands
from discord.ext import commands

import config
import collectors  # noqa: F401 — register collectors
from collectors.base import get_collector, get_enabled_collectors
from collectors.process_helpers import format_process_table, top_processes
from utils.embeds import (
    COLOR_ACCENT,
    COLOR_CRITICAL,
    build_help_embed,
    build_message_embed,
    build_overview_embed,
    build_stats_embed,
)
from utils.formatting import format_boot_time, human_duration


def _check_stats_access(interaction: discord.Interaction) -> bool:
    if config.GUILD_ID and interaction.guild_id != config.GUILD_ID:
        raise app_commands.CheckFailure("This bot is restricted to a specific server.")

    if config.ALLOWED_ROLE_IDS:
        member = interaction.user
        if not isinstance(member, discord.Member):
            raise app_commands.CheckFailure("Member context required for role check.")
        role_ids = {role.id for role in member.roles}
        if not any(role_id in role_ids for role_id in config.ALLOWED_ROLE_IDS):
            raise app_commands.CheckFailure(
                "You do not have permission to run server stats commands."
            )

    return True


stats_access = app_commands.check(_check_stats_access)


def _requester_name(interaction: discord.Interaction) -> str:
    return interaction.user.display_name


def _brand_kwargs(interaction: discord.Interaction) -> dict:
    bot_user = interaction.client.user
    kwargs: dict = {
        "requester": _requester_name(interaction),
    }
    if bot_user is not None:
        kwargs["author_name"] = bot_user.display_name
        kwargs["author_icon_url"] = bot_user.display_avatar.url
    return kwargs


class Stats(commands.Cog):
    """Slash commands that report local server statistics."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, app_commands.CheckFailure):
            message = str(error) or "You cannot run this command."
            embed = build_message_embed(
                "Access denied",
                message,
                color=COLOR_CRITICAL,
                requester=_requester_name(interaction),
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        raise error

    async def _unavailable(self, interaction: discord.Interaction, topic: str) -> None:
        embed = build_message_embed(
            "Unavailable",
            f"{topic} stats are unavailable right now.",
            color=COLOR_ACCENT,
            requester=_requester_name(interaction),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="help", description="Show available server stats commands")
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = build_help_embed(**_brand_kwargs(interaction))
        await interaction.response.send_message(embed=embed)

    @stats_access
    @app_commands.command(name="stats", description="Overview of server stats")
    async def stats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        sections = [collector.collect() for collector in get_enabled_collectors()]
        hostname = next(
            (section.get("hostname") for section in sections if section.get("hostname")),
            None,
        )
        embed = build_overview_embed(
            sections,
            hostname=hostname,
            **_brand_kwargs(interaction),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="cpu", description="CPU usage, load average, and temperature")
    async def cpu(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("system")
        if collector is None:
            await self._unavailable(interaction, "CPU")
            return

        data = collector.collect()
        fields = [f for f in data["fields"] if f["name"] in ("CPU", "Load average", "Temperature")]
        embed = build_stats_embed(
            "CPU",
            fields,
            severity=data.get("cpu_percent"),
            description="Live CPU metrics for this host.",
            hostname=data.get("hostname"),
            **_brand_kwargs(interaction),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="mem", description="Memory and swap usage")
    async def mem(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("process")
        if collector is None:
            await self._unavailable(interaction, "Memory")
            return

        data = collector.collect()
        embed = build_stats_embed(
            "Memory",
            data["mem_fields"],
            severity=data["memory"].percent,
            description="RAM and swap usage on this host.",
            **_brand_kwargs(interaction),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="disk", description="Disk usage by mount point")
    async def disk(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("disk")
        if collector is None:
            await self._unavailable(interaction, "Disk")
            return

        data = collector.collect()
        embed = build_stats_embed(
            "Disk",
            data["fields"],
            severity=data.get("max_percent"),
            description="Disk usage by mount point (tmpfs/snap loops skipped).",
            **_brand_kwargs(interaction),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="net", description="Network throughput and totals")
    async def net(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("network")
        if collector is None:
            await self._unavailable(interaction, "Network")
            return

        data = collector.collect()
        embed = build_stats_embed(
            "Network",
            data["fields"],
            description="Network throughput since the last sample, plus lifetime totals.",
            **_brand_kwargs(interaction),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="uptime", description="System uptime and boot time")
    async def uptime(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("system")
        if collector is None:
            await self._unavailable(interaction, "Uptime")
            return

        data = collector.collect()
        uptime_seconds = data["uptime_seconds"]
        boot_time = data["boot_time"]
        fields = [
            {
                "name": "Uptime",
                "value": human_duration(uptime_seconds),
                "inline": True,
            },
            {
                "name": "Boot time",
                "value": format_boot_time(boot_time),
                "inline": True,
            },
            {
                "name": "Host",
                "value": data.get("hostname", "unknown"),
                "inline": True,
            },
        ]
        embed = build_stats_embed(
            "Uptime",
            fields,
            description="How long this host has been running.",
            hostname=data.get("hostname"),
            **_brand_kwargs(interaction),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="top", description="Top processes by CPU or memory")
    @app_commands.describe(
        sort_by="Sort processes by CPU or memory usage",
        count="Number of processes to show (1–15)",
    )
    @app_commands.choices(
        sort_by=[
            app_commands.Choice(name="CPU", value="cpu"),
            app_commands.Choice(name="Memory", value="mem"),
        ]
    )
    async def top(
        self,
        interaction: discord.Interaction,
        sort_by: str,
        count: app_commands.Range[int, 1, 15] = 10,
    ) -> None:
        await interaction.response.defer()
        metric = sort_by
        processes = top_processes(metric, limit=count, sample_interval=0.15)

        label = "CPU" if metric == "cpu" else "Memory"
        fields = [
            {
                "name": f"Top {count} by {label}",
                "value": format_process_table(processes),
                "inline": False,
            }
        ]
        embed = build_stats_embed(
            f"Top Processes · {label}",
            fields,
            description=f"Processes ranked by {label.lower()} usage.",
            **_brand_kwargs(interaction),
        )
        await interaction.followup.send(embed=embed)
