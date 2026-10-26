# Backend

## Module 3 farm-state API

Module 3 is the shared operational state owner. `FarmState` is assembled from
the season, growth-stage, task, problem, and check-in rows; it is not a separate
JSON snapshot.

| Endpoint | Purpose |
| --- | --- |
| `GET /farmlands/{farmland_id}/state` | Current season, growth stage, season progress, tasks, open problems, and latest check-in |
| `PATCH /farmlands/{farmland_id}/state/growth-stage` | Set or clear the current stage for the active season |
| `GET /farmlands/{farmland_id}/tasks` | List tasks, optionally filtered by `status`, derived `schedule_state`, or `season_id` |
| `POST /farmlands/{farmland_id}/tasks` | Create a farmer, weather, disease, or system task |
| `PATCH /farmlands/{farmland_id}/tasks/{task_id}` | Mark a task pending, completed, skipped, or cancelled |
| `POST /farmlands/{farmland_id}/seasons/{season_id}/tasks/from-plan` | Materialize Module 2 plan actions as idempotent Module 3 tasks |
| `GET /farmlands/{farmland_id}/problems` | List current and historical farm problems |
| `POST /farmlands/{farmland_id}/problems` | Record a farmer, weather, or disease problem |
| `PATCH /farmlands/{farmland_id}/problems/{problem_id}` | Change problem status |
| `GET /farmlands/{farmland_id}/check-ins` | List recent farmer check-ins |
| `POST /farmlands/{farmland_id}/check-ins` | Record a field observation and notes |

Task status values are `pending`, `completed`, `skipped`, and `cancelled`.
The API derives `schedule_state` (`upcoming`, `due`, `overdue`, or
`unscheduled`) for pending tasks from their UTC deadline and the current time;
it does not persist a value that can go stale. Date-only plan actions are due
through the end of their Bangladesh calendar day. No check-in notifications are
sent automatically.

Every Module 3 endpoint requires a verified farmer identity in
`request.state.current_farmer_id`; farmland lookups are scoped to that owner.
The authentication provider must populate this state after validating the
request token. Until Module 1 supplies that provider, unauthenticated calls
receive `401` and a farmer cannot access another farmer's farmland.

### Module 2 task import

The season-plan import accepts stable references so retries do not create
duplicate tasks. Module 2 supplies its generated action definitions to this
endpoint; each action is validated against the active season plan, attached to
a growth stage, and scheduled through the end of its planting-date offset in
Bangladesh time.

### Frontend integration boundary

The existing Expo `AppProvider` still uses in-memory demo data and does not
call these endpoints. The backend API is the durable Module 3 contract; wiring
the screens to it depends on Module 1 providing authenticated UUID farmlands
and an authentication layer that installs `request.state.current_farmer_id`.
Until then, frontend task/check-in/problem edits are demo-only and reset when
the app reloads.

```json
{
  "tasks": [
    {
      "reference": "top-dressing-1",
      "growth_stage_id": "00000000-0000-0000-0000-000000000001",
      "title": "Apply first top dressing",
      "description": "Apply the planned nitrogen dose.",
      "days_after_planting": 18,
      "priority": "high"
    }
  ]
}
```

The season needs a planting date and active plan, and every stage ID must belong
to that plan. Existing tasks with the same stable reference are returned as-is.

### Module 4 and Module 6 updates

Other modules write through Module 3 rather than keeping a second task or
problem state. For example, Module 4 can create a task with `source: "weather"`
and a stable `source_reference` such as `weather-event:rain-2026-10-07`.
Module 6 can create a problem with `source: "disease_detection"`. Repeating a
task write with the same season and source reference returns the existing task.

### Tests

From the `backend` directory, install the runtime and test dependencies, then
run the unit and API tests:

```bash
python -m pip install -r requirements.txt -r requirements-test.txt
python -m pytest tests -q
```

The API tests use SQLite for isolation. A test-only compiler maps the
PostgreSQL `JSONB` columns to SQLite `JSON`; production models and migrations
remain PostgreSQL-native. PostgreSQL migration/schema checks should also be run
with `alembic upgrade head` and `alembic check` against a development/test
PostgreSQL database.


## Module 6 disease detection

Module 6 exposes an image-analysis API for the Saon110 Bangladesh crop-disease
classifier. It reads the active crop and growth stage through Module 3's
GET /farmlands/{farmland_id}/state contract, persists each valid prediction in
disease_results, and asks Module 3's POST /farmlands/{farmland_id}/problems
contract to create or reuse an open problem for confident disease predictions.

Endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | /farmlands/{farmland_id}/disease-results | Analyze one multipart image field named image |
| GET | /farmlands/{farmland_id}/disease-results | List recent saved analyses; limit and offset are supported |
| POST | /farmlands/{farmland_id}/disease-results/{result_id}/sync-problem | Retry linking a saved possible-issue result to Module 3 |

