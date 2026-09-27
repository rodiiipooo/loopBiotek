#!/usr/bin/env python3
"""Optimal earth-shelter submersion fraction.

Sweeps the fraction f of building height below grade and picks f* that
minimizes annual temperature-maintenance energy. Homes must keep a
sunlight path and are not fully buried. Storage and cold storage may
use f = 1. entrance_greenhouse_enclosure adds an air pad over a light
roof or an entrance. The same command prints community hot-water loads
and a shared-microgrid CapEx stub (ASSUMPTION). It does not open Stage 2+
cascade spend.

Usage (from the repo root, with the project venv):

    python climate/thermal-model/submersion_opt.py
    python climate/thermal-model/climate_envelope_sim.py --optimize
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import asdict, dataclass, field, replace
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import climate_envelope_sim as env

OUT_DIR = env.OUT_DIR

# ---------------------------------------------------------------------------
# ASSUMPTION defaults. The markdown table in SUBMERSION_OPTIMAL.md mirrors
# these constants. Change them together.
# ---------------------------------------------------------------------------

# Soil conductivity (W/(m·K)) and volumetric heat capacity (J/(m³·K)).
# moisture_retention is a 0–1 switch: 0 dry, 1 saturated.
K_DRY = 0.30
K_SAT = 1.50
RHO_C_DRY = 1.3e6
RHO_C_SAT = 2.8e6
# Extra conduction path through soil at the buried face (m), lengthened
# as more of the height is submerged (shared berm / longer path).
SOIL_PATH_M = 0.80
GROUND_THROTTLE_GAMMA = 0.75
# Legacy earth-tube UA is derated by (1 + γ_tube f) and scaled by k/k_ref.
TUBE_THROTTLE_GAMMA = 0.40
K_SOIL_REF = 0.80
# Day-of-year used only for the daylight aperture check (near equinox).
DAYLIGHT_DOY = 80
# Unenclosed stick-up: open aperture, not an insulated wall.
OPEN_U = 12.0           # W/(m²·K)
OPEN_ACH = 4.0          # extra air changes per hour at f = 0, scaled by (1-f)
OPEN_SHGC = 0.85
TAU_OPEN = 1.0
# Above-grade greenhouse or vestibule over a light surface or an entrance.
# ASSUMPTION planning values, not a measured sunspace.
BUFFER_HEIGHT_M = 2.4
BUFFER_VESTIBULE_PLAN_M2 = 6.0
BUFFER_ENTRANCE_M2 = 2.0
BUFFER_U = 2.8
BUFFER_ACH = 1.5
BUFFER_TAU = 0.70
BUFFER_ABSORPTANCE = 0.25
BUFFER_ROOM_AIR_FROM_PAD = 0.75
# Visible transmittance of a water-film roof vs the dry glazing tau_vis.
TAU_ROOF_WATER = 0.55
# Share of monthly horizontal irradiance treated as isotropic diffuse.
# The rest uses the clear-sky tilt ratio. Stops a clear-sky beam factor
# from being applied to a cloudy monthly GHI.
DIFFUSE_FRACTION = 0.50
# Water-pane solar split inherited from the legacy envelope model.
G_SOLAR_TO_ROOM_WATER = 0.08
G_SOLAR_TO_WATER = 0.62
# Informational electric conversion. The objective is thermal kWh, not this.
COP_HEAT = 2.5
COP_COOL = 3.0

# Material library stubs. U in W/(m²·K). Glazing also carries SHGC and tau_vis.
WALL_MATERIALS: Dict[str, Dict[str, float]] = {
    "insulated_concrete": {"U": 0.45},
    "sip_r20": {"U": 0.28},
    "earthbag": {"U": 1.10},
    "uninsulated_concrete": {"U": 3.30},
}
ROOF_MATERIALS: Dict[str, Dict[str, float]] = {
    "insulated_roof": {"U": 0.30},
    "vegetated_roof": {"U": 0.40},
    "uninsulated_metal": {"U": 5.50},
}
FLOOR_MATERIALS: Dict[str, Dict[str, float]] = {
    "insulated_slab": {"U": 0.50},
    "uninsulated_slab": {"U": 1.50},
}
GLAZING_MATERIALS: Dict[str, Dict[str, float]] = {
    "double_polycarbonate": {"U": 2.8, "SHGC": 0.55, "tau_vis": 0.65},
    "double_low_e": {"U": 1.6, "SHGC": 0.35, "tau_vis": 0.60},
    "single_poly": {"U": 5.5, "SHGC": 0.75, "tau_vis": 0.80},
}
STRUCTURES: Dict[str, Dict[str, float]] = {
    "concrete_berm": {"mass_wall_frac": 0.35, "slab_thickness_m": 0.20},
    "timber_frame": {"mass_wall_frac": 0.08, "slab_thickness_m": 0.12},
    "earthbag_mass": {"mass_wall_frac": 0.90, "slab_thickness_m": 0.25},
}


@dataclass(frozen=True)
class UseTypeSpec:
    """Setpoint band, gains, and caps that differ by how the cell is used.

    ``requires_sunlight`` means a clear ceiling or glazed wall/roof surfaces.
    ``max_f_policy`` is a hard cap on the fraction of height below grade.
    Homes stay strictly below 1. Storage may use 1.
    """

    key: str
    T_heat_C: float
    T_cool_C: float
    q_internal_W_per_m2: float
    min_daylight_ratio: float
    egress_min_clear_height_m: float
    view_min_exposed_fraction: float
    wall_glazing_frac: float
    requires_sunlight: bool = False
    max_f_policy: float = 1.0


USE_TYPES: Dict[str, UseTypeSpec] = {
    "living": UseTypeSpec(
        key="living",
        T_heat_C=20.0,
        T_cool_C=26.0,
        q_internal_W_per_m2=8.0,
        min_daylight_ratio=0.12,
        egress_min_clear_height_m=1.05,
        view_min_exposed_fraction=0.30,
        wall_glazing_frac=0.40,
        requires_sunlight=True,
        # Never fully bury a home. Egress/view/daylight usually bind tighter.
        max_f_policy=0.85,
    ),
    "storage": UseTypeSpec(
        key="storage",
        # Wider than living (20–26 °C) but still a conditioned band. A 5–35 °C
        # band sits inside the free-float DFW year for this envelope, so every
        # f has the same (zero) energy and the sweep cannot see burial.
        T_heat_C=10.0,
        T_cool_C=28.0,
        q_internal_W_per_m2=1.0,
        min_daylight_ratio=0.0,
        egress_min_clear_height_m=0.0,
        view_min_exposed_fraction=0.0,
        wall_glazing_frac=0.0,
        requires_sunlight=False,
        max_f_policy=1.0,
    ),
    "cold_storage": UseTypeSpec(
        key="cold_storage",
        # Refrigerated band, colder than dry storage. ASSUMPTION: a cooler
        # (about 1–4 °C), not a freezer. Fully buried is allowed.
        T_heat_C=1.0,
        T_cool_C=4.0,
        q_internal_W_per_m2=2.0,
        min_daylight_ratio=0.0,
        egress_min_clear_height_m=0.0,
        view_min_exposed_fraction=0.0,
        wall_glazing_frac=0.0,
        requires_sunlight=False,
        max_f_policy=1.0,
    ),
    "greenhouse": UseTypeSpec(
        key="greenhouse",
        T_heat_C=12.0,
        T_cool_C=30.0,
        q_internal_W_per_m2=2.0,
        min_daylight_ratio=0.40,
        egress_min_clear_height_m=0.45,
        view_min_exposed_fraction=0.0,
        wall_glazing_frac=0.10,
    ),
}


@dataclass(frozen=True)
class MonthClimate:
    name: str
    doy: int
    days: int
    T_min_C: float
    T_max_C: float
    ghi_kwh_m2: float
    day_length_h: float


@dataclass(frozen=True)
class SiteClimate:
    """Local air-temperature series plus the undisturbed-soil annual wave."""

    name: str
    latitude_deg: float
    T_mean_soil_C: float
    A_surf_K: float
    t_peak_doy: float
    months: Tuple[MonthClimate, ...]


# Rounded planning values in the shape of Dallas–Fort Worth monthly normals.
# Not a TMY file. Replace the table (or pass a CSV) for another site.
DFW_MONTHS: Tuple[MonthClimate, ...] = (
    MonthClimate("Jan", 15, 31, 2.2, 13.9, 2.7, 10.2),
    MonthClimate("Feb", 46, 28, 4.4, 16.1, 3.5, 11.0),
    MonthClimate("Mar", 74, 31, 8.9, 20.6, 4.6, 12.0),
    MonthClimate("Apr", 105, 30, 13.3, 25.0, 5.5, 13.0),
    MonthClimate("May", 135, 31, 18.3, 28.9, 6.2, 13.8),
    MonthClimate("Jun", 166, 30, 22.8, 33.3, 6.8, 14.2),
    MonthClimate("Jul", 196, 31, 25.0, 35.6, 6.9, 14.0),
    MonthClimate("Aug", 227, 31, 24.4, 35.6, 6.2, 13.3),
    MonthClimate("Sep", 258, 30, 20.6, 31.1, 5.1, 12.3),
    MonthClimate("Oct", 288, 31, 14.4, 26.1, 4.0, 11.3),
    MonthClimate("Nov", 319, 30, 8.3, 19.4, 2.9, 10.4),
    MonthClimate("Dec", 349, 31, 3.3, 14.4, 2.4, 10.0),
)

DFW_TYPICAL = SiteClimate(
    name="dfw_typical",
    latitude_deg=32.90,
    T_mean_soil_C=18.5,
    A_surf_K=11.0,
    t_peak_doy=205.0,
    months=DFW_MONTHS,
)


@dataclass
class SubmersionCase:
    """One planning case. Switches cover Rod's driver list."""

    name: str
    use_type: str
    L_m: float = 10.0
    W_m: float = 10.0
    H_m: float = 3.0
    clear_ceiling: bool = False
    water_panes: bool = False
    above_grade_enclosure: bool = True
    glazed_roof_frac: float = 1.0
    ceiling_tilt_deg: float = 0.0
    ceiling_azimuth_from_south_deg: float = 0.0
    wall_material: str = "insulated_concrete"
    roof_material: str = "insulated_roof"
    glazing_material: str = "double_polycarbonate"
    floor_material: str = "insulated_slab"
    structure: str = "concrete_berm"
    soil_moisture_retention: float = 0.50
    wall_glazing_frac: Optional[float] = None
    # Azimuth from south, degrees (west positive), and relative weight.
    glazing_azimuth_weights: Tuple[Tuple[float, float], ...] = (
        (0.0, 0.70),
        (90.0, 0.15),
        (-90.0, 0.15),
    )
    # Greenhouse or vestibule over the light surface and/or the entrance.
    entrance_greenhouse_enclosure: bool = False


