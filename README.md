# QuickPoll — Backend

This is the API and WebSocket server behind QuickPoll. It handles creating polls, casting votes, closing polls, and pushing live results to anyone watching — no page refresh needed.

The problem it solves is simple: normal polls make you refresh to see results. This one pushes updates the instant a vote comes in, so a room full of people watching the same poll all see the bars move at the same time.

No login required. Anyone can create a poll and get a shareable link. The creator also gets a private admin link to close voting whenever they want.

## Who it's for

Anyone who needs a quick, no-signup poll — team standups, live audience Q&A, "pineapple on pizza yes or no" arguments. Built to be frictionless. If someone has to create an account just to vote, they've already left.

## Why it exists

I wanted to get real hands-on experience with WebSockets instead of just reading about them. Polling apps are a good fit for that — you actually need real-time updates for the thing to feel right, not just as a nice-to-have.

## Tech stack

- **Django** + **Django REST Framework** — the API layer
- **Django Channels** — WebSocket support, running on ASGI instead of the usual WSGI
- **Redis** (via Upstash) — the channel layer that lets votes get broadcast out to everyone connected
- **daphne** — ASGI server, since `runserver` doesn't handle WebSockets
- **SQLite** locally, **PostgreSQL** in production

## Quick Start

```bash
git clone <quickpoll-backend>
cd quickpoll-backend
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and fill in the values. You'll need a `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

And a `REDIS_URL`. Get one free from [Upstash](https://upstash.com) — grab the connection string from your dashboard and make sure it starts with `rediss://` (the extra "s" means SSL, which Upstash requires).

Then:

```bash
python manage.py migrate
daphne quickpoll_backend.asgi:application
```

Server runs at `http://localhost:8000`. Use `daphne`, not `runserver` — this project needs ASGI to handle WebSocket connections, and `runserver` only speaks regular HTTP.

## How the real-time part works

When someone opens a poll, their browser opens a WebSocket connection and joins a "room" for that specific poll (technically a Channels group). When a vote comes in through the normal REST endpoint, the server saves it to the database, then broadcasts the updated results to everyone in that poll's room through Redis. Nobody has to ask for new data — it just arrives.

## Identity, without accounts

There's no user model here on purpose. Poll creators get a random `admin_token` at creation time, shown once, used to close their poll later. Voters pick a display name and get an anonymous ID stored in their browser, which stops them from voting twice on the same poll. It's not bulletproof — clearing your browser storage would let you vote again — but it's enough for what this is.

## Known limitations

- **No real vote-fraud prevention.** Anonymous voter IDs live in localStorage. Clear it, vote again. Fine for casual polls, not fine for anything that actually matters.
- **No poll history or dashboard.** Once you have the link, that's your only way back to a poll. Lose the link, lose access (unless you saved the admin token locally).
- **Free-tier Redis quirks.** Upstash needs `RedisPubSubChannelLayer` instead of the default `RedisChannelLayer`, plus `?protocol=2` on the connection string, or the WebSocket connection just hangs. Already handled in this codebase, but worth knowing if you're setting up your own Redis elsewhere.
- **No rate limiting yet.** Nothing stops someone from spamming poll creation right now.

## License

MIT. Do what you want with it.