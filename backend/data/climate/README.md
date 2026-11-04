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
release. Keep raw/global rasters outside the mobile package. The included
NASA POWER bundles are normalized derivatives of the public POWER Daily API
for three representative points (2001–2025). The [Registry of Open Data on
AWS](https://registry.opendata.aws/nasa-power/) lists NASA POWER as CC BY 4.0
and says to cite the POWER project; retain the source URL, retrieval date,
original variable names/units and this attribution when reusing the cache. The
[NASA POWER methodology](https://power.larc.nasa.gov/docs/methodology/) confirms native grids
vary by product: standard meteorology is 0.5° × 0.625°, while solar is 1° ×
1°. See the [NASA POWER acknowledgement](https://power.larc.nasa.gov/docs/acknowledgements/).
These are reference-point samples, not district averages or field measurements.
See the source register for the product-specific citation and current coverage.

For any other dataset, document the license and redistribution decision for
the exact product/version before publishing a derived or source asset.

The checked-in fixtures under `backend/tests/fixtures/foundation/` are
synthetic test data and are not climate evidence.

BRRI Aman calendar research is recorded in
[`AMAN_CALENDAR_SOURCE_REVIEW.md`](AMAN_CALENDAR_SOURCE_REVIEW.md), with a
machine-readable but explicitly unreviewed candidate at
[`candidates/aman_brri_dhan80.json`](candidates/aman_brri_dhan80.json). These
research files are not production cache bundles or approved agricultural
knowledge. Do not import them as recommendations until the documented expert
review is complete.
