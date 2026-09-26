"""Numerical contract for the Stage-4 jumbo Coturnix screening model."""

import math
import unittest

from research.quail.quail_model import (
    BREEDER_CAP,
    BROODER_CAP,
    DRESSED_LB,
    GROWOUT_CAP_JUMBO,
    INCUBATOR_EGGS_PER_BATCH,
    KIT_PRICE_USD,
    PIPELINE_DAYS,
    PRIME_RATE,
    can_sustain,
    fair_forward_price_per_lb,
    fair_prepaid_contract,
    kits_needed,
    population,
    production_rate,
    production_rate_required,
    sustain_inventory_lb,
    t_ready,
)


class SampleScenarioTest(unittest.TestCase):
    def test_pipeline_ready_day_is_eleven_weeks(self):
        self.assertEqual(PIPELINE_DAYS, 77)
        self.assertEqual(t_ready(2.0, y=5, z=15, U=1), 77)

    def test_ready_week_production_rate(self):
        self.assertEqual(production_rate(76, y=5, z=15, U=1), 0.0)
        rate = production_rate(77, y=5, z=15, U=1)
        # 37.5 birds/week * 0.77 lb ≈ 28.9 lb/week
        self.assertAlmostEqual(rate, 28.9, delta=0.05)
        self.assertAlmostEqual(rate, 37.5 * DRESSED_LB, places=6)

    def test_consumption_is_covered_at_ready_and_not_before(self):
        self.assertFalse(can_sustain(2.0, 76, y=5, z=15, U=1))
        self.assertTrue(can_sustain(2.0, 77, y=5, z=15, U=1))
        self.assertEqual(sustain_inventory_lb(2.0, 77, y=5, z=15, U=1), 0.0)
        # 7 days short of the pipeline: one week of consumption must be on hand.
        self.assertAlmostEqual(
            sustain_inventory_lb(2.0, 70, y=5, z=15, U=1), 2.0, places=6
        )

    def test_kits_and_required_rate(self):
        self.assertEqual(kits_needed(2.0, y=5, z=15), 1)
        self.assertEqual(production_rate_required(2.0), 2.0)
        per_kit = production_rate(77, y=5, z=15, U=1)
        self.assertEqual(kits_needed(per_kit + 0.1, y=5, z=15), 2)

    def test_prepaid_matches_prime_discount(self):
        expected = fair_forward_price_per_lb()
        self.assertAlmostEqual(expected, 12.4633, places=4)
        prepaid = fair_prepaid_contract(expected_price=expected, r_prime=0.07, T=0.5)
        self.assertAlmostEqual(prepaid, expected / math.sqrt(1.07), places=6)
        self.assertAlmostEqual(prepaid, 12.0488, delta=0.00015)
        self.assertEqual(PRIME_RATE, 0.07)

    def test_kit_capacities_and_price(self):
        self.assertEqual(INCUBATOR_EGGS_PER_BATCH, 216)
        self.assertEqual(BROODER_CAP, 150)
        self.assertEqual(GROWOUT_CAP_JUMBO, 75)
        self.assertEqual(BREEDER_CAP, 45)
        self.assertAlmostEqual(KIT_PRICE_USD, 3449.99, places=2)

    def test_population_at_ready_is_inside_kit_caps(self):
        pop = population(77, y=5, z=15, U=1)
        self.assertLessEqual(pop["brooder"], BROODER_CAP)
        self.assertLessEqual(pop["grow_out"], GROWOUT_CAP_JUMBO)
        self.assertLessEqual(pop["breeders"], BREEDER_CAP)
        self.assertEqual(pop["founder_males"], 5)
        self.assertEqual(pop["founder_females"], 15)
        self.assertGreater(pop["meat_birds_per_week"], 0)


if __name__ == "__main__":
    unittest.main()
