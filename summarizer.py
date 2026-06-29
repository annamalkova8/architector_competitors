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

Respond with 2-4 short bullet points (each bullet under 25 words), in plain \
text using "- " as the bullet marker. No intro, no outro, no headers.

If you find nothing notable in that timeframe, respond with exactly:
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
        tools=[{"type": "web_search"}],
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
