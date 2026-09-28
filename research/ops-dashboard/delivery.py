#!/usr/bin/env python3
"""Starters per pound, and a delivery schedule that keeps the breeding floor.

Quail growth is the ops-dashboard ASSUMPTION curve. The floor that cannot be
sold is the strict genetics floor (Ne >= 50, F_max = 0) together with the
synergy rule that founders are not the product. Stage 4 planning only.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import engine

_GENETICS = Path(__file__).resolve().parents[1] / "genetics"
if str(_GENETICS) not in sys.path:
    sys.path.insert(0, str(_GENETICS))

import reproduction as genetics  # noqa: E402
from circular_buffers import (  # noqa: E402
    ALPHA,
    FAIRNESS,
    M_WEEKLY,
    R_INF,
    R_TBILL,
    SAFETY_FRAC,
    birds_now_for_demand,
    fair_prepaid,
    safe_sell_limit,
)

N0_CAP = 20000
PROBE = 1000.0


def _profile(species: str) -> dict:
    if species == "quail":
        return {
            "species": "quail",
            "females_per_male": 3.0,
            "stage": "Stage 4 quail planning. Not a purchase.",
            "growth_tag": "ASSUMPTION",
        }
    if species == "fish":
        return {
            "species": "fish",
            "females_per_male": 1.0,
            "stage": "Stage 5 aquaponics fish planning. Not a purchase. Growth curve is the quail stub's shape with the fish Ne floor.",
            "growth_tag": "ASSUMPTION",
        }
    raise ValueError("delivery structure is for quail or fish")


def _model(species: str):
    # Fish has no separate growth curve yet. Use the quail stub and say so.
    key = "quail" if species == "fish" else species
    if key not in engine.SPECIES:
        raise ValueError("unknown species")
    return engine.SPECIES[key]


def keep_headcount(species: str) -> int:
    """Birds that must remain: strict Ne floor. Founders are not sold down through it."""
    profile = _profile(species)
    floor = genetics.keep_floor(1, None, None, profile["females_per_male"])
    return int(floor["genetics_floor"])


def safe_lb(n0: float, month: int, species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> float:
    """P10 dressed pounds at month T if the starting herd is kept intact."""
    model = _model(species)
    weeks = engine.weeks_for_month(month)
    head = engine._max_headcount(
        n0, float(n0), weeks, {}, [weeks - 1], model, engine.clear_fraction(reliability), n_paths, seed
    )
    return head / model.headcount_per_unit


def birds_per_lb(month: int, species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> float:
    """Starters required per delivered pound. Falls as T rises.

    The growth curve scales with the starting herd (the bin cap is a multiple
    of N0), so this ratio does not depend on the order size. The Ne floor is
    applied later, in N0_required.
    """
    produced = safe_lb(PROBE, month, species, reliability, n_paths, seed)
    if produced <= 1e-9:
        raise RuntimeError("no safe pounds at the probe herd")
    return PROBE / produced


def n0_required(q_lb: float, month: int, species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> dict:
    """Smallest starting herd that can deliver q_lb at month T and still keep breeders."""
    if q_lb <= 0:
        raise ValueError("q_lb must be > 0")
    profile = _profile(species)
    quantile = engine.planning_quantile(reliability)
    per_lb = birds_per_lb(month, species, quantile, n_paths, seed)
    keep = keep_headcount(species)
    growth_n0 = q_lb * per_lb
    n0 = max(float(keep), growth_n0)
    # Confirm the rounded herd still clears the order. Scale-free, so one bump is enough.
    if safe_lb(n0, month, species, quantile, n_paths, seed) + 1e-6 < q_lb:
        n0 = max(n0, growth_n0) * 1.01
    produced = safe_lb(n0, month, species, quantile, n_paths, seed)
    feasible = produced + 1e-6 >= q_lb and n0 <= N0_CAP
    return {
        "species": species,
        "month": month,
        "q_lb": q_lb,
        "reliability": quantile,
        "birds_per_lb": per_lb,
        "birds_per_lb_with_floor": n0 / q_lb,
        "growth_only_n0": growth_n0,
        "genetics_floor": keep,
        "n0": n0,
        "safe_lb": produced,
        "remaining_lb": max(0.0, produced - q_lb),
        "feasible": feasible,
        "floor_binds": growth_n0 <= keep + 1e-6,
        "stage": profile["stage"],
        "growth_tag": profile["growth_tag"],
        "genetics_mode": "strict",
    }


def _month_for_week(week: int) -> int:
    """Smallest planning month whose end falls on or after this delivery week."""
    if week < 1:
        raise ValueError("week must be >= 1")
    month = 1
    while engine.weeks_for_month(month) < week:
        month += 1
        if month >= engine.MAX_MONTH:
            return engine.MAX_MONTH
    return month


def _sex_one_to_three(n_needed: float, males_min: int, females_min: int) -> tuple[int, int]:
    """Smallest whole flock at 1 male : 3 females that covers the count and both floors.

    Jumbo Coturnix in the quail SPEC keep one male for three females. That ratio
    puts as many hens on eggs as the mating practice allows, which is the
    reproductive maximum used here. A hen-heavier flock would leave hens without
    a male at that practice; a male-heavier flock would idle egg slots.
    """
    males = max(int(males_min), math.ceil(float(n_needed) / 4.0 - 1e-12))
    females = 3 * males
    if females < int(females_min):
        males = max(males, math.ceil(int(females_min) / 3.0 - 1e-12))
        females = 3 * males
    return males, females


def flock_today(
    week: int,
    order_lb: float = 40.0,
    species: str = "quail",
    reliability: float = engine.DEFAULT_QUANTILE,
    n_paths: int = engine.DEFAULT_PATHS,
    seed: int = engine.DEFAULT_SEED,
) -> dict:
    """Flock on hand today for a surplus-only dressed-quail delivery at week `week`.

    Question: a buyer takes `order_lb` pounds at week n. What population must
    already be here so the sale comes from firm surplus, and a 1:3 breeding
    flock is still on hand and able to grow.

    N_today is the larger of:
    - the P10 herd that can finish order_lb * safety_frac / alpha pounds
      (harsh tail, firm fraction, cull-governor gross-up), and
    - the Ne nucleus grossed up for weekly mortality over the lead, plus
      birds_now_for_demand for the slaughtered headcount.

    Breeders are not the product. safe_sell_limit must still allow the sale
    above the genetics floor. min_breeders_for_demand is not used: that kit
    inverse can cull above a cage cap, which would raid the breed floor.
    Stage 4 planning.
    """
    if species != "quail":
        raise ValueError("flock_today is quail planning")
    week = int(week)
    if week < 1:
        raise ValueError("week must be >= 1")
    if order_lb <= 0:
        raise ValueError("order_lb must be > 0")

    profile = _profile(species)
    dress = float(engine.QUAIL_LB_PER_BIRD)
    heads = float(order_lb) / dress
    survival = (1.0 - M_WEEKLY) ** week
    if survival <= 0.0:
        raise RuntimeError("no survivors over this lead")

    floor = genetics.keep_floor(1, None, None, profile["females_per_male"])
    males_floor = int(floor["males_min"])
    females_floor = int(floor["females_min"])
    males_min_today = math.ceil(males_floor / survival - 1e-12)
    females_min_today = math.ceil(females_floor / survival - 1e-12)
    n_breed_today = males_min_today + females_min_today

    pipe = birds_now_for_demand(
        heads,
        m_weekly=M_WEEKLY,
        lead_weeks=float(week),
        safety_frac=SAFETY_FRAC,
        alpha=ALPHA,
    )
    n_pipe = float(pipe["n_pipeline_min"])
    n_deterministic = n_breed_today + n_pipe

    month = _month_for_week(week)
    firm_lb = float(order_lb) * SAFETY_FRAC / ALPHA
    p10 = n0_required(firm_lb, month, species, reliability, n_paths, seed)
    n_p10 = float(p10["n0"])
    n_needed = max(n_deterministic, n_p10)
    males, females = _sex_one_to_three(n_needed, males_min_today, females_min_today)
    n_today = males + females

    males_alive = males * survival
    females_alive = females * survival
    alive = males_alive + females_alive
    breed_floor_n = float(males_floor + females_floor)
    surplus_alive = alive - breed_floor_n
    breeders_remain = (
        surplus_alive + 1e-6 >= heads
        and males_alive + 1e-6 >= males_floor
        and females_alive + 1e-6 >= females_floor
    )
    limited = safe_sell_limit(
        alive,
        breed_floor_n,
        alpha=ALPHA,
        safety_frac=SAFETY_FRAC,
        m_weekly=M_WEEKLY,
        lead_weeks=0.0,
        n_req_forward=breed_floor_n,
    )
    firm_ok = float(limited["allowed_firm"]) + 1e-6 >= heads
    fail_closed = bool(breeders_remain and firm_ok and p10["feasible"])

    spot = float(engine.SPECIES["quail"].spot_usd_per_unit)
    price = fair_prepaid(spot, week / 52.0, r_inf=R_INF, r_tbill=R_TBILL, fairness=FAIRNESS)
    return {
        "week": week,
        "month": month,
        "order_lb": float(order_lb),
        "heads": heads,
        "dress_lb": dress,
        "n_today": n_today,
        "males": males,
        "females": females,
        "ratio_females_per_male": females / males,
        "ratio_label": "1:3",
        "n_pipe": n_pipe,
        "n_breed_today": n_breed_today,
        "n_deterministic": n_deterministic,
        "n_p10": n_p10,
        "binding": "p10" if n_p10 >= n_deterministic - 1e-9 else "pipeline",
        "males_floor": males_floor,
        "females_floor": females_floor,
        "alpha": ALPHA,
        "safety_frac": SAFETY_FRAC,
        "m_weekly": M_WEEKLY,
        "f_prelim": float(price["F_prelim"]),
        "p0": float(price["E_P0"]),
        "T_years": week / 52.0,
        "allowed_firm": float(limited["allowed_firm"]),
        "fail_closed": fail_closed,
        "stage": profile["stage"],
        "growth_tag": "ASSUMPTION",
        "note": (
            "Surplus only. The standing flock is 1 male : 3 females, the jumbo "
            "Coturnix ratio in the quail SPEC. N_today is the larger of the P10 "
            "herd for the safety-grossed firm order and the mortality pipeline "
            "plus the Ne nucleus. Breeders are not sold. Stage 4 planning."
        ),
    }


def _lots_harvest(lots: list[tuple[int, float]], species: str) -> tuple[dict[int, float], int]:
    model = _model(species)
    harvest: dict[int, float] = {}
    last = 1
    for month, qty in lots:
        week = engine.weeks_for_month(month) - 1
        last = max(last, week + 1)
        harvest[week] = harvest.get(week, 0.0) + qty * model.headcount_per_unit
    return harvest, last


def schedule_n0(lots: list[tuple[int, float]], species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> dict:
    """Smallest N0 that can meet every lot on the P10 harsh tail and still keep breeders."""
    if not lots or any(qty <= 0 for _, qty in lots):
        raise ValueError("lots must be positive")
    quantile = engine.planning_quantile(reliability)
    clear = engine.clear_fraction(quantile)
    profile = _profile(species)
    model = _model(species)
    keep = float(keep_headcount(species))
    harvest, weeks = _lots_harvest(lots, species)

    def fits(n0: float) -> bool:
        if n0 + 1e-9 < keep:
            return False
        return engine._survival(n0, n0, weeks, harvest, model, n_paths, seed) + 1e-12 >= clear

    if not fits(keep):
        lo = keep
        hi = max(keep * 2, 2.0)
        found = False
        while hi <= N0_CAP:
            if fits(hi):
                found = True
                break
            lo = hi
            hi = min(N0_CAP, hi * 2)
            if hi == lo:
                break
        if not found:
            return _schedule_result(lots, N0_CAP, False, 0.0, profile, keep, quantile)
        for _ in range(24):
            mid = 0.5 * (lo + hi)
            if fits(mid):
                hi = mid
            else:
                lo = mid
        n0 = hi
    else:
        n0 = keep
    extra = engine._max_headcount(n0, n0, weeks, harvest, [weeks - 1], model, clear, n_paths, seed)
    remaining = extra / model.headcount_per_unit
    return _schedule_result(lots, n0, True, remaining, profile, keep, quantile)


def _schedule_result(lots, n0, feasible, remaining, profile, keep, reliability) -> dict:
    total = sum(qty for _, qty in lots)
    return {
        "lots": [{"month": month, "qty_lb": qty} for month, qty in lots],
        "total_lb": total,
        "n0": n0,
        "birds_per_lb": None if total <= 0 else n0 / total,
        "remaining_lb": remaining,
        "feasible": feasible and n0 <= N0_CAP + 1e-6,
        "genetics_floor": keep,
        "reliability": reliability,
        "stage": profile["stage"],
        "growth_tag": profile["growth_tag"],
        "genetics_mode": "strict",
    }


def _windows_from_request(body: dict) -> list[dict]:
    if body.get("orders"):
        orders = []
        for row in body["orders"]:
            qty = float(row["qty_lb"])
            earliest = int(row.get("earliest_month", row.get("month")))
            latest = int(row.get("latest_month", row.get("month", earliest)))
            orders.append({"qty_lb": qty, "earliest_month": earliest, "latest_month": latest})
        return orders
    qty = float(body["qty_lb"])
    months = [int(m) for m in body["months"]]
    return [{"qty_lb": qty, "earliest_month": min(months), "latest_month": max(months), "candidates": months}]


def recommend(orders: list[dict], species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> dict:
    """Pick the feasible assignment with the smallest starting herd.

    Ties go to the plan with more P10 room left after the deliveries.
    All-soon is the earliest month in each window. The recommendation may be
    a later single month or a split. Infeasible plans fail closed.
    """
    candidates = _candidate_assignments(orders)
    scored = []
    for name, lots in candidates:
        scored.append((name, schedule_n0(lots, species, reliability, n_paths, seed)))
    feasible = [(name, row) for name, row in scored if row["feasible"]]
    if not feasible:
        soon = next((row for name, row in scored if name == "all_soon"), scored[0][1])
        return {
            "feasible": False,
            "fail_closed": True,
            "message": (
                "Stop. None of these delivery months can fill the order without "
                "using the breeding herd. Do not promise it."
            ),
            "plans": {name: row for name, row in scored},
            "recommended": None,
            "all_soon": soon,
            "species": species,
        }
    feasible.sort(key=lambda item: (item[1]["n0"], -item[1]["remaining_lb"]))
    name, best = feasible[0]
    soon = next(row for n, row in scored if n == "all_soon")
    later = best["n0"] + 1e-6 < soon["n0"] or (
        abs(best["n0"] - soon["n0"]) <= 1e-6 and best["remaining_lb"] > soon["remaining_lb"] + 1e-6
    )
    if later:
        message = (
            f"Use { _lot_phrase(best['lots']) }. "
            f"Starting herd about {best['n0']:.0f}. "
            "A sooner lump would need more birds or would leave less room."
        )
    else:
        message = (
            f"Use { _lot_phrase(best['lots']) }. Starting herd about {best['n0']:.0f}."
        )
    return {
        "feasible": True,
        "fail_closed": False,
        "message": message,
        "recommended_name": name,
        "recommended": best,
        "all_soon": soon,
        "plans": {n: row for n, row in scored},
        "species": species,
        "beats_all_soon": later or name != "all_soon",
    }


def _lot_phrase(lots: list[dict]) -> str:
    parts = [f"{row['qty_lb']:g} lb in month {row['month']}" for row in lots]
    return " and ".join(parts)


def _candidate_assignments(orders: list[dict]) -> list[tuple[str, list[tuple[int, float]]]]:
    """All-soon, all-late, each single month that every order can use, and an even split."""
    soon = []
    late = []
    for order in orders:
        soon.append((int(order["earliest_month"]), float(order["qty_lb"])))
        late.append((int(order["latest_month"]), float(order["qty_lb"])))
    plans = [("all_soon", _merge(soon)), ("all_late", _merge(late))]
    # Months every order can hit.
    common = None
    for order in orders:
        window = set(range(int(order["earliest_month"]), int(order["latest_month"]) + 1))
        if order.get("candidates"):
            window &= set(int(m) for m in order["candidates"])
        common = window if common is None else common & window
    for month in sorted(common or []):
        lots = _merge([(month, float(order["qty_lb"])) for order in orders])
        plans.append((f"month_{month}", lots))
    if len(orders) == 1 and orders[0].get("candidates") and len(orders[0]["candidates"]) > 1:
        months = sorted(int(m) for m in orders[0]["candidates"])
        share = float(orders[0]["qty_lb"]) / len(months)
        plans.append(("even_split", [(month, share) for month in months]))
    # Unique by lots.
    seen = set()
    unique = []
    for name, lots in plans:
        key = tuple(lots)
        if key in seen:
            continue
        seen.add(key)
        unique.append((name, lots))
    return unique


def _merge(lots: list[tuple[int, float]]) -> list[tuple[int, float]]:
    totals: dict[int, float] = {}
    for month, qty in lots:
        totals[month] = totals.get(month, 0.0) + qty
    return sorted(totals.items())


def plan_request(body: dict, n_paths: int = engine.DEFAULT_PATHS) -> dict:
    species = str(body.get("species") or "quail")
    raw = body.get("reliability")
    reliability = engine.planning_quantile(None if raw in (None, "") else float(raw))
    orders = _windows_from_request(body)
    months = []
    for order in orders:
        if order.get("candidates"):
            months.extend(int(m) for m in order["candidates"])
        else:
            months.extend(range(int(order["earliest_month"]), int(order["latest_month"]) + 1))
    months = sorted(set(months))
    qty = sum(float(order["qty_lb"]) for order in orders)
    # Table is for the combined pounds delivered as one lump at each candidate month.
    table = [n0_required(qty, month, species, reliability, n_paths) for month in months]
    rec = recommend(orders, species, reliability, n_paths)
    table_falls = all(table[i]["birds_per_lb"] > table[i + 1]["birds_per_lb"] + 1e-9 for i in range(len(table) - 1))
    return {
        "species": species,
        "reliability": reliability,
        "qty_lb": qty,
        "table": table,
        "birds_per_lb_falls_with_T": table_falls,
        "recommendation": rec,
        "formula": (
            "birds_per_lb(T) = N_probe / Q_P10(N_probe, T); "
            "N0(Q, T) = max(N_keep, Q * birds_per_lb(T)); "
            "Q_P10 is the harsh lower tail (only 10% of futures are this low or lower); "
            "N_keep is the strict Ne floor"
        ),
        "stage_gate": "Planning only. Stage 1 worms remain the only active spend. No Stage 2-5 CapEx.",
    }


def smoke(path: Path | None = None) -> dict:
    table = [n0_required(10, month, "quail", 0.10) for month in (3, 6, 12)]
    per_lb = [row["birds_per_lb"] for row in table]
    assert per_lb[0] > per_lb[1] > per_lb[2]

    one = plan_request({"species": "quail", "qty_lb": 10, "months": [3, 6, 12], "reliability": 0.10})
    assert one["birds_per_lb_falls_with_T"]
    assert one["recommendation"]["feasible"]
    assert one["recommendation"]["recommended_name"] != "all_soon"
    late_lots = one["recommendation"]["recommended"]["lots"]
    assert max(lot["month"] for lot in late_lots) > 3

    big = plan_request({"species": "quail", "qty_lb": 40, "months": [3, 6, 12], "reliability": 0.10})
    by_month = {row["month"]: row for row in big["table"]}
    assert by_month[3]["n0"] > by_month[12]["n0"]
    assert big["recommendation"]["recommended"]["n0"] + 1e-6 < big["recommendation"]["all_soon"]["n0"]

    split = recommend(
        [
            {"qty_lb": 15, "earliest_month": 3, "latest_month": 3},
            {"qty_lb": 15, "earliest_month": 3, "latest_month": 12},
        ],
        "quail",
        0.10,
    )
    assert split["feasible"]
    assert split["recommended"]["n0"] + 1e-6 < split["all_soon"]["n0"]
    assert any(lot["month"] > 3 for lot in split["recommended"]["lots"])

    # A huge order in month 1 only, beyond the search cap, fails closed.
    tiny_window = recommend(
        [{"qty_lb": 5000, "earliest_month": 1, "latest_month": 1}],
        "quail",
        0.10,
    )
    assert tiny_window["fail_closed"] is True
    assert abs(table[0]["reliability"] - 0.10) < 1e-9
    # A higher percentile counts on better growth, so it needs fewer starters per pound.
    assert birds_per_lb(6, "quail", 0.10) > birds_per_lb(6, "quail", 0.50)
    try:
        engine.planning_quantile(0.90)
    except ValueError:
        pass
    else:
        raise AssertionError("P90 is not a sell-room or delivery quantile")

    today = flock_today(26, 40.0)
    soon = flock_today(4, 40.0)
    heavier = flock_today(26, 80.0)
    assert today["fail_closed"] and soon["fail_closed"] and heavier["fail_closed"]
    assert today["females"] == 3 * today["males"]
    assert soon["n_today"] > today["n_today"]
    assert heavier["n_today"] > today["n_today"]
    assert today["week"] == 26 and abs(today["f_prelim"] - soon["p0"] * 0.9) < 0.4

    payload = {
        "ok": True,
        "flock_today_40lb_week_26": {
            "n_today": today["n_today"],
            "males": today["males"],
            "females": today["females"],
            "binding": today["binding"],
            "f_prelim": today["f_prelim"],
            "fail_closed": today["fail_closed"],
        },
        "sample_10lb": table,
        "birds_per_lb": per_lb,
        "ten_lb_recommendation": one["recommendation"]["recommended"],
        "forty_lb_n0": {str(k): by_month[k]["n0"] for k in (3, 6, 12)},
        "forty_lb": big["table"],
        "split_n0": split["recommended"]["n0"],
        "all_soon_split_case_n0": split["all_soon"]["n0"],
        "formula": one["formula"],
    }
    out = path or Path(__file__).resolve().parent / "results" / "delivery_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = smoke()
    print("birds_per_lb T=3,6,12", [round(x, 3) for x in result["birds_per_lb"]])
    for row in result["sample_10lb"]:
        print(
            f"T={row['month']} N0={row['n0']:.1f} birds/lb={row['birds_per_lb']:.3f} "
            f"safe_lb={row['safe_lb']:.2f} floor_binds={row['floor_binds']}"
        )
    print("40 lb N0", {k: round(v, 1) for k, v in result["forty_lb_n0"].items()})
    for row in result["forty_lb"]:
        print(
            f"40lb T={row['month']} N0={row['n0']:.1f} birds/lb={row['birds_per_lb']:.3f} "
            f"safe_lb={row['safe_lb']:.2f} room={row['remaining_lb']:.2f}"
        )
    print("split", round(result["split_n0"], 1), "vs all soon", round(result["all_soon_split_case_n0"], 1))
    knee = result["flock_today_40lb_week_26"]
    print(
        f"flock today week 26: N={knee['n_today']} {knee['males']}M/{knee['females']}F "
        f"bind={knee['binding']} F_prelim={knee['f_prelim']:.4f}"
    )
