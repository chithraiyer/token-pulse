# Implementation Plan: TokenPulse — Claude Code Cost & Usage Monitor (v1)

**Branch**: `001-cost-usage-monitor` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-cost-usage-monitor/spec.md`

## Summary

TokenPulse ingests daily Claude Code token usage (per member, per model), stores only
non-content metadata, computes cost from versioned pricing tables, flags per-member
spending spikes with a rolling-average rule, and emits explainable rule-based
optimization recommendations. It ships two data sources — a **Demo** synthetic
generator that runs with zero API keys, and a **Live** Anthropic Usage & Cost Admin API
client — and a React dashboard for team- and member-level trends. A written v2 roadmap
is included but not built.

**Technical approach**: a small Python (FastAPI) backend split into a pure, test-first
`core` package (pricing, aggregation, spike detection, recommendation rules, report
assembly) and thin I/O layers (ingestion, persistence, HTTP API, CLI); a React + Vite +
Recharts frontend; SQLite storage (SQLCipher-encrypted in live mode). All money-path
output is a deterministic pure function of input records plus pinned pricing-table and
rule-catalog versions.

## Technical Context

**Language/Version**: Backend Python 3.12; Frontend TypeScript 5.x on Node 20

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, httpx, Typer
(CLI), structlog; pytest + respx + coverage. Frontend: React 18, Vite, Recharts,
TanStack Query, vitest + React Testing Library. Live-mode encryption: `sqlcipher3-binary`.

**Storage**: SQLite via SQLAlchemy. Live mode: SQLCipher whole-database encryption at
rest, passphrase from `TOKENPULSE_DB_KEY`. Demo mode: plain SQLite file. Monetary values
stored as integer micro-USD (`*_micros`); token counts as integers.

**Testing**: Backend pytest (`tests/unit`, `tests/contract`, `tests/integration`),
test-first for everything under `core/`. Frontend vitest + RTL. One determinism
integration test (generate report twice, assert byte-identical).

**Target Platform**: Local developer machine (macOS / Linux / Windows) + modern browser.
No hosted deployment required for v1 acceptance.

**Project Type**: Web application (React frontend + FastAPI backend + CLI) in a single
repository.

**Performance Goals**: Dashboard API < 200 ms p95 locally on the reference dataset;
`demo seed` + `ingest` < 30 s; full README quickstart < 5 minutes.

**Constraints**: Deterministic report output (byte-identical for identical inputs +
config versions); demo mode fully offline with zero secrets; exact money math (integer
micro-USD, no floats on the money path); no prompt/completion/code content persisted;
UTC day bucketing.

**Scale/Scope**: 3–15 members, ~90 days history, ~5 models, 2 sources ⇒ ~15k usage rows.
4 dashboard views (team overview, member detail, spikes, recommendations); 1 spike rule;
4 recommendation rules.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution v1.0.0. Each principle is mapped to concrete design commitments; two
deviations are tracked in **Complexity Tracking**.

| Principle | Status | How this plan satisfies it |
|-----------|--------|----------------------------|
| **I. Accuracy Over Estimation** | PASS | Live cost stored from the Cost Admin API (authoritative); demo cost from a bundled `pricing/anthropic-<date>.json` (versioned + dated). Every `UsageRecord` carries its `pricing_table_version`. Reports recompute past periods with period-effective rates (FR-012). Live mode runs a reconciliation pass (Σ tokens×pricing vs Σ Cost API amount); deltas over tolerance surface as a `ReconciliationWarning`, never hidden. All projected/hypothetical dollars (recommendation savings) are labeled estimates with their basis (FR-011). |
| **II. Explainable, Rule-Based Recommendations** | PASS | Single versioned `rules/catalog-v<n>.yaml`; each rule has a stable id, condition, threshold params, and a documented savings formula. Recommendation output records rule id, catalog version, observed trigger data, suggested change, threshold in effect, and the savings calculation (FR-026, FR-029a). Pure evaluator ⇒ reproducible (FR-028). Rule (d) emits no dollar figure. |
| **III. Test-First for Money-Path Logic (NON-NEGOTIABLE)** | PASS | All cost, aggregation, spike-detection, severity, and rule-evaluation code lives in `backend/src/tokenpulse/core/` with **no I/O**. Tests are written first (red → green), covering normal, boundary, and empty/partial-data cases per module. CI enforces coverage on `core/`. Bug fixes on the money path add a failing regression test first. |
| **IV. Privacy & Proportionality** | PARTIAL — see Complexity Tracking | Only enumerated metadata is stored (FR-031). Team-level aggregation is the default view (FR-033). Retention default 90 days, configurable, hard-delete (FR-032). Live DB encrypted at rest (FR-032a). **Deviations**: (1) no authentication / RBAC / access logging and no engineer self-service view in v1; (2) one stored field beyond the constitution's enumerated list — `source_identity` (API key / workspace id). Both justified and tracked below. |
| **V. Deterministic & Observable Reports** | PASS | `core.reports` is a pure function of (records, pricing version, rule-catalog version). Sorted iteration by `(member_id, date, model)`; integer micro-USD math with fixed rounding; seeded RNG for demo; wall-clock only in run metadata, excluded from the determinism comparison. structlog emits a machine-parseable trace linking every spike flag and recommendation to source record ids + rule version, with a redaction filter that bars content and secrets. Each `ReportRun` records pricing version, rule-catalog version, source window, tool version, mode. |

**Data Handling & Security Constraints**: storable fields limited to the FR-031 set
**plus** `source_identity` (deviation 2). Secrets from env only, never logged
(structlog redaction). TLS is the httpx default for the Admin API. Retention configurable
with documented 90-day default. Third-party delivery: N/A in v1 (no Slack/email/BI
export).

**Development Workflow & Quality Gates**: PR + one reviewer; CI runs backend `pytest` +
`ruff` + `mypy`, frontend `vitest` + `tsc` + `eslint`. Money-path PRs must show
test-first evidence. Pricing-table or rule-catalog changes require a version bump +
`CHANGELOG` entry + tests on the changed entries. The `source_identity` field is
introduced with an ADR referencing Principle IV (tracked task). Report-format changes
must keep the determinism test green.

**Gate result (pre-Phase 0)**: PASS with two justified, tracked deviations. No unjustified violations.

### Post-Design Re-Check (after Phase 1)

Re-evaluated against `research.md`, `data-model.md`, `contracts/`, `quickstart.md`:

- **Principle III/V** — reinforced: `core/` is import-isolated from `db/`, `api/`,
  `ingestion/`; `core.reports.build_report(...)` is pure; determinism rules (sorted keys,
  integer micro-USD, seeded RNG, timestamp excluded) are specified and covered by a
  dedicated test (Scenario E).
- **Principle I** — reinforced: live mode stores the Cost API amount as authoritative and
  adds a reconciliation pass with a stated tolerance surfaced in `ReportRun.reconciliation`
  and the dashboard.
- **Principle IV** — no new personal-data fields introduced by the design. The extra
  persisted flags (`cost_is_estimate`, `is_unattributed`, `IngestionRun`/`ReportRun`
  metadata) are operational/data-quality markers carrying no content or personal data, so
  they do not require an amendment. `source_identity` remains the only enumerated-list
  deviation (ADR `0001`).
- **No new deviations.** Gate still PASS with the same two tracked items.

## Project Structure

### Documentation (this feature)

```text
specs/001-cost-usage-monitor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── rest-api.openapi.yaml       # Backend HTTP API consumed by the frontend
│   ├── cli.md                      # CLI command surface
│   ├── anthropic-admin-api.md      # Consumed external contract + fixture shape
│   ├── pricing-table.schema.json   # Bundled pricing-table file schema
│   └── rule-catalog.schema.json    # Bundled rule-catalog file schema
├── checklists/
│   └── requirements.md  # Created by /speckit-specify, updated by /speckit-clarify
└── tasks.md             # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── src/tokenpulse/
│   ├── core/                     # PURE, test-first — the money path
│   │   ├── money.py              # micro-USD integer type + rounding helpers
│   │   ├── pricing.py            # PricingTable load + cost(tokens, model, version)
│   │   ├── aggregation.py        # per member / team / model / window rollups
│   │   ├── spikes.py             # rolling-7d baseline, threshold flag, severity bands
│   │   ├── recommendations/
│   │   │   ├── catalog.py        # rule-catalog loader + versioning
│   │   │   ├── rules.py          # the 4 rule evaluators (pure)
│   │   │   └── savings.py        # conservative savings formulas
│   │   └── reports.py            # pure report assembly (pinned versions)
│   ├── ingestion/
│   │   ├── anthropic_client.py   # httpx client for usage_report + cost_report
│   │   ├── demo_generator.py     # seeded synthetic dataset (5–8 members, 90 days)
│   │   ├── attribution.py        # AttributionMap: source_identity -> member
│   │   └── pipeline.py           # normalize -> upsert (idempotent)
│   ├── db/
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── session.py            # engine (SQLCipher in live mode)
│   │   └── migrations/           # Alembic
│   ├── api/
│   │   ├── app.py                # FastAPI app + structlog + demo-mode banner flag
│   │   └── routers/             # trends.py, spikes.py, recommendations.py, meta.py, ingest.py
│   ├── config.py                # mode, threshold overrides, retention, DB path/key
│   └── cli.py                    # Typer: seed / ingest / report / prune / reconcile
├── config/
│   ├── pricing/anthropic-2026-09-01.json
│   └── rules/catalog-v1.yaml
└── tests/
    ├── unit/core/               # money-path tests (written first)
    ├── contract/                # API schema tests + anthropic_client fixture tests
    ├── integration/             # seed->ingest->report->API; determinism test
    └── fixtures/                # recorded Admin API responses

