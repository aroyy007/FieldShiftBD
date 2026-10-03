# 🌾 AI Farmer Assistant — Project Plan

> **This document is the source of truth for the project.**
>
> **STRICT RULE:** Always follow this plan. Do not change, restructure, remove, or redefine another module's plan, responsibilities, dependencies, contracts, or workflow without explicit team-level agreement.
>
> **Module-level freedom:** A team member may suggest improvements, alternatives, refactors, or a more detailed implementation plan **only inside their own assigned module**. Such suggestions must not alter another module or the shared project contract unless the team explicitly agrees to the change.

---

## 1. Project Goal

Build an AI-based chatbot that acts as a farmer's season-long assistant — from farm onboarding and crop selection through planning, monitoring, weather-aware decisions, disease detection, and harvesting.

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

### Produces

- Crop Recommendation(s)
- Selected Crop
- Season Plan
- Growth Stage definitions
- Harvest guidance
- Season history data

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
- Satellite monitoring
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

