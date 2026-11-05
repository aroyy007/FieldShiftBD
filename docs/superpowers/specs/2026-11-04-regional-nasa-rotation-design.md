# Regional NASA crop and rotation advisor — design

Date: 2026-11-04. Status: proposed design; no dataset ingestion or product implementation is claimed by this document. Owner request narrows the first release to Rajshahi and Chattogram, replacing the earlier nationwide acquisition target for this workstream.

## 1. Product decision

Build an explainable comparison of the farmer's current annual crop sequence and two locally documented alternatives. Show calendar fit, historical climate exposure, irrigation dependence, farmer constraints, and important unknowns. A one-crop request uses the same engine with a one-step sequence.

Choose a deterministic evidence engine before attempting calibrated yield simulation. Alternatives considered: (a) an LLM generating recommendations from retrieved documents, which cannot supply auditable calculations; (b) a fully calibrated AquaCrop/APSIM system, which needs cultivar, soil, management, and validation inputs we do not yet hold; (c) the selected staged engine, which produces useful comparisons now and allows a calibrated simulator later. These are design recommendations, not decisions already approved by the owner.

Do not force every NASA product into every crop score. Integrate all researched families into acquisition/provenance/inventory, but permit `not_applicable`, `no_coverage`, and `context_only`. GEDI and GRACE cannot honestly become field crop performance measurements.

## 2. Current code and required changes

| Existing component | Current behavior | Proposed change |
|---|---|---|
| `backend/app/services/climate/power_history.py` | POWER point acquisition and daily cache | Keep provider; extend optional meteorological variables in a separate v2 representation |
| `backend/app/services/climate/parquet_codec.py` | Strict daily table: rain, T2M, solar | Preserve v1; create a multi-source feature format rather than squeezing rasters into this table |
| `backend/app/services/climate/district_publish.py` | Content-addressed point-cache publication | Reuse checksum/atomic-publication pattern for regional releases; do not relabel points as district means |
| `backend/src/compute/agro.py` | Onset, GDD, annual comparison, sensitivity | Reuse with explicit input/method compatibility; add separate exposure/calendar/water modules |
| `backend/app/services/rotation_comparison.py` | Two BRRI examples gated on farm scope; NASA is context | Retain as v1 fallback; add v2 baseline and candidate evaluation |
| `backend/app/contracts/challenge/v1.py` | Strict literals, two-alternative availability validator, selection disabled | Add independent v2 types and endpoints; do not silently change v1 semantics |
| `backend/app/api/routes_m2_advisor.py` | Owned-farm comparisons and planting-window API | Delegate new orchestration to a service through a separate route module |
| `frontend/src/components/RotationComparisonCard.tsx` | Examples, history, calendar gaps, climate context | Add v2 comparison UI, preserve fallback display |
| `backend/app/services/profile_intake/snapshot.py` | Authenticated farm/history snapshot | Reuse ownership and stable snapshot inputs |
| `backend/app/services/actions/coordinator.py`, `operational_actions/task_diff.py` | Confirmed-action foundation | Integrate a separately implemented season-plan action; comparison itself remains read-only |

At inspection time, existing historical POWER is reference-point coverage, not regional raster coverage. No IMERG/SMAP/ECOSTRESS/NDVI/Landsat/GRACE/SRTM/GEDI runtime pipeline exists. Documentation and source registration do not count as ingestion.

## 3. Geography and supported questions

