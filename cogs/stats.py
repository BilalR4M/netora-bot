"""Discord slash commands for server stats."""

import discord
from discord import app_commands
from discord.ext import commands

import config
import collectors  # noqa: F401 — register collectors
from collectors.base import get_collector, get_enabled_collectors
from collectors.process_helpers import format_process_line, top_processes
from utils.embeds import build_overview_embed, build_stats_embed
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
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
            return
        raise error

    @stats_access
    @app_commands.command(name="stats", description="Overview of server stats")
    async def stats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        sections = [collector.collect() for collector in get_enabled_collectors()]
        hostname = next(
            (section.get("hostname") for section in sections if section.get("hostname")),
            None,
        )
        embed = build_overview_embed(sections, hostname=hostname)
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="cpu", description="CPU usage, load average, and temperature")
    async def cpu(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("system")
        if collector is None:
            await interaction.followup.send("System stats are unavailable.")
            return

        data = collector.collect()
        fields = [f for f in data["fields"] if f["name"] in ("CPU", "Load average", "Temperature")]
        embed = build_stats_embed(
            "CPU",
            fields,
            severity=data.get("cpu_percent"),
            footer=data.get("hostname"),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="mem", description="Memory and swap usage")
    async def mem(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("process")
        if collector is None:
            await interaction.followup.send("Memory stats are unavailable.")
            return

        data = collector.collect()
        embed = build_stats_embed(
            "Memory",
            data["mem_fields"],
            severity=data["memory"].percent,
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="disk", description="Disk usage by mount point")
    async def disk(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("disk")
        if collector is None:
            await interaction.followup.send("Disk stats are unavailable.")
            return

        data = collector.collect()
        embed = build_stats_embed(
            "Disk",
            data["fields"],
            severity=data.get("max_percent"),
        )
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="net", description="Network throughput and totals")
    async def net(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("network")
        if collector is None:
            await interaction.followup.send("Network stats are unavailable.")
            return

        data = collector.collect()
        embed = build_stats_embed("Network", data["fields"])
        await interaction.followup.send(embed=embed)

    @stats_access
    @app_commands.command(name="uptime", description="System uptime and boot time")
    async def uptime(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        collector = get_collector("system")
        if collector is None:
            await interaction.followup.send("Uptime stats are unavailable.")
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
        embed = build_stats_embed("Uptime", fields, footer=data.get("hostname"))
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
        lines = [format_process_line(proc, cpu, mem) for proc, cpu, mem in processes]

        label = "CPU" if metric == "cpu" else "Memory"
        value = "\n".join(lines) if lines else "No process data available."
        fields = [{"name": f"Top {count} by {label}", "value": value, "inline": False}]
        embed = build_stats_embed(f"Top Processes · {label}", fields)
        await interaction.followup.send(embed=embed)
