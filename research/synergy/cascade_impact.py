#!/usr/bin/env python3
"""Cross-species impact of selling one species at month t. Planning only.

Stage 1 worms remain the only spend. Quail is Stage 4 planning. Fish and
plants are Stage 5 stubs. This does not buy animals, feed, or equipment.

A sale reports the herd that remains, the Ne floor, P10 room left, the feed
those animals stop eating, and the worm surplus that keeps reproducing.
If that surplus is left in the bin it can crowd the carrying line. If a
Stage 5 fish herd is named, the surplus can be offered as extra feed, and
the plant cushion has to absorb the extra plant demand. Buffers fail closed:
breeders are not raided to fill a gap.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPS = ROOT.parent / "ops-dashboard"
GENETICS = ROOT.parent / "genetics"
for folder in (ROOT, OPS, GENETICS):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import engine  # noqa: E402
import quail_income  # noqa: E402
import reproduction as genetics  # noqa: E402
from circular_buffers import BUFFER_WEEKS  # noqa: E402

# Fewer draws than the sell-room screen so this report returns on a laptop.
# Same seed and the same P10 rule (clear fraction 0.90).
CASCADE_PATHS = 200
HORIZON = 12
# Demo worm starters. Present stock in the sample is larger so quail feed
# does not immediately empty the bin.
WORM_FLOOR_HEADCOUNT = 16500.0
# Share of carrying capacity that counts as density stress. ASSUMPTION.
DENSITY_STRESS = 0.85
# Stage 5 ASSUMPTION stubs. Not a measured tilapia ration or crop yield.
FISH_INTAKE_G_PER_DAY = 12.0
FISH_WORM_SHARE = 0.20
FISH_PLANT_SHARE = 0.80
# One extra base fish ration of worms raises the growth index by this fraction.
FISH_GROWTH_LIFT = 0.15
FISH_GROWTH_CAP = 1.25
LB_PER_KG = 2.2046226218

SAMPLE = {
    "quail_males": 24,
    "quail_females": 72,
    "worm_headcount": 250_000,
    "worm_floor": WORM_FLOOR_HEADCOUNT,
    "species": "quail",
    "n": 16,
    "month": 4,
    "horizon_months": HORIZON,
    "fish_n": 0,
}
REFUSE_SAMPLE = dict(SAMPLE, n=40)
SHORT_SAMPLE = {
    "quail_males": 80,
    "quail_females": 240,
    "worm_headcount": WORM_FLOOR_HEADCOUNT,
    "worm_floor": WORM_FLOOR_HEADCOUNT,
    "species": "quail",
    "n": 40,
    "month": 6,
    "horizon_months": HORIZON,
    "fish_n": 0,
}
FISH_SAMPLE = dict(SAMPLE, fish_n=40)


def _round(value: float, places: int = 4) -> float:
    return round(float(value), places)


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(math.floor(q * (len(ordered) - 1)))
    idx = min(len(ordered) - 1, max(0, idx))
    return ordered[idx]


def _grow(n: float, factor: float, capacity: float) -> float:
    room = 1.0 - n / capacity
    if room < 0.0:
        room = 0.0
    return n + n * (factor - 1.0) * room


def _kg_per_bird_month() -> float:
    return quail_income.INTAKE_G_PER_BIRD_DAY * quail_income.DAYS_PER_MONTH / 1000.0


def _worms_per_kg() -> float:
    return engine.WORM_HEADCOUNT_PER_LB * LB_PER_KG


def _month_of_week(horizon: int) -> dict[int, int]:
    """Map a 0-based week index to the month whose end week it is, if any."""
    found: dict[int, int] = {}
    for month in range(1, horizon + 1):
        found[engine.weeks_for_month(month) - 1] = month
    return found


def _sale_week(month: int) -> int:
    """First 0-based week of the delivery month. Birds leave before they eat."""
    if month <= 1:
        return 0
    return engine.weeks_for_month(month - 1)


def quail_floor(founders: float | None) -> dict:
    """Birds that must stay. Founders raise the synergy floor. Ne never drops under 50."""
    anchor = genetics.keep_floor(1.0, None, None, 3.0)["genetics_floor"]
    n0 = anchor if founders is None else max(float(founders), 0.0)
    return genetics.keep_floor(n0, None, None, 3.0)


def _split_sale(males: float, females: float, n: float) -> tuple[float, float]:
    total = males + females
    if total <= 0:
        raise ValueError("quail herd is empty")
    if n < 0:
        raise ValueError("sale must be >= 0")
    if n > total + 1e-9:
        raise ValueError("cannot sell more quail than are on hand")
    return n * males / total, n * females / total


def _p10_extra_headcount(
    species: str,
    n0: float,
    floor: float,
    month: int,
    base: dict[int, float],
    n_paths: int,
) -> float:
    """Largest extra headcount at `month` that the P10 tail can still carry."""
    model = engine.SPECIES[species]
    weeks = engine.weeks_for_month(month)
    return engine._max_headcount(
        n0,
        floor,
        weeks,
        base,
        [weeks - 1],
        model,
        engine.clear_fraction(engine.DEFAULT_QUANTILE),
        n_paths,
        engine.DEFAULT_SEED,
    )


def _even_monthly_headcount(
    species: str,
    n0: float,
    floor: float,
    horizon: int,
    base: dict[int, float],
    n_paths: int,
) -> float:
    model = engine.SPECIES[species]
    weeks = engine.weeks_for_month(horizon)
    ends = [week for week in engine.month_end_weeks(horizon) if week < weeks]
    return engine._max_headcount(
        n0,
        floor,
        weeks,
        base,
        ends,
        model,
        engine.clear_fraction(engine.DEFAULT_QUANTILE),
        n_paths,
        engine.DEFAULT_SEED,
    )


def _paths(
    *,
    quail0: float,
    quail_floor_n: float,
    worm0: float,
    worm_floor_n: float,
    sale_birds: float,
    sale_week: int,
    apply_sale: bool,
    horizon: int,
    n_paths: int,
) -> dict:
    """P10 and heavy standing herds. Feed offtake never crosses a breed floor."""
    weeks = engine.weeks_for_month(horizon)
    quail_model = engine.SPECIES["quail"]
    worm_model = engine.SPECIES["worms"]
    shocks_q = engine._shocks(quail_model, weeks, n_paths, engine.DEFAULT_SEED)
    shocks_w = engine._shocks(worm_model, weeks, n_paths, engine.DEFAULT_SEED + 1)
    cap_q = engine._capacity(quail_model, quail0, quail_floor_n)
    cap_w = engine._capacity(worm_model, worm0, worm_floor_n)
    month_end = _month_of_week(horizon)
    per_bird_month = _kg_per_bird_month()
    worm_kg_bird_week = per_bird_month * quail_income.WORM_SHARE / engine.WEEKS_PER_MONTH
    plant_kg_bird_week = per_bird_month * quail_income.PLANT_SHARE / engine.WEEKS_PER_MONTH
    worms_per_kg = _worms_per_kg()
    standing_q = {month: [] for month in range(1, horizon + 1)}
    standing_w = {month: [] for month in range(1, horizon + 1)}
    feed_worm = {month: [] for month in range(1, horizon + 1)}
    feed_plant = {month: [] for month in range(1, horizon + 1)}
    demand_worm = {month: [] for month in range(1, horizon + 1)}
    short_worm = {month: [] for month in range(1, horizon + 1)}
    for fq, fw in zip(shocks_q, shocks_w):
        nq = float(quail0)
        nw = float(worm0)
        broken = False
        week_worm = {month: 0.0 for month in range(1, horizon + 1)}
        week_plant = {month: 0.0 for month in range(1, horizon + 1)}
        week_demand = {month: 0.0 for month in range(1, horizon + 1)}
        week_short = {month: 0.0 for month in range(1, horizon + 1)}
        current_month = 1
        for week, (factor_q, factor_w) in enumerate(zip(fq, fw)):
            if apply_sale and week == sale_week:
                nq -= sale_birds
                if nq < 0.0:
                    nq = 0.0
            nq = _grow(nq, factor_q, cap_q)
            nw = _grow(nw, factor_w, cap_w)
            if nq + 1e-6 < quail_floor_n or nw + 1e-6 < worm_floor_n:
                broken = True
            demand_head = nq * worm_kg_bird_week * worms_per_kg
            surplus = max(0.0, nw - worm_floor_n)
            take = min(demand_head, surplus)
            nw -= take
            demand_kg = nq * worm_kg_bird_week
            # Weeks before the first month-end still belong to month 1.
            while current_month < horizon and week > engine.weeks_for_month(current_month) - 1:
                current_month += 1
            week_worm[current_month] += take / worms_per_kg
            week_plant[current_month] += nq * plant_kg_bird_week
            week_demand[current_month] += demand_kg
            week_short[current_month] += max(0.0, demand_head - take) / worms_per_kg
            if week in month_end and not broken:
                month = month_end[week]
                standing_q[month].append(nq)
                standing_w[month].append(nw)
                feed_worm[month].append(week_worm[month])
                feed_plant[month].append(week_plant[month])
                demand_worm[month].append(week_demand[month])
                short_worm[month].append(week_short[month])
    q = engine.DEFAULT_QUANTILE
    heavy = 1.0 - q

    def pack(table: dict[int, list[float]]) -> list[dict]:
        rows = []
        for month in range(1, horizon + 1):
            rows.append(
                {
                    "month": month,
                    "p10": _round(_percentile(table[month], q), 2),
                    "heavy": _round(_percentile(table[month], heavy), 2),
                }
            )
        return rows

    return {
        "quail": pack(standing_q),
        "worms": pack(standing_w),
        "worm_feed_kg": pack(feed_worm),
        "worm_demand_kg": pack(demand_worm),
        "plant_feed_kg": pack(feed_plant),
        "worm_short_kg": pack(short_worm),
        "worm_capacity": cap_w,
        "quail_capacity": cap_q,
    }


def _plant_cushion(plant_feed: list[dict], fish_extra: list[float]) -> dict:
    """Opening production matches month-1 heavy demand. Cushion is B_s weeks.

    Both the match and the fish ration are ASSUMPTION stubs. Stage 5.
    """
    if not plant_feed:
        return {"cushion_kg": [], "broken": False, "gap_kg": 0.0}
    opening = plant_feed[0]["heavy"]
    production = opening
    buffer_months = BUFFER_WEEKS / engine.WEEKS_PER_MONTH
    cushion = production * buffer_months
    rows = []
    broken = False
    worst = 0.0
    for row, extra in zip(plant_feed, fish_extra):
        demand = row["heavy"] + extra
        cushion = cushion + production - demand
        if cushion < -1e-6:
            broken = True
            worst = min(worst, cushion)
        rows.append({"month": row["month"], "cushion_kg": _round(cushion, 2), "demand_kg": _round(demand, 2)})
    return {
        "production_kg_per_month": _round(production, 2),
        "opening_cushion_kg": _round(production * buffer_months, 2),
        "months": rows,
        "broken": broken,
        "gap_kg": _round(abs(worst) if broken else 0.0, 2),
        "tag": "ASSUMPTION",
        "future": (
            "Aquaponic water composition, nutrient distribution, and nutrient mix "
            "are not modeled. They are the long-term lever for higher plant growth."
        ),
    }


def _fish_extra(excess_worm_kg: list[float], fish_n: float) -> dict:
    """Stage 5 stub. Empty fish herd means the excess worms stay in the bin."""
    if fish_n <= 0:
        return {
            "stage": 5,
            "tag": "ASSUMPTION",
            "fish_n": 0,
            "active": False,
            "growth_index": [1.0 for _ in excess_worm_kg],
            "extra_plant_kg": [0.0 for _ in excess_worm_kg],
            "extra_worm_kg": [0.0 for _ in excess_worm_kg],
            "note": "No Stage 5 fish herd. Excess worms are not reallocated.",
        }
    per_month = FISH_INTAKE_G_PER_DAY * quail_income.DAYS_PER_MONTH / 1000.0
    base_worm = fish_n * per_month * FISH_WORM_SHARE
    base_plant = fish_n * per_month * FISH_PLANT_SHARE
    indexes = []
    extra_plant = []
    extra_worm = []
    for spare in excess_worm_kg:
        fed = min(max(0.0, spare), base_worm) if base_worm > 0 else 0.0
        lift = 1.0 + FISH_GROWTH_LIFT * (fed / base_worm if base_worm else 0.0)
        lift = min(FISH_GROWTH_CAP, lift)
        indexes.append(_round(lift, 4))
        extra_plant.append(_round(base_plant * (lift - 1.0), 3))
        extra_worm.append(_round(base_worm * (lift - 1.0), 3))
    return {
        "stage": 5,
        "tag": "ASSUMPTION",
        "fish_n": fish_n,
        "active": True,
        "base_worm_kg": _round(base_worm, 3),
        "base_plant_kg": _round(base_plant, 3),
        "growth_index": indexes,
        "extra_plant_kg": extra_plant,
        "extra_worm_kg": extra_worm,
        "formula": (
            "growth_index = min(cap, 1 + lift * min(excess, base_worm) / base_worm); "
            "extra plant = base_plant * (growth_index - 1)"
        ),
        "note": (
            f"ASSUMPTION stub: {FISH_INTAKE_G_PER_DAY:g} g/fish/day, "
            f"{FISH_WORM_SHARE:.0%} worms / {FISH_PLANT_SHARE:.0%} plant. Not a measured ration."
        ),
    }


def _svg(series_hold: dict, series_sale: dict) -> str:
    """Two panels: P10 worm pounds and P10 quail, hold versus sale."""
    worms_hold = [row["p10"] / engine.WORM_HEADCOUNT_PER_LB for row in series_hold["worms"]]
    worms_sale = [row["p10"] / engine.WORM_HEADCOUNT_PER_LB for row in series_sale["worms"]]
    quail_hold = [row["p10"] for row in series_hold["quail"]]
    quail_sale = [row["p10"] for row in series_sale["quail"]]
    width, top, left, right = 680, 16, 44, 12
    plot_w, plot_h, gap = width - left - right, 92, 28

    def panel(y0: float, hold: list[float], sale: list[float], color: str, title: str) -> str:
        lo = min(hold + sale)
        hi = max(hold + sale)
        if hi <= lo:
            hi = lo + 1.0

        def points(values: list[float]) -> str:
            parts = []
            for i, value in enumerate(values):
                x = left + (0 if len(values) == 1 else plot_w * i / (len(values) - 1))
                y = y0 + plot_h * (1.0 - (value - lo) / (hi - lo))
                parts.append(f"{x:.1f},{y:.1f}")
            return " ".join(parts)

        return (
            f'<text x="{left}" y="{y0 - 4:.0f}" font-size="12" fill="#1c1915">{title}</text>'
            f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{points(hold)}" />'
            f'<polyline fill="none" stroke="{color}" stroke-width="2.2" stroke-dasharray="6 4" points="{points(sale)}" />'
        )

    height = top + plot_h + gap + plot_h + 28
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">'
        '<rect width="100%" height="100%" fill="#fffdf8"/>'
        f"{panel(top + 14, worms_hold, worms_sale, '#1d4e89', 'P10 worm pounds. Solid hold, dashed sale.')}"
        f"{panel(top + 14 + plot_h + gap, quail_hold, quail_sale, '#9a3412', 'P10 quail. Solid hold, dashed sale.')}"
        f'<text x="{left}" y="{height - 8}" font-size="11" fill="#5c564c">'
        "ASSUMPTION growth. P10. Not a purchase."
        "</text></svg>"
    )


def impact(scenario: dict | None = None) -> dict:
    """Sell n units of species S at month t and report the cascade."""
    raw = dict(SAMPLE)
    if scenario:
        raw.update({key: value for key, value in scenario.items() if value is not None})
    species = str(raw.get("species", "quail")).strip().lower()
    if species not in ("quail", "worms"):
        raise ValueError("species must be quail or worms")
    males = float(raw.get("quail_males", SAMPLE["quail_males"]))
    females = float(raw.get("quail_females", SAMPLE["quail_females"]))
    if males < 0 or females < 0:
        raise ValueError("quail counts must be >= 0")
    worm0 = float(raw.get("worm_headcount", SAMPLE["worm_headcount"]))
    worm_floor_n = float(raw.get("worm_floor", WORM_FLOOR_HEADCOUNT))
    if worm0 <= 0 or worm_floor_n < 0:
        raise ValueError("worm herd must be positive and the floor cannot be negative")
    if worm_floor_n > worm0 + 1e-6:
        raise ValueError("worm floor cannot sit above the present herd")
    n = float(raw.get("n", SAMPLE["n"]))
    month = int(raw.get("month", SAMPLE["month"]))
    horizon = int(raw.get("horizon_months", HORIZON))
    if month < 1 or month > horizon or horizon > engine.MAX_MONTH:
        raise ValueError("month must sit inside the horizon")
    fish_n = float(raw.get("fish_n", 0) or 0)
    if fish_n < 0:
        raise ValueError("fish herd cannot be negative")
    n_paths = int(raw.get("n_paths", CASCADE_PATHS))
    founders = raw.get("quail_founders")
    floor = quail_floor(None if founders in (None, "") else float(founders))
    quail0 = males + females
    sale_birds = 0.0
    sale_worm_head = 0.0
    direct: dict
    if species == "quail":
        sell_m, sell_f = _split_sale(males, females, n)
        verdict = genetics.cull_plan(
            males,
            females,
            sell_m,
            sell_f,
            floor["synergy_floor"],
            3.0,
        )
        sale_birds = n if verdict["allowed"] else 0.0
        room_birds = _p10_extra_headcount("quail", quail0, floor["keep"], month, {}, n_paths)
        sale_week = _sale_week(month)
        base = {sale_week: n} if verdict["allowed"] else {}
        # Room left is further headcount at that same month after this sale.
        # A sale booked at the start of the month is not the month-end harvest
        # the engine uses, so the check below uses the month-end P10 cap.
        room_after = _p10_extra_headcount("quail", quail0, floor["keep"], month, {engine.weeks_for_month(month) - 1: n} if verdict["allowed"] else {}, n_paths)
        p10_ok = n <= room_birds + 1e-6
        if verdict["allowed"] and not p10_ok:
            sale_birds = 0.0
            verdict = dict(verdict)
            verdict["allowed"] = False
            verdict["reasons"] = list(verdict["reasons"]) + [
                "P10 harvest room at that month is smaller than the sale"
            ]
        direct = {
            "species": "quail",
            "unit": "birds",
            "sold": n if verdict["allowed"] else 0.0,
            "requested": n,
            "sold_males": _round(sell_m, 2) if verdict["allowed"] else 0.0,
            "sold_females": _round(sell_f, 2) if verdict["allowed"] else 0.0,
            "remaining_males": _round(verdict["males_after"] if verdict["allowed"] else males, 2),
            "remaining_females": _round(verdict["females_after"] if verdict["allowed"] else females, 2),
            "remaining_herd": _round((verdict["males_after"] + verdict["females_after"]) if verdict["allowed"] else quail0, 2),
            "Ne_after": _round(verdict["Ne_after"] if verdict["allowed"] else genetics.wright_ne(males, females), 2),
            "delta_F_after": _round(verdict["delta_F_after"] if verdict["allowed"] else genetics.delta_f(genetics.wright_ne(males, females)), 4),
            "floor": floor,
            "genetics_allowed": not any("Ne" in item or "floor" in item or "males" in item for item in verdict["reasons"]),
            "p10_room_birds": _round(room_birds, 2),
            "p10_room_lb": _round(room_birds * engine.QUAIL_LB_PER_BIRD, 2),
            "p10_room_left_birds": _round(room_after if verdict["allowed"] else room_birds, 2),
            "p10_ok": p10_ok and verdict["allowed"],
            "reasons": verdict["reasons"],
        }
        allowed = verdict["allowed"] and p10_ok
    else:
        sale_worm_head = n * engine.WORM_HEADCOUNT_PER_LB
        if sale_worm_head > worm0 - worm_floor_n + 1e-6:
            reasons = ["sale would take worms out of the breeding floor"]
            allowed = False
        else:
            reasons = []
            allowed = True
        room_head = _p10_extra_headcount("worms", worm0, worm_floor_n, month, {}, n_paths)
        room_after = _p10_extra_headcount(
            "worms",
            worm0,
            worm_floor_n,
            month,
            {engine.weeks_for_month(month) - 1: sale_worm_head} if allowed else {},
            n_paths,
        )
        if allowed and sale_worm_head > room_head + 1e-6:
            allowed = False
            reasons = ["P10 harvest room at that month is smaller than the sale"]
        direct = {
            "species": "worms",
            "unit": "lb",
            "sold": n if allowed else 0.0,
            "requested": n,
            "remaining_herd": _round((worm0 - sale_worm_head) if allowed else worm0, 1),
            "floor_headcount": worm_floor_n,
            "p10_room_lb": _round(room_head / engine.WORM_HEADCOUNT_PER_LB, 2),
            "p10_room_left_lb": _round((room_after if allowed else room_head) / engine.WORM_HEADCOUNT_PER_LB, 2),
            "p10_ok": allowed,
            "reasons": reasons,
            "Ne_after": None,
            "note": "Worms have no sex ratio and no Ne floor in this planner.",
        }
        sale_birds = 0.0

    hold = _paths(
        quail0=quail0,
        quail_floor_n=floor["keep"],
        worm0=worm0 - (sale_worm_head if allowed and species == "worms" else 0.0),
        worm_floor_n=worm_floor_n,
        sale_birds=0.0,
        sale_week=_sale_week(month),
        apply_sale=False,
        horizon=horizon,
        n_paths=n_paths,
    )
    # When the worm sale is allowed, both paths start after the removal so the
    # quail comparison stays fair. The with-sale quail path then removes birds.
    sold_worm0 = worm0 - (sale_worm_head if allowed and species == "worms" else 0.0)
    sale_path = _paths(
        quail0=quail0,
        quail_floor_n=floor["keep"],
        worm0=worm0,
        worm_floor_n=worm_floor_n,
        sale_birds=sale_birds,
        sale_week=_sale_week(month),
        apply_sale=allowed and species == "quail",
        horizon=horizon,
        n_paths=n_paths,
    )
    if allowed and species == "worms":
        # Hold path above already removed the sold worms. Rebuild the unsold path.
        hold = _paths(
            quail0=quail0,
            quail_floor_n=floor["keep"],
            worm0=worm0,
            worm_floor_n=worm_floor_n,
            sale_birds=0.0,
            sale_week=_sale_week(month),
            apply_sale=False,
            horizon=horizon,
            n_paths=n_paths,
        )
        sale_path = _paths(
            quail0=quail0,
            quail_floor_n=floor["keep"],
            worm0=sold_worm0,
            worm_floor_n=worm_floor_n,
            sale_birds=0.0,
            sale_week=_sale_week(month),
            apply_sale=False,
            horizon=horizon,
            n_paths=n_paths,
        )

    excess = []
    for left, right, feed_l, feed_r in zip(
        hold["worms"], sale_path["worms"], hold["worm_demand_kg"], sale_path["worm_demand_kg"]
    ):
        excess.append(
            {
                "month": left["month"],
                "excess_headcount": _round(right["p10"] - left["p10"], 1),
                "excess_lb": _round((right["p10"] - left["p10"]) / engine.WORM_HEADCOUNT_PER_LB, 3),
                "feed_kg_delta": _round(feed_r["p10"] - feed_l["p10"], 3),
            }
        )
    at = next(row for row in excess if row["month"] == month)
    peak = max(excess, key=lambda row: row["excess_lb"])
    plant_delta = []
    for left, right in zip(hold["plant_feed_kg"], sale_path["plant_feed_kg"]):
        plant_delta.append(
            {
                "month": left["month"],
                "plant_kg_delta": _round(right["heavy"] - left["heavy"], 3),
            }
        )
    excess_kg = [
        max(0.0, row["excess_lb"] * engine.WORM_HEADCOUNT_PER_LB / _worms_per_kg()) for row in excess
    ]
    fish = _fish_extra(excess_kg, fish_n)
    plants_hold = _plant_cushion(hold["plant_feed_kg"], [0.0 for _ in excess])
    plants_sale = _plant_cushion(sale_path["plant_feed_kg"], fish["extra_plant_kg"])
    density = sale_path["worms"][-1]["p10"] > DENSITY_STRESS * sale_path["worm_capacity"]
    hold_gap = sum(row["heavy"] for row in hold["worm_short_kg"])
    sale_gap = sum(row["heavy"] for row in sale_path["worm_short_kg"])
    # Harsh feed gap is the heavy tail of the shortfall, same side as the heavy herd.
    short_worse = sale_gap > hold_gap + 0.05
    early_short = any(
        row["heavy"] > 0.5 for row in sale_path["worm_short_kg"] if row["month"] <= month
    )
    feed_blocked = short_worse or early_short
    plant_worse = plants_sale["broken"] and (
        plants_sale["gap_kg"] > plants_hold["gap_kg"] + 1e-6
    )
    if not allowed:
        status = "refuse"
    elif feed_blocked or plant_worse:
        status = "refuse"
    elif density or plants_sale["broken"]:
        status = "warn"
    else:
        status = "ok"

    further = 0.0
    if species == "quail" and allowed:
        further = _even_monthly_headcount(
            "quail",
            quail0,
            floor["keep"],
            horizon,
            {engine.weeks_for_month(month) - 1: n},
            n_paths,
        )
    schedule = []
    for row, feed, plant in zip(excess, sale_path["worm_feed_kg"], sale_path["plant_feed_kg"]):
        birds = n if status != "refuse" and allowed and species == "quail" and row["month"] == month else 0.0
        # Take the freed worms as product while they are still above the hold path.
        # Leaving them in the bin lets the growing quail flock eat them later.
        worm_product = max(0.0, row["excess_lb"]) if status != "refuse" and allowed else 0.0
        schedule.append(
            {
                "month": row["month"],
                "quail_birds": _round(birds, 2),
                "further_monthly_birds_p10": _round(further, 2),
                "worm_feed_lb": _round(feed["p10"] * LB_PER_KG, 3),
                "worm_product_lb": _round(worm_product, 3),
                "plant_kg": plant["heavy"],
            }
        )
    if status == "refuse" and direct.get("sold"):
        direct["tested_sale"] = direct["sold"]
        direct["sold"] = 0.0
        if species == "quail":
            direct["remaining_males"] = _round(males, 2)
            direct["remaining_females"] = _round(females, 2)
            direct["remaining_herd"] = _round(quail0, 2)
            direct["Ne_after"] = _round(genetics.wright_ne(males, females), 2)
        else:
            direct["remaining_herd"] = _round(worm0, 1)
    if status == "refuse" and not allowed:
        message = "Sale refused. " + (" ".join(direct["reasons"]) or "The breeding floor holds.")
    elif status == "refuse" and feed_blocked:
        message = (
            "Sale stopped. Worm feed for the remaining herd would take the breeding floor, "
            "and the cascade fails closed instead."
        )
    elif status == "refuse":
        message = (
            "Sale stopped. Sending the extra worms on to fish would drop the plant cushion "
            "below the no-sale path. The buffer fails closed."
        )
    elif density:
        message = (
            "Sale fits the P10 room and the Ne floor. "
            "Leaving the extra worms in the bin crowds the carrying line. "
            "Sell that surplus, or the Stage 5 stub can offer it to fish."
        )
    elif plants_sale["broken"]:
        message = (
            "Sale fits the P10 room and the Ne floor. "
            "Plant production is an opening-sized stub, so quail growth outruns it on both paths. "
            "The sale makes that plant gap smaller. "
            "A higher plant growth rate is the open lever, not a modeled yield."
        )
    else:
        message = "Sale fits the P10 room, the Ne floor, and the feed buffers on this plan."

    return {
        "stage_gate": "Stage 1 worms are the only spend. Quail is Stage 4 planning. Fish and plants are Stage 5 stubs.",
        "status": status,
        "booked": status != "refuse",
        "message": message,
        "quantile": engine.DEFAULT_QUANTILE,
        "paths": n_paths,
        "direct": direct,
        "consumption": {
            "formula": (
                "worm_kg = birds * 22 g/day * 0.30 * days_in_month; "
                "plant_kg = birds * 22 g/day * 0.70 * days_in_month; "
                "delta is the with-sale path minus the hold path"
            ),
            "intake_tag": "ASSUMPTION",
            "at_sale_month": {
                "worm_feed_kg_delta": at["feed_kg_delta"],
                "plant_kg_delta": next(row["plant_kg_delta"] for row in plant_delta if row["month"] == month),
            },
            "months": [
                {
                    "month": row["month"],
                    "worm_feed_kg_delta": row["feed_kg_delta"],
                    "plant_kg_delta": plant["plant_kg_delta"],
                }
                for row, plant in zip(excess, plant_delta)
            ],
        },
        "surplus": {
            "formula": (
                "Same logistic as the ops screen, shared shocks. "
                "Sold birds stop eating at the start of month t. "
                "Uneaten worms stay in the bin and keep growing. "
                "excess_lb(t) = P10_worms(sale) - P10_worms(hold), in pounds."
            ),
            "growth_tag": "ASSUMPTION",
            "excess_lb_at_sale": at["excess_lb"],
            "excess_headcount_at_sale": at["excess_headcount"],
            "excess_lb_peak": peak["excess_lb"],
            "excess_peak_month": peak["month"],
            "excess_lb_at_horizon": excess[-1]["excess_lb"],
            "months": excess,
            "density_stress": density,
            "density_line": DENSITY_STRESS,
            "density_tag": "ASSUMPTION",
        },
        "fish": fish,
        "plants": {
            "hold": plants_hold,
            "with_sale": plants_sale,
            "worse_because_of_sale": plant_worse,
        },
        "schedule": schedule,
        "buffers": {
            "worm_feed_short": feed_blocked,
            "plant_broken": plants_sale["broken"],
            "breeders_raided": False,
            "fail_closed": status == "refuse",
        },
        "series": {"hold": hold, "sale": sale_path},
        "svg": _svg(hold, sale_path),
        "formulas": {
            "Ne": "Ne = 4*Nm*Nf/(Nm+Nf); refuse when Ne would fall below 50",
            "P10": "Room is the 10th percentile of headroom. clear fraction = 0.90.",
            "feed": "22 g/bird/day ASSUMPTION, 30% worms, 70% plant, plus the 2-week buffer on plants.",
            "worms": "Median doubling 13 weeks, cap 16x the larger of the present herd and the floor. Not worm_growth_mc.",
        },
    }


def smoke(path: Path | None = None) -> dict:
    """Sample sale, a refused Ne sale, a short worm bin, and a Stage 5 fish stub."""
    sample = impact(SAMPLE)
    refused = impact(REFUSE_SAMPLE)
    short = impact(SHORT_SAMPLE)
    fish = impact(FISH_SAMPLE)
    payload = {
        "ok": True,
        "stage_gate": sample["stage_gate"],
        "sample_status": sample["status"],
        "sample_excess_lb_at_sale": sample["surplus"]["excess_lb_at_sale"],
        "sample_excess_lb_peak": sample["surplus"]["excess_lb_peak"],
        "sample_excess_peak_month": sample["surplus"]["excess_peak_month"],
        "sample_excess_lb_at_horizon": sample["surplus"]["excess_lb_at_horizon"],
        "sample_feed_delta_kg": sample["consumption"]["at_sale_month"],
        "sample_remaining": sample["direct"]["remaining_herd"],
        "sample_ne": sample["direct"]["Ne_after"],
        "sample_p10_room_birds": sample["direct"]["p10_room_birds"],
        "sample_p10_room_left_birds": sample["direct"]["p10_room_left_birds"],
        "fish_growth_index_at_sale": fish["fish"]["growth_index"][SAMPLE["month"] - 1],
        "fish_extra_plant_kg_at_sale": fish["fish"]["extra_plant_kg"][SAMPLE["month"] - 1],
        "plant_gap_hold_kg": sample["plants"]["hold"]["gap_kg"],
        "plant_gap_sale_kg": sample["plants"]["with_sale"]["gap_kg"],
        "plant_gap_fish_kg": fish["plants"]["with_sale"]["gap_kg"],
        "refuse_status": refused["status"],
        "short_status": short["status"],
        "short_fail_closed": short["buffers"]["fail_closed"],
        "breeders_raided": sample["buffers"]["breeders_raided"],
    }
    if sample["status"] == "refuse":
        raise SystemExit("sample sale should fit the floor and the P10 room")
    if sample["surplus"]["excess_lb_at_sale"] <= 0:
        raise SystemExit("selling birds should leave more worms by the sale month")
    if sample["surplus"]["excess_lb_peak"] <= sample["surplus"]["excess_lb_at_sale"]:
        raise SystemExit("excess worms should keep reproducing after the sale month")
    if sample["consumption"]["at_sale_month"]["worm_feed_kg_delta"] >= 0:
        raise SystemExit("fewer birds should demand less worm feed in the sale month")
    if refused["status"] != "refuse":
        raise SystemExit("a sale through the Ne floor must be refused")
    if short["status"] != "refuse" or short["buffers"]["breeders_raided"]:
        raise SystemExit("a short worm bin must fail closed without raiding breeders")
    if not fish["fish"]["active"]:
        raise SystemExit("fish stub should be active when fish_n is set")
    out = path or ROOT / "results" / "cascade_impact_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    stored = dict(payload)
    stored["sample_message"] = sample["message"]
    stored["direct"] = sample["direct"]
    stored["surplus_months"] = sample["surplus"]["months"]
    stored["fish_note"] = fish["fish"]["note"]
    out.write_text(json.dumps(stored, indent=2) + "\n", encoding="utf-8")
    # Keep the svg off the smoke file; the plot script writes the PNG.
    payload["svg"] = sample["svg"]
    payload["series"] = sample["series"]
    return payload


if __name__ == "__main__":
    result = smoke()
    print(
        f"status={result['sample_status']}  "
        f"excess_lb_at_month={result['sample_excess_lb_at_sale']}  "
        f"excess_lb_at_horizon={result['sample_excess_lb_at_horizon']}  "
        f"Ne={result['sample_ne']}  "
        f"refuse={result['refuse_status']}  short={result['short_status']}"
    )