- Canonical district IDs: Rajshahi `5081`, Chattogram `2015`, from M1. Aliases such as Chittagong resolve to `2015`.
- Scope is these two districts, not their divisions and not all Chittagong Hill Tracts. District polygons, publication date, source/license, and hash must be selected and recorded before area-based publication. A point cache can still be displayed while geometry is pending.
- A farmer pin selects a supporting analysis cell. With district-only input, return district cropland summaries and their spatial variability, never an arbitrary centroid as the farmer's field.
- Rajshahi questions: dry-season irrigation dependence, rainfall variability, hot periods, and feasible turnaround between wet-season rice and dry-season crops.
- Chattogram questions: heavy rainfall exposure, drainage/land type, terrain variability, and cloud-limited vegetation evidence. Soil and irrigation-water salinity need local measurements or published maps; none of the listed satellites directly measures the farm's salinity or soil nitrogen.
- Farmer profile: field/pin or district, area, land/soil type with provenance, irrigation source/reliability, previous/current crops and dates, budget/labor constraints, preferred crops, and ordered priorities. Unknown values stay unknown.
- Initial comparison horizon: one complete agricultural year, represented by real dates crossing year boundaries; longer rotations become a later feature. An incomplete current season is not invented into an annual baseline.

## 4. Dataset roles and product decisions

Full product/version, access, QA and citation investigation: `docs/research/2026-11-04-nasa-agriculture-product-research.md`. Versions are acquisition pins, not a reason to assume the newest release shares an older schema.

| Family / first product candidate | Data and support | Rotation use | Prohibited inference |
|---|---|---|---|
| POWER Daily Point/Regional | Daily meteorology; standard met grid 0.5° × 0.625°, solar 1° | Long-term onset, thermal exposure, GDD; reference ET only with adequate inputs | Village climate accuracy or future forecast from historical observations |
| GPM IMERG Final `GPM_3IMERGDF` V07 | Daily precipitation, 0.1°; inspect variable units and actual granules | Stage/date-window rainfall and dry spells, upper-tail rainfall exposure, compare against POWER | Independent confirmation when sources share upstream products; flood-depth prediction |
| SMAP `SPL3SMP_E` plus optional `SPL4SMGP` | Enhanced surface wetness grid 9 km; L4 9 km/3-hour modeled surface/root-zone states | Surface wetness anomalies; optional modeled root-zone context | 9 km posting equals 9 km independent radiometer resolution; direct field workability or irrigation prescription |
| MODIS `MOD13Q1.061` | 250 m nominal, 16-day NDVI/EVI composites | Regional seasonal vegetation envelope and greenness gaps | Crop identity, exact transplant dates, measured bare soil, or a daily interpolated observation |
| Landsat 8/9 Collection 2 L2 Tier 1 SR | 30 m reflectance; 16-day individual orbit/8-day combined opportunity before clouds | Finer crop/vegetation context, heterogeneity, clear-scene cross-check | Every small field resolved; NDVI detects a specific disease or proves crop identity |
| ECOSTRESS `ECO_L2T_LSTE` V003, optional `ECO_L3T_JET` V002 | Approximately 70 m, irregular clear-sky overpasses; LST and separately modeled ET | Acquisition-time surface-temperature anomalies, ET plausibility checks | LST equals 2 m air temperature, or sparse ET gives daily irrigation requirements |
| GRACE/GRACE-FO JPL mascons | Monthly total water-storage anomaly; sampled grid is finer than its several-hundred-km support | Regional long-term water context and an explanation of groundwater reliance | Rajshahi-district groundwater volume, farm water table, or ranking adjacent farms |
| SRTMGL1 V003 | ~30 m posting, February 2000 radar-derived elevation | Derive slope at native grid, summarize terrain; contextual erosion exposure | Measured erosion, modern drainage/flood inundation, or bare-earth accuracy everywhere |
| GEDI L4A Version 3 candidate | ~25 m lidar footprints, sampled woody above-ground biomass density with uncertainty | Tree/agroforestry contextual panel when woody cover and valid footprints exist | Annual rice/pulse biomass, soil organic carbon or crop-rotation carbon sequestration |

Core computation uses POWER + IMERG + reviewed crop evidence. SMAP/MODIS/SRTM enrich the first regional release. Landsat and ECOSTRESS strengthen spatial/heat evidence where valid scenes exist. GRACE remains regional context; GEDI is conditional agroforestry context. Every acquired asset appears with its actual status, including exclusion reasons.

## 5. Common grid without false precision

