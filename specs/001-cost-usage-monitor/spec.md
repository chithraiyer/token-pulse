# Feature Specification: TokenPulse — Claude Code Cost & Usage Monitor (v1)

**Feature Branch**: `001-cost-usage-monitor`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "TokenPulse — Claude Code Cost & Usage Monitor (v1 Spec). A lightweight tool that lets an engineering manager see per-person Claude Code token/cost trends, automatically flags usage spikes, and produces plain-English rule-based optimization recommendations. Two data source modes: Live (Anthropic Usage & Cost Admin API) and Demo (synthetic dataset generator that runs with zero API keys). v1 also ships a written v2 roadmap but does not build it."

## Clarifications

### Session 2026-09-07

- Q: In live mode, how does TokenPulse attribute usage to an individual team member given the Admin API buckets by API key / workspace? → A: Operator maintains a config mapping (API key / workspace → team member); ingestion joins live records to a member via that map, and unmapped keys surface as "unattributed".
- Q: Should recommendation-rule numeric thresholds be fixed in the spec now or deferred to the rule catalog? → A: Spec fixes a default value per rule; those defaults live in the versioned, operator-tunable rule catalog, and changing one bumps the catalog version.
- Q: Does v1 need encryption at rest for member-attributed data? → A: Yes whenever real member-attributed data is stored (live mode); demo mode, which holds only synthetic data, may store plaintext.
- Q: How is spike severity classified? → A: Four bands (Low/Moderate/High/Critical) by the actual-to-baseline ratio relative to the configured threshold T, with absolute-dollar excess floors that demote a band when the day's excess is small.
- Q: How many days of history should the demo dataset generate by default? → A: 90 days (matches the default retention window; ~12 weeks of trend, room for 2–3 separated spikes, covers every rolling-window rule).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Zero-setup demo mode (Priority: P1)

An evaluator (hiring manager, teammate, or the author showing a portfolio piece) clones the repository, follows the quickstart, and within a few minutes has a fully populated dashboard driven entirely by synthetic data — no Anthropic account, organization access, or API key required.

**Why this priority**: The portfolio demonstration runs entirely on this dataset. Without it, nobody without privileged Anthropic credentials can see the product work at all, so it is the foundation every other story is shown on.

**Independent Test**: From a fresh clone with no environment secrets set, follow the README quickstart. Confirm the application starts in demo mode and the dashboard shows 5–8 team members with 90 days of daily usage history and visible spike periods.

**Acceptance Scenarios**:

1. **Given** a fresh clone with no API keys configured, **When** the operator runs the quickstart, **Then** the application starts in demo mode and loads a synthetic dataset of 5–8 team members with 90 days of daily history.
2. **Given** demo mode is active, **When** the operator views any screen, **Then** a clear "synthetic demo data" indicator is visible.
3. **Given** the default demo seed, **When** the dataset is generated twice, **Then** the two datasets are byte-identical.
4. **Given** the generated demo dataset, **When** the operator inspects it, **Then** it contains 2–3 deliberately injected spike periods (e.g. one member running a premium model in a loop for a week) with otherwise natural day-to-day variance.

---

### User Story 2 - Usage & cost trend dashboard (Priority: P1)

An engineering manager opens the dashboard and sees team-level cost and token-usage trends over time, then drills into a specific engineer and model to understand the shape of that usage.

**Why this priority**: This is the core "pulse". The primary value proposition is seeing at a glance whether usage is trending normally or climbing, per person and per team, without manually parsing console exports.

**Independent Test**: With any dataset loaded (demo or live), open the dashboard, select a date range, and confirm that team-level and per-member trend lines render with totals and period-over-period change.

**Acceptance Scenarios**:

1. **Given** a loaded dataset, **When** the manager opens the dashboard, **Then** team-level cost and token trends are shown for a default recent range.
2. **Given** the dashboard is open, **When** the manager selects a custom date range, **Then** all trend lines, totals, and change indicators update to that range.
3. **Given** a team trend view, **When** the manager selects a single team member, **Then** that member's cost and token trends broken out by model are shown.
4. **Given** a member has flagged spike days within the selected range, **When** their trend is displayed, **Then** those days are visually marked on the line.
5. **Given** a selected range, **When** totals are displayed, **Then** the team total equals the sum of the per-member totals for that range.

