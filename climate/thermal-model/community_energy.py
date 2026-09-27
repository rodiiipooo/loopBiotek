"""Community hot-water and space loads, then a microgrid CapEx stub.

Headcounts come from the existing planning inputs:

- People ``H`` and body weight ``W`` are the defaults of
  ``economics/community_capital.py`` ``run_example`` (also the facility
  m²/person used to size living floor area).
- Worm and quail counts are ``research/ops-dashboard/store.py``
  ``DEFAULT_HERD``. Worms are the Stage 1 herd stub. Quail is the Stage 4
  planning stub in that same dict, not a purchase.

Dollar-per-kW figures and gallons per head are ASSUMPTION. This module does
not add the result to ``setup_capex`` and does not open Stage 2+ spend.
"""
from __future__ import annotations

import importlib.util
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence

# ASSUMPTION planning values. Not a plumbing code and not a quote.
GAL_PER_PERSON_DAY_MAINT = 10.0       # hygiene and cooking
GAL_PER_PERSON_DAY_DISC = 5.0         # longer showers, extra wash
DHW_TARGET_C = 49.0                   # mixed hot delivery
DHW_INLET_C = 18.0                    # cold supply, near the annual soil mean
# Quail: ops-dashboard herd is small. Heated wash/brooder water, not drinking.
GAL_PER_QUAIL_DAY = 0.02
QUAIL_WATER_TARGET_C = 40.0
# Worms are a soil-temperature culture (biology README: about 18–23 °C).
# No heated-water allotment. Their count is still an input so the chain is wired.
GAL_PER_WORM_DAY = 0.0
WORM_WATER_TARGET_C = 20.0

# Draw shapes. Maintenance in a 4 h morning window, discretionary in 2 h evening.
MAINT_DRAW_H = 4.0
DISC_DRAW_H = 2.0

# Space peak / average. Cold storage runs flatter than a clear-roof home.
SPACE_PEAK_FACTOR = {
    "living": 4.0,
    "storage": 2.5,
    "cold_storage": 1.5,
    "greenhouse": 3.0,
}
# Extra living energy people choose beyond the thermostat band.
LIVING_DISCRETIONARY_FRAC = 0.15

# Shared microgrid. ASSUMPTION unit costs, DFW capacity factor, critical autonomy.
PV_USD_PER_KW = 2500.0
BATTERY_USD_PER_KWH = 400.0
PV_CAPACITY_FACTOR = 0.18
AUTONOMY_H = 12.0
# Water-draw peak and space peak do not land on the same hour in full.
SPACE_WATER_COINCIDENCE = 0.80

GALLON_M3 = 1.0 / 264.172
RHO_WATER = 997.0
CP_WATER = 4182.0
J_PER_KWH = 3.6e6

CELL_FLOOR_M2 = 100.0  # default L=W=10 m illustration cell


@dataclass(frozen=True)
class Population:
    H: float
    W_kg: float
    worms: float
    quail: float
    m2_per_person: float
    sources: Dict[str, str]


@dataclass(frozen=True)
class WaterStream:
    name: str
    role: str  # maintenance | discretionary
    gallons_per_day: float
    target_C: float
    inlet_C: float
    kwh_per_day: float
    peak_kw: float


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load(name: str, path: str):
    import sys

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    # dataclasses look up the class module in sys.modules during decoration.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def default_population() -> Population:
    """H, W, facility m², and herd counts already stored elsewhere in this repo."""
    root = repo_root()
    capital = _load("community_capital", os.path.join(root, "economics", "community_capital.py"))
    store = _load("ops_store", os.path.join(root, "research", "ops-dashboard", "store.py"))
    defaults = capital.run_example.__defaults__ or (20.0, 70.0)
    H = float(defaults[0])
    W = float(defaults[1])
    herd = store.DEFAULT_HERD
    worms = float(herd["worms"]["n0"])
    quail = float(herd["quail"]["n0"])
    m2 = float(capital.facility_m2_per_person(W))
    return Population(
        H=H,
        W_kg=W,
        worms=worms,
        quail=quail,
        m2_per_person=m2,
        sources={
            "H_W": "economics/community_capital.py run_example defaults",
            "m2_per_person": "economics/community_capital.py FacilityParams via facility_m2_per_person",
            "worms": "research/ops-dashboard/store.py DEFAULT_HERD worms n0 (Stage 1 stub)",
            "quail": "research/ops-dashboard/store.py DEFAULT_HERD quail n0 (Stage 4 planning stub, not spend)",
        },
    )


