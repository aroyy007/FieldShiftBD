# Dhaka and Chattogram NASA POWER reference points

## Verified station references

Bangladesh Meteorological Department (BMD), *Changing Climate of Bangladesh*, table “Observational sites in Bangladesh,” lists:

| Reference station | WMO ID | Latitude | Longitude | Elevation |
| --- | ---: | ---: | ---: | ---: |
| Dhaka | 41923 | 23.78° N | 90.38° E | 8.5 m |
| Chattogram Patenga | 41978 | 22.22° N | 91.80° E | 5.5 m |

These are BMD station coordinates, usable as documented reference points for a NASA POWER point request. Chattogram Patenga is distinct from Chattogram Ambagan (WMO 41977; 22.35° N, 91.82° E); do not substitute the Ambagan point when the intended reference is Patenga.

## NASA POWER provenance and request semantics

- The official [Daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) describes daily point time series, offers UTC and Local Solar Time (LST), and says daily requests default to LST. Include `time-standard=UTC` explicitly for reproducible calendar-day comparisons (or explicitly document LST if that is the chosen convention). Daily records are available from 1981-01-01 through near real time; the actual requested and returned date range should be recorded with each cache artifact.
- A point request represents a single latitude/longitude time series, not a measurement at the BMD station. POWER values represent grid-cell estimates/averages. Its [data-source documentation](https://power.larc.nasa.gov/docs/methodology/data/sources/) identifies primary meteorology as GMAO MERRA-2 at 0.5° × 0.625° and primary solar data as CERES SYN1deg at 1° × 1°. The same page notes higher-resolution precipitation from GPM IMERG; NASA documents this separately as `IMERG_PRECTOT` at 0.1° (~10 km), daily UTC, available from June 1, 1998. Therefore, “POWER at the station coordinate” must not be presented as station-observed or field-scale weather, and precipitation provenance must name the selected parameter/source.
- The [POWER parameter dictionary](https://power.larc.nasa.gov/parameters/) is the authoritative catalog for parameter identifiers, communities, and units. For this project, record the exact API parameter IDs and returned units for temperature, precipitation, humidity, and solar radiation; do not infer a common resolution/source just because parameters are in one response. NASA's [meteorology methodology and validation page](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/) identifies MERRA-2/GEOS meteorological provenance, reports daily temperature in °C and precipitation in mm/day, describes precipitation correction (`PRECTOTCORR`), and documents comparisons against surface observations. The [derived meteorological parameters page](https://power.larc.nasa.gov/docs/methodology/data/derived/met-derived-parameters/) explains that relative humidity is calculated from meteorological inputs and is a grid-averaged estimate.
- The current historical-cache request in this repository uses `PRECTOTCORR` (rainfall, mm/day), `T2M` (daily temperature, °C), and `ALLSKY_SFC_SW_DWN` (daily all-sky surface shortwave radiation; cache expects MJ/m²/day). These are separate POWER parameters, and the response `parameters` metadata should be retained as the authority for returned units. The separate weather-context request also uses `RH2M`; NASA documents relative humidity as calculated from meteorological inputs. If substituting `IMERG_PRECTOT` for rainfall, label it explicitly: it is a distinct, shorter-history, higher-resolution source, not a continuation of `PRECTOTCORR`.
- NASA's [temporal API overview](https://power.larc.nasa.gov/docs/services/api/temporal/) defines point data as a time series for one coordinate and the selected date span. Preserve the request coordinates, parameter IDs, community, UTC/LST setting, requested/returned dates, API retrieval time, and whether the response came from live retrieval or a cache in the dataset provenance.

## Caveats for use

Station coordinates are a transparent anchor for selecting a POWER grid estimate; they do not make the estimate a BMD station observation. The grid varies by source/parameter, so a single “about 50 km” label is not accurate for every returned variable. For Dhaka/Chattogram climate trends, use one consistent time standard and parameter/source across years; do not mix the long MERRA-2 rainfall history with the shorter IMERG series without labeling that change. No data were downloaded or altered for this note.

## Official sources

- BMD, [*Changing Climate of Bangladesh* (2024), observational-station table](https://www.bmd.gov.bd/file/2024/02/27/pdf/162368.pdf).
- NASA POWER, [Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/).
- NASA POWER, [Temporal API overview](https://power.larc.nasa.gov/docs/services/api/temporal/).
- NASA POWER, [Data sources](https://power.larc.nasa.gov/docs/methodology/data/sources/).
- NASA POWER, [Meteorology data sources and validation](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/).
- NASA POWER, [Derived meteorological parameters](https://power.larc.nasa.gov/docs/methodology/data/derived/met-derived-parameters/).
- NASA POWER, [Parameter dictionary](https://power.larc.nasa.gov/parameters/).
