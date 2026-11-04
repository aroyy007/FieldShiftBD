# District cache inventory delivery

Date:2026-11-01, Asia/Dhaka. Branch:arijit. Base:8f0bb9b.
Scope:owner-requested implementation continuation; no GitHub push.

## Delivered

- Public `GET /advisory/districts` returns the 64 canonical Bangladesh district
  IDs/names and bounded local index-file presence:cached, missing or unreadable.
  It returns `cached_count` and `requires_validation_on_load=true`, with
  `Cache-Control: no-store` for fresh inventory checks.
- Metadata inspection never opens climate payloads, hashes large assets,
  acquires data or exposes local file paths/private farm records. Escaping
  symlinks and oversized/non-regular indexes are unreadable. Actual advisory
  reads retain full schema, asset/source and cache validation.
- The bilingual public selector puts saved-data entries first while retaining
  every district. Counts explicitly describe saved-file presence rather than
  verified or fresh evidence. Missing data leaves published variety calendars
  accessible. If inventory fails, the original advisory flow remains usable.
- Shared JSON Schema/TypeScript and route ownership inventory are synchronized.
  No database schema, operational state, authentication or agronomic-rule changes.

Current local inventory:64 identifiers,1 cached index (Rajshahi). This does not
claim that all64 districts have NASA histories or that a cache file is valid.

## Verification

- New inventory HTTP cases observed RED before implementation, then GREEN.
  The explicit no-store regression also failed before its header was added.
- Focused cache/advisory/contract/ownership set:18 passed before the final
  metadata-only/no-store case; the full suite below includes all4 new API cases.
- Full backend suite against fresh disposable PostgreSQL16:353passed,7 existing
  dependency/schema warnings,no skips. Alembic upgrade and schema check passed.
- Frontend:40tests passed, including2 RED→GREEN ordering/fallback cases. Lint
  and TypeScript passed. Cleared web export completed with21routes.
- Live browser→API at390px:64districts/1cached count, Bangla picker, Dhaka missing
  data with retained calendar, English switch, inventory503 recovery while the
  actual Rajshahi advisory still succeeds. Page width390px matched viewport;
  no page errors. Inventory503 was injected only for the explicit failure check.
- Independent Spec and Standards review:0actionable findings in the declared
  scope. Native Android/field usability was not established by browser checks.

Verification preview uses4173 with an isolated API on8012 and dummy credentials.
It is not the production environment. The disposable PostgreSQL test database
was removed after the suite; existing application containers/data were preserved.

## Deferred work and rulings

- Parquet packaging remains unimplemented. Host PyPI, direct wheel and Docker
  package downloads failed; do not add an uninstalled codec or claim a completed
  data release. Pending publication tests are retained in this plan's ignored
  execution ledger. Existing inline JSON cache stays authoritative.
- The inventory uses metadata-only presence to keep public requests bounded.
  It deliberately requires full validation on load rather than decoding64
  histories or hashing potentially gigabytes of assets on every list request.
- Keep the owner's current workspace/branch and unrelated source captures/UI
  changes. Presentation outputs are preserved and are outside this commit.
- Nationwide acquisition/QA/rights, reviewed GDD/calendar/stage rules, complete
  rotation feasibility and confirmed operational actions remain parent-plan gates.

See [increment plan](../plans/2026-11-01-parquet-cache-and-coverage.md) and
[previous delivery](2026-11-01-calendar-nasa-rotation-delivery.md).
