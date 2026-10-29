# FieldShift BD — NASA Planting Windows, Rotation Decisions and Bangla Mobile Delivery

**Revised:** 2026-10-29, Asia/Dhaka. **Status:** implementation plan; no feature is complete merely because it appears here.

**Authority:** the user's 2026-10-29 request makes the supplied organizer instructions and the complete final problem statement the required product scope. This document specializes [the canonical project plan](../../plan.md) without replacing the six owners or creating a seventh module. The [voice plan](2026-10-06-voice-first-bangla.md) supplies the detailed accessibility channel. Existing runtime contracts remain the compatibility baseline; additive contracts below must be recorded before implementation, rather than silently changing another owner's fields.

**Accepted follow-up:** the owner approved three linked additions after competitor research: a decision-driven field question, a rotation robustness envelope and conditional Plan B with farmer confirmation. The [adaptive-decision specification](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md) is the implementation detail for §15 and additional gates A01-A08. All original requirements below remain required; see the [complete plan index](README.md).

## 1. Source material and scope interpretation

Preserved organizer inputs:

1. [Brief and killer demo](references/2026-10-29-organizer/01-brief.png).
2. [48-hour schedule, pre-build and cut order](references/2026-10-29-organizer/02-48-hour-plan.png).
3. [Datasets, onset example and validity guidance](references/2026-10-29-organizer/03-data.png).
4. [Architecture diagram](references/2026-10-29-organizer/04-architecture.png).
5. [Build prompt](references/2026-10-29-organizer/05-build-prompt.png).
6. [Unedited final problem statement](references/2026-10-29-organizer/problem-statement.md), copied from the user's original file outside the repository.

The deliverable combines two connected decisions: **when to plant/transplant** and **which multi-season rotation to choose**. The organizer's rice planting-window example does not remove the final statement's rotation, soil-health, resource and uncertainty requirements. Although the original statement uses “may” for many considerations, the user has requested their inclusion: every consideration is mapped below to implementation and evidence. Alternative datasets phrased as “MODIS or VIIRS”, “Landsat/MODIS” or “SRTM or other elevation” can be satisfied by the chosen named product; each choice is documented. All other individually named source families have a scoped role in the full delivery.

**Full target:** all 64 Bangladesh districts, at least three source-supported crop/season profiles, current rotation plus at least two alternatives, all mapped functions, and an installable Android app. A crop/season profile is not automatically a distinct rotation strategy. Rice seasons such as Aman must not be inserted as duplicate M1 crop species; use the existing Rice crop and an explicit advisory season/variety profile.

**48-hour milestone:** the organizer schedule in §11 is a timed vertical slice after data preparation. The screenshot's fallback order is documented, but no scope cut is automatically authorized: a one-district/one-crop demo, missing SMAP or missing map is a partial milestone, not full completion. Unavailable scientific information is shown explicitly; missing evidence must be resolved or reported as a release gap, never fabricated to turn a checkbox green.

## 2. Product outcome and acceptance narrative

A farmer signs in, sees all saved farms and selects a farm to open its scoped chat. From chat or a visible advisory entry, they select a district and crop/season, review their saved soil/resources and state their priorities. The app states a short actionable planting/transplanting advisory in Bangla, shows the earlier/recent onset distributions and thermal evidence, compares three rotations and offers a sourced explanation. The farmer selects an option; only an explicit confirmed M2 action can create/update a season plan, and M3 owns resulting tasks/current stage. M5 speaks the same deterministic result and does not recalculate the science.

**Organizer demo:** Rajshahi → Aman rice → observed usable-rain onset shift since 2001 → two distributions → revised transplanting window → assumptions and sources → short Bangla explanation on a phone. The screenshot's “eleven days later” is illustrative, **not a target to hardcode**. Use the actual calculated sign and magnitude; report weak/no evidence if appropriate. No historical comparison establishes causation or guarantees next-season weather.

Acceptance requires a meaningful final sentence, not only a chart. When evidence is inadequate, the meaningful sentence explains what cannot be recommended and what field information the farmer should check. Farmer judgment and local expertise remain explicit.

The accepted extension makes that information request decision-driven: one safe answer that changes the supported feasible set, then an explanation of tested calendar/resource limits and a saved contingency. Updated evidence may propose a precise plan/task change; the farmer reviews it before a version-checked, idempotent M2/M3 transaction. A post-planting crop switch cannot rewrite actual history.

## 3. Actual starting point and integration constraints

Source-inspection baseline: commit `1077a06`; the 2026-10-28 review is [recorded here](../research/2026-10-28-challenge-readiness-review.md). Recheck the working tree before implementing.

| Reuse | Remaining work |
|---|---|
| Existing M1 password auth, owner-scoped farmland profiles, administrative fields, coordinates, soil/land type, irrigation, equipment and budget | Add missing rotation history, relevant soil measurements and farmer priorities through a documented M1-compatible contract |
| Existing M2 evidence gates, catalog, recommendation and season APIs | Source verified crop calendars/stages/tasks, implement planting-window/rotation logic; shipped knowledge does not yet enable season-plan generation/activation |
| Existing M3 tasks, problems, check-ins and operational state | Integrate confirmed plan output; prevent duplicate task generation and stale-season writes |
| Existing M4 NASA POWER/Open-Meteo adapters | Add long historical, satellite and climate-scenario ingestion/cache; existing 30-day history is insufficient |
| Existing M5 farm chat, API client, secure token storage and fallback path | Add Bangla outputs, advisory intent, typed result rendering and voice/confirmation integration |
| Existing M6 disease loop | Preserve healthy/uncertain/repeat behavior; reconcile its present automatic Problem write with the voice confirmation policy before changing it |
| Expo 57 / React Native 0.86 / FastAPI / SQLAlchemy / PostgreSQL / Alembic | Configure actual Android identity, release API URL, production runtime, cache bundles and real-phone verification |

