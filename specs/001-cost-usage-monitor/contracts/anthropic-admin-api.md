# Contract: Anthropic Usage & Cost Admin API (consumed, Live mode)

TokenPulse **consumes** this external contract; it does not implement it. Field names
below are the **assumed** shape and MUST be verified against current Anthropic docs at
implementation time. All client behaviour is covered by fixture-backed contract tests
(`backend/tests/contract/`, fixtures in `backend/tests/fixtures/`) so the build stays
offline and deterministic.

## Auth & headers

| Header | Value |
|--------|-------|
| `x-api-key` | Admin API key (`sk-ant-admin...`) from `TOKENPULSE_ADMIN_API_KEY` |
| `anthropic-version` | `2023-06-01` |
| `content-type` | `application/json` |

Base URL: `https://api.anthropic.com`. TLS enforced (httpx default). Key never logged.

## Endpoint 1 — Message usage report

`GET /v1/organizations/usage_report/messages`

Query parameters (assumed):

| Param | Value used by TokenPulse |
|-------|--------------------------|
| `starting_at` | window start (ISO 8601, UTC) |
| `ending_at` | window end (ISO 8601, UTC) |
| `bucket_width` | `1d` |
| `group_by[]` | `api_key_id`, `workspace_id`, `model` |
| `limit` | page size (e.g. `100`) |
| `page` | opaque cursor from the previous response |

Expected response (assumed):

```jsonc
{
  "data": [
    {
      "starting_at": "2026-08-01T00:00:00Z",
      "ending_at": "2026-08-02T00:00:00Z",
      "results": [
        {
          "api_key_id": "apikey_01ABC",
          "workspace_id": "wrkspc_01XYZ",
          "model": "claude-opus-4",
          "uncached_input_tokens": 12345,
          "cache_creation_input_tokens": 2000,
          "cache_read_input_tokens": 8000,
          "output_tokens": 4567
        }
      ]
    }
  ],
  "has_more": true,
  "next_page": "page_xxx"
}
```

Mapping → `UsageRecord`:

| Response field | UsageRecord field |
|----------------|-------------------|
| `results[].uncached_input_tokens` | `input_tokens` |
| `results[].cache_creation_input_tokens` | `cache_write_tokens` |
| `results[].cache_read_input_tokens` | `cache_read_tokens` |
| `results[].output_tokens` | `output_tokens` |
| `results[].model` | `model` |
| `results[].api_key_id` (or `workspace_id`) | `source_identity` (+ `identity_kind`) |
| bucket `starting_at` date | `date` (UTC day) |

`source_identity` resolves to `member_id` via `AttributionMapEntry`; unmatched →
`__unattributed__`.

## Endpoint 2 — Cost report

`GET /v1/organizations/cost_report`

Query parameters (assumed): `starting_at`, `ending_at`, `bucket_width=1d`,
`group_by[]=workspace_id`, `group_by[]=description`, `limit`, `page`.

Expected response (assumed): daily buckets each listing line items with an `amount`
(`{ "value": "12.34", "currency": "USD" }` or minor units — confirm) per
`workspace_id` / `description`.

Use: the summed USD amount per (day, workspace) is the **authoritative** `cost_micros`
for live records (converted to integer micro-USD). The pricing-table computation is used
only for the reconciliation pass and for recommendation repricing.

## Pagination

Follow `next_page` (or equivalent cursor) while `has_more` is true. Requests are
sequential.

## Failure handling (see research.md §5)

| Condition | TokenPulse behaviour |
|-----------|----------------------|
| HTTP 429 / 5xx | exponential backoff + jitter, honour `Retry-After`, ≤ 5 retries |
| Still failing after retries | affected day range → `IngestionRun.gap_days`; run `status = partial`; exit 1; **no fabricated usage** (FR-006) |
| 401 / 403 | abort with a clear "check admin key / org access" message |
| Model absent from pricing table | record stored; `cost_is_estimate = true`; surfaced (US5 scenario 5) |
| Re-run over an already-ingested range | idempotent upsert; no duplicates (FR-007) |

## Version drift

If real field names differ from the assumptions above, update: this file, the
`anthropic_client` mapping, and the fixtures — in one change. No other module reads the
raw API shape (the client normalizes to `UsageRecord` at the boundary).
