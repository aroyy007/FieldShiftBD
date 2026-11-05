# Regional NASA Crop and Rotation Advisor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compare a farmer's baseline and two locally supported crop sequences in Rajshahi and Chattogram using reviewed agronomy, farmer priorities and appropriately scaled NASA evidence.

**Architecture:** Acquisition workers publish immutable regional evidence releases. Deterministic M2 functions evaluate dates, exposure and constraints from local release features; authenticated APIs and the existing Expo app explain the results and propose a separately confirmed season plan. Coarse observations retain their native support even when joined to a common analysis grid.

**Tech Stack:** Existing Python 3.12/FastAPI/Pydantic/SQLAlchemy/PostgreSQL and Expo/React Native/TypeScript; PyArrow Parquet feature releases; isolated acquisition image with earthaccess, rasterio, pyproj, xarray and source-format readers. Dependency versions are locked after pilot compatibility checks.

**Spec:** `docs/superpowers/specs/2026-11-04-regional-nasa-rotation-design.md`; product research: `docs/research/2026-11-04-nasa-agriculture-product-research.md`.

## Global constraints

- First supported districts: Rajshahi `5081`, Chattogram `2015`. Do not implement or advertise full Bangladesh coverage for this workstream.
- Grid: `bd-ea-1km-v1`, EPSG:6933, 1,000 m cells, projected origin `(0,0)`, floor-based row/column; WGS84 public geometries.
- Existing v1 contracts, daily POWER caches and endpoints remain backward compatible; new comparison contract version is `2.0.0`.
- Native/effective support, source dependencies, units, QA, observation period, retrieval/cache status and provenance travel with every metric.
- No operational writes during comparison. M3 owns seasons/tasks and M5 coordinates explicit confirmation.
- No automatic planting shift from rainfall-onset difference; no crop-biomass/soil-carbon claims from GEDI; no district groundwater claims from GRACE; no LST in air-temperature/GDD calculations.
- Missing information cannot improve eligibility or ordering. Optional/context-only sources do not create a false mandatory failure.
- Evidence remains source-checked/unreviewed until a real reviewer and scope/date are recorded. Source publication does not equal agronomist approval.
- No request-time NASA scraping/download in the comparison route; use a validated local release.
- All tasks below are proposed work. No implementation, dataset download or benchmark pass is claimed by checking this plan into the repository.

## Review focus

1. Mixed/coastal cells and a pin outside its claimed district: resolve scope explicitly, mask ocean, preserve boundary overlap; Task 1/3 tests.
2. Cloudy/missing observations and incompatible product units/releases: retain unknowns, never generate false rain/cover/ET; Task 2/4/5 tests.
3. Cross-year calendars, incomplete baseline, missing cultivar parameters and unknown salinity/water: no invented dates or confident preference; Task 6/7 tests.
4. Multiple analysis cells sharing one source pixel, and SMAP-L4 sharing IMERG ancestry: no inflated samples/confidence; Task 3/8 tests.
5. Profile/release changes between comparison and plan confirmation: revalidate snapshot/release and ownership, reject obsolete proposals without partial writes; Task 9/11 tests.

---

## Delivery slices and dependencies

| Slice | Tasks | Independently reviewable result |
|---|---|---|
| A — Regional foundation | 1–3 | Validated product samples, boundaries, common-grid features and atomic release |
| B — Real rotation decision | 6–9 using POWER/IMERG from A | Baseline + supported alternatives, NASA exposure and user priorities affect comparison |
| C — Soil/vegetation/terrain | 4, then repeat 8/9 acceptance | SMAP/MODIS/SRTM enrich existing comparison with partial-data behavior |
| D — Remaining researched products | 5, then 8/9 acceptance | Landsat/ECOSTRESS plus GRACE/GEDI roles are visible with truthful applicability |
| E — Farmer delivery | 10–12 | Bangla/English screen, confirmed handoff, reproducible demo and validation report |

Do not postpone a working rainfall/calendar comparison until every optional NASA family is available. Within a slice, preserve interface dependencies described below. Commit after each verified task; pushing/merging is a separate owner instruction.

## File structure

New source ingestion belongs under `backend/app/services/earth_observation/`; data science under `backend/src/compute/`; M2 orchestration under `backend/app/services/rotation/`. New files below are proposed, not existing implementations.