Preserve all existing routes and field meanings. Do not replace the existing auth system, create a parallel farm store or move M3 ownership into the advisor. Reuse existing columns and JSON metadata only when semantics match; do not hide arbitrary schemas in unrelated fields. Persistent additions need an explicit schema/contract diff and forward/backward migration review. No migration or code change is performed by this planning update.

## 4. Responsibility and additive interfaces

| Owner | Planned responsibility | Interface and invariants |
|---|---|---|
| M1 | Farmer/farm context, previous rotation, measured soil properties, priorities/constraints | Existing profile plus additive `RotationHistoryInput`, measurement provenance and `FarmerPriorities`; tenant scoped, unknown differs from zero |
| M4 | Environmental source acquisition, QA, harmonization, district Parquet and map layers | Read-only `DistrictClimateBundle`; history, forecast, satellite observation and projection kept distinct; no call to M2 or M3 is required to build a district cache |
| M2 | Crop/variety/season rules, onset/GDD/window calculation, comparative statistics, rotation scenarios | Pure compute result → `PlantingWindowAdvisory` and `RotationComparison`; no operational writes on exploration |
| M3 | Active season state, confirmed task creation/changes, problems | Existing `SeasonPlan`/initial-task handoff; idempotent effects and current-season checks |
| M5 | Conversation, Bangla/English explanation, voice, proposed-action routing | Renders M2 facts and evidence IDs; cannot invent days, doses, yield or source claims; executes through the owning module |
| M6 | Disease evidence and disease-result lifecycle | May inform crop-family/problem constraints through existing M3 state; not the planting-window calculator |
| Frontend/shared infra | Mobile map, charts, evidence, audio, offline UI and deployment | Expo Router, React Native SVG/vector icons; no image icons, no imitation time/network status strip |

```text
POWER · IMERG · SMAP · NDVI + other scoped NASA layers + local agronomy
                 │ pre-event/source refresh (M4)
                 ▼
     versioned district Parquet + geometry + manifests
                 │ read-only DistrictClimateBundle
                 ▼
  backend/src/compute/agro.py (M2): onset · GDD · distributions · shift
                 │                  └── rotation comparison + uncertainty
                 ▼
       existing FastAPI app: GET /advisory
                 │
     ┌───────────┴─────────────────────────┐
     ▼                                     ▼
 district map + two-period charts   actionable Bangla/English sentence
     └──────────────────┬──────────────────┘
                        ▼
            assumptions + dataset citations
                        │ confirmed choice only
                        ▼
        existing M2 SeasonPlan → M3 tasks/state
                        └────────── M5 scoped chat + speech
```

The organizer's `src/compute/agro.py` lives under the existing **backend** (`backend/src/compute/agro.py`), not inside Expo's route directory or a new server. Package it normally and call it from a small M2 service adapter; pure functions have no HTTP, DB, network or audio side effects. Data download, normalization and rendering stay outside compute.

## 5. Data preparation, provenance and offline contract

### 5.1 Required source families

| ID | Source and fields | Role and coverage discipline |
|---|---|---|
| D01 | NASA POWER: daily rainfall, T2M, solar radiation; Tmin/Tmax and wind/humidity if required by a documented method | Backbone for 2001-2025 district onset/GDD. Pin actual parameter IDs/units (`PRECTOTCORR`, `T2M`, `ALLSKY_SFC_SW_DWN` after metadata verification). A district centroid is a representative grid point, not a district-wide mean or field observation |
| D02 | GPM IMERG precipitation | Spatial rainfall and extreme-precipitation comparisons; select run/version and consistent daily aggregation. Explain differences from POWER; never average inconsistent products without an evaluated method |
| D03 | SMAP soil moisture | Wetness anomaly and suitability context over its real available period from 2015 onward. Retrieval quality, water/flood contamination and coarse footprint matter; surface wetness is not a guaranteed workability/root-zone measurement |
| D04 | MODIS NDVI (chosen MODIS/VIIRS option; candidate MOD13Q1 collection 6.1) | QA-masked vegetation/green-up/season transition and bare-field proxies, 2001-2025 where valid; composite interval is not an exact transplanting date. If VIIRS is substituted, pin its period and cross-sensor harmonization |
| D05 | Landsat surface reflectance/temperature products | Finer land-cover, vegetation and stress context; mask cloud/shadow and document sampling limitations. Validate selected collection and coverage before computation |
| D06 | ECOSTRESS temperature/ET products | Plant heat/water-stress and evaporation/ET evidence over available acquisitions; retain observation times and retrieval/model limitations |
| D07 | GRACE and GRACE-FO water-storage anomalies | Long-term regional water-storage context and gaps; not district groundwater volume, well availability or field-level maps |
| D08 | SRTM elevation (chosen elevation option) | Slope/terrain/erosion susceptibility context; terrain alone cannot establish flood risk, infiltration or erosion rate |
| D09 | GEDI biomass/structure samples | Explicitly scoped biomass/agroforestry context where sample coverage exists; not annual-crop soil organic matter or universal crop biomass |
| D10 | NASA downscaled climate scenarios, e.g. NEX-GDDP-CMIP6 | Predictive-climate exploration required by organizer brief. Pin scenario, models, baseline, future period and bias/harmonization procedure; show ensemble spread. Projections and user “what-if” sliders are separate from observed 2001-2025 distributions and near-term forecasts |
| D11 | Local soil, BARC/BRRI/DAE crop/variety calendars, stage definitions, season tasks, water/forage/legume traits and market/resource information | Explainable local applicability through existing evidence policies; record exact source and claim. Do not label farmer-reported soil as lab tested, zoning as field fit, or unsourced economics as expected profit |
| D12 | District boundaries and crop/land-cover mask | Reuse M1 canonical district identifiers/aliases. Pin boundary/mask version, license, source, crop mask age and aggregation weights; mapping must not introduce a competing location catalog |