def kwh_per_gallon_per_k() -> float:
    mass = GALLON_M3 * RHO_WATER
    return mass * CP_WATER / J_PER_KWH


def _stream(name: str, role: str, gallons: float, target_C: float, inlet_C: float, draw_h: float) -> WaterStream:
    delta = max(0.0, target_C - inlet_C)
    kwh_day = gallons * kwh_per_gallon_per_k() * delta
    peak = kwh_day / draw_h if draw_h > 0.0 else 0.0
    return WaterStream(name, role, gallons, target_C, inlet_C, kwh_day, peak)


def water_streams(pop: Population) -> List[WaterStream]:
    """Consumed hot water. Hydronic loop volume is inventory, not this list."""
    people_maint = pop.H * GAL_PER_PERSON_DAY_MAINT
    people_disc = pop.H * GAL_PER_PERSON_DAY_DISC
    quail = pop.quail * GAL_PER_QUAIL_DAY
    worms = pop.worms * GAL_PER_WORM_DAY
    return [
        _stream("people_dhw_maintenance", "maintenance", people_maint, DHW_TARGET_C, DHW_INLET_C, MAINT_DRAW_H),
        _stream("people_dhw_discretionary", "discretionary", people_disc, DHW_TARGET_C, DHW_INLET_C, DISC_DRAW_H),
        _stream("quail_process", "maintenance", quail, QUAIL_WATER_TARGET_C, DHW_INLET_C, MAINT_DRAW_H),
        _stream("worm_heated_water", "maintenance", worms, WORM_WATER_TARGET_C, DHW_INLET_C, MAINT_DRAW_H),
    ]


def hydronic_inventory_gal(living_floor_m2: float, uses_water_panes: bool) -> float:
    """Roof-loop fluid stock scaled from the 100 m² cell pipe geometry.

    This is gallons in the pipes, not gallons heated per day. Space heat and
    cool are the thermostat totals, not a daily reheat of this volume.
    """
    if not uses_water_panes or living_floor_m2 <= 0.0:
        return 0.0
    import climate_envelope_sim as env

    cell = env.PipeGeometry()
    return cell.total_fluid_gallons * (living_floor_m2 / CELL_FLOOR_M2)


@dataclass
class SpaceLoad:
    name: str
    use_type: str
    f_star: Optional[float]
    floor_m2: float
    role_note: str
    maintenance_kwh: float
    discretionary_kwh: float
    peak_kw: float


def space_loads(optima: Sequence, pop: Population) -> List[SpaceLoad]:
    """Scale each swept cell to a community floor area.

    Living uses ``H * m2_per_person`` from community capital. Dry storage and
    cold storage are one shared 100 m² cell each (ASSUMPTION). A greenhouse,
    if present, is also one cell and is not part of the shared microgrid.
    """
    by_name = {item.case.name: item for item in optima}
    living_m2 = pop.H * pop.m2_per_person
    plan = [
        ("living", living_m2, "homes; sunlight-capped submersion"),
        ("storage", CELL_FLOOR_M2, "one shared dry store; prefer full burial"),
        ("cold_storage", CELL_FLOOR_M2, "one shared refrigerated store; prefer full burial"),
        ("greenhouse", CELL_FLOOR_M2, "one planning greenhouse; not in the shared microgrid"),
    ]
    loads: List[SpaceLoad] = []
    for name, area, note in plan:
        result = by_name.get(name)
        if result is None or result.E_star_kWh is None:
            continue
        cell_area = result.case.L_m * result.case.W_m
        scale = area / cell_area if cell_area > 0.0 else 0.0
        maint = result.E_star_kWh * scale
        disc = maint * LIVING_DISCRETIONARY_FRAC if name == "living" else 0.0
        factor = SPACE_PEAK_FACTOR.get(result.case.use_type, 2.0)
        peak = (maint + disc) / 8760.0 * factor
        loads.append(
            SpaceLoad(
                name=name,
                use_type=result.case.use_type,
                f_star=result.f_star,
                floor_m2=area,
                role_note=note,
                maintenance_kwh=maint,
                discretionary_kwh=disc,
                peak_kw=peak,
            )
        )
    return loads


