# ── Stage 1: dependency installer ────────────────────────────────────────────
# Use the official uv image to resolve and install dependencies into a venv.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Install dependencies first (separate layer — only rebuilds when deps change).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the source and install the project itself.
COPY app/ ./app/
RUN uv sync --frozen --no-dev

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy the installed virtualenv from the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Copy application source.
COPY --from=builder /app/app ./app/

# Ensure the data directory exists as a mount point for the SQLite database.
# The actual storage backend (local bind mount or Azure File Share) is attached
# at runtime — the image itself is storage-agnostic.
RUN mkdir -p /app/data
VOLUME /app/data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
