import unittest
from vertical_export import *

class TestPlanning(unittest.TestCase):
    def test_reverse(self):
        r=reverse(30000,8000,10,100,3.5,2.5)
        self.assertEqual(r["units"],7)
        self.assertGreaterEqual(r["operating_income"],30000)
    def test_market(self):
        self.assertIsNone(reverse(30000,8000,10,100,3.5,2.5,market_limit=100))
    def test_shortage(self):
        self.assertEqual(evaluate(0,100,10,10,3,1)["shortage"],100)
    def test_mass(self):
        self.assertEqual(biomass_step(10,2,0,1,100),(0,11))
    def test_light(self):
        self.assertAlmostEqual(led_kwh(1,20,2.8),20/10.08)
    def test_nutrients(self):
        self.assertEqual(nutrient_balance({"food":2},{"food":{"protein":10}},{"protein":30},1),{"protein":-10})

if __name__=="__main__":
    unittest.main()
