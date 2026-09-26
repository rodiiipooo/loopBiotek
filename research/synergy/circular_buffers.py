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
R_PRIME = 0.07  # SOURCED Fed H.15 bank prime, 2026-09-24
FAIRNESS = 0.9
EPSILON = 0.01  # Loop report alpha_Q example
ALPHA = 0.9  # reliability stand-in for the worm P10 firm book
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
    r_prime: float = R_PRIME,
    fairness: float = FAIRNESS,
    transport: float = 0.0,
) -> dict:
    """Unified prepaid for any sellable good.

    E[P(T)] = E[P0] * (1+r_inf)^T
    F_prelim = fairness * E[P(T)] / (1+r_prime)^T
    F_final = F_prelim + transport
    """
    if T < 0:
        raise ValueError("T must be >= 0")
    if r_inf <= -1.0 or r_prime <= -1.0:
        raise ValueError("rates must be > -1")
    if fairness < 0 or transport < 0:
        raise ValueError("fairness and transport must be >= 0")
    e_t = float(p0) * (1.0 + r_inf) ** T
    npv = e_t / (1.0 + r_prime) ** T
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
        "r_prime": r_prime,
        "fairness": fairness,
        "transport": float(transport),
        "formula": (
            "E[P(T)] = E[P0] * (1+r_inf)^T; "
            "F_prelim = fairness * E[P(T)] / (1+r_prime)^T; "
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
    payload = {
        "stage_gate": "Stage 1 worms only. Synergy math is planning. No Stage 2-5 spend.",
        "ok": all(row["fail_closed"] for row in shocks.values()),
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
