import logging
import asyncio
from datetime import datetime, timezone, timedelta
import os
from openai import OpenAI
from telethon import TelegramClient
from telethon.sessions import StringSession

import config

logger = logging.getLogger(__name__)
client = OpenAI(api_key=config.OPENAI_API_KEY)

COMPETITOR_PROMPT = """\
        Search the web for news, product announcements, pricing changes, funding, \
        partnerships, or other notable updates about "{name}" ({hint}) from the \
        last {days} days.

        Respond in this exact structure:

        1. First line: a short 1-2 sentence summary in Russian of the overall \
        situation/trend for this competitor based on what you found.
        2. Then a blank line.
        3. Then 2-4 bullet points in English, using "- " as the bullet marker, \
        each bullet followed by its source link in parentheses like (https://...).

        No intro, no outro, no headers. If nothing notable found:
        Заметных обновлений за последние {days} дней не найдено.
        """

CHANNEL_PROMPT = """\
    Below are messages from the Telegram channel @{channel} from the last {days} days.
    Write a short summary in Russian (3-5 sentences) of the main topics, trends, \
    and key takeaways discussed only about medicine, health, aging. Be concise and informative. No bullet points, \
    just flowing text.

    Messages:
    {messages}
    """


async def _fetch_channel_messages_async(tg: TelegramClient, channel: str) -> list[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
    texts = []
    async for message in tg.iter_messages(channel, limit=500):
        if message.date < cutoff:
            break
        if message.text and message.text.strip():
            texts.append(message.text.strip())
    return texts


async def _summarize_all_channels_async() -> dict[str, str]:
    """Open one Telethon session, fetch all channels, return {channel: summary}."""
    session = StringSession(os.environ.get("TELETHON_SESSION_STRING", ""))
    results = {}

    async with TelegramClient(session, config.TELETHON_API_ID, config.TELETHON_API_HASH) as tg:
        for channel in config.TG_CHANNELS:
            logger.info("Fetching messages from @%s", channel)
            try:
                messages = await _fetch_channel_messages_async(tg, channel)
                if not messages:
                    results[channel] = f"Сообщений за последние {config.LOOKBACK_DAYS} дней не найдено."
                    continue

                sampled = messages[:200]
                messages_blob = "\n\n".join(
                    f"[{i+1}] {m[:500]}" for i, m in enumerate(reversed(sampled))
                )
                prompt = CHANNEL_PROMPT.format(
                    channel=channel,
                    days=config.LOOKBACK_DAYS,
                    messages=messages_blob,
                )
                response = client.responses.create(
                    model=config.OPENAI_MODEL,
                    reasoning={"effort": "low"},
                    input=prompt,
                )
                results[channel] = (response.output_text or "").strip()
            except Exception as exc:
                logger.exception("Failed to summarize channel @%s", channel)
                results[channel] = f"(ошибка: {exc})"

    return results


def summarize_competitor(competitor: dict) -> str:
    prompt = COMPETITOR_PROMPT.format(
        name=competitor["name"],
        hint=competitor["query_hint"],
        days=config.LOOKBACK_DAYS,
    )
    response = client.responses.create(
        model=config.OPENAI_MODEL,
        reasoning={"effort": "low"},
        tools=[{"type": "web_search", "search_context_size": "low"}],
        input=prompt,
    )
    return (response.output_text or "").strip()


async def build_summary() -> str:
    sections = []

    # --- TG channels ---
    sections.append("<b>📱 Telegram-каналы</b>")
    channel_summaries = await _summarize_all_channels_async()
    for channel, summary in channel_summaries.items():
        sections.append(f"<b>@{_escape_html(channel)}</b>\n{_escape_html(summary)}")

    # --- Competitors ---
    sections.append("<b>🏁 Конкуренты</b>")
    for competitor in config.COMPETITORS:
        name = competitor["name"]
        logger.info("Fetching update for %s", name)
        try:
            text = summarize_competitor(competitor)
        except Exception as exc:
            logger.exception("Failed to summarize %s", name)
            text = f"(error: {exc})"
        sections.append(f"<b>{_escape_html(name)}</b>\n{_escape_html(text)}")

    header = f"<b>📊 Дайджест</b> — последние {config.LOOKBACK_DAYS} дней\n"
    return header + "\n\n" + "\n\n".join(sections)


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")