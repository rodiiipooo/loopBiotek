# Land

Zone allocation and earthwork workflow for the 10-acre reference site.

- **Allocation SoR:** `allocation.yaml` (must match `../site/site.yaml` acres / purposes).
- **Geometry SoR:** `../site/parcels.geojson`.

## Suggested toolchain

| Tool | Use |
|------|-----|
| **QGIS** | Digitize / edit parcels, style zones, export DXF for CAD bridge if needed |
| **GRASS GIS** | Watershed / terrain analysis on 3DEP DEM |
| **WhiteboxTools** | Fast DEM processing (depression fill, slope, viewshed) |

Workflow sketch: pull DEM → clip → slope/aspect → mark Zone 1 berm footprints → update `allocation.yaml` purposes → regenerate climate layout chart.