```
backend/app/contracts/challenge/v2.py
backend/app/services/earth_observation/
  registry.py  discovery.py  acquisition.py  qa.py  grid.py
  harmonize.py  release.py  provider.py
  products/{imerg,smap,modis,srtm,landsat,ecostress,grace,gedi}.py
backend/app/services/rotation/{catalog,service,explanations}.py
backend/src/compute/{rotation_calendar,rotation_exposure,rotation_preferences,water_balance}.py
backend/app/api/routes_m2_rotation_v2.py
backend/scripts/{prefetch_regional_evidence,publish_regional_evidence}.py
backend/data/earth_observation/{products.json,regions.json,qa-policy-v1.json}
backend/app/data/m2_knowledge_sources/rotation_catalog_v2.json
frontend/src/services/rotation-comparison.ts
frontend/src/components/rotation/{ComparisonPanel,OptionCard,TradeoffTable,EvidenceDetails}.tsx
```

## Task 1: Version contracts, region scope and product catalog

**Files:** Create v2 contract, `earth_observation/registry.py`, `grid.py`, `backend/data/earth_observation/products.json`, `regions.json`, QA policy. Modify climate source register with researched candidate versions while retaining `planned` until actual publication. Tests: `backend/tests/test_rotation_v2_contracts.py`, `test_eo_registry.py`, `test_eo_grid.py`.

**Interfaces:** `resolve_analysis_cell(lon: float, lat: float, region_code: str, regions: RegionRegistry) -> AnalysisLocation`; `ProductDefinition` and `EvidenceReleaseManifest`; v2 `RotationCompareRequest`, `RotationComparisonV2`, `RotationOptionV2`, `FeatureEvidence`, `MetricEvidence` as defined by spec section 8. `MetricEvidence` includes metric_id, nullable value/unit, status, valid_year_count, total_year_count, evidence_ids and method_id. `FeatureEvidence` includes scope/support/units/QA/version metadata, not just a URL.

- [ ] Add failing contract tests: only `5081`/`2015` supported in v2; malformed priority/unknown candidate IDs rejected; missing metric has null value; current sequence uses the same option schema as alternatives; no selection authorization in comparison.
- [ ] Add geospatial tests: negative projected coordinates use floor, edge cells stable across runs, boundary-intersection weights sum to covered area, farm pin outside district rejected with correction hint, district-only scope remains district aggregate.
- [ ] Run `docker compose exec backend pytest tests/test_rotation_v2_contracts.py tests/test_eo_registry.py tests/test_eo_grid.py -q`; confirm missing implementation failures.
- [ ] Select permitted district polygons and cropland-mask source; record owner/version/date/license/CRS/hash. If unavailable, mark area-based release blocked and keep current point-cache mode; do not invent geometry from names.
- [ ] Implement schemas and registry. Pin candidate products: SMAP SPL3SMP_E v6/SPL4SMGP v8; IMERG Final daily v07; MOD13Q1.061; Landsat C2 L2 T1; ECO_L2T_LSTE.003 and ECO_L3T_JET.002; SRTMGL1.003; JPL mascon RL06.3_v04; GEDI L4A v3. Persist resolved collection/DOI/CMR IDs at discovery.
- [ ] Add observation kind `retrieval|reanalysis|assimilation|model_output|static_surface|farmer_report|regional_agronomy`; add shared-input groups and role `decision|corroboration|context_only|not_applicable`.
- [ ] Rerun the task tests; commit `feat: define regional evidence and rotation v2 contracts`.

## Task 2: Acquire and normalize POWER plus IMERG pilot data

**Files:** Create `earth_observation/discovery.py`, `acquisition.py`, `qa.py`, `products/imerg.py`, `backend/scripts/prefetch_regional_evidence.py`, `backend/requirements-geo.in`, locked acquisition dependency file and `backend/Dockerfile.acquire`. Modify POWER provider only where needed to expose a compatible acquisition adapter; keep its existing output schema stable. Tests: `test_eo_acquisition.py`, `test_eo_imerg.py`, existing POWER tests.

