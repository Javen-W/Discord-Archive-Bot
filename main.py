from bot import Bot
from dotenv import load_dotenv
import logging
import os

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    load_dotenv()  # take environment variables from .env.
    token = os.getenv('DISCORD_TOKEN')
    bot = Bot(token=token)
