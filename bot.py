import logging
import discord
from discord.ext.commands import bot, command


class Bot(discord.ext.commands.Bot):
    def __init__(self, token: str):
        # define intents
        intents = discord.Intents.default()
        intents.message_content = True

        # init base client class
        super().__init__(command_prefix="!", intents=intents)

        # run client
        super().run(token=token)

    async def on_ready(self):
        logging.info(f"Ready from {self.user}!")

    async def on_message(self, message):
        logging.info("on_message()")
        if message.author == self.user:
            return
        if message.content.startswith("$hello"):
            await message.channel.send("Hello!")
        logging.info(message.channel)
