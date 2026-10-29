# Foundation Readiness and Six-Person Work Allocation

**Authority:** [final consolidated plan](FINAL_IMPLEMENTATION_PLAN.md). **Status:** shared foundation implemented on the current working branch; readiness evidence is recorded in §8. This is the integration handoff for six contributors, not a claim that the six domain features or production datasets are complete. The integration steward is one of the six owners (default M5 role), not a seventh module/person.

## 1. What exists and what is missing

Baseline was `336bf6c`. The shared contract, deterministic fakes, safe-off runtime, transaction-aware persistence spine, cache-only reader, frontend module seams, CI gates, ownership map, and teammate briefs now exist at the paths below. Keep algorithms, real providers/datasets, production voice/offline behavior, and module-owned feature work with their assigned owners. Do not replace the implemented app with six empty copies.

## 2. Foundation gates and deliverables

| Gate | Implement before sharing the base | Responsible role / proof |
|---|---|---|
| B00 Baseline | **Implemented.** Baseline `336bf6c`; isolated PostgreSQL 16 test DB; root/backend `.env.example` placeholders; unrelated pre-existing work preserved. | Backend baseline and full unit suite; frontend lint/typecheck; clean disposable DB used. Migration verification is restricted to a database name containing `test`. |
| B01 Contracts | **Implemented.** Versioned v1 Pydantic contracts, ports, JSON Schema and generated TypeScript. Includes source lineage/quality, M1 farm profile snapshot, climate coverage, advisory/rotation/adaptive outputs, action/receipt/task-diff, consent, deferred M6 sync and typed errors. M3's existing `FarmStateRead`/`GET /farmlands/{id}/state` is reused; no duplicate operational-state API or schema was added. | `backend/app/contracts/challenge/`; `backend/contracts/jsonschema/`; `frontend/src/modules/shared/contracts.generated.ts`; existing M3 contract at `backend/app/schemas/farm_state.py`; generator has a drift check. |
| B02 Fakes | **Implemented.** Deterministic module adapters/fixtures use synthetic-only records and cover healthy/uncertain/low-confidence, stale, unsupported, conflict, retry and failure cases. Existing M3 state-read consumers keep their module-specific fakes; no competing M3 state implementation is introduced. | `backend/tests/fakes/`; M3 read contract adapter in `backend/app/services/module3_client.py`, its consumer fake in `backend/tests/test_disease_api.py`, and M4's existing fixture/projection in `backend/app/services/mock_farm_state.py` / `farm_state_read_slice.py`; tests cover fake contracts and state transitions. Fakes are never production providers. |
| B03 Composition | **Implemented.** One startup registration, typed availability endpoint, injectable runtime and default-off module flags; no import-time network/model download. Unavailable features return typed 503. | `backend/app/services/foundation/`; `backend/app/api/routes_foundation.py`; existing routes remain unchanged. |
| B04 Transaction spine | **Implemented and PostgreSQL-tested.** Unit of work, transaction-aware M3 task-diff operation, consent-gated/versioned action lifecycle, idempotency, preconditions, immutable receipts and transactional outbox. | `backend/app/services/actions/`; `backend/app/services/operational_actions/`; rollback, scope, retry and concurrent confirmation tests. Existing public M3 routes keep their own commit behavior. |
| B05 Schema spine | **Implemented and migration-tested.** One additive migration creates eight new tables and append-only triggers for immutable records; existing tables are untouched. | `backend/alembic/versions/c6f4e739a2b1_add_shared_foundation_persistence_spine.py`; `DB_SCHEMA.md` §20; clean upgrade, downgrade/re-upgrade with legacy rows and `alembic check` passed. |
| B06 Data spine | **Foundation implemented; source population remains M4 work.** Configurable cache root; default bounds are 2 MiB per manifest, 1 GiB per asset, and 4 GiB per bundle, with 1 MiB checksum chunks. Reader is traversal-safe/cache-only and checks schema, expiry, declared sizes and checksums; offline network guard, synthetic fixture and D01–D12 source register are present. | `backend/app/services/climate/cache.py`; `backend/data/climate/`; `backend/tests/test_climate_cache.py`. No live district cache or calibration is claimed. |
| B07 Frontend spine | **Implemented; user flow browser check recorded in §8.** Shared M1–M6 export folders, typed client, generated types, EN/BN namespace registry, safe-disabled cache/outbox/speech, explicit-tap consent, confirmation-card model and existing-route mounts. | `frontend/src/modules/`; `npm run lint`, `npx tsc --noEmit`, `npm test`; no native Expo API or production queue/speech behavior was guessed. |
| B08 M6 compatibility | **Contract/fake seam implemented; live sync remains M6/M3 integration work.** Deferred confirmation requires an explicit pending/confirmed/denied choice; confirmed sync requires a consent receipt; a Problem link is legal only for a synchronized result. Feature stays off and current DiseaseResult/Problem routes were not changed. | `DiseaseProblemSyncRequest` and `DiseaseProblemSyncReceipt` in `backend/app/contracts/challenge/v1.py`; M6 fake tests. No production DiseaseResult→Problem sync endpoint is added by this foundation. |
| B09 Verification/CI | **Implemented and locally verified.** Separate contract, per-module unit matrix, PostgreSQL integration, and frontend lint/typecheck/test/build jobs. Includes deterministic artifact drift and module-selective test commands. | `.github/workflows/ci.yml`; `backend/scripts/test_modules.py`; `backend/scripts/export_challenge_contracts.py`. No cloud key is required for core checks. |
| B10 Handoff | **Implemented; release commit/tag must match the verified commit.** Six briefs define boundaries, dependencies, contract commands and shared-file ownership; ownership manifest carries exact paths and feature defaults. | `docs/plans/module-briefs/M1.md` through `M6.md`; `docs/plans/TEAMMATE_AI_AGENT_STARTER.md`; `backend/contracts/module-ownership.json`. Do not branch teammates before the verified foundation commit is available. |

