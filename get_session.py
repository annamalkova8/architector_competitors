# run_once_get_session.py  (run locally, not on Railway)
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv
load_dotenv()

with TelegramClient(StringSession(), int(os.environ["API_ID"]), os.environ["API_HASH"]) as client:
    print("SESSION STRING:", client.session.save())