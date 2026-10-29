# FieldShift BD — Adaptive Decisions and Confirmed Plan B

> **Consolidated authority — 2026-10-29:** Read [FINAL_IMPLEMENTATION_PLAN.md](FINAL_IMPLEMENTATION_PLAN.md) first. This document remains a detailed source specification; the final plan reconciles all four plans, foundation readiness and six-person work allocation. Original source snapshots are preserved there from commit `336bf6c`.

**Revision:** 2026-10-29, Asia/Dhaka. **Status:** required planned extension, not an implemented feature. The project owner accepted the three linked additions after the competitor review. This document extends the [challenge delivery plan](2026-10-29-nasa-planting-window-and-rotation.md), [canonical plan](../../plan.md) and [voice plan](2026-10-06-voice-first-bangla.md). All organizer/final-statement requirements remain required. Read the complete plan set through the [index](README.md).

## 1. Accepted scope and completion order

Deliver three connected behaviors after the required organizer and rotation flow works:

| ID | Behavior | Additional result |
|---|---|---|
| A01 | Ask the field question that changes the decision | One useful farmer-observable question selected by deterministic comparison of supported options under unknown inputs |
| A02 | Rotation robustness envelope | Explicit tested delay/water/heat scenarios, feasible ranges and binding constraints for the current rotation and supported alternatives |
| A03 | Conditional Plan B | A saved, versioned contingency policy; dated evidence produces a proposed plan/task difference; a farmer confirmation applies the current supported change once |

These are additions to the three-rotation comparison, explanation and confirmed M2-to-M3 lifecycle. They do not replace onset/GDD/statistics, NASA data, maps, offline behavior, deployment or submission work. The organizer's timed 48-hour milestone stays intact; this extension has no invented delivery-time guarantee.

Multi-farm rice-floor allocation, shared-pump scheduling, a general minimum-change optimizer and outcome-study tooling remain research suggestions outside this accepted three-feature increment. Do not silently add them as release gates. Simple constraint explanations belong to A01/A02 and are included.

Core logic uses Python, existing FastAPI/PostgreSQL, pinned local agronomy and M4 evidence. No purchased LLM, speech or SMS service is required. Existing optional AI may paraphrase a validated result without changing facts. Production hosting/device costs follow the parent plan.

## 2. Current baseline and module ownership

Planning baseline: commit `1077a06`, recheck before implementation. M2 currently derives persisted recommendation context from saved M1 data; its routes live under `/advisor`. M2 owns season lifecycle/plan definitions. M3 owns operational tasks and current stage. `Season` permits only one active season per farmland. M2 services currently perform internal commits; an atomic confirmed multi-module update cannot be achieved by merely calling today's independent HTTP endpoints in sequence.

| Owner | Added responsibility | Invariant |
|---|---|---|
| M1 | Confirmed observable answers and their provenance; read-only profile snapshot for M2 | Hypothetical scenario overrides never overwrite the saved farm; unknown, denied and zero differ |
| M2 | A01 question selection, A02 feasibility analysis, A03 contingency evaluation; owns analytical result/policy records | Returns calculations and plan/task definitions, never mutates M3 operational tasks or current stage |
| M4 | Typed dated/QA-checked evidence and evidence freshness rules | Observations, forecasts, projections and what-if inputs remain distinguishable; cannot execute a crop switch |
| M3 | Current operational state; apply allowed task differences and preserve history | No automatic completed-task overwrite; maintain farm/season/task constraints and one-time effects |
| M5 | Display/speak questions, evidence and proposals; existing planned ProposedAction confirmation orchestration | Stores one pending-action record; invokes owning modules; no parallel science or farm-state store |
| M6 | Existing DiseaseResult lifecycle | Existing problems may constrain supported crop-family choices through M3; no new scan write behavior is introduced here |
| Frontend/shared infra | Farm-scoped cards, accessible charts, diff/confirmation, persistent cache and recovery | One result drives text, speech and share summary; account switch clears/isolate private cached results |

## 3. Shared analytical interface

Keep compute behind a small interface: evaluate a normalized immutable farm/rotation snapshot, an explicit rule bundle, dated evidence, bounded scenario configuration and evaluation time; return a typed result without DB/network writes. The implementation may use private pure functions for questions, constraint checks and trigger evaluation. Do not duplicate these calculations in chat or React Native.

Every result contains:

