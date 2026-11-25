# Vertical equipment and export screening (planning only)

Claim: planning/equipment_catalog.json, vertical_export.py, test_vertical_export.py and this README. No live cascade gates, site geometry or economic source-of-record workbook changed. Stage 1 remains the only active spend.

Run from repository root:
```sh
python planning/vertical_export.py
python -m unittest discover -s planning -p 'test_vertical_export.py'
```

Catalog prices are provisional snapshots from the preceding research review, not fresh quotes. Null means unknown, not zero. Equipment footprint excludes access and shared facilities. Yield scenarios are not probability quantiles. Fodder and waste rows are not exportable human food. Do not sum alternative quail egg and meat maxima. Use USDA FoodData Central (https://fdc.nal.usda.gov/) for edible nutrient composition. No complete diet is asserted.

The annual screening model subtracts resident demand, feed and reserve before export, caps sales by market demand, and charges variable cost on all production. Costs exclude debt and taxes; include all relevant operating costs in inputs. Example uses 10 residents, $2500/month target, $3.50/lb sale, $2.50/lb cost, 10% buffer and 100 lb/person/year greens. It requires seven Greenery S units ($1.505M equipment only) under these assumptions, not a purchase recommendation.

Next: replace notebook fixed fish harvest with cohort mass conservation; reconcile insect counts and dry mass; enforce seed reserve and eligible feed; add age-specific quail egg allocation, actual crop light/yield calibration, complete nutrient requirements and upper bounds, hourly HVAC/water/power, supplier quotes and market offtake. Integrate with reference/loop_params.xlsx only after validation. Keep historical notebook intact until regression tests exist. Use joint stochastic scenarios for P10 firm surplus, not low/base/high labels as quantiles. Vertical-only crop candidates include compact tubers, legumes and oil crops; no broad-acre crop assumptions.
