import logging
import discord


class Bot(discord.Client):
    def __init__(self, token: str):
        # define intents
        intents = discord.Intents.default()
        intents.message_content = True

        # init base client class
        super().__init__(intents=intents)

        # run client
        super().run(token=token)

    async def on_ready(self):
        logging.info(f"Ready from f{self.user}!")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith("$hello"):
            await message.channel.send("Hello!")
