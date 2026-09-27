"""Stochastic sell limits for the community ops dashboard. Planning only.

Uses the Python standard library (no numpy). Worm and quail paths are a seeded
logistic stand-in so a laptop can run the screen on its own. They are not the
Stage-1 spend model, and they do not authorize later-stage purchases.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

_SYNERGY = Path(__file__).resolve().parents[1] / "synergy"
if str(_SYNERGY) not in sys.path:
    sys.path.insert(0, str(_SYNERGY))

try:
    from circular_buffers import FAIRNESS, R_INF, R_PRIME, breed_floor, fair_prepaid  # noqa: E402
except ImportError as err:
    raise ImportError(
        "This folder expects research/synergy next to it. Clone the whole repository, "
        "then run from research/ops-dashboard."
    ) from err

WEEKS_PER_MONTH = 52.0 / 12.0
DEFAULT_PATHS = 2000
DEFAULT_SEED = 20260926
MAX_MONTH = 36
# P10: 10th percentile of pounds you can still finish. Harsh futures.
# The 90th percentile is the good-growth case and is not a sell-room default.
DEFAULT_QUANTILE = 0.10


def planning_quantile(value: float | None = None) -> float:
    """Lower-tail percentile used for sell room and delivery planning.

    0.10 is P10. About 10% of futures are this low or lower. Values above 0.50
    would plan on a better-than-median future, so they are refused.
    """
    quantile = DEFAULT_QUANTILE if value is None else float(value)
    if not 0.0 < quantile <= 0.5:
        raise ValueError(
            "Sell room uses the harsh tail. P10 is 0.10. "
            "A percentile above 0.50 counts on a good future and is not used."
        )
    return quantile


def clear_fraction(quantile: float) -> float:
    """Share of scenarios that can still deliver the P-quantile amount.

    P10 (0.10) means 90% of futures finish at least that many pounds.
    """
    return 1.0 - planning_quantile(quantile)

# Ozark Worm Farms bulk listing: 10 lb at $420. Shelf price, not a farm-gate contract.
WORM_SPOT_USD_PER_LB = 42.0
WORM_SPOT_NOTE = (
    "SOURCED shelf price: Ozark Worm Farms bulk red wigglers, 10 lb at $420 "
    "($42/lb). https://ozarkwormfarms.com/products/bulk-red-wiggler-worms "
    "Not a contracted farm-gate price. Override it for a real buyer."
)
# Vendors quote about 800–1000 adults per pound. Planning count uses 1000.
WORM_HEADCOUNT_PER_LB = 1000.0

QUAIL_SPOT_USD_PER_LB = (13.17 + 10.06 + 14.16) / 3.0
# Retired for quail orders. Delivery and quail_income sum sex- and age-specific
# dressed weights in research/quail/bird_mc.py. This scalar remains only so the
# fish screen can keep the old logistic stub.
QUAIL_LB_PER_BIRD = (13.0 / 16.0) * 0.72  # ~0.585 lb, flat, not used for quail meat plans


class SpeciesModel:
    def __init__(
        self,
        key: str,
        label: str,
        unit: str,
        headcount_per_unit: float,
        spot_usd_per_unit: float,
        spot_note: str,
        doubling_weeks: float,
        weekly_sigma: float,
        carrying_multiple: float,
        tag: str,
        note: str,
    ) -> None:
        self.key = key
        self.label = label
        self.unit = unit
        self.headcount_per_unit = headcount_per_unit
        self.spot_usd_per_unit = spot_usd_per_unit
        self.spot_note = spot_note
        self.doubling_weeks = doubling_weeks
        self.weekly_sigma = weekly_sigma
        self.carrying_multiple = carrying_multiple
        self.tag = tag
        self.note = note

    def to_public(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "unit": self.unit,
            "headcount_per_unit": self.headcount_per_unit,
            "spot_usd_per_unit": self.spot_usd_per_unit,
            "spot_note": self.spot_note,
            "doubling_weeks": self.doubling_weeks,
            "weekly_sigma": self.weekly_sigma,
            "carrying_multiple": self.carrying_multiple,
            "tag": self.tag,
            "note": self.note,
        }


SPECIES: dict[str, SpeciesModel] = {
    "worms": SpeciesModel(
        key="worms",
        label="Worms (live)",
        unit="lb",
        headcount_per_unit=WORM_HEADCOUNT_PER_LB,
        spot_usd_per_unit=WORM_SPOT_USD_PER_LB,
        spot_note=WORM_SPOT_NOTE,
        doubling_weeks=13.0,
        weekly_sigma=0.015,
        carrying_multiple=16.0,
        tag="ASSUMPTION",
        note=(
            "Planning stand-in, not worm_growth_mc. Median doubling about 13 weeks "
            "(~90 days) before the bin cap, with small weekly noise. "
            "Bin cap is 16 times the breed floor. 1,000 worms per pound is a planning count."
        ),
    ),
    "quail": SpeciesModel(
        key="quail",
        label="Quail (dressed meat)",
        unit="lb",
        headcount_per_unit=1.0 / QUAIL_LB_PER_BIRD,
        spot_usd_per_unit=QUAIL_SPOT_USD_PER_LB,
        spot_note=(
            "SOURCED foodservice mean from research/quail "
            "(13.17, 10.06, 14.16 USD/lb). Quail orders use research/quail/bird_mc.py. "
            "This logistic stub remains for the fish screen only."
        ),
        doubling_weeks=26.0,
        weekly_sigma=0.01,
        carrying_multiple=8.0,
        tag="ASSUMPTION",
        note=(
            "Thin stub kept for the fish screen. Quail meat plans use bird_mc.py, "
            "not this 0.585 lb/bird scalar. Do not treat this as permission to buy quail kits."
        ),
    ),
}


def weeks_for_month(month: int) -> int:
    if month < 1:
        raise ValueError("month must be >= 1")
    return max(1, int(round(month * WEEKS_PER_MONTH)))


def month_end_weeks(months: int) -> list[int]:
    """0-based week indexes for the end of months 1..months. Unique, ordered."""
    seen: list[int] = []
    for month in range(1, months + 1):
        idx = weeks_for_month(month) - 1
        if not seen or seen[-1] != idx:
            seen.append(idx)
    return seen


def resolve_floor(n0: float, n_start: float | None, n_safety: float | None) -> float:
    start = float(n0 if n_start is None else n_start)
    safety = float(n0 if n_safety is None else n_safety)
    return breed_floor(float(n0), start, safety)


def price_quote(species: str, delivery_month: int, transport: float = 0.0) -> dict:
    model = SPECIES[species]
    quoted = fair_prepaid(
        model.spot_usd_per_unit,
        delivery_month / 12.0,
        r_inf=R_INF,
        r_prime=R_PRIME,
        fairness=FAIRNESS,
        transport=transport,
    )
    quoted["unit"] = model.unit
    quoted["species"] = species
    quoted["delivery_month"] = delivery_month
    quoted["spot_note"] = model.spot_note
    return quoted


_SHOCKS: dict[tuple, list[list[float]]] = {}


def _shocks(model: SpeciesModel, weeks: int, n_paths: int, seed: int) -> list[list[float]]:
    """Weekly growth factors. Cached so a binary search replays the same futures."""
    key = (model.key, model.doubling_weeks, model.weekly_sigma, weeks, n_paths, seed)
    cached = _SHOCKS.get(key)
    if cached is not None:
        return cached
    mu = math.log(2.0 ** (1.0 / model.doubling_weeks))
    rng = random.Random(seed)
    table = [
        [math.exp(rng.gauss(mu, model.weekly_sigma)) for _ in range(weeks)]
        for _ in range(n_paths)
    ]
    _SHOCKS[key] = table
    return table


def _capacity(model: SpeciesModel, n0: float, floor: float) -> float:
    return model.carrying_multiple * max(float(n0), float(floor), 1.0)


def _replay(
    n0: float,
    floor: float,
    shocks: list[list[float]],
    harvest_at_week: dict[int, float],
    capacity: float,
    reliability: float | None = None,
) -> float:
    """Share of scenarios that stay at or above the breed floor.

    If reliability is set, stop once too many scenarios have already failed.
    """
    n_paths = len(shocks)
    fails = 0
    fail_limit = None
    if reliability is not None:
        fail_limit = n_paths - math.ceil(reliability * n_paths - 1e-12)
    for row in shocks:
        n = float(n0)
        good = True
        for week, factor in enumerate(row):
            room = 1.0 - n / capacity
            if room < 0.0:
                room = 0.0
            n = n + n * (factor - 1.0) * room
            take = harvest_at_week.get(week, 0.0)
            if take:
                n -= take
            if n < 0.0:
                n = 0.0
            if n + 1e-6 < floor:
                good = False
                break
        if not good:
            fails += 1
            if fail_limit is not None and fails > fail_limit:
                return (n_paths - fails) / n_paths
    return (n_paths - fails) / n_paths


def _survival(
    n0: float,
    floor: float,
    weeks: int,
    harvest_at_week: dict[int, float],
    model: SpeciesModel,
    n_paths: int,
    seed: int,
) -> float:
    """Share of scenarios whose headcount stays at or above the breed floor."""
    if weeks < 1:
        raise ValueError("weeks must be >= 1")
    shocks = _shocks(model, weeks, n_paths, seed)
    return _replay(n0, floor, shocks, harvest_at_week, _capacity(model, n0, floor))


def _last_week_headrooms(
    n0: float,
    floor: float,
    shocks: list[list[float]],
    base_harvest: dict[int, float],
    capacity: float,
) -> list[float]:
    """Spare headcount at the final week, after any harvest already on the book.

    A scenario that already broke the floor contributes no spare (negative).
    """
    rooms: list[float] = []
    for row in shocks:
        n = float(n0)
        broken = False
        for week, factor in enumerate(row):
            room = 1.0 - n / capacity
            if room < 0.0:
                room = 0.0
            n = n + n * (factor - 1.0) * room
            take = base_harvest.get(week, 0.0)
            if take:
                n -= take
            if n < 0.0:
                n = 0.0
            if n + 1e-6 < floor:
                broken = True
                break
        rooms.append(-1.0 if broken else n - floor)
    return rooms


def _headroom_cap(rooms: list[float], reliability: float) -> float:
    """Largest H such that at least `reliability` of scenarios have room >= H.

    `reliability` here is the share of futures that must clear, not the P10
    number. P10 passes 0.90 into this function.
    """
    n_paths = len(rooms)
    if n_paths == 0:
        return 0.0
    need = math.ceil(reliability * n_paths - 1e-12)
    if need > n_paths:
        return 0.0
    ordered = sorted(rooms)
    return max(0.0, ordered[n_paths - need])


def _max_headcount(
    n0: float,
    floor: float,
    weeks: int,
    base_harvest: dict[int, float],
    add_weeks: list[int],
    model: SpeciesModel,
    reliability: float,
    n_paths: int,
    seed: int,
) -> float:
    """Largest equal headcount added on each week in add_weeks that stays safe."""
    if not add_weeks:
        return 0.0
    shocks = _shocks(model, weeks, n_paths, seed)
    capacity = _capacity(model, n0, floor)
    if add_weeks == [weeks - 1]:
        rooms = _last_week_headrooms(n0, floor, shocks, base_harvest, capacity)
        return _headroom_cap(rooms, reliability)

    def ok(extra: float) -> bool:
        harvest = dict(base_harvest)
        for week in add_weeks:
            harvest[week] = harvest.get(week, 0.0) + extra
        return _replay(n0, floor, shocks, harvest, capacity, reliability) >= reliability - 1e-12

    if not ok(0.0):
        return 0.0
    hi = capacity
    if ok(hi):
        return hi
    lo = 0.0
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        if ok(mid):
            lo = mid
        else:
            hi = mid
    return lo


def bookings_to_harvest(species: str, bookings: list[dict]) -> dict[int, float]:
    """Map promised/draft rows to headcount removed at month-end weeks."""
    model = SPECIES[species]
    harvest: dict[int, float] = {}
    for row in bookings:
        if row.get("species") != species:
            continue
        if row.get("status") not in ("draft", "promised"):
            continue
        month = int(row["delivery_month"])
        week = weeks_for_month(month) - 1
        headcount = float(row["qty"]) * model.headcount_per_unit
        harvest[week] = harvest.get(week, 0.0) + headcount
    return harvest


def promised_units(species: str, bookings: list[dict]) -> float:
    total = 0.0
    for row in bookings:
        if row.get("species") != species:
            continue
        if row.get("status") not in ("draft", "promised"):
            continue
        total += float(row["qty"])
    return total


def _units(headcount: float, model: SpeciesModel) -> float:
    return headcount / model.headcount_per_unit


def sell_limit(
    species: str,
    n0: float,
    bookings: list[dict],
    n_start: float | None = None,
    n_safety: float | None = None,
    reliability: float = DEFAULT_QUANTILE,
    horizon_months: int = 12,
    n_paths: int = DEFAULT_PATHS,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Remaining room for one more delivery at horizon_months, after bookings.

    `reliability` is the lower-tail percentile. Default 0.10 is P10.
    """
    if species not in SPECIES:
        raise KeyError(species)
    quantile = planning_quantile(reliability)
    clear = clear_fraction(quantile)
    if horizon_months < 1 or horizon_months > MAX_MONTH:
        raise ValueError(f"horizon_months must be 1..{MAX_MONTH}")
    model = SPECIES[species]
    floor = resolve_floor(n0, n_start, n_safety)
    weeks = weeks_for_month(horizon_months)
    base = bookings_to_harvest(species, bookings)
    # Drop deliveries past the horizon from the path (they are not in this window)
    # but still count them in "already promised" so the overseer sees the whole book.
    base = {week: qty for week, qty in base.items() if week < weeks}
    already = promised_units(species, bookings)
    clear_rate = _survival(n0, floor, weeks, base, model, n_paths, seed)
    at_week = weeks - 1
    extra_head = _max_headcount(
        n0, floor, weeks, base, [at_week], model, clear, n_paths, seed
    )
    extra_units = _units(extra_head, model)
    quote = price_quote(species, horizon_months)
    booked_ok = clear_rate + 1e-12 >= clear
    tail = f"P{quantile * 100:.0f}"
    if not booked_ok:
        message = (
            "Stop. What is already promised does not leave the breeding herd intact "
            f"in the {tail} harsh futures. Do not add another sale."
        )
    elif extra_units <= 1e-6:
        message = (
            "Nothing more is safe to sell in this window. "
            "The breeding herd has to stay put."
        )
    else:
        message = (
            f"You can still promise about {extra_units:.1f} {model.unit} "
            f"for month {horizon_months}. That is the {tail} amount: "
            f"what you can still deliver when outcomes are bad. "
            f"Only {quantile:.0%} of futures are this low or lower."
        )
    return {
        "species": species,
        "label": model.label,
        "unit": model.unit,
        "n0": float(n0),
        "breed_floor_headcount": floor,
        "reliability": quantile,
        "horizon_months": horizon_months,
        "safe_to_sell_units": round(extra_units, 4),
        "safe_to_sell_headcount": round(extra_head, 1),
        "already_promised_units": round(already, 4),
        "remaining_room_units": round(extra_units, 4),
        "book_still_safe": booked_ok,
        "fail_closed": (not booked_ok) or extra_units <= 1e-6,
        "message": message,
        "price": quote,
        "model_tag": model.tag,
        "model_note": model.note,
        "paths": n_paths,
        "seed": seed,
    }