The shared foundation is ready for module owners to begin isolated domain implementation after its verified commit is shared. It does **not** mean NASA climate series, agronomic onset/degree-day calculations, rotation evidence, adaptive policies, live disease sync, actual voice, or durable offline sync are complete. Readiness is per seam: domain work may use B01–B03 fakes; persistence integrations must pass B04/B05/B08 gates; production voice/offline needs platform-specific consent, security, delivery and native capability checks. Do not treat a safe-off interface or synthetic fixture as production advice.

## 3. Implemented foundation paths and module-owned extension locations

The first rows below are implemented foundation code. Remaining module feature paths are owner work; check existing routes/services before adding a parallel implementation.

| Area | Reserved location | Primary writer |
|---|---|---|
| Shared contracts and ports | `backend/app/contracts/challenge/`; JSON Schema at `backend/contracts/jsonschema/`; generated TS at `frontend/src/modules/shared/contracts.generated.ts` | Steward, single writer |
| Deterministic fakes | `backend/tests/fakes/m1.py` through `m6.py`; fixtures at `backend/tests/fixtures/foundation/` | Test-only; module owners may extend their fake after contract review |
| Climate cache | `backend/app/services/climate/cache.py`; `backend/data/climate/` | Foundation reader is read-only/offline; M4 owns ingestion, calibration and real bundles |
| Profile snapshot | `backend/app/services/profile_intake/snapshot.py` | Reads M1 records; M1 remains authoritative writer |
| Operational state read | Existing `GET /farmlands/{id}/state` + `FarmStateRead`; M6's authenticated `Module3Gateway` and M4's scoped `FarmStateSlice` projection | M3 remains authoritative; consumers reuse the existing contract, and M4/M6 keep their existing test fakes |
| Operational task diff | `backend/app/services/operational_actions/task_diff.py` | Transaction-aware M3-owned write seam; never call a separately committing route inside the UOW |
| Action coordination and outbox | `backend/app/services/actions/` | M5 orchestration; M2/M3/M6 own source-domain data |
| Runtime composition | `backend/app/services/foundation/`; `backend/app/api/routes_foundation.py` | Steward; safe-off and read-only availability only |
| Module frontend exports | `frontend/src/modules/m1/` through `m6/`; shared ports/adapters in `frontend/src/modules/shared/` | Corresponding module owner; shared registry has one writer |
| Localized strings | Shared namespace registry `frontend/src/modules/shared/i18n.ts` | Shared namespace registration is steward-owned; module copy is owner-owned |
| Test selection | `backend/scripts/test_modules.py`; `backend/tests/test_*.py`; shared fakes under `backend/tests/fakes/` | Each module suite runs independently of peer servers |
| Owner briefs | `docs/plans/module-briefs/M1.md` through `M6.md`; starter at `docs/plans/TEAMMATE_AI_AGENT_STARTER.md` | Shared handoff docs; each owner updates only their brief when scope changes |
| Domain algorithms/services | Existing M1–M6 module paths; M2's planned pure agronomy code belongs under `backend/app/services/` and must be named once by its owner | Module owner; no algorithm or external-data provider is implemented by this foundation |

