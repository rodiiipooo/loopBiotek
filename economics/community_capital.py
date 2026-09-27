#!/usr/bin/env python3
"""Proportional community capital payback and headcount/weight setup CapEx.

Planning math for the open LoopBiotek repo. Dollar inputs are parameters.
Default planning numbers are labeled ASSUMPTION and are not verified
commercial performance.

Stage 1 (worms) in biology/CASCADE.md is the only active spend until Rod
clears a later stage. ``other_capex`` is a caller-supplied hook and defaults
to 0. This module does not open Stage 2+ purchases and does not sell a herd
forward.

R_t is distributable surplus the caller has already computed after the
nutrition stack, operating costs, and Module 11-style reserves.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

EPS = 1e-9

ASSUMPTION_NOTE = (
    "ASSUMPTION: planning value, not verified commercial performance. "
    "Not legal, tax, or securities advice. "
    "Stage 1 (worms) is the only active spend until Rod clears biology/CASCADE.md. "
    "other_capex is a caller-supplied hook (default 0) for a cited setup cost."
)

POST_EQUAL = "equal_per_member"
POST_LABOR = "labor_shares"
POST_PAYBACK_RULES = (POST_EQUAL, POST_LABOR)


def _as_float(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a real number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _nonnegative(name: str, value: float) -> float:
    number = _as_float(name, value)
    if number < 0:
        raise ValueError(f"{name} must be >= 0")
    return number


def _positive(name: str, value: float) -> float:
    number = _as_float(name, value)
    if number <= 0:
        raise ValueError(f"{name} must be > 0")
    return number


def _snap(value: float) -> float:
    if abs(value) <= EPS:
        return 0.0
    return value


@dataclass(frozen=True)
class Member:
    """One person in the pool. ``contribution`` is x_i. ``active`` marks a current resident."""

    member_id: str
    contribution: float
    active: bool = True
    labor_share: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.member_id, str) or not self.member_id.strip():
            raise ValueError("member_id must be a non-empty string")
        object.__setattr__(self, "contribution", _nonnegative("contribution", self.contribution))
        labor = _nonnegative("labor_share", self.labor_share)
        object.__setattr__(self, "labor_share", labor)


@dataclass(frozen=True)
class ShareResult:
    pool: float
    shares: dict[str, float]
    pool_empty: bool


@dataclass(frozen=True)
class PoolEvent:
    """Policy event applied at the start of period ``t`` (0-based).

    kind:
      late_join — junior tranche; does not change locked senior shares
      exit — unpaid capital claim continues; dropped from post-payback
      forfeit — unpaid claim is written off; that share is not given to others
    """

    t: int
    kind: str
    member: Optional[Member] = None
    member_id: Optional[str] = None


@dataclass(frozen=True)
class FoodStockParams:
    """Food-stock setup parameters. Defaults are ASSUMPTION planning values."""

    food_days: float = 90.0
    kcal_per_kg_body_per_day: float = 30.0
    kcal_per_kg_food: float = 3600.0
    usd_per_kg_food: float = 2.5
    basis: str = "kcal_per_kg_body"
    kg_per_person_per_day_at_ref: float = 0.6
    ref_weight_kg: float = 70.0


@dataclass(frozen=True)
class FacilityParams:
    """Facility shell parameters. Defaults are ASSUMPTION planning values.

    ``area_weight_elasticity`` 0 keeps floor area independent of body weight.
    1 scales m²/person in proportion to W / ref_weight_kg.
    """

    usd_per_m2: float = 800.0
    m2_per_person: float = 12.0
    ref_weight_kg: float = 70.0
    area_weight_elasticity: float = 0.0


@dataclass(frozen=True)
class CapexResult:
    food_stock_capex: float
    facility_capex: float
    other_capex: float
    setup_capex: float
    assumption_note: str
    kg_food_per_person_per_day: float
    m2_per_person: float
    H: float
    W: float


@dataclass(frozen=True)
class Coverage:
    pool: float
    x_min: float
    shortfall: float
    surplus_capital: float
    covers: bool
    coverage_ratio: Optional[float]


@dataclass(frozen=True)
class PeriodRow:
    t: int
    surplus: float
    phase: str
    capital_payments: dict[str, float]
    post_payback_payments: dict[str, float]
    cumulative: dict[str, float]
    remaining: dict[str, float]
    remaining_principal: dict[str, float]
    obligation: dict[str, float]
    unallocated: float
    fully_repaid_after: bool


@dataclass(frozen=True)
class Schedule:
    rows: list[PeriodRow]
    shares_by_tranche: list[dict[str, float]]
    pool_empty: bool
    interest_rate_per_period: float
    post_payback: str
    fully_repaid: bool
    cleared_at_period: Optional[int]
    opening_pool: float


class _Claim:
    def __init__(self, member: Member, share: float, tranche: int) -> None:
        self.member_id = member.member_id
        self.contribution = member.contribution
        self.share = share
        self.tranche = tranche
        self.principal = member.contribution
        self.interest_due = 0.0
        self.cumulative = 0.0
        self.active = member.active
        self.labor_share = member.labor_share
        self.forfeited = False

    def owed(self) -> float:
        return self.principal + self.interest_due


def _unique_members(members: Sequence[Member]) -> None:
    seen: set[str] = set()
    for member in members:
        if member.member_id in seen:
            raise ValueError(f"duplicate member_id {member.member_id}")
        seen.add(member.member_id)


def ownership_shares(members: Sequence[Member]) -> ShareResult:
    """s_i = x_i / X. If X = 0, shares are undefined and ``pool_empty`` is true."""

    _unique_members(members)
    pool = sum(member.contribution for member in members)
    if pool <= EPS:
        return ShareResult(pool=0.0, shares={}, pool_empty=True)
    shares = {member.member_id: member.contribution / pool for member in members}
    return ShareResult(pool=pool, shares=shares, pool_empty=False)


def _open_tranche(claims: list[_Claim], tranche_shares: list[dict[str, float]], cohort: Sequence[Member]) -> None:
    _unique_members(cohort)
    existing = {claim.member_id for claim in claims}
    for member in cohort:
        if member.member_id in existing:
            raise ValueError(f"duplicate member_id {member.member_id}")
    pool = sum(member.contribution for member in cohort)
    tranche = len(tranche_shares)
    if pool <= EPS:
        share_map = {member.member_id: 0.0 for member in cohort}
    else:
        share_map = {member.member_id: member.contribution / pool for member in cohort}
    tranche_shares.append(dict(share_map))
    for member in cohort:
        claims.append(_Claim(member, share_map[member.member_id], tranche))


def _tranche_owed(claims: Sequence[_Claim], tranche: int) -> float:
    return sum(claim.owed() for claim in claims if claim.tranche == tranche and not claim.forfeited)


def _total_owed(claims: Sequence[_Claim]) -> float:
    return sum(claim.owed() for claim in claims if not claim.forfeited)


def _apply_capital_payment(claim: _Claim, amount: float) -> float:
    owed = claim.owed()
    amount = min(amount, owed)
    to_interest = min(claim.interest_due, amount)
    claim.interest_due = _snap(claim.interest_due - to_interest)
    to_principal = amount - to_interest
    claim.principal = _snap(claim.principal - to_principal)
    claim.cumulative += amount
    return amount


def _distribute_post(claims: Sequence[_Claim], amount: float, mode: str) -> tuple[dict[str, float], float]:
    post = {claim.member_id: 0.0 for claim in claims}
    active = [claim for claim in claims if claim.active and not claim.forfeited]
    if not active or amount <= EPS:
        return post, amount if amount > EPS else 0.0
    if mode == POST_EQUAL:
        weights = [1.0 for _ in active]
    elif mode == POST_LABOR:
        weights = [claim.labor_share for claim in active]
    else:
        raise ValueError(f"unknown post_payback rule {mode}")
    total_w = sum(weights)
    if total_w <= EPS:
        return post, amount
    for claim, weight in zip(active, weights):
        post[claim.member_id] = amount * (weight / total_w)
    return post, 0.0


def _apply_events(
    events: Sequence[PoolEvent],
    t: int,
    claims: list[_Claim],
    tranche_shares: list[dict[str, float]],
) -> None:
    period_events = [event for event in events if event.t == t]
    by_id = {claim.member_id: claim for claim in claims}
    joins: list[Member] = []
    for event in period_events:
        if event.kind in ("exit", "forfeit"):
            if not event.member_id or event.member_id not in by_id:
                raise ValueError(f"{event.kind} requires an existing member_id")
            claim = by_id[event.member_id]
            claim.active = False
            if event.kind == "forfeit":
                claim.forfeited = True
                claim.principal = 0.0
                claim.interest_due = 0.0
                claim.share = 0.0
                tranche_shares[claim.tranche][claim.member_id] = 0.0
        elif event.kind == "late_join":
            if event.member is None:
                raise ValueError("late_join requires a member")
            joins.append(event.member)
        else:
            raise ValueError(f"unknown event kind {event.kind}")
    if joins:
        _open_tranche(claims, tranche_shares, joins)


def payback_schedule(
    members: Sequence[Member],
    surplus: Sequence[float],
    events: Sequence[PoolEvent] = (),
    interest_rate_per_period: float = 0.0,
    post_payback: str = POST_EQUAL,
) -> Schedule:
    """Pay capital back at locked shares, then switch to the post-payback rule.

    While any obligation remains in a tranche, member i in that tranche receives

        payment_i,t = min(obligation_i,t, s_i * R_available)

    s_i is fixed when the tranche opens (s_i = x_i / X_tranche). A capped
    member stops. Their unclaimed slice is not added to anyone else's share.
    If the tranche is then clear, leftover cash moves to the next (junior)
    tranche. If the tranche still has unpaid principal, leftover cash is
    recorded as unallocated for that period.

    After every tranche is clear, leftover surplus in that same period, and
    every later R_t, follows ``post_payback`` (default: equal per active member).

    ``interest_rate_per_period`` defaults to 0 (principal only). A positive
    rate is an ASSUMPTION: simple interest on outstanding principal at the
    start of the period, retired before principal.
    """

    if post_payback not in POST_PAYBACK_RULES:
        raise ValueError(f"post_payback must be one of {POST_PAYBACK_RULES}")
    rate = _nonnegative("interest_rate_per_period", interest_rate_per_period)
    cashflows = [_nonnegative("R_t", value) for value in surplus]
    _unique_members(members)
    for event in events:
        if isinstance(event.t, bool) or not isinstance(event.t, int):
            raise ValueError("event t must be an integer period index")
        if event.t < 0 or event.t >= len(cashflows):
            raise ValueError(f"event t={event.t} is outside the surplus series")

    claims: list[_Claim] = []
    tranche_shares: list[dict[str, float]] = []
    opening_pool = sum(member.contribution for member in members)
    pool_empty = opening_pool <= EPS
    if members:
        _open_tranche(claims, tranche_shares, members)

    rows: list[PeriodRow] = []
    cleared_at: Optional[int] = None
    for t, cash in enumerate(cashflows):
        _apply_events(events, t, claims, tranche_shares)
        for claim in claims:
            if rate > 0 and not claim.forfeited and claim.principal > 0:
                claim.interest_due += claim.principal * rate
        obligation = {claim.member_id: claim.owed() for claim in claims}
        had_obligation = sum(obligation.values()) > EPS
        available = cash
        unallocated = 0.0
        capital_payments = {claim.member_id: 0.0 for claim in claims}
        if had_obligation:
            gross = cash
            for tranche in range(len(tranche_shares)):
                if _tranche_owed(claims, tranche) <= EPS:
                    continue
                for claim in claims:
                    if claim.tranche != tranche:
                        continue
                    owed = claim.owed()
                    if claim.forfeited or claim.share <= 0 or owed <= EPS:
                        continue
                    raw = claim.share * gross
                    pay = owed if raw + EPS >= owed else raw
                    pay = min(pay, available)
                    paid = _apply_capital_payment(claim, pay)
                    available = _snap(available - paid)
                    capital_payments[claim.member_id] += paid
                if _tranche_owed(claims, tranche) > EPS:
                    unallocated = _snap(unallocated + available)
                    available = 0.0
                    break
                gross = available
        if _total_owed(claims) <= EPS:
            post, held = _distribute_post(claims, available, post_payback)
            unallocated = _snap(unallocated + held)
        else:
            post = {claim.member_id: 0.0 for claim in claims}
        clear_now = _total_owed(claims) <= EPS
        if clear_now and cleared_at is None:
            cleared_at = t
        rows.append(
            PeriodRow(
                t=t,
                surplus=cash,
                phase="capital_recovery" if had_obligation else "post_payback",
                capital_payments=capital_payments,
                post_payback_payments=post,
                cumulative={claim.member_id: claim.cumulative for claim in claims},
                remaining={claim.member_id: claim.owed() for claim in claims},
                remaining_principal={claim.member_id: claim.principal for claim in claims},
                obligation=obligation,
                unallocated=unallocated,
                fully_repaid_after=clear_now,
            )
        )

    fully_repaid = _total_owed(claims) <= EPS
    if not cashflows:
        cleared_at = None
    return Schedule(
        rows=rows,
        shares_by_tranche=tranche_shares,
        pool_empty=pool_empty,
        interest_rate_per_period=rate,
        post_payback=post_payback,
        fully_repaid=fully_repaid,
        cleared_at_period=cleared_at if fully_repaid else None,
        opening_pool=0.0 if pool_empty else opening_pool,
    )


def food_kg_per_person_per_day(W: float, food: Optional[FoodStockParams] = None) -> float:
    """Kilograms of stocked food per person per day, scaled by body weight."""

    params = food if food is not None else FoodStockParams()
    weight = _positive("W", W)
    if params.basis == "kcal_per_kg_body":
        kcal_per_kg_food = _positive("kcal_per_kg_food", params.kcal_per_kg_food)
        kcal_per_kg_body = _nonnegative("kcal_per_kg_body_per_day", params.kcal_per_kg_body_per_day)
        return (kcal_per_kg_body * weight) / kcal_per_kg_food
    if params.basis == "kg_scaled":
        ref = _positive("ref_weight_kg", params.ref_weight_kg)
        kg_ref = _nonnegative("kg_per_person_per_day_at_ref", params.kg_per_person_per_day_at_ref)
        return kg_ref * (weight / ref)
    raise ValueError("food basis must be 'kcal_per_kg_body' or 'kg_scaled'")


def food_stock_capex(H: float, W: float, food: Optional[FoodStockParams] = None) -> float:
    """FoodStockCapEx = H * food_days * kg_per_person_day(W) * $/kg."""

    params = food if food is not None else FoodStockParams()
    headcount = _nonnegative("H", H)
    days = _nonnegative("food_days", params.food_days)
    price = _nonnegative("usd_per_kg_food", params.usd_per_kg_food)
    return headcount * days * food_kg_per_person_per_day(W, params) * price


def facility_m2_per_person(W: float, facility: Optional[FacilityParams] = None) -> float:
    params = facility if facility is not None else FacilityParams()
    weight = _positive("W", W)
    ref = _positive("ref_weight_kg", params.ref_weight_kg)
    area = _nonnegative("m2_per_person", params.m2_per_person)
    elasticity = _as_float("area_weight_elasticity", params.area_weight_elasticity)
    scale = (weight / ref) ** elasticity
    return area * scale


def facility_capex(H: float, W: float, facility: Optional[FacilityParams] = None) -> float:
    """FacilityCapEx = H * m²/person(W) * $/m²."""

    params = facility if facility is not None else FacilityParams()
    headcount = _nonnegative("H", H)
    unit_cost = _nonnegative("usd_per_m2", params.usd_per_m2)
    return headcount * facility_m2_per_person(W, params) * unit_cost


def setup_capex(
    H: float,
    W: float,
    food: Optional[FoodStockParams] = None,
    facility: Optional[FacilityParams] = None,
    other_capex: float = 0.0,
) -> CapexResult:
    """SetupCapEx = FoodStockCapEx + FacilityCapEx + other_capex.

    ``other_capex`` defaults to 0. Pass a cited Stage-1 setup figure when one
    exists. The default does not add quail, cricket, land, algae, or aquaponics cost.
    """

    food_params = food if food is not None else FoodStockParams()
    facility_params = facility if facility is not None else FacilityParams()
    other = _nonnegative("other_capex", other_capex)
    food_cost = food_stock_capex(H, W, food_params)
    facility_cost = facility_capex(H, W, facility_params)
    return CapexResult(
        food_stock_capex=food_cost,
        facility_capex=facility_cost,
        other_capex=other,
        setup_capex=food_cost + facility_cost + other,
        assumption_note=ASSUMPTION_NOTE,
        kg_food_per_person_per_day=food_kg_per_person_per_day(W, food_params),
        m2_per_person=facility_m2_per_person(W, facility_params),
        H=float(H),
        W=float(W),
    )


def equal_contributor_amount(x_min: float, n: int) -> float:
    """Each of n people pays the same amount to fund X_min."""

    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer")
    required = _nonnegative("X_min", x_min)
    return required / n


def pool_coverage(contributions: Sequence[float], x_min: float) -> Coverage:
    """Report whether Σ x_i covers required setup CapEx, including an explicit shortfall."""

    amounts = [_nonnegative("contribution", value) for value in contributions]
    required = _nonnegative("X_min", x_min)
    pool = sum(amounts)
    shortfall = max(0.0, required - pool)
    surplus_capital = max(0.0, pool - required)
    covers = pool + EPS >= required
    ratio = None if required <= EPS else pool / required
    return Coverage(
        pool=pool,
        x_min=required,
        shortfall=shortfall,
        surplus_capital=surplus_capital,
        covers=covers,
        coverage_ratio=ratio,
    )


def _money(value: float) -> str:
    return f"{value:,.2f}"


def _print_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
    widths = [len(header) for header in headers]
    rendered = []
    for row in rows:
        cells = [str(cell) for cell in row]
        rendered.append(cells)
        widths = [max(width, len(cell)) for width, cell in zip(widths, cells)]
    header_line = "  ".join(header.rjust(width) for header, width in zip(headers, widths))
    print(header_line)
    print("  ".join("-" * width for width in widths))
    for cells in rendered:
        print("  ".join(cell.rjust(width) for cell, width in zip(cells, widths)))


def run_example(H: float = 20.0, W: float = 70.0) -> None:
    """Print three planning scenarios: equal shares, 50/12.5, and unequal H/W sizing."""

    sized = setup_capex(H, W)
    x_min = sized.setup_capex
    print("=" * 78)
    print("LoopBiotek community capital payback (planning)")
    print("Stage 1 worms are the only active spend until Rod clears biology/CASCADE.md.")
    print(sized.assumption_note)
    print("=" * 78)
    print()
    print(f"Setup from H={H:g} residents, W={W:g} kg  (default parameters are ASSUMPTION)")
    print(f"  kg food / person / day     {sized.kg_food_per_person_per_day:.4f}")
    print(f"  FoodStockCapEx             ${_money(sized.food_stock_capex)}")
    print(f"  m2 / person                {sized.m2_per_person:.2f}")
    print(f"  FacilityCapEx              ${_money(sized.facility_capex)}")
    print(f"  other_capex hook           ${_money(sized.other_capex)}")
    print(f"  SetupCapEx = X_min         ${_money(x_min)}")
    print(f"  equal contribution, n=5    ${_money(equal_contributor_amount(x_min, 5))}")
    print("  interest_rate_per_period   0 (principal only)")
    print()

    pay_periods = 10
    period_surplus = x_min / pay_periods
    recovery = [period_surplus] * pay_periods
    series = recovery + [period_surplus]

    print("SCENARIO 1 — equal 5 × 20% of X_min")
    equal_members = [Member(f"m{i+1}", x_min / 5.0) for i in range(5)]
    equal = payback_schedule(equal_members, series)
    print("Each dollar of contribution draws the same fraction of R_t. Equal x_i → equal payments.")
    _print_table(
        ["t", "R_t", "pay_each", "cum_capital", "phase"],
        [
            [
                row.t,
                _money(row.surplus),
                _money(row.capital_payments["m1"] + row.post_payback_payments["m1"]),
                _money(row.cumulative["m1"]),
                row.phase,
            ]
            for row in equal.rows
        ],
    )
    print(f"Cleared at period {equal.cleared_at_period}. Later surplus is equal per resident, not a capital claim.")
    print()

    print("SCENARIO 2 — one 50% + four 12.5% of the same X_min")
    skewed = [
        Member("p50", 0.50 * x_min),
        Member("p12a", 0.125 * x_min),
        Member("p12b", 0.125 * x_min),
        Member("p12c", 0.125 * x_min),
        Member("p12d", 0.125 * x_min),
    ]
    skew = payback_schedule(skewed, series)
    first = skew.rows[0]
    per_dollar = first.capital_payments["p50"] / skewed[0].contribution
    print(
        f"Period 0 rate per dollar invested = {per_dollar:.6f} "
        f"(= R_t / X). The 50% member receives 4× the dollars of a 12.5% member."
    )
    _print_table(
        ["t", "R_t", "pay_50", "pay_12.5", "cum_capital_50", "cum_capital_12.5", "phase"],
        [
            [
                row.t,
                _money(row.surplus),
                _money(row.capital_payments["p50"] + row.post_payback_payments["p50"]),
                _money(row.capital_payments["p12a"] + row.post_payback_payments["p12a"]),
                _money(row.cumulative["p50"]),
                _money(row.cumulative["p12a"]),
                row.phase,
            ]
            for row in skew.rows
        ],
    )
    last = skew.rows[-1]
    print(
        "After principal is cleared, the next surplus is split equally "
        f"({_money(last.post_payback_payments['p50'])} each), "
        "so the 50% capital claim does not continue."
    )
    print()

    print("SCENARIO 3 — unequal contributions and H, W sizing")
    unequal_amounts = {
        "c80": 80_000.0,
        "c40": 40_000.0,
        "c20": 20_000.0,
        "c10": 10_000.0,
        "c5": 5_000.0,
    }
    unequal_members = [Member(name, amount) for name, amount in unequal_amounts.items()]
    pool = sum(unequal_amounts.values())
    cover = pool_coverage(list(unequal_amounts.values()), x_min)
    print(
        f"Pool X = ${_money(pool)} against X_min ${_money(x_min)} at H={H:g}, W={W:g}. "
        f"covers={cover.covers}  shortfall=${_money(cover.shortfall)}  "
        f"coverage_ratio={cover.coverage_ratio:.4f}"
    )
    print("Payback still runs on contributed capital only. The shortfall stays unmet.")
    # 20% of principal each paying period, with a leading zero-surplus stretch, then one post period.
    step = pool * 0.2
    unequal_series = [0.0, step, step, step, step, step, pool * 0.1]
    unequal = payback_schedule(unequal_members, unequal_series)
    _print_table(
        ["t", "R_t", "pay_c80", "pay_c5", "cum_capital_80", "cum_capital_5", "unallocated", "phase"],
        [
            [
                row.t,
                _money(row.surplus),
                _money(row.capital_payments["c80"] + row.post_payback_payments["c80"]),
                _money(row.capital_payments["c5"] + row.post_payback_payments["c5"]),
                _money(row.cumulative["c80"]),
                _money(row.cumulative["c5"]),
                _money(row.unallocated),
                row.phase,
            ]
            for row in unequal.rows
        ],
    )
    print("The R_t = 0 period leaves balances unchanged. The last row is post-payback (equal per member).")
    print()
    print("H, W → SetupCapEx and the equal n=5 contribution (ASSUMPTION defaults)")
    grid_rows = []
    cases = [
        (H, W, 0.0),
        (H, W * 90.0 / 70.0, 0.0),
        (H / 2.0, W, 0.0),
        (H, W * 90.0 / 70.0, 1.0),
    ]
    for head, weight, elasticity in cases:
        facility = FacilityParams(area_weight_elasticity=elasticity)
        result = setup_capex(head, weight, facility=facility)
        grid_rows.append(
            [
                f"{head:g}",
                f"{weight:.1f}",
                f"{elasticity:g}",
                _money(result.food_stock_capex),
                _money(result.facility_capex),
                _money(result.setup_capex),
                _money(equal_contributor_amount(result.setup_capex, 5)),
                _money(max(0.0, result.setup_capex - pool)),
            ]
        )
    _print_table(
        ["H", "W_kg", "area_elast", "food", "facility", "X_min", "each_of_5", "shortfall_vs_155k"],
        grid_rows,
    )
    print("area_elast 0 keeps facility area independent of W. area_elast 1 scales m² with W/70 kg.")
    print()
    print("Policy stubs (not legal advice) — late joiner is junior; forfeit does not raise the other share")
    late = payback_schedule(
        [Member("early", 100.0)],
        [40.0, 40.0, 40.0, 40.0, 40.0],
        events=[PoolEvent(2, "late_join", Member("late", 100.0))],
    )
    print("Late joiner of 100 at t=2, senior principal 100, R_t=40:")
    for row in late.rows:
        late_pay = row.capital_payments.get("late", 0.0)
        print(
            f"  t={row.t}  early={row.capital_payments['early']:.0f}  "
            f"late={late_pay:.0f}  early_remaining={row.remaining_principal['early']:.0f}"
        )
    forfeited = payback_schedule(
        [Member("stay", 100.0), Member("leave", 100.0)],
        [100.0],
        events=[PoolEvent(0, "forfeit", member_id="leave")],
    )
    row = forfeited.rows[0]
    print(
        f"Forfeit at t=0: stay_pay={row.capital_payments['stay']:.0f}  "
        f"leave_pay={row.capital_payments['leave']:.0f}  "
        f"unallocated={row.unallocated:.0f}  stay_remaining={row.remaining_principal['stay']:.0f}"
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Community capital payback and H,W setup CapEx examples")
    parser.add_argument("--H", type=float, default=20.0, help="average daily resident count")
    parser.add_argument("--W", type=float, default=70.0, help="average resident body weight, kg")
    args = parser.parse_args()
    run_example(H=args.H, W=args.W)


if __name__ == "__main__":
    main()
