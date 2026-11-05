# Regional rotation implementation — first increment

Date: 2026-11-04. Workspace: Fieldshift. This is a partial implementation of the regional NASA plan, not completion of its twelve tasks. No GitHub push was performed.

## Delivered and connected

- Separate v2 Pydantic/TypeScript contracts and owned, read-only comparison API; existing v1 remains available.
- Rajshahi 5081 / Chattogram 2015 product and source inventory; existing validated POWER reference-point histories are connected.
- Baseline and published BRRI examples share an option representation. Actual crop/date steps, expected-harvest distinctions, review gaps and data-source details are visible in the Crop Advisor.
- Historical rainfall replay for dated recorded steps, complete-window/missing-day logic, calendar overlap/turnaround checks and a deterministic preference function. Eligible ordering is deliberately unavailable on today's unreviewed/dataless alternatives; a tested preference function is not evidence that runtime recommendations are calibrated.
- Common analysis-cell projection, area-weighted intensive-value aggregation with retained source IDs, checksum-addressed bounded Parquet release utilities, documented precipitation-unit conversion and Landsat scale/offset NDVI helper. These are processing primitives, not a published harmonized regional raster product.
- Public CMR discovery, credential-safe bounded sample downloader, explicit provider-EULA handoff and isolated geo-worker dependency pins/image recipe. Discovery is capped and its truncation flag is retained; it is not full-archive acquisition.

## Real data access

Public CMR queries succeeded for IMERG, SMAP surface and MODIS around two explicitly labeled pilot search rectangles during 2024-01-01–07. Reports under `backend/data/earth_observation/discovery-*.json` retain public granule IDs and URLs. The rectangles are not approved district geometry or field observations.

The supplied Earthdata credential was stored only in ignored `backend/.env`; it was not placed in source/report output. IMERG download returned HTTP 403 with `EULA Acceptance Failure`. After the owner reported approval, a retry still returned the same provider response. The CLI records `source_approval_required` and the official approval URL. MODIS sample access also failed; no protected granule was decoded or published in this increment. Do not claim protected-product availability or token validity solely from metadata discovery.

An initial unpinned geo-reader installation was rejected by pip hash verification. It was discarded; hash verification was not disabled. A pinned isolated installation succeeded for numpy 2.1.3, h5py 3.12.1, pyproj 3.7.0 and shapely 2.0.6. These are listed in `backend/requirements-geo.txt`, with no additional mandatory API dependency.

## Verification

- Existing baseline backend suite: 360 passed, 5 skipped.
- New focused regional suite: 21 passed with isolated geo dependencies. This includes synthetic/unavailable/stale source rejection, ownership/no-mutation, deterministic hashes, download/EULA behavior, checksums/path guards, calendar overlap, missing rainfall, preferences, coordinate projection and scale-factor examples.
- Complete backend suite after fixes: **381 passed, 5 skipped, 8 warnings** (90.23 s), Python 3.12 container. Warnings include existing library deprecations and a test-cache write warning. No skipped test is claimed as passing.
- Frontend: **42 passed**; TypeScript and Expo lint exit 0; web export succeeded.
- Browser: synthetic local account and two explicitly TEST ONLY fields; Rajshahi and Chattogram Crop Advisor load. Priority changes and planning year changes reload the comparison. Missing crop dates and unavailable sources are shown, and NASA POWER 2001–2025 reference-point provenance is expandable. Phone viewport 390×844 was inspected.
- New source/report token-pattern scan: 0 matches; `backend/.env` remains ignored.
- Browser screenshot: `docs/reviews/artifacts/2026-11-04-regional-comparison.jpg`.

## Independent review and fixes

A read-only fresh reviewer identified three issues, fixed in one pass:

1. POWER cache quality gate now rejects synthetic manifests and synthetic/stale/unavailable provenance; four reproducing parameterized tests failed before the fix and passed afterward.
2. UI now renders each crop/interval, expected-versus-recorded harvest and the matching rainfall step label. Presentation tests cover the dated labels and explicit missing dates.
3. Comparison refresh key now includes season identity, status and date corrections, in addition to explicit reload revision. Tests pin activation/date invalidation; the full operational season-confirmation flow was not exercised or newly implemented.

## Still open / next work

- Reconcile provider authorization on the same Earthdata account, acquire valid samples and inspect arrays/quality flags before any product ingestion claim.
- Select/license/check district geometry and a crop/land-cover mask; build coastal/ocean-aware area-based releases. Current inventory remains `boundary_required`.
- Implement product-specific raster/footprint decoders and publish actual multi-source features. The QA helpers are not full sensor pipelines; all non-POWER runtime product states remain `not_acquired`.
- Populate reviewed regional crop calendars, turnaround rules, cultivar GDD and irrigation comparisons. Runtime alternatives remain unknown or outside scope; there is no preferred rotation or automatic planting shift.
- Add qualified candidate scoring/explanations, source-specific uncertainty validation, saved comparisons and confirmed M3/M5 plan handoff when their evidence gates are met.

Resume from these open items rather than rebuilding delivered contracts/routes/utilities. No task-level claim that all of Task 1, 2, 3, etc. is finished is made.
