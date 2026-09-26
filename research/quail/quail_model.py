#!/usr/bin/env python3
"""
Loop Biotek — Jumbo Coturnix japonica planning model.

STAGE GATE: Quail is Stage 4 in the bio cascade. Stage 1 is worms.
This module is planning math only — do not open quail spend until Stage-1 gate.

Capacity unit: Grit "Quail Professional Kit" (U = number of kits).
Core inverse: kits_needed(X, t, y, z) s.t. meat_lbs(t,y,z,U) >= X under kit caps.

Also: P_meat(t) competing forward $/lb; fair prepaid F_0 = E[P_comp]/(1+r_prime)^T.

Tags: SOURCED vs ASSUMPTION — see SPEC.md. No fabricated Admin-analytics labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Union
import math

DAYS_PER_YEAR = 365.25
DAYS_PER_WEEK = 7.0

# ---------------------------------------------------------------------------
# Jumbo Coturnix biology (defaults). Standard small Coturnix kept only as notes.
# ---------------------------------------------------------------------------

EGGS_PER_HEN_PER_YEAR = 280.0  # SOURCED range 200–300 (hobby/commercial Coturnix; jumbo similar)
HATCH_RATE = 0.75  # ASSUMPTION mid of reported 62.5–92.5% hatchability band
SEX_RATIO_FEMALE = 0.50  # ASSUMPTION ~1:1
INCUBATION_DAYS = 17.5  # SOURCED 17–18 days
MATURITY_DAYS = 49.0  # ASSUMPTION mid of 6–8 weeks to lay (jumbo)
SLAUGHTER_DAYS = 63.0  # ASSUMPTION mid of 8–10 weeks jumbo meat harvest window
LIVE_WEIGHT_OZ = 13.0  # ASSUMPTION mid of 12–14 oz jumbo finish (homestead/breeder guides)
DRESS_YIELD = 0.72  # ASSUMPTION mid of 70–75% dressed yield cites
DRESS_WEIGHT_LBS = (LIVE_WEIGHT_OZ / 16.0) * DRESS_YIELD  # ~0.585 lb ≈ 9.4 oz
WEEKLY_MORTALITY = 0.01  # ASSUMPTION ~1%/week; replace with farm data
BREEDER_MALES_PER_FEMALE = 1.0 / 3.0  # ASSUMPTION common ~1♂:3♀
MAX_BREEDER_AGE_DAYS = 365.0  # ASSUMPTION rotate ~1 year
# Fraction of chicks promoted into breeding slots at maturity (rest stay meat lane)
FRAC_FEMALE_TO_BREEDERS = 0.12  # ASSUMPTION
FRAC_MALE_TO_BREEDERS = 0.04  # ASSUMPTION

# Brood / grow age bands matching Grit kit narrative (weeks 0–4 brood, 4–6 grow;
# jumbo meat continues in grow-out until slaughter_days).
BROOD_DAYS = 28.0  # SOURCED kit copy: first 4 weeks brooding
GROW_START_DAYS = 28.0  # SOURCED kit: grow-out weeks 4–6+

# ---------------------------------------------------------------------------
# Grit Quail Professional Kit capacity (U kits)
# Source: https://store.grit.com/products/quail-professional-kit?variant=47213766246652
# Component capacities from same-SKU Cimuka/Hatching Time listings.
# ---------------------------------------------------------------------------

KIT_SKU = "QUAIL-PROKIT"
KIT_URL = "https://store.grit.com/products/quail-professional-kit?variant=47213766246652"
KIT_PRICE_USD = 3449.99  # SOURCED sale price on Grit page (list $3729.96)
KIT_INCUBATOR_EGGS_PER_BATCH = 216  # SOURCED kit page: CT120SH set/hatch up to 216 quail eggs
KIT_BROODER_HEADS = 150  # SOURCED Hatching Time CB25-03-5K: up to 150 quail
# Breeding cage BYK-03-5K: 75 standard / 15 per layer; larger birds 3 per section × 15 sections = 45
KIT_BREEDER_HEADS_STANDARD = 75  # SOURCED
KIT_BREEDER_HEADS_JUMBO = 45  # SOURCED (3 per section × 15 sections)
KIT_BREEDER_FOOTPRINT_IN = (38.6, 24.0, 77.2)  # SOURCED L×W×H inches (breeding cage)
# Grow-out GL25-03-5K: manufacturer does not publish a fixed headcount ("depends on breed").
# For jumbo teens we derate toward the breeding-cage larger-bird guidance.
KIT_GROWOUT_HEADS_JUMBO = 75  # ASSUMPTION (derated; mark clearly in SPEC)
KIT_GROWOUT_FOOTPRINT_IN = (36.3, 21.6, 77.2)  # SOURCED assembled dims (Gone Broody / HT family)

# Default binding capacity for this model = jumbo
KIT_BREEDER_HEADS = KIT_BREEDER_HEADS_JUMBO
KIT_GROWOUT_HEADS = KIT_GROWOUT_HEADS_JUMBO

# ---------------------------------------------------------------------------
# Economics
# ---------------------------------------------------------------------------

PRIME_RATE = 0.07  # SOURCED Fed H.15 bank prime 7.00% as of 2026-09-24 (release 2026-09-25)
PRIME_RATE_AS_OF = "2026-09-24"
PRIME_RATE_SOURCE = "https://www.federalreserve.gov/releases/h15/"

# Competing $/lb — whole-bird foodservice preferred for fair default.
# Dress weight jumbo ≈ 9.4 oz; foodservice comps often quote 4–5 oz standard birds —
# $/lb still comparable as price per pound of dressed meat.
COMP_PRICES_USD_PER_LB = (
    ("webstaurant_mf_whole_4_5oz_regular", 13.17, "foodservice", "sourced"),
    ("webstaurant_mf_whole_4_5oz_plus", 10.06, "foodservice_member", "sourced"),
    ("manchester_farms_case_4oz_approx", 14.16, "producer_case", "sourced"),
    ("dartagnan_semi_boneless_4x4oz", 31.99, "specialty_retail", "sourced"),
    ("blog_farm_raised_mid", 8.00, "retail_guide_blog", "candidate"),  # quarantine; excluded from default
)

DEFAULT_P_COMP_LABELS = (
    "webstaurant_mf_whole_4_5oz_regular",
    "webstaurant_mf_whole_4_5oz_plus",
    "manchester_farms_case_4oz_approx",
)
FORWARD_DRIFT_PER_YEAR = 0.0  # ASSUMPTION flat competing forward curve


@dataclass
class BiologyParams:
    eggs_per_hen_per_year: float = EGGS_PER_HEN_PER_YEAR
    hatch_rate: float = HATCH_RATE
    sex_ratio_female: float = SEX_RATIO_FEMALE
    incubation_days: float = INCUBATION_DAYS
    maturity_days: float = MATURITY_DAYS
    slaughter_days: float = SLAUGHTER_DAYS
    dress_weight_lbs: float = DRESS_WEIGHT_LBS
    weekly_mortality: float = WEEKLY_MORTALITY
    breeder_males_per_female: float = BREEDER_MALES_PER_FEMALE
    max_breeder_age_days: float = MAX_BREEDER_AGE_DAYS
    frac_female_to_breeders: float = FRAC_FEMALE_TO_BREEDERS
    frac_male_to_breeders: float = FRAC_MALE_TO_BREEDERS
    brood_days: float = BROOD_DAYS


@dataclass
class KitParams:
    """Per-kit capacities. Defaults = Grit Quail Professional Kit, jumbo stocking."""

    incub_eggs_per_batch: float = KIT_INCUBATOR_EGGS_PER_BATCH
    brooder_heads: float = KIT_BROODER_HEADS
    growout_heads: float = KIT_GROWOUT_HEADS
    breeder_heads: float = KIT_BREEDER_HEADS
    price_usd: float = KIT_PRICE_USD


@dataclass
class PopulationState:
    week: int
    day: float
    males_breeders: float
    females_breeders: float
    males_brood: float
    females_brood: float
    males_grow: float
    females_grow: float
    males_total: float
    females_total: float
    total: float
    eggs_set_this_week: float
    eggs_desired_this_week: float
    chicks_hatched_this_week: float
    birds_slaughtered_this_week: float
    meat_lbs_this_week: float
    meat_lbs_cumulative: float
    capacity_bind: str  # which constraint throttled this week, if any


@dataclass
class PopulationPath:
    states: list
    params: BiologyParams
    kit: KitParams
    U: float
    y0: float
    z0: float

    def at_day(self, t_days: float) -> PopulationState:
        if not self.states:
            raise ValueError("empty path")
        w = int(t_days // DAYS_PER_WEEK)
        w = max(0, min(w, len(self.states) - 1))
        return self.states[w]


def expected_comp_price(
    labels: Sequence[str] = DEFAULT_P_COMP_LABELS,
    comps: Sequence[tuple] = COMP_PRICES_USD_PER_LB,
) -> float:
    by_label = {c[0]: c[1] for c in comps}
    vals = [by_label[lab] for lab in labels]
    return sum(vals) / len(vals)


def P_meat(
    t_years: float,
    p_spot: Optional[float] = None,
    drift_per_year: float = FORWARD_DRIFT_PER_YEAR,
) -> float:
    """
    Fair forward competing price of quail meat $/lb at delivery t (years).
    P_meat(t) = P_spot * exp(μ t); default μ=0 (flat).
    """
    if p_spot is None:
        p_spot = expected_comp_price()
    return float(p_spot * math.exp(drift_per_year * t_years))


def fair_prepaid_forward_per_lb(
    T_years: float,
    p_comp: Optional[float] = None,
    r_prime: float = PRIME_RATE,
    continuous: bool = False,
    drift_per_year: float = FORWARD_DRIFT_PER_YEAR,
) -> dict:
    """
    Fair prepaid forward $/lb. Buyer deposit at 0 is a loan to Loop until delivery T.

    Discrete:  F_0 = E[P_comp(T)] / (1 + r_prime)^T
    Continuous: F_0 = E[P_comp(T)] * exp(-r_prime * T)

    Cash flows: deposit F_0 at t=0; deliver 1 lb at T; no further cash if fully prepaid.
    """
    if p_comp is None:
        p_comp = expected_comp_price()
    if T_years < 0:
        raise ValueError("T_years must be >= 0")
    p_delivery = P_meat(T_years, p_spot=p_comp, drift_per_year=drift_per_year)
    if continuous:
        df = math.exp(-r_prime * T_years)
        formula = "F_0 = E[P_comp(T)] * exp(-r_prime * T)"
    else:
        df = 1.0 / ((1.0 + r_prime) ** T_years)
        formula = "F_0 = E[P_comp(T)] / (1 + r_prime)^T"
    f0 = p_delivery * df
    return {
        "F_0_usd_per_lb": f0,
        "E_P_comp_at_T": p_delivery,
        "P_comp_spot": p_comp,
        "T_years": T_years,
        "r_prime": r_prime,
        "r_prime_as_of": PRIME_RATE_AS_OF,
        "discount_factor": df,
        "continuous": continuous,
        "formula": formula,
        "cash_flows": {
            "t0_deposit_per_lb": f0,
            "tT_delivery_lbs": 1.0,
            "tT_additional_cash": 0.0,
        },
        "implied_interest_credit_vs_pay_at_T": p_delivery - f0,
    }


def kit_caps(U: float, kit: Optional[KitParams] = None) -> dict:
    k = kit or KitParams()
    U = float(U)
    incub_w = KIT_INCUBATOR_EGGS_PER_BATCH  # per batch; weekly set ≈ batch * 7/incubation
    return {
        "U": U,
        "breeder_heads": U * k.breeder_heads,
        "brooder_heads": U * k.brooder_heads,
        "growout_heads": U * k.growout_heads,
        "incub_eggs_per_batch": U * k.incub_eggs_per_batch,
        # Continuous-set approximation: batches roll every incubation period
        "incub_eggs_per_week": U * k.incub_eggs_per_batch * (DAYS_PER_WEEK / INCUBATION_DAYS),
        "kit_capex_usd": U * k.price_usd,
    }


def _eggs_per_hen_per_week(p: BiologyParams) -> float:
    return p.eggs_per_hen_per_year / (DAYS_PER_YEAR / DAYS_PER_WEEK)


def simulate_population(
    y: float,
    z: float,
    U: float,
    weeks: int,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
) -> PopulationPath:
    """
    Weekly cohort sim for jumbo Coturnix under U Grit kits.

    y, z = starting male, female breeders.
    Capacity binds: breeders, brooder (age < brood_days), grow-out (brood→slaughter),
    and incubator eggs/week. Excess eggs not set; overcrowding → egg set throttled
    and/or harvest accelerated is not modeled — we throttle intake (eggs set).
    """
    p = params or BiologyParams()
    k = kit or KitParams()
    U = float(U)
    if U <= 0:
        raise ValueError("U (kit units) must be > 0")

    caps = kit_caps(U, k)
    surv = 1.0 - p.weekly_mortality
    incub_w = max(1, int(round(p.incubation_days / DAYS_PER_WEEK)))
    slaughter_w = max(1, int(round(p.slaughter_days / DAYS_PER_WEEK)))
    maturity_w = max(1, int(round(p.maturity_days / DAYS_PER_WEEK)))
    brood_w = max(1, int(round(p.brood_days / DAYS_PER_WEEK)))
    max_breed_w = max(1, int(round(p.max_breeder_age_days / DAYS_PER_WEEK)))

    # If starters exceed breeder cage, they still exist but we flag; egg output uses
    # only housed breeders (capped). Unhoused starters are ASSUMPTION: culled/held out.
    starters = float(y) + float(z)
    if starters > caps["breeder_heads"] + 1e-9:
        scale = caps["breeder_heads"] / starters
        y = float(y) * scale
        z = float(z) * scale
        start_note = "starters_scaled_to_breeder_cap"
    else:
        start_note = ""

    eggs_pipeline: list[float] = []
    # grower cohorts by age in weeks: [males, females]
    grow_cohorts: list[list[float]] = []
    breed_cohorts: list[list[float]] = [[float(y), float(z)]]

    states: list[PopulationState] = []
    meat_cum = 0.0

    for w in range(weeks + 1):
        bind = start_note if w == 0 and start_note else ""

        for c in breed_cohorts:
            c[0] *= surv
            c[1] *= surv
        for c in grow_cohorts:
            c[0] *= surv
            c[1] *= surv

        # Cull aged breeders → meat
        culled = 0.0
        if len(breed_cohorts) > max_breed_w:
            old = breed_cohorts[:-max_breed_w]
            breed_cohorts = breed_cohorts[-max_breed_w:]
            for c in old:
                culled += c[0] + c[1]

        males_b = sum(c[0] for c in breed_cohorts)
        females_b = sum(c[1] for c in breed_cohorts)

        # Soft-cap breeders to kit capacity (throttle promotions later; trim excess to meat)
        if males_b + females_b > caps["breeder_heads"]:
            overflow = males_b + females_b - caps["breeder_heads"]
            # remove from oldest cohorts preferentially
            left = overflow
            for c in breed_cohorts:
                head = c[0] + c[1]
                if head <= 0 or left <= 0:
                    continue
                take = min(head, left)
                frac = take / head
                culled += take
                c[0] *= 1.0 - frac
                c[1] *= 1.0 - frac
                left -= take
            males_b = sum(c[0] for c in breed_cohorts)
            females_b = sum(c[1] for c in breed_cohorts)
            bind = bind or "breeder_cap"

        # Desired eggs from hens
        eggs_desired = females_b * _eggs_per_hen_per_week(p)

        # Incubator weekly set capacity
        eggs_cap_incub = caps["incub_eggs_per_week"]

        # Brooder / grow-out headroom limits how many chicks we can afford to hatch soon.
        # Approximate: don't set more eggs than hatch_rate-adjusted free slots in brooder
        # after accounting for eggs already in pipeline that will hatch into brooder window.
        def _heads_in_age(lo_w: int, hi_w: int) -> float:
            total = 0.0
            for age, c in enumerate(reversed(grow_cohorts)):
                # age 0 = newest
                if lo_w <= age < hi_w:
                    total += c[0] + c[1]
            return total

        brood_heads = _heads_in_age(0, brood_w)
        grow_heads = _heads_in_age(brood_w, slaughter_w)
        brood_free = max(0.0, caps["brooder_heads"] - brood_heads)
        grow_free = max(0.0, caps["growout_heads"] - grow_heads)
        # Chicks hatching this week consume brooder; longer-run: limit set by min free
        # Convert free chick slots to eggs via hatch_rate
        chick_slots = min(brood_free, grow_free + brood_free)  # crude joint
        eggs_cap_space = chick_slots / max(p.hatch_rate, 1e-9) if chick_slots < 1e18 else eggs_desired

        eggs_set = min(eggs_desired, eggs_cap_incub, eggs_cap_space)
        if eggs_set + 1e-9 < eggs_desired:
            if eggs_cap_incub <= eggs_cap_space and eggs_cap_incub < eggs_desired:
                bind = bind or "incubator_cap"
            else:
                bind = bind or "brooder_or_growout_cap"

        eggs_pipeline.append(eggs_set)

        chicks = 0.0
        if w >= incub_w:
            chicks = eggs_pipeline[w - incub_w] * p.hatch_rate
        chicks_f = chicks * p.sex_ratio_female
        chicks_m = chicks * (1.0 - p.sex_ratio_female)
        grow_cohorts.append([chicks_m, chicks_f])

        # Promote at maturity into breeders (subject to breeder free slots + sex ratio)
        promoted_bind = False
        if len(grow_cohorts) >= maturity_w + 1:
            idx = len(grow_cohorts) - 1 - maturity_w
            if idx >= 0:
                cohort = grow_cohorts[idx]
                take_f = cohort[1] * p.frac_female_to_breeders
                take_m = cohort[0] * p.frac_male_to_breeders
                males_b_now = sum(c[0] for c in breed_cohorts)
                females_b_now = sum(c[1] for c in breed_cohorts)
                free = max(0.0, caps["breeder_heads"] - (males_b_now + females_b_now))
                want = take_f + take_m
                if want > free:
                    scale = free / want if want > 0 else 0.0
                    take_f *= scale
                    take_m *= scale
                    promoted_bind = True
                target_m = (females_b_now + take_f) * p.breeder_males_per_female
                if males_b_now + take_m > target_m:
                    take_m = max(0.0, target_m - males_b_now)
                cohort[0] -= take_m
                cohort[1] -= take_f
                if take_m + take_f > 0:
                    breed_cohorts.append([take_m, take_f])
                if promoted_bind:
                    bind = bind or "breeder_cap_promotion"

        # Harvest at slaughter age + culls
        harvested = culled
        if len(grow_cohorts) > slaughter_w:
            due = grow_cohorts[:-slaughter_w]
            grow_cohorts = grow_cohorts[-slaughter_w:]
            for c in due:
                harvested += c[0] + c[1]

        meat_lbs = harvested * p.dress_weight_lbs
        meat_cum += meat_lbs

        # Recount compartments
        brood_m = brood_f = grow_m = grow_f = 0.0
        for age, c in enumerate(reversed(grow_cohorts)):
            if age < brood_w:
                brood_m += c[0]
                brood_f += c[1]
            else:
                grow_m += c[0]
                grow_f += c[1]
        males_b = sum(c[0] for c in breed_cohorts)
        females_b = sum(c[1] for c in breed_cohorts)

        states.append(
            PopulationState(
                week=w,
                day=w * DAYS_PER_WEEK,
                males_breeders=males_b,
                females_breeders=females_b,
                males_brood=brood_m,
                females_brood=brood_f,
                males_grow=grow_m,
                females_grow=grow_f,
                males_total=males_b + brood_m + grow_m,
                females_total=females_b + brood_f + grow_f,
                total=males_b + females_b + brood_m + brood_f + grow_m + grow_f,
                eggs_set_this_week=eggs_set,
                eggs_desired_this_week=eggs_desired,
                chicks_hatched_this_week=chicks,
                birds_slaughtered_this_week=harvested,
                meat_lbs_this_week=meat_lbs,
                meat_lbs_cumulative=meat_cum,
                capacity_bind=bind,
            )
        )

    return PopulationPath(states=states, params=p, kit=k, U=U, y0=float(y), z0=float(z))


def meat_lbs(
    t: float,
    y: float,
    z: float,
    U: float,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    *,
    t_unit: str = "days",
) -> float:
    """
    Cumulative harvestable dressed meat (lbs) by time t, given starters y♂ z♀ and U kits.

    t_unit: 'days' | 'weeks' | 'years'
    """
    if t_unit == "days":
        t_days = float(t)
    elif t_unit == "weeks":
        t_days = float(t) * DAYS_PER_WEEK
    elif t_unit == "years":
        t_days = float(t) * DAYS_PER_YEAR
    else:
        raise ValueError("t_unit must be days|weeks|years")
    weeks = int(math.ceil(t_days / DAYS_PER_WEEK)) + 1
    path = simulate_population(y, z, U, weeks=weeks, params=params, kit=kit)
    return path.at_day(t_days).meat_lbs_cumulative


def quail_population(
    t: float,
    y: float,
    z: float,
    U: float = 1.0,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    *,
    t_unit: str = "days",
) -> dict:
    """N(t): heads by compartment at time t (jumbo Coturnix under U kits)."""
    if t_unit == "days":
        t_days = float(t)
    elif t_unit == "weeks":
        t_days = float(t) * DAYS_PER_WEEK
    elif t_unit == "years":
        t_days = float(t) * DAYS_PER_YEAR
    else:
        raise ValueError("t_unit must be days|weeks|years")
    weeks = int(math.ceil(t_days / DAYS_PER_WEEK)) + 1
    path = simulate_population(y, z, U, weeks=weeks, params=params, kit=kit)
    st = path.at_day(t_days)
    return {
        "day": st.day,
        "week": st.week,
        "males": st.males_total,
        "females": st.females_total,
        "total": st.total,
        "males_breeders": st.males_breeders,
        "females_breeders": st.females_breeders,
        "brood": st.males_brood + st.females_brood,
        "grow": st.males_grow + st.females_grow,
        "meat_lbs_cumulative": st.meat_lbs_cumulative,
        "U": U,
        "capacity_bind": st.capacity_bind,
    }


def kits_needed(
    X: float,
    t: float,
    y: float,
    z: float,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    *,
    t_unit: str = "days",
    U_max: int = 50,
) -> dict:
    """
    Inverse problem: minimum integer kit units U* such that
        meat_lbs(t, y, z, U*) >= X
    subject to kit capacity constraints inside the simulator.

    Also reports whether starters y+z alone force a floor on U
    (breeder cage: ceil((y+z)/breeder_heads_per_kit)).

    Returns dict with U_star, meat_at_U, housing_floor_U, feasible, search path.
    """
    k = kit or KitParams()
    housing_floor = int(math.ceil((float(y) + float(z)) / k.breeder_heads)) if (y + z) > 0 else 1
    housing_floor = max(1, housing_floor)

    if t_unit == "days":
        t_days = float(t)
    elif t_unit == "weeks":
        t_days = float(t) * DAYS_PER_WEEK
    elif t_unit == "years":
        t_days = float(t) * DAYS_PER_YEAR
    else:
        raise ValueError("t_unit must be days|weeks|years")

    path_log = []
    U_star = None
    meat_at = None
    for U in range(housing_floor, U_max + 1):
        m = meat_lbs(t_days, y, z, U, params=params, kit=k, t_unit="days")
        path_log.append({"U": U, "meat_lbs": m})
        if m + 1e-9 >= float(X):
            U_star = U
            meat_at = m
            break

    feasible = U_star is not None
    # Optional: minimum breeders hint if even U_max fails — scale flock suggestion
    breeders_hint = None
    if not feasible:
        # Try more hens with U_max: binary-ish scale on z
        breeders_hint = (
            "Demand unmet at U_max with given y,z. Increase breeders (z) and/or horizon t, "
            "or raise U_max."
        )

    return {
        "X_lbs": float(X),
        "t_days": t_days,
        "y": float(y),
        "z": float(z),
        "housing_floor_U": housing_floor,
        "U_star": U_star,
        "meat_lbs_at_U_star": meat_at,
        "feasible": feasible,
        "U_max": U_max,
        "search": path_log,
        "note": breeders_hint,
        "kit_capex_at_U_star": (U_star * k.price_usd) if U_star else None,
    }


def min_breeders_for_demand(
    X: float,
    t: float,
    U: float,
    male_female_ratio: float = BREEDER_MALES_PER_FEMALE,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    *,
    t_unit: str = "days",
    z_max: int = 500,
) -> dict:
    """
    Optional dual inverse: fix U kits, find minimal female breeders z (with y = ratio*z)
    such that meat_lbs(t,y,z,U) >= X, subject to y+z <= U * breeder_heads.
    """
    k = kit or KitParams()
    cap = float(U) * k.breeder_heads
    best = None
    log = []
    for z in range(1, z_max + 1):
        y = male_female_ratio * z
        if y + z > cap + 1e-9:
            break
        m = meat_lbs(t, y, z, U, params=params, kit=k, t_unit=t_unit)
        log.append({"z": z, "y": y, "meat_lbs": m})
        if m + 1e-9 >= float(X):
            best = {"y": y, "z": z, "meat_lbs": m, "U": U}
            break
    return {
        "X_lbs": float(X),
        "U": float(U),
        "breeder_cap": cap,
        "solution": best,
        "feasible": best is not None,
        "search_tail": log[-10:],
    }




# ---------------------------------------------------------------------------
# Primary API: sustained production rate vs average consumption
# ---------------------------------------------------------------------------

def production_rate(
    t: float,
    y: float,
    z: float,
    U: float,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    *,
    t_unit: str = "days",
    window_weeks: int = 4,
    rate_unit: str = "lb_per_week",
) -> dict:
    """
    Harvest / meat production rate achievable around time t.

    r_prod(t; y,z,U) ≈ mean weekly dressed lbs over [t, t + window_weeks],
    after the system has had time to fill the pipeline (first slaughter ~ slaughter_days).

    Returns lb/week (default) or lb/day. Also reports instantaneous week rate at t.
    """
    if t_unit == "days":
        t_days = float(t)
    elif t_unit == "weeks":
        t_days = float(t) * DAYS_PER_WEEK
    elif t_unit == "years":
        t_days = float(t) * DAYS_PER_YEAR
    else:
        raise ValueError("t_unit must be days|weeks|years")

    end_week = int(math.ceil(t_days / DAYS_PER_WEEK)) + max(1, int(window_weeks))
    path = simulate_population(y, z, U, weeks=end_week, params=params, kit=kit)
    w0 = int(t_days // DAYS_PER_WEEK)
    w0 = max(0, min(w0, len(path.states) - 1))
    w1 = min(len(path.states) - 1, w0 + max(1, int(window_weeks)) - 1)
    weekly = [path.states[w].meat_lbs_this_week for w in range(w0, w1 + 1)]
    mean_week = sum(weekly) / len(weekly) if weekly else 0.0
    inst = path.states[w0].meat_lbs_this_week
    if rate_unit == "lb_per_week":
        r = mean_week
        r_inst = inst
    elif rate_unit == "lb_per_day":
        r = mean_week / DAYS_PER_WEEK
        r_inst = inst / DAYS_PER_WEEK
    else:
        raise ValueError("rate_unit must be lb_per_week|lb_per_day")
    return {
        "t_days": t_days,
        "y": float(y),
        "z": float(z),
        "U": float(U),
        "r_prod": r,
        "r_prod_instant_week": r_inst if rate_unit == "lb_per_week" else r_inst,
        "rate_unit": rate_unit,
        "window_weeks": int(window_weeks),
        "weekly_lbs_in_window": weekly,
        "capacity_bind_at_t": path.states[w0].capacity_bind,
        "meat_lbs_cumulative_at_t": path.states[w0].meat_lbs_cumulative,
    }


def can_sustain(
    c_bar: float,
    t: float,
    y: float,
    z: float,
    U: float,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    *,
    t_unit: str = "days",
    window_weeks: int = 4,
    rate_unit: str = "lb_per_week",
    hold_weeks: int = 12,
    initial_inventory_lbs: float = 0.0,
) -> dict:
    """
    Whether production from t onward can consistently supply average consumption c̄.

    Definition (inventory buffer — batch harvest OK):
      I_0 = initial_inventory_lbs
      I_{w+1} = I_w + harvest_w - c_week
      sustains if I_w >= 0 for all w in [t, t+hold_weeks) AND
      mean r_prod over window_weeks at t >= c_bar.

    c_bar and rate_unit must match (both lb/week or both lb/day).
    """
    pr = production_rate(
        t, y, z, U, params=params, kit=kit,
        t_unit=t_unit, window_weeks=window_weeks, rate_unit=rate_unit,
    )
    if rate_unit == "lb_per_week":
        c_week = float(c_bar)
    else:
        c_week = float(c_bar) * DAYS_PER_WEEK

    if t_unit == "days":
        t_days = float(t)
    elif t_unit == "weeks":
        t_days = float(t) * DAYS_PER_WEEK
    else:
        t_days = float(t) * DAYS_PER_YEAR

    end_week = int(math.ceil(t_days / DAYS_PER_WEEK)) + max(hold_weeks, window_weeks) + 2
    path = simulate_population(y, z, U, weeks=end_week, params=params, kit=kit)
    w0 = int(t_days // DAYS_PER_WEEK)
    inv = float(initial_inventory_lbs)
    weeks_ok = []
    min_inv = inv
    for i in range(hold_weeks):
        wi = min(len(path.states) - 1, w0 + i)
        harvest = path.states[wi].meat_lbs_this_week
        inv = inv + harvest - c_week
        min_inv = min(min_inv, inv)
        weeks_ok.append({
            "week": wi,
            "meat_lbs": harvest,
            "inventory_end": inv,
            "ok": inv >= -1e-9,
        })
    inv_ok = all(row["ok"] for row in weeks_ok)
    mean_ok = pr["r_prod"] + 1e-9 >= float(c_bar)
    return {
        "c_bar": float(c_bar),
        "rate_unit": rate_unit,
        "r_prod": pr["r_prod"],
        "r_prod_required": float(c_bar),
        "sustains": inv_ok and mean_ok,
        "mean_window_ok": mean_ok,
        "inventory_ok": inv_ok,
        "min_inventory_lbs": min_inv,
        "hold_weeks_detail": weeks_ok,
        "surplus_rate": pr["r_prod"] - float(c_bar),
        "production": pr,
    }


def t_ready(
    c_bar: float,
    y: float,
    z: float,
    U: float,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    *,
    rate_unit: str = "lb_per_week",
    window_weeks: int = 4,
    hold_weeks: int = 12,
    max_weeks: int = 104,
    initial_inventory_lbs: float = 0.0,
) -> dict:
    """
    Earliest time (days) at which production can sustain average consumption c̄
    under the inventory-buffer rule in can_sustain (batch harvest allowed).

    Scans weekly from first slaughter week onward.
    """
    p = params or BiologyParams()
    first_w = max(1, int(round(p.slaughter_days / DAYS_PER_WEEK)))
    # Simulate once; reuse for inventory checks
    path = simulate_population(y, z, U, weeks=max_weeks, params=p, kit=kit)
    if rate_unit == "lb_per_day":
        c = float(c_bar)
        c_week = c * DAYS_PER_WEEK
    else:
        c = float(c_bar)
        c_week = c

    ramp = []
    ready_week = None
    for w in range(first_w, max_weeks - hold_weeks):
        weekly = [path.states[wi].meat_lbs_this_week for wi in range(w, min(len(path.states), w + window_weeks))]
        mean_w = sum(weekly) / len(weekly) if weekly else 0.0
        r = mean_w / DAYS_PER_WEEK if rate_unit == "lb_per_day" else mean_w
        inv = float(initial_inventory_lbs)
        inv_ok = True
        for i in range(hold_weeks):
            wi = min(len(path.states) - 1, w + i)
            inv = inv + path.states[wi].meat_lbs_this_week - c_week
            if inv < -1e-9:
                inv_ok = False
                break
        ok = inv_ok and (r + 1e-9 >= c)
        ramp.append({
            "week": w,
            "day": w * DAYS_PER_WEEK,
            "r_prod_lb_per_week": mean_w,
            "sustains": ok,
        })
        if ok:
            ready_week = w
            break

    return {
        "c_bar": float(c_bar),
        "rate_unit": rate_unit,
        "y": float(y),
        "z": float(z),
        "U": float(U),
        "t_ready_days": (ready_week * DAYS_PER_WEEK) if ready_week is not None else None,
        "t_ready_weeks": ready_week,
        "feasible": ready_week is not None,
        "r_prod_required": float(c_bar),
        "ramp_path": ramp,
        "sustain_rule": "inventory_buffer",
    }


def rate_ramp_table(
    y: float,
    z: float,
    U: float,
    weeks: int = 52,
    params: Optional[BiologyParams] = None,
    kit: Optional[KitParams] = None,
    window_weeks: int = 4,
) -> list:
    """Ramp path: weekly mean production rate (lb/week) from week 0..weeks."""
    path = simulate_population(y, z, U, weeks=weeks + window_weeks, params=params, kit=kit)
    rows = []
    for w in range(0, weeks + 1):
        weekly = [path.states[wi].meat_lbs_this_week for wi in range(w, min(len(path.states), w + window_weeks))]
        mean_w = sum(weekly) / len(weekly) if weekly else 0.0
        st = path.states[w]
        rows.append({
            "week": w,
            "day": w * DAYS_PER_WEEK,
            "r_prod_lb_per_week": mean_w,
            "meat_lbs_week": st.meat_lbs_this_week,
            "meat_lbs_cum": st.meat_lbs_cumulative,
            "total_heads": st.total,
            "breeders": st.males_breeders + st.females_breeders,
            "bind": st.capacity_bind,
        })
    return rows


def forward_table(
    delivery_years: Sequence[float],
    p_comp: Optional[float] = None,
    r_prime: float = PRIME_RATE,
    continuous: bool = False,
) -> list:
    return [
        fair_prepaid_forward_per_lb(T, p_comp=p_comp, r_prime=r_prime, continuous=continuous)
        for T in delivery_years
    ]


def defaults_table() -> list:
    return [
        {"name": "species", "value": "jumbo Coturnix japonica", "unit": "", "tag": "SCOPE"},
        {"name": "eggs_per_hen_per_year", "value": EGGS_PER_HEN_PER_YEAR, "unit": "eggs/hen/yr", "tag": "SOURCED range 200–300"},
        {"name": "hatch_rate", "value": HATCH_RATE, "unit": "fraction", "tag": "ASSUMPTION (lit. 0.625–0.925)"},
        {"name": "incubation_days", "value": INCUBATION_DAYS, "unit": "days", "tag": "SOURCED 17–18"},
        {"name": "maturity_days", "value": MATURITY_DAYS, "unit": "days", "tag": "ASSUMPTION mid 6–8 wk"},
        {"name": "slaughter_days", "value": SLAUGHTER_DAYS, "unit": "days", "tag": "ASSUMPTION mid 8–10 wk jumbo"},
        {"name": "live_weight_oz", "value": LIVE_WEIGHT_OZ, "unit": "oz", "tag": "ASSUMPTION mid 12–14"},
        {"name": "dress_yield", "value": DRESS_YIELD, "unit": "fraction", "tag": "ASSUMPTION mid 70–75%"},
        {"name": "dress_weight_lbs", "value": round(DRESS_WEIGHT_LBS, 4), "unit": "lb/bird", "tag": "DERIVED"},
        {"name": "weekly_mortality", "value": WEEKLY_MORTALITY, "unit": "/week", "tag": "ASSUMPTION"},
        {"name": "kit_incub_eggs_batch", "value": KIT_INCUBATOR_EGGS_PER_BATCH, "unit": "eggs", "tag": "SOURCED Grit kit"},
        {"name": "kit_brooder_heads", "value": KIT_BROODER_HEADS, "unit": "birds", "tag": "SOURCED CB25-03-5K"},
        {"name": "kit_growout_heads_jumbo", "value": KIT_GROWOUT_HEADS_JUMBO, "unit": "birds", "tag": "ASSUMPTION derated"},
        {"name": "kit_breeder_heads_jumbo", "value": KIT_BREEDER_HEADS_JUMBO, "unit": "birds", "tag": "SOURCED 3/section×15"},
        {"name": "kit_price_usd", "value": KIT_PRICE_USD, "unit": "USD", "tag": "SOURCED Grit sale"},
        {"name": "prime_rate", "value": PRIME_RATE, "unit": "/yr", "tag": f"SOURCED Fed H.15 {PRIME_RATE_AS_OF}"},
        {"name": "E_P_comp_default", "value": round(expected_comp_price(), 4), "unit": "USD/lb", "tag": "DERIVED foodservice mean"},
    ]


if __name__ == "__main__":
    print("dress_lb", round(DRESS_WEIGHT_LBS, 4), "E[P_comp]", round(expected_comp_price(), 4))
    print(kits_needed(50, 180, y=5, z=15, t_unit="days", U_max=10))
