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
| `entrance_greenhouse_enclosure` | Air pad over the light roof or the entrance. Off by default. See below |
| material keys | `wall_material`, `roof_material`, `glazing_material`, `floor_material` |
| `structure` | Slab thickness and berm mass fraction (mass scales up slightly with \(f\)) |
| `soil_moisture_retention` | \(\phi\) in the \(k\) and \(\rho c\) blends |

Light on a tilted surface uses a daily clear-sky beam factor blended with an isotropic diffuse sky. ASSUMPTION: half of monthly GHI is diffuse, so a clear-sky beam ratio is not applied to a cloudy monthly total. Horizontal roofs stay at a factor of 1. The half-sine shape of the day is unchanged; only the daily total is rescaled.

Daylight ratio is transmittance-weighted aperture over floor area. The roof uses water-film \(\tau = 0.55\) when `water_panes` is on, otherwise the glazing `tau_vis`. The check is made at day-of-year 80 (near equinox), not as a full daylight-autonomy model.

## Hard use rules

Homes must keep a sunlight path: a clear ceiling or glazed wall/roof surfaces. A living case with neither is infeasible. Homes also carry a hard cap \(f \le 0.85\) (`no_full_burial`) so they are never fully buried. Egress and view usually bind tighter than that cap.

Dry storage and refrigerated storage have no daylight requirement and may use \(f = 1\). The sweep still picks the energy minimum; on the default envelope that minimum is full burial.

Cold storage is a cooler band, about 1–4 °C (ASSUMPTION), not a freezer. Soil near 18 °C is warmer than that band, so burial does not make refrigeration free. It still beats leaving the walls in summer air, so \(f^\star\) lands at 100%.

## Use-type caps

Feasible \(f\) must satisfy every cap:

\[
f \le 1 - \frac{h_\mathrm{egress}}{H},\qquad
f \le 1 - \phi_\mathrm{view},\qquad
f \le f_\mathrm{policy},\qquad
\mathrm{daylight}(f) \ge \mathrm{daylight}_\min
\]

| Use | Band (°C) | Gains | Daylight min | Egress clear height | View exposed fraction | Policy max \(f\) |
|-----|-----------|-------|--------------|---------------------|-----------------------|-----------------:|
| living | 20–26 | 8 W/m² | 0.12 | 1.05 m | 0.30 | 0.85 |
| storage | 10–28 | 1 W/m² | 0 | 0 (floor hatch allowed) | 0 | 1 |
| cold_storage | 1–4 | 2 W/m² | 0 | 0 | 0 | 1 |
| greenhouse | 12–30 | 2 W/m² | 0.40 | 0.45 m | 0 | 1 |

These are ASSUMPTION planning limits, not a building-code check. The living egress height is a stand-in so a window and door head can sit above grade. The greenhouse height is a walk-in door, looser than living. The default living example uses a clear water-pane roof, so daylight is met from above and egress is what stops burial.

A 5–35 °C dry-storage band was tried and rejected as the example: with this envelope the free-float year already stays inside it, so \(E(f)\) is zero everywhere and burial does not change the objective. 10–28 °C is still much wider than the living band and is wide enough for DFW to show a real load.

On the default materials, \(E(f)\) falls as \(f\) rises through the whole feasible interval (see the plot). \(f^\star\) therefore sits on the tightest cap. The sweep is still an argmin: if a material, setpoint, or climate makes high \(f\) cost more than it saves, the reported limiter is `energy minimum inside the cap` instead of `use-type cap`.

## ASSUMPTION table

| Input | Default | Role |
|-------|---------|------|
| Cell | \(L=W=10\,\mathrm{m}\), \(H=3\,\mathrm{m}\) | Zone-1 illustration size |
| Living ceiling | clear, water panes on, above-grade enclosed | Sunlight from the roof; egress stops full burial |
| Greenhouse ceiling | clear, water panes on, tilt 0° (horizontal) | Roof loop is the legacy water-ceiling path |
| Storage / cold storage ceiling | opaque, water panes off, enclosed | No glazing; full burial allowed |
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
| living (clear roof) | 65% | egress (daylight is already met; full burial is also forbidden) | 32,334 (heat 12,233, cool 20,100) |
| storage | 100% | no cap inside (0, 1) | 16 (all cooling) |
| cold_storage | 100% | no cap inside (0, 1) | 27,035 (all cooling) |
| greenhouse | 85% | egress door height | 511 (all cooling) |

Living stays in the sun. Storage and cold storage go to the bottom of the cut. The clear living roof is why that cell's energy is high: wall burial still helps (about 104,000 kWh/year at \(f=0\) versus 32,000 at 65%), and \(f=1\) would be lower still but is not allowed.

| \(f\) | Living kWh | Storage kWh | Cold storage kWh |
|------:|-----------:|------------:|-----------------:|
| 0% | 103,800 | 1,250 | 31,100 |
| 50% | 42,500 | 430 | 29,200 |
| \(f^\star\) | 32,334 at 65% | 16 at 100% | 27,035 at 100% |
| 100% | 15,700 (infeasible: egress and no-full-burial) | 16 | 27,035 |

