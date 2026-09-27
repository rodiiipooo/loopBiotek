#!/usr/bin/env python3
"""Individual jumbo Coturnix Monte Carlo. Planning only.

Each path keeps a count of birds at each week of age and each sex. That is
the individual draw: every bird of that age and sex faces the same weekly
hazard, and hatch sex is a separate draw. Meat is the sum of dressed weights
of the birds actually removed.

Stage 4 planning. Stage 1 worms remain the only spend. Kit price times U is
a planning total, not a purchase.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

QUAIL = Path(__file__).resolve().parent
OPS = QUAIL.parent / "ops-dashboard"
GEN = QUAIL.parent / "genetics"
for folder in (QUAIL, OPS, GEN):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import engine  # noqa: E402
import reproduction as genetics  # noqa: E402

SEED = engine.DEFAULT_SEED
# Fewer paths than the worm screen. Same P10 rule: 90% of futures must clear.
PATHS = 48
MAX_AGE = 80
# Named peak. Lay onset 6–8 weeks is sourced in RESEARCH.md. The peak week is not.
PEAK_EGG_WEEK = 12  # ASSUMPTION: eggs/hen/week peaks at week 12 of life
MATURITY_WEEK = 7  # ASSUMPTION mid of the 6–8 week onset
HARVEST_WEEK = 8  # ASSUMPTION start of the 8–10 week jumbo meat window
HATCH_RATE = 0.75  # ASSUMPTION mid of the 0.625–0.925 band
# Hatch sex is about even. The 1♂:3♀ ratio is who we keep, not who hatches.
HATCH_FEMALE = 0.50  # ASSUMPTION
INCUBATION_WEEKS = 3  # ASSUMPTION rounding of 17–18 days up to a whole week
EGGS_PER_HEN_YEAR = 280.0  # SOURCED range 200–300; peak week uses 280/52
# Live weight asymptotes sit inside the 12–14 oz jumbo band. Sex split is assumed.
MALE_LIVE_OZ = 12.0  # ASSUMPTION
FEMALE_LIVE_OZ = 14.0  # ASSUMPTION
MALE_DRESS = 0.74  # ASSUMPTION inside 70–75%
FEMALE_DRESS = 0.70  # ASSUMPTION inside 70–75%
# Weekly hazard rises with age. First week is higher. Not a published life table.
HAZARD_WEEK0 = 0.02  # ASSUMPTION
HAZARD_BASE = 0.004  # ASSUMPTION
HAZARD_SLOPE = 0.00018  # ASSUMPTION per week of life
# Hold this share above the Ne floor so one week's deaths do not sell the breeders.
BREEDER_PAD = 0.25  # ASSUMPTION

# Mother Earth News kit page, fetched 2026-09-26. Same SKU as the Grit listing.
# https://store.motherearthnews.com/products/quail-professional-kit?variant=46564622795007
KIT_URL = (
    "https://store.motherearthnews.com/products/quail-professional-kit"
    "?currency=USD&country=US&variant=46564622795007"
)
KIT_LIST_USD = 3729.96  # SOURCED list price on that page
KIT_SALE_USD = 3449.99  # SOURCED earlier Grit sale price; not on the MEN list line
KIT_EGGS_PER_BATCH = 216  # SOURCED on the MEN/Grit getting-started steps
# Standing caps. Brooder and the 3-per-section breeder line are prior sourced notes.
# The MEN page does not restate headcounts. Grow-out jumbo is still an assumption.
BROODER_HEADS = 150  # SOURCED Hatching Time CB25-03-5K, not restated on the MEN page
GROWOUT_HEADS = 75  # ASSUMPTION jumbo derate
BREEDER_HEADS = 45  # SOURCED 3 jumbo per section × 15 sections
# Leave headroom so a noisy hatch does not overflow the grow-out cage.
CHICK_FILL = 0.80  # ASSUMPTION
# Physical sum of the three housings. The binding check is per compartment.
BIRDS_PER_KIT = BROODER_HEADS + GROWOUT_HEADS + BREEDER_HEADS
# No egg cooler is listed. ASSUMPTION: one setter load can sit for the week.
EGG_STORE_PER_KIT = KIT_EGGS_PER_BATCH
EGGS_SET_PER_WEEK = KIT_EGGS_PER_BATCH * (7.0 / 17.5)
# The kit has no meat cooler. Harvest is assumed to leave the same week.
COLD_LB_PER_KIT = None

N0_CAP = 4000
HORIZON = 24


def keep_counts() -> tuple[int, int]:
    floor = genetics.keep_floor(1, None, None, 3.0)
    return int(floor["males_min"]), int(floor["females_min"])


def hazard(age: int) -> float:
    if age <= 0:
        return HAZARD_WEEK0
    return min(0.08, HAZARD_BASE + HAZARD_SLOPE * age)


def survival_to(age: int) -> float:
    """Share of birds still alive at the start of this week. Deterministic schedule."""
    live = 1.0
    for week in range(age):
        live *= 1.0 - hazard(week)
    return live


def eggs_per_hen_week(age: int) -> float:
    """Zero before maturity, rising to week PEAK_EGG_WEEK, then declining."""
    if age < MATURITY_WEEK:
        return 0.0
    peak = EGGS_PER_HEN_YEAR / 52.0
    if age <= PEAK_EGG_WEEK:
        span = PEAK_EGG_WEEK - (MATURITY_WEEK - 1)
        return peak * (age - (MATURITY_WEEK - 1)) / span
    return peak * math.exp(-0.025 * (age - PEAK_EGG_WEEK))


def live_oz(sex: str, age: int) -> float:
    """Logistic live weight. ASSUMPTION shape. Asymptotes are the jumbo band."""
    ceiling = FEMALE_LIVE_OZ if sex == "F" else MALE_LIVE_OZ
    return ceiling / (1.0 + math.exp(-0.70 * (age - 5.0)))


def dressed_lb(sex: str, age: int) -> float:
    """Pounds of meat if this bird is harvested. Zero before the meat window."""
    if age < HARVEST_WEEK:
        return 0.0
    dress = FEMALE_DRESS if sex == "F" else MALE_DRESS
    return live_oz(sex, age) / 16.0 * dress


def _binom(rng: random.Random, n: int, p: float) -> int:
    n = int(n)
    if n <= 0 or p <= 0.0:
        return 0
    if p >= 1.0:
        return n
    if n >= 30:
        draw = int(round(rng.gauss(n * p, math.sqrt(n * p * (1.0 - p)))))
        return max(0, min(n, draw))
    return sum(1 for _ in range(n) if rng.random() < p)


def _count(rng: random.Random, mean: float) -> int:
    if mean <= 0:
        return 0
    draw = int(round(rng.gauss(mean, math.sqrt(mean))))
    return max(0, draw)


def kits_for_standing(n0: int) -> int:
    """Smallest U whose compartments can hold the purchased cohort before offspring."""
    bro = math.ceil(n0 / BROODER_HEADS)
    grow = math.ceil(n0 / GROWOUT_HEADS)
    breed = math.ceil(sum(keep_counts()) / BREEDER_HEADS)
    return max(1, bro, grow, breed)


def _shift_survive(rng: random.Random, counts: list[int]) -> list[int]:
    nxt = [0] * (MAX_AGE + 1)
    for age, n in enumerate(counts):
        if n <= 0 or age >= MAX_AGE:
            continue
        nxt[age + 1] = _binom(rng, n, 1.0 - hazard(age))
    return nxt


def _hold_counts() -> tuple[int, int]:
    """Birds the harvest will not take. A pad above the Ne floor is an assumption."""
    keep_m, keep_f = keep_counts()
    return (
        int(math.ceil(keep_m * (1.0 + BREEDER_PAD))),
        int(math.ceil(keep_f * (1.0 + BREEDER_PAD))),
    )


def _protected(counts: list[int], hold: int) -> list[int]:
    """Keep the youngest adults. Older birds are the ones sold."""
    protected = [0] * (MAX_AGE + 1)
    left = hold
    for age in range(HARVEST_WEEK, MAX_AGE + 1):
        if left <= 0:
            break
        take = min(counts[age], left)
        protected[age] = take
        left -= take
    return protected


def _free_dressed(males: list[int], females: list[int], keep_m: int, keep_f: int) -> float:
    """Dressed pounds still standing above the birds we will not sell."""
    del keep_m, keep_f
    hold_m, hold_f = _hold_counts()
    prot_m = _protected(males, hold_m)
    prot_f = _protected(females, hold_f)
    got = 0.0
    for age in range(MAX_AGE, HARVEST_WEEK - 1, -1):
        for sex, counts, prot in (("M", males, prot_m), ("F", females, prot_f)):
            weight = dressed_lb(sex, age)
            free = counts[age] - prot[age]
            if weight > 0 and free > 0:
                got += free * weight
    return got


def _take_free(males: list[int], females: list[int], limit: float, by_heads: bool) -> float:
    """Sell oldest free birds. Returns dressed pounds. Limit is heads or pounds."""
    hold_m, hold_f = _hold_counts()
    prot_m = _protected(males, hold_m)
    prot_f = _protected(females, hold_f)
    got_lb = 0.0
    got_n = 0
    for age in range(MAX_AGE, HARVEST_WEEK - 1, -1):
        for sex, counts, prot in (("M", males, prot_m), ("F", females, prot_f)):
            weight = dressed_lb(sex, age)
            free = counts[age] - prot[age]
            if weight <= 0 or free <= 0:
                continue
            if by_heads:
                if got_n >= limit:
                    return got_lb
                take = min(free, int(limit - got_n))
            else:
                if got_lb + 1e-9 >= limit:
                    return got_lb
                take = min(free, int(math.ceil((limit - got_lb) / weight)))
            counts[age] -= take
            got_n += take
            got_lb += take * weight
    return got_lb


def _harvest(males: list[int], females: list[int], need_lb: float, keep_m: int, keep_f: int) -> float:
    """Remove older birds first until the pound target is met. Youngest adults stay."""
    del keep_m, keep_f
    return _take_free(males, females, need_lb, False)


def run_path(
    rng: random.Random,
    n0: int,
    harvest_lb: dict[int, float],
    weeks: int,
    U: int,
) -> dict:
    keep_m, keep_f = keep_counts()
    males = [0] * (MAX_AGE + 1)
    females = [0] * (MAX_AGE + 1)
    n_m = int(round(n0 / 4.0))
    n_f = int(n0) - n_m
    males[0] = n_m
    females[0] = n_f
    incubating: list[list[int]] = []
    meat = []
    unstored = []
    housed = True
    breeders_ok = True
    egg_overflow = 0
    eggs_unset = 0
    standing_week: list[int] = []
    peaks = {"brooder": 0, "grow": 0, "breed": 0, "standing": 0}
    weekly_chick_slots = CHICK_FILL * min(U * BROODER_HEADS / 4.0, U * GROWOUT_HEADS / 4.0)
    set_cap = min(int(U * EGGS_SET_PER_WEEK), int(weekly_chick_slots / HATCH_RATE))
    store_cap = int(U * EGG_STORE_PER_KIT)
    for week in range(weeks):
        males = _shift_survive(rng, males)
        females = _shift_survive(rng, females)
        eggs = 0
        for age in range(MATURITY_WEEK, MAX_AGE + 1):
            rate = eggs_per_hen_week(age)
            if females[age] and rate > 0:
                eggs += _count(rng, females[age] * rate)
        store_kept = min(eggs, store_cap)
        egg_overflow += max(0, eggs - store_kept)
        set_n = min(store_kept, set_cap)
        eggs_unset += store_kept - set_n
        incubating.append([INCUBATION_WEEKS, set_n])
        hatched_from = 0
        still = []
        for left, n_eggs in incubating:
            left -= 1
            if left <= 0:
                hatched_from += n_eggs
            else:
                still.append([left, n_eggs])
        incubating = still
        chicks = _binom(rng, hatched_from, HATCH_RATE)
        fem = _binom(rng, chicks, HATCH_FEMALE)
        females[0] += fem
        males[0] += chicks - fem
        bro = sum(males[a] + females[a] for a in range(0, 4))
        grow_young = sum(males[a] + females[a] for a in range(4, HARVEST_WEEK))
        adult_m = sum(males[a] for a in range(HARVEST_WEEK, MAX_AGE + 1))
        adult_f = sum(females[a] for a in range(HARVEST_WEEK, MAX_AGE + 1))
        breed_m = min(keep_m, adult_m)
        breed_f = min(keep_f, adult_f)
        meat_adults = (adult_m - breed_m) + (adult_f - breed_f)
        grow_occ = grow_young + meat_adults
        breed_occ = breed_m + breed_f
        standing = bro + grow_young + adult_m + adult_f
        peaks["brooder"] = max(peaks["brooder"], bro)
        peaks["grow"] = max(peaks["grow"], grow_occ)
        peaks["breed"] = max(peaks["breed"], breed_occ)
        peaks["standing"] = max(peaks["standing"], standing)
        standing_week.append(standing)
        need = float(harvest_lb.get(week, 0.0))
        spilled = 0.0
        got = 0.0
        cap_grow = U * GROWOUT_HEADS
        if grow_occ > cap_grow:
            # Only the birds that do not fit leave. The kit has no meat cooler.
            processed = _take_free(males, females, grow_occ - cap_grow, True)
            got = min(processed, need)
            spilled = max(0.0, processed - need)
            grow_young = sum(males[a] + females[a] for a in range(4, HARVEST_WEEK))
            adult_m = sum(males[a] for a in range(HARVEST_WEEK, MAX_AGE + 1))
            adult_f = sum(females[a] for a in range(HARVEST_WEEK, MAX_AGE + 1))
            grow_occ = grow_young + max(0, adult_m - keep_m) + max(0, adult_f - keep_f)
            if grow_occ > cap_grow or bro > U * BROODER_HEADS:
                housed = False
        if need > got:
            got += _harvest(males, females, need - got, keep_m, keep_f)
        if bro > U * BROODER_HEADS or breed_occ > U * BREEDER_HEADS:
            housed = False
        meat.append(got)
        unstored.append(spilled)
        if week + 1 >= HARVEST_WEEK:
            now_m = sum(males[a] for a in range(HARVEST_WEEK, MAX_AGE + 1))
            now_f = sum(females[a] for a in range(HARVEST_WEEK, MAX_AGE + 1))
            if now_m < keep_m or now_f < keep_f:
                breeders_ok = False
    return {
        "meat": meat,
        "unstored_lb": unstored,
        "housed": housed,
        "breeders_ok": breeders_ok,
        "egg_overflow": egg_overflow,
        "eggs_unset": eggs_unset,
        "peaks": peaks,
        "standing_week": standing_week,
        "leftover_lb": _free_dressed(males, females, keep_m, keep_f),
        "standing_end": sum(males) + sum(females),
    }


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    idx = min(len(ordered) - 1, max(0, int(math.floor(q * (len(ordered) - 1)))))
    return ordered[idx]


_SIM_CACHE: dict[tuple, dict] = {}


def _harvest_key(harvest_lb: dict[int, float]) -> tuple:
    return tuple(sorted((int(week), round(float(need), 4)) for week, need in harvest_lb.items()))


def simulate(
    n0: int,
    harvest_lb: dict[int, float],
    weeks: int,
    U: int | None = None,
    n_paths: int = PATHS,
    seed: int = SEED,
) -> dict:
    n0 = int(n0)
    U = kits_for_standing(n0) if U is None else int(U)
    key = (n0, _harvest_key(harvest_lb), int(weeks), U, int(n_paths), int(seed))
    cached = _SIM_CACHE.get(key)
    if cached is not None:
        return cached
    rows = []
    for i in range(n_paths):
        rng = random.Random(seed + i * 10007 + n0 * 17)
        rows.append(run_path(rng, n0, harvest_lb, weeks, U))
    result = {"n0": n0, "U": U, "paths": rows, "weeks": weeks}
    _SIM_CACHE[key] = result
    return result


def surplus_lb(n0: int, month: int, quantile: float = engine.DEFAULT_QUANTILE, n_paths: int = PATHS, U: int | None = None) -> dict:
    """Dressed pounds if every legal meat bird is taken at month T. Breeders stay.

    The quantile is the harsh lower tail (default 0.10). A path that overflows
    a kit or loses the breeding floor contributes zero.
    """
    q = engine.planning_quantile(quantile)
    week = engine.weeks_for_month(month) - 1
    huge = {week: 1.0e9}
    sim = simulate(n0, huge, week + 1, U, n_paths)
    pounds = []
    housed = 0
    for row in sim["paths"]:
        if row["housed"] and row["breeders_ok"]:
            housed += 1
            pounds.append(row["meat"][week] + row["unstored_lb"][week])
        else:
            pounds.append(0.0)
    return {
        "n0": n0,
        "U": sim["U"],
        "month": month,
        "quantile": q,
        "q_lb": _percentile(pounds, q),
        "p50_lb": _percentile(pounds, 0.50),
        "housed_paths": housed,
        "paths": n_paths,
    }


def p10_meat(n0: int, month: int, n_paths: int = PATHS, U: int | None = None) -> dict:
    """10th percentile dressed pounds from one harvest at month T. Breeders stay."""
    row = surplus_lb(n0, month, engine.DEFAULT_QUANTILE, n_paths, U)
    row["p10_lb"] = row["q_lb"]
    return row


def clears(n0: int, harvest_lb: dict[int, float], weeks: int, U: int | None = None, n_paths: int = PATHS, quantile: float = engine.DEFAULT_QUANTILE) -> dict:
    sim = simulate(n0, harvest_lb, weeks, U, n_paths)
    ok = 0
    overflow = []
    peaks = []
    for row in sim["paths"]:
        short = any(
            row["meat"][week] + 1e-6 < need
            for week, need in harvest_lb.items()
            if need > 0 and week < weeks
        )
        good = row["housed"] and row["breeders_ok"] and not short
        if good:
            ok += 1
        overflow.append(row["egg_overflow"])
        peaks.append(row["peaks"])
    q = engine.planning_quantile(quantile)
    rate = ok / n_paths if n_paths else 0.0
    housed_fail = sum(1 for row in sim["paths"] if not row["housed"]) / n_paths if n_paths else 1.0
    unset = [row["eggs_unset"] for row in sim["paths"]]
    unstored = [sum(row["unstored_lb"]) for row in sim["paths"]]
    leftover = [row["leftover_lb"] if row["housed"] and row["breeders_ok"] else 0.0 for row in sim["paths"]]
    heavy = peaks[int(0.9 * (len(peaks) - 1))] if peaks else {}
    return {
        "n0": sim["n0"],
        "U": sim["U"],
        "clear_rate": rate,
        "clears_p10": rate + 1e-12 >= engine.clear_fraction(q),
        "quantile": q,
        "housing_fail_rate": housed_fail,
        "egg_overflow_p50": _percentile(overflow, 0.50),
        "unset_p50": _percentile(unset, 0.50),
        "unstored_p50": _percentile(unstored, 0.50),
        "leftover_p10": _percentile(leftover, engine.DEFAULT_QUANTILE),
        "peak_example": heavy,
        "kit_list_usd": sim["U"] * KIT_LIST_USD,
        "capex_note": "Planning total only. Stage 1 worms remain the only spend. Do not buy kits.",
    }


def _month_harvest(dollars_by_month: dict[int, float]) -> tuple[dict[int, float], int]:
    harvest: dict[int, float] = {}
    last = 1
    for month, dollars in dollars_by_month.items():
        price = float(engine.price_quote("quail", int(month))["F_prelim"])
        week = engine.weeks_for_month(int(month)) - 1
        harvest[week] = harvest.get(week, 0.0) + (dollars / price if price > 0 else 0.0)
        last = max(last, week + 1)
    return harvest, last


def _too_young(harvest: dict[int, float], weeks: int) -> bool:
    """A lot before the meat window cannot be dressed."""
    return any(0 < need and week < HARVEST_WEEK - 1 for week, need in harvest.items() if week < weeks)


def _one_cohort_short(harvest: dict[int, float], weeks: int) -> bool:
    """Pounds demanded before offspring can be dressed, versus one purchased flock at the cap."""
    first_offspring = 17  # lay ~week 6, hatch +3, dress +8
    early = sum(need for week, need in harvest.items() if week < min(weeks, first_offspring))
    cap = N0_CAP * dressed_lb("F", 16) * survival_to(16)
    return early > cap


def _fit(n0: int, harvest: dict[int, float], weeks: int, n_paths: int, quantile: float = engine.DEFAULT_QUANTILE) -> dict:
    """Smallest U that houses this flock. More kits only when eggs are unset or a cage overflows."""
    if _too_young(harvest, weeks) or _one_cohort_short(harvest, weeks):
        return {
            "n0": int(n0),
            "U": kits_for_standing(n0),
            "clear_rate": 0.0,
            "clears_p10": False,
            "housing_fail_rate": 0.0,
            "unset_p50": 0.0,
            "feasible": False,
            "fail_closed": True,
            "message": (
                "This schedule asks for dressed meat before birds reach the harvest window, "
                "or it sells one purchased cohort more than once."
            ),
        }
    U = kits_for_standing(n0)
    last = None
    gap = 1.0 - engine.clear_fraction(engine.DEFAULT_QUANTILE)
    later_meat = any(week >= 17 and need > 0 for week, need in harvest.items())
    worked = None
    for _ in range(8):
        last = clears(n0, harvest, weeks, U, n_paths, quantile)
        if last["clears_p10"]:
            worked = last
            break
        # Spare eggs matter only after offspring can be dressed. A week-8 lump does not.
        needs_shell = last["housing_fail_rate"] > gap or (later_meat and last["unset_p50"] > 1.0)
        if not needs_shell:
            return last
        nxt = min(36, max(U + 1, int(math.ceil(U * 1.4))))
        if nxt <= U:
            return last
        U = nxt
    if worked is None:
        return last
    lo = kits_for_standing(n0)
    hi = worked["U"]
    while lo < hi:
        mid = (lo + hi) // 2
        trial = clears(n0, harvest, weeks, mid, n_paths, quantile)
        if trial["clears_p10"]:
            hi = mid
            worked = trial
        else:
            lo = mid + 1
    return worked


def n0_for_harvest(harvest: dict[int, float], weeks: int, n_paths: int = PATHS, quantile: float = engine.DEFAULT_QUANTILE) -> dict:
    """Smallest 1:3 starter flock whose P10 paths clear this pound schedule."""
    keep = sum(keep_counts())
    if _too_young(harvest, weeks) or _one_cohort_short(harvest, weeks):
        return {
            "n0": None,
            "U": None,
            "feasible": False,
            "fail_closed": True,
            "message": (
                "This schedule asks for dressed meat before birds reach the harvest window, "
                "or it sells one purchased cohort more than once."
            ),
        }

    def ok(n0: int) -> dict:
        return _fit(n0, harvest, weeks, n_paths, quantile)

    lo = keep
    trial = ok(lo)
    if trial["clears_p10"]:
        trial["feasible"] = True
        trial["fail_closed"] = False
        return trial
    hi = lo
    found = None
    while hi < N0_CAP:
        hi = min(N0_CAP, hi + max(16, hi // 2))
        trial = ok(hi)
        if trial["clears_p10"]:
            found = trial
            break
        lo = hi
    if found is None:
        return {
            "n0": None,
            "U": None,
            "feasible": False,
            "fail_closed": True,
            "message": "No starter flock inside the cap clears this schedule on the P10 tail without taking breeders or overflowing a kit.",
        }
    for _ in range(12):
        if hi - lo <= 4:
            break
        mid = (lo + hi) // 2
        mid -= mid % 4
        trial = ok(mid)
        if trial["clears_p10"]:
            hi = mid
            found = trial
        else:
            lo = mid
    found = ok(hi)
    found["feasible"] = bool(found["clears_p10"])
    found["fail_closed"] = not found["feasible"]
    return found


def n0_for_dollars(dollars_by_month: dict[int, float], n_paths: int = PATHS) -> dict:
    """Smallest 1:3 starter flock whose P10 paths clear every named month."""
    harvest, weeks = _month_harvest(dollars_by_month)
    return n0_for_harvest(harvest, weeks, n_paths)


def binding_kit(peaks: dict, U: int) -> str:
    """Which compartment is closest to its cap."""
    ratios = {
        "brooder": peaks.get("brooder", 0) / (U * BROODER_HEADS),
        "grow-out": peaks.get("grow", 0) / (U * GROWOUT_HEADS),
        "breeder cage": peaks.get("breed", 0) / (U * BREEDER_HEADS),
    }
    name = max(ratios, key=ratios.get)
    return f"{name} at {ratios[name]:.0%} of U×cap"


def standing_by_month(n0: int, harvest_lb: dict[int, float], weeks: int, U: int, n_paths: int = PATHS) -> list[dict]:
    """Standing birds at each month end, before that week's harvest."""
    sim = simulate(n0, harvest_lb, weeks, U, n_paths)
    rows = []
    for month in range(1, HORIZON + 1):
        week = engine.weeks_for_month(month) - 1
        if week >= weeks:
            break
        vals = []
        for row in sim["paths"]:
            if row["housed"] and week < len(row["standing_week"]):
                vals.append(float(row["standing_week"][week]))
            else:
                vals.append(0.0)
        rows.append(
            {
                "month": month,
                "herd_p10": _percentile(vals, engine.DEFAULT_QUANTILE),
                "herd_heavy": _percentile(vals, 1.0 - engine.DEFAULT_QUANTILE),
            }
        )
    return rows


