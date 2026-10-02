import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "0"))
PLAYER_GROUP_ID = int(os.getenv("PLAYER_GROUP_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required in .env file")
