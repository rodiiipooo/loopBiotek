"""Proofs for proportional capital payback and H,W setup CapEx.

Planning math only. Numbers in these tests are fixtures, not commercial results.
"""

from __future__ import annotations

import unittest

from community_capital import (
    FacilityParams,
    FoodStockParams,
    Member,
    PoolEvent,
    equal_contributor_amount,
    facility_capex,
    food_stock_capex,
    ownership_shares,
    payback_schedule,
    pool_coverage,
    run_example,
    setup_capex,
)


class OwnershipTests(unittest.TestCase):
    def test_equal_shares(self):
        result = ownership_shares([Member("a", 20), Member("b", 20), Member("c", 20)])
        self.assertFalse(result.pool_empty)
        self.assertAlmostEqual(result.pool, 60.0)
        for share in result.shares.values():
            self.assertAlmostEqual(share, 1.0 / 3.0)

    def test_proportional_shares(self):
        result = ownership_shares(
            [
                Member("big", 50),
                Member("s1", 12.5),
                Member("s2", 12.5),
                Member("s3", 12.5),
                Member("s4", 12.5),
            ]
        )
        self.assertAlmostEqual(result.pool, 100.0)
        self.assertAlmostEqual(result.shares["big"], 0.5)
        self.assertAlmostEqual(result.shares["s1"], 0.125)

    def test_zero_pool_is_explicit(self):
        result = ownership_shares([Member("a", 0), Member("b", 0)])
        self.assertTrue(result.pool_empty)
        self.assertEqual(result.pool, 0.0)
        self.assertEqual(result.shares, {})

    def test_empty_membership_is_explicit(self):
        result = ownership_shares([])
        self.assertTrue(result.pool_empty)
        self.assertEqual(result.shares, {})

    def test_negative_contribution_rejected(self):
        with self.assertRaises(ValueError):
            ownership_shares([Member("a", -1)])