Use `bd-ea-1km-v1`: EPSG:6933 equal-area, 1,000 m square cells, origin `(0,0)` in projected meters; row/column use mathematical floor for negative coordinates. Retain WGS84 API geometry and exact transform. Select intersecting cells from the two district polygons; include enough source halo to obtain full source-cell support and terrain derivatives. A cropped acquisition rectangle is not the administrative boundary.

The 1 km grid is a join/visualization grid. It does not upgrade coarse observations to 1 km measurements. Each layer retains `native_grid`, `effective_support`, `source_support_id`, pixel overlap weights and provenance. Adjacent cells sharing a SMAP, IMERG, POWER, or GRACE support unit are not independent samples. Aggregate duplicate supports before spatial uncertainty calculations. GRACE is associated regionally rather than painted as independent 1 km groundwater pixels.

Processing rules:

1. Decode units, valid ranges, scale/offset, fill values and bitmask QA **before** any interpolation or aggregation.
2. Fine continuous layers: compute NDVI from valid scaled Landsat red/NIR per scene; area-weighted valid-pixel mean and quantiles to 1 km. Native per-pixel NDVI then mean is the defined method; do not silently swap for NDVI of mean reflectances. Preserve valid crop-covered fraction and sampling date.
3. SRTM: derive slope in a metric projection at native terrain resolution with a halo, then summarize median/P90 slope. Slope of an averaged 1 km DEM would erase hills.
4. Categorical masks: nearest/mode or fractional class cover; never bilinear soil/land-cover classes. Version crop-mask year and uncertainty separately. Do not infer the mask from NDVI alone.
5. Coarse intensive layers (SMAP volumetric moisture, IMERG mm/day, POWER): conservative overlap-weighted mean to target cells; retain all contributing source IDs. Do not sum depths over space; rainfall volume is a separately derived quantity with cell area.
6. GRACE: one valid regional time series with provider uncertainty/leakage caveats; no district contrast from a single coarse support. GEDI: footprint-to-cell join and count/SE summaries; no continuous biomass interpolation from sparse footprints.
7. Raster viewing may use bilinear rendering for continuous maps, but computations use the published feature method and include it in output metadata.

Temporal alignment:

- Daily climate: UTC days, matching existing POWER history. IMERG half-hourly rates, if used, integrate `mm/h × 0.5h`; daily products must follow actual variable units. A day with missing intervals is incomplete, not zero rain.
- SMAP: preserve overpass or 3-hour timestamp. Daily summaries record sample count and QA; do not label model-filled L4 as a direct measurement.
- MODIS: retain composite start/end and valid observation/quality metadata; overlapping composites do not become independent daily samples.
- Landsat/ECOSTRESS: acquisition-time observations with cloud-gap status; group ECOSTRESS comparisons by local-solar-time/day-night class to avoid treating diurnal sampling as climate change.
- GRACE: monthly, no invented daily values. SRTM: static epoch. GEDI: actual footprint timestamp and measurement epoch.
- Seasonal summaries use crop/stage calendar overlaps, not a uniform monthly mean for all crops.

## 6. Analysis periods, QA and access

Separate products by their real records: POWER and IMERG historical analysis target 2001–2025; MODIS the same years where valid. Landsat 8/9 target 2013–2025. SMAP target 2015–2025; ECOSTRESS target 2018–2025; GEDI available footprints from 2019 onward; GRACE actual available months from 2002 onward, preserving mission gaps. Version-specific start dates and gaps come from catalog/granule discovery and must override these target requests.

Do not trim all history to a short common interval just to include every instrument. Report sample periods per metric. Direct POWER–IMERG comparisons use matched valid dates/support; evaluate source disagreement rather than average away bias. L4 SMAP precipitation forcing can share IMERG ancestry, so it is not a third independent rainfall vote.

Initial operational QA policy, explicitly FieldShift policy rather than NASA-certified thresholds:

- Historical daily season metric requires >=90% valid days; dry-spell metrics require complete windows. At least 10 valid annual seasons for a primary historical summary; otherwise partial/insufficient.
- Existing 2001–2012 versus 2013–2025 onset analysis retains its current denominator and definition. Add year counts, effect magnitude, sensitivity and year-block resampling; a p-value does not prove planting suitability.
- Optical cell-season summary requires >=50% valid cropland-area support in at least three independent composites/scenes; show support counts. Test 30/50/70% area coverage sensitivity. These gates require review against actual scene availability before release.
- Current-observation mode, if later enabled: moisture older than 7 days and optical/thermal scene older than 32 days is labeled stale by configurable application policy. Historical baseline assets are not expired solely because they describe 2025; integrity and release/version supersession are separate.
- No root-zone wetness threshold, stage heat threshold, minimum turn-around time or crop-specific GDD target enters a farmer recommendation without a source/scope/review record.
- Known product advisories must be checked and stored at acquisition. Do not assume one SMAP reprocessing notice applies identically to every product family/version.

Use official CMR/Earthdata search, `earthaccess` and product-native/subsetting services; USGS STAC/download access for Landsat where available. AppEEARS/Harmony are conditional on exact supported collection; no blanket support assumption. Earth Engine may be an optional acquisition backend with project/auth and current terms checked; it is not required for farmer requests. Do not scrape NASA raster files through HTML extractors. Government agronomy pages/PDFs may be collected separately with claim-level citations and reuse review.

Credentials are backend acquisition secrets, never frontend values, repo content or cache metadata. This planning task neither uses nor validates the credentials previously pasted in chat. Discovery/download may proceed during implementation using appropriately provisioned runtime secrets.

## 7. Rotation evaluation

### Candidate construction and evidence

Use the same `RotationOptionV2` for the current sequence and alternatives, with `role=baseline|alternative`. Current incomplete history gets `baseline_completeness=incomplete` and no invented fallow period. Retain baseline even when it violates a constraint so farmers can see the reason; it cannot be recommended as feasible.

Enumerate only documented regional candidate sequences with reviewed date windows, crop/variety duration basis, soil/land/irrigation requirements and crop-family traits. Intended crop pool: Aman rice, Boro rice, wheat, mustard, mungbean, and a locally documented pulse/vegetable option; each entry remains disabled in a region until evidence permits it. Do not promote three rice seasons as three different rotation strategies.

Research candidates to investigate, **not approved presets**:

- Rajshahi: farmer baseline; Aman–wheat–mungbean; Aman–mustard/pulse–fallow or another locally documented sequence after exact calendar and water checks.
- Chattogram: farmer baseline; Aman–a documented Rabi pulse/oilseed/vegetable–fallow; irrigated Boro–fallow–Aman where land, drainage, water and local evidence fit. Greater Chittagong-region and southwestern-coastal findings cannot authorize every Chattogram farm.

If fewer than two alternatives qualify, return fewer with explicit rejection/missing reasons. Never pad with unsafe or geographically unsupported options merely to satisfy a demo count. A completed demo needs a deliberately selected source-supported farm scenario with a real baseline plus two qualified alternatives.

### Deterministic stages

