# FieldShift PostgreSQL Schema Proposal

> **Status: design draft.** This document makes concrete recommendations for a standalone
> PostgreSQL implementation, but it does not authorize migrations. The team must approve
> the shared domain contract before schema implementation begins.

## 1. Overview

The database should follow the project's six-module architecture and the core product hierarchy:

```text
Farmer → Farmland → Season → Farm State
```

The other module data attaches to these core entities.

The database should **not** be split into six independent module databases. Instead, there should be one shared relational data model with clear ownership boundaries.

The core relationship is:

```text
Farmer
  │
  ├── FarmProfile
  │
  └── Farmland
        │
        ├── Crop Preferences and Recommendations
        │
        ├── Seasons
        │     │
        │     ├── Season Plan
        │     │     ├── Growth Stages
        │     │     └── Tasks
        │     │
        │     └── Farm State
        │           ├── Problems
        │           ├── Check-ins
        │           └── Current Stage
        │
        ├── Weather Events
        ├── Weather Alerts
        │
        ├── Disease Results
        │
        └── Conversations
              ├── Chat Messages
              └── Chat Responses
```

This follows the project's rule that Module 3 is the central farm-state hub, while Modules 4, 5, and 6 read from and/or write through the agreed farm-state representation rather than creating competing state systems.

### Decisions used in this proposal

- Use **standalone PostgreSQL**; this design does not depend on Supabase, Supabase Auth, or Row Level Security.
- Use UUID primary keys, `timestamptz` timestamps stored in UTC, foreign keys, and explicit constraints.
- A farmland has one farmer/owner in the first release. Do not add shared farm memberships until that workflow is required.
- Store a season's crop and harvest outcome on the `seasons` row. Do not duplicate them in a separate `farm_history` table.
- Represent `FarmState` as a Module 3 service/API view over normalized season, task, problem, and check-in data; do not store a second aggregate copy.
- Store task lifecycle status (`pending`, `completed`, `skipped`, `cancelled`); derive “due” and “overdue” from the due time and current status.
- Keep queryable domain facts in typed columns. Use `jsonb` only for bounded, variable provider/model payloads or flexible profile details, not as a replacement for relational data.
- Store uploaded files outside PostgreSQL (object storage); persist only a storage key and relevant metadata.

These choices are a recommended starting point. Changes to shared contracts, ownership, or module boundaries still require team agreement as stated in `plan.md`.

---

# 2. Farmer vs Farmland

The product's UI has multiple farmlands under one farmer:

```text
Farmer
 ├── Farmland A
 ├── Farmland B
 └── Farmland C
```

Therefore, `Farmer` and `Farmland` should be separate entities.

## `farmers`

Represents the person.

```text
id                  uuid primary key
name                text not null
phone_e164          text not null unique
created_at          timestamptz not null
updated_at          timestamptz not null
```

Authentication credentials should be implemented only after the authentication approach is agreed. If the backend owns password authentication, store an Argon2id password hash in a separate credential field/table—never a plaintext password. Do not treat a phone number alone as proof of identity.

## `farmlands`

Represents an individual piece or farming unit owned or managed by the farmer.

```text
id                      uuid primary key
farmer_id               uuid not null references farmers(id)
name                    text not null
country_code            char(2) not null default 'BD'
division                text
district                text
upazila                 text
village_or_locality     text
latitude                numeric(9,6)
longitude               numeric(9,6)
land_area_sqm           numeric(14,3) not null check (land_area_sqm > 0)
land_area_display_unit  text not null
soil_type               text
irrigation_available    boolean
water_source            text
farming_method          text
created_at              timestamptz not null
updated_at              timestamptz not null
```

Convert user-entered area to canonical square metres on input; retain the display unit (`square_metre`, `decimal`, `acre`, or `hectare`) for presentation. Do not include `bigha` until the team agrees on a region-specific conversion because its size is not uniform. Use `CHECK` constraints for latitude/longitude ranges and the approved display-unit values. `latitude` and `longitude` must either both be null or both be present. Keep administrative location names as text initially; introduce reference tables only when the team has a reliable, maintained Bangladesh location dataset. Use the coordinates for weather queries when available.

