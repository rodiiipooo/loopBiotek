# AGENTS — how to edit LoopBiotek

This tree is the **agent-editable spine**. Prefer structured text over binary CAD.

## File formats (SoR)

| Domain | Source of record | Do not use as SoR |
|--------|------------------|-------------------|
| Site geometry | `site/site.yaml`, `site/parcels.geojson` | DWG, proprietary GIS locks |
| Land purposes | `land/allocation.yaml` | ad-hoc notes |
| Buildings | `buildings/models/*.ifc` | **DWG** (AutoCAD only via DXF import/export bridge) |
| Water | `water/*.inp` (EPANET) | undocumented spreadsheets |
| Waste | `waste/*.inp` (SWMM) + QSDsan models | — |
| Power | `power/*.dss` (OpenDSS) | — |
| Algae | `algae/cell.yaml` | — |
| Economics | `reference/loop_params.xlsx` | copied numbers without citation |
| Climate | `climate/thermal-model/*.py` + `outputs/` | — |

## Rules

1. **Never treat DWG as SoR.** Round-trip through DXF if CAD review is required; commit IFC + YAML/GeoJSON.
2. **Claim a bead before editing** — leave a short note in the PR / commit / chat claiming the file path you will change (one agent per file when possible).
3. **Extend `site/site.yaml` carefully:** update acres and purposes, then sync `parcels.geojson` polygons and `land/allocation.yaml`.
4. **Buildings:** create/edit IFC with IfcOpenShell scripts or Bonsai/MCP tools; bump version suffix (`_v1` → `_v2`) and document the change in `buildings/PROOF.md` or a changelog.
5. **Run sims after parametric changes:**
   - Climate charts: ` .venv/bin/python climate/thermal-model/climate_envelope_sim.py`
   - Water: WNTR / EPANET on `water/stub.inp`
   - Power: OpenDSSDirect on `power/stub.dss`
6. **Do not delete** `climate/` or `reference/`.
7. Use the project venv: `/workspace/loopBiotek/.venv`.

## Quick prove path (buildings)

```bash
cd /workspace/loopBiotek
.venv/bin/python buildings/scripts/create_zone1_cell.py
.venv/bin/python buildings/scripts/edit_zone1_cell.py
# Inspect buildings/PROOF.md
```
