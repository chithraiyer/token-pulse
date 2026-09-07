# Phase 0 Research: TokenPulse v1

All Technical Context unknowns resolved below. Each item: Decision / Rationale /
Alternatives considered.

## 1. Backend language & framework

**Decision**: Python 3.12 + FastAPI, with a pure `core/` package (no web/DB imports) for
the money path and Typer for the CLI.

**Rationale**: The spec's money path is numeric/statistical (rolling averages, ratios,
cost math, savings formulas) and demands test-first + determinism — Python + `pytest` +
`Decimal`/integer math is the shortest path to that discipline. FastAPI gives typed
Pydantic v2 request/response models that double as the frontend contract. The user's own
stack note offered "Python (FastAPI) or Node (Express) — pick whichever"; Python chosen.

**Alternatives considered**: Node/Express + TypeScript (one language across the stack,
but weaker story for exact decimal money math and concise statistical code);
full-stack Next.js (couples the pure money path to a web framework, fighting Principle
III/V isolation).

## 2. Frontend

**Decision**: React 18 + Vite + TypeScript, Recharts for trend lines and spike markers,
TanStack Query for data fetching, vitest + React Testing Library for component tests.

**Rationale**: Matches the spec's suggested stack. Recharts covers time-series lines with
annotated points (spike markers) with minimal code. Vite keeps `npm run dev` fast for the
< 5-minute quickstart.

**Alternatives considered**: Next.js (SSR unneeded for a local single-user dashboard);
D3 direct (more control, more code than the 4 simple views need); Chart.js (weaker React
integration than Recharts).

## 3. Storage & encryption at rest

**Decision**: SQLite via SQLAlchemy 2.x + Alembic. **Live mode**: whole-database
encryption with SQLCipher through the `sqlcipher3-binary` wheel, passphrase from
`TOKENPULSE_DB_KEY`. **Demo mode**: plain SQLite file (synthetic data only, per
Clarification Q3). Money stored as integer micro-USD (`cost_micros`), tokens as integers.

**Rationale**: SQLite meets the "zero setup" bar (SC-001) and the tiny scale (~15k rows).
Whole-DB SQLCipher keeps all SQL-side aggregation working (needed for determinism and
simplicity) while satisfying FR-032a; it is a single, well-understood mechanism covering
every column at once. Integer micro-USD removes floating-point drift from the money path
(Principle I/V) while still allowing `SUM()` in SQL.

**Alternatives considered**:
- *Application-layer column encryption* (SQLAlchemy `TypeDecorator` + AES-GCM via
  `cryptography`): portable with no native dependency, but blocks SQL aggregation of
  encrypted numeric columns, complicates determinism, and still leaks row counts. Kept as
  a documented fallback if a SQLCipher wheel is unavailable on a target platform.
- *Postgres*: violates zero-setup; noted as a v2 upgrade path.
- *OS-level disk encryption only* (BitLocker/FileVault/LUKS): not an application-level
  guarantee; Clarification Q3 requires the store itself to be encrypted.
- *Storing cost as REAL/float*: rejected — non-deterministic rounding on the money path.

## 4. Anthropic Usage & Cost Admin API (Live mode)

**Decision**: A thin httpx client hitting the organization usage and cost report
endpoints, authenticated with an **Admin API key** (`x-api-key`) plus the
`anthropic-version` header. Pull day-bucketed data (`bucket_width = 1d`) grouped by API
key / workspace and model, following the cursor pagination until exhausted. Persist both:
token buckets from the usage report and USD amounts from the cost report. Treat exact
field names as **verify-at-implementation** against current docs; encode the assumed
shape in `contracts/anthropic-admin-api.md` and back all client tests with recorded
fixtures.

**Rationale**: The spec (User Story 5, FR-002) fixes the source and the grouping. The API
buckets by API key / workspace, not by person — hence Clarification Q1's operator-supplied
`AttributionMap`. Storing the cost report amount as authoritative satisfies Principle I;
the pricing-table computation is used for reconciliation and for recommendation
repricing. Fixture-backed contract tests keep the build offline and deterministic and
insulate us from doc drift.

