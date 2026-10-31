# Reviewed crop-calendar data for the planting-window advisory

Public source references are separate: `/advisor/calendar-references` reads
`app/data/m2_knowledge_sources/brri_crop_calendar_references.json` without creating
approved knowledge rows. The public `/advisory` uses an explicitly provisional
rainfall definition and district cache; cultivar GDD and recommended shifts are
null until reviewed rules support them. Source-checking does not fill reviewer IDs.

The authenticated M2 endpoint intentionally returns `insufficient_data` until
an `AgriculturalKnowledge` row for the selected crop satisfies all of these:

- `category == "crop_calendar"`
- `review_status == "approved"`, with both `reviewed_by` and `reviewed_at`
- its JSON `content` has the structure below; values must come from the cited,
  reviewed agronomic source, not from an LLM or a synthetic fixture

The numeric values below only illustrate the JSON shape. They are not
validated Bangladesh crop-calendar or GDD recommendations and must not be
loaded into production as-is.

```json
{
  "planting_window": {
    "season_start_month": 6,
    "season_start_day": 1,
    "season_end_month": 10,
    "season_end_day": 31
  },
  "gdd": {
    "base_temperature_c": 10,
    "cap_temperature_c": 30
  }
}
```

The API reports observed rainfall-onset and GDD evidence. It does not currently
calculate a planting-date adjustment. A future adjustment must be derived from
a reviewed crop calendar and checked against the relevant agronomic and farm
constraints; an observed climate shift alone is not enough. The output is not a
field-scale measurement or a yield guarantee.

POWER requests cover 2001-01-01 through 2025-12-31 for the saved farm
coordinates and are cached under `CLIMATE_CACHE_DIR`. Every year must have
complete daily values for its configured season to enter the onset samples.
The UI reports the approximately 50 km area-level scale and the retrieval/cache
state alongside the results.