Every family above needs a working ingestion/normalization path and a tested role in the full release. Its actual applicability/coverage is returned per district. A genuine empty footprint is a documented unavailable signal, not zero and not a fabricated substitute. D01/D03/D04 pre-caches are required across all 64 districts over their available periods. Other rasters are clipped/aggregated before release; no full global archive or raw raster download in the APK. Release cache completeness is audited, with per-variable coverage and explicit gaps.

### 5.2 Cache schema and build procedure

- Store analytical files outside PostgreSQL: `backend/data/climate/<cache_version>/<district_code>/<dataset>.parquet`, with `manifest.json`, a coverage report and checksums. Commit the small manifests, algorithms, licenses and a reproducible download/refresh command. Host larger allowed artifacts as versioned release assets with hashes, not opaque untracked laptop files.
- Common columns: `district_code`, `source_product`, `source_version`, `variable`, `date_or_interval_start`, `interval_end`, `value`, `unit`, `quality_flag`, `valid_count`, `coverage_fraction`, `aggregation_method`, `native_grid_or_footprint`, `retrieval_id`. Preserve native observations separately when daily alignment would imply false precision.
- Manifest: provider/landing URL and request or asset IDs, retrieval/publication dates, actual temporal coverage, CRS/spatial/temporal resolution, scale/offset/fill value, license/attribution, boundary/mask version, transformations, source checksum, cache checksum and method/config version. Public metadata contains no tokens or farmer identifiers.
- D01 includes full calendars for 2001-01-01 through 2025-12-31 and explicit valid/missing flags; deduplicate requests for districts sharing grid cells, respect provider limits, retry with bounded backoff and checkpoint downloads.
- Freeze `2001-2012` and `2013-2025` as the organizer's primary comparison periods. Do not silently slide them forward with the current date. Later observations are a separately labeled update.
- Choose and persist the POWER daily time standard; distinguish UTC, local solar time and Asia/Dhaka civil days. Do not relabel a daily LST total as a measured Bangladesh midnight-to-midnight total.
- Harmonize district/crop-mask aggregates and analysis intervals with documented area weights, valid-pixel thresholds and quality masks. Rainfall totals, temperature means, NDVI composites and monthly storage anomalies need different aggregation rules. No nearest-neighbor upscaling can create field-scale precision.
- `OFFLINE=1` **forces cache reads** throughout the analytical process: no NASA, weather, LLM, geocoding, remote map tiles or implicit model downloads. Missing/corrupt data returns a typed cache error or explicit per-layer unavailability; never fall back to live data silently. Prove this with network-denied tests.
- Server cache-only mode is distinct from a disconnected phone. Bundle permitted compact district geometries and release summaries on-device and persist last-viewed results with source dates; full rotation recalculation offline requires a tested local implementation or precomputed supported scenarios. Queued writes are not described as completed.

## 6. Agronomic compute and statistical specification

### 6.1 Agronomic configuration

For each district/crop/variety/season, store source-backed calendar, nursery/sowing versus transplanting distinction, onset search window, rain threshold, wet-day definition, dry-spell rule, degree-day base, optional upper cap, thermal targets, photoperiod limits and evidence IDs. Agreement with an agronomically informed person, as requested in the organizer pre-build list, is recorded with date and scope; it does not replace source provenance or silently approve unrelated knowledge. Unknown values block the relevant numerical recommendation, rather than introducing universal rice defaults.

Bangladesh Aman photoperiod/variety behavior and nursery age must be considered before moving a transplanting date from a thermal calculation. A regional rain-onset change is not itself sufficient authorization to shift every crop calendar by the same number.

### 6.2 Usable-rain onset

Organizer demonstration parameters: rolling window 7 days, rainfall sum at least 20 mm, maximum dry spell 7 days. These are configurable demonstration settings pending local justification, not scientifically universal constants. Store a versioned definition and show it in both languages.

The screenshot example's comment and body do not fully agree: checking for any wet day in the next seven days does not establish “no dry spell longer than seven days”, and its loop can miss the last candidate window. Implement the stated agronomic definition correctly rather than reproducing that bug.

The implementation must:

1. Use a complete, ordered, dated series; reject duplicates/invalid negatives/fill values and preserve missing days.
2. Restrict candidate start dates to the source-backed crop-season search window, with sufficient trailing data even across year boundaries.
3. Require the configured rainfall total over the candidate window, and evaluate **consecutive** dry days in a declared post-onset verification horizon. Publish the horizon and whether “dry” means `<` or `<=` the wet-day threshold. No hidden choice of horizon.
4. Return the first valid onset date, with the candidate-window start explicitly defined as the convention, or a reason such as `no_onset`, `insufficient_data` or `truncated_verification`. Do not claim rain physically began on a dry first day of a summed window.
5. Distinguish a true no-onset year from missing/corrupt data. Report annual exclusions and no-onset counts; analyze their frequency separately so conditioning only on valid onsets does not hide drought years.
6. Repeat the entire annual detection and period comparison at rainfall thresholds **15, 20 and 25 mm** for the organizer's ±5 mm sensitivity requirement; report sign/magnitude/support changes. Keep 7-day window/dry-spell parameters explicit and add further justified sensitivity checks.

### 6.3 Growing-degree-day accumulation

Provide a deterministic function with a documented temperature method, planting/nursery/transplanting reference, base, cap and units. A supported daily-mean method is `daily_gdd = max(0, T2M - Tbase)`; if capped, use the precisely documented capped method consistently. An average-Tmin/Tmax method is a different version, not an interchangeable fallback. Aggregate in degree-Celsius days, never interpret Kelvin as Celsius.

Use crop-specific sourced base/target values. Missing days do not become zero thermal accumulation. Emit completeness flags or an explicitly labeled, validated imputation method. Compare annual cumulative curves and target-reaching dates between the same two periods. Document photoperiod/water effects and avoid treating GDD alone as a validated phenology model.

### 6.4 Two-period comparison and proposed shift

- One annual onset sample per district/crop/season/year; nominal maximum sample counts are 12 and 13, not thousands of daily pseudo-replicates.
- Express onset as day offset from a common season anchor so leap years and cross-year seasons are comparable. Retain actual dates/year labels for display.
- Return both annual distributions, counts, exclusions, medians, spread, effect size and an uncertainty interval, plus a two-sided **Mann-Whitney U** statistic/p-value and the pinned implementation/method. Handle ties using a documented suitable method. Tests verify the reported statistic orientation and method.
- Mann-Whitney tests distribution differences under assumptions; it does not by itself prove an eleven-day median shift or a climate cause. State independent-year assumptions; assess serial dependence and use a suitable blocked resampling sensitivity where relevant. Label small samples/weak evidence. When surveying many district/crop pairs, report the multiple-testing procedure and retain raw and adjusted values where used.
- Compute `observed_onset_shift_days = median(recent) - median(earlier)`, with **positive = later**. Keep the raw estimate and expose a whole-day display using one named rounding rule (ties away from zero). Do not mix date arithmetic with an undocumented rounding convention.
- Keep `observed_onset_shift_days` separate from `recommended_window_shift_days`. Derive a candidate window from the sourced existing calendar and onset/thermal constraints, then evaluate wetness, heat, flood/terrain context, photoperiod, irrigation, nursery needs, resources and rotation overlap. Return the rounded final recommendation only when supported. No feasible window → explain constraints; never silently clamp an infeasible date into an apparently safe recommendation.
- Fix a reproducible resampling seed/config. Return `supported`, `uncertain`, `insufficient_evidence` or `no_feasible_window` and the explanation. A p-value alone is never the advisory acceptance gate.

### 6.5 NDVI, soil moisture and model validation

Use crop-masked QA-filtered NDVI to evaluate whether predicted seasonal windows align with observed green-up/season transitions over available years. Farmers' actual planting dates require consented ground records; NDVI is a phenology proxy, not proof of an individual planting decision. Use year-based holdouts, report timing error/coverage and exclude validation leakage.

SMAP anomalies, ECOSTRESS ET/temperature, Landsat stress indicators and GRACE regional storage add scoped evidence/limitations. Soil workability needs local soil texture, drainage and field assessment; satellite surface moisture alone cannot establish it. Low NDVI is not uniquely a bare field, heat or disease.

Compare at least an existing-calendar baseline, rain-onset-only method and combined rain/thermal/local-constraint method. Report performance, uncertainty and failure cases; retain a simpler method if the richer method is not better validated. Define acceptance metrics and agronomically meaningful error tolerance before examining holdout results.

## 7. Full rotation and soil-health decision support

Build at least three **multi-season strategies** per supported farm: current rotation plus two locally evidenced alternatives. Calendar shifts of the same crop alone do not satisfy a meaningful three-rotation comparison. Ask for missing current rotation rather than inventing it. Include source-supported legume/cover/deep-rooting/drought-tolerant options where locally feasible, expanding M1's catalog through its owner.

Each strategy returns a common dated calendar, explanatory factors, applicability, unavailable evidence and tradeoffs for:

- Nutrient cycling and nitrogen-fixing potential; fixation potential is not an automatically known fertilizer credit.
- Soil cover, bare-field intervals, organic-matter contribution potential, infiltration and erosion susceptibility. No unmeasured soil-carbon or infiltration improvement percentages.
- Crop-family/pest-cycle considerations, informed by M3 open problems and sourced host relationships. No guaranteed disease prevention.
- Water demand/irrigation feasibility, historical heat/dry-spell/extreme-rain/frost exposure and climate-scenario sensitivity. For quantitative ET/water balance use a documented method such as FAO-56 with appropriate crop/soil inputs and paddy-specific losses where relevant.
- Forage value, equipment/labor access, water availability, budget and market suitability. Cite price/cost location/date and use ranges; without evidence give qualitative constraints rather than promised income.
- Farmer priorities: conserve water, improve soil structure, earn supplemental income, forage or preferred crops. Show how priority changes alter tradeoffs and exclusions; no opaque single score without factor explanations.