---

### User Story 3 - Automatic spike detection (Priority: P2)

Without configuring any thresholds, the manager sees which engineer-days are abnormal, with the baseline and the magnitude of the deviation shown so that each flag is self-explanatory.

**Why this priority**: Turns raw trends into an actionable signal and answers "should I be worried?" automatically. Valuable on top of Story 2, but Story 2 alone is already a usable MVP.

**Independent Test**: Load the demo dataset, open the spikes view, and confirm every injected spike is listed with baseline, actual, deviation, and severity, while no non-spike day is listed.

**Acceptance Scenarios**:

1. **Given** a member with at least 7 days of prior history, **When** a day's cost exceeds 2.5× their rolling 7-day average cost, **Then** that day is flagged as a spike.
2. **Given** a spike is flagged, **When** it is displayed, **Then** it shows the baseline average, the actual value, the deviation, and a severity classification.
3. **Given** a member with fewer than 7 days of prior history in range, **When** the spikes view is shown, **Then** that member is marked "insufficient history" and is not flagged.
4. **Given** the configured spike multiple is changed, **When** detection re-runs, **Then** flags are recomputed against the new multiple.
5. **Given** the same dataset and configuration, **When** detection runs twice, **Then** the resulting set of flags is identical.

---

### User Story 4 - Rule-based optimization recommendations (Priority: P2)

For each notable usage pattern, the manager gets a plain-English suggestion, a conservative dollar estimate of the potential saving, and the reasoning that produced it — something they can forward to the engineer or their finance partner.

**Why this priority**: Makes the tool prescriptive rather than merely descriptive, which is the main differentiator. Depends on usage data being present but not on live ingestion.

**Independent Test**: Load the demo dataset (which contains a premium-model-in-a-loop pattern, a low-cache-hit pattern, and a high-volume pattern). Open recommendations and confirm each expected rule fires with its rule identifier, the observed data, the suggested change, and the savings calculation.

**Acceptance Scenarios**:

1. **Given** sustained high premium-model (Opus) usage on lightweight requests, **When** recommendations are generated, **Then** a "shift this workload to a smaller model (Sonnet/Haiku)" recommendation appears with an estimated saving and its calculation.
2. **Given** sustained high uncached input-token volume with a low cache-hit ratio, **When** recommendations are generated, **Then** an "enable prompt caching" recommendation appears with an estimated saving.
3. **Given** a high-volume, non-urgent usage pattern, **When** recommendations are generated, **Then** a "use the Batch API" recommendation appears, citing the 50% batch-discount assumption.
4. **Given** a sudden shift in a team's model mix (e.g. from Sonnet to Opus), **When** recommendations are generated, **Then** a "review model mix" item appears flagged for human judgement with no dollar figure attached.
5. **Given** any recommendation, **When** it is displayed, **Then** it names the rule identifier, the rule-catalog version, the observed data that triggered it, and — if a dollar figure is shown — the savings formula and its assumptions.
6. **Given** the same dataset and rule-catalog version, **When** recommendations are generated twice, **Then** the recommendations and projected savings are identical.

---

### User Story 5 - Live Anthropic usage ingestion (Priority: P3)

The manager supplies an Admin API key, switches the tool to live mode, and it pulls real day-bucketed usage — broken out by workspace / API key and model — into the same dashboard, spike, and recommendation views.

**Why this priority**: Makes the tool real for an actual team, but the portfolio demonstration does not depend on it and it requires a privileged organization credential that most evaluators will not have.

**Independent Test**: With a valid Admin API key and live mode enabled, run ingestion for a date range and confirm usage records are created per day and model and then appear in the dashboard in the same form as demo data.

**Acceptance Scenarios**:

1. **Given** a valid Admin API key and live mode enabled, **When** ingestion runs for a date range, **Then** daily usage records per workspace / API key and model are stored and joined to a team member via the operator-maintained attribution mapping.
2. **Given** live ingestion has run, **When** the dashboard is opened, **Then** live data populates the same trend, spike, and recommendation views as demo data.
3. **Given** ingestion is re-run for an already-ingested date range, **When** it completes, **Then** no duplicate records are created.
4. **Given** the API returns an incomplete result for part of the requested range, **When** ingestion completes, **Then** the missing days are reported as gaps and are not fabricated.
5. **Given** a model in the usage data is absent from the pricing table, **When** cost is computed, **Then** that cost is marked as an unpriced estimate and surfaced rather than hidden.
6. **Given** usage from an API key / workspace that is not in the attribution mapping, **When** ingestion runs, **Then** that usage is stored and shown under an "unattributed" pseudo-member, not discarded.

---

### Edge Cases

- **Cold start**: A member with fewer than 7 days of history has no baseline; those days are shown as "insufficient history" and never flagged as spikes.
- **Partial requested window**: A requested date range that extends beyond available data shows the covered window and marks missing days as incomplete; no values are backfilled.
- **Failed / partial live page**: A live API page that fails or returns partial data produces a reported gap for the affected days, not fabricated usage.
- **Zero-usage days**: A day with genuine zero usage counts as `0` in the baseline; it is distinct from a missing day.
- **Spike inside insufficient history**: A day that would qualify as a spike but falls within a member's first 7 days is not flagged; the member is listed under "insufficient history".
- **Consecutive spikes**: When several high days fall inside one rolling window, later days' baselines rise; a sustained spike may "normalize" after roughly a week. This is accepted and documented behaviour for v1.
- **Unknown model**: A model present in usage data but absent from the active pricing table yields a cost explicitly labeled "unpriced estimate", surfaced in the UI.
- **Day boundary**: All daily bucketing uses UTC calendar days regardless of viewer locale.
- **Retention boundary**: Records that reach exactly the configured retention age are deleted on the next retention pass.
- **Extreme single-day usage**: A day that dwarfs the baseline (e.g. 50×) is classified Critical when its absolute excess also clears the Critical dollar floor, and otherwise into the highest band its dollar excess supports — computed without error.
- **Tiny-dollar spike**: A day that is many times the baseline but whose baseline (and therefore excess) is a few cents stays at Low/Moderate because the High/Critical dollar floors are not met.
- **Demo reproducibility**: Regenerating the demo dataset with the same seed produces an identical dataset; changing the seed produces a different but structurally similar dataset.

## Requirements *(mandatory)*

### Functional Requirements

#### Ingestion & data source

- **FR-001**: System MUST ingest daily token usage aggregated per team member and per model, capturing input tokens, output tokens, and cached tokens for each member/model/day.
- **FR-002**: System MUST support two selectable ingestion modes — **Live** (Anthropic Usage & Cost Admin API, day-bucketed, broken out by workspace / API key and model) and **Demo** (synthetic dataset generator) — chosen via a single configuration value.
- **FR-003**: Demo mode MUST operate with zero API keys or external credentials and MUST generate 5–8 synthetic team members with 90 days (configurable) of daily usage history exhibiting realistic day-to-day variance, 2–3 deliberately injected and well-separated spike scenarios, and at least one team-level model-mix shift spanning two consecutive 7-day windows.
- **FR-004**: System MUST clearly indicate in both the user interface and the README when it is running on synthetic demo data.
- **FR-005**: Live mode MUST authenticate using an Admin API key sourced from environment variables or a secrets manager; the key MUST NOT be committed to the repository or written to logs.
- **FR-006**: System MUST NOT silently backfill missing days with estimated values; an incomplete source window MUST be reported as incomplete in any affected report or view.
- **FR-007**: Ingestion MUST be idempotent — re-running ingestion for a date range already ingested MUST NOT create duplicate usage records.
- **FR-008**: The data model and ingestion layer MUST be provider-agnostic so that additional providers (e.g. OpenAI, Gemini) can be added in a later version without changing the stored schema. Only Anthropic is wired up in v1.
- **FR-008a**: Live mode MUST attribute usage to a team member via an operator-maintained mapping of source identity (API key and/or workspace) → team member. Ingestion MUST join each live usage record to a member through this mapping.
- **FR-008b**: Usage from a source identity not present in the mapping MUST be retained and surfaced as "unattributed" (its own pseudo-member) rather than dropped or silently merged into another member.

