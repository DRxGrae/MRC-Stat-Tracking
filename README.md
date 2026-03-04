# MRC Discord Bot

Python Discord bot using `discord.py`, managed with `uv`, designed to run in Docker (DigitalOcean-friendly).

## Features

- Message context menu command: right-click a message -> Apps -> `Image dimensions`
- Message context menu command: right-click a message -> Apps -> `Get stats` (admin-only OCR + debug overlay)
- Admin-only (requires Discord `Administrator` permission)
- Attachment-only: reads image attachments on the selected message
- Replies ephemerally with each image's `WIDTHxHEIGHT`

## Local development

Prereqs:

- Python 3.12 installed (required for OCR dependencies)
- `uv` installed (`pip install uv`)

Install deps:

```bash
uv python install 3.12.12

# If you previously created a venv with a different Python version, delete it first.
# PowerShell: Remove-Item -Recurse -Force .venv
# cmd.exe:    rmdir /s /q .venv

uv sync -p 3.12.12
```

Create a local `.env` (recommended):

```bat
copy .env.example .env
```

Set `DISCORD_TOKEN` inside `.env`.

The bot will automatically load `.env` on startup for local development.

Run:

```bash
uv run python -m bot
```

Optional (faster command updates while developing):

- Set `DISCORD_GUILD_ID` to a server ID you control. The bot will sync commands to that guild as well as globally.

Add it to `.env`:

```text
DISCORD_GUILD_ID=123456789012345678
```

## PyCharm run configuration

1. Set interpreter to the project venv: `.venv\\Scripts\\python.exe`
2. Create a Run Configuration:
   - Type: Python
   - Module name: `bot`
   - Working directory: repo root
   - Environment variables: `DISCORD_TOKEN=...` (and optional `DISCORD_GUILD_ID=...`)

## Discord setup

1. Create an application at https://discord.com/developers/applications
2. Bot -> create a bot user
3. Copy the bot token and set it as `DISCORD_TOKEN`
4. OAuth2 -> URL Generator
   - Scopes: `bot`, `applications.commands`
   - Bot permissions: no privileged intents required; permissions can be minimal (command is admin-gated)
5. Use the generated URL to invite the bot to your servers

## Environment variables

- `DISCORD_TOKEN` (required): bot token
- `DISCORD_GUILD_ID` (optional): dev guild id for faster command sync
- `PADDLEOCR_HOME` (optional): where OCR models/cache are stored (Docker default: `/app/.cache`)

## Run on DigitalOcean (Docker)

You can run this on either DigitalOcean App Platform (recommended for simple hosting) or a Droplet.

### Option A: DigitalOcean App Platform

1. Push this repo to GitHub/GitLab
2. In DigitalOcean: Create -> Apps -> link your repo
3. Choose Dockerfile-based build (it will use `Dockerfile`)
4. Make sure the component type is a `Worker` (not a Web Service)
5. Add environment variables:
    - `DISCORD_TOKEN` (required)
    - `DISCORD_GUILD_ID` (optional; speeds up command iteration)
6. Deploy

Notes:

- Global app command updates can take time to propagate in Discord. For faster iteration, set `DISCORD_GUILD_ID` while testing.
- The first OCR run may download models. App Platform containers have ephemeral disks; expect re-downloads on redeploy unless you add persistent storage.

### Option B: DigitalOcean Droplet

These instructions assume a DigitalOcean Droplet with Docker installed.

### 1) Provision a Droplet

- Create a Droplet (Ubuntu recommended)
- SSH into it

Install Docker + Compose (if not already installed):

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

### 2) Deploy

On the Droplet:

```bash
git clone <your-repo-url>
cd MRC-Stat-Tracking
```

Create an `.env` file (do not commit it):

```bash
cat > .env <<'EOF'
DISCORD_TOKEN=your_token_here
# Optional: speeds up command iteration for one guild
# DISCORD_GUILD_ID=123456789012345678
EOF
```

Build and run:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f
```

Update to latest:

```bash
git pull
docker compose up -d --build
```

Notes:

- Global app command updates can take time to propagate in Discord. For faster iteration, set `DISCORD_GUILD_ID` while testing.

## How to use

In a server where the bot is installed:

1. Find a message with an image attachment
2. Right click the message -> Apps -> `Image dimensions`
3. If you have Administrator permission, the bot responds ephemerally with the dimensions

OCR:

1. Find a message with a scoreboard screenshot as an image attachment
2. Right click the message -> Apps -> `Get stats`
3. If you have Administrator permission, the bot responds ephemerally with an embed containing parsed stats + a debug overlay image

## Numpy integration

The OCR pipeline already works with numpy arrays via OpenCV. If you open images with Pillow elsewhere, converting is straightforward:

```py
arr = np.asarray(img)
```
