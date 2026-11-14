# FieldShift BD API

The FieldShift BD backend is a FastAPI service. This page describes every route the app exposes, how to authenticate, and the request and response shapes you will use most. The live, always-current reference is the interactive OpenAPI page the server generates.

| Item | Value |
| --- | --- |
| Local base URL | `http://localhost:8000` |
| Interactive docs (Swagger UI) | `http://localhost:8000/docs` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |
| Health check | `GET /health` → `{"status":"ok","service":"FieldShift API","version":"1.0.0","database":"connected"}` |
| Content type | `application/json` (the disease scan upload is `multipart/form-data`) |
| IDs | UUID strings |
| Dates | ISO 8601 (`2026-11-13`, `2026-11-13T06:00:00Z`) |

## Authentication

Accounts are identified by a Bangladeshi mobile number in E.164 form (`+8801XXXXXXXXX`) and a password. Register or log in to get a token, then send it on every protected route:

```http
Authorization: Bearer <access_token>
```

- Tokens are JWTs signed with HS256 using `SECRET_KEY` and expire after 90 days.
- The API refuses to start if `SECRET_KEY` is missing or shorter than 32 characters.
- Every farm-scoped route checks that the farmland belongs to the signed-in farmer. Another farmer's farmland returns `404`.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Rahim Uddin","phone_e164":"+8801712345678","password":"a-long-password"}'
# → 201 {"access_token":"eyJ...","token_type":"bearer","farmer_id":"…"}
```

## Errors

Errors use FastAPI's shape:

| Status | Meaning |
| --- | --- |
| `401` | Missing, expired or invalid token |
| `404` | The resource does not exist or is not yours |
| `409` | The request conflicts with current state (for example, closing a season that is not active, or scanning a leaf when the farm has no active season) |
| `422` | Validation error. `detail` lists each field: `{"detail":[{"loc":["body","latitude"],"msg":"Input should be less than or equal to 90",…}]}` |
| `503` | A challenge feature switch is off. The body carries `detail.details.feature` naming the switch |

## Feature switches

Some challenge features are off unless their environment variable is `true` in `backend/.env`:

| Variable | Default in `.env.example` | Turns on |
| --- | --- | --- |
| `CHALLENGE_ROTATION_ENABLED` | `true` | Rotation comparison routes |
| `CHALLENGE_CLIMATE_ENABLED` | `false` | Climate evidence features |
| `CHALLENGE_ADVISORY_ENABLED` | `false` | Advisory features |
| `CHALLENGE_ADAPTIVE_DECISIONS_ENABLED` | `false` | Adaptive decision features |
| `CHALLENGE_ACTION_CONFIRMATION_ENABLED` | `false` | Chat-proposed actions and their confirmation |
| `CHALLENGE_DISEASE_PROBLEM_SYNC_ENABLED` | `false` | Turning a confirmed disease scan into a farm problem |
| `CHALLENGE_VOICE_ENABLED` | `false` | Voice features |
| `OFFLINE_MODE` | `false` | Blocks all outbound calls (weather providers, Gemini) |

---

## 1. System

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/` | – | Service banner |
| GET | `/health` | – | Service and database status |
| GET | `/challenge/foundation/availability` | – | Which challenge features are on |
| POST | `/challenge/consents` | ✓ | Record a consent decision (`purpose`: `personalized_advice`, `offline_storage`, `speech_audio_transcription`, `disease_problem_sync`, `research`; `decision`: `granted`, `denied`, `withdrawn`) |

## 2. Accounts, profile and farmlands (Module 1)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | – | Create an account. Body: `name`, `phone_e164`, `password`. Returns `201` + token |
| POST | `/auth/login` | – | Log in. Body: `phone_e164`, `password` |
| GET | `/profile` | ✓ | The farmer's account, profile and farmlands |
| PATCH | `/profile/farmer-profile` | ✓ | Update `farming_experience_years`, `equipment`, `livestock`, `preferred_language` (`bn` or `en`) |
| GET | `/farmlands` | ✓ | List my farmlands |
| POST | `/farmlands` | ✓ | Create a farmland (fields below) |
| GET | `/farmlands/{farmland_id}` | ✓ | One farmland |
| PATCH | `/farmlands/{farmland_id}` | ✓ | Update any farmland field |
| GET | `/farmlands/{farmland_id}/onboarding-status` | ✓ | Which profile fields are filled and what to ask next |