@dataclass
class CurvePoint:
    f: float
    feasible: bool
    E_kWh: float
    E_heat_kWh: float
    E_cool_kWh: float
    E_elec_kWh: float
    daylight_ratio: float
    closure_K: float


@dataclass
class Optimum:
    case: SubmersionCase
    climate_name: str
    f_star: Optional[float]
    f_max: float
    caps: Dict[str, float]
    binding_caps: List[str]
    limiter: str
    E_star_kWh: Optional[float]
    E_heat_kWh: Optional[float]
    E_cool_kWh: Optional[float]
    E_elec_kWh: Optional[float]
    soil_k: float
    curve: List[CurvePoint] = field(default_factory=list)
    note: str = ""


def has_sunlight_path(case: SubmersionCase) -> bool:
    """Clear ceiling or glazed surfaces. Open sky with no glazing does not count."""
    roof = case.clear_ceiling and case.glazed_roof_frac > 0.0
    walls = case.above_grade_enclosure and glazing_fraction(case) > 0.0
    return roof or walls


def example_cases() -> List[SubmersionCase]:
    """Sunlit living, fully buryable dry storage, cold storage, and a greenhouse."""
    return [
        SubmersionCase(
            name="living",
            use_type="living",
            clear_ceiling=True,
            water_panes=True,
            above_grade_enclosure=True,
            glazed_roof_frac=1.0,
        ),
        SubmersionCase(
            name="storage",
            use_type="storage",
            clear_ceiling=False,
            water_panes=False,
            above_grade_enclosure=True,
        ),
        SubmersionCase(
            name="cold_storage",
            use_type="cold_storage",
            clear_ceiling=False,
            water_panes=False,
            above_grade_enclosure=True,
        ),
        SubmersionCase(
            name="greenhouse",
            use_type="greenhouse",
            clear_ceiling=True,
            water_panes=True,
            above_grade_enclosure=True,
            glazed_roof_frac=1.0,
            ceiling_tilt_deg=0.0,
            ceiling_azimuth_from_south_deg=0.0,
        ),
    ]


def _require(mapping: Dict, key: str, kind: str):
    if key not in mapping:
        known = ", ".join(sorted(mapping))
        raise KeyError(f"unknown {kind} {key!r}; choose from {known}")
    return mapping[key]


def soil_properties(moisture_retention: float) -> Tuple[float, float, float]:
    """Return k (W/(m·K)), ρc (J/(m³·K)), and damping depth D (m)."""
    phi = min(1.0, max(0.0, float(moisture_retention)))
    k = K_DRY + phi * (K_SAT - K_DRY)
    rho_c = RHO_C_DRY + phi * (RHO_C_SAT - RHO_C_DRY)
    alpha = k / rho_c
    omega = 2.0 * math.pi / (365.25 * 86400.0)
    damping_m = math.sqrt(2.0 * alpha / omega)
    return k, rho_c, damping_m


def T_soil_C(z_m: float, doy: float, climate: SiteClimate, damping_m: float) -> float:
    """Undisturbed soil temperature at depth z (Kusuda wave, ASSUMPTION phase)."""
    z = max(0.0, float(z_m))
    D = max(damping_m, 1e-3)
    phase = 2.0 * math.pi * (doy - climate.t_peak_doy) / 365.25 - z / D
    return climate.T_mean_soil_C + climate.A_surf_K * math.exp(-z / D) * math.cos(phase)


