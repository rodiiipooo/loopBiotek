"""Annual screening model, not a biological simulation or procurement authorization."""
import math
import json
from pathlib import Path

CATALOG = Path(__file__).with_name("equipment_catalog.json")

def catalog():
    return {p["id"]: p for p in json.loads(CATALOG.read_text())["products"]}

def evaluate(units, annual_yield, residents, demand, price, variable_cost,
             reserve=0.1, internal_feed=0, fixed_cost=0, market_limit=math.inf):
    values = (units, annual_yield, residents, demand, price, variable_cost,
              internal_feed, fixed_cost, market_limit)
    if any(math.isnan(v) or v < 0 for v in values) or not 0 <= reserve < 1:
        raise ValueError("Invalid nonnegative inputs or reserve")
    if int(units) != units:
        raise ValueError("Equipment units must be integral")
    gross = units * annual_yield
    available = gross * (1-reserve)
    required = residents*demand + internal_feed
    shortage = max(0, required-available)
    surplus = max(0, available-required)
    sold = min(surplus, market_limit)
    return dict(production=gross, shortage=shortage, surplus=surplus,
                sold=sold, revenue=sold*price,
                operating_income=sold*price-gross*variable_cost-fixed_cost)

def reverse(target, annual_yield, residents, demand, price, variable_cost,
            reserve=0.1, internal_feed=0, fixed_cost=0, market_limit=math.inf):
    if target < 0:
        raise ValueError("Target must be nonnegative")
    evaluate(0, annual_yield, residents, demand, price, variable_cost,
             reserve, internal_feed, fixed_cost, market_limit)
    margin = annual_yield*((1-reserve)*price-variable_cost)
    required = residents*demand+internal_feed
    if margin <= 0:
        return None
    units = max(0, math.ceil((target+required*price+fixed_cost)/margin))
    units = max(units, math.ceil(required/(annual_yield*(1-reserve))))
    result = evaluate(units, annual_yield, residents, demand, price,
                      variable_cost, reserve, internal_feed, fixed_cost, market_limit)
    if result["shortage"] > 1e-8 or result["operating_income"]+1e-8 < target:
        return None
    return dict(units=units, **result)

def led_kwh(area_m2, dli, efficacy):
    if min(area_m2,dli) < 0 or efficacy <= 0:
        raise ValueError("Invalid lighting parameters")
    return area_m2*dli/(3.6*efficacy)

def canopy_area(floor_m2, rack_fraction, tiers, utilization=1):
    if floor_m2 < 0 or not 0 <= rack_fraction <= 1 or not 0 <= utilization <= 1 or tiers < 1 or int(tiers)!=tiers:
        raise ValueError("Invalid geometry")
    return floor_m2*rack_fraction*tiers*utilization

def biomass_step(stock, growth, stocking, mortality, requested_harvest):
    if min(stock,growth,stocking,mortality,requested_harvest)<0:
        raise ValueError("Negative biomass flow")
    available = stock+growth+stocking
    if mortality > available:
        raise ValueError("Mortality exceeds biomass")
    harvest = min(requested_harvest, available-mortality)
    return available-mortality-harvest, harvest

def nutrient_balance(food_kg, composition, requirements, residents):
    """Composition maps food -> nutrient -> amount/kg edible; requirements annual/person.
    Missing composition is an error, never silently treated as zero."""
    if residents < 0 or any(v < 0 for v in food_kg.values()) or any(v < 0 for v in requirements.values()):
        raise ValueError("Negative nutrition input")
    return {n: sum(q*composition[f][n] for f,q in food_kg.items())-residents*r
            for n,r in requirements.items()}

if __name__ == "__main__":
    # Prior UI scenario; assumptions, not a validated business case.
    p = catalog()["greens"]
    result = reverse(30000,p["yield_base"],10,100,3.5,2.5)
    if result is not None:
        result["equipment_capex"] = result["units"]*p["price_usd"]
    print(json.dumps(result, indent=2))
