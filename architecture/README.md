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
| Live cascade | `biology/` | `CASCADE.md`; worm MC is external |
| Economics | `economics/` → `reference/` | xlsx / PDF; gates in `biology/CASCADE.md` |

## Commercial funnel (high level)

1. **Reference site** (this repo) — prove closed-loop cells on 10 acres.
2. **Pilot** — 2-cell energy baseline (~41 kWh/day) with ≥50% earth submersion.
3. **Productize** — agent-editable IFC + network stubs for rapid site adaptation.
4. **Scale** — replicate zone template; nutrient-primary algae as value capture; biofuel secondary.

## Capital cascade (funds the funnel)

Before scaling the commercial funnel, cash compounds through live biology:

1. Worms (forward-sell to poultry farms)
2. Crickets + isopods (rollie pollies)
3. Land + semi-underground vertical greens + algae (Zone 1–2)
4. Quail (vertical integrate)
5. Aquaponics
6. Community QoL from **surplus only**

SoR: [`../biology/CASCADE.md`](../biology/CASCADE.md). **Active: Stage 1 only.** Agents must not open Stage 2+ spend without Rod clearing the Stage-1 gate (≥$2k/mo vermiculture revenue, or a firm prepaid forward runway covering Stage-1 costs).
