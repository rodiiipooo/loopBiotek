#!/usr/bin/env python3
"""Circular-shock buffers for the Loop cascade. Planning math only.

Stage 1 worms remain the spend source of record. Nothing here authorizes
Stage 2–5 purchases. The probabilistic culling governor is NOT simulated;
`cull_cap_deterministic` is an explicit proxy (see SPEC.md).
"""

from __future__ import annotations

import json
from pathlib import Path

# Defaults shared with research/quail fair prepaid.
R_INF = 0.027  # SOURCED BLS CPI-U Food, August 2026
R_INF_AS_OF = "2026-08"
# 3-month Treasury bill, secondary market, discount basis (FRED DTB3).
# SOURCED FRED DTB3 observation 2026-09-22: 4.01%.
# https://fred.stlouisfed.org/series/DTB3
# Rod lock for the prepaid discount. The H.15 3-month constant maturity
# the same week (4.24% on 2026-09-25) is a different quote and is not r_tbill.
R_TBILL = 0.0401
R_TBILL_AS_OF = "2026-09-22"
R_TBILL_TENOR = "3-month"
R_TBILL_SOURCE = "https://www.federalreserve.gov/releases/h15/"
FAIRNESS = 0.9
EPSILON = 0.01  # Loop report alpha_Q example
ALPHA = 0.9  # reliability stand-in for the worm P10 firm book
SAFETY_FRAC = 1.15  # ASSUMPTION gross-up on a forward breeder need
M_WEEKLY = 0.01  # planning weekly mortality; same default as research/quail
BUFFER_WEEKS = 2.0  # ASSUMPTION planning default, not a measured coverage

# Planning ceilings. Quail/BSFL round the Loop Module 2 break-evens
# (~0.405 and ~0.705 in reference/complete_model.ipynb). Others are unnamed
# until a source exists — do not invent a number.
WASTE_CEILINGS = {
    "quail": {
        "phi_max": 0.41,
        "tag": "SOURCED",
        "note": "Loop Module 2 break-even ~0.405; planning ceiling 0.41",
    },
    "bsfl": {
        "phi_max": 0.71,
        "tag": "SOURCED",
        "note": "Loop Module 2 break-even ~0.705; planning ceiling 0.71",
    },
    "crickets": {
        "phi_max": None,
        "tag": "ASSUMPTION",
        "note": "placeholder until sourced; no numeric ceiling",
    },
    "isopods": {
        "phi_max": None,
        "tag": "ASSUMPTION",
        "note": "placeholder until sourced; no numeric ceiling",
    },
    "fish": {
        "phi_max": None,
        "tag": "ASSUMPTION",
        "note": "placeholder until sourced; no numeric ceiling",
    },
    "worms": {
        "phi_max": None,
        "tag": "ASSUMPTION",
        "note": "placeholder until sourced; no numeric ceiling",
    },
}


def breed_floor(n0: float, n_start: float, n_safety: float) -> float:
    """N_floor = max(N0, N_start, N_safety). Sell only above this."""
    return max(float(n0), float(n_start), float(n_safety))


def surplus(n: float, floor: float) -> float:
    """Headcount that may be sold or culled. Never negative."""
    return max(0.0, float(n) - float(floor))


def firm_surplus(n: float, floor: float, alpha: float = ALPHA) -> float:
    """Reliability-quantile surplus. Not the median (P50) herd.

    Countable stock is alpha * N. Firm book is only what remains above the
    floor in that view. Worm alpha=0.9 stands in for the P10 firm-book rule
    until worm_forward_book is ported.
    """
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    return surplus(alpha * float(n), floor)


