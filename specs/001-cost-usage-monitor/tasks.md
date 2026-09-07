---

description: "Task list for TokenPulse — Claude Code Cost & Usage Monitor (v1)"
---

# Tasks: TokenPulse — Claude Code Cost & Usage Monitor (v1)

**Input**: Design documents from `/specs/001-cost-usage-monitor/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. The constitution (Principle III — NON-NEGOTIABLE) requires test-first
development for all money-path logic (cost, aggregation, spike detection, severity, rule
evaluation). Contract and integration tests are included to cover the spec's acceptance
scenarios and `quickstart.md`.

**Organization**: Tasks are grouped by user story. Phases 1–2 are shared prerequisites;
Phases 3–7 are one user story each in priority order; Phase 8 is polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5; Setup / Foundational / Polish tasks carry no story label
- File paths are repo-relative

## Path Conventions

Web app per plan.md: `backend/src/tokenpulse/`, `backend/tests/`, `backend/config/`,
`frontend/src/`, `frontend/tests/`, `docs/`, `scripts/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repo scaffold and toolchain

- [ ] T001 Create monorepo structure (`backend/`, `frontend/`, `docs/`, `scripts/`) per plan.md
- [ ] T002 [P] Initialize backend Python 3.12 project with `uv` in `backend/pyproject.toml` (fastapi, uvicorn, pydantic, sqlalchemy, alembic, httpx, typer, structlog, python-dotenv, pyyaml)
- [ ] T003 [P] Add backend dev/test deps in `backend/pyproject.toml` (pytest, pytest-cov, respx, ruff, mypy, jsonschema)
- [ ] T004 [P] Scaffold frontend with Vite React-TS in `frontend/package.json` (react, react-dom, recharts, @tanstack/react-query, react-router-dom)
- [ ] T005 [P] Add frontend dev/test deps in `frontend/package.json` (vitest, @testing-library/react, @testing-library/jest-dom, eslint, prettier, typescript)
- [ ] T006 [P] Configure backend lint/type in `backend/ruff.toml` and `backend/mypy.ini` (strict on `tokenpulse/core`)
- [ ] T007 [P] Configure frontend lint/format in `frontend/.eslintrc.cjs`, `frontend/.prettierrc`, `frontend/tsconfig.json` (strict)
- [ ] T008 [P] Add CI workflow `.github/workflows/ci.yml` (backend: ruff + mypy + pytest w/ coverage gate on `tokenpulse/core`; frontend: eslint + tsc + vitest)
- [ ] T009 [P] Add `Makefile` and `scripts/demo.sh` + `scripts/demo.ps1` stubs at repo root
- [ ] T010 [P] Add `.gitignore`, `.editorconfig`, `.gitattributes` (LF normalization) at repo root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core money-path primitives, persistence, config, logging, API/CLI/frontend shells that every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T011 [P] Write ADR `docs/adr/0001-source-identity-field.md` documenting both plan.md Complexity Tracking deviations (the `source_identity` stored field and the no-auth/RBAC deferral), each referencing Principle IV — **done**
- [ ] T012 [P] Unit tests (test-first) for micro-USD money type in `backend/tests/unit/core/test_money.py`
- [ ] T013 Implement `backend/src/tokenpulse/core/money.py` (integer micro-USD, `ROUND_HALF_UP` quantize, parse/format, Decimal helpers) — make T012 pass
- [ ] T014 [P] Copy contract schemas into the package: `backend/config/schemas/pricing-table.schema.json` and `backend/config/schemas/rule-catalog.schema.json` (from `specs/001-cost-usage-monitor/contracts/`)
- [ ] T015 [P] Unit tests (test-first) for pricing loader + `cost()` in `backend/tests/unit/core/test_pricing.py` (date selection, unknown model → estimate, normal/boundary/empty)
- [ ] T016 Implement `backend/src/tokenpulse/core/pricing.py` (load dated tables, select by record date, `cost(tokens, model, version)`, unknown-model estimate flag) — make T015 pass
- [ ] T017 [P] Add bundled pricing table `backend/config/pricing/anthropic-2026-09-01.json` (valid against schema)
- [ ] T018 [P] Unit tests (test-first) for rule-catalog loader + versioning in `backend/tests/unit/core/test_catalog.py`
- [ ] T019 Implement `backend/src/tokenpulse/core/recommendations/catalog.py` (load YAML, schema-validate, expose spike params + rules + version) — make T018 pass
- [ ] T020 [P] Add bundled rule catalog `backend/config/rules/catalog-v1.yaml` with FR-019 / FR-020a / FR-029 defaults
- [ ] T021 [P] Unit tests (test-first) for aggregation rollups in `backend/tests/unit/core/test_aggregation.py` (per member/team/model/window; missing vs zero; PoP null; team == Σ members)
- [ ] T022 Implement `backend/src/tokenpulse/core/aggregation.py` (daily series, period totals, prev-period delta, `by_model`, invariant) — make T021 pass
- [ ] T023 Implement config loader `backend/src/tokenpulse/config.py` + `backend/tokenpulse.example.toml` (mode, db path/key, `retention_days`, threshold overrides; env `TOKENPULSE_ADMIN_API_KEY`, `TOKENPULSE_DB_KEY`)
- [ ] T024 Implement `backend/src/tokenpulse/logging.py` (structlog JSON to stderr, allow-list processor + secret redaction so no content/keys can be logged — FR-036)
- [ ] T025 Implement `backend/src/tokenpulse/db/session.py` (SQLAlchemy engine/session; plain SQLite for demo; SQLCipher URL when `mode=live` + `TOKENPULSE_DB_KEY`)
- [ ] T026 [P] Implement SQLAlchemy models in `backend/src/tokenpulse/db/models.py` (Team, Member, AttributionMapEntry, UsageRecord, IngestionRun, SpikeFlag, Recommendation, ReportRun) per data-model.md
- [ ] T027 Initialize Alembic in `backend/` and create the initial migration for all tables under `backend/src/tokenpulse/db/migrations/`
- [ ] T028 Add a data migration seeding the reserved Member `__unattributed__` and the two demo Teams in `backend/src/tokenpulse/db/migrations/`
- [ ] T029 Implement idempotent upsert + normalization skeleton in `backend/src/tokenpulse/ingestion/pipeline.py` (`RawUsageBucket` → `UsageRecord`, unique keys per data-model.md)
- [ ] T030 Implement FastAPI app skeleton `backend/src/tokenpulse/api/app.py` (router registration, structlog middleware, exception handler → `Error` schema)
- [ ] T031 Implement `/api/meta` route in `backend/src/tokenpulse/api/routers/meta.py` (returns `Meta` from config + loaders)
- [ ] T032 Implement Typer CLI skeleton `backend/src/tokenpulse/cli.py` (global options `--config/--db/--json/--log-level`; register subcommands; `serve`)
- [ ] T033 [P] Frontend app shell in `frontend/src/main.tsx` + `frontend/src/App.tsx` (router, layout, TanStack Query provider)
- [ ] T034 [P] Frontend typed API client base `frontend/src/api/client.ts` + `frontend/src/api/types.ts` derived from `specs/001-cost-usage-monitor/contracts/rest-api.openapi.yaml`
- [ ] T035 [P] Frontend `frontend/src/components/DemoBanner.tsx` (reads `/api/meta`, shows synthetic-data banner — FR-004)
- [ ] T036 [P] Frontend `frontend/src/lib/format.ts` (micro-USD → USD, date, percent helpers)