**Assumed request shape** (to confirm):
- `GET /v1/organizations/usage_report/messages` — params `starting_at`, `ending_at`,
  `bucket_width=1d`, `group_by[]=api_key_id`, `group_by[]=workspace_id`,
  `group_by[]=model`, `limit`, `page` (cursor).
- `GET /v1/organizations/cost_report` — params `starting_at`, `ending_at`,
  `bucket_width=1d`, `group_by[]=workspace_id`, `group_by[]=description` (line item),
  pagination as above.
- Headers: `x-api-key: <admin key>`, `anthropic-version: 2023-06-01`.
- Token fields expected per bucket: uncached input, cache-creation (write) input,
  cache-read input, output. Failure/partial pages → recorded as gaps (FR-006), not
  fabricated.

**Alternatives considered**: Claude Code local session logs as the live source (rejected
in Clarification Q1 — Option D — because it does not generalize to an org view and is not
the spec's named source); the SDK's admin helpers (thin wrapper over the same REST
endpoints; a direct httpx client keeps dependencies minimal and fixtures simple).

## 5. Rate limiting, pagination & partial failures (live ingestion)

**Decision**: Sequential paged requests with bounded exponential backoff + jitter on HTTP
429/5xx (cap ~5 retries), honoring `Retry-After` when present. A page that still fails
after retries marks the affected day range as an **ingestion gap** for that
group; the run reports gaps and exits non-zero, and no usage is fabricated (FR-006, US5
scenario 4). Ingestion is resumable: idempotent upsert keyed on
`(source, source_identity, model, date)` means re-running fills only the gaps.

**Rationale**: Closes the "Outstanding" integration item from `/speckit-clarify` with the
minimum needed for a daily batch tool at this scale. No streaming, no queue.

**Alternatives considered**: a job queue / scheduler (out of scope — daily manual or cron
invocation is enough for v1); failing the whole run on any page error (loses already-good
data and fights idempotent resume).

## 6. Determinism strategy (Principle V)

**Decision**: `core.reports.build_report(records, pricing_version, rule_catalog_version)`
is a pure function. Rules: (a) integer micro-USD arithmetic, single rounding point
(`ROUND_HALF_UP` to micro-USD) defined in `core/money.py`; (b) all iteration over
explicitly sorted keys `(member_id, date, model)`; (c) demo RNG seeded from config
(default fixed); (d) generation timestamp and host live only in `ReportRun` metadata and
are excluded from the determinism comparison; (e) JSON serialization with sorted keys and
fixed separators for the byte-identical check. Integration test: build twice, assert
equal (SC-005, SC-010).

**Rationale**: Directly enforces FR-034 and the constitution's byte-identical requirement.

**Alternatives considered**: floating-point with epsilon-tolerant comparison (fails
"byte-identical"); snapshot tests only (catch regressions but don't prove purity).

## 7. Cost reconciliation (Principle I)

**Decision**: In live mode, after ingestion, compute Σ(tokens × period pricing table) per
(period, workspace) and compare to Σ(cost-report amount). If the absolute delta exceeds
the greater of 1% or $1.00, emit a `ReconciliationWarning` carried into the report and
shown in the dashboard header; the authoritative stored `cost_micros` remains the
cost-report amount. Demo mode has no external truth, so reconciliation is skipped and the
pricing-table cost is authoritative.

**Rationale**: FR-009 + constitution "unreconciled deltas MUST be surfaced, not hidden".
Tolerance chosen to absorb rounding and minor rate-table lag without masking real drift.

**Alternatives considered**: hard-fail on any delta (brittle against pricing-table lag);
no reconciliation (violates Principle I).

## 8. Pricing table & rule catalog file formats

**Decision**: Pricing table = JSON at `backend/config/pricing/anthropic-<effective-date>.json`
validated by `contracts/pricing-table.schema.json`: `{ version, effective_start,
effective_end, currency: "USD", models: { "<model-id>": { input_per_mtok,
output_per_mtok, cache_write_per_mtok, cache_read_per_mtok } } }`. Rule catalog = YAML at
`backend/config/rules/catalog-v<n>.yaml` validated by `contracts/rule-catalog.schema.json`:
`{ version, rules: [ { id, title, enabled, window_days, thresholds: {...},
savings_formula } ] }`, seeded with the FR-029 defaults and the spike parameters
(FR-019/FR-020a) as tunable entries (FR-029a).

**Rationale**: JSON pricing tables are easy to diff, machine-load, and date-partition for
FR-012. YAML catalog is human-reviewable (Principle II "single, reviewable catalog").
Multiple dated pricing files let a past report reprice with period-correct rates.

**Alternatives considered**: a single pricing file with nested date ranges (harder to
diff and reason about which version applied); thresholds in code (fails FR-029a
tunability + version-bump-on-change).

## 9. Demo dataset generator

**Decision**: Deterministic generator seeded from config (fixed default). Produces 6
members across 2 teams, 90 days (configurable) of daily per-model usage with lognormal
day-to-day variance around per-member baselines, weekend dampening, and a realistic model
mix. Injects: (1) a week-long Opus-in-a-loop spike for one member; (2) a sharp 1–2 day
spike for another; (3) a team-level Sonnet→Opus model-mix shift spanning two consecutive
7-day windows. Also plants a low-cache-hit / high-input pattern and a steady high-volume
pattern so all four recommendation rules fire (US4 independent test).

**Rationale**: Covers every rolling-window rule and both spike shapes with enough
separation that the 2.5× rule flags exactly the injected days and nothing else (SC-003).

**Alternatives considered**: replaying an anonymized real export (privacy risk, not
reproducible, needs a real org); pure uniform random (won't reliably trigger or
cleanly separate the rules).

## 10. Spike baseline & severity (from spec, no open questions)

Confirmed from spec: baseline = raw trailing 7 calendar days of member daily
`cost_micros` (includes prior flagged days); flag when `actual ≥ T × baseline`,
`T` default 2.5, tunable; `< 7` prior days ⇒ "insufficient history", never flagged.
Severity = four bands on `r = actual/baseline` vs `T` (Low `[T,2T)`, Moderate `[2T,3T)`,
High `[3T,5T)`, Critical `≥5T`) with dollar-excess floors ($50 High, $200 Critical)
demoting a band until satisfied. Bands and floors are rule-catalog params.

## 11. Observability

**Decision**: `structlog` JSON logs. A processor drops any key not on an allow-list and
redacts values matching secret patterns, so no prompt/completion content or API keys can
be logged (FR-036). Each spike flag and recommendation logs an event carrying the
contributing `usage_record` ids, the rule id + catalog version, and the `report_run` id,
enabling the SC-008 "trace in under 2 minutes" check.

**Alternatives considered**: stdlib `logging` with a formatter (less structured, easier to
leak fields); OpenTelemetry traces (overkill for a local batch tool).

## 12. Packaging, deployment & quickstart

**Decision**: `uv` for backend deps/venv; `npm` for frontend. A `scripts/demo.{sh,ps1}`
one-command path: create venv, `tokenpulse seed` (demo data), start `uvicorn`, start Vite
dev server, open the browser. Optional `docker-compose.yml` for a container path. Target
< 5 minutes, zero API keys (SC-001, FR-037). README embeds the architecture diagram from
`docs/architecture.md`, a "how I used AI to build this" section, and screenshots/GIF
(SC-009).

**Alternatives considered**: Docker-only (adds a Docker prerequisite that can blow the
5-minute budget on a cold pull); a full-stack framework single deploy (couples money path
to web runtime).

## Resolved Outstanding items from `/speckit-clarify`

- **Dashboard latency target** → set to < 200 ms p95 locally on the reference dataset
  (Technical Context / Performance Goals).
- **Loading / empty states** → each view specifies empty ("insufficient history",
  "no data in range", ingestion-gap notice) and loading (skeleton) states; captured in
  `contracts/rest-api.openapi.yaml` response examples and the frontend component list.
- **Admin API rate-limit / pagination / partial-failure policy** → Research §5.
