# Six-module implementation foundation

This directory is the machine-readable ownership and public-interface index for parallel module work. The canonical authority remains [`plan.md`](../../plan.md), [`docs/plans/README.md`](../../docs/plans/README.md), and [`docs/plans/FOUNDATION_AND_PARALLEL_WORK.md`](../../docs/plans/FOUNDATION_AND_PARALLEL_WORK.md); this manifest is a checked summary, not a second database/API schema.

The shared root and health endpoints (`GET /`, `GET /health`) are infrastructure-owned and intentionally listed outside M1–M6.

## Work independently at these seams

| Module | Own implementation | Stable integration seam | Do not take over |
|---|---|---|---|
| M1 | Farmer auth/profile, farmland, catalog and confirmed farmer facts | Existing M1 routes and M2 `FarmProfileInput` composition | Another module's operational or season records |
| M2 | Crop recommendations, approved knowledge, season lifecycle/plan definitions and new pure advisory computations | Existing `/advisor` routes plus authenticated `/advisor/farmlands/{farmland_id}/planting-window`; response includes annual NASA onset/GDD evidence and provenance | M1 profile/catalog or M3 task/current-stage writes |
| M3 | Farm state, current operational stage, tasks, problems, check-ins | Existing `/farmlands/{id}/state`, tasks, problems, check-ins and plan-task import contracts | M2 plan definition or duplicate state in a new snapshot table |
| M4 | Weather/environment source adapters, QA and dated evidence | Existing `/weather` contracts; planned read-only climate bundle supplied to M2 | Crop decision rules, plan selection or task execution |
| M5 | Farm-scoped conversation, language/voice and proposed-action presentation | Existing chat schemas/routes and the shared ProposedAction contract when approved | Recalculation of agronomy or direct writes to M1/M2/M3/M6 data |
| M6 | Inference and persisted disease result lifecycle | Existing disease endpoints/schema and M3 problem contract | A second farm-problem store |

`seasons.current_growth_stage_id` physically lives on the existing season row, while the operational value is changed only through the M3 state interface. Keep this logical write ownership clear; do not move the column or introduce a parallel current-stage record.

## Contract-first workflow for each contributor

1. Claim only the assigned module folder and list the existing schema/route contract used by callers.
2. Keep external inputs behind the existing typed schemas or an owner-reviewed additive schema. A mock implements that same interface; it must not define a different payload than the production adapter.
3. Add a narrow behavior test at the public interface, then implementation; keep fixtures synthetic and visibly test-only. Avoid import-time network/DB access.
4. Keep DB writes inside the owning module and authenticated farm scope. Migrations are additive, reversible where possible, and include existing-data and clean-database tests.
5. Run the targeted module suite, then `python -m pytest tests -q`; run PostgreSQL migration checks for schema changes. For frontend work also follow [`frontend/AGENTS.md`](../../frontend/AGENTS.md), run lint/typecheck and check a real mobile browser viewport.
6. Update the owning section of `module-ownership.json` when public routes/owned models change; add a contract test. For cross-module changes, record the affected owners and compatibility decision in the shared contract/plan before the interface ships.

The smoke contract test [`tests/test_module_architecture_contract.py`](../tests/test_module_architecture_contract.py) checks that all six manifest identities remain present, every router endpoint is listed under exactly one owner and registered in FastAPI OpenAPI, key request/response schemas retain expected model references and fields, and owned models import. [`integration-mocks.json`](../tests/fixtures/modules/integration-mocks.json) supplies synthetic seam examples that are validated against existing M1–M6 Pydantic contracts; M1→M2 reuses the clearly marked Golden Farm fixture. Each teammate can copy a mock through the existing public contract without waiting for another module's implementation. These smoke checks do not prove behavior, authorization or agronomic correctness; those remain in the existing module tests and parent release gates.

## Shared challenge contract v1

The cross-module Pydantic source of truth is `app/contracts/challenge/v1.py`.
Its JSON Schema and generated TypeScript are checked in at
`contracts/jsonschema/challenge-v1.schema.json` and
`frontend/src/modules/shared/contracts.generated.ts`. Regenerate after a
reviewed contract change with:

```bash
python scripts/export_challenge_contracts.py
python scripts/export_challenge_contracts.py --check
python -m pytest tests/test_foundation_contracts.py tests/test_contract_generation.py -q
```

Executable deterministic adapters are in `tests/fakes/`; all their data is
synthetic and test-only. Run a module suite without another module server with
`python scripts/test_modules.py m1` through `m6`, or
`python scripts/test_modules.py foundation`.

The shared transaction spine uses `app/services/actions/` and calls the
transaction-aware M3 owner operation in `app/services/operational_actions/`.
Its PostgreSQL migration is `c6f4e739a2b1`; feature flags stay false until each
consumer passes its release gates. Check the shared read-only endpoint at
`GET /challenge/foundation/availability`. Missing providers produce a typed
503 unavailable error and never a successful fake result.

Consent records are append-only. Their monotonic server-assigned `version` is
scoped to `(farmer_id, purpose)` and determines the latest decision; the
client-supplied `captured_at` is retained as provenance and cannot reorder
consent. Deferred disease-to-Problem sync is a v1 contract/fake only; the
production sync endpoint remains owned by the coordinated M3/M6 work.

The clean database and existing-row migration paths use `alembic upgrade head`,
`alembic check`, and `python scripts/verify_foundation_upgrade_compat.py`
against a disposable PostgreSQL database whose name contains `test`. Never
point the compatibility script at a development or production database: it
intentionally downgrades and upgrades the configured test database.
