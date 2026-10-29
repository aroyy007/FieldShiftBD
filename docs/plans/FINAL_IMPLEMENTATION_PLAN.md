# FieldShift BD — Final Consolidated Implementation Plan

**Owner-requested consolidation:** 2026-10-29, Asia/Dhaka. **Status:** planning specification, not a completion report. Read this first, then the [foundation/work allocation](FOUNDATION_AND_PARALLEL_WORK.md) and [AI-agent starter](TEAMMATE_AI_AGENT_STARTER.md).

## 1. Authority, full scope and source preservation

This is the active consolidated delivery specification for all six contributors. It combines the original project plan, NASA planting-window/rotation plan, accepted adaptive-decision plan and Bangla voice plan. The full four source snapshots from commit `336bf6c` are included below as traceable appendices; source filenames, hashes and section coverage are recorded in the [source manifest](plan-source-manifest.json). No source requirement is silently dropped by a short summary.

Precedence: explicit subsequent owner instructions → this document's reconciled rules and delivery requirements → detailed source appendices with their original applicability. Existing deployed contracts remain compatibility constraints until an additive, reviewed change ships. Earlier statements that call an individual source document the sole source of truth are superseded by this consolidation. Source examples are not evidence, working endpoints or actual team approval.

“Everything” includes the complete original six-module lifecycle, the organizer/final-statement scope, all three accepted adaptive features, voice flows F1–F9, contract changes CCR-1–CCR-12 and later pilot/upgrade deliverables. Preserve original conditionality: alternative datasets, named candidate libraries, paid-provider examples and optional first-class audio are choices/triggers, not an instruction to purchase every provider or install competing engines. Deferred scope must remain visible in the backlog and must not be described as finished.

No award, globally unique invention, indefinitely free hosting, field-validated benefit or zero merge-conflict guarantee is asserted. The plan makes decisions actionable and scientific contributions reproducible.

## 2. Current state and honest completion boundaries

Code baseline: `336bf6c` on local `Aveshek` at consolidation time; inspect current Git state before starting. Existing M1–M6 runtime code is present, including password auth, saved farms/resources, farm-scoped chat, crop-advisor/lifecycle interfaces, operational state/tasks/problems, weather and disease analysis. Earlier source inspections found missing verified season-plan/stage/task agronomy and no completed long-baseline NASA/rotation/voice/adaptive implementation. Verify those findings rather than assuming they have changed.

The foundation commit adds an existing-route/model ownership inventory, selected schema/required-field/enum checks and synthetic Pydantic-validated seam fixtures. Its reported backend run was 213 passed, 2 skipped. That historical result does not prove new analytical, voice or transactional work. These fixtures are examples, not runnable mocks of every future module and not production agricultural knowledge.

**Still required before full parallel integration:** future shared schemas, executable fake adapters, TypeScript contract outputs, composition hooks/feature flags, transaction/confirmation skeleton, migrations and shared frontend seams. See foundation gates B00–B10. Source-data preparation and scientific implementation can proceed independently against fixed contracts; all 64 real district datasets need not exist before a contributor can start local unit work.

## 3. Farmer experience and domain invariants

Password register/sign-in → `/farmlands` lists all owned farms → selecting a farm opens `/farmlands/[id]/chat`. Preserve Division, District, Upazila, Village/locality separately; persist resources and permission-based coordinates. GPS is the phone's position, not automatically the farm's. Prefill administration only when reliable; show denial/failure and allow manual entry.

Farm resources cover sourced soil/land type, irrigation/water source, equipment, budget and relevant previous crops/rotation. Unknown, zero, false, farmer report, regional inference and laboratory measurement remain distinct. Progressive onboarding asks only useful missing facts and supports correction/skip.

The farmer sees a short supported planting/transplanting sentence, earlier/recent rainfall-onset distributions and GDD evidence; compares the current multi-season rotation with at least two supported alternatives; answers one decision-changing observable question when necessary; examines tested feasibility ranges; explicitly selects/activates a plan. M2 owns lifecycle/plan/stage definitions; M3 owns operational current stage/tasks/problems/check-ins. M5 explains the same returned facts in Bangla/English.

A selected plan carries a versioned contingency. Updated dated evidence can propose a supported Plan B with exact plan/task differences. Farmer confirmation applies current approved values once. Preserve actual planting history, completed/skipped/cancelled work, unrelated tasks and one-active-season-per-farm constraints. A crop change after planting requires a separately supported lifecycle transition; otherwise reject it.

Single data owner per domain; existing authenticated routes and meanings remain compatible. No parallel auth/farm/current-state store. No exploration GET or scenario calculation starts a season or changes operational tasks. Use M3 for all persistent Problems. A DiseaseResult may persist as technical scan history; creating a farm Problem is a separate confirmed action after CCR-11 ships.

## 4. Complete scientific and dataset work

### 4.1 Coverage and provenance

Full target: 64 canonical Bangladesh districts; at least three locally supported crop/season profiles; three meaningful multi-season rotation strategies per supported farm including its actual current rotation. Rice/Aman is Rice plus season/variety, not a duplicated crop species. No unsupported second/third alternative is fabricated merely to reach a count.

Implement all source families and bounded roles defined in source S1: POWER daily rainfall/T2M/solar (2001–2025 backbone); IMERG spatial precipitation; SMAP available from 2015; MODIS NDVI as the chosen MODIS/VIIRS option; Landsat; ECOSTRESS; GRACE/GRACE-FO; SRTM; GEDI; downscaled climate scenarios such as NEX-GDDP-CMIP6; local agronomy/soil/market/resource evidence; versioned district boundaries/crop masks. Actual empty coverage is reported unavailable. GRACE is regional storage, GEDI structure samples, NDVI composite greenness and SMAP coarse wetness; none becomes an invented field measurement.

M4 builds versioned per-district Parquet outside PostgreSQL with manifests, source/transform/cache hashes, QA/fill flags, units, native resolution/footprint, valid coverage, aggregation method, CRS, retrieval/publication periods, source IDs and licenses. Deduplicate shared grid requests; bound retries, downloads and memory. Pin POWER UTC/LST choices and distinguish them from Asia/Dhaka days. Harmonize different temporal/spatial products explicitly; do not average unlike products blindly. Release large permitted data as hashed versioned assets; ship compact permitted geometry/results on device.

`OFFLINE=1` forbids analytical network fallback, including LLM/geocoding/remote tiles/model downloads. Missing/corrupt cache gives typed unavailability. A disconnected phone has a separate scoped cache/outbox and cannot claim fresh server computation. Complete dataset QA and licensing before release, not just before a demo screenshot.

### 4.2 Pure compute and agronomy

Place organizer pure compute at `backend/src/compute/agro.py`, packaged/importable by the existing backend. Inject normalized data/config/time; no HTTP/DB/audio side effects. M2 owns the implementation, M4 only supplies evidence.

Use sourced crop/variety/season calendars, nursery/transplant distinction, onset search windows, wet/dry definitions and verification horizon, GDD base/cap/method/targets, photoperiod and nursery-age constraints. Record scoped agronomic review and provenance. Demo defaults (7-day sum ≥20 mm, max consecutive dry spell 7 days) need local justification. Correct the source screenshot's incomplete wet-day test and missed-last-window defect; do not copy them.

Use complete dated series; preserve missingness; validate duplicates/negatives/fill values; detect first valid onset over a declared verification horizon, including cross-year trailing data. Return no-onset versus insufficient/truncated data distinctly. Compare no-onset frequency separately from distributions conditional on onset. Repeat annual detection and comparison at 15/20/25 mm. Name candidate-window-start convention and any dry first day.

Compute sourced daily GDD with explicit mean or Tmin/Tmax method, optional cap, planting/nursery reference, units and completeness. Apply crop-specific agronomic feasibility before recommending a date shift; a rain-onset shift is not itself permission to shift every crop.

Freeze 2001–2012 (12 years) and 2013–2025 (13 years); keep later observations separately labeled. Return annual samples, exclusions, spread/medians, two-sided Mann–Whitney U/statistic orientation/method/p-value, ties/small-sample handling, effect and uncertainty. State annual dependence and causal limits. Separate raw observed onset shift, explicitly rounded signed whole-day display and recommended window shift. Validate seasonal anchors/leap years. No predetermined “11 days” result.

Compare baseline/rain-only/combined methods using held-out timing evidence and NDVI/ground observations with honest coverage; prevent temporal leakage and tune only on training data. Report what evidence changes when NASA/supplemental layers are removed. Predicted feasibility is not observed historical yield or causal farm benefit.

### 4.3 Rotation decision factors

Every rotation includes dated calendars, applicability/support state, uncertainty and explanations of nutrient cycling/legume fixation potential, soil cover/bare intervals, organic-matter potential, infiltration/erosion susceptibility, crop-family/pest cycle, water/irrigation/heat/dry/extreme-rain/frost constraints, forage, equipment/labor, budget and local market evidence. Use documented FAO-56-style methods only when inputs and paddy losses are supported. No invented fertilizer credit, carbon/erosion percentage, income or savings.

Farmer priorities change transparent tradeoffs/exclusions rather than an opaque universal score. Historical observations, near-term forecast, climate projection and manually perturbed what-if scenarios remain separate. Show source-scale and model/ensemble uncertainty; do not mutate historical distributions while moving a slider.

## 5. Three adaptive features and execution rules

**A01 — Next field question:** enumerate supported plausible unknown-input domains and relevant joint combinations; choose one observable question that resolves feasibility ambiguity first, then transparent ranking ambiguity, with answer burden and stable tie-breaking. Never ask a farmer to guess a lab result. Provide unknown/skip, no-question/no-option outcomes, provenance and correction invalidation. Hypothetical answers stay scenarios; confirmed M1 saves cause authoritative recomputation. Keep satellite/farmer observations distinct when scale/date disagree.

**A02 — Robustness envelope:** evaluate bounded delay/water/heat domains supported by the method; return all tested feasible intervals/components and binding crop/stage/constraint, domain/step/units/count, edge truncation and uncertainty. Do not assume monotonicity, infer exact continuous thresholds from coarse points, or combine one-axis margins into a joint guarantee. Missing axes remain unavailable. Bound CPU/payload/concurrency; cache by all relevant versions. This tests calendar/resources, not survival/yield probability.

**A03 — Conditional Plan B:** bind policy to farm/season/plan/rule/method versions and source freshness. Support typed states: no trigger, needs observation, needs field confirmation, trigger met, alternative unsupported, expired, superseded. Missing rain is not observed no-onset; forecasts can request review, not prove an observed event. Order evidence by effective time/quality, handle corrections/conflicts, prevent repeated-update oscillation and recompute alternatives against current facts.

Record immutable results/proposals with server-derived scope, snapshot revisions/digests, cache/rule/source IDs, generated/expiry time and exact keep/add/reschedule/cancel diff. Respect planting state. Confirmation checks owner, expiry, current versions, support and exact approved values. Different values require a fresh proposal/read-back. Same action/key/payload returns a saved receipt; different payload with that key returns conflict. Competing confirmations/cancel/expiry serialize.

Use one shared PostgreSQL transaction with transaction-aware M1/M2/M3/M6 owner operations as applicable. Refactor necessary internal commits while preserving existing route behavior; no chained HTTP commits pretending to be atomic. M5 coordinates the unit of work, not the domains' mutations. Store action receipt and post-commit delivery outbox with effects; roll back all pre-commit failure; recover notifications after a crash without repeating effects. Lock deterministic scopes and enforce uniqueness/current-version checks.

Reevaluate on advisory refresh, relevant confirmed farm/state changes and new M4 evidence. Full release includes bounded backend refresh/delivery jobs with deduplication/retry, in-app notices and tested push delivery. An on-open-only pilot is explicitly partial unattended monitoring.

## 6. HTTP, persistence and shared contracts

Existing routes remain the baseline. Add `GET /advisory?district=&crop=&season=`; omitted season either resolves one configured profile or returns choices. Public district results are bounded/read-only/private-data-free. Authenticated `POST /advisor/farmlands/{id}/rotation-comparisons` returns three strategies, source-window results and A01/A02/A03 preview. Its `/{result_id}/reevaluations` evaluates immutable current scope without operational writes. M1 profile saves and M2 selection use the single shared ProposedAction mechanism; M5's planned `/v1/actions/{id}/confirm` and `/cancel` never bypass owner operations.

Typed result fields include canonical district/crop/season, schema/method/cache/result IDs, support status/warnings/gaps, observed raw/display shifts, recommended shift/windows, period distributions/exclusions, GDD/thermal details, statistics/effect/uncertainty, sensitivity/validation, assumptions/provenance, bilingual advice/speech/SMS. Farm results add snapshot/operational/policy revisions, next_question, robustness and contingency_evaluation. Units/date/time standards and unavailable/null semantics are part of the contract.

Use existing ownership errors (non-enumerating 404), invalid-input 422, stale/key conflict 409, documented resource/rate limits and typed required-cache 503. Insufficient agronomic evidence is a structured non-actionable result with null unsupported numbers. Do not promise every route produces a complete recommendation without data.

Planned additive storage: M1 versioned consent/preferences/fact provenance/rotation history; M2 immutable adaptive_decision_records and adaptive_plan_policies; M5 pending_actions/receipts and durable delivery support if absent. Reuse correctly matching fields. No arbitrary unrelated JSON dumping, duplicate current state, raw raster/audio in PostgreSQL or competing confirmation store. Files use storage keys. Enforce farm/season/plan consistency, one active season, action/policy/version uniqueness and stable task references. Explicit DB_SCHEMA diff, migration graph/backfill/old-client/rollback checks precede persistence implementation. Disabling execution on rollback preserves audit/history, not automatic restoration of obsolete plans.

CCR-1–CCR-12 remain tracked implementation decisions. Resolve schemas/error behavior together once in foundation B01; record owner acceptance and version. Owner product authorization is already given by this request; do not claim other teammates have signed technical details or repeatedly ask permission for routine module-internal work.

## 7. Voice, accessibility, all nine flows and offline

Bangla default with English parity; large targets (≥56 dp where specified), readable type, replay/hear-label, equal gutters, SVG/vector icons, no imitation time/network strip, safe areas/keyboard/large-text handling. Map has a district-list alternative and actual-resolution legends; display time layers, rotation timeline, uncertainty, GDD/distributions and glossary (ET/NDVI/anomaly/frost/water balance/satellite versus ground).

Tier 0 Android uses runtime-capability-checked Bengali device STT, installed system TTS and ~150–250 consented human core prompts. Device/vendor online processing is disclosed; no usable language means tap-first. Android ≤12 cannot use the library's Android 13+ locale query. Prefer verified on-device recognition; never silently use another language. Actual native builds/physical low-memory phones are mandatory; Expo Go/Chrome cannot establish native voice support.

No background/closed-app microphone or custom wake word. One visible listening session, start/stop cues, silence/noise coaching, VAD/length bounds (15 s commands/questions, 60 s descriptions), wired/Bluetooth handling, interruption/background stop. Normalize dialect synonyms, Bangla/English digits, fractions, units and relative dates. Read every numeric/date/unit value back before saving. Two failed attempts offer tap choices. Confidence thresholds are provider-specific and measured.

M1 owns C1 mic/C2 processing disclosure/C3 optional recording retention/C4 photo consent and preferences; M5 owns speech I/O. No audio retention by default; C3 is opt-in with agreed retention (90 days is a proposal), deletion/withdrawal and provider-change reconsent. C2/C3 use taps per the source assumption pending actual policy review. Redact personal data/logs; no secrets in URLs. Legal/terms checks are release work, not unsupported legal claims in this document.

| Flow | Required behavior |
|---|---|
| F1 | Spoken first-run lesson/consent, permission explanation and widget setup help |
| F2 | Speak/tap navigation to tasks/alerts/health/back/home and explicit farm disambiguation |
| F3 | One missing farm field at a time; parsing/read-back; correct/skip; confirmed regional bigha conversion only; canonical units preserved |
| F4 | Grounded short Q&A, replay/more, scoped context, disease-photo offer and proposed write; queued messages receive honest status |
| F5 | Read tasks; exact matched task complete/skip/reschedule proposal and confirmation; taps also prevent accidental writes |
| F6 | Photo coaching/blur-dark check, optional symptoms, image-based M6 screening and confidence limits; source-backed actions; separate confirmed M3 Problem handoff |
| F7 | Tested alert push/in-app delivery, foreground listening and explicit task-change confirmation |
| F8 | Actual NASA advisory/rotations, why/evidence view, bilingual narration, under-160-Unicode-character sharing/compose and confirmed plan selection |
| F9 | Decision question → separately confirmed saved answer → envelope → dated contingency → exact confirmed Plan B diff and refreshed scoped state |

T0 reads/navigation need no write confirmation. T1 data changes need exact read-back plus explicit yes/tap. T2 irreversible/sensitive actions (season close, deletion, sharing, consent withdrawal) need tap; undo is only a supported pre-execution/recoverable operation. Bind yes to one current visible action; navigation/session/expiry/interruptions invalidate ambiguous confirmation. Routine transcript/scan history persistence is disclosed, not recursive confirmation for every technical row.

Launcher/widget/shortcut/notification deep links must resolve authentication and explicit farm choice before opening a farm-scoped mic/action. A widget tap may start listening only when the app is visible, context is safe and the user action is valid. Optional voice playback respects preferences/shared-phone context. App closed means no autoplay. iOS stays tap-first until usable Bengali STT is measured.

M6 currently auto-syncs Problems: CCR-11 must introduce coordinated confirmed/deferred sync across backend, client and retry path. UI confirmation alone does not undo an earlier write. Protect healthy/uncertain/repeat outcomes, source/category/severity/status, disease-result links and immediate shared-state refresh. Description-only remains preliminary M5 Q&A, never a fabricated image diagnosis. No unapproved chemical doses.

Cache scoped tasks/alerts/summary/results and permitted audio; show age and invalidate on account/farm/season/version changes. Queue eligible transcripts/photos/confirmed actions with original key/payload/revisions/expiry. Raw audio queues only if a real adapter and consent cover it. Retry with backoff/limits, survive restart, no stale auto-renewal or cross-account replay. Resumable compact uploads require a working backend protocol, not a frontend claim. Provider outage/missing voice has tap/bundled fallback.

## 8. Six contributors and explicit integration ownership

Exactly six module owners remain; no seventh product module. One of the six also acts as integration steward, default M5 owner until the team names another. This is a rotating technical responsibility, not an invented teammate name or reassignment of domains. Other owners submit shared-file patches through the steward.

| Owner | Complete remaining allocation | Frontend contribution |
|---|---|---|
| M1 | Auth/profile regression; location/resources; priorities/history/measured-fact provenance; progressive intake; consent/preferences/local-unit normalization; catalog IDs and approved synonym persistence | Farm/onboarding/resources/consent views and module-local strings |
| M2 | Verified local agronomy/calendar/stage/task definitions; all pure onset/GDD/stats/window/rotation work; analytical result/policy records; A01/A02/A03 decision logic; selection/season/harvest definitions | Advisory/distribution/GDD/rotation/question/envelope views and evidence explanations |
| M3 | Operational stage/state/tasks/check-ins/problems; task-diff execution/retry support; completed-history invariants; Problem idempotency and M6 linkage interface | Tasks/problems/check-in views, operational diff renderer |
| M4 | All required NASA/local environmental ingestion, QA/Parquet/cache/manifests, coverage/geometry/map layers, projections/forecast separation, weather suppression and evidence refresh | Evidence/layer map controls, alerts and source availability |
| M5 | Conversation/grounding/intents/Bangla parsing/voice shell; ProposedAction orchestrator/UOW/receipt/outbox; shared frontend composition/i18n/offline client; release integration coordination | Chat, microphone/speaker/confirmation/navigation/widget/shortcut/shared accessibility |
| M6 | Image-quality coaching, local model rights/deployability, disease/symptom schema, inference/verification/history, deferred confirmed Problem handoff and scan UI | Crop-health/photo/result/history and safe confidence presentation |

M1 owns persisted crop catalog identities/labels; M2 authors agronomic variety/season rules and synonym proposals; M5 reads the approved lexicon for speech. M3 owns operational value `seasons.current_growth_stage_id` despite M2 owning season lifecycle/definition records. M4's historical bundle cannot depend on M3/M2; only live farm weather impact reads M3. M5 never owns another domain's science or writes.

Physical file allocations, reserved global files, separate branches and one-writer migrations are mandatory in [FOUNDATION_AND_PARALLEL_WORK.md](FOUNDATION_AND_PARALLEL_WORK.md). Domain ownership alone cannot prevent Git conflicts in a shared file.

## 9. Delivery stages, all-source completion and verification

| Stage | Required delivery and release meaning |
|---|---|
| R0 Foundation | B00–B10 ready for the affected seams; versioned contract tag + six starter packs; feature implementations can start with executable fakes |
| R1 Complete hackathon product | Full organizer/final-statement science/data/three rotations + F1–F9 Android/tap/voice + adaptive three-feature loop + production/submission gates. Single-district 48-hour slice is partial, not this full completion |
| R2 Field pilot | Source voice Phase 5: ≥8 regions and ≥20 speakers/region consented speech study, 40–60 farmers for 3–4 weeks, 6–8 phone/wider platform evaluation as applicable; report real failures and measured corrections |
| R3 Provisioned upgrades | Preserve voice Phase 6: evaluate/licence/provision self-hosted STT/TTS when Tier 0 fails its gate, provider swap/A-B and possible fine-tuning; iOS voice/distribution, store listing, Quick Settings/Control Center/Action Button/shortcut options and first-class audio when its CCR is activated. Record funding/capability conditions; never count unperformed work complete |