**Interfaces:** `discover_assets(product_id: str, region_code: str, start: date, end: date) -> list[SourceAsset]`; `acquire_assets(assets: list[SourceAsset], config: AcquisitionConfig) -> AcquisitionReport`; `normalize_asset(asset: SourceAsset, product: ProductDefinition) -> NormalizedAsset`. Credentials supplied to backend worker only. CLI `python -m scripts.prefetch_regional_evidence --district 5081 --district 2015 --products power,imerg --start 2024-01-01 --end 2024-12-31 --max-download-gb 10 --report <path>`; `--offline` forbids network.

- [ ] Write tests for timeout/retry, auth failure with sanitized report, resume checksum match, truncated asset, HTML error body masquerading as data, missing-day handling and mm/hour-to-depth conversion on a known synthetic example.
- [ ] Run `docker compose exec backend pytest tests/test_eo_acquisition.py tests/test_eo_imerg.py -q`; observe expected failures.
- [ ] Implement bounded downloader: 2 concurrent requests per source, <=3 retries with backoff, explicit download quota, no arbitrary client URL or token in output. Interrupted files remain temporary; raw checksum-addressed assets become immutable only after validation.
- [ ] Download actual pilot granules for both regions after runtime credentials/access setup. Inspect dimensions, units, fill values, QA and actual time coverage; save a small permitted decoded fixture with provenance. A successful metadata search alone does not pass this step.
- [ ] Keep PRECTOTCORR and IMERG separate. Extend v2 POWER acquisition with Tmax/Tmin and optionally RH2M/WS2M; do not reinterpret existing T2M as the published Tmax/Tmin GDD method. A regional POWER release samples/deduplicates source support across the polygon; previous point bundles remain labeled points.
- [ ] Rerun tests and real sample validation; record successful/blocked access. Only then expand history to 2001–2025 and lock dependencies/image; commit `feat: acquire reproducible regional climate evidence`.

## Task 3: Harmonize and publish multi-source evidence releases

**Files:** Create `earth_observation/harmonize.py`, `release.py`, `provider.py`, `backend/scripts/publish_regional_evidence.py`; reuse publication principles from existing `climate/district_publish.py` without altering its table schema. Tests: `test_eo_harmonize.py`, `test_eo_release.py`.

**Interfaces:** `harmonize_asset(asset: NormalizedAsset, grid: AnalysisGrid, qa: QAPolicy) -> FeaturePartition`; `publish_release(partitions: list[FeaturePartition], manifest: EvidenceReleaseManifest, root: Path) -> str`; `RegionalEvidenceProvider.get_context(location: AnalysisLocation, *, release_id: str) -> RegionalEvidenceContext`. Partition key includes region, product, variable and year; manifests provide byte and decoded-row limits.

- [ ] Test constant coarse rasters, fine-raster area-weighted means, rainfall-depth preservation, categorical masks, coastal partial cells, CRS roundtrip, nodata exclusion and sample-count behavior where 100 target cells share one source pixel.
- [ ] Test unit mismatch, no valid overlap, checksum tamper, missing partition, oversized manifest, symlink/path traversal, interrupted publication and rollback to previous release. Assert no partial release becomes current.
- [ ] Run `docker compose exec backend pytest tests/test_eo_harmonize.py tests/test_eo_release.py -q` and confirm initial failures.
- [ ] Implement the spec's methods: native mask/scale first; area weights for intensive values; no bilinear categorical interpolation; slope before terrain aggregation; coarse support IDs retained. Record requested and actual dates separately.
- [ ] Publish 2024 pilot, compare native versus derived totals/means on known windows, then full required partitions. Add cache `hit|missing|corrupt|superseded`; historical coverage is distinct from freshness of current observations.
- [ ] Rerun tests and cold-load the published manifest with network disabled; commit `feat: publish regional NASA feature releases`.

## Task 4: Add SMAP, MODIS and SRTM evidence

**Files:** Create `products/smap.py`, `modis.py`, `srtm.py`; extend QA registry and feature adapters. Tests: `test_eo_smap.py`, `test_eo_modis.py`, `test_eo_srtm.py`.

**Interfaces:** All implement `normalize_asset(...) -> NormalizedAsset` and Task 3 feature publication. Publish metrics `surface_moisture_anomaly`, optional `modeled_rootzone_anomaly`, `seasonal_ndvi`, `vegetation_observation_coverage`, `slope_median_deg`, `slope_p90_deg`; exact product band names validated against real samples.

