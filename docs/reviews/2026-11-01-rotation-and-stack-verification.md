# Rotation preview and full stack verification — 2026-11-01

Working branch: `arijit`. Verification applies to the current uncommitted workspace;
it is not a production release or a statement that every final-plan gate is met.

## Delivered increment

- Authenticated `POST /advisor/farmlands/{farmland_id}/rotation-comparisons`
  reads the saved M1 profile and recorded M2 seasons through the shared snapshot.
- Two BRRI source patterns appear only for irrigated high/medium-high land with
  clay/clay-loam soil. Missing and out-of-scope inputs are explicit.
- Crop Advisor renders the recorded sequence, published examples, source dates,
  qualitative sequence characteristics and unassessed factors in Bangla/English.
- Source capture timestamps are preserved. The comparison performs no season or
  task writes. Runtime remains default-off; example env files explicitly enable
  the preview with `CHALLENGE_ROTATION_ENABLED=true`.
- Shared JSON Schema, TypeScript, route ownership and API contract inventory were
  updated. Test runtime state is isolated so M5 switch changes cannot disable
  later M2 tests.

Source: BRRI Rice-Based Farming Systems Department, page updated 2020-06-07,
locally captured 2026-11-01:
<https://brri.gov.bd/pages/static-pages/6922dc9b933eb65569e1140d>.

## Verification evidence

| Check | Result |
|---|---|
| Full backend `pytest -q --tb=short` | 333 passed, 7 dependency/schema warnings, no skips |
| PostgreSQL | Fresh disposable PostgreSQL 16 database; all migrations and `alembic check` passed; PostgreSQL integration tests included above |
| Final focused API/contract/snapshot checks after provenance and explanation corrections | 35 passed, 3 warnings |
| Frontend `npm test` | 38 passed |
| Frontend lint and TypeScript | `npm run lint` and `npx tsc --noEmit` passed |
| Web export | `npx expo export --platform web` passed; 20 routes |
| Browser | Exported landing loaded; selecting Bangla changed the visible copy; signup navigation worked |

The full suite ran before the final small provenance/explanation corrections;
the focused set above was rerun after both corrections. Test packages were
downloaded from PyPI on the host and installed offline in Docker after Docker's
PyPI requests timed out. Temporary test environment files and the disposable
verification database were cleaned up.

## Open gates

- Signup still displays English after Bangla is selected on the landing page.
  Carrying a shared language preference through onboarding and translating its
  forms remains a frontend follow-up.
- Browser verification did not exercise every authenticated screen or native
  Android flow. Automated API tests do not establish complete device usability.
- Rotation ranking, dated calendars, NASA climate feasibility, resource/market
  constraints, soil-health quantification and confirmed plan selection are not
  implemented by this preview. Its narrow ecosystem scope is not nationwide
  rotation coverage or field validation.
- The BRRI source is provisional for this display; no current agronomist review
  is recorded. No soil, yield, cost, fertilizer or water savings are claimed.
- External Gemini/NASA live calls were not repeated by this verification pass;
  suite fixtures and the local captured reference sources exercise those seams.
- An existing whitespace difference remains in the raw captured BARC copyright
  HTML. Its captured bytes were preserved.

No commit or push was performed in this continuation.