Historical observations, near-term forecasts and future climate scenarios appear as separate evidence modes. Future projections carry scenario/model/period uncertainty; sliders changing rain/temperature are labeled **what-if**, not a weather prediction. No scenario automatically mutates an active farm season or creates tasks.

## 8. HTTP and result contract

Add to the existing FastAPI application:

```text
GET /advisory?district=<canonical-code-or-supported-alias>&crop=<catalog-key>&season=<season-key>
```

The organizer's district/crop-only form must work: when season is omitted, use a single configured unambiguous profile, or return selectable profiles instead of guessing. Resolve `Aman rice` as Rice + Aman advisory profile. A successful numerical result includes:

| Field | Required meaning |
|---|---|
| `district`, `crop`, `season`, `method_version`, `cache_version`, `result_id` | Resolved canonical identity and reproducible result identity |
| `status`, `warnings`, `evidence_gaps` | Decision support/uncertainty, not just HTTP success |
| `observed_onset_shift_days_raw`, `observed_onset_shift_days`, `recommended_window_shift_days` | Signed estimate, whole-day display and distinct agronomic recommendation; unsupported values are null |
| `baseline_window`, `recommended_window`, `window_kind` | Sourced calendar, computed feasible dates and sowing/transplanting distinction |
| `periods` | Fixed earlier/recent ranges, annual onset samples, exclusions/no-onset counts, spread/medians; both chart-ready distributions |
| `thermal` | Base/cap/method, annual GDD curves or compact equivalent, target-reaching dates, completeness |
| `statistics` | Mann-Whitney U, p-value, method, effect size, uncertainty and assumptions |
| `sensitivity` | Full ±5 mm threshold results and stability assessment |
| `validation`, `environmental_evidence` | NDVI/SMAP and other source contributions, holdout metrics, missing coverage |
| `assumptions`, `provenance` | Every configurable agronomic/statistical assumption and dataset/source/license/hash block |
| `advice_bn`, `advice_en`, `speech_text_bn`, `sms_summary_bn`, `sms_summary_en` | Same supported facts, concise actionable sentence first, summaries strictly below 160 Unicode characters |

District-only results contain no private farm details and may be served as bounded public read-only cache results with request controls. Farm-specific rotation exploration uses an authenticated M2 endpoint such as `POST /advisor/farmlands/{id}/rotation-comparisons`, deriving farm ownership/context from saved M1 data. It returns three strategies and their referenced window results. Selecting a scenario uses existing/explicitly extended M2 write contracts with confirmation and idempotency; a public query cannot select a farmer's crop.

Errors: invalid identifiers/parameters → documented 422; ambiguous season → documented selectable response; missing source cache → 503 with a typed code; missing agronomic evidence → valid structured insufficient-evidence result with null numerical recommendation. Never return a fake zero-day shift or an HTML server error as an advisory. A missing supplemental layer may permit a qualified result only if the agreed minimum evidence still holds.

No actual SMS delivery is needed merely to satisfy “could be sent”. Implement copy/share/compose of the SMS-length summary with a confirmation before opening an external send action. Display Unicode character and estimated segment counts: a Bangla string under 160 characters is not necessarily one GSM SMS segment. Do not add a paid SMS gateway as a hidden dependency.

The authenticated rotation result also carries the adaptive specification's `next_question`, `robustness` and `contingency_evaluation` with server-resolved scope, revision tokens, source freshness and typed unavailable states. Its reevaluation interface never changes operational state. Confirmed execution uses the shared ProposedAction mechanism and transaction-aware owner operations, not sequential independently committing HTTP calls. Public district results contain none of these private farm policies/answers.

## 9. Mobile frontend, voice and visualization

- Preserve sign-in → all farms → selected farm chat; add district/crop advisory and rotation comparison within the existing navigation. District exploration can work without GPS; Use current location must not assume the phone is physically at the farm.
- Bangla default and English switch; localized dates/digits/units, readable type, balanced left/right gutters, accessible SVG/vector icons, no fake status bar. Test realistic widths 320/360/375/390/412/430 dp/CSS px, appropriate heights, large text, safe areas and keyboard behavior.
- Top result is **one clear action sentence**, followed by the revised/baseline planting or transplanting window and its support state. No chart-only dead end. Read it aloud and provide replay; do not speak raw statistical jargon by default.
- Interactive district map using bundled permitted district geometry, legend, selected district and accessible list fallback. Add dataset/time-layer controls for rainfall/moisture, heat/vegetation stress, terrain and regional storage at their actual resolution; do not portray GRACE as field detail.
- Two-period distribution chart with identical axes/bins or an ECDF, annual observations, sample/exclusion counts and uncertainty; add GDD accumulation comparison and threshold-sensitivity view. Respect seasonal anchors and leap-year labeling.
- Rotation timeline and side-by-side factors including bare periods, risks and priority changes. Show field vulnerability estimates only when local-resolution evidence supports them; otherwise explicitly label regional context and unassessed field risk.
- Evidence view shows onset definition, every assumption, dataset URLs/versions/period/scale and factual uncertainties. Plain-language glossary: evapotranspiration, soil moisture anomaly, NDVI, frost risk and water balance; distinguish satellite/reanalysis/ground observations and explain combining them.
- Scenario sliders for rain/temperature update labeled simulations while historical distributions remain unchanged; climate projections have distinct model/scenario controls.
- Android device STT/system TTS and recorded prompts follow the linked voice plan. Chrome responsive checks validate layout, charts and navigation; physical Android builds validate recognition, speech, microphone lifecycle, permissions and offline behavior.
- Screen-result state, spoken response and SMS derive from the same typed result. An LLM cannot choose a different shift, cite absent data or turn uncertain evidence into a confident action.
- Add one decision-question card with unknown/skip choices, accessible tested-feasibility ranges, and a contingency/diff confirmation view. Keep hypothetical answers distinct from confirmed saved M1 facts; stale/offline proposals cannot silently renew or execute after their approved values change. Details: adaptive specification §8 and voice flow F9.

