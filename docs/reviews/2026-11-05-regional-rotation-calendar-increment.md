# Regional rotation: calendar and historical context increment

## Implemented

- Added source-checked BRRI calendar references, with variety, season and cultivation-method matching. Method mismatch and missing evidence remain explicit; agricultural review is pending.
- Connected the authenticated rotation comparison to published calendar windows and historical NASA POWER reference-point rainfall. For complete paired years, it reports median totals for shorter and longer possible calendar intervals. These are interval comparisons, not a forecast, a confidence interval, a field measurement or crop water demand. No rotation is ranked or activated.
- Added an expandable bilingual calendar evidence view, including the method described by the source, source link, and evidence limitations.
- Added an isolated IMERG daily V07 decoder, support-preserving area-weighted pilot grid and offline staging. Raw and staged sample provenance, units, dates, checksums, and the discovery search rectangle are checked. District assignment remains an unverified request label; the rectangle is not a district boundary. Staged data is not connected to the app and is not published as current.
- Coordinate float32 regression coverage checks adjacent native cells share edges, and rejects coordinates that do not match the expected grid.

## Evidence and verification

- Calendar research: [source review](../research/2026-11-04-rotation-calendar-extension.md). BRRI pages are published references, not evidence of expert approval for this app.
- Authenticated local browser flow: Rajshahi and Chattogram demo fields both displayed BRRI dhan31 calendar and their respective 2001–2025 POWER historical interval medians.
- Full backend suite: 396 passed, 5 skipped, 8 warnings. Focused regional tests, frontend tests, TypeScript and lint were also run; see the implementation ledger for final results.
- Actual IMERG granule download was retried after the reported account approval, but the upstream service still returned HTTP 403 `EULA Acceptance Failure`. The decoder and grid tests use synthetic files only. No claim of operational IMERG data integration or validated source format is made.

## Remaining

Validate source-specific access with Earthdata, use a real granule to verify format and science QA, obtain verified geography, and prevent unreviewed pilot-grid data from being used as district evidence. Complete crop-specific expert-reviewed calendar and water-demand data, feasibility and meaningful tradeoff analysis before producing farmer recommendations or claiming the wider plan is complete.
