# Architecture

LoopBiotek stack layers and commercial funnel (summary).

## Layers (agent-editable spine)

| Layer | Path | SoR formats |
|-------|------|-------------|
| Site / land | `site/`, `land/` | YAML, GeoJSON |
| Climate | `climate/thermal-model/` | Python sim + PNG outputs |
| Water | `water/` | EPANET `.inp` |
| Waste | `waste/` | SWMM `.inp` + QSDsan |
| Power | `power/` | OpenDSS `.dss` |
| Buildings | `buildings/` | **IFC** |
| Algae | `algae/` | YAML + QSDsan/PM2 |
| Economics | `economics/` → `reference/` | xlsx / PDF |

## Commercial funnel (high level)

1. **Reference site** (this repo) — prove closed-loop cells on 10 acres.
2. **Pilot** — 2-cell energy baseline (~41 kWh/day) with ≥50% earth submersion.
3. **Productize** — agent-editable IFC + network stubs for rapid site adaptation.
4. **Scale** — replicate zone template; nutrient-primary algae as value capture; biofuel secondary.