def _daily_tilt_factor_raw(
    tilt_deg: float, az_from_south_deg: float, doy: float, lat_deg: float
) -> float:
    """Daily irradiation on a tilted plane divided by daily horizontal irradiation.

    Clear-sky geometry only: the sun is integrated from sunrise to sunset and
    the ratio multiplies the climate file's horizontal half-sine. ASSUMPTION:
    the diurnal shape stays a half-sine; only the daily total is rescaled.
    Azimuth is degrees from south, west positive.
    """
    lat = math.radians(lat_deg)
    dec = math.radians(23.45 * math.sin(math.radians(360.0 * (284.0 + doy) / 365.0)))
    arg = -math.tan(lat) * math.tan(dec)
    if arg >= 1.0:
        return 0.0
    omega_s = math.pi if arg <= -1.0 else math.acos(arg)
    tilt = math.radians(tilt_deg)
    az_s = math.radians(az_from_south_deg)
    n_z = math.cos(tilt)
    n_y = math.sin(tilt) * math.cos(az_s)
    n_x = math.sin(tilt) * math.sin(az_s)
    n_steps = 36
    sum_h = 0.0
    sum_t = 0.0
    for i in range(n_steps):
        omega = -omega_s + (2.0 * omega_s) * (i + 0.5) / n_steps
        sin_alt = (
            math.sin(lat) * math.sin(dec)
            + math.cos(lat) * math.cos(dec) * math.cos(omega)
        )
        if sin_alt <= 0.0:
            continue
        cos_alt = math.sqrt(max(0.0, 1.0 - sin_alt * sin_alt))
        denom = cos_alt * math.cos(lat)
        if abs(denom) < 1e-8:
            cos_az = 1.0
        else:
            cos_az = (sin_alt * math.sin(lat) - math.sin(dec)) / denom
        cos_az = min(1.0, max(-1.0, cos_az))
        sin_az = math.sqrt(max(0.0, 1.0 - cos_az * cos_az))
        if omega < 0.0:
            sin_az = -sin_az
        sun_z = sin_alt
        sun_y = cos_alt * cos_az
        sun_x = cos_alt * sin_az
        sum_h += sun_z
        sum_t += max(0.0, sun_x * n_x + sun_y * n_y + sun_z * n_z)
    if sum_h <= 1e-9:
        return 0.0
    return sum_t / sum_h


@lru_cache(maxsize=4096)
def _tilt_cached(tilt_centi: int, az_centi: int, doy: int, lat_centi: int) -> float:
    return _daily_tilt_factor_raw(tilt_centi / 100.0, az_centi / 100.0, float(doy), lat_centi / 100.0)


def daily_tilt_factor(
    tilt_deg: float, az_from_south_deg: float, doy: float, lat_deg: float
) -> float:
    return _tilt_cached(
        int(round(tilt_deg * 100.0)),
        int(round(az_from_south_deg * 100.0)),
        int(round(doy)),
        int(round(lat_deg * 100.0)),
    )


def effective_tilt_factor(
    tilt_deg: float, az_from_south_deg: float, doy: float, lat_deg: float
) -> float:
    """Blend clear-sky beam geometry with an isotropic diffuse sky."""
    direct = daily_tilt_factor(tilt_deg, az_from_south_deg, doy, lat_deg)
    diffuse = 0.5 * (1.0 + math.cos(math.radians(tilt_deg)))
    frac = min(1.0, max(0.0, DIFFUSE_FRACTION))
    return (1.0 - frac) * direct + frac * diffuse


def glazing_fraction(case: SubmersionCase) -> float:
    if case.wall_glazing_frac is not None:
        return float(case.wall_glazing_frac)
    return USE_TYPES[case.use_type].wall_glazing_frac


def azimuth_weights(case: SubmersionCase) -> List[Tuple[float, float]]:
    raw = list(case.glazing_azimuth_weights)
    total = sum(w for _, w in raw)
    if total <= 0.0:
        raise ValueError(f"{case.name}: glazing azimuth weights must sum to > 0")
    return [(az, w / total) for az, w in raw]


def daylight_ratio(case: SubmersionCase, f: float, climate: SiteClimate) -> float:
    """Glazed (or open) aperture area times visible transmittance, over floor area."""
    floor = case.L_m * case.W_m
    if floor <= 0.0:
        return 0.0
    glaze = _require(GLAZING_MATERIALS, case.glazing_material, "glazing")
    aperture = 0.0
    if case.clear_ceiling and case.glazed_roof_frac > 0.0:
        tau = TAU_ROOF_WATER if case.water_panes else glaze["tau_vis"]
        if case.entrance_greenhouse_enclosure:
            tau *= BUFFER_TAU
        sky = effective_tilt_factor(
            case.ceiling_tilt_deg,
            case.ceiling_azimuth_from_south_deg,
            DAYLIGHT_DOY,
            climate.latitude_deg,
        )
        aperture += floor * case.glazed_roof_frac * tau * min(1.25, max(0.0, sky))
    perimeter = 2.0 * (case.L_m + case.W_m)
    exposed = perimeter * max(0.0, 1.0 - f) * case.H_m
    if case.above_grade_enclosure:
        aperture += exposed * glazing_fraction(case) * glaze["tau_vis"]
    else:
        aperture += exposed * TAU_OPEN
    return aperture / floor


def max_f_for_daylight(case: SubmersionCase, climate: SiteClimate) -> float:
    spec = USE_TYPES[case.use_type]
    if spec.min_daylight_ratio <= 0.0:
        return 1.0
    if daylight_ratio(case, 0.0, climate) + 1e-12 < spec.min_daylight_ratio:
        return -1.0
    lo, hi = 0.0, 1.0
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if daylight_ratio(case, mid, climate) >= spec.min_daylight_ratio:
            lo = mid
        else:
            hi = mid
    return lo


def constraint_caps(case: SubmersionCase, climate: SiteClimate) -> Dict[str, float]:
    spec = USE_TYPES[case.use_type]
    if case.H_m <= 0.0:
        raise ValueError("building height must be positive")
    caps = {"domain": 1.0}
    if spec.egress_min_clear_height_m > 0.0:
        caps["egress"] = max(0.0, 1.0 - spec.egress_min_clear_height_m / case.H_m)
    if spec.view_min_exposed_fraction > 0.0:
        caps["view"] = max(0.0, 1.0 - spec.view_min_exposed_fraction)
    if spec.max_f_policy < 1.0 - 1e-9:
        caps["no_full_burial"] = min(1.0, max(0.0, spec.max_f_policy))
    caps["daylight"] = max_f_for_daylight(case, climate)
    if spec.requires_sunlight and not has_sunlight_path(case):
        caps["sunlight"] = -1.0
    return caps


def f_max_from_caps(caps: Dict[str, float]) -> float:
    if any(v < 0.0 for v in caps.values()):
        return -1.0
    return min(caps.values()) if caps else 1.0


def binding_cap_names(case: SubmersionCase, caps: Dict[str, float], f_max: float) -> List[str]:
    """Caps that actually stop f. A vacant daylight cap of 1 is not a bind."""
    if f_max < 0.0:
        return ["infeasible"]
    spec = USE_TYPES[case.use_type]
    names = []
    for name, value in caps.items():
        if abs(value - f_max) > 5e-3:
            continue
        if name == "daylight" and spec.min_daylight_ratio <= 0.0:
            continue
        if name == "domain" and any(
            other != "domain" and abs(other_value - f_max) <= 5e-3
            for other, other_value in caps.items()
        ):
            continue
        names.append(name)
    return names or ["domain"]


