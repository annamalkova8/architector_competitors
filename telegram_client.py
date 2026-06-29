"""
Thin wrapper around python-telegram-bot's send_message, with support for
posting into a specific forum topic (message_thread_id) inside a supergroup.
"""

import logging

from telegram import Bot
from telegram.constants import ParseMode

import config

logger = logging.getLogger(__name__)

MAX_MESSAGE_LEN = 4000  # Telegram's real limit is 4096; leave headroom


async def send_summary(bot: Bot, text: str) -> None:
    """Send (and chunk, if needed) a summary message to the configured chat/topic."""
    chunks = _chunk_text(text, MAX_MESSAGE_LEN)
    for chunk in chunks:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            message_thread_id=config.TELEGRAM_MESSAGE_THREAD_ID,
            text=chunk,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    logger.info(
        "Sent summary to chat_id=%s thread_id=%s (%d chunk(s))",
        config.TELEGRAM_CHAT_ID,
        config.TELEGRAM_MESSAGE_THREAD_ID,
        len(chunks),
    )


def _chunk_text(text: str, max_len: int) -> list[str]:
    """Split text into chunks no longer than max_len, breaking on blank lines."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > max_len:
            if current:
                chunks.append(current)
            current = para
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
