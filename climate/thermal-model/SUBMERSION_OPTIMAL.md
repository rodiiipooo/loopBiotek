# Optimal submersion fraction

Planning output for how much of a cell's height should sit below grade. The legacy summer illustration still uses `RoomParams.submersion = 0.70` so the free-float charts stay comparable. That 70% is not the recommendation. `submersion_opt.py` sweeps the fraction \(f \in [0,1]\) and reports the feasible \(f^\star\) that minimizes annual temperature-maintenance energy.

This is thermal research for layout. It does not open Stage 2+ cascade spend. `biology/CASCADE.md` is unchanged. The Loop report's ~41 kWh/day and ~12% earth-shelter figures are still the food-system load grounding; they are not this sweep.

## Run

From the repo root (the tree that contains `climate/`):

```bash
.venv/bin/python climate/thermal-model/submersion_opt.py
# same entry point:
.venv/bin/python climate/thermal-model/climate_envelope_sim.py --optimize
```

Writes `climate/thermal-model/outputs/submersion_optimal.json` and `submersion_optimal.png`.

Other flags: `--f-step`, `--hours`, `--latitude`, `--t-mean-soil`, `--climate-csv`.

## Objective

For each month, a design day is integrated with the existing room + water-loop Euler step (`climate_envelope_sim.simulate`). An ideal thermostat holds room air in the use-type band \([T_\mathrm{heat}, T_\mathrm{cool}]\). Heating and cooling are the thermal kilowatt-hours delivered to the room (not site electricity).

\[
E(f) = \sum_m N_m \left(E_{\mathrm{heat},m}(f) + E_{\mathrm{cool},m}(f)\right)
\]

\(f^\star\) is the feasible grid point with the smallest \(E\). Ties go to the smaller \(f\) (less excavation). The structural mass is slow, so each day starts at the daily-mean two-node balance, clamped into the band, and the integrator reports the last 24 h of a 72 h run. On the default cases that window closes to within a few hundredths of a kelvin.

Electric energy in the JSON divides heating by COP 2.5 and cooling by COP 3.0. Those COPs are an ASSUMPTION and are not the objective.

## Geometry

\[
P = 2(L+W),\qquad
A_\mathrm{buried} = P\, f\, H,\qquad
A_\mathrm{exposed} = P\, (1-f)\, H
\]

The floor area \(LW\) is always in soil contact. Its depth is the bottom of the wall, \(z_\mathrm{floor} = \max(f H, 0.05\,\mathrm{m})\). The buried-wall sink is the wall centroid, \(z_\mathrm{wall} = \max(f H / 2, 0.05\,\mathrm{m})\). Roof-loop tubes, when they are on, see \(z_\mathrm{tube} = \max(f H, 0.30\,\mathrm{m})\).

## Outdoor air and \(T_\mathrm{soil}(z)\)

Each month is one diurnal design day: outdoor temperature is the existing cosine between that month's \(T_\min\) and \(T_\max\), and horizontal irradiance is the existing half-sine whose daily integral matches the month's global horizontal irradiation.

Undisturbed soil is a one-harmonic wave (Kusuda form). ASSUMPTION phase: the surface is warmest on day 205.

\[
T_\mathrm{soil}(z,t) = T_\mathrm{mean} + A_\mathrm{surf}\, e^{-z/D} \cos\left(\frac{2\pi}{365.25}(t - t_\mathrm{peak}) - \frac{z}{D}\right)
\]

\[
D = \sqrt{2\alpha / \omega},\quad \alpha = k/(\rho c),\quad \omega = 2\pi/(365.25 \times 86400)
\]

Soil moisture retention \(\phi \in [0,1]\) sets conductivity and heat capacity:

\[
k = k_\mathrm{dry} + \phi (k_\mathrm{sat} - k_\mathrm{dry})
\]

and the same blend for \(\rho c\). Wetter soil couples the room more strongly and damps the annual wave over a shorter distance.

## Ground throttling

Wall and floor conduction put the envelope U-value in series with a soil path that gets longer as more of the height is buried (shared berm, longer path). ASSUMPTION:

\[
UA = \left(\frac{1}{UA_\mathrm{ins}} + \frac{L_\mathrm{path}(1+\gamma f)}{k\, A}\right)^{-1}
\]

\(L_\mathrm{path} = 0.80\,\mathrm{m}\), \(\gamma = 0.75\). Extra buried area still adds conductance, but each square metre is less effective at high \(f\).

The roof-loop reject UA is the existing earth-tube expression, then scaled. It is not replaced:

\[
UA_\mathrm{legacy} = (400 + 3200 f)\,\frac{A_\mathrm{floor}}{100} + 1.5\, L_\mathrm{pipe}\, f
\]

