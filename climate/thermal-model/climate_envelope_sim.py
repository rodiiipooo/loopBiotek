#!/usr/bin/env python3
"""
LoopBiotek climate-envelope simulation
======================================
Coupled transient model: room air (+ structural mass) + glazed-roof water loop
+ earth conduction, with explicit pipe geometry (ID, serpentine length, fluid
gallons) and thermal-expansion pressure rise.

North Texas summer baseline (ambient peak ~40 C, deep soil ~18 C).
Zone-1 cell-scale defaults: L=W=10 m, H=3 m, 70% submersion, 1/2" PEX @ 10 cm.

Usage:
    python climate_envelope_sim.py
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, asdict
from typing import Dict, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
RHO_WATER = 997.0          # kg/m3
CP_WATER = 4182.0          # J/(kg·K)
RHO_AIR = 1.2              # kg/m3
CP_AIR = 1005.0            # J/(kg·K)
RHO_CONCRETE = 2400.0      # kg/m3
CP_CONCRETE = 880.0        # J/(kg·K)
BETA_WATER = 2.1e-4        # 1/K volumetric expansion (near 20–40 C)
GALLON_PER_M3 = 264.172


@dataclass
class PipeGeometry:
    """Serpentine PEX (or similar) roof-loop geometry."""
    pipe_id_mm: float = 12.07          # 1/2" PEX nominal ID ~0.475"
    tube_spacing_m: float = 0.10       # 10 cm center-to-center
    window_L_m: float = 10.0           # glazed / cooled plan length
    window_W_m: float = 10.0           # glazed / cooled plan width
    header_extra_m: float = 8.0        # supply+return headers / trunks
    expansion_tank_gal: float = 8.0    # bladder expansion tank
    fittings_gal: float = 2.0          # manifolds, pump volute, etc.
    flow_gpm: float = 12.0             # total circulating flow (split across banks)
    n_parallel_circuits: int = 10      # banks fed in parallel (realistic velocity)

    @property
    def pipe_id_m(self) -> float:
        return self.pipe_id_mm / 1000.0

    @property
    def n_runs(self) -> int:
        return max(1, int(round(self.window_W_m / self.tube_spacing_m)))

    @property
    def serpentine_length_m(self) -> float:
        # Parallel runs along L, spaced across W, plus short return bends + headers
        run_len = self.n_runs * self.window_L_m
        bends = (self.n_runs - 1) * self.tube_spacing_m * math.pi / 2  # rough U-bends
        return run_len + bends + self.header_extra_m

    @property
    def pipe_volume_m3(self) -> float:
        r = self.pipe_id_m / 2.0
        return math.pi * r * r * self.serpentine_length_m

    @property
    def pipe_gallons(self) -> float:
        return self.pipe_volume_m3 * GALLON_PER_M3

    @property
    def total_fluid_gallons(self) -> float:
        return self.pipe_gallons + self.expansion_tank_gal + self.fittings_gal

    @property
    def fluid_mass_kg(self) -> float:
        return (self.total_fluid_gallons / GALLON_PER_M3) * RHO_WATER

    @property
    def velocity_m_s(self) -> float:
        # Flow split across parallel circuits → per-circuit velocity
        flow_m3_s = (self.flow_gpm * 0.00378541) / 60.0
        flow_per = flow_m3_s / max(1, self.n_parallel_circuits)
        area = math.pi * (self.pipe_id_m / 2.0) ** 2
        return flow_per / area if area > 0 else 0.0


@dataclass
class RoomParams:
    L_m: float = 10.0
    W_m: float = 10.0
    H_m: float = 3.0
    submersion: float = 0.70           # fraction of height below grade
    glazed_roof_frac: float = 1.0      # fraction of plan area with water-cooled glazing
    # Envelope U-values (W/(m²·K))
    U_glazing: float = 2.8             # double-wall polycarbonate / glass to ambient
    U_earth_wall: float = 0.45         # buried wall → soil
    U_earth_floor: float = 0.50        # floor slab → soil
    U_exposed_wall: float = 0.70       # above-grade wall → ambient
    UA_roof_to_water: float = None     # set from pipe geometry if None
    ACH: float = 1.0                   # infiltration / controlled vent air changes/h
    Q_internal_W: float = 800.0        # lights + animals + equipment (cell-scale)
    # Solar disposition on water-cooled glazed roof (must sum ≤ 1)
    g_solar_to_room: float = 0.08      # transmitted / re-radiated into room
    g_solar_to_water: float = 0.62     # absorbed by exterior water film / absorber plate
    # Structural thermal mass (concrete floor slab + berm-coupled walls)
    slab_thickness_m: float = 0.20
    mass_wall_frac: float = 0.35       # extra wall mass as fraction of slab mass
    T_soil_C: float = 18.0
    T0_room_C: float = 26.0
    T0_water_C: float = 22.0
    P0_kPa: float = 200.0              # cold fill / static pressure
    K_sys_kPa: float = 8.0e4           # lumped bulk modulus before tank softening


@dataclass
class ClimateParams:
    """North Texas summer diurnal baseline; override for other sites."""
    T_min_C: float = 26.0
    T_max_C: float = 40.0
    T_peak_hour: float = 15.0
    G_peak_W_m2: float = 950.0
    day_length_h: float = 13.5
    sunrise_h: float = 6.25


def outdoor_T(t_h: np.ndarray, clim: ClimateParams) -> np.ndarray:
    phase = 2 * math.pi * (t_h - clim.T_peak_hour) / 24.0
    mid = 0.5 * (clim.T_min_C + clim.T_max_C)
    amp = 0.5 * (clim.T_max_C - clim.T_min_C)
    return mid + amp * np.cos(phase)


def solar_G(t_h: np.ndarray, clim: ClimateParams) -> np.ndarray:
    sunset = clim.sunrise_h + clim.day_length_h
    G = np.zeros_like(t_h, dtype=float)
    day = (t_h >= clim.sunrise_h) & (t_h <= sunset)
    x = (t_h[day] - clim.sunrise_h) / clim.day_length_h
    G[day] = clim.G_peak_W_m2 * np.sin(math.pi * x)
    return np.clip(G, 0.0, None)


def ua_roof_to_water(pipe: PipeGeometry) -> float:
    """
    Effective UA (W/K) from room air / absorber underside to circulating water.
    Absorber strip contact + tube outer surface; h_eff ~ 40 W/(m²·K) with flow.
    """
    od_m = pipe.pipe_id_m + 2 * 0.0018   # ~1/2" PEX OD
    # Use projected absorber width ≈ tube spacing (continuous plate) rather than
    # bare tube perimeter — plate transfers much better.
    plate_area = pipe.window_L_m * pipe.window_W_m
    tube_area = math.pi * od_m * pipe.serpentine_length_m
    h_plate = 25.0   # room-side convection to plate underside
    h_tube = 120.0   # water-side (forced)
    # Two resistances in series: room→plate and plate→water (tube)
    R_room = 1.0 / (h_plate * plate_area)
    R_tube = 1.0 / (h_tube * tube_area * 0.5)  # half perimeter bonded
    return 1.0 / (R_room + R_tube)


def areas(room: RoomParams) -> Dict[str, float]:
    floor = room.L_m * room.W_m
    perimeter = 2 * (room.L_m + room.W_m)
    H_u = room.submersion * room.H_m
    H_e = (1.0 - room.submersion) * room.H_m
    return {
        "floor": floor,
        "glazed_roof": floor * room.glazed_roof_frac,
        "buried_wall": perimeter * H_u,
        "exposed_wall": perimeter * H_e,
        "volume": floor * room.H_m,
    }


def room_capacitance(room: RoomParams) -> float:
    """Air + concrete slab + fraction of berm/wall mass (J/K)."""
    A = areas(room)
    C_air = RHO_AIR * CP_AIR * A["volume"]
    m_slab = RHO_CONCRETE * A["floor"] * room.slab_thickness_m
    m_wall = room.mass_wall_frac * m_slab
    C_mass = (m_slab + m_wall) * CP_CONCRETE
    return C_air + C_mass


def simulate(
    room: RoomParams,
    pipe: PipeGeometry,
    clim: ClimateParams,
    hours: float = 48.0,   # 2 days so diurnal state settles; report last 24 h
    dt_s: float = 60.0,
) -> Dict[str, np.ndarray]:
    """Forward-Euler coupled transient for room (air+mass) + loop water."""
    A = areas(room)
    UA_rw = room.UA_roof_to_water if room.UA_roof_to_water is not None else ua_roof_to_water(pipe)
    C_room = room_capacitance(room)
    C_water = pipe.fluid_mass_kg * CP_WATER

    V_dot = A["volume"] * room.ACH / 3600.0
    UA_inf = RHO_AIR * CP_AIR * V_dot

    # Ground heat-exchanger reject (dedicated earth tubes in berm + buried
    # return). Sized so a 70%-submerged cell can reject ~peak solar on ~12–15 K
    # ΔT to 18 °C soil. Scales strongly with submersion.
    # Base: ~3.5 kW/K at full submersion for 100 m² roof; linear in floor area.
    UA_reject = (400.0 + 3200.0 * room.submersion) * (A["floor"] / 100.0)  # W/K
    # Extra from buried header trunks in the berm
    UA_reject += 1.5 * pipe.serpentine_length_m * room.submersion  # ~1.5 W/(m·K)

    n = int(hours * 3600 / dt_s) + 1
    t_all = np.arange(n) * dt_s / 3600.0
    T_out_all = outdoor_T(t_all % 24.0, clim)
    G_all = solar_G(t_all % 24.0, clim)

    T_r = np.zeros(n)
    T_w = np.zeros(n)
    P = np.zeros(n)
    Q_water_abs = np.zeros(n)

    T_r[0] = room.T0_room_C
    T_w[0] = room.T0_water_C
    T_ref = room.T0_water_C

    V_pipe = pipe.pipe_volume_m3
    V_tank = pipe.expansion_tank_gal / GALLON_PER_M3
    soft = V_pipe / (V_pipe + 1.2 * V_tank + 1e-12)

    for i in range(n - 1):
        To = T_out_all[i]
        Gi = G_all[i]
        Tr, Tw = T_r[i], T_w[i]
        Ts = room.T_soil_C

        Q_solar_room = room.g_solar_to_room * Gi * A["glazed_roof"]
        Q_solar_water = room.g_solar_to_water * Gi * A["glazed_roof"]
        Q_int = room.Q_internal_W

        Q_rw = UA_rw * (Tr - Tw)
        Q_roof_amb = room.U_glazing * A["glazed_roof"] * (Tr - To)
        Q_earth = (
            room.U_earth_floor * A["floor"] * (Tr - Ts)
            + room.U_earth_wall * A["buried_wall"] * (Tr - Ts)
        )
        Q_wall_amb = room.U_exposed_wall * A["exposed_wall"] * (Tr - To)
        Q_inf = UA_inf * (Tr - To)
        Q_reject = UA_reject * (Tw - Ts)

        dTr = (Q_solar_room + Q_int - Q_rw - Q_roof_amb - Q_earth - Q_wall_amb - Q_inf) / C_room
        dTw = (Q_rw + Q_solar_water - Q_reject) / C_water

        T_r[i + 1] = Tr + dTr * dt_s
        T_w[i + 1] = Tw + dTw * dt_s
        Q_water_abs[i] = Q_rw + Q_solar_water

        dT_w = T_w[i + 1] - T_ref
        P[i + 1] = room.P0_kPa + room.K_sys_kPa * soft * BETA_WATER * dT_w

    Q_water_abs[-1] = Q_water_abs[-2]
    P[0] = room.P0_kPa

    # Return last 24 h only (settled diurnal)
    mask = t_all >= (hours - 24.0)
    t_h = t_all[mask] - (hours - 24.0)
    return {
        "t_h": t_h,
        "T_out": T_out_all[mask],
        "T_room": T_r[mask],
        "T_water": T_w[mask],
        "P_kPa": P[mask],
        "G": G_all[mask],
        "Q_water_W": Q_water_abs[mask],
        "UA_rw": np.array([UA_rw]),
        "UA_reject": np.array([UA_reject]),
        "C_room": np.array([C_room]),
    }


def print_sizing_summary(
    room: RoomParams, pipe: PipeGeometry, sim: Dict[str, np.ndarray]
) -> Dict[str, float]:
    mid = (sim["t_h"] >= 12.0) & (sim["t_h"] <= 16.0)
    peak_room = float(np.max(sim["T_room"]))
    peak_water = float(np.max(sim["T_water"]))
    midday_room = float(np.max(sim["T_room"][mid]))
    midday_water = float(np.max(sim["T_water"][mid]))
    midday_P = float(np.max(sim["P_kPa"][mid]))
    peak_Q_kW = float(np.max(sim["Q_water_W"])) / 1000.0
    heat_absorbed_mid_kW = float(np.mean(sim["Q_water_W"][mid])) / 1000.0

    print("=" * 64)
    print("LoopBiotek climate-envelope — sizing summary")
    print("=" * 64)
    print(f"Room: {room.L_m:.1f}×{room.W_m:.1f}×{room.H_m:.1f} m  "
          f"submersion={room.submersion*100:.0f}%")
    print(f"Glazed roof area: {areas(room)['glazed_roof']:.1f} m²")
    print(f"Room thermal mass C: {float(sim['C_room'][0])/1e6:.2f} MJ/K")
    print("-" * 64)
    print(f"Pipe ID:              {pipe.pipe_id_mm:.2f} mm  (1/2\" PEX)")
    print(f"Tube spacing:         {pipe.tube_spacing_m*100:.0f} cm")
    print(f"Serpentine runs:      {pipe.n_runs}")
    print(f"Parallel circuits:    {pipe.n_parallel_circuits}")
    print(f"Pipe length:          {pipe.serpentine_length_m:.1f} m")
    print(f"Pipe volume:          {pipe.pipe_gallons:.2f} gal")
    print(f"Expansion tank:       {pipe.expansion_tank_gal:.1f} gal")
    print(f"Fittings/manifold:    {pipe.fittings_gal:.1f} gal")
    print(f"TOTAL fluid gallons:  {pipe.total_fluid_gallons:.2f} gal")
    print(f"Fluid mass:           {pipe.fluid_mass_kg:.1f} kg")
    print(f"Flow:                 {pipe.flow_gpm:.1f} gpm total  →  "
          f"per-circuit velocity {pipe.velocity_m_s:.2f} m/s")
    print(f"UA room↔water:        {float(sim['UA_rw'][0]):.0f} W/K")
    print(f"UA ground reject:     {float(sim['UA_reject'][0]):.0f} W/K")
    print("-" * 64)
    print(f"Mid-day peak T_room:  {midday_room:.2f} °C  (24h max {peak_room:.2f})")
    print(f"Mid-day peak T_water: {midday_water:.2f} °C  (24h max {peak_water:.2f})")
    print(f"Mid-day peak P:       {midday_P:.1f} kPa")
    print(f"Heat absorbed (water) mid-day mean: {heat_absorbed_mid_kW:.2f} kW  "
          f"(peak {peak_Q_kW:.2f} kW)")
    print("=" * 64)

    return {
        "pipe_length_m": pipe.serpentine_length_m,
        "pipe_gallons": pipe.pipe_gallons,
        "total_gallons": pipe.total_fluid_gallons,
        "fluid_mass_kg": pipe.fluid_mass_kg,
        "velocity_m_s": pipe.velocity_m_s,
        "midday_T_room": midday_room,
        "midday_T_water": midday_water,
        "midday_P_kPa": midday_P,
        "peak_Q_kW": peak_Q_kW,
        "heat_absorbed_mid_kW": heat_absorbed_mid_kW,
        "peak_T_room": peak_room,
        "peak_T_water": peak_water,
    }


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_24h_temps_pressure(sim: Dict[str, np.ndarray], path: str) -> None:
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    t = sim["t_h"]
    ax1.plot(t, sim["T_out"], color="#dd6b20", lw=2, label="Outdoor T")
    ax1.plot(t, sim["T_room"], color="#c53030", lw=2.2, label="Room T")
    ax1.plot(t, sim["T_water"], color="#2b6cb0", lw=2.2, label="Water (loop) T")
    ax1.axhline(18, color="#718096", ls="--", lw=1, label="Deep soil 18 °C")
    ax1.set_xlabel("Hour of day")
    ax1.set_ylabel("Temperature (°C)")
    ax1.set_xlim(0, 24)
    ax1.set_xticks(range(0, 25, 3))
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(t, sim["P_kPa"], color="#553c9a", lw=1.8, ls="-.", label="Loop pressure")
    ax2.set_ylabel("Loop pressure (kPa)", color="#553c9a")
    ax2.tick_params(axis="y", labelcolor="#553c9a")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
    ax1.set_title(
        "LoopBiotek Zone-1 cell — 24 h temperatures & loop pressure\n"
        "(North Texas summer baseline, 70% earth-submerged, water-cooled glazed roof)"
    )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _vertical_profile(
    T_soil: float,
    T_berm: float,
    T_room: float,
    T_water: float,
    T_amb: float,
    ny: int = 200,
    nx: int = 120,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = np.linspace(0, 1, ny)
    x = np.linspace(0, 1, nx)
    X, Y = np.meshgrid(x, y)
    T = np.zeros_like(Y)

    for j, yi in enumerate(y):
        if yi < 0.25:
            f = yi / 0.25
            t = T_soil + (T_berm - T_soil) * f * 0.3
        elif yi < 0.40:
            f = (yi - 0.25) / 0.15
            t = T_soil + (T_berm - T_soil) * (0.3 + 0.7 * f)
        elif yi < 0.72:
            t = T_room
        elif yi < 0.82:
            t = T_water
        else:
            t = T_amb
        T[j, :] = t

    wall_mask = (X < 0.12) | (X > 0.88)
    for j, yi in enumerate(y):
        if 0.25 <= yi < 0.55:
            T[j, wall_mask[j]] = T_berm + 0.15 * (T_room - T_berm)
        elif 0.55 <= yi < 0.72:
            T[j, wall_mask[j]] = 0.5 * (T_room + T_amb)

    rng = np.random.default_rng(0)
    room_band = (Y >= 0.40) & (Y < 0.72) & ~wall_mask
    T[room_band] += rng.normal(0, 0.12, size=T[room_band].shape)
    return X, Y, T


def plot_heatmap_cross_section(
    room: RoomParams,
    sim: Dict[str, np.ndarray],
    path: str,
) -> None:
    snapshots = [
        ("06:00", 6.0),
        ("12:00", 12.0),
        ("18:00", 18.0),
        ("00:00", 0.0),
    ]
    fig, axs = plt.subplots(1, 4, figsize=(14, 5.2), sharey=True)
    cmap = LinearSegmentedColormap.from_list(
        "thermal",
        ["#1a365d", "#2b6cb0", "#48bb78", "#f6e05e", "#ed8936", "#c53030"],
    )
    all_T = np.concatenate([sim["T_room"], sim["T_water"], sim["T_out"], [room.T_soil_C]])
    vmin = max(14.0, float(np.min(all_T)) - 2)
    vmax = min(45.0, float(np.max(all_T)) + 2)
    im = None

    for ax, (label, hour) in zip(axs, snapshots):
        idx = int(np.argmin(np.abs(sim["t_h"] - hour)))
        T_room = float(sim["T_room"][idx])
        T_water = float(sim["T_water"][idx])
        T_amb = float(sim["T_out"][idx])
        T_soil = room.T_soil_C
        T_berm = 0.65 * T_soil + 0.35 * T_room

        X, Y, T = _vertical_profile(T_soil, T_berm, T_room, T_water, T_amb)
        im = ax.pcolormesh(X, Y, T, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
        ax.set_title(f"{label}\nT_r={T_room:.1f}  T_w={T_water:.1f}  T∞={T_amb:.1f}")
        ax.set_xlabel("← wall | room span | wall →")
        ax.set_xticks([])

        if ax is axs[0]:
            for y, txt in [
                (0.12, "deep soil"),
                (0.32, "berm/wall"),
                (0.55, "room air"),
                (0.77, "fluid roof"),
                (0.91, "ambient"),
            ]:
                ax.text(
                    0.02, y, txt, color="white", fontsize=8, fontweight="bold",
                    transform=ax.transAxes,
                    bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.35, ec="none"),
                )

    axs[0].set_ylabel("Elevation (deep soil → ambient)")
    for ax in axs:
        ax.set_ylim(0, 1)
        ax.set_yticks([0.12, 0.32, 0.55, 0.77, 0.91])
        ax.set_yticklabels(["soil", "berm", "room", "roof", "air"])

    cbar = fig.colorbar(im, ax=axs, fraction=0.025, pad=0.02)
    cbar.set_label("Temperature (°C)")
    fig.suptitle(
        "Cross-section heat map — earth → berm → room → water-cooled roof → ambient\n"
        f"Submersion {room.submersion*100:.0f}% · Zone-1 cell",
        fontsize=12,
    )
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def hvac_proxy_kwh(sim: Dict[str, np.ndarray], T_set: float = 28.0) -> float:
    """Proxy daily HVAC cooling energy (kWh): ∫ UA·max(0, T_room − T_set) dt."""
    UA_proxy = 200.0  # W/K
    dt_h = float(sim["t_h"][1] - sim["t_h"][0])
    excess = np.clip(sim["T_room"] - T_set, 0, None)
    return float(np.sum(UA_proxy * excess * dt_h) / 1000.0)


def plot_submersion_sensitivity(
    base_room: RoomParams,
    pipe: PipeGeometry,
    clim: ClimateParams,
    path: str,
) -> None:
    fracs = np.linspace(0.0, 1.0, 11)
    peaks = []
    energies = []
    for s in fracs:
        room = RoomParams(**{**asdict(base_room), "submersion": float(s)})
        room.UA_roof_to_water = None
        sim = simulate(room, pipe, clim)
        peaks.append(float(np.max(sim["T_room"])))
        energies.append(hvac_proxy_kwh(sim))

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(fracs * 100, peaks, "o-", color="#c53030", lw=2, markersize=7, label="Peak room T")
    ax1.set_xlabel("Submersion (% of building height below grade)")
    ax1.set_ylabel("Peak room temperature (°C)", color="#c53030")
    ax1.tick_params(axis="y", labelcolor="#c53030")
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 100)

    ax2 = ax1.twinx()
    ax2.plot(
        fracs * 100, energies, "s--", color="#2b6cb0", lw=2, markersize=7,
        label="Daily HVAC-proxy energy",
    )
    ax2.set_ylabel("Daily HVAC-proxy cooling energy (kWh)", color="#2b6cb0")
    ax2.tick_params(axis="y", labelcolor="#2b6cb0")

    ax1.axvline(50, color="#718096", ls=":", lw=1.2)
    ax1.text(
        51, max(peaks) - 0.15 * (max(peaks) - min(peaks) + 0.5),
        "report baseline\n~50% earth-sheltered",
        fontsize=8, color="#4a5568",
    )

    # Annotate ~12% energy reduction 0→50% if visible
    if energies[0] > 0:
        save_50 = 100.0 * (energies[0] - energies[5]) / energies[0]
        ax2.text(
            0.02, 0.05,
            f"0→50% submersion: HVAC-proxy {save_50:.0f}% lower",
            transform=ax2.transAxes, fontsize=8, color="#2b6cb0",
        )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)
    ax1.set_title(
        "Submersion sensitivity — peak room T & HVAC-proxy energy\n"
        "(water-cooled roof held constant; earth UA scales with buried area)"
    )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_site_layout_10acre(path: str) -> None:
    """
    Top-down 660×660 ft (10 acre) 4-zone layout:
      Zone1 earth habitat  0.75 ac
      Zone2 climate canopy 1.75 ac
      Zone3 outdoor        4.5  ac
      Zone4 buffer         3.0  ac
    """
    S = 660.0
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_xlim(0, S)
    ax.set_ylim(0, S)
    ax.set_aspect("equal")
    ax.set_xlabel("ft")
    ax.set_ylabel("ft")

    colors = {
        1: "#c6f6d5",
        2: "#90cdf4",
        3: "#faf089",
        4: "#e2e8f0",
    }

    buf = 55.0  # ~3.06 ac perimeter buffer
    ax.add_patch(mpatches.Rectangle((0, 0), S, S, facecolor=colors[4], edgecolor="#4a5568", lw=2))

    ix0, iy0 = buf, buf
    iw, ih = S - 2 * buf, S - 2 * buf

    z1 = 180.0
    ax.add_patch(mpatches.FancyBboxPatch(
        (ix0 + 10, iy0 + ih - z1 - 10), z1, z1,
        boxstyle="round,pad=2,rounding_size=12",
        facecolor=colors[1], edgecolor="#22543d", lw=2,
    ))

    z2w, z2h = 320.0, 240.0
    ax.add_patch(mpatches.FancyBboxPatch(
        (ix0 + z1 + 25, iy0 + ih - z2h - 10), z2w, z2h,
        boxstyle="round,pad=2,rounding_size=12",
        facecolor=colors[2], edgecolor="#2c5282", lw=2,
    ))

    ax.add_patch(mpatches.FancyBboxPatch(
        (ix0 + 10, iy0 + 10), iw - 20, 220,
        boxstyle="round,pad=2,rounding_size=12",
        facecolor=colors[3], edgecolor="#975a16", lw=2,
    ))
    ax.add_patch(mpatches.FancyBboxPatch(
        (ix0 + z1 + z2w + 40, iy0 + 240), iw - (z1 + z2w + 50), ih - 250,
        boxstyle="round,pad=2,rounding_size=12",
        facecolor=colors[3], edgecolor="#975a16", lw=2,
    ))

    def label(x, y, text):
        ax.text(
            x, y, text, ha="center", va="center", fontsize=10, fontweight="bold",
            color="#1a202c",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", alpha=0.85, ec="none"),
        )

    label(ix0 + 10 + z1 / 2, iy0 + ih - 10 - z1 / 2,
          "Zone 1 — Earth Habitat\n0.75 ac\n(partially submerged cells)")
    label(ix0 + z1 + 25 + z2w / 2, iy0 + ih - 10 - z2h / 2,
          "Zone 2 — Climate Canopy\n1.75 ac\n(water-cooled glazed roof)")
    label(ix0 + iw / 2, iy0 + 10 + 110,
          "Zone 3 — Outdoor Production\n4.5 ac\n(fields, forage, solar)")
    label(S / 2, 28, "Zone 4 — Buffer / Berm / Access  ·  3.0 ac")
    label(
        ix0 + z1 + z2w + 40 + (iw - z1 - z2w - 50) / 2,
        iy0 + 240 + (ih - 250) / 2,
        "Zone 3\n(cont.)",
    )

    ax.annotate(
        "", xy=(S - 40, S - 80), xytext=(S - 40, S - 140),
        arrowprops=dict(arrowstyle="->", color="black", lw=2),
    )
    ax.text(S - 40, S - 60, "N", ha="center", fontsize=12, fontweight="bold")

    ax.set_title(
        "LoopBiotek 10-acre site layout (660 × 660 ft)\n"
        "4-zone Gemini design — earth-coupled communities",
        fontsize=13,
    )
    legend_patches = [
        mpatches.Patch(facecolor=colors[1], edgecolor="#22543d", label="Z1 Earth Habitat 0.75 ac"),
        mpatches.Patch(facecolor=colors[2], edgecolor="#2c5282", label="Z2 Climate Canopy 1.75 ac"),
        mpatches.Patch(facecolor=colors[3], edgecolor="#975a16", label="Z3 Outdoor 4.5 ac"),
        mpatches.Patch(facecolor=colors[4], edgecolor="#4a5568", label="Z4 Buffer 3.0 ac"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=9, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    room = RoomParams()
    pipe = PipeGeometry()
    clim = ClimateParams()

    sim = simulate(room, pipe, clim)
    summary = print_sizing_summary(room, pipe, sim)

    p1 = os.path.join(OUT_DIR, "24h_temps_pressure.png")
    p2 = os.path.join(OUT_DIR, "heatmap_cross_section.png")
    p3 = os.path.join(OUT_DIR, "submersion_sensitivity.png")
    p4 = os.path.join(OUT_DIR, "site_layout_10acre.png")

    print("\nGenerating figures…")
    plot_24h_temps_pressure(sim, p1)
    plot_heatmap_cross_section(room, sim, p2)
    plot_submersion_sensitivity(room, pipe, clim, p3)
    plot_site_layout_10acre(p4)

    for p in (p1, p2, p3, p4):
        sz = os.path.getsize(p)
        print(f"  wrote {p}  ({sz} bytes)")

    np.savez(
        os.path.join(OUT_DIR, "sim_summary.npz"),
        **{k: np.array([v]) for k, v in summary.items()},
    )
    print("\nDone. Yes — model includes pipe ID, serpentine length, and fluid gallons.")


if __name__ == "__main__":
    main()
