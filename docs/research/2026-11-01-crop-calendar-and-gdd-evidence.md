# Bangladesh rice calendar and GDD evidence — 2026-11-01

Status: independently source-checked research candidates. No agronomist approval,
field validation, reviewer identity, or production eligibility is asserted here.
This research extends the existing dhan80 candidate review; it does not change
runtime knowledge or remove its approval gate.

## Main three crop/season reference profiles

These are three rice/season profiles, not three crop species. All dates below
are recurring month-day ranges stated by the source. A range is not a promise
for every district, season, field, or year. Do not turn a reported life duration
into a transplant-to-harvest duration without a documented reference event.

| Profile | Seedbed sowing | Seedling age | Transplanting | Harvest | Reported duration |
|---|---|---|---|---|---|
| BRRI dhan80 / Aman | 07-05–07-25 | 25–30 days | 07-30–08-20 | 11-11–11-30 | 130 days |
| BRRI dhan100 / Boro | 11-15–11-29 | 35–40 days | 12-20–01-10 | 04-13–04-28 | 148 days |
| BRRI dhan48 / Aus | 04-15–04-30 | 15–20 days | 05-01–05-15 | 08-14–09-04 | 110 days |

### S1 — BRRI dhan80, Aman

Official [BRRI profile](https://riceprofile.brri.gov.bd/varieties/90), accessed
2026-11-01; page publication/update date was not shown in the inspected text.
Its broad scope is rainfed transplanted Aman on high/medium-high land in nearly
all Bangladesh regions. It supports the first table row. Manual weeding options
are 12–15 and 30–35 days after transplanting, with 40–45 days if needed.
Supplemental irrigation is conditional on missing rain at transplanting and
drought between booting and milk stages. Those stage names have no fixed day
offsets in this source. No source-endorsed NASA onset adjustment appears.

### S2 — BRRI dhan100, Boro

Official [BRRI profile](https://riceprofile.brri.gov.bd/varieties/107), accessed
2026-11-01; inspected page has no explicit publication/update date. It describes
irrigated high, medium-high and medium-low land with broad Bangladesh scope.
The second table row's sowing/transplant ranges explicitly vary by agro-region
and ecosystem. Manual weeding options are 12–15 and 30–35 days after
transplanting, optionally 40–45 days. Its irrigation reference describes AWD
from 15 days after transplanting until booting; standing water from booting
through full flowering; and drainage/stopping irrigation 10–15 days before
maturity depending on location. No water-depth threshold or dated booting/
flowering boundary is established by these statements.

### S3 — BRRI dhan48, Aus

Official [BRRI profile](https://riceprofile.brri.gov.bd/varieties/2), accessed
2026-11-01; inspected page has no explicit publication/update date. It describes
medium-high to medium-low land, generally excluding drought-prone areas, and
supports the third table row. Its first manual weeding window is 12–15 days
after transplanting. The second manual window is printed as **30–30 days**:
exclude that ambiguous value rather than silently changing it. Mechanical
weeding is a separate option. Supplemental irrigation is conditional on rain
being insufficient for timely establishment or during vegetative growth.

## GDD method evidence

Sultana et al., *Agroclimatic Indices of Rice (Oryza sativa L.) Influenced by
Different Planting Times*, Bangladesh Rice Journal 23(2), 87–94 (2019),
DOI [10.3329/brj.v23i2.48251](https://doi.org/10.3329/brj.v23i2.48251).
The DOI resolver failed in this tool; the article was verified in the
[BRRI-hosted journal PDF](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/2ce90d9a86c245259ca2b160a2464781.pdf),
zero-based PDF pages 90–95, especially index 92 (printed journal page 89) for
the method. The parsed PDF places the article's printed page 87 at PDF index
90. Accessed 2026-11-01.

The study used a **10°C base** and **(daily Tmax + daily Tmin) / 2 − base**.
It accumulated from transplanting to maturity. Its context is Gazipur, Aman
2016, two experimental lines and BRRI dhan49 as check. It does not validate
dhan80, dhan100 or dhan48-specific targets, upper caps, or national stage dates.
No upper cap is stated in this method. Observed totals varied with genotype
and planting date; they must not become one universal maturity target.

Implementation implication: acquire actual Tmax/Tmin if reproducing this paper.
Using POWER T2M directly is a separately named approximation requiring explicit
method review. A zero-floor on daily GDD is also an implementation convention
to state and justify. Do not present an unsupported 30°C cap as source-derived.

## What the evidence permits now

- Store a separately labeled calendar-reference catalog with claim-level source
  links, recurring dates, explicit establishment event, scope, capture date,
  missing publication date, and pending agronomic review.
- Show source-supported observation/check milestones in a read-only reference
  view. Turning a weeding option into a reminder is an application adaptation;
  it must preserve its range and optional/conditional nature.
- Preserve irrigation conditions and require current observations; these pages
  do not establish that irrigation is needed today on a farmer's field.
- Use the three profiles as candidates for calendar-overlap research, preserving
  cross-year Boro dates. They are not evidence of jointly feasible rotations.

## Remaining evidence and review gates

1. **Full stages:** none of these pages supplies a complete cultivar-specific
   dated sequence of vegetative/reproductive/ripening stages. The current M2
   plan builder requires growth stages; do not invent stage dates to unlock it.
2. **Task schema:** current `due_day_offset` represents one day. Source ranges,
   observed-stage triggers, conditions, alternative practices and source
   references need explicit representation or a non-operational reference view.
3. **Climate decision:** monsoon-onset search intervals, threshold rationale,
   acceptable planting shifts, photoperiod constraints, GDD mapping and thermal
   targets need scoped agronomic review. Irrigated Boro cannot be treated as
   simply rain-onset limited.
4. **Coverage:** broad prose does not establish village/field suitability;
   drought/salinity/land/irrigation exceptions must be checked against saved
   profile values and authoritative locality evidence.
5. **Treatments:** dhan80's fertilizer row lists more nutrient labels than
   numeric entries, and the pages repeat some organic-input text. Do not import
   ambiguous doses or treat published potential savings as measured farm gains.
6. **Rights/freshness:** the BRRI pages display a copyright/all-rights-reserved
   footer; no explicit open redistribution license was found in the inspected
   pages. Link and attribute factual references; separately resolve rights for
   republishing full pages, images, or large captures. Record actual snapshots
   and checksums before treating a future dataset release as reproducible.

Ask the project owner for an actual agronomist/extension reviewer only for the
remaining scientific approvals. A bearer API token cannot resolve those gaps.

## Bounded follow-up for the existing rotation patterns

A fourth source reference was checked for the explicitly named BRRI dhan31
option in the existing rotation catalog: [BRRI dhan31 profile](https://riceprofile.brri.gov.bd/varieties/42),
accessed 2026-11-01. It describes transplanted Aman on high/medium-high land,
with mild photoperiod sensitivity. Seedbed sowing is June 29–July 14; seedlings
25–30 days; transplanting July 23–August 14; harvest November 9–24; reported
life duration 140 days. Manual weeding options are 12–15 and 30–35 days after
transplanting. Supplemental irrigation is conditional on inadequate rain at
establishment or drought during booting–milk stages. Exact stage dates and a
climate-shift rule remain absent.

The structured catalog includes this as a fourth reference, with all profiles
explicitly marked `cultivation_method=transplanted`. Matching a rotation step
requires both the named variety and the same establishment method. A cultivar
name alone does not permit mapping a transplanting calendar onto a wet-seeded
step. In particular, existing BRRI rotation examples contain wet-seeded Boro,
Aus or Aman steps; these remain without verified matching calendars here.

The variety-list links for dhan33 and BR26 resolved to detail URLs, but those
pages failed to fetch in the research tool. A direct dhan28 profile was not
located in this bounded pass. No calendar was guessed for any of those steps.

## Rajshahi representative point — bounded follow-up

**Primary source verified 2026-11-01:** Bangladesh Meteorological Department,
[Report on Cyclone Roanu](https://live8.bmd.gov.bd/file/2017/04/09/pdf/36934.pdf),
Table 5 continuation, zero-based PDF page **47**, printed page **45**. Its
station table identifies **Rajshahi**, latitude **24.37° N**, longitude
**88.70° E**. The report concerns May 2016; its formal publication date was not
verified (the URL path alone is not publication metadata).

Suggested display label: **Rajshahi — BMD station reference point (published
report)**; Bangla: **রাজশাহী — BMD স্টেশনের প্রকাশিত নির্দেশক বিন্দু**.

This is a named meteorological station point usable as an explicitly selected
representative location for a coarse POWER point query. It is **not** a
district centroid, district average, village coordinate, or farmer field.
The source prints two decimal places and does not specify a geodetic datum in
this table; no transformation or higher spatial precision is established.
The source does not prove that station metadata remains unchanged today.
This one point provides no evidence of all-64-district coverage. Acquiring NASA
data at it does not turn NASA's gridded values into BMD station observations.

Additional indexed official metadata from BMD's *Changing Climate of Bangladesh*
lists the same Rajshahi coordinates with local ID 10320 and WMO ID 41895, but
the 16 MB source exceeded this browsing tool's size limit, so the directly
verified report above is the acquisition reference. No dataset was downloaded
and no runtime coordinate was changed in this research task.