This allows a farmer to have multiple independent farming contexts:

```text
Rahim
 │
 ├── North Field
 │     └── Potato season
 │
 └── South Field
       └── Rice season
```

This maps directly to the product flow:

```text
All Farmlands
      ↓
Selected Farmland
      ↓
Farmland-specific activity
```

---

# 3. Farm Profile

The shared contract includes information such as:

- location
- land area and unit
- soil information
- irrigation availability
- water source
- previous crop and yield
- farming equipment
- farming experience
- farming method
- seasonal budget
- crop preferences
- optional livestock information

These should not necessarily all live in one huge table.

## `farmer_profiles`

Farmer-level information:

```text
id                      uuid primary key
farmer_id               uuid not null unique references farmers(id)
farming_experience_years numeric(4,1) check (farming_experience_years is null or farming_experience_years >= 0)
equipment               jsonb not null default '[]'
livestock               jsonb not null default '[]'
created_at              timestamptz not null
updated_at              timestamptz not null
```

Farmland-level information belongs on `farmlands` and is not duplicated in this profile. Previous crops and yields are obtained from completed `seasons` (see below), avoiding a second, potentially inconsistent farm-history record.

Crop preferences are relational rather than a JSON list:

## `farmland_crop_preferences`

```text
farmland_id     uuid not null references farmlands(id)
crop_id         uuid not null references crops(id)
preference_rank integer not null check (preference_rank > 0)
notes           text
created_at      timestamptz not null
primary key (farmland_id, crop_id)
unique (farmland_id, preference_rank)
```

The budget is season-specific and belongs on `seasons` as `budget_amount` plus `budget_currency`, rather than on the farmland profile.

---

# 4. Crops

The database should distinguish the crop itself from a crop being grown on a particular farmland.

## `crops`

Agricultural crop identity/master data:

```text
id                  uuid primary key
name                text not null
scientific_name     text
description         text
created_at          timestamptz not null
updated_at          timestamptz not null
```

Examples:

```text
Potato
Rice
Tomato
Chili
Wheat
```

Treat this table as a shared crop catalogue, not a hard-coded allowlist of crops. Do not limit farmer choices to the example crops above.

### `crop_varieties` and agricultural knowledge provenance

Add `crop_varieties` for locally meaningful variety names, linked to `crops`. A variety may be unknown when a season is first created, so the season may retain a farmer-entered `variety_name` until a curated variety record exists. Do not block onboarding or crop selection on catalogue completeness.

For crop suitability, planting windows, and other advice, retain source/provenance with the knowledge record: source name, source URL or document identifier, applicable region, valid/effective dates where relevant, review status, and reviewer. Only use knowledge marked reviewed/approved for farmer-facing recommendations. The initial schema should not invent crop calendars or treat the sample crops as a complete Bangladesh dataset.

Suggested tables:

```text
crop_varieties
  id                  uuid primary key
  crop_id             uuid not null references crops(id)
  name                text not null
  description         text
  created_at          timestamptz not null
  unique (crop_id, name)

agricultural_knowledge
  id                  uuid primary key
  crop_id             uuid references crops(id)
  crop_variety_id     uuid references crop_varieties(id)
  category            text not null
  region_code         text
  content             jsonb not null
  source_name         text not null
  source_reference    text
  effective_from      date
  effective_to        date
  review_status       text not null
  reviewed_by         uuid references farmers(id)
  reviewed_at         timestamptz
  created_at          timestamptz not null
  updated_at          timestamptz not null
```

Knowledge not yet reviewed is retained for curation but must not be used as authoritative farmer-facing advice. `region_code` should use an agreed convention before data entry (for example an agreed administrative code), not free-form labels with inconsistent spellings.

## `seasons`

