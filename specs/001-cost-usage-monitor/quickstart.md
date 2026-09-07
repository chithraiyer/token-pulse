# Quickstart & Validation Guide: TokenPulse v1

Runnable scenarios that prove the feature works end to end. Commands assume repo root.
Details of shapes live in [`data-model.md`](./data-model.md) and
[`contracts/`](./contracts/); do not duplicate them here.

## Prerequisites

- Python 3.12 + [`uv`](https://docs.astral.sh/uv/)
- Node 20 + npm
- No API keys for the demo path

## One-command demo (Scenario A — the portfolio path)

```bash
scripts/demo.sh          # Windows: scripts/demo.ps1
```

Runs: `uv sync` → `uv run tokenpulse seed` → `uv run tokenpulse report` →
start API (`127.0.0.1:8000`) → `cd frontend && npm ci && npm run dev` → open the browser.

**Expected outcome (validates SC-001, FR-037, FR-003, FR-004):**

- Completes in < 5 minutes from a fresh clone with no environment variables set.
- Dashboard loads at `http://localhost:5173` showing 6 members across 2 teams, 90 days of
  daily history.
- A persistent "Synthetic demo data" banner is visible on every view.
- `GET /api/meta` → `{ "mode": "demo", "is_demo_data": true, ... }`.

## Scenario B — Trend dashboard (User Story 2)

Steps:

1. Open the Overview page. Confirm team-level cost and token trend lines for a default
   recent range.
2. Change the date range → all trends, totals, and period-over-period deltas update.
3. Click a member → per-member trends broken out by model.
4. Toggle to the member with the injected week-long spike → the spike days are visibly
   marked on the line.

**Checks (FR-013–FR-017, SC-002):**

- `GET /api/totals?start=&end=` → `team.cost_micros == Σ members[].cost_micros` exactly.
- `GET /api/trends?...` → points on flagged days carry `is_spike: true`; days with no
  record carry `missing: true` (not `value: 0`).

## Scenario C — Spike detection (User Story 3)

```bash
uv run tokenpulse report --start <first> --end <last> --json
```

**Checks (FR-018–FR-023, FR-020a, SC-003):**

- Every deliberately injected spike day appears in `GET /api/spikes`; no non-spike day
  does.
- Each flag has `baseline_avg_micros`, `actual_micros`, `deviation_ratio`,
  `excess_micros`, `severity ∈ {low,moderate,high,critical}`, `spike_multiple`,
  `rule_catalog_version`.
- Members with < 7 prior days in range appear in `insufficient_history`, not in `flags`.
- Re-run `report` → identical flag set (determinism).
- Edit `spike.multiple` in a copied `catalog-v2.yaml`, run with `--rule-catalog v2` →
  flags recompute against the new `T`.

## Scenario D — Recommendations (User Story 4)

Open the Recommendations page (or `GET /api/recommendations`).

**Checks (FR-024–FR-029a, SC-004):**

- All four rule ids fire on the demo dataset: `opus-on-lightweight`,
  `low-cache-utilisation`, `steady-high-volume`, `model-mix-shift`.
- Each item shows `rule_id`, `rule_catalog_version`, `trigger_data`, `threshold_data`,
  and `message`.
- `opus-on-lightweight`, `low-cache-utilisation`, `steady-high-volume` carry
  `estimated_savings_micros` + `savings_basis` (formula + assumptions).
- `model-mix-shift` has `estimated_savings_micros: null`.
- Re-generate → byte-identical recommendations (same dataset + catalog version).

## Scenario E — Determinism (SC-005, SC-010, FR-034)

```bash
uv run tokenpulse seed --reset && uv run tokenpulse report --check-determinism
uv run tokenpulse seed --reset            # same seed
# diff the two report JSON exports -> identical
```

Expected: `--check-determinism` exits `0`; a second `seed` with the same seed produces an
identical dataset.

## Scenario F — Privacy & retention (FR-031, FR-032, SC-007)

```bash
uv run sqlite3 tokenpulse.db '.schema'    # demo DB
uv run tokenpulse prune --dry-run --retention-days 30
```

**Checks:**

- No column or row anywhere holds prompt/completion/code text — only the metadata fields
  in `data-model.md`.
- `prune` reports rows older than the window; with `--retention-days 30` on 90 days of
  demo data it targets ~60 days of rows; real run hard-deletes them.

## Scenario G — Live mode smoke (User Story 5) — optional, needs credentials

```bash
export TOKENPULSE_ADMIN_API_KEY=sk-ant-admin-...
export TOKENPULSE_DB_KEY=...                     # SQLCipher passphrase
cp config/attribution.example.yaml config/attribution.yaml   # edit mappings
uv run tokenpulse ingest --start 2026-08-01 --end 2026-08-14
```

**Checks (FR-002, FR-005, FR-006–FR-008b, FR-032a, SC-006, SC-007a):**

- Switching to live required only the two env vars + `mode = live` in config — no code
  change.
- Live records populate the same dashboard/spike/recommendation views.
- Usage from an unmapped API key / workspace shows under the `__unattributed__` member.
- Re-running the same window creates no duplicates.
- If a page fails after retries, `IngestionRun.gap_days` lists the affected days and the
  command exits `1`; no fabricated usage.
- Inspecting `tokenpulse.db` without `TOKENPULSE_DB_KEY` yields no readable identifiers or
  values (encrypted at rest).
- `GET /api/report-runs/latest` includes a `reconciliation` array; any period over
  tolerance is surfaced in the dashboard header.

## Scenario H — Observability trace (SC-008, FR-036)

Pick any spike flag or recommendation shown in the UI; find its `report_run_id` /
`rule_id`. Grep the JSON logs (stderr capture) for that id → the log event lists the
contributing `usage_record` ids and the rule/catalog version. No log line contains
content or secrets.

## Automated coverage

| Layer | Location | Proves |
|-------|----------|--------|
| Unit (test-first) | `backend/tests/unit/core/` | money math, aggregation, spike + severity, each rule — normal/boundary/empty (Principle III) |
| Contract | `backend/tests/contract/` | `rest-api.openapi.yaml` response shapes; `anthropic_client` against fixtures |
| Integration | `backend/tests/integration/` | seed → report → API; determinism; retention; reconciliation warning |
| Frontend | `frontend/tests/` | trend chart spike markers, demo banner, empty/loading states |