- [ ] Add tests for SMAP invalid/coastal-water flags, explicit 0–5 cm versus modeled root-zone depth, MODIS scale/QA/cloud gaps and static DEM slope at native metric resolution.
- [ ] Assert SMAP-L4/IMERG common ancestry retained; no inflated independent N. Assert missing MODIS composites yield unknown cover rather than bare field. Test optical 30/50/70% coverage sensitivity.
- [ ] Run `docker compose exec backend pytest tests/test_eo_smap.py tests/test_eo_modis.py tests/test_eo_srtm.py -q` to verify failures.
- [ ] Acquire sample files in each region, implement decoders, preserve source-quality flags alongside normalized QA. Verify product-specific 2026 advisories; start with completed 2015–2025 SMAP and 2001–2025 MODIS.
- [ ] Publish expanded release. Ordinary crop comparison must still return a partial result if optional moisture/optical coverage fails. Rerun tests; commit `feat: add wetness vegetation and terrain context`.

## Task 5: Integrate Landsat, ECOSTRESS, GRACE and GEDI within their valid roles

**Files:** Create `products/landsat.py`, `ecostress.py`, `grace.py`, `gedi.py`; extend product registry and release inventory. Tests: corresponding `test_eo_<product>.py`.

**Interfaces:** Same acquisition/normalization contracts. Additional `RegionalStorageContext` contains mascon/region identity, monthly anomaly/units/baseline/uncertainty; `WoodyBiomassContext` contains valid footprint count/epoch/AGBD/SE and applicability. Neither is an annual-crop performance target.

- [ ] Test Landsat scaled reflectance NDVI against a hand calculation that differs from raw-DN NDVI; test cloud/shadow/saturation flags and near-zero index denominator.
- [ ] Test LSTE V3 versus JET V2 schema separation, LST cannot enter GDD, instantaneous flux cannot be summed as mm/day and unmatched local observation times cannot create a thermal trend.
- [ ] Test GRACE replicated samples do not become independent district groundwater values, mission gap stays null, GEDI V3 quality/domain flags differ from V2 and crop-only land yields `not_applicable`.
- [ ] Run `docker compose exec backend pytest tests/test_eo_landsat.py tests/test_eo_ecostress.py tests/test_eo_grace.py tests/test_eo_gedi.py -q` to verify expected failures.
- [ ] Acquire regional pilot observations and inspect actual units/flags. Add Landsat 2013–2025, ECOSTRESS 2018–2025 and actual GRACE/GEDI coverage only after sample checks. If valid crop or woody observations are absent, publish `no_coverage` with reason instead of fabricated surfaces.
- [ ] Rerun tests; publish a release inventory with decision/context/not-applicable roles for every family; commit `feat: add thermal regional water and woody landscape evidence`.

## Task 6: Build source-scoped crop/rotation catalog and calendar feasibility

**Files:** Create `services/rotation/catalog.py`, `rotation_catalog_v2.json`, `src/compute/rotation_calendar.py`; reuse `crop_calendar_references.py` and current source records. Tests: `test_rotation_catalog_v2.py`, `test_rotation_calendar.py`.

**Interfaces:** `load_rotation_candidates(region_code: str, snapshot: FarmProfileSnapshot) -> list[RotationCandidate]`; `evaluate_calendar(candidate: RotationCandidate, planning_year: int, rules: ReviewedRuleSet) -> CalendarFeasibility`. Candidate carries crop codes, event basis, date windows, source/review IDs and applicability; baseline uses the same dated-step structure.

- [ ] Write tests for Aman-to-Rabi crossing December, seedbed versus transplant dates, incompatible crop durations, sourced turnaround, leap dates, missing GDD targets and incomplete baseline history.
- [ ] Run `docker compose exec backend pytest tests/test_rotation_catalog_v2.py tests/test_rotation_calendar.py -q`; confirm initial failures.
- [ ] Extract exact regional crop pattern/calendar conditions from research and government sources; human review status is not invented. Cross-reference Chittagong-region study upazilas with district `2015`; Hill Tracts must not leak into the district catalog.
- [ ] Implement eligibility as eligible/ineligible/unknown with explicit source IDs. Retain existing baseline even if invalid; do not fabricate a complete annual sequence or turn missing dates into fallow.
- [ ] Produce a researcher-reviewed demo scenario with two defensible alternatives; if unavailable, preserve insufficient evidence and log the exact agronomy input still needed. Rerun tests; commit `feat: evaluate sourced rotation calendars`.

