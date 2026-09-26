"""Print the Stage-4 worked example and write ``results/sample_run.*``."""

from __future__ import annotations

import json
from pathlib import Path

from research.quail.quail_model import (
    E_P_COMP_USD_PER_LB,
    KIT_PRICE_USD,
    PRIME_AS_OF,
    PRIME_RATE,
    fair_forward_price_per_lb,
    fair_prepaid_contract,
    kits_needed,
    population,
    production_rate,
    production_rate_required,
    sustain_inventory_lb,
    t_ready,
)

Y = 5
Z = 15
U = 1
C_BAR = 2.0
T_YEARS = 0.5


def sample() -> dict:
    ready = t_ready(C_BAR, Y, Z, U)
    rate = production_rate(ready, Y, Z, U)
    expected = fair_forward_price_per_lb()
    prepaid = fair_prepaid_contract(expected, PRIME_RATE, T_YEARS)
    return {
        "y_founder_males": Y,
        "z_founder_females": Z,
        "U_kits": U,
        "c_bar_lb_per_week": C_BAR,
        "t_ready_days": ready,
        "t_ready_weeks": None if ready is None else ready / 7.0,
        "r_prod_lb_per_week": rate,
        "r_prod_rounded_1dp": None if rate is None else round(rate, 1),
        "production_rate_required_lb_per_week": production_rate_required(C_BAR),
        "sustain_inventory_lb_at_ready": sustain_inventory_lb(C_BAR, ready, Y, Z, U),
        "kits_needed": kits_needed(C_BAR, Y, Z),
        "kit_price_usd": KIT_PRICE_USD,
        "population_at_ready": population(ready, Y, Z, U),
        "E_P_comp_usd_per_lb": expected,
        "prime_rate": PRIME_RATE,
        "prime_as_of": PRIME_AS_OF,
        "T_years": T_YEARS,
        "F0_usd_per_lb": prepaid,
        "note": (
            "Stage-4 planning screen only. Stage 1 worms remain the spend "
            "source of record. r_prod 28.875 lb/week rounds to 28.9."
        ),
    }


def format_report(result: dict) -> str:
    lines = [
        "Jumbo Coturnix Stage-4 screen",
        f"y={result['y_founder_males']} males, z={result['z_founder_females']} females, "
        f"U={result['U_kits']} kit, c_bar={result['c_bar_lb_per_week']} lb/week",
        f"t_ready = {result['t_ready_days']} days "
        f"(week {result['t_ready_weeks']:.0f})",
        f"r_prod = {result['r_prod_lb_per_week']:.4f} lb/week "
        f"(≈ {result['r_prod_rounded_1dp']:.1f})",
        f"production_rate_required = {result['production_rate_required_lb_per_week']} lb/week",
        f"sustain inventory at ready = {result['sustain_inventory_lb_at_ready']} lb",
        f"kits_needed = {result['kits_needed']} at ${result['kit_price_usd']:.2f} list",
        f"E[P_comp] = {result['E_P_comp_usd_per_lb']:.4f} USD/lb",
        f"prime = {result['prime_rate']:.2%} as of {result['prime_as_of']}, "
        f"T = {result['T_years']} y",
        f"F0 = {result['F0_usd_per_lb']:.6f} USD/lb (≈ 12.0488)",
        result["note"],
    ]
    return "\n".join(lines) + "\n"


def write_results(result: dict, report: str) -> Path:
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "sample_run.txt").write_text(report, encoding="utf-8")
    (out / "sample_run.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return out


def main() -> None:
    result = sample()
    report = format_report(result)
    write_results(result, report)
    print(report, end="")
    # Guard the published sample so a silent drift fails the CLI.
    if result["t_ready_days"] != 77:
        raise SystemExit(f"t_ready drifted: {result['t_ready_days']}")
    if abs(result["r_prod_lb_per_week"] - 28.9) > 0.05:
        raise SystemExit(f"r_prod drifted: {result['r_prod_lb_per_week']}")
    if abs(result["E_P_comp_usd_per_lb"] - E_P_COMP_USD_PER_LB) > 1e-9:
        raise SystemExit("E[P] drifted")
    if abs(result["F0_usd_per_lb"] - 12.0488) > 0.00015:
        raise SystemExit(f"F0 drifted: {result['F0_usd_per_lb']}")


if __name__ == "__main__":
    main()
