#!/usr/bin/env python3
"""Which orders to accept without starving the cascade or the breeding herd.

Stage 4 planning only. Stage 1 worms remain the only spend. Nothing here places
a live order, quotes a buyer, or authorizes a purchase.

The operator knob is ``R_min``: average monthly revenue over the next ``H``
months (default 3). Default ``R_min`` is $3,000, the planning figure in
``economics/MARGIN_3K_BACKSOLVE.md``. This gate compares revenue, not
contribution. Contribution is a second check, and only when a variable cost
exists. That cost is an ASSUMPTION.

``g`` is not chosen first. After a sale, every feed edge and every Ne floor
still has to clear. The implied ``g_s`` is 0 on that retained stock: do not
shrink it. Biological doubling is reported beside it. It is not the target.

``sellable_for_growth`` is still the weekly growth helper. ``g`` there is a
fraction per week, the same clock as ``M_WEEKLY``. ``g = 0.01`` means one
percent per week. ``t`` is a whole number of weeks. ``accept_order`` uses that
helper as an extra cap only when the operator explicitly passes ``g``.

The biological stand-in is the ops-dashboard doubling time:

    rho = 2 ** (1 / doubling_weeks)

That doubling time is an ASSUMPTION (worms 13 weeks, quail 26 weeks). A lump
sale of ``S`` heads today still sustains ``g`` through week ``t`` when

    (N - S) * rho**t >= N * (1 + g)**t

which rearranges to

    S <= N * (1 - (1 + g)**t / rho**t)

when ``rho > 1 + g``. Otherwise nothing is spare and the allowed sale is 0.

That growth cap is then cut by ``safe_sell_limit`` (firm surplus, and the
mortality proxy that keeps the forward breeder need), by the genetics floor
from ``keep_floor`` / ``cull_plan`` (17 males and 51 females for Coturnix at
the default Ne), and, for a delivery at week ``t``, by the inverse of
``birds_now_for_demand`` and ``flock_today``.

Missing herd counts, a missing doubling time, or a helper that cannot answer
fail closed: allowed = 0.
"""

from __future__ import annotations

import importlib
import inspect
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_RESEARCH = _HERE.parent
for _sub in ("synergy", "genetics", "quail"):
    _path = str(_RESEARCH / _sub)
    if _path not in sys.path:
        sys.path.insert(0, _path)
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import delivery  # noqa: E402
import engine  # noqa: E402
import reproduction as genetics  # noqa: E402
from circular_buffers import (  # noqa: E402
    ALPHA,
    BUFFER_WEEKS,
    FAIRNESS,
    M_WEEKLY,
    R_INF,
    R_TBILL,
    SAFETY_FRAC,
    birds_now_for_demand,
    breed_floor,
    fair_prepaid,
    margin_backsolve,
    safe_sell_limit,
)

STAGE_GATE = (
    "Stage 4 planning only. Stage 1 worms remain the only spend. "
    "No live trading and no CapEx purchase."
)

# ASSUMPTION. economics/MARGIN_3K_BACKSOLVE.md records $3.169/lb variable cost
# times the 0.585 lb dress weight, which is about $1.85 per bird. The source
# JSON is not in this checkout, so this stays a planning placeholder.
QUAIL_VAR_COST_PER_BIRD = 1.85
QUAIL_VAR_COST_TAG = (
    "ASSUMPTION $1.85/bird. MARGIN_3K_BACKSOLVE planning lock $3.169/lb "
    "times dress weight ~0.585 lb. Not an invoice."
)

# ASSUMPTION. Path C on that same page: $1,644 cash margin on $2,000 worm
# revenue, ratio 0.822. Variable share of revenue is the rest. Not a farm cost.
WORM_CASH_MARGIN_RATIO = 0.822
WORM_OPEX_FRACTION = 1.0 - WORM_CASH_MARGIN_RATIO
WORM_OPEX_TAG = (
    "ASSUMPTION worm opex is 17.8% of prepaid revenue "
    "(1 - 0.822 from MARGIN_3K_BACKSOLVE path C)."
)

# Operator-facing target is REVENUE, not contribution. The $3,000 figure is the
# planning target on economics/MARGIN_3K_BACKSOLVE.md (that page also shows a
# contribution backsolve). Not a measured bill and not permission to buy birds.
DEFAULT_R_MIN = 3000.0
DEFAULT_H_MONTHS = 3
DEFAULT_R_MIN_TAG = (
    "Primary gate is average monthly REVENUE, default $3,000 over 3 months, "
    "from economics/MARGIN_3K_BACKSOLVE.md. Contribution is a secondary "
    "ASSUMPTION check when a variable cost exists."
)
# Older calls passed M_min. It is the same dollar knob, read as revenue.
DEFAULT_M_MIN = DEFAULT_R_MIN
DEFAULT_M_MIN_TAG = DEFAULT_R_MIN_TAG

# Cyclic feed. This is the order-control graph, not the Stage-1 spend order
# in biology/CASCADE.md. Stage 1 worms remain the only spend.
# algae (nutrient water) → plants
# plants → worms, crickets, and quail (edible plants)
# worms → fish and quail
# crickets → fish and quail
CASCADE_EDGES = (
    ("algae", "plants", "enriched nutrient water"),
    ("plants", "worms", "plant product and waste"),
    ("plants", "crickets", "plant product and waste"),
    ("plants", "quail", "edible plants"),
    ("worms", "fish", "worms"),
    ("worms", "quail", "worms"),
    ("crickets", "fish", "crickets"),
    ("crickets", "quail", "crickets"),
)
# greens is the herd-book name for the plant node.
NODE_ALIASES = {"greens": "plants", "vegetables": "plants", "fruit": "plants", "fruits": "plants"}

# ASSUMPTION weekly ration: upstream herd-units per downstream head.
# Not a measured diet. Algae and plant edges have no default rate; those
# edges fail closed until feed_rates or feed_reserve_heads is set.
# The stock that must stay is rate * downstream breed floor * BUFFER_WEEKS.
ASSUMPTION_FEED_PER_WEEK = {
    ("worms", "quail"): 20.0,
    ("worms", "fish"): 20.0,
    ("crickets", "quail"): 10.0,
    ("crickets", "fish"): 10.0,
}
ASSUMPTION_FEED_TAG = (
    "ASSUMPTION ration, upstream units per downstream head per week. "
    "Not a measured diet. Override with policy['feed_rates']. "
    "Buffer on hand is that rate times the downstream breed floor times "
    f"{BUFFER_WEEKS:g} weeks."
)

# Species this gate knows how to sex. Doubling times for worms and quail come
# from engine.SPECIES. Anything else needs state["doubling_weeks"] or the
# growth cap is 0.
SPECIES_META = {
    "worms": {"sexed": False, "females_per_male": None, "stage": "Stage 1 worms. This module does not authorize spend."},
    "crickets": {"sexed": False, "females_per_male": None, "stage": "Stage 2 planning. Not a purchase."},
    "isopods": {"sexed": False, "females_per_male": None, "stage": "Stage 2 planning. Not a purchase."},
    "greens": {"sexed": False, "females_per_male": None, "stage": "Stage 3 planning. Not a purchase."},
    "plants": {"sexed": False, "females_per_male": None, "stage": "Stage 3 planning. Not a purchase. Aquaponic vegetables, fruits, and plants."},
    "algae": {"sexed": False, "females_per_male": None, "stage": "Stage 3 planning. Not a purchase."},
    "quail": {"sexed": True, "females_per_male": 3.0, "stage": "Stage 4 quail planning. Not a purchase."},
    "fish": {"sexed": True, "females_per_male": 1.0, "stage": "Stage 5 fish planning. Not a purchase."},
}

_FLOCK_HAS_SUSTAIN = "sustain_peak" in inspect.signature(delivery.flock_today).parameters
_FLOCK_CACHE: dict[tuple[int, float], tuple[float | None, str | None]] = {}
_HEAD_TOL = 1e-6


@dataclass
class AcceptDecision:
    """One gate result. ``accept`` is true only when every reason list is empty."""

    accept: bool
    reasons: list[str]
    caps: dict
    residuals: dict
    reservations: dict
    notes: list[str] = field(default_factory=list)
    stage_gate: str = STAGE_GATE

    def to_dict(self) -> dict:
        return asdict(self)


def quail_planning_state(males: float, females: float, n0: float | None = None) -> dict:
    """Headcounts for a Coturnix planning check. ``n0`` defaults to the Ne floor.

    ``n0`` is the breed-floor anchor (founders / safety), not today's flock.
    Set it below ``n_now`` or the surplus is zero and nothing can be sold.
    """
    anchor = float(_genetics_floor("quail") if n0 is None else n0)
    return {
        "n_now": float(males) + float(females),
        "n_males": float(males),
        "n_females": float(females),
        "n0": anchor,
        "n_start": anchor,
        "n_safety": anchor,
    }


def default_price_fn(order: dict, state: dict | None = None) -> dict | None:
    """USD per order unit from ``fair_prepaid`` / ``F_prelim``.

    Inflation 2.7%, 3-month bill 4.01%, fairness 0.9. Spot is the engine
    shelf price. Returns None when this checkout has no spot for the species.
    """
    del state  # the quote does not depend on the herd
    species = str(order.get("species") or "")
    if species not in engine.SPECIES:
        return None
    week = order.get("week")
    if week is None:
        return None
    try:
        horizon = float(week)
    except (TypeError, ValueError):
        return None
    if horizon < 0:
        return None
    spot = float(engine.SPECIES[species].spot_usd_per_unit)
    quoted = fair_prepaid(spot, horizon / 52.0, r_inf=R_INF, r_tbill=R_TBILL, fairness=FAIRNESS)
    unit = _order_unit(order, species)
    per_lb = float(quoted["F_prelim"])
    if unit == "lb":
        usd = per_lb
    elif unit == "head":
        per_head = _lb_per_head(species)
        if per_head is None:
            return None
        usd = per_lb * per_head
    else:
        return None
    return {
        "usd_per_unit": usd,
        "unit": unit,
        "F_prelim": per_lb,
        "T_years": horizon / 52.0,
        "r_inf": R_INF,
        "r_tbill": R_TBILL,
        "fairness": FAIRNESS,
        "quote": quoted,
    }


