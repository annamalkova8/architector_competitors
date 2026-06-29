"""
Configuration for the competitor-update Telegram bot.

Edit COMPETITORS to add/remove companies you want tracked.
Everything else comes from environment variables (see .env.example).
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Competitors to track. Add/remove freely.
# `query_hint` gives the model extra context so search results stay relevant
# (useful for names that collide with other products/companies).
# ---------------------------------------------------------------------------
COMPETITORS = [
    {"name": "Peloton", "query_hint": "Peloton fitness platform (bike/treadmill/app)"},
    {"name": "Decathlon Coach / Decathlon health", "query_hint": "Decathlon digital health or fitness coaching product"},
    {"name": "Whoop", "query_hint": "Whoop fitness/recovery wearable and app"},
    {"name": "Welltory", "query_hint": "Welltory HRV and health analytics app"},
    {"name": "Bevel", "query_hint": "Bevel health/recovery platform"},
]

# ---------------------------------------------------------------------------
# Lookback window for "what's new" — keeps results focused on recent news
# rather than the model recalling old facts from training data.
# ---------------------------------------------------------------------------
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "14"))

# ---------------------------------------------------------------------------
# Telegram target: a specific forum topic inside a supergroup.
# CHAT_ID is the supergroup id (negative number, e.g. -1004296790192).
# MESSAGE_THREAD_ID is the forum topic id. Leave unset/blank to post to
# "General" instead of a specific topic.
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
_thread_id_raw = os.environ.get("TELEGRAM_MESSAGE_THREAD_ID", "").strip()
TELEGRAM_MESSAGE_THREAD_ID = int(_thread_id_raw) if _thread_id_raw else None

# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")

# ---------------------------------------------------------------------------
# Schedule: every N days (default 14 = every 2 weeks).
# The bot computes "next run" from this interval starting at process boot,
# so the exact day-of-week will drift to whenever the process started.
# If you want a fixed day/time instead, see the README section on Railway Cron.
# ---------------------------------------------------------------------------
SCHEDULE_INTERVAL_DAYS = int(os.environ.get("SCHEDULE_INTERVAL_DAYS", "14"))

# Command that triggers an on-demand summary
COMMAND_NAME = "update"
