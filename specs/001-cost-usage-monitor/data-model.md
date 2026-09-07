# Phase 1 Data Model: TokenPulse v1

Persisted entities, derived (computed, non-persisted) structures, and the config
artifacts. Money is stored as **integer micro-USD** (`*_micros`, 1 = 1e-6 USD); tokens as
integers; all dates are **UTC calendar days** (`DATE`), all timestamps UTC (`TIMESTAMP`).

Storable persisted fields are limited to the constitution's Section 2 list **plus**
`source_identity` (tracked deviation — `docs/adr/0001-source-identity-field.md`). No
prompt, completion, code, or file content is stored anywhere.

---

## Persisted entities

### Team

| Field | Type | Notes |
|-------|------|-------|
| `id` | TEXT PK | slug, e.g. `platform` |
| `name` | TEXT | display name |

### Member  (spec: "User (team member)")

| Field | Type | Notes |
|-------|------|-------|
| `id` | TEXT PK | stable id |
| `display_name` | TEXT | |
| `team_id` | TEXT FK → Team.id | |
| `is_unattributed` | BOOLEAN | exactly one reserved row `id = "__unattributed__"`, `true`; holds live usage whose `source_identity` is unmapped (FR-008b) |

- **Uniqueness**: `id`. The reserved unattributed member is seeded by migration.
- **Relationships**: one Team has many Members; one Member has many UsageRecords.

### AttributionMapEntry  (live mode only — FR-008a)

| Field | Type | Notes |
|-------|------|-------|
| `source_identity` | TEXT PK | API key id or workspace id string as returned by the Admin API |
| `identity_kind` | TEXT | `api_key` \| `workspace` |
| `member_id` | TEXT FK → Member.id | target member |

- Loaded from an operator-maintained file (`config/attribution.yaml`) on each live
  ingest; upserted. Editing the file + re-ingesting re-resolves attribution.
- Not used in demo mode.

### UsageRecord

One member's usage of one model on one UTC day from one source.

| Field | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | surrogate |
| `member_id` | TEXT FK → Member.id | resolved member (or `__unattributed__`) |
| `source` | TEXT | `live` \| `demo` |
| `source_identity` | TEXT NULL | API key / workspace id (live only; NULL for demo) — *tracked deviation* |
| `date` | DATE | UTC day |
| `model` | TEXT | provider model id, e.g. `claude-opus-4` |
| `input_tokens` | INTEGER | uncached input tokens |
| `output_tokens` | INTEGER | |
| `cache_read_tokens` | INTEGER | cache-read input tokens |
| `cache_write_tokens` | INTEGER | cache-creation input tokens |
| `request_type` | TEXT NULL | interaction type if the source provides it |
| `cost_micros` | INTEGER | authoritative cost: Cost API amount (live) or pricing-table computed (demo) |
| `cost_is_estimate` | BOOLEAN | `true` when derived from the pricing table or the model was unpriced (FR-011, US5 scenario 5) |
| `pricing_table_version` | TEXT | version whose rates apply to this record's `date` |
| `ingested_at` | TIMESTAMP | run metadata, excluded from determinism comparison |

- **Idempotency key (unique index)**: `(source, source_identity, model, date)` for live;
  `(source, member_id, model, date)` for demo (`source_identity` NULL). Re-ingestion
  upserts, never duplicates (FR-007).
- **Validation**: all token counts ≥ 0; `cost_micros` ≥ 0; `date` within
  `[today-… , today]`; `pricing_table_version` must resolve to a bundled table whose
  effective range contains `date` (else `cost_is_estimate = true` + `ReconciliationWarning`).
- **Missing vs zero**: absence of a row for a member/day = missing (shown as a gap); a row
  with all-zero tokens and `cost_micros = 0` = genuine zero (counts in the baseline).

### IngestionRun

| Field | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | |
| `mode` | TEXT | `live` \| `demo` |
| `requested_start` / `requested_end` | DATE | window asked for |
| `covered_start` / `covered_end` | DATE | window actually stored |
| `gap_days` | JSON | list of `{start, end, group}` not fabricated (FR-006) |
| `status` | TEXT | `complete` \| `partial` \| `failed` |
| `started_at` / `finished_at` | TIMESTAMP | |
| `tool_version` | TEXT | |

### SpikeFlag

Persisted output of the spike rule for a member/day (FR-020, FR-020a).

| Field | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | |
| `member_id` | TEXT FK → Member.id | |
| `date` | DATE | the flagged day |
| `baseline_avg_micros` | INTEGER | rolling trailing-7-day mean of daily `cost_micros` |
| `actual_micros` | INTEGER | that day's total `cost_micros` |
| `deviation_ratio` | TEXT | decimal string `actual / baseline` (exact, not float) |
| `excess_micros` | INTEGER | `actual - baseline` |
| `severity` | TEXT | `low` \| `moderate` \| `high` \| `critical` |
| `spike_multiple` | TEXT | `T` in effect (decimal string) |
| `high_floor_micros` / `critical_floor_micros` | INTEGER | dollar floors in effect |
| `rule_catalog_version` | TEXT | catalog that produced this flag |
| `report_run_id` | INTEGER FK → ReportRun.id | |

