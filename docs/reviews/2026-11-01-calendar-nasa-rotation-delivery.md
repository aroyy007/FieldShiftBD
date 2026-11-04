# Calendar, NASA advisory and rotation evidence delivery

Date:2026-11-01, Asia/Dhaka. Branch:arijit. Authority:
`docs/plans/2026-11-01-calendar-advisory-rotation-implementation.md` and the
owner's three-step implementation request. The owner explicitly deferred expert
agronomic review until later; source verification does not invent that approval.

## Implemented

- Four BRRI source references: dhan80/Aman, dhan31/Aman, dhan100/Boro and
  dhan48/Aus, with recurring sowing/transplant/harvest dates, seedling age,
  conditional care, sources and exclusions. No approved DB rows or operational
  tasks are created by the catalog. The GDD study's10°C base and Tmax/Tmin method
  are stored with their Gazipur Aman scope; cultivar base/cap/target stay null.
- Public calendar API plus cache-only `GET /advisory?district=&crop=&season=`.
  Canonical Bangladesh district IDs/names are validated; missing season returns
  choices. Invalid/missing/stale cache cannot trigger a NASA download or a
  fabricated recommendation. No private farm data enters the public response.
- Canonical deterministic compute at `backend/src/compute/agro.py`, with
  compatibility imports for existing callers. Full candidate search includes
  trailing observations across year boundaries; missing confirmation tails are
  separated from observed no-onset years. Sensitivity uses15/20/25mm.
- Explicit district prefetch/publish CLI, sourced sampling-point metadata,
  original replay retrieval timestamp and content-hashed local JSON versions.
  The parser now reads NASA GeoJSON daily data rather than parameter metadata
  and respects solar-unit metadata (AG response already uses MJ/m²/day).
  Normalizer v2 prevents reuse of older incorrectly normalized point caches.
- A real NASA response for BMD's published Rajshahi station reference point
  (24.37N,88.70E) was fetched, preserved and replayed through the corrected
  normalizer:9131 daily rows,2001–2025. Under the stated exploratory May–October
  definition, baseline12/recent13years give an observed median shift of0days.
  No predetermined11-day result or planting-date adjustment is used.
- Public bilingual district/season page, onset-distribution chart, GDD rendering
  when reviewed data exists, source/period/scale/cache labels and short summaries.
  Landing and Crop Advisor provide entry points. Calendar/care changes with the
  selected public season; unrelated source varieties are not substituted.
- Rotation API/UI now includes recorded season dates, district NASA context and
  exact variety/season/establishment-method calendar references. Wet-seeded steps
  cannot use transplanted dates. Incomplete calendar evidence blocks feasibility,
  ranking and plan selection.

## Review and verification

Spec review found search-window truncation, primary-threshold labelling and
replay provenance/refresh defects. Standards review found replay reuse,
stale-source acceptance and season/calendar mismatch. All were addressed with
backend regression tests or browser verification. Additional browser findings
(query hydration and cached build API URL) were corrected and rechecked.

- Full backend suite:349 passed,7 existing dependency/schema warnings; no skips.
- Fresh disposable PostgreSQL16 migrations and `alembic check`:passed.
- Frontend tests:38 passed; TypeScript and lint passed; web export:21 routes.
- Browser: actual cached NASA chart and source dates, BN/EN deep links,
  Boro→dhan100 and Aus→dhan48, and missing Dhaka cache verified. A fresh tab
  had no browser error logs.390px DOM width matched page width; district target
  measured326×56px. Native Android usability is not established by this check.

The local browser build uses the isolated test API on127.0.0.1:8012 and preview
server4173. This is not production deployment configuration. Changing Expo public
API environment variables may require a cleared Metro export cache.

## Remaining evidence/release gates

1. Agronomist review of onset/search assumptions, exact temperature inputs,
   cultivar thermal targets, full growth-stage/task schedules and applicable
   planting-shift policy. Public GDD/recommended shifts remain null meanwhile.
2. Full64-district climate-cache population, native-resolution/QA/rights review,
   Parquet release, additional NASA layers and held-out validation. One sourced
   grid point is not a district average, current station observation or field
   measurement. Other district identifiers can be selected but data may be absent.
3. Complete calendars for every rotation step (including wet-seeded varieties
   and green manure), calendar/resource feasibility and transparent tradeoff
   evaluation. Current context integration is not complete rotation scoring.
4. Reviewed activation/confirmation, physical-device testing and broader final
   plan gates remain separate. No claim of measured soil/yield/cost improvement.

## Primary evidence

- Calendar/GDD sources and limitations:
  [research record](../research/2026-11-01-crop-calendar-and-gdd-evidence.md).
- [NASA POWER daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/).
- [BMD Roanu report](https://live8.bmd.gov.bd/file/2017/04/09/pdf/36934.pdf),
  Table5 continuation, PDF index47/printed45:station coordinates. The event was
  2016; current station position/publication date/datum are not established.

Pre-existing BARC source captures and other workspace changes were preserved.
The full test result describes this workspace, including those existing sources.