## 10. Verification and release gates

No checkbox below is pre-completed. Each requires a fresh command/report or observed session, date, commit/cache/method versions and evidence path. Synthetic fixtures verify logic only and never become production agricultural advice.

| Gate | Required verification |
|---|---|
| V01 Data | 64 canonical districts, source manifests, cache hashes, duplicate/date/unit/fill/QA validation, honest source-family coverage and source-policy expiry |
| V02 Pure compute | Hand-calculated onset/GDD cases; inclusive last candidate; true consecutive dry spells; false onset; no onset; missing/negative values; trailing horizon; leap/cross-year dates; base/cap/units |
| V03 Statistics | Fixed 12/13-year periods; ties/constant/unequal/insufficient samples; all-no-onset case; seeded intervals; signed raw/rounded shifts; U orientation; annual independence limits and full 15/20/25 mm sensitivity |
| V04 Agronomy | Source-backed base/calendar/stages; sowing versus transplanting; photo/thermal limitations; impossible overlaps; irrigation constraints; weak evidence and no-feasible-window outputs; informed-person review recorded |
| V05 Source/model validity | Held-out NDVI/ground timing with coverage; baseline/rain-only/combined comparison; no leakage; supplemental-layer ablation changes evidence/confidence appropriately; NASA removal is visible |
| V06 API/contracts | GET `/advisory` fields/errors, aliases/season ambiguity, units/provenance, Unicode SMS <160, same facts in both languages; no GET operational writes |
| V07 Offline | `OFFLINE=1` with network denied; missing/corrupt caches; bundled map, no hidden tiles/LLM; disconnected phone last result/staleness; restart and queued-action semantics |
| V08 Farm isolation | Two farmers/two farms, unauthorized IDs, expired auth, duplicate confirm, stale season/action, session switch and correct crop/season in chat |
| V09 Existing lifecycle | Fresh DB import → signup → all farms → recommendation → plan activation → M3 tasks → M4 alert → M5 reply → M6 result/problem visible → harvest close/history |
| V10 Rotation | Current + two alternatives, nutrient/cover/pest/water/forage/market factors, priorities, missing data, infeasible options and overlap checks; exploration never starts a season |
| V11 Browser | Chrome standard mobile viewport matrix, map/chart interactions, Bangla fonts/text scaling, equal gutters, permission denial and provider failures with screenshots |
| V12 Native | Signed APK on actual low-end Android: install/update/cold start, mic/TTS unavailable/denied, background stop, interruptions, weak/offline data and source-dated cached result |
| V13 Usability | At least one person outside the team completes district/crop selection and explains the advisory; report actual sample/task results and failure cases. Wider dialect/pilot study remains separately reported |
| V14 Production | HTTPS URL from phone on mobile data, no localhost dependency, release signing, no dev reload/public trust DB, protected secrets, backup/restore, bounded resources/latency and service-outage behavior |
| V15 Submission | Apache-2.0 for original project code, retained upstream notices, per-dataset/model licenses, public accessible repo, dataset URLs in README, completed NASA page, exact challenge title/category, recorded demo and real teamwork evidence |

Run existing appropriate backend unit/contract/integration suites against a clean PostgreSQL test database and add meaningful compute/API/rotation tests. Run Expo lint/typecheck and browser/native checks for changed functionality. Never equate mocked services, an existing test count or a responsive browser with a validated release.

The accepted follow-up additionally requires [A01-A08](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md): question impact, non-monotonic envelopes, dated trigger handling, schema compatibility, transactional race/crash/retry correctness, existing lifecycle regressions, actual browser/native/offline use and measured decision value. These gates are planned and unverified.

## 11. Organizer schedule and full delivery sequence

### 11.1 Pre-event work (must be disclosed in submission)

- [ ] Preserve inputs and record the requirement matrix; finalize additive contracts with affected owners.
- [ ] Cache POWER, NDVI and SMAP for every district, all other scoped data families and permitted geometry; verify download script/manifests and offline bundle.
- [ ] Source/record crop calendars, degree-day bases, onset/search/verification definitions and local agronomic agreement; support at least three crop/season profiles and suitable rotation alternatives.
- [ ] Draft Bangla/English strings, glossary, short advisory/SMS templates and recorded core prompts.
- [ ] Prove actual native build/device speech path, release host capacity and existing M1-M6 baseline. Resolve the season-plan knowledge blocker.

### 11.2 48-hour organizer milestone