Represents one crop cycle on a farmland:

```text
id                      uuid primary key
farmland_id             uuid not null references farmlands(id)
crop_id                 uuid not null references crops(id)
crop_variety_id         uuid references crop_varieties(id)
variety_name            text
planting_date           date
expected_harvest_date   date
actual_harvest_date     date
status                  text not null
current_growth_stage_id uuid
budget_amount           numeric(14,2) check (budget_amount is null or budget_amount >= 0)
budget_currency         char(3) not null default 'BDT'
actual_yield            numeric(14,3) check (actual_yield is null or actual_yield >= 0)
yield_unit              text
outcome_notes           text
created_at              timestamptz not null
updated_at              timestamptz not null
```

Agree the canonical `yield_unit` values before collecting data; never compare yields stored in different units without conversion.

This is preferable to repeatedly storing strings such as:

```text
crop = "Potato"
```

throughout the database.

Use a database constraint for the agreed season statuses and a check that the actual harvest date is not before the planting date when both are present. A season's `actual_yield`, `yield_unit`, and `outcome_notes` are the season-close history. The previous-crop/yield context for a new recommendation is queried from earlier seasons on that farmland; there is no separate `farm_history` table.

When `crop_variety_id` is set, verify that it belongs to the same `crop_id` (using a composite foreign key or an equivalent database constraint). Keep `variety_name` for a farmer-entered name when no curated variety exists.

Recommended season statuses: `planned`, `active`, `completed`, `cancelled`. Permit only one active season per farmland with a partial unique index if the team confirms the product must support only one active crop cycle on each farmland.

---

# 5. Crop Recommendations

Module 2 needs to recommend suitable crops before the farmer selects one.

## `crop_recommendations`

```text
id              uuid primary key
farmland_id     uuid not null references farmlands(id)
crop_id         uuid not null references crops(id)
score           numeric(6,5) check (score is null or score between 0 and 1)
status          text not null
reasoning       jsonb not null default '{}'
knowledge_refs  jsonb not null default '[]'
created_at      timestamptz not null
```

Because recommendations must be explainable, the recommendation should also preserve the reasoning.

Keep explanation structured in `reasoning` rather than adding a new SQL column for every explanation category. Its API contract should define stable keys and values; it may include:

```text
soil_reason
timing_reason
irrigation_reason
climate_reason
land_area_reason
budget_reason
concerns
```

For example:

```json
{
  "suitable_because": [
    "soil",
    "planting_timing",
    "irrigation",
    "climate"
  ],
  "concerns": [
    "water_availability",
    "disease_risk"
  ]
}
```

The important requirement is that recommendations should not depend only on one opaque score.

Recommended recommendation statuses: `proposed`, `selected`, `dismissed`, `expired`. Keep `score` optional and supplementary; the structured explanation and approved knowledge references are more important than ranking by a single score.

---

# 6. Season Plan

The season plan is a major part of the system because Module 3 turns it into operational tasks.

## `season_plans`

```text
id          uuid primary key
season_id   uuid not null references seasons(id)
title       text not null
description text
status      text not null
created_at  timestamptz not null
updated_at  timestamptz not null
```

## `growth_stages`

```text
id              uuid primary key
season_plan_id  uuid not null references season_plans(id)
name            text not null
description     text
sequence        integer not null check (sequence > 0)
start_day       integer check (start_day is null or start_day >= 0)
end_day         integer check (end_day is null or end_day >= start_day)
created_at      timestamptz not null
```

Require unique `(season_plan_id, sequence)` so stages have a stable order. `seasons.current_growth_stage_id` is nullable before a stage is known; the application must ensure it refers to a stage in that season's plan.

Recommended plan statuses: `draft`, `active`, `superseded`, `completed`.

Example:

```text
Season Plan
│
├── Germination
├── Vegetative
├── Flowering
├── Tuber/Bulb Development
└── Harvest
```

Growth stages should be separate records because the farm-state engine needs to know the current stage.