def _monthly_income(units_per_month: float, species: str, months: int) -> float:
    total = 0.0
    for month in range(1, months + 1):
        total += units_per_month * price_quote(species, month)["F_prelim"]
    return total


def _scale_floor_inputs(
    n0: float, n_start: float | None, n_safety: float | None, new_n0: float
) -> tuple[float, float | None, float | None]:
    if n0 <= 0:
        raise ValueError("n0 must be > 0 to scale")
    factor = new_n0 / float(n0)
    start = None if n_start is None else float(n_start) * factor
    safety = None if n_safety is None else float(n_safety) * factor
    return float(new_n0), start, safety


def _even_monthly_cap(
    species: str,
    n0: float,
    n_start: float | None,
    n_safety: float | None,
    months: int,
    reliability: float,
    n_paths: int,
    seed: int,
) -> dict:
    model = SPECIES[species]
    floor = resolve_floor(n0, n_start, n_safety)
    weeks = weeks_for_month(months)
    ends = [week for week in month_end_weeks(months) if week < weeks]
    head = _max_headcount(
        n0, floor, weeks, {}, ends, model, reliability, n_paths, seed
    )
    units = _units(head, model)
    cumulative_units = units * len(ends)
    income = _monthly_income(units, species, len(ends))
    return {
        "breed_floor_headcount": floor,
        "month_ends": len(ends),
        "max_monthly_headcount": head,
        "max_monthly_units": units,
        "max_cumulative_units": cumulative_units,
        "income_at_cap_usd": income,
    }


