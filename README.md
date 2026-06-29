# Competitor Update Bot

Telegram bot that posts a short "what's new with our competitors" summary
into a specific topic of a supergroup — either every 2 weeks automatically,
or on demand via `/update`. Uses OpenAI's Responses API with the built-in
web search tool, so no scraping or RSS feeds needed.

Tracks (edit in `config.py`): Peloton, Decathlon health/coaching, Whoop,
Welltory, Bevel.

## How it works

- One long-running Python process (`bot.py`) does two things at once:
  - Listens for the `/update` command (Telegram long-polling) → runs the
    summary immediately and posts it.
  - Runs a background job every `SCHEDULE_INTERVAL_DAYS` (default 14) that
    does the same thing automatically.
- For each competitor, it calls OpenAI's Responses API with the
  `web_search` tool and asks for recent news in the last `LOOKBACK_DAYS`
  days, as 2-4 short bullets.
- The combined summary is sent to your supergroup, into a specific forum
  topic if you set one.

## 1. Make the bot an admin in the supergroup

Bots generally need admin rights (or explicit "Send Messages" permission)
to post into forum topics. In Telegram:

1. Open **Архитектор здоровья 3.0** → group settings → Administrators
2. Add your bot, give it at least "Send Messages" (you don't need to grant
   it other admin powers like deleting messages or banning users)

## 2. Find your forum topic's `message_thread_id`

Your group has topics (`is_forum: true`). To post into a specific topic
instead of "General", you need that topic's numeric ID:

**Easiest way — Telegram Web:**
1. Open the group in [web.telegram.org](https://web.telegram.org)
2. Click into the specific topic (e.g. "Competitors")
3. Look at the URL: `.../#-1004296790192_1234` → `1234` is your
   `message_thread_id`

**Alternative — via the Bot API directly:**
1. Send any message in that topic (as a human)
2. Call `https://api.telegram.org/bot<TOKEN>/getUpdates` in your browser
   or with `curl`
3. Find your message in the JSON response — it has a
   `"message_thread_id": <number>` field at the same level as `"chat"`

Put that number in `TELEGRAM_MESSAGE_THREAD_ID`. Leave it blank to post
to "General" instead.

## 3. Configure environment variables

Copy `.env.example` to `.env` for local testing, or set these directly as
Railway variables (Settings → Variables) for deployment:

| Variable | Required | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | from @BotFather |
| `TELEGRAM_CHAT_ID` | yes | `-1004296790192` for your group |
| `TELEGRAM_MESSAGE_THREAD_ID` | no | the topic ID from step 2; blank = General |
| `OPENAI_API_KEY` | yes | your OpenAI key |
| `OPENAI_MODEL` | no | defaults to `gpt-5.5` |
| `SCHEDULE_INTERVAL_DAYS` | no | defaults to `14` (every 2 weeks) |
| `LOOKBACK_DAYS` | no | defaults to `14`; how far back to search per run |

## 4. Run locally (optional, before deploying)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export $(grep -v '^#' .env | xargs)   # or use python-dotenv if you prefer
python bot.py
```

Then in your Telegram group's topic, type `/update` — within ~10-30
seconds (5 competitors × one web-search call each) you should see a
summary posted.

## 5. Deploy to Railway

1. Push this folder to a GitHub repo (or use Railway's CLI to deploy
   directly from disk — `railway up`)
2. In Railway: **New Project → Deploy from GitHub repo**
3. Add the environment variables from step 3 in **Variables**
4. Railway will detect `railway.json` / `Procfile` and run
   `python bot.py` as a **worker** (no public HTTP port needed — this bot
   uses polling, not webhooks, so there's nothing to expose)
5. Deploy. Check the **Logs** tab — you should see:
   ```
   Bot starting. Posting to chat_id=-1004296790192 thread_id=1234 every 14 day(s).
   ```

That's it — the process stays alive, polls Telegram for `/update`, and
fires the biweekly job in the background.

### Note on the schedule's exact timing

`SCHEDULE_INTERVAL_DAYS` is a simple "every N days since the process
started" timer, not a calendar-locked day/time (e.g. "every other
Monday at 9am"). This is the simplest reliable option for a
long-running worker process, but it means:

- If Railway restarts your service (deploys, crashes, etc.), the 14-day
  countdown restarts from that moment.
- There's no guaranteed day-of-week.

If you want it pinned to an exact day/time (e.g. "every other Monday
9:00 CET") regardless of restarts, the cleaner approach is **Railway
Cron Schedule** jobs instead of an in-process timer:
- Split `run_and_send` into its own one-shot script (`run_once.py`)
- Deploy *that* as a separate Railway service with a **Cron Schedule**
  (e.g. `0 9 */14 * *` — Railway cron syntax doesn't support "every 2
  weeks" natively, so in practice people either run it weekly and skip
  odd weeks in code, or just accept the simple in-process timer above)
- Keep `bot.py` (the `/update` listener) as a second, separate Railway
  service running continuously

Happy to build that split version if you want the precise schedule —
the current setup trades a small amount of timing precision for a much
simpler one-process deployment.

## Customizing

- **Add/remove competitors**: edit the `COMPETITORS` list in `config.py`
- **Change summary depth/style**: edit `PROMPT_TEMPLATE` in
  `summarizer.py`
- **Change lookback window**: `LOOKBACK_DAYS` env var
- **Change schedule frequency**: `SCHEDULE_INTERVAL_DAYS` env var

## Cost note

Each run makes one Responses API call per competitor (5 calls per run,
~26 calls/year at the biweekly default + however many manual `/update`s
you trigger). Each call includes a web search, which OpenAI bills
per-call in addition to token usage — check current pricing on
OpenAI's pricing page before relying on this at scale.
