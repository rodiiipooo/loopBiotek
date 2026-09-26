# Climate envelope thermal model

Coupled transient simulation of a LoopBiotek Zone-1 cell: **room air + structural mass + glazed-roof water loop + earth conduction**, with explicit pipe geometry and thermal-expansion pressure.

## How to run

```bash
cd /workspace/loopBiotek
source .venv/bin/activate          # or: .venv/bin/python
python climate/thermal-model/climate_envelope_sim.py
```

Regenerates four PNGs under `outputs/`:

| File | Contents |
|------|----------|
| `24h_temps_pressure.png` | Outdoor / room / water T vs time; twin-axis loop pressure (kPa) |
| `heatmap_cross_section.png` | Vertical cross-section heat maps at 06:00 / 12:00 / 18:00 / 00:00 |
| `submersion_sensitivity.png` | Peak room T & HVAC-proxy kWh vs submersion % |
| `site_layout_10acre.png` | Top-down 660×660 ft 4-zone layout |

## Equations (lumped capacitance)

**Room (air + concrete slab / berm mass)**

\[
C_{\mathrm{room}}\dot T_r = Q_{\mathrm{solar→room}} + Q_{\mathrm{int}}
  - UA_{rw}(T_r - T_w)
  - U_{\mathrm{glaze}}A_{\mathrm{roof}}(T_r - T_\infty)
  - U_{\mathrm{earth}}A_{\mathrm{buried}}(T_r - T_{\mathrm{soil}})
  - U_{\mathrm{wall}}A_{\mathrm{exposed}}(T_r - T_\infty)
  - \dot m_{\mathrm{inf}} c_p (T_r - T_\infty)
\]

\(C_{\mathrm{room}}\) includes air plus a 20 cm concrete slab and a berm-coupled wall mass fraction (~57 MJ/K for the default cell).

**Roof-loop water (exterior absorber film + serpentine)**

\[
C_w\dot T_w = UA_{rw}(T_r - T_w) + Q_{\mathrm{solar→water}}
  - UA_{\mathrm{reject}}(T_w - T_{\mathrm{soil}})
\]

Ground-reject UA scales strongly with submersion (earth tubes in the berm + buried returns), ~3.7 kW/K at 70% for the default 100 m² roof — sized so peak solar can be dumped on ~12–15 K ΔT to 18 °C soil.

**Pipe geometry → gallons**

Serpentine length \(L_{\mathrm{pipe}} \approx N_{\mathrm{runs}} L + \text{U-bends} + \text{headers}\), \(N_{\mathrm{runs}} = W / s_{\mathrm{tube}}\).

\[
V_{\mathrm{pipe}} = \pi (d_i/2)^2 L_{\mathrm{pipe}},\quad
\text{gal} = V\cdot 264.172
\]

Total system gallons = pipe + expansion tank + fittings. Total flow is split across `n_parallel_circuits` so per-circuit velocity stays in the ~0.5–1 m/s PEX range.

**Pressure from thermal expansion**

\[
\Delta P = K_{\mathrm{sys,eff}}\,\beta\,\Delta T_w
\]

with \(K_{\mathrm{sys,eff}}\) softened by the expansion-tank volume fraction (bladder).

**Climate (North Texas summer baseline)**

Diurnal outdoor air: cosine peaking near 15:00 between \(T_{\min}=26\,^\circ\mathrm{C}\) and \(T_{\max}=40\,^\circ\mathrm{C}\). Horizontal irradiance: half-sine from sunrise ≈ 06:25 over a 13.5 h day, noon peak 950 W/m². Override via `ClimateParams`. Simulation runs 48 h and reports the settled last 24 h.

## Defaults (Zone-1 cell)

- Room \(L=W=10\,\mathrm{m}\), \(H=3\,\mathrm{m}\), submersion 70%
- Glazed roof ≈ full plan area; exterior water film catches most solar (`g_water≈0.62`, `g_room≈0.08`)
- 1/2″ PEX (ID ≈ 12.07 mm), 10 cm spacing, 10 parallel circuits, 12 gpm total
- Deep soil \(T_{\mathrm{soil}}=18\,^\circ\mathrm{C}\)
- Report grounding: 2-cell farm ≈ 41 kWh/day; earth-sheltered ≈ −12% (~5 kWh/day)

## Assumptions

- Lumped single-node room+mass and single-node loop fluid (no stratification).
- Exterior absorber disposition: majority of irradiance is intercepted by the water film before entering the room.
- Ground HX capacity increases with submersion; at 0% the loop runs much hotter (see sensitivity plot).
- HVAC-proxy energy on the sensitivity plot is \(\int UA_{\mathrm{proxy}}\max(0,T_r-T_{\mathrm{set}})\,dt\) with \(T_{\mathrm{set}}=28\,^\circ\mathrm{C}\), not a full vapor-compression model.
- Materials: water properties at ~20–40 °C; PEX ID for 1/2″ SDR-9 style tubing.

See also `../../reference/` for the Loop report PDF, notebooks, and xlsx inputs, and `PARAMS_FROM_XLSX.md` for extracted workbook fields.
