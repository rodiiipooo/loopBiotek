#!/usr/bin/env python3
"""CLI: jumbo Coturnix production-rate ramp + fair forward table + optional kits_needed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from quail_model import (
    DRESS_WEIGHT_LBS,
    FAIRNESS_DISCOUNT_FACTOR,
    INFLATION_RATE,
    INFLATION_RATE_AS_OF,
    KIT_PRICE_USD,
    PRIME_RATE,
    PRIME_RATE_AS_OF,
    can_sustain,
    expected_comp_price,
    fair_prepaid_forward_per_lb,
    forward_table,
    kits_needed,
    meat_lbs,
    production_rate,
    quail_population,
    rate_ramp_table,
    simulate_population,
    t_ready,
    defaults_table,
    kit_caps,
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Loop Biotek jumbo quail planning (Stage 4 planning math)")
    ap.add_argument("--y", type=float, default=5.0, help="starting male breeders")
    ap.add_argument("--z", type=float, default=15.0, help="starting female breeders")
    ap.add_argument("--U", type=float, default=1.0, help="Grit Quail Professional Kit units")
    ap.add_argument("--c-bar", type=float, default=2.0, help="avg consumption rate lb/week")
    ap.add_argument("--weeks", type=int, default=40, help="ramp horizon weeks")
    ap.add_argument("--X", type=float, default=None, help="optional cumulative meat demand lbs")
    ap.add_argument("--json-out", type=str, default="", help="write results JSON path")
    args = ap.parse_args()

    print("=" * 72)
    print("Loop Biotek — Jumbo Coturnix (Stage 4 planning; Stage 1 = worms SoR)")
    print("=" * 72)
    print(f"Starters: y={args.y}♂  z={args.z}♀   Kits U={args.U}   dress={DRESS_WEIGHT_LBS:.3f} lb/bird")
    print(f"Kit capex @U: ${args.U * KIT_PRICE_USD:,.2f}   Caps: {kit_caps(args.U)}")
    print()

    # Population path (sample)
    path = simulate_population(args.y, args.z, args.U, weeks=args.weeks)
    print("--- Population / harvest path (every 4 weeks) ---")
    print(f"{'wk':>4} {'day':>6} {'total':>8} {'breed':>8} {'meat_wk':>9} {'meat_cum':>10} {'bind':>18}")
    for st in path.states[::4]:
        breed = st.males_breeders + st.females_breeders
        print(
            f"{st.week:4d} {st.day:6.0f} {st.total:8.1f} {breed:8.1f} "
            f"{st.meat_lbs_this_week:9.3f} {st.meat_lbs_cumulative:10.3f} {st.capacity_bind or '-':>18}"
        )

    print()
    print("--- Production rate ramp (4-week mean lb/week) ---")
    ramp = rate_ramp_table(args.y, args.z, args.U, weeks=args.weeks)
    print(f"{'wk':>4} {'r_prod':>10} {'cum_lb':>10} {'heads':>8}")
    for row in ramp[::4]:
        print(f"{row['week']:4d} {row['r_prod_lb_per_week']:10.3f} {row['meat_lbs_cum']:10.3f} {row['total_heads']:8.1f}")

    print()
    ready = t_ready(args.c_bar, args.y, args.z, args.U, rate_unit="lb_per_week")
    print(f"--- Sustain consumption c̄ = {args.c_bar} lb/week ---")
    print(f"t_ready: {ready['t_ready_days']} days (week {ready['t_ready_weeks']})  feasible={ready['feasible']}")
    if ready["feasible"]:
        cs = can_sustain(args.c_bar, ready["t_ready_days"], args.y, args.z, args.U)
        print(f"At t_ready: r_prod={cs['r_prod']:.3f} lb/wk  sustains={cs['sustains']}  surplus={cs['surplus_rate']:.3f}")

    print()
    p_comp = expected_comp_price()
    print(
        f"--- Fair prepaid (prime={PRIME_RATE*100:.2f}% as of {PRIME_RATE_AS_OF}; "
        f"r_inf={INFLATION_RATE*100:.1f}% CPI-U Food {INFLATION_RATE_AS_OF}; "
        f"fairness={FAIRNESS_DISCOUNT_FACTOR:.2f}; transport=$0/lb) ---"
    )
    print(f"E[P_comp(0)] spot = ${p_comp:.4f}/lb (foodservice mean)")
    print(
        "E[P_comp(T)] = E[P_comp(0)] * (1+r_inf)^T; "
        "NPV = E[P_comp(T)] / (1+r_prime)^T; "
        "F_prelim = 0.9 * NPV; F_final = F_prelim + transport"
    )
    print(f"{'T_yr':>6} {'P_meat(T)':>12} {'F_prelim':>12} {'F_final':>12} {'DF':>8}")
    for row in forward_table([0.25, 0.5, 0.75, 1.0, 1.5, 2.0], p_comp=p_comp):
        print(
            f"{row['T_years']:6.2f} ${row['E_P_comp_at_T']:11.4f} "
            f"${row['F_prelim_usd_per_lb']:11.4f} "
            f"${row['F_0_usd_per_lb']:11.4f} {row['time_value_discount_factor']:8.4f}"
        )
    sample = fair_prepaid_forward_per_lb(0.5, p_comp=p_comp)
    flat = fair_prepaid_forward_per_lb(0.5, p_comp=p_comp, r_inf=0.0)
    print(
        f"Cash flows (T=0.5y, r_inf={INFLATION_RATE:.3f}): "
        f"deposit F_final ${sample['F_0_usd_per_lb']:.4f}/lb at t=0 "
        f"(F_prelim ${sample['F_prelim_usd_per_lb']:.4f}; "
        f"E[P_comp(T)] ${sample['E_P_comp_at_T']:.4f}); deliver 1 lb at T."
    )
    print(
        f"Zero-inflation check (r_inf=0, same T, prime, fairness): "
        f"F_prelim ${flat['F_prelim_usd_per_lb']:.4f}/lb"
    )

    out = {
        "y": args.y,
        "z": args.z,
        "U": args.U,
        "c_bar_lb_per_week": args.c_bar,
        "t_ready": ready,
        "fair_forward_sample_T0.5": sample,
        "fair_forward_sample_T0.5_r_inf_0": flat,
        "E_P_comp": p_comp,
        "prime_rate": PRIME_RATE,
        "prime_as_of": PRIME_RATE_AS_OF,
        "r_inf": INFLATION_RATE,
        "r_inf_as_of": INFLATION_RATE_AS_OF,
        "defaults": defaults_table(),
        "ramp": ramp,
    }

    if args.X is not None:
        kn = kits_needed(args.X, args.weeks * 7, args.y, args.z, t_unit="days")
        print()
        print(f"--- kits_needed for cumulative X={args.X} lb by day {args.weeks*7} ---")
        print(json.dumps({k: kn[k] for k in kn if k != "search"}, indent=2))
        out["kits_needed"] = kn

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2, default=str))
        print(f"\nWrote {args.json_out}")


if __name__ == "__main__":
    main()