Organizer milestone is retained verbatim in S1: pre-cache/agronomic definitions/Bangla strings; Day 1 morning compute/tests, afternoon district/crop/distributions, evening advisory/assumptions and 18:30 event-local recording; Day 2 morning bilingual phone/SMS/outside-team test, noon freeze/record/submit. Original cut order is an explicit future scope decision only, never silent acceptance of missing full requirements.

All V01–V15 and adaptive A01–A08 apply with their full definitions in S1/S2. Add all voice-phase acceptance criteria in S3, including ≥200 parser cases, voice/tap navigation comprehension, wrong-action safeguards and real consented pilot work. Metrics such as command accuracy ≥90% quiet/≥80% field, 8/10 task navigation, median voice reply ≤6 s simulated 3G/≤3 s cached, widget warm≤2 s/cold≤4 s and pilot success≥85% are targets to measure, not results. Any tuning after a capability spike is versioned and explained; do not retroactively change targets just to pass.

Test pure hand-worked dates/units/missingness/statistics/constraints; module contracts/fakes; real PostgreSQL migration/transactions/races/crash recovery; clean-user and existing-user lifecycle; two farmers/two farms; auth/deep links, chat retry dedup/absent season, M6 healthy/uncertain/repeat and shared refresh; network-denied OFFLINE=1; actual Chrome mobile widths 320/360/375/390/412/430 with realistic heights, large text/keyboard; signed native Android permissions/mic/TTS/interruption/cache; outside-team usability. Existing counts/skipped tests are not proof of untested PostgreSQL/native behavior.

## 10. Production, source rights and submission

Use existing FastAPI/SQLAlchemy/PostgreSQL/Alembic and Expo/React Native/Router. Pin dependencies and selected source products. Follow frontend/AGENTS.md, actual SDK docs and config plugins; no manual native-directory edits. Original code Apache-2.0 with upstream notices and separate data/model permissions. Current noncommercial M6 checkpoint needs an explicit compatible replacement or separately permitted release decision; do not automatically relicense weights/screenshots/data.

No purchased speech/LLM/SMS API is required for deterministic advice or Android pilot. Provision measured backend/storage/network/model capacity, durable backups/restore, secrets, HTTPS, release URL reachable from a phone, signing/update path, no dev reload/public trust DB and bounded source/job/inference resources. Free quotas are bounded pilots. Store fees/platform capabilities/provider terms are verified at release. SMS copy/share/compose suffices; show Bangla character/segment implications and confirm external sharing.

Public accessible repository, README dataset URLs/algorithm/assumptions/limitations, working official project page with exact challenge/category, recorded demo, authentic teamwork evidence and original judging criteria are required. Demonstrate actual NASA-derived result → useful field question → supported feasible choice/range → labeled changed evidence → exact confirmed Plan B → single M3 update/scoped chat; clearly label synthetic triggers and distinguish usability from agronomic field validation. Do not claim NASA endorsement.

## 11. Reconciliation decisions and unresolved technical choices

| Issue across the sources | Final rule |
|---|---|
| Multiple documents each claim canonical authority | This consolidation controls delivery; full frozen sources remain requirements with reconciled applicability |
| Original no-unrelated-satellite scope versus new NASA requirement | All specified agricultural/environmental layers are included; unrelated marketplace/payments/social/financial systems remain excluded |
| M2 source text says no NASA dependency | Existing recommendation/lifecycle remains usable; new analytical adapter consumes typed read-only M4 bundles, no import-time network or M3 dependency |
| Crop synonym ownership differs | M1 persists catalog/synonyms; M2 proposes scientific mappings; M5 consumes read-only |
| M6 auto-write versus all-flow confirmation | Coordinated CCR-11 deferred-problem execution; DiseaseResult history still persists; no confirmed feature until all call/retry paths match |
| Immediate mic/deep link versus all-farm selection | Authenticate and resolve explicit farm first; no accidental cross-farm command |
| Voice task-reschedule request versus status-only API | Add a reviewed M3 date-change contract or show unsupported; do not invent a PATCH field |
| No schema change preference versus new durable features | Reuse matching fields first; explicit reviewed additive migrations are allowed where needed; do not hide schema in unrelated JSON |
| Zero-cost goal versus iOS/cloud/store/pilot | Android pilot target first; retain funded/conditional later deliverables and their blockers |
| Market suitability versus unrestricted market-price Q&A | Sourced dated market evidence may support rotation factors; no invented live prices, marketplace or financial service |
| Shared schema owner versus one writer per file | Integration steward applies affected-owner-approved shared changes once; no unilateral migration heads/global-file races |

Foundation must settle concrete contract fields, error codes, freshness/config/time conventions, action lifecycle/locking and migration graph. These are technical handoff decisions, not missing product intent. Named people, device capability, actual agronomy, source rights and recorded teammate acceptance must never be invented.

## 12. Requirement accounting and future changes

Source S0 covers the original lifecycle/domain/mock/Golden Farm/Git/testing/DoD rules. S1 includes every O01–O16/P01–P14/J01–J02 requirement, datasets D01–D12 and V01–V15. S2 includes adaptive A01–A08 and D0–D6. S3 contains all F1–F9, CCR-1–CCR-12, phases 0–6, assumptions/risks, pilot and capability requirements. Every original heading is enumerated in the source manifest and its complete content appears below.

