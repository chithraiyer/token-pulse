#!/usr/bin/env bash
# TokenPulse zero-key demo: synthetic data + API + dashboard. No API keys required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> [1/4] Backend deps (uv sync)"
(cd backend && uv sync --extra dev)

echo "==> [2/4] Seed synthetic dataset (demo mode, no keys)"
(cd backend && uv run tokenpulse --config tokenpulse.demo.toml seed --reset)
# TODO(US3 T067): add `uv run tokenpulse report` here once the report command lands.

echo "==> [3/4] Start API on http://127.0.0.1:8000"
(cd backend && uv run tokenpulse --config tokenpulse.demo.toml serve --host 127.0.0.1 --port 8000) &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

echo "==> [4/4] Start dashboard on http://localhost:5173"
if command -v npm >/dev/null 2>&1; then
  (cd frontend && npm ci && npm run dev)
else
  echo "npm not found — install Node 20+ to run the dashboard. API is up at :8000."
  wait $API_PID
fi