---

# 7. Tasks

Tasks belong to Module 3 because Module 3 owns the operational state of the farm.

## `tasks`

```text
id                  uuid primary key
season_id           uuid not null references seasons(id)
growth_stage_id     uuid references growth_stages(id)
title               text not null
description         text
due_at              timestamptz
status              text not null
priority            text not null
source              text not null
completed_at        timestamptz
created_at          timestamptz not null
updated_at          timestamptz not null
```

Possible statuses:

```text
pending
completed
skipped
cancelled
```

“Due” and “overdue” are derived in queries/API responses from `due_at`, the current time, and `status`; they are not persisted statuses. This prevents stale values when time passes.

Recommended priorities: `low`, `normal`, `high`, `urgent`.

Possible task sources:

```text
season_plan
weather
disease
farmer
system
```

The `source` field becomes useful when a task is created or modified because of weather, disease, farmer input, or the season plan.

---

# 8. Farm State

Farm State is the central operational state owned by Module 3.

A `farm_state` record should not become a giant JSON document containing copies of every task, problem, weather event, etc.

Instead, the current state should point to the normalized records that represent it.

## `FarmState` representation (no `farm_states` table)

```text
No separate persisted table in the first version.
```

`FarmState` is the Module 3 service/API representation assembled from normalized records:

```text
FarmState
 ├── current_growth_stage → growth_stages
 ├── tasks                → tasks
 ├── problems             → problems
 └── check-ins            → farm_checkins
```

The current growth stage is stored on the active `seasons` row; tasks, problems, and check-ins remain their own records. This avoids a duplicate farm-state snapshot that could become inconsistent. If later requirements need an auditable event/snapshot history, design that separately rather than adding a JSON state blob.

---

# 9. Problems

Problems are owned by Module 3 because they are persistent farm-state information.

## `problems`

```text
id              uuid primary key
farmland_id     uuid not null references farmlands(id)
season_id       uuid references seasons(id)
source          text not null
category        text not null
description     text not null
severity        text not null
status          text not null
created_at      timestamptz not null
resolved_at     timestamptz
```

Example:

```text
source: disease_detection
category: leaf_disease
description: Possible late blight
severity: moderate
status: open
```

Recommended problem statuses: `open`, `monitoring`, `resolved`, `dismissed`. Recommended severity values: `low`, `moderate`, `high`, `critical`.

The important ownership relationship is:

```text
Disease Detection
      ↓
Disease Result
      ↓
Farm Brain / Module 3
      ↓
Persistent Farm Problem
```

Module 6 analyzes the disease; Module 3 owns the persistent problem representation.

---

# 10. Disease Results

Disease analysis should be separate from the persistent farm problem.

## `disease_results`

```text
id                  uuid primary key
farmland_id         uuid not null references farmlands(id)
season_id           uuid references seasons(id)
crop_id             uuid references crops(id)
image_storage_key   text
possible_issue      text
confidence          numeric(6,5) check (confidence is null or confidence between 0 and 1)
symptoms            jsonb not null default '[]'
recommended_actions jsonb not null default '[]'
model_details       jsonb not null default '{}'
created_at          timestamptz not null
```

Store image bytes in object storage, not in PostgreSQL. Keep a storage key rather than a permanent public URL; generate access URLs through the backend. `model_details` must not contain credentials or unnecessary personal data.

Relationship:

```text
DiseaseResult
     │
     │ creates/updates
     ▼
Problem
```

This preserves the distinction between:

- disease analysis content — Module 6
- persistent farm problem/state — Module 3

---

# 11. Weather

Raw/processed weather information and farmer-facing alerts should be separate.

## `weather_events`

```text
id              uuid primary key
farmland_id     uuid not null references farmlands(id)
provider        text not null
provider_ref    text
event_type      text not null
description     text
severity        text
start_time      timestamptz not null
end_time        timestamptz
data            jsonb not null default '{}'
created_at      timestamptz not null
```