def series_soil_UA(U: float, area: float, k_soil: float, f: float) -> float:
    """Insulation and a soil path in series. Soil path lengthens with f."""
    if area <= 1e-8 or U <= 0.0 or k_soil <= 0.0:
        return 0.0
    ua_ins = U * area
    ua_soil = k_soil * area / (SOIL_PATH_M * (1.0 + GROUND_THROTTLE_GAMMA * f))
    return 1.0 / (1.0 / ua_ins + 1.0 / ua_soil)


def throttled_tube_UA(
    room: env.RoomParams, pipe: env.PipeGeometry, floor_area: float, k_soil: float, f: float
) -> float:
    """Legacy earth-tube UA, scaled by soil conductivity and submersion throttle."""
    base = env.ua_ground_reject(room, pipe, floor_area)
    return base * (k_soil / K_SOIL_REF) / (1.0 + TUBE_THROTTLE_GAMMA * max(0.0, f))


def month_to_climate(month: MonthClimate) -> env.ClimateParams:
    sunrise = 12.0 - 0.5 * month.day_length_h
    g_peak = month.ghi_kwh_m2 * 1000.0 * math.pi / (2.0 * month.day_length_h)
    return env.ClimateParams(
        T_min_C=month.T_min_C,
        T_max_C=month.T_max_C,
        T_peak_hour=15.0,
        G_peak_W_m2=g_peak,
        day_length_h=month.day_length_h,
        sunrise_h=sunrise,
    )


def _pipe_for_roof(case: SubmersionCase, glazed_area: float) -> env.PipeGeometry:
    full = case.L_m * case.W_m
    if glazed_area <= 1e-8 or full <= 0.0:
        return env.PipeGeometry(window_L_m=case.L_m, window_W_m=case.W_m)
    scale = math.sqrt(glazed_area / full)
    return env.PipeGeometry(
        window_L_m=case.L_m * scale,
        window_W_m=case.W_m * scale,
    )


@dataclass(frozen=True)
class BufferSpec:
    """Air pad between outdoors and the facility. Disabled specs are all zeros."""

    enabled: bool
    covers_light: bool
    plan_m2: float
    volume_m3: float
    roof_area_in_buffer_m2: float
    wall_area_in_buffer_m2: float
    UA_outdoor: float
    C_J_per_K: float