1. **Eligibility:** geography, crop duration/dates, land/soil, water access, known salinity, budget/labor if supported cost data exist, and crop preferences/avoidances. Output `eligible`, `ineligible`, or `unknown`, with rule and source IDs. Missing salinity is a high-relevance unknown in coastal scope, not a universal prohibition.
2. **Calendar feasibility:** anchor sowing/transplanting/harvest events correctly; check overlap plus sourced turnaround intervals. Enumerate permissible dates within reviewed windows. GDD with Tmax/Tmin is not silently replaced by T2M or a different base.
3. **Replay historical years:** evaluate eligible dates against observed daily climate and stage windows. Produce valid-year count, median/interquartile range, adverse-year fraction and missing-year reasons. Describe fractions as historical frequencies, not forecast probabilities.
4. **Exposure features:** rainfall/longest complete dry spell; air-heat exposure if stage thresholds are reviewed; wetness anomalies as coarse context; seasonal vegetation continuity; bare-field exposure only when calendar/history plus reviewed cover assumptions support it; terrain exposure proxy. NDVI alone cannot establish bare soil because harvest, cloud, water and residue can look similar. Observed NDVI, SMAP and ECOSTRESS describe the land and management actually present at acquisition, not the outcome of an unplanted alternative; alternative-specific stress requires a reviewed response model or is left unknown. Source observations and counterfactual estimates stay separately typed.
5. **Water:** first compare supported irrigation-dependence categories. Compute FAO-56 reference ET only after acquiring Tmax/Tmin, humidity/dewpoint, wind with height, radiation and elevation. Optional `ETc=Kc×ETo` and daily root-zone balance require reviewed Kc, soil profile/field capacity/wilting point/root depth and management. Paddy rice needs a distinct ponding/percolation model. Until then do not display litres, irrigation dates or water-saving percentages. ECOSTRESS actual ET evaluates observed conditions, not the counterfactual ET of an unplanted crop.
6. **Tradeoff vector:** calendar fit; modeled/observed exposure; irrigation dependence; cover gap; crop-family repetition; legume presence; supported budget/labor/market metrics. Nitrogen fixation/residue are potential mechanisms with source/management conditions, not measured fertilizer savings or soil-carbon improvement.
7. **Preference ordering:** apply hard exclusions first; show the non-dominated eligible set on dimensions fully available to every compared option. Within it order lexicographically by farmer's ordered priorities, then calendar buffer, then stable ID; no hidden weighted “accuracy” number. Required-priority unknowns yield `ordering_status=insufficient_evidence`; show a factual comparison without claiming a winner. Tie means co-preferred, not a forced winner. Increasing water scarcity must be capable of changing the result through water constraints/categories; context-only GRACE must not change field ranking.
8. **Explanation:** every result statement links to a metric, rule, source or farmer assertion. LLM may translate/narrate these outputs, never choose numeric thresholds or fabricate scientific benefits.

Planting-window adjustment is a separate output: evaluate candidate dates inside the reviewed calendar and find a permitted window under the same constraints. Return shift relative to a specified farmer/reference window only when the same event is compared and the result is stable under parameter sensitivity. Otherwise `recommended_shift_days=null` with reason. The median change in rainfall onset is not automatically the planting shift.

## 8. API and module connections

New contract module `backend/app/contracts/challenge/v2.py`; existing v1 remains readable. New authenticated `POST /advisor/v2/farmlands/{farmland_id}/rotation-comparisons`, body `{planning_year, priorities, candidate_ids?, scenario?}`. Server loads owned snapshot; client cannot submit a different farmer's profile or unrestricted geometry. Response is transient by default; storing requires a separate explicit save action.

Response types:

- `RotationComparisonV2`: contract_version `2.0.0`, farmland_id, snapshot_hash, release_id, planning_year, requested/used priorities, baseline completeness, options, preferred_option_ids, ordering_status, limitations, generated_at.
- `RotationOptionV2`: role, source sequence, dated steps, eligibility and reasons, calendar result, metric vector, why/benefits/risks/unknowns, evidence_ids. An expected benefit is typed `modeled`, `source_reported` or `qualitative`; the type is visible.
- `FeatureEvidence`: source/product/version, variable/units, raw+processed asset IDs/checksums, native+effective support, common cell ID, transform, source-support IDs, valid sample/date range, aggregation and QA methods, review/version, cache state and exclusions.
- Status enums: option `eligible|ineligible|unknown`; metric `available|partial|missing|not_applicable`; comparison `available|partial|insufficient_evidence|unsupported_region`; ordering `ordered|tied|insufficient_evidence`. A missing optional GEDI footprint cannot make an ordinary rice comparison fail.
- Add `GET /advisor/v2/regions` for released dataset coverage and `GET /advisor/v2/evidence/{public_asset_id}` for allowlisted public metadata, never raw filesystem paths or private farm data. Comparison details remain authenticated. Rate-limit bounded `scenario` experiments.