**Checkpoint**: Money path primitives + DB + API/CLI/frontend shells ready — user stories can begin

---

## Phase 3: User Story 1 - Zero-setup demo mode (Priority: P1) 🎯 MVP

**Goal**: `tokenpulse seed` produces a deterministic 90-day synthetic dataset (6 members / 2 teams) with injected spikes and rule-triggering patterns; app runs with zero API keys and shows a synthetic-data banner.

**Independent Test**: From a fresh clone with no env vars, run the seed command; verify 5–8 members with 90 days of history, 2–3 injected spikes, and `GET /api/meta` → `is_demo_data: true`. Re-running with the same seed yields a byte-identical dataset.

### Tests for User Story 1

- [ ] T037 [P] [US1] Unit test (test-first) for the demo generator in `backend/tests/unit/ingestion/test_demo_generator.py` (same seed → identical dataset; contains 2–3 spikes, a team model-mix shift, a low-cache pattern, a steady-high-volume pattern)
- [ ] T038 [P] [US1] Integration test in `backend/tests/integration/test_seed.py` (6 members / 2 teams, 90 days, row counts; idempotent re-run creates no duplicates)
- [ ] T039 [P] [US1] Contract test for `/api/meta` in `backend/tests/contract/test_meta.py` (`is_demo_data` true, versions + `spike_multiple` present after seed)

