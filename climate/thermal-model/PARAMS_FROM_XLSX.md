# Parameters extracted from `reference/loop_params.xlsx`

The workbook is a **quail-kit CAPEX / cash-flow** model (not thermal). Useful fields for LoopBiotek planning; none override the climate-envelope defaults directly, but they size the Zone-1 cell load context.

## Scale & production (sheet `1_Inputs`, `2_Equipment_Sizing`)

| Parameter | Value | Unit / note |
|-----------|------:|-------------|
| Community residents H | 20 | people (scenarios 10/20/40/77) |
| Hens per kit (full) | 200 | birds |
| Eggs / incubator batch | 216 | per kit |
| Incubation cycle | 21 | days → 72 eggs/wk/kit bottleneck |
| Kits for H=20 meat constraint | 1 | ceil(H / 42.8) |
| RULE OF THUMB | — | 1 kit ≈ 43 people meat, ≈ 80 eggs |

## Capex highlights (`3_Capex`, `1_Inputs`)

| Item | Cost |
|------|-----:|
| Quail Professional Kit | $3,729.96 |
| Shelter retrofit (site, once) | $3,000 |
| Cold storage | $800 |
| Utility hookups | $500 |
| Typical balanced CAPEX (H=20, 1 kit) | **$9,917** |

## Cash flow (`4_Monthly_CashFlow`, `5_Scenarios`)

- Steady revenue (H=20, scenario B): **$1,199 / mo**; opex **$552 / mo**; net **$647 / mo**
- Cash break-even month **25**; economic (incl. food value) month **15**
- Scenario C (2 kits) cash break-even ~15 mo, net ~$1,980 / mo

## Future phases (`7_Future_Phases`) — climate-relevant

| Module | Rough CAPEX |
|--------|------------:|
| Greenhouse / season extension | ~$3,000–8,000 |
| Sprout room | ~$1,000–2,000 |
| Tilapia (tanks, filtration) | ~$3,000–5,000 |

## Not in xlsx (taken from Loop report PDF instead)

- 2-cell farm ≈ **41 kWh/day**; incubator+brooder ≈ **19 kWh/day**
- Earth-sheltered ≈ **−12%** energy (~5 kWh/day)
- Off-grid energy package: 5 kW PV + 20 kWh battery (report §7)

**Thermal model implication:** `Q_internal_W ≈ 800 W` cell-scale continuous proxy is consistent with a share of the ~19 kWh/day incubator/brooder load plus lights/animals (~0.8 kW × 24 h ≈ 19 kWh if that load were continuous; in practice duty-cycled — kept as a conservative daytime-biased internal gain).
