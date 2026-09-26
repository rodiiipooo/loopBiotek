# Jumbo Coturnix quail — production-rate & fair-forward SPEC

**Stage gate:** Quail is **Stage 4** in the Loop Biotek bio cascade. **Stage 1 (worms) remains source of record** for live ops spend. This package is **planning math only**.

Canonical tree (repo): `research/quail/` in [rodiiipooo/loopBiotek](https://github.com/rodiiipooo/loopBiotek).  
Scratch sibling of worm model: `/workspace/quail-revenue-model/`.

Product: **jumbo Coturnix japonica** meat (not standard small Coturnix unless labeled).  
Capacity unit: **Grit Quail Professional Kit** — decision variable \(U\).

---

## Primary question

Given average buyer/community consumption \(\bar{c}\) (lb/week) of product \(p\) = dressed jumbo quail meat, starting breeders \(y\) males / \(z\) females, and \(U\) kits:

1. What production rate \(r_{\mathrm{prod}}(t; y,z,U)\) is achievable at/after \(t\)?
2. Is \(r_{\mathrm{prod}}(t) \ge \bar{c}\) (steady supply)?
3. What is \(t_{\mathrm{ready}}(\bar{c}, y, z, U)\) — earliest time the rate sustains \(\bar{c}\)?

**Sustain rule (inventory buffer):** batch harvest is OK. With weekly draw \(\bar{c}\), inventory \(I_{w+1}=I_w+\mathrm{harvest}_w-\bar{c}\) must stay \(\ge 0\) for `hold_weeks`, and the window-mean \(r_{\mathrm{prod}}\ge\bar{c}\).
4. What ramp path (weekly rates) gets you there?

### Functions

| Function | Role |
|----------|------|
| `production_rate(t, y, z, U, ...)` | \(r_{\mathrm{prod}}\) ≈ mean weekly dressed lbs over a window after \(t\) |
| `can_sustain(c_bar, t, y, z, U, ...)` | whether rate meets \(\bar{c}\) for `hold_weeks` |
| `t_ready(c_bar, y, z, U, ...)` | earliest day/week rate sustains \(\bar{c}\) + ramp path |
| `rate_ramp_table(y, z, U, weeks)` | full ramp |
| `meat_lbs(t, y, z, U)` | cumulative dressed lbs (helper) |
| `kits_needed(X, t, y, z)` | min \(U\) for cumulative demand \(X\) (helper) |
| `P_meat(t)`, `fair_prepaid_forward_per_lb(T)` | competing forward + prime-discounted prepaid |

---

## Biology (jumbo defaults)

See `RESEARCH.md` for citations. Tags: **SOURCED** vs **ASSUMPTION**.

| Param | Default | Tag |
|-------|---------|-----|
| Eggs/hen/year | 280 | SOURCED range 200–300 |
| Hatch rate | 0.75 | ASSUMPTION (lit. ~0.625–0.925) |
| Sex ratio ♀ | 0.50 | ASSUMPTION |
| Incubation | 17.5 d | SOURCED 17–18 |
| Maturity | 49 d | ASSUMPTION mid 6–8 wk |
| Slaughter (jumbo) | 63 d | ASSUMPTION mid 8–10 wk meat window |
| Live weight | 13 oz | ASSUMPTION mid 12–14 oz |
| Dress yield | 0.72 | ASSUMPTION mid 70–75% |
| Dress weight | ~0.585 lb | DERIVED |
| Weekly mortality | 0.01 | ASSUMPTION |
| Breeder ratio | 1♂:3♀ | ASSUMPTION |

---

## Kit capacity \(U\) (Grit Quail Professional Kit)

Product: https://store.grit.com/products/quail-professional-kit?variant=47213766246652  
SKU `QUAIL-PROKIT`, sale **$3,449.99** (list $3,729.96) — **SOURCED** page fetch 2026-09-26.

| Component | Capacity | Tag |
|-----------|----------|-----|
| CT120SH incubator | 216 quail eggs/batch | SOURCED kit page |
| CB25-03-5K brooder 5-layer | 150 quail | SOURCED Hatching Time same SKU |
| GL25-03-5K grow-out 5-layer | 75 jumbo (derated) | **ASSUMPTION** (vendor: “depends on breed”) |
| BYK-03-5K breeding cage | 75 standard; **45 jumbo** (3/section × 15) | SOURCED HT/Grit capacity notes |
| Breeding cage footprint | 38.6 × 24 × 77.2 in | SOURCED |

Simulator **throttles egg set** when incubator, brooder, or grow-out caps bind; excess breeders above cage cap are culled to meat.

Weekly incubator set approx: \(U \times 216 \times 7/17.5\).

---

## Economics — deposit ≈ loan

Competing spot \(E[P_{\mathrm{comp}}]\) = mean of foodservice whole-bird $/lb comps (Webstaurant Manchester Farms regular/plus, Manchester case) — see RESEARCH. Specialty retail (D’Artagnan) listed but **excluded** from default mean.

Flat forward (ASSUMPTION \(\mu=0\)):

\[
P_{\mathrm{meat}}(T) = E[P_{\mathrm{comp}}]\, e^{\mu T}
\]

Buyer prepay at \(t=0\) is a loan to Loop until delivery \(T\). Fair prepaid:

\[
F_0 = \frac{E[P_{\mathrm{comp}}(T)]}{(1 + r_{\mathrm{prime}})^T}
\]

(or continuous \(F_0 = E[P_{\mathrm{comp}}(T)]\, e^{-r T}\)).

**Prime rate used:** \(r_{\mathrm{prime}} = 7.00\%\) — Fed H.15 bank prime loan, observation **2026-09-24**, release 2026-09-25. https://www.federalreserve.gov/releases/h15/

Cash flows: deposit \(F_0\) per lb at 0; deliver 1 lb at \(T\); no further cash if fully prepaid at fair PV.

**Pitch:** offer at \(F_0\) is actuarially fair vs competing delivery price given time-value of deposit. Margin = offer \(-\, F_0\) (positive = Loop captures surplus; negative = subsidy).

---

## Evidence tiers

- **Trusted:** Fed H.15; Grit/Hatching Time product pages with explicit numbers; peer-reviewed hatchability/slaughter ranges.
- **Candidate (quarantine):** blog retail $/lb guides; grow-out headcount derate; mortality; replacement fractions.

Do **not** invent “Source: Admin analytics” labels.

---

## Run

```bash
cd research/quail   # or /workspace/quail-revenue-model
python run_example.py --y 5 --z 15 --U 1 --c-bar 2 --weeks 40
```