def buffer_spec(
    case: SubmersionCase,
    floor_area: float,
    exposed_area: float,
    glazed_area: float,
    opaque_area: float,
) -> BufferSpec:
    """Greenhouse over a light roof, or a vestibule over the entrance hatch.

    A clear ceiling is the light-entering surface, so the pad covers that
    roof. An opaque roof only puts the door or hatch inside the pad.
    """
    empty = BufferSpec(False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    if not case.entrance_greenhouse_enclosure:
        return empty
    covers_light = bool(case.clear_ceiling and case.glazed_roof_frac > 0.0 and glazed_area > 0.0)
    wall_in = min(BUFFER_ENTRANCE_M2, max(0.0, exposed_area))
    if covers_light:
        plan = max(floor_area * min(1.0, case.glazed_roof_frac), BUFFER_VESTIBULE_PLAN_M2)
        roof_in = floor_area
    else:
        plan = BUFFER_VESTIBULE_PLAN_M2
        hatch = max(0.0, BUFFER_ENTRANCE_M2 - wall_in)
        roof_in = min(hatch, opaque_area + glazed_area)
    volume = plan * BUFFER_HEIGHT_M
    side = 4.0 * math.sqrt(max(plan, 1e-6)) * BUFFER_HEIGHT_M
    skin = plan + side
    ua_skin = BUFFER_U * skin
    ua_inf = env.RHO_AIR * env.CP_AIR * volume * BUFFER_ACH / 3600.0
    capacitance = env.RHO_AIR * env.CP_AIR * volume
    return BufferSpec(
        enabled=True,
        covers_light=covers_light,
        plan_m2=plan,
        volume_m3=volume,
        roof_area_in_buffer_m2=roof_in,
        wall_area_in_buffer_m2=wall_in,
        UA_outdoor=ua_skin + ua_inf,
        C_J_per_K=capacitance,
    )


def build_envelope(
    case: SubmersionCase,
    f: float,
    month: MonthClimate,
    climate: SiteClimate,
    hours: float,
    dt_s: float,
) -> Tuple[env.RoomParams, env.PipeGeometry, env.SimExtras, env.ClimateParams]:
    """Map switches + f + one design day onto the envelope integrator."""
    spec = _require(USE_TYPES, case.use_type, "use type")
    wall = _require(WALL_MATERIALS, case.wall_material, "wall material")
    roof = _require(ROOF_MATERIALS, case.roof_material, "roof material")
    glaze = _require(GLAZING_MATERIALS, case.glazing_material, "glazing")
    floor_mat = _require(FLOOR_MATERIALS, case.floor_material, "floor material")
    structure = _require(STRUCTURES, case.structure, "structure")
    k_soil, _rho_c, damping_m = soil_properties(case.soil_moisture_retention)

    f = min(1.0, max(0.0, f))
    floor_area = case.L_m * case.W_m
    if case.clear_ceiling:
        glazed_area = floor_area * min(1.0, max(0.0, case.glazed_roof_frac))
    else:
        glazed_area = 0.0
    opaque_area = max(0.0, floor_area - glazed_area)
    glazed_frac = 0.0 if floor_area <= 0.0 else glazed_area / floor_area

    water_on = bool(case.water_panes and glazed_area > 0.0)
    if water_on:
        g_room = G_SOLAR_TO_ROOM_WATER
        g_water = G_SOLAR_TO_WATER
        ua_rw: Optional[float] = None
    elif glazed_area > 0.0:
        g_room = glaze["SHGC"]
        g_water = 0.0
        ua_rw = 0.0
    else:
        g_room = 0.0
        g_water = 0.0
        ua_rw = 0.0

    perimeter = 2.0 * (case.L_m + case.W_m)
    exposed_area = perimeter * (1.0 - f) * case.H_m
    frac_g = glazing_fraction(case)
    if case.above_grade_enclosure:
        ua_exposed = wall["U"] * exposed_area * (1.0 - frac_g) + glaze["U"] * exposed_area * frac_g
        ach_extra = 0.0
        solar_area = exposed_area * frac_g
        shgc_wall = glaze["SHGC"]
    else:
        ua_exposed = OPEN_U * exposed_area
        ach_extra = OPEN_ACH * (1.0 - f)
        solar_area = exposed_area
        shgc_wall = OPEN_SHGC

    z_floor = max(f * case.H_m, 0.05)
    z_wall = max(0.5 * f * case.H_m, 0.05)
    z_tube = max(f * case.H_m, 0.30)
    t_floor = T_soil_C(z_floor, month.doy, climate, damping_m)
    t_wall = T_soil_C(z_wall, month.doy, climate, damping_m)
    t_tube = T_soil_C(z_tube, month.doy, climate, damping_m)

    buried_area = perimeter * f * case.H_m
    ua_wall = series_soil_UA(wall["U"], buried_area, k_soil, f)
    ua_floor = series_soil_UA(floor_mat["U"], floor_area, k_soil, f)

    room = env.RoomParams(
        L_m=case.L_m,
        W_m=case.W_m,
        H_m=case.H_m,
        submersion=f,
        glazed_roof_frac=glazed_frac,
        U_glazing=glaze["U"],
        U_earth_wall=wall["U"],
        U_earth_floor=floor_mat["U"],
        U_exposed_wall=wall["U"],
        UA_roof_to_water=ua_rw,
        ACH=1.0,
        Q_internal_W=spec.q_internal_W_per_m2 * floor_area,
        g_solar_to_room=g_room,
        g_solar_to_water=g_water,
        slab_thickness_m=structure["slab_thickness_m"],
        mass_wall_frac=structure["mass_wall_frac"] * (0.30 + 0.70 * f),
        T_soil_C=t_tube,
        T0_room_C=0.5 * (spec.T_heat_C + spec.T_cool_C),
        T0_water_C=t_tube,
    )
    pipe = _pipe_for_roof(case, glazed_area if water_on else 0.0)
    if water_on:
        ua_reject = throttled_tube_UA(room, pipe, floor_area, k_soil, f)
    else:
        ua_reject = 0.0

    clim = month_to_climate(month)
    t_all = env.simulation_hours(hours, dt_s)
    horizontal = env.solar_G(t_all % 24.0, clim)
    extra = np.zeros_like(horizontal)
    if solar_area > 0.0:
        for az, weight in azimuth_weights(case):
            scale = effective_tilt_factor(90.0, az, month.doy, climate.latitude_deg)
            extra += shgc_wall * (solar_area * weight) * scale * horizontal
    if case.clear_ceiling and glazed_area > 0.0:
        roof_scale = effective_tilt_factor(
            case.ceiling_tilt_deg,
            case.ceiling_azimuth_from_south_deg,
            month.doy,
            climate.latitude_deg,
        )
    else:
        roof_scale = 1.0

    buf = buffer_spec(case, floor_area, exposed_area, glazed_area, opaque_area)
    ua_roof = glaze["U"] * glazed_area + roof["U"] * opaque_area
    if buf.enabled and floor_area > 0.0:
        roof_frac = min(1.0, buf.roof_area_in_buffer_m2 / floor_area)
        wall_frac = 0.0 if exposed_area <= 1e-8 else min(1.0, buf.wall_area_in_buffer_m2 / exposed_area)
        ua_roof_buffer = ua_roof * roof_frac
        ua_roof_outdoor = ua_roof - ua_roof_buffer
        ua_wall_buffer = ua_exposed * wall_frac
        ua_wall_outdoor = ua_exposed - ua_wall_buffer
        pad_frac = BUFFER_ROOM_AIR_FROM_PAD
        if buf.covers_light:
            roof_scale *= BUFFER_TAU
        q_buffer = buf.plan_m2 * BUFFER_ABSORPTANCE * horizontal
    else:
        ua_roof_buffer = 0.0
        ua_roof_outdoor = ua_roof
        ua_wall_buffer = 0.0
        ua_wall_outdoor = ua_exposed
        pad_frac = 0.0
        q_buffer = np.zeros_like(horizontal)

    extras = env.SimExtras(
        T_soil_floor_C=t_floor,
        T_soil_wall_C=t_wall,
        T_soil_reject_C=t_tube,
        UA_floor_earth=ua_floor,
        UA_wall_earth=ua_wall,
        UA_exposed=ua_exposed,
        UA_reject=ua_reject,
        U_roof_opaque=roof["U"],
        A_roof_opaque=opaque_area,
        ACH_extra=ach_extra,
        roof_solar_scale=roof_scale,
        Q_solar_room_extra_W=extra,
        T_heat_C=spec.T_heat_C,
        T_cool_C=spec.T_cool_C,
        buffer_enabled=buf.enabled,
        C_buffer=buf.C_J_per_K,
        UA_buffer_outdoor=buf.UA_outdoor,
        UA_roof_outdoor=ua_roof_outdoor,
        UA_roof_buffer=ua_roof_buffer,
        UA_wall_outdoor=ua_wall_outdoor,
        UA_wall_buffer=ua_wall_buffer,
        buffer_infiltration_from_pad=pad_frac,
        Q_solar_buffer_W=q_buffer if buf.enabled else None,
        T0_buffer_C=0.5 * (spec.T_heat_C + spec.T_cool_C),
        buffer_plan_m2=buf.plan_m2,
        buffer_volume_m3=buf.volume_m3,
    )
    return room, pipe, extras, clim


def steady_node_temperatures(
    room: env.RoomParams,
    pipe: env.PipeGeometry,
    extras: env.SimExtras,
    clim: env.ClimateParams,
) -> Tuple[float, float, float]:
    """Daily-mean room, water, and buffer temperatures with the thermostat off.

    The structural mass is slow compared with a day, so the transient is
    started here (then clamped to the band) instead of drifting for weeks.
    The buffer return is the outdoor mean when the air pad is off.
    """
    areas = env.areas(room)
    ua_rw = room.UA_roof_to_water if room.UA_roof_to_water is not None else env.ua_roof_to_water(pipe)
    ach = room.ACH + extras.ACH_extra
    v_dot = areas["volume"] * ach / 3600.0
    ua_inf = env.RHO_AIR * env.CP_AIR * v_dot
    ua_exposed = 0.0 if extras.UA_exposed is None else extras.UA_exposed
    ua_floor = 0.0 if extras.UA_floor_earth is None else extras.UA_floor_earth
    ua_wall = 0.0 if extras.UA_wall_earth is None else extras.UA_wall_earth
    ua_rej = 0.0 if extras.UA_reject is None else extras.UA_reject
    ua_out = (
        extras.U_roof_opaque * extras.A_roof_opaque
        + room.U_glazing * areas["glazed_roof"]
        + ua_exposed
        + ua_inf
    )
    t_out = 0.5 * (clim.T_min_C + clim.T_max_C)
    t_floor = room.T_soil_C if extras.T_soil_floor_C is None else extras.T_soil_floor_C
    t_wall = room.T_soil_C if extras.T_soil_wall_C is None else extras.T_soil_wall_C
    t_rej = room.T_soil_C if extras.T_soil_reject_C is None else extras.T_soil_reject_C
    # One synthetic day; mean(G) matches the half-sine used in the integrator.
    t_day = env.simulation_hours(24.0, 3600.0)
    g_mean = float(np.mean(env.solar_G(t_day % 24.0, clim)))
    q_roof_r = room.g_solar_to_room * extras.roof_solar_scale * g_mean * areas["glazed_roof"]
    q_roof_w = room.g_solar_to_water * extras.roof_solar_scale * g_mean * areas["glazed_roof"]
    q_wall = 0.0 if extras.Q_solar_room_extra_W is None else float(np.mean(extras.Q_solar_room_extra_W))
    ua_inf_buf = 0.0
    ua_rb = 0.0
    if extras.buffer_enabled:
        pad = min(1.0, max(0.0, extras.buffer_infiltration_from_pad))
        ua_inf_buf = pad * ua_inf
        ua_rb = extras.UA_roof_buffer + extras.UA_wall_buffer + ua_inf_buf
    ua_direct = max(0.0, ua_out - ua_rb)
    a_rr = ua_rw + ua_direct + ua_rb + ua_floor + ua_wall
    rhs_r = q_roof_r + q_wall + room.Q_internal_W + ua_direct * t_out + ua_floor * t_floor + ua_wall * t_wall
    a_ww = ua_rw + ua_rej
    rhs_w = q_roof_w + ua_rej * t_rej
    q_buf = 0.0 if extras.Q_solar_buffer_W is None else float(np.mean(extras.Q_solar_buffer_W))
    ua_bo = extras.UA_buffer_outdoor if extras.buffer_enabled else 0.0
    if a_ww <= 1e-8 and ua_rb <= 1e-8:
        t_r = t_out if a_rr <= 1e-8 else rhs_r / a_rr
        return t_r, t_rej, t_out
    # Water: Tw = (rhs_w + ua_rw * Tr) / a_ww
    # Buffer: Tb = (q_buf + ua_bo * t_out + ua_rb * Tr) / (ua_rb + ua_bo)
    water_den = a_ww if a_ww > 1e-8 else 1.0
    buf_den = ua_rb + ua_bo
    if buf_den <= 1e-8:
        buf_den = 1.0
        ua_rb_eff = 0.0
        rhs_b = t_out
    else:
        ua_rb_eff = ua_rb
        rhs_b = q_buf + ua_bo * t_out
    # (a_rr - ua_rw^2/a_ww - ua_rb^2/buf_den) Tr = rhs_r + ua_rw*rhs_w/a_ww + ua_rb*rhs_b/buf_den
    coef = a_rr
    rhs = rhs_r
    if a_ww > 1e-8:
        coef -= (ua_rw * ua_rw) / water_den
        rhs += ua_rw * rhs_w / water_den
    if ua_rb_eff > 1e-8:
        coef -= (ua_rb_eff * ua_rb_eff) / buf_den
        rhs += ua_rb_eff * rhs_b / buf_den
    if abs(coef) <= 1e-8:
        return t_out, t_rej, t_out
    t_r = rhs / coef
    t_w = t_rej if a_ww <= 1e-8 else (rhs_w + ua_rw * t_r) / water_den
    t_b = t_out if ua_rb_eff <= 1e-8 else (rhs_b + ua_rb_eff * t_r) / buf_den
    return t_r, t_w, t_b


def day_energy(
    case: SubmersionCase,
    f: float,
    month: MonthClimate,
    climate: SiteClimate,
    hours: float = 72.0,
    dt_s: float = 60.0,
) -> Tuple[float, float, float]:
    """Settled-day heating kWh, cooling kWh, and |ΔT| closure across that day."""
    room, pipe, extras, clim = build_envelope(case, f, month, climate, hours, dt_s)
    t_r, t_w, t_b = steady_node_temperatures(room, pipe, extras, clim)
    if extras.T_heat_C is not None and extras.T_cool_C is not None:
        t_r = min(extras.T_cool_C, max(extras.T_heat_C, t_r))
    room.T0_room_C = t_r
    room.T0_water_C = t_w
    extras.T0_buffer_C = t_b
    sim = env.simulate(room, pipe, clim, hours=hours, dt_s=dt_s, extras=extras)
    closure = abs(float(sim["T_room"][0]) - float(sim["T_room"][-1]))
    return float(sim["E_heat_kWh"][0]), float(sim["E_cool_kWh"][0]), closure


def annual_energy(
    case: SubmersionCase,
    f: float,
    climate: SiteClimate,
    hours: float = 72.0,
    dt_s: float = 60.0,
    months: Optional[Sequence[MonthClimate]] = None,
) -> Tuple[float, float, float, float]:
    """Return annual thermal kWh, heating, cooling, and the worst day-closure (K)."""
    use_months = climate.months if months is None else months
    heat = 0.0
    cool = 0.0
    worst_closure = 0.0
    for month in use_months:
        h, c, closure = day_energy(case, f, month, climate, hours=hours, dt_s=dt_s)
        heat += h * month.days
        cool += c * month.days
        worst_closure = max(worst_closure, closure)
    return heat + cool, heat, cool, worst_closure


def f_grid(f_step: float, f_max: float) -> List[float]:
    if f_step <= 0.0 or f_step > 1.0:
        raise ValueError("f_step must be in (0, 1]")
    n = int(round(1.0 / f_step))
    values = [round(i * f_step, 5) for i in range(n + 1)]
    if 0.0 <= f_max <= 1.0:
        snapped = round(f_max, 5)
        if all(abs(v - snapped) > 1e-4 for v in values):
            values.append(snapped)
    return sorted(values)


def sweep_case(
    case: SubmersionCase,
    climate: SiteClimate = DFW_TYPICAL,
    f_step: float = 0.05,
    hours: float = 72.0,
    dt_s: float = 60.0,
    months: Optional[Sequence[MonthClimate]] = None,
) -> Optimum:
    caps = constraint_caps(case, climate)
    f_max = f_max_from_caps(caps)
    binding = binding_cap_names(case, caps, f_max)
    k_soil, _, _ = soil_properties(case.soil_moisture_retention)
    curve: List[CurvePoint] = []
    for f in f_grid(f_step, f_max if f_max >= 0.0 else 1.0):
        total, heat, cool, closure = annual_energy(
            case, f, climate, hours=hours, dt_s=dt_s, months=months
        )
        day = daylight_ratio(case, f, climate)
        spec = USE_TYPES[case.use_type]
        feasible = f_max >= 0.0 and f <= f_max + 1e-6 and day + 1e-9 >= spec.min_daylight_ratio
        elec = heat / COP_HEAT + cool / COP_COOL
        curve.append(
            CurvePoint(
                f=f,
                feasible=feasible,
                E_kWh=total,
                E_heat_kWh=heat,
                E_cool_kWh=cool,
                E_elec_kWh=elec,
                daylight_ratio=day,
                closure_K=closure,
            )
        )
    feasible_pts = [p for p in curve if p.feasible]
    if not feasible_pts:
        return Optimum(
            case=case,
            climate_name=climate.name,
            f_star=None,
            f_max=f_max,
            caps=caps,
            binding_caps=binding,
            limiter="infeasible",
            E_star_kWh=None,
            E_heat_kWh=None,
            E_cool_kWh=None,
            E_elec_kWh=None,
            soil_k=k_soil,
            curve=curve,
            note="No f in [0, 1] meets the daylight / egress / view caps.",
        )
    best = min(feasible_pts, key=lambda p: (p.E_kWh, p.f))
    on_cap = abs(best.f - f_max) <= max(0.5 * f_step, 1e-3)
    limiter = "use-type cap" if on_cap else "energy minimum inside the cap"
    return Optimum(
        case=case,
        climate_name=climate.name,
        f_star=best.f,
        f_max=f_max,
        caps=caps,
        binding_caps=binding,
        limiter=limiter,
        E_star_kWh=best.E_kWh,
        E_heat_kWh=best.E_heat_kWh,
        E_cool_kWh=best.E_cool_kWh,
        E_elec_kWh=best.E_elec_kWh,
        soil_k=k_soil,
        curve=curve,
        note="",
    )


def read_month_csv(path: str) -> Tuple[MonthClimate, ...]:
    """Load a site year. Columns: name,doy,days,T_min_C,T_max_C,ghi_kwh_m2,day_length_h."""
    required = {"name", "doy", "days", "T_min_C", "T_max_C", "ghi_kwh_m2", "day_length_h"}
    rows: List[MonthClimate] = []
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = required - fields
        if missing:
            raise ValueError(f"climate CSV missing columns: {sorted(missing)}")
        for row in reader:
            if not row.get("name"):
                continue
            rows.append(
                MonthClimate(
                    name=row["name"].strip(),
                    doy=int(float(row["doy"])),
                    days=int(float(row["days"])),
                    T_min_C=float(row["T_min_C"]),
                    T_max_C=float(row["T_max_C"]),
                    ghi_kwh_m2=float(row["ghi_kwh_m2"]),
                    day_length_h=float(row["day_length_h"]),
                )
            )
    if not rows:
        raise ValueError(f"no month rows in {path}")
    return tuple(rows)


def switches_dict(case: SubmersionCase) -> Dict[str, object]:
    spec = USE_TYPES[case.use_type]
    return {
        "use_type": case.use_type,
        "clear_ceiling": case.clear_ceiling,
        "water_panes": case.water_panes,
        "above_grade_enclosure": case.above_grade_enclosure,
        "L_m": case.L_m,
        "W_m": case.W_m,
        "H_m": case.H_m,
        "glazed_roof_frac": case.glazed_roof_frac if case.clear_ceiling else 0.0,
        "ceiling_tilt_deg": case.ceiling_tilt_deg,
        "ceiling_azimuth_from_south_deg": case.ceiling_azimuth_from_south_deg,
        "wall_material": case.wall_material,
        "roof_material": case.roof_material,
        "glazing_material": case.glazing_material,
        "floor_material": case.floor_material,
        "structure": case.structure,
        "soil_moisture_retention": case.soil_moisture_retention,
        "wall_glazing_frac": glazing_fraction(case),
        "glazing_azimuth_weights": list(case.glazing_azimuth_weights),
        "T_heat_C": spec.T_heat_C,
        "T_cool_C": spec.T_cool_C,
        "q_internal_W_per_m2": spec.q_internal_W_per_m2,
        "min_daylight_ratio": spec.min_daylight_ratio,
        "egress_min_clear_height_m": spec.egress_min_clear_height_m,
        "view_min_exposed_fraction": spec.view_min_exposed_fraction,
        "entrance_greenhouse_enclosure": case.entrance_greenhouse_enclosure,
    }


def format_report(results: Sequence[Optimum]) -> str:
    lines = [
        "Submersion optimizer — annual temperature-maintenance energy",
        "Objective: thermal kWh an ideal thermostat delivers to hold the use-type band.",
        "f is the fraction of building height below grade. Defaults are ASSUMPTIONs.",
        "The legacy summer illustration (RoomParams.submersion = 0.70) is not this f*.",
        "",
        f"{'case':<18}{'f*':>8}{'f_max':>8}{'E_kWh':>12}{'heat':>10}{'cool':>10}  limiter",
    ]
    for result in results:
        if result.f_star is None or result.E_star_kWh is None:
            lines.append(f"{result.case.name:<18}{'—':>8}{result.f_max * 100:7.1f}%  infeasible")
            continue
        lines.append(
            f"{result.case.name:<18}{result.f_star * 100:7.1f}%"
            f"{result.f_max * 100:7.1f}%"
            f"{result.E_star_kWh:12.0f}"
            f"{result.E_heat_kWh:10.0f}"
            f"{result.E_cool_kWh:10.0f}  {result.limiter}"
        )
        cap_txt = ", ".join(f"{k}={v * 100:.1f}%" for k, v in result.caps.items())
        lines.append(f"  caps: {cap_txt}")
        lines.append(f"  binding: {', '.join(result.binding_caps)}")
        sw = switches_dict(result.case)
        lines.append(
            "  switches: use_type={use_type} clear_ceiling={clear_ceiling} "
            "water_panes={water_panes} above_grade_enclosure={above_grade_enclosure} "
            "entrance_greenhouse_enclosure={entrance_greenhouse_enclosure}".format(**sw)
        )
        lines.append(
            "  envelope: {L_m:.0f}×{W_m:.0f}×{H_m:.1f} m  wall={wall_material} "
            "roof={roof_material} glazing={glazing_material} floor={floor_material} "
            "structure={structure}".format(**sw)
        )
        lines.append(
            "  soil moisture retention={soil_moisture_retention:.2f} → k={k:.2f} W/(m·K)  "
            "tilt={tilt:.0f}° az_from_south={az:.0f}°  glazing frac={g:.2f}".format(
                soil_moisture_retention=sw["soil_moisture_retention"],
                k=result.soil_k,
                tilt=sw["ceiling_tilt_deg"],
                az=sw["ceiling_azimuth_from_south_deg"],
                g=sw["wall_glazing_frac"],
            )
        )
        worst = max(p.closure_K for p in result.curve) if result.curve else 0.0
        lines.append(f"  worst day-closure on the sweep: {worst:.2f} K (want a small number)")
    lines.append("")
    lines.append(
        "Electric kWh in the JSON divide heating by COP "
        f"{COP_HEAT:.1f} and cooling by COP {COP_COOL:.1f} (ASSUMPTION). "
        "They are not the objective."
    )
    return "\n".join(lines)


def optimum_to_json(result: Optimum) -> Dict:
    return {
        "name": result.case.name,
        "climate": result.climate_name,
        "f_star": result.f_star,
        "f_star_percent": None if result.f_star is None else round(100.0 * result.f_star, 2),
        "f_max": result.f_max,
        "binding_caps": result.binding_caps,
        "limiter": result.limiter,
        "caps": result.caps,
        "E_star_kWh": result.E_star_kWh,
        "E_heat_kWh": result.E_heat_kWh,
        "E_cool_kWh": result.E_cool_kWh,
        "E_elec_kWh": result.E_elec_kWh,
        "soil_k_W_per_mK": result.soil_k,
        "switches": switches_dict(result.case),
        "note": result.note,
        "curve": [asdict(point) for point in result.curve],
    }


def plot_optimal_curves(results: Sequence[Optimum], path: str) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 5.5))
    colors = {
        "living": "#c53030",
        "storage": "#2b6cb0",
        "cold_storage": "#6b46c1",
        "greenhouse": "#2f855a",
    }
    for result in results:
        if not result.curve or result.f_star is None:
            continue
        color = colors.get(result.case.use_type, "#4a5568")
        xs = [point.f * 100.0 for point in result.curve]
        ys = [point.E_kWh for point in result.curve]
        padded = bool(result.case.entrance_greenhouse_enclosure)
        ax.plot(
            xs,
            ys,
            "--" if padded else "-o",
            color=color,
            lw=1.6 if padded else 2.0,
            ms=3.5 if padded else 4.5,
            alpha=0.95 if padded else 1.0,
            label=f"{result.case.name}   f* = {result.f_star * 100:.0f}%",
        )
        if not padded:
            ax.axvline(result.f_star * 100.0, color=color, ls="--", lw=1.0, alpha=0.85)
    ax.set_xlabel("Submersion (% of building height below grade)")
    ax.set_ylabel("Annual temperature-maintenance energy (thermal kWh)")
    ax.set_xlim(0, 100)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    ax.set_title(
        "Optimal submersion — annual thermostat energy vs height fraction\n"
        "DFW typical-month days · solid is the bare envelope · dashed curve is the air pad"
    )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def buffer_comparison_cases() -> List[SubmersionCase]:
    """Same cells as the examples, with the entrance greenhouse switched on.

    The greenhouse use type is already a glazed roof, so it is not wrapped again.
    """
    wanted = ("living", "storage", "cold_storage")
    base = {case.name: case for case in example_cases()}
    return [
        replace(base[name], name=f"{name}+pad", entrance_greenhouse_enclosure=True)
        for name in wanted
    ]