frontend/
├── src/
│   ├── pages/                   # Overview, MemberDetail, Spikes, Recommendations
│   ├── components/              # TrendChart, SpikeTable, RecommendationCard, DemoBanner
│   ├── api/                     # typed client generated/derived from rest-api.openapi.yaml
│   └── lib/                     # formatting (currency, dates)
└── tests/                       # vitest + RTL

docs/
├── architecture.md             # architecture diagram + data flow (README references it)
├── adr/0001-source-identity-field.md   # Principle IV deviation record
└── v2-roadmap.md               # FR-030

scripts/
└── demo.sh / demo.ps1          # one-command quickstart (seed + start API + start UI)
```

**Structure Decision**: Web application (Option 2) — a `backend/` FastAPI service +
`frontend/` React app in one repo. The backend isolates all money-path logic in a pure
`core/` package so Principle III (test-first) and Principle V (determinism) are
structurally enforced: `core/` has no imports from `db/`, `api/`, or `ingestion/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **No authentication / RBAC / access logging; no engineer self-service view (Principle IV)** | v1 is a single-operator local portfolio tool; the primary demo runs entirely on synthetic data. Adding auth + a role model + audit logging would multiply scope and directly fight SC-001 (5-minute zero-key quickstart). | A minimal admin/engineer role split was considered but still requires user identity, session handling, and an access-log store for a tool that, in v1, one person runs locally against fake data. Deferred to v2 (spec Out of Scope). Mitigation: team-level default view, strict data minimization, and no content ever stored. |
| **One stored field beyond the constitution's enumerated set: `source_identity` (API key / workspace id) on `UsageRecord` + `AttributionMap` (Section 2)** | Live per-person attribution (Clarification Q1) maps provider account identity → member; the id is also needed for idempotent re-ingestion and to label "unattributed" usage traceably (Principle V). | Storing only the resolved `member_id` loses the ability to show unattributed usage, re-resolve attribution after a mapping fix, or trace a record to its provider bucket. The value is provider-side account metadata, contains no prompt/PII content, and is covered by live-mode encryption at rest. Introduced via `docs/adr/0001-source-identity-field.md` referencing Principle IV. |
