# OSS tech spine

Agent-editable infrastructure spine for a **10-acre** closed-loop biotech / regenerative site (660×660 ft), aligned to a four-zone Gemini design. The project overview stays in the root [README](../README.md).

| Zone | Acres | Role |
|------|------:|------|
| 1 Earth Habitat | 0.75 | Earth-sheltered cells (design min ≥50% submersion; sim baseline 70%) |
| 2 Climate Canopy | 1.75 | Controlled canopy; **algae nutrient density primary**, biofuel secondary |
| 3 Outdoor Production | 4.5 | Outdoor ag / open production |
| 4 Buffer / Edge | 3.0 | Ecological buffer, access, utilities |

Energy grounding (Loop report): ~**41 kWh/day** for a 2-cell farm; ~**12%** savings from earth-sheltering.

## Layout

```
loopBiotek/
  AGENTS.md              # how agents edit (formats, IFC SoR, claim beads, run sims)
  biology/               # CASCADE.md — Stage 1 worms; Stage 2+ closed until Rod clears the gate
  site/                  # site.yaml + parcels.geojson + dem/
  land/                  # allocation.yaml + QGIS/GRASS/Whitebox workflow
  water/                 # EPANET stub.inp
  waste/                 # SWMM stub.inp + QSDsan notes
  power/                 # OpenDSS stub.dss + GridLAB-D/pvlib notes
  buildings/             # IFC SoR; create/edit scripts; models/
  algae/                 # cell.yaml (Zone 2 nutrients)
  climate/thermal-model/ # envelope sim + outputs (pre-existing)
  economics/             # points at reference/loop_params.xlsx
  architecture/          # layers + commercial funnel
  reference/             # PDF, notebooks, xlsx (pre-existing)
  .venv/                 # project Python env
```

## Venv

```bash
cd /workspace/loopBiotek
source .venv/bin/activate
# Core: numpy, matplotlib, ifcopenshell, pyyaml
# Also installed: wntr, OpenDSSDirect.py
```

## Regenerate climate charts

```bash
cd /workspace/loopBiotek
.venv/bin/python climate/thermal-model/climate_envelope_sim.py
```

Writes PNGs under `climate/thermal-model/outputs/` (`24h_temps_pressure.png`, `heatmap_cross_section.png`, `submersion_sensitivity.png`, `site_layout_10acre.png`). Details: `climate/thermal-model/README.md`.

## How agents extend `site.yaml`

1. Edit zone `acres` / `purpose` / elevation notes in `site/site.yaml`.
2. Update matching polygons in `site/parcels.geojson` (local feet, SW origin).
3. Mirror purposes into `land/allocation.yaml`.
4. If Zone 1 cell geometry changes, regenerate IFC via `buildings/scripts/` and re-run the climate sim if submersion or envelope params shift.
5. Follow `AGENTS.md` (claim bead; IFC not DWG as SoR).

## Prove buildings chain

```bash
.venv/bin/python buildings/scripts/create_zone1_cell.py  # → buildings/models/zone1_cell_v1.ifc
.venv/bin/python buildings/scripts/edit_zone1_cell.py    # → buildings/models/zone1_cell_v2.ifc
```

See `buildings/PROOF.md` for the documented agent edit.