#### Cost & pricing

- **FR-009**: System MUST record a cost in USD for every usage record. In live mode the cost MUST derive from the provider's cost data; in demo mode the cost MUST be computed from a bundled, versioned, dated pricing table.
- **FR-010**: Every stored usage record MUST carry the identifier/version of the pricing table used to derive its cost.
- **FR-011**: Any derived, projected, or approximated dollar figure MUST be visibly labeled as an estimate and MUST carry its calculation basis (pricing-table version, date range, and assumptions).
- **FR-012**: Recomputing a report for a past period MUST use the pricing rates in effect for that period, not the current rates.

#### Trends & dashboard

- **FR-013**: System MUST display cost and token-usage trends over an operator-selectable time range, showing team-level trends by default.
- **FR-014**: System MUST allow drill-down from team level to per-member and per-model trend views.
- **FR-015**: Trend views MUST render as time-series lines with spike days visually marked.
- **FR-016**: System MUST show, per member and per team, totals and period-over-period change for the selected range.
- **FR-017**: For any selected range, the displayed team total MUST equal the sum of the per-member totals for that range.

#### Spike detection

- **FR-018**: System MUST compute each member's baseline as the rolling 7-day average of their daily cost.
- **FR-019**: System MUST flag any day where a member's actual daily cost exceeds their baseline by a configurable multiple, defaulting to 2.5×.
- **FR-020**: Each spike flag MUST record the baseline average, the actual value, the deviation, and a severity classification.
- **FR-020a**: Severity MUST be one of Low / Moderate / High / Critical, derived deterministically. Let `T` be the configured spike multiple (default 2.5×), `r` the actual-to-baseline ratio, and `E` the actual-minus-baseline cost in USD. The ratio band is: Low = `T ≤ r < 2T`, Moderate = `2T ≤ r < 3T`, High = `3T ≤ r < 5T`, Critical = `r ≥ 5T`. A dollar floor then applies: Critical requires `E ≥ $200` and High requires `E ≥ $50`; if the floor is unmet, the band drops one level and the check repeats until the floor is satisfied or Low is reached. Both the ratio band and the dollar floors MUST be operator-tunable parameters in the rule catalog (per FR-029a).
- **FR-021**: System MUST NOT flag spikes for a member with fewer than 7 days of prior history in the analysed window; such members MUST be shown as "insufficient history".
- **FR-022**: Spike detection MUST be deterministic — identical input data and configuration produce an identical set of flags regardless of processing order or wall-clock time.
- **FR-023**: The spike multiple MUST be operator-configurable without code changes.

#### Recommendations

- **FR-024**: System MUST generate plain-English, rule-based optimization recommendations from an inspectable rule catalog. No machine-learning or non-deterministic scoring is permitted for anything presented as a recommendation.
- **FR-025**: The rule catalog MUST be versioned, with each rule carrying a stable identifier.
- **FR-026**: Each recommendation MUST state the rule that fired, the observed data that triggered it, the concrete suggested change, and — where a dollar figure is claimed — the estimated USD saving together with its calculation and assumptions.
- **FR-027**: Estimated savings MUST be conservative and MUST document their assumptions; a rule that cannot bound its estimate MUST NOT state a dollar figure.
- **FR-028**: Recommendations MUST be reproducible — the same input dataset and rule-catalog version yield identical recommendations and projected savings.
- **FR-029**: v1 MUST implement at least these rules, all using metadata-only signals (no prompt or completion content is inspected or stored). Each rule's trigger uses a trailing 7-day window per subject and the stated default threshold:
  - **(a)** **High premium-model use on lightweight work** — Opus is ≥ 60% of the member's trailing-7-day cost AND the member's mean Opus output:input token ratio is ≤ 0.2 → suggest moving that workload class to Sonnet or Haiku. Saving = trailing-window Opus cost minus the same token volume repriced at Sonnet rates.
  - **(b)** **Low cache utilisation** — cache-read tokens are < 10% of total input tokens over the trailing 7 days AND trailing-7-day input tokens ≥ 1,000,000 → estimate the saving from enabling prompt caching.
  - **(c)** **Steady high-volume workload** — trailing-7-day mean daily tokens ≥ 5,000,000 with day-to-day coefficient of variation ≤ 0.3 (i.e. steady, batch-like, not bursty) → suggest the Batch API, citing the standard 50% discount.
  - **(d)** **Model-mix shift** — a team's Opus share of cost rises by ≥ 25 percentage points from the prior 7-day window to the current one → flag for human review with no dollar figure.
