import logging
from datetime import datetime, timezone, timedelta

from openai import OpenAI
from telethon.sync import TelegramClient

import config

logger = logging.getLogger(__name__)
client = OpenAI(api_key=config.OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

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

Example:
Компания выпустила новое приложение для трекинга сна и объявила о раунде финансирования.

- Launched new sleep-tracking app feature (https://example.com/article1)
- Raised $20M Series B led by XYZ Capital (https://example.com/article2)

No intro, no outro, no headers. If nothing notable found:
Заметных обновлений за последние {days} дней не найдено.
"""

CHANNEL_PROMPT = """\
Below are messages from the Telegram channel @{channel} from the last {days} days.
Write a short summary in Russian (3-5 sentences) of the main topics, trends, \
and key takeaways discussed. Be concise and informative. No bullet points, \
just flowing text.

Messages:
{messages}
"""


# ---------------------------------------------------------------------------
# Telegram channel reading (Telethon)
# ---------------------------------------------------------------------------

def fetch_channel_messages(channel: str) -> list[str]:
    """Fetch messages from a public TG channel for the last LOOKBACK_DAYS."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
    texts = []

    with TelegramClient(
        config.TELETHON_SESSION,
        config.TELETHON_API_ID,
        config.TELETHON_API_HASH,
    ) as tg:
        for message in tg.iter_messages(channel, limit=500):
            if message.date < cutoff:
                break
            if message.text and message.text.strip():
                texts.append(message.text.strip())

    return texts


def summarize_channel(channel: str) -> str:
    """Fetch messages and summarize with OpenAI (no web search needed)."""
    messages = fetch_channel_messages(channel)

    if not messages:
        return "Сообщений за последние {} дней не найдено.".format(config.LOOKBACK_DAYS)

    # Keep under token limit — take the most recent 200 messages, trim each
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
    return (response.output_text or "").strip()


# ---------------------------------------------------------------------------
# Competitor web search (existing logic, updated prompt)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Build the full message
# ---------------------------------------------------------------------------

def build_summary() -> str:
    sections = []

    # --- TG channels section ---
    sections.append("<b>📱 Telegram-каналы</b>")
    for channel in config.TG_CHANNELS:
        logger.info("Summarizing TG channel @%s", channel)
        try:
            summary = summarize_channel(channel)
        except Exception as exc:
            logger.exception("Failed to summarize channel @%s", channel)
            summary = f"(ошибка: {exc})"
        sections.append(f"<b>@{_escape_html(channel)}</b>\n{_escape_html(summary)}")

    # --- Competitors section ---
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