All three endpoints require Module 1's verified farmer authentication. The M6 API
forwards the request's Bearer token or session cookie when it calls Module 3.
The internal Module 3 URL defaults to http://127.0.0.1:8000 and can be changed
with MODULE3_API_BASE_URL. Expo web origins are controlled by CORS_ORIGINS.
For a phone or emulator, set EXPO_PUBLIC_API_URL to an address reachable from
that device.

The endpoint accepts JPEG, PNG, and WebP files up to 10 MB. It checks file
decoding and dimensions, but it does not detect blur, framing, or whether a leaf
is in the photo. The selected classifier returns one class for the whole image;
it does not mark or explain individual symptoms. Low model scores and a
prediction whose crop prefix conflicts with Module 3's active crop are saved
as uncertain results and do not create a farm problem. Healthy results are
saved without a problem. A confident, matching disease class creates a
moderate-severity Module 3 problem. Repeated matching detections reuse an
existing open or monitored problem for the same season and category. Module 6
serializes its problem syncs per farm with a PostgreSQL advisory lock and
refreshes Module 3 state before creating a problem. If Module 3 is unavailable
during a problem write, the analysis remains saved and the screen offers a
retry for that same result. A retry reuses a problem if the earlier write has
already committed, without re-running inference or Gemini. However, Module 3's
current problem endpoint always inserts: a POST that continues after the
Module 6 client times out can commit after the retry's state check and create a
duplicate. Closing that timeout race requires an idempotency key or equivalent
support in Module 3.

When `GEMINI_API_KEY` is configured, Module 6 sends the uploaded photo to
Gemini for an independent visual cross-check. A possible farm problem is
created only when Gemini and the local classifier both identify a possible
issue on the active crop. Disagreement, uncertainty, or a Gemini error is
stored as an uncertain analysis and never creates a farm problem. With no key,
the local classifier runs alone. The frontend tells the farmer that Gemini may
receive the photo. Store the key only in the backend environment file (`.env`
at the project root for Docker Compose, or `backend/.env` for a local backend
process) or in the deployment secret manager; do not commit it. Rotate any key
that has been exposed.

The root `.env.example` is configured for Docker Compose, where the backend
uses `DB_HOST=db` and `DB_PORT=5432`. For a backend process running on the host,
copy `backend/.env.example` to `backend/.env` and point `DB_HOST`, `DB_PORT`,
and `DATABASE_URL` at the local database; the Compose database is published on
`127.0.0.1:5433`. The default `GEMINI_MODEL` is `gemini-3.8-flash` and the
request timeout is configurable with `GEMINI_TIMEOUT_SECONDS`.

The threshold defaults to 0.70 and can be changed with
DISEASE_CONFIDENCE_THRESHOLD. This is a prototype screening threshold, not a
calibrated probability or a field-validation result. Confidence is not used as
problem severity. The model does not produce verified symptoms or
disease-specific treatment advice, so the API returns no observed symptoms and
only conservative follow-up actions.

Put the downloaded checkpoint at backend/model/crop_veg_plant_disease_model.pth
or set DISEASE_MODEL_WEIGHTS_PATH. The class mapping is tracked at
app/data/plant_disease_classes.json. Install base, test, and ML dependencies
with pip install -r requirements.txt -r requirements-test.txt
-r requirements-ml.txt. The Docker image installs CPU PyTorch wheels. A clone
does not contain the ignored checkpoint; mount or download it into the model
directory before running inference.

The model repository declares CC BY-NC 4.0. Keep its attribution and
non-commercial restriction in mind for any use outside the NASA challenge:
https://huggingface.co/Saon110/bd-crop-vegetable-plant-disease-model

No database migration is required: disease_results already exists in the
shared schema. DiseaseResult stores an M3 problem ID in model_details after a
successful problem write; no new Problem foreign key is added.

## Agricultural knowledge starter set

`app/data/agricultural_knowledge_seed.json` contains five source-grounding
records based on public BARC, BAMIS, and SRDI information. They are deliberately
`in_review`, do not contain crop-specific fertilizer rates or treatments, and
are excluded from farmer-facing use until an authorized reviewer approves them.
This adds the data and import path; it does not add a chat retrieval endpoint or
automatically import records during application startup. Module 5 can retrieve
approved, in-scope records when its knowledge-grounding flow is implemented.
The source audit at `docs/knowledgebase-source-review.md` covers all ten
reviewed sites and explains why the dynamic map/advisory pages are not bulk
scraped into permanent advice.

After applying the database migrations, validate and import the seed from the
`backend` directory:

```bash
python -m scripts.import_agricultural_knowledge --check-only
python -m scripts.import_agricultural_knowledge
```

The importer uses deterministic IDs, preserves an unchanged review decision,
returns edited seed records to `in_review`, and never deletes records omitted
from the file. It writes to the existing `agricultural_knowledge` table, so no
schema migration is needed.

`python -m scripts.import_reference_data` runs this seed import together with
the M1 crop catalog and the policy-accepted BARC knowledge used by Module 2;
see `M2_GUIDE.md` → "Current knowledge coverage".