def sellable_for_growth(
    species: str,
    state: dict | None,
    g: float,
    t: int,
    n_sales_horizon: list | dict | None = None,
    *,
    delivery_cap: bool = True,
) -> dict:
    """Heads that can be sold now, and at week ``t``, while growth stays at ``g``.

    ``g`` is per week. ``t`` is whole weeks.

    With ``n_sales_horizon`` (a list of ``{week, heads}`` or ``{week, lb}``, or a
    ``{week: heads}`` map), ``feasible`` says whether that schedule keeps the
    terminal herd on ``N * (1+g)**t`` and off the breed floor. ``residual`` is
    extra heads still sellable at week ``t``. An unreadable schedule or missing
    herd data returns allowed 0 and ``feasible`` false.

    ``delivery_cap`` adds the quail ``flock_today`` inverse on the week-``t``
    delivery. The weekly income walk turns it off; it does not change ``allowed``.
    """
    key = str(species or "").strip().lower()
    blank = _blank(key, g, t)
    weeks = _whole_weeks(t)
    rate = _growth_rate(g)
    if weeks is None or rate is None:
        blank["reasons"] = ["g must be >= 0 and t must be a whole number of weeks"]
        return blank
    loaded = _load_herd(key, state)
    if loaded is None:
        blank["reasons"] = [_herd_problem(key, state)]
        blank["g_per_week"] = rate
        blank["t_weeks"] = weeks
        return blank
    rho = _rho(key, state or {})
    if rho is None:
        blank["reasons"] = [
            "doubling time missing; growth cap fail closed at 0. "
            "Pass state['doubling_weeks'] or use worms/quail from the ops-dashboard stub."
        ]
        blank["g_per_week"] = rate
        blank["t_weeks"] = weeks
        return blank

    floors = _floors(key, loaded)
    firm = _firm_sex_cap(key, loaded, weeks, floors)
    growth_now = _growth_lump(loaded["n_now"], rate, weeks, rho)
    allowed = _nonneg_min(growth_now, firm["cap"])
    by_t, by_caps = _delivery_heads(key, loaded, rate, weeks, rho, floors, delivery_cap)
    # safe_sell_limit compounds survival only (no births). If that proxy will
    # not release a single animal over this lead, a delivery inside the same
    # lead is refused too. The doubling stand-in is not allowed to overrule it.
    delivery_note = by_caps.get("reason")
    if firm["safe_sell"] <= _HEAD_TOL and firm["sex"] > _HEAD_TOL:
        by_t = 0.0
        delivery_note = (
            "safe_sell_limit releases 0 over this lead (mortality proxy, no births); "
            "delivery cap fail closed at 0"
        )
    binding = _binding(
        [("growth", growth_now), ("firm_or_ne", firm["cap"])]
    )
    schedule = None
    feasible = True
    residual = allowed
    reasons: list[str] = []
    if delivery_note:
        reasons.append(delivery_note)
    if firm["reason"]:
        reasons.append(firm["reason"])
        allowed = 0.0
        by_t = 0.0
        feasible = False
        residual = 0.0
        binding = "fail_closed"
    elif n_sales_horizon is not None:
        schedule, schedule_reason = _normalize_schedule(n_sales_horizon, key)
        if schedule_reason:
            feasible = False
            residual = 0.0
            reasons.append(schedule_reason)
        else:
            forecast = _forecast(key, loaded, rate, weeks, rho, floors, schedule)
            feasible = forecast["feasible"]
            residual = forecast["residual"] if feasible else 0.0
            reasons.extend(forecast["reasons"])

    return {
        "species": key,
        "unit": "head",
        "allowed": allowed,
        "allowed_lb": _heads_to_lb(key, allowed),
        "allowed_by_t": by_t,
        "allowed_by_t_lb": _heads_to_lb(key, by_t),
        "g_per_week": rate,
        "t_weeks": weeks,
        "rho_per_week": rho,
        "doubling_weeks": _doubling_weeks(key, state or {}),
        "doubling_tag": _doubling_tag(key, state or {}),
        "feasible": feasible,
        "residual": residual,
        "residual_lb": _heads_to_lb(key, residual),
        "reasons": reasons,
        "binding": binding,
        "caps": {
            "growth_now": growth_now,
            "firm_or_ne": firm["cap"],
            "safe_sell_allowed_firm": firm["safe_sell"],
            "sex_surplus": firm["sex"],
            "peak_meat": firm["peak"],
            "growth_at_t": by_caps["growth_at_t"],
            "pipeline": by_caps["pipeline"],
            "flock_today": by_caps["flock_today"],
            "firm_at_t": by_caps["firm_at_t"],
        },
        "floor": floors,
        "schedule": schedule,
        "fail_closed": False,
        "formula": (
            "S_now <= N * (1 - (1+g)^t / rho^t), then safe_sell_limit and the "
            "Ne/keep floor. rho = 2^(1/doubling_weeks). g is per week. "
            "A delivery at t also has to fit birds_now_for_demand and, for quail, flock_today."
        ),
        "stage_gate": STAGE_GATE,
        "stage": SPECIES_META.get(key, {}).get("stage", "Unknown species. Fail closed if counts are thin."),
    }


def order_roi(
    order: dict,
    state: dict | None,
    price_fn=None,
    hurdle: float = 0.0,
) -> dict:
    """Contribution and ROI for one order.

    Revenue is ``qty * price``. The default price is ``F_prelim``.

    Variable cost is the ASSUMPTION table in this module. Opportunity cost is
    the growth those heads would still have added by the delivery week if they
    had stayed:

        opp_heads = H * ((1 + g) ** t - 1)
        opp_cost = opp_heads * max(0, revenue_per_head - var_per_head)

    The heads in the order are already in ``revenue``. Only the growth increment
    is opportunity. ``g`` comes from ``order['g']`` or ``state['g']`` (else 0).
    ``t`` is ``order['opp_weeks']`` or the delivery week.

    Capital tied defaults to variable cost (the cash sunk to fill the order),
    unless ``order['capital_tied_usd']`` is set.

        contribution = revenue - var_cost - opp_cost
        ROI = contribution / capital_tied
        accept_hurdle_met = ROI >= hurdle or contribution >= 0

    Missing price, missing variable cost, or non-positive capital fails closed
    (``accept_hurdle_met`` false).
    """
    species = str((order or {}).get("species") or "").strip().lower()
    hurdle_v = _optional_float(hurdle)
    if hurdle_v is None:
        hurdle_v = 0.0
    heads = _order_heads(order or {}, species) if order else None
    week = _whole_weeks((order or {}).get("week")) if order else None
    reasons: list[str] = []
    if not order or heads is None or heads < 0 or week is None:
        reasons.append("order species, quantity, or delivery week is missing")
    if state is None or _load_herd(species, state) is None:
        reasons.append("herd state is missing; ROI fail closed")
    quote = None
    usd_per_unit = None
    if not reasons:
        fn = price_fn or default_price_fn
        try:
            quote = fn(order, state)
        except Exception as err:  # noqa: BLE001 — a bad quote must not open the gate
            reasons.append(f"price_fn failed ({err}); fail closed")
            quote = None
        usd_per_unit = _usd_per_unit(quote)
        if usd_per_unit is None:
            reasons.append("no price for this species; fail closed")
        elif usd_per_unit < 0:
            reasons.append("price is negative; fail closed")
    var_pack = _variable_cost(species, heads or 0.0, None)
    if not reasons and var_pack is None:
        reasons.append(f"variable cost for {species} is not in the ASSUMPTION table; fail closed")

    g = 0.0
    if order and order.get("g") is not None:
        parsed = _growth_rate(order.get("g"))
        g = 0.0 if parsed is None else parsed
    elif isinstance(state, dict) and state.get("g") is not None:
        parsed = _growth_rate(state.get("g"))
        g = 0.0 if parsed is None else parsed
    if order and order.get("opp_weeks") is not None:
        opp_weeks = _whole_weeks(order.get("opp_weeks"))
    else:
        opp_weeks = week
    if opp_weeks is None:
        opp_weeks = 0

    revenue = None
    var_cost = None
    opp_heads = None
    opp_cost = None
    contribution = None
    capital = None
    roi = None
    met = False
    if not reasons and usd_per_unit is not None and var_pack is not None and heads is not None:
        qty = float(order["qty"])
        revenue = usd_per_unit * qty
        if var_pack["mode"] == "per_head":
            var_cost = heads * var_pack["per_head"]
        else:
            var_cost = revenue * var_pack["revenue_fraction"]
        if revenue < 0 or var_cost < 0:
            reasons.append("revenue or variable cost went negative; fail closed")
        else:
            price_per_head = revenue / heads if heads > _HEAD_TOL else 0.0
            var_per_head = var_cost / heads if heads > _HEAD_TOL else 0.0
            growth = (1.0 + g) ** int(opp_weeks) - 1.0
            opp_heads = heads * max(0.0, growth)
            opp_cost = opp_heads * max(0.0, price_per_head - var_per_head)
            contribution = revenue - var_cost - opp_cost
            if order.get("capital_tied_usd") is not None:
                capital = _optional_float(order.get("capital_tied_usd"))
            else:
                capital = var_cost
            if capital is None or capital <= 0:
                reasons.append("capital tied must be > 0; fail closed")
                capital = None
            else:
                roi = contribution / capital
                met = bool(roi >= hurdle_v - 1e-12 or contribution >= -1e-9)

    return {
        "species": species,
        "heads": heads,
        "week": week,
        "g_per_week": g,
        "opp_weeks": opp_weeks,
        "revenue": revenue,
        "var_cost": var_cost,
        "var_cost_tag": None if var_pack is None else var_pack["tag"],
        "opp_heads": opp_heads,
        "opp_cost": opp_cost,
        "contribution": contribution,
        "capital_tied": capital,
        "roi": roi,
        "hurdle": hurdle_v,
        "accept_hurdle_met": met and not reasons,
        "reasons": reasons,
        "price": quote if isinstance(quote, dict) else {"usd_per_unit": usd_per_unit},
        "opp_formula": (
            "opp_heads = H * ((1+g)^t - 1); "
            "opp_cost = opp_heads * max(0, revenue_per_head - var_per_head); "
            "contribution = revenue - var_cost - opp_cost; "
            "ROI = contribution / capital_tied"
        ),
        "stage_gate": STAGE_GATE,
    }