def fair_prepaid(
    p0: float,
    T: float,
    r_inf: float = R_INF,
    r_tbill: float = R_TBILL,
    fairness: float = FAIRNESS,
    transport: float = 0.0,
) -> dict:
    """Unified prepaid for any sellable good.

    E[P(T)] = E[P0] * (1+r_inf)^T
    F_prelim = fairness * E[P(T)] / (1+r_tbill)^T
    F_final = F_prelim + transport

    r_tbill is the 3-month Treasury constant-maturity yield (annual).
    """
    if T < 0:
        raise ValueError("T must be >= 0")
    if r_inf <= -1.0 or r_tbill <= -1.0:
        raise ValueError("rates must be > -1")
    if fairness < 0 or transport < 0:
        raise ValueError("fairness and transport must be >= 0")
    e_t = float(p0) * (1.0 + r_inf) ** T
    npv = e_t / (1.0 + r_tbill) ** T
    f_prelim = fairness * npv
    f_final = f_prelim + float(transport)
    return {
        "E_P0": float(p0),
        "E_P_T": e_t,
        "NPV": npv,
        "F_prelim": f_prelim,
        "F_final": f_final,
        "T": T,
        "r_inf": r_inf,
        "r_tbill": r_tbill,
        "r_tbill_as_of": R_TBILL_AS_OF,
        "r_tbill_tenor": R_TBILL_TENOR,
        "fairness": fairness,
        "transport": float(transport),
        "formula": (
            "E[P(T)] = E[P0] * (1+r_inf)^T; "
            "F_prelim = fairness * E[P(T)] / (1+r_tbill)^T; "
            "F_final = F_prelim + transport"
        ),
    }


def waste_ceiling(species: str) -> dict:
    key = species.strip().lower()
    if key not in WASTE_CEILINGS:
        raise KeyError(f"unknown species {species!r}")
    row = dict(WASTE_CEILINGS[key])
    row["species"] = key
    return row


def waste_fraction_ok(species: str, phi: float) -> dict:
    """True/False when a ceiling exists. None when the ceiling is still a placeholder."""
    row = waste_ceiling(species)
    if row["phi_max"] is None:
        row.update({"phi": float(phi), "ok": None})
        return row
    row.update({"phi": float(phi), "ok": float(phi) <= row["phi_max"] + 1e-12})
    return row


def cull_cap_deterministic(
    n_breed: float,
    n_req: float,
    tau_weeks: float,
    growth_per_week: float = 1.0,
    epsilon: float = EPSILON,
    n_floor: float | None = None,
) -> dict:
    """Proxy for the Loop culling governor. Not a probability.

    The report's rule is the largest harvest H such that
    P(N(w+tau) < N_req(w+tau)) <= epsilon.
    This stand-in has no draws. It requires the point projection to clear
    N_req / (1 - epsilon) after compounding growth_per_week for tau_weeks:

        (N - H) * g^tau >= N_req / (1 - epsilon)

    If n_floor is set, H is also clipped to surplus above that floor.
    """
    if not 0.0 <= epsilon < 1.0:
        raise ValueError("epsilon must be in [0, 1)")
    if tau_weeks < 0:
        raise ValueError("tau_weeks must be >= 0")
    if growth_per_week <= 0:
        raise ValueError("growth_per_week must be > 0")
    margin = float(n_req) / (1.0 - epsilon)
    grown = growth_per_week ** float(tau_weeks)
    raw = float(n_breed) - margin / grown
    h = max(0.0, raw)
    clipped_to_floor = False
    if n_floor is not None:
        cap = surplus(n_breed, n_floor)
        if h > cap:
            h = cap
            clipped_to_floor = True
    return {
        "H": h,
        "proxy": True,
        "epsilon": epsilon,
        "tau_weeks": float(tau_weeks),
        "margin_headcount": margin,
        "clipped_to_floor": clipped_to_floor,
        "note": "deterministic proxy for P(shortfall)<=epsilon; not a Monte Carlo",
    }


def cap_offtake_change(
    offtake_prev: float,
    offtake_proposed: float,
    n_breed: float,
    n_floor: float,
    alpha: float = ALPHA,
) -> dict:
    """Cap a weekly offtake change so the reliability view stays above the floor.

    Countable stock = alpha * N. Allowed offtake is surplus of that countable
    stock above the floor. A proposed jump past that surplus is refused
    (export halted) instead of cutting breeders.
    """
    room = firm_surplus(n_breed, n_floor, alpha=alpha)
    allowed = min(max(0.0, float(offtake_proposed)), room)
    # Do not raise offtake above the previous week if the raise is what
    # breaches the room. Still never exceed room.
    if offtake_proposed > offtake_prev and offtake_proposed > room:
        allowed = min(max(0.0, float(offtake_prev)), room)
    return {
        "allowed_offtake": allowed,
        "export_halted": allowed + 1e-9 < float(offtake_proposed),
        "firm_room": room,
        "alpha": alpha,
        "floor": float(n_floor),
    }


