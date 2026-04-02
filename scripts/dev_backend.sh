#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/backend"

if [ -x ".venv/bin/uvicorn" ]; then
  exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
fi

exec python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

