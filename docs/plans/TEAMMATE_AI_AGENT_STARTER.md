# Teammate AI-Agent Starter — Codex, Claude Code and Other Coding Agents

Use the English prompt below with any coding agent; it names repository-relative files so the project can be cloned on any machine. Human-facing reports should use natural Bangla with technical names retained. No specific AI subscription, paid tool or agent-memory service is required.

## 1. Human setup

Give each of the six people one module ID (M1–M6), the repository path and the actual shared foundation commit/tag. Do not invent teammate names. Use a separate checkout/branch per person. Read [final plan](FINAL_IMPLEMENTATION_PLAN.md) and [foundation gates](FOUNDATION_AND_PARALLEL_WORK.md); check the assigned module's [brief](module-briefs/M1.md) by replacing M1 with the actual ID. Do not tell the agent `foundation-v1` exists until the tag has actually been created and verified.

Copy the prompt, replace the three values and send it as the agent's user message. The agent must inspect actual files and open foundation gaps; a prompt cannot make missing contracts implemented. If a needed shared seam is not ready, the agent can still prepare module-local pure logic/data work against a clearly identified draft fake and report the integration blocker without altering another owner's files.

## 2. Copy/paste prompt

```text
You are implementing one assigned module in FieldShift BD.

Assigned module: <M1, M2, M3, M4, M5 or M6 — choose one>
Repository: <absolute path to this person's isolated checkout>
Approved shared base: <actual verified Git commit SHA/tag>

Implement all work allocated to this module in the complete final plan,
including its later/conditional obligations when their conditions are met.
Preserve every other module's ownership and existing compatible behavior.
User-facing reports: natural Bangla; keep technical names in English.

Start by reading these saved repository files:
1. Every applicable AGENTS.md, plus backend/guide.md and DB_SCHEMA.md.
2. docs/plans/FINAL_IMPLEMENTATION_PLAN.md — active consolidated authority.
   Read its reconciled rules, your responsibilities and detailed source appendices.
3. docs/plans/FOUNDATION_AND_PARALLEL_WORK.md — B00-B10 readiness,
   owned paths, reserved shared files, migration and integration process.
4. docs/plans/module-briefs/<assigned-module>.md.
5. backend/contracts/README.md, module-ownership.json and relevant existing
   schemas, routes, tests and fixtures.

First inspect Git branch/status/base and actual code. Preserve unrelated dirty
changes and secrets. Do not pull/reset/clean or overwrite somebody else's work.
Do not assume a package, route, schema, fixture or shared base mentioned as
proposed in the plan already exists. Verify it on disk/in OpenAPI.

Before coding, report briefly:
- The module, base SHA, owned implementation paths and consumed contracts.
- Existing working behavior you will reuse and relevant open foundation gates.
- The first independently testable slice and required evidence.
Then proceed with authorized module-local implementation. Do not stop just to
ask permission for routine reversible choices already covered by the plan.

Architecture and change discipline:
- Domain owner writes its data; consumers use agreed interfaces.
- Use frozen typed contracts and executable fake adapters at external seams.
  Do not create a competing auth/API client/farm state/confirmation store.
- Shared contracts, app composition, ORM/migrations, global fixture/manifest,
  dependencies/lockfiles, CI, AppProvider, farm-data, shared UI/layout/theme and
  generated artifacts have a single integration steward. Read them freely;
  produce a precise proposed patch/contract request for the steward rather
  than editing outside your allocation or guessing a teammate's payload.
- A shared change request states producer, consumers, exact old/new schema,
  units/null/error semantics, compatibility, migration and tests. Keep working
  on independent local slices while a genuinely required decision is pending.
- Keep module frontend code/i18n under its assigned namespace; give the steward
  an exported mount instead of all six editing FarmlandChat/AppProvider.
- No import-time network/data/model downloads. Keep compute pure and inject
  clock/evidence/storage at the agreed seam.
- Every synthetic fixture is test-only. Never seed it as agricultural advice.
  Missing evidence returns explicit unavailable/conditional results, not invented
  thresholds, percentages, dates, yield, prices or false success.
- Typed future skeletons must not execute real side effects until dependencies
  and migrations are verified. Do not claim a stub as an implemented feature.

Correctness:
- Enforce farmer/farm/season/plan ownership and exact current-state preconditions.
- Preserve no-active-crop/no-season cases; unknown is not zero or false.
- Explicit read-back/confirmation for writes. Sensitive actions require a tap.
- Replays of same action/key/payload return the committed receipt; stale values
  or changed payloads conflict. Multi-owner effects use one real PostgreSQL UOW,
  never a sequence of independent HTTP/commit calls.
- Respect completed tasks, actual planting history and one active season.
- Device offline queue and server OFFLINE=1 are distinct. Scope caches/writes
  to account/farm/season/version/expiry; no cross-account replay or silent renewal.
- Reconcile disease Problem creation with deferred confirmation in coordinated
  M3/M5/M6 interfaces; changing only a UI card cannot prevent a backend auto-write.

Verification:
- Use meaningful tests at existing public/contract seams, hand-worked expected
  cases and deterministic fakes, then real adapters/integration as available.
- Run your owner tests and the shared module architecture contract suite.
  Before merge, run the complete backend suite and appropriate PostgreSQL
  migration/transaction checks against a disposable test database.
- If frontend changes, follow frontend/AGENTS.md: inspect actual Expo version,
  verify matching official docs for native APIs, use Expo Router/config plugins,
  SDK-compatible installation, lint/typecheck and Chrome real mobile viewports.
- Native voice/permissions/background behavior needs physical Android evidence;
  responsive Chrome does not prove it. Report unavailable device/data blockers.
- Test positive, missing/invalid/stale, denied permission/provider outage,
  unauthorized/two-farm, retry/concurrent confirmation and rollback cases relevant
  to your module. Do not add meaningless tests just to inflate counts.
- Review the changed diff against the final plan and standards. Report actual
  command results, skips and limitations; do not reuse historical green counts.

Completion and handoff:
- Produce module-local implementation + contracts/fake usage + tests + evidence.
- Map final-plan requirement IDs, voice flows/CCRs and release gates to actual
  commits/files/test results. List anything remaining or conditionally deferred.
- Describe exact shared patches/dependency PRs needed for integration.
- Stay on the assigned branch. Do not merge, deploy, force-push, create public
  issues, send teammate messages or push to a different branch without explicit
  authorization. Commit/push/PR only according to the human team's given workflow;
  no local skill may override a narrower instruction from the human.
- Never say the entire project or all four source plans are complete merely
  because this assigned module or its mocks pass.
```