\[
UA_\mathrm{tubes} = UA_\mathrm{legacy}\,\frac{k}{k_\mathrm{ref}}\,\frac{1}{1+\gamma_\mathrm{tube} f}
\]

with \(k_\mathrm{ref} = 0.80\,\mathrm{W/(m\cdot K)}\) and \(\gamma_\mathrm{tube} = 0.40\). Tubes dump into \(T_\mathrm{soil}(z_\mathrm{tube})\), not into the wall node. Deeper burial is a steadier sink; the \(\gamma_\mathrm{tube}\) term is the throttle.

## Envelope switches

| Switch | Effect |
|--------|--------|
| `use_type` | Band, internal gains, daylight / egress / view caps, default wall-glazing fraction |
| `L_m`, `W_m`, `H_m` | Areas, volume, and the egress cap \(1 - h_\mathrm{egress}/H\) |
| `clear_ceiling` | Glazed roof vs opaque roof. Opaque area uses the roof material U and admits no solar |
| `water_panes` | On a clear roof, solar split and UA follow the legacy roof loop (`g_room=0.08`, `g_water=0.62`, `ua_roof_to_water`). Off: glazing SHGC goes to the room, loop UA is zero |
| `ceiling_tilt_deg`, `ceiling_azimuth_from_south_deg` | Scales roof irradiance. Azimuth is degrees from south, west positive |
| `glazing_azimuth_weights` | How exposed glazing (or an open stick-up) faces. Default 70% south, 15% east, 15% west |
| `above_grade_enclosure` | True: exposed wall uses the wall material plus the glazing fraction. False: the stick-up is an opening, \(U=12\,\mathrm{W/(m^2\cdot K)}\), extra infiltration \(4(1-f)\) ACH |
| material keys | `wall_material`, `roof_material`, `glazing_material`, `floor_material` |
| `structure` | Slab thickness and berm mass fraction (mass scales up slightly with \(f\)) |
| `soil_moisture_retention` | \(\phi\) in the \(k\) and \(\rho c\) blends |

Light on a tilted surface uses a daily clear-sky beam factor blended with an isotropic diffuse sky. ASSUMPTION: half of monthly GHI is diffuse, so a clear-sky beam ratio is not applied to a cloudy monthly total. Horizontal roofs stay at a factor of 1. The half-sine shape of the day is unchanged; only the daily total is rescaled.

Daylight ratio is transmittance-weighted aperture over floor area. The roof uses water-film \(\tau = 0.55\) when `water_panes` is on, otherwise the glazing `tau_vis`. The check is made at day-of-year 80 (near equinox), not as a full daylight-autonomy model.

## Use-type caps

Feasible \(f\) must satisfy every cap:

\[
f \le 1 - \frac{h_\mathrm{egress}}{H},\qquad
f \le 1 - \phi_\mathrm{view},\qquad
\mathrm{daylight}(f) \ge \mathrm{daylight}_\min
\]

| Use | Band (°C) | Gains | Daylight min | Egress clear height | View exposed fraction | Wall glazing fraction |
|-----|-----------|-------|--------------|---------------------|-----------------------|------------------------|
| living | 20–26 | 8 W/m² | 0.12 | 1.05 m | 0.30 | 0.40 |
| storage | 10–28 | 1 W/m² | 0 | 0 (floor hatch allowed) | 0 | 0 |
| greenhouse | 12–30 | 2 W/m² | 0.40 | 0.45 m | 0 | 0.10 |

These are ASSUMPTION planning limits, not a building-code check. The living egress height is a stand-in so a window and door head can sit above grade. The greenhouse height is a walk-in door, looser than living. Storage may be fully buried.

A 5–35 °C storage band was tried and rejected as the example: with this envelope the free-float year already stays inside it, so \(E(f)\) is zero everywhere and burial does not change the objective. 10–28 °C is still much wider than the living band and is wide enough for DFW to show a real load.

On the default materials, \(E(f)\) falls as \(f\) rises through the whole feasible interval (see the plot). \(f^\star\) therefore sits on the tightest cap. The sweep is still an argmin: if a material, setpoint, or climate makes high \(f\) cost more than it saves, the reported limiter is `energy minimum inside the cap` instead of `use-type cap`.

## ASSUMPTION table

