#!/usr/bin/env python3
"""Starters per pound, and a delivery schedule that keeps the breeding floor.

Quail meat is the individual jumbo Coturnix Monte Carlo: dressed pounds are
the sum of sex- and age-specific weights of the birds actually removed.
Fish still uses the logistic stub. The floor that cannot be sold is the
strict genetics floor (Ne >= 50, F_max = 0). Stage 4 planning only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import engine

_GENETICS = Path(__file__).resolve().parents[1] / "genetics"
_QUAIL = Path(__file__).resolve().parents[1] / "quail"
for folder in (_GENETICS, _QUAIL):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import bird_mc  # noqa: E402
import reproduction as genetics  # noqa: E402

N0_CAP = 20000
PROBE = 1000.0


def _profile(species: str) -> dict:
    if species == "quail":
        return {
            "species": "quail",
            "females_per_male": 3.0,
            "stage": "Stage 4 quail planning. Not a purchase.",
            "growth_tag": "individual Monte Carlo, sex-specific dressed weight",
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


def _quail_paths(n_paths: int) -> int:
    """The bird Monte Carlo is not the 2,000-path worm screen."""
    return max(8, min(int(n_paths), bird_mc.PATHS))


def safe_lb(n0: float, month: int, species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> float:
    """Harsh-tail dressed pounds at month T if breeders are kept."""
    if species == "quail":
        del seed
        info = bird_mc.surplus_lb(max(1, int(round(n0))), month, reliability, _quail_paths(n_paths))
        return float(info["q_lb"])
    model = _model(species)
    weeks = engine.weeks_for_month(month)
    head = engine._max_headcount(
        n0, float(n0), weeks, {}, [weeks - 1], model, engine.clear_fraction(reliability), n_paths, seed
    )
    return head / model.headcount_per_unit


def birds_per_lb(month: int, species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> float:
    """Starters per delivered pound at a probe herd. Falls as birds get heavier.

    Quail is not scale-free: breeders are a fixed keep, and kit cages bind.
    N0_required searches the order. This ratio is only the probe.
    """
    probe = 400.0 if species == "quail" else PROBE
    produced = safe_lb(probe, month, species, reliability, n_paths, seed)
    if produced <= 1e-9:
        return float("inf")
    return probe / produced


def _quail_n0_row(q_lb: float, month: int, quantile: float, n_paths: int, profile: dict, keep: int) -> dict:
    """Search starters. Pounds are sex- and age-specific dressed weights, not one lb/bird."""
    week = engine.weeks_for_month(month) - 1
    paths = _quail_paths(n_paths)
    base = {
        "species": "quail",
        "month": month,
        "q_lb": q_lb,
        "reliability": quantile,
        "genetics_floor": keep,
        "stage": profile["stage"],
        "growth_tag": profile["growth_tag"],
        "genetics_mode": "strict",
        "flat_lb_retired": (13.0 / 16.0) * 0.72,
    }
    if week < bird_mc.HARVEST_WEEK - 1:
        base.update(
            {
                "birds_per_lb": None,
                "birds_per_lb_with_floor": None,
                "growth_only_n0": None,
                "n0": None,
                "safe_lb": 0.0,
                "remaining_lb": 0.0,
                "feasible": False,
                "fail_closed": True,
                "floor_binds": False,
                "U": None,
                "message": "No dressed meat before week 8 of life. Month 1 is inside that window.",
            }
        )
        return base

    found = bird_mc.n0_for_harvest({week: float(q_lb)}, week + 1, paths, quantile)
    if not found.get("feasible") or found.get("n0") is None:
        base.update(
            {
                "birds_per_lb": None,
                "birds_per_lb_with_floor": None,
                "growth_only_n0": None,
                "n0": None,
                "safe_lb": 0.0,
                "remaining_lb": 0.0,
                "feasible": False,
                "fail_closed": True,
                "floor_binds": False,
                "U": found.get("U"),
                "message": found.get("message") or "No starter flock inside the cap clears this pound on the harsh tail.",
            }
        )
        return base
    n0 = int(found["n0"])
    safe = float(q_lb) + float(found.get("leftover_p10") or 0.0)
    base.update(
        {
            "birds_per_lb": n0 / float(q_lb),
            "birds_per_lb_with_floor": n0 / float(q_lb),
            "growth_only_n0": n0,
            "n0": float(n0),
            "safe_lb": safe,
            "remaining_lb": float(found.get("leftover_p10") or 0.0),
            "feasible": True,
            "fail_closed": False,
            "floor_binds": n0 <= keep,
            "U": found.get("U"),
            "kit_list_usd": found.get("kit_list_usd"),
        }
    )
    return base


def n0_required(q_lb: float, month: int, species: str = "quail", reliability: float = engine.DEFAULT_QUANTILE, n_paths: int = engine.DEFAULT_PATHS, seed: int = engine.DEFAULT_SEED) -> dict:
    """Smallest starting herd that can deliver q_lb at month T and still keep breeders."""
    if q_lb <= 0:
        raise ValueError("q_lb must be > 0")
    profile = _profile(species)
    quantile = engine.planning_quantile(reliability)
    keep = keep_headcount(species)
    if species == "quail":
        return _quail_n0_row(q_lb, month, quantile, n_paths, profile, keep)
    per_lb = birds_per_lb(month, species, quantile, n_paths, seed)
    growth_n0 = q_lb * per_lb
    n0 = max(float(keep), growth_n0)
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
    """Smallest N0 that can meet every lot on the harsh tail and still keep breeders."""
    if not lots or any(qty <= 0 for _, qty in lots):
        raise ValueError("lots must be positive")
    quantile = engine.planning_quantile(reliability)
    profile = _profile(species)
    keep = float(keep_headcount(species))
    if species == "quail":
        harvest: dict[int, float] = {}
        weeks = 1
        for month, qty in lots:
            week = engine.weeks_for_month(month) - 1
            harvest[week] = harvest.get(week, 0.0) + float(qty)
            weeks = max(weeks, week + 1)
        found = bird_mc.n0_for_harvest(harvest, weeks, _quail_paths(n_paths), quantile)
        n0 = found.get("n0")
        feasible = bool(found.get("feasible")) and n0 is not None and float(n0) <= N0_CAP
        row = _schedule_result(
            lots,
            float(n0) if n0 is not None else float(bird_mc.N0_CAP),
            feasible,
            float(found.get("leftover_p10") or 0.0),
            profile,
            keep,
            quantile,
        )
        row["U"] = found.get("U")
        row["kit_list_usd"] = found.get("kit_list_usd")
        row["fail_closed"] = not feasible
        if not feasible:
            row["message"] = found.get("message") or "Stop. This delivery cannot be dressed without the breeding flock."
        return row
    clear = engine.clear_fraction(quantile)
    model = _model(species)
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
    n0s = [row.get("n0") for row in table]
    table_falls = (
        len(n0s) >= 2
        and all(n is not None for n in n0s)
        and n0s[0] > n0s[-1] + 1e-9
    )
    formula = (
        "Quail: N0 is the smallest 1:3 flock whose harsh-tail dressed pounds "
        "(sum of sex- and age-specific weights) cover the order. Breeders stay. "
        "A flat 0.585 lb/bird is retired. Fish still uses the logistic stub."
        if species == "quail"
        else (
            "birds_per_lb(T) = N_probe / Q_P10(N_probe, T); "
            "N0(Q, T) = max(N_keep, Q * birds_per_lb(T)); "
            "Q_P10 is the harsh lower tail; N_keep is the strict Ne floor"
        )
    )
    return {
        "species": species,
        "reliability": reliability,
        "qty_lb": qty,
        "table": table,
        "birds_per_lb_falls_with_T": table_falls,
        "recommendation": rec,
        "formula": formula,
        "stage_gate": "Planning only. Stage 1 worms remain the only active spend. No Stage 2-5 CapEx.",
    }


def smoke(path: Path | None = None) -> dict:
    table = [n0_required(10, month, "quail", 0.10) for month in (3, 6, 12)]
    assert all(row["feasible"] for row in table)
    assert table[0]["n0"] > table[-1]["n0"]
    assert all(table[i]["n0"] + 1e-6 >= table[i + 1]["n0"] for i in range(len(table) - 1))

    one = plan_request({"species": "quail", "qty_lb": 10, "months": [3, 6, 12], "reliability": 0.10})
    assert one["birds_per_lb_falls_with_T"]
    assert one["recommendation"]["feasible"]
    assert one["recommendation"]["recommended"]["n0"] <= one["recommendation"]["all_soon"]["n0"] + 1e-6

    big = plan_request({"species": "quail", "qty_lb": 40, "months": [3, 6, 12], "reliability": 0.10})
    by_month = {row["month"]: row for row in big["table"]}
    assert by_month[3]["n0"] > by_month[12]["n0"]
    assert big["recommendation"]["recommended"]["n0"] + 1e-6 <= big["recommendation"]["all_soon"]["n0"]

    split = recommend(
        [
            {"qty_lb": 15, "earliest_month": 3, "latest_month": 3},
            {"qty_lb": 15, "earliest_month": 3, "latest_month": 12},
        ],
        "quail",
        0.10,
    )
    assert split["feasible"]
    assert split["recommended"]["n0"] + 1e-6 <= split["all_soon"]["n0"]
    assert any(lot["month"] >= 3 for lot in split["recommended"]["lots"])

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

    per_lb = [row["birds_per_lb"] for row in table]
    payload = {
        "ok": True,
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