Open the complete snapshots: [S0 original project](#source-s0), [S1 NASA delivery](#source-s1), [S2 adaptive decisions](#source-s2), [S3 voice](#source-s3). The appendices contain all detailed constraints/test targets that the integrated work allocation must satisfy.

Track implementation using requirement IDs plus commit/method/cache/device/test evidence; open, implemented and verified are different states. Track each conditionally deferred item with trigger, owner and unresolved dependency. Do not delete it to claim “all four plans complete.” New scope/amendments update this plan and relevant schema/ownership records together, followed by a fresh shared base tag.

<!-- SOURCE_APPENDICES -->

<a id="source-s0"></a>

## Appendix S0 — Complete source snapshot

Source: `plan.md` at `336bf6c`. The reconciled final rules above take precedence. Full text is retained for requirement traceability; source headings are prefixed and local links relocated for this combined file.

<details>
<summary>Read complete S0 specification (97 source headings)</summary>

### S0 · 🌾 AI Farmer Assistant — Project Plan

> **This document is the source of truth for the project.**
>
> **2026-10-29 planning amendment, requested by the project owner:** Deliver the organizer's NASA planting-window advisory together with the complete final Field Shift problem statement. Section 20 and [the detailed challenge delivery plan](2026-10-29-nasa-planting-window-and-rotation.md) define this added scope, acceptance gates and requirement traceability. The [Bangla voice plan](2026-10-06-voice-first-bangla.md) is its accessibility delivery plan. Existing six-module ownership remains the baseline; proposed additive interfaces must be recorded with affected owners before implementation. This amendment does not claim those interfaces or features are already implemented.
>
> **Accepted follow-up, 2026-10-29:** After the required organizer/rotation flow, deliver decision-driven field questions, rotation robustness envelopes and a confirmed conditional Plan B. The [adaptive-decision specification](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md) defines A01-A08 acceptance gates, ownership, proposed schema and safe execution. This is owner-authorized planning scope; implementation contract/migration decisions still need recording. Start with the [complete plan index](README.md).
>
> **STRICT RULE:** Always follow this plan. Do not change, restructure, remove, or redefine another module's plan, responsibilities, dependencies, contracts, or workflow without explicit team-level agreement.
>
> **Module-level freedom:** A team member may suggest improvements, alternatives, refactors, or a more detailed implementation plan **only inside their own assigned module**. Such suggestions must not alter another module or the shared project contract unless the team explicitly agrees to the change.

---

### S0 · 1. Project Goal

Build FieldShift BD as a farmer-centered decision-support mobile app using NASA Earth observations, historical and predictive climate data, local soil/crop knowledge and farmer priorities. It must explain how usable-rain onset and crop thermal accumulation have changed, recommend supported planting/transplanting windows, and compare at least three multi-season rotation strategies including the farmer's existing rotation. Soil health, water/resource feasibility and uncertainty are part of each comparison.

The existing season-long assistant carries these decisions through farm onboarding, crop selection, season planning, monitoring, weather-aware actions, disease detection, harvest and future rotation history. It supports farmer judgment and local expertise. The organizer's planting-window advisory and the final statement's rotation exploration are both required; one does not replace the other.

The farmer should experience **one unified assistant**, not six separate systems.

The six modules are independent development units connected through shared contracts and a shared farm state.

---

### S0 · 2. Core Product Principle

The product is **not simply “ChatGPT for farmers.”**

It is an **AI farm manager with a conversational interface**.

The system should understand:

```text
Who is the farmer?
        ↓
Where is the farm?
        ↓
What resources does the farmer have?
        ↓
What crop is being grown?
        ↓
What growth stage is the crop in?
        ↓
What tasks are due?
        ↓
What problems are open?
        ↓
What is the weather doing?
        ↓
What does the farmer need to know or do next?
```

---

### S0 · 3. Six-Module Architecture

### S0 · Module 1 — Farm Profile & Onboarding

### S0 · Owns

The progressive intake conversation and the single source of truth for farmer/farm information.

### S0 · Responsibilities

- Progressive onboarding conversation
- Location
- Land area and land unit
- Soil information
- Irrigation availability
- Water source
- Previous crop and yield
- Farming equipment
- Farming experience
- Organic/conventional preference
- Budget
- Crop preferences
- Current and previous multi-season rotation, farmer priorities and constraints needed for scenario comparison (additive contract; preserve existing profile fields)
- Source/measurement context for relevant soil information; distinguish farmer report, lab measurement and regional estimate
- Optional livestock information
- Farmer corrections/updates
- Profile completion state
- Validation and normalization of profile information

### S0 · Key design problem

This is a **stateful conversation**, not a static form.

The module must:

1. Track information already known.
2. Ask only for missing information.
3. Allow the farmer to correct previous answers.
4. Persist the profile in the agreed shared structure.

### S0 · Depends on

None.

---

### S0 · Module 2 — Crop Advisor & Season Lifecycle

### S0 · Owns

Crop suitability reasoning, crop selection, season-plan generation, harvest guidance, and season-close history.

### S0 · Responsibilities

- Determine suitable crops from the farm profile
- Explain suitability per factor
- Present possible crop choices
- Support farmer crop selection
- Generate crop-specific season plan
- Define growth stages
- Define stage-specific tasks
- Provide harvest guidance
- Record season outcome information
- Preserve useful season history for future advisory
- Compute source-backed usable-rain onset, crop-specific growing degree days, two-period statistical comparison and supported planting/transplanting window shifts
- Compare current rotation with at least two locally supported alternatives using soil, climate, crop-family, water, resource and farmer-priority factors
- Return actionable Bangla/English advice, SMS-length summaries, uncertainty, sensitivity results and evidence references for frontend/M5 presentation

### S0 · Key design problem

Recommendations must be **explainable**.

Do not rely on one opaque score as the primary explanation.

Preferred reasoning format:

```text
Suitable because:
- Soil
- Planting timing
- Irrigation
- Climate/region
- Land area
- Budget/resources

Potential concerns:
- Water availability
- Weather sensitivity
- Common disease/pest risks
- Other relevant constraints
```

### S0 · Major project constraint

The main bottleneck is **reliable local agricultural knowledge and crop/variety/season data**, not code.

The owner of this module must prioritize sourcing and structuring the agricultural knowledge before building complex recommendation logic.

### S0 · Depends on

Module 1 — Farm Profile.

For the Section 20 advisory extension, consume the read-only district environmental cache/feature interface supplied by M4. This analytical input does not require M3 operational state and must not create a circular dependency: M4 historical-data ingestion is independent of M2/M3.

### S0 · Produces

- Crop Recommendation(s)
- Selected Crop
- Season Plan
- Growth Stage definitions
- Harvest guidance
- Season history data
- PlantingWindowAdvisory and RotationComparison (additive contracts in Section 20)

---

### S0 · Module 3 — Farm Brain (Task & Monitoring Engine)

### S0 · Owns

The current operational state of the farm.

### S0 · Responsibilities

- Convert season plans into actionable tasks
- Track daily/weekly tasks
- Track due, pending, completed, skipped, and overdue tasks
- Track current growth stage
- Track farmer check-ins
- Track farm problems/issues
- Record problem status
- Maintain current farm state
- Provide farm state to other modules
- Accept state updates from other modules
- Avoid unnecessary notification/check-in spam

### S0 · Key design problem

This is a **state engine + scheduler**, not a content-generation feature.

It must be able to represent states such as:

```text
Week 4
Current stage = Vegetative
Fertilizer task = Due
Weed-control task = Pending
Problem = Possible leaf disease
```

### S0 · Structural role

This is the **central farm-state hub**.

Modules 4, 5, and 6 read from and/or write to Module 3's state instead of creating independent farm-state systems.

### S0 · Depends on

Module 2 — Season Plan.

### S0 · Produces

- Current Farm State
- Current Crop
- Current Growth Stage
- Task State
- Open Problems
- Check-in State
- Season progress state

---

### S0 · Module 4 — Weather Intelligence & Alerts

### S0 · Owns

Turning weather information into crop-relevant, growth-stage-aware actions and alerts.

### S0 · Responsibilities

- Obtain/process weather information
- Evaluate weather against farm location
- Read crop and growth stage from Module 3
- Consider current and upcoming tasks
- Identify potential agricultural impact
- Generate actionable weather alerts
- Suppress unnecessary alerts
- Acquire, quality-check, harmonize and pre-cache district NASA POWER, IMERG, SMAP, NDVI and the additional scoped Earth-observation/climate layers defined in Section 20
- Expose versioned read-only historical/environmental features, provenance and honest availability/resolution for M2; separate observations, forecasts, reanalysis and climate projections

### S0 · Required reasoning pipeline

```text
Weather
   ↓
Farm location
   ↓
Current crop
   ↓
Growth stage
   ↓
Current/upcoming tasks
   ↓
Potential impact
   ↓
Recommended action
   ↓
Alert only when useful
```

### S0 · Key design problem

The system should not simply notify:

> “Rain tomorrow.”

It should determine whether the rain changes what the farmer should do.

Example:

```text
Heavy rain expected
        ↓
Irrigation is scheduled
        ↓
Potentially unnecessary irrigation
        ↓
Send actionable alert
```

### S0 · Depends on

Module 3 — Current Farm State / Growth Stage / Tasks.

This dependency applies to operational alerts. District source ingestion, offline caches and the M4 → M2 historical/environmental interface operate independently of farm/task state; they must not depend on an active season.

---

### S0 · Module 5 — Open-Ended Conversational Layer

### S0 · Owns

The main conversational interface and message routing.

### S0 · Responsibilities

- Accept farmer messages
- Identify intent
- Determine whether a message is normal Q&A, task-related, farm-state-related, weather-related, or disease-related
- Retrieve relevant farm context
- Retrieve relevant agricultural knowledge
- Generate contextual responses
- Route disease-related image requests to Module 6
- Keep responses grounded in the agreed agricultural knowledge
- Render and speak the M2 planting-window/rotation result in Bangla or English, preserving computed values, uncertainty and citations
- Route advisory/rotation questions and explicitly confirmed actions through owning modules; do not recalculate scientific claims in the LLM

### S0 · Key design problem

The chatbot must **not behave like generic ChatGPT**.

Every relevant answer should use available context such as:

```text
Farm Profile
+
Current Crop
+
Current Growth Stage
+
Current Tasks
+
Open Problems
+
Relevant Agricultural Knowledge
```

Agronomic claims should be grounded in the project's approved agricultural knowledge rather than invented independently per conversation.

### S0 · Depends on

- Module 1 — Farm Profile
- Module 2 — Agricultural knowledge/facts
- Module 3 — Current Farm State

### S0 · Important ownership rule

Module 5 owns the **conversation**, but it does not become the owner of farm state, crop data, weather data, or disease data.

---

### S0 · Module 6 — Disease Detection

### S0 · Owns

Image-based crop disease/symptom analysis.

### S0 · Responsibilities

- Accept crop images
- Analyze image
- Identify possible disease/symptom category
- Provide confidence level
- Explain visible symptom indicators where appropriate
- Provide safe, practical next actions
- Include the appropriate uncertainty/disclaimer
- Write the result into Module 3 as a farm problem/state update

### S0 · Preferred response structure

```text
Possible issue:
[Diagnosis/category]

Confidence:
[Low / Moderate / High]

Observed symptoms:
[Relevant symptoms]

Recommended actions:
[Practical actions]

Status:
[Recorded as an open farm problem]
```

### S0 · Key design problem

Disease detection must not be an isolated one-off feature.

The result must flow back into the farm state:

```text
Image
 ↓
Module 6
 ↓
Disease Result
 ↓
Module 3
 ↓
Open Farm Problem
```

### S0 · Depends on

Module 3 — for crop context and for writing the result into farm state.

---

### S0 · 4. Shared Domain Model / Contract Layer

This is **not a seventh product module**.

It is the shared contract that allows all six modules to work in parallel.

Before implementation, the team must agree on the structure and meaning of at least:

```text
Farmer
FarmProfile
Crop
CropRecommendation
Season
SeasonPlan
GrowthStage
Task
Problem
WeatherEvent
WeatherAlert
DiseaseResult
FarmState
ChatMessage
ChatResponse
DistrictClimateBundle
PlantingWindowAdvisory
RotationComparison
FarmerPriorities / RotationHistoryInput
```

### S0 · Example: FarmProfile

```text
farmer_id
location
land_area
land_unit
soil_type
irrigation_available
water_source
previous_crop
previous_yield
equipment
farming_experience
farming_method
budget
crop_preferences
livestock
```

### S0 · Example: Season

```text
season_id
farm_id
crop
variety
planting_date
expected_harvest_date
current_growth_stage
status
```

### S0 · Example: Task

```text
task_id
season_id
title
description
due_date
status
priority
```

### S0 · Example: Problem

```text
problem_id
farm_id
season_id
source
category
description
severity
status
created_at
resolved_at
```

### S0 · Example: DiseaseResult

```text
disease_result_id
farm_id
season_id
crop
possible_issue
confidence
symptoms
recommended_actions
created_at
```

> **Contract rule:** Once the shared contract is agreed, individual modules must build against it. A developer must not silently change a shared field because it is convenient for their module.

---

### S0 · 5. Parallel Development Strategy

### S0 · Core rule

**No module developer should wait for another module to finish implementation.**

The team works in parallel using:

1. Shared contracts
2. Mock data
3. Mock dependency providers
4. Clearly defined inputs/outputs
5. Incremental integration

The dependency graph describes runtime dependencies, **not development order**.

---

### S0 · Development model

```text
                 SHARED CONTRACTS
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
       M1              M2               M3
        │               │                │
        │               │                │
        └───────────────┼────────────────┘
                        │
               MOCK / REAL INTERFACES
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
       M4              M5               M6
```

All modules can start after the contracts are agreed.

---

### S0 · 6. Mock-First Development Rule

Every module with dependencies must initially support mock inputs.

Example:

```text
Module 2
    ↓
Mock FarmProfile
    ↓
Crop Recommendation
    ↓
Season Plan
```

Later:

```text
Mock FarmProfile
       ↓ replace
Real Module 1 output
```

The business logic should not need to be rewritten just because the data provider changes from mock to real.

---

### S0 · Required mock data

The repository should contain shared mock scenarios, for example:

```text
mock-data/
├── farm-001/
│   ├── farm-profile.json
│   ├── season.json
│   ├── farm-state.json
│   ├── tasks.json
│   ├── problems.json
│   ├── weather.json
│   └── disease-result.json
│
└── farm-002/
    └── ...
```

The mock structure must follow the shared contracts.

---

### S0 · 7. Golden Farm Integration Scenario

The team will maintain at least one shared fictional farm used for integration testing.

Example:

```text
FARM-001

Farmer:
Rahim

Location:
Comilla

Land:
2 acres

Soil:
Loamy

Irrigation:
Available

Crop:
Potato

Planting date:
20 Nov

Current growth stage:
Vegetative

Open problem:
Possible leaf disease

Weather:
Heavy rain expected
```

The exact values are examples only; the team may define the final test scenario while preserving the same contract structure.

### S0 · Golden-flow test

The complete system should eventually support this sequence:

```text
Farm onboarding
      ↓
Crop recommendation
      ↓
Crop selected
      ↓
Season plan
      ↓
Farm Brain creates tasks
      ↓
Weather affects a task
      ↓
Weather alert generated
      ↓
Farmer asks a contextual question
      ↓
Chatbot answers using farm context
      ↓
Farmer uploads crop image
      ↓
Disease detection
      ↓
Problem written to Farm Brain
      ↓
Future chatbot/check-ins can see the problem
```

---

### S0 · 8. Module Interfaces

Each module must clearly document:

```text
INPUTS
OUTPUTS
OWNED DATA
READ-ONLY DATA
STATE CHANGES
DEPENDENCIES
MOCK INPUTS
INTEGRATION TESTS
```

### S0 · Conceptual interfaces

### S0 · M1 → M2

```text
FarmProfile
```

### S0 · M2 → M3

```text
SeasonPlan
GrowthStages
InitialTasks
```

### S0 · M3 → M4

```text
FarmLocation
CurrentCrop
CurrentGrowthStage
RelevantTasks
FarmState
```

### S0 · M3 → M5

```text
FarmProfile
CurrentCrop
CurrentGrowthStage
Tasks
OpenProblems
FarmState
```

### S0 · M5 → M6

```text
Image
Crop
GrowthStage
OptionalSymptoms
```

### S0 · M6 → M3

```text
DiseaseResult / ProblemUpdate
```

### S0 · M4 → M3

When a weather event requires a farm-state or task adjustment, the change must be represented through the agreed Module 3 state/task contract rather than a private duplicate state.

### S0 · M4 → M2 (2026-10-29 analytical extension)

```text
DistrictClimateBundle
Historical/satellite/climate-scenario features
Source QA, coverage, resolution, method/cache versions and provenance
```

This is a read-only cache/feature interface; historical acquisition does not read M2 or require M3. M2 owns agronomic interpretation and comparative outputs. The new public read-only district `/advisory` route and authenticated farm scenario/write paths are specified in the detailed Section 20 plan. Record additive field/error contracts before implementation; existing M1-M6 routes remain compatible.

---

### S0 · 9. Ownership Rules

### S0 · Rule 1 — Single owner per data domain

| Data | Owner |
|---|---|
| Farmer/Farm Profile | M1 |
| Crop suitability knowledge | M2 |
| Season Plan | M2 |
| Growth-stage operational state | M3 |
| Tasks | M3 |
| Farm Problems | M3 |
| Farm Check-ins | M3 |
| Weather processing | M4 |
| Weather Alerts | M4 |
| District environmental acquisition, QA and caches | M4 |
| Planting-window science and rotation comparison | M2 |
| Farmer priorities, soil measurements and reported rotation history | M1 |
| Conversation | M5 |
| Disease Analysis | M6 |
| Disease Result content | M6 |
| Persistent farm-state representation of disease/problem | M3 |

A module may **read** another module's data, but it must not silently create a competing source of truth.

---

### S0 · 10. Development Rules

### S0 · Rule A — Follow the plan

**Always follow this `plan.md`.**

Do not independently redesign the overall architecture.

Do not move features between modules without team-level agreement.

Do not change another module's responsibility.

Do not change shared contracts unilaterally.

Do not introduce a new cross-module dependency without agreement.

---

### S0 · Rule B — Suggestions are allowed only inside your module

A developer may propose:

- Better implementation approaches
- Better internal structure
- Refactoring
- Alternative algorithms/models
- Better UX within their module
- Better testing strategies
- Additional internal helper functions

**Only for their own module.**

Example:

> M4 developer suggests a better alert-suppression strategy.

Allowed.

Example:

> M4 developer decides that M3 should no longer own farm problems.

Not allowed without team agreement.

---

### S0 · Rule C — Shared contract changes require team agreement

The following are shared and therefore cannot be changed by one person alone:

- Domain model names
- Required shared fields
- Field meanings
- Module boundaries
- Module ownership
- Cross-module interfaces
- Dependency direction
- Integration flow

A proposed change should be discussed and agreed upon before modifying the shared contract.

---

### S0 · Rule D — Use mocks to stay independent

If your dependency is unfinished:

**Do not wait.**

Build a mock implementation that follows the agreed contract.

---

### S0 · Rule E — Integrate incrementally

Do not wait until the end to merge everything.

Replace mock dependencies with real implementations gradually.

---

### S0 · 11. Git / Branching Strategy

Recommended branch structure:

```text
main
│
├── module/farm-profile
├── module/crop-advisor
├── module/farm-brain
├── module/weather
├── module/chatbot
└── module/disease
```

### S0 · Rules

- Each developer primarily works in their own module branch.
- Keep commits focused.
- Do not make unrelated edits to another developer's module.
- Shared contract changes must be discussed before merging.
- Pull requests should explain what changed and which contract/interface is affected.
- `main` should remain integration-ready.

---

### S0 · 12. Integration Workflow

### S0 · Stage 1 — Contract setup

All team members agree on:

```text
Domain models
Input/output contracts
Module ownership
Dependency direction
Golden Farm
Mock data format
```

Then development starts in parallel.

---

### S0 · Stage 2 — Independent implementation

Each developer builds their module against the contract and mock data.

```text
M1 → mock-free / independent
M2 → mock M1
M3 → mock M2
M4 → mock M3 + mock weather
M5 → mock M1 + M3 + M2 knowledge
M6 → mock M3
```

---

### S0 · Stage 3 — Incremental replacement

Replace mocks with real module outputs in controlled steps.

Example:

```text
M2
 ↓
Mock M1
 ↓
[Integration]
 ↓
Real M1
```

Then:

```text
M3
 ↓
Mock M2
 ↓
[Integration]
 ↓
Real M2
```

Continue without stopping work in other modules.

---

### S0 · 13. Testing Strategy

Each module must have:

### S0 · Unit tests

Test internal logic without depending on other modules.

### S0 · Contract tests

Verify that the module's inputs and outputs match the shared contract.

### S0 · Integration tests

Verify real communication with connected modules.

### S0 · Golden-flow test

Verify the complete farmer journey using the shared Golden Farm.

---

### S0 · 14. Definition of Done Per Module

A module is considered complete only when:

```text
[ ] Responsibilities from this plan are implemented
[ ] Module works independently with mock data
[ ] Shared contract is respected
[ ] Inputs/outputs are documented
[ ] Core edge cases are handled
[ ] Unit tests exist
[ ] Contract tests exist
[ ] Integration path is defined
[ ] No unrelated module code was changed
[ ] Module can be integrated without redesigning another module
```

---

### S0 · 15. Recommended Development Milestones

### S0 · Milestone 0 — Shared Contract

Complete before serious parallel implementation:

- Domain objects
- Input/output contracts
- Ownership rules
- Golden Farm
- Mock data
- Repository structure

All six developers can then start together.

---

### S0 · Milestone 1 — Core Farm Lifecycle

The system can:

```text
Onboard farmer
   ↓
Build Farm Profile
   ↓
Recommend crops
   ↓
Select crop
   ↓
Generate Season Plan
   ↓
Create Farm Brain state/tasks
```

---

### S0 · Milestone 2 — Continuous Assistance

Add:

```text
Farm monitoring
Weather intelligence
Contextual chatbot
Proactive alerts/check-ins
```

---

### S0 · Milestone 3 — Disease Loop

Add:

```text
Image upload
   ↓
Disease detection
   ↓
Disease result
   ↓
Farm problem
   ↓
Farm Brain
   ↓
Future assistance
```

---

### S0 · Milestone 4 — Harvest & Season Close

Add:

```text
Harvest guidance
   ↓
Harvest result
   ↓
Season close
   ↓
History
   ↓
Future crop advisory context
```

---

### S0 · 16. What We Will NOT Do

Until explicitly agreed by the team, do not expand the architecture with unrelated features such as:

- Marketplace
- Payments
- Social network/community system
- Supplier marketplace
- Satellite features unrelated to the NASA agricultural/environmental analysis explicitly required in Section 20
- Complex financial products
- Unrelated farm management systems

These may be future ideas, but they are not part of the current six-module plan.

---

### S0 · 17. Final Architecture

```text
                         🌾 AI FARMER ASSISTANT
                                  │
                         Unified Chat Interface
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ M5 Conversational Layer  │
                    └────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
   ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
   │ M1 Farm     │       │ M2 Crop     │       │ M6 Disease  │
   │ Profile     │       │ Advisor     │       │ Detection   │
   └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
          │                     │                       │
          └─────────────────────┼───────────────────────┘
                                ▼
                    ┌──────────────────────────┐
                    │ M3 FARM BRAIN            │
                    │ State • Tasks • Problems │
                    │ Growth • Monitoring      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ M4 Weather Intelligence  │
                    │ & Alerts                 │
                    └──────────────────────────┘
```

The architecture above describes **runtime relationships**. It does **not** dictate sequential development.

Section 20 adds a separate analytical path: `M4 district source caches → M2 planting-window/rotation compute → advisory UI + M5 explanation`. Confirmed selections continue through `M2 SeasonPlan → M3 tasks/state`; exploration alone never changes the active season.

Development remains parallel through contracts and mocks.

---

### S0 · 18. Team Commandments

1. **Follow this plan.**
2. **Do not change another module's scope.**
3. **Do not change shared contracts unilaterally.**
4. **Work independently using mocks.**
5. **Document every module's inputs and outputs.**
6. **Keep one source of truth for shared farm state.**
7. **Integrate incrementally, never all at once.**
8. **Module-level suggestions are welcome inside your own module.**
9. **Cross-module changes require team agreement.**
10. **The farmer sees one assistant, even though the system has six modules.**

---

### S0 · 19. Change-Control Statement

**This `plan.md` is the baseline project plan and must be treated as immutable during normal development.**

Developers may improve their own module internally and may add implementation-level notes under their own module, but they must not change the project's overall plan, module ownership, shared contracts, dependency structure, or scope on their own.

Any proposed cross-module or project-level change must be raised to the full team for agreement before it is applied to `plan.md`.

Until such agreement occurs, **continue following the existing plan exactly as written.**

The dated Section 20 planning amendment and its accepted adaptive-decision follow-up were explicitly requested by the project owner on 2026-10-29. They record the required product direction and proposed additive interfaces; they do not authorize an individual implementer to invent incompatible fields, apply undocumented migrations or move another module's data ownership.

---

### S0 · 20. Organizer and Final Challenge Delivery Requirements — 2026-10-29

The complete implementation and verification specification is [NASA planting windows, rotation decisions and Bangla mobile delivery](2026-10-29-nasa-planting-window-and-rotation.md). Its Section 13 maps all five organizer images and every part of the [preserved final statement](references/2026-10-29-organizer/problem-statement.md) to owners, outputs and release evidence. The original optional considerations are included in this project's scope because the user explicitly requested complete coverage.

### S0 · Required outcomes

1. District/crop/season selection for Bangladesh, including Rajshahi/Aman, source-backed rainfall-onset and thermal analysis over 2001-2025, and an actionable planting/transplanting sentence with a supported revised window.
2. Fixed 2001-2012 versus 2013-2025 onset distributions; Mann-Whitney U statistic/p-value with assumptions; signed whole-day shifts, effect/uncertainty and complete threshold sensitivity at 15/20/25 mm. The organizer's example eleven-day shift is illustrative, never a hardcoded outcome.
3. Crop-specific sourced GDD bases/calendars, explicit usable-rain definition with a true consecutive dry-spell rule, and tests for each pure function in `backend/src/compute/agro.py`.
4. Versioned district Parquet, all-64-district POWER/NDVI/SMAP coverage over actual available periods, the additional source families and local data in the detailed plan, and `OFFLINE=1` that prevents all live analytical fallback.
5. Existing FastAPI app exposes `GET /advisory?district=&crop=` with explicit season resolution, shifts, both distributions, statistics, assumptions and provenance; farm-specific scenarios remain authenticated and owner scoped.
6. Current rotation plus two evidence-supported alternatives, with soil health, nutrient cycling, cover/bare periods, erosion/infiltration potential, pests, water, forage, market/resources, farmer priorities, gaps and uncertainty explained.
7. Bangla/English React Native UI with a district map, two-period and GDD charts, timelines/overlays, labeled climate/what-if exploration, visible assumptions/citations and strictly under-160-character summaries suitable for sharing/SMS composition.
8. Explain satellite versus ground data and scientific terms; use realistic spatial support, holdout validation and method comparisons. No fabricated field measurements, future-weather certainty or unsupported yield/profit/water-saving figures.
9. Preserve all-farm listing after sign-in, farm-scoped chat, confirmed M2-to-M3 season/task handoff and M6 integration. Add the voice plan's Android speech/tap fallback, real-phone checks and offline safety without replacing existing auth/state stores.
10. Apache-2.0 original code with upstream/data/model rights retained, public working repo, dataset URLs and methods in README, completed official project page, exact challenge identification, demonstration video and genuine contribution evidence.
11. After the required core flow, add the [accepted adaptive decisions](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md): M2 chooses a useful farmer-observable question and computes bounded feasible ranges; M1 persists confirmed answers; dated M4 evidence prompts a supported Plan B; M5 presents the exact diff and confirmation; transaction-aware M2/M3 operations apply it once. Preserve completed work, planting history and all farm/season ownership. No paid AI is needed for these deterministic rules.

### S0 · Milestones and completion policy

Follow the detailed plan's pre-event preparation and organizer schedule: Day 1 morning compute/tests; afternoon map/crop/distributions; evening advisory/assumptions and recording by 18:30 event-local time; Day 2 morning bilingual phone UI, summaries and an outside-team test; noon freeze/record/submit. This is an initial vertical-slice milestone, not a guarantee that the entire full scope fits 48 hours.

The screenshot's cut order is retained as a contingency, not an automatic waiver of the user's full scope. Report partial milestones honestly and keep outstanding gates open. Full completion requires V01-V15 in the detailed plan plus A01-A08 in the accepted adaptive-decision specification: data, science, agronomy, API, offline, isolation, lifecycle/rotation, decision questions/envelopes/policies, atomic confirmed execution, responsive browser, physical Android, usability, production and submission evidence. Planning checkboxes do not establish implementation or field validation. Rice-floor portfolio optimization, shared-pump scheduling and other research suggestions are not part of this accepted three-feature increment.


</details>

<a id="source-s1"></a>

## Appendix S1 — Complete source snapshot

Source: `docs/plans/2026-10-29-nasa-planting-window-and-rotation.md` at `336bf6c`. The reconciled final rules above take precedence. Full text is retained for requirement traceability; source headings are prefixed and local links relocated for this combined file.

<details>
<summary>Read complete S1 specification (26 source headings)</summary>

### S1 · FieldShift BD — NASA Planting Windows, Rotation Decisions and Bangla Mobile Delivery

**Revised:** 2026-10-29, Asia/Dhaka. **Status:** implementation plan; no feature is complete merely because it appears here.

**Authority:** the user's 2026-10-29 request makes the supplied organizer instructions and the complete final problem statement the required product scope. This document specializes [the canonical project plan](../../plan.md) without replacing the six owners or creating a seventh module. The [voice plan](2026-10-06-voice-first-bangla.md) supplies the detailed accessibility channel. Existing runtime contracts remain the compatibility baseline; additive contracts below must be recorded before implementation, rather than silently changing another owner's fields.

**Accepted follow-up:** the owner approved three linked additions after competitor research: a decision-driven field question, a rotation robustness envelope and conditional Plan B with farmer confirmation. The [adaptive-decision specification](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md) is the implementation detail for §15 and additional gates A01-A08. All original requirements below remain required; see the [complete plan index](README.md).

### S1 · 1. Source material and scope interpretation

Preserved organizer inputs:

1. [Brief and killer demo](references/2026-10-29-organizer/01-brief.png).
2. [48-hour schedule, pre-build and cut order](references/2026-10-29-organizer/02-48-hour-plan.png).
3. [Datasets, onset example and validity guidance](references/2026-10-29-organizer/03-data.png).
4. [Architecture diagram](references/2026-10-29-organizer/04-architecture.png).
5. [Build prompt](references/2026-10-29-organizer/05-build-prompt.png).
6. [Unedited final problem statement](references/2026-10-29-organizer/problem-statement.md), copied from the user's original file outside the repository.

The deliverable combines two connected decisions: **when to plant/transplant** and **which multi-season rotation to choose**. The organizer's rice planting-window example does not remove the final statement's rotation, soil-health, resource and uncertainty requirements. Although the original statement uses “may” for many considerations, the user has requested their inclusion: every consideration is mapped below to implementation and evidence. Alternative datasets phrased as “MODIS or VIIRS”, “Landsat/MODIS” or “SRTM or other elevation” can be satisfied by the chosen named product; each choice is documented. All other individually named source families have a scoped role in the full delivery.

**Full target:** all 64 Bangladesh districts, at least three source-supported crop/season profiles, current rotation plus at least two alternatives, all mapped functions, and an installable Android app. A crop/season profile is not automatically a distinct rotation strategy. Rice seasons such as Aman must not be inserted as duplicate M1 crop species; use the existing Rice crop and an explicit advisory season/variety profile.

**48-hour milestone:** the organizer schedule in §11 is a timed vertical slice after data preparation. The screenshot's fallback order is documented, but no scope cut is automatically authorized: a one-district/one-crop demo, missing SMAP or missing map is a partial milestone, not full completion. Unavailable scientific information is shown explicitly; missing evidence must be resolved or reported as a release gap, never fabricated to turn a checkbox green.

### S1 · 2. Product outcome and acceptance narrative

A farmer signs in, sees all saved farms and selects a farm to open its scoped chat. From chat or a visible advisory entry, they select a district and crop/season, review their saved soil/resources and state their priorities. The app states a short actionable planting/transplanting advisory in Bangla, shows the earlier/recent onset distributions and thermal evidence, compares three rotations and offers a sourced explanation. The farmer selects an option; only an explicit confirmed M2 action can create/update a season plan, and M3 owns resulting tasks/current stage. M5 speaks the same deterministic result and does not recalculate the science.

**Organizer demo:** Rajshahi → Aman rice → observed usable-rain onset shift since 2001 → two distributions → revised transplanting window → assumptions and sources → short Bangla explanation on a phone. The screenshot's “eleven days later” is illustrative, **not a target to hardcode**. Use the actual calculated sign and magnitude; report weak/no evidence if appropriate. No historical comparison establishes causation or guarantees next-season weather.

Acceptance requires a meaningful final sentence, not only a chart. When evidence is inadequate, the meaningful sentence explains what cannot be recommended and what field information the farmer should check. Farmer judgment and local expertise remain explicit.

The accepted extension makes that information request decision-driven: one safe answer that changes the supported feasible set, then an explanation of tested calendar/resource limits and a saved contingency. Updated evidence may propose a precise plan/task change; the farmer reviews it before a version-checked, idempotent M2/M3 transaction. A post-planting crop switch cannot rewrite actual history.

### S1 · 3. Actual starting point and integration constraints

Source-inspection baseline: commit `1077a06`; the 2026-10-28 review is [recorded here](../research/2026-10-28-challenge-readiness-review.md). Recheck the working tree before implementing.

| Reuse | Remaining work |
|---|---|
| Existing M1 password auth, owner-scoped farmland profiles, administrative fields, coordinates, soil/land type, irrigation, equipment and budget | Add missing rotation history, relevant soil measurements and farmer priorities through a documented M1-compatible contract |
| Existing M2 evidence gates, catalog, recommendation and season APIs | Source verified crop calendars/stages/tasks, implement planting-window/rotation logic; shipped knowledge does not yet enable season-plan generation/activation |
| Existing M3 tasks, problems, check-ins and operational state | Integrate confirmed plan output; prevent duplicate task generation and stale-season writes |
| Existing M4 NASA POWER/Open-Meteo adapters | Add long historical, satellite and climate-scenario ingestion/cache; existing 30-day history is insufficient |
| Existing M5 farm chat, API client, secure token storage and fallback path | Add Bangla outputs, advisory intent, typed result rendering and voice/confirmation integration |
| Existing M6 disease loop | Preserve healthy/uncertain/repeat behavior; reconcile its present automatic Problem write with the voice confirmation policy before changing it |
| Expo 57 / React Native 0.86 / FastAPI / SQLAlchemy / PostgreSQL / Alembic | Configure actual Android identity, release API URL, production runtime, cache bundles and real-phone verification |

Preserve all existing routes and field meanings. Do not replace the existing auth system, create a parallel farm store or move M3 ownership into the advisor. Reuse existing columns and JSON metadata only when semantics match; do not hide arbitrary schemas in unrelated fields. Persistent additions need an explicit schema/contract diff and forward/backward migration review. No migration or code change is performed by this planning update.

### S1 · 4. Responsibility and additive interfaces

| Owner | Planned responsibility | Interface and invariants |
|---|---|---|
| M1 | Farmer/farm context, previous rotation, measured soil properties, priorities/constraints | Existing profile plus additive `RotationHistoryInput`, measurement provenance and `FarmerPriorities`; tenant scoped, unknown differs from zero |
| M4 | Environmental source acquisition, QA, harmonization, district Parquet and map layers | Read-only `DistrictClimateBundle`; history, forecast, satellite observation and projection kept distinct; no call to M2 or M3 is required to build a district cache |
| M2 | Crop/variety/season rules, onset/GDD/window calculation, comparative statistics, rotation scenarios | Pure compute result → `PlantingWindowAdvisory` and `RotationComparison`; no operational writes on exploration |
| M3 | Active season state, confirmed task creation/changes, problems | Existing `SeasonPlan`/initial-task handoff; idempotent effects and current-season checks |
| M5 | Conversation, Bangla/English explanation, voice, proposed-action routing | Renders M2 facts and evidence IDs; cannot invent days, doses, yield or source claims; executes through the owning module |
| M6 | Disease evidence and disease-result lifecycle | May inform crop-family/problem constraints through existing M3 state; not the planting-window calculator |
| Frontend/shared infra | Mobile map, charts, evidence, audio, offline UI and deployment | Expo Router, React Native SVG/vector icons; no image icons, no imitation time/network status strip |

```text
POWER · IMERG · SMAP · NDVI + other scoped NASA layers + local agronomy
                 │ pre-event/source refresh (M4)
                 ▼
     versioned district Parquet + geometry + manifests
                 │ read-only DistrictClimateBundle
                 ▼
  backend/src/compute/agro.py (M2): onset · GDD · distributions · shift
                 │                  └── rotation comparison + uncertainty
                 ▼
       existing FastAPI app: GET /advisory
                 │
     ┌───────────┴─────────────────────────┐
     ▼                                     ▼
 district map + two-period charts   actionable Bangla/English sentence
     └──────────────────┬──────────────────┘
                        ▼
            assumptions + dataset citations
                        │ confirmed choice only
                        ▼
        existing M2 SeasonPlan → M3 tasks/state
                        └────────── M5 scoped chat + speech
```

The organizer's `src/compute/agro.py` lives under the existing **backend** (`backend/src/compute/agro.py`), not inside Expo's route directory or a new server. Package it normally and call it from a small M2 service adapter; pure functions have no HTTP, DB, network or audio side effects. Data download, normalization and rendering stay outside compute.

### S1 · 5. Data preparation, provenance and offline contract

### S1 · 5.1 Required source families

| ID | Source and fields | Role and coverage discipline |
|---|---|---|
| D01 | NASA POWER: daily rainfall, T2M, solar radiation; Tmin/Tmax and wind/humidity if required by a documented method | Backbone for 2001-2025 district onset/GDD. Pin actual parameter IDs/units (`PRECTOTCORR`, `T2M`, `ALLSKY_SFC_SW_DWN` after metadata verification). A district centroid is a representative grid point, not a district-wide mean or field observation |
| D02 | GPM IMERG precipitation | Spatial rainfall and extreme-precipitation comparisons; select run/version and consistent daily aggregation. Explain differences from POWER; never average inconsistent products without an evaluated method |
| D03 | SMAP soil moisture | Wetness anomaly and suitability context over its real available period from 2015 onward. Retrieval quality, water/flood contamination and coarse footprint matter; surface wetness is not a guaranteed workability/root-zone measurement |
| D04 | MODIS NDVI (chosen MODIS/VIIRS option; candidate MOD13Q1 collection 6.1) | QA-masked vegetation/green-up/season transition and bare-field proxies, 2001-2025 where valid; composite interval is not an exact transplanting date. If VIIRS is substituted, pin its period and cross-sensor harmonization |
| D05 | Landsat surface reflectance/temperature products | Finer land-cover, vegetation and stress context; mask cloud/shadow and document sampling limitations. Validate selected collection and coverage before computation |
| D06 | ECOSTRESS temperature/ET products | Plant heat/water-stress and evaporation/ET evidence over available acquisitions; retain observation times and retrieval/model limitations |
| D07 | GRACE and GRACE-FO water-storage anomalies | Long-term regional water-storage context and gaps; not district groundwater volume, well availability or field-level maps |
| D08 | SRTM elevation (chosen elevation option) | Slope/terrain/erosion susceptibility context; terrain alone cannot establish flood risk, infiltration or erosion rate |
| D09 | GEDI biomass/structure samples | Explicitly scoped biomass/agroforestry context where sample coverage exists; not annual-crop soil organic matter or universal crop biomass |
| D10 | NASA downscaled climate scenarios, e.g. NEX-GDDP-CMIP6 | Predictive-climate exploration required by organizer brief. Pin scenario, models, baseline, future period and bias/harmonization procedure; show ensemble spread. Projections and user “what-if” sliders are separate from observed 2001-2025 distributions and near-term forecasts |
| D11 | Local soil, BARC/BRRI/DAE crop/variety calendars, stage definitions, season tasks, water/forage/legume traits and market/resource information | Explainable local applicability through existing evidence policies; record exact source and claim. Do not label farmer-reported soil as lab tested, zoning as field fit, or unsourced economics as expected profit |
| D12 | District boundaries and crop/land-cover mask | Reuse M1 canonical district identifiers/aliases. Pin boundary/mask version, license, source, crop mask age and aggregation weights; mapping must not introduce a competing location catalog |

Every family above needs a working ingestion/normalization path and a tested role in the full release. Its actual applicability/coverage is returned per district. A genuine empty footprint is a documented unavailable signal, not zero and not a fabricated substitute. D01/D03/D04 pre-caches are required across all 64 districts over their available periods. Other rasters are clipped/aggregated before release; no full global archive or raw raster download in the APK. Release cache completeness is audited, with per-variable coverage and explicit gaps.

### S1 · 5.2 Cache schema and build procedure

- Store analytical files outside PostgreSQL: `backend/data/climate/<cache_version>/<district_code>/<dataset>.parquet`, with `manifest.json`, a coverage report and checksums. Commit the small manifests, algorithms, licenses and a reproducible download/refresh command. Host larger allowed artifacts as versioned release assets with hashes, not opaque untracked laptop files.
- Common columns: `district_code`, `source_product`, `source_version`, `variable`, `date_or_interval_start`, `interval_end`, `value`, `unit`, `quality_flag`, `valid_count`, `coverage_fraction`, `aggregation_method`, `native_grid_or_footprint`, `retrieval_id`. Preserve native observations separately when daily alignment would imply false precision.
- Manifest: provider/landing URL and request or asset IDs, retrieval/publication dates, actual temporal coverage, CRS/spatial/temporal resolution, scale/offset/fill value, license/attribution, boundary/mask version, transformations, source checksum, cache checksum and method/config version. Public metadata contains no tokens or farmer identifiers.
- D01 includes full calendars for 2001-01-01 through 2025-12-31 and explicit valid/missing flags; deduplicate requests for districts sharing grid cells, respect provider limits, retry with bounded backoff and checkpoint downloads.
- Freeze `2001-2012` and `2013-2025` as the organizer's primary comparison periods. Do not silently slide them forward with the current date. Later observations are a separately labeled update.
- Choose and persist the POWER daily time standard; distinguish UTC, local solar time and Asia/Dhaka civil days. Do not relabel a daily LST total as a measured Bangladesh midnight-to-midnight total.
- Harmonize district/crop-mask aggregates and analysis intervals with documented area weights, valid-pixel thresholds and quality masks. Rainfall totals, temperature means, NDVI composites and monthly storage anomalies need different aggregation rules. No nearest-neighbor upscaling can create field-scale precision.
- `OFFLINE=1` **forces cache reads** throughout the analytical process: no NASA, weather, LLM, geocoding, remote map tiles or implicit model downloads. Missing/corrupt data returns a typed cache error or explicit per-layer unavailability; never fall back to live data silently. Prove this with network-denied tests.
- Server cache-only mode is distinct from a disconnected phone. Bundle permitted compact district geometries and release summaries on-device and persist last-viewed results with source dates; full rotation recalculation offline requires a tested local implementation or precomputed supported scenarios. Queued writes are not described as completed.

### S1 · 6. Agronomic compute and statistical specification

### S1 · 6.1 Agronomic configuration

For each district/crop/variety/season, store source-backed calendar, nursery/sowing versus transplanting distinction, onset search window, rain threshold, wet-day definition, dry-spell rule, degree-day base, optional upper cap, thermal targets, photoperiod limits and evidence IDs. Agreement with an agronomically informed person, as requested in the organizer pre-build list, is recorded with date and scope; it does not replace source provenance or silently approve unrelated knowledge. Unknown values block the relevant numerical recommendation, rather than introducing universal rice defaults.

Bangladesh Aman photoperiod/variety behavior and nursery age must be considered before moving a transplanting date from a thermal calculation. A regional rain-onset change is not itself sufficient authorization to shift every crop calendar by the same number.

### S1 · 6.2 Usable-rain onset

Organizer demonstration parameters: rolling window 7 days, rainfall sum at least 20 mm, maximum dry spell 7 days. These are configurable demonstration settings pending local justification, not scientifically universal constants. Store a versioned definition and show it in both languages.

The screenshot example's comment and body do not fully agree: checking for any wet day in the next seven days does not establish “no dry spell longer than seven days”, and its loop can miss the last candidate window. Implement the stated agronomic definition correctly rather than reproducing that bug.

The implementation must:

1. Use a complete, ordered, dated series; reject duplicates/invalid negatives/fill values and preserve missing days.
2. Restrict candidate start dates to the source-backed crop-season search window, with sufficient trailing data even across year boundaries.
3. Require the configured rainfall total over the candidate window, and evaluate **consecutive** dry days in a declared post-onset verification horizon. Publish the horizon and whether “dry” means `<` or `<=` the wet-day threshold. No hidden choice of horizon.
4. Return the first valid onset date, with the candidate-window start explicitly defined as the convention, or a reason such as `no_onset`, `insufficient_data` or `truncated_verification`. Do not claim rain physically began on a dry first day of a summed window.
5. Distinguish a true no-onset year from missing/corrupt data. Report annual exclusions and no-onset counts; analyze their frequency separately so conditioning only on valid onsets does not hide drought years.
6. Repeat the entire annual detection and period comparison at rainfall thresholds **15, 20 and 25 mm** for the organizer's ±5 mm sensitivity requirement; report sign/magnitude/support changes. Keep 7-day window/dry-spell parameters explicit and add further justified sensitivity checks.

### S1 · 6.3 Growing-degree-day accumulation

Provide a deterministic function with a documented temperature method, planting/nursery/transplanting reference, base, cap and units. A supported daily-mean method is `daily_gdd = max(0, T2M - Tbase)`; if capped, use the precisely documented capped method consistently. An average-Tmin/Tmax method is a different version, not an interchangeable fallback. Aggregate in degree-Celsius days, never interpret Kelvin as Celsius.

Use crop-specific sourced base/target values. Missing days do not become zero thermal accumulation. Emit completeness flags or an explicitly labeled, validated imputation method. Compare annual cumulative curves and target-reaching dates between the same two periods. Document photoperiod/water effects and avoid treating GDD alone as a validated phenology model.

### S1 · 6.4 Two-period comparison and proposed shift

- One annual onset sample per district/crop/season/year; nominal maximum sample counts are 12 and 13, not thousands of daily pseudo-replicates.
- Express onset as day offset from a common season anchor so leap years and cross-year seasons are comparable. Retain actual dates/year labels for display.
- Return both annual distributions, counts, exclusions, medians, spread, effect size and an uncertainty interval, plus a two-sided **Mann-Whitney U** statistic/p-value and the pinned implementation/method. Handle ties using a documented suitable method. Tests verify the reported statistic orientation and method.
- Mann-Whitney tests distribution differences under assumptions; it does not by itself prove an eleven-day median shift or a climate cause. State independent-year assumptions; assess serial dependence and use a suitable blocked resampling sensitivity where relevant. Label small samples/weak evidence. When surveying many district/crop pairs, report the multiple-testing procedure and retain raw and adjusted values where used.
- Compute `observed_onset_shift_days = median(recent) - median(earlier)`, with **positive = later**. Keep the raw estimate and expose a whole-day display using one named rounding rule (ties away from zero). Do not mix date arithmetic with an undocumented rounding convention.
- Keep `observed_onset_shift_days` separate from `recommended_window_shift_days`. Derive a candidate window from the sourced existing calendar and onset/thermal constraints, then evaluate wetness, heat, flood/terrain context, photoperiod, irrigation, nursery needs, resources and rotation overlap. Return the rounded final recommendation only when supported. No feasible window → explain constraints; never silently clamp an infeasible date into an apparently safe recommendation.
- Fix a reproducible resampling seed/config. Return `supported`, `uncertain`, `insufficient_evidence` or `no_feasible_window` and the explanation. A p-value alone is never the advisory acceptance gate.

### S1 · 6.5 NDVI, soil moisture and model validation

Use crop-masked QA-filtered NDVI to evaluate whether predicted seasonal windows align with observed green-up/season transitions over available years. Farmers' actual planting dates require consented ground records; NDVI is a phenology proxy, not proof of an individual planting decision. Use year-based holdouts, report timing error/coverage and exclude validation leakage.

SMAP anomalies, ECOSTRESS ET/temperature, Landsat stress indicators and GRACE regional storage add scoped evidence/limitations. Soil workability needs local soil texture, drainage and field assessment; satellite surface moisture alone cannot establish it. Low NDVI is not uniquely a bare field, heat or disease.

Compare at least an existing-calendar baseline, rain-onset-only method and combined rain/thermal/local-constraint method. Report performance, uncertainty and failure cases; retain a simpler method if the richer method is not better validated. Define acceptance metrics and agronomically meaningful error tolerance before examining holdout results.

### S1 · 7. Full rotation and soil-health decision support

Build at least three **multi-season strategies** per supported farm: current rotation plus two locally evidenced alternatives. Calendar shifts of the same crop alone do not satisfy a meaningful three-rotation comparison. Ask for missing current rotation rather than inventing it. Include source-supported legume/cover/deep-rooting/drought-tolerant options where locally feasible, expanding M1's catalog through its owner.

Each strategy returns a common dated calendar, explanatory factors, applicability, unavailable evidence and tradeoffs for:

- Nutrient cycling and nitrogen-fixing potential; fixation potential is not an automatically known fertilizer credit.
- Soil cover, bare-field intervals, organic-matter contribution potential, infiltration and erosion susceptibility. No unmeasured soil-carbon or infiltration improvement percentages.
- Crop-family/pest-cycle considerations, informed by M3 open problems and sourced host relationships. No guaranteed disease prevention.
- Water demand/irrigation feasibility, historical heat/dry-spell/extreme-rain/frost exposure and climate-scenario sensitivity. For quantitative ET/water balance use a documented method such as FAO-56 with appropriate crop/soil inputs and paddy-specific losses where relevant.
- Forage value, equipment/labor access, water availability, budget and market suitability. Cite price/cost location/date and use ranges; without evidence give qualitative constraints rather than promised income.
- Farmer priorities: conserve water, improve soil structure, earn supplemental income, forage or preferred crops. Show how priority changes alter tradeoffs and exclusions; no opaque single score without factor explanations.

Historical observations, near-term forecasts and future climate scenarios appear as separate evidence modes. Future projections carry scenario/model/period uncertainty; sliders changing rain/temperature are labeled **what-if**, not a weather prediction. No scenario automatically mutates an active farm season or creates tasks.

### S1 · 8. HTTP and result contract

Add to the existing FastAPI application:

```text
GET /advisory?district=<canonical-code-or-supported-alias>&crop=<catalog-key>&season=<season-key>
```

The organizer's district/crop-only form must work: when season is omitted, use a single configured unambiguous profile, or return selectable profiles instead of guessing. Resolve `Aman rice` as Rice + Aman advisory profile. A successful numerical result includes:

| Field | Required meaning |
|---|---|
| `district`, `crop`, `season`, `method_version`, `cache_version`, `result_id` | Resolved canonical identity and reproducible result identity |
| `status`, `warnings`, `evidence_gaps` | Decision support/uncertainty, not just HTTP success |
| `observed_onset_shift_days_raw`, `observed_onset_shift_days`, `recommended_window_shift_days` | Signed estimate, whole-day display and distinct agronomic recommendation; unsupported values are null |
| `baseline_window`, `recommended_window`, `window_kind` | Sourced calendar, computed feasible dates and sowing/transplanting distinction |
| `periods` | Fixed earlier/recent ranges, annual onset samples, exclusions/no-onset counts, spread/medians; both chart-ready distributions |
| `thermal` | Base/cap/method, annual GDD curves or compact equivalent, target-reaching dates, completeness |
| `statistics` | Mann-Whitney U, p-value, method, effect size, uncertainty and assumptions |
| `sensitivity` | Full ±5 mm threshold results and stability assessment |
| `validation`, `environmental_evidence` | NDVI/SMAP and other source contributions, holdout metrics, missing coverage |
| `assumptions`, `provenance` | Every configurable agronomic/statistical assumption and dataset/source/license/hash block |
| `advice_bn`, `advice_en`, `speech_text_bn`, `sms_summary_bn`, `sms_summary_en` | Same supported facts, concise actionable sentence first, summaries strictly below 160 Unicode characters |

District-only results contain no private farm details and may be served as bounded public read-only cache results with request controls. Farm-specific rotation exploration uses an authenticated M2 endpoint such as `POST /advisor/farmlands/{id}/rotation-comparisons`, deriving farm ownership/context from saved M1 data. It returns three strategies and their referenced window results. Selecting a scenario uses existing/explicitly extended M2 write contracts with confirmation and idempotency; a public query cannot select a farmer's crop.

Errors: invalid identifiers/parameters → documented 422; ambiguous season → documented selectable response; missing source cache → 503 with a typed code; missing agronomic evidence → valid structured insufficient-evidence result with null numerical recommendation. Never return a fake zero-day shift or an HTML server error as an advisory. A missing supplemental layer may permit a qualified result only if the agreed minimum evidence still holds.

No actual SMS delivery is needed merely to satisfy “could be sent”. Implement copy/share/compose of the SMS-length summary with a confirmation before opening an external send action. Display Unicode character and estimated segment counts: a Bangla string under 160 characters is not necessarily one GSM SMS segment. Do not add a paid SMS gateway as a hidden dependency.

The authenticated rotation result also carries the adaptive specification's `next_question`, `robustness` and `contingency_evaluation` with server-resolved scope, revision tokens, source freshness and typed unavailable states. Its reevaluation interface never changes operational state. Confirmed execution uses the shared ProposedAction mechanism and transaction-aware owner operations, not sequential independently committing HTTP calls. Public district results contain none of these private farm policies/answers.

### S1 · 9. Mobile frontend, voice and visualization

- Preserve sign-in → all farms → selected farm chat; add district/crop advisory and rotation comparison within the existing navigation. District exploration can work without GPS; Use current location must not assume the phone is physically at the farm.
- Bangla default and English switch; localized dates/digits/units, readable type, balanced left/right gutters, accessible SVG/vector icons, no fake status bar. Test realistic widths 320/360/375/390/412/430 dp/CSS px, appropriate heights, large text, safe areas and keyboard behavior.
- Top result is **one clear action sentence**, followed by the revised/baseline planting or transplanting window and its support state. No chart-only dead end. Read it aloud and provide replay; do not speak raw statistical jargon by default.
- Interactive district map using bundled permitted district geometry, legend, selected district and accessible list fallback. Add dataset/time-layer controls for rainfall/moisture, heat/vegetation stress, terrain and regional storage at their actual resolution; do not portray GRACE as field detail.
- Two-period distribution chart with identical axes/bins or an ECDF, annual observations, sample/exclusion counts and uncertainty; add GDD accumulation comparison and threshold-sensitivity view. Respect seasonal anchors and leap-year labeling.
- Rotation timeline and side-by-side factors including bare periods, risks and priority changes. Show field vulnerability estimates only when local-resolution evidence supports them; otherwise explicitly label regional context and unassessed field risk.
- Evidence view shows onset definition, every assumption, dataset URLs/versions/period/scale and factual uncertainties. Plain-language glossary: evapotranspiration, soil moisture anomaly, NDVI, frost risk and water balance; distinguish satellite/reanalysis/ground observations and explain combining them.
- Scenario sliders for rain/temperature update labeled simulations while historical distributions remain unchanged; climate projections have distinct model/scenario controls.
- Android device STT/system TTS and recorded prompts follow the linked voice plan. Chrome responsive checks validate layout, charts and navigation; physical Android builds validate recognition, speech, microphone lifecycle, permissions and offline behavior.
- Screen-result state, spoken response and SMS derive from the same typed result. An LLM cannot choose a different shift, cite absent data or turn uncertain evidence into a confident action.
- Add one decision-question card with unknown/skip choices, accessible tested-feasibility ranges, and a contingency/diff confirmation view. Keep hypothetical answers distinct from confirmed saved M1 facts; stale/offline proposals cannot silently renew or execute after their approved values change. Details: adaptive specification §8 and voice flow F9.

### S1 · 10. Verification and release gates

No checkbox below is pre-completed. Each requires a fresh command/report or observed session, date, commit/cache/method versions and evidence path. Synthetic fixtures verify logic only and never become production agricultural advice.

| Gate | Required verification |
|---|---|
| V01 Data | 64 canonical districts, source manifests, cache hashes, duplicate/date/unit/fill/QA validation, honest source-family coverage and source-policy expiry |
| V02 Pure compute | Hand-calculated onset/GDD cases; inclusive last candidate; true consecutive dry spells; false onset; no onset; missing/negative values; trailing horizon; leap/cross-year dates; base/cap/units |
| V03 Statistics | Fixed 12/13-year periods; ties/constant/unequal/insufficient samples; all-no-onset case; seeded intervals; signed raw/rounded shifts; U orientation; annual independence limits and full 15/20/25 mm sensitivity |
| V04 Agronomy | Source-backed base/calendar/stages; sowing versus transplanting; photo/thermal limitations; impossible overlaps; irrigation constraints; weak evidence and no-feasible-window outputs; informed-person review recorded |
| V05 Source/model validity | Held-out NDVI/ground timing with coverage; baseline/rain-only/combined comparison; no leakage; supplemental-layer ablation changes evidence/confidence appropriately; NASA removal is visible |
| V06 API/contracts | GET `/advisory` fields/errors, aliases/season ambiguity, units/provenance, Unicode SMS <160, same facts in both languages; no GET operational writes |
| V07 Offline | `OFFLINE=1` with network denied; missing/corrupt caches; bundled map, no hidden tiles/LLM; disconnected phone last result/staleness; restart and queued-action semantics |
| V08 Farm isolation | Two farmers/two farms, unauthorized IDs, expired auth, duplicate confirm, stale season/action, session switch and correct crop/season in chat |
| V09 Existing lifecycle | Fresh DB import → signup → all farms → recommendation → plan activation → M3 tasks → M4 alert → M5 reply → M6 result/problem visible → harvest close/history |
| V10 Rotation | Current + two alternatives, nutrient/cover/pest/water/forage/market factors, priorities, missing data, infeasible options and overlap checks; exploration never starts a season |
| V11 Browser | Chrome standard mobile viewport matrix, map/chart interactions, Bangla fonts/text scaling, equal gutters, permission denial and provider failures with screenshots |
| V12 Native | Signed APK on actual low-end Android: install/update/cold start, mic/TTS unavailable/denied, background stop, interruptions, weak/offline data and source-dated cached result |
| V13 Usability | At least one person outside the team completes district/crop selection and explains the advisory; report actual sample/task results and failure cases. Wider dialect/pilot study remains separately reported |
| V14 Production | HTTPS URL from phone on mobile data, no localhost dependency, release signing, no dev reload/public trust DB, protected secrets, backup/restore, bounded resources/latency and service-outage behavior |
| V15 Submission | Apache-2.0 for original project code, retained upstream notices, per-dataset/model licenses, public accessible repo, dataset URLs in README, completed NASA page, exact challenge title/category, recorded demo and real teamwork evidence |

Run existing appropriate backend unit/contract/integration suites against a clean PostgreSQL test database and add meaningful compute/API/rotation tests. Run Expo lint/typecheck and browser/native checks for changed functionality. Never equate mocked services, an existing test count or a responsive browser with a validated release.

The accepted follow-up additionally requires [A01-A08](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md): question impact, non-monotonic envelopes, dated trigger handling, schema compatibility, transactional race/crash/retry correctness, existing lifecycle regressions, actual browser/native/offline use and measured decision value. These gates are planned and unverified.

### S1 · 11. Organizer schedule and full delivery sequence

### S1 · 11.1 Pre-event work (must be disclosed in submission)

- [ ] Preserve inputs and record the requirement matrix; finalize additive contracts with affected owners.
- [ ] Cache POWER, NDVI and SMAP for every district, all other scoped data families and permitted geometry; verify download script/manifests and offline bundle.
- [ ] Source/record crop calendars, degree-day bases, onset/search/verification definitions and local agronomic agreement; support at least three crop/season profiles and suitable rotation alternatives.
- [ ] Draft Bangla/English strings, glossary, short advisory/SMS templates and recorded core prompts.
- [ ] Prove actual native build/device speech path, release host capacity and existing M1-M6 baseline. Resolve the season-plan knowledge blocker.

### S1 · 11.2 48-hour organizer milestone

| Organizer slot | Deliverable | Evidence |
|---|---|---|
| Day 1 morning | Onset, GDD and shift-test implementation in `backend/src/compute/agro.py`, including sensitivity and tests | V02/V03 hand-calculated cases and green test output |
| Day 1 afternoon | District map, crop/season selection and 2001-2012 vs 2013-2025 distribution comparison | Working `/advisory` and mobile screenshots |
| Day 1 evening | Actionable advisory sentence, revised window, assumptions/sources; record by **18:30 local event time** | Recorded Rajshahi/Aman result using measured values |
| Day 2 morning | Bangla/English interface, phone layout, <160-character summaries; test with a person outside the team | Usability observations and browser + phone checks |
| Day 2 noon | Freeze, record and submit that milestone | Pinned commit/cache, working repo/page and demo |

The organizer's 18:30 and noon are event checkpoints, not dates inferred from the current clock. Full multi-source, rotation, field-validation and production scope may exceed this milestone; keep its gates open and report status accurately.

### S1 · 11.3 Full completion sequence

1. **Foundation:** pre-event cache/knowledge/native prerequisites, source licensing, contracts and clean lifecycle (V01/V04/V08/V09).
2. **Planting-window science:** pure onset/GDD, period comparison, Mann-Whitney, sensitivity, validated candidate window and HTTP result (V02-V06).
3. **Challenge depth:** source harmonization, all scoped layers, predictive-climate exploration, held-out comparisons and three rotation strategies (V05/V10).
4. **Farmer delivery:** mobile map/charts, assumptions/glossary, Bangla/English sentence/SMS, device speech and offline behavior (V07/V11-V13).
5. **Accepted adaptive decisions:** after the required flow works, complete question selection → robustness analysis → policy preview → atomic confirmed Plan B → mobile/voice/offline integration. Follow adaptive increments D1-D5 and gates A01-A08; no substitute for the required science/rotation flow.
6. **Production/submission:** measured host/device performance, bounded policy refresh/delivery and outage handling, clean deployment, license/attribution, contribution evidence, video and public project page (V14/V15 and adaptive D6).

Suggested organizer fallback order, **only if a later explicit scope decision is made**: one crop instead of three → one district told properly → drop SMAP while retaining rainfall/temperature → drop map while retaining the advisory. This is not the acceptance definition for the user's full request.

### S1 · 12. Cost, licenses and deployment

Original project code is planned for **Apache-2.0**, as organizer specifies. Add the root license/NOTICE and preserve `frontend/LICENSE` and other upstream MIT/license notices. Source screenshots, datasets and model weights are not automatically relicensed by the application license. Inventory all dependencies/artifacts; replace or separately permission any noncommercial/restricted model before claiming the full distribution is commercial compatible. The current M6 weights are CC-BY-NC-4.0 and require an explicit release decision.

Use free/open tools for computation and development: Python, NumPy/SciPy, Parquet tooling, existing FastAPI/PostgreSQL, Expo/React Native and SVG. No paid speech, SMS or LLM service is required for the deterministic advisory; optional providers must fail gracefully. Select a measured hosting arrangement, durable artifacts/database, HTTPS, secure deployment variables and a tested backup restore. A free tier or donated team machine may support a bounded pilot, not a promise of indefinitely free reliable production.

Keep service terms separate from open-data licenses. Open-Meteo free hosted access is noncommercial and quota limited. Store distribution fees, Android verification changes, native build constraints and free-host sleeping/retention limitations are detailed in the [feasibility review](../research/2026-10-28-free-mobile-voice-feasibility.md). Direct APK release can serve a supported pilot; do not label a development Expo web server as a deployed mobile application.

### S1 · 13. Requirement traceability

All rows are **planned, not verified** until their gates pass. Full statement considerations are included because the user requested complete coverage, without misrepresenting their original optional wording as an organizer mandate.

| ID | Source requirement | Plan sections / acceptance evidence |
|---|---|---|
| O01 | Satellite observations + predictive climate → farmer adaptation | §5 D01-D10, §6-7; V01/V05/V10 |
| O02 | Bangladesh district/crop rice planting-window tool; 25 years; shift in days | §1-2, §6, §8; V02-V06 |
| O03 | Rajshahi/Aman, two distributions, revised transplanting window, Bangla phone | §2/§9/§11; V06/V11-V13; example 11 is never fabricated |
| O04 | POWER daily rain, temperature, solar; IMERG spatial rainfall | §5 D01/D02, §6; V01/V05 |
| O05 | SMAP + MODIS or VIIRS NDVI; every-district pre-cache | §5 D03/D04/§5.2, §6.5; V01/V05/V07 |
| O06 | Agreed onset and crop-specific degree-day base/calendar | §6.1-6.3/§11.1; V04 |
| O07 | `src/compute/agro.py`, onset/GDD/shift, each function tested | §4/§6; V02/V03 |
| O08 | Explicit onset definition, consecutive dry-spell check and stable thresholds | §6.2; V02/V03; correct example-code inconsistencies |
| O09 | 2001-2012 vs 2013-2025, Mann-Whitney U, whole-day shift, ±5 mm | §6.4/§8; V03/V06 |
| O10 | Parquet per district, pre-event pipeline, `OFFLINE=1` cache only | §4/§5.2; V01/V07 |
| O11 | FastAPI GET `/advisory?district=&crop=`, distributions/statistic/assumptions/provenance | §8; V06 |
| O12 | District map, charts, one actionable sentence at top, Bangla + English phone UI | §9; V11-V13 |
| O13 | SMS summary strictly under 160 characters, sendable output | §8/§9; V06/V11 |
| O14 | Every assumption and onset definition visible, dataset citations | §5-6/§8-9; V01/V06/V11 |
| O15 | Apache-2.0, public repo, README with each dataset URL | §12; V15 |
| O16 | All 48-hour slots, pre-build, 18:30 recording, outside-team test, freeze/submit and cut order | §11; V13/V15; cuts require explicit scope decision |
| P01 | NASA + local soil + crop traits + farmer priorities | §4-5/§7; V01/V10 |
| P02 | Temperature/heat, rain/extremes, moisture, evaporation, frost, vegetation stress and long-term water | §5 D01-D10/§6-7/§9; V05/V10/V11 |
| P03 | All named dataset families: SMAP, ECOSTRESS, GPM, Landsat, MODIS, POWER, GRACE/FO, elevation, GEDI | §5 D01-D09 and source applicability; V01/V05 |
| P04 | Crop vulnerability, seasonal transitions and bare-field periods | §6.5/§7/§9; V05/V10 |
| P05 | Three rotations including current; rationale/benefits/gaps/risks | §7-8; V10 |
| P06 | Nutrient cycling, erosion, organic matter, pests, water, forage and market | §7; V04/V10 |
| P07 | Nitrogen-fixing, cover, deep-rooting and drought-tolerant explanations | §7/§9; V04/V10/V13 |
| P08 | Compare modeling/statistical approaches, uncertainty and expert judgment | §6.1/§6.4-6.5; V03-V05 |
| P09 | Harmonize spatial/temporal grids and resolutions | §5.2; V01/V05 |
| P10 | Maps over time and local vulnerability with honest resolution | §5/§9; V05/V11 |
| P11 | Timelines, dataset overlays and rainfall/temperature scenario sliders | §7/§9; V10/V11 |
| P12 | Explain ET, anomalies, NDVI, frost, water balance and ground vs satellite observations | §9; V11/V13 |
| P13 | Farmer input: water, equipment, markets, priorities; limited technical literacy | §4/§7/§9; V10/V13 |
| P14 | Supports farmer judgment/local expertise; no unsupported guaranteed outcomes | §2/§6-9; V04/V05/V13 |
| J01 | Provided scoring: validity, relevance, presentation, teamwork, UX, NASA use | §10-11 and demo; V05/V11-V13/V15 |
| J02 | Exact challenge category/title, public repository, completed official project page | §10-11; V15; verify event rules, do not invent missing image criteria |
| F01 | Owner-accepted decision-driven field question after competitor review | §15; adaptive §§3-4/§8; A01/A04/A06-A08 |
| F02 | Owner-accepted robustness envelope with binding constraints | §15; adaptive §5; A02/A04/A06-A08 |
| F03 | Owner-accepted saved contingency and farmer-confirmed Plan B | §15; adaptive §§6-9; A03-A08 |

### S1 · 14. Scientific and technical references

The organizer screenshots/final statement are requirements; these primary sources justify implementation details. Pin selected product versions, current terms and locally applicable agronomic sources during data preparation.

- [Official challenge](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).
- [NASA POWER daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) — metadata, time standards, source-resolution and request limits; [meteorological sources](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/).
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg).
- [NASA SMAP mission](https://science.nasa.gov/mission/smap/) — 2015 launch; [science operations](https://www.nasa.gov/news-release/nasa-soil-moisture-mission-begins-science-operations/).
- [NASA MOD13Q1](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1/) — product/collection and 16-day composite support.
- [NASA ECOSTRESS](https://ecostress.jpl.nasa.gov/), [Landsat](https://landsat.gsfc.nasa.gov/), [GRACE](https://grace.jpl.nasa.gov/), [SRTM](https://www.earthdata.nasa.gov/data/instruments/srtm), [GEDI](https://gedi.umd.edu/) — select concrete product IDs, quality flags and valid periods, not a generic NASA label.
- [NASA NEX-GDDP-CMIP6](https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/) — future scenario products and scale.
- [SciPy Mann-Whitney U](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html) — independent samples, statistic and ties/method handling.
- [FAO-56](https://www.fao.org/4/x0490e/x0490e00.htm) — crop water requirements and explicit assumptions.
- [Expo speech-recognition maintainer](https://github.com/jamsch/expo-speech-recognition) — native builds and platform capabilities; see linked voice plan for full device testing.

### S1 · 15. Accepted adaptive-decision extension

The full implementation specification is [Adaptive Decisions and Confirmed Plan B](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md). It adds three linked behaviors only: ask an observable question that changes a supported choice, calculate bounded calendar/resource feasibility under declared scenarios, and maintain a supported contingency whose exact plan/task changes require fresh farmer confirmation. Its source-review inspiration is recorded without claiming global novelty.

M1 owns confirmed facts; M2 owns analytical results, rules, plan definitions and policies; M4 owns dated evidence; M3 owns operational state; M5 owns presentation/confirmation orchestration. A policy evaluation alone cannot change crop/season/task records. Required extensions include immutable result/version IDs, explicit evidence freshness, a single ProposedAction path, atomic owner operations with replay receipts and post-commit delivery recovery. Additive migrations need the exact shared-contract/DB diff before code; this plan does not modify the schema.

Complete the core organizer/final-statement flow first, then this extension before claiming the accepted full release. An initial milestone may omit it only when reported as incomplete. Broader multi-farm rice allocation, pump coordination and outcome research remain deferred suggestions. No paid reasoning API is required, and no unsupported agronomic rule or benefit percentage can be introduced to make the feature appear complete.

</details>

<a id="source-s2"></a>

## Appendix S2 — Complete source snapshot

Source: `docs/plans/2026-10-29-adaptive-decisions-and-confirmed-plan-b.md` at `336bf6c`. The reconciled final rules above take precedence. Full text is retained for requirement traceability; source headings are prefixed and local links relocated for this combined file.

<details>
<summary>Read complete S2 specification (14 source headings)</summary>

### S2 · FieldShift BD — Adaptive Decisions and Confirmed Plan B

**Revision:** 2026-10-29, Asia/Dhaka. **Status:** required planned extension, not an implemented feature. The project owner accepted the three linked additions after the competitor review. This document extends the [challenge delivery plan](2026-10-29-nasa-planting-window-and-rotation.md), [canonical plan](../../plan.md) and [voice plan](2026-10-06-voice-first-bangla.md). All organizer/final-statement requirements remain required. Read the complete plan set through the [index](README.md).

### S2 · 1. Accepted scope and completion order

Deliver three connected behaviors after the required organizer and rotation flow works:

| ID | Behavior | Additional result |
|---|---|---|
| A01 | Ask the field question that changes the decision | One useful farmer-observable question selected by deterministic comparison of supported options under unknown inputs |
| A02 | Rotation robustness envelope | Explicit tested delay/water/heat scenarios, feasible ranges and binding constraints for the current rotation and supported alternatives |
| A03 | Conditional Plan B | A saved, versioned contingency policy; dated evidence produces a proposed plan/task difference; a farmer confirmation applies the current supported change once |

These are additions to the three-rotation comparison, explanation and confirmed M2-to-M3 lifecycle. They do not replace onset/GDD/statistics, NASA data, maps, offline behavior, deployment or submission work. The organizer's timed 48-hour milestone stays intact; this extension has no invented delivery-time guarantee.

Multi-farm rice-floor allocation, shared-pump scheduling, a general minimum-change optimizer and outcome-study tooling remain research suggestions outside this accepted three-feature increment. Do not silently add them as release gates. Simple constraint explanations belong to A01/A02 and are included.

Core logic uses Python, existing FastAPI/PostgreSQL, pinned local agronomy and M4 evidence. No purchased LLM, speech or SMS service is required. Existing optional AI may paraphrase a validated result without changing facts. Production hosting/device costs follow the parent plan.

### S2 · 2. Current baseline and module ownership

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

### S2 · 3. Shared analytical interface

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

### S2 · 4. A01 — Decision-driven next question

1. Start with the supported crop/variety/rule set and known farm facts. Separate hard feasibility constraints from preference-based ranking and evidence gaps.
2. Enumerate a bounded, source-supported domain for each decision-relevant unknown. Use farmer-observable categories such as irrigation access or waterlogging history; do not invent a precise soil pH, lab nutrient value, flow rate or groundwater depth.
3. Evaluate the feasible set and transparent ranking under these values, including credible joint combinations where inputs interact. Never vary correlated inputs independently unless the rule bundle justifies that combination. If limits prevent joint evaluation, report incomplete analysis rather than false certainty.
4. Prefer a question that resolves hard feasibility ambiguity, then one that separates supported options. Rank remaining questions by documented worst-case ambiguity reduction and low answer burden; use a stable question ID as the final tie-break. Without calibrated probabilities, do not describe the score as expected information gain or statistical confidence.
5. Return one question with safe answer choices, `unknown` and `skip`, affected alternatives, reason for asking and applicability/evidence IDs. No decision-changing question means return none; unsupported alternatives do not become recommendations just to create a question.
6. Tap/voice answer is read back. An exploratory answer may recalculate a labeled scenario. Persisting it uses the M1 confirmed update, then rebuilds the authoritative M2 snapshot. Do not reuse hypothetical result IDs as saved-farm recommendations.
7. Corrections invalidate derived questions/results. Do not loop on declined/unknown answers; retain ambiguity and offer supported next steps or a measurement need.

A remote coarse SMAP observation and a recent farmer field report may both be valid at their own scales. Keep both with time/provenance, flag the mismatch and request a relevant observation. Do not silently average them or let M5 choose which is true.

**Acceptance:** hand-worked rule fixtures show the question changes/narrows a feasible set or distinguishes the disclosed ranking; irrelevant and lab-only questions are excluded; dependent inputs, all-tied/no-option results, corrections, skip and no-supported-answer cases are deterministic.

### S2 · 5. A02 — Robustness envelope and binding constraints

Calculate how a candidate rotation fits supported calendar/resource constraints over a declared bounded scenario domain. Display it as calendar/resource feasibility, not guaranteed yield, survival probability or a universal safe percentage.

- Analyze source-supported axes: planting/transplanting delay in whole days; documented irrigation availability/capacity categories or measured units; temperature perturbations within the supported method. If water response or heat response cannot be calculated, return that axis unavailable. Do not fabricate an ET/yield model.
- Store domain, step size, units, reference dates, constraints, joint versus one-axis-at-a-time interpretation, and evaluated scenario count. A one-dimensional margin does not establish feasibility under combined stressors.
- Evaluate all allowed points within configured compute limits. Return every feasible interval/component, gaps, baseline status, first failing evaluated points and the binding crop/stage/rule. Do not assume monotonicity or infer a continuous exact threshold from coarse grid points. Coarse intervals include their resolution/uncertainty; when the edge is reached, say “not failed within tested range”.
- Respect nursery age, photoperiod, cross-year calendars, crop turnover, water/equipment limits, current planted state and overlap. A “delay” cannot move actual past operations or relabel observations.
- Keep historical observations, future projections and manually perturbed scenarios separate. Preserve the original onset distributions while exploring what-if values.
- Run constraint checks under missing information. Return conditional ranges with explicit assumptions or unavailable status; unknown is never silently replaced by favorable conditions.
- Cache by immutable snapshot, rule/data/method versions and scenario domain. Bound CPU, memory, payload, concurrent requests and scenario count; over-budget requests produce a documented limit error, not an approximate result labeled exhaustive. Record measured target latency before release.

**Acceptance:** hand-calculated boundaries; disjoint/non-monotonic ranges; impossible baseline; insufficient coverage; date/leap-year/unit conversion; coarse-grid truncation; combined stressor examples; repeatable cache keys and bounded workload. UI must explain why the tested range is not a future-weather guarantee.

### S2 · 6. A03 — Saved contingency and confirmed application

### S2 · 6.1 Policy, evidence and evaluation

On confirmed plan selection, M2 stores a policy bound to the exact farm/selected season/plan, method and rule versions. A policy includes typed supported trigger predicates, applicable observation/provider/scale, required farmer confirmation, freshness/coverage rules, latest feasible action dates, alternative candidates and expiry. The baseline plan can be saved when no supported Plan B exists; the policy explicitly says `unsupported`, without inventing one. Re-evaluation computes alternatives against current context rather than executing a frozen obsolete candidate.

Use a deliberately bounded trigger vocabulary, for example confirmed irrigation unavailability or failure to meet the declared usable-rain criterion by a locally supported date. Distinguish `no_trigger`, `needs_observation`, `needs_field_confirmation`, `trigger_met`, `alternative_unsupported`, `expired` and `superseded`. Forecasts can trigger a review request only under a labeled review policy; they do not prove observed onset failure. Missing rain data cannot establish a dry/no-onset condition.

Deterministic evidence precedence uses effective observation time, quality and source-policy rules, not arrival order alone. Out-of-order updates, contradictory records and withdrawn/corrected evidence invalidate dependent proposals. Apply documented noise/debounce rules only where scientifically supported; do not oscillate between plans on repeated identical observations.

Minimum release refresh triggers: advisory opened/refreshed, relevant confirmed M1/M3 change and new M4 evidence ingested. Implement one bounded shared-backend re-evaluation job with deduplication/retry for already selected policies, or explicitly retain an on-open pilot limitation until that job exists; unattended monitoring cannot be claimed before it is verified. Push delivery is separate: in-app review notices are the minimum, with push only through the existing tested notification path. No continuous phone listener is required.

### S2 · 6.2 Proposal lifecycle

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

### S2 · 6.3 Atomic execution and retries

Use the shared PostgreSQL transaction through transaction-aware owner operations, not chained calls that each commit. M2 and M3 keep their ownership; an orchestration unit of work coordinates them. Before integration, refactor only necessary internal commit behavior to accept an outer transaction while preserving existing public route behavior. Document lock ordering, isolation, task reference uniqueness and full rollback semantics.

Lock action/plan/season and relevant profile/task/policy state in deterministic order; validate the expected digest/revisions; re-evaluate support/freshness at confirmation; apply only the approved diff. If data changes the proposal, return `409 stale_proposal` and require review of a fresh proposal. Never execute materially different values under an old confirmation.

Unique idempotency scope includes account, farm and action; persist request hash and execution receipt in the same transaction as effects. Same key/payload returns the same result even after a dropped response; a different payload with that key returns `409 idempotency_conflict`. Competing actions based on the same plan cannot both apply. Expiry/cancellation racing confirmation has one serialized terminal outcome. An expired already-executed action still returns its saved receipt to a legitimate retry; expiry prevents a new execution.

Before-commit failure rolls everything back. Notification/cache invalidation happens after commit with deduplication; failure there does not mark a committed action failed or run it again. A process crash between commit and notification is recoverable through an after-commit delivery/outbox record in that transaction. The phone's retry queue is not the server's transactional outbox.

### S2 · 7. Proposed HTTP and persistence additions

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

### S2 · 8. Mobile, Bangla voice and offline behavior

Preserve sign-in → all farm profiles → selected farm chat. Use existing farm advisory/comparison navigation. Add: one question card with `জানি না`/skip, feasible-range view with accessible text, contingency status and exact before/after confirmation card. Use balanced gutters, SVG/vector icons, no fake status strip and large-text layouts. Numerical content, spoken explanation and summaries come from the same typed result.

Voice reads farm name, question/answer, uncertainty and proposed changes before accepting confirmation. Ambiguous “yes” after farm navigation, expired action or competing question cannot confirm a prior proposal. One active target is explicit; taps remain available when speech fails. Confirming a profile answer does not also confirm Plan B.

Offline shows source-dated cached results with scope/version/expiry. An exploratory answer may be saved locally as a draft, but no fresh calculation is claimed unless a tested bundled method/scenario covers it. An eligible confirmed action may be queued with its original payload, scope, versions, key and expiry; execution revalidates on reconnect and requests a fresh review if stale. Expired actions are not renewed or auto-confirmed. Session/farm switch cannot replay an action in a different scope. Server `OFFLINE=1` remains cache-only and distinct from a disconnected phone.

### S2 · 9. Delivery increments and verification gates

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

### S2 · 10. Demonstration and claims

Show a supported Bangladesh farm and three rotations with the required NASA onset/GDD evidence. Start with missing irrigation information; ask the selected field question. Save a confirmed observable answer, explain the changed feasible set and supported robustness range. Introduce a clearly labeled dated observation/scenario and show Plan B's reason and exact diff. Confirm once, demonstrate updated M3 tasks/scoped chat, then show a dropped-response retry without duplicate effects and an unsupported case that declines a numeric answer.

Use measured findings rather than predetermined numerical benefits. A synthetic trigger may demonstrate logic only when visibly labeled; it is not actual farmer validation. Match the supplied criteria through scientific validity, NASA's traceable decision contribution, usable Bangla mobile interaction and a coherent recorded story. No feature guarantees an award.

This is new behavior relative to our current code/explicit result contracts, not a claim of global invention. Adaptation-margin interaction already appears in RotaShift's illustrative prototype. Retain attribution and independently implement permitted ideas; see the [source review](../research/2026-10-29-competitor-feature-opportunities.md) and [repository findings](../research/2026-10-29-competitor-repositories.md) before reusing code/assets.

</details>

<a id="source-s3"></a>

## Appendix S3 — Complete source snapshot

Source: `docs/plans/2026-10-06-voice-first-bangla.md` at `336bf6c`. The reconciled final rules above take precedence. Full text is retained for requirement traceability; source headings are prefixed and local links relocated for this combined file.

<details>
<summary>Read complete S3 specification (47 source headings)</summary>

### S3 · Voice-First Bangla Experience — Implementation Plan

> **Revised 2026-10-29:** This is the voice/accessibility delivery plan for [the organizer and final-challenge implementation plan](2026-10-29-nasa-planting-window-and-rotation.md), under `plan.md` Section 20. All five organizer images and the complete final statement are preserved and mapped there. Voice delivers the planting-window and rotation decisions; it does not substitute for their scientific implementation. Checkboxes are targets, not claims of completed work.
>
> **For contributors:** Use the existing Expo/FastAPI app and module contracts. Track implementation and verification evidence for each phase, the parent plan's V01-V15 gates and the accepted adaptive-decision A01-A08 gates. Read the [complete plan index](README.md) and [adaptive-decision specification](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md). F9/CCR-12 below integrate the owner's accepted three-feature follow-up.

**Goal:** Let a Bangladeshi farmer with limited literacy and little smartphone experience explore NASA-informed planting/transplanting windows and at least three rotation strategies, understand evidence/tradeoffs, and use the season-long assistant mainly by speaking Bangla and listening. Every voice action has a tap path. Bangla and English expose the same computed facts.

**Architecture:** Voice is an input/output channel of the one assistant, not a seventh module. Tier 0 recognition, playback and confirmation UI live on the device; optional server STT/TTS and backend action orchestration belong to M5. M4 supplies environmental evidence, M2 owns planting/rotation science, M1 owns profiles, M3 owns operational tasks/problems and M6 owns disease analysis. Voice does not acquire their data ownership.

**Tech Stack:** Existing Expo SDK 57 / React Native 0.86 / Expo Router, FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL, Docker Compose (dev). Reuse image picker, location, API client and SecureStore. Add device speech/audio/localization/cache facilities after compatibility checks. Server STT/TTS is an optional later adapter; no paid model/API is needed for deterministic advisory or basic voice.

**Cost strategy:** Build an Android pilot without purchased voice APIs using device engines and recorded prompts. Existing hardware/free quotas can cover a bounded pilot; they do not guarantee indefinitely free, durable production. See §4.0 and the [feasibility review](../research/2026-10-28-free-mobile-voice-feasibility.md).

### S3 · 0. Required Challenge Integration and Delivery Order

1. Follow the parent plan's complete requirement matrix: 2001-2025 onset/GDD, 2001-2012 versus 2013-2025 distributions, Mann-Whitney U, supported whole-day window shift and ±5 mm sensitivity; NASA/local data, map/charts, assumptions/provenance; three rotations, soil/resources and farmer priorities.
2. Compute/cache the science before narrating it. `/advisory?district=&crop=` and authenticated M2 farm scenarios supply every displayed/spoken date, shift, uncertainty and evidence ID. An LLM cannot invent or recalculate them.
3. First voice slice: select district/crop or farm, hear/replay the actionable Bangla advisory, ask why, compare rotations and hear today's tasks. Structured writes follow owner-contract integration. Core UI remains bilingual and tap accessible.
4. Show onset definition and every assumption, with spoken explanations. Generate SMS summaries strictly below 160 Unicode characters from the typed result; show true Bangla SMS segment implications rather than promising one segment.
5. Preserve sign-in → all saved farms → selected farm chat. Never silently select a farm from a district voice command or replace the entry flow with a private spoken summary.
6. Chrome validates layout; physical Android release/development builds validate speech, permissions, mic lifecycle, installed Bengali models/voices, offline behavior and low-memory usability.
7. Follow the parent's pre-event/48-hour milestone and full release gates. The organizer's cut order is a separately authorized contingency, not permission to omit full requirements silently.

### S3 · Global Constraints

- `plan.md` is the source of truth. Do not move features between modules or change shared contracts without team agreement (plan.md §10 Rules A–C, §19). Every contract change in this plan is listed in **§9 Contract Change Requests** and is **blocked until the team agrees**.
- The app must **not** listen while closed or in the background. Microphone opens only after a user action (tap, widget tap, shortcut, or assistant "open app" launch) while the app is visible.
- **No voice-commanded farm save, update, delete, or external send without explicit confirmation** (§6). Explain ordinary transcript/chat persistence and analytical caching through consent; technical logs do not recursively ask permission for every write.
- Every voice action has a tap alternative. Every text label has an icon and a "hear this" option.
- Bangla (`bn-BD`) is the default UI and speech language. English is secondary.
- Audio is **not retained** by default. Audio retention needs separate, opt-in consent.
- Store files outside PostgreSQL; keep only a storage key (DB_SCHEMA.md §1, §10).
- Frontend: use `npx expo install` for packages; native modules need a development build (not Expo Go). Run `npx expo lint` and `npx tsc --noEmit` before done (frontend/AGENTS.md). Verify every Expo API against SDK 57 docs before use.
- Do not edit `ios/` or `android/` by hand; use `app.json` and config plugins (frontend/AGENTS.md).
- **Pilot cost constraint:** no purchased speech/LLM/SMS API is required. Hosting, persistent storage, licenses and distribution must pass the parent gates; do not promise indefinite zero operating cost.
- **License rule:** use only models/datasets that allow commercial use (MIT, Apache-2.0, CC-BY, CC-BY-SA with attribution). **Do not use non-commercial (NC) models**, e.g. Meta MMS-TTS / MMS-ASR (CC-BY-NC 4.0). Check the license of every fine-tuned checkpoint before use.

---

### S3 · 1. Current State of the Repository (reconciled 2026-10-29)

Baseline source inspection: `1077a06`; this inventory is not a new runtime-test result.

| Area | Existing implementation / remaining gap |
|---|---|
| Auth/profile | M1 password auth, Argon2id, farm listing/location/resources and token storage exist; reuse them |
| Frontend/backend | M1-M6 services, screens, chat replies, image picker/upload and tests exist; do not rebuild placeholders |
| M2 knowledge | Narrow suitability/harvest evidence exists; verified season stages/tasks still need sourcing for clean-user plan activation |
| NASA | Current POWER history is 30 days; district caches, long-history onset/GDD/statistics, projections and rotations remain parent work |
| Voice/localization | Device speech, Bangla UI/audio, consent/preferences and structured action confirmation remain work |
| Offline/release | Secure token storage exists; account-isolated farm/result caches/outbox, real release identity/API URL, native testing and durable hosting remain work |
| M6 conflict | Current scan auto-creates/reuses an M3 Problem for possible disease; a later UI confirm cannot prevent that write. Reconcile with owners before F6 |

Reuse existing auth, routes, models and fixtures. Add missing source-backed data/interfaces rather than competing systems. Add Bangla/voice scenarios without using synthetic test agronomy as production advice. See the [source review](../research/2026-10-28-challenge-readiness-review.md) and parent §3 for evidence paths.

---

### S3 · 2. Design Principles for Low-Literacy, First-Time Smartphone Users

1. **One big mic button** on every screen, bottom center, same place always. Tap to talk, tap again to stop (hold-to-talk is hard for new users; offer it as a setting).
2. **Talk back first, text second.** Every assistant reply plays as audio automatically (can turn off). Text is shown large, in Bangla, with a replay button.
3. **Short replies.** First reply ≤ 2 short sentences. Then: "আরও শুনতে চাইলে 'আরও' বলুন" + a "আরও" button.
4. **Icons + color + sound on every control.** Long-press any button → it speaks its name. Max 4 main choices per screen.
5. **Farm summary = "আজকে কী করবো".** After explicit farm selection, offer today's task/alert and planting/rotation advice. Sign-in still opens all farms; no private summary for an implicitly selected farm.
6. **Never a dead end.** Every screen has "পেছনে" (back) and "শুরুতে" (home), both by voice and tap.
7. **Yes/No is the main decision pattern.** Big green ✓ "হ্যাঁ" and red ✗ "না" buttons; the farmer can also say them.
8. **Numbers spoken the farmer's way:** "দেড় বিঘা", "আড়াই মণ", "৩০ শতাংশ", "পরশু".
9. **Shared phones are common** (assumption A4): show the active farmer's name + photo; switching user is a voice/tap action.

---

### S3 · 3. Opening the App by Voice — Platform Assessment

### S3 · 3.1 What the platforms allow

**Android**
- A third-party app **cannot** keep an always-on wake word. The always-on hotword APIs (`AlwaysOnHotwordDetector`, `HotwordDetectionService`) are system APIs for the privileged default assistant only (Android 12+).
- Microphone access is "while-in-use". A microphone foreground service cannot start from the background (Android 12+); on Android 14+ it throws `SecurityException`. Android 17 adds more background-audio limits.
- A home-screen widget tap, app shortcut, Quick Settings tile tap, or notification tap **is** a user action that brings the app to the foreground. The app may then open the mic.
- The default assistant (Google Assistant / Gemini) can open installed apps by name. Gemini supports Bengali and is available in Bangladesh. **Whether "open <app>" device actions work with Bengali voice is not documented** → test in Phase 0.

**iOS**
- No third-party wake word or background listening (App Review and platform limits).
- Siri has **no standalone Bangla**. It only accepts Bangla mixed with English in "English (India)" mode; replies are not in Bangla.
- Do not assume usable `bn-BD` recognition from `SFSpeechRecognizer`. Query actual OS/device capability and test recognized language; unsupported Bangla means tap-first. Never substitute another language silently or infer speech recognition from keyboard support.
- iOS does have Bengali (India) voices for VoiceOver / Live Speech → system TTS in Bangla is likely usable (verify).
- Launch options: App Intents / App Shortcuts ("Hey Siri, open FieldShift" in English), home/lock-screen widgets, Control Center controls (iOS 18+), Action Button (newer Pro models), Back Tap (accessibility).

### S3 · 3.2 Recommendation (practical and privacy-conscious)

**No custom wake word. No background listening.** Reasons: blocked by both platforms for third-party apps, high battery cost, Play Store foreground-service declarations, and it would break farmer trust (a hot mic in the pocket).

Instead, "one touch to talk":

| Priority | Entry point | Platform | Behavior |
|---|---|---|---|
| P1 | **Launcher icon with a Bangla, speakable name** (e.g. label "ফিল্ডশিফট") | Both | Opens auth/all-farms entry; after farm selection offers summary. Mic needs the intended user action. |
| P1 | **Home-screen widget: one big mic button** | Android first | Tap → deep link `fieldshift://listen` → app opens in listening mode immediately (user action = allowed). |
| P1 | **Notification tap on an alert/task** | Both | Opens the item and plays it aloud. |
| P2 | **App shortcuts** (long-press icon): "প্রশ্ন করুন", "আজকের কাজ", "ফসলের ছবি" | Both | Deep links to listen / tasks / camera. |
| P2 | **Default assistant "open FieldShift"** | Android (Gemini/Assistant), iOS (Siri, English) | Works only if the assistant supports it; test with Bengali settings. We do not rely on it. |
| P3 | Quick Settings tile (Android), Control Center control / Action Button (iOS) | Both | Same deep link. Lower priority: hard for first-time users to set up. |

Field agents / family members set up the widget during onboarding (assumption A6). The onboarding includes a spoken "how to open me" lesson.

---

### S3 · 4. Speech Stack

### S3 · 4.0 Cost Tiers

| Tier | When | STT | TTS | Platforms | Cost |
|---|---|---|---|---|---|
| **Tier 0 — No purchased speech API (v1)** | Prototype and bounded pilot | Android device recognition with verified `bn-BD`/`bn-IN` support, online/on-device as available | Bundled prompts and installed Bengali system TTS | Android first; iOS tap-first unless tested otherwise | No app speech API fee; device/data/hosting resources still exist |
| **Tier 1 — Self-hosted open source** | Measured need and provisioned hosting | Evaluate exact Whisper/IndicConformer checkpoints and upstream rights on local samples | Evaluate exact Indic Parler-TTS or other licensed checkpoint; measure RAM/latency | Android + iOS | CPU/GPU, storage and operations |
| **Tier 2 — Paid cloud** | Only if Tier 1 fails accuracy/latency targets | e.g. Google Cloud STT `bn-BD`, Gemini Live API `bn-BD` | Cloud TTS | Android + iOS | Per-minute fees |

Tier 0 consequences (accepted for v1):
- Accuracy depends on the phone's engine (usually Google). It cannot be fine-tuned for dialects. Mitigate with the command lexicon, read-back, and tap fallback.
- When online, the Android recognizer normally sends audio to the engine vendor (Google). Consent C2 must say this (§5).
- Supported locales differ by phone/OEM. Check at runtime; if `bn-BD`/`bn-IN` is absent → tap mode.
- iOS stays tap-first unless actual capability tests establish usable Bangla STT; use installed TTS/prompts where available.
- Free zero-cost tools for development only (not for serving users): own laptop, Google Colab/Kaggle free tiers for Tier 1 model evaluation.

### S3 · 4.1 Speech-to-text (STT)

Layered approach behind one interface (`SpeechRecognizer` on device, `SttProvider` on server). **v1 uses layers B and C only (Tier 0).** Layer A is added in Tier 1/2.

| Layer | Use | Engine | Notes |
|---|---|---|---|
| **A. Server STT (Tier 1/2)** | Free speech: questions, farm details, problem descriptions | Tier 1: `tugstugi` Whisper-medium or IndicConformer, self-hosted. Tier 2: Google Cloud STT `bn-BD`, Gemini Live API `bn-BD`. Chosen by bake-off on field data. | Works on iOS and Android. Needs network and hosting. Provider is swappable. |
| **B. Device STT (Tier 0 default)** | Supported Android speech | On Android 13+ query supported/downloaded locales and download where supported. Android 12 and below cannot use this library's `getSupportedLocales()`; use availability/attempt/error handling. Prefer verified on-device mode; disclose online mode or offer taps. | No speech API purchase; quality/availability varies. Never silently recognize another language. |
| **C. No STT** | Unsupported locale, offline without model, permission denied | Tap choices, prerecorded prompts/text; no automatic raw recording | Tap path remains available. |

Evaluate exact checkpoints on Bangla samples; a wrong-script anecdote is not a universal rejection of every small model. Do not bundle large speech models in low-end Android v1 without measured feasibility. Check original weights/data rights as well as converted-port labels.

**Command matching:** Normalize transcript (Bangla/English digits, remove filler words, collapse spelling variants) → match against a **command lexicon** with dialect synonyms (e.g. "কাজ / কাম / কামকাজ", "আজকে / আইজকা / আজ"). If no command match → send to M5 intent routing.

**Number/unit/date parser (Bangla):** "দেড়", "আড়াই", "সোয়া", "পৌনে"; units বিঘা, শতাংশ/শতক, কাঠা, একর, মণ, কেজি; dates "আজ", "কাল", "পরশু", "আগামী সোমবার", Bangla month names. Output always goes through read-back confirmation.

> **Bigha conflict:** DB_SCHEMA.md excludes `bigha` until a region-specific conversion is agreed. Farmers will say বিঘা. Proposal (CCR-5): store the spoken value + unit as said, ask the farmer "আপনার এলাকায় এক বিঘা কত শতাংশ?" once, then convert. Team decision needed.

### S3 · 4.2 Text-to-speech (TTS) and audio

| Content | Source | Why |
|---|---|---|
| Fixed prompts (menu names, onboarding, confirmations, errors, yes/no) | **Pre-recorded human Bangla voice**, bundled in the app (~150–250 clips, Opus) | Most natural, works offline, consistent, zero cost (team/volunteer voice with a signed release). Use a clear standard Bangla speaker; field-test understanding across dialects. |
| Dynamic text (answers, task titles, alerts) | **Tier 0:** device TTS (`expo-speech`, `bn-BD`/`bn-IN` voice). **Tier 1:** server TTS (`vits_rasa_13` / Indic Parler-TTS), cached by text hash | Android Google TTS has Bengali; iOS has Bengali (India) voices (verify quality). If the phone has no Bengali voice → show text + play the nearest bundled prompt. |
| Long answers | Tier 0: device TTS, split into short sentences. Tier 1: server TTS, cached | Consistent voice across devices only at Tier 1. |

Speech rate default 0.85–0.9× (tune in field). Replay button on every spoken message.

### S3 · 4.3 Local accents and dialects
- Phase 0 dataset: record consented samples from target regions (§11) and measure WER/CER per region and noise level per candidate engine.
- Dialect synonym lexicon for commands, crops (with M2 catalogue), units, and dates. Owned by M5 (commands) and M2 (crop names — read only).
- Allow the farmer to answer any question with a tap list; voice is never the only path.
- Optional later: contextual biasing / phrase hints (crop names, farmland names) if the chosen STT provider supports it.

### S3 · 4.4 Noisy environments
- Show a live level meter while listening; if noise is too high: "চারপাশে অনেক শব্দ। ফোন মুখের কাছে আনুন।"
- Voice activity detection (VAD) end-pointing + max clip length (15 s for commands/questions, 60 s for descriptions).
- Tier 1: server-side VAD and noise suppression before STT with open-source tools (Silero VAD — MIT, RNNoise — BSD). Tier 0: rely on the device engine; give the farmer coaching prompts instead.
- Support wired/Bluetooth headsets.
- Field test conditions: wind, irrigation pump/shallow tube-well engine, rain on tin roof, market crowd, livestock.

### S3 · 4.5 Weak or no internet
- **Offline-first queue**: eligible transcripts/messages, photos and confirmed actions show "পাঠানো হবে". Queue raw audio only if an implemented adapter provides recordings and consent/retention explicitly covers temporary storage. Device STT does not guarantee recoverable audio.
- Confirmed actions carry an **idempotency key** so retries never double-apply.
- Cache: today's tasks, alerts, farm summary, and their TTS audio, so Home works offline.
- Audio upload: Opus ~16 kbps mono 16 kHz; resumable/retry with backoff; timeouts sized for 2G/EDGE.
- Network-state indicator as an icon + sound, not text only.
- Scope queued data by farmer/farm/season/request ID/creation/expiry/state version. Reject stale/conflicting actions and clear/isolate data on logout/account switch; never replay old irrigation advice as today's instruction.
- Parent `OFFLINE=1` means cache-only server analysis, not disconnected-phone STT/geocoding/tiles. Bundle permitted compact map/results and show source age.

### S3 · 4.6 Unclear speech — handling rules
| Situation | Behavior |
|---|---|
| Silence / nothing heard | "কিছু শুনতে পাইনি। আবার বলুন।" + mic stays ready. |
| Low STT confidence, or no intent match | "আমি ঠিক বুঝিনি।" Then show/speak **top 2–3 guesses as big picture buttons**: "আপনি কি এটা বলতে চেয়েছেন?" |
| Second failure in a row | Switch to tap mode for this step: show the choices with icons; mic still available. |
| Ambiguous slot (e.g. which farmland, which task) | Ask one short question with tap choices: "কোন জমির কথা? উত্তরের জমি না দক্ষিণের জমি?" |
| Out-of-scope (e.g. loan, market price) | Say what the app can do; do not invent an answer (plan.md §16). |
| Transcript contains a number/date/unit | Always read back in words before any save. |

Confidence thresholds are provider-specific; calibrate in Phase 0 (assumption A8). Rule: **never guess for a write action.**

---

### S3 · 5. Consent and Privacy

1. **First-run consent, spoken + shown, in Bangla.** Separate, plain choices:
   - C1 Microphone use (required for voice; tap-only mode works without it).
   - C2 Voice is converted to text over the internet. **Tier 0:** by the phone's speech service (usually Google) — say so by name. **Tier 1/2:** by our server or our provider. Explain: "আপনার কথা লেখায় বদলাতে ইন্টারনেটে পাঠানো হয়". Re-ask C2 when the tier changes.
   - C3 Keep voice recordings to improve the app (**optional, off by default**).
   - C4 Camera/photos for crop problems (asked at first use).
   Consent is given by tapping "হ্যাঁ, রাজি". A spoken "হ্যাঁ" is recorded as supporting evidence but the tap is required for C2/C3 (assumption A9 — legal review).
2. OS permission prompt appears only after our own spoken explanation (pre-permission screen).
3. **Mic indicator:** clear "শুনছি…" animation + sound cue at start and stop. No listening without it.
4. **Retention:** audio deleted after transcription unless C3 = yes. Transcripts are kept as chat messages (needed for farm context). C3 recordings: retention limit (proposal 90 days) and delete-on-request.
5. **Withdraw anytime:** Settings → "আমার তথ্য" → voice/tap toggles; spoken command "আমার রেকর্ডিং মুছে দাও" → Tier 2 confirmation.
6. Consent records are versioned (text version, time, method, device). Owner: M1 (farmer data) — **CCR-2**.
7. STT/TTS provider: Tier 0 — follow the device engine's terms and disclose them. Tier 1 — audio stays on our server. Tier 2 — data processing agreement, no training on our audio unless C3, region/transfer reviewed. Check current Bangladesh personal-data law before launch (assumption A10).
8. Never put personal data in URLs or logs; redact phone numbers in transcripts sent to analytics.

---

### S3 · 6. Confirmation Policy (applies to all flows)

| Tier | Action examples | Confirmation |
|---|---|---|
| **T0 Read / navigate** | Open tasks, hear alerts, ask a question, go back | None. Announce what happened ("আজকের কাজ খুললাম"). Undo = "পেছনে". |
| **T1 Save / change own data** | Mark task done/skipped, save a profile field, add farmland, record a crop problem, add a note | **Read back + explicit yes.** "আপনি বললেন: 'সার দেওয়া শেষ'। আমি কি এই কাজটা শেষ হিসেবে রাখবো?" → spoken "হ্যাঁ" **or** tap ✓. Anything else = cancel. Shows a card with the exact values. |
| **T2 Irreversible / sensitive** | Delete farmland/data, close season, withdraw consent, delete recordings, share data | Read back + **tap ✓ required** (voice "হ্যাঁ" alone is not enough) + 5-second undo where possible. |

Mechanism: M5 persists its own chat/confirmation records but does not directly mutate another domain. Return a **ProposedAction** with exact farm/target/values; backend execution checks ownership, expiry, current state/season and replay protection before calling the owner. Expiry (proposed 10 minutes) is versioned/configured. **CCR-3.** Irreversible deletion cannot promise an undo after completion; any undo window must precede deletion or use a documented recoverable operation.

---

### S3 · 7. User Flows

Notation: 🗣 farmer speech, 🔊 app speech, 👆 tap alternative.

### S3 · F1 — First run, consent, voice lesson (P1)
1. App opens → 🔊 "আসসালামু আলাইকুম / নমস্কার। আমি ফিল্ডশিফট, আপনার খেতের সহকারী।" (greeting text decided with field team).
2. 🔊 Explain mic button with animation. 👆 "শুনুন" replays.
3. Consent C1, C2 (C3 optional) — §5.
4. OS mic permission.
5. Practice: 🔊 "বড় সবুজ বোতাম চাপুন, তারপর বলুন 'আজকের কাজ'।" Success → praise; failure → §4.6.
6. Offer widget setup (Android) with a helper (field agent / family).

### S3 · F2 — Navigate by voice (P1)
- 🗣 "আজকের কাজ" / "কাজ দেখাও" → Tasks (T0).
- 🗣 "সতর্কতা" / "আবহাওয়া" → Alerts; plays the top alert.
- 🗣 "ফসলের অবস্থা" → Crop health. 🗣 "পেছনে", "শুরুতে".
- 🗣 "উত্তরের জমি" → switch farmland (if ambiguous → tap choice).
- 👆 Same four big icons on Home; long-press speaks the name.

### S3 · F3 — Share farm details (M1 onboarding by voice) (P2)
1. M1 decides the next missing field (plan.md M1 "ask only for missing information").
2. 🔊 One question at a time: "আপনার জমি কতটুকু?"
3. 🗣 "দেড় বিঘা" → parser → 🔊 "দেড় বিঘা, ঠিক আছে?" + card [দেড় বিঘা] ✓ ✗ (T1).
4. Unit conversion question if needed (CCR-5).
5. 👆 Each question also has a picture-choice answer (e.g. soil type pictures, irrigation yes/no, water source icons) and a number pad with big digits.
6. 🗣 "ভুল হয়েছে, জমি দুই বিঘা" → correction proposal → T1 confirm.
7. 🗣 "পরে বলবো" → skip; M1 asks later.

### S3 · F4 — Ask a question (M5) (P2)
1. 🗣 "আলুর পাতা হলুদ হচ্ছে কেন?" → device STT (Tier 0; server STT at Tier 1) → transcript → M5 with farm context.
2. 🔊 Short grounded answer (≤ 2 sentences) + "আরও শুনতে চান?"
3. If M5 detects a disease-type question → offers F6: "একটা ছবি তুলবেন?" ✓ ✗.
4. If M5 detects an action ("সার দিয়েছি") → ProposedAction → T1 confirm.
5. Offline → queued; 🔊 "নেট এলে উত্তর দেবো।" Notification when answer arrives; tap → plays answer.

### S3 · F5 — Manage tasks (M3) (P2 read, P3 write)
1. 🗣 "আজকের কাজ কী?" → 🔊 "আজ ২টা কাজ। এক, সার দেওয়া। দুই, সেচ দেখা।"
2. 🗣 "প্রথমটা শেষ" / "সার দেওয়া হয়ে গেছে" → match task → 🔊 read back → T1 confirm → M3 updates status `completed`.
3. 🗣 "সেচ আজকে করবো না" → propose `skipped` (T1). 🗣 "কালকে মনে করিয়ে দিও" → propose reschedule if M3 supports farmer-sourced changes (task `source = 'farmer'` exists in the model).
4. 👆 Each task card: big ✓ "শেষ", ⏭ "বাদ", 🔊 "শুনুন". A tap on ✓ still shows the confirm card (T1) — prevents accidental taps.

### S3 · F6 — Scan or describe a crop problem (M6 → M3) (P3)
1. Entry: 🗣 "ফসলে সমস্যা" / 👆 camera icon / from F4.
2. 🔊 Photo coaching: "আক্রান্ত পাতা কাছে থেকে তুলুন। ছায়ায় না, আলোতে।" On-device blur/darkness check → 🔊 "ছবি ঝাপসা, আবার তুলুন।"
3. 🔊 "সমস্যাটা মুখে বলুন।" 🗣 "পাতায় বাদামি দাগ, দুই দিন ধরে" → transcript → M5 extracts `OptionalSymptoms` (existing M5→M6 contract).
4. Describe-only path stays in M5's grounded preliminary Q&A with uncertainty and a request for a photo/local help. Current M6 requires an image; do not invent an image diagnosis without an explicitly implemented, validated new contract.
5. M6 result → 🔊 plain-language confidence: High "সম্ভবত …", Moderate "হতে পারে …", Low "নিশ্চিত না। কৃষি অফিসারকে দেখান।" + 1–3 practical actions. Safety: no chemical dose by voice without the approved knowledge source; always suggest local extension officer for low confidence.
6. 🔊 "এই সমস্যাটা খাতায় তুলে রাখবো?" → T1 → M3 records Problem (status `open`). First implement CCR-11 so M6's current auto-write cannot precede confirmation; use an idempotent handoff and do not create the Problem twice.
7. Offline: eligible photo/transcript queued; audio only under §4.5's adapter/consent conditions. Later notifications require an implemented delivery path; a frontend-only queue cannot promise background delivery.

### S3 · F7 — Proactive alert listening (M4/M3) (P3)
1. Push notification (title in Bangla, short). Tap → app opens on the alert and plays it.
2. 🔊 "কাল ভারী বৃষ্টি হতে পারে। আজকের সেচ দরকার নেই।" → "সেচের কাজ বাদ দেবো?" → T1.
3. Notifications never auto-play audio while the app is closed (OS rules + privacy).

### S3 · F8 — Planting-window and rotation advice (M4 → M2 → M5/frontend)

1. Select farm/district and crop/season by tap or speech; clarify ambiguity and distinguish Aman advisory season from a duplicate Rice species.
2. Read the actual M2 `/advisory`/authenticated rotation result. Speak its short Bangla action/uncertainty first; show bilingual text, revised window and replay.
3. "কেন?" opens/speaks the two-period explanation, onset/GDD definitions and source limitations. Show distributions, GDD/sensitivity, sample counts, assumptions and dataset citations.
4. Compare current rotation plus two alternatives; changing water/soil/income priorities calls M2 and narrates its returned tradeoffs.
5. Copy/share the <160-character summary; confirm external composition/send and show Bangla SMS segment implications. No paid SMS gateway dependency.
6. Selecting/activating a scenario is a confirmed M2 action. M3 receives the agreed SeasonPlan/initial tasks; exploration does not mutate state. Missing evidence/no feasible window gives an explanation without an invented date.
7. Disconnected users see source-dated cached results or a clear absence; a queued request is not fresh satellite analysis.

### S3 · F9 — One useful question, robustness and confirmed Plan B (accepted follow-up)

1. After the required F8 flow works, render M2's A01 decision-driven question. Speak why this observable answer matters and offer the same typed choices by tap, including unknown/skip. Do not ask the farmer to guess lab-only values or repeat declined questions.
2. Read back the interpreted answer and farm name. An exploratory answer changes only a labeled scenario. Saving the answer is a distinct M1 ProposedAction; after confirmation, recompute from the saved authoritative snapshot. Confirming that answer cannot also select a crop or execute Plan B.
3. Read M2's A02 tested feasibility range with the binding crop/stage/constraint and uncertainty. Distinguish a bounded scenario result from a promise about crop survival, yield or tomorrow's weather. Allow text/list alternatives to the chart.
4. Show the selected plan's versioned contingency and source dates. When M2 reports a supported trigger, speak the reason, old/new dates and task diff from its A03 proposal. Missing/old/conflicting evidence gives a clear unavailable/review state, not an invented trigger.
5. Confirm or cancel using CCR-3; server verifies current owner/farm/season/plan/task revisions, freshness and expiry. Use transaction-aware M2/M3 operations and one execution receipt. Stale values require a new card/read-back; no automatic crop switch or completed-task rewrite. Preserve actual planting history.
6. An ambiguous “হ্যাঁ”, a farm switch, interrupted narration or an expired proposal cannot confirm a different/earlier action. Bind the response to the one visible current action. Replays of an already executed action return the saved outcome without duplicate changes.
7. Refresh the shared farm state after successful commit so tasks and farm-scoped chat agree. Offline shows the dated cached result; queued confirmation preserves its original payload/key/versions/expiry and revalidates on reconnect. An outdated action needs fresh review, never automatic reconfirmation.

The authoritative compute, policy, proposed persistence and execution specification is the [adaptive plan](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md). Core F9 logic requires no paid AI/speech API.

---

### S3 · 8. Required Changes

### S3 · 8.1 Frontend (`frontend/`)

New, non-route code lives outside `src/app/` (AGENTS.md).

| Path (proposed) | Responsibility |
|---|---|
| `src/voice/VoiceProvider.tsx` | Voice session state machine: `idle → listening → processing → speaking → awaiting_confirmation`; one active session app-wide. |
| `src/voice/recorder.ts` | Audio capture (Opus), level meter, VAD end-point, max length. |
| `src/voice/recognizer.ts` | `SpeechRecognizer` interface; impls: `deviceRecognizer` (**Tier 0 default**, Android system engine, on-device or online), `serverRecognizer` (Tier 1/2, upload), `noopRecognizer` (tap mode). Capability check at startup selects the impl; config flag selects the tier. |
| `src/voice/commands.ts` + `src/voice/lexicon.bn.ts` | Command lexicon with dialect synonyms; normalizer; matcher returning top-N with scores. |
| `src/voice/parse.bn.ts` | Bangla numbers, fractions (দেড়/আড়াই/সোয়া/পৌনে), units, relative dates. Pure functions, unit-tested. |
| `src/voice/speaker.ts` | Plays bundled clips, device TTS (`expo-speech`), or server TTS audio; replay; rate setting. |
| `src/voice/prompts.ts` + `assets/audio/bn/*.opus` | Prompt IDs → bundled recordings + fallback text. |
| `src/components/MicButton.tsx` | Big fixed mic button with states, sound cues, accessibility label. |
| `src/components/ConfirmCard.tsx` | T1/T2 confirmation UI (values, ✓/✗, T2 requires tap, undo). |
| `src/components/ChoiceList.tsx` | Picture choices for unclear speech and tap mode. |
| `src/components/SpeakableButton.tsx` | Long-press → speak label; used to wrap `components/ui.tsx` buttons. |
| `src/i18n/` | Bangla-first strings (`expo-localization`), Bangla digits. Replace English strings in all screens. |
| Existing `src/services/api-client.ts` | Reuse typed requests, token provider and unauthorized handling; add bounded weak-network/offline behavior without a competing client. |
| `src/offline/queue.ts` | Persist eligible messages/photos/actions with tenant/farm/season scope, expiry, state version, idempotency and retry. Audio is conditional on §4.5. |
| `src/consent/` | Consent screens (spoken), state, withdraw. |
| `src/app/onboarding/*` | F1 first-run flow + voice lesson. |
| `src/app/listen.tsx` | Deep-link target `fieldshift://listen` → opens mic immediately. |
| `src/app/farmlands/[id]/crop-health.tsx` | Reuse current camera/upload/M6 result/history integration; add F6 coaching/description without duplicate scans/Problem writes. |
| `src/app/farmlands/[id]/tasks.tsx` | Reuse current API-backed tasks; add accessible controls/readback and confirmation before changes. |
| `src/components/FarmlandChat.tsx` | Add mic, play replies, show ProposedAction confirm cards, queued state. |
| `src/context/AppProvider.tsx` | Reuse existing API-backed auth/farm/chat state; add account-isolated persistent cache. |
| `app.json` | `name`/launcher label speakable Bangla; `scheme: "fieldshift"`; mic/camera permission strings in Bangla; config plugins for speech recognition, widget, shortcuts. |
| Widget / shortcuts | Android widget + app shortcuts via config plugin; iOS App Shortcuts / widget via config plugin or a small native target. Verify SDK 57-compatible libraries in Phase 0. |

Packages to evaluate (install with `npx expo install`, verify SDK 57; all free/open-source): `expo-speech-recognition` (MIT), `expo-audio`, `expo-speech`, `expo-camera` or `expo-image-picker`, `expo-localization`, `expo-notifications`, `expo-file-system`, `expo-network`, `expo-secure-store`, a persisted store (e.g. `expo-sqlite`), widget/shortcut libraries.

**Zero-cost build and distribution:** build the Android development/release APK locally (`npx expo run:android` / local Gradle release build) instead of paid cloud build minutes; install by direct APK. Play Store (one-time fee) and iOS distribution (paid Apple developer account) are deferred until funding (see §15).

Web build (`docker compose` Expo web) must keep working: voice degrades to tap-only or browser Web Speech where supported.

### S3 · 8.2 Backend (`backend/`)

| Path (proposed) | Owner | Responsibility |
|---|---|---|
| Existing `app/api/routes_m1_profile.py` + security/auth dependencies | M1 | Reuse password auth and owner-scoped profiles; no parallel auth store. |
| `app/api/routes_speech.py` | M5 | **Tier 1/2 only — not needed for zero-cost v1** (device does STT/TTS). `POST /v1/speech/transcribe` (multipart audio, `farmland_id`, `hint: command|free|description`) → `{transcript, alternatives[], confidence, duration_ms, provider}`. `POST /v1/speech/synthesize` `{text}` → audio (cached by hash). |
| `app/services/speech/` | M5 | Tier 1/2: `SttProvider` / `TtsProvider` interfaces; adapters for faster-whisper (`tugstugi` Whisper-medium), IndicConformer, `vits_rasa_13` / Indic Parler-TTS, optional cloud; Silero VAD + RNNoise; audio validation (type, size ≤ 2 MB, duration ≤ 60 s); delete audio after transcription unless consent C3. |
| Voice metadata on messages | M5 | Tier 0: the app sends the **transcript as text** plus `metadata.input_mode = "voice"`, `stt_engine = "android-system"`, `stt_confidence` (if the engine returns it). |
| Existing `app/api/routes_m5_chat.py`, `app/services/chat_engine.py`, `app/schemas/chat.py` | M5 | Extend existing routes additively with validated voice metadata, speech text, proposed actions and follow-up choices. Do not create duplicate `/v1` chat routes merely to follow obsolete example names. |
| Parent `/advisory` and authenticated M2 rotation result | M2 with M4 read-only input | Supply computed facts, bilingual sentence/SMS and assumptions/source IDs to F8; M5 renders rather than recalculates. |
| Adaptive result and policy reevaluation, same M2 rotation interface | M2 with M1/M4 read-only input; M3 operational execution | F9 question/robustness/contingency preview; reuse ProposedAction for exact confirmed diffs. Transaction-aware owner operations must replace naive chained committing calls before execution is enabled. |
| `app/api/routes_actions.py` + `app/services/actions/` | M5 (orchestration only) | `POST /v1/actions/{id}/confirm`, `/cancel`. On confirm, call the **owning module's** service (M1 profile update, M3 task status / problem create). Idempotency key required. |
| `app/api/routes_consent.py` | M1 | `GET/PUT /v1/farmers/me/consents`. |
| Object storage (dev: a self-hosted, free S3-compatible server in `docker-compose.yml`, or local disk volume for v1; check the server's license, e.g. AGPL terms) | Shared infra | Audio (only with C3) and crop photos (M6). |
| `app/services/nlu/` | M5 | Intent + slot extraction from Bangla transcripts; uses M2 crop catalogue (read-only) and M3 task list for matching. |
| `backend/tests/` | Each owner | Unit tests (parsers, confirmation state machine), contract tests (ChatResponse, ProposedAction), integration tests with Golden Farm. |
| `mock-data/farm-001/` | Shared | Add Bangla transcripts + expected intents/actions for voice tests. |
| Evaluation harness `backend/tools/stt_eval/` | M5 | Run candidates over the field dataset (Tier 0 Android engine transcripts collected on test phones + Tier 1 open models run on a laptop/free notebook); report WER/CER by region/noise. |

### S3 · 8.3 Data (see CCRs — none applied without team agreement)
- **Voice metadata without schema change (recommended first):** store voice messages as `message_type = 'text'` with the transcript in `message` and `metadata = {input_mode: "voice", stt_provider, stt_confidence, audio_retained: false}`. `attachment_key` set only when C3 = yes.
- `pending_actions` table (M5-owned): `id, conversation_id, farmer_id, farmland_id, action_type, target_module, payload jsonb, status (proposed|confirmed|cancelled|expired|executed|failed), confirm_method (voice|tap), idempotency_key unique, expires_at, created_at, executed_at`.
- `farmer_consents` (M1-owned): `id, farmer_id, consent_type, granted bool, text_version, method, granted_at, revoked_at`.
- Farmer preferences (M1): reuse existing `preferred_language`; add missing `voice_replies_enabled`/`speech_rate` only through documented contracts. Stored chat metadata does not imply `ChatMessageCreate` accepts arbitrary input: validate/allowlist voice fields explicitly.

---

### S3 · 9. Contract Change Requests (need team agreement — plan.md Rule C)

| ID | Change | Affects | Why |
|---|---|---|---|
| CCR-1 | Voice is an I/O channel inside M5 (speech endpoints owned by M5) | M5 scope | Avoid a 7th module; M5 already owns conversation input. |
| CCR-2 | Versioned consent persistence and missing preferences; reuse `preferred_language` | M1, shared contract | Specify additive storage/migration only where needed; no duplicate profile. |
| CCR-3 | `ProposedAction` contract + `pending_actions`; M5 may *propose*, owning module *executes* | M1, M3, M5, M6 | Mandatory confirmation without M5 owning data. |
| CCR-4 | `ChatResponse` adds `speech_text`, `proposed_actions`, `follow_up_choices` | M5 contract | Spoken replies and tap alternatives. |
| CCR-5 | Accept বিঘা/কাঠা/শতাংশ input with farmer-confirmed local conversion | M1, DB_SCHEMA `land_area_display_unit` | Farmers speak local units. |
| CCR-6 | Optional later: `chat_messages.message_type` adds `audio` | Shared schema | Only if audio messages must be first-class; metadata approach avoids it. |
| CCR-7 | Object storage service in dev/prod stack | Infra | Photos (M6) and opt-in audio. |
| CCR-8 | Bangla crop/variety synonyms in M2 catalogue | M2 | Speech matching for crop names. |
| CCR-9 | Android-first without purchased speech API, capability fallback and measured release costs | All modules | No universal offline-Bangla/iOS-STT or indefinitely free production promise. |
| CCR-10 | Typed M2 advisory/rotation and M4 district climate input; confirmed M2 selection | M1/M2/M3/M4/M5 | Parent §§4/8; retain routes/ownership, no operational writes from district queries. |
| CCR-11 | Reconcile M6 scan auto-problem behavior with F6 confirmation | M3/M5/M6 | Prevent pre-confirmation and duplicate writes; a later UI card cannot fix today's scan side effect. |
| CCR-12 | A01 question/A02 envelope/A03 contingency result, versioned policy/proposal, M1 answer provenance and atomic M2/M3 apply through CCR-3 | M1/M2/M3/M4/M5, shared DB/infra | Owner accepted product scope; [adaptive specification](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md) §§3-9 define contract/migration review, one-time execution, stale-state handling and A01-A08 gates. No second confirmation store or automatic crop change. |

---

### S3 · 10. Module Dependencies

```text
Existing foundation: Auth + API client ── source/contract fixtures ── Bangla i18n
                                   │
            ┌──────────────────────┼─────────────────────────────┐
            ▼                      ▼                             ▼
   Voice shell (frontend,   M5 Speech API (STT/TTS)      Consent (M1, CCR-2)
   Tier 0 device STT/TTS)   [Tier 1 only, Phase 6]
            │                      │                             │
            └──────────┬───────────┘                             │
                       ▼                                         │
          M5 Chat + NLU + ProposedAction (CCR-3/4) ◄─────────────┘
              │          │            │             │
     reads M1 profile  reads M3    reads M2      routes to M6
     writes via M1     writes via  crop names    (image + OptionalSymptoms)
     (F3)              M3 (F5,F6)  (CCR-8)              │
                                                        ▼
                                              M6 result → M3 Problem (T1)
            Voice launch (widget/shortcuts/deep links) depends only on the voice shell.
            Offline queue depends on API client + idempotent actions.
            M4 district caches → M2 window/rotation → M5 explanation (F8).
            Confirmed choice → M2 SeasonPlan → M3 operational tasks/state.
            After core delivery: M2 field question → confirmed M1 fact → revised M2 envelope.
            Dated M4 evidence → M2 policy/diff → M5 confirmation → atomic M2/M3 apply (F9).
```

Each module keeps working against mocks (plan.md §6); voice tests use `mock-data/` transcripts.

---

### S3 · 11. Implementation Phases (prioritized)

### S3 · Phase 0 — Spikes, prerequisites, agreements (P0, blocks everything)
- [ ] Verify the parent plan's data/compute/result prerequisites for F8 and create consented Bangla command/advisory examples with known failure cases.
- [ ] **Tier 0 go/no-go spike:** use borrowed low-end Android phones including Android 10–12 and 13+, 2–4 GB RAM; apply version-appropriate capability checks (§4.1), online/on-device/model-download tests, installed Bengali TTS and mic interruption/background checks. Record actual devices/results. Wider 6–8-phone/iOS coverage is a broader-rollout gate, not fabricated demo evidence.
- [ ] Collect an initial consented speech/usability sample and report actual people/devices/noise. The ≥8-region/≥20-speaker-per-region study is a separate Phase 5/§12 gate, not a prerequisite for the initial 48-hour advisory slice.
- [ ] STT evaluation on that dataset: **Tier 0** Android engine (transcripts collected on the test phones) vs **Tier 1** open models (`tugstugi` Whisper-medium, IndicConformer) run on a laptop or free notebook tier. Report WER/CER per region & noise. Decision: is Tier 0 good enough for v1 commands and short answers?
- [ ] TTS listening test with 15+ farmers: team-recorded prompts vs Android system TTS (vs Tier 1 open TTS sample) — comprehension + preference.
- [ ] Record the bundled prompt set (team/volunteer voice, signed voice release).
- [ ] Record affected-owner implementation decisions for CCR-1…CCR-12; this planning update is not evidence that the team has already signed off.
- [ ] Verify existing auth/API integration, reuse source/contract fixtures, produce a local native Android build and agree the actual app name/scheme.
- [ ] Privacy review of consent text (Tier 0 disclosure of the phone's speech service).

**Acceptance:** measured capability report; tap fallback/provisioned alternative when speech fails; contract decisions recorded; native build runs on a phone; available confidence signals calibrated or explicitly absent; core recordings and typed advisory narration verified. Record actual resources/spend rather than declaring zero total production cost.

### S3 · Phase 1 — Accessible voice shell + navigation (P1)
- [ ] Bangla-first UI (i18n), large targets (≥ 56 dp), icons + SpeakableButton, Home "আজকে কী করবো".
- [ ] Consent flow F1 and voice lesson.
- [ ] MicButton, `deviceRecognizer` (Tier 0) + `noopRecognizer`, `SpeechRecognizer` interface ready for `serverRecognizer`, speaker with bundled prompts + system TTS, VoiceProvider state machine.
- [ ] Command lexicon + matcher; navigation F2; unclear-speech rules §4.6.
- [ ] iOS and phones without Bangla STT: tap-first UI with spoken prompts (no mic button shown, or mic shows "এই ফোনে কথা বোঝা যায় না" once).
- [ ] Offline indicator; cached Home summary.

**Acceptance:**
- All navigation commands (≥ 15) recognized top-1 ≥ 90% in quiet and ≥ 80% in field noise on the Phase 0 test set (targets — adjust after Phase 0).
- Every screen usable with mic permission denied (tap-only), verified by test script.
- Mic never active without visible "শুনছি" state; no mic use when app is backgrounded (automated + manual check on Android 14+).
- Usability: ≥ 8 of 10 low-literacy test farmers reach Tasks and Alerts by voice and by tap without help.

### S3 · Phase 2 — Read flows + Q&A + voice onboarding (P1)
- [ ] F8: speak/replay the actual planting-window and rotation result with source facts, uncertainty, chart/evidence links and bilingual/SMS consistency; meet parent V06/V10/V11 gates.
- [ ] After the required core flow, F9 reads M2's question and tested envelope, distinguishes hypothetical from saved answers, and supports unknown/skip/read-back without paid reasoning APIs. Record adaptive A01/A02/A07 evidence.
- [ ] F4 ask a question via M5 (mock M1/M2/M3 context) with spoken short answer, "আরও", replay.
- [ ] F5 read tasks; F7 read alerts.
- [ ] F3 farm details by voice with Bangla number/unit/date parser and picture-choice alternatives.
- [ ] ConfirmCard + ProposedAction (CCR-3/4) for F3 saves.

**Acceptance:**
- Parser unit tests: ≥ 200 Bangla number/unit/date cases pass (দেড়, আড়াই, সোয়া, পৌনে, বিঘা, শতাংশ, পরশু …).
- Zero profile writes without a confirmed ProposedAction (contract test + DB assertion).
- Median voice round trip (5-s question → first audio of answer) ≤ 6 s on simulated 3G; ≤ 3 s for cached/bundled prompts.
- Tier 0 check: no paid API call anywhere in the flow (network log review).

### S3 · Phase 3 — Write flows + crop problems (P1)
- [ ] F5 mark done/skip/reschedule with T1 confirmation; idempotent execution in M3.
- [ ] F6 photo coaching, blur check, spoken description → M6 `OptionalSymptoms` → spoken result → T1 → M3 Problem.
- [ ] T2 actions (delete, withdraw consent, delete recordings) require tap.
- [ ] Offline queue for messages, photos, confirmed actions.
- [ ] After core delivery and adaptive D1-D3, complete F9's Plan B diff/confirmation, atomic owner execution, saved receipt/retry and scoped state refresh. Enable execution only after adaptive A03-A06 concurrency/rollback checks; validate A07-A08 with browser and actual Android use.

**Acceptance:**
- Automated tests: for every write intent, no state change before confirm; cancel/timeout leaves state unchanged; retry with same idempotency key applies once.
- T2 cannot complete by voice alone (test).
- Golden-flow (plan.md §7) runs on mocks and real integration: advisory/rotation → confirmed selection → season plan → M3 tasks → question/photo → disease result → problem visible in next answer. Clean-user activation uses actual approved stage/task data; synthetic fixtures remain test-only.
- Queued items survive app restart and sync once on reconnect.

### S3 · Phase 4 — Voice launch entry points (P2)
- [ ] Deep links: `fieldshift://listen`, `fieldshift://farm/{id}/tasks`, `/alerts`, `/camera`.
- [ ] Android widget (big mic) + app shortcuts; notification tap → open + play.
- [ ] Spoken "how to open me" lesson; setup guide for field agents.
- [ ] *(Deferred to funded stage)* iOS App Shortcuts (App Intents) + widget; Siri phrase in English documented. Needs a paid Apple developer account for distribution.

**Acceptance:** widget tap → listening within 2 s on a low-end test phone (cold start ≤ 4 s); no mic start without the user action; shortcuts work on Android 10–15 test devices.

### S3 · Phase 5 — Field pilot and tuning (P2)
- [ ] Complete the consented ≥8-region/≥20-speaker-per-region study with mixed age/gender, quiet/field noise and actual WER/CER/task results. Do not imply completion in the initial 48-hour milestone.
- [ ] Pilot with 40–60 farmers across regions for 3–4 weeks (§12).
- [ ] Expand dialect lexicon; tune thresholds, speech rate, reply length.
- [ ] Measure and fix top failure intents.

**Acceptance:** task success ≥ 85% for F2/F4/F5 by voice-or-tap; ≤ 1 wrong saved action per 200 confirmed actions (target) and zero unconfirmed writes; farmer-reported understanding of spoken replies ≥ 80%.

### S3 · Phase 6 — Tier 1 upgrade and optional improvements (P3, needs hosting budget)
- [ ] Self-host Tier 1 STT/TTS (`routes_speech.py`, `app/services/speech/`) with open-source models; fine-tune on consented field data (C3) if Tier 0 accuracy is weak for some regions.
- [ ] Switch recognizer by config flag; A/B compare Tier 0 vs Tier 1 on the pilot dataset.
- [ ] iOS voice (server STT) + iOS distribution; Play Store listing.
- [ ] Quick Settings tile / Control Center; audio messages as first-class (CCR-6).

**Acceptance:** Tier 1 beats Tier 0 WER/CER on the field dataset before switching; switching needs no app-flow change (same interface).

---

### S3 · 12. Field-Testing Needs

- **Regions/dialects (minimum):** Chattogram (Chatgaiya), Sylhet (Sylheti), Noakhali, Barishal, Rangpur, Rajshahi/Varendra, Mymensingh, Khulna/Jashore; plus a central/standard-Bangla control group. Indigenous languages (e.g. Chakma, Santali, Garo) are **out of scope** for v1 (assumption A3) — record the gap.
- **People:** women and men; ages 18–70+; low/no literacy; first-time smartphone users; farmers using a family member's phone.
- **Devices:** low-end Android (2–3 GB RAM, Android Go where possible), older Android 10–12, mid-range Android 14–15, 1–2 iPhones.
- **Conditions:** open field with wind, near running irrigation pump, rain on tin roof, home with TV, market. Headset vs no headset.
- **Network:** no signal, 2G/EDGE, unstable 3G/4G, data-saver on, low balance.
- **Method:** task-based sessions with a facilitator speaking local dialect; think-aloud is hard for this group → observe + short follow-up questions; log anonymized interaction events (with consent).
- **Ethics:** verbal + recorded informed consent in Bangla; separate consent for audio dataset; compensation for time; data stored securely, deletable on request; partner with local agriculture extension staff and community organizations (assumption A6).
- **Metrics:** WER/CER by region & noise, command top-1 accuracy, task success, time on task, clarification count per task, confirmation error rate, abandoned sessions, comprehension of spoken replies (teach-back).

---

### S3 · 13. Assumptions (verify)

| ID | Assumption |
|---|---|
| A1 | Most target farmers use Android; iOS is secondary. Verify with pilot recruitment data. |
| A2 | Target users speak a Bangla dialect and understand standard Bangla when spoken slowly. |
| A3 | Indigenous languages are out of scope for v1. |
| A4 | Many phones are shared within a family. |
| A5 | Farmers have intermittent mobile data, often 2G/3G, sometimes none for hours. |
| A6 | Field agents / extension staff / family can help with install, consent, and widget setup. |
| A7 | The Android system engine (Tier 0) reaches acceptable Bangla accuracy for commands and short answers; if not, a Tier 1 open model does. Phase 0 decides. |
| A8 | Provider confidence scores are usable for thresholds after calibration. |
| A9 | Tap is required for legal consent; voice "হ্যাঁ" is supporting evidence only (legal review). |
| A10 | Bangladesh personal-data rules apply to voice and farm data; current law to be checked before launch. |
| A11 | Gemini/Assistant "open app" in Bengali may or may not work; not a dependency. |
| A12 | Existing auth/M1-M6 APIs are reused. Clean-user season knowledge, NASA advisory/rotation and additive voice/action interfaces still need implementation/verification. |
| A13 | No purchased speech API is the pilot target. Hosting, durable data, distribution and operating capacity are measured; free tiers/donated machines do not establish indefinite free production. |
| A14 | Most pilot phones have Google's speech services and a Bengali TTS voice installed (Phase 0 verifies). |
| A15 | Free tools stay free and their terms allow this use (device speech services, open model licenses). Re-check before launch. |

### S3 · 14. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Poor Bangla STT for regional dialects | Core experience fails | Phase 0 evaluation on field data; command lexicon with synonyms; tap fallback after 2 failures; never guess on writes; Tier 1 fine-tuned open model as upgrade path. |
| Tier 0 engine cannot be tuned or controlled | Accuracy plateau; vendor may change behavior | Keep `SpeechRecognizer` interface; Tier 1 ready as fallback; monitor clarification rate. |
| Tier 0 sends audio to the phone's speech vendor | Privacy concern | Clear C2 disclosure; prefer on-device recognition when available; Tier 1 keeps audio on our server. |
| Actual device has no usable Bangla recognition/voice | Missing or wrong-language output | Capability-based tap-first UI, verified voices/prompts and optional provisioned server adapter; never silently change language. |
| Android `bn-BD` support varies by phone/OEM | Some phones get no voice | Runtime capability check; tap mode; offline queue. |
| Zero budget for hosting during pilot | Backend downtime | Run on team machine for small pilot; keep app useful offline with cached data. |
| Using a non-commercial model by mistake | Legal risk | License rule in Global Constraints; license check in code review. |
| Wrong action saved from misheard speech | Wrong farm records, bad advice | T1/T2 confirmation, read-back of numbers, idempotency, undo, audit trail. |
| Weak network → slow replies | Users give up | Bundled prompts, cached Home, queue + notification, compact audio, short timeouts with spoken status. |
| Privacy fear of "listening phone" | Low adoption | No wake word, visible/audible mic state, no audio retention by default, easy withdraw. |
| Cost when users grow beyond pilot | Capacity/availability shortfall | Device speech avoids purchased calls; measure backend/storage/inference/data costs, cache appropriately and provision before scaling. |
| Unsafe agronomic advice read aloud (pesticide doses) | Harm | Answers only from approved knowledge (plan.md M5, DB_SCHEMA provenance); low-confidence → extension officer. |
| Cross-module contract changes not agreed | Blocks phases 2–3 | Raise CCRs in Phase 0; build against mocks meanwhile. |
| Expo SDK 57 library compatibility (speech, widgets) | Rework | Verify in Phase 0 dev build; config plugins only. |
| Low-end phones: memory/battery | Crashes, slow | No always-on listening, no large on-device models in v1, test on 2 GB devices. |

### S3 · 15. Open Decisions for the Team
1. Record CCR-1…CCR-12 implementation decisions with affected owners, including M4/M2 analytical input, M6 confirmation reconciliation and the accepted adaptive policy/atomic execution contracts. Product direction is owner-authorized; do not claim migration/teammate signoff without a record.
2. Verify existing auth and season-data prerequisites; document additive schema/interfaces rather than redesigning auth.
3. App display name and deep-link scheme (must be easy to say in Bangla).
4. Tier 0 go/no-go after Phase 0; when to move to Tier 1 (hosting source and budget).
5. Voice talent for recorded prompts and greeting wording (volunteer, signed release).
6. Pilot regions and partner organizations.
7. When to pay for Play Store / Apple developer accounts (deferred; not needed for APK pilot).

### S3 · Sources and verification status

The original 2026-10-06 links below are background references, not proof of current capability. The [feasibility review](../research/2026-10-28-free-mobile-voice-feasibility.md) records native speech/build/cost checks; the [2026-10-29 parent plan](2026-10-29-nasa-planting-window-and-rotation.md) records organizer/science requirements. Recheck matching Expo SDK 57 docs and actual devices before native implementation. Model ports/anecdotes below are candidates to verify, not established license/benchmark evidence.
- Android foreground service types / while-in-use microphone: https://developer.android.com/develop/background-work/services/fgs/service-types , https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start
- Android 17 background audio hardening: https://developer.android.com/about/versions/17/changes/bg-audio
- Android hotword detection is a system API: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/service/voice/HotwordDetectionService.java
- Siri Indian multilingual mode (Bangla mixed with English only): https://support.apple.com/en-us/105012
- iOS 27 feature availability (Bangla keyboards, Bengali VoiceOver/Live Speech): https://www.apple.com/ios/feature-availability/
- expo-speech-recognition (wraps SFSpeechRecognizer / Android SpeechRecognizer): https://github.com/jamsch/expo-speech-recognition
- Bengali voice dialer experience (small Whisper → Devanagari): https://dev.to/devksarkar/i-tried-to-build-a-bengali-voice-dialer-for-android-here-is-what-actually-happened-and-how-i-40ak
- Gemini mobile app languages/countries: https://support.google.com/gemini/answer/14579026?hl=en&co=GENIE.Platform%3DAndroid
- Gemini Live API languages (bn-BD): https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice
- AI4Bharat IndicConformer (MIT): https://github.com/AI4Bharat/IndicConformerASR , https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual
- BengaliAI `tugstugi` Whisper-medium (Apache-2.0, derived ports): https://huggingface.co/winshades/bengaliai-whisper-medium-ggml , https://huggingface.co/psdn-ai/bangla-asr
- Bangla long-form ASR comparison (tugstugi lowest WER): https://arxiv.org/html/2603.03158
- Indic Parler-TTS (Apache-2.0): https://huggingface.co/ai4bharat/indic-parler-tts
- Meta MMS-TTS Bengali (CC-BY-NC 4.0 — do not use): https://huggingface.co/facebook/mms-tts-ben

</details>
