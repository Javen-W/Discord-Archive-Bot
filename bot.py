import discord
from discord import Intents, client


class Bot(discord.Client):
    def __init__(self, token: str):
        # define intents
        intents = discord.Intents.default()
        intents.message_content = True

        # init base client class
        super().__init__(intents=Intents.All)
        super().run(token=token)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')
