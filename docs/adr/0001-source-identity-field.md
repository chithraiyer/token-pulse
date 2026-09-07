# ADR 0001: Constitution deviations for TokenPulse v1 — `source_identity` stored field and no auth/RBAC

- **Status**: Accepted
- **Date**: 2026-09-07
- **Feature**: `001-cost-usage-monitor` (see `specs/001-cost-usage-monitor/plan.md` →
  Complexity Tracking)
- **Constitution**: v1.0.0 — Principle IV (Privacy & Proportionality),
  Section "Data Handling & Security Constraints"
- **Deciders**: project maintainer

## Context

The Token Pulse constitution constrains what member-attributed data may be stored and
how per-member views are protected:

- **Section 2 (Data Handling & Security Constraints)** enumerates the storable fields:
  member identifier, team identifier, timestamp, model, request/interaction type, input
  tokens, output tokens, cache-read tokens, cache-write tokens, computed cost, and the
  pricing-table version. *"Adding any new stored field REQUIRES a constitution amendment
  or an explicit ADR referencing Principle IV."*
- **Principle IV** requires per-member breakdowns to be gated behind an explicit
  access-control role, access grants to be logged, and monitored engineers to be able to
  view their own usage data.

The v1 feature — a single-operator local portfolio tool whose primary demo runs on
synthetic data (`specs/001-cost-usage-monitor/spec.md`) — cannot meet both of these as
written without disproportionate scope. Two deviations were identified during planning.
This ADR is the "explicit ADR referencing Principle IV" that Section 2 calls for, and it
also records the Principle IV access-control deferral.

## Deviation 1 — new stored field: `source_identity`

### Decision

`UsageRecord` gains a nullable `source_identity` column (the Anthropic **API key id** or
**workspace id** as returned by the Usage & Cost Admin API), and a new
`AttributionMapEntry` table stores an operator-maintained mapping
`source_identity → member_id`. `source_identity` is populated in **live mode only** and
is `NULL` for demo records.

### Why it is needed

- **Per-person attribution (Clarification Q1).** The Admin API buckets usage by API key /
  workspace, not by person. Mapping that provider-side identity to a `Member` is the only
  way live mode can deliver the per-person trends the product exists for.
- **Idempotent re-ingestion (FR-007).** The live idempotency key is
  `(source, source_identity, model, date)`; without the stored identity, re-running an
  ingest cannot deduplicate.
- **Traceable "unattributed" usage (FR-008b, Principle V).** Usage from an unmapped key
  must be shown under a reserved `__unattributed__` member *and* remain traceable to the
  originating key so the operator can fix the mapping and re-resolve.

### Why the simpler alternative was rejected

Storing only the resolved `member_id` loses all three capabilities above: unattributed
usage could not be displayed or later re-attributed, and records could not be traced to
their provider bucket for the Principle V audit trail.

### Scope and mitigations

- `source_identity` is **provider-side account metadata**. It contains no prompt,
  completion, code, or file content and no personal data beyond an opaque account
  identifier.
- It is covered by live-mode encryption at rest (FR-032a) and by the same
  operator-configurable retention as the rest of `UsageRecord` (FR-032, default 90 days).
- It never appears in logs (structlog redaction, FR-036) and is never transmitted to a
  third party (no external delivery in v1).
- Demo mode does not use or store it.

## Deviation 2 — no authentication, RBAC, access logging, or engineer self-service view

### Decision

v1 ships as a **single-operator tool** with no end-user authentication, no role model, no
access-grant logging, and no engineer-facing "view my own usage" surface. Per-member
breakdowns are available to whoever runs the tool. These capabilities are deferred to v2
(recorded in `spec.md` → Out of Scope and Assumptions).

### Why it is needed

- The primary artifact is a portfolio demo that must run from a fresh clone in under five
  minutes with **zero API keys** (SC-001, FR-037). Introducing login, sessions, a role
  store, and an audit-log store directly fights that goal.
- In v1 the tool is run locally by one person, most often against the **synthetic** demo
  dataset (fake team members), so the surveillance risk Principle IV guards against is
  minimal in practice.

### Why the simpler alternative was rejected

A minimal admin/engineer role split still requires user identity, session handling, and a
persisted access log — substantial machinery for a tool that, in v1, one person runs
locally. It would not be exercised by the demo and would measurably slow the quickstart.

### Scope and mitigations that remain in force

- **Data minimization is fully enforced**: no prompt/completion/code/file content is ever
  stored (FR-031); only the enumerated metadata (plus `source_identity`, Deviation 1).
- **Team-level aggregation is the default view** (FR-033); per-member is a drill-down.
- **Encryption at rest** for real data (live mode, FR-032a) and **configurable retention
  with hard delete** (FR-032) still apply.
- **Structured audit trail** linking every spike flag and recommendation to its source
  records and rule version still applies (FR-036, SC-008).

## Consequences

- **Positive**: the 5-minute zero-key quickstart is preserved; live per-person
  attribution, idempotent ingest, and unattributed-usage traceability all work; the data
  model stays provider-agnostic for the v2 multi-provider goal.
- **Negative / accepted risk**: a real multi-user deployment of v1 would expose
  per-member data to any operator without a role check or access log. This is acceptable
  only for the single-operator/local and demo use described in the spec.
- **Follow-up for v2** (tracked in `docs/v2-roadmap.md`):
  1. Introduce authentication + an access-control role gating per-member views, with
     access-grant logging (Principle IV).
  2. Add an engineer self-service view of their own usage (Principle IV).
  3. Revisit whether `source_identity` should be hashed or tokenized once a real identity
     provider is in place.
- **Constitution bookkeeping**: this ADR satisfies the Section 2 requirement for an
  explicit ADR referencing Principle IV. No constitution amendment is made. If a future
  change stores an additional attributed field or weakens a Principle IV mitigation
  listed above, that requires its own ADR or an amendment.