**`FarmlandCreate`** (only `name` and `land_area_sqm` are required):

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | |
| `land_area_sqm` | number | Greater than 0 |
| `land_area_display_unit` | `square_metre` · `decimal` · `acre` · `hectare` | How the app shows the area |
| `division`, `district`, `upazila`, `village_or_locality` | string | Names from `/reference/locations` |
| `latitude`, `longitude` | number | −90…90, −180…180 |
| `soil_type` | string | A label or alias from `/reference/profile-vocabulary` |
| `land_type` | `high` · `medium_high` · `medium_low` · `low` · `very_low` | |
| `irrigation_available` | boolean | |
| `water_source`, `farming_method` | string | |
| `budget_amount`, `budget_currency` | number, string | Currency defaults to BDT |
| `previous_crop`, `previous_yield_amount`, `previous_yield_unit` | string, number, string | `previous_crop` also forms the rotation baseline when no seasons are recorded |
| `equipment` | string[] | |

```bash
curl -X POST http://localhost:8000/farmlands -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{
  "name": "Rahim'\''s field", "land_area_sqm": 4047, "land_area_display_unit": "acre",
  "division": "Rajshahi", "district": "Rajshahi", "upazila": "Paba",
  "latitude": 24.42, "longitude": 88.62, "soil_type": "Clay loam", "land_type": "high",
  "irrigation_available": true, "water_source": "Shallow tube well", "previous_crop": "Boro rice"}'
```

## 3. Crop catalog and reference data (Module 1)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/crops` | – | Crop catalog with Bangla names, aliases and varieties |
| GET | `/crops/{crop_id}` | – | One crop |
| GET | `/reference/locations` | – | Divisions → districts → upazilas (English and Bangla) |
| GET | `/reference/profile-vocabulary` | – | Canonical soil textures, land types and other profile terms |

## 4. Crop Advisor and seasons (Module 2)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/advisor/farmlands/{farmland_id}/recommendations` | ✓ | Match the saved farm profile against approved BARC/BRRI knowledge. Returns `status` (`available`, `no_approved_knowledge`, …), `recommendations`, per-crop `crop_assessments`, missing profile fields and area-level context |
| GET | `/advisor/farmlands/{farmland_id}/recommendations` | ✓ | Saved recommendations |
| POST | `/advisor/recommendations` | ✓ | Same check for a profile sent in the body (`FarmProfileInput`) |
| POST | `/advisor/recommendations/{recommendation_id}/dismiss` | ✓ | Dismiss a recommendation |
| GET | `/advisor/calendar-references` | – | Published variety calendars. Query: `crop`, `season` |
| POST | `/advisor/seasons` | ✓ | Choose a crop and create a planned season. Body: `farmland_id`, `crop_id`, optional `crop_variety_id`, `variety_name`, `planting_date`, `expected_harvest_date`, `recommendation_id` |
| GET | `/advisor/farmlands/{farmland_id}/seasons` | ✓ | Season history |
| POST | `/advisor/seasons/{season_id}/plan` | ✓ | Generate the season plan (`season_id`, `title`). Returns `409` when no approved plan knowledge exists for the crop |
| GET | `/advisor/seasons/{season_id}/plan` | ✓ | The plan and its growth stages |
| POST | `/advisor/seasons/{season_id}/activate` | ✓ | Make a planned season active (needs a plan) |
| POST | `/advisor/seasons/{season_id}/close` | ✓ | Close an active season with `actual_yield`, `yield_unit`, `actual_harvest_date`, `outcome_notes` |
| GET | `/advisor/seasons/{season_id}/harvest-guidance` | ✓ | Published harvest window and checks for the season's crop |
| GET | `/advisor/farmlands/{farmland_id}/planting-window` | ✓ | NASA POWER rainfall-onset and GDD evidence for a season. Query: `season_id` (required) |
| POST | `/advisor/farmlands/{farmland_id}/rotation-comparisons` | ✓ | v1 rotation comparison (kept for compatibility) |

## 5. Regional rotation comparison, v2

