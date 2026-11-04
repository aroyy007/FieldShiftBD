# Aman planting-window evidence review

**Research date:** 2026-10-30
**Status:** Source-checked candidate evidence; not approved production knowledge.
**Scope:** BRRI dhan80 (Aman rice), Bangladesh. This evidence is variety-level where stated, but it does not establish suitability for every field or village.

## Evidence found

| Claim | Source evidence | Scope and limits |
|---|---|---|
| BRRI dhan80 is a rainfed transplanted Aman variety. | BRRI Rice Profile says it is a rain-dependent transplanted Aman variety and was approved for Aman cultivation in 2017. | Variety-level description. A recommendation to shift planting according to observed rainfall onset is not stated. |
| The variety is generally suitable in almost all Bangladesh regions; it is described for high and medium-high land. | BRRI Rice Profile. | Broad regional context, not a village or field-level suitability assessment. |
| Seedbed sowing: 5–25 July; seedlings 25–30 days old; transplanting: 30 July–20 August. | BRRI Rice Profile. | Published variety-specific calendar window. It is not a climate-change adjustment rule. |
| Life duration: 130 days; harvest: 11–30 November. | BRRI Rice Profile. | Reported variety profile values; not a guaranteed harvest date for a particular field or year. |
| Supplemental irrigation may be needed if rain is absent at transplanting; drought from booting through milk stage calls for supplemental irrigation. | BRRI Rice Profile. | Conditional guidance; the profile does not specify a daily schedule or field-specific water amount. |
| A rice GDD base temperature of 10°C was used in a BRRI Aman study. | Sultana et al. (2019), BRRI Gazipur T. Aman experiment; formula used `(Tmax + Tmin) / 2 - Tbase`, with Tbase=10°C. | A rice-method candidate, not a dhan80-specific thermal requirement. Study site was Gazipur and the check variety was BRRI dhan49, not dhan80. No upper-temperature cap was specified in the cited method. |

## What this can support in FieldShift

- A clearly labeled **BRRI dhan80 Aman calendar reference** with provenance and a warning that farm-level suitability is not established.
- A general rice GDD calculation candidate using 10°C as the base, if the UI labels the method and its limits. NASA POWER daily mean temperature can support a calculation only if the implementation documents that it uses daily mean temperature in place of the paper's `(Tmax + Tmin) / 2` expression and validates the parameter mapping.
- Historical rainfall onset comparison as climate evidence, independent from a crop recommendation.

## What remains unsupported

- A BRRI-endorsed rule that moves the 30 July–20 August window by the measured NASA rainfall-onset shift.
- A BRRI dhan80-specific GDD requirement, GDD cap, or mapping from accumulated GDD to transplanting/harvest dates.
- Village-level suitability, soil workability from coarse satellite data, or a yield outcome.
- A complete climate onset search interval and threshold interpretation tied to the BRRI variety calendar. The source calendar is a transplanting window, not a definition of monsoon onset.

## Additional BRRI locality and calendar sources

BRRI publishes a **Rice Database** page that lists (a) BRRI varieties by agro-ecological region and market demand, (b) varieties suitable for rainfed transplanted Aman in different areas, (c) district-level rice area/production/yield series, and (d) a rice crop calendar. The page says it was last updated 2025-07-27. BRRI also lists season calendars for Aus, Aman, and Boro; its calendar page reports last update 2026-04-23. The BRRI Rice Profile describes browsing variety recommendations by division, district, and upazila.

These are promising Bangladesh-wide/locality sources, but the other linked BRRI tables have **not** been extracted or checked for effective dates, boundary keys, methodology, or reuse terms. The Aman suitability PDF and season-calendar image are reviewed separately below. Do not infer village-level evidence from a dataset labelled only "area-wise" or agro-ecological-zone level. Until a calendar rule is reviewed and mapped against M1 location IDs, the dhan80 candidate above remains general reference evidence only.

Therefore, this evidence must **not** be loaded as an approved `crop_calendar` record. The authenticated advisory should continue to return `insufficient_data` for an adjusted planting recommendation until an agronomist approves (1) the onset definition and search interval, (2) whether/how the historical onset delta may adjust the cited transplanting window, and (3) the GDD method's temperature inputs and whether the general 10°C base is appropriate for the selected cultivar and purpose. No reviewer identity or approval is inferred from this research.

## Primary sources

