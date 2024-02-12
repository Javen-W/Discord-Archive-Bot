import logging
import discord
from discord.ext.commands import bot, command
import validators
from urllib.parse import urlparse, ParseResult
import yt_dlp
import os


class Bot(discord.ext.commands.Bot):

    video_netlocs = ["youtu.be"]

    def __init__(self, token: str):
        # define intents
        intents = discord.Intents.default()
        intents.message_content = True

        # load bot config TODO
        self.archive_channels = ["archive", "test"]
        self.output_path = './archive'
        self.ytdl_config = {
            'paths': {'home': self.output_path},
            'download_archive': os.path.join(self.output_path, 'archive_ledger.txt'),
            'progress_hooks': [self.video_progress_hook],
        }

        # init base client class
        super().__init__(command_prefix="!", intents=intents)

        # run client
        super().run(token=token)

    async def on_ready(self):
        logging.info(f"Ready from {self.user}!")
        # self.download_video('https://www.youtube.com/watch?v=osGTtARJlJs')

    async def on_message(self, message):
        # check for bot messages
        if message.author == self.user:
            return

        # check if message is from configured channel(s)
        if len(self.archive_channels) and str(message.channel) not in self.archive_channels:
            return

        # is this message an url?
        if self.is_url(message.content):
            logging.info("is url")
            parsed_url = urlparse(message.content)
            logging.info(parsed_url)

            # is this a video url?
            if self.is_video_url(parsed_url):
                logging.info("is video url")
                self.download_video(message.content)

        else:
            logging.info("not url")

        if message.content.startswith("$hello"):
            await message.channel.send("Hello!")

    @classmethod
    def is_url(cls, text: str) -> bool:
        return validators.url(text)

    @classmethod
    def is_video_url(cls, result: ParseResult) -> bool:
        return result.netloc in cls.video_netlocs

    def download_video(self, url: str):
        # TODO is youtube video?
        with yt_dlp.YoutubeDL(self.ytdl_config) as ydl:
            err = ydl.download([url])
            if err:
                logging.error("Failed to download youtube video!", err)

    @classmethod
    def video_progress_hook(cls, d):
        logging.info(d['_percent_str'])