M1 owns profile/history provenance; M4 owns acquisition/releases; M2 owns deterministic comparison; M3 owns confirmed seasons/tasks; M5 owns chat/action narration and confirmation; M6 contributes only confirmed disease history as context until reviewed pest-family rules exist. Comparison must not create tasks/problems or activate seasons. Implement a season-plan proposal through existing action coordination only after its explicit handler, idempotency and preconditions are ready; do not assume task-diff support already authorizes a new plan action.

## 9. Storage, release and runtime

Acquisition workers (Python 3.12) use a separate geo dependency group: earthaccess, xarray, rasterio/GDAL, pyproj, h5/netCDF readers, shapely and optionally dask. Pin a tested lock/image during implementation; do not invent unverified package versions. Current API requirements are deliberately small and lack these geo dependencies.

Raw provider assets are immutable with checksums; georasters use COG where suitable; long chunked arrays use Zarr only where it improves bounded regional workloads; cell/date feature tables use Parquet/GeoParquet. Default API reads precomputed regional Parquet and summary JSON, not full raster stacks. No mandatory PostGIS/GEE/serverless rewrite.

Proposed release layout: `backend/data/earth_observation/releases/<release_id>/{manifest.json,regions.json,features/,summaries/,tiles/}`. Raw assets live in ignored acquisition storage/object storage. Release manifest includes all product versions, processing code/config hash, region/mask hashes, units/time rules, QA, license/citation, row counts/size and failed sources. Publish atomically after validation, keep previous release, verify checksums on load and cache by release+snapshot+priorities+scenario.

Commit only allowed small deterministic demo subsets/derived features and manifests; larger public data uses versioned object storage with checksum download/bootstrap and offline packaging. GitHub/LFS download is not a substitute for deployment cache installation. Do not redistribute government captures, journals or model assets under the app's Apache license without checking their own terms.

## 10. Farmer UI

Flow: field profile → “পরের বছরে কী চাষ করব?” → choose priority and confirm current sequence → baseline + alternatives → compare water/calendar/risk → inspect evidence or change priorities → explicitly request a plan proposal.

Top text answers the farmer's question in one sentence; factual constraints precede technical charts. Each card shows calendar, why it fits/does not fit, main tradeoff, missing information and a next step. Example copy is **illustrative, no computed result claimed**: “সেচের নির্ভরতা কমানো আপনার অগ্রাধিকার। এই বিকল্পে সেচের চাহিদা তুলনামূলক কম হতে পারে; তবে মুগের স্থানীয় ক্যালেন্ডার নিশ্চিত করা দরকার।”

Expandable NASA evidence shows actual periods, grid scale, data age, source/cache and model-versus-observation label. Optional map switches rainfall/wetness/vegetation/terrain layers; no per-field green “safe” polygons from coarse NASA cells. Low bandwidth default uses summaries; maps load on request. Bangla/English string keys, existing font tokens and screen-reader labels apply. Weather forecasts, historical evidence and user-defined what-if changes occupy separately labeled views.

## 11. Research already done and limits of transfer