def _check_unit_interval(name: str, value: float, *, upper_open: bool = False) -> float:
    v = float(value)
    if upper_open:
        if not 0.0 <= v < 1.0:
            raise ValueError(f"{name} must be in [0, 1)")
    elif not 0.0 < v <= 1.0:
        raise ValueError(f"{name} must be in (0, 1]")
    return v


def safe_sell_limit(
    n_now: float,
    floor: float,
    alpha: float = ALPHA,
    safety_frac: float = SAFETY_FRAC,
    m_weekly: float = M_WEEKLY,
    lead_weeks: float = 0.0,
    n_req_forward: float | None = None,
) -> dict:
    """Fail-closed firm offtake. Deterministic. The Monte Carlo governor is TBD.

    H_max = max(0, N_now - floor)
    D_firm <= alpha * H_max

    When n_req_forward is set, the harvest is also clipped with the same
    shape as cull_cap_deterministic: survivors of what you keep must cover
    the forward breeder need times safety_frac. The per-week factor is
    survival (1 - m), not growth. Epsilon is left at 0 in that call because
    safety_frac is the margin; the report's epsilon = 0.01 draw is not run.
    """
    alpha_v = _check_unit_interval("alpha", alpha)
    if float(safety_frac) <= 0.0:
        raise ValueError("safety_frac must be > 0")
    m_v = _check_unit_interval("m_weekly", m_weekly, upper_open=True)
    if float(lead_weeks) < 0.0:
        raise ValueError("lead_weeks must be >= 0")
    if n_req_forward is not None and float(n_req_forward) < 0.0:
        raise ValueError("n_req_forward must be >= 0")

    h_max = surplus(n_now, floor)
    firm_max = alpha_v * h_max
    cull_cap_keep = None
    clipped_to_floor = None
    if n_req_forward is not None:
        # safety_frac scales the need; epsilon=0 so it is not applied twice.
        # (1-m) compounds as the deterministic "growth" factor (survival).
        proxy = cull_cap_deterministic(
            float(n_now),
            float(n_req_forward) * float(safety_frac),
            tau_weeks=float(lead_weeks),
            growth_per_week=1.0 - m_v,
            epsilon=0.0,
            n_floor=float(floor),
        )
        cull_cap_keep = proxy["H"]
        clipped_to_floor = proxy["clipped_to_floor"]
    allowed = firm_max if cull_cap_keep is None else min(firm_max, cull_cap_keep)
    return {
        "surplus": h_max,
        "firm_max": firm_max,
        "cull_cap_keep": cull_cap_keep,
        "allowed_firm": allowed,
        "n_now": float(n_now),
        "floor": float(floor),
        "alpha": alpha_v,
        "safety_frac": float(safety_frac),
        "m_weekly": m_v,
        "lead_weeks": float(lead_weeks),
        "n_req_forward": None if n_req_forward is None else float(n_req_forward),
        "clipped_to_floor": clipped_to_floor,
        "note": (
            "Deterministic fail-closed proxy. Firm offtake is alpha times surplus "
            "above the floor, then the cull cap when a forward breeder need is set. "
            "Full Monte Carlo governor (epsilon=0.01) is TBD. Cut offtake first; "
            "do not sell the breed floor."
        ),
    }


def birds_now_for_demand(
    d_firm: float,
    m_weekly: float = M_WEEKLY,
    lead_weeks: float = 10.0,
    safety_frac: float = SAFETY_FRAC,
    alpha: float = ALPHA,
) -> dict:
    """On-hand pipeline before a firm delivery.

    N_pipeline >= D_firm / (1-m)^w * s/alpha

    w is lead_weeks. s is safety_frac. alpha is the firm-book fraction.
    """
    if float(d_firm) < 0.0:
        raise ValueError("d_firm must be >= 0")
    alpha_v = _check_unit_interval("alpha", alpha)
    if float(safety_frac) <= 0.0:
        raise ValueError("safety_frac must be > 0")
    m_v = _check_unit_interval("m_weekly", m_weekly, upper_open=True)
    if float(lead_weeks) < 0.0:
        raise ValueError("lead_weeks must be >= 0")
    survival = (1.0 - m_v) ** float(lead_weeks)
    if survival <= 0.0:
        raise ValueError("survival over the lead must be > 0")
    n_min = float(d_firm) / survival * (float(safety_frac) / alpha_v)
    return {
        "n_pipeline_min": n_min,
        "d_firm": float(d_firm),
        "m_weekly": m_v,
        "lead_weeks": float(lead_weeks),
        "safety_frac": float(safety_frac),
        "alpha": alpha_v,
        "pipeline_multiple": (n_min / float(d_firm)) if float(d_firm) > 0.0 else None,
        "formula": "N_pipeline >= D_firm / (1-m)^w * s/alpha",
    }