| Input | Default | Role |
|-------|---------|------|
| Cell | \(L=W=10\,\mathrm{m}\), \(H=3\,\mathrm{m}\) | Zone-1 illustration size |
| Living ceiling | opaque, water panes off, above-grade enclosed | Daylight has to come from walls |
| Greenhouse ceiling | clear, water panes on, tilt 0° (horizontal) | Roof loop is the legacy water-ceiling path |
| Storage ceiling | opaque, water panes off, enclosed | No glazing |
| Glazing | `double_polycarbonate` U=2.8, SHGC=0.55, \(\tau_\mathrm{vis}=0.65\) | Walls and dry roofs |
| Wall / floor / opaque roof | insulated concrete 0.45 / insulated slab 0.50 / insulated roof 0.30 W/(m²·K) | Also `sip_r20`, `earthbag`, `uninsulated_concrete`, `uninsulated_slab`, `vegetated_roof`, `uninsulated_metal`, `double_low_e`, `single_poly` |
| Structure | `concrete_berm` (slab 0.20 m, wall-mass fraction 0.35) | Also `timber_frame`, `earthbag_mass` |
| Soil \(\phi\) | 0.50 | \(k\) from 0.30 dry to 1.50 saturated; \(\rho c\) from 1.3e6 to 2.8e6 J/(m³·K) |
| \(T_\mathrm{mean}\), \(A_\mathrm{surf}\) | 18.5 °C, 11 K | DFW undisturbed soil. Legacy free-float plots still use a fixed 18 °C |
| Throttle | \(L_\mathrm{path}=0.80\,\mathrm{m}\), \(\gamma=0.75\), \(\gamma_\mathrm{tube}=0.40\) | Series soil path and earth-tube derate |
| Diffuse fraction | 0.50 | Tilt correction on monthly GHI |
| Open stick-up | U=12 W/(m²·K), +4 ACH at \(f=0\), SHGC 0.85 | Only if `above_grade_enclosure` is false |
| Infiltration when enclosed | 1 ACH | Same base as the legacy room |
| COP heat / cool | 2.5 / 3.0 | Reported only |

## Example under those defaults

DFW typical-month days, \(f\) step 0.05, 10×10×3 m cell. Re-run the command after changing any ASSUMPTION; do not copy these kilowatt-hours as a new baseline.

| Case | \(f^\star\) | What binds | Annual thermal kWh |
|------|------------:|------------|-------------------:|
| living | 61.5% | daylight (egress would allow 65%, view 70%) | 9,054 (heat 1,282, cool 7,771) |
| storage | 100% | no cap inside (0, 1) | 16 (all cooling) |
| greenhouse | 85% | egress door height | 511 (all cooling) |

The three recommendations differ. Energy at the ends of each curve:

| \(f\) | Living kWh | Storage kWh | Greenhouse kWh |
|------:|-----------:|------------:|---------------:|
| 0% | 19,300 | 1,250 | 55,700 |
| 25% | 14,700 | 760 | 21,900 |
| 50% | 10,800 | 430 | 8,270 |
| \(f^\star\) | 9,054 at 61.5% | 16 at 100% | 511 at 85% |
| 100% | 4,360 (infeasible for living) | 16 | 0 (infeasible: egress) |

One switch at a time, same cell, shows the other drivers are live:

- Living with a clear water-pane roof: daylight is satisfied from above, so \(f^\star\) moves from 61.5% to the **65% egress cap**, and annual energy rises to about **32,000 kWh**. Wall burial cannot offset that roof solar inside the egress cap.
- Living at \(f=0.40\) with the stick-up left unenclosed: about **62,000 kWh** versus **12,300 kWh** when that stick-up is an insulated wall.
- Greenhouse at 85% with water panes off: about **64,000 kWh** versus **511 kWh** with the roof loop hooked up.
- Storage at \(f=0.50\): soil moisture retention 0 → about **510 kWh**; retention 1 → about **410 kWh**.

## Plug in DFW or another site

The default series is `DFW_TYPICAL` in `submersion_opt.py`: twelve design days shaped like Dallas–Fort Worth monthly normals (rounded planning values, not a TMY file), latitude 32.90°N, soil mean 18.5 °C. `site.yaml` does not yet carry a weather file. Until one exists, replace this table.

CSV columns, one row per design period (usually 12):

```text
name,doy,days,T_min_C,T_max_C,ghi_kwh_m2,day_length_h
Jan,15,31,2.2,13.9,2.7,10.2
```

```bash
.venv/bin/python climate/thermal-model/submersion_opt.py \
  --climate-csv my_months.csv --latitude 32.9 --t-mean-soil 18.5
```

`--t-mean-soil` is the undisturbed annual mean at depth, not the legacy plot's fixed 18 °C sink. Surface amplitude and the day-205 phase stay at the DFW ASSUMPTION unless you build a `SiteClimate` in Python and call `sweep_case`.

The extreme North Texas summer day (26–40 °C, 950 W/m² peak) remains `ClimateParams` inside `climate_envelope_sim.py`. That path is the free-float illustration, including `submersion_sensitivity.png`. It is not the annual objective used for \(f^\star\).
