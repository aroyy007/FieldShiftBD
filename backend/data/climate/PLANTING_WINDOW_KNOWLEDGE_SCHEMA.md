# Reviewed crop-calendar data for the planting-window advisory

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
    "season_end_day": 31,
    "onset_shift_policy": "shift_window_by_observed_onset_delta"
  },
  "gdd": {
    "base_temperature_c": 10,
    "cap_temperature_c": 30
  }
}
```

The adjustment policy must be explicitly supported by the reviewed source.
If it is absent, the API may not convert an observed climate shift into a crop
planting adjustment. The output reports historical evidence and the adjustment
in days; it is not a field-scale measurement or a yield guarantee.

POWER requests cover 2001-01-01 through 2025-12-31 for the saved farm
coordinates and are cached under `CLIMATE_CACHE_DIR`. Every year must have
complete daily values for its configured season to enter the onset samples.
The UI reports the approximately 50 km area-level scale and the retrieval/cache
state alongside the results.