- **FR-029a**: The default thresholds in FR-029 (and the spike multiple in FR-019) MUST be stored as versioned, operator-tunable parameters in the rule catalog. Changing any threshold MUST bump the rule-catalog version, and every recommendation MUST report the threshold value that was in effect.

#### Roadmap (documented, not built in v1)

- **FR-030**: The repository MUST include a written v2 roadmap covering at minimum: OpenAI + Gemini usage ingestion on the same data model; Slack alerts on spike detection; a weekly digest email with a narrative summary; and team-level budget thresholds and forecasting. v1 MUST NOT implement any of these.

#### Privacy, retention & observability

- **FR-031**: System MUST NOT store prompt content, completion content, code, or file contents. Only usage metadata is retained: member identifier, team identifier, date/timestamp, model, request/interaction type, input tokens, output tokens, cache-read tokens, cache-write tokens, computed cost, and pricing-table version.
- **FR-032**: Per-member usage metadata MUST have an operator-configurable retention period with a documented default of 90 days; data older than the retention period MUST be deleted, not merely hidden.
- **FR-032a**: When running in live mode (real member-attributed data), the persistence store MUST be encrypted at rest. Demo mode, which stores only synthetic data, MAY run without encryption so the zero-setup quickstart has no key step.
- **FR-033**: Reporting MUST default to team-level aggregation, with per-member breakdowns available to the operator.
- **FR-034**: Given identical input data and pinned configuration (pricing-table version and rule-catalog version), the system MUST produce identical reports, spike flags, and recommendations.
- **FR-035**: Each generated report MUST record the pricing-table version, rule-catalog version, source-data window, and tool version used to produce it.
- **FR-036**: System MUST emit structured, machine-parseable logs that trace each spike flag and each recommendation back to the underlying daily records and the rule version that produced it, containing no prompt/completion content and no secrets.

#### Setup

- **FR-037**: The application MUST run locally from a fresh clone in demo mode within 5 minutes by following the README quickstart, with no API keys required.

### Key Entities *(include if feature involves data)*

- **User (team member)**: A monitored engineer. Attributes: identifier, display name, team identifier. A reserved "unattributed" pseudo-member holds live usage whose source identity is not mapped.
- **AttributionMap**: An operator-maintained set of entries mapping a source identity (API key and/or workspace) to a team member. Used only in live mode. Attributes: source identity, member reference.
- **UsageRecord**: One member's usage of one model on one day. Attributes: member reference, source identity (API key / workspace, live mode only), date (UTC day), model, input tokens, output tokens, cached tokens (read / write), computed cost (USD), data source (live | demo), pricing-table version. Provider-agnostic in shape.
- **PricingTable**: A versioned, dated set of per-model rates (input, output, cache-read, cache-write) used to compute cost for a period. Attributes: version identifier, effective date range, per-model rates.
- **Spike**: An abnormal member-day. Attributes: member reference, date, baseline average, actual value, deviation, severity classification (Low / Moderate / High / Critical), and the spike-multiple and dollar-floor parameters in effect.
- **Recommendation**: A rule-based optimization suggestion. Attributes: subject (member or team) reference, rule identifier, rule-catalog version, summary of triggering data, plain-English message, estimated USD saving (nullable), assumptions/calculation note.
- **RuleCatalog**: The versioned collection of recommendation rules. Attributes: catalog version, and per rule: stable identifier, description, triggering condition, savings-calculation method.
- **ReportRun**: Metadata describing one generation of reports. Attributes: generation timestamp, source-data window, pricing-table version, rule-catalog version, tool version, data-source mode.

## Out of Scope (v1)

