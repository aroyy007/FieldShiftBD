# Rotation calendar Task 6 — evidence gap record

**Date:** 2026-11-07
**Status:** source-scoped candidate and deterministic calendar checks implemented; no researcher-reviewed comparison scenario is available yet.

## What the code can support

- The comparison accepts Rajshahi (`5081`) and Chattogram (`2015`) and loads the existing BRRI rotation-pattern source without copying its claims into a second data file.
- Published examples retain their source IDs and `source_verified_pending_agronomy_review` status. Local applicability stays `unknown` unless a recorded, understood profile value conflicts with the source scope.
- The candidate baseline contains only the farmer's recorded/active-season intervals. Missing history is not filled with assumed fallow crops or dates.
- A variety calendar is attached to a step only when crop, season, variety, and cultivation method match exactly and the source has exact interval endpoints. A broad date range is not collapsed into one artificial date.
- Calendar checks report date gaps, overlap, missing intervals, and missing reviewed turnaround rules. They do not calculate GDD, yield, soil benefit, irrigation demand, or a planting shift.

## Inputs still needed before a defensible regional demo can be ranked

For **each crop step in each proposed sequence**, an agronomist or authorized local reviewer needs to supply or approve:

1. The exact variety/cultivar and cultivation method (seedbed, transplant, or direct/wet-seeded) used by the calendar.
2. Establishment and harvest window dates for the relevant agro-ecology/district, plus the event that defines crop duration.
3. The source-backed minimum turnaround interval between successive crops, if one is required.
4. Local applicability conditions: land class, soil texture, irrigation/water access, and any upazila/ecosystem boundary for which the source is valid.
5. If thermal exposure or GDD is to be compared: reviewed base temperature, cap, target degree-days, and stage durations for that same cultivar/method. All are currently absent or unvalidated in the catalog.
6. Reviewer identity/organization, review date, and the exact source/profile/version approved for use.

Current examples have unresolved inputs: BRRI-RFS-01 names multiple possible varieties and does not identify the Boro establishment method; BRRI-RFS-02 includes a chickpea calendar that is not verified and rice-method/calendar mismatches; BRRI-RFS-04 includes an undated Sesbania step and unresolved rice dates. The sources do not establish district-level fit for both pilot regions.

Until these items are reviewed, the app reports alternatives as `unknown`, calendar/GDD metrics as missing, and preference ordering as insufficient evidence. It does not claim that the published examples are locally recommended rotations.
