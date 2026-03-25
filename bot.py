import asyncio
import datetime
import json
import logging
import logging.handlers
import os
import re
import discord
import validators
import yaml
import yt_dlp
import yt_dlp.utils
from urllib.parse import urlparse, ParseResult

# bot consts
HISTORY_LIMIT = 100

# All recognised YouTube netlocs (desktop, mobile, music, short-link)
YT_NETLOCS = {
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}

# Logs directory (relative to working directory)
LOGS_DIR = "./logs"

# Video file extensions recognised during archive scanning
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.m4v'}


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
            # Download entire playlists; skip unavailable items without aborting
            'noplaylist': False,
            'ignoreerrors': True,
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

        # Backfill metadata for any existing archived videos that are missing it.
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._backfill_metadata_sync)

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
        """
        Returns True for any YouTube URL variant:
        regular videos, Shorts, playlists, livestreams, YouTube Music, and mobile links.
        """
        return result.netloc in YT_NETLOCS

    async def download_youtube_video(self, url: str) -> bool:
        """
        Attempts to download a video from the given URL.
        Runs yt-dlp in a thread pool to avoid blocking the event loop.
        Returns True if successful.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._download_youtube_video_sync, url)

    def _download_youtube_video_sync(self, url: str) -> bool:
        """Synchronous yt-dlp download, intended to be run in a thread pool executor."""
        try:
            archive_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            with yt_dlp.YoutubeDL(self.ytdl_config) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return False
                # Generate metadata for each downloaded entry (handles playlists too).
                entries = info.get('entries')
                if entries is not None:
                    for entry in entries:
                        if entry:
                            self._generate_metadata(ydl, entry, archive_date)
                else:
                    self._generate_metadata(ydl, info, archive_date)
                return True
        except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
            self.logger.error(f"yt-dlp error for {url}: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"Unexpected error downloading {url}: {e}")
            return False

    def _find_video_file(self, ydl: yt_dlp.YoutubeDL, info: dict) -> str | None:
        """
        Attempts to locate the actual video file on disk for the given yt-dlp info dict.
        yt-dlp may change the extension after merging streams, so common extensions are tried
        if the primary expected path does not exist.
        Returns the file path if found, otherwise None.
        """
        expected_path = ydl.prepare_filename(info)
        if os.path.exists(expected_path):
            return expected_path
        base = os.path.splitext(expected_path)[0]
        for ext in VIDEO_EXTENSIONS:
            candidate = base + ext
            if os.path.exists(candidate):
                return candidate
        return None

    def _generate_metadata(
        self,
        ydl: yt_dlp.YoutubeDL,
        info: dict,
        archive_date: str | None = None,
        video_path: str | None = None,
    ) -> bool:
        """
        Generates a JSON metadata file alongside the downloaded video file.
        The file shares the video's base name with a .json extension.
        Returns True if the metadata was written successfully.
        """
        if not info:
            return False

        try:
            if video_path is None:
                video_path = self._find_video_file(ydl, info)

            if video_path:
                metadata_path = os.path.splitext(video_path)[0] + '.json'
            else:
                # Fall back: place metadata in the archive directory named by video ID.
                archive_dir = self.cfg.get('archive_path', './archive')
                video_id = info.get('id', 'unknown')
                metadata_path = os.path.join(archive_dir, f"{video_id}.json")
                self.logger.warning(
                    f"Video file not found for '{video_id}'; "
                    f"metadata will be written to {metadata_path}"
                )

            # Convert yt-dlp's YYYYMMDD upload_date to ISO 8601.
            upload_date_raw = info.get('upload_date')
            upload_date = None
            if upload_date_raw:
                try:
                    upload_date = datetime.datetime.strptime(
                        upload_date_raw, '%Y%m%d'
                    ).strftime('%Y-%m-%d')
                except ValueError:
                    upload_date = upload_date_raw

            file_size = None
            if video_path and os.path.exists(video_path):
                file_size = os.path.getsize(video_path)

            metadata = {
                'title': info.get('title'),
                'creator': info.get('uploader') or info.get('channel'),
                'upload_date': upload_date,
                'archive_date': archive_date or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'file_size_bytes': file_size,
                'description': info.get('description'),
                'original_url': info.get('webpage_url') or info.get('original_url'),
                'duration_seconds': info.get('duration'),
                'video_id': info.get('id'),
                'thumbnail_url': info.get('thumbnail'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'tags': info.get('tags') or [],
                'categories': info.get('categories') or [],
                'age_limit': info.get('age_limit'),
            }

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Metadata saved: {metadata_path}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to generate metadata for '{info.get('id', 'unknown')}': {e}"
            )
            return False

    def _backfill_metadata_sync(self) -> None:
        """
        Scans the archive directory for video files that are missing a companion
        metadata JSON file and attempts to fetch and write the missing metadata from
        YouTube without re-downloading the video.
        Intended to run in a thread pool executor so the event loop is not blocked.
        """
        archive_path = self.cfg.get('archive_path', './archive')
        if not os.path.isdir(archive_path):
            self.logger.debug("Archive directory does not exist; skipping metadata backfill.")
            return

        missing = []
        for filename in os.listdir(archive_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in VIDEO_EXTENSIONS:
                continue
            video_path = os.path.join(archive_path, filename)
            metadata_path = os.path.splitext(video_path)[0] + '.json'
            if not os.path.exists(metadata_path):
                missing.append((filename, video_path))

        if not missing:
            self.logger.debug("No videos are missing metadata; skipping backfill.")
            return

        self.logger.info(f"Backfilling metadata for {len(missing)} video(s).")

        # Build a lightweight config for metadata-only fetching (no download).
        fetch_config = {
            k: v for k, v in self.ytdl_config.items()
            if k not in ('progress_hooks', 'download_archive')
        }
        fetch_config['logger'] = self.logger

        for filename, video_path in missing:
            # yt-dlp's default output template (%(title)s [%(id)s].%(ext)s) embeds the
            # YouTube video ID (always exactly 11 chars) in square brackets at the end of
            # the base name.  The pattern below matches that convention to extract the ID.
            match = re.search(r'\[([A-Za-z0-9_-]{11})\]', filename)
            if not match:
                self.logger.warning(
                    f"Cannot determine video ID from filename '{filename}'; "
                    "skipping metadata backfill for this file."
                )
                continue

            video_id = match.group(1)
            yt_url = f"https://www.youtube.com/watch?v={video_id}"
            self.logger.info(f"Fetching metadata for '{filename}' (ID: {video_id})")

            try:
                with yt_dlp.YoutubeDL(fetch_config) as ydl:
                    info = ydl.extract_info(yt_url, download=False)
                    if info:
                        # Approximate the archive date from the file's modification time.
                        mtime = os.path.getmtime(video_path)
                        archive_date = datetime.datetime.fromtimestamp(
                            mtime, tz=datetime.timezone.utc
                        ).strftime('%Y-%m-%dT%H:%M:%SZ')
                        self._generate_metadata(ydl, info, archive_date, video_path)
                    else:
                        self.logger.warning(f"No metadata returned for '{filename}'.")
            except Exception as e:
                self.logger.error(f"Error backfilling metadata for '{filename}': {e}")

    def video_progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            self.logger.info(f"{d.get('_percent_str', '?%')} of {d.get('filename', 'unknown')}")
        elif status == 'finished':
            self.logger.info(f"Download finished: {d.get('filename', 'unknown')}")
        elif status == 'error':
            self.logger.error(f"Download error for: {d.get('filename', 'unknown')}")

    @classmethod
    def _init_logger(cls):
        """
        Initializes the bot logger.
        Logs to the console (INFO+) and to a daily-rotating file in ./logs/ (DEBUG+).
        Each run's log file is named bot.log and rotated at midnight, keeping 30 days.
        """
        os.makedirs(LOGS_DIR, exist_ok=True)

        logger = logging.getLogger("bot")
        logger.setLevel(logging.DEBUG)
        log_format = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_format)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

        # Rotate the log file daily; keep 30 days of history
        log_file = os.path.join(LOGS_DIR, "bot.log")
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when='midnight', interval=1, backupCount=30, encoding='utf-8',
        )
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        return logger
