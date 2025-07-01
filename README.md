# Discord Archive Bot

This repository contains a Python-based Discord bot designed to automatically archive media content from specified Discord channels. The bot listens for YouTube video links in configured channels, downloads them using yt-dlp, and stores them on the host server. Built with Discord.py and Docker support, it provides a scalable solution for archiving media, with extensible features for webpage scraping, file archiving, and role-based permissions. The bot is ideal for automated data collection, applicable to manufacturing data logging and archival systems.

## Table of Contents
- [Discord Archive Bot](#discord-archive-bot)
  - [Project Overview](#project-overview)
  - [Features](#features)
  - [Approach](#approach)
  - [Tools and Technologies](#tools-and-technologies)
  - [Setup and Usage](#setup-and-usage)
  - [References](#references)

## Project Overview
The Discord Archive Bot automates the archiving of YouTube video links posted in specified Discord channels. It uses Discord.py to monitor messages, validates URLs, and downloads videos to a configured host directory using yt-dlp. The bot supports Docker for easy deployment and includes a configurable setup via YAML and environment variables. Currently, it archives YouTube videos, with planned features for webpage scraping, Discord file archiving, and role-based permissions. The system processes up to 100 messages per channel on startup, adding reaction emojis (✅ for success, ❌ for failure) to indicate archiving status.

## Features
- [x] Download and archive linked Youtube videos
- [ ] Scape and archive linked webpages
- [ ] Download and archive posted Discord files (images, documents, videos, etc.)
- [ ] Download and archive linked Rumble videos
- [x] Docker support
- [ ] Host server file navigation & status
- [ ] Role permissions

## Approach
The project is structured as a modular bot system:
- **Bot Core (`bot.py`)**: Implements a `Bot` class using Discord.py, handling message events and URL processing. Validates URLs with the `validators` library and downloads YouTube videos using yt-dlp with progress logging. Supports reaction emojis for user feedback and a `$hello` command for testing.
- **Configuration (`config.yaml`, `.env`)**: Uses YAML for bot settings (e.g., command prefix, archive channels, archive path) and `.env` for secure storage of the Discord bot token.
- **Main Script (`main.py`)**: Initializes the bot, loads environment variables, and sets up logging for debugging and monitoring.
- **Docker Support (`dockerfile`, `docker_build.sh`)**: Provides a lightweight Docker image (`python:3.10-slim`) for deployment, mounting a host archive directory to store downloaded videos.
- **Logging**: Implements dual logging (console and file) for tracking bot activity, errors, and download progress.

The bot processes messages by:
1. Checking if the message is from a configured channel and not sent by itself.
2. Validating URLs and identifying YouTube links (`youtu.be`, `www.youtube.com`).
3. Downloading videos to the specified archive path, maintaining a download history to avoid duplicates.
4. Adding reaction emojis to indicate success or failure.

## Tools and Technologies
- **Python**: Core language for bot logic and media downloading.
- **Discord.py**: Library for interacting with the Discord API.
- **yt-dlp**: Tool for downloading YouTube videos.
- **validators**: Library for URL validation.
- **PyYAML**: Parsing configuration files.
- **python-dotenv**: Managing environment variables for secure token storage.
- **Docker**: Containerization for portable deployment.
- **Logging**: Dual console and file logging for debugging and monitoring.

## Setup and Usage
1. **Prerequisites**:
   - Clone the repository: `git clone <repository-url>`
   - Create a Discord bot application via [Discord Developer Portal](https://discord.com/developers/docs/intro) with message content intent enabled and invite it to your server.
   - Install Docker (optional) for containerized deployment.
2. **Configuration**:
- Create `.env` with `DISCORD_TOKEN=<your-bot-token>`.
- Edit `config.yaml` to specify archive channels and path (e.g., `archive_path: /archive`).
- Example `config.yaml`:
  ```yaml
  command_prefix: $
  archive_channels:
    - general
    - media
  archive_path: /archive
  ```
3. **Running**:
- **With Docker**: Run `./docker_build.sh` to build and start the container, ensuring the archive directory is mounted.
- **Without Docker**: Install dependencies (`pip install -r requirements.txt`) and run `python main.py`.
4. **Notes**:
- The bot archives YouTube videos from specified channels and responds to `$hello`.
- Ensure the archive directory exists and is writable.
- Web version may have limitations; Docker or local deployment recommended for full functionality.

## References
- [Discord.py Documentation](https://discordpy.readthedocs.io/en/stable/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Docker Documentation](https://docs.docker.com/)
- [validators Documentation](https://validators.readthedocs.io/en/latest/)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