| Field | Meaning |
|---|---|
| `result_id`, `schema_version`, `method_version` | Server-generated immutable identity and reproducible algorithm/schema versions |
| `farmland_id`, `season_id`, `season_plan_id` | Server-resolved scope; season/plan may be null during pre-selection exploration |
| `profile_version`, `operational_version`, `policy_version` | Authoritative snapshot/revision tokens, not timestamps trusted from the client |
| `cache_version`, `rule_bundle_hash`, `evidence_refs` | Pinned source inputs including dates, support scale, coverage and freshness |
| `generated_at`, `valid_until` | UTC instants; applicability dates and calendar days use declared Asia/Dhaka conventions |
| `status`, `evidence_gaps`, `warnings` | Supported/conditional/insufficient-evidence outcome; null unsupported numbers |
| `next_question`, `robustness`, `contingency_evaluation` | Typed A01/A02/A03 results, including explicit unavailable reasons |
| `explanation_bn`, `explanation_en`, `speech_text`, `assumptions` | Same facts in each presentation, with source/constraint references |

Version tokens cover all decision-relevant saved fields, plan definitions and operational task/stage changes. Prefer monotonic revisions where available; otherwise compute a server-side canonical digest, check it within the write transaction and lock the affected records. A hash without transactional concurrency control does not prevent lost updates. Evidence expiry is source/variable-specific and versioned; there is no universal invented freshness window.

Freeze concrete schemas/OpenAPI and mappings with affected owners before feature code. The user has approved this product direction; this plan does not claim teammates have already approved a migration or every proposed field name.

## 4. A01 — Decision-driven next question

1. Start with the supported crop/variety/rule set and known farm facts. Separate hard feasibility constraints from preference-based ranking and evidence gaps.
2. Enumerate a bounded, source-supported domain for each decision-relevant unknown. Use farmer-observable categories such as irrigation access or waterlogging history; do not invent a precise soil pH, lab nutrient value, flow rate or groundwater depth.
3. Evaluate the feasible set and transparent ranking under these values, including credible joint combinations where inputs interact. Never vary correlated inputs independently unless the rule bundle justifies that combination. If limits prevent joint evaluation, report incomplete analysis rather than false certainty.
4. Prefer a question that resolves hard feasibility ambiguity, then one that separates supported options. Rank remaining questions by documented worst-case ambiguity reduction and low answer burden; use a stable question ID as the final tie-break. Without calibrated probabilities, do not describe the score as expected information gain or statistical confidence.
5. Return one question with safe answer choices, `unknown` and `skip`, affected alternatives, reason for asking and applicability/evidence IDs. No decision-changing question means return none; unsupported alternatives do not become recommendations just to create a question.
6. Tap/voice answer is read back. An exploratory answer may recalculate a labeled scenario. Persisting it uses the M1 confirmed update, then rebuilds the authoritative M2 snapshot. Do not reuse hypothetical result IDs as saved-farm recommendations.
7. Corrections invalidate derived questions/results. Do not loop on declined/unknown answers; retain ambiguity and offer supported next steps or a measurement need.

A remote coarse SMAP observation and a recent farmer field report may both be valid at their own scales. Keep both with time/provenance, flag the mismatch and request a relevant observation. Do not silently average them or let M5 choose which is true.

**Acceptance:** hand-worked rule fixtures show the question changes/narrows a feasible set or distinguishes the disclosed ranking; irrelevant and lab-only questions are excluded; dependent inputs, all-tied/no-option results, corrections, skip and no-supported-answer cases are deterministic.

## 5. A02 — Robustness envelope and binding constraints

Calculate how a candidate rotation fits supported calendar/resource constraints over a declared bounded scenario domain. Display it as calendar/resource feasibility, not guaranteed yield, survival probability or a universal safe percentage.

- Analyze source-supported axes: planting/transplanting delay in whole days; documented irrigation availability/capacity categories or measured units; temperature perturbations within the supported method. If water response or heat response cannot be calculated, return that axis unavailable. Do not fabricate an ET/yield model.
- Store domain, step size, units, reference dates, constraints, joint versus one-axis-at-a-time interpretation, and evaluated scenario count. A one-dimensional margin does not establish feasibility under combined stressors.
- Evaluate all allowed points within configured compute limits. Return every feasible interval/component, gaps, baseline status, first failing evaluated points and the binding crop/stage/rule. Do not assume monotonicity or infer a continuous exact threshold from coarse grid points. Coarse intervals include their resolution/uncertainty; when the edge is reached, say “not failed within tested range”.
- Respect nursery age, photoperiod, cross-year calendars, crop turnover, water/equipment limits, current planted state and overlap. A “delay” cannot move actual past operations or relabel observations.
- Keep historical observations, future projections and manually perturbed scenarios separate. Preserve the original onset distributions while exploring what-if values.
- Run constraint checks under missing information. Return conditional ranges with explicit assumptions or unavailable status; unknown is never silently replaced by favorable conditions.
- Cache by immutable snapshot, rule/data/method versions and scenario domain. Bound CPU, memory, payload, concurrent requests and scenario count; over-budget requests produce a documented limit error, not an approximate result labeled exhaustive. Record measured target latency before release.

