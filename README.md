# Discord Server Stats Bot

A Python Discord bot that reports **local Ubuntu server statistics** via slash commands. Built with `discord.py` and `psutil`, using a pluggable collector registry so Docker container stats can be added later without changing commands.

## Features

| Command | Description |
|---------|-------------|
| `/stats` | Overview of all enabled collectors |
| `/cpu` | CPU usage, load average, temperature |
| `/mem` | RAM and swap usage |
| `/disk` | Disk usage per mount (skips tmpfs/overlay/snap loops) |
| `/net` | Network throughput and totals |
| `/uptime` | Uptime and boot time |
| `/top` | Top processes by CPU or memory |

Access is restricted by guild ID and optional role allowlist (see Configuration).

## Requirements

- Ubuntu 26.04 LTS (or similar Linux host)
- Python 3.12+
- A Discord application with bot token

## Discord setup

1. Create an application at [Discord Developer Portal](https://discord.com/developers/applications).
2. Under **Bot**, create a bot and copy the token.
3. Enable **Privileged Gateway Intents** only if you need them later (this bot uses default intents).
4. Under **OAuth2 → URL Generator**, select:
   - Scopes: `bot`, `applications.commands`
   - Bot permissions: minimal (no special permissions required for slash commands in allowed roles)
5. Invite the bot to your server using the generated URL.

## Local development (Windows or Linux)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DISCORD_TOKEN and GUILD_ID

python bot.py
```

Set `GUILD_ID` to your test server ID for instant slash-command sync during development.

## Configuration

Copy `.env.example` to `.env` (or use `/etc/dc-bot.env` on the server):

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Bot token from Discord Developer Portal |
| `GUILD_ID` | Guild ID for guild-scoped command sync (0 = global sync) |
| `ALLOWED_ROLE_IDS` | Comma-separated role IDs; empty = any guild member |

## Production deployment on Ubuntu 26.04

Ubuntu uses an externally managed system Python (PEP 668), so deploy with a virtual environment:

```bash
sudo adduser --system --group --home /opt/dc-bot dcbot
sudo mkdir -p /opt/dc-bot
sudo rsync -a --exclude venv --exclude .env . /opt/dc-bot/
cd /opt/dc-bot
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
sudo chown -R dcbot:dcbot /opt/dc-bot
```

Create environment file (restrict permissions):

```bash
sudo cp .env.example /etc/dc-bot.env
sudo chmod 600 /etc/dc-bot.env
sudo chown root:root /etc/dc-bot.env
# Edit /etc/dc-bot.env with production values
```

Install and start the systemd unit:

```bash
sudo cp deploy/dc-bot.service /etc/systemd/system/dc-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now dc-bot
```

View logs:

```bash
journalctl -u dc-bot -f
```

## Architecture

Collectors register themselves via `@register` in `collectors/`. Slash commands in `cogs/stats.py` call collectors and render embeds via `utils/embeds.py`.

```
Discord → cogs/stats.py → collectors/* → psutil
                       → utils/embeds.py → Discord
```

## Extending: Docker container stats

The `collectors/docker.py` stub is disabled unless `/var/run/docker.sock` exists. To add real container stats:

1. Install the Docker SDK:
   ```bash
   pip install docker
   ```
2. Add the service user to the `docker` group:
   ```bash
   sudo usermod -aG docker dcbot
   ```
3. Implement `DockerCollector.collect()` to return per-container CPU, memory, and status.
4. Restart the bot — `/stats` will automatically include the Docker section when the collector is enabled.

No changes are required in `cogs/stats.py`; the registry picks up enabled collectors automatically.

## Security notes

- Keep `DISCORD_TOKEN` and `/etc/dc-bot.env` readable only by root (`chmod 600`).
- Use `ALLOWED_ROLE_IDS` so only admins/operators can query system stats.
- The bot runs as unprivileged `dcbot` with systemd hardening in `deploy/dc-bot.service`.

## License

MIT (or your choice — add a LICENSE file if needed).
