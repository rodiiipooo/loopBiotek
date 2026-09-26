"""Stage-4 jumbo Coturnix meat-rate screen.

Stage 1 worms remain the source of record for spend. Nothing here authorizes
a kit purchase. Capacities that the Grit listing does not state are marked
ASSUMED in ``SOURCES.md``.

Worked example (y=5 males, z=15 females, U=1 kit, c_bar=2 lb/week):

- pipeline ready at day 77 (21-day setter cycle + 56-day jumbo finish)
- housing-limited rate 37.5 birds/week * 0.77 lb = 28.875 lb/week (≈ 28.9)
- prepaid F_0 = E[P_comp] / (1 + r_prime)^T
"""

from __future__ import annotations

import math
from typing import Optional

# --- Kit: Grit / Hatching Time Quail Professional Kit (Cimuka QUAIL-PROKIT) ---
# SOURCED from the product page unless marked ASSUMED.
INCUBATOR_EGGS_PER_BATCH = 216
KIT_PRICE_USD = 3449.99
KIT_URL = (
    "https://store.grit.com/products/quail-professional-kit?variant=47213766246652"
)

# Standing-bird caps. Brooder, jumbo grow-out, and breeder counts are not
# printed on the product page; they are planning assumptions for this kit's
# 5-layer Cimuka stack. See SOURCES.md.
BROODER_CAP = 150
GROWOUT_CAP_JUMBO = 75
BREEDER_CAP = 45
GROWOUT_LAYERS = 5
BIRDS_PER_GROWOUT_LAYER_JUMBO = 15  # 5 * 15 = 75

# Stage lengths.
# Biological incubation for Coturnix is 17 days (MSU Extension). The
# operational setter/hatcher cycle used here is 21 days, matching
# reference/loop_params.xlsx as extracted in
# climate/thermal-model/PARAMS_FROM_XLSX.md (216 eggs / 21 days = 72 eggs/week).
INCUBATION_DAYS_BIOLOGICAL = 17
INCUBATION_DAYS = 21
BROODER_DAYS = 28  # Grit: first 4 weeks of life
GROWOUT_DAYS = 14  # Grit: weeks 4-6 (the published grow-out window)
MEAT_AGE_DAYS = 56  # ASSUMED jumbo table age (8 weeks), longer than the 6-week cage move
PIPELINE_DAYS = INCUBATION_DAYS + MEAT_AGE_DAYS  # 77

# Housing throughput. Brooder 150 / 4 weeks and jumbo grow-out 75 / 2 weeks
# bind at the same 37.5 birds/week. An 8-week finish needs more standing
# space than brooder+grow-out if that weekly rate is held the whole way;
# SPEC.md states that limit. This module still reports the housing-window
# rate the worked example asks for.
BIRDS_PER_WEEK_HOUSING = BROODER_CAP / (BROODER_DAYS / 7.0)  # 37.5

# Body weight. 16 oz live is the top of advertised jumbo Coturnix claims.
# 0.77 RTC yield is optimistic. Product is the ≈28.9 lb/week screen.
LIVE_LB = 1.0
DRESS_FRAC = 0.77
DRESSED_LB = LIVE_LB * DRESS_FRAC  # 0.77

# Reproduction. 6 eggs/hen/week is inside a high Coturnix lay rate.
# Fertility 0.90 is the Padgett & Ivey (1959) result for 5 males : 15 females.
EGGS_PER_HEN_WEEK = 6.0
FERTILITY_AT_ADEQUATE_MALES = 0.90
MIN_MALES_PER_FEMALE = 1.0 / 5.0
HATCH_RATE = 0.80
SURVIVAL_TO_PROCESS = 0.95

# Fed H.15 bank prime loan, 2026-09-24 column, release dated 2026-09-25.
PRIME_RATE = 0.07
PRIME_AS_OF = "2026-09-24"
# Screening composite for the worked prepaid example. Not the mean of the
# distributor quotes in SOURCES.md (those are higher). ASSUMED anchor.
E_P_COMP_USD_PER_LB = 12.4633


def fertility(y: float, z: float) -> float:
    """Egg fertility from the male:female founder ratio.

    y is founder males, z is founder females. At or above 1 male per 5
    females, fertility stays at the Padgett & Ivey 0.90 benchmark. Below
    that ratio it scales down linearly. No females means no fertile eggs.
    """
    if z <= 0 or y <= 0:
        return 0.0
    ratio = y / z
    if ratio >= MIN_MALES_PER_FEMALE:
        return FERTILITY_AT_ADEQUATE_MALES
    return FERTILITY_AT_ADEQUATE_MALES * (ratio / MIN_MALES_PER_FEMALE)