| Organizer slot | Deliverable | Evidence |
|---|---|---|
| Day 1 morning | Onset, GDD and shift-test implementation in `backend/src/compute/agro.py`, including sensitivity and tests | V02/V03 hand-calculated cases and green test output |
| Day 1 afternoon | District map, crop/season selection and 2001-2012 vs 2013-2025 distribution comparison | Working `/advisory` and mobile screenshots |
| Day 1 evening | Actionable advisory sentence, revised window, assumptions/sources; record by **18:30 local event time** | Recorded Rajshahi/Aman result using measured values |
| Day 2 morning | Bangla/English interface, phone layout, <160-character summaries; test with a person outside the team | Usability observations and browser + phone checks |
| Day 2 noon | Freeze, record and submit that milestone | Pinned commit/cache, working repo/page and demo |

The organizer's 18:30 and noon are event checkpoints, not dates inferred from the current clock. Full multi-source, rotation, field-validation and production scope may exceed this milestone; keep its gates open and report status accurately.

### 11.3 Full completion sequence

1. **Foundation:** pre-event cache/knowledge/native prerequisites, source licensing, contracts and clean lifecycle (V01/V04/V08/V09).
2. **Planting-window science:** pure onset/GDD, period comparison, Mann-Whitney, sensitivity, validated candidate window and HTTP result (V02-V06).
3. **Challenge depth:** source harmonization, all scoped layers, predictive-climate exploration, held-out comparisons and three rotation strategies (V05/V10).
4. **Farmer delivery:** mobile map/charts, assumptions/glossary, Bangla/English sentence/SMS, device speech and offline behavior (V07/V11-V13).
5. **Accepted adaptive decisions:** after the required flow works, complete question selection → robustness analysis → policy preview → atomic confirmed Plan B → mobile/voice/offline integration. Follow adaptive increments D1-D5 and gates A01-A08; no substitute for the required science/rotation flow.
6. **Production/submission:** measured host/device performance, bounded policy refresh/delivery and outage handling, clean deployment, license/attribution, contribution evidence, video and public project page (V14/V15 and adaptive D6).

Suggested organizer fallback order, **only if a later explicit scope decision is made**: one crop instead of three → one district told properly → drop SMAP while retaining rainfall/temperature → drop map while retaining the advisory. This is not the acceptance definition for the user's full request.

## 12. Cost, licenses and deployment

Original project code is planned for **Apache-2.0**, as organizer specifies. Add the root license/NOTICE and preserve `frontend/LICENSE` and other upstream MIT/license notices. Source screenshots, datasets and model weights are not automatically relicensed by the application license. Inventory all dependencies/artifacts; replace or separately permission any noncommercial/restricted model before claiming the full distribution is commercial compatible. The current M6 weights are CC-BY-NC-4.0 and require an explicit release decision.

Use free/open tools for computation and development: Python, NumPy/SciPy, Parquet tooling, existing FastAPI/PostgreSQL, Expo/React Native and SVG. No paid speech, SMS or LLM service is required for the deterministic advisory; optional providers must fail gracefully. Select a measured hosting arrangement, durable artifacts/database, HTTPS, secure deployment variables and a tested backup restore. A free tier or donated team machine may support a bounded pilot, not a promise of indefinitely free reliable production.

Keep service terms separate from open-data licenses. Open-Meteo free hosted access is noncommercial and quota limited. Store distribution fees, Android verification changes, native build constraints and free-host sleeping/retention limitations are detailed in the [feasibility review](../research/2026-10-28-free-mobile-voice-feasibility.md). Direct APK release can serve a supported pilot; do not label a development Expo web server as a deployed mobile application.

## 13. Requirement traceability

All rows are **planned, not verified** until their gates pass. Full statement considerations are included because the user requested complete coverage, without misrepresenting their original optional wording as an organizer mandate.

