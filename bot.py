import asyncio
import logging
import discord
import validators
from urllib.parse import urlparse, ParseResult
import yt_dlp
import os
import yaml

# bot consts
HISTORY_LIMIT = 100
YT_NETLOCS = ["youtu.be", "www.youtube.com"]


class Bot(discord.ext.commands.Bot):

    def __init__(self):
        # define intents
        intents = discord.Intents.default()
        intents.message_content = True

        # load bot config
        with open('config.yaml', 'r') as f:
            self.cfg = yaml.safe_load(f)

        # init logger
        self.logger = self._init_logger()

        # init youtube downloader config
        self.ytdl_config = {
            'logger': self.logger,
            'paths': {'home': self.cfg.get('archive_path')},
            'download_archive': os.path.join(self.cfg.get('archive_path'), '.archive'),
            'progress_hooks': [self.video_progress_hook],
            # Robust format selection: prefer mp4, fall back to best available
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            # Retry on transient errors
            'retries': 10,
            'fragment_retries': 10,
            # Use a larger HTTP chunk size to reduce throttling
            'http_chunk_size': 10485760,  # 10 MB
        }

        # init base client class
        super().__init__(command_prefix=self.cfg.get('command_prefix'), intents=intents)

    async def on_ready(self):
        self.logger.info(f"Ready from {self.user}!")
        for channel_name in self.cfg.get('archive_channels', []):
            channel = discord.utils.get(self.get_all_channels(), name=channel_name)
            if channel is None:
                self.logger.warning(f"Configured channel '{channel_name}' not found; skipping.")
                continue
            async for msg in channel.history(limit=HISTORY_LIMIT, oldest_first=False):
                await self.process_message(msg)

    async def on_message(self, message):
        await self.process_message(message)
        await self.process_commands(message)

    async def process_message(self, message):
        # check for bot messages
        if message.author == self.user:
            return

        # check if message is from configured channel(s)
        archive_channels = self.cfg.get('archive_channels', [])
        if archive_channels and str(message.channel) not in archive_channels:
            return

        # is this message a url?
        if self.is_url(message.content):
            parsed_url = urlparse(message.content)
            self.logger.info(parsed_url)

            # is this a youtube video url?
            if self.is_youtube_url(parsed_url):
                yt_url = message.content
                success = await self.download_youtube_video(yt_url)
                if success:
                    await message.add_reaction("✅")
                else:
                    await message.add_reaction("❌")

        if message.content.startswith("$hello"):
            await message.channel.send("Hello!")

    @classmethod
    def is_url(cls, text: str) -> bool:
        return validators.url(text)

    @classmethod
    def is_youtube_url(cls, result: ParseResult) -> bool:
        return result.netloc in YT_NETLOCS

    async def download_youtube_video(self, url: str) -> bool:
        """
        Attempts to download a video from the given URL.
        Runs yt-dlp in a thread pool to avoid blocking the event loop.
        Returns True if successful.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_youtube_video_sync, url)

    def _download_youtube_video_sync(self, url: str) -> bool:
        """Synchronous yt-dlp download, intended to be run in a thread pool executor."""
        try:
            with yt_dlp.YoutubeDL(self.ytdl_config) as ydl:
                err = ydl.download([url])
                return not err
        except Exception as e:
            self.logger.error(f"Download failed for {url}: {e}")
            return False

    def video_progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            self.logger.info(f"{d.get('_percent_str', '?%')} of {d.get('filename', 'unknown')}")
        elif status == 'finished':
            self.logger.info(f"Download finished: {d.get('filename', 'unknown')}")

    @classmethod
    def _init_logger(cls):
        """
        Initializes the bot logger.
        Logs to both log file and standard output.
        """
        logger = logging.getLogger("bot")
        logger.setLevel(logging.DEBUG)
        log_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_format)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

        info_handler = logging.FileHandler('./bot.log')
        info_handler.setFormatter(log_format)
        info_handler.setLevel(logging.DEBUG)
        logger.addHandler(info_handler)
        return logger
