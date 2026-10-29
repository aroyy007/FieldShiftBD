# 🌾 AI Farmer Assistant — Project Plan

> **This document is the source of truth for the project.**
>
> **2026-10-29 planning amendment, requested by the project owner:** Deliver the organizer's NASA planting-window advisory together with the complete final Field Shift problem statement. Section 20 and [the detailed challenge delivery plan](docs/plans/2026-10-29-nasa-planting-window-and-rotation.md) define this added scope, acceptance gates and requirement traceability. The [Bangla voice plan](docs/plans/2026-10-06-voice-first-bangla.md) is its accessibility delivery plan. Existing six-module ownership remains the baseline; proposed additive interfaces must be recorded with affected owners before implementation. This amendment does not claim those interfaces or features are already implemented.
>
> **Accepted follow-up, 2026-10-29:** After the required organizer/rotation flow, deliver decision-driven field questions, rotation robustness envelopes and a confirmed conditional Plan B. The [adaptive-decision specification](docs/plans/2026-10-29-adaptive-decisions-and-confirmed-plan-b.md) defines A01-A08 acceptance gates, ownership, proposed schema and safe execution. This is owner-authorized planning scope; implementation contract/migration decisions still need recording. Start with the [complete plan index](docs/plans/README.md).
>
> **STRICT RULE:** Always follow this plan. Do not change, restructure, remove, or redefine another module's plan, responsibilities, dependencies, contracts, or workflow without explicit team-level agreement.
>
> **Module-level freedom:** A team member may suggest improvements, alternatives, refactors, or a more detailed implementation plan **only inside their own assigned module**. Such suggestions must not alter another module or the shared project contract unless the team explicitly agrees to the change.

---

## 1. Project Goal

Build FieldShift BD as a farmer-centered decision-support mobile app using NASA Earth observations, historical and predictive climate data, local soil/crop knowledge and farmer priorities. It must explain how usable-rain onset and crop thermal accumulation have changed, recommend supported planting/transplanting windows, and compare at least three multi-season rotation strategies including the farmer's existing rotation. Soil health, water/resource feasibility and uncertainty are part of each comparison.

The existing season-long assistant carries these decisions through farm onboarding, crop selection, season planning, monitoring, weather-aware actions, disease detection, harvest and future rotation history. It supports farmer judgment and local expertise. The organizer's planting-window advisory and the final statement's rotation exploration are both required; one does not replace the other.

The farmer should experience **one unified assistant**, not six separate systems.

The six modules are independent development units connected through shared contracts and a shared farm state.

---

# 2. Core Product Principle

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

# 3. Six-Module Architecture

## Module 1 — Farm Profile & Onboarding

### Owns

The progressive intake conversation and the single source of truth for farmer/farm information.

### Responsibilities

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

### Key design problem

This is a **stateful conversation**, not a static form.

The module must:

1. Track information already known.
2. Ask only for missing information.
3. Allow the farmer to correct previous answers.
4. Persist the profile in the agreed shared structure.

### Depends on

None.

---

## Module 2 — Crop Advisor & Season Lifecycle

### Owns

Crop suitability reasoning, crop selection, season-plan generation, harvest guidance, and season-close history.

### Responsibilities

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

### Key design problem

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

### Major project constraint

The main bottleneck is **reliable local agricultural knowledge and crop/variety/season data**, not code.

The owner of this module must prioritize sourcing and structuring the agricultural knowledge before building complex recommendation logic.

### Depends on

Module 1 — Farm Profile.

For the Section 20 advisory extension, consume the read-only district environmental cache/feature interface supplied by M4. This analytical input does not require M3 operational state and must not create a circular dependency: M4 historical-data ingestion is independent of M2/M3.

### Produces

- Crop Recommendation(s)
- Selected Crop
- Season Plan
- Growth Stage definitions
- Harvest guidance
- Season history data
- PlantingWindowAdvisory and RotationComparison (additive contracts in Section 20)

---

## Module 3 — Farm Brain (Task & Monitoring Engine)

### Owns

The current operational state of the farm.

### Responsibilities

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

### Key design problem

This is a **state engine + scheduler**, not a content-generation feature.

It must be able to represent states such as:

```text
Week 4
Current stage = Vegetative
Fertilizer task = Due
Weed-control task = Pending
Problem = Possible leaf disease
```

### Structural role

This is the **central farm-state hub**.

Modules 4, 5, and 6 read from and/or write to Module 3's state instead of creating independent farm-state systems.

### Depends on

Module 2 — Season Plan.

### Produces