def income_cases(n_paths: int = PATHS) -> dict:
    """$1,000 at about 60 days, and $2,000 a month from month 2."""
    price2 = float(engine.price_quote("quail", 2)["F_prelim"])
    lump = n0_for_dollars({2: 1000.0}, n_paths)
    monthly = {month: 2000.0 for month in range(2, HORIZON + 1)}
    sustain = n0_for_dollars(monthly, n_paths)
    earliest = None
    if not sustain["feasible"]:
        for start in range(2, 10):
            trial_months = {month: 2000.0 for month in range(start, min(HORIZON, start + 6) + 1)}
            trial = n0_for_dollars(trial_months, n_paths)
            if trial["feasible"]:
                earliest = {"first_month": start, **trial}
                break
    return {
        "flat_lb_retired": (13.0 / 16.0) * 0.72,
        "f_prelim_month_2": price2,
        "lb_for_1000": 1000.0 / price2,
        "lump_1000_month_2": lump,
        "sustain_2000_from_month_2": sustain,
        "earliest_2000_window": earliest,
        "birds_per_kit": BIRDS_PER_KIT,
        "breeder_per_kit": BREEDER_HEADS,
        "growout_per_kit": GROWOUT_HEADS,
        "brooder_per_kit": BROODER_HEADS,
        "peak_egg_week": PEAK_EGG_WEEK,
        "dressed_lb_week_9": {
            "male": round(dressed_lb("M", 9), 4),
            "female": round(dressed_lb("F", 9), 4),
        },
    }