## 3. Module briefs

| Module | Open this brief | Key integration partners |
|---|---|---|
| M1 | [Profile and onboarding](module-briefs/M1.md) | M2/M5 for confirmed facts, M4 for canonical location |
| M2 | [Science, rotation and adaptive decisions](module-briefs/M2.md) | M1 context, M4 evidence, M3 operations, M5 narration |
| M3 | [Operational state and task/Problem changes](module-briefs/M3.md) | M2 plans, M5 UOW, M6 confirmed Problem |
| M4 | [Environmental evidence and cache](module-briefs/M4.md) | M2 analysis, M3 live state, M5 updates |
| M5 | [Conversation, voice and shared integration](module-briefs/M5.md) | All domain owners; steward responsibility |
| M6 | [Disease lifecycle and confirmed handoff](module-briefs/M6.md) | M3/M5 for deferred Problem actions |

## 4. Handoff report template

```text
Module / branch / base SHA / final SHA:
Requirements implemented / verified / still open:
Owned files changed:
Contract version + producers/consumers + mocks used:
Shared steward patches and dependency branches:
Schema/migration changes and clean/existing DB proof:
Commands + actual outputs/skips:
Browser viewport/device and observed behavior (if applicable):
Missing data/native capability/conditional later scope:
Integration sequence and rollback/feature flag:
```

The scaffold does not promise zero merge conflicts. Isolation, one writer for shared files, fixed contracts and verification reduce both textual conflicts and failures that Git cannot detect.