A home with an opaque roof and no wall glazing is rejected (`sunlight` cap). Greenhouse at 85% with water panes off is about 64,000 kWh versus 511 kWh with the roof loop. Dry storage at \(f=0.50\): soil moisture retention 0 → about 510 kWh; retention 1 → about 410 kWh.

## Entrance greenhouse (air pad)

Switch: `entrance_greenhouse_enclosure`. Default is off, so the table above is the bare envelope.

When the facility still has a light-entering roof, an above-grade greenhouse covers that roof (plan area = floor area, at least a 6 m² vestibule). When the roof is opaque, only a vestibule covers the entrance: 6 m² of plan and a 2 m² door or hatch. At full burial the hatch is a patch of roof; if some wall is still above grade, that 2 m² comes out of the exposed wall first.

The pad is one air node. ASSUMPTION defaults:

| Input | Value |
|-------|------:|
| Height | 2.4 m |
| Outer glazing U | 2.8 W/(m²·K) (double polycarbonate) |
| Outdoor air changes of the pad | 1.5 /h |
| Outer solar / visible transmittance | 0.70 |
| Share of horizontal irradiance absorbed in the pad | 0.25 |
| Room infiltration drawn from the pad | 75% (the rest still leaks outdoors) |

Outdoor skin conductance is \(U\) times plan plus the four walls, plus the pad's own infiltration. The facility surfaces inside the pad, and 75% of the room's air changes, exchange with pad air \(T_b\) instead of outdoors. Those conductances still add up to the bare envelope; only the far-side temperature changes. A covered light roof also multiplies roof solar and the roof's daylight ratio by 0.70. The pad's capacitance is the air in \(A_\mathrm{plan} \times 2.4\,\mathrm{m}\), stepped implicitly each minute so a small vestibule stays stable.

On the same DFW year, \(f^\star\) does not move. Living is still stopped at the 65% egress cap, and both stores still minimize at 100%. The energy at that \(f^\star\) does move:

| Case | \(f^\star\) bare | \(f^\star\) with pad | Thermal kWh bare | Thermal kWh with pad |
|------|----------------:|---------------------:|-----------------:|---------------------:|
| living (clear roof) | 65% | 65% | 32,334 | 28,519 |
| storage | 100% | 100% | 16 | 143 |
| cold storage | 100% | 100% | 27,035 | 23,510 |

The living roof sits under the greenhouse, so less solar enters and the roof conducts to pad air. That is about 3,800 kWh/year less at the same 65%. The cold store's hatch and most of its air leakage see pad air, which sits between the 1–4 °C room and the weather, so cooling falls by about 3,500 kWh/year and \(f^\star\) stays fully buried. The dry store was already near zero load; the vestibule's solar gain creates about 143 kWh/year of cooling that the bare buried box did not have. Full burial is still its minimum.

## Community loads and shared microgrid

The same command prints gallons heated, powered heat, the maintenance/discretionary split, and a microgrid CapEx stub. Detail is in [`community_energy.py`](community_energy.py). Headcounts are not a second population model:

- \(H = 20\), \(W = 70\,\mathrm{kg}\), and 12 m²/person come from `economics/community_capital.py` (`run_example` defaults and `facility_m2_per_person`).
- 16,500 worms and 20 quail come from `research/ops-dashboard/store.py` `DEFAULT_HERD`. Worms are the Stage 1 stub. Quail is the Stage 4 planning stub in that dict, not a purchase.

Consumed hot water (ASSUMPTION): 10 gal/person/day maintenance and 5 gal/person/day discretionary, heated from 18 °C to 49 °C. Quail add 0.02 gal/bird/day to 40 °C. Worms add none. Energy is \(\rho V c_p \Delta T\). With those defaults the print is about **200 gal/day maintenance** (9,900 kWh/year, peak about 6.8 kW) and **100 gal/day discretionary** (5,000 kWh/year). The living roof loop is about 98 gal of pipe inventory for 240 m², not a daily reheat.

Space conditioning uses each case's \(f^\star\), scaled to floor area. Living floor is \(H \times 12\,\mathrm{m^2}\). Dry storage and cold storage are one 100 m² shared cell each. Living also carries a 15% discretionary adder (ASSUMPTION) on top of the thermostat. On this run that is about 77,600 kWh/year maintenance for the homes, 16 kWh for the dry store, and 27,000 kWh for the cooler.

The microgrid stub serves shared dry storage, shared cold storage, and the central hot-water plant. It does not size the homes. ASSUMPTION unit costs: $2,500/kW PV, $400/kWh battery, DFW capacity factor 0.18, 12 h of battery on the maintenance peak. This run: about **27 kW PV**, **121 kWh battery**, **$115,000**. That figure is not added to `community_capital` `setup_capex` (`other_capex` stays 0). Stage 1 worms remain the only active spend.

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
