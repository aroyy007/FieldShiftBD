# M4 ↔ Shared Schema Contract Proposal

**Module 4 — Weather Intelligence & Alerts**
Owner: `sharif/weather` branch
Status: proposal for Milestone-0 team agreement (Rule C — shared-contract
changes need team sign-off)

---

## 1. Purpose

M4 is a *leaf* module: it reads farm state from M3, reasons about whether
forecast weather changes what the farmer should do, and emits alerts. It owns
two tables (`weather_events`, `weather_alerts`) and writes to no one else's.

This document maps M4's internal types to the columns it persists, and lists
the small set of **shared-contract asks** M4 needs from other modules (chiefly
M3) so the current mock seams can be swapped for real integrations without
reshaping M4's logic.

Core product rule this contract must preserve (schema doc, line 568, verbatim):

> "The system should avoid simply notifying the farmer about weather without
> determining whether it changes what the farmer should do."

Everything below exists to serve that rule: the value-add is **suppression**,
not notification. The contract therefore carries enough provenance (which
threshold crossed, which task triggered the alert) to explain *why* an alert
fired — and to justify why detected events were deliberately withheld.

---

## 2. Reasoning pipeline (where each type lives)

```
Weather (providers)                         app/services/weather_providers.py
  → DetectedEvent        (detect_events)    app/services/weather_suppression.py
  → Farm Location /Crop /Stage /Tasks       app/services/mock_farm_state.py  (M3 seam)
  → AlertDecision        (_decide)          app/services/weather_suppression.py
  → WeatherEvent / WeatherAlert  (persist)  app/models/weather.py            [TODO: route layer]
  → *Out schemas         (wire contract)    app/schemas/weather.py
```

Internal dataclasses (`DetectedEvent`, `AlertDecision`, `Threshold`) are
deliberately **not** 1:1 with either the ORM tables or the wire schemas — per
schema-doc §14, not every internal type needs its own table or identical wire
shape.

---

## 3. Internal type → persisted column mapping

### 3.1 `DetectedEvent` → `weather_events`

`DetectedEvent` (`weather_suppression.py`) is produced by `detect_events` and
persisted as one `weather_events` row.

| DetectedEvent field | weather_events column | Notes |
|---|---|---|
| `event_type`        | `event_type` (String 50) | `heavy_rain` \| `heat_stress` \| `high_wind` |
| `severity`          | `severity` (String 20)   | `low` \| `medium` \| `high` |
| `description`       | `description` (Text)     | human-readable summary |
| `start_date`        | `start_time` (DateTime tz) | date string → day-start timestamp |
| `end_date`          | `end_time` (DateTime tz)   | date string → day-end timestamp |
| `facts`             | `data` (JSONB)           | via `to_event_data()` → `facts` key |
| `threshold`         | `data` (JSONB)           | via `to_event_data()` → `threshold` key (see §4) |
| (window)            | `data` (JSONB)           | `detected_window: {start, end}` |
| —                   | `farmland_id` (UUID, no FK) | from the farm-state slice |
| —                   | `id`, `created_at`       | DB-generated |

`DetectedEvent.to_event_data()` is the single serializer for the `data` column.

### 3.2 `AlertDecision` (emitted) → `weather_alerts`

Only decisions with `emitted=True` become `weather_alerts` rows. Suppressed
decisions are **not persisted as alerts** (they may optionally be logged for
transparency, but must never surface to the farmer as a bare weather report).

| AlertDecision field | weather_alerts column | Notes |
|---|---|---|
| `title`             | `title` (String 200) | |
| `message`           | `message` (Text)     | |
| `recommended_action`| `recommended_action` (Text) | the action the farmer should now take |
| `event.severity`    | `severity` (String 20) | mirrors the source event |
| `event` (row)       | `weather_event_id` (UUID, real FK → weather_events.id, ON DELETE CASCADE) | self-contained within M4, so this FK is enforced |
| `triggering_tasks`  | `data`/future column | task ids/titles that triggered the alert — see §5.3 |
| —                   | `farmland_id` (UUID, no FK) | from the slice |
| —                   | `season_id` (UUID, no FK, nullable) | from the slice when known |
| —                   | `status` (String 20, default `unread`) | farmer-facing read state |
| —                   | `id`, `created_at`, `read_at` | DB-generated / set on read |

`suppression_reason` (on suppressed decisions) has **no column** and is not
persisted; it is returned on the API only via `SuppressedEventOut` for
transparency/debugging.