def _energy_near(result: Optimum, f: float) -> Optional[float]:
    if not result.curve:
        return None
    point = min(result.curve, key=lambda row: abs(row.f - f))
    return point.E_kWh


def format_buffer_comparison(base: Sequence[Optimum], padded: Sequence[Optimum]) -> str:
    """Energy and f* with the air pad against the same cell without it."""
    by_name = {result.case.name: result for result in base}
    lines = [
        "",
        "Entrance greenhouse air pad — with vs without",
        "ASSUMPTION: buffer height {:.1f} m, outer glazing U {:.1f} W/(m²·K), "
        "buffer ACH {:.1f}, outer transmittance {:.2f}.".format(
            BUFFER_HEIGHT_M, BUFFER_U, BUFFER_ACH, BUFFER_TAU
        ),
        "A clear roof is covered by a greenhouse of that plan. An opaque roof only "
        "pads a {:.0f} m² vestibule and a {:.0f} m² door or hatch.".format(
            BUFFER_VESTIBULE_PLAN_M2, BUFFER_ENTRANCE_M2
        ),
        f"Room infiltration drawn from the pad: {BUFFER_ROOM_AIR_FROM_PAD:.0%}. "
        f"Buffer keeps {BUFFER_ABSORPTANCE:.0%} of the horizontal irradiance on its plan.",
        f"{'case':<18}{'f* bare':>10}{'f* pad':>10}{'E bare':>12}{'E pad':>12}{'E pad at bare f*':>18}",
    ]
    for result in padded:
        parent_name = result.case.name[: -len("+pad")] if result.case.name.endswith("+pad") else ""
        parent = by_name.get(parent_name)
        if parent is None or parent.f_star is None or result.f_star is None:
            lines.append(f"{result.case.name:<18}  infeasible")
            continue
        same_f = _energy_near(result, parent.f_star)
        same_txt = "—" if same_f is None else f"{same_f:12.0f}"
        lines.append(
            f"{parent_name:<18}{parent.f_star * 100:9.1f}%{result.f_star * 100:9.1f}%"
            f"{parent.E_star_kWh:12.0f}{result.E_star_kWh:12.0f}{same_txt:>18}"
        )
    return "\n".join(lines)