def write_schedule_plots(folder: Path) -> list[Path]:
    """Egg rate and survival versus age. These curves are the schedules, not a random path."""
    folder.mkdir(parents=True, exist_ok=True)
    ages = list(range(0, 61))
    eggs = [eggs_per_hen_week(age) for age in ages]
    live = [survival_to(age) for age in ages]
    male_lb = [dressed_lb("M", age) for age in ages]
    female_lb = [dressed_lb("F", age) for age in ages]
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    egg_path = folder / "quail_egg_rate_vs_age.png"
    live_path = folder / "quail_survival_vs_age.png"
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.plot(ages, eggs, color="#9a3412", lw=2.2)
    ax.axvline(PEAK_EGG_WEEK, color="#5c564c", ls=":", lw=1)
    ax.scatter([PEAK_EGG_WEEK], [eggs_per_hen_week(PEAK_EGG_WEEK)], color="#9a3412", zorder=3)
    ax.set_xlabel("Age, weeks of life")
    ax.set_ylabel("Eggs per hen per week")
    ax.set_title(f"Hen egg rate. Peak week x = {PEAK_EGG_WEEK} (ASSUMPTION)")
    fig.text(0.01, 0.01, "Onset 6–8 weeks is sourced. The peak week and the decline slope are assumptions. Only females lay.", fontsize=8, color="#5c564c")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(egg_path, dpi=140)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.plot(ages, live, color="#1d4e89", lw=2.2, label="Survival")
    ax.plot(ages, male_lb, color="#1f6b45", lw=1.6, label="Male dressed lb")
    ax.plot(ages, female_lb, color="#9a3412", lw=1.6, label="Female dressed lb")
    ax.set_xlabel("Age, weeks of life")
    ax.set_ylabel("Share alive, or dressed pounds")
    ax.set_title("Survival and sex-specific dressed weight")
    ax.legend(frameon=False)
    fig.text(0.01, 0.01, "ASSUMPTION hazard (higher in week 0, then rising with age). ASSUMPTION sex weights inside the 12–14 oz jumbo band.", fontsize=8, color="#5c564c")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(live_path, dpi=140)
    plt.close(fig)
    return [egg_path, live_path]