1. Bangladesh Rice Research Institute (BRRI), [BRRI dhan80 Rice Profile](https://riceprofile.brri.gov.bd/varieties/90), accessed 2026-10-30. The page identifies Aman season, broad land/region context, seedbed and transplanting dates, life duration, irrigation notes, and harvest period.
2. A. Sultana et al., “Agroclimatic Indices of Rice (*Oryza sativa* L.) Influenced by Different Planting Times,” *Bangladesh Rice Journal* 23(2), 87–94 (2019), [BRRI-hosted PDF](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/2ce90d9a86c245259ca2b160a2464781.pdf), DOI [10.3329/brj.v23i2.48251](https://doi.org/10.3329/brj.v23i2.48251). Relevant details: abstract and study description on PDF p. 90; GDD formula and 10°C base on PDF p. 92. The experiment was conducted at BRRI Gazipur in T. Aman 2016 with BRRI dhan49 as the check variety.
3. NASA POWER, [Daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/). Check the exact requested parameter and temporal aggregation used by the implementation before describing its input as daily mean temperature.
4. BRRI, [Rice Database](https://brri.gov.bd/pages/static-pages/6922dbd4933eb65569e0cd7e), last updated 2025-07-27 per page metadata. Lists district-level rice statistics and area/AEZ-specific Aman variety resources; underlying linked datasets still require extraction and review.
5. BRRI, [Rice Calendars](https://brri.gov.bd/pages/static-pages/6922dea6933eb65569e1c55f), last updated 2026-04-23 per page metadata. Lists separate JPG downloads for Aus, Aman, and Boro; the Aman image was visually inspected and credits BARC & AFACI.
6. BRRI Rice Profile, [about and locality features](https://riceprofile.brri.gov.bd/about). Describes variety recommendations by division, district, and upazila; the interactive source data and reuse conditions have not yet been reviewed.
7. BRRI-hosted [Suitable Varieties against Locations for T. Aman (Rainfed) Cultivation in Bangladesh](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/b1df79dafa654e7baa4f4289982d68b7.pdf), accessed 2026-10-30. Eight-page area/land-type suitability reference; no printed effective date or reuse license identified during this review.
8. BRRI calendar page's [Aman JPG](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/8bab203903584153bb488bcb73b94acd.jpg), accessed 2026-10-30. Image footer credits BARC & AFACI; see scope limitation above.

## Review handoff

Ask a rice agronomist/BRRI extension specialist to approve the four unresolved decisions above. Record the reviewer, review date, source edition/date, and accepted method in the approved knowledge record; only then should the record be imported for the production API.

## Locality-source follow-up (2026-10-30)

### BRRI Rice Profile area-varieties page

The public [area-varieties page](https://riceprofile.brri.gov.bd/area-varieties) explicitly asks users to choose a **division, district, and upazila** and says it will show suitable BRRI rice varieties. BRRI's [About page](https://riceprofile.brri.gov.bd/about) confirms those locality recommendations are available without login. The public portal also describes its variety catalogue as season-aware (Aus, Aman, Boro), with cultivation guidance and archived publications.

One live UI sample was checked for **Rajshahi division → Rajshahi district → Godagari upazila**. The UI returned five suitable varieties: four Aman drought-tolerant entries (BRRI dhan56, dhan57, dhan66, dhan71) and one Boro cold-tolerant entry (BRRI dhan36). The cards expose variety characteristics such as lifecycle/duration, yield, and amylose, with detail links. This establishes that the UI has at least one upazila-keyed result, not that all upazilas/seasons have complete or current coverage. It does not establish village-level recommendations. Capture date: 2026-10-30.

The page's publicly accessible HTML exposes the selectors and result area, but the underlying recommendation records/API, completeness, update cadence, methodology, and reuse/licensing terms were **not established** in this review. Do not bulk-ingest the BRRI Rice Profile UI data or present it as an unrestricted dataset until BRRI confirms reuse terms and the underlying data's provenance/coverage. For a prototype, cite the BRRI page, retain the exact locality and capture date, and label the item as a BRRI portal reference; do not combine it with a NASA-derived planting shift as if BRRI endorsed that calculation.

### BRRI Rice Database and crop calendars

The official [Rice Database page](https://brri.gov.bd/pages/static-pages/6922dbd4933eb65569e0cd7e) lists resources for Aman varieties suitable to different areas, rice area/production/yield by district, season-wise area/production/yield, irrigation, and the Bangladesh rice crop calendar. The Aman suitability PDF and calendar image are inspected below; the other linked tables/files still need extraction and review for effective date, geographic keys, methods, and reuse terms before they can populate production recommendations.

One linked resource has now been inspected: BRRI's [Suitable Varieties against Locations for T. Aman (Rainfed) Cultivation in Bangladesh](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/b1df79dafa654e7baa4f4289982d68b7.pdf) PDF (8 pages; link currently hosted in BRRI's database page). It is organized by division, district, named upazilas, and ecosystem/land type; rows list variety identifiers for high/medium-high land, low land, and in some areas drought-prone, saline, submergence, or post-flood conditions. For example, the Rajshahi district row lists Godagari among its upazilas and separately identifies high/medium-high, lowland, and drought-prone variety sets. This is a useful **Aman, rainfed, location-and-land-type suitability reference**, not an annual calendar or a village/field-specific recommendation. Its date/effective period is not printed in the extracted pages, administrative spellings/coverage need reconciliation against the app's location IDs, and no reuse license was found on the linked index/PDF during this check. Keep it as candidate evidence until those issues and agronomic review are resolved; do not interpret a missing land type as evidence of unsuitability.

The official [Rice Calendars page](https://brri.gov.bd/pages/static-pages/6922dea6933eb65569e1c55f) reports a last-updated date of 2026-04-23 and exposes downloadable JPGs for Aus, Aman, and Boro. I visually inspected the linked [Aman calendar image](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/8bab203903584153bb488bcb73b94acd.jpg): it is a season-stage infographic, and its footer credits **BARC & AFACI**. It is not a machine-readable district/upazila dataset; the chart's full date details have not been transcribed or agronomically reviewed. The index shows an “all rice” download label but did not expose a target URL in the page's accessibility content. Treat this as general crop-calendar reference only, and attribute the chart to BARC & AFACI if used. Do not claim that it supplies location-specific planting windows or a reviewed NASA-based shift rule.

### BARC Crop Zoning suitability capture (2026-10-30)

The separate [BARC Agri-Advisory Portal copyright policy](https://portal.cropzoning.gov.bd/copyrightPolicy) states that portal material may be reproduced if presented accurately and without misleading context, with prominent source acknowledgement. Its [Terms of Use](https://portal.cropzoning.gov.bd/termsOfUse) disclaim completeness/accuracy guarantees and advise users to verify information and obtain appropriate professional advice. Those conditions support attributed reuse of this portal snapshot; they do not turn it into field measurements or a BARC endorsement of FieldShift.

The public portal's crop-zoning API was captured through `backend/scripts/capture_barc_portal_sources.py` into `backend/app/data/source_captures/barc_crop_zoning/`. The installed capture manifest contains **675 files**: lists for all **64 districts**, all **482 distinct upazila codes** from those lists, and **482 matching upazila suitability responses**. Each file is pinned with its retrieval time and SHA-256. Capture timestamps range from 2026-10-30 16:22 to 16:43 Asia/Dhaka. The capture passed local integrity checks: every manifest file exists, all JSON parses, all hashes match, and there are no missing or extra upazila response codes versus the source lists.

This is national **upazila-level crop-zoning context**, not village, cadastral plot, or farmer-reported soil data. The source API returns crop/season/situation rows with suitability class counts; it does not establish current field conditions, a yield forecast, or planting dates. Existing M2 policy code explicitly labels imported entries `regional_context_only`, retains the source URL/provenance, and blocks them from being interpreted as farm-level fit. A complete API capture means all source-listed upazila responses were fetched; it does not assert that every crop has a positive or complete suitability row in every upazila.

The raw capture and importer policy are present in the working tree. I could not run `scripts.import_reference_data --check-only` during this continuation because the Docker daemon was unavailable and the host Python is 3.9, while the backend requires Python 3.10+. Therefore, database/read-model acceptance of this refreshed snapshot remains unverified; do not claim it has been imported until that check succeeds.

### Safe next data step

Next, transcribe the season-stage dates from the chart only if they can be independently reviewed, document the source/reuse terms, preserve the source edition/file and metadata, map the Aman PDF's names to FieldShift administrative IDs, and verify coverage before loading a supported subset. Keep village/farm recommendations unavailable unless a source explicitly supports that resolution. Until agronomic review approves a crop-calendar rule and a climate-adjustment policy, keep the authenticated adjusted-window advisory at `insufficient_data`; the portal/PDF may be shown separately as sourced variety context, not an automatic climate-adjusted planting recommendation.