| ID | Source requirement | Plan sections / acceptance evidence |
|---|---|---|
| O01 | Satellite observations + predictive climate → farmer adaptation | §5 D01-D10, §6-7; V01/V05/V10 |
| O02 | Bangladesh district/crop rice planting-window tool; 25 years; shift in days | §1-2, §6, §8; V02-V06 |
| O03 | Rajshahi/Aman, two distributions, revised transplanting window, Bangla phone | §2/§9/§11; V06/V11-V13; example 11 is never fabricated |
| O04 | POWER daily rain, temperature, solar; IMERG spatial rainfall | §5 D01/D02, §6; V01/V05 |
| O05 | SMAP + MODIS or VIIRS NDVI; every-district pre-cache | §5 D03/D04/§5.2, §6.5; V01/V05/V07 |
| O06 | Agreed onset and crop-specific degree-day base/calendar | §6.1-6.3/§11.1; V04 |
| O07 | `src/compute/agro.py`, onset/GDD/shift, each function tested | §4/§6; V02/V03 |
| O08 | Explicit onset definition, consecutive dry-spell check and stable thresholds | §6.2; V02/V03; correct example-code inconsistencies |
| O09 | 2001-2012 vs 2013-2025, Mann-Whitney U, whole-day shift, ±5 mm | §6.4/§8; V03/V06 |
| O10 | Parquet per district, pre-event pipeline, `OFFLINE=1` cache only | §4/§5.2; V01/V07 |
| O11 | FastAPI GET `/advisory?district=&crop=`, distributions/statistic/assumptions/provenance | §8; V06 |
| O12 | District map, charts, one actionable sentence at top, Bangla + English phone UI | §9; V11-V13 |
| O13 | SMS summary strictly under 160 characters, sendable output | §8/§9; V06/V11 |
| O14 | Every assumption and onset definition visible, dataset citations | §5-6/§8-9; V01/V06/V11 |
| O15 | Apache-2.0, public repo, README with each dataset URL | §12; V15 |
| O16 | All 48-hour slots, pre-build, 18:30 recording, outside-team test, freeze/submit and cut order | §11; V13/V15; cuts require explicit scope decision |
| P01 | NASA + local soil + crop traits + farmer priorities | §4-5/§7; V01/V10 |
| P02 | Temperature/heat, rain/extremes, moisture, evaporation, frost, vegetation stress and long-term water | §5 D01-D10/§6-7/§9; V05/V10/V11 |
| P03 | All named dataset families: SMAP, ECOSTRESS, GPM, Landsat, MODIS, POWER, GRACE/FO, elevation, GEDI | §5 D01-D09 and source applicability; V01/V05 |
| P04 | Crop vulnerability, seasonal transitions and bare-field periods | §6.5/§7/§9; V05/V10 |
| P05 | Three rotations including current; rationale/benefits/gaps/risks | §7-8; V10 |
| P06 | Nutrient cycling, erosion, organic matter, pests, water, forage and market | §7; V04/V10 |
| P07 | Nitrogen-fixing, cover, deep-rooting and drought-tolerant explanations | §7/§9; V04/V10/V13 |
| P08 | Compare modeling/statistical approaches, uncertainty and expert judgment | §6.1/§6.4-6.5; V03-V05 |
| P09 | Harmonize spatial/temporal grids and resolutions | §5.2; V01/V05 |
| P10 | Maps over time and local vulnerability with honest resolution | §5/§9; V05/V11 |
| P11 | Timelines, dataset overlays and rainfall/temperature scenario sliders | §7/§9; V10/V11 |
| P12 | Explain ET, anomalies, NDVI, frost, water balance and ground vs satellite observations | §9; V11/V13 |
| P13 | Farmer input: water, equipment, markets, priorities; limited technical literacy | §4/§7/§9; V10/V13 |
| P14 | Supports farmer judgment/local expertise; no unsupported guaranteed outcomes | §2/§6-9; V04/V05/V13 |
| J01 | Provided scoring: validity, relevance, presentation, teamwork, UX, NASA use | §10-11 and demo; V05/V11-V13/V15 |
| J02 | Exact challenge category/title, public repository, completed official project page | §10-11; V15; verify event rules, do not invent missing image criteria |
| F01 | Owner-accepted decision-driven field question after competitor review | §15; adaptive §§3-4/§8; A01/A04/A06-A08 |
| F02 | Owner-accepted robustness envelope with binding constraints | §15; adaptive §5; A02/A04/A06-A08 |
| F03 | Owner-accepted saved contingency and farmer-confirmed Plan B | §15; adaptive §§6-9; A03-A08 |

## 14. Scientific and technical references

The organizer screenshots/final statement are requirements; these primary sources justify implementation details. Pin selected product versions, current terms and locally applicable agronomic sources during data preparation.

- [Official challenge](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).
- [NASA POWER daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) — metadata, time standards, source-resolution and request limits; [meteorological sources](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/).
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg).
- [NASA SMAP mission](https://science.nasa.gov/mission/smap/) — 2015 launch; [science operations](https://www.nasa.gov/news-release/nasa-soil-moisture-mission-begins-science-operations/).
- [NASA MOD13Q1](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1/) — product/collection and 16-day composite support.
- [NASA ECOSTRESS](https://ecostress.jpl.nasa.gov/), [Landsat](https://landsat.gsfc.nasa.gov/), [GRACE](https://grace.jpl.nasa.gov/), [SRTM](https://www.earthdata.nasa.gov/data/instruments/srtm), [GEDI](https://gedi.umd.edu/) — select concrete product IDs, quality flags and valid periods, not a generic NASA label.
- [NASA NEX-GDDP-CMIP6](https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/) — future scenario products and scale.
- [SciPy Mann-Whitney U](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html) — independent samples, statistic and ties/method handling.
- [FAO-56](https://www.fao.org/4/x0490e/x0490e00.htm) — crop water requirements and explicit assumptions.
- [Expo speech-recognition maintainer](https://github.com/jamsch/expo-speech-recognition) — native builds and platform capabilities; see linked voice plan for full device testing.

## 15. Accepted adaptive-decision extension

The full implementation specification is [Adaptive Decisions and Confirmed Plan B](2026-10-29-adaptive-decisions-and-confirmed-plan-b.md). It adds three linked behaviors only: ask an observable question that changes a supported choice, calculate bounded calendar/resource feasibility under declared scenarios, and maintain a supported contingency whose exact plan/task changes require fresh farmer confirmation. Its source-review inspiration is recorded without claiming global novelty.

M1 owns confirmed facts; M2 owns analytical results, rules, plan definitions and policies; M4 owns dated evidence; M3 owns operational state; M5 owns presentation/confirmation orchestration. A policy evaluation alone cannot change crop/season/task records. Required extensions include immutable result/version IDs, explicit evidence freshness, a single ProposedAction path, atomic owner operations with replay receipts and post-commit delivery recovery. Additive migrations need the exact shared-contract/DB diff before code; this plan does not modify the schema.

Complete the core organizer/final-statement flow first, then this extension before claiming the accepted full release. An initial milestone may omit it only when reported as incomplete. Broader multi-farm rice allocation, pump coordination and outcome research remain deferred suggestions. No paid reasoning API is required, and no unsupported agronomic rule or benefit percentage can be introduced to make the feature appear complete.