### Implementation for User Story 1

- [ ] T040 [US1] Implement `backend/src/tokenpulse/ingestion/demo_generator.py` (seeded RNG, lognormal daily variance, weekend dampening, model mix, injected spikes + patterns per research.md §9)
- [ ] T041 [US1] Wire the demo path in `backend/src/tokenpulse/ingestion/pipeline.py` (cost via `core.pricing`, `source="demo"`, `cost_is_estimate`)
- [ ] T042 [US1] Implement the `seed` command in `backend/src/tokenpulse/cli.py` (`--seed 20260907`, `--days 90`, `--members 6`, `--reset`)
- [ ] T043 [US1] Finalize `/api/meta` fields in `backend/src/tokenpulse/api/routers/meta.py` (pricing versions list, `rule_catalog_version`, `spike_multiple`, `retention_days`)
- [ ] T044 [P] [US1] Frontend: `frontend/src/api/useMeta.ts` hook + mount `DemoBanner` in the layout
- [ ] T045 [US1] Update `scripts/demo.sh` and `scripts/demo.ps1` to run `uv sync` → `tokenpulse seed` → `tokenpulse report` → start the API

**Checkpoint**: `tokenpulse seed` populates the DB; `/api/meta` and the demo banner work

---

## Phase 4: User Story 2 - Usage & cost trend dashboard (Priority: P1)

**Goal**: Team-level and per-member/per-model cost and token trend lines over a selectable date range, with totals, period-over-period change, and the team = Σ members invariant.

**Independent Test**: With the demo dataset loaded, open the dashboard, select a date range, and confirm team and per-member trend lines render with totals and PoP change; `GET /api/totals` shows `team.cost_micros == Σ members[].cost_micros`.

### Tests for User Story 2

- [ ] T046 [P] [US2] Contract test `/api/teams` in `backend/tests/contract/test_teams.py`
- [ ] T047 [P] [US2] Contract test `/api/trends` in `backend/tests/contract/test_trends.py` (series shape, `is_spike`, `missing` flags, `empty_reason`)
- [ ] T048 [P] [US2] Contract test `/api/totals` in `backend/tests/contract/test_totals.py` (team == Σ members; PoP null with no prior period)
- [ ] T049 [P] [US2] Integration test in `backend/tests/integration/test_trends_totals.py` (seed → invariant + PoP over the demo range)
- [ ] T050 [P] [US2] Frontend component tests in `frontend/tests/TrendChart.test.tsx` (renders lines; date-range change refetches; empty + loading states)

### Implementation for User Story 2

