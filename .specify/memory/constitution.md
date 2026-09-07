<!--
Sync Impact Report
- Version change: (unversioned template) -> 1.0.0
- Rationale: Initial ratification of the project constitution. MAJOR bump from an
  un-adopted template to a governing v1.0.0 baseline.
- Principles defined:
  - I. Accuracy Over Estimation
  - II. Explainable, Rule-Based Recommendations
  - III. Test-First for Money-Path Logic (NON-NEGOTIABLE)
  - IV. Privacy & Proportionality
  - V. Deterministic & Observable Reports
- Added sections:
  - Data Handling & Security Constraints (Section 2)
  - Development Workflow & Quality Gates (Section 3)
  - Governance
- Removed sections: none
- Templates / files reviewed for consistency:
  - .specify/templates/plan-template.md (Constitution Check gate) - consistent, no edit required
  - .specify/templates/spec-template.md - consistent, no edit required
  - .specify/templates/tasks-template.md - consistent, no edit required
- Deferred TODOs: none
-->

# Token Pulse Constitution

## Core Principles

### I. Accuracy Over Estimation

Every token count, model attribution, and dollar figure Token Pulse reports MUST trace
back to an authoritative source record (Claude Code usage logs or the provider usage/billing
API). The product exists so engineering managers can make budget decisions; a wrong number is
worse than a missing one.

- Reported spend MUST reconcile to the provider's billed amount within a documented tolerance;
  unreconciled deltas MUST be surfaced, not hidden.
- Any value that is derived, projected, or approximated MUST be visibly labeled as an estimate
  and MUST carry its calculation basis (pricing table version, assumptions, date range).
- Pricing tables and model rate cards MUST be versioned and dated. Recomputing a past report
  MUST use the rates in effect for that period, not today's rates.
- If source data is incomplete for a requested window, the report MUST say so explicitly and
  MUST NOT silently backfill with guesses.

Rationale: Managers act on these numbers with real money; silent estimation destroys trust and
is not recoverable once discovered.

### II. Explainable, Rule-Based Recommendations

Cost-reduction recommendations (model selection, prompt caching, Batch API, and any future
levers) MUST be produced by explicit, inspectable rules. Opaque or non-deterministic scoring is
prohibited for anything presented as a recommendation.

- Each recommendation MUST state: the rule that fired, the observed data that triggered it, the
  concrete suggested change, and the projected saving with its calculation.
- Rules MUST live in a single, reviewable catalog with a stable identifier and a version.
- A recommendation MUST be reproducible: given the same input dataset and rule version, the
  system produces the identical recommendation and projected saving.
- Projected savings MUST be conservative and MUST document their assumptions; a rule that cannot
  bound its estimate MUST NOT claim a dollar figure.

Rationale: A recommendation a manager cannot explain to their team or their finance partner will
not be adopted, and an unexplained wrong recommendation is a liability.

### III. Test-First for Money-Path Logic (NON-NEGOTIABLE)

Any code that computes cost, aggregates usage, detects spending spikes, or evaluates a
recommendation rule is "money-path" logic. Money-path logic MUST be developed test-first.

- The order is: write the test, confirm it fails, then implement. This is enforced in review.
- Every cost calculation, spike-detection threshold, aggregation boundary (per member, per team,
  per model, per time window), and recommendation rule MUST have unit tests covering normal,
  boundary, and empty/partial-data cases.
- Bug fixes in money-path logic MUST add a regression test that fails before the fix.
- Refactors of money-path logic MUST hold existing tests green with no assertion changes unless
  the change in behavior is documented in the PR.

Rationale: Errors here are financial and are trusted by default; tests are the only durable
guard, and writing them first is what keeps coverage honest.

### IV. Privacy & Proportionality

Token Pulse monitors individual engineers. Data collection MUST be the minimum needed to report
spend and generate recommendations, and MUST be proportionate to that purpose.

- Prompt content, completion content, file contents, and code MUST NOT be stored. Only metadata
  is retained: token counts, model, cache hit/miss, request type, timestamps, computed cost, and
  a member identifier.