The main decision-support route. It compares the farmer's current crops with three BRRI-published rotations for the farm's district and orders them by the farmer's priority. It never creates a season or task, and it never selects a plan (`selection_allowed` is always `false`).

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/advisor/v2/regions` | – | Supported pilot regions and the state of each NASA product (`hit`, `pilot_unreviewed`, `not_acquired`) |
| POST | `/advisor/v2/farmlands/{farmland_id}/rotation-comparisons` | ✓ | Compare rotations |

**Request (`RotationCompareRequest`)**

| Field | Type | Notes |
| --- | --- | --- |
| `planning_year` | integer | 2001–2040 |
| `priorities` | array, 1–5 unique | Ordered: `water`, `rainfall`, `diversity`, `calendar`, `income`. Default `["water","calendar"]` |

How each priority orders the options (the first priority decides; later ones break ties):

| Priority | Metric | Better is |
| --- | --- | --- |
| `water` | `irrigated_dry_season_steps`: dry-season crops that usually need irrigation | Lower |
| `rainfall` | `dry_spell_exposure_days`: longest typical dry spell (≤1 mm/day) during the crops, from NASA POWER 2001–2025 | Lower |
| `diversity` | `crop_family_count`: distinct plant families | Higher |
| `calendar` | `calendar_coverage_share`: share of crops with published or recorded dates | Higher |
| `income` | `market_income_evidence`: no data yet | Never ranks |

**Response (`RotationComparisonV2`), main fields**

| Field | Meaning |
| --- | --- |
| `status` | `partial` for supported districts; `unsupported_region` elsewhere (Rajshahi `5081` and Chattogram `2015` are supported) |
| `baseline_completeness` | `complete`, `incomplete` or `not_recorded` |
| `options[]` | The baseline (`role: baseline`) and three alternatives. Each has `steps`, `eligibility` (`unknown` or `ineligible` when land, soil or irrigation is outside the published scope), `metrics[]` (value, unit, status, method, years used), `why_en/bn`, `benefits_en/bn`, `risks_en/bn`, `gaps_en/bn`, `evidence_ids` |
| `exploration_status` | `ordered`, `tied` or `insufficient_evidence` |
| `exploration_order[]` | `{option_id, position, basis:[{priority, metric_id, value}]}` |
| `unranked_options[]` | Options not ordered, with the reason in English and Bangla |
| `evidence[]` | Sources with coverage dates, spatial support and cache state |
| `limitations_en/bn` | Plain statements of what the comparison does not establish |

```bash
curl -X POST http://localhost:8000/advisor/v2/farmlands/$FARM/rotation-comparisons \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"planning_year": 2027, "priorities": ["water", "diversity"]}'
# exploration_order: BRRI-RFS-02 (0 irrigated dry-season crops) → BRRI-RFS-04 → BRRI-RFS-01 → baseline
```

## 6. Public district climate advisory

No account needed.

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/advisory/districts` | – | All 64 districts and whether a NASA POWER cache is present |
| GET | `/advisory` | – | Rainfall history and planting-window evidence. Query: `district` (required), `crop`, `season` |

## 7. Weather alerts (Module 4)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/weather/assessment/{farmland_id}` | ✓ | Alerts that change what the farmer should do (heavy rain, heat, wind, rain probability), from the Open-Meteo 7-day forecast and the last 30 days of NASA POWER. Also lists suppressed events and each provider's state. Needs farm coordinates (`422` otherwise) |
| GET | `/weather/raw/{farmland_id}` | ✓ | The raw provider payloads |
| GET | `/weather/assessment/{farmland_id}/demo` | – | Offline demo with mock weather. Query: `rain_mm`, `with_irrigation_task` |

Alert thresholds are demo values pending agronomist review (`app/services/weather_thresholds.py`).

