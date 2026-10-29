# District climate cache layout

Production bundles live outside PostgreSQL under `CLIMATE_CACHE_DIR` (default
`backend/data/climate/cache/`):

```text
<root>/<canonical-district-code>/bundle.json
<root>/<canonical-district-code>/<versioned source assets>
```

`bundle.json` must validate against `DistrictClimateBundle`; each declared
asset path is relative to the cache root and is checked for traversal, byte
length, SHA-256, dataset version, time coverage, units, and QA status before a
reader returns it. Unknown and expired bundles are unavailable, never zero.
The cache reader caps manifests at 2 MiB, individual assets at 1 GiB, and
combined bundle assets at 4 GiB by default; SHA-256 is streamed in 1 MiB
chunks. `ClimateBundleCache` accepts explicit limits for the deployment's
resource budget. The runtime climate adapter is cache-only.
Retrieval, harmonization, QA, and release of production datasets belong to M4
and must not be implied by the synthetic tests.

Only compact, legally redistributable district bundles belong in an app
release. Keep raw/global rasters outside the mobile package. Document the
license and redistribution decision for every exact product/version before
publishing any derived or source asset.

The checked-in fixtures under `backend/tests/fixtures/foundation/` are
synthetic test data and are not climate evidence.
