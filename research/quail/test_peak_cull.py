#!/usr/bin/env python3
"""Smoke for the Coturnix peak-lay cull. Stage 4 planning. Not a purchase.

Run from anywhere:

    python3 research/quail/test_peak_cull.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import quail_model as q  # noqa: E402


def main() -> dict:
    # Rise, plateau, and the week the planning slot gives up.
    assert q.productive_hen_fraction(5) == 0.0
    assert q.productive_hen_fraction(6) == 0.0
    assert abs(q.productive_hen_fraction(15) - 1.0) < 1e-12
    assert abs(q.productive_hen_fraction(26) - 1.0) < 1e-12
    assert q.hen_in_peak(13) is False
    assert q.hen_in_peak(14) is True
    assert q.hen_in_peak(33) is True
    assert q.hen_in_peak(34) is False
    assert q.productive_hen_fraction(34) < q.PEAK_SLOT_MIN
    ages = q.peak_age_weeks()
    assert ages[0] == 14 and ages[-1] == 33

    # 1 male : 3 females, and the slot count snaps up to that ratio.
    snapped = q.peak_slot_targets(52)
    assert snapped["females"] == 3 * snapped["males"]
    assert snapped["males"] >= 17 and snapped["females"] >= 51
    exact = q.peak_slot_targets(51)
    assert exact == {"males": 17, "females": 51}

    # Steady state holds the in-peak hen slots. Day-old inflow is the pipeline.
    held = q.steady_peak_flock(51)
    m = q.WEEKLY_MORTALITY
    r = held["day_old_females_per_week"]
    in_peak = sum(r * ((1.0 - m) ** a) for a in ages)
    assert abs(in_peak - 51.0) < 1e-6
    assert held["breeder_males"] == 17
    assert held["breeder_females"] == 51
    assert abs(held["breeder_females"] / held["breeder_males"] - 3.0) < 1e-12
    assert held["hens_into_cage_per_week"] > 0.0
    assert held["pipeline_birds"] > 0.0
    # Peak hen-day is above the blended 280/year rate. The blend already includes decline.
    assert held["peak_eggs_per_hen_week"] > q.EGGS_PER_HEN_PER_YEAR / (q.DAYS_PER_YEAR / q.DAYS_PER_WEEK)

    # Out-of-peak hens go to meat. The 17/51 floor stays. Replacements fill the slots.
    kept = q.peak_cull_policy(
        [
            {"id": "m", "sex": "M", "age_weeks": 20, "count": 17},
            {"id": "young", "sex": "F", "age_weeks": 20, "count": 51},
            {"id": "old", "sex": "F", "age_weeks": 40, "count": 10},
        ]
    )
    assert kept["cull_to_meat_hens"] == 10
    assert kept["replacements_hens"] == 0
    assert kept["floor_held"] is True
    assert kept["fail_closed"] is True
    assert kept["females_remaining"] >= 51
    assert kept["males_remaining"] >= 17

    # Every hen is past peak. Culling them would raid Ne. Keep them and ask for 51 replacements.
    blocked = q.peak_cull_policy(
        age_bins=[
            {"sex": "M", "age_weeks": 20, "count": 17},
            {"sex": "F", "age_weeks": 40, "count": 51},
        ]
    )
    assert blocked["cull_to_meat_hens"] == 0
    assert blocked["kept_out_of_peak_hens"] == 51
    assert blocked["replacements_hens"] == 51
    assert blocked["floor_held"] is True
    assert blocked["raided_floor"] is False

    # Extra males above 1:3 of the hens on hand are surplus. In-peak hens are not capped.
    surplus_males = q.peak_cull_policy(
        age_bins=[
            {"sex": "M", "age_weeks": 20, "count": 30},
            {"sex": "F", "age_weeks": 20, "count": 60},
        ],
        target_hen_slots=51,
    )
    assert surplus_males["cull_to_meat_hens"] == 0
    assert surplus_males["cull_to_meat_males"] == 10
    assert surplus_males["males_remaining"] == 20
    assert surplus_males["females_remaining"] == 60
    assert surplus_males["females_remaining"] == 3 * surplus_males["males_remaining"]

    # Age-structured eggs: starters placed in peak lay at the peak rate; past-peak hens do not.
    # Zero weekly mortality so the starter cull is the full pen, not a survival haircut.
    params = q.BiologyParams(use_peak_lay=True, weekly_mortality=0.0)
    early = q.simulate_population(5, 15, 1, weeks=0, params=params)
    assert abs(early.states[0].hens_in_peak - 15.0) < 1e-6
    assert early.states[0].eggs_desired_this_week > 15.0 * 6.0
    later = q.simulate_population(5, 15, 1, weeks=24, params=params)
    culled = sum(row.peak_culls_this_week for row in later.states)
    assert culled > 14.0

    table = q.productive_fraction_table(60)
    assert len(table) == 61
    assert table[15]["in_peak"] is True
    assert table[34]["in_peak"] is False

    payload = {
        "ok": True,
        "stage_gate": "Stage 4 quail planning. Stage 1 worms remain the only spend.",
        "peak_weeks": [ages[0], ages[-1]],
        "peak_hen_day": q.PEAK_HEN_DAY,
        "peak_slot_min": q.PEAK_SLOT_MIN,
        "steady_51": {
            "day_old_females_per_week": held["day_old_females_per_week"],
            "hens_into_cage_per_week": held["hens_into_cage_per_week"],
            "pipeline_birds": held["pipeline_birds"],
            "pipeline_males": held["pipeline_males"],
            "pipeline_females": held["pipeline_females"],
            "breeder_males": held["breeder_males"],
            "breeder_females": held["breeder_females"],
        },
        "fraction_by_week": table,
        "tags": q.layer_life_cycle(),
    }
    out = HERE / "results" / "peak_cull_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = main()
    steady = result["steady_51"]
    print(
        "peak weeks",
        result["peak_weeks"],
        "into cage/week",
        round(steady["hens_into_cage_per_week"], 3),
        "pipeline",
        round(steady["pipeline_birds"], 2),
    )