## Task 7: Compute seasonal exposure and bounded water metrics

**Files:** Create `src/compute/rotation_exposure.py`, `water_balance.py`; reuse `agro.py` without changing its current GDD method under the same name. Tests: `test_rotation_exposure.py`, `test_rotation_water_balance.py`.

**Interfaces:** `evaluate_exposure(calendar: CalendarFeasibility, context: RegionalEvidenceContext, rules: ReviewedRuleSet) -> ExposureVector`; `compute_reference_et(weather: DailyWeatherInputs, method: ETMethod) -> DailyETSeries`; `evaluate_water_dependence(candidate: RotationCandidate, water: FarmWaterContext, rules: ReviewedRuleSet) -> WaterAssessment`.

- [ ] Add known-answer tests for rainfall sum, complete-window dry spell, Tmax/Tmin GDD, reviewed heat-stage exposure, historical valid-year denominator, missing crop stage and soil uncertainty. Low-coverage seasons cannot become success years. Observed baseline NDVI/moisture/ET must not be reused as a measured counterfactual outcome for an unplanted alternative.
- [ ] Add FAO-56 worked-example test before enabling reference ET; test missing humidity/wind/radiation returns `insufficient_inputs`. Test ECOSTRESS observations cannot predict another unplanted crop's ET and paddy rice cannot use an upland bucket as if calibrated.
- [ ] Run `docker compose exec backend pytest tests/test_rotation_exposure.py tests/test_rotation_water_balance.py -q` and confirm failures.
- [ ] Implement season/stage replay on each source's actual years; compare candidates on common valid years where possible and label differing periods. Optional water-balance execution stays disabled until reviewed soil/Kc/management parameters exist; irrigation dependence can still be compared categorically.
- [ ] Implement bare-field interval only from dated calendar/history and explicit residue/cover assumptions. Pair with rainfall/slope as an exposure proxy; do not output erosion tonnes or nitrogen/carbon savings.
- [ ] Rerun tests, retain nulls/reasons for unavailable metrics; commit `feat: compute climate exposure for crop sequences`.

## Task 8: Apply preferences, uncertainty and explain the comparison

**Files:** Create `src/compute/rotation_preferences.py`, `services/rotation/explanations.py`, `services/rotation/service.py`; tests `test_rotation_preferences.py`, `test_rotation_uncertainty.py`, `test_rotation_service_v2.py`.

**Interfaces:** `compare_options(options: list[EvaluatedOption], priorities: list[Priority]) -> PreferenceResult`; `compare_rotations(snapshot: FarmProfileSnapshot, request: RotationCompareRequest, evidence: RegionalEvidenceContext, catalog: ReviewedRuleSet) -> RotationComparisonV2`. `PreferenceResult` returns ordered groups/non-dominated IDs, ordering_status, used_dimensions and exclusions; ties are groups.

- [ ] Write fixture tests where reliable irrigation versus no irrigation changes admissibility; water-first versus income-first priorities change ordering only if both metrics are actually supported. If income data is missing, assert `insufficient_evidence`, not invented profit.
- [ ] Test baseline/alternatives share the same eligibility/metric rules; adding an unknown metric cannot improve preference; optional GEDI absence does not block rice; duplicate source supports cannot narrow uncertainty; deterministic hash/input yields repeatable output.
- [ ] Run `docker compose exec backend pytest tests/test_rotation_preferences.py tests/test_rotation_uncertainty.py tests/test_rotation_service_v2.py -q` and confirm failures.
- [ ] Implement hard constraints → complete comparable dimensions → non-dominated set → lexicographic priorities → sourced calendar buffer → stable display ID. No unexplained total score.
- [ ] Reuse annual comparison/15–20–25 mm sensitivity; bootstrap whole years/support units. At short records use coverage/spread without a probability claim. Retain shared input ancestry and POWER/IMERG disagreement.
- [ ] Generate bilingual explanation templates from metric/rule/source IDs. `recommended_shift_days` remains null unless candidate dates pass reviewed calendar and exposure constraints; never directly copy rainfall-onset shift.
- [ ] Run source ablation: POWER/IMERG removal changes a known exposure test case; GRACE/GEDI context removal leaves annual-crop ordering unchanged. Record real pilot results separately from synthetic decision tests. Commit `feat: explain farmer priorities and climate rotation tradeoffs`.

