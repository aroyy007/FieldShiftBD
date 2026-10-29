# Six-module implementation foundation

This directory is the machine-readable ownership and public-interface index for parallel module work. The canonical authority remains [`plan.md`](../../plan.md) and [`docs/plans/README.md`](../../docs/plans/README.md); this manifest is a checked summary, not a second database/API schema.

The shared root and health endpoints (`GET /`, `GET /health`) are infrastructure-owned and intentionally listed outside M1–M6.

## Work independently at these seams

| Module | Own implementation | Stable integration seam | Do not take over |
|---|---|---|---|
| M1 | Farmer auth/profile, farmland, catalog and confirmed farmer facts | Existing M1 routes and M2 `FarmProfileInput` composition | Another module's operational or season records |
| M2 | Crop recommendations, approved knowledge, season lifecycle/plan definitions and new pure advisory computations | Existing `/advisor` routes and existing M2 response schemas; additive versioned result contract for the NASA/adaptive plan | M1 profile/catalog or M3 task/current-stage writes |
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

No new API, table, Alembic revision or migration is introduced by this scaffold. Future NASA/adaptive interfaces in the accepted plan require their own schema, owner review, fixtures and tests before implementation.