| Primary research / method | What it establishes for this design | What it does not establish |
|---|---|---|
| [Ali et al., 2021, Rajshahi rainfall/crop planning](https://journalajaar.com/index.php/AJAAR/article/view/307), DOI 10.9734/ajaar/2021/v16i430183 | Examines 1975–2019 rainfall, seasonal water deficit and crop planning; supports testing dry-season demand | A validated farm irrigation model or automatic planting shift |
| [Chaki et al., 2021, Field Crops Research](https://doi.org/10.1016/j.fcr.2021.108109) | Trials including Rajshahi compare rice–wheat systems and a mungbean intensification option; outcomes depend on environment/management | Guaranteed soil/N/water improvement on all farms. Publisher full text was blocked in this session; only accessible abstract/index evidence was used |
| [Shahidullah et al., Chittagong cropping systems](https://www.banglajol.info/index.php/BRJ/article/view/38199/25985), DOI 10.3329/brj.v21i2.38199 | A 2016 survey across 42 upazilas documents regional crop-pattern diversity, useful for a location-scoped catalog | Current calendar approval; the five-district study region is not Chattogram district and not Hill Tracts |
| [Nath et al., 2022, JAEID](https://www.jaeid.it/index.php/jaeid/article/view/11961), DOI 10.36253/jaeid-11961 | Landsat crop-pattern mapping in southeastern Chittagong demonstrates the value of ground-truth validation | Transferable FieldShift model accuracy; this project's observations/training data differ |
| [Krupnik et al., surface-water intensification study](https://doi.org/10.1016/j.landusepol.2016.10.001) | Connects geospatial evidence with water availability and field crop observations in southwestern Bangladesh | Direct validation for Rajshahi or Chattogram; full PMC access was blocked and only indexed abstract findings used |
| [Khan et al., 2024, PLOS Water](https://journals.plos.org/water/article?id=10.1371/journal.pwat.0000153) | Shows irrigation/salinity scenarios require river, field and simulation evidence in the south-central coast | NASA rainfall alone establishes safe coastal irrigation or a Chattogram-specific result |
| [FAO-56](https://www.fao.org/4/x0490e/x0490e00.htm) and [AquaCrop inputs](https://www.fao.org/aquacrop/overview/input-requirements/en/) | Supply transparent ET/soil-water methods and explicit calibration/input requirements | A ready-to-use calibrated model for our crop varieties and fields |

This research supports the architecture and candidate evidence collection, not a claim that FieldShift already validates yields, groundwater savings, carbon, nitrogen or erosion. Research-paper scope is recorded separately from human agronomy review.

## 12. Validation and release gates

Data: product scale/QA decoding, crop masks, CRS transforms, rainfall mass/area consistency, temporal completeness, source shared ancestry, release corruption, cross-boundary cells and ocean/coastal masking.

Science: known-answer onset/GDD/ET examples; calendar event semantics; missing days cannot shorten dry spells; cloudy NDVI cannot become bare soil; coarse cloned pixels cannot inflate N; LST cannot enter air-heat/GDD formulas; GEDI cannot enter annual-crop biomass; GRACE cannot become district groundwater.

Decision: common-year/common-metric comparisons; identical constraints for baseline and alternatives; priorities can change ordering; unknowns cannot improve scores; replay same inputs yields same hash/result; all option rejection reasons trace to evidence. Ablate NASA features and report which metrics/ordering change; zero ranking effect for context-only products is expected and disclosed.

External: compare available BMD/BAMIS station observations against gridded weather on matched dates; independent crop-calendar/field records for phenology; blinded agronomist review of cases; held-out years and geography when labels permit. Bootstrap uncertainty is on years/source supports, never duplicated 1 km cells. Report sample sizes and unvalidated components; choose any numeric performance acceptance target before seeing holdout results.

Release gates: two district manifests; at least one genuine baseline + two supported alternatives demo; NASA feature change visibly changes an appropriate comparison metric; no invented score; missing-source/offline flow; ownership and confirmation checks; Bangla/English phone-width walkthrough; current tests/typecheck/lint; reproducible release download and offline startup. If a dataset has no suitable coverage, show that fact rather than claim all nine are used in ranking.

## 13. Work order

1. Versioned contracts, region boundaries/masks and source registry.
2. POWER/IMERG + harmonization + crop/calendar constraints: first functional regional comparison.
3. SMAP/MODIS/SRTM: wetness, seasonal vegetation and terrain enrichment.
4. Landsat/ECOSTRESS + GRACE/GEDI conditional context: complete researched source coverage with truthful applicability.
5. Farmer comparison UI/API, preference ordering, evidence and validation; confirmed plan handoff only after action tests.

The eight instrument/data families are covered in design (Landsat and MODIS are separate product pipelines). Additional climate projections such as NEX-GDDP-CMIP6 are a later, separate scenario phase. A hotter/drier user slider in the initial version is labeled a sensitivity experiment, not NASA's future prediction.
