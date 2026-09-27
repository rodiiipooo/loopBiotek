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
        by_name = {case.name: case for case in opt.example_cases()}
        living = by_name["living"]
        storage = by_name["storage"]
        cold = by_name["cold_storage"]
        f_living = opt.f_max_from_caps(opt.constraint_caps(living, opt.DFW_TYPICAL))
        f_storage = opt.f_max_from_caps(opt.constraint_caps(storage, opt.DFW_TYPICAL))
        f_cold = opt.f_max_from_caps(opt.constraint_caps(cold, opt.DFW_TYPICAL))
        self.assertTrue(living.clear_ceiling)
        self.assertTrue(opt.has_sunlight_path(living))
        self.assertLess(f_living, 0.90)
        self.assertGreater(f_living, 0.5)
        self.assertAlmostEqual(f_storage, 1.0)
        self.assertAlmostEqual(f_cold, 1.0)

    def test_home_without_glazing_is_infeasible(self):
        dark = opt.SubmersionCase(
            "dark-home",
            "living",
            clear_ceiling=False,
            wall_glazing_frac=0.0,
        )
        caps = opt.constraint_caps(dark, opt.DFW_TYPICAL)
        self.assertLess(caps["sunlight"], 0.0)
        self.assertLess(opt.f_max_from_caps(caps), 0.0)

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
        greenhouse = next(case for case in opt.example_cases() if case.name == "greenhouse")
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
        storage = next(case for case in opt.example_cases() if case.name == "storage")
        months = (opt.DFW_MONTHS[0], opt.DFW_MONTHS[6])
        enclosed = opt.annual_energy(storage, 0.4, opt.DFW_TYPICAL, hours=48.0, months=months)
        opened = opt.SubmersionCase(
            "open",
            "storage",
            above_grade_enclosure=False,
        )
        open_energy = opt.annual_energy(opened, 0.4, opt.DFW_TYPICAL, hours=48.0, months=months)
        self.assertGreater(open_energy[0], enclosed[0] * 2.0)


class SweepTest(unittest.TestCase):
    def test_living_keeps_sun_and_stores_go_to_full_burial(self):
        results = opt.run_examples(f_step=0.25, hours=48.0)
        by_name = {result.case.name: result for result in results}
        living = by_name["living"]
        storage = by_name["storage"]
        cold = by_name["cold_storage"]
        self.assertIsNotNone(living.f_star)
        self.assertIsNotNone(storage.f_star)
        self.assertIsNotNone(cold.f_star)
        self.assertLess(living.f_star, 0.90)
        self.assertGreaterEqual(storage.f_star, 0.95)
        self.assertGreaterEqual(cold.f_star, 0.95)
        self.assertLess(living.f_star, storage.f_star)
        self.assertTrue(opt.has_sunlight_path(living.case))
        for result in (living, storage, cold):
            at_zero = next(point for point in result.curve if point.f == 0.0)
            at_star = next(point for point in result.curve if abs(point.f - result.f_star) < 1e-6)
            self.assertLessEqual(at_star.E_kWh, at_zero.E_kWh + 1e-6)
            self.assertLessEqual(result.f_star, result.f_max + 1e-6)
            self.assertLess(max(point.closure_K for point in result.curve), 0.5)


class CommunityEnergyTest(unittest.TestCase):
    def test_headcounts_match_existing_stubs(self):
        import community_energy as energy

        pop = energy.default_population()
        self.assertEqual(pop.H, 20.0)
        self.assertEqual(pop.W_kg, 70.0)
        self.assertEqual(pop.worms, 16500.0)
        self.assertEqual(pop.quail, 20.0)
        self.assertAlmostEqual(pop.m2_per_person, 12.0)

    def test_gallons_split_and_scale_with_people(self):
        import community_energy as energy

        pop = energy.default_population()
        streams = energy.water_streams(pop)
        maint = sum(row.gallons_per_day for row in streams if row.role == "maintenance")
        disc = sum(row.gallons_per_day for row in streams if row.role == "discretionary")
        self.assertAlmostEqual(maint, 20.0 * 10.0 + 20.0 * 0.02, places=3)
        self.assertAlmostEqual(disc, 20.0 * 5.0, places=3)
        hotter = energy._stream("hot", "maintenance", 10.0, 60.0, 18.0, 4.0)
        cooler = energy._stream("cool", "maintenance", 10.0, 40.0, 18.0, 4.0)
        self.assertGreater(hotter.kwh_per_day, cooler.kwh_per_day)
        doubled = energy.Population(
            H=40.0, W_kg=70.0, worms=0.0, quail=0.0, m2_per_person=12.0, sources={}
        )
        base_people = sum(row.gallons_per_day for row in streams if row.name.startswith("people"))
        more = sum(
            row.gallons_per_day
            for row in energy.water_streams(doubled)
            if row.name.startswith("people")
        )
        self.assertAlmostEqual(more, 2.0 * base_people)

    def test_microgrid_capex_is_positive_and_labeled(self):
        import community_energy as energy

        pop = energy.default_population()
        streams = energy.water_streams(pop)
        spaces = [
            energy.SpaceLoad("storage", "storage", 1.0, 100.0, "", 1000.0, 0.0, 0.5),
            energy.SpaceLoad("cold_storage", "cold_storage", 1.0, 100.0, "", 8000.0, 0.0, 1.5),
        ]
        grid = energy.size_microgrid(streams, spaces)
        self.assertGreater(grid.capex_usd, 0.0)
        self.assertGreater(grid.pv_kw, 0.0)
        self.assertGreater(grid.battery_kwh, 0.0)
        self.assertGreater(grid.annual_maintenance_kwh, grid.annual_discretionary_kwh)
        self.assertIn("cold storage", " ".join(grid.serves))


if __name__ == "__main__":
    unittest.main()