def margin_backsolve(
    target_margin_usd: float,
    margin_per_unit: float,
    unit_name: str = "unit",
) -> dict:
    """H = target_margin_usd / margin_per_unit. Planning division only."""
    per = float(margin_per_unit)
    if per <= 0.0:
        raise ValueError("margin_per_unit must be > 0")
    if not str(unit_name).strip():
        raise ValueError("unit_name must be non-empty")
    return {
        "units": float(target_margin_usd) / per,
        "target_margin_usd": float(target_margin_usd),
        "margin_per_unit": per,
        "unit_name": str(unit_name),
        "formula": "H = target_margin_usd / margin_per_unit",
    }


def _shock_record(name: str, n_before: float, n_after: float, floor: float, export_halted: bool, detail: dict) -> dict:
    raided = n_after + 1e-9 < floor
    return {
        "name": name,
        "export_halted": bool(export_halted),
        "breeders_raided": raided,
        "fail_closed": bool(export_halted) and not raided,
        "breeders_before": n_before,
        "breeders_after": n_after,
        "floor": floor,
        **detail,
    }


def shock_scenarios() -> dict:
    """Four shocks. Each must halt export before breeders are taken under the floor."""
    # +50% quail offtake. Countable stock (alpha=0.9) only has room for the old rate.
    n_q, floor_q = 100.0, breed_floor(80, 80, 80)
    prev, proposed = 10.0, 15.0
    q = cap_offtake_change(prev, proposed, n_q, floor_q, alpha=ALPHA)
    n_q_after = n_q - q["allowed_offtake"]

    # -30% worm hatch. Floor stays at max(N0, new start, safety), not the shocked start.
    n_w = 1200.0
    n0_w, safety_w, start_w = 1000.0, 1000.0, 1200.0
    start_shocked = 0.7 * start_w
    floor_w = breed_floor(n0_w, start_shocked, safety_w)
    naive_sell = surplus(n_w, start_shocked)  # would follow the hatch print down
    guarded_sell = surplus(n_w, floor_w)
    n_w_after = n_w - guarded_sell

    # 2-week feed delay. The buffer is reserved for breeders; export feed is refused.
    n_feed, floor_feed = 100.0, breed_floor(80, 80, 80)
    buffer_weeks = BUFFER_WEEKS
    delay_weeks = 2.0
    breeder_reserve = delay_weeks
    export_feed_weeks = 1.0
    available_for_export = buffer_weeks - breeder_reserve
    feed_halt = export_feed_weeks > available_for_export + 1e-12

    # Insect die-off. Mortality is assigned to surplus first (control priority,
    # not a biological claim). Downstream feed export above the remaining
    # surplus is halted. Breeders are not sold to fill the order.
    n_i, floor_i = 100.0, breed_floor(70, 70, 70)
    die = 25.0
    n_i_after = n_i - die
    export_requested = 20.0
    insect_allowed = surplus(n_i_after, floor_i)
    insect_halt = insect_allowed + 1e-9 < export_requested

    return {
        "quail_offtake_plus_50": _shock_record(
            "quail_offtake_plus_50",
            n_q,
            n_q_after,
            floor_q,
            q["export_halted"],
            {"proposed_offtake": proposed, "allowed_offtake": q["allowed_offtake"]},
        ),
        "worm_hatch_minus_30": _shock_record(
            "worm_hatch_minus_30",
            n_w,
            n_w_after,
            floor_w,
            naive_sell > guarded_sell + 1e-9,
            {
                "naive_sell_if_floor_followed_hatch": naive_sell,
                "allowed_sell": guarded_sell,
                "start_after_shock": start_shocked,
            },
        ),
        "feed_delay_2_weeks": _shock_record(
            "feed_delay_2_weeks",
            n_feed,
            n_feed,  # no cull to stretch feed
            floor_feed,
            feed_halt,
            {
                "buffer_weeks": buffer_weeks,
                "delay_weeks": delay_weeks,
                "available_export_feed_weeks": available_for_export,
            },
        ),
        "insect_dieoff": _shock_record(
            "insect_dieoff",
            n_i,
            n_i_after,
            floor_i,
            insect_halt,
            {
                "mortality": die,
                "export_requested": export_requested,
                "allowed_export": insect_allowed,
                "mortality_rule": "surplus first; do not sell breeders to fill feed orders",
            },
        ),
    }


