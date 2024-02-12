# Discord Archive Bot
A simple Python3 Discord bot for interfacing with data archiving utilities. Simply configure & host the application for your server, then any linked or hard-copied media posted to the configured channels are automatically listened for and archived to the host server machine.

## Features
- [x] Download and archive linked Youtube videos
- [ ] Scape and archive linked webpages
- [ ] Download and archive posted Discord files (images, documents, videos, etc.)
- [ ] Download and archive linked Rumble videos
- [x] Docker support
- [ ] Host server file navigation & status
- [ ] Role permissions

## Setup
1. Create a Discord [bot application](https://discord.com/developers/docs/intro) with the appropriate permissions then invite the bot to the desired Discord server through the developer portal.
3. Clone the code repository and navigate to the root project directory.
4. Create an `.env` file containing an environment variable for your bot token `DISCORD_TOKEN=...`.
5. Modify `config.yaml` and optionally `docker_build.sh` for your needs.
6. If using Docker, start the program by running `docker_build.sh`. Otherwise, install the required dependences in `requirements.txt` and start the program by running `main.py`.