class PaybackTests(unittest.TestCase):
    def test_equal_contributions_have_equal_streams_and_same_clearing_period(self):
        members = [Member(f"m{i}", 100.0) for i in range(5)]
        surplus = [50.0] * 10 + [50.0]
        schedule = payback_schedule(members, surplus)
        self.assertEqual(schedule.cleared_at_period, 9)
        for row in schedule.rows[:10]:
            self.assertEqual(row.phase, "capital_recovery")
            self.assertAlmostEqual(row.unallocated, 0.0)
            pays = list(row.capital_payments.values())
            self.assertTrue(all(abs(p - 10.0) < 1e-9 for p in pays))
        # Same recovery per dollar invested.
        row0 = schedule.rows[0]
        for member in members:
            per_dollar = row0.capital_payments[member.member_id] / member.contribution
            self.assertAlmostEqual(per_dollar, 50.0 / 500.0)
        # After principal is gone, capital claims stop. Equal residents share the next surplus.
        done = schedule.rows[10]
        self.assertEqual(done.phase, "post_payback")
        self.assertTrue(all(v == 0.0 for v in done.capital_payments.values()))
        self.assertTrue(all(abs(v - 10.0) < 1e-9 for v in done.post_payback_payments.values()))

    def test_larger_investor_recovers_more_dollars_at_the_same_rate(self):
        members = [
            Member("big", 400.0),
            Member("a", 100.0),
            Member("b", 100.0),
            Member("c", 100.0),
            Member("d", 100.0),
        ]
        schedule = payback_schedule(members, [80.0] * 10)
        self.assertEqual(schedule.cleared_at_period, 9)
        first = schedule.rows[0]
        self.assertAlmostEqual(first.capital_payments["big"], 40.0)
        self.assertAlmostEqual(first.capital_payments["a"], 10.0)
        self.assertAlmostEqual(first.capital_payments["big"] / 400.0, first.capital_payments["a"] / 100.0)
        self.assertAlmostEqual(schedule.rows[-1].cumulative["big"], 400.0)
        self.assertAlmostEqual(schedule.rows[-1].cumulative["a"], 100.0)

    def test_capital_stops_at_principal_and_leftover_is_not_a_capital_claim(self):
        members = [Member("big", 300.0), Member("small", 100.0)]
        schedule = payback_schedule(members, [1000.0])
        row = schedule.rows[0]
        self.assertEqual(row.phase, "capital_recovery")
        self.assertAlmostEqual(row.capital_payments["big"], 300.0)
        self.assertAlmostEqual(row.capital_payments["small"], 100.0)
        # ASSUMPTION: once every principal is cleared, leftover R is equal per active member.
        self.assertAlmostEqual(row.post_payback_payments["big"], 300.0)
        self.assertAlmostEqual(row.post_payback_payments["small"], 300.0)
        self.assertAlmostEqual(row.unallocated, 0.0)
        self.assertTrue(schedule.fully_repaid)

    def test_zero_surplus_stretches_without_changing_balances(self):
        schedule = payback_schedule([Member("a", 100.0), Member("b", 100.0)], [0.0, 0.0, 0.0])
        self.assertFalse(schedule.fully_repaid)
        self.assertIsNone(schedule.cleared_at_period)
        for row in schedule.rows:
            self.assertAlmostEqual(row.remaining["a"], 100.0)
            self.assertAlmostEqual(row.cumulative["a"], 0.0)
            self.assertEqual(row.phase, "capital_recovery")

    def test_zero_pool_has_no_capital_phase(self):
        schedule = payback_schedule([Member("a", 0.0), Member("b", 0.0)], [40.0])
        self.assertTrue(schedule.pool_empty)
        row = schedule.rows[0]
        self.assertEqual(row.phase, "post_payback")
        self.assertAlmostEqual(row.post_payback_payments["a"], 20.0)
        self.assertAlmostEqual(row.post_payback_payments["b"], 20.0)

    def test_negative_surplus_rejected(self):
        with self.assertRaises(ValueError):
            payback_schedule([Member("a", 10.0)], [-1.0])

    def test_default_interest_is_zero_and_optional_rate_increases_obligation(self):
        principal_only = payback_schedule([Member("a", 100.0)], [100.0])
        self.assertAlmostEqual(principal_only.rows[0].capital_payments["a"], 100.0)
        self.assertTrue(principal_only.fully_repaid)

        # ASSUMPTION: simple interest on outstanding principal, interest paid before principal.
        with_interest = payback_schedule([Member("a", 100.0)], [50.0, 50.0, 50.0], interest_rate_per_period=0.1)
        self.assertAlmostEqual(with_interest.interest_rate_per_period, 0.1)
        self.assertGreater(with_interest.rows[0].obligation["a"], 100.0)
        self.assertFalse(with_interest.rows[0].fully_repaid_after)
        self.assertAlmostEqual(with_interest.rows[0].capital_payments["a"], 50.0)
        # Period 0: +10 interest, pay 50 → principal 60. Period 1: +6 interest, pay 50 → principal 16.
        self.assertAlmostEqual(with_interest.rows[1].remaining_principal["a"], 16.0)
        self.assertTrue(with_interest.fully_repaid)
        self.assertGreater(with_interest.rows[-1].cumulative["a"], 100.0)

    def test_labor_shares_apply_only_after_payback(self):
        members = [
            Member("a", 100.0, labor_share=1.0),
            Member("b", 100.0, labor_share=3.0),
        ]
        schedule = payback_schedule(members, [200.0, 40.0], post_payback="labor_shares")
        self.assertAlmostEqual(schedule.rows[0].capital_payments["a"], 100.0)
        self.assertAlmostEqual(schedule.rows[0].post_payback_payments["a"], 0.0)
        self.assertAlmostEqual(schedule.rows[1].post_payback_payments["a"], 10.0)
        self.assertAlmostEqual(schedule.rows[1].post_payback_payments["b"], 30.0)
        self.assertAlmostEqual(schedule.rows[1].capital_payments["a"], 0.0)

    def test_late_joiner_does_not_dilute_locked_shares(self):
        schedule = payback_schedule(
            [Member("early", 100.0)],
            [40.0, 40.0, 40.0, 40.0, 40.0],
            events=[PoolEvent(2, "late_join", Member("late", 100.0))],
        )
        # Periods 0 and 1: early still owns the whole locked pool.
        self.assertAlmostEqual(schedule.rows[0].capital_payments["early"], 40.0)
        self.assertAlmostEqual(schedule.rows[1].cumulative["early"], 80.0)
        self.assertNotIn("late", schedule.rows[1].capital_payments)
        # Period 2 clears the senior remainder (20) and only then pays the junior tranche.
        self.assertAlmostEqual(schedule.rows[2].capital_payments["early"], 20.0)
        self.assertAlmostEqual(schedule.rows[2].capital_payments["late"], 20.0)
        self.assertAlmostEqual(schedule.shares_by_tranche[0]["early"], 1.0)
        self.assertAlmostEqual(schedule.shares_by_tranche[1]["late"], 1.0)

    def test_forfeit_does_not_raise_the_other_share(self):
        schedule = payback_schedule(
            [Member("stay", 100.0), Member("leave", 100.0)],
            [100.0],
            events=[PoolEvent(0, "forfeit", member_id="leave")],
        )
        row = schedule.rows[0]
        self.assertAlmostEqual(row.capital_payments["stay"], 50.0)
        self.assertAlmostEqual(row.capital_payments["leave"], 0.0)
        self.assertAlmostEqual(row.remaining_principal["stay"], 50.0)
        # Freed share is not given to the remaining capital claim while it is still unpaid.
        self.assertAlmostEqual(row.unallocated, 50.0)
        self.assertAlmostEqual(row.post_payback_payments["stay"], 0.0)

    def test_exit_keeps_unpaid_claim_and_drops_post_payback(self):
        schedule = payback_schedule(
            [Member("stay", 100.0), Member("leave", 100.0)],
            [200.0, 40.0],
            events=[PoolEvent(0, "exit", member_id="leave")],
        )
        self.assertAlmostEqual(schedule.rows[0].capital_payments["leave"], 100.0)
        self.assertAlmostEqual(schedule.rows[1].post_payback_payments["stay"], 40.0)
        self.assertAlmostEqual(schedule.rows[1].post_payback_payments["leave"], 0.0)