Example:

```text
event_type: heavy_rain
severity: high
start_time: ...
end_time: ...
```

## `weather_alerts`

```text
id                  uuid primary key
farmland_id         uuid not null references farmlands(id)
season_id           uuid references seasons(id)
weather_event_id    uuid references weather_events(id)
title               text not null
message             text not null
recommended_action  text
severity            text not null
status              text not null
created_at          timestamptz not null
read_at             timestamptz
```

The intended reasoning flow is:

```text
Weather
   ↓
Weather Event
   ↓
Farm Location
   ↓
Current Crop
   ↓
Growth Stage
   ↓
Current / Upcoming Tasks
   ↓
Potential Impact
   ↓
Recommended Action
   ↓
Weather Alert
```

The system should avoid simply notifying the farmer about weather without determining whether it changes what the farmer should do.

Recommended alert statuses: `new`, `read`, `actioned`, `dismissed`. Recommended severity values: `low`, `moderate`, `high`, `critical`.

---

# 12. Farmer Check-ins

Module 3 also tracks farmer check-ins.

## `farm_checkins`

```text
id                  uuid primary key
farmland_id         uuid not null references farmlands(id)
season_id           uuid references seasons(id)
checkin_at          timestamptz not null
growth_stage_id     uuid references growth_stages(id)
notes               text
observations        jsonb not null default '{}'
created_at          timestamptz not null
```

Potential future fields:

```text
crop_condition
water_condition
pest_observed
disease_observed
farmer_notes
```

These can be added when the check-in workflow is finalized.

---

# 13. Chat

Conversation belongs to Module 5.

## `conversations`

```text
id              uuid primary key
farmland_id     uuid not null references farmlands(id)
farmer_id       uuid not null references farmers(id)
title           text
created_at      timestamptz not null
updated_at      timestamptz not null
```

## `chat_messages`

```text
id                  uuid primary key
conversation_id     uuid not null references conversations(id)
sender_type         text not null
message             text
message_type        text not null
attachment_key      text
metadata            jsonb not null default '{}'
created_at          timestamptz not null
```

Possible `sender_type` values:

```text
farmer
assistant
system
```

Possible `message_type` values:

```text
text
image
system
```

Enforce that a conversation's `farmer_id` owns the referenced farmland, preferably by using a composite foreign key or an equivalent database constraint after the final table keys are agreed. The API must also check ownership on every read and write; never trust a client-supplied `farmland_id`.

Require either a non-empty `message` or an `attachment_key`; validate allowed `sender_type` and `message_type` values with database constraints. Keep message order deterministic with `(conversation_id, created_at, id)` when listing history.

A conversation should be associated with a farmland so that the selected farmland automatically provides the relevant context.

For example:

```text
North Field
    ↓
Conversation
    ↓
Farmland-specific context
    ├── Current Crop
    ├── Growth Stage
    ├── Tasks
    ├── Open Problems
    └── Relevant Agricultural Knowledge
```

---

# 14. ChatResponse

The shared contract includes `ChatResponse`, but this does not necessarily need to become a database table.

A response can simply be represented as:

```text
chat_messages
sender_type = assistant
```

`ChatResponse` can instead remain an application/API response contract.

Important principle:

> Not every domain model needs to become a SQL table.

---

# 15. Overall PostgreSQL Schema

The first-pass relational structure is:

```text
farmers
│
├── farmer_profiles
│
└── farmlands
     │
     ├── farmland_crop_preferences
     │
     ├── crop_recommendations
     │      └── crops
     │             └── crop_varieties
     │                    └── agricultural_knowledge
     │
     ├── seasons
     │      │
     │      ├── season_plans
     │      │      │
     │      │      └── growth_stages
     │      │
     │      ├── tasks
     │      │
     │      ├── problems
     │      │
     │      └── farm_checkins
     │
     ├── weather_events
     │      └── weather_alerts
     │
     ├── disease_results
     │
     └── conversations
            └── chat_messages
```