def smoke(path: Path | None = None) -> dict:
    """Write results/circular_buffers_smoke.json and return the payload."""
    p0 = (13.17 + 10.06 + 14.16) / 3.0  # same foodservice mean as research/quail
    priced = fair_prepaid(p0, 0.5)
    flat = fair_prepaid(p0, 0.5, r_inf=0.0)
    cull = cull_cap_deterministic(100.0, 90.0, tau_weeks=8, growth_per_week=1.0, epsilon=EPSILON, n_floor=95.0)
    shocks = shock_scenarios()
    sell_open = safe_sell_limit(1000.0, 800.0)
    sell_forward = safe_sell_limit(1000.0, 800.0, lead_weeks=10.0, n_req_forward=750.0)
    pipeline = birds_now_for_demand(100.0)
    backsolve_lb = margin_backsolve(3000.0, 7.82, unit_name="lb")
    helpers_ok = (
        abs(sell_open["surplus"] - 200.0) < 1e-9
        and abs(sell_open["firm_max"] - 180.0) < 1e-9
        and sell_open["cull_cap_keep"] is None
        and abs(sell_open["allowed_firm"] - 180.0) < 1e-9
        and sell_forward["cull_cap_keep"] is not None
        and sell_forward["allowed_firm"] <= sell_forward["firm_max"] + 1e-9
        and sell_forward["allowed_firm"] <= sell_forward["cull_cap_keep"] + 1e-9
        and sell_forward["allowed_firm"] + 1e-9 < sell_forward["firm_max"]
        and pipeline["n_pipeline_min"] > pipeline["d_firm"]
        and abs(backsolve_lb["units"] - (3000.0 / 7.82)) < 1e-9
    )
    payload = {
        "stage_gate": "Stage 1 worms only. Synergy math is planning. No Stage 2-5 spend.",
        "ok": all(row["fail_closed"] for row in shocks.values()) and helpers_ok,
        "helpers_ok": helpers_ok,
        "fair_prepaid_T0.5": priced,
        "fair_prepaid_T0.5_r_inf_0": {"F_prelim": flat["F_prelim"]},
        "waste_ceilings": {name: waste_ceiling(name) for name in WASTE_CEILINGS},
        "waste_checks": {
            "quail_0.41": waste_fraction_ok("quail", 0.41),
            "quail_0.50": waste_fraction_ok("quail", 0.50),
            "bsfl_0.71": waste_fraction_ok("bsfl", 0.71),
            "crickets_placeholder": waste_fraction_ok("crickets", 0.2),
        },
        "cull_cap_proxy": cull,
        "safe_sell_open": sell_open,
        "safe_sell_forward_need": sell_forward,
        "birds_now_for_demand": pipeline,
        "margin_backsolve_3k_per_lb": backsolve_lb,
        "breed_floor_example": {
            "floor": breed_floor(10, 12, 9),
            "surplus_above_floor": surplus(15, breed_floor(10, 12, 9)),
            "firm_surplus_alpha_0.9": firm_surplus(15, breed_floor(10, 12, 9), ALPHA),
        },
        "shocks": shocks,
        "legacy_note": (
            "worm_forward_book flat 33% discount is legacy in the external "
            "worm model and is not used here. New planning prices use F_prelim."
        ),
    }
    out = path or Path(__file__).resolve().parent / "results" / "circular_buffers_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = smoke()
    if not result["ok"]:
        raise SystemExit("shock scenarios did not fail closed")
    sample = result["fair_prepaid_T0.5"]
    print(
        f"F_prelim(T=0.5)={sample['F_prelim']:.4f}  "
        f"F_final={sample['F_final']:.4f}  shocks_ok={result['ok']}"
    )
