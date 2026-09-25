# Site

Reference **10-acre** LoopBiotek parcel (660×660 ft) with four Gemini-aligned zones.

| File | Role |
|------|------|
| `site.yaml` | Acres, zone purposes, elevation / submersion notes, energy baseline |
| `parcels.geojson` | Boundary + 4 zone polygons (local feet, SW origin) |
| `dem/` | USGS 3DEP DEM pull instructions (placeholder until downloaded) |

## Agent edits

1. Change acres / purposes in `site.yaml`.
2. Update polygon coordinates in `parcels.geojson` so areas stay consistent.
3. Mirror zone purposes into `../land/allocation.yaml`.
4. Do **not** treat CAD drawings as source of record — site geometry lives here in YAML + GeoJSON.