## Task 9: Authenticated API, runtime adapter and explicit save

**Files:** Create `api/routes_m2_rotation_v2.py`; modify `app/main.py`, `services/foundation/runtime.py`, contract export script; create optional saved-artifact model and Alembic migration following the actual existing migration chain. Tests: `test_rotation_api_v2.py`, contract generation, migration/ownership tests.

**Interfaces:** `POST /advisor/v2/farmlands/{farmland_id}/rotation-comparisons` with typed request; `GET /advisor/v2/regions`; allowlisted public `GET /advisor/v2/evidence/{public_asset_id}`; explicit `POST /advisor/v2/farmlands/{farmland_id}/rotation-comparisons/saved` accepts recipe/hash, re-evaluates server-side and stores authoritative output after owner request.

- [ ] Test 401 unauthenticated, 404 non-owned farm, 422 malformed/out-of-scope request; partial optional source, 503 no valid core release, and path/asset allowlist. Keep public region metadata free of farm/account details.
- [ ] Test comparison POST does not create seasons/tasks/problems or persistent farm artifacts. Save rejects changed snapshot/release with 409, is idempotent and cannot trust client-supplied metrics. Migration downgrade/data retention is reviewed before use on real DB.
- [ ] Run `docker compose exec backend pytest tests/test_rotation_api_v2.py tests/test_contract_generation.py -q` and confirm new-route failures.
- [ ] Implement route dependency ownership, service adapter and bounded result caching by snapshot/release/request hash. Export v2 TypeScript separately; keep v1 generated types unchanged.
- [ ] Rerun tests including existing planting-window/rotation tests; commit `feat: expose regional rotation v2 API`.

## Task 10: Farmer comparison UI and evidence view

**Files:** Create frontend service and rotation components in file tree; modify `frontend/src/app/farmlands/[id]/crop-advisor.tsx`, localization dictionaries and generated v2 contracts; extend `frontend/src/app/advisory.tsx` only to link regional evidence. Read `frontend/AGENTS.md` and matching installed Expo SDK docs before implementation.

**Interfaces:** `fetchRotationComparison(farmlandId, request, signal?) -> Promise<RotationComparisonV2>`; one request envelope/version from Task 9. Component renders baseline and alternatives using the same `OptionCard`; no independent browser-side agronomic computation.

- [ ] Add service/component cases for supported region, unsupported district, unknown current sequence, cloudy/missing source, no eligible alternative, ties, outdated release and two changed priority inputs. Use existing frontend test infrastructure; add a component harness only if needed for meaningful behavior assertions.
- [ ] Implement farmer flow: confirm history → choose priority → compare → expand evidence → request plan proposal. Main screen shows understandable Bangla/English next step, water/calendar/risk and missing information; metadata is expandable.
- [ ] Keep technical terms out of primary copy; expose NASA source, observation period, effective scale and cache label in details. Start summary-only; map loads on request and never depicts coarse cells as field “safe” zones.
- [ ] Open browser at phone widths and enter two farm scenarios/priorities; inspect requests/responses, auth/errors and all touched navigation. Test skeleton/error/retry/cancel behavior and no silent mutation.
- [ ] Run frontend `npm test`, `npm run lint`, `npx tsc --noEmit`, and web export using the installed package manager; run relevant backend API tests. Commit `feat: show farmer rotation comparisons in Bangla and English`.

## Task 11: Confirmed M3 plan handoff and M5 explanation

**Files:** Modify existing M5 action route/coordinator and M3 operational owner only after inspecting their current action schemas; add `services/operational_actions/rotation_plan.py` for a specific supported season-plan proposal. Tests: `test_rotation_plan_confirmation.py`; existing action/outbox/task-diff tests.