class OrderBook:
    """Open reservations. In memory, and optionally a JSON file.

    Reservations are subtracted in full from the firm cap. That can understate
    a staggered book. It does not sell the same surplus twice.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = None if path is None else Path(path)
        self.orders: list[dict] = []
        self.released: list[dict] = []
        if self.path and self.path.exists():
            self.load()

    def reserve(self, order: dict) -> dict:
        species = str(order.get("species") or "").strip().lower()
        week = _whole_weeks(order.get("week"))
        heads = order.get("heads")
        if heads is None:
            heads = _order_heads(order, species)
        else:
            heads = _optional_float(heads)
        if not species or week is None or heads is None or heads <= 0:
            return {"ok": False, "reason": "reservation needs species, week, and positive heads"}
        order_id = str(order.get("id") or self._next_id())
        if any(row["id"] == order_id for row in self.orders):
            return {"ok": False, "reason": f"order {order_id} is already reserved"}
        row = {
            "id": order_id,
            "species": species,
            "heads": float(heads),
            "week": int(week),
            "unit": order.get("unit") or "head",
            "qty": order.get("qty"),
            "buyer": order.get("buyer"),
            "status": "open",
        }
        self.orders.append(row)
        self._save()
        return {"ok": True, "order": dict(row)}

    def release(self, order_id: str) -> dict:
        key = str(order_id)
        kept: list[dict] = []
        found = None
        for row in self.orders:
            if row["id"] == key and found is None:
                found = dict(row)
                found["status"] = "released"
            else:
                kept.append(row)
        if found is None:
            return {"ok": False, "reason": f"unknown order {key}"}
        self.orders = kept
        self.released.append(found)
        self._save()
        return {"ok": True, "order": found}

    def reserved_heads(self, species: str) -> float:
        key = str(species).strip().lower()
        return sum(float(row["heads"]) for row in self.orders if row["species"] == key)

    def schedule(self, species: str) -> list[dict]:
        key = str(species).strip().lower()
        return [
            {"week": int(row["week"]), "heads": float(row["heads"])}
            for row in self.orders
            if row["species"] == key
        ]

    def available_firm(
        self,
        species: str,
        week: int,
        state: dict | None,
        g: float,
        t: int | None = None,
    ) -> dict:
        """Firm heads still free for ``species`` at ``week`` after open reservations."""
        key = str(species).strip().lower()
        delivery_week = _whole_weeks(week)
        horizon = delivery_week if t is None else _whole_weeks(t)
        if delivery_week is None or horizon is None:
            return {
                "species": key,
                "week": week,
                "available": 0.0,
                "reserved_heads": 0.0,
                "fail_closed": True,
                "reason": "week must be a whole number",
                "stage_gate": STAGE_GATE,
            }
        horizon = max(horizon, delivery_week)
        row = sellable_for_growth(key, state, g, horizon)
        gross = row["allowed"] if delivery_week <= 0 else row["allowed_by_t"]
        reserved = self.reserved_heads(key)
        available = max(0.0, float(gross) - reserved)
        return {
            "species": key,
            "week": delivery_week,
            "t_weeks": horizon,
            "gross": gross,
            "reserved_heads": reserved,
            "available": available,
            "available_lb": _heads_to_lb(key, available),
            "unit": "head",
            "fail_closed": bool(row["fail_closed"] and available <= _HEAD_TOL),
            "sellable": row,
            "stage_gate": STAGE_GATE,
        }

    def load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.orders = list(payload.get("orders") or [])
        self.released = list(payload.get("released") or [])

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "stage_gate": STAGE_GATE,
            "orders": self.orders,
            "released": self.released,
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _next_id(self) -> str:
        return f"ord-{1 + len(self.orders) + len(self.released)}"


def _node_name(species: str) -> str:
    key = str(species).strip().lower()
    return NODE_ALIASES.get(key, key)


def _book_key_for_node(cascade_state: dict, node: str) -> str | None:
    """Herd-book key for a feed-graph node. ``plants`` also matches ``greens``."""
    names = [node]
    if node == "plants":
        names.extend(["greens", "plants"])
    seen: list[str] = []
    for name in names:
        if name not in seen:
            seen.append(name)
    for name, herd_key in ((n, n) for n in seen):
        if herd_key in cascade_state:
            return herd_key
    for herd_key in cascade_state:
        if _node_name(herd_key) == node:
            return str(herd_key)
    return None


def _feed_rate(upstream: str, downstream: str, policy: dict | None) -> tuple[float | None, str]:
    rates = {} if not policy else (policy.get("feed_rates") or {})
    for key in ((upstream, downstream), f"{upstream}->{downstream}"):
        if key in rates and rates[key] is not None:
            value = _optional_float(rates[key])
            if value is None or value < 0:
                return None, "bad"
            return value, "policy"
    if (upstream, downstream) in ASSUMPTION_FEED_PER_WEEK:
        return float(ASSUMPTION_FEED_PER_WEEK[(upstream, downstream)]), "ASSUMPTION"
    return None, "missing"


def cascade_feed_plan(
    cascade_state: dict | None,
    policy: dict | None = None,
    pending_heads: dict | None = None,
) -> dict:
    """Retained stock, implied weekly g, and whether every feed edge still clears.

    The operator does not pick ``g``. For each species the retained headcount
    is the breed floor plus the feed buffer. Implied ``g_s`` is 0 when that
    stock is still on hand after the pending sale (do not shrink it). It is
    missing when the sale would cut the buffer. Biological doubling is reported
    next to that and is not the target.

    A feed edge with both ends in the book and no ration fails closed, unless
    the upstream already carries ``feed_reserve_heads``.
    """
    if not isinstance(cascade_state, dict):
        return {
            "edges_clear": False,
            "reasons": ["cascade_state is missing; feed check fail closed"],
            "by_species": {},
            "edges": [],
            "stage_gate": STAGE_GATE,
        }
    pending = pending_heads or {}
    reasons: list[str] = []
    edges: list[dict] = []
    draws: dict[str, float] = {}
    for upstream, downstream, what in CASCADE_EDGES:
        up_key = _book_key_for_node(cascade_state, upstream)
        down_key = _book_key_for_node(cascade_state, downstream)
        if up_key is None or down_key is None:
            continue
        up_herd = _load_herd(up_key, cascade_state.get(up_key))
        down_herd = _load_herd(down_key, cascade_state.get(down_key))
        if up_herd is None or down_herd is None:
            reasons.append(f"{upstream} → {downstream}: herd counts missing; feed edge fail closed")
            edges.append({
                "upstream": upstream,
                "downstream": downstream,
                "what": what,
                "clears": False,
                "reason": "counts missing",
            })
            continue
        rate, rate_tag = _feed_rate(upstream, downstream, policy)
        explicit = _optional_float(up_herd.get("feed_reserve_heads")) or 0.0
        if rate_tag == "bad":
            reasons.append(f"{upstream} → {downstream}: feed rate is not a positive number; fail closed")
            edges.append({"upstream": upstream, "downstream": downstream, "what": what, "clears": False})
            continue
        if rate is None:
            if explicit > 0:
                # One explicit buffer covers every unrated edge out of this upstream.
                draws[up_key] = max(draws.get(up_key, 0.0), explicit)
                edges.append({
                    "upstream": upstream,
                    "upstream_key": up_key,
                    "downstream": downstream,
                    "downstream_key": down_key,
                    "what": what,
                    "rate_per_week": None,
                    "rate_tag": "feed_reserve_heads",
                    "buffer_weeks": float(BUFFER_WEEKS),
                    "draw_heads": explicit,
                    "clears": True,
                })
                continue
            else:
                reasons.append(
                    f"{upstream} → {downstream} ({what}): no ration; fail closed. "
                    "Set policy['feed_rates'] or feed_reserve_heads. " + ASSUMPTION_FEED_TAG
                )
                edges.append({
                    "upstream": upstream,
                    "downstream": downstream,
                    "what": what,
                    "clears": False,
                    "rate_tag": "missing",
                })
                continue
        else:
            down_floor = _floors(down_key, down_herd)["keep"]
            draw = float(rate) * float(down_floor) * float(BUFFER_WEEKS)
        draws[up_key] = draws.get(up_key, 0.0) + draw
        edges.append({
            "upstream": upstream,
            "upstream_key": up_key,
            "downstream": downstream,
            "downstream_key": down_key,
            "what": what,
            "rate_per_week": rate,
            "rate_tag": rate_tag,
            "buffer_weeks": float(BUFFER_WEEKS),
            "draw_heads": draw,
            "clears": True,
        })

    by_species: dict[str, dict] = {}
    for key, herd in cascade_state.items():
        loaded = _load_herd(str(key), herd if isinstance(herd, dict) else None)
        if loaded is None:
            reasons.append(f"{key}: herd counts missing; fail closed")
            by_species[str(key)] = {"edges_clear": False}
            continue
        floors = _floors(str(key), loaded)
        feed_heads = max(float(loaded.get("feed_reserve_heads") or 0.0), draws.get(str(key), 0.0))
        retained = float(floors["keep"]) + feed_heads
        sold = float(pending.get(str(key), pending.get(_node_name(key), 0.0)) or 0.0)
        n_after = float(loaded["n_now"]) - sold
        headroom = n_after - retained
        rho = _rho(str(key), loaded)
        g_bio = None if rho is None else rho - 1.0
        holds = headroom >= -1e-6
        if not holds:
            reasons.append(
                f"{key}: after the sale {n_after:.1f} heads remain, under the "
                f"retained {retained:.1f} (breed floor {floors['keep']:.1f} + feed buffer {feed_heads:.1f})"
            )
        by_species[str(key)] = {
            "retained_heads": retained,
            "breed_floor": float(floors["keep"]),
            "feed_heads": feed_heads,
            "n_now": float(loaded["n_now"]),
            "n_after": n_after,
            "headroom_heads": headroom,
            "g_implied_per_week": 0.0 if holds else None,
            "g_biological_per_week": g_bio,
            "g_note": (
                "Implied g is 0 on the retained stock: do not shrink the breed floor or the feed buffer. "
                "g_biological_per_week is the doubling stand-in, not a target."
            ),
            "edges_clear": holds,
        }
    for edge in edges:
        if not edge.get("clears", False):
            continue
        up_key = edge.get("upstream_key")
        if up_key is None or up_key not in by_species:
            continue
        edge["clears"] = bool(by_species[up_key].get("edges_clear"))
    edges_clear = not reasons and all(edge.get("clears", False) for edge in edges)
    return {
        "edges_clear": edges_clear,
        "reasons": reasons,
        "by_species": by_species,
        "edges": edges,
        "feed_tag": ASSUMPTION_FEED_TAG,
        "stage_gate": STAGE_GATE,
    }


def rank_skus(cascade_state: dict | None, policy: dict | None = None) -> dict:
    """Rank sellable species by revenue toward ``R_min`` per unit of the tightest upstream.

    Score = prepaid revenue per head / upstream units that head consumes per week.
    The denominator is the binding inbound edge: the upstream with the fewest
    weeks of firm surplus cover. A species with no upstream in the book is
    scored on its own head (denominator 1).

    Missing price, or a live inbound edge with no ration, leaves the species
    unranked. The winner is the highest finite score.
    """
    if not isinstance(cascade_state, dict) or not cascade_state:
        return {
            "ranked": [],
            "unranked": [],
            "winner": None,
            "reasons": ["cascade_state is missing; ranking fail closed"],
            "stage_gate": STAGE_GATE,
        }
    rules = policy or {}
    rows: list[dict] = []
    unranked: list[dict] = []
    firm_surplus: dict[str, float] = {}
    for key, herd in cascade_state.items():
        loaded = _load_herd(str(key), herd if isinstance(herd, dict) else None)
        if loaded is None:
            unranked.append({"species": str(key), "reason": "herd counts missing"})
            continue
        floors = _floors(str(key), loaded)
        firm_surplus[str(key)] = _firm_sex_cap(str(key), loaded, 0, floors)["cap"]
    for key in list(cascade_state):
        species = str(key)
        if species not in firm_surplus:
            continue
        revenue = _revenue_per_head(species)
        if revenue is None or revenue <= 0:
            unranked.append({"species": species, "reason": "no prepaid price; fail closed"})
            continue
        inbound = []
        for upstream, downstream, what in CASCADE_EDGES:
            if _node_name(species) != downstream and species != downstream:
                continue
            up_key = _book_key_for_node(cascade_state, upstream)
            if up_key is None:
                continue
            rate, rate_tag = _feed_rate(upstream, downstream, rules)
            if rate is None or rate <= 0:
                unranked.append({
                    "species": species,
                    "reason": f"{upstream} → {downstream} ({what}) has no ration; not ranked",
                })
                inbound = None
                break
            surplus = firm_surplus.get(up_key, 0.0)
            weekly = float(rate)
            cover = surplus / weekly if weekly > 0 else 0.0
            inbound.append({
                "upstream": up_key,
                "what": what,
                "rate_per_week": weekly,
                "rate_tag": rate_tag,
                "upstream_surplus_heads": surplus,
                "weeks_of_cover": cover,
            })
        if inbound is None:
            continue
        if not inbound:
            score = revenue
            bottleneck = species
            units = 1.0
            cover = None
            rate_tag = "own surplus"
        else:
            binding = min(inbound, key=lambda edge: edge["weeks_of_cover"])
            units = float(binding["rate_per_week"])
            score = revenue / units
            bottleneck = binding["upstream"]
            cover = binding["weeks_of_cover"]
            rate_tag = binding["rate_tag"]
        rows.append({
            "species": species,
            "revenue_per_head": revenue,
            "bottleneck": bottleneck,
            "bottleneck_units_per_head": units,
            "weeks_of_cover": cover,
            "score": score,
            "rate_tag": rate_tag,
            "score_formula": "revenue_per_head / bottleneck_units_per_head",
        })
    rows.sort(key=lambda row: row["score"], reverse=True)
    return {
        "ranked": rows,
        "unranked": unranked,
        "winner": None if not rows else rows[0]["species"],
        "objective": "revenue toward R_min per unit of the tightest upstream surplus",
        "feed_tag": ASSUMPTION_FEED_TAG,
        "stage_gate": STAGE_GATE,
    }


def firm_monthly_contribution(
    species: str,
    state: dict,
    g: float,
    H_months: int = 3,
    order: dict | None = None,
    *,
    weeks: int | None = None,
) -> dict:
    """Monthly revenue of the weekly firm surplus, plus contribution when cost is known.

    The operator-facing number is revenue (``min_monthly_revenue``). ``min_monthly``
    is that same revenue figure. Contribution is secondary and is present only
    when the ASSUMPTION variable cost exists.

    Each week the herd sells ``sellable_for_growth(..., t=1).allowed`` and the
    remainder is multiplied by ``rho``. At ``g = 0`` that holds the herd flat,
    which is the implied rule when the operator did not set a growth rate.

    An order inside the window that is larger than that week's take is removed
    anyway. Later weeks then run on the smaller herd.

    Prices are fair prepaid at a 4-week tenor. Opportunity cost is not charged
    again here; it lives on ``order_roi``.
    """
    key = str(species).strip().lower()
    rate = _growth_rate(g)
    loaded = _load_herd(key, state)
    rho = None if loaded is None else _rho(key, loaded)
    if rate is None or loaded is None or rho is None:
        return {
            "ok": False,
            "min_monthly": 0.0,
            "mean_monthly": 0.0,
            "reasons": ["runway inputs missing; fail closed"],
            "weekly_heads": [],
            "stage_gate": STAGE_GATE,
        }
    if weeks is None:
        months = _whole_weeks(H_months)
        if months is None or months < 1:
            return {
                "ok": False,
                "min_monthly": 0.0,
                "mean_monthly": 0.0,
                "reasons": ["H_months must be a positive whole number"],
                "weekly_heads": [],
                "stage_gate": STAGE_GATE,
            }
        span = int(round(months * 52.0 / 12.0))
    else:
        span = int(weeks)
    if span < 1:
        span = 1
    revenue_per = _revenue_per_head(key)
    margin = _margin_per_head(key)
    if revenue_per is None or revenue_per <= 0:
        return {
            "ok": False,
            "min_monthly": 0.0,
            "min_monthly_revenue": 0.0,
            "mean_monthly": 0.0,
            "mean_monthly_revenue": 0.0,
            "min_monthly_contribution": None,
            "contribution_ok": False,
            "target_kind": "revenue",
            "reasons": ["no positive fair revenue per head; runway fail closed"],
            "weekly_heads": [],
            "revenue_per_head": revenue_per,
            "margin_per_head": margin,
            "stage_gate": STAGE_GATE,
        }
    order_heads = None
    order_week = None
    if order is not None:
        order_heads = _order_heads(order, key)
        order_week = _whole_weeks(order.get("week"))
        if order_heads is None or order_week is None:
            return {
                "ok": False,
                "min_monthly": 0.0,
                "mean_monthly": 0.0,
                "reasons": ["order on the runway is unreadable; fail closed"],
                "weekly_heads": [],
                "stage_gate": STAGE_GATE,
            }
    cursor = dict(loaded)
    weekly_heads: list[float] = []
    weekly_revenue: list[float] = []
    weekly_contribution: list[float] = []
    reasons: list[str] = []
    for week in range(span):
        cap_row = sellable_for_growth(key, cursor, rate, 1, delivery_cap=False)
        cap = float(cap_row["allowed"])
        sell = cap
        if order_week == week and order_heads is not None:
            if order_heads > cap + 1e-6:
                sell = float(order_heads)
        nxt = _step_herd(key, cursor, sell, rho)
        if nxt is None:
            reasons.append(
                f"week {week}: selling {sell:.2f} heads breaks the breed floor"
            )
            weekly_heads.append(0.0)
            weekly_revenue.append(0.0)
            break
        weekly_heads.append(sell)
        weekly_revenue.append(sell * revenue_per)
        if margin is not None:
            weekly_contribution.append(sell * margin)
        cursor = nxt
    if not weekly_revenue:
        reasons.append("runway window was empty")
    min_week = min(weekly_revenue) if weekly_revenue else 0.0
    mean_week = (sum(weekly_revenue) / len(weekly_revenue)) if weekly_revenue else 0.0
    scale = 52.0 / 12.0
    min_revenue = min_week * scale
    mean_revenue = mean_week * scale
    if weekly_contribution:
        min_contribution = min(weekly_contribution) * scale
        mean_contribution = (sum(weekly_contribution) / len(weekly_contribution)) * scale
        contribution_ok = min_contribution >= -1e-9
    else:
        min_contribution = None
        mean_contribution = None
        contribution_ok = True
    if margin is not None and margin < 0:
        contribution_ok = False
        reasons.append("ASSUMPTION contribution check: variable cost exceeds prepaid revenue per head")
    return {
        "ok": not reasons,
        "target_kind": "revenue",
        "min_monthly": min_revenue,
        "mean_monthly": mean_revenue,
        "min_monthly_revenue": min_revenue,
        "mean_monthly_revenue": mean_revenue,
        "min_monthly_contribution": min_contribution,
        "mean_monthly_contribution": mean_contribution,
        "contribution_ok": contribution_ok and not reasons,
        "revenue_per_head": revenue_per,
        "margin_per_head": margin,
        "margin_tag": (
            "Primary figure is F_prelim revenue at 4 weeks. "
            "Contribution subtracts the ASSUMPTION variable cost when one exists. "
            "Opportunity cost is not in the runway."
        ),
        "weekly_heads": weekly_heads,
        "reasons": reasons,
        "herd_end": cursor.get("n_now"),
        "stage_gate": STAGE_GATE,
    }


def accept_order(
    order: dict,
    book: OrderBook | None,
    cascade_state: dict | None,
    policy: dict | None = None,
) -> AcceptDecision:
    """Accept only when integrity, feed edges, the revenue floor, and ROI all hold.

    The primary income test is average monthly revenue over ``H`` months against
    ``R_min`` (default $3,000). Contribution is a secondary ASSUMPTION check.
    ``g`` is applied as an extra whole-herd cap only when the policy sets it.
    Otherwise the implied rule is: do not shrink the breed floor or the feed buffer.

    Fail closed. ``book`` may be None (no open reservations). ``cascade_state``
    maps species name to herd state. The order species has to be in that map.
    """
    notes = [
        STAGE_GATE,
        DEFAULT_R_MIN_TAG,
        ASSUMPTION_FEED_TAG,
        "Spend order stays worms first (biology/CASCADE.md). The feed graph in this module is cyclic and is not permission to buy the later stages.",
    ]
    rules = _policy(policy)
    if rules["notes"]:
        notes.extend(rules["notes"])
    reasons: list[str] = []
    if not isinstance(order, dict):
        return _decision(False, ["order is missing"], {}, {}, {}, notes)
    species = str(order.get("species") or "").strip().lower()
    if species not in SPECIES_META:
        reasons.append(f"unknown species {species or '(blank)'}; fail closed")
    if not isinstance(cascade_state, dict) or species not in cascade_state:
        reasons.append("cascade_state is missing this species; fail closed")
        state = None
    else:
        state = cascade_state.get(species)
    week = _whole_weeks(order.get("week")) if isinstance(order, dict) else None
    heads = _order_heads(order, species) if isinstance(order, dict) else None
    if week is None or heads is None or heads <= 0:
        reasons.append("order needs a positive quantity and a whole delivery week")
    if rules["error"]:
        reasons.append(rules["error"])
    horizon = rules["t_weeks"]
    if week is not None and horizon is not None and week > horizon:
        reasons.append(
            f"delivery week {week} is outside the growth horizon of {horizon} weeks"
        )

    reserved = 0.0 if book is None else book.reserved_heads(species)
    schedule = [] if book is None else book.schedule(species)
    if week is not None and heads is not None and heads > 0:
        schedule = list(schedule) + [{"week": week, "heads": heads}]

    caps: dict = {}
    residuals: dict = {}
    reservations = {
        "id": order.get("id"),
        "species": species,
        "heads": heads,
        "qty": order.get("qty"),
        "unit": order.get("unit"),
        "week": week,
        "buyer": order.get("buyer"),
        "status": "refused",
    }

    if state is not None and not reasons:
        pending = {species: heads + reserved}
        feed = cascade_feed_plan(cascade_state, rules, pending)
        residuals["implied_g"] = feed.get("by_species")
        residuals["feed_edges"] = feed.get("edges")
        if not feed.get("edges_clear"):
            reasons.extend(feed.get("reasons") or ["a cascade feed edge does not clear"])
        feed_heads = float((feed.get("by_species") or {}).get(species, {}).get("feed_heads") or 0.0)
        guarded = dict(state)
        guarded["feed_reserve_heads"] = max(float(state.get("feed_reserve_heads") or 0.0), feed_heads)
        verdict = _removal_verdict(species, guarded, heads + reserved)
        if not verdict["ok"]:
            reasons.extend(verdict["reasons"] or ["sale would breach the breed floor"])
        growth = sellable_for_growth(
            species,
            guarded,
            rules["g"],
            horizon,
            schedule if rules["g_explicit"] else None,
        )
        caps = growth.get("caps") or {}
        caps["allowed_now"] = growth.get("allowed")
        caps["allowed_by_t"] = growth.get("allowed_by_t")
        caps["g_explicit"] = rules["g_explicit"]
        caps["g_implied_per_week"] = (feed.get("by_species") or {}).get(species, {}).get("g_implied_per_week")
        residuals["growth"] = {
            "feasible": growth.get("feasible"),
            "residual": growth.get("residual"),
            "reasons": growth.get("reasons"),
            "applied": rules["g_explicit"],
        }
        if rules["g_explicit"] and not growth.get("feasible"):
            detail = "; ".join(growth.get("reasons") or []) or "post-sale herd misses the growth path"
            reasons.append(f"growth gate: {detail}")
        # The long-lead firm cap belongs to the growth helper. It applies
        # only when the operator set g. Otherwise the hard stop is the
        # breed floor, the feed buffer, and firm surplus at delivery week.
        if rules["g_explicit"]:
            firm_cap = float(caps.get("firm_or_ne") or 0.0)
            if heads + reserved > firm_cap + 1e-4:
                reasons.append(
                    "order exceeds firm surplus above the Ne floor and the feed buffer"
                )
        delivery_lead = week if week is not None else 0
        casc_reasons, casc_notes, casc_mode = _cascade_gate(
            cascade_state, species, heads + reserved, delivery_lead
        )
        notes.extend(casc_notes)
        residuals["cascade_mode"] = casc_mode
        reasons.extend(casc_reasons)
        runway = firm_monthly_contribution(
            species,
            guarded,
            rules["g"],
            rules["H_months"],
            order,
        )
        residuals["runway"] = {
            "target_kind": "revenue",
            "min_monthly_revenue": runway.get("min_monthly_revenue"),
            "mean_monthly_revenue": runway.get("mean_monthly_revenue"),
            "min_monthly_contribution": runway.get("min_monthly_contribution"),
            "contribution_ok": runway.get("contribution_ok"),
            "margin_per_head": runway.get("margin_per_head"),
            "revenue_per_head": runway.get("revenue_per_head"),
            "reasons": runway.get("reasons"),
        }
        if not runway.get("ok"):
            reasons.append("revenue floor: " + "; ".join(runway.get("reasons") or ["unreadable"]))
        elif float(runway.get("min_monthly_revenue") or 0.0) + 1e-6 < float(rules["R_min"]):
            reasons.append(
                f"revenue floor: ${runway['min_monthly_revenue']:.0f}/mo after this book "
                f"is under R_min ${float(rules['R_min']):.0f}/mo"
            )
        elif runway.get("min_monthly_contribution") is not None and not runway.get("contribution_ok"):
            reasons.append(
                "ASSUMPTION contribution check: variable cost leaves monthly contribution below 0"
            )
    elif state is not None:
        # Still report caps when an earlier input failed, if the herd loads.
        if _load_herd(species, state) is not None and horizon is not None and rules["g"] is not None:
            growth = sellable_for_growth(species, state, rules["g"], horizon)
            caps = growth.get("caps") or {}
            caps["allowed_now"] = growth.get("allowed")

    roi_order = dict(order)
    if rules["g"] is not None:
        roi_order["g"] = rules["g"]
    roi = order_roi(roi_order, state if isinstance(state, dict) else None, rules["price_fn"], rules["hurdle"])
    residuals["roi"] = {
        "revenue": roi.get("revenue"),
        "var_cost": roi.get("var_cost"),
        "opp_cost": roi.get("opp_cost"),
        "contribution": roi.get("contribution"),
        "roi": roi.get("roi"),
        "accept_hurdle_met": roi.get("accept_hurdle_met"),
        "reasons": roi.get("reasons"),
    }
    if not roi.get("accept_hurdle_met"):
        detail = "; ".join(roi.get("reasons") or []) or "contribution below the hurdle"
        reasons.append(f"ROI gate: {detail}")

    accept = not reasons
    reservations["status"] = "proposed" if accept else "refused"
    if accept and rules["commit"] and book is not None:
        saved = book.reserve(reservations)
        residuals["commit"] = saved
        if not saved.get("ok"):
            accept = False
            reasons.append(f"reservation failed: {saved.get('reason')}")
            reservations["status"] = "refused"
        else:
            reservations = saved["order"]
    return _decision(accept, reasons, caps, residuals, reservations, notes)


def capacity_plan(
    R_min: float = DEFAULT_R_MIN,
    H_months: int = DEFAULT_H_MONTHS,
    species: str = "quail",
    state: dict | None = None,
    cascade_state: dict | None = None,
    *,
    horizon_weeks: int | None = None,
    g: float | None = None,
) -> dict:
    """Birds to hold today so average monthly revenue can clear ``R_min``.

    ``R_min`` is revenue, not contribution. ``g`` is optional. When it is
    omitted the schedule sells only the surplus that keeps the herd from
    shrinking (implied g = 0 on the retained stock). Pass ``g`` only to
    demand a faster whole-herd path. This does not buy stock.
    """
    key = str(species).strip().lower()
    g_explicit = g is not None
    rate = 0.0 if g is None else _growth_rate(g)
    months = _whole_weeks(H_months)
    weeks = _whole_weeks(horizon_weeks) if horizon_weeks is not None else (
        None if months is None else int(round(months * 52.0 / 12.0))
    )
    target = _optional_float(R_min)
    base = {
        "species": key,
        "target_kind": "revenue",
        "R_min": target,
        "R_min_tag": DEFAULT_R_MIN_TAG,
        "M_min": target,
        "H_months": months,
        "g_per_week": rate,
        "g_explicit": g_explicit,
        "g_source": (
            "operator g, an extra whole-herd cap"
            if g_explicit
            else "implied: maintain the herd (g = 0). Not an operator growth target."
        ),
        "horizon_weeks": weeks,
        "feasible": False,
        "hold_heads": None,
        "hold_lb": None,
        "weekly_sell_heads": None,
        "schedule": [],
        "state": None,
        "min_monthly": 0.0,
        "min_monthly_revenue": 0.0,
        "reasons": [],
        "stage_gate": STAGE_GATE,
        "stage": SPECIES_META.get(key, {}).get("stage"),
    }
    if (
        key not in SPECIES_META
        or rate is None
        or months is None
        or months < 1
        or weeks is None
        or weeks < 1
        or weeks > 520
        or target is None
        or target < 0
    ):
        base["reasons"] = ["capacity_plan needs a known species, R_min >= 0, H_months >= 1, and at most 520 weeks"]
        return base
    if _rho(key, state or {}) is None and key not in engine.SPECIES:
        base["reasons"] = ["doubling time missing; fail closed"]
        return base
    anchor = _anchor_n0(key, state)
    if anchor is None:
        base["reasons"] = ["breed-floor anchor n0 is missing; fail closed"]
        return base
    revenue_per = _revenue_per_head(key)
    margin = _margin_per_head(key)
    if revenue_per is None or revenue_per <= 0:
        base["reasons"] = ["no positive prepaid revenue per head; cannot size a flock"]
        return base
    if margin is not None and margin < 0:
        base["reasons"] = ["ASSUMPTION contribution check: variable cost exceeds revenue per head"]
        base["revenue_per_head"] = revenue_per
        base["margin_per_head"] = margin
        return base
    if target <= _HEAD_TOL:
        hold = _state_for_hold(key, anchor, anchor, state)
        base.update({
            "feasible": True,
            "hold_heads": hold["n_now"],
            "hold_lb": _heads_to_lb(key, hold["n_now"]),
            "weekly_sell_heads": 0.0,
            "state": hold,
            "min_monthly": 0.0,
            "min_monthly_revenue": 0.0,
            "revenue_per_head": revenue_per,
            "margin_per_head": margin,
            "note": "R_min is 0, so the hold is the breed floor and the sell schedule is empty.",
        })
        return base

    def trial(heads: float) -> dict:
        herd = _state_for_hold(key, heads, anchor, state)
        sim = firm_monthly_contribution(key, herd, rate, weeks=weeks)
        sim["state"] = herd
        return sim

    meta = SPECIES_META[key]
    step = 4.0 if key == "quail" else 1.0
    lo = anchor
    probe = trial(lo)
    if probe.get("ok") and probe.get("contribution_ok", True) and probe["min_monthly_revenue"] + 1e-6 >= target:
        chosen = probe
    else:
        hi = max(lo * 2, lo + step)
        found = False
        for _ in range(24):
            probe = trial(hi)
            if probe.get("ok") and probe.get("contribution_ok", True) and probe["min_monthly_revenue"] + 1e-6 >= target:
                found = True
                break
            lo = hi
            hi = min(hi * 2, 2_000_000.0)
            if hi >= 2_000_000.0:
                break
        if not found:
            base["reasons"] = [
                "no herd under 2,000,000 heads throws off R_min in prepaid revenue"
            ]
            base["revenue_per_head"] = revenue_per
            base["margin_per_head"] = margin
            return base
        for _ in range(28):
            mid = 0.5 * (lo + hi)
            if key == "quail":
                mid = math.ceil(mid / step) * step
            probe = trial(mid)
            if probe.get("ok") and probe.get("contribution_ok", True) and probe["min_monthly_revenue"] + 1e-6 >= target:
                hi = mid
            else:
                lo = mid
            if abs(hi - lo) <= step:
                break
        chosen = trial(hi)
    herd = chosen["state"]
    schedule = [
        {"week": index, "heads": heads}
        for index, heads in enumerate(chosen.get("weekly_heads") or [])
    ]
    check = sellable_for_growth(key, herd, rate, weeks, schedule, delivery_cap=False)
    feasible = (
        bool(chosen.get("ok"))
        and bool(chosen.get("contribution_ok", True))
        and bool(check.get("feasible"))
        and chosen["min_monthly_revenue"] + 1e-6 >= target
    )
    reasons = []
    if not feasible:
        reasons.extend(chosen.get("reasons") or [])
        reasons.extend(check.get("reasons") or [])
        if not reasons:
            reasons.append("sized herd did not keep both the revenue floor and the retained stock")
    backsolve = None
    try:
        backsolve = margin_backsolve(target, revenue_per, "head")
    except ValueError:
        backsolve = None
    feed = None
    if cascade_state is not None:
        feed = cascade_feed_plan({**cascade_state, key: herd}, {"feed_rates": None})
        if not feed.get("edges_clear"):
            feasible = False
            reasons.extend(feed.get("reasons") or ["feed edges do not clear at this hold"])
    return {
        "species": key,
        "target_kind": "revenue",
        "R_min": target,
        "R_min_tag": DEFAULT_R_MIN_TAG,
        "M_min": target,
        "H_months": months,
        "g_per_week": rate,
        "g_explicit": g_explicit,
        "g_source": base["g_source"],
        "horizon_weeks": weeks,
        "feasible": feasible,
        "hold_heads": herd["n_now"],
        "hold_males": herd.get("n_males"),
        "hold_females": herd.get("n_females"),
        "hold_lb": _heads_to_lb(key, herd["n_now"]),
        "weekly_sell_heads": (chosen.get("weekly_heads") or [None])[0],
        "schedule": schedule,
        "min_monthly": chosen.get("min_monthly_revenue"),
        "mean_monthly": chosen.get("mean_monthly_revenue"),
        "min_monthly_revenue": chosen.get("min_monthly_revenue"),
        "mean_monthly_revenue": chosen.get("mean_monthly_revenue"),
        "min_monthly_contribution": chosen.get("min_monthly_contribution"),
        "contribution_ok": chosen.get("contribution_ok"),
        "revenue_per_head": revenue_per,
        "margin_per_head": margin,
        "revenue_backsolve_heads_per_month": None if backsolve is None else backsolve["units"],
        "schedule_feasible": check.get("feasible"),
        "feed": None if feed is None else {"edges_clear": feed.get("edges_clear"), "reasons": feed.get("reasons")},
        "state": herd,
        "reasons": reasons,
        "note": (
            "Hold is the flock on hand today. The schedule is the weekly firm "
            "surplus whose prepaid revenue clears R_min. It is not a purchase list. "
            f"{meta['stage']}"
        ),
        "stage_gate": STAGE_GATE,
        "stage": meta["stage"],
    }


def _decision(accept: bool, reasons: list[str], caps: dict, residuals: dict, reservations: dict, notes: list[str]) -> AcceptDecision:
    # Preserve order, drop repeats.
    seen: list[str] = []
    for reason in reasons:
        if reason and reason not in seen:
            seen.append(reason)
    return AcceptDecision(
        accept=bool(accept) and not seen,
        reasons=seen,
        caps=caps,
        residuals=residuals,
        reservations=reservations,
        notes=notes,
    )


def _policy(policy: dict | None) -> dict:
    source = policy or {}
    notes: list[str] = []
    error = None
    g_explicit = "g" in source and source.get("g") is not None
    if g_explicit:
        g = _growth_rate(source["g"])
        if g is None:
            error = "policy g must be >= 0 and < 1"
            g = None
    else:
        g = 0.0
        notes.append(
            "g was not set. Implied rule: do not shrink the breed floor or the feed buffer. "
            "g_s is reported after the sale. It is not the knob."
        )
    if "t_weeks" in source and source["t_weeks"] is not None:
        t_weeks = _whole_weeks(source["t_weeks"])
        if t_weeks is None:
            error = error or "policy t_weeks must be a whole number of weeks"
    else:
        t_weeks = 26
        notes.append("t_weeks defaulted to 26.")
    if "H_months" in source and source["H_months"] is not None:
        months = _whole_weeks(source["H_months"])
        if months is None or months < 1:
            error = error or "policy H_months must be a positive whole number"
            months = None
    else:
        months = 3
    if "R_min" in source:
        if source["R_min"] is None:
            error = error or "R_min is missing; fail closed"
            r_min = None
        else:
            r_min = _optional_float(source["R_min"])
            if r_min is None or r_min < 0:
                error = error or "R_min must be >= 0"
                r_min = None
    elif "M_min" in source:
        if source["M_min"] is None:
            error = error or "R_min is missing; fail closed"
            r_min = None
        else:
            r_min = _optional_float(source["M_min"])
            if r_min is None or r_min < 0:
                error = error or "R_min must be >= 0"
                r_min = None
            else:
                notes.append("M_min is read as R_min. The dollar test is monthly revenue, not contribution.")
    else:
        r_min = DEFAULT_R_MIN
        notes.append(DEFAULT_R_MIN_TAG)
    hurdle = _optional_float(source.get("hurdle", 0.0))
    if hurdle is None:
        error = error or "hurdle must be a number"
        hurdle = 0.0
    return {
        "g": g,
        "g_explicit": g_explicit,
        "t_weeks": t_weeks,
        "H_months": months if months is not None else DEFAULT_H_MONTHS,
        "R_min": 0.0 if r_min is None else r_min,
        "M_min": 0.0 if r_min is None else r_min,
        "hurdle": hurdle,
        "price_fn": source.get("price_fn"),
        "feed_rates": source.get("feed_rates") or {},
        "commit": bool(source.get("commit", False)),
        "notes": notes,
        "error": error,
    }


def _blank(species: str, g, t) -> dict:
    return {
        "species": species,
        "unit": "head",
        "allowed": 0.0,
        "allowed_lb": 0.0,
        "allowed_by_t": 0.0,
        "allowed_by_t_lb": 0.0,
        "g_per_week": g,
        "t_weeks": t,
        "feasible": False,
        "residual": 0.0,
        "residual_lb": 0.0,
        "reasons": [],
        "binding": "fail_closed",
        "caps": {},
        "floor": None,
        "fail_closed": True,
        "stage_gate": STAGE_GATE,
    }


def _herd_problem(species: str, state: dict | None) -> str:
    if not isinstance(state, dict):
        return "herd state is missing; fail closed"
    if species not in SPECIES_META:
        return f"unknown species {species}; fail closed"
    if state.get("n_now") is None or state.get("n0") is None:
        return "n_now and n0 are required; fail closed"
    meta = SPECIES_META[species]
    if meta["sexed"] and (state.get("n_males") is None or state.get("n_females") is None):
        return f"{species} needs n_males and n_females; fail closed. Breeders are not guessed."
    return "herd counts are inconsistent or negative; fail closed"


def _load_herd(species: str, state: dict | None) -> dict | None:
    if species not in SPECIES_META or not isinstance(state, dict):
        return None
    n_now = _optional_float(state.get("n_now"))
    n0 = _optional_float(state.get("n0"))
    if n_now is None or n0 is None or n_now < 0 or n0 < 0:
        return None
    loaded = dict(state)
    loaded["n_now"] = n_now
    loaded["n0"] = n0
    meta = SPECIES_META[species]
    if meta["sexed"]:
        males = _optional_float(state.get("n_males"))
        females = _optional_float(state.get("n_females"))
        if males is None or females is None or males < 0 or females < 0:
            return None
        if abs((males + females) - n_now) > 1e-4:
            return None
        loaded["n_males"] = males
        loaded["n_females"] = females
    feed = state.get("feed_reserve_heads")
    if feed is None:
        loaded["feed_reserve_heads"] = 0.0
    else:
        feed_v = _optional_float(feed)
        if feed_v is None or feed_v < 0:
            return None
        loaded["feed_reserve_heads"] = feed_v
    return loaded


def _floors(species: str, state: dict) -> dict:
    meta = SPECIES_META[species]
    n0 = float(state["n0"])
    n_start = state.get("n_start")
    n_safety = state.get("n_safety")
    start = n0 if n_start is None else float(n_start)
    safety = n0 if n_safety is None else float(n_safety)
    if meta["sexed"]:
        info = genetics.keep_floor(n0, start, safety, meta["females_per_male"])
        keep = float(info["keep"])
        males_min = int(info["males_min"])
        females_min = int(info["females_min"])
        genetics_floor = float(info["genetics_floor"])
        ne_min = float(info["ne_min"])
    else:
        keep = float(breed_floor(n0, start, safety))
        males_min = None
        females_min = None
        genetics_floor = None
        ne_min = None
        info = {"keep": keep}
    feed = float(state.get("feed_reserve_heads") or 0.0)
    return {
        "keep": keep,
        "unsellable": keep + feed,
        "feed_reserve_heads": feed,
        "males_min": males_min,
        "females_min": females_min,
        "genetics_floor": genetics_floor,
        "ne_min": ne_min,
        "n0": n0,
        "n_start": start,
        "n_safety": safety,
        "raw": info,
    }


def _firm_sex_cap(species: str, state: dict, lead_weeks: int, floors: dict) -> dict:
    peak, peak_reason = _peak_meat_cap(species, state)
    if peak_reason:
        return {
            "cap": 0.0,
            "safe_sell": 0.0,
            "sex": 0.0,
            "peak": peak,
            "reason": peak_reason,
        }
    limited = safe_sell_limit(
        float(state["n_now"]),
        float(floors["unsellable"]),
        alpha=ALPHA,
        safety_frac=SAFETY_FRAC,
        m_weekly=M_WEEKLY,
        lead_weeks=float(max(0, lead_weeks)),
        n_req_forward=float(floors["keep"]),
    )
    sex = _max_removable(species, state, floors)
    parts = [float(limited["allowed_firm"]), sex]
    if peak is not None:
        parts.append(peak)
    return {
        "cap": _nonneg_min(*parts),
        "safe_sell": float(limited["allowed_firm"]),
        "sex": sex,
        "peak": peak,
        "reason": None,
    }


def _max_removable(species: str, state: dict, floors: dict) -> float:
    meta = SPECIES_META[species]
    n_now = float(state["n_now"])
    keep = float(floors["unsellable"])
    if n_now + _HEAD_TOL < keep:
        return 0.0
    if not meta["sexed"]:
        return max(0.0, n_now - keep)
    males = float(state["n_males"])
    females = float(state["n_females"])
    males_min = float(floors["males_min"])
    females_min = float(floors["females_min"])
    if males + _HEAD_TOL < males_min or females + _HEAD_TOL < females_min:
        return 0.0
    hi = min(
        max(0.0, males - males_min) + max(0.0, females - females_min),
        max(0.0, n_now - keep),
    )
    if hi <= _HEAD_TOL:
        return 0.0
    if _sale_allowed(species, state, floors, hi):
        return hi
    lo = 0.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if _sale_allowed(species, state, floors, mid):
            lo = mid
        else:
            hi = mid
    return lo


def _sale_allowed(species: str, state: dict, floors: dict, heads: float) -> bool:
    return _removal_verdict(species, state, heads, floors)["ok"]


def _removal_verdict(species: str, state: dict, heads: float, floors: dict | None = None) -> dict:
    loaded = _load_herd(species, state)
    if loaded is None:
        return {"ok": False, "reasons": ["herd counts missing; fail closed"], "state": None}
    floors = floors or _floors(species, loaded)
    if heads < -_HEAD_TOL:
        return {"ok": False, "reasons": ["negative sale"], "state": None}
    if heads <= _HEAD_TOL:
        return {"ok": True, "reasons": [], "state": loaded, "sold_males": 0.0, "sold_females": 0.0}
    meta = SPECIES_META[species]
    if not meta["sexed"]:
        if loaded["n_now"] - heads + _HEAD_TOL < floors["unsellable"]:
            return {
                "ok": False,
                "reasons": ["order exceeds surplus above the breed floor"],
                "state": None,
            }
        nxt = dict(loaded)
        nxt["n_now"] = loaded["n_now"] - heads
        return {"ok": True, "reasons": [], "state": nxt, "sold_males": 0.0, "sold_females": 0.0}
    males_min = float(floors["males_min"])
    females_min = float(floors["females_min"])
    alloc = _allocate_sale(
        loaded["n_males"],
        loaded["n_females"],
        heads,
        males_min,
        females_min,
    )
    if alloc is None:
        room_m = max(0.0, loaded["n_males"] - males_min)
        room_f = max(0.0, loaded["n_females"] - females_min)
        blocked: list[str] = []
        if (
            loaded["n_males"] + _HEAD_TOL < males_min
            or loaded["n_females"] + _HEAD_TOL < females_min
            or heads > room_m + room_f + 1e-5
        ):
            blocked.append(
                "sale would drop males or females under the Ne floor "
                f"({int(males_min)} males / {int(females_min)} females)"
            )
        if loaded["n_now"] - heads + _HEAD_TOL < floors["unsellable"]:
            blocked.append("order exceeds surplus above the breed floor")
        if not blocked:
            blocked.append("order exceeds surplus above the breed floor")
        return {"ok": False, "reasons": blocked, "state": None}
    sold_m, sold_f = alloc
    try:
        plan = genetics.cull_plan(
            loaded["n_males"],
            loaded["n_females"],
            sold_m,
            sold_f,
            float(floors["n0"]),
            meta["females_per_male"],
            floors["n_start"],
            floors["n_safety"],
        )
    except ValueError as err:
        return {"ok": False, "reasons": [str(err)], "state": None}
    if not plan["allowed"]:
        return {"ok": False, "reasons": list(plan["reasons"]), "state": None}
    if plan["males_after"] + plan["females_after"] + _HEAD_TOL < floors["unsellable"]:
        return {
            "ok": False,
            "reasons": ["order exceeds surplus above the breed floor"],
            "state": None,
        }
    nxt = dict(loaded)
    nxt["n_males"] = float(plan["males_after"])
    nxt["n_females"] = float(plan["females_after"])
    nxt["n_now"] = nxt["n_males"] + nxt["n_females"]
    return {"ok": True, "reasons": [], "state": nxt, "sold_males": sold_m, "sold_females": sold_f}


def _allocate_sale(
    males: float,
    females: float,
    heads: float,
    males_min: float,
    females_min: float,
) -> tuple[float, float] | None:
    """Sell extra males first, then extra females, and never cross the sex floors."""
    sm = float(males)
    sf = float(females)
    sold_m = 0.0
    sold_f = 0.0
    remaining = float(heads)

    def take(room: float, sex: str) -> None:
        nonlocal sm, sf, sold_m, sold_f, remaining
        cut = min(remaining, max(0.0, room))
        if cut <= 0:
            return
        if sex == "M":
            sm -= cut
            sold_m += cut
        else:
            sf -= cut
            sold_f += cut
        remaining -= cut

    take(sm - max(males_min, sf / 3.0), "M")
    take(sf - max(females_min, 3.0 * sm), "F")
    take(sm - males_min, "M")
    take(sf - females_min, "F")
    if remaining > 1e-5:
        return None
    return sold_m, sold_f


def _growth_lump(n_now: float, g: float, t: int, rho: float) -> float:
    if t <= 0 or n_now <= 0 or rho <= 0:
        return 0.0
    target_ratio = (1.0 + g) ** t
    grown = rho ** t
    if grown <= target_ratio:
        return 0.0
    return float(n_now) * (1.0 - target_ratio / grown)


def _delivery_heads(species, state, g, t, rho, floors, delivery_cap: bool) -> tuple[float, dict]:
    n_now = float(state["n_now"])
    grown = n_now * (rho ** t)
    growth_at_t = max(0.0, grown - n_now * ((1.0 + g) ** t))
    pipeline = _pipeline_cap(state, t, floors)
    future = dict(state)
    future["n_now"] = grown
    if SPECIES_META[species]["sexed"]:
        scale = (rho ** t) if n_now > 0 else 0.0
        future["n_males"] = float(state["n_males"]) * scale
        future["n_females"] = float(state["n_females"]) * scale
    future_floors = _floors(species, future)
    firm_at_t = _firm_sex_cap(species, future, 0, future_floors)["cap"]
    flock_cap = None
    if delivery_cap and species == "quail" and t >= 1:
        flock_cap, flock_reason = _flock_delivery_cap(n_now, t)
        if flock_reason or flock_cap is None:
            return 0.0, {
                "growth_at_t": growth_at_t,
                "pipeline": pipeline,
                "flock_today": 0.0,
                "firm_at_t": firm_at_t,
                "reason": flock_reason or "flock_today failed; fail closed",
            }
    parts = [growth_at_t, pipeline, firm_at_t]
    if flock_cap is not None:
        parts.append(flock_cap)
    return _nonneg_min(*parts), {
        "growth_at_t": growth_at_t,
        "pipeline": pipeline,
        "flock_today": flock_cap,
        "firm_at_t": firm_at_t,
    }


def _pipeline_cap(state: dict, t: int, floors: dict) -> float:
    """Inverse of birds_now_for_demand: firm heads deliverable at week t."""
    if t < 0:
        return 0.0
    survival = (1.0 - M_WEEKLY) ** t
    if survival <= 0:
        return 0.0
    if floors["males_min"] is not None:
        males = math.ceil(float(floors["males_min"]) / survival - 1e-12)
        females = math.ceil(float(floors["females_min"]) / survival - 1e-12)
        hold = float(males + females)
    else:
        hold = float(floors["keep"]) / survival
    hold += _peak_pipeline_birds(floors)
    room = float(state["n_now"]) - hold - float(floors["feed_reserve_heads"])
    if room <= 0:
        return 0.0
    try:
        probe = birds_now_for_demand(
            1.0,
            m_weekly=M_WEEKLY,
            lead_weeks=float(t),
            safety_frac=SAFETY_FRAC,
            alpha=ALPHA,
        )
    except ValueError:
        return 0.0
    per_head = float(probe["n_pipeline_min"])
    if per_head <= 0:
        return 0.0
    return room / per_head


def _peak_pipeline_birds(floors: dict) -> float:
    """Replacement chicks that are not meat, when the peak-cull helper is importable."""
    if floors.get("females_min") is None:
        return 0.0
    fn = _load_symbol("quail_model", "steady_peak_flock")
    if fn is None:
        return 0.0
    try:
        row = fn(
            float(floors["females_min"]),
            M_WEEKLY,
            int(floors["males_min"]),
            int(floors["females_min"]),
        )
    except Exception:
        return 0.0
    return max(0.0, float(row.get("pipeline_birds") or 0.0))


def _peak_meat_cap(species: str, state: dict) -> tuple[float | None, str | None]:
    if species != "quail":
        return None, None
    if not state.get("age_bins") and not state.get("birds"):
        return None, None
    fn = _load_symbol("quail_model", "peak_cull_policy")
    if fn is None:
        return 0.0, (
            "age structure was provided but peak_cull_policy is not on this branch; fail closed"
        )
    try:
        row = fn(birds=state.get("birds"), age_bins=state.get("age_bins"))
    except Exception as err:  # noqa: BLE001
        return 0.0, f"peak_cull_policy failed ({err}); fail closed"
    meat = float(row.get("cull_to_meat_hens") or 0.0) + float(row.get("cull_to_meat_males") or 0.0)
    return max(0.0, meat), None


def _flock_delivery_cap(n_now: float, week: int) -> tuple[float | None, str | None]:
    key = (int(week), round(float(n_now), 4))
    if key in _FLOCK_CACHE:
        return _FLOCK_CACHE[key]
    dress = float(engine.QUAIL_LB_PER_BIRD)

    def n_today(heads: float):
        if heads <= 1e-9:
            return 0.0
        kwargs = {"sustain_peak": True} if _FLOCK_HAS_SUSTAIN else {}
        try:
            row = delivery.flock_today(int(week), float(heads) * dress, **kwargs)
        except Exception:
            return "error"
        if not row.get("fail_closed", False):
            return "too_big"
        return float(row["n_today"])

    lo = 0.0
    hi = max(1.0, min(float(n_now), 64.0))
    error = None
    for _ in range(16):
        got = n_today(hi)
        if got == "error":
            error = "flock_today failed; fail closed"
            break
        if got == "too_big" or got > n_now + 1e-6:
            break
        lo = hi
        hi *= 2.0
        if hi > max(n_now * 4.0, 1.0):
            break
    if error:
        result = (None, error)
        _FLOCK_CACHE[key] = result
        return result
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        got = n_today(mid)
        if got == "error":
            result = (None, "flock_today failed; fail closed")
            _FLOCK_CACHE[key] = result
            return result
        if got == "too_big" or got > n_now + 1e-6:
            hi = mid
        else:
            lo = mid
    result = (max(0.0, lo), None)
    _FLOCK_CACHE[key] = result
    return result


def _forecast(species, state, g, t, rho, floors, schedule: list[tuple[int, float]]) -> dict:
    by_week: dict[int, float] = {}
    for week, heads in schedule:
        if week < 0 or week > t:
            return {"feasible": False, "residual": 0.0, "reasons": ["a sale sits outside the horizon"]}
        if heads < 0:
            return {"feasible": False, "residual": 0.0, "reasons": ["a sale is negative"]}
        by_week[week] = by_week.get(week, 0.0) + heads
    cursor = dict(state)
    initial = float(state["n_now"])
    for week in range(0, t + 1):
        sold = by_week.get(week, 0.0)
        live_floors = _floors(species, cursor)
        cap = _firm_sex_cap(species, cursor, t - week, live_floors)["cap"]
        if sold > cap + 1e-4:
            return {
                "feasible": False,
                "residual": 0.0,
                "reasons": [
                    f"week {week}: {sold:.2f} heads exceeds firm surplus or the Ne floor ({cap:.2f})"
                ],
            }
        verdict = _removal_verdict(species, cursor, sold, live_floors)
        if not verdict["ok"]:
            return {"feasible": False, "residual": 0.0, "reasons": verdict["reasons"]}
        cursor = verdict["state"]
        if week < t:
            cursor = _grow(cursor, rho)
    target = initial * ((1.0 + g) ** t)
    if cursor["n_now"] < target - max(1e-3, 1e-6 * target):
        return {
            "feasible": False,
            "residual": 0.0,
            "reasons": [
                f"terminal herd {cursor['n_now']:.1f} is under the growth path {target:.1f}"
            ],
        }
    end_floors = _floors(species, cursor)
    if cursor["n_now"] + _HEAD_TOL < end_floors["keep"]:
        return {"feasible": False, "residual": 0.0, "reasons": ["terminal herd is under the breed floor"]}
    spare = max(0.0, cursor["n_now"] - target)
    firm_left = _firm_sex_cap(species, cursor, 0, end_floors)["cap"]
    return {"feasible": True, "residual": min(spare, firm_left), "reasons": []}


def _step_herd(species: str, state: dict, sold: float, rho: float) -> dict | None:
    verdict = _removal_verdict(species, state, sold)
    if not verdict["ok"]:
        return None
    return _grow(verdict["state"], rho)


def _grow(state: dict, rho: float) -> dict:
    nxt = dict(state)
    if "n_males" in state and "n_females" in state:
        nxt["n_males"] = float(state["n_males"]) * rho
        nxt["n_females"] = float(state["n_females"]) * rho
        nxt["n_now"] = nxt["n_males"] + nxt["n_females"]
    else:
        nxt["n_now"] = float(state["n_now"]) * rho
    return nxt


def _normalize_schedule(raw, species: str) -> tuple[list[tuple[int, float]] | None, str | None]:
    rows: list[tuple[int, float]] = []
    if isinstance(raw, dict):
        items = [{"week": key, "heads": value} for key, value in raw.items()]
    elif isinstance(raw, list):
        items = raw
    else:
        return None, "sales schedule must be a list or a week map"
    for item in items:
        if isinstance(item, dict):
            week = _whole_weeks(item.get("week"))
            if item.get("heads") is not None:
                heads = _optional_float(item.get("heads"))
            elif item.get("lb") is not None or item.get("qty") is not None:
                probe = {
                    "species": species,
                    "qty": item.get("lb", item.get("qty")),
                    "unit": item.get("unit") or ("lb" if item.get("lb") is not None else "head"),
                }
                heads = _order_heads(probe, species)
            else:
                heads = None
        else:
            return None, "each sale needs a week and a headcount"
        if week is None or heads is None:
            return None, "a sale is missing a whole week or a headcount"
        rows.append((week, heads))
    return rows, None


def _cascade_gate(cascade_state: dict, order_species: str, heads: float, lead_weeks: int) -> tuple[list[str], list[str], str]:
    reasons: list[str] = []
    firm_take = _load_firm_take()
    if firm_take is None:
        mode = "per_species_stub"
        notes = [
            "STUB: research/cascade_growth is not on this branch. "
            "Each species is checked on its own floor via safe_sell_limit / keep_floor. "
            "Set feed_reserve_heads on a species to hold biomass back for whoever eats it. "
            "This sale does not lower another species' floor."
        ]
    else:
        mode = "cascade_growth.firm_take"
        notes = ["Downstream feed uses cascade_growth.model.firm_take."]
    for name, herd in cascade_state.items():
        key = str(name).strip().lower()
        loaded = _load_herd(key, herd if isinstance(herd, dict) else None)
        if loaded is None:
            reasons.append(f"{key}: herd counts missing; cascade check fail closed")
            continue
        floors = _floors(key, loaded)
        if loaded["n_now"] + _HEAD_TOL < floors["keep"]:
            reasons.append(f"{key}: already under its breed floor; refuse new orders")
            continue
        if key != order_species:
            continue
        cap = _firm_sex_cap(key, loaded, lead_weeks, floors)["cap"]
        if heads > cap + 1e-4:
            reasons.append(f"{key}: order plus reservations exceed that species' own firm surplus")
        if firm_take is not None:
            try:
                take = float(firm_take(
                    loaded["n_now"],
                    floors["unsellable"],
                    heads,
                    M_WEEKLY,
                    lead_weeks=float(lead_weeks),
                    n_req_forward=floors["keep"],
                ))
            except Exception as err:  # noqa: BLE001
                reasons.append(f"{key}: firm_take failed ({err}); fail closed")
                continue
            if heads > take + 1e-4:
                reasons.append(f"{key}: cascade firm_take will not release {heads:.2f} heads")
    return reasons, notes, mode


def _variable_cost(species: str, heads: float, revenue: float | None) -> dict | None:
    del revenue
    if species == "quail":
        return {"mode": "per_head", "per_head": QUAIL_VAR_COST_PER_BIRD, "tag": QUAIL_VAR_COST_TAG}
    if species == "worms":
        return {"mode": "revenue_fraction", "revenue_fraction": WORM_OPEX_FRACTION, "tag": WORM_OPEX_TAG}
    return None


def _revenue_per_head(species: str) -> float | None:
    """Fair prepaid revenue per head at a 4-week tenor. None if this species has no spot."""
    quote = default_price_fn({"species": species, "qty": 1, "unit": "head", "week": 4}, None)
    if quote is None:
        return None
    return float(quote["usd_per_unit"])


def _margin_per_head(species: str) -> float | None:
    """Fair contribution per head at a 4-week tenor. None if price or cost is missing."""
    revenue = _revenue_per_head(species)
    if revenue is None:
        return None
    pack = _variable_cost(species, 1.0, revenue)
    if pack is None:
        return None
    if pack["mode"] == "per_head":
        var = pack["per_head"]
    else:
        var = revenue * pack["revenue_fraction"]
    return revenue - var


def _state_for_hold(species: str, heads: float, anchor: float, template: dict | None) -> dict:
    herd = dict(template or {})
    herd["n0"] = float(herd.get("n0", anchor))
    herd["n_start"] = float(herd.get("n_start", herd["n0"]))
    herd["n_safety"] = float(herd.get("n_safety", herd["n0"]))
    count = max(float(heads), float(herd["n0"]))
    meta = SPECIES_META[species]
    if meta["sexed"] and species == "quail":
        males = max(int(math.ceil(count / 4.0 - 1e-12)), 1)
        females = 3 * males
        herd["n_males"] = float(males)
        herd["n_females"] = float(females)
        herd["n_now"] = float(males + females)
    elif meta["sexed"]:
        males = max(int(math.ceil(count / 2.0 - 1e-12)), 1)
        females = males
        herd["n_males"] = float(males)
        herd["n_females"] = float(females)
        herd["n_now"] = float(males + females)
    else:
        herd["n_now"] = count
    if herd.get("doubling_weeks") is None and species not in engine.SPECIES:
        pass
    return herd


def _anchor_n0(species: str, state: dict | None) -> float | None:
    if isinstance(state, dict) and state.get("n0") is not None:
        return _optional_float(state.get("n0"))
    if SPECIES_META[species]["sexed"]:
        return _genetics_floor(species)
    return None


def _genetics_floor(species: str) -> float:
    meta = SPECIES_META[species]
    info = genetics.keep_floor(1, None, None, meta["females_per_male"])
    return float(info["genetics_floor"])


def _order_heads(order: dict, species: str) -> float | None:
    if order.get("heads") is not None and order.get("qty") is None:
        return _optional_float(order.get("heads"))
    qty = order.get("qty")
    if qty is None:
        return _optional_float(order.get("heads"))
    qty_v = _optional_float(qty)
    if qty_v is None:
        return None
    unit = _order_unit(order, species)
    if unit == "head":
        return qty_v
    if unit == "lb":
        per = _lb_per_head(species)
        if per is None or per <= 0:
            return None
        return qty_v / per
    return None


def _order_unit(order: dict, species: str) -> str:
    raw = str(order.get("unit") or "").strip().lower()
    if raw in ("lb", "lbs", "pound", "pounds"):
        return "lb"
    if raw in ("head", "heads", "bird", "birds"):
        return "head"
    if species == "worms":
        return "lb"
    return "head"


def _lb_per_head(species: str) -> float | None:
    if species == "quail":
        return float(engine.QUAIL_LB_PER_BIRD)
    if species == "worms":
        per_lb = float(engine.WORM_HEADCOUNT_PER_LB)
        if per_lb <= 0:
            return None
        return 1.0 / per_lb
    return None


def _heads_to_lb(species: str, heads: float | None) -> float | None:
    if heads is None:
        return None
    per = _lb_per_head(species)
    if per is None:
        return None
    return float(heads) * per


def _rho(species: str, state: dict) -> float | None:
    doubling = _doubling_weeks(species, state)
    if doubling is None or doubling <= 0:
        return None
    return 2.0 ** (1.0 / doubling)


def _doubling_weeks(species: str, state: dict) -> float | None:
    if isinstance(state, dict) and state.get("doubling_weeks") is not None:
        return _optional_float(state.get("doubling_weeks"))
    model = engine.SPECIES.get(species)
    if model is None:
        return None
    return float(model.doubling_weeks)


def _doubling_tag(species: str, state: dict) -> str:
    if isinstance(state, dict) and state.get("doubling_weeks") is not None:
        return "ASSUMPTION from state['doubling_weeks']"
    model = engine.SPECIES.get(species)
    if model is None:
        return "missing"
    return f"ASSUMPTION from ops-dashboard {species} stub ({model.tag})"


def _usd_per_unit(quote) -> float | None:
    if quote is None:
        return None
    if isinstance(quote, dict):
        if quote.get("usd_per_unit") is not None:
            return _optional_float(quote.get("usd_per_unit"))
        if quote.get("F_prelim") is not None:
            return _optional_float(quote.get("F_prelim"))
        return None
    return _optional_float(quote)


def _load_firm_take():
    model = _RESEARCH / "cascade_growth" / "model.py"
    if not model.exists():
        return None
    root = str(_RESEARCH)
    if root not in sys.path:
        sys.path.insert(0, root)
    return _load_symbol("cascade_growth.model", "firm_take")


def _load_symbol(module: str, name: str):
    try:
        mod = importlib.import_module(module)
    except Exception:
        return None
    return getattr(mod, name, None)


def _binding(parts: list[tuple[str, float]]) -> str:
    finite = [(name, value) for name, value in parts if value is not None and math.isfinite(value)]
    if not finite:
        return "fail_closed"
    return min(finite, key=lambda item: item[1])[0]


def _nonneg_min(*values: float) -> float:
    return max(0.0, min(values))


def _whole_weeks(value) -> int | None:
    number = _optional_float(value)
    if number is None or number < 0:
        return None
    if abs(number - round(number)) > 1e-6:
        return None
    return int(round(number))


def _growth_rate(value) -> float | None:
    number = _optional_float(value)
    if number is None or number < 0 or number >= 1.0:
        return None
    return number


def _optional_float(value) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number