def smoke(path: Path | None = None) -> dict:
    cases = income_cases()
    lump = cases["lump_1000_month_2"]
    sustain = cases["sustain_2000_from_month_2"]
    assert cases["dressed_lb_week_9"]["female"] > cases["dressed_lb_week_9"]["male"] > 0
    assert eggs_per_hen_week(PEAK_EGG_WEEK) > eggs_per_hen_week(MATURITY_WEEK)
    assert eggs_per_hen_week(40) < eggs_per_hen_week(PEAK_EGG_WEEK)
    assert survival_to(40) < survival_to(8) < 1
    if lump["feasible"]:
        assert lump["n0"] >= sum(keep_counts())
        assert lump["U"] >= 1
    plots = write_schedule_plots(QUAIL / "results")
    # Also drop copies where the gallery looks.
    gallery = QUAIL.parent / "plots"
    gallery.mkdir(parents=True, exist_ok=True)
    for plot in plots:
        target = gallery / plot.name
        target.write_bytes(plot.read_bytes())
    payload = {
        "ok": True,
        "stage": "Stage 4 planning. Stage 1 worms remain the only spend. Kit dollars are not a purchase.",
        "flat_lb_per_bird_retired": cases["flat_lb_retired"],
        "peak_egg_week": PEAK_EGG_WEEK,
        "birds_per_kit_sum": BIRDS_PER_KIT,
        "brooder_per_kit": BROODER_HEADS,
        "growout_per_kit": GROWOUT_HEADS,
        "breeder_per_kit": BREEDER_HEADS,
        "kit_list_usd": KIT_LIST_USD,
        "dressed_lb_week_9": cases["dressed_lb_week_9"],
        "lb_for_1000_at_month_2": cases["lb_for_1000"],
        "f_prelim_month_2": cases["f_prelim_month_2"],
        "lump_1000": {key: lump[key] for key in lump if key != "peak_example"},
        "sustain_2000": {key: sustain[key] for key in sustain if key != "peak_example"},
        "earliest_2000": None
        if cases["earliest_2000_window"] is None
        else {key: cases["earliest_2000_window"][key] for key in cases["earliest_2000_window"] if key != "peak_example"},
        "plots": [str(item) for item in plots],
    }
    if lump.get("peak_example") and lump.get("U"):
        payload["lump_binding"] = binding_kit(lump["peak_example"], lump["U"])
    out = path or QUAIL / "results" / "bird_mc_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["smoke_path"] = str(out)
    return payload


if __name__ == "__main__":
    result = smoke()
    lump = result["lump_1000"]
    sustain = result["sustain_2000"]
    print(
        f"flat lb retired={result['flat_lb_per_bird_retired']:.4f}  "
        f"week9 male={result['dressed_lb_week_9']['male']}  female={result['dressed_lb_week_9']['female']}"
    )
    print(
        f"$1000 month2 feasible={lump.get('feasible')} N0={lump.get('n0')} U={lump.get('U')} "
        f"list=${lump.get('kit_list_usd')}"
    )
    print(f"$2000/mo from month2 feasible={sustain.get('feasible')} N0={sustain.get('n0')} U={sustain.get('U')}")
    print("earliest", result["earliest_2000"])
    print("binding", result.get("lump_binding"))
