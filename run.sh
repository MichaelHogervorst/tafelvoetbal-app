#!/bin/bash
set -e

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example — review it before running in production."
fi

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
