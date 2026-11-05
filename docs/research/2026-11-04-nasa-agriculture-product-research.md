# NASA agriculture products for a Rajshahi and Chattogram rotation advisor

Research date: 2026-11-04. This is a product and literature assessment, not evidence that these products have been downloaded into FieldShift. Public catalog coverage does not prove valid observations over either pilot area: the acquisition inventory must establish that.

## Product selection and scientific role

### SMAP: distinguish a retrieved surface observation from modeled root-zone moisture

**Candidate observation:** SPL3SMP_E Version 6, daily composite on the 9 km EASE-Grid 2.0 (EPSG:6933), available from 2015-03-31, HDF5 with Earthdata Login. It estimates surface moisture; inspect AM/PM retrieval and surface-quality flags, water/frozen-ground/vegetation conditions, and fill values before aggregation. The 9 km posting does not imply independent 9 km measurements; the radiometer footprint is broader. Source: [NSIDC product and quality documentation](https://nsidc.org/data/spl3smp_e/versions/6).

**Candidate root-zone context:** SPL4SMGP Version 8, 9 km, three-hour time averages from 2015-03-31. It assimilates radiometer brightness temperatures into a land-surface model. Root-zone values are model estimates, not a sensor directly measuring underground. V8 precipitation outside North America/high latitudes uses IMERG V07, so SMAP-L4 and IMERG must not count as independent confirmations. A current NSIDC notice identifies geolocation problems for 2026-05-14 through 2026-07-28 and pending reprocessing: initially use 2015–2025 and inventory affected 2026 files explicitly. Source: [NSIDC SPL4SMGP V8](https://nsidc.org/data/spl4smgp/versions/8).

SMAP surface and root-zone moisture represent approximately 0–5 cm and 0–100 cm respectively, in volumetric fraction (m³/m³). Proposed role: historical moisture percentiles and area-level dry/wet context during each crop's establishment period. Do not infer field trafficability, irrigation litres, soil texture, fertility, or paddy water depth from a grid value alone. Depth/units reference: [ORNL soil-moisture product comparison](https://daac.ornl.gov/soilmoisture/guide.html).

### ECOSTRESS: surface temperature and evapotranspiration are distinct products

**LST:** ECO_L2T_LSTE Version 3 is active, 70 m tiled UTM data, variable observation times, record beginning 2018-07-09. Use LST, error, cloud/water masks and QC; verify units and scale from each selected asset. It is an instantaneous surface-temperature observation, not daily 2-m air temperature or a crop's GDD input. Source: [NASA V003 product](https://doi.org/10.5067/ECOSTRESS/ECO_L2T_LSTE.003).

**ET:** ECO_L3T_JET Version 2 provides 70 m instantaneous/daytime ET components from modeling. ET is not obtained by renaming LST. Pin JET separately from LSTE because version numbers differ. Preserve acquisition time, daytime/instantaneous convention and asset units; do not sum an instantaneous energy-flux band into daily millimetres without the documented integration/conversion. Source: [NASA JET product](https://data.nasa.gov/dataset/ecostress-tiled-evapotranspiration-instantaneous-and-daytime-l3-global-70-m-v002-391c7), [ECOSTRESS product/algorithm table](https://ecostress.jpl.nasa.gov/data/atbds-summary-table).

Proposed role: optional recent thermal/evaporative stress evidence when clear-sky acquisitions exist. Compare like observation times and season/land cover; a hotter bare soil pixel is not proof of crop water stress. ISS coverage and clouds produce irregular gaps. A scene-level acquisition check is a prerequisite for either pilot.

### GPM: IMERG rainfall

Select **GPM_3IMERGDF Version 07 Final daily precipitation**, on 0.1° cells; use the historical 2001–2025 window to match current POWER analysis. IMERG's native retrieval cadence is half-hourly; daily files avoid accidentally treating mm/hour as mm/day. Final is retrospectively gauge-adjusted and delayed roughly months; it cannot drive same-day alerts. Early/Late streams must be separately labeled and must not silently replace Final in historical statistics. Source: [NASA daily Final product](https://data.nasa.gov/dataset/gpm-imerg-final-precipitation-l3-1-day-0-1-degree-x-0-1-degree-v07-gpm-3imergdf-at-ges-dis-13ed8).

The current V07 archive exposes 1998–1999 directories although some general descriptions still say 2000. Query and record granule dates rather than copying a blanket mission start; the proposed 2001 start avoids this extension issue. Source: [GES DISC daily archive](https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGDF.07/contents.html).

Proposed role: spatial rainfall, seasonal totals, dry spells and heavy-rain exposure; compare POWER and IMERG over matched periods, retain disagreement, and never average the two by default. Satellite precipitation has regional/topographic bias and is not a rain gauge on the farmer's land.

### Landsat: smaller-area vegetation evidence

Select USGS **Landsat 8/9 Collection 2 Level-2 Surface Reflectance**, 30 m optical pixels. Landsat 8 starts in 2013 and Landsat 9 in 2021; a single satellite repeats about 16 days, but clouds reduce usable sampling. Apply QA_PIXEL/QA_RADSAT and aerosol checks before vegetation indices. Reflectance conversion is `DN × 0.0000275 − 0.2`; because of the offset, computing NDVI from raw DN gives a different result. Source: [USGS Collection 2 products](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products), [USGS scale factors](https://www.usgs.gov/faqs/how-do-i-use-a-scale-factor-landsat-level-2-science-products).

Proposed role: neighborhood cropland/vegetation fractions, seasonal green-up and possible bare periods after QA and sufficient observations. NDVI is a dimensionless greenness proxy, not a crop identity, nitrogen test, biomass measurement or yield prediction. A small parcel may occupy only part of one pixel. Monsoon clouds can make an entire period indeterminate.

### MODIS: longer, coarser vegetation history

Select **MOD13Q1.061**, Terra NDVI/EVI, 250 m sinusoidal grid, 16-day composites since 2000. Scale vegetation-index integers by 0.0001 and apply product QA. The composite selects a suitable observation; it is not a simple mean of every day and does not establish a planting date to daily precision. Source: [NASA MOD13Q1 V061](https://doi.org/10.5067/MODIS/MOD13Q1.061).

Proposed role: long seasonal neighborhood vegetation context, phenology stability and comparison with farmer-reported crop history. Mixed pixels and cloud/smoothing effects prevent treating NDVI peaks as definitive crop labels. MODIS and Landsat should retain separate source series and bias/overlap diagnostics, not be concatenated as identical sensors. New VIIRS continuity can be a later extension; verify the specific product before adding it.

### NASA POWER: retain the existing historical backbone

POWER Daily API supports UTC or local-solar-time daily series beginning in 1981, with parameter-specific availability to verify. Select current FieldShift's 2001–2025 range for comparable historical analysis. POWER includes gridded reanalysis and satellite-derived products, not only direct satellite measurements. Source: [POWER daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/).

Meteorological source grids are 0.5° × 0.625° and solar grids 1° × 1°. Keep PRECTOTCORR (mm/day), T2M/T2M_MIN/T2M_MAX (°C), and ALLSKY_SFC_SW_DWN (MJ/m²/day), with units verified in the actual API response. Humidity/wind may support a later documented reference-ET method. Proposed role: onset and dry spells, heat exposure, reviewed crop-specific GDD and climatological context. No-key API; cache immutable query/response metadata. Source: [POWER official API tutorial and resolution description](https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/).

### GRACE/GRACE-FO: regional total water storage, not a village groundwater sensor

The current JPL mascon page labels **RL06.3_v04**. Monthly water-storage anomalies are distributed at 0.5° sampling, but native support is about 3° mascons; neighboring output pixels are not independent. The baseline is 2004–2009. Retain release, mascon ID, uncertainty, baseline, gaps and coastal leakage treatment. Source: [JPL mascon documentation](https://grace.jpl.nasa.gov/data/get-data/jpl_global_mascons/).

GRACE observes **total water-storage anomaly**, not groundwater alone. A groundwater residual requires estimates of soil water, surface water and other relevant stores, plus propagated errors and validation; rainfall-minus-ET is not a groundwater measurement. Proposed role: regional long-term water-pressure context for irrigation-intensive sequences. Do not generate distinct Rajshahi/Chattogram field water budgets from interpolated GRACE pixels. The GRACE-to-GRACE-FO mission gap must remain visible.

### SRTM: terrain context

Select **SRTMGL1 Version 003**, global one arc-second (approximately 30 m) elevation, acquired during 2000-02-11–21. It is a static historic surface-elevation product, not a current flood-depth sensor. Source: [NASA SRTM catalog](https://data.nasa.gov/dataset/nasa-shuttle-radar-topography-mission-global-1-arc-second-v003-e47e1), [NASA SRTM quick guide](https://www.earthdata.nasa.gov/s3fs-public/2025-05/SRTM_Quick_Guide.pdf).

Proposed role: derive slope on a metric grid before aggregating, and provide broad terrain screening. At Chattogram, agricultural lowlands, hills, forest, urban and coastal land must be separated. Elevation/slope alone do not determine flood risk, soil erosion tonnes or drainage suitability. Avoid calculating slope after averaging a DEM to a coarse grid. Buildings, vegetation, void fills and small floodplain relief require caution.

### GEDI: optional woody vegetation, not seasonal crop biomass

**GEDI L4A Version 3** now has a 2026-09-02 guide and DOI 10.3334/ORNLDAAC/2508. It predicts aboveground biomass density (Mg/ha) with standard errors at sparse ~25 m footprints, about 60 m along-track and 600 m between tracks. Record begins 2019; observations pause March 2023–April 2024. V3 quality schema differs from V2: use the release-specific `l2_quality_flag_rel3`, `l4_quality_flag_rel3`, outlier and prediction-domain flags. Source: [ORNL V3 guide](https://daacweb-prod.ornl.gov/GEDI/guides/GEDI_L4A_AGB_Density_V3.html).

Proposed role: optional Chattogram agroforestry/woody-landscape context with sample counts and uncertainty. Rasterizing sparse shots does not create wall-to-wall observations. It does not establish the rice/maize crop's biomass, soil carbon change or carbon benefit from switching rotations. An annual-crop advisor should mark it non-applicable where no defensible woody-land use exists.

## Existing research and what FieldShift can borrow

1. **Gumma et al. (2014), Mapping seasonal rice cropland extent and area in the high cropping intensity environment of Bangladesh using MODIS 500m data for the year 2010.** Uses eight-day MODIS and ancillary data with 605 field-plot locations containing crop type, intensity and water-source records. Supports phenology plus local ground-truth validation, not unvalidated NDVI crop recognition. [Research-institute full text](https://oar.icrisat.org/7640/7/Mapping%20seasonal%20rice%20cropland%20extent%20and%20area%20in%20the%20high%20cropping.pdf).
2. **Sustainable crop intensification through surface water irrigation in Bangladesh? A geospatial assessment of landscape-scale production potential (2016).** Combines remote-sensing cropping intensity, freshwater availability, salinity and elevation with farmer observations in southwestern Bangladesh. Supports screening multiple constraints together; its southwestern outcomes are not transferable constants for Rajshahi or Chattogram. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5142720/). Search exposed the abstract; full-page retrieval encountered a browser challenge.
3. **Hasan et al. (2019), Contribution of Rainwater to the Irrigation Requirement for Paddy Cultivation at Tanore Upazila in Rajshahi.** Uses BMD/BMDA data and a stated consumptive-use method. Supports local seasonal water accounting, but published historical results are not today's irrigation prescription and its coefficients require review before reuse. [Publisher paper](https://journals.sagepub.com/doi/10.1177/1178622119837544).
4. **Shamsudduha et al. (2012), Monitoring groundwater storage changes in the highly seasonal humid tropics: Validation of GRACE measurements in the Bengal Basin.** Tests basin-scale GRACE against groundwater evidence. Supports GRACE plus local hydrologic validation; it does not validate village-level GRACE groundwater values. [Publisher DOI](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2011WR010993).
5. **Statistical comparison of satellite-retrieved precipitation products with rain gauge observations over Bangladesh (2018).** Evaluates precipitation products against gauges over 2014–2016. Supports seasonal/regional error assessment before deploying IMERG thresholds. [Publisher DOI](https://www.tandfonline.com/doi/abs/10.1080/01431161.2018.1433890).
6. **Tanim et al. (2021), Evaluation of Spatial Rainfall Products in Sparsely Gauged Region Using Copula Uncertainty Modeling with Triple Collocation.** Tests satellite/reanalysis rainfall and topography-dependent errors in Bangladesh. Supports special attention to Chattogram terrain; copying its adjustment requires methods/data replication. [Publisher DOI](https://ascelibrary.org/doi/abs/10.1061/%28ASCE%29HE.1943-5584.0002071).

These studies establish relevant prior work. None establishes that combining all listed NASA products automatically creates an accurate rotation recommendation.

## Harmonization decisions recommended for the implementation plan

- Preserve native data and QA first; never overwrite input rasters with reprojected outputs.
- Use one explicit equal-area **analysis grid** for compatible regional layers, with cell ID, CRS, transform and extent stored in a versioned manifest. Fine data can aggregate to it with valid-area weights. Coarse grids remain coarse-support context even if represented on the analysis grid.
- Keep a fine terrain/optical layer and a coarse climate/moisture layer when the native scales differ greatly. A common grid is an indexing and integration choice, not an increase in independent spatial information.
- Do not force GRACE or sparse GEDI shots into the same numerical crop-cell score. Join GRACE region/mascon context; aggregate GEDI only within justified woody-land polygons with enough samples.
- Reject missing/invalid data before arithmetic. Store valid fraction, sample count, acquisition dates, QA policy, native support and temporal aggregation in every derived feature.
- Separate sums (daily rainfall to season), means (temperature), robust summaries (NDVI/LST observations), static values (terrain), and monthly regional storage. Never repeat monthly GRACE into daily rows and call it daily observed data.
- Maintain 2001–2025 POWER/IMERG/MODIS long history, 2015–2025 moisture overlap, and acquisition-specific ECOSTRESS/GEDI windows. Do not claim 25-year trends for SMAP, ECOSTRESS or GEDI.
- Evaluate rainfall sources and moisture predictors with held-out years and spatial blocks; account for SMAP-L4/IMERG shared inputs and mixed optical pixels.
- Validate units, QA and availability with actual pilot granules before final dependency/product locks. This research did not download protected products or inspect pilot granule arrays.