- Reporting defaults to team-level aggregation. Per-member breakdowns are gated behind an
  explicit access-control role.
- Member-attributed data MUST be encrypted at rest and MUST have a configurable retention period
  with a documented default; data past retention MUST be deleted, not merely hidden.
- Monitored engineers MUST be able to view their own usage data.
- Exports and integrations MUST NOT transmit member-attributed data to third parties without an
  explicit, configured opt-in.

Rationale: A tool that surveils people loses its team's cooperation fast; minimal, transparent,
access-controlled data is the only sustainable footing.

### V. Deterministic & Observable Reports

Given the same input data and the same configuration versions (pricing table, rule catalog),
Token Pulse MUST produce byte-identical reports. Its decisions MUST be auditable after the fact.

- Report generation MUST be a pure function of its inputs plus pinned config versions; wall-clock
  time, iteration order, and locale MUST NOT change output.
- Every spike flag and every recommendation MUST be traceable in structured logs to the records
  and rule version that produced it.
- Logs MUST be structured (machine-parseable) and MUST NOT contain prompt/completion content or
  secrets.
- Each report MUST record the pricing-table version, rule-catalog version, source-data window,
  and tool version used to produce it.

Rationale: Managers will challenge surprising numbers; reproducibility and an audit trail turn
those challenges into a lookup instead of an investigation.

## Data Handling & Security Constraints

- Storable fields are restricted to: member identifier, team identifier, timestamp, model,
  request/interaction type, input tokens, output tokens, cache-read tokens, cache-write tokens,
  computed cost, and the pricing-table version used. Adding any new stored field REQUIRES a
  constitution amendment or an explicit ADR referencing Principle IV.
- Secrets (provider API keys, tokens) MUST be sourced from environment or a secrets manager,
  never committed, never logged.
- Member-attributed data at rest MUST be encrypted; transport MUST be TLS.
- Retention has a documented default (recommended: 90 days for raw per-request metadata,
  longer only for pre-aggregated team totals) and MUST be operator-configurable.
- Access to per-member views MUST be role-gated and access grants MUST be logged.
- Third-party delivery (Slack, email, BI exports) MUST default to aggregated data; per-member
  detail leaves the system only via explicit configuration.

## Development Workflow & Quality Gates

- All changes land via pull request with at least one reviewer.
- CI MUST pass before merge: unit tests, linting, and type checks where the language supports
  them.
- Money-path changes (see Principle III) additionally REQUIRE: test-first evidence in the PR,
  and reviewer sign-off specifically acknowledging the calculation change.
- Changes to the pricing table or the rule catalog REQUIRE: a version bump on that artifact, a
  changelog entry, and tests covering the changed entries.
- Changes that add or alter a stored data field REQUIRE explicit reference to Principle IV and
  Section "Data Handling & Security Constraints" in the PR description.
- User-facing report format changes MUST include a determinism test (same input -> same output).

## Governance

This constitution supersedes other process documents where they conflict. It governs how Token
Pulse is built and what guarantees it makes to the teams it monitors.

- **Amendments**: Proposed via PR that modifies this file, including an updated Sync Impact
  Report and a rationale. Merge REQUIRES approval from the project maintainer(s). Amendments that
  weaken Principle III or Principle IV REQUIRE an explicit migration and communication plan.
- **Versioning policy**: This document is versioned with semantic versioning.
  - MAJOR: removal or backward-incompatible redefinition of a principle or governance rule.
  - MINOR: a new principle or section, or materially expanded normative guidance.
  - PATCH: clarifications, wording, and non-semantic refinements.
- **Compliance review**: Every PR review MUST verify the change complies with the applicable
  principles. Complexity or deviation MUST be justified in the PR and is presumed rejected if
  unjustified. A full constitution compliance pass SHOULD occur at each release.
- **Runtime guidance**: Agent and contributor runtime guidance lives in repository docs and
  MUST defer to this constitution on any conflict.

**Version**: 1.0.0 | **Ratified**: 2026-09-07 | **Last Amended**: 2026-09-07