@dataclass
class Microgrid:
    """Infrastructure for shared facilities and the central hot-water plant."""

    annual_maintenance_kwh: float
    annual_discretionary_kwh: float
    maintenance_peak_kw: float
    pv_kw: float
    battery_kwh: float
    capex_usd: float
    serves: List[str]


def size_microgrid(streams: Sequence[WaterStream], spaces: Sequence[SpaceLoad]) -> Microgrid:
    shared_names = ("storage", "cold_storage")
    shared = [row for row in spaces if row.name in shared_names]
    water_maint = [row for row in streams if row.role == "maintenance"]
    water_disc = [row for row in streams if row.role == "discretionary"]
    annual_maint = sum(row.maintenance_kwh for row in shared) + sum(row.kwh_per_day * 365.0 for row in water_maint)
    annual_disc = sum(row.discretionary_kwh for row in shared) + sum(row.kwh_per_day * 365.0 for row in water_disc)
    space_peak = sum(row.peak_kw for row in shared)
    water_peak = max((row.peak_kw for row in water_maint), default=0.0)
    # Discretionary water is an evening draw; it does not add to the maintenance peak.
    maint_peak = space_peak + SPACE_WATER_COINCIDENCE * water_peak
    annual = annual_maint + annual_disc
    pv_from_energy = annual / (8760.0 * PV_CAPACITY_FACTOR) if PV_CAPACITY_FACTOR > 0.0 else 0.0
    pv_kw = max(pv_from_energy, maint_peak)
    battery_kwh = maint_peak * AUTONOMY_H
    capex = pv_kw * PV_USD_PER_KW + battery_kwh * BATTERY_USD_PER_KWH
    return Microgrid(
        annual_maintenance_kwh=annual_maint,
        annual_discretionary_kwh=annual_disc,
        maintenance_peak_kw=maint_peak,
        pv_kw=pv_kw,
        battery_kwh=battery_kwh,
        capex_usd=capex,
        serves=["shared dry storage", "shared cold storage", "central hot-water plant"],
    )


def community_report(optima: Sequence, pop: Optional[Population] = None) -> Dict:
    people = pop if pop is not None else default_population()
    streams = water_streams(people)
    spaces = space_loads(optima, people)
    grid = size_microgrid(streams, spaces)
    living = next((row for row in spaces if row.name == "living"), None)
    uses_panes = False
    for item in optima:
        if item.case.name == "living":
            uses_panes = bool(item.case.water_panes and item.case.clear_ceiling)
    loop_gal = hydronic_inventory_gal(people.H * people.m2_per_person, uses_panes)
    return {
        "assumption_note": (
            "ASSUMPTION unit costs and per-head gallons. Planning stub only. "
            "Not added to community_capital setup_capex (other_capex stays 0). "
            "Stage 1 worms remain the only active spend."
        ),
        "population": asdict(people),
        "water": [asdict(row) for row in streams],
        "water_gallons_per_day": {
            "maintenance": sum(row.gallons_per_day for row in streams if row.role == "maintenance"),
            "discretionary": sum(row.gallons_per_day for row in streams if row.role == "discretionary"),
        },
        "water_kwh_per_year": {
            "maintenance": sum(row.kwh_per_day * 365.0 for row in streams if row.role == "maintenance"),
            "discretionary": sum(row.kwh_per_day * 365.0 for row in streams if row.role == "discretionary"),
        },
        "hydronic_loop_gallons_inventory": loop_gal,
        "space": [asdict(row) for row in spaces],
        "microgrid": asdict(grid),
        "living_floor_m2": None if living is None else living.floor_m2,
    }


