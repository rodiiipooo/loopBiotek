#!/usr/bin/env python3
"""Smoke for the Stage-4 order gate. Planning fixtures, not a sale.

    python3 research/ops-dashboard/test_order_control.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import order_control as oc


def _herd(males: float, females: float, n0: float = 68.0) -> dict:
    return oc.quail_planning_state(males, females, n0)


def _policy(**overrides) -> dict:
    # g is explicit here so the older integrity tests still apply the growth helper.
    # The operator default, used by check_revenue_floor, does not set g.
    base = {"g": 0.0, "t_weeks": 26, "H_months": 3, "R_min": 0.0, "hurdle": 0.0}
    base.update(overrides)
    return base


def check_sellable_falls_as_growth_rises() -> list[dict]:
    state = _herd(1000, 3000)
    rows = [oc.sellable_for_growth("quail", state, g, 26) for g in (0.0, 0.01, 0.02)]
    amounts = [row["allowed"] for row in rows]
    assert amounts[0] > amounts[1] > amounts[2] > 0, amounts
    assert all(row["fail_closed"] is False for row in rows)
    missing = oc.sellable_for_growth("quail", {}, 0.01, 26)
    assert missing["allowed"] == 0 and missing["fail_closed"] is True
    huge = oc.sellable_for_growth(
        "quail", state, 0.0, 26, [{"week": 0, "heads": 10000}]
    )
    assert huge["feasible"] is False and huge["residual"] == 0
    # Mortality proxy, no births. A worm herd only a little above its floor
    # cannot cover that floor for 13 weeks, so both caps are 0. A larger herd can.
    thin = oc.sellable_for_growth("worms", {"n_now": 20000, "n0": 16500}, 0.0, 13)
    thick = oc.sellable_for_growth("worms", {"n_now": 30000, "n0": 16500}, 0.0, 13)
    assert thin["allowed"] == 0 and thin["allowed_by_t"] == 0
    assert thick["allowed"] > 0
    nameless = oc.sellable_for_growth("crickets", {"n_now": 1000, "n0": 100}, 0.0, 10)
    assert nameless["allowed"] == 0 and nameless["fail_closed"] is True
    return rows


def check_surplus_and_ne() -> tuple[oc.AcceptDecision, oc.AcceptDecision]:
    book = oc.OrderBook()
    surplus = oc.accept_order(
        {"species": "quail", "qty": 5000, "unit": "head", "week": 4},
        book,
        {"quail": _herd(50, 150)},
        _policy(),
    )
    assert surplus.accept is False
    assert any("surplus" in reason for reason in surplus.reasons), surplus.reasons

    nucleus = oc.accept_order(
        {"species": "quail", "qty": 1, "unit": "head", "week": 4},
        book,
        {"quail": _herd(17, 51)},
        _policy(),
    )
    assert nucleus.accept is False
    assert any("Ne floor" in reason for reason in nucleus.reasons), nucleus.reasons
    return surplus, nucleus


def check_reservations() -> None:
    state = _herd(1000, 3000)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "order_book.json"
        book = oc.OrderBook(path)
        before = book.available_firm("quail", 26, state, 0.0, 26)
        assert before["available"] > 10, before
        saved = book.reserve({"id": "A", "species": "quail", "heads": 25, "week": 26})
        assert saved["ok"] is True
        after = book.available_firm("quail", 26, state, 0.0, 26)
        assert after["available"] <= before["available"] - 25 + 1e-6
        assert after["reserved_heads"] == 25
        reloaded = oc.OrderBook(path)
        assert reloaded.reserved_heads("quail") == 25
        released = book.release("A")
        assert released["ok"] is True
        restored = book.available_firm("quail", 26, state, 0.0, 26)
        assert abs(restored["available"] - before["available"]) < 1e-6


def check_roi_reject() -> oc.AcceptDecision:
    def cheap(order, state):
        del order, state
        return 0.20

    decision = oc.accept_order(
        {"id": "cheap", "species": "quail", "qty": 20, "unit": "lb", "week": 8},
        oc.OrderBook(),
        {"quail": _herd(1000, 3000)},
        _policy(price_fn=cheap),
    )
    assert decision.accept is False
    assert any(reason.startswith("ROI gate") for reason in decision.reasons), decision.reasons
    assert decision.residuals["roi"]["accept_hurdle_met"] is False
    return decision


def check_sample() -> tuple[oc.AcceptDecision, oc.AcceptDecision, dict]:
    plan = oc.capacity_plan(3000, species="quail")
    assert plan["feasible"] is True, plan["reasons"]
    assert plan["target_kind"] == "revenue"
    assert plan["min_monthly_revenue"] + 1e-6 >= 3000.0
    assert plan["g_explicit"] is False
    state = plan["state"]
    accept = oc.accept_order(
        {"id": "sample-yes", "species": "quail", "qty": 10, "unit": "head", "week": 4, "buyer": "planning sample"},
        oc.OrderBook(),
        {"quail": state},
        {"t_weeks": 26, "H_months": 3, "R_min": 3000.0, "hurdle": 0.0},
    )
    assert accept.accept is True, accept.reasons
    assert accept.residuals["runway"]["target_kind"] == "revenue"
    reject = oc.accept_order(
        {"id": "sample-no", "species": "quail", "qty": 100000, "unit": "head", "week": 4},
        oc.OrderBook(),
        {"quail": state},
        {"t_weeks": 26, "H_months": 3, "R_min": 3000.0, "hurdle": 0.0},
    )
    assert reject.accept is False
    return accept, reject, plan


def check_revenue_floor_and_rank() -> dict:
    small = oc.accept_order(
        {"species": "quail", "qty": 1, "unit": "head", "week": 4},
        oc.OrderBook(),
        {"quail": _herd(40, 120)},
        {},
    )
    assert small.accept is False
    assert any("revenue floor" in reason for reason in small.reasons), small.reasons

    runway = oc.firm_monthly_contribution("quail", _herd(1000, 3000), 0.0, 3)
    assert runway["min_monthly_revenue"] > runway["min_monthly_contribution"] > 0

    worms = {"n_now": 20000, "n0": 16500}
    quail = _herd(17, 51)
    starved = oc.accept_order(
        {"species": "worms", "qty": 2000, "unit": "head", "week": 1},
        oc.OrderBook(),
        {"worms": worms, "quail": quail},
        {"R_min": 0},
    )
    assert starved.accept is False
    assert any("feed buffer" in reason or "retained" in reason for reason in starved.reasons), starved.reasons

    ranking = oc.rank_skus({"worms": {"n_now": 50000, "n0": 16500}, "quail": _herd(100, 300)})
    assert ranking["winner"] == "quail", ranking
    assert ranking["ranked"][0]["score"] > ranking["ranked"][1]["score"]
    return ranking


def _public_row(row: dict) -> dict:
    return {
        "g_per_week": row["g_per_week"],
        "allowed_heads_now": row["allowed"],
        "allowed_lb_now": row["allowed_lb"],
        "allowed_heads_at_t": row["allowed_by_t"],
        "binding": row["binding"],
        "fail_closed": row["fail_closed"],
    }


def main() -> None:
    rows = check_sellable_falls_as_growth_rises()
    surplus, nucleus = check_surplus_and_ne()
    check_reservations()
    cheap = check_roi_reject()
    accept, reject, plan = check_sample()
    ranking = check_revenue_floor_and_rank()

    print("Quail sellable heads. Horizon 26 weeks. Herd 1000 males + 3000 females. Floor 68.")
    print("g is an optional weekly helper. The operator knob is R_min, monthly revenue.")
    print("Sell-now is the lump that still leaves N*(1+g)^t when g is passed to sellable_for_growth.")
    print("Deliver-at-week-26 also stops at the pipeline and flock_today caps, so it can sit flat until growth binds.")
    print(f"{'g/week':>8} {'sell now':>12} {'deliver at week 26':>20} {'binding':>12}")
    for row in rows:
        print(
            f"{row['g_per_week']:8.2f} {row['allowed']:12.1f} {row['allowed_by_t']:20.1f} {row['binding']:>12}"
        )
    print(
        f"Sample accept: {accept.accept}  "
        f"10 heads in week 4 on a {plan['hold_heads']:.0f}-bird hold "
        f"(revenue ${plan['min_monthly_revenue']:.0f}/mo, R_min $3000)."
    )
    print(f"Sample reject: {reject.accept}  100000 heads. {reject.reasons[0]}")
    print(
        f"Rank winner: {ranking['winner']}  "
        f"score {ranking['ranked'][0]['score']:.4f} vs {ranking['ranked'][1]['species']} "
        f"{ranking['ranked'][1]['score']:.4f}"
    )
    print("Stage 4 planning only. Stage 1 worms remain the only spend.")

    payload = {
        "ok": True,
        "stage_gate": oc.STAGE_GATE,
        "objective": "monthly revenue R_min",
        "R_min": oc.DEFAULT_R_MIN,
        "H_months": oc.DEFAULT_H_MONTHS,
        "quail_week_26": [_public_row(row) for row in rows],
        "surplus_reject": surplus.reasons,
        "ne_reject": nucleus.reasons,
        "roi_reject": cheap.reasons,
        "sample_accept": accept.to_dict(),
        "sample_reject_reason": reject.reasons,
        "capacity_hold_heads": plan["hold_heads"],
        "capacity_min_monthly_revenue": plan["min_monthly_revenue"],
        "capacity_min_monthly_contribution": plan["min_monthly_contribution"],
        "capacity_g_explicit": plan["g_explicit"],
        "rank_winner": ranking["winner"],
        "rank_rows": ranking["ranked"],
        "g_unit": "fraction per week, optional helper",
    }
    # Drop the nested herd state from the accept residuals if any non-JSON sneaks in.
    out = Path(__file__).resolve().parent / "results" / "order_control_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
