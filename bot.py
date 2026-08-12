"""Discord server stats bot entrypoint."""

import logging
import sys

import discord
import psutil
from discord.ext import commands

import collectors  # noqa: F401 — register collectors
from config import DISCORD_TOKEN, GUILD_ID
from cogs.stats import Stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dc_bot")


class StatsBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.add_cog(Stats(self))
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %d command(s) to guild %s", len(synced), GUILD_ID)
        else:
            synced = await self.tree.sync()
            logger.info("Synced %d global command(s)", len(synced))

    async def on_ready(self) -> None:
        psutil.cpu_percent(interval=0.1)
        logger.info("Logged in as %s (id=%s)", self.user, self.user.id)


def main() -> None:
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set. Copy .env.example to .env and configure it.")
        sys.exit(1)

    bot = StatsBot()
    bot.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
