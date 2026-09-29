#!/usr/bin/env python3
"""Regenerate cascade growth figures and check the couplings.

One command, from this directory:

    python3 smoke.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_RESEARCH = Path(__file__).resolve().parents[1]
for folder in (_RESEARCH / "ops-dashboard",):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import model  # noqa: E402
import plots  # noqa: E402
import engine  # noqa: E402
import quail_income  # noqa: E402

PLOTS = _RESEARCH / "plots"
OUT = Path(__file__).resolve().parent / "results" / "cascade_growth_smoke.json"


def _at(ens: dict, name: str, week: int, which: str = "p50") -> float:
    return float(ens["series"][name][which][week])


def main() -> dict:
    doubling = model.worm_biomass_doubling_week()
    if doubling["doubling_week"] != 13:
        raise SystemExit(f"uncoupled worm doubling week is {doubling['doubling_week']}, expected 13")

    practice = model.ensemble(
        model.PRACTICE_MALES,
        model.PRACTICE_FEMALES,
        weeks=model.DEFAULT_WEEKS,
        paths=model.DEFAULT_PATHS,
        seed=model.DEFAULT_SEED,
    )
    male_heavy = model.ensemble(
        model.MALE_HEAVY_MALES,
        model.MALE_HEAVY_FEMALES,
        weeks=model.DEFAULT_WEEKS,
        paths=model.DEFAULT_PATHS,
        seed=model.DEFAULT_SEED,
    )

    again = model.simulate(
        model.PRACTICE_MALES,
        model.PRACTICE_FEMALES,
        weeks=12,
        seed=model.DEFAULT_SEED,
        path_index=2,
        stochastic=True,
    )
    again_b = model.simulate(
        model.PRACTICE_MALES,
        model.PRACTICE_FEMALES,
        weeks=12,
        seed=model.DEFAULT_SEED,
        path_index=2,
        stochastic=True,
    )
    if again[-1]["quail_total"] != again_b[-1]["quail_total"]:
        raise SystemExit("same seed and path index did not replay")
    for row in again[1:]:
        if row["worm_export_headcount"] > row["worm_allowed_headcount"] + 1e-6:
            raise SystemExit("worm export exceeded safe_sell_limit")
        if row["cricket_harvest_headcount"] > row["cricket_allowed_headcount"] + 1e-6:
            raise SystemExit("cricket harvest exceeded safe_sell_limit")
        if row["quail_breeder_export"] != 0.0:
            raise SystemExit("quail breeders were exported")

    if abs(model.WORM_DOUBLING_TARGET_WEEKS - engine.SPECIES["worms"].doubling_weeks) > 1e-9:
        raise SystemExit("worm doubling target drifted from the ops dashboard")
    if abs(model.WORM_WEEKLY_SIGMA - engine.SPECIES["worms"].weekly_sigma) > 1e-12:
        raise SystemExit("worm sigma drifted from the ops dashboard")
    if abs(model.WORM_CARRYING_MULTIPLE - engine.SPECIES["worms"].carrying_multiple) > 1e-12:
        raise SystemExit("worm carrying multiple drifted from the ops dashboard")
    if abs(model.WORM_PER_LB - engine.WORM_HEADCOUNT_PER_LB) > 1e-12:
        raise SystemExit("worms per pound drifted from the ops dashboard")
    if abs(model.QUAIL_INTAKE_G_PER_DAY - quail_income.INTAKE_G_PER_BIRD_DAY) > 1e-12:
        raise SystemExit("quail intake drifted from quail_income")
    if abs(model.QUAIL_WORM_SHARE - quail_income.WORM_SHARE) > 1e-12:
        raise SystemExit("quail protein share drifted from quail_income")

    allowed_tags = {"ASSUMPTION", "SOURCED", "DERIVED", "SCOPE"}
    catalog = model.parameter_catalog()
    if any(row["tag"] not in allowed_tags for row in catalog):
        raise SystemExit("a planning input has no tag")

    hens_gap_26 = _at(practice, "quail_breeder_females", 26) / max(_at(male_heavy, "quail_breeder_females", 26), 1e-9)
    hens_gap_52 = _at(practice, "quail_breeder_females", 52) / max(_at(male_heavy, "quail_breeder_females", 52), 1e-9)
    if hens_gap_26 < 1.5 or hens_gap_52 < 1.4:
        raise SystemExit("1:3 founders did not keep more breeder hens than 3:1")
    if _at(practice, "greens_canopy_kg", 26) > _at(male_heavy, "greens_canopy_kg", 26) - 10.0:
        raise SystemExit("the larger hen flock did not draw greens down faster")
    if _at(practice, "cricket_adults", 26) > _at(male_heavy, "cricket_adults", 26) - 40.0:
        raise SystemExit("the larger hen flock did not leave fewer cricket adults")
    if _at(practice, "protein_to_fish_kg", 8) >= _at(male_heavy, "protein_to_fish_kg", 8):
        raise SystemExit("fish did not receive less protein when the quail flock was larger")
    if _at(practice, "protein_to_fish_kg", 26) >= _at(male_heavy, "protein_to_fish_kg", 26):
        raise SystemExit("fish protein share did not stay lower for the larger hen flock")
    if _at(practice, "manure_to_worms_kg", 26) <= _at(male_heavy, "manure_to_worms_kg", 26):
        raise SystemExit("the larger flock did not return more manure")
    if practice["quail_males0"] * 3 != practice["quail_females0"]:
        raise SystemExit("practice founders are not 1 male to 3 females")
    if male_heavy["quail_males0"] != 3 * male_heavy["quail_females0"]:
        raise SystemExit("comparison founders are not 3 males to 1 female")
    if practice["quail_males0"] + practice["quail_females0"] != male_heavy["quail_males0"] + male_heavy["quail_females0"]:
        raise SystemExit("the two founder flocks do not have the same headcount")

    written = plots.write_all(practice, male_heavy, PLOTS)
    for file in written:
        if not file.is_file() or file.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise SystemExit(f"missing png {file}")

    payload = {
        "ok": True,
        "stage_gate": model.STAGE_GATE,
        "seed": model.DEFAULT_SEED,
        "paths": model.DEFAULT_PATHS,
        "weeks": model.DEFAULT_WEEKS,
        "p10_note": practice["p10_note"],
        "worm_doubling_week_ample_feed": doubling["doubling_week"],
        "practice_founders": {"males": practice["quail_males0"], "females": practice["quail_females0"]},
        "male_heavy_founders": {"males": male_heavy["quail_males0"], "females": male_heavy["quail_females0"]},
        "week_26_median": {
            "practice_hens": _at(practice, "quail_breeder_females", 26),
            "male_heavy_hens": _at(male_heavy, "quail_breeder_females", 26),
            "practice_greens_kg": _at(practice, "greens_canopy_kg", 26),
            "male_heavy_greens_kg": _at(male_heavy, "greens_canopy_kg", 26),
            "practice_crickets": _at(practice, "cricket_adults", 26),
            "male_heavy_crickets": _at(male_heavy, "cricket_adults", 26),
            "practice_protein_to_fish_kg": _at(practice, "protein_to_fish_kg", 26),
            "male_heavy_protein_to_fish_kg": _at(male_heavy, "protein_to_fish_kg", 26),
            "practice_manure_kg": _at(practice, "manure_to_worms_kg", 26),
            "male_heavy_manure_kg": _at(male_heavy, "manure_to_worms_kg", 26),
            "practice_worm_kg": _at(practice, "worm_biomass_kg", 26),
            "male_heavy_worm_kg": _at(male_heavy, "worm_biomass_kg", 26),
        },
        "plots": [str(path.relative_to(_RESEARCH.parent)) for path in written],
        "parameters": catalog,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    slim = {key: value for key, value in payload.items() if key != "parameters"}
    # Keep the tagged catalog beside the summary so a reader can see every ASSUMPTION.
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return slim


if __name__ == "__main__":
    result = main()
    if not result["ok"]:
        raise SystemExit("cascade growth smoke failed")
    week = result["week_26_median"]
    print(
        f"doubling_week={result['worm_doubling_week_ample_feed']}  "
        f"hens_1to3={week['practice_hens']:.1f}  hens_3to1={week['male_heavy_hens']:.1f}  "
        f"greens_1to3={week['practice_greens_kg']:.1f}  greens_3to1={week['male_heavy_greens_kg']:.1f}"
    )
    for plot in result["plots"]:
        print(plot)