- [ ] T051 [P] [US2] Implement `/api/teams` router `backend/src/tokenpulse/api/routers/teams.py`
- [ ] T052 [US2] Implement `/api/trends` + `/api/totals` in `backend/src/tokenpulse/api/routers/trends.py` (uses `core.aggregation`; `is_spike` from latest `ReportRun` flags if present, else false)
- [ ] T053 [P] [US2] Frontend hooks `frontend/src/api/useTrends.ts`, `useTotals.ts`, `useTeams.ts`
- [ ] T054 [P] [US2] Frontend `frontend/src/components/TrendChart.tsx` (Recharts line, spike-dot markers, missing-day gaps)
- [ ] T055 [P] [US2] Frontend `frontend/src/components/TotalsCards.tsx` (totals + PoP delta)
- [ ] T056 [P] [US2] Frontend `frontend/src/components/DateRangePicker.tsx`
- [ ] T057 [US2] Frontend `frontend/src/pages/Overview.tsx` (team trends + totals + range control)
- [ ] T058 [US2] Frontend `frontend/src/pages/MemberDetail.tsx` (per-member trends, `by_model` toggle)
- [ ] T059 [US2] Frontend routing + nav for Overview / MemberDetail in `frontend/src/App.tsx`
- [ ] T060 [US2] Update `scripts/demo.sh` / `scripts/demo.ps1` to also start the frontend dev server and open the browser
- [ ] T061 [P] [US2] Frontend empty/loading skeleton states for trend views in `frontend/src/components/Skeletons.tsx`

**Checkpoint**: End-to-end demo dashboard runs on synthetic data (satisfies SC-001, SC-002) — this is the meaningful MVP

---

## Phase 5: User Story 3 - Automatic spike detection (Priority: P2)

**Goal**: Rolling 7-day baseline per member, flag days ≥ 2.5× baseline (configurable), four severity bands with dollar-excess floors, "insufficient history" handling, deterministic flags.

**Independent Test**: Load the demo dataset, open the spikes view; every injected spike day is listed with baseline / actual / deviation / severity, no non-spike day is listed, and members with < 7 prior days show as "insufficient history". Running `report` twice yields an identical flag set.

### Tests for User Story 3

- [ ] T062 [P] [US3] Unit tests (test-first) for `core.spikes` in `backend/tests/unit/core/test_spikes.py` (baseline; exactly-T boundary; < 7 days; zero-usage days; consecutive-spike normalization; severity band boundaries; dollar-floor demotion; tiny-dollar spike; 50× extreme)
- [ ] T063 [P] [US3] Integration test in `backend/tests/integration/test_spikes.py` (seed → flags == injected spike days and none else — SC-003; determinism: run twice identical)
- [ ] T064 [P] [US3] Contract test `/api/spikes` in `backend/tests/contract/test_spikes.py` (`flags` + `insufficient_history`)

### Implementation for User Story 3

- [ ] T065 [US3] Implement `backend/src/tokenpulse/core/spikes.py` (rolling-7d baseline, flag at `r ≥ T`, four-band severity + dollar-floor demotion, `insufficient_history`) — make T062 pass
- [ ] T066 [US3] Implement `backend/src/tokenpulse/core/reports.py` — pure `build_report(...)` producing `SpikeFlag`s (sorted iteration, pinned pricing + catalog versions)
- [ ] T067 [US3] Persist report + flags and implement the `report` command in `backend/src/tokenpulse/cli.py` (`--start/--end`, `--rule-catalog`, `--check-determinism`)
- [ ] T068 [US3] Implement `/api/spikes` in `backend/src/tokenpulse/api/routers/spikes.py` and `/api/report-runs/latest` in `backend/src/tokenpulse/api/routers/meta.py`
- [ ] T069 [US3] Populate `is_spike` in the trends router from the latest `ReportRun` (`backend/src/tokenpulse/api/routers/trends.py`)
- [ ] T070 [P] [US3] Frontend `frontend/src/api/useSpikes.ts` + `frontend/src/components/SpikeTable.tsx` (severity badges, insufficient-history note)
- [ ] T071 [P] [US3] Frontend `frontend/src/pages/Spikes.tsx` + nav entry
- [ ] T072 [US3] Frontend: activate spike markers + severity styling in `frontend/src/components/TrendChart.tsx`
- [ ] T073 [US3] Add `tokenpulse report --check-determinism` to `.github/workflows/ci.yml`

**Checkpoint**: Spikes view + trend markers work on demo data; determinism enforced in CI

---

## Phase 6: User Story 4 - Rule-based optimization recommendations (Priority: P2)

