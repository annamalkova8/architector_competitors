"""
Main entrypoint.

Runs a single long-lived process that:
  1. Listens for the /update command (polling) and replies with a fresh
     competitor summary on demand.
  2. Schedules a recurring job (every SCHEDULE_INTERVAL_DAYS, default 14)
     that posts the same summary automatically.

Both paths post to the same configured chat + forum topic
(TELEGRAM_CHAT_ID / TELEGRAM_MESSAGE_THREAD_ID).
"""

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
import summarizer
import telegram_client

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def run_and_send(bot) -> None:
    text = await summarizer.build_summary()  # was: summarizer.build_summary()
    await telegram_client.send_summary(bot, text)


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /update — runs on demand, in whichever chat/topic it's called from
    is ignored; we always post to the configured CHAT_ID/THREAD_ID so this works
    even if someone runs /update from a different topic or DM."""
    await update.message.reply_text("Fetching competitor updates… this can take a minute.")
    try:
        await run_and_send(context.bot)
    except Exception as exc:
        logger.exception("Manual /update failed")
        await update.message.reply_text(f"Failed to fetch updates: {exc}")


async def scheduled_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for the recurring JobQueue job."""
    logger.info("Running scheduled competitor summary")
    try:
        await run_and_send(context.bot)
    except Exception:
        logger.exception("Scheduled summary failed")


def main() -> None:
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler(config.COMMAND_NAME, update_command))

    # Recurring job: first run 60s after boot, then every N days.
    interval_seconds = config.SCHEDULE_INTERVAL_DAYS * 24 * 60 * 60
    application.job_queue.run_repeating(
        scheduled_job,
        interval=interval_seconds,
        first=60,
        name="competitor_summary",
    )

    logger.info(
        "Bot starting. Posting to chat_id=%s thread_id=%s every %d day(s).",
        config.TELEGRAM_CHAT_ID,
        config.TELEGRAM_MESSAGE_THREAD_ID,
        config.SCHEDULE_INTERVAL_DAYS,
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
