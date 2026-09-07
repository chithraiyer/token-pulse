# Contract: TokenPulse CLI (`tokenpulse`)

Typer-based CLI. Exit code `0` on success, `1` on any error, `2` on invalid arguments.
All output that is not a prompt goes to stdout as either a human table or, with
`--json`, a single JSON object. Structured logs go to stderr.

## Global options

| Option | Default | Notes |
|--------|---------|-------|
| `--config PATH` | `./tokenpulse.toml` | mode, retention, threshold overrides, DB path |
| `--db PATH` | from config or `./tokenpulse.db` | SQLite/SQLCipher file |
| `--json` | off | machine-readable output |
| `--log-level` | `info` | `debug\|info\|warning\|error` |

Environment: `TOKENPULSE_ADMIN_API_KEY` (live), `TOKENPULSE_DB_KEY` (live, SQLCipher
passphrase). Never passed as flags; never logged.

## Commands

### `tokenpulse seed`

Generate the synthetic demo dataset and store it (mode is forced to `demo`).

| Option | Default | Notes |
|--------|---------|-------|
| `--seed INT` | `20260907` | fixed default ⇒ reproducible dataset (SC-010) |
| `--days INT` | `90` | days of history |
| `--members INT` | `6` | 5–8 allowed |
| `--reset` | off | drop and recreate demo rows first |

Outcome: idempotent for a given `(seed, days, members)`; re-running without `--reset`
is a no-op. Prints member/day/spike counts.

### `tokenpulse ingest`

Pull live usage + cost from the Anthropic Admin API into the store (mode `live`).

| Option | Default | Notes |
|--------|---------|-------|
| `--start DATE` | required | UTC day, inclusive |
| `--end DATE` | yesterday | UTC day, inclusive |
| `--attribution PATH` | `./config/attribution.yaml` | source_identity → member map (FR-008a) |

Behaviour: paginates both reports; bounded backoff on 429/5xx; unresolved
`source_identity` → `__unattributed__` (FR-008b); pages that fail after retries become
`gap_days` and status `partial`, never fabricated (FR-006). Idempotent upsert on
`(source, source_identity, model, date)` (FR-007). Requires both env vars; exits `1`
with a clear message if missing. On success, automatically runs `report`.

### `tokenpulse report`

Recompute spike flags + recommendations + reconciliation for a window; write a new
`ReportRun`. Pure over stored records + pinned config versions.

| Option | Default | Notes |
|--------|---------|-------|
| `--start DATE` / `--end DATE` | full stored range | analysis window |
| `--pricing-version STR` | auto by date | override for what-if recomputation |
| `--rule-catalog STR` | latest bundled | e.g. `v1` |
| `--check-determinism` | off | build twice, assert byte-identical, exit `1` on mismatch (SC-005) |

Prints counts by severity, recommendation count, and any `ReconciliationWarning`.

### `tokenpulse prune`

Delete `UsageRecord` rows older than the retention window (default 90 days, FR-032);
hard delete. `--dry-run` prints what would be removed. `--retention-days INT` overrides
config for this run.

### `tokenpulse serve`

Start the FastAPI app (`uvicorn`) on `--host`/`--port` (default `127.0.0.1:8000`).
Convenience wrapper; `uvicorn tokenpulse.api.app:app` also works.

## Exit / error contract

| Situation | Exit | Output |
|-----------|------|--------|
| Success | 0 | result table or `{ "ok": true, ... }` |
| Live env vars missing | 1 | `error: TOKENPULSE_ADMIN_API_KEY and TOKENPULSE_DB_KEY are required for live mode` |
| Partial ingest (gaps) | 1 | run summary incl. `gap_days`; `status: partial` |
| Determinism mismatch | 1 | first differing path in the report JSON |
| Bad arguments | 2 | Typer usage message |