- Current Farm State
- Current Crop
- Current Growth Stage
- Task State
- Open Problems
- Check-in State
- Season progress state

---

## Module 4 — Weather Intelligence & Alerts

### Owns

Turning weather information into crop-relevant, growth-stage-aware actions and alerts.

### Responsibilities

- Obtain/process weather information
- Evaluate weather against farm location
- Read crop and growth stage from Module 3
- Consider current and upcoming tasks
- Identify potential agricultural impact
- Generate actionable weather alerts
- Suppress unnecessary alerts
- Acquire, quality-check, harmonize and pre-cache district NASA POWER, IMERG, SMAP, NDVI and the additional scoped Earth-observation/climate layers defined in Section 20
- Expose versioned read-only historical/environmental features, provenance and honest availability/resolution for M2; separate observations, forecasts, reanalysis and climate projections

### Required reasoning pipeline

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

### Key design problem

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

### Depends on

Module 3 — Current Farm State / Growth Stage / Tasks.

This dependency applies to operational alerts. District source ingestion, offline caches and the M4 → M2 historical/environmental interface operate independently of farm/task state; they must not depend on an active season.

---

## Module 5 — Open-Ended Conversational Layer

### Owns

The main conversational interface and message routing.

### Responsibilities

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

### Key design problem

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

### Depends on

- Module 1 — Farm Profile
- Module 2 — Agricultural knowledge/facts
- Module 3 — Current Farm State

### Important ownership rule

Module 5 owns the **conversation**, but it does not become the owner of farm state, crop data, weather data, or disease data.

---

## Module 6 — Disease Detection

### Owns

Image-based crop disease/symptom analysis.

### Responsibilities

- Accept crop images
- Analyze image
- Identify possible disease/symptom category
- Provide confidence level
- Explain visible symptom indicators where appropriate
- Provide safe, practical next actions
- Include the appropriate uncertainty/disclaimer
- Write the result into Module 3 as a farm problem/state update

### Preferred response structure

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

### Key design problem

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

### Depends on

Module 3 — for crop context and for writing the result into farm state.

---

# 4. Shared Domain Model / Contract Layer

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

### Example: FarmProfile

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

### Example: Season

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

### Example: Task

```text
task_id
season_id
title
description
due_date
status
priority
```

### Example: Problem

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

### Example: DiseaseResult

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

# 5. Parallel Development Strategy

## Core rule

**No module developer should wait for another module to finish implementation.**

The team works in parallel using:

1. Shared contracts
2. Mock data
3. Mock dependency providers
4. Clearly defined inputs/outputs
5. Incremental integration

The dependency graph describes runtime dependencies, **not development order**.

---

## Development model

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

# 6. Mock-First Development Rule

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

## Required mock data

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

# 7. Golden Farm Integration Scenario

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

### Golden-flow test

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

# 8. Module Interfaces

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

## Conceptual interfaces

### M1 → M2

```text
FarmProfile
```

### M2 → M3

```text
SeasonPlan
GrowthStages
InitialTasks
```

### M3 → M4

```text
FarmLocation
CurrentCrop
CurrentGrowthStage
RelevantTasks
FarmState
```

### M3 → M5

```text
FarmProfile
CurrentCrop
CurrentGrowthStage
Tasks
OpenProblems
FarmState
```

### M5 → M6

```text
Image
Crop
GrowthStage
OptionalSymptoms
```

### M6 → M3

```text
DiseaseResult / ProblemUpdate
```

### M4 → M3

When a weather event requires a farm-state or task adjustment, the change must be represented through the agreed Module 3 state/task contract rather than a private duplicate state.

### M4 → M2 (2026-10-29 analytical extension)

```text
DistrictClimateBundle
Historical/satellite/climate-scenario features
Source QA, coverage, resolution, method/cache versions and provenance
```

This is a read-only cache/feature interface; historical acquisition does not read M2 or require M3. M2 owns agronomic interpretation and comparative outputs. The new public read-only district `/advisory` route and authenticated farm scenario/write paths are specified in the detailed Section 20 plan. Record additive field/error contracts before implementation; existing M1-M6 routes remain compatible.

---

# 9. Ownership Rules

## Rule 1 — Single owner per data domain

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

# 10. Development Rules

## Rule A — Follow the plan

**Always follow this `plan.md`.**

Do not independently redesign the overall architecture.

Do not move features between modules without team-level agreement.

Do not change another module's responsibility.

Do not change shared contracts unilaterally.

Do not introduce a new cross-module dependency without agreement.

---

## Rule B — Suggestions are allowed only inside your module

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

