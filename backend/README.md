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
