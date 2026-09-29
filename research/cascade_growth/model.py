#!/usr/bin/env python3
"""Coupled stochastic growth across the Loop cascade. Planning only.

Stage 1 worms remain the only active spend. Quail in this module is Stage 4
planning. Fish is Stage 5 planning. Nothing here authorizes a purchase.

Each species is a life-cycle chain. Sex is tracked for quail and for
aquaponics fish breeders. Worms are hermaphrodites and are counted as
biomass-bearing headcount. Crickets, isopods, greens, and algae are stage
or biomass pools without a binary sex state.

Weekly noise is binomial (normal approximation above 80 individuals) on
survival and hatch, Poisson (same approximation) on recruits, and a
lognormal multiplier of median 1 on fecundity. Internal feed transfers use
``safe_sell_limit`` from the synergy buffers: at most alpha times surplus
above the breed floor. Breeders are not cut to feed another species.

Numbers that are not already locked in this repository are tagged
ASSUMPTION in ``parameter_catalog``.
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

_RESEARCH = Path(__file__).resolve().parents[1]
for _folder in (_RESEARCH / "quail", _RESEARCH / "synergy"):
    if str(_folder) not in sys.path:
        sys.path.insert(0, str(_folder))

try:
    from circular_buffers import breed_floor, safe_sell_limit  # noqa: E402
    from quail_model import (  # noqa: E402
        BREEDER_MALES_PER_FEMALE,
        BROOD_DAYS,
        DAYS_PER_WEEK,
        DAYS_PER_YEAR,
        EGGS_PER_HEN_PER_YEAR,
        FRAC_FEMALE_TO_BREEDERS,
        FRAC_MALE_TO_BREEDERS,
        HATCH_RATE,
        INCUBATION_DAYS,
        MATURITY_DAYS,
        SEX_RATIO_FEMALE,
        SLAUGHTER_DAYS,
        WEEKLY_MORTALITY,
    )
except ImportError as err:
    raise ImportError(
        "This folder expects research/quail and research/synergy next to it. "
        "Clone the whole repository, then run from research/cascade_growth."
    ) from err


STAGE_GATE = (
    "Stage 1 worms only. This growth graph is Stage 4 planning research. "
    "It does not open Stage 2–5 spend."
)

DEFAULT_SEED = 20260928
DEFAULT_WEEKS = 52
DEFAULT_PATHS = 40
ALPHA = 0.9  # synergy firm-book stand-in

# Worm stand-in locked to research/ops-dashboard/engine.py (ASSUMPTION there).
WORM_DOUBLING_TARGET_WEEKS = 13.0
WORM_WEEKLY_SIGMA = 0.015
WORM_CARRYING_MULTIPLE = 16.0
WORM_PER_LB = 1000.0
WORM_KG_EACH = (1.0 / WORM_PER_LB) * 0.45359237  # DERIVED from the planning count and 0.45359237 kg/lb
WORM_FLOOR = 16500.0  # ASSUMPTION. Same planning starter as the ops screen.
WORM_WEEKLY_M = 0.005  # ASSUMPTION. Not the quail 1%/week rate.

# Quail ration, same ASSUMPTION as research/ops-dashboard/quail_income.py.
QUAIL_INTAKE_G_PER_DAY = 22.0
QUAIL_WORM_SHARE = 0.30
QUAIL_PLANT_SHARE = 1.0 - QUAIL_WORM_SHARE

# Life-cycle widths in weeks. Quail widths are the quail_model day counts / 7.
WORM_COCOON_WEEKS = 3  # ASSUMPTION
WORM_JUVENILE_WEEKS = 8  # ASSUMPTION
CRICKET_NYMPH_WEEKS = 4  # ASSUMPTION, README Module 3 demo uses ~4 weeks
ISOPOD_JUVENILE_WEEKS = 6  # ASSUMPTION
FISH_FRY_WEEKS = 4  # ASSUMPTION
FISH_JUVENILE_WEEKS = 6  # ASSUMPTION

QUAIL_INCUB_WEEKS = max(1, int(round(INCUBATION_DAYS / DAYS_PER_WEEK)))
QUAIL_BROOD_WEEKS = max(1, int(round(BROOD_DAYS / DAYS_PER_WEEK)))
QUAIL_MATURITY_WEEKS = max(1, int(round(MATURITY_DAYS / DAYS_PER_WEEK)))
QUAIL_SLAUGHTER_WEEKS = max(QUAIL_MATURITY_WEEKS + 1, int(round(SLAUGHTER_DAYS / DAYS_PER_WEEK)))
QUAIL_EGGS_PER_HEN_WEEK = EGGS_PER_HEN_PER_YEAR / (DAYS_PER_YEAR / DAYS_PER_WEEK)

# Planning fecundity, calibrated so an uncoupled worm herd's biomass first
# doubles near the 13-week ops-dashboard stand-in. Not a measured clutch.
WORM_COCOONS_PER_BREEDER_WEEK = 0.22  # ASSUMPTION
WORM_JUVENILE_MASS_FRAC = 0.45  # ASSUMPTION
WORM_COCOON_MASS_FRAC = 0.05  # ASSUMPTION
WORM_INTAKE_KG = WORM_KG_EACH * 0.25  # ASSUMPTION, fraction of adult body mass per week
WORM_JUVENILE_INTAKE_FRAC = 0.40  # ASSUMPTION
EXTERNAL_FEEDSTOCK_KG = 2.2  # ASSUMPTION stage-1 bedding/scrap, not a purchase
CASTINGS_PER_KG_FEED = 0.50  # ASSUMPTION
CASTINGS_TO_GREENS = 0.70  # ASSUMPTION split of the casting mass
CASTINGS_TO_ALGAE = 0.30  # ASSUMPTION
WORM_SIGMA_FECUNDITY = WORM_WEEKLY_SIGMA

CRICKET_FLOOR = 900.0  # ASSUMPTION planning breeders, not a purchase
CRICKET_START_ADULTS = 2800.0  # ASSUMPTION
CRICKET_EGGS_PER_ADULT_WEEK = 0.55  # ASSUMPTION, sex folded into a per-adult rate
CRICKET_WEEKLY_SURVIVAL = 0.95  # ASSUMPTION, README Module 3 demo
CRICKET_HARVEST_CAP_FRAC = 0.60  # ASSUMPTION, README Module 3 demo harvest fraction
CRICKET_KG = 0.0005  # ASSUMPTION, 0.5 g adult
CRICKET_INTAKE_KG = 0.00035  # ASSUMPTION fresh feed / adult / week
CRICKET_NYMPH_INTAKE_FRAC = 0.45  # ASSUMPTION
CRICKET_CAP = 12000.0  # ASSUMPTION
CRICKET_SIGMA = 0.04  # ASSUMPTION
FRASS_PER_KG_FEED = 0.40  # ASSUMPTION, README Module 3 demo

ISOPOD_FLOOR = 250.0  # ASSUMPTION
ISOPOD_START_ADULTS = 700.0  # ASSUMPTION
ISOPOD_RECRUITS_PER_ADULT_WEEK = 0.10  # ASSUMPTION, sex folded in
ISOPOD_WEEKLY_SURVIVAL = 0.97  # ASSUMPTION
ISOPOD_KG = 0.0002  # ASSUMPTION
ISOPOD_INTAKE_KG = 0.00035  # ASSUMPTION
ISOPOD_MANURE_SHARE = 0.35  # ASSUMPTION fraction of isopod diet from the manure pool
ISOPOD_MANURE_CAP_FRAC = 0.18  # ASSUMPTION, cannot take more than this share of the pool
ISOPOD_CAP = 5000.0  # ASSUMPTION
ISOPOD_SIGMA = 0.04  # ASSUMPTION

GREENS_FLOOR_KG = 6.0  # ASSUMPTION canopy that is not feed
GREENS_START_CANOPY_KG = 36.0  # ASSUMPTION
GREENS_START_SEEDLING_KG = 3.0  # ASSUMPTION
GREENS_WEEKLY_GROWTH = 0.62  # ASSUMPTION relative growth at full nutrient and space
GREENS_CAP_KG = 90.0  # ASSUMPTION
GREENS_SEEDLING_KG_WEEK = 0.80  # ASSUMPTION replant, not a seed order
CASTINGS_REF_GREENS_KG = 1.6  # ASSUMPTION castings that saturate the nutrient index
GREENS_NUTRIENT_FLOOR = 0.45  # ASSUMPTION starter fertility so greens are not zero

ALGAE_FLOOR_KG = 0.40  # ASSUMPTION
ALGAE_START_KG = 1.6  # ASSUMPTION
ALGAE_WEEKLY_GROWTH = 0.30  # ASSUMPTION
ALGAE_CAP_KG = 8.0  # ASSUMPTION
ALGAE_NUTRIENT_REF_KG = 1.2  # ASSUMPTION
ALGAE_NUTRIENT_FLOOR = 0.22  # ASSUMPTION

QUAIL_CAP = 360.0  # ASSUMPTION planning headcount, not a Grit kit cap
QUAIL_BREEDER_CAP = 160.0  # ASSUMPTION
QUAIL_SIGMA = 0.05  # ASSUMPTION fecundity noise; survival stays binomial at WEEKLY_MORTALITY
QUAIL_MANURE_KG = 0.028  # ASSUMPTION per bird per week
# Practice stocking and the comparison stocking. Totals match.
PRACTICE_MALES = 4.0
PRACTICE_FEMALES = 12.0  # 1♂:3♀, 16 founders
MALE_HEAVY_MALES = 12.0
MALE_HEAVY_FEMALES = 4.0  # 3♂:1♀, same 16 founders

FISH_START_MALES = 2.0
FISH_START_FEMALES = 4.0
FISH_MALE_PER_FEMALE = 0.5  # ASSUMPTION 1♂:2♀ breeder practice
FISH_FRY_PER_FEMALE_WEEK = 1.6  # ASSUMPTION managed, not a pond boom
FISH_WEEKLY_SURVIVAL = 0.97  # ASSUMPTION
FISH_PROMOTE_FRAC = 0.08  # ASSUMPTION of graduating juveniles that become breeders
FISH_HARVEST_FRAC = 0.25  # ASSUMPTION, README Module 4 demo weekly cap
FISH_GROWOUT_HOLD = 12.0  # ASSUMPTION headcount kept back from harvest
FISH_START_GROWOUT = 18.0  # ASSUMPTION
FISH_CAP = 280.0  # ASSUMPTION
FISH_INTAKE_KG = 0.012  # ASSUMPTION per growout-equivalent fish per week
FISH_ALGAE_SHARE = 0.45  # ASSUMPTION of the fish ration that algae can cover
FISH_SIGMA = 0.05  # ASSUMPTION
FISH_SLUDGE_KG = 0.004  # ASSUMPTION per fish-equivalent per week
FISH_FLOOR = FISH_START_MALES + FISH_START_FEMALES


def parameter_catalog() -> list[dict]:
    """Tagged planning inputs. SOURCED means the quail file already uses that tag."""
    return [
        {"name": "quail_eggs_per_hen_per_year", "value": EGGS_PER_HEN_PER_YEAR, "unit": "eggs/hen/yr", "tag": "SOURCED", "note": "research/quail range 200–300; weekly rate is derived"},
        {"name": "quail_eggs_per_hen_week", "value": round(QUAIL_EGGS_PER_HEN_WEEK, 4), "unit": "eggs/hen/wk", "tag": "DERIVED", "note": "EGGS_PER_HEN_PER_YEAR / (365.25/7)"},
        {"name": "quail_hatch_rate", "value": HATCH_RATE, "unit": "fraction", "tag": "ASSUMPTION", "note": "research/quail midpoint of a literature band"},
        {"name": "quail_sex_ratio_female", "value": SEX_RATIO_FEMALE, "unit": "fraction of chicks", "tag": "ASSUMPTION", "note": "hatch sex, not the breeder stocking ratio"},
        {"name": "quail_breeder_males_per_female", "value": BREEDER_MALES_PER_FEMALE, "unit": "males/female", "tag": "ASSUMPTION", "note": "1♂:3♀ jumbo Coturnix practice in research/quail"},
        {"name": "quail_weekly_mortality", "value": WEEKLY_MORTALITY, "unit": "/week", "tag": "ASSUMPTION", "note": "research/quail default"},
        {"name": "quail_frac_female_to_breeders", "value": FRAC_FEMALE_TO_BREEDERS, "unit": "fraction", "tag": "ASSUMPTION", "note": "research/quail"},
        {"name": "quail_frac_male_to_breeders", "value": FRAC_MALE_TO_BREEDERS, "unit": "fraction", "tag": "ASSUMPTION", "note": "research/quail; extra males are not recruited to match surplus males"},
        {"name": "quail_incub_weeks", "value": QUAIL_INCUB_WEEKS, "unit": "weeks", "tag": "DERIVED", "note": "round(17.5/7) with the quail_model half-week rule"},
        {"name": "quail_maturity_weeks", "value": QUAIL_MATURITY_WEEKS, "unit": "weeks", "tag": "DERIVED", "note": "from maturity_days 49, ASSUMPTION in research/quail"},
        {"name": "quail_slaughter_weeks", "value": QUAIL_SLAUGHTER_WEEKS, "unit": "weeks", "tag": "DERIVED", "note": "from slaughter_days 63, ASSUMPTION in research/quail"},
        {"name": "quail_intake_g_per_day", "value": QUAIL_INTAKE_G_PER_DAY, "unit": "g/bird/day", "tag": "ASSUMPTION", "note": "same figure as quail_income.INTAKE_G_PER_BIRD_DAY"},
        {"name": "quail_protein_share", "value": QUAIL_WORM_SHARE, "unit": "fraction of ration", "tag": "ASSUMPTION", "note": "quail_income worm share; this graph fills it with insects then worms"},
        {"name": "quail_plant_share", "value": QUAIL_PLANT_SHARE, "unit": "fraction of ration", "tag": "ASSUMPTION", "note": "the rest of that ration, taken from greens"},
        {"name": "worm_floor_headcount", "value": WORM_FLOOR, "unit": "breeders", "tag": "ASSUMPTION", "note": "16,500 planning starters already used on the ops screen"},
        {"name": "worm_doubling_target_weeks", "value": WORM_DOUBLING_TARGET_WEEKS, "unit": "weeks", "tag": "ASSUMPTION", "note": "ops-dashboard worm stand-in; fecundity is calibrated toward it"},
        {"name": "worm_weekly_sigma", "value": WORM_WEEKLY_SIGMA, "unit": "log sd", "tag": "ASSUMPTION", "note": "ops-dashboard worm stand-in"},
        {"name": "worm_carrying_multiple", "value": WORM_CARRYING_MULTIPLE, "unit": "x floor", "tag": "ASSUMPTION", "note": "ops-dashboard worm stand-in"},
        {"name": "worm_per_lb", "value": WORM_PER_LB, "unit": "adults/lb", "tag": "ASSUMPTION", "note": "ops-dashboard planning count"},
        {"name": "worm_cocoons_per_breeder_week", "value": WORM_COCOONS_PER_BREEDER_WEEK, "unit": "cocoons/breeder/wk", "tag": "ASSUMPTION", "note": "planning rate; clutch size is folded in; calibrated not measured"},
        {"name": "worm_weekly_mortality", "value": WORM_WEEKLY_M, "unit": "/week", "tag": "ASSUMPTION", "note": "slower than the quail planning mortality"},
        {"name": "external_feedstock_kg", "value": EXTERNAL_FEEDSTOCK_KG, "unit": "kg/week", "tag": "ASSUMPTION", "note": "stage-1 bin feedstock so worms are not fed only by later species"},
        {"name": "cricket_weekly_survival", "value": CRICKET_WEEKLY_SURVIVAL, "unit": "/week", "tag": "ASSUMPTION", "note": "README Module 3 demo, not a new measurement"},
        {"name": "cricket_harvest_cap_frac", "value": CRICKET_HARVEST_CAP_FRAC, "unit": "fraction of adults", "tag": "ASSUMPTION", "note": "README Module 3 demo"},
        {"name": "frass_per_kg_feed", "value": FRASS_PER_KG_FEED, "unit": "kg/kg", "tag": "ASSUMPTION", "note": "README Module 3 demo"},
        {"name": "fish_harvest_frac", "value": FISH_HARVEST_FRAC, "unit": "fraction of growout", "tag": "ASSUMPTION", "note": "README Module 4 demo weekly cap"},
        {"name": "alpha_firm", "value": ALPHA, "unit": "fraction of surplus", "tag": "ASSUMPTION", "note": "synergy firm-book stand-in, not a P50 sale"},
        {"name": "seed", "value": DEFAULT_SEED, "unit": "", "tag": "SCOPE", "note": "default ensemble seed"},
    ]


# Species/stage dependency graph. The figure and the step function share this list.
COUPLINGS = [
    {"src": "worms.breeder", "dst": "worms.cocoon", "kind": "fecundity", "label": "cocoons"},
    {"src": "worms.cocoon", "dst": "worms.juvenile", "kind": "maturation", "label": "hatch"},
    {"src": "worms.juvenile", "dst": "worms.breeder", "kind": "maturation", "label": "mature"},
    {"src": "external.feedstock", "dst": "worms.breeder", "kind": "feed", "label": "stage-1 feedstock"},
    {"src": "quail.breeder_f", "dst": "worms.breeder", "kind": "manure", "label": "manure"},
    {"src": "fish.growout", "dst": "worms.breeder", "kind": "manure", "label": "sludge"},
    {"src": "crickets.adult", "dst": "worms.breeder", "kind": "manure", "label": "frass"},
    {"src": "isopods.adult", "dst": "worms.breeder", "kind": "competition", "label": "manure competition"},
    {"src": "worms.breeder", "dst": "greens.canopy", "kind": "nutrient", "label": "castings"},
    {"src": "worms.breeder", "dst": "algae.culture", "kind": "nutrient", "label": "castings"},
    {"src": "algae.culture", "dst": "greens.canopy", "kind": "nutrient", "label": "nutrient water"},
    {"src": "fish.growout", "dst": "algae.culture", "kind": "nutrient", "label": "fish water"},
    {"src": "greens.seedling", "dst": "greens.canopy", "kind": "maturation", "label": "establish"},
    {"src": "greens.canopy", "dst": "crickets.nymph", "kind": "feed", "label": "greens"},
    {"src": "greens.canopy", "dst": "quail.breeder_f", "kind": "feed", "label": "greens"},
    {"src": "greens.canopy", "dst": "isopods.juvenile", "kind": "feed", "label": "residue"},
    {"src": "crickets.egg", "dst": "crickets.nymph", "kind": "maturation", "label": "hatch"},
    {"src": "crickets.nymph", "dst": "crickets.adult", "kind": "maturation", "label": "mature"},
    {"src": "crickets.adult", "dst": "crickets.egg", "kind": "fecundity", "label": "eggs"},
    {"src": "isopods.juvenile", "dst": "isopods.adult", "kind": "maturation", "label": "mature"},
    {"src": "isopods.adult", "dst": "isopods.juvenile", "kind": "fecundity", "label": "manca"},
    {"src": "crickets.adult", "dst": "quail.breeder_f", "kind": "feed", "label": "insects"},
    {"src": "isopods.adult", "dst": "quail.breeder_f", "kind": "feed", "label": "isopods"},
    {"src": "worms.juvenile", "dst": "quail.breeder_f", "kind": "feed", "label": "live worms"},
    {"src": "crickets.adult", "dst": "fish.growout", "kind": "feed", "label": "insects"},
    {"src": "worms.juvenile", "dst": "fish.growout", "kind": "feed", "label": "live worms"},
    {"src": "algae.culture", "dst": "fish.growout", "kind": "feed", "label": "algae"},
    {"src": "quail.breeder_f", "dst": "quail.egg", "kind": "fecundity", "label": "eggs"},
    {"src": "quail.egg", "dst": "quail.chick", "kind": "maturation", "label": "hatch"},
    {"src": "quail.chick", "dst": "quail.grow", "kind": "maturation", "label": "brood"},
    {"src": "quail.grow", "dst": "quail.breeder_f", "kind": "maturation", "label": "hens"},
    {"src": "quail.grow", "dst": "quail.breeder_m", "kind": "maturation", "label": "males at 1:3"},
    {"src": "fish.breeder_f", "dst": "fish.fry", "kind": "fecundity", "label": "fry"},
    {"src": "fish.fry", "dst": "fish.juvenile", "kind": "maturation", "label": "grow"},
    {"src": "fish.juvenile", "dst": "fish.growout", "kind": "maturation", "label": "growout"},
    {"src": "fish.juvenile", "dst": "fish.breeder_f", "kind": "maturation", "label": "breeders"},
]


NODE_LAYOUT = {
    "external.feedstock": (0.15, 2.55, "Stage-1\nfeedstock", "external"),
    "worms.cocoon": (1.85, 4.55, "worm\ncocoon", "worms"),
    "worms.juvenile": (1.85, 3.15, "worm\njuvenile", "worms"),
    "worms.breeder": (1.85, 1.55, "worm\nbreeder", "worms"),
    "crickets.egg": (3.85, 5.15, "cricket\negg", "crickets"),
    "crickets.nymph": (3.85, 3.85, "cricket\nnymph", "crickets"),
    "crickets.adult": (3.85, 2.45, "cricket\nadult", "crickets"),
    "isopods.juvenile": (5.45, 4.35, "isopod\njuvenile", "isopods"),
    "isopods.adult": (5.45, 2.85, "isopod\nadult", "isopods"),
    "greens.seedling": (7.15, 5.05, "greens\nseedling", "greens"),
    "greens.canopy": (7.15, 3.45, "greens\ncanopy", "greens"),
    "algae.culture": (7.15, 1.45, "algae", "algae"),
    "quail.egg": (9.15, 5.15, "quail\negg", "quail"),
    "quail.chick": (9.15, 3.95, "quail\nchick", "quail"),
    "quail.grow": (9.15, 2.75, "quail\ngrower", "quail"),
    "quail.breeder_f": (10.85, 4.15, "quail\nhen", "quail"),
    "quail.breeder_m": (10.85, 2.35, "quail\nmale", "quail"),
    "fish.fry": (12.55, 4.85, "fish\nfry", "fish"),
    "fish.juvenile": (12.55, 3.55, "fish\njuvenile", "fish"),
    "fish.growout": (12.55, 2.15, "fish\ngrowout", "fish"),
    "fish.breeder_f": (14.15, 3.85, "fish\nfemale", "fish"),
    "fish.breeder_m": (14.15, 2.15, "fish\nmale", "fish"),
}

GROUP_COLOR = {
    "external": "#d6d3d1",
    "worms": "#c4a484",
    "crickets": "#fdba74",
    "isopods": "#d6d3d1",
    "greens": "#86efac",
    "algae": "#5eead4",
    "quail": "#93c5fd",
    "fish": "#a5b4fc",
}


def _zeros(n: int) -> list[float]:
    return [0.0] * n


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def draw_factor(rng: random.Random, sigma: float, stochastic: bool) -> float:
    """Lognormal multiplier with median 1. The deterministic rate is the median rate."""
    if not stochastic or sigma <= 0.0:
        return 1.0
    return math.exp(sigma * rng.gauss(0.0, 1.0))


def draw_binom(rng: random.Random, n: float, p: float, stochastic: bool) -> float:
    """Survivors or successes. Expected value when stochastic is False."""
    count = max(0.0, float(n))
    prob = _clamp(float(p), 0.0, 1.0)
    if count == 0.0 or prob == 0.0:
        return 0.0
    if not stochastic or prob == 1.0:
        return count * prob
    if count >= 80.0:
        sd = math.sqrt(count * prob * (1.0 - prob))
        return _clamp(rng.gauss(count * prob, sd), 0.0, count)
    whole = int(round(count))
    return float(sum(1 for _ in range(whole) if rng.random() < prob))


def draw_count(rng: random.Random, lam: float, stochastic: bool) -> float:
    """Poisson recruits. Expected value when stochastic is False."""
    mean = max(0.0, float(lam))
    if mean == 0.0 or not stochastic:
        return mean
    if mean >= 40.0:
        return max(0.0, rng.gauss(mean, math.sqrt(mean)))
    limit = math.exp(-mean)
    draw = 1.0
    k = 0
    while draw > limit:
        k += 1
        draw *= rng.random()
    return float(k - 1)


def firm_take(
    n_now: float,
    floor: float,
    requested: float,
    m_weekly: float,
    lead_weeks: float = 0.0,
    n_req_forward: float | None = None,
) -> float:
    """Headcount that safe_sell_limit will release. Never the breed floor.

    When ``n_req_forward`` is set, the synergy helper also keeps enough
    survivors to cover that future breeder need. Replacement animals are
    not feed.
    """
    if requested <= 0.0 or n_now <= 0.0:
        return 0.0
    allowed = safe_sell_limit(
        n_now,
        floor,
        alpha=ALPHA,
        m_weekly=m_weekly,
        lead_weeks=lead_weeks,
        n_req_forward=n_req_forward,
    )["allowed_firm"]
    return max(0.0, min(float(requested), allowed))


def _advance(bins: list[float], incoming: float, p_surv: float, rng: random.Random, stochastic: bool) -> tuple[list[float], float]:
    survived = [draw_binom(rng, value, p_surv, stochastic) for value in bins]
    matured = survived[-1] if survived else 0.0
    nxt = [incoming] + survived[:-1] if survived else [incoming]
    return nxt, matured


def _room(n: float, cap: float) -> float:
    if cap <= 0.0:
        return 1.0
    return max(0.0, 1.0 - float(n) / float(cap))


@dataclass
class Cohort:
    age: int
    males: float
    females: float
    promoted: bool = False


@dataclass
class State:
    worm_cocoons: list[float]
    worm_juveniles: list[float]
    worm_breeders: float
    cricket_eggs: list[float]
    cricket_nymphs: list[float]
    cricket_adults: float
    isopod_juveniles: list[float]
    isopod_adults: float
    greens_seedling: float
    greens_canopy: float
    algae: float
    quail_eggs: list[float]
    quail_young: list[Cohort]
    quail_males: float
    quail_females: float
    fish_fry: list[float]
    fish_juveniles: list[float]
    fish_growout: float
    fish_males: float
    fish_females: float
    castings_greens: float = 0.0
    castings_algae: float = 0.0
    fish_nutrient: float = 0.0
    manure_in: float = 0.0
    frass_in: float = 0.0
    sludge_in: float = 0.0
    feedstock_in: float = EXTERNAL_FEEDSTOCK_KG
    quail_floor: float = field(default=PRACTICE_MALES + PRACTICE_FEMALES)


def initial_state(quail_males: float, quail_females: float) -> State:
    """Founding stocks. Quail sex is the sensitivity. Other starts stay put."""
    if quail_males < 0 or quail_females < 0:
        raise ValueError("quail founders must be >= 0")
    # Bin fills are ASSUMPTION planning stocks so the pipelines are not empty
    # at week 0. They are not purchases.
    juveniles = _zeros(WORM_JUVENILE_WEEKS)
    for i in range(WORM_JUVENILE_WEEKS):
        juveniles[i] = 250.0
    nymphs = _zeros(CRICKET_NYMPH_WEEKS)
    for i in range(CRICKET_NYMPH_WEEKS):
        nymphs[i] = 400.0
    iso_j = _zeros(ISOPOD_JUVENILE_WEEKS)
    for i in range(ISOPOD_JUVENILE_WEEKS):
        iso_j[i] = 60.0
    return State(
        worm_cocoons=_zeros(WORM_COCOON_WEEKS),
        worm_juveniles=juveniles,
        worm_breeders=WORM_FLOOR,
        cricket_eggs=_zeros(1),
        cricket_nymphs=nymphs,
        cricket_adults=CRICKET_START_ADULTS,
        isopod_juveniles=iso_j,
        isopod_adults=ISOPOD_START_ADULTS,
        greens_seedling=GREENS_START_SEEDLING_KG,
        greens_canopy=GREENS_START_CANOPY_KG,
        algae=ALGAE_START_KG,
        quail_eggs=_zeros(QUAIL_INCUB_WEEKS),
        quail_young=[],
        quail_males=float(quail_males),
        quail_females=float(quail_females),
        fish_fry=_zeros(FISH_FRY_WEEKS),
        fish_juveniles=_zeros(FISH_JUVENILE_WEEKS),
        fish_growout=FISH_START_GROWOUT,
        fish_males=FISH_START_MALES,
        fish_females=FISH_START_FEMALES,
        quail_floor=breed_floor(
            float(quail_males) + float(quail_females),
            float(quail_males) + float(quail_females),
            float(quail_males) + float(quail_females),
        ),
    )


def worm_equivalent(state: State) -> float:
    return (
        state.worm_breeders
        + WORM_JUVENILE_MASS_FRAC * sum(state.worm_juveniles)
        + WORM_COCOON_MASS_FRAC * sum(state.worm_cocoons)
    )


def worm_biomass_kg(state: State) -> float:
    return worm_equivalent(state) * WORM_KG_EACH


def quail_birds(state: State) -> tuple[float, float, float, float]:
    """Males, females, chicks, growers. Breeders are included in the sex totals."""
    chicks_m = chicks_f = grow_m = grow_f = 0.0
    for cohort in state.quail_young:
        if cohort.age < QUAIL_BROOD_WEEKS:
            chicks_m += cohort.males
            chicks_f += cohort.females
        else:
            grow_m += cohort.males
            grow_f += cohort.females
    males = state.quail_males + chicks_m + grow_m
    females = state.quail_females + chicks_f + grow_f
    return males, females, chicks_m + chicks_f, grow_m + grow_f


def fish_equivalent(state: State) -> float:
    fry = sum(state.fish_fry)
    juveniles = sum(state.fish_juveniles)
    return (
        0.15 * fry
        + 0.45 * juveniles
        + state.fish_growout
        + state.fish_males
        + state.fish_females
    )


def fish_headcount(state: State) -> float:
    return (
        sum(state.fish_fry)
        + sum(state.fish_juveniles)
        + state.fish_growout
        + state.fish_males
        + state.fish_females
    )


def _take_from_bins(bins: list[float], amount: float) -> list[float]:
    """Remove ``amount`` from the oldest bins first."""
    left = max(0.0, amount)
    out = list(bins)
    for i in range(len(out) - 1, -1, -1):
        if left <= 0.0:
            break
        take = min(out[i], left)
        out[i] -= take
        left -= take
    return out


def step(state: State, rng: random.Random, stochastic: bool = True) -> tuple[State, dict]:
    """One week. Returns the next state and the flows that produced it."""
    males, females, _chicks, _grow = quail_birds(state)
    q_birds = males + females
    worm_juv = sum(state.worm_juveniles)
    cricket_nymph = sum(state.cricket_nymphs)
    iso_juv = sum(state.isopod_juveniles)

    # Plants respond to last week's nutrients, then animals eat this week's growth.
    g_index = _clamp(state.castings_greens / CASTINGS_REF_GREENS_KG, GREENS_NUTRIENT_FLOOR, 1.15)
    greens_room = _room(state.greens_canopy, GREENS_CAP_KG)
    seedling_in = GREENS_SEEDLING_KG_WEEK * g_index
    established = min(state.greens_seedling, seedling_in)
    canopy = state.greens_canopy + established
    canopy = canopy + canopy * GREENS_WEEKLY_GROWTH * g_index * greens_room
    seedling = max(0.0, state.greens_seedling - established) + seedling_in * 0.35

    a_index = _clamp(
        (state.castings_algae + state.fish_nutrient) / ALGAE_NUTRIENT_REF_KG,
        ALGAE_NUTRIENT_FLOOR,
        1.15,
    )
    algae = state.algae + state.algae * ALGAE_WEEKLY_GROWTH * a_index * _room(state.algae, ALGAE_CAP_KG)

    worm_demand = state.worm_breeders * WORM_INTAKE_KG + worm_juv * WORM_INTAKE_KG * WORM_JUVENILE_INTAKE_FRAC
    manure_pool = state.feedstock_in + state.manure_in + state.frass_in + state.sludge_in
    iso_manure_demand = state.isopod_adults * ISOPOD_INTAKE_KG * ISOPOD_MANURE_SHARE
    iso_manure = min(iso_manure_demand, ISOPOD_MANURE_CAP_FRAC * manure_pool)
    worm_got = min(worm_demand, max(0.0, manure_pool - iso_manure))
    worm_index = 1.0 if worm_demand <= 1e-12 else worm_got / worm_demand

    greens_available = max(0.0, canopy - GREENS_FLOOR_KG)
    cricket_demand = (
        state.cricket_adults * CRICKET_INTAKE_KG
        + cricket_nymph * CRICKET_INTAKE_KG * CRICKET_NYMPH_INTAKE_FRAC
    )
    cricket_maint = CRICKET_FLOOR * CRICKET_INTAKE_KG
    take_cricket_maint = min(cricket_maint, greens_available)
    left = greens_available - take_cricket_maint
    plant_demand = q_birds * (QUAIL_INTAKE_G_PER_DAY * 7.0 / 1000.0) * QUAIL_PLANT_SHARE
    take_quail_plant = min(plant_demand, left)
    left -= take_quail_plant
    take_cricket_extra = min(max(0.0, cricket_demand - cricket_maint), left)
    left -= take_cricket_extra
    iso_plant_demand = state.isopod_adults * ISOPOD_INTAKE_KG * (1.0 - ISOPOD_MANURE_SHARE)
    iso_juv_demand = iso_juv * ISOPOD_INTAKE_KG * 0.5
    take_isopod_plant = min(iso_plant_demand + iso_juv_demand, left)
    greens_eaten = take_cricket_maint + take_quail_plant + take_cricket_extra + take_isopod_plant
    canopy_after = canopy - greens_eaten
    if canopy_after + 1e-6 < GREENS_FLOOR_KG:
        raise RuntimeError("greens floor raided")
    cricket_got = take_cricket_maint + take_cricket_extra
    cricket_index = 1.0 if cricket_demand <= 1e-12 else cricket_got / cricket_demand
    isopod_got = iso_manure + take_isopod_plant
    isopod_demand = iso_manure_demand + iso_plant_demand + iso_juv_demand
    isopod_index = 1.0 if isopod_demand <= 1e-12 else isopod_got / isopod_demand

    protein_demand = q_birds * (QUAIL_INTAKE_G_PER_DAY * 7.0 / 1000.0) * QUAIL_WORM_SHARE
    fish_eq = fish_equivalent(state)
    fish_demand = fish_eq * FISH_INTAKE_KG
    algae_available = max(0.0, algae - ALGAE_FLOOR_KG)
    algae_for_fish = min(algae_available, FISH_ALGAE_SHARE * fish_demand)
    fish_protein_demand = max(0.0, fish_demand - algae_for_fish)
    algae_after = algae - algae_for_fish
    if algae_after + 1e-6 < ALGAE_FLOOR_KG:
        raise RuntimeError("algae floor raided")

    cricket_allowed = firm_take(
        state.cricket_adults,
        CRICKET_FLOOR,
        state.cricket_adults,
        1.0 - CRICKET_WEEKLY_SURVIVAL,
        lead_weeks=float(CRICKET_NYMPH_WEEKS + 1),
        n_req_forward=CRICKET_FLOOR,
    )
    cricket_cap_heads = min(cricket_allowed, CRICKET_HARVEST_CAP_FRAC * state.cricket_adults)
    isopod_allowed = firm_take(
        state.isopod_adults,
        ISOPOD_FLOOR,
        state.isopod_adults,
        1.0 - ISOPOD_WEEKLY_SURVIVAL,
        lead_weeks=float(ISOPOD_JUVENILE_WEEKS),
        n_req_forward=ISOPOD_FLOOR,
    )
    live_worms = state.worm_breeders + worm_juv
    worm_allowed = firm_take(
        live_worms,
        WORM_FLOOR,
        live_worms,
        WORM_WEEKLY_M,
        lead_weeks=float(WORM_COCOON_WEEKS + WORM_JUVENILE_WEEKS),
        n_req_forward=WORM_FLOOR,
    )
    worm_physical = worm_juv + max(0.0, state.worm_breeders - WORM_FLOOR)
    worm_cap_heads = min(worm_allowed, worm_physical)

    def _share(cap_heads: float, quail_kg: float, fish_kg: float, head_kg: float) -> tuple[float, float]:
        """Split a firm surplus in proportion to demand. Unused surplus stays put."""
        if cap_heads <= 0.0 or head_kg <= 0.0:
            return 0.0, 0.0
        want = (max(0.0, quail_kg) + max(0.0, fish_kg)) / head_kg
        if want <= 0.0:
            return 0.0, 0.0
        scale = min(1.0, cap_heads / want)
        return scale * max(0.0, quail_kg) / head_kg, scale * max(0.0, fish_kg) / head_kg

    # Quail and fish share each protein surplus in proportion to demand.
    # A larger quail flock takes a larger share and leaves less for fish.
    # Neither draw can pass safe_sell_limit, applied above as cap_heads.
    worm_kg_each = WORM_KG_EACH * WORM_JUVENILE_MASS_FRAC
    cricket_for_quail, cricket_for_fish = _share(cricket_cap_heads, protein_demand, fish_protein_demand, CRICKET_KG)
    protein_after_crickets_q = max(0.0, protein_demand - cricket_for_quail * CRICKET_KG)
    protein_after_crickets_f = max(0.0, fish_protein_demand - cricket_for_fish * CRICKET_KG)
    isopod_for_quail, isopod_for_fish = _share(isopod_allowed, protein_after_crickets_q, protein_after_crickets_f, ISOPOD_KG)
    protein_after_iso_q = max(0.0, protein_after_crickets_q - isopod_for_quail * ISOPOD_KG)
    protein_after_iso_f = max(0.0, protein_after_crickets_f - isopod_for_fish * ISOPOD_KG)
    worm_for_quail, worm_for_fish = _share(worm_cap_heads, protein_after_iso_q, protein_after_iso_f, worm_kg_each)

    cricket_harvest = cricket_for_quail + cricket_for_fish
    isopod_harvest = isopod_for_quail + isopod_for_fish
    worm_harvest = worm_for_quail + worm_for_fish
    cricket_adults = state.cricket_adults - cricket_harvest
    isopod_adults = state.isopod_adults - isopod_harvest
    if cricket_harvest > 0.0 and cricket_adults + 1e-6 < CRICKET_FLOOR:
        raise RuntimeError("cricket breeders raided")
    if isopod_harvest > 0.0 and isopod_adults + 1e-6 < ISOPOD_FLOOR:
        raise RuntimeError("isopod breeders raided")
    breeder_spare = max(0.0, state.worm_breeders - WORM_FLOOR)
    worm_from_juv = min(worm_harvest, worm_juv)
    worm_from_breeders = min(breeder_spare, max(0.0, worm_harvest - worm_from_juv))
    worm_juveniles = _take_from_bins(state.worm_juveniles, worm_from_juv)
    worm_breeders = state.worm_breeders - worm_from_breeders
    if worm_from_breeders > 0.0 and worm_breeders + 1e-6 < WORM_FLOOR:
        raise RuntimeError("worm breeders raided")

    quail_protein_got = (
        cricket_for_quail * CRICKET_KG
        + isopod_for_quail * ISOPOD_KG
        + worm_for_quail * WORM_KG_EACH * WORM_JUVENILE_MASS_FRAC
    )
    plant_index = 1.0 if plant_demand <= 1e-12 else take_quail_plant / plant_demand
    protein_index = 1.0 if protein_demand <= 1e-12 else quail_protein_got / protein_demand
    quail_index = _clamp(min(plant_index, protein_index), 0.0, 1.0)
    protein_got_fish = (
        cricket_for_fish * CRICKET_KG
        + isopod_for_fish * ISOPOD_KG
        + worm_for_fish * WORM_KG_EACH * WORM_JUVENILE_MASS_FRAC
    )
    fish_got = algae_for_fish + protein_got_fish
    fish_index = 1.0 if fish_demand <= 1e-12 else _clamp(fish_got / fish_demand, 0.0, 1.0)

    # Feed shortage scales fecundity below. It does not add a second
    # mortality on top of the species weekly rate. A death spiral would hide
    # the sex-ratio comparison the graph is there to show.
    q_surv = 1.0 - WEEKLY_MORTALITY
    worm_surv = 1.0 - WORM_WEEKLY_M
    worm_breeders = draw_binom(rng, worm_breeders, worm_surv, stochastic)
    worm_equiv_now = (
        worm_breeders
        + WORM_JUVENILE_MASS_FRAC * sum(worm_juveniles)
        + WORM_COCOON_MASS_FRAC * sum(state.worm_cocoons)
    )
    worm_room = _room(worm_equiv_now, WORM_CARRYING_MULTIPLE * WORM_FLOOR)
    cocoons_in = draw_count(
        rng,
        worm_breeders * WORM_COCOONS_PER_BREEDER_WEEK * worm_index * worm_room * draw_factor(rng, WORM_SIGMA_FECUNDITY, stochastic),
        stochastic,
    )
    worm_cocoons, cocoons_out = _advance(state.worm_cocoons, cocoons_in, worm_surv, rng, stochastic)
    worm_juveniles, juveniles_out = _advance(worm_juveniles, cocoons_out, worm_surv, rng, stochastic)
    worm_breeders = worm_breeders + juveniles_out

    c_surv = CRICKET_WEEKLY_SURVIVAL
    cricket_adults = draw_binom(rng, cricket_adults, c_surv, stochastic)
    cricket_room = _room(cricket_adults, CRICKET_CAP)
    cricket_eggs_in = draw_count(
        rng,
        cricket_adults * CRICKET_EGGS_PER_ADULT_WEEK * cricket_index * cricket_room * draw_factor(rng, CRICKET_SIGMA, stochastic),
        stochastic,
    )
    cricket_eggs, cricket_hatch = _advance(state.cricket_eggs, cricket_eggs_in, c_surv, rng, stochastic)
    cricket_nymphs, nymphs_out = _advance(state.cricket_nymphs, cricket_hatch, c_surv, rng, stochastic)
    cricket_adults = cricket_adults + nymphs_out

    i_surv = ISOPOD_WEEKLY_SURVIVAL
    isopod_adults = draw_binom(rng, isopod_adults, i_surv, stochastic)
    isopod_room = _room(isopod_adults, ISOPOD_CAP)
    isopod_in = draw_count(
        rng,
        isopod_adults * ISOPOD_RECRUITS_PER_ADULT_WEEK * isopod_index * isopod_room * draw_factor(rng, ISOPOD_SIGMA, stochastic),
        stochastic,
    )
    isopod_juveniles, isopod_grad = _advance(state.isopod_juveniles, isopod_in, i_surv, rng, stochastic)
    isopod_adults = isopod_adults + isopod_grad

    quail_males = draw_binom(rng, state.quail_males, q_surv, stochastic)
    quail_females = draw_binom(rng, state.quail_females, q_surv, stochastic)
    young: list[Cohort] = []
    for cohort in state.quail_young:
        young.append(
            Cohort(
                cohort.age + 1,
                draw_binom(rng, cohort.males, q_surv, stochastic),
                draw_binom(rng, cohort.females, q_surv, stochastic),
                cohort.promoted,
            )
        )
    q_total_now = quail_males + quail_females + sum(c.males + c.females for c in young)
    q_room = _room(q_total_now, QUAIL_CAP)
    eggs_laid = draw_count(
        rng,
        quail_females * QUAIL_EGGS_PER_HEN_WEEK * quail_index * q_room * draw_factor(rng, QUAIL_SIGMA, stochastic),
        stochastic,
    )
    quail_eggs, hatching = _advance(state.quail_eggs, eggs_laid, 1.0, rng, stochastic)
    chicks = draw_binom(rng, hatching, HATCH_RATE, stochastic)
    chick_f = draw_binom(rng, chicks, SEX_RATIO_FEMALE, stochastic)
    chick_m = max(0.0, chicks - chick_f)
    if chick_m + chick_f > 0.0:
        young.append(Cohort(0, chick_m, chick_f, False))

    meat_birds = 0.0
    kept: list[Cohort] = []
    for cohort in young:
        if cohort.age == QUAIL_MATURITY_WEEKS and not cohort.promoted:
            take_f = cohort.females * FRAC_FEMALE_TO_BREEDERS * q_room
            take_m = cohort.males * FRAC_MALE_TO_BREEDERS * q_room
            target_m = (quail_females + take_f) * BREEDER_MALES_PER_FEMALE
            take_m = min(take_m, max(0.0, target_m - quail_males))
            breeder_room = max(0.0, QUAIL_BREEDER_CAP - (quail_males + quail_females))
            if take_m + take_f > breeder_room > 0.0:
                scale = breeder_room / (take_m + take_f)
                take_m *= scale
                take_f *= scale
            elif breeder_room <= 0.0:
                take_m = 0.0
                take_f = 0.0
            cohort.males -= take_m
            cohort.females -= take_f
            quail_males += take_m
            quail_females += take_f
            cohort.promoted = True
        if cohort.age >= QUAIL_SLAUGHTER_WEEKS:
            meat_birds += cohort.males + cohort.females
            continue
        kept.append(cohort)
    # Meat is growers finishing the cycle. Founding breeders are not harvested.
    breeder_export = 0.0

    f_surv = FISH_WEEKLY_SURVIVAL
    fish_males = draw_binom(rng, state.fish_males, f_surv, stochastic)
    fish_females = draw_binom(rng, state.fish_females, f_surv, stochastic)
    fish_growout = draw_binom(rng, state.fish_growout, f_surv, stochastic)
    fish_room = _room(fish_headcount(state), FISH_CAP)
    fry_in = draw_count(
        rng,
        fish_females * FISH_FRY_PER_FEMALE_WEEK * fish_index * fish_room * draw_factor(rng, FISH_SIGMA, stochastic),
        stochastic,
    )
    fish_fry, fry_out = _advance(state.fish_fry, fry_in, f_surv, rng, stochastic)
    fish_juveniles, fish_grad = _advance(state.fish_juveniles, fry_out, f_surv, rng, stochastic)
    promote = fish_grad * FISH_PROMOTE_FRAC * _clamp(fish_index, 0.0, 1.0)
    prom_f = 0.5 * promote
    prom_m = 0.5 * promote
    prom_m = min(prom_m, max(0.0, (fish_females + prom_f) * FISH_MALE_PER_FEMALE - fish_males))
    fish_males += prom_m
    fish_females += prom_f
    fish_growout += max(0.0, fish_grad - prom_f - prom_m)
    fish_harvest = min(FISH_HARVEST_FRAC * fish_growout, max(0.0, fish_growout - FISH_GROWOUT_HOLD))
    fish_growout -= fish_harvest
    # Growout harvest does not touch fish breeders. Mortality may later
    # leave the founding count, and that is not an export.

    birds_after = quail_males + quail_females + sum(c.males + c.females for c in kept)
    manure = QUAIL_MANURE_KG * birds_after * (0.35 + 0.65 * quail_index)
    frass = FRASS_PER_KG_FEED * cricket_got
    fish_eq_after = (
        0.15 * sum(fish_fry)
        + 0.45 * sum(fish_juveniles)
        + fish_growout
        + fish_males
        + fish_females
    )
    sludge = FISH_SLUDGE_KG * fish_eq_after
    castings = CASTINGS_PER_KG_FEED * worm_got
    # Attribute worm intake across the pool that remained after isopods,
    # so manure is visible even when stage-1 feedstock covers most of the meal.
    pool_parts = {
        "feedstock": state.feedstock_in,
        "manure": state.manure_in,
        "frass": state.frass_in,
        "sludge": state.sludge_in,
    }
    manure_left = max(0.0, pool_parts["manure"] - iso_manure)
    pool_parts["manure"] = manure_left
    pool_sum = sum(pool_parts.values())
    if pool_sum > 1e-12 and worm_got > 0.0:
        used = min(worm_got, pool_sum) / pool_sum
        feedstock_used = pool_parts["feedstock"] * used
        manure_used = pool_parts["manure"] * used
        frass_used = pool_parts["frass"] * used
        sludge_used = pool_parts["sludge"] * used
    else:
        feedstock_used = manure_used = frass_used = sludge_used = 0.0

    nxt = State(
        worm_cocoons=worm_cocoons,
        worm_juveniles=worm_juveniles,
        worm_breeders=worm_breeders,
        cricket_eggs=cricket_eggs,
        cricket_nymphs=cricket_nymphs,
        cricket_adults=cricket_adults,
        isopod_juveniles=isopod_juveniles,
        isopod_adults=isopod_adults,
        greens_seedling=seedling,
        greens_canopy=canopy_after,
        algae=algae_after,
        quail_eggs=quail_eggs,
        quail_young=kept,
        quail_males=quail_males,
        quail_females=quail_females,
        fish_fry=fish_fry,
        fish_juveniles=fish_juveniles,
        fish_growout=fish_growout,
        fish_males=fish_males,
        fish_females=fish_females,
        castings_greens=castings * CASTINGS_TO_GREENS,
        castings_algae=castings * CASTINGS_TO_ALGAE,
        fish_nutrient=sludge,
        manure_in=manure,
        frass_in=frass,
        sludge_in=sludge,
        feedstock_in=EXTERNAL_FEEDSTOCK_KG,
        quail_floor=state.quail_floor,
    )
    flows = {
        "worm_feed_index": worm_index,
        "cricket_feed_index": cricket_index,
        "quail_feed_index": quail_index,
        "fish_feed_index": fish_index,
        "isopod_feed_index": isopod_index,
        "feedstock_to_worms_kg": feedstock_used,
        "manure_to_worms_kg": manure_used,
        "frass_to_worms_kg": frass_used,
        "sludge_to_worms_kg": sludge_used,
        "isopod_manure_kg": iso_manure,
        "castings_kg": castings,
        "greens_to_crickets_kg": cricket_got,
        "greens_to_quail_kg": take_quail_plant,
        "greens_to_isopods_kg": take_isopod_plant,
        "crickets_to_quail_kg": cricket_for_quail * CRICKET_KG,
        "crickets_to_fish_kg": cricket_for_fish * CRICKET_KG,
        "isopods_to_quail_kg": isopod_for_quail * ISOPOD_KG,
        "worms_to_quail_kg": worm_for_quail * WORM_KG_EACH * WORM_JUVENILE_MASS_FRAC,
        "worms_to_fish_kg": worm_for_fish * WORM_KG_EACH * WORM_JUVENILE_MASS_FRAC,
        "isopods_to_fish_kg": isopod_for_fish * ISOPOD_KG,
        "algae_to_fish_kg": algae_for_fish,
        "quail_eggs_laid": eggs_laid,
        "quail_meat_birds": meat_birds,
        "quail_breeder_export": breeder_export,
        "protein_to_fish_kg": (
            cricket_for_fish * CRICKET_KG
            + isopod_for_fish * ISOPOD_KG
            + worm_for_fish * WORM_KG_EACH * WORM_JUVENILE_MASS_FRAC
        ),
        "fish_harvest": fish_harvest,
        "worm_export_headcount": worm_harvest,
        "worm_allowed_headcount": worm_cap_heads,
        "cricket_harvest_headcount": cricket_harvest,
        "cricket_allowed_headcount": cricket_cap_heads,
        "raid": False,
    }
    return nxt, flows


def observe(state: State, week: int, flows: dict | None = None) -> dict:
    males, females, chicks, growers = quail_birds(state)
    row = {
        "week": week,
        "worm_biomass_kg": worm_biomass_kg(state),
        "worm_breeders": state.worm_breeders,
        "cricket_adults": state.cricket_adults,
        "isopod_adults": state.isopod_adults,
        "greens_canopy_kg": state.greens_canopy,
        "algae_kg": state.algae,
        "quail_males": males,
        "quail_females": females,
        "quail_total": males + females,
        "quail_chicks": chicks,
        "quail_growers": growers,
        "quail_breeder_females": state.quail_females,
        "fish_total": fish_headcount(state),
        "fish_growout": state.fish_growout,
    }
    if flows:
        row.update(flows)
    return row


SERIES = (
    "worm_biomass_kg",
    "worm_breeders",
    "cricket_adults",
    "isopod_adults",
    "greens_canopy_kg",
    "algae_kg",
    "quail_males",
    "quail_females",
    "quail_total",
    "quail_breeder_females",
    "fish_total",
    "fish_growout",
    "quail_feed_index",
    "worm_feed_index",
    "crickets_to_quail_kg",
    "crickets_to_fish_kg",
    "worms_to_quail_kg",
    "worms_to_fish_kg",
    "isopods_to_fish_kg",
    "protein_to_fish_kg",
    "manure_to_worms_kg",
    "feedstock_to_worms_kg",
    "castings_kg",
    "quail_eggs_laid",
    "greens_to_quail_kg",
    "greens_to_crickets_kg",
    "greens_to_isopods_kg",
    "algae_to_fish_kg",
    "isopod_manure_kg",
)


def simulate(
    quail_males: float,
    quail_females: float,
    weeks: int = DEFAULT_WEEKS,
    seed: int = DEFAULT_SEED,
    path_index: int = 0,
    stochastic: bool = True,
) -> list[dict]:
    """Weekly records, including week 0 (the start, before any transition)."""
    if weeks < 1:
        raise ValueError("weeks must be >= 1")
    rng = random.Random(int(seed) + int(path_index) * 10007)
    state = initial_state(quail_males, quail_females)
    rows = [observe(state, 0)]
    for week in range(1, weeks + 1):
        state, flows = step(state, rng, stochastic=stochastic)
        row = observe(state, week, flows)
        if row["worm_export_headcount"] > row["worm_allowed_headcount"] + 1e-6:
            raise RuntimeError("worm export exceeded safe_sell_limit")
        if row["cricket_harvest_headcount"] > row["cricket_allowed_headcount"] + 1e-6:
            raise RuntimeError("cricket harvest exceeded safe_sell_limit")
        if row["quail_breeder_export"] > 0.0:
            raise RuntimeError("quail breeders were exported")
        rows.append(row)
    return rows


def quantile(values: list[float], q: float) -> float:
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0, 1]")
    xs = sorted(float(v) for v in values)
    if not xs:
        raise ValueError("empty sample")
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    weight = pos - lo
    return xs[lo] * (1.0 - weight) + xs[hi] * weight


def ensemble(
    quail_males: float,
    quail_females: float,
    weeks: int = DEFAULT_WEEKS,
    paths: int = DEFAULT_PATHS,
    seed: int = DEFAULT_SEED,
) -> dict:
    """P10 and median of each series. P10 is the harsh path, not a quantity to sell."""
    if paths < 2:
        raise ValueError("paths must be >= 2")
    runs = [
        simulate(quail_males, quail_females, weeks=weeks, seed=seed, path_index=i, stochastic=True)
        for i in range(paths)
    ]
    weeks_ix = [row["week"] for row in runs[0]]
    series: dict[str, dict[str, list[float]]] = {}
    for name in SERIES:
        columns = [[run[t].get(name, 0.0) for run in runs] for t in range(len(weeks_ix))]
        series[name] = {
            "p10": [quantile(col, 0.10) for col in columns],
            "p50": [quantile(col, 0.50) for col in columns],
        }
    return {
        "stage_gate": STAGE_GATE,
        "seed": seed,
        "paths": paths,
        "weeks": weeks_ix,
        "quail_males0": float(quail_males),
        "quail_females0": float(quail_females),
        "series": series,
        "p10_note": (
            "P10 is the 10th percentile across seeded paths at that week. "
            "It is a harsh trajectory. Firm offtake inside each path is still "
            "alpha times surplus, not this percentile and not the median."
        ),
    }


def worm_biomass_doubling_week(seed: int = DEFAULT_SEED) -> dict:
    """First week uncoupled worm biomass is at least twice the start.

    Quail, insects, and fish are absent, so nothing eats the herd. Feedstock
    is ample in this check so the week measures the life-cycle rate, not the
    coupled feed cap. Deterministic. The cocoon rate is an ASSUMPTION chosen
    so this week meets the 13-week stand-in.
    """
    # Ample feedstock: the 13-week stand-in is not a feed cap. The coupled
    # runs keep EXTERNAL_FEEDSTOCK_KG, which can bind later.
    saved_feed = EXTERNAL_FEEDSTOCK_KG
    globals()["EXTERNAL_FEEDSTOCK_KG"] = 1.0e6
    rng = random.Random(seed)
    state = initial_state(0.0, 0.0)
    state.cricket_adults = 0.0
    state.cricket_nymphs = _zeros(CRICKET_NYMPH_WEEKS)
    state.cricket_eggs = _zeros(1)
    state.isopod_adults = 0.0
    state.isopod_juveniles = _zeros(ISOPOD_JUVENILE_WEEKS)
    state.fish_males = 0.0
    state.fish_females = 0.0
    state.fish_growout = 0.0
    state.fish_fry = _zeros(FISH_FRY_WEEKS)
    state.fish_juveniles = _zeros(FISH_JUVENILE_WEEKS)
    state.quail_floor = 0.0
    start = worm_biomass_kg(state)
    week_hit = None
    biomass = start
    try:
        for week in range(1, 80):
            state, _flows = step(state, rng, stochastic=False)
            biomass = worm_biomass_kg(state)
            if week_hit is None and biomass >= 2.0 * start:
                week_hit = week
                break
    finally:
        globals()["EXTERNAL_FEEDSTOCK_KG"] = saved_feed
    return {
        "start_kg": start,
        "doubling_week": week_hit,
        "biomass_kg_at_hit": biomass,
        "target_weeks": WORM_DOUBLING_TARGET_WEEKS,
        "tag": "ASSUMPTION",
        "note": "Deterministic uncoupled herd. Planning fecundity, not a field clutch.",
    }
