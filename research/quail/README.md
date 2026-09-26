# Quail research (Stage 4 planning)

Screening math for jumbo *Coturnix japonica* meat on one [Grit Quail Professional Kit](https://store.grit.com/products/quail-professional-kit?variant=47213766246652). Read [`SPEC.md`](SPEC.md) for the formulas and [`SOURCES.md`](SOURCES.md) for what is sourced versus assumed.

Stage 1 worms are still the spend source of record (`biology/CASCADE.md`). This package does not open quail spend.

## Run the worked example

From the repository root:

```bash
python -m research.quail
```

That writes `research/quail/results/sample_run.txt` and `sample_run.json` and prints:

- `y=5` males, `z=15` females, `U=1` kit, `c_bar=2` lb/week
- `t_ready` = 77 days (week 11)
- `r_prod` = 28.875 lb/week (≈ 28.9)
- `E[P_comp]` = 12.4633 USD/lb
- prime 7% as of 2026-09-24, `T=0.5` year
- `F0` ≈ 12.0488 USD/lb

## Tests

```bash
python -m unittest research.quail.test_quail_model
```

## API

| Function | Returns |
|----------|---------|
| `production_rate(t, y, z, U)` | Dressed lb/week at day `t` |
| `production_rate_required(c_bar)` | lb/week required to cover average consumption |
| `t_ready(c_bar, y, z, U)` | First day the steady rate covers `c_bar`, or `None` |
| `sustain_inventory_lb(c_bar, t, y, z, U)` | Freezer pounds required at day `t` |
| `can_sustain(c_bar, t, y, z, U)` | Whether day `t` can carry `c_bar` |
| `kits_needed(c_bar, y, z)` | Whole kits so the steady rate covers `c_bar` |
| `population(t, y, z, U)` | Standing birds and the weekly meat-bird count |
| `fair_forward_price_per_lb()` | `E[P_comp]` USD/lb |
| `fair_prepaid_contract(r_prime, T)` | `F0 = E[P] / (1+r_prime)^T` |

Import path: `research.quail`.