**Acceptance:** hand-calculated boundaries; disjoint/non-monotonic ranges; impossible baseline; insufficient coverage; date/leap-year/unit conversion; coarse-grid truncation; combined stressor examples; repeatable cache keys and bounded workload. UI must explain why the tested range is not a future-weather guarantee.

## 6. A03 — Saved contingency and confirmed application

### 6.1 Policy, evidence and evaluation

On confirmed plan selection, M2 stores a policy bound to the exact farm/selected season/plan, method and rule versions. A policy includes typed supported trigger predicates, applicable observation/provider/scale, required farmer confirmation, freshness/coverage rules, latest feasible action dates, alternative candidates and expiry. The baseline plan can be saved when no supported Plan B exists; the policy explicitly says `unsupported`, without inventing one. Re-evaluation computes alternatives against current context rather than executing a frozen obsolete candidate.

Use a deliberately bounded trigger vocabulary, for example confirmed irrigation unavailability or failure to meet the declared usable-rain criterion by a locally supported date. Distinguish `no_trigger`, `needs_observation`, `needs_field_confirmation`, `trigger_met`, `alternative_unsupported`, `expired` and `superseded`. Forecasts can trigger a review request only under a labeled review policy; they do not prove observed onset failure. Missing rain data cannot establish a dry/no-onset condition.

Deterministic evidence precedence uses effective observation time, quality and source-policy rules, not arrival order alone. Out-of-order updates, contradictory records and withdrawn/corrected evidence invalidate dependent proposals. Apply documented noise/debounce rules only where scientifically supported; do not oscillate between plans on repeated identical observations.

Minimum release refresh triggers: advisory opened/refreshed, relevant confirmed M1/M3 change and new M4 evidence ingested. Implement one bounded shared-backend re-evaluation job with deduplication/retry for already selected policies, or explicitly retain an on-open pilot limitation until that job exists; unattended monitoring cannot be claimed before it is verified. Push delivery is separate: in-app review notices are the minimum, with push only through the existing tested notification path. No continuous phone listener is required.

### 6.2 Proposal lifecycle

```text
saved policy + dated evidence + current farm/season snapshot
                 ↓ evaluate without operational writes
no trigger / missing evidence / unsupported alternative → explain, retain current plan
                 ↓ supported trigger and alternative
immutable change proposal → one M5 ProposedAction → farmer sees exact changes
                 ↓ confirm / cancel / expire
server checks owner + versions + expiry + evidence + planting state + idempotency
                 ↓ valid
single transaction: M2 plan/policy changes + M3 eligible task changes + action receipt
                 ↓ committed
refresh farm state/chat; notify once; retries return the original outcome
```

A proposal includes old/new plan and dates, binding reason/source IDs, `keep/add/reschedule/cancel` task definitions, required resources, expected snapshot versions, expiry and irreversible-action warnings when relevant. It contains no guessed yield/profit/savings. Only source-backed pending tasks belonging to the affected plan are eligible for the displayed change. Preserve completed/skipped/cancelled work, farmer-created work, unrelated disease/weather tasks and actual dates. Changes to any of those need a separate explicit supported action.

**Before planting:** a supported crop/variety/date change may be proposed if planned-season constraints permit it. **After planting/irreversible field work:** do not silently change crop identity, recreate the season or rewrite actual history. Offer only evidence-supported in-season actions or clearly explain that a different plan requires a separately confirmed lifecycle transition. If no valid transition is implemented, block that switch. Multi-season strategy selection must not create several active seasons.

### 6.3 Atomic execution and retries

Use the shared PostgreSQL transaction through transaction-aware owner operations, not chained calls that each commit. M2 and M3 keep their ownership; an orchestration unit of work coordinates them. Before integration, refactor only necessary internal commit behavior to accept an outer transaction while preserving existing public route behavior. Document lock ordering, isolation, task reference uniqueness and full rollback semantics.

Lock action/plan/season and relevant profile/task/policy state in deterministic order; validate the expected digest/revisions; re-evaluate support/freshness at confirmation; apply only the approved diff. If data changes the proposal, return `409 stale_proposal` and require review of a fresh proposal. Never execute materially different values under an old confirmation.