def reverse_income(
    species: str,
    n0: float,
    target_income_usd: float,
    months: int,
    reliability: float = DEFAULT_QUANTILE,
    n_start: float | None = None,
    n_safety: float | None = None,
    n_paths: int = DEFAULT_PATHS,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Largest safe monthly sell, and whether target cash is inside that cap.

    `reliability` is the lower-tail percentile. Default 0.10 is P10.
    """
    if species not in SPECIES:
        raise KeyError(species)
    if target_income_usd < 0:
        raise ValueError("target income must be >= 0")
    if months < 1 or months > MAX_MONTH:
        raise ValueError(f"months must be 1..{MAX_MONTH}")
    quantile = planning_quantile(reliability)
    clear = clear_fraction(quantile)
    tail = f"P{quantile * 100:.0f}"
    model = SPECIES[species]
    cap = _even_monthly_cap(
        species, n0, n_start, n_safety, months, clear, n_paths, seed
    )
    quote = price_quote(species, months)
    per_month_value = _monthly_income(1.0, species, cap["month_ends"])
    if target_income_usd <= 0 or per_month_value <= 0:
        needed = 0.0
    else:
        needed = target_income_usd / per_month_value
    feasible = cap["income_at_cap_usd"] + 1e-6 >= target_income_usd
    lump_qty_for_target = (
        0.0 if quote["F_prelim"] <= 0 else target_income_usd / quote["F_prelim"]
    )
    # Lump at the horizon: one delivery, no monthly drip.
    weeks = weeks_for_month(months)
    floor = cap["breed_floor_headcount"]
    lump_head = _max_headcount(
        n0, floor, weeks, {}, [weeks - 1], model, clear, n_paths, seed
    )
    lump_units = _units(lump_head, model)
    lump_income = lump_units * quote["F_prelim"]

    min_n0 = None
    later_month = None
    if not feasible and n0 > 0:
        min_n0 = _min_n0_for_target(
            species, n0, n_start, n_safety, target_income_usd, months, clear, n_paths, seed
        )
        later_month = _later_month_for_target(
            species, n0, n_start, n_safety, target_income_usd, months, clear, n_paths, seed
        )

    lump_covers = lump_income + 1e-6 >= target_income_usd
    if feasible:
        message = (
            f"Yes. Selling about {needed:.2f} {model.unit} each month through month {months} "
            f"would bring in ${target_income_usd:,.0f} on the {tail} harsh case. "
            f"The safe monthly cap is {cap['max_monthly_units']:.2f} {model.unit}."
        )
    else:
        bits = [
            f"Not as a steady monthly sale. The safe monthly cap is {cap['max_monthly_units']:.2f} {model.unit}, "
            f"about ${cap['income_at_cap_usd']:,.0f} by month {months}. "
            "A bigger monthly cull would cut into the breeding herd, so it stays blocked."
        ]
        if lump_covers:
            bits.append(
                f"One delivery in month {months} can be as large as {lump_units:.1f} {model.unit} "
                f"(about ${lump_income:,.0f}). "
                f"About {lump_qty_for_target:.1f} {model.unit} that month covers ${target_income_usd:,.0f} "
                "if you are not also selling every month."
            )
        if min_n0 is not None:
            bits.append(
                f"To hit the target from steady monthly sales, start with about {min_n0:,.0f}."
            )
        else:
            bits.append("A larger starting herd inside the search range still does not cover steady monthly sales.")
        if later_month is not None:
            bits.append(f"The same starting herd can cover steady monthly sales by month {later_month}.")
        else:
            bits.append(
                f"Waiting through month {MAX_MONTH} still does not cover steady monthly sales on the {tail} harsh case."
            )
        message = " ".join(bits)

    return {
        "species": species,
        "label": model.label,
        "unit": model.unit,
        "n0": float(n0),
        "target_income_usd": float(target_income_usd),
        "months": months,
        "reliability": quantile,
        "breed_floor_headcount": floor,
        "f_prelim_usd_per_unit": quote["F_prelim"],
        "f_prelim_at_month": months,
        "price": quote,
        "max_monthly_sell_units": round(cap["max_monthly_units"], 4),
        "max_cumulative_sell_units": round(cap["max_cumulative_units"], 4),
        "monthly_offtake_cap_headcount": round(cap["max_monthly_headcount"], 1),
        "income_at_cap_usd": round(cap["income_at_cap_usd"], 2),
        "qty_for_target_monthly_units": round(needed, 4),
        "feasible": feasible,
        "lump_covers_target": lump_covers,
        "lump_qty_for_target_units": round(lump_qty_for_target, 4),
        "lump_at_horizon_units": round(lump_units, 4),
        "lump_income_usd": round(lump_income, 2),
        "min_n0": None if min_n0 is None else round(min_n0, 1),
        "later_month": later_month,
        "model_tag": model.tag,
        "model_note": model.note,
        "message": message,
        "paths": n_paths,
        "seed": seed,
        "stage_gate": "Stage 1 worms only. This result does not authorize Stage 2–5 spend.",
    }


def _target_feasible_at(
    species: str,
    n0: float,
    n_start: float | None,
    n_safety: float | None,
    target_income_usd: float,
    months: int,
    reliability: float,
    n_paths: int,
    seed: int,
) -> bool:
    cap = _even_monthly_cap(
        species, n0, n_start, n_safety, months, reliability, n_paths, seed
    )
    return cap["income_at_cap_usd"] + 1e-6 >= target_income_usd


def _min_n0_for_target(
    species, n0, n_start, n_safety, target, months, reliability, n_paths, seed
) -> float | None:
    hi_n0 = float(n0)
    found = False
    for _ in range(8):
        hi_n0 *= 2.0
        scaled = _scale_floor_inputs(n0, n_start, n_safety, hi_n0)
        if _target_feasible_at(species, *scaled, target, months, reliability, n_paths, seed):
            found = True
            break
    if not found:
        return None
    lo = float(n0)
    hi = hi_n0
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        scaled = _scale_floor_inputs(n0, n_start, n_safety, mid)
        if _target_feasible_at(species, *scaled, target, months, reliability, n_paths, seed):
            hi = mid
        else:
            lo = mid
    return hi


def _later_month_for_target(
    species, n0, n_start, n_safety, target, months, reliability, n_paths, seed
) -> int | None:
    for later in range(months + 1, MAX_MONTH + 1):
        if _target_feasible_at(
            species, n0, n_start, n_safety, target, later, reliability, n_paths, seed
        ):
            return later
    return None


def booking_is_safe(
    species: str,
    n0: float,
    bookings_including_new: list[dict],
    n_start: float | None = None,
    n_safety: float | None = None,
    reliability: float = DEFAULT_QUANTILE,
    n_paths: int = DEFAULT_PATHS,
    seed: int = DEFAULT_SEED,
) -> bool:
    """True when every draft/promised delivery through its own month keeps the floor.

    `reliability` is the lower-tail percentile. Default 0.10 is P10, so the
    book must still clear in 90% of futures.
    """
    model = SPECIES[species]
    relevant = [
        row
        for row in bookings_including_new
        if row.get("species") == species and row.get("status") in ("draft", "promised")
    ]
    if not relevant:
        return True
    horizon = max(int(row["delivery_month"]) for row in relevant)
    horizon = min(MAX_MONTH, max(1, horizon))
    floor = resolve_floor(n0, n_start, n_safety)
    weeks = weeks_for_month(horizon)
    harvest = bookings_to_harvest(species, relevant)
    harvest = {week: qty for week, qty in harvest.items() if week < weeks}
    return _survival(n0, floor, weeks, harvest, model, n_paths, seed) + 1e-12 >= clear_fraction(reliability)
