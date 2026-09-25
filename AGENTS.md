# AGENTS — how to edit LoopBiotek

This tree is the **agent-editable spine**. Prefer structured text over binary CAD.

Checked in today for the capital cascade: `biology/`, `site/site.yaml`, `land/allocation.yaml`, `architecture/README.md`, and `economics/README.md`. Other paths in the table are the planned spine and are not all present in this repository yet.

Do not commit `.venv`, secrets, or the worm Monte Carlo. That model stays at the external sibling path `/workspace/worm-revenue-model/`.

## File formats (SoR)

| Domain | Source of record | Do not use as SoR |
|--------|------------------|-------------------|
| Site geometry | `site/site.yaml`, `site/parcels.geojson` (geojson planned) | DWG, proprietary GIS locks |
| Land purposes | `land/allocation.yaml` | ad-hoc notes |
| Buildings | `buildings/models/*.ifc` (planned) | **DWG** (AutoCAD only via DXF import/export bridge) |
| Water | `water/*.inp` (EPANET, planned) | undocumented spreadsheets |
| Waste | `waste/*.inp` (SWMM, planned) + QSDsan models | — |
| Power | `power/*.dss` (OpenDSS, planned) | — |
| Algae | `algae/cell.yaml` (planned) | — |
| Live cascade | `biology/CASCADE.md` | ad-hoc chat plans |
| Economics | cascade gates in `biology/CASCADE.md`; workbook in `reference/` when present | copied numbers without citation |
| Climate | `climate/thermal-model/*.py` + `outputs/` (planned) | — |

## Rules

1. **Never treat DWG as SoR.** Round-trip through DXF if CAD review is required; commit IFC + YAML/GeoJSON when those files exist.
2. **Claim a bead before editing** — leave a short note in the PR / commit / chat claiming the file path you will change (one agent per file when possible).
3. **Extend `site/site.yaml` carefully:** update acres and purposes, then sync `parcels.geojson` polygons (when present) and `land/allocation.yaml`.
4. **Buildings:** create/edit IFC with IfcOpenShell scripts or Bonsai/MCP tools; bump version suffix (`_v1` → `_v2`) and document the change. Do not invent those models in a cascade-only change.
5. **Run sims after parametric changes** when the sim trees exist in the checkout. Do not assume a project `.venv` is committed here.
6. **Do not delete** `biology/CASCADE.md`. Do not delete `climate/` or `reference/` if they are added later.
7. Worm population and forward-book models live under `/workspace/worm-revenue-model/`. Link results back into `economics/` when citing cash gates. Do not copy that code into this repo.

## Live biology cascade

8. **Capital cascade SoR is `biology/CASCADE.md`.** Order stays worms → crickets+isopods (rollie pollies) → land + semi-underground vertical greens + algae → quail → aquaponics → community QoL from surplus only.
9. **Stage 1 (worms) is the only active spend** until vermiculture revenue is at least $2k/mo, or a firm prepaid forward runway covers Stage-1 costs. Agents must not open Stage 2+ spend without Rod clearing that gate.
10. Firm forward book is P10 surplus only. Do not sell the median (P50) herd forward.