This design has roughly 19 tables, including crop preferences, crop varieties, and reviewed agricultural knowledge. `FarmState` and `ChatResponse` are API/domain representations, not separate tables. The team may defer tables for modules that are not yet implementing data persistence, but should not create duplicate state/history tables.

---

# 16. Important Schema Decision: Foreign Keys

The shared contract examples sometimes represent entities using fields such as:

```text
Season
    farm_id
    crop
```

For the actual relational database, prefer foreign keys:

```text
Season
    farmland_id → farmlands.id
    crop_id     → crops.id
```

Likewise:

```text
DiseaseResult
    farmland_id → farmlands.id
    season_id   → seasons.id
    crop_id     → crops.id
```

This provides referential integrity and prevents inconsistent duplicated strings.

For example, avoid relying on:

```text
crop = "Potato"
```

in multiple unrelated records when they can reference the same `crops.id`.

---

# 17. Central Context Key

The most important architectural decision is to make:

```text
farmland_id
```

the primary context key throughout the application.

The hierarchy should be:

```text
farmland_id
     ↓
season_id
     ↓
Module 3 FarmState API view
     ↓
tasks / problems / weather / disease / chat
```

Then:

- `farmland_id` = primary farming context
- `season_id` = current crop-cycle context
- `growth_stage_id` = current operational stage

This matches the product UX:

```text
Farmer
   ↓
Farmland
   ↓
Farming Activity
   ↓
Conversation
```

and the backend architecture:

```text
M1 → M2 → M3 → M4
             ↘ M5
             ↘ M6
```

with M3 acting as the central farm-state hub.

---

# 18. Recommended Next Step

Do not write the final SQL migration yet.

First finalize these three things:

1. **Exact table list**
2. **Relationships and foreign keys**
3. **Which fields should be JSON vs normalized columns**

After those are agreed, convert the design into PostgreSQL migrations with:

- UUID primary keys
- Foreign keys and explicit delete behavior
- `timestamptz` timestamps in UTC
- `CHECK`, `UNIQUE`, and not-null constraints
- Indexes on foreign keys and common filtering/sorting paths
- PostgreSQL `jsonb` only for the flexible payloads identified above
- Alembic migrations and reviewed seed/demo data
- Backend authorization checks that scope every farmland query to its owner

## 19. PostgreSQL implementation conventions

- Give UUID primary keys a server-side `gen_random_uuid()` default. Use `now()` defaults for creation timestamps where appropriate; keep `updated_at` changes consistent through application code or a documented trigger.
- Prefer `ON DELETE RESTRICT` for farmers, farmlands, seasons, and records that form farm history. Use `ON DELETE CASCADE` only for dependent records whose lifecycle is strictly owned by a parent (for example chat messages when a conversation is intentionally deleted). Define deletion/retention behavior before enabling user-facing deletion.
- PostgreSQL does not automatically index referencing foreign-key columns. Add indexes for foreign keys and common access patterns, including `(farmer_id, created_at)` on conversations, `(conversation_id, created_at)` on chat messages, `(season_id, status, due_at)` on tasks, and `(farmland_id, status, created_at)` on alerts/problems.
- Prefer `CHECK` constraints for small, evolving status vocabularies rather than PostgreSQL enum types, so adding a status does not require enum-specific migration handling. The allowed values must still be explicit and validated in both API schemas and the database.
- Where a row stores both `farmland_id` and `season_id`, enforce that the season belongs to that same farmland (for example with a composite foreign key using a unique `(id, farmland_id)` key on `seasons`). Apply the same principle to a conversation's farmer and farmland ownership.
- Use UTC-aware timestamps for event times; use `date` for calendar dates such as planting/harvest dates.
- Enforce ownership in backend authorization and query scoping. Standalone PostgreSQL does not provide Supabase RLS as an implicit protection layer.

The database must remain consistent with the shared domain contract and the six-module ownership model.
