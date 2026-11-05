# Real satellite file: local prototype and QA

The owner supplied one IMERG daily granule (two byte-identical copies), two SRTM zip tiles and one MOD13Q1 HDF4 file. Originals were copied into ignored `backend/data/earth_observation/raw/`; no file was downloaded or transmitted by the app. The copies' origin is user-supplied and has not been independently authenticated.

## IMERG

The file matches the discovered granule name and decodes as IMERG V07B: `precipitation` and `precipitation_cnt` use time/lon/lat dimensions, daily mean rate units `mm/day`, and the time bounds cover 2024-01-01 UTC. The prototype requires all 48 valid half-hourly observations for a native cell. Actual 0 mm is retained as valid, and 0–47 counts are excluded. Pilot rectangles are search boxes, not verified district boundaries or farm plots. Their equal-area 1 km grids preserve source-cell identifiers; they do not increase native satellite resolution.

The authenticated rotation response exposes the staged, separately labeled `prototype_unreviewed` observation only. For the two current local samples, each rectangle had nine source cells with 100% valid area and an area-weighted mean of 0 mm on this one day. This is not a trend, field rainfall, forecast, current weather, or a recommendation input. The source identity, quality and geography remain pending review. Missing/corrupt sample yields no pilot observation and does not block rotation.

## SRTM

Each ZIP contained exactly one 3601 × 3601 signed big-endian HGT tile. The prototype displays one native point for each rectangle, with 2000 acquisition and the exact coordinates. Coordinates are reference points, not farmer fields. Land versus water is not established: Chattogram's selected point reports 0 m. The API verifies the stored reference point against its archive and checksum and caches the result based on file identity. It does not calculate slope, flood risk or suitability.

## MODIS

The delivered file is genuine-format HDF4 with MOD13Q1.061 data structures and the 2023-12-19 through 2024-01-03 composite. Local GDAL inspection identified the NDVI and pixel-reliability layers. Rajshahi's chosen reference point had reliability code 1 (marginal); the chosen Chattogram point had fill reliability 255. No NDVI-based result or recommendation is generated from these sample pixels. GDAL was installed inside the running development container for inspection; this is not yet captured in the project's reproducible geo worker image and will not survive container replacement.

## Verification and remaining work

The rotation prototype was checked in the browser for synthetic Rajshahi and Chattogram farms; real-data display is limited to the samples above. Independent review prompted user-supplied/unverified provenance wording, UTC time-bounds checking, valid-area wording, SRTM archive/manifest consistency, asymmetric coordinate tests, and corrupt ZIP handling. The system still needs complete multi-year IMERG data, verified boundaries, MODIS QA and a reproducible decoder, reviewed crop/irrigation rules, and additional datasets before a dataset-based ranked recommendation can be claimed. Raw files are Git-ignored and there has been no GitHub push.

### Follow-up implementation — field-coordinate SRTM sample

The v2 rotation API now samples the nearest available SRTM HGT node using the farm profile's latitude/longitude instead of returning a fixed city reference point. If coordinates are absent or fall outside the supplied regional tile, the API omits the elevation. The bilingual UI calls it an elevation sample near the field and states that the supplied tile origin and land/water status are unverified; this value is context only and is not used to rank rotations. The generated TypeScript contract includes the field-coordinate sample basis.

Verification: backend full suite 407 passed/7 skipped; focused SRTM, pilot and regional rotation tests 27 passed/1 skipped. Frontend TypeScript check passed; frontend tests passed 45/45 when run with the test suite's expected `EXPO_PUBLIC_API_URL=http://127.0.0.1:8000` (Compose normally supplies `localhost` for the browser). Direct reads against both supplied SRTM tiles returned 11 m for the current Rajshahi demo coordinate and 0 m for Chattogram. No browser/device test or GitHub push was done for this increment.

GRACE access note: the PO.DAAC page left open in the browser was the unfiltered `TELLUS_GRAC-GRFO_MASCON_GRID_RL06.3_V4` product. Its own description warns it is intended for expert use and does not correct coastal leakage. For a Bangladesh pilot including coastal Chattogram, evaluate the [CRI-filtered collection](https://podaac.jpl.nasa.gov/dataset/TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4), while retaining its coarse regional support and remaining uncertainties. An attempted local download did not succeed; no GRACE values were ingested.

### Shared prototype package

The four named owner-supplied IMERG, MODIS, and SRTM input samples, the two pilot manifests/data slices, and their QA reports are now part of the project package. Binary originals are tracked with Git LFS so a teammate can retrieve them using `git lfs pull`; generated and future operational downloads remain outside the reviewed pilot release. The IMERG source identity is still user-supplied/unverified, and this packaging does not promote it to a recommendation input.
