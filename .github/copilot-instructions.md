# Copilot Instructions

## Repository Overview

This repository contains a Python-based Discord bot that automatically archives media content (YouTube videos) from specified Discord channels. The bot monitors configured channels, validates URLs, downloads YouTube videos using yt-dlp, and stores them on the host server. It uses reaction emojis (✅ success, ❌ failure) to indicate archiving status.

**Size**: Small project (~5 source files)  
**Language**: Python 3.10  
**Type**: Discord bot / media archiver

---

## Project Layout

```
Discord-Archive-Bot/
├── .github/
│   └── copilot-instructions.md   # This file
├── bot.py                        # Core Bot class (discord.py), message handling, URL validation, yt-dlp integration
├── main.py                       # Entry point: loads .env, initializes logging, starts Bot
├── config.yaml                   # Bot configuration (command prefix, archive channels, archive path)
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image definition (python:3.10-slim)
├── docker_build.sh               # Script to build and run Docker container
├── README.md                     # Project documentation
└── .gitignore                    # Ignores .env, __pycache__, archive/, *.log
```

### Key Source Files

- **`bot.py`**: Defines `Bot(discord.ext.commands.Bot)`. Key methods:
  - `__init__`: loads `config.yaml`, sets up logger and yt-dlp config, calls `super().run(token)`
  - `on_ready`: processes last 100 messages in each configured channel on startup
  - `on_message` / `process_message`: validates URLs, downloads YouTube videos, adds reactions
  - `download_youtube_video`: wraps yt-dlp, returns `bool` success
  - `_init_logger`: dual logging (console INFO, file DEBUG) to `./bot.log`
- **`main.py`**: Calls `load_dotenv()`, reads `DISCORD_TOKEN` env var, instantiates `Bot`
- **`config.yaml`**: YAML config with keys `archive_path`, `archive_channels` (list), `command_prefix`

### Configuration

- **`.env`** (not committed): Must contain `DISCORD_TOKEN=<your-bot-token>`
- **`config.yaml`**: Controls `command_prefix`, `archive_channels`, and `archive_path`
- The bot reads `config.yaml` at startup relative to the working directory

### Constants (in `bot.py`)

- `HISTORY_LIMIT = 100` — messages to process per channel on startup
- `YT_NETLOCS = ["youtu.be", "www.youtube.com"]` — recognized YouTube domains

---

## Dependencies

Defined in `requirements.txt`:

```
discord.py==2.3.1
python-dotenv==1.0.0
validators==0.20.0
yt-dlp
pyyaml==6.0.1
```

Install with:
```bash
pip install -r requirements.txt
```

> **Note**: Most dependencies are pinned to specific versions. If you update a dependency version, verify compatibility with the rest of the stack and check for known security advisories.

---

## Bootstrap, Build, and Run

### Running without Docker

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env with your Discord bot token
echo "DISCORD_TOKEN=<your-token>" > .env

# 3. Edit config.yaml to set archive_path, archive_channels, command_prefix

# 4. Ensure the archive directory exists
mkdir -p ./archive

# 5. Run the bot
python main.py
```

### Running with Docker

```bash
# Build and run (mounts ./archive to /archive in the container)
./docker_build.sh
```

The Docker image is based on `python:3.10-slim`. The host `./archive` directory is mounted to `/archive` inside the container. The container is run with `--env-file=.env`.

---

## Testing

There is no automated test suite in this repository. Validate changes manually by:

1. Running `python main.py` with a valid `.env` and `config.yaml`
2. Posting a YouTube URL in a configured Discord channel and verifying the ✅/❌ reaction and that the video file appears in the archive directory
3. Checking `bot.log` for errors

---

## Linting

No linter is configured. Follow PEP 8 style conventions for any Python changes.

---

## Architecture Notes

- `Bot.__init__` calls `super().run(token)` which blocks — the bot runs until interrupted
- `config.yaml` path is relative to the working directory; always run from the repo root
- yt-dlp stores a download history in `<archive_path>/.archive` to avoid re-downloading
- The bot does **not** process its own messages (checked via `message.author == self.user`)
- Channel filtering: if `archive_channels` is non-empty, only messages from those channels are processed (matched by channel name string)
- The `$hello` command (hardcoded in `process_message`) responds with "Hello!" for testing