- **Unique**: `(report_run_id, member_id, date)`.
- **Not produced** when the member has < 7 prior days of history in the analysed window
  (FR-021) — such members are reported separately as `insufficient_history` (derived, not
  a row).

### Recommendation

Persisted output of a recommendation rule (FR-026).

| Field | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | |
| `subject_kind` | TEXT | `member` \| `team` |
| `subject_id` | TEXT | Member.id or Team.id |
| `rule_id` | TEXT | stable id from the catalog (e.g. `opus-on-lightweight`) |
| `rule_catalog_version` | TEXT | |
| `window_start` / `window_end` | DATE | trailing window evaluated |
| `trigger_data` | JSON | observed values that fired the rule (e.g. `{opus_cost_share: 0.71, out_in_ratio: 0.12}`) |
| `threshold_data` | JSON | threshold values in effect |
| `message` | TEXT | plain-English suggestion |
| `estimated_savings_micros` | INTEGER NULL | NULL for rule (d) and any rule that cannot bound its estimate (FR-027) |
| `savings_basis` | JSON NULL | formula + assumptions when a figure is given (FR-011) |
| `report_run_id` | INTEGER FK → ReportRun.id | |

- **Unique**: `(report_run_id, rule_id, subject_kind, subject_id)`.

### ReportRun

| Field | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | |
| `generated_at` | TIMESTAMP | metadata only — excluded from the determinism comparison |
| `source_window_start` / `source_window_end` | DATE | |
| `mode` | TEXT | `live` \| `demo` |
| `pricing_table_versions` | JSON | all versions referenced by records in the window |
| `rule_catalog_version` | TEXT | |
| `tool_version` | TEXT | |
| `reconciliation` | JSON NULL | `{computed_micros, reported_micros, delta_micros, within_tolerance}` per period (live only) |

---

## Derived structures (computed, not persisted)

| Structure | Shape | Source |
|-----------|-------|--------|
| `TrendSeries` | per (scope, metric) list of `{date, value}` where scope ∈ {team, member, member×model}, metric ∈ {cost_micros, tokens} | `core.aggregation` over UsageRecord |
| `PeriodTotals` | `{scope_id, cost_micros, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, prev_period_delta_pct}` | `core.aggregation`; team total == Σ member totals (FR-017 invariant, asserted in tests) |
| `InsufficientHistory` | list of `member_id` with < 7 prior days in range | `core.spikes` |
| `ReconciliationWarning` | `{period, workspace, computed_micros, reported_micros, delta_micros}` | `core.reports` (live) |

---

## Config artifacts (bundled, versioned — not in the database)

### PricingTable — `backend/config/pricing/anthropic-<effective-date>.json`

`{ version, effective_start, effective_end, currency: "USD", models: { "<model-id>":
{ input_per_mtok, output_per_mtok, cache_write_per_mtok, cache_read_per_mtok } } }`.
Rates are decimal strings. Multiple dated files coexist; a record's `date` selects the
file whose effective range contains it (FR-012). Schema:
`contracts/pricing-table.schema.json`. Change ⇒ new file + `CHANGELOG` + tests.

### RuleCatalog — `backend/config/rules/catalog-v<n>.yaml`

`{ version, spike: { multiple, high_floor_usd, critical_floor_usd,
severity_ratio_bands }, rules: [ { id, title, enabled, window_days, thresholds: {...},
savings_formula, assumptions } ] }`. Seeded `v1` with FR-019 / FR-020a / FR-029
defaults. Schema: `contracts/rule-catalog.schema.json`. Any threshold change ⇒ version
bump + `CHANGELOG` + tests (FR-029a).

Seeded `v1` rule entries:

| `rule_id` | window_days | key thresholds | savings |
|-----------|-------------|----------------|---------|
| `opus-on-lightweight` | 7 | `opus_cost_share ≥ 0.60`, `opus_out_in_ratio ≤ 0.20` | window Opus cost − same tokens repriced at Sonnet |
| `low-cache-utilisation` | 7 | `cache_hit_ratio < 0.10`, `input_tokens ≥ 1_000_000` | modeled cacheable-input saving at cache-read vs input rate (conservative fraction) |
| `steady-high-volume` | 7 | `mean_daily_tokens ≥ 5_000_000`, `daily_cv ≤ 0.30` | 50% of window cost for the batchable share |
| `model-mix-shift` | 7 vs prior 7 | `opus_cost_share_increase ≥ 0.25` (percentage points) | none (flag only) |

---

## Entity relationship summary

```text
Team 1───* Member 1───* UsageRecord *───1 (model id, free text)
                 │              ▲
                 │              │ resolves via
                 │        AttributionMapEntry (live only)
                 │
                 ├──* SpikeFlag ──* 1 ReportRun
                 └──* Recommendation ──* 1 ReportRun   (Recommendation.subject may be Team)
IngestionRun (standalone; records covered window + gaps)
```

## Lifecycle notes

- **UsageRecord**: created by ingestion (idempotent upsert); deleted only by the
  retention job when `date < today - retention_days` (default 90, FR-032). No update path
  except upsert of token/cost values for the same idempotency key.
- **SpikeFlag / Recommendation**: fully recomputed per `ReportRun`; not mutated. Old runs
  may be pruned but the latest run is always retained.
- **AttributionMapEntry**: rewritten from the operator file on each live ingest.
