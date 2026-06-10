# TODO

## Phase 1 — Scaffold
- [x] Step 0 — Init repo: uv + pyproject.toml, folder structure
- [x] Step 1 — Minimal FastAPI app with one health route
- [x] Step 1.5 — Simple homepage at `/`
- [x] Step 2 — SQLite setup: connection + schema (games, players)
- [x] Step 3 — Local dev conveniences: .env.example, run.sh, concise README

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
- [x] Step 5 — Leaderboard page
- [x] Step 6 — New game → submit score → update stats + Elo
- [x] Step 6.1 — Track real points per team (score inputs on new game form; store actual scores instead of 1/0)
- [x] Step 7 — Game history page (`/games`; table with date, teams, score, winner highlighted)
- [x] Step 8 — Player detail page (`/player/{name}`; stats cards + personal game history with W/L)
- [x] Step 9 — Dual rating system: TrueSkill alongside Elo; support 1v1, 2v1 and 2v2 game formats

## Phase 4 — Infra

### Step 10 — Docker
- [x] Step 10.1 — Pick base image (`python:3.13-slim` or uv official image); decide uv-in-container vs export to `requirements.txt`
- [x] Step 10.2 — Write `Dockerfile`: install deps, copy app, `mkdir -p /app/data`, declare `VOLUME /app/data` (mount point only — no storage backend chosen here), set uvicorn `CMD`
- [x] Step 10.3 — Write `.dockerignore`: exclude `.env`, `data/`, `.venv`, `.git`, `__pycache__`
- [x] Step 10.4 — Make `DB_PATH` configurable via env var (`db_path` in pydantic-settings) so storage location is pure config, never hardcoded
- [x] Step 10.5 — Add `docker-compose.yml` for local dev: bind mount `./data:/app/data` so the DB survives container restarts without any Azure involvement
- [x] Step 10.6 — Ensure all config is passed via env vars at runtime; no `.env` baked into the image; verify pydantic-settings picks them up without a file present
- [ ] Step 10.7 — Build + smoke-test locally: run with compose mount, verify `.db` survives a container restart, hit `/health`

### Step 11 — Terraform (production mount lives here, not in the Dockerfile)

Decision pending: where does the SQLite `.db` live in production? Two competing
approaches below — pick ONE before implementing. The core difference is the host:
"db on the server" needs a *persistent local disk*, which ACA Consumption does not
provide (its disk is ephemeral → wiped on every redeploy).

#### Step 11.a — Local persistent disk ("keep the db on the server")
Colleague's advice: simpler and faster (no network file share in the I/O path).
Requires a host that actually has a persistent disk — so this changes the hosting
choice. Two ways to realise it:

- [ ] Step 11.a.1 — Decide host: **(a)** Azure VM with a persistent data disk, or
      **(b)** ACA on the **Dedicated** workload profile with a managed-disk volume
      (Consumption plan is NOT an option here — ephemeral disk = data loss on redeploy)
- [ ] Step 11.a.2 — Provision the host + persistent disk in Terraform (VM + data disk,
      or ACA Environment with Dedicated profile + storage volume)
- [ ] Step 11.a.3 — Mount the persistent disk at `/app/data`; set `DB_PATH=/app/data/tafelvoetbal.db`
- [ ] Step 11.a.4 — ACR: registry + push pipeline
- [ ] Step 11.a.5 — Deploy the container/app to the host; pin a single instance (single SQLite writer)
- [ ] Step 11.a.6 — Redeploy strategy: update the image only; verify the disk is NOT
      re-created/wiped on redeploy (the decisive risk to test for this approach)
- [ ] Step 11.a.7 — Backup plan: the disk is the single source of truth — schedule
      disk snapshots / DB file backups (no separate durable store otherwise)

Trade-offs: + lowest latency, simplest mental model, fewer moving parts.
            − tied to one host; persistence depends on never recreating the disk;
              backups are on you; VM means more to manage, Dedicated means more cost.

#### Step 11.b — Azure File Share mount (current plan)
Decouples storage from compute; storage survives any container/host lifecycle.

- [ ] Step 11.b.1 — ACR: registry + push pipeline (image is the only thing that changes on redeploy)
- [ ] Step 11.b.2 — Storage Account + File Share (`tafelvoetbal-data`); this is where the `.db` lives permanently
- [ ] Step 11.b.3 — Container App Environment: register the File Share as ACA storage
- [ ] Step 11.b.4 — Container App: mount the share at `/app/data`, set `DB_PATH=/app/data/tafelvoetbal.db`,
      pin `min=max=1` replica (single SQLite writer), inject all env vars/secrets from Key Vault or ACA secrets
- [ ] Step 11.b.5 — Wire redeploy pipeline: only the image tag is updated; storage is never touched → data safe across deploys

Trade-offs: + runs on cheap ACA Consumption; storage fully decoupled from compute;
              survives redeploys/crashes/scale-to-zero by design; standard pattern.
            − small per-op SMB latency (negligible at this scale); SMB write-locking
              caveat for SQLite (mitigated by single replica + WAL).

