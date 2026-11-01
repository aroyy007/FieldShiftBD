# Versioned NASA Parquet cache and district availability

Parent authority: FINAL_IMPLEMENTATION_PLAN.md §§4.1, 6 and the owner's continuation request.
Base: 8f0bb9b on arijit. Preserve unrelated work and presentation outputs. No GitHub push.

## Increment

1. Publish normalized daily observations as immutable content-addressed Parquet,
   with a small versioned index and original source provenance. Read the old JSON
   representation for compatibility. The public and farm consumer contracts still
   return the validated DistrictClimateBundle shape. Do not invent source rights.
2. Validate file hashes, schemas, row counts, dates, units and memory bounds before
   returning observations. Preserve daily quality flags. Do not let a damaged or
   mixed representation silently fall back to another version. No analytical
   request acquires data or accesses a remote Parquet URI.
3. Expose bounded public district-cache availability across all 64 canonical IDs
   and show it in the bilingual district selector. Availability is not agronomic
   suitability, a recommendation, full NASA layer coverage or field validation.
4. Replay the existing sourced Rajshahi history locally into the new format and
   prove advisory/rotation consumers preserve results. Test focused and full
   backend suites, frontend type/lint/tests/export and the browser flow.

## Impact and compatibility

Affected owners: M4 storage/acquisition, M2 advisory inventory, shared response
schema for the additive inventory, frontend public advisory. No auth, farm state,
season, task, disease or database migration changes. Other shared consumers keep
in-memory daily_series semantics. Pin the storage codec dependency in backend
requirements. Keep a versioned JSON index and immutable assets for rollback;
existing inline bundles remain readable. Source agronomy and GDD review gates
remain unchanged. Parquet packaging does not resolve outstanding dataset QA,
rights review, nationwide acquisition or agronomic validation.

## Verification seams

Publication/read round trip and corruption/resource-bound tests precede storage
implementation. Public HTTP tests cover 64 IDs, unavailable/expired/corrupt cache,
private-data exclusion and forbidden network access. Frontend request/state tests
and browser checks cover inventory labels and missing-data recovery.

## Execution update

Dependency acquisition failed through the host PyPI index, direct wheel host,
and disposable Docker network. Parquet implementation is deferred with pending
red tests preserved in the plan's ignored ledger directory. No new codec or
unverified dependency ships in this increment. The implemented API is a file-
presence inventory (`cached_count`, `requires_validation_on_load=true`), with
no-store refresh semantics. Public advisory retains all evidence validation.
Nationwide identifier selection is not nationwide data coverage.

## Storage implementation update — 2026-11-01

The earlier dependency block is resolved for the Python 3.12 implementation
environment. PyArrow 26.0.0 is pinned. District publication now writes a compact
versioned JSON index and an immutable SHA-256-addressed Parquet asset. The bounded
reader retains legacy inline-JSON support and validates checksum, format/schema,
unit metadata, finite values, row count, nulls, date ordering, file size, metadata
and decoded table limits before returning the existing bundle contract. The
first Parquet publication archives the prior JSON index; subsequent publications
keep prior indexes and immutable data assets.

The local Rajshahi POWER cache (point at 24.37 N, 88.70 E; 2001-01-01 through
2025-12-31; 9,131 observations) was converted without another NASA request. Its
daily series is 100,347 bytes as Parquet. Before/after public advisory and
rotation-comparison outputs matched exactly, and the `/advisory` HTTP route
returned the same provisional 0-day exploratory shift with a cache-hit status.
This is one representative point cache, not 64-district coverage or a district
average. Other NASA layers, data-rights review, QA and agronomic approval remain
open. Full backend verification: 356 passed, 5 skipped; the skips are existing
PostgreSQL-only checks unavailable in this local run. No frontend files changed.
