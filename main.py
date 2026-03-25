from bot import Bot
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    load_dotenv()  # take environment variables from .env.
    token = os.getenv('DISCORD_TOKEN')
    bot = Bot()
    bot.run(token=token)
