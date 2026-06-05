# TODO

## Phase 1 — Scaffold
- [x] Step 0 — Init repo: uv + pyproject.toml, folder structure
- [x] Step 1 — Minimal FastAPI app with one health route
- [x] Step 1.5 — Simple homepage at `/`
- [x] Step 2 — SQLite setup: connection + schema (games, players)
- [ ] Step 3 — Local dev conveniences: .env.example, run.sh, concise README

## Phase 2 — Auth (Entra ID, server-side Authorization Code Flow + session cookie)
Decision: in-app MSAL (works local + prod identically). Long-lived session cookie
(~14 days), http_only, same_site=lax, https_only in prod only.
- [x] Step 4.0 — Register app in Entra ID (done via az CLI: app "dip-tafelvoetbal-app", single-tenant, redirect http://localhost:8000/auth/callback, secret in local .env)
- [x] Step 4.1 — Config + secrets plumbing (pydantic-settings, extend .env.example)
- [x] Step 4.2 — Add SessionMiddleware (signed cookie, long-lived max_age)
- [x] Step 4.3 — Login + callback + logout routes (MSAL confidential client)
- [x] Step 4.4 — Auth dependency/guard; protect existing routes
- [x] Step 4.5 — Local-dev bypass (AUTH_ENABLED=false injects fake user) [folded into 4.4]
- [x] Step 4.6 — Show signed-in user + logout link in UI

## Phase 3 — Core features (one at a time)
- [ ] Step 5 — Leaderboard page
- [ ] Step 6 — New game → submit score → update stats + Elo
- [ ] Step 7 — Game history page
- [ ] Step 8 — Player detail page

## Phase 4 — Infra
- [ ] Step 8.5 — Docker (Dockerfile, .dockerignore) — deferred to here
- [ ] Step 9 — Terraform: Container App, ACR, Storage (Azure Files mount for SQLite)