def _birds_per_week(y: float, z: float, U: float) -> float:
    """Housing- and egg-limited meat birds finished per week, per the screen."""
    if U <= 0:
        return 0.0
    eggs_week = max(0.0, z) * EGGS_PER_HEN_WEEK
    incubator_eggs_week = (INCUBATOR_EGGS_PER_BATCH / (INCUBATION_DAYS / 7.0)) * U
    chicks_week = min(eggs_week, incubator_eggs_week) * fertility(y, z) * HATCH_RATE * SURVIVAL_TO_PROCESS
    housing_birds_week = BIRDS_PER_WEEK_HOUSING * U
    return min(chicks_week, housing_birds_week)


def production_rate(t: float, y: float = 5, z: float = 15, U: float = 1) -> float:
    """Dressed meat lb/week at day ``t``.

    Zero until the pipeline day (day 77 in the sample). After that, the
    housing-limited steady rate. For the sample this is 37.5 * 0.77 lb.
    """
    if t < PIPELINE_DAYS:
        return 0.0
    return _birds_per_week(y, z, U) * DRESSED_LB


def production_rate_required(c_bar: float) -> float:
    """Dressed lb/week the flock must deliver to cover average consumption."""
    if c_bar < 0:
        raise ValueError("c_bar must be non-negative")
    return float(c_bar)


def t_ready(c_bar: float, y: float = 5, z: float = 15, U: float = 1) -> Optional[int]:
    """First day the steady rate can cover ``c_bar`` lb/week.

    Returns None when even the steady rate is below consumption.
    """
    if production_rate(PIPELINE_DAYS, y, z, U) + 1e-12 < c_bar:
        return None
    return PIPELINE_DAYS


def sustain_inventory_lb(
    c_bar: float, t: float, y: float = 5, z: float = 15, U: float = 1
) -> float:
    """Pounds of meat that must already be on hand at day ``t``.

    Before ``t_ready`` the pipeline has not started, so the buffer is
    ``c_bar`` times the remaining weeks. At and after ready, a rate at or
    above ``c_bar`` carries the flow and the buffer is zero. Infinite when
    the steady rate can never cover ``c_bar``.
    """
    ready = t_ready(c_bar, y, z, U)
    if ready is None:
        return math.inf
    if t >= ready:
        return 0.0
    return c_bar * (ready - t) / 7.0


def can_sustain(
    c_bar: float, t: float, y: float = 5, z: float = 15, U: float = 1
) -> bool:
    """True when day ``t`` is at or past ready and the rate covers ``c_bar``."""
    ready = t_ready(c_bar, y, z, U)
    return ready is not None and t >= ready


def kits_needed(c_bar: float, y: float = 5, z: float = 15) -> int:
    """Whole Quail Professional Kits so steady meat rate covers ``c_bar``."""
    per_kit = production_rate(PIPELINE_DAYS, y, z, 1)
    if per_kit <= 0:
        raise ValueError("one kit produces no meat at this founder ratio")
    return int(math.ceil(c_bar / per_kit - 1e-9))


def population(t: float, y: float = 5, z: float = 15, U: float = 1) -> dict:
    """Standing inventory snapshot. Founders occupy the breeder cage.

    Brooder and grow-out fill linearly from hatch day to pipeline day, then
    sit on the kit caps. Meat birds per week are zero until day 77.
    """
    if t < INCUBATION_DAYS:
        frac = 0.0
    elif t >= PIPELINE_DAYS:
        frac = 1.0
    else:
        frac = (t - INCUBATION_DAYS) / (PIPELINE_DAYS - INCUBATION_DAYS)
    birds_week = _birds_per_week(y, z, U) if t >= PIPELINE_DAYS else 0.0
    return {
        "day": t,
        "founder_males": y,
        "founder_females": z,
        "breeders": min(BREEDER_CAP * U, max(0.0, y) + max(0.0, z)),
        "eggs_in_incubator": INCUBATOR_EGGS_PER_BATCH * U * (1.0 if t >= 0 else 0.0),
        "brooder": BROODER_CAP * U * frac,
        "grow_out": GROWOUT_CAP_JUMBO * U * frac,
        "meat_birds_per_week": birds_week,
        "r_prod_lb_per_week": production_rate(t, y, z, U),
    }


def fair_forward_price_per_lb(expected_price: Optional[float] = None) -> float:
    """Expected comparable meat price E[P_comp], USD per lb.

    This is the delivery-date expectation. The prepaid contract discounts it.
    """
    if expected_price is None:
        return E_P_COMP_USD_PER_LB
    return float(expected_price)


def fair_prepaid_contract(
    expected_price: Optional[float] = None,
    r_prime: float = PRIME_RATE,
    T: float = 0.5,
) -> float:
    """Fair prepaid price F_0 = E[P_comp] / (1 + r_prime)^T, USD per lb.

    ``T`` is years. ``r_prime`` is the annual bank prime rate (decimal).
    """
    if T < 0:
        raise ValueError("T must be non-negative")
    if r_prime <= -1:
        raise ValueError("r_prime must be greater than -1")
    return fair_forward_price_per_lb(expected_price) / (1.0 + r_prime) ** T