## 4. Existing-file write allocation

An owner may edit only their listed existing files and assigned new subtree; read other modules freely. Missing files require checking actual names, not creating a second version. This allocation concerns physical Git writes; domain operations retain final-plan ownership.

| Owner | Existing backend implementation files | Existing frontend files/screens |
|---|---|---|
| M1 | `api/routes_m1_profile.py`, `api/routes_m1_catalog.py`, `schemas/profile.py`, `schemas/catalog.py`, `services/m1_reference.py`, `services/m1_catalog_import.py`, M1 data catalogs | `services/m1-reference.ts`, `services/farm-location.ts`, auth screens, `app/farmlands/index.tsx` list, farm add/manage/profile-setup/resources screens and M1 profile components |
| M2 | `api/routes_m2_advisor.py`, `schemas/m2_advisor.py`, `services/m2_*`, M2 evidence files/import tooling | `services/m2-advisor.ts`, crop-advisor/season-plan screens, CropAdvisorPresentation and related icons |
| M3 | `api/routes_farm_state.py`, `schemas/farm_state.py`, `services/farm_state.py`, `services/farm_state_read_slice.py` | `utils/task-dates.ts`, tasks/problems/check-ins screens and operational-only view components |
| M4 | `api/routes_m4_weather.py`, `schemas/weather.py`, weather provider/threshold/suppression and mock-farm-state files | alerts screen; new `modules/m4/` maps/layer/exported views |
| M5 | `api/routes_m5_chat.py`, `schemas/chat.py`, `services/chat_engine.py` | `services/m5-chat.ts`, FarmlandChat, chat screen; shared files only in steward capacity under the next section |
| M6 | `api/routes_disease.py`, `schemas/disease.py`, disease_inference/gemini_verification/module3_client files, M6 class/model artifacts | `utils/disease-api.ts`, crop-health screen, ScanLeafResult and scan-only icons |

All paths above are relative to `backend/app/` or `frontend/src/` as appropriate. Existing `frontend/src/services/farm-data.ts`, `app/index.tsx`, `app/farmlands/[id]/index.tsx`, shared `field-screen-ui.tsx`/`ui.tsx`/sidebar/layout components are steward-owned, since several modules consume them. M3 can request a farm-data adapter patch; M4 can request a map/layout mount; M6 can request shared refresh hooks. Do not let all six edit these files concurrently.

## 5. Single-writer shared files

Only the integration steward writes `backend/app/main.py`, `core/config.py`, DB/session/security infrastructure, shared contract package, `app/models/*`, model export files, Alembic revisions/environment, DB_SCHEMA, global fixture/harness files, ownership manifest, global test config, requirements/lockfiles, Docker/compose, CI workflows, global documentation index, root plan, app config/package lock, `frontend/src/services/api-client.ts`, `services/farm-data.ts`, `context/AppProvider.tsx`, `app/_layout.tsx`, farm layouts/sidebar, shared theme/UI/i18n registry and generated artifacts. This avoids same-file domain-owner collisions; model meaning still needs the affected domain owner's review.

Domain owners submit patch text/branch commits scoped to the shared need; steward applies one serialized integration patch. Generated output has one generator/writer and deterministic check, not hand-merged edits. PostgreSQL migrations get unique revision IDs and a planned single head; if parallel revisions already exist, steward inspects the graph and creates a reviewed merge revision when appropriate—never rename an applied revision or change a teammate's schema blindly.

## 6. Git and integration protocol

