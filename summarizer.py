"""
Calls the OpenAI Responses API (with the built-in web_search tool) to get a
short bullet-point summary of recent news for each tracked competitor.
"""

import logging

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

client = OpenAI(api_key=config.OPENAI_API_KEY)

PROMPT_TEMPLATE = """\
    Search the web for news, product announcements, pricing changes, funding, \
    partnerships, or other notable updates about "{name}" ({hint}) from the \
    last {days} days.

    Respond in this exact structure:

    1. First line: a short 1-2 sentence summary in Russian of the overall \
    situation/trend for this competitor based on what you found.
    2. Then a blank line.
    3. Then 2-4 bullet points (each under 25 words, in English is fine), \
    using "- " as the bullet marker, each bullet followed by its source link \
    in parentheses.

    Example format:
    Компания выпустила новое приложение для трекинга сна и объявила о раунде \
    финансирования.

    - Launched new sleep-tracking app feature (https://example.com/article1)
    - Raised $20M Series B led by XYZ Capital (https://example.com/article2)

    No intro, no outro, no headers beyond this structure.

    If you find nothing notable in that timeframe, respond with exactly:
    Заметных обновлений за последние {days} дней не найдено.

    - No notable updates found in the last {days} days.
    """


def _summarize_one(competitor: dict) -> str:
    """Run one web-search-grounded summary call for a single competitor."""
    prompt = PROMPT_TEMPLATE.format(
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

    text = (response.output_text or "").strip()
    if not text:
        text = "- No notable updates found (empty response)."
    return text


def build_summary() -> str:
    """
    Build the full multi-competitor summary message.
    Returns Telegram-ready text (HTML formatting tags allowed, since the
    telegram client sends with parse_mode=HTML).
    """
    sections = []
    for competitor in config.COMPETITORS:
        name = competitor["name"]
        logger.info("Fetching update for %s", name)
        try:
            bullets = _summarize_one(competitor)
        except Exception as exc:  # keep going even if one competitor fails
            logger.exception("Failed to summarize %s", name)
            bullets = f"- (error fetching update: {exc})"

        sections.append(f"<b>{_escape_html(name)}</b>\n{_escape_html(bullets)}")

    header = f"<b>🏁 Competitor update</b> — last {config.LOOKBACK_DAYS} days\n"
    return header + "\n\n" + "\n\n".join(sections)


def _escape_html(text: str) -> str:
    """Minimal HTML escaping for Telegram parse_mode=HTML."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