**Interfaces:** `propose_rotation_plan(farmer_id, farmland_id, comparison_hash, option_id) -> ProposedAction`; registered action kind `rotation_plan`, executed by M3 handler within existing unit of work. Include expected farm/snapshot/release/calendar versions and selected season only; a whole annual rotation is not silently activated as simultaneous seasons.

- [ ] Test comparison never writes; proposal shows exact season/task diff; confirm applies once; repeated idempotency key returns same receipt; dismiss writes no season; ownership/release/profile changes reject stale action.
- [ ] Test a future multi-crop intention cannot create overlapping active seasons. Missing reviewed stages/tasks leaves plan unexecutable with reason rather than generating unsupported schedules.
- [ ] Run `docker compose exec backend pytest tests/test_rotation_plan_confirmation.py -q`; confirm missing handler failures.
- [ ] Implement explicit confirmation through M5/M3 transactional ownership. Chat can narrate the persisted comparison but cannot execute a free-form agronomic action. M6 disease output is contextual unless reviewed rules and confirmed problem history support a constraint.
- [ ] Run focused and existing action/outbox tests; verify UI confirmation/cancel and reload state. Commit `feat: confirm sourced rotation season plans`.

## Task 12: Validate, package and update public claims

**Files:** Create `docs/reviews/2026-11-04-regional-rotation-validation.md` at execution time with actual dated results; maintain product/release citations and `README.md`; add offline regional bootstrap script and a small permitted demo release. Do not pre-populate success claims from this plan.

- [ ] Validate real pilot source samples against documented units/QA, independent gauges/calendar observations where accessible, source overlap bias and native-versus-grid summaries. Record label counts, geography, years, unavailable data and review identity.
- [ ] Perform temporal holdout and spatial-support blocking if evaluating predictive rules. Fit thresholds on training only. Pre-register performance thresholds after pilot data QA and before holdout evaluation; no unmeasured accuracy percentage.
- [ ] Run `docker compose exec backend pytest -q`; frontend tests/lint/typecheck/web export; contract generation and migration checks. Use Docker/Python 3.12; host Python 3.9 is not an acceptable backend validation environment.
- [ ] Restart clean services; create authorized synthetic local accounts; test two regional farms, ownership, changed priorities, saved comparison, confirmation and app pages through the browser. Test corrupt/missing release and offline cache mode. External crop-image transfer is outside this rotation task.
- [ ] Measure cold/warm comparison response time and memory on recorded hardware. Provisional engineering target: warm API p95 <=2 seconds for <=20 sequences and <=31 supported date candidates per sequence; timeout <=10 seconds with useful error. Reduce/precompute work if target missed; no performance claim without measurements.
- [ ] Install the exact demo release into a clean deployment path from versioned storage, verify hashes, disable network and reproduce comparison. Map tiles are optional; evidence and decisions must remain available without external tile/CDN services.
- [ ] README lists actually ingested products/versions, two supported districts, real methods, review gaps, source licenses and context-only roles. Include no nationwide support, guaranteed yields/soil benefits or village-scale observation claims.
- [ ] Commit reviewed code/data manifests/docs. Do not push until the owner requests publication for this implementation batch.

## Acceptance checklist and handoff

- [ ] Both region IDs resolve to reviewed geometry and actual validated product inventory.
- [ ] A real demo baseline and two supported alternatives share identical comparison rules.
- [ ] Farmer priorities and climate evidence demonstrably affect eligible-option comparison; unsupported priorities return unknown.
- [ ] Historical onset statistics, sensitivity, crop calendars and planting-date outputs retain their distinct meanings.
- [ ] Every listed NASA family has an acquisition/applicability result, even if no valid coverage or context-only; no fabricated raster is used for completeness.
- [ ] Native support, units, time, QA, shared ancestry, references and cache status remain inspectable.
- [ ] Missing crop review or insufficient observations reduce claims instead of generating certainty.
- [ ] UI explains a useful next step and all M3 writes require tested confirmation.
- [ ] Tests and real browser/data validation are reported separately with exact scope.

Recommended next implementation unit: Tasks 1–3 plus 6–9 for a complete POWER/IMERG-backed regional comparison. Add Task 4, then Task 5 without delaying the first usable comparison. Estimated effort is not reliable until pilot data access and agronomy review availability are established; those are the first implementation checks.