class CapexTests(unittest.TestCase):
    def test_food_stock_scales_with_headcount_and_weight(self):
        food = FoodStockParams(
            food_days=90.0,
            kcal_per_kg_body_per_day=30.0,
            kcal_per_kg_food=3600.0,
            usd_per_kg_food=2.5,
        )
        one = food_stock_capex(20, 70, food)
        self.assertAlmostEqual(one, 2625.0)
        self.assertAlmostEqual(food_stock_capex(40, 70, food), 2 * one)
        self.assertAlmostEqual(food_stock_capex(20, 140, food), 2 * one)

    def test_facility_optional_weight_elasticity(self):
        flat = FacilityParams(usd_per_m2=800.0, m2_per_person=12.0, area_weight_elasticity=0.0)
        self.assertAlmostEqual(facility_capex(20, 70, flat), 192_000.0)
        self.assertAlmostEqual(facility_capex(20, 140, flat), 192_000.0)
        linear = FacilityParams(usd_per_m2=800.0, m2_per_person=12.0, ref_weight_kg=70.0, area_weight_elasticity=1.0)
        self.assertAlmostEqual(facility_capex(20, 140, linear), 384_000.0)

    def test_kg_scaled_food_basis(self):
        food = FoodStockParams(
            basis="kg_scaled",
            food_days=10.0,
            usd_per_kg_food=4.0,
            kg_per_person_per_day_at_ref=0.5,
            ref_weight_kg=70.0,
        )
        self.assertAlmostEqual(food_stock_capex(2, 140, food), 80.0)

    def test_setup_is_food_plus_facility_plus_hook_and_default_hook_is_zero(self):
        food = FoodStockParams(food_days=10, kcal_per_kg_body_per_day=30, kcal_per_kg_food=3000, usd_per_kg_food=1)
        facility = FacilityParams(usd_per_m2=100, m2_per_person=2, area_weight_elasticity=0)
        bare = setup_capex(H=4, W=50, food=food, facility=facility)
        self.assertEqual(bare.other_capex, 0.0)
        self.assertAlmostEqual(bare.setup_capex, bare.food_stock_capex + bare.facility_capex)
        hooked = setup_capex(H=4, W=50, food=food, facility=facility, other_capex=15)
        self.assertAlmostEqual(hooked.setup_capex, bare.setup_capex + 15.0)
        self.assertIn("ASSUMPTION", hooked.assumption_note)

    def test_coverage_and_equal_split(self):
        short = pool_coverage([100, 200], x_min=1000)
        self.assertFalse(short.covers)
        self.assertAlmostEqual(short.shortfall, 700.0)
        self.assertAlmostEqual(short.coverage_ratio, 0.3)
        exact = pool_coverage([250, 250], x_min=500)
        self.assertTrue(exact.covers)
        self.assertAlmostEqual(exact.shortfall, 0.0)
        self.assertAlmostEqual(equal_contributor_amount(1000, 5), 200.0)
        with self.assertRaises(ValueError):
            equal_contributor_amount(1000, 0)

    def test_invalid_body_and_headcount_rejected(self):
        with self.assertRaises(ValueError):
            food_stock_capex(-1, 70, FoodStockParams())
        with self.assertRaises(ValueError):
            facility_capex(10, 0, FacilityParams())


class ExampleTests(unittest.TestCase):
    def test_run_example_prints_three_scenarios(self):
        import contextlib
        from io import StringIO

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            run_example()
        text = buf.getvalue()
        self.assertIn("SCENARIO 1", text)
        self.assertIn("SCENARIO 2", text)
        self.assertIn("SCENARIO 3", text)
        self.assertIn("ASSUMPTION", text)
        self.assertIn("Stage 1", text)
        self.assertIn("shortfall", text)


if __name__ == "__main__":
    unittest.main()
