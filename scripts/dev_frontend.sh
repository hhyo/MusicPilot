#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/frontend"

if command -v pnpm >/dev/null 2>&1; then
  PNPM_BIN="pnpm"
else
  PNPM_BIN="$(npm prefix -g)/bin/pnpm"
fi

if [ ! -x "$PNPM_BIN" ]; then
  echo "pnpm not found. Please install pnpm before running frontend scripts." >&2
  exit 1
fi

exec "$PNPM_BIN" --config.manage-package-manager-versions=false dev --host 0.0.0.0
