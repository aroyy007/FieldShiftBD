# FieldShift Database Schema Proposal

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
        ├── Crop Recommendations
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
id
name
phone
password_hash
created_at
updated_at
```

## `farmlands`

Represents an individual piece or farming unit owned or managed by the farmer.

```text
id
farmer_id
name
location
land_area
land_unit
soil_type
irrigation_available
water_source
farming_method
budget
created_at
updated_at
```

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
- budget
- crop preferences
- optional livestock information

These should not necessarily all live in one huge table.

## `farmer_profiles`

Farmer-level information:

```text
id
farmer_id
farming_experience
equipment
livestock
created_at
updated_at
```

## `farmlands`

Farmland-level information:

```text
id
farmer_id
name
location
land_area
land_unit
soil_type
irrigation_available
water_source
farming_method
budget
crop_preferences
created_at
updated_at
```

## `farm_history`

Information that changes from season to season:

```text
id
farmland_id
season_id
previous_crop
previous_yield
yield_unit
notes
created_at
```

This prevents the farmland profile from becoming a single oversized table.

---

# 4. Crops

The database should distinguish the crop itself from a crop being grown on a particular farmland.

## `crops`

Agricultural master/knowledge data:

```text
id
name
scientific_name
description
created_at
```

Examples:

```text
Potato
Rice
Tomato
Chili
Wheat
```

A season then references a crop.

## `seasons`

Represents one crop cycle on a farmland:

```text
id
farmland_id
crop_id
variety
planting_date
expected_harvest_date
actual_harvest_date
status
created_at
updated_at
```

This is preferable to repeatedly storing strings such as:

```text
crop = "Potato"
```

throughout the database.

---

# 5. Crop Recommendations

Module 2 needs to recommend suitable crops before the farmer selects one.

## `crop_recommendations`

```text
id
farmland_id
crop_id
score
status
created_at
```

Because recommendations must be explainable, the recommendation should also preserve the reasoning.

Possible structured fields:

```text
soil_reason
timing_reason
irrigation_reason
climate_reason
land_area_reason
budget_reason
concerns
```

Alternatively, the reasoning can later be represented as structured JSON:

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

---

# 6. Season Plan

The season plan is a major part of the system because Module 3 turns it into operational tasks.

## `season_plans`

```text
id
season_id
title
description
created_at
updated_at
```

## `growth_stages`

```text
id
season_plan_id
name
description
sequence
start_day
end_day
created_at
```

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
id
season_id
growth_stage_id
title
description
due_date
status
priority
source
completed_at
created_at
updated_at
```

Possible statuses:

```text
pending
due
completed
skipped
overdue
```

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

## `farm_states`

```text
id
farmland_id
season_id
current_growth_stage_id
status
last_checkin_at
updated_at
```

The overall state becomes:

```text
FarmState
 ├── current_growth_stage → growth_stages
 ├── tasks                → tasks
 ├── problems             → problems
 └── check-ins            → farm_checkins
```

This prevents duplicate sources of truth.

---

# 9. Problems

Problems are owned by Module 3 because they are persistent farm-state information.

## `problems`

```text
id
farmland_id
season_id
source
category
description
severity
status
created_at
resolved_at
```

Example:

```text
source: disease_detection
category: leaf_disease
description: Possible late blight
severity: moderate
status: open
```

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
id
farmland_id
season_id
crop_id
image_url
possible_issue
confidence
symptoms
recommended_actions
created_at
```

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
id
farmland_id
event_type
description
severity
start_time
end_time
data
created_at
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
id
farmland_id
season_id
weather_event_id
title
message
recommended_action
severity
status
created_at
read_at
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

---

# 12. Farmer Check-ins

Module 3 also tracks farmer check-ins.

## `farm_checkins`

```text
id
farmland_id
season_id
checkin_date
growth_stage_id
notes
created_at
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
id
farmland_id
farmer_id
title
created_at
updated_at
```

## `chat_messages`

```text
id
conversation_id
sender_type
message
message_type
created_at
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

The same principle may apply to `FarmState`, depending on the final implementation.

---

# 15. Overall Supabase/PostgreSQL Schema

The first-pass relational structure is:

```text
farmers
│
├── farmer_profiles
│
└── farmlands
     │
     ├── farm_history
     │
     ├── crop_recommendations
     │      └── crops
     │
     ├── seasons
     │      │
     │      ├── season_plans
     │      │      │
     │      │      └── growth_stages
     │      │
     │      ├── tasks
     │      │
     │      ├── farm_states
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

This results in roughly 15–17 tables depending on final decisions around profile/history/state representation.

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
farm_state
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

After those are agreed, convert the design into a proper Supabase/PostgreSQL schema with:

- UUID primary keys
- Foreign keys
- Appropriate enums
- `created_at` / `updated_at`
- Indexes
- Constraints
- Row Level Security (RLS)
- Supabase migrations
- Seed/demo data

The database should remain consistent with the shared domain contract and the six-module ownership model.