def run_examples(
    climate: SiteClimate = DFW_TYPICAL,
    f_step: float = 0.05,
    hours: float = 72.0,
    cases: Optional[Iterable[SubmersionCase]] = None,
) -> List[Optimum]:
    chosen = list(example_cases() if cases is None else cases)
    return [sweep_case(case, climate=climate, f_step=f_step, hours=hours) for case in chosen]


def write_outputs(
    results: Sequence[Optimum],
    stem: str = "submersion_optimal",
    community: Optional[Dict] = None,
    buffer_comparison: Optional[Sequence[Optimum]] = None,
) -> Tuple[str, str]:
    os.makedirs(OUT_DIR, exist_ok=True)
    json_path = os.path.join(OUT_DIR, stem + ".json")
    png_path = os.path.join(OUT_DIR, stem + ".png")
    payload = {
        "objective": "annual thermal kWh to hold the use-type temperature band",
        "f_definition": "fraction of building height below grade",
        "legacy_illustration_submersion": 0.70,
        "assumptions": {
            "K_DRY": K_DRY,
            "K_SAT": K_SAT,
            "SOIL_PATH_M": SOIL_PATH_M,
            "GROUND_THROTTLE_GAMMA": GROUND_THROTTLE_GAMMA,
            "TUBE_THROTTLE_GAMMA": TUBE_THROTTLE_GAMMA,
            "K_SOIL_REF": K_SOIL_REF,
            "TAU_ROOF_WATER": TAU_ROOF_WATER,
            "COP_HEAT": COP_HEAT,
            "COP_COOL": COP_COOL,
            "note": "ASSUMPTION defaults. See SUBMERSION_OPTIMAL.md.",
        },
        "cases": [optimum_to_json(result) for result in results],
        "community_energy": community,
        "buffer_comparison": None
        if buffer_comparison is None
        else [optimum_to_json(result) for result in buffer_comparison],
        "buffer_assumptions": {
            "height_m": BUFFER_HEIGHT_M,
            "vestibule_plan_m2": BUFFER_VESTIBULE_PLAN_M2,
            "entrance_m2": BUFFER_ENTRANCE_M2,
            "U_W_per_m2K": BUFFER_U,
            "ACH": BUFFER_ACH,
            "tau": BUFFER_TAU,
            "absorptance": BUFFER_ABSORPTANCE,
            "room_air_from_pad": BUFFER_ROOM_AIR_FROM_PAD,
            "note": "ASSUMPTION. See SUBMERSION_OPTIMAL.md.",
        },
    }
    with open(json_path, "w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    plotted = list(results)
    if buffer_comparison:
        plotted.extend(buffer_comparison)
    plot_optimal_curves(plotted, png_path)
    return json_path, png_path


def main_optimize(argv: Optional[Sequence[str]] = None) -> List[Optimum]:
    parser = argparse.ArgumentParser(description="Optimal building-height submersion fraction")
    parser.add_argument("--f-step", type=float, default=0.05, help="sweep step in fraction of height")
    parser.add_argument("--hours", type=float, default=72.0, help="integrator horizon per design day")
    parser.add_argument(
        "--climate-csv",
        default=None,
        help="replace DFW months; columns name,doy,days,T_min_C,T_max_C,ghi_kwh_m2,day_length_h",
    )
    parser.add_argument("--latitude", type=float, default=None, help="site latitude (degrees north)")
    parser.add_argument("--t-mean-soil", type=float, default=None, help="undisturbed annual-mean soil °C")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    climate = DFW_TYPICAL
    months = climate.months
    if args.climate_csv:
        months = read_month_csv(args.climate_csv)
    if args.climate_csv or args.latitude is not None or args.t_mean_soil is not None:
        climate = SiteClimate(
            name="custom" if args.climate_csv else climate.name,
            latitude_deg=climate.latitude_deg if args.latitude is None else args.latitude,
            T_mean_soil_C=climate.T_mean_soil_C if args.t_mean_soil is None else args.t_mean_soil,
            A_surf_K=climate.A_surf_K,
            t_peak_doy=climate.t_peak_doy,
            months=months,
        )

    results = run_examples(climate=climate, f_step=args.f_step, hours=args.hours)
    padded = run_examples(
        climate=climate,
        f_step=args.f_step,
        hours=args.hours,
        cases=buffer_comparison_cases(),
    )
    print(format_report(results))
    print(format_buffer_comparison(results, padded))
    names = {result.case.name: result for result in results}
    living = names.get("living")
    storage = names.get("storage")
    cold = names.get("cold_storage")
    if (
        living
        and storage
        and living.f_star is not None
        and storage.f_star is not None
        and abs(living.f_star - storage.f_star) < 1e-6
    ):
        print("WARNING: living and storage f* are the same under these defaults.")
    if (
        living
        and living.f_star is not None
        and cold
        and cold.f_star is not None
        and living.f_star >= 0.95
    ):
        print("WARNING: living f* is at full burial; sunlight policy should keep it below that.")
    import community_energy

    community = community_energy.community_report(results)
    print(community_energy.format_community_report(community))
    if not args.no_plot:
        json_path, png_path = write_outputs(
            results, community=community, buffer_comparison=padded
        )
        print(f"wrote {json_path}")
        print(f"wrote {png_path}")
    return results


if __name__ == "__main__":
    main_optimize()