1. Record remote/main/base SHA and actual ownership allocation. Create one isolated checkout/worktree and feature branch per person from the same verified base; never let six agents operate one working directory. Suggested new names are `feature/m1-profile`, `feature/m2-advisory`, … `feature/m6-disease`, created only when requested by the human/team workflow.
2. Keep each branch limited to assigned paths. Rebase/merge shared foundation updates deliberately; no force-push/rewrite of another person's branch. No automatic pulls into dirty work or reset/clean discarding changes.
3. Contract producer and consumer prepare typed fixtures/fakes first; domain implementation uses those contracts without waiting for another branch. M4 data ingestion and M2 pure compute may proceed in parallel; the new analytical bundle has no M3 dependency.
4. Submit small module PRs with contract version, touched paths, migration/dependency list, verification commands/results and unsupported cases. Required changes outside ownership go through the steward.
5. Integrate one seam at a time: M1 snapshot ↔ M2; M4 bundle ↔ M2; M2 plan ↔ M3; M3 state ↔ M4/M5/M6; M6 deferred result ↔ M5 confirmation ↔ M3; M5 action UOW ↔ owning operations; then frontend/voice/offline.
6. Validate the merged candidate, not only isolated branch tests. Full Golden Farm + real PostgreSQL integration and UI checks precede advancing the release gate. Never treat a conflict-free textual merge as semantic compatibility.
7. If two branches touch a shared file, stop automatic conflict resolution and compare both domain intentions against the frozen contract; steward merges once and both affected owners validate. Do not select “ours/theirs” wholesale.

## 7. What prevents which failure

| Failure | Control |
|---|---|
| Same-line/module composition conflicts | One writer for globals + module-local exports/strings/tests + isolated checkouts |
| Silent schema disagreement without a Git conflict | Versioned producer/consumer contracts, generated types, fake/real conformance and exact compatibility checks |
| Multiple Alembic heads or broken old data | Serialized migrations, unique revision allocation, clean/existing test DB checks |
| Double action/partial task change | Shared UOW, receipt/idempotency and PostgreSQL rollback/race tests |
| M6 Problem created before consent | Coordinated feature-negotiated deferred sync and idempotent M3 owner execution |
| Fake scaffold presented as complete science | Typed unavailable placeholders, default-off runtime execution, synthetic-only fixtures and explicit evidence gates |
| User expects zero conflict guarantee | Report residual risk: API semantics, changed source assumptions and integration failures still require review/tests |

## 8. Foundation handoff evidence and definition of done

Verified locally on `2026-10-29` from baseline `336bf6c`:

| Check | Command / environment | Result |
|---|---|---|
| Full backend unit and PostgreSQL suite | `cd backend && .venv/Scripts/python -m pytest -q` with the disposable PostgreSQL test URL configured | **265 passed**; 7 existing deprecation/metadata warnings |
| Foundation-focused backend selector | `cd backend && .venv/Scripts/python scripts/test_modules.py foundation -q` | **52 passed**; synthetic fakes, cache limits, profile snapshot, and action boundaries included |
| Clean PostgreSQL migration + backward-data compatibility | PostgreSQL 16 disposable DB `fieldshift_foundation_test`; `alembic upgrade head`; `python scripts/verify_foundation_upgrade_compat.py`; `alembic check` | **Passed**; seeded pre-foundation farmer/farm/crop rows survived; no schema drift |
| PostgreSQL action and migration integration | `pytest -q tests/test_pg_foundation_integration.py tests/test_pg_reference_integration.py` | **5 passed**; append-only, consent version ordering, concurrency, receipts/outbox and reference integration included |
| Contract artifacts | `python scripts/export_challenge_contracts.py --check` | **Passed**, JSON Schema and TypeScript are current |
| Frontend | `npm run lint`; `npx tsc --noEmit`; `npm test`; `npx expo export --platform web` | **Passed**; frontend tests **12/12**; all 20 Expo Router routes exported |
| Browser auth and farmlands flow | Real Chrome with mobile emulation at **393×852** and **360×800** | **Passed**: signup, profile load, add/save farm, list/search/clear, select farm → chat; API returned expected 201/200; no browser runtime errors or horizontal overflow |

The shared interface is implementable without peer servers or production credentials. Runtime effects stay disabled until the owning module's real dependencies meet their release gate. A handoff is not complete from folders/JSON examples alone; the executable interfaces, tests, ownership map and evidence above travel together.

**Open production dependency review:** `npm audit --omit=dev` against the unchanged dependency lock reports 15 findings (5 low, 6 moderate, 4 high, 0 critical), including Expo/tooling transitive packages and `expo-router` query-string dependencies. No dependency versions were changed as part of this shared-contract foundation. Review SDK-compatible patched versions before a production release; do not apply a broad/major `npm audit fix` without confirming Expo compatibility and rerunning mobile/build checks.
