# Module 2: Crop Advisor & Season Lifecycle

## M2 INPUTS

- M1 `FarmProfile` data using the M2 `FarmProfileInput` schema.
- Crop and variety catalogue records, farmland records, and approved
  `AgriculturalKnowledge` records from the existing shared persistence layer.
- Farmer crop selection, season dates/budget, season-plan request metadata, and
  season outcome information.

Until M1 is connected, callers can pass a contract-shaped mock profile directly
to `POST /advisor/recommendations`. The HTTP path still requires its
`farmland_id` to refer to an existing farmland record; service tests use a mock
session for full M1-independent behavior.

## M2 OUTPUTS

- `CropRecommendationSet`: explicit result status/message and zero or more
  recommendations with factor-level explanations and knowledge provenance.
- Selected crop represented as a planned `Season`.
- `SeasonPlanResponse`: `SeasonPlan`, ordered `GrowthStageDefinition` values,
  `InitialTaskDefinition` values for M3, and source references.
- Reviewed harvest guidance with source references and season outcome/history
  responses.

## M2 OWNED DATA

Crop recommendations, season selection/lifecycle, season plans, growth-stage
definitions, harvest guidance response, and season outcome history.

## M2 READ-ONLY DATA

Farm/farmer profile, crop and variety catalogue, crop preferences, and reviewed
agricultural knowledge. M2 does not own the farmland/profile or crop catalogue.

## M2 STATE CHANGES

M2 persists recommendations, creates planned seasons, creates/supersedes season
plans and growth-stage definitions, activates season lifecycle status, and
records season-close outcome fields. M2 returns initial task definitions but
does not create, schedule, complete, or otherwise mutate operational tasks.
M2 does not set or expose the current operational growth stage.
**Module 3 owns operational task state and current growth-stage state.**

## M2 DEPENDENCIES

- M1 FarmProfile contract (currently accepted directly as an API payload/mock).
- Existing shared crop, farmland, season, plan, and knowledge persistence
  models.
- No dependency on M3 implementation, NASA, ML, LLM, or external agricultural
  APIs.

## M2 MOCK INPUTS

Use `FarmProfileInput` directly as the M1 mock. For service tests, the fake
session supplies synthetic farm and catalogue records. Any knowledge used in
tests is labelled `SYNTHETIC TEST FIXTURE — NOT AGRICULTURAL ADVICE`; no mock
agronomic records are seeded into production data.

The plan's top-level `previous_yield` is supported. For compatibility with the
older M2 nested shape, `previous_crop.yield_amount` is still accepted and is
copied to `previous_yield` when the top-level value is omitted; conflicting
values are rejected. The plan's `farming_experience` and `budget` names are
accepted and serialized, while M2 internals retain their existing
`farming_experience_years` and `budget_amount` attributes.

Example profile payload shape (identifiers are illustrative only):

```json
{
  "farmer_id": "11111111-1111-4111-8111-111111111111",
  "farmland_id": "22222222-2222-4222-8222-222222222222",
  "location": { "country_code": "BD", "district": "Example district" },
  "land_area": 2,
  "land_unit": "acre",
  "soil_type": "provided by M1",
  "irrigation_available": true,
  "equipment": [],
  "crop_preferences": [],
  "livestock": []
}
```

## M2 INTEGRATION TESTS

M2 contract tests validate M1 → M2 profile payloads and M2 → M3
`SeasonPlan`/growth-stage/task-definition shapes. Service tests use a mock
session and synthetic-only knowledge fixtures. The integration handoff is:

```text
M1 FarmProfile → M2 recommendation/selection → SeasonPlan + GrowthStages
                                             → InitialTaskDefinitions → M3 Tasks
```

M3 owns the operational task state and must not treat M2 task definitions as
already scheduled or completed tasks.

## API

All routes are mounted under `/advisor`:

| Method and path | Purpose |
|---|---|
| `POST /recommendations` | Generate explainable recommendations from a farm profile and approved knowledge; returns an explicit empty-result reason |
| `GET /farmlands/{farmland_id}/recommendations` | Read saved recommendations for a farmland |
| `POST /recommendations/{recommendation_id}/dismiss` | Dismiss a proposed recommendation |
| `POST /seasons` | Select a crop and create a planned season |
| `GET /farmlands/{farmland_id}/seasons` | Read season history for advisory context |
| `POST /seasons/{season_id}/plan` | Generate a plan from approved season-plan knowledge |
| `GET /seasons/{season_id}/plan` | Read the latest active, draft, or completed plan |
| `POST /seasons/{season_id}/activate` | Activate the season lifecycle after a plan exists |
| `GET /seasons/{season_id}/harvest-guidance` | Return reviewed harvest guidance |
| `POST /seasons/{season_id}/close` | Record harvest outcome and complete the season |

Every route requires the verified farmer identity from
`request.state.current_farmer_id` and scopes farmland, recommendation, and
season access to that owner. This uses the shared Module 1 authentication
dependency already used by Module 3; it does not add a second auth or profile
store. Until Module 1 installs the verified identity, these routes return
`401 Authentication required`. The mobile client can obtain a bearer token
from the shared auth integration through `setM2AccessTokenProvider`; never put
a farmer session token in an `EXPO_PUBLIC_*` build variable.

## Agricultural knowledge format

### Agricultural Knowledge Layer

The M2 provider in `app/services/m2_knowledge.py` retrieves structured evidence
from the existing shared `AgriculturalKnowledge` records; it does not rank crops
or make recommendation decisions. The M2 suitability logic consumes the
returned evidence to explain matching positive factors, constraints, and risks.
The provider supports the evidence already consumed by M2: crop suitability
factors, soil and irrigation factors, season-plan/crop-calendar growth stages,
and harvest guidance. The existing record's category and content carry the
specific agricultural factor and its evidence/value; locality and applicability
are represented by its region code and structured content context.

Each returned item preserves the knowledge ID, crop and variety, factor/category,
conditions, evidence/value, region/context, source name/type/reference, review
status and reviewer, and effective dates. Since the shared model has no dedicated
`source_type` field, M2 reads it from the record's structured `content` metadata.
Records must have a non-empty `source_type` there as well as a source name.
Only `approved` records effective on the query date are returned. Crop and
variety-specific rows must match the requested crop and variety; region-specific
rows must match a supplied locality value, and structured applicability
conditions must match the available profile context. Missing context fails
closed for conditional evidence. When no valid record applies, the provider
returns `missing_approved_effective_evidence` with an empty item list. M2 does
not fall back to draft/unreviewed evidence or invent a recommendation.

Add authoritative knowledge later by entering the source's structured evidence
in the existing knowledge record, including its crop/variety scope, category,
region/context, `source_type`, source name/reference, review fields, and valid
effective dates. A record should be approved only after its agronomic claims,
local applicability, provenance, and effective period have been reviewed. No
new model or migration is needed for this M2 layer.

> M2 uses reviewed/effective agricultural evidence for real recommendations. Synthetic fixtures are test-only and are never production knowledge.

Test fixtures use clearly labelled synthetic records and verify filtering and
provenance behavior only; they are never advice or production knowledge. The
provider does not call external sources, and this implementation adds no
agricultural facts.

Only rows in `agricultural_knowledge` marked `approved` and currently within
their effective dates can inform farmer-facing results. A recommendation also
requires at least one explicit factor explanation in the approved `content`.
The service does not generate generic recommendations, infer missing facts, or
turn the optional score into the primary explanation.

For recommendations, content may provide `factors` organized by stable keys
such as `soil`, `planting_timing`, `irrigation`, `climate`, `land_area`, and
`budget`. Each value may contain `kind` (`positive_factors`,
`limiting_factors`, or `risks_or_concerns`) and an `explanation`. A positive
factor must include a `when` condition that matches the available profile, or
the knowledge row must have a matching `applicability` object. Supported
conditions currently cover soil type, irrigation availability, water source,
farming method, and country/division/district/upazila location values. Missing
profile values and unsupported conditions fail closed. This prevents general
crop facts from being presented as a claim that a crop suits a particular farm.