Unique idempotency scope includes account, farm and action; persist request hash and execution receipt in the same transaction as effects. Same key/payload returns the same result even after a dropped response; a different payload with that key returns `409 idempotency_conflict`. Competing actions based on the same plan cannot both apply. Expiry/cancellation racing confirmation has one serialized terminal outcome. An expired already-executed action still returns its saved receipt to a legitimate retry; expiry prevents a new execution.

Before-commit failure rolls everything back. Notification/cache invalidation happens after commit with deduplication; failure there does not mark a committed action failed or run it again. A process crash between commit and notification is recoverable through an after-commit delivery/outbox record in that transaction. The phone's retry queue is not the server's transactional outbox.

## 7. Proposed HTTP and persistence additions

These routes/fields are planned extensions, not claims of existing interfaces. Existing `/advisor` recommendation/season routes and existing `/advisory` plan remain compatible.

| Planned interface | Behavior |
|---|---|
| `POST /advisor/farmlands/{id}/rotation-comparisons` | Existing parent-plan extension returns A01/A02 plus contingency preview. Saved M1 context is authoritative; explicit scenario overrides are labeled ephemeral and cannot directly execute |
| `POST /advisor/farmlands/{id}/rotation-comparisons/{result_id}/reevaluations` | Evaluates policy/new evidence against server-resolved current scope; returns A03 state and immutable proposed diff. May save M2 analytical/evaluation records; never changes selected crop, season or operational tasks |
| M1 existing profile update through ProposedAction | Confirm observable answers, then recalculate a new authoritative result |
| M5 planned `POST /v1/actions/{id}/confirm` and `/cancel` | Shared CCR-3 action mechanism performs A03 and initial selection; no second Plan B confirmation store or bypass endpoint |

Ownership failures use existing non-enumerating 404 behavior; invalid domains/units use 422; stale proposal/key conflict use 409; configured resource limits use documented 422/429 as appropriate; unavailable required cache uses typed 503. Valid evaluation with missing agronomic evidence returns a typed non-actionable outcome, not fake zero margins. Public `/advisory` must not expose private answers/policies/proposals.

**Explicit schema proposal, before migration implementation:**

- M2 `adaptive_decision_records`: immutable `id`, owner-scoped farmland, optional season/plan IDs, versions/digests, method/cache/rule identifiers, generated/expiry times and schema-validated analytical JSON. Store compact typed results, not rasters/audio or arbitrary executable predicates.
- M2 `adaptive_plan_policies`: farm/season/plan/result references, policy revision, typed predicate/config and source references, `active/expired/superseded/unsupported` state. Policy activation and result selection are explicit confirmed writes. Evaluation history references immutable result/evidence IDs.
- Reuse planned M5 `pending_actions`/ProposedAction persistence, extending its payload/preconditions/receipt fields for the above transaction protocol; do not create another farm-state authority. Add a transactional delivery record only if the existing backend lacks one.
- M1 answer provenance reuses correctly matching profile/measurement fields; any missing structure needs a named additive migration. It must retain original reported value/unit, normalized value, effective time, source/method and confirmation context.
- Enforce foreign keys ensuring a season belongs to the same farm and a plan belongs to that season, using composite referenced keys where required. Add bounded JSON/schema validation, version uniqueness, stable task references, policy-activation uniqueness and access/query indexes. Do not weaken current status checks or one-active-season/task reference constraints.
- Write the exact DB_SCHEMA/shared-contract diff and Alembic revision with forward/backward compatibility, nullable/backfill approach, rollback data-loss policy and clean/existing-database checks. Existing farmers must still sign in and list farms without any adaptive data. Feature rollback disables execution and preserves audit/history; it must not restore obsolete operational plans automatically.

This planning update applies no migrations. Immutable result IDs and append-only explanation/evaluation history do not substitute for M3's operational state.

## 8. Mobile, Bangla voice and offline behavior

Preserve sign-in → all farm profiles → selected farm chat. Use existing farm advisory/comparison navigation. Add: one question card with `জানি না`/skip, feasible-range view with accessible text, contingency status and exact before/after confirmation card. Use balanced gutters, SVG/vector icons, no fake status strip and large-text layouts. Numerical content, spoken explanation and summaries come from the same typed result.

Voice reads farm name, question/answer, uncertainty and proposed changes before accepting confirmation. Ambiguous “yes” after farm navigation, expired action or competing question cannot confirm a prior proposal. One active target is explicit; taps remain available when speech fails. Confirming a profile answer does not also confirm Plan B.

Offline shows source-dated cached results with scope/version/expiry. An exploratory answer may be saved locally as a draft, but no fresh calculation is claimed unless a tested bundled method/scenario covers it. An eligible confirmed action may be queued with its original payload, scope, versions, key and expiry; execution revalidates on reconnect and requests a fresh review if stale. Expired actions are not renewed or auto-confirmed. Session/farm switch cannot replay an action in a different scope. Server `OFFLINE=1` remains cache-only and distinct from a disconnected phone.