**Goal**: Four metadata-only rules from the versioned catalog produce plain-English recommendations, each carrying rule id + catalog version + trigger data + threshold data + message, with a conservative savings figure and its basis (rule `model-mix-shift` carries no dollar figure).

**Independent Test**: On the demo dataset, open recommendations; all four rule ids fire, each shows its trigger/threshold data and message, three carry `estimated_savings_micros` + `savings_basis`, and `model-mix-shift` has `null` savings. Re-generation is byte-identical.

### Tests for User Story 4

- [ ] T074 [P] [US4] Unit tests (test-first) for the four rules in `backend/tests/unit/core/test_rules.py` (fire / no-fire boundary; empty data; `model-mix-shift` null savings)
- [ ] T075 [P] [US4] Unit tests (test-first) for savings formulas in `backend/tests/unit/core/test_savings.py` (conservative; Opus→Sonnet reprice; caching; batch 50%)
- [ ] T076 [P] [US4] Integration test in `backend/tests/integration/test_recommendations.py` (seed → all four rule ids present; determinism)
- [ ] T077 [P] [US4] Contract test `/api/recommendations` in `backend/tests/contract/test_recommendations.py` (rule id/version/trigger/threshold/message; `savings_basis` present or null)

### Implementation for User Story 4

- [ ] T078 [US4] Implement `backend/src/tokenpulse/core/recommendations/rules.py` (four pure evaluators over trailing-7d aggregates) — make T074 pass
- [ ] T079 [US4] Implement `backend/src/tokenpulse/core/recommendations/savings.py` (formulas + assumptions → micro-USD) — make T075 pass
- [ ] T080 [US4] Extend `backend/src/tokenpulse/core/reports.py` to build + persist `Recommendation`s; extend `report` command output
- [ ] T081 [US4] Implement `/api/recommendations` router `backend/src/tokenpulse/api/routers/recommendations.py`
- [ ] T082 [P] [US4] Frontend `frontend/src/api/useRecommendations.ts` + `frontend/src/components/RecommendationCard.tsx` (rule id, version, `trigger_data`, `threshold_data`, `savings_basis`)
- [ ] T083 [US4] Frontend `frontend/src/pages/Recommendations.tsx` + nav entry

**Checkpoint**: Recommendations view works on demo data; all four rules fire

---

## Phase 7: User Story 5 - Live Anthropic usage ingestion (Priority: P3)

**Goal**: Admin API client pulls day-bucketed usage + cost, joins to members via the operator `AttributionMap` (unmapped → `__unattributed__`), idempotent upsert, gaps reported not fabricated, live DB encrypted at rest, cost reconciliation surfaced — all feeding the same views.

**Independent Test**: With a mocked Admin API, run `tokenpulse ingest` for a range; records populate the same dashboard / spike / recommendation views; re-running creates no duplicates; a failed page becomes `gap_days` and a non-zero exit; unmapped usage shows under `__unattributed__`; the live DB file has no readable identifiers without the key.

### Tests for User Story 5

- [ ] T084 [P] [US5] Add Admin API fixtures in `backend/tests/fixtures/` (usage_report pages, cost_report pages, 429-then-200, 401)
- [ ] T085 [P] [US5] Contract tests for the client in `backend/tests/contract/test_anthropic_client.py` (pagination, backoff + `Retry-After`, header auth, 401 abort) using respx
- [ ] T086 [P] [US5] Unit tests for the attribution resolver in `backend/tests/unit/ingestion/test_attribution.py` (mapped; unmapped → `__unattributed__`)
- [ ] T087 [P] [US5] Integration test (mocked client) in `backend/tests/integration/test_live_ingest.py` (ingest → records → same `/api` endpoints; idempotent re-run; partial page → `gap_days` + exit 1; unknown model → estimate; reconciliation warning)
- [ ] T088 [P] [US5] Encryption-at-rest test in `backend/tests/integration/test_encryption.py` (live DB file has no plaintext member ids / values without `TOKENPULSE_DB_KEY`)

### Implementation for User Story 5