Content may provide `suitable_because`, `limiting_factors`, or `concerns` lists
of explanation strings or `{ "factor": "...", "explanation": "..." }`
objects; positive entries still need matching conditions. Source references
are included in each factor returned to the caller. Region-specific knowledge
is used only when its `region_code` exactly matches a supplied location value;
agree on a canonical region-code format before approving/entering such data.

For plan generation, approved `season_plan` or `crop_calendar` content must
include a non-empty `growth_stages` array matching `GrowthStageDefinition`.
Optional `initial_tasks` items match `InitialTaskDefinition`; these remain
recommendations for M3 and are not persisted as M3 task state.

For harvest guidance, approved `harvest_guidance` or `harvest` content must
match the `HarvestGuidance` schema. Do not mark a record approved until its
agronomic statements, locality, source, and effective period have been reviewed.

## Ownership and persistence

M2 uses the existing `CropRecommendation`, `Season`, `SeasonPlan`, and
`GrowthStage` persistence models. Season outcomes are stored on `Season`.
`Task` remains M3-owned. No shared model, migration, or database schema was
changed to implement M2.

### Authoritative Knowledge Sources

#### Source hierarchy and review

Prefer Bangladesh government agricultural bodies and national agricultural
research institutes (BARC, DAE, BRRI, BARI, and other relevant NARS bodies),
then recognized universities, FAO and other appropriate international
organizations, and peer-reviewed research. Organization identity alone does
not make a claim production-ready: retain the exact source and reference and
review each claim, crop/variety, context, and effective period. Knowledge stays
unapproved until an authorized reviewer evaluates it. The shared model records
`review_status`, `reviewed_by`, and `reviewed_at`, but the repository does not
yet define an authorization/workflow for assigning reviewers.

#### Source research and initial coverage

The M2 source register at `backend/app/data/m2_knowledge_sources/` records the
pages reviewed, their traceable URLs, supportable information, and limitations.
Potato is the initial target because the plan's Golden Farm scenario names
potato. Wheat and maize appear in frontend demo examples, but those examples do
not establish Bangladesh agronomic context and are only future candidates.
There are no repository crop or variety seed records, so source candidates are
not bound to database IDs. No production knowledge rows have been added or
approved. At present no planting dates, growth stages, harvest advice, soil or
water requirements, regional crop recommendation, or similar crop claim has
been verified for ingestion.

BARC's Land Suitability Assessment and Crop Zoning pages describe national
methodology and expose maps/classes for crops including potato. The methodology
uses agro-edaphic and agro-climatic factors; maps can support locality-specific
suitability only when the appropriate underlying locality data, date/version,
and crop identity are verified. The accessible sources reviewed here do not
provide a dated, verified Comilla-local potato dataset ready for M2 ingestion.
Do not generalize national aggregate map areas into a farm-level recommendation.

#### Provenance, context, and dates

Use the existing `AgriculturalKnowledge` model fields for crop, variety,
category, `content`, region, source name/reference, review state, and effective
dates. Store `source_type`, publication date, and any structured evidence
metadata inside `content`, since the shared model has no dedicated columns for
them. Keep locality and season context explicit; do not translate districts,
upazilas, or agro-ecological zones into each other without a source-backed
mapping. If a source does not state a publication date or effective interval,
record that as unknown; do not invent dates. Effective-date filtering remains
inclusive on the query date, and M2 uses only `approved` rows with valid
effective dates.

#### Ingestion procedure and limits

For each candidate claim, record its exact source, title, URL, publication date
if stated, source type, crop and variety scope, fact and M2 category, locality or
other context, effective period, and limitations. Normalize only the minimum
facts M2 needs; keep a claim in candidate/draft form until an authorized review
has confirmed it. M2 does not scrape or download source material at runtime. If
no approved/effective evidence matches the requested crop and farm context, M2
returns missing evidence and does not make a recommendation. Current source
coverage does not yet support production recommendations or season plans; NASA
or environmental-data evaluation should wait until sourced, reviewed records
exist.