def format_community_report(report: Dict) -> str:
    pop = report["population"]
    water = {row["name"]: row for row in report["water"]}
    gallons = report["water_gallons_per_day"]
    water_kwh = report["water_kwh_per_year"]
    grid = report["microgrid"]
    lines = [
        "",
        "Community energy → shared microgrid (ASSUMPTION gallons and unit costs)",
        "Not added to community_capital setup_capex. Stage 1 worms remain the only active spend.",
        f"People H={pop['H']:.0f}, W={pop['W_kg']:.0f} kg  ({pop['sources']['H_W']})",
        f"Facility area {pop['m2_per_person']:.1f} m²/person → living floor {report['living_floor_m2']:.0f} m²",
        f"Worms {pop['worms']:.0f} ({pop['sources']['worms']})",
        f"Quail {pop['quail']:.0f} ({pop['sources']['quail']})",
        "",
        "Heated water (consumed)",
        f"  maintenance   {gallons['maintenance']:.1f} gal/day   {water_kwh['maintenance']:.0f} kWh/year",
        f"    people DHW  {water['people_dhw_maintenance']['gallons_per_day']:.1f} gal/day "
        f"to {water['people_dhw_maintenance']['target_C']:.0f} °C  "
        f"peak {water['people_dhw_maintenance']['peak_kw']:.2f} kW",
        f"    quail       {water['quail_process']['gallons_per_day']:.2f} gal/day "
        f"to {water['quail_process']['target_C']:.0f} °C",
        f"    worms       {water['worm_heated_water']['gallons_per_day']:.1f} gal/day "
        "(no heated-water allotment)",
        f"  discretionary {gallons['discretionary']:.1f} gal/day   {water_kwh['discretionary']:.0f} kWh/year  "
        f"peak {water['people_dhw_discretionary']['peak_kw']:.2f} kW",
        f"  hydronic loop inventory {report['hydronic_loop_gallons_inventory']:.1f} gal "
        "(pipe stock, not a daily reheat)",
        "",
        "Space conditioning at each f*  (maintenance = thermostat; living discretionary is an adder)",
    ]
    for row in report["space"]:
        f_txt = "—" if row["f_star"] is None else f"{100.0 * row['f_star']:.1f}%"
        lines.append(
            f"  {row['name']:<14} f*={f_txt:>6}  floor {row['floor_m2']:.0f} m²  "
            f"maint {row['maintenance_kwh']:.0f} kWh/yr  "
            f"disc {row['discretionary_kwh']:.0f}  peak {row['peak_kw']:.2f} kW"
        )
    lines.extend(
        [
            "",
            "Shared microgrid (dry storage + cold storage + central hot water)",
            f"  maintenance {grid['annual_maintenance_kwh']:.0f} kWh/year   "
            f"discretionary {grid['annual_discretionary_kwh']:.0f} kWh/year",
            f"  maintenance peak {grid['maintenance_peak_kw']:.2f} kW",
            f"  PV {grid['pv_kw']:.1f} kW  ×  ${PV_USD_PER_KW:.0f}/kW   "
            f"battery {grid['battery_kwh']:.0f} kWh  ×  ${BATTERY_USD_PER_KWH:.0f}/kWh",
            f"  CapEx ${grid['capex_usd']:.0f}   (ASSUMPTION; capacity factor {PV_CAPACITY_FACTOR:.2f}, "
            f"autonomy {AUTONOMY_H:.0f} h on the maintenance peak)",
        ]
    )
    return "\n".join(lines)