## 8. Farm state, tasks, problems and check-ins (Module 3)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/farmlands/{farmland_id}/state` | ✓ | Active season, growth stage, tasks and open problems |
| PATCH | `/farmlands/{farmland_id}/state/growth-stage` | ✓ | Set `growth_stage_id` |
| GET | `/farmlands/{farmland_id}/tasks` | ✓ | Query: `season_id`, `status`, `schedule_state`, `limit`, `offset` |
| POST | `/farmlands/{farmland_id}/tasks` | ✓ | `title` (required), `description`, `due_at`, `priority` (`low`…`urgent`), `source` (`farmer`, `season_plan`, `weather`, `disease`, `system`) |
| GET | `/farmlands/{farmland_id}/tasks/{task_id}` | ✓ | One task |
| PATCH | `/farmlands/{farmland_id}/tasks/{task_id}` | ✓ | `status`: `pending`, `completed`, `skipped`, `cancelled` |
| POST | `/farmlands/{farmland_id}/seasons/{season_id}/tasks/from-plan` | ✓ | Import the season plan's tasks |
| GET | `/farmlands/{farmland_id}/problems` | ✓ | Query: `status` |
| POST | `/farmlands/{farmland_id}/problems` | ✓ | `category`, `description` (required), `severity`, `source` |
| GET / PATCH | `/farmlands/{farmland_id}/problems/{problem_id}` | ✓ | Read or update a problem's status |
| GET | `/farmlands/{farmland_id}/check-ins` | ✓ | Query: `limit`, `offset` |
| POST | `/farmlands/{farmland_id}/check-ins` | ✓ | `notes`, `observations`, `growth_stage_id`, `checkin_at` |

## 9. Disease screening (Module 6)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/farmlands/{farmland_id}/disease-results` | ✓ | Upload a leaf photo as form field `image`. Needs an active season (`409` otherwise) |
| GET | `/farmlands/{farmland_id}/disease-results` | ✓ | Scan history. Query: `limit`, `offset` |
| POST | `/farmlands/{farmland_id}/disease-results/{disease_result_id}/sync-problem` | ✓ | Retry turning a confirmed result into a farm problem |

```bash
curl -X POST http://localhost:8000/farmlands/$FARM/disease-results \
  -H "Authorization: Bearer $TOKEN" -F image=@leaf.jpg
```

The response has `outcome` (`healthy`, `uncertain`, `possible_disease`), `confidence_level`, `verification` (optional Gemini check), `problem_sync`, a `message` and a `disclaimer`. Results below `DISEASE_CONFIDENCE_THRESHOLD` (default 0.70) come back as `uncertain`.

## 10. Chat and actions (Module 5)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/farmlands/{farmland_id}/chat` | ✓ | Quick chat. Body: `message` (Bangla or English), optional `client_request_id` |
| POST | `/farmlands/{farmland_id}/conversations` | ✓ | Start a conversation (`title` optional) |
| GET | `/farmlands/{farmland_id}/conversations` | ✓ | List conversations |
| GET | `/farmlands/{farmland_id}/conversations/{conversation_id}` | ✓ | Messages in a conversation |
| POST | `/farmlands/{farmland_id}/conversations/{conversation_id}/messages` | ✓ | Send a message |
| GET | `/farmlands/{farmland_id}/actions/pending` | ✓ | Actions the assistant proposed |
| POST | `/farmlands/{farmland_id}/actions/proposals` | ✓ | Create a proposal |
| POST | `/farmlands/{farmland_id}/actions/{action_id}/confirm` | ✓ | Confirm or reject: `expected_version`, `idempotency_key`, `decision` (`confirm` or `reject`) |

A chat reply includes the classified `intent` (`crop_advice`, `weather_inquiry`, `disease_inquiry`, `task_inquiry`, `resource_inquiry`, `onboarding_help`, `general_qa`), a `context_summary` of the farm data used, and `suggested_actions`. Answers use Google Gemini when `GEMINI_API_KEY` is set. The app reads replies aloud with the device's text-to-speech and takes Bangla voice input (`bn-BD`) where the phone or browser supports it.

## Typical flow

1. `POST /auth/register` → token
2. `POST /farmlands` with district, soil, land type, irrigation and previous crop
3. `POST /advisor/farmlands/{id}/recommendations` → crop matches
4. `POST /advisor/v2/farmlands/{id}/rotation-comparisons` with the farmer's priority
5. `POST /advisor/seasons`, then `/plan` and `/activate`
6. `GET /weather/assessment/{id}` and `GET /farmlands/{id}/tasks` during the season
7. `POST /farmlands/{id}/disease-results` when a leaf looks sick
8. `POST /advisor/seasons/{id}/close` after harvest
