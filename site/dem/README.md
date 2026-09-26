# DEM (USGS 3DEP)

Placeholder — no raster checked in yet.

## How to pull

1. Identify AOI from `../parcels.geojson` (reproject local feet to WGS84 / State Plane for the real site).
2. Download USGS **3DEP** 1 m or 10 m DEM via:
   - [USGS National Map Downloader](https://apps.nationalmap.gov/downloader/)
   - `elevation` / `py3dep` / `opentopography` APIs
3. Place GeoTIFF(s) here, e.g. `dem_3dep_1m.tif`.
4. In QGIS / GRASS / WhiteboxTools, clip to site AOI and derive slope, aspect, cut/fill for Zone 1 berms (≥50% submersion design min).

Until a DEM lands, climate sims use the flat-site + submersion % parameter in `climate/thermal-model/`.