## Rule C — Shared contract changes require team agreement

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

## Rule D — Use mocks to stay independent

If your dependency is unfinished:

**Do not wait.**

Build a mock implementation that follows the agreed contract.

---

## Rule E — Integrate incrementally

Do not wait until the end to merge everything.

Replace mock dependencies with real implementations gradually.

---

# 11. Git / Branching Strategy

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

## Rules

- Each developer primarily works in their own module branch.
- Keep commits focused.
- Do not make unrelated edits to another developer's module.
- Shared contract changes must be discussed before merging.
- Pull requests should explain what changed and which contract/interface is affected.
- `main` should remain integration-ready.

---

# 12. Integration Workflow

## Stage 1 — Contract setup

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

## Stage 2 — Independent implementation

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

## Stage 3 — Incremental replacement

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

# 13. Testing Strategy

Each module must have:

### Unit tests

Test internal logic without depending on other modules.

### Contract tests

Verify that the module's inputs and outputs match the shared contract.

### Integration tests

Verify real communication with connected modules.

### Golden-flow test

Verify the complete farmer journey using the shared Golden Farm.

---

# 14. Definition of Done Per Module

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

# 15. Recommended Development Milestones

## Milestone 0 — Shared Contract

Complete before serious parallel implementation:

- Domain objects
- Input/output contracts
- Ownership rules
- Golden Farm
- Mock data
- Repository structure

All six developers can then start together.

---

## Milestone 1 — Core Farm Lifecycle

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

## Milestone 2 — Continuous Assistance

Add:

```text
Farm monitoring
Weather intelligence
Contextual chatbot
Proactive alerts/check-ins
```

---

## Milestone 3 — Disease Loop

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

## Milestone 4 — Harvest & Season Close

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

# 16. What We Will NOT Do

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

# 17. Final Architecture

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

# 18. Team Commandments

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

# 19. Change-Control Statement

**This `plan.md` is the baseline project plan and must be treated as immutable during normal development.**

Developers may improve their own module internally and may add implementation-level notes under their own module, but they must not change the project's overall plan, module ownership, shared contracts, dependency structure, or scope on their own.

Any proposed cross-module or project-level change must be raised to the full team for agreement before it is applied to `plan.md`.

Until such agreement occurs, **continue following the existing plan exactly as written.**

The dated Section 20 planning amendment and its accepted adaptive-decision follow-up were explicitly requested by the project owner on 2026-10-29. They record the required product direction and proposed additive interfaces; they do not authorize an individual implementer to invent incompatible fields, apply undocumented migrations or move another module's data ownership.

---

# 20. Organizer and Final Challenge Delivery Requirements — 2026-10-29

The complete implementation and verification specification is [NASA planting windows, rotation decisions and Bangla mobile delivery](docs/plans/2026-10-29-nasa-planting-window-and-rotation.md). Its Section 13 maps all five organizer images and every part of the [preserved final statement](docs/plans/references/2026-10-29-organizer/problem-statement.md) to owners, outputs and release evidence. The original optional considerations are included in this project's scope because the user explicitly requested complete coverage.

## Required outcomes

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
11. After the required core flow, add the [accepted adaptive decisions](docs/plans/2026-10-29-adaptive-decisions-and-confirmed-plan-b.md): M2 chooses a useful farmer-observable question and computes bounded feasible ranges; M1 persists confirmed answers; dated M4 evidence prompts a supported Plan B; M5 presents the exact diff and confirmation; transaction-aware M2/M3 operations apply it once. Preserve completed work, planting history and all farm/season ownership. No paid AI is needed for these deterministic rules.

## Milestones and completion policy

Follow the detailed plan's pre-event preparation and organizer schedule: Day 1 morning compute/tests; afternoon map/crop/distributions; evening advisory/assumptions and recording by 18:30 event-local time; Day 2 morning bilingual phone UI, summaries and an outside-team test; noon freeze/record/submit. This is an initial vertical-slice milestone, not a guarantee that the entire full scope fits 48 hours.

The screenshot's cut order is retained as a contingency, not an automatic waiver of the user's full scope. Report partial milestones honestly and keep outstanding gates open. Full completion requires V01-V15 in the detailed plan plus A01-A08 in the accepted adaptive-decision specification: data, science, agronomy, API, offline, isolation, lifecycle/rotation, decision questions/envelopes/policies, atomic confirmed execution, responsive browser, physical Android, usability, production and submission evidence. Planning checkboxes do not establish implementation or field validation. Rice-floor portfolio optimization, shared-pump scheduling and other research suggestions are not part of this accepted three-feature increment.