- Real-time or streaming ingestion — daily batch ingestion is sufficient.
- Multi-provider ingestion (OpenAI, Gemini) — the data model must allow it, but only Anthropic is wired up.
- Slack or email alerting — captured as a v2 roadmap item.
- Machine-learning or statistical anomaly detection beyond the fixed rolling-average rule.
- End-user authentication and role-based access control, and engineer self-service views — v1 is a single-operator tool (see Assumptions); deferred to v2.
- Hosted / production deployment as an acceptance requirement — local execution is the target for the portfolio version.
- Non-USD currencies.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can clone the repository and see a populated dashboard in demo mode in under 5 minutes, without providing any API key.
- **SC-002**: The dashboard displays per-member and per-team cost and token trends for any date range within the ingested data, with team totals equal to the sum of member totals for that range.
- **SC-003**: On the demo dataset, the tool flags every deliberately injected spike and flags no non-spike day.
- **SC-004**: 100% of displayed recommendations show their triggering rule identifier, the observed data, and — wherever a dollar figure is claimed — the savings calculation, verifiable by inspection.
- **SC-005**: Running report generation twice on the same input data and configuration produces identical totals, spike flags, and recommendations.
- **SC-006**: Switching from demo mode to live mode requires only supplying an Admin API key and changing one configuration value — no code changes.
- **SC-007**: No stored record contains prompt or completion text, verifiable by inspecting the data-store schema and its contents.
- **SC-007a**: In live mode, the persistence store is encrypted at rest — verifiable by inspecting the store file without the key and finding no readable member identifiers or usage values.
- **SC-008**: A reviewer can trace any single spike flag or recommendation shown in the interface back to the specific daily records that produced it, using the structured logs, in under 2 minutes.
- **SC-009**: The README contains a problem statement, an architecture diagram, a "how I used AI to build this" section, and 2–3 dashboard screenshots or a GIF.
- **SC-010**: The demo dataset generator produces an identical dataset on repeated runs with the same seed.

## Assumptions

- **Single-operator tool**: v1 runs locally for one engineering manager. There is no end-user authentication or role-based access control in v1; per-member views are available to that operator. Multi-user RBAC and engineer self-service views are deferred to v2 (noted against constitution Principle IV). Data minimization (no prompt/completion/code content stored) and team-level-first presentation are still enforced in v1.
- **"Spend"** for baseline and spike comparison means computed cost in USD, not raw token count.
- **Daily buckets** use UTC calendar days.
- **Cost source**: in live mode, cost derives from Anthropic's cost reporting; in demo mode, cost is computed from a versioned, dated pricing table bundled in the repository. Both are labeled with the pricing-table version.
- **Metadata-only recommendation signals**: "lightweight request", "low cache utilisation", "steady high volume", and "model-mix shift" are approximated from metadata only — token ratios, uncached-input volume, cache-hit ratio, daily-volume variance, and model cost shares (see FR-029 for the default thresholds). No prompt content is inspected or stored.
- **Demo seed**: the synthetic generator is deterministically seeded and ships with a fixed default seed so the portfolio demo is reproducible.
- **Demo history length**: default 90 days of daily history (configurable), chosen to match the retention window and to give every rolling-window rule enough data.
- **Baseline definition**: the rolling 7-day baseline uses the raw trailing 7 calendar days of the member's cost, including any prior flagged spike days. This is accepted for v1 explainability.
- **Spike multiple**: default 2.5×, operator-configurable via configuration.
- **Retention**: default 90 days for per-member daily metadata, operator-configurable.
- **Currency**: USD only.
- **Team membership** is treated as static within a reporting run; mid-period team changes are not modeled in v1.
- **Batch API rule** assumes the standard 50% batch discount versus standard pricing for the same model and token volume.
- **Presentation**: trends are delivered as a web dashboard viewed in a modern browser.
- **v2 roadmap** is a documentation deliverable in the repository, not a product feature.

### Dependencies

- Live mode depends on access to the Anthropic Usage & Cost Admin API endpoint for message usage and a valid Admin API key with organization-level visibility.
- Live mode assumes the operator can supply an accurate API key / workspace → team member mapping; accuracy of per-person live attribution is only as good as that mapping. A roughly one-key-per-engineer setup is assumed.
- Requires a bundled, maintained pricing table covering the Anthropic models that appear in usage data.
- Requires a local persistence store for usage metadata, spikes, recommendations, and run metadata.