- [ ] T089 [US5] Implement `backend/src/tokenpulse/ingestion/anthropic_client.py` (httpx, `x-api-key` + `anthropic-version`, cursor pagination, exponential backoff + jitter, `Retry-After`, 401/403 abort) per `contracts/anthropic-admin-api.md`
- [ ] T090 [US5] Implement `backend/src/tokenpulse/ingestion/attribution.py` (load `config/attribution.yaml`, resolve `source_identity` → member, unattributed fallback) + `backend/config/attribution.example.yaml`
- [ ] T091 [US5] Extend `backend/src/tokenpulse/ingestion/pipeline.py` live path (map usage + cost buckets → `UsageRecord`; cost from cost_report; idempotency key `(source, source_identity, model, date)`; unknown-model estimate; write `IngestionRun` + `gap_days`)
- [ ] T092 [US5] Add the SQLCipher engine path in `backend/src/tokenpulse/db/session.py` and add `sqlcipher3-binary` to `backend/pyproject.toml` (live mode only)
- [ ] T093 [US5] Implement reconciliation in `backend/src/tokenpulse/core/reports.py` (Σ tokens × pricing vs Σ cost_report; tolerance `max(1%, $1)`; `ReconciliationWarning` → `ReportRun.reconciliation`)
- [ ] T094 [US5] Implement the `ingest` command in `backend/src/tokenpulse/cli.py` (`--start/--end/--attribution`; env-var checks; auto-run report; exit codes per `contracts/cli.md`)
- [ ] T095 [US5] Implement `POST /api/ingest` router `backend/src/tokenpulse/api/routers/ingest.py` (demo + live; 202 with `IngestionRun`; 409 when live creds missing)
- [ ] T096 [US5] Extend `/api/report-runs/latest` to include `reconciliation` in `backend/src/tokenpulse/api/routers/meta.py`
- [ ] T097 [P] [US5] Frontend `frontend/src/components/ReconciliationBanner.tsx` (header warning when any period is over tolerance)

**Checkpoint**: Live smoke (quickstart Scenario G) passes with a mocked client

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Retention, observability trace, docs, packaging, and full quickstart validation

- [ ] T098 [P] Implement the `prune` retention command + test in `backend/src/tokenpulse/cli.py` and `backend/tests/integration/test_retention.py` (default 90 days, hard delete, `--dry-run` — FR-032)
- [ ] T099 [P] Add structlog trace events linking each `SpikeFlag` and `Recommendation` to source `usage_record` ids + rule/catalog version in `backend/src/tokenpulse/core/reports.py` (SC-008)
- [ ] T100 [P] Write `docs/architecture.md` with an architecture + data-flow diagram
- [ ] T101 [P] Write `docs/v2-roadmap.md` (OpenAI + Gemini ingestion, Slack spike alerts, weekly digest email, team budgets & forecasting — FR-030)
- [ ] T102 [P] Write `README.md` (problem statement, embedded architecture diagram, "how I used AI to build this", screenshot/GIF placeholders, < 5-minute quickstart — SC-009)
- [ ] T103 [P] Add `CHANGELOG.md` with pricing-table and rule-catalog v1 entries
- [ ] T104 [P] Enforce a coverage gate for `tokenpulse/core` in `backend/pyproject.toml` and `.github/workflows/ci.yml`
- [ ] T105 [P] Frontend: consistent loading skeletons + empty states across all pages in `frontend/src/components/`
- [ ] T106 [P] Add optional `docker-compose.yml` + `backend/Dockerfile` + `frontend/Dockerfile`
- [ ] T107 Performance smoke test `backend/tests/integration/test_perf_smoke.py` (`/api/trends` and `/api/totals` p95 < 200 ms on the reference dataset)
- [ ] T108 Run all `quickstart.md` scenarios A–H end to end and fix any gaps
- [ ] T109 [P] Accessibility + formatting pass on the dashboard (labels, contrast, keyboard nav)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup — **blocks all user stories**
- **User Stories (Phases 3–7)**: each depends only on Foundational; US1 → US2 → US3 → US4 → US5 in priority order, but see cross-story notes below
- **Polish (Phase 8)**: depends on the user stories it touches (retention/observability need Phase 5–6; quickstart run needs all)

