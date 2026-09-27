"""Checks for the submersion optimizer and the untouched legacy summer balance."""
from __future__ import annotations

import tempfile
import unittest

import climate_envelope_sim as env
import submersion_opt as opt


class LegacyBalanceTest(unittest.TestCase):
    def test_summer_illustration_unchanged(self):
        room, pipe, clim = env.RoomParams(), env.PipeGeometry(), env.ClimateParams()
        sim = env.simulate(room, pipe, clim)
        self.assertAlmostEqual(float(sim["T_room"].max()), 31.827772187740887, places=5)
        self.assertAlmostEqual(float(sim["UA_reject"][0]), 3714.7284278170328, places=4)
        self.assertAlmostEqual(env.hvac_proxy_kwh(sim), 5.5565465665796285, places=5)
        self.assertAlmostEqual(room.submersion, 0.70)


class SoilAndLightTest(unittest.TestCase):
    def test_horizontal_tilt_factor_is_one(self):
        self.assertAlmostEqual(opt.effective_tilt_factor(0.0, 0.0, 80, 32.9), 1.0, places=6)

    def test_deeper_soil_is_closer_to_the_annual_mean(self):
        _, _, damping = opt.soil_properties(0.5)
        climate = opt.DFW_TYPICAL
        shallow = opt.T_soil_C(0.2, 196, climate, damping)
        deep = opt.T_soil_C(3.0, 196, climate, damping)
        self.assertGreater(abs(shallow - climate.T_mean_soil_C), abs(deep - climate.T_mean_soil_C))
        self.assertGreater(shallow, deep)

    def test_moisture_raises_conductivity(self):
        k_dry, _, _ = opt.soil_properties(0.0)
        k_wet, _, _ = opt.soil_properties(1.0)
        self.assertAlmostEqual(k_dry, opt.K_DRY)
        self.assertAlmostEqual(k_wet, opt.K_SAT)
        self.assertGreater(k_wet, k_dry)

    def test_tube_throttle_derates_the_legacy_ua(self):
        room = env.RoomParams(submersion=0.7)
        pipe = env.PipeGeometry()
        base = env.ua_ground_reject(room, pipe, 100.0)
        ua = opt.throttled_tube_UA(room, pipe, 100.0, k_soil=opt.K_SOIL_REF, f=0.7)
        self.assertAlmostEqual(ua, base / (1.0 + opt.TUBE_THROTTLE_GAMMA * 0.7))
        self.assertLess(ua, base)


class ConstraintTest(unittest.TestCase):
    def test_caps_differ_by_use(self):
        living, storage, greenhouse = opt.example_cases()
        f_living = opt.f_max_from_caps(opt.constraint_caps(living, opt.DFW_TYPICAL))
        f_storage = opt.f_max_from_caps(opt.constraint_caps(storage, opt.DFW_TYPICAL))
        f_greenhouse = opt.f_max_from_caps(opt.constraint_caps(greenhouse, opt.DFW_TYPICAL))
        self.assertLess(f_living, f_greenhouse)
        self.assertLess(f_greenhouse, f_storage)
        self.assertAlmostEqual(f_storage, 1.0)
        self.assertGreater(f_living, 0.5)
        self.assertLess(f_living, 0.70)

    def test_opaque_greenhouse_cannot_meet_daylight(self):
        case = opt.SubmersionCase("dark-greenhouse", "greenhouse", clear_ceiling=False)
        caps = opt.constraint_caps(case, opt.DFW_TYPICAL)
        self.assertLess(caps["daylight"], 0.0)
        self.assertLess(opt.f_max_from_caps(caps), 0.0)

    def test_climate_csv_roundtrip(self):
        month = opt.DFW_MONTHS[0]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as handle:
            handle.write("name,doy,days,T_min_C,T_max_C,ghi_kwh_m2,day_length_h\n")
            handle.write(
                f"{month.name},{month.doy},{month.days},{month.T_min_C},"
                f"{month.T_max_C},{month.ghi_kwh_m2},{month.day_length_h}\n"
            )
            path = handle.name
        loaded = opt.read_month_csv(path)
        self.assertEqual(loaded[0], month)


class SwitchTest(unittest.TestCase):
    def test_water_panes_enable_ground_reject(self):
        greenhouse = opt.example_cases()[2]
        month = opt.DFW_MONTHS[6]
        _, _, wet, _ = opt.build_envelope(greenhouse, 0.85, month, opt.DFW_TYPICAL, 48.0, 60.0)
        dry_case = opt.SubmersionCase(
            "dry",
            "greenhouse",
            clear_ceiling=True,
            water_panes=False,
        )
        _, _, dry, _ = opt.build_envelope(dry_case, 0.85, month, opt.DFW_TYPICAL, 48.0, 60.0)
        self.assertGreater(wet.UA_reject, 1000.0)
        self.assertEqual(dry.UA_reject, 0.0)

    def test_open_stickup_costs_more_than_an_enclosed_wall(self):
        living = opt.example_cases()[0]
        months = (opt.DFW_MONTHS[0], opt.DFW_MONTHS[6])
        enclosed = opt.annual_energy(living, 0.4, opt.DFW_TYPICAL, hours=48.0, months=months)
        opened = opt.SubmersionCase(
            "open",
            "living",
            above_grade_enclosure=False,
        )
        open_energy = opt.annual_energy(opened, 0.4, opt.DFW_TYPICAL, hours=48.0, months=months)
        self.assertGreater(open_energy[0], enclosed[0] * 2.0)


class SweepTest(unittest.TestCase):
    def test_living_storage_and_greenhouse_recommend_different_f(self):
        results = opt.run_examples(f_step=0.25, hours=48.0)
        by_name = {result.case.name: result for result in results}
        living, storage, greenhouse = by_name["living"], by_name["storage"], by_name["greenhouse"]
        self.assertIsNotNone(living.f_star)
        self.assertIsNotNone(storage.f_star)
        self.assertIsNotNone(greenhouse.f_star)
        self.assertLess(living.f_star, greenhouse.f_star)
        self.assertLess(greenhouse.f_star, storage.f_star)
        self.assertNotAlmostEqual(living.f_star, 0.70, places=2)
        for result in results:
            at_zero = next(point for point in result.curve if point.f == 0.0)
            at_star = next(point for point in result.curve if abs(point.f - result.f_star) < 1e-6)
            self.assertLessEqual(at_star.E_kWh, at_zero.E_kWh + 1e-6)
            self.assertLessEqual(result.f_star, result.f_max + 1e-6)
            self.assertLess(max(point.closure_K for point in result.curve), 0.5)


if __name__ == "__main__":
    unittest.main()