## 9. Delivery increments and verification gates

| Increment | Work and dependency | Evidence before advancing |
|---|---|---|
| D0 Required baseline | Parent data/science/rotation and actual approved season stages/tasks; auth/isolation and known M1-M6 regressions | Parent V01-V13 appropriate to the working baseline; prerequisite gaps explicitly open |
| D1 Contracts | Freeze A01-A03 result schemas, source rules, migrations and CCR-3/CCR-10/CCR-12 mappings with affected owners | Fixtures for supported/unknown/stale states; migration/compatibility review; no claim of existing signoff |
| D2 Pure decisions | Implement A01 and A02 through the shared M2 interface | A01-A02 hand-worked fixtures, conditional cases and compute limits |
| D3 Policy preview | Immutable policy/evaluation records; trigger/diff preview without execution | Stale/contradictory evidence and pre/post-planting distinctions; no operational writes |
| D4 Confirmed execution | Transaction-aware M2/M3 operations, ProposedAction, receipt and delivery outbox | Forced rollback/crash/retry and concurrent-confirm tests against PostgreSQL |
| D5 Farmer delivery | Question → persisted answer → recalculation → margin → trigger → confirmed change | Real browser and physical Android flow, Bangla read-back, voice/tap and offline recovery |
| D6 Release | Bounded refresh job, observed latency/load, feature rollback, licenses, demo/submission | All parent gates V01-V15 plus A04-A08 below; report actual evidence and remaining gaps |

| Gate | Required additional proof |
|---|---|
| A01 Question | Impact-based deterministic choice, supported answer domain, joint unknowns, no irrelevant/lab guessing, skip/correction and provenance |
| A02 Envelope | Exact fixtures, disjoint ranges, coarse-grid/edge bounds, combined stressors, unknowns, units/date correctness and request limits |
| A03 Policy | Typed trigger states, actual evidence date/coverage, no-onset versus missing, source conflict, expiry, repeated/out-of-order updates and pre/post-planting behavior |
| A04 Contracts/schema | Existing client payloads still work; anonymous/other-owner isolation; clean/existing DB migrations; nullable data; constraints and rollback behavior |
| A05 Transaction | Simultaneous confirm/cancel/expiry; conflicting actions; stale task/profile/plan; dropped response; payload/key mismatch; pre-commit failure; post-commit crash and deduplicated recovery |
| A06 Regression | Password auth/all farms, M1 save, M2 existing recommendation/activation/harvest, M3 completed tasks/current stage, M4 alerts, M5 retry dedup and absent crop/season, M6 healthy/uncertain/repeat scan and immediate shared-state refresh |
| A07 Browser/native/offline | Chrome 320/360/375/390/412/430 mobile widths; accessible text; two accounts/farms; real-user question/answer/cancel/confirm; stale cached proposal; permission denial; physical Android mic interruption and queued reconnect |
| A08 Value/operations | Outside-team user explains the question, constraint and changed task; measured latency/resource limits; refresh/delivery failures; source-removal comparison; public demo distinguishes fixtures from real evidence |

Tests must assert resulting DB state, supported explanations and user-visible changes through the same interfaces callers use. Keep synthetic agronomy in fixtures, never in the production knowledgebase. Browser validation requires observing the actual flow; green backend tests do not establish browser or native success.

## 10. Demonstration and claims

Show a supported Bangladesh farm and three rotations with the required NASA onset/GDD evidence. Start with missing irrigation information; ask the selected field question. Save a confirmed observable answer, explain the changed feasible set and supported robustness range. Introduce a clearly labeled dated observation/scenario and show Plan B's reason and exact diff. Confirm once, demonstrate updated M3 tasks/scoped chat, then show a dropped-response retry without duplicate effects and an unsupported case that declines a numeric answer.

Use measured findings rather than predetermined numerical benefits. A synthetic trigger may demonstrate logic only when visibly labeled; it is not actual farmer validation. Match the supplied criteria through scientific validity, NASA's traceable decision contribution, usable Bangla mobile interaction and a coherent recorded story. No feature guarantees an award.

This is new behavior relative to our current code/explicit result contracts, not a claim of global invention. Adaptation-margin interaction already appears in RotaShift's illustrative prototype. Retain attribution and independently implement permitted ideas; see the [source review](../research/2026-10-29-competitor-feature-opportunities.md) and [repository findings](../research/2026-10-29-competitor-repositories.md) before reusing code/assets.