### Cross-Story Notes (kept minimal so each story stays independently testable)

- **US2** renders without US3; `is_spike` is simply `false` until US3 exists. US2 is fully testable alone.
- **US3** creates `core/reports.py`; **US4** extends the same file (T080) and **US5** extends it again (T093) — these three tasks are sequential, not `[P]`.
- **US3/US4** consume `core/aggregation.py` (Foundational T022); no new dependency.
- **US5** reuses `ingestion/pipeline.py` (Foundational T029, extended by US1 T041 and US5 T091 — sequential on that file) and the same API routers; it adds live-only concerns without changing demo behavior.
- **Spike markers in the trend chart** (T072) and **reconciliation banner** (T097) are the only frontend items that depend on a later story's backend.

### Within Each User Story

- Test tasks are written first and must fail before implementation (money-path: NON-NEGOTIABLE)
- `core/` pure logic → `reports.py` assembly → CLI command → API route → frontend
- Models/loaders before services; services before endpoints; endpoints before UI

### Parallel Opportunities

- Setup: T002–T010 all `[P]`
- Foundational: T011, T012/T015/T018/T021 (test files) `[P]`; T014, T017, T020 `[P]`; T026, T033–T036 `[P]`. T013→after T012; T016→after T015; T019→after T018; T022→after T021; T027/T028→after T026; T030/T031→after T025/T026
- Within a story: all test tasks `[P]`; frontend hook/component tasks `[P]` with each other; backend route work is sequential where it shares a router file
- Across stories: once Foundational is done, US1–US5 backends can be built in parallel by different people **except** the shared `core/reports.py` and `ingestion/pipeline.py` edits noted above

---

## Parallel Example: User Story 3

```bash
# Write all US3 tests first (parallel), confirm they fail:
Task: "Unit tests for core.spikes in backend/tests/unit/core/test_spikes.py"        # T062
Task: "Integration test in backend/tests/integration/test_spikes.py"                 # T063
Task: "Contract test /api/spikes in backend/tests/contract/test_spikes.py"           # T064

# Then implement (T065 → T066 → T067 sequential; T070, T071 parallel):
Task: "Implement core/spikes.py"                                                     # T065
Task: "Frontend useSpikes.ts + SpikeTable.tsx"                                       # T070
Task: "Frontend Spikes.tsx page"                                                     # T071
```

---

## Implementation Strategy

### MVP First

1. Phase 1 (Setup) → Phase 2 (Foundational)
2. Phase 3 (US1): deterministic demo data + `/api/meta` + banner
3. Phase 4 (US2): trend dashboard on demo data
4. **STOP and VALIDATE**: quickstart Scenarios A and B — this satisfies SC-001 and SC-002 and is demoable

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. + US1 + US2 → **MVP**: zero-key demo dashboard (validate, demo)
3. + US3 → spike detection + markers (validate Scenario C)
4. + US4 → recommendations (validate Scenario D)
5. + US5 → live ingestion behind a mocked client (validate Scenario G)
6. Phase 8 → retention, observability trace, docs, full quickstart A–H

### Parallel Team Strategy

After Foundational: Dev A on US1+US2 (critical path), Dev B on US3, Dev C on US4; US5 after the API surface from US2/US3 stabilizes. Coordinate on `core/reports.py` and `ingestion/pipeline.py`.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task
- `[US#]` label maps every user-story task to a spec.md story for traceability
- Money-path tests (`backend/tests/unit/core/`) are written first and must fail before implementation (constitution Principle III)
- Determinism: `core/` is import-isolated from `db/`, `api/`, `ingestion/`; verify with `tokenpulse report --check-determinism`
- Commit after each task or logical group; changes to `config/pricing/*` or `config/rules/*` require a version bump + `CHANGELOG` entry + tests
- Stop at any checkpoint to validate a story independently
