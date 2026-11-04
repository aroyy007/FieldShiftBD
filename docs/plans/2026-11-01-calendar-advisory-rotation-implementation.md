# Calendar → NASA advisory → rotation implementation

Authority: FINAL_IMPLEMENTATION_PLAN.md and the owner's three-step request.
Workspace: existing `arijit` branch; preserve the existing dirty workspace.

## Delivery tasks

1. Evidence: check primary agronomy sources; retain structured source references,
   GDD method/input scope, stage/task support, review status and missing fields.
   Never invent a reviewer, thermal target, crop schedule or climate-shift policy.
2. Shared analytical service: separate deterministic onset/GDD computation from
   acquisition and routes; keep existing farm API compatible. Distinguish calendar
   reference, reviewed rule and supported recommendation.
3. Public cache-only advisory: canonical district/crop/season validation; read
   district cache through its bounded reader. No public request downloads NASA
   history. Missing/corrupt data and unsupported agronomy stay explicit. Private
   farm/season data must never enter public results.
4. Acquisition and farmer charts: explicit prefetch CLI for district representative
   points with provenance; display period distributions/GDD and bilingual action,
   assumptions, source period/scale/cache status. Point data is not a district mean.
5. Rotation evidence: attach applicable reviewed calendars and NASA period evidence
   to documented sequences; compute supported calendar constraints only. Missing
   calendar/GDD/field inputs remain unavailable and cannot produce a rank or plan.
6. Verify and review: meaningful compute/API/permission tests, full PostgreSQL
   suite, frontend type/lint/tests/export; document remaining external-review gates.

## Integration decisions

- Reuse M1 canonical geocodes. The cache key is the canonical 4-digit district
  code; public input may use the exact canonical name or code.
- Reuse M2 agronomy ownership, M4 climate reader, existing contract generator and
  existing Crop Advisor screen. No second farm store or operational writes.
- Research verification is not agronomist approval. A source-backed published
  window may be displayed with scope while adjusted recommendations remain null.
- No district centroid is guessed. A prefetched point requires explicit source
  coordinates and a representativeness label; unpopulated districts are supported
  identifiers with unavailable data, not claimed climate coverage.

## Progress

- Source evidence: four BRRI transplanted rice profiles source-checked and exposed
  through a public reference API and bilingual farmer views. Operational approval,
  cultivar thermal targets and full dated stage/task rules remain pending review.
- Historical pipeline: public cache-only API, canonical district selector,
  distribution/GDD rendering, source/time/point/cache labels and bounded summaries
  implemented. Real Rajshahi POWER history:9131 daily rows,2001–2025. Current
  exploratory May–October observed median shift:0days, baseline12/recent13years.
- Rotation integration: exact variety/season/establishment matching, source
  calendar references, recorded-season dates and district NASA context added.
  Full reviewed calendar feasibility, ranking and operational selection remain
  unavailable where evidence is missing; no numeric soil/yield benefit is claimed.
- Review findings corrected: full candidate search with trailing confirmation,
  fixed sensitivity protocol, original replay acquisition times/explicit refresh,
  stale-source rejection and matching public season/calendar selection.
- Verification:349 backend tests passed including PostgreSQL integrations; clean
  migrations and Alembic schema check;38 frontend tests passed, clean lint and
  TypeScript,21-route web export. Browser verified BN/EN deep links, real chart,
  Boro/Aus references and unavailable district;390px width without overflow.
- External dependency: owner will arrange agronomic review later. Full64-district
  climate population, versioned Parquet publication, additional NASA source
  layers, physical Android testing and final agronomic validation remain open.
