# Potato evidence research package

**Research date:** 2026-10-06

**Status:** Source-supported candidates for M2 review only. No production
knowledge was created, approved, or ingested. The evidence statements below
report what sources say; they are not current or Comilla-specific farming
recommendations.

## Verified evidence candidates

| Fact ID | M2 category | Source-supported claim | Geographic scope | Proposed M2 use |
|---|---|---|---|---|
| POTATO-001 | Season context | BARC says potato is grown in Bangladesh during Rabi and defines Rabi as mid-October to mid-March. | Bangladesh-wide general context | Season context only; not an exact planting/harvest date. |
| POTATO-002 | Soil and land context | BARC says medium-high to high land with loamy to sandy-loam soil is best suited for potato cultivation. | General Bangladesh handbook context; no locality specified | Candidate only; requires land-type and current local review. |
| POTATO-003 | Environmental context | BARC describes winter cultivation in most parts of Bangladesh, sunny conditions and sufficient soil moisture as appropriate, and gives an optimum growth/development range of 15–21°C. | Bangladesh, qualified as “most parts”; not Comilla-specific | General context only; no climate comparison or recommendation. |
| POTATO-004 | Sowing window | BARC gives 15–30 November as optimum and October–December as a possible sowing period. | General Bangladesh handbook context; no variety or district specified | Candidate only; requires current locality/variety review before planning. |
| POTATO-005 | Irrigation context | BARC says irrigation depends on soil type; it lists possible timings at 8–10, 40–45, and 60–65 days after sowing and a furrow water depth. | General handbook context; not Comilla or variety-specific | Candidate only; do not convert into an automatic schedule. |
| POTATO-006 | Harvest interval | BARC says harvest at 80–90 days after sowing, depending on variety. | General handbook context; variety-dependent | Candidate interval only; not a fixed date or maturity indicator. |
| POTATO-007 | Map interpretation | BARC defines suitability classes against percentages of maximum attainable yield and says zoning summarizes upazila cultivable-area shares in each class. | Bangladesh; upazila-area aggregation | Interpret a verified local map only; not field-level suitability. |

The production-technology facts come from BARC's **Hand Book of Agricultural
Technology**, published May 2013. The potato chapter's printed pages are noted in
the JSON package. Its age is material: present-day validity has not been
independently established, so every item remains a review candidate. The BARC
online suitability-methodology page does not show a publication or map-data
version date.

### Sources

1. **Bangladesh Agricultural Research Council (BARC), _Hand Book of Agricultural
   Technology_**, published May 2013. Source URL: [BARC-hosted PDF](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-barc/2024/12/053a0722429448d4903412ce683a7d06.pdf). Relevant source locations: introduction (printed pp. 1–2); Potato introduction and land/soil/sowing/irrigation material (printed pp. 35, 38–39); harvesting and seed preservation (printed p. 45).
2. **BARC, _Land Suitability Assessment and Crop Zoning of Bangladesh — Introduction and methodology_**, date not stated: [methodology page](https://apps.barc.gov.bd/cropzoning/homes/intro). It describes the factors and map classification methodology and upazila-area aggregation.
3. **BARC, _Suitability Map of Potato — Bangladesh map_**, date/version not stated: [potato map](https://apps.barc.gov.bd/cropzoning/homes/bdMap/12). The displayed totals are national aggregate areas and do not identify Comilla.
4. **BARC, _Crop Suitability Maps and Data / Crop Zone Maps and Data_**, date/version not stated: [data catalogue](https://apps.barc.gov.bd/cropzoning/homes/downloads/2). Potato map/data links are listed. The linked Potato-zone spreadsheet could not be inspected through the available research reader, so it is not used as evidence here.
5. **BARC, Crop Zoning Information System**, current page accessed 2026-10-06: [CZIS](https://czis.cropzoning.gov.bd/). It requests an upazila code for suitability analysis and provides Division/District/Upazila selectors. A Comilla potato result was not retrieved or verified in this research.

## Comilla coverage

There is **not enough evidence for a Comilla-specific potato recommendation**.
BARC's methodology supports upazila-scale zoning in principle, but the
Comilla district/upazila class and a versioned supporting dataset were not
verified. The Bangladesh potato map is an aggregate. An upazila result would
still describe area coverage and must not be restated as proof that the
Golden Farm's example 2-acre field is suitable.

The Golden Farm's Comilla location, two-acre size, loamy soil, available
irrigation, prior potato crop, and vegetative stage are demo values, not source
evidence. In particular, the BARC soil statement also depends on land type,
which the demo does not provide.

## Rejected or insufficient claims

- **Comilla potato class:** not retrieved or verified; national totals cannot
  substitute for the local result.
- **Golden Farm field suitability:** rejected as a claim because project demo
  values are not agronomic evidence, and the required land-type context is
  absent.
- **Complete growth-stage sequence and local stage durations:** not found in
  the inspected potato passages; operation timings after sowing are not
  growth-stage definitions.
- **Disease-based early harvest dates:** excluded from M2 because the cited
  statement appears within disease-control material and disease ownership is
  outside M2.
- **Variety-specific harvest scheduling:** no variety was identified for the
  Golden Farm, and the handbook explicitly says the harvest interval depends
  on variety.

Other inspected BARC pages are recorded in the existing source register. This
package does not modify that register, database rows, migrations, models, M2
services, or any other module.

## Update — 2026-10-08

The original package stays as research. Production knowledge is now created by
`python -m scripts.import_reference_data` from pinned captures of BARC's
Agri-Advisory Portal and crop-zoning API (see `source_register.json` and
`barc_portal_claims.json`):

- **Accepted:** potato is suitable on high land with loam soil (POTATO-002,
  narrowed). The portal's English and Bangla text both state this; values
  stated in only one language are excluded.
- **Rejected because the portal's two language versions disagree:** sowing
  window (POTATO-004), irrigation timing (POTATO-005), and the crop-wide
  harvest interval (POTATO-006).
- **Variety durations:** 68 potato varieties have a published duration, which
  M2 uses for a harvest window when the season has a variety and planting
  date. Four varieties publish no duration and are not used.
- **Comilla / Cumilla:** upazila suitability distributions for all 16 current
  Cumilla upazilas are regional context only. The legacy "Comilla" upazila
  snapshot is kept but no longer matches current upazila names.
- **Still missing:** growth-stage definitions, initial tasks, and
  disease-independent harvest maturity indicators for potato. BARI's 10th
  edition handbook (December 2024) could not be machine-verified (SutonnyMJ
  encoding), so season plans remain unavailable.

