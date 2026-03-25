from bot import Bot
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    load_dotenv()  # take environment variables from .env.
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN environment variable is not set. "
            "Please create a .env file with DISCORD_TOKEN=<your-bot-token>."
        )
    bot = Bot()
    bot.run(token=token)
