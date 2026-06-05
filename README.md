# tafelvoetbal-app

Foosball score tracker and leaderboard. Work in progress — see [TODO.md](TODO.md) for the build plan.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (package & environment manager)

## Setup

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env — set AUTH_ENABLED=false for local development
```

## Run

```bash
./run.sh
```

Or directly:

```bash
uv run uvicorn app.main:app --reload
```

App starts at `http://localhost:8000`.

## Auth

Authentication uses Entra ID (Azure AD) via MSAL (Authorization Code Flow).

- **Local dev:** set `AUTH_ENABLED=false` in `.env` — a fake dev user is injected, no login required
- **Production:** set `AUTH_ENABLED=true` — users must sign in with their Digital Power account

## Routes

| Path | Description |
|---|---|
| `GET /` | Homepage (protected) |
| `GET /auth/login` | Start Entra ID sign-in |
| `GET /auth/callback` | OAuth callback (handled by app) |
| `GET /auth/logout` | Sign out |
| `GET /health` | Liveness check — always public |
| `GET /docs` | API docs — only available when `AUTH_ENABLED=false` |

## Project structure

```
app/
  main.py             # FastAPI app, middleware, exception handlers
  config.py           # Settings loaded from .env (pydantic-settings)
  database.py         # SQLite connection + schema init
  auth.py             # MSAL confidential client helpers
  dependencies.py     # Auth guard (get_current_user)
  templates_engine.py # Shared Jinja2 instance
  routers/
    health.py         # GET /health
    pages.py          # GET / (homepage)
    auth.py           # /auth/login, /auth/callback, /auth/logout
  templates/          # Jinja2 HTML templates
  static/             # CSS / JS / images
data/                 # SQLite DB file (git-ignored, auto-created on startup)
.env.example          # Environment variable template — copy to .env
```

  routers/         # Route handlers (grouped by topic)
    health.py      # /health
  templates/       # Jinja2 HTML templates (used from Step 5)
  static/          # CSS / JS / images (used from Step 5)
pyproject.toml     # Dependencies + tooling config (uv, ruff)
TODO.md            # Step-by-step build plan
```