### 3.3 Wire schemas (`app/schemas/weather.py`)

The API never returns a bare weather report. `WeatherAssessmentOut` returns
`alerts` + `suppressed_events` (reasons) + context. `WeatherEventOut` /
`ThresholdOut` exist for debug/transparency surfaces, not the farmer feed.

---

## 4. Threshold provenance

`Threshold` (`weather_thresholds.py`, frozen dataclass) carries
`key / value / unit / source`. There is **no shared column** for this
provenance today, so it travels inside `weather_events.data.threshold` via
`Threshold.as_dict()`.

- Defaults are **demo placeholders** (Bangladesh smallholder context), not
  validated agronomy — each `source` string says so.
- `get_thresholds(overrides)` is the configuration seam: values can be tuned
  without touching rule logic; unit/source are preserved and the source gets an
  `(overridden)` suffix for traceability.

**Milestone-0 ask (optional):** if the team wants thresholds tunable per
crop/region from a shared config table, M4 would read that table here. Until
then, provenance-in-`data` is sufficient and self-contained.

---

## 5. Milestone-0 asks (shared-contract items needing team agreement)

These are the only places M4 reaches beyond its own tables. Each currently has
a working mock seam, so none block M4 standalone — but they must be agreed
before real cross-module wiring.

### 5.1 M3 farm-state read slice

M4 consumes a read-only projection (`FarmStateSlice` in `mock_farm_state.py`):
`farmland_id, season_id, growth_stage_id, latitude, longitude, crop_name,
growth_stage, location_name, tasks[]`.

**Ask:** M3 exposes a read API returning this shape (or equivalent) keyed by
`farmland_id`. Swap point is `get_farm_state_slice()` — a single function.
M4 never writes farm state (Rule B: M4 suggests, it does not mutate).

### 5.2 `TaskRef.category`

M4 reasons about impact by task **category** (`irrigation`, `spraying`,
`harvest`, `fertilizing`, `transplanting`). The team `tasks` schema has a
`source` column but **no `category`**, so M4 currently derives/normalizes it
in the mock.

**Ask:** either (a) M3 adds a `category` (or `type`) column to `tasks`, or
(b) the team agrees a canonical mapping M4 may own. Preference: (a), so impact
rules are driven by data all modules share rather than an M4-private mapping.
The `_EVENT_IMPACT` map (`weather_suppression.py`) is the consumer.

### 5.3 Persisting triggering tasks on an alert

`AlertDecision.triggering_tasks` records which farmer task(s) caused the alert
to fire — the audit trail for "why did I get this alert?". There is no column
for it yet.

**Ask:** agree whether to add a `weather_alerts.triggering_task_ids` (UUID
array / JSONB) column, or keep it inside `data`. M4 is fine with either; it
only needs the decision recorded so the frontend can show provenance.

### 5.4 Deferred cross-module FK constraints

`weather_events.farmland_id`, `weather_alerts.farmland_id`, and
`weather_alerts.season_id` are typed `UUID` but carry **no DB FK constraint**,
because the `farmlands` / `seasons` tables do not exist on this branch yet.
This keeps Alembic `--autogenerate` clean (it would otherwise fail on missing
referents). The self-referential `weather_alerts.weather_event_id` FK **is**
enforced, since both tables are M4-owned.

**Ask:** once M3's `farmlands` / `seasons` tables land, add these FK
constraints in a follow-up migration. Documented in `app/models/weather.py`.

---

## 6. What M4 does NOT ask for

- No writes to any other module's tables.
- No shared `Base` changes — M4 inherits the single `app/models/base.py:Base`
  so Alembic sees one unified MetaData.
- No new router registration conflicts — M4 owns only `/weather/*`.
- No changes to teammate scaffolding (`config.py`, `database.py`,
  `routes_system.py`, `docker-compose.yml`, `alembic/env.py`) — all verified
  compatible as-is.

---

## 7. Open follow-ups (M4-internal, not contract)

1. **Migration (blocked):** `alembic revision --autogenerate -m "m4 weather
   tables"` then `alembic upgrade head`. Blocked only on a running Postgres
   (Docker). Autogenerate scope is confirmed to be exactly
   `weather_events` + `weather_alerts`.
2. **Persist alerts:** the route layer is currently read-only; persisting
   emitted alerts to `weather_alerts` is a follow-up once the migration is
   applied. The engine result objects already carry everything needed.
