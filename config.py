from dotenv import load_dotenv
load_dotenv()

import os

# --- Telegram bot (existing) ---
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
_thread_id_raw = os.environ.get("TELEGRAM_MESSAGE_THREAD_ID", "").strip()
TELEGRAM_MESSAGE_THREAD_ID = int(_thread_id_raw) if _thread_id_raw else None

# --- Telethon (user account, for reading channels) ---
TELETHON_API_ID = int(os.environ["API_ID"])
TELETHON_API_HASH = os.environ["API_HASH"]
TELETHON_SESSION = os.environ.get("TELETHON_SESSION", "competitor_bot")

TG_CHANNELS = [
    "revertaza_longevity",
    "AgeManagment",
    "preventage_chat",
    "dietolog_kononenko_spb",
]

# --- OpenAI ---
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")

# --- Competitors (existing) ---
COMPETITORS = [
    {"name": "Peloton", "query_hint": "Peloton fitness platform (bike/treadmill/app)"},
    {"name": "Dacadoo", "query_hint": "Scientifically proven digital health technology software that benefits your business, customers, prospects, and employees."},
    {"name": "Whoop", "query_hint": "Whoop fitness/recovery wearable and app"},
    {"name": "Welltory", "query_hint": "Welltory HRV and health analytics app"},
    {"name": "Bevel", "query_hint": "Bevel health/recovery platform"},
]

LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "14"))
SCHEDULE_INTERVAL_DAYS = int(os.environ.get("SCHEDULE_INTERVAL_DAYS", "14"))
COMMAND_NAME = "update"