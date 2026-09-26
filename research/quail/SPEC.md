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
| Dress weight | ~0.585 lb | DERIVED cohort helper. Retired for the individual-bird meat planner. |
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

Competing spot \(E[P_{\mathrm{comp}}(0)]\) = mean of foodservice whole-bird $/lb comps (Webstaurant Manchester Farms regular/plus, Manchester case) — see RESEARCH. Specialty retail (D’Artagnan) listed but **excluded** from default mean.

Buyer prepay at \(t=0\) is a loan to Loop until delivery \(T\). **Most-fair prepaid** inflates competing goods first, then discounts at prime, then applies fairness 0.9 (Rod 2026-09-26):

\[
E[P_{\mathrm{comp}}(T)] = E[P_{\mathrm{comp}}(0)]\,(1 + r_{\mathrm{inf}})^{T}
\]

\[
\mathrm{NPV}_{\mathrm{comp}}(T) = \frac{E[P_{\mathrm{comp}}(T)]}{(1 + r_{\mathrm{prime}})^{T}}
\]

\[
F_{\mathrm{prelim}} = 0.9 \cdot \mathrm{NPV}_{\mathrm{comp}}(T)
= 0.9 \cdot E[P_{\mathrm{comp}}(0)] \left(\frac{1 + r_{\mathrm{inf}}}{1 + r_{\mathrm{prime}}}\right)^{T}
\]

Continuous flag (`continuous=True`):

\[
E[P_{\mathrm{comp}}(T)] = E[P_{\mathrm{comp}}(0)]\, e^{r_{\mathrm{inf}} T},\quad
\mathrm{NPV}_{\mathrm{comp}}(T) = E[P_{\mathrm{comp}}(T)]\, e^{-r_{\mathrm{prime}} T},\quad
F_{\mathrm{prelim}} = 0.9 \cdot \mathrm{NPV}_{\mathrm{comp}}(T)
\]

The factor \(0.9\) is a **10% discount on the NPV** of competing goods. The deposit is still discounted at prime.

**Default \(r_{\mathrm{inf}} = 2.7\%\)** — BLS CPI-U **Food**, 12-month percent change, **August 2026** (release 2026-09-11). https://www.bls.gov/news.release/archives/cpi_09112026.htm Overridable via `r_inf` or `drift_per_year` (pass 0 for a flat goods curve, or another rate). Same window, not used as the default: all-items CPI **3.4%**; meats, poultry, fish, and eggs **1.1%**. This meat forward uses **Food 2.7%**.

**Sophisticated (network):** average transport cost by delivery location sits on top and does not change the goods-NPV fairness core:

$$
F_{\mathrm{final}} = F_{\mathrm{prelim}} + c_{\mathrm{transport}}(\mathrm{location})
$$

That layer enables richer strategies for the network (hub placement, route pooling).

**Prime rate used:** \(r_{\mathrm{prime}} = 7.00\%\) — Fed H.15 bank prime loan, observation **2026-09-24**, release 2026-09-25. https://www.federalreserve.gov/releases/h15/

Cash flows: deposit \(F_{\mathrm{final}}\) per lb at 0; deliver 1 lb at \(T\); no further cash if fully prepaid.

**Pitch:** \(F_{\mathrm{prelim}}\) is the most-fair goods price (food inflation, prime on the deposit, then 10% NPV discount). Add transparent transport only when using the location model. Margin vs \(F_{\mathrm{prelim}}\) is Loop surplus/subsidy on the goods; transport should track cost, not hidden margin.

This is the same identity implemented by `fair_prepaid_forward_per_lb` in `quail_model.py` and, for every sellable cascade good, by `fair_prepaid` in [`../synergy/circular_buffers.py`](../synergy/circular_buffers.py).

## Cascade buffers

Quail rate, kit caps, and this prepaid stay in this file. Multi-species breed floors, waste ceilings, offtake shocks, and the rule that a shock halts export before breeders are cut are in [`../synergy/SPEC.md`](../synergy/SPEC.md). Pedigree and inbreeding haircuts for this flock are in [`../genetics/SPEC.md`](../genetics/SPEC.md). Both are planning only. They do not open Stage 2–5 spend. Stage 1 worms remain the source of record.

---

## Individual bird (meat planner)

`bird_mc.py` replaces the flat headcount-per-pound scalar for delivery and the dollar cases. The cohort helper in `quail_model.py` still uses the 13 oz × 72% mid-band bird (~0.585 lb) for its production-rate sample. That scalar is retired here.

Each path is a count of birds by sex and week of age. Every bird of that age faces the same weekly hazard (binomial). Hatch sex is its own draw. Only females lay. Purchased chicks are 1♂:3♀. Hatched chicks are 50/50 (ASSUMPTION). Kept breeders are the strict floor, 17♂ + 51♀, plus a 25% pad (ASSUMPTION) so one week's deaths are not the birds we sell. Harvest walks older birds first. Pounds are the sum of that bird's dressed weight.

| Schedule | Value | Tag |
|----------|-------|-----|
| Peak egg week \(x\) | 12 | ASSUMPTION. Onset 6–8 weeks is sourced. Rate is 0 before week 7, rises to 280/52 at week 12, then declines |
| Weekly hazard | 0.02 in week 0, else min(0.08, 0.004 + 0.00018 × age) | ASSUMPTION. Not a published life table |
| Male live asymptote | 12 oz | ASSUMPTION inside the 12–14 oz jumbo band |
| Female live asymptote | 14 oz | ASSUMPTION, same band |
| Male dress | 0.74 | ASSUMPTION inside 70–75% |
| Female dress | 0.70 | ASSUMPTION inside 70–75% |
| Dressed lb at week 9 | male 0.5232, female 0.5774 | DERIVED from those curves. The old smoke used one 0.585 lb bird |

Meat before week 8 is zero, so a month-1 order fails closed.

### Kit \(U\) on this planner

Mother Earth News listing (same SKU, fetched 2026-09-26): list **$3,729.96**, CT120SH up to 216 eggs, life-stage steps, breed/temperature disclaimer. That page does **not** restate standing headcounts. This planner keeps the prior caps: brooder 150 (sourced), jumbo breeder **45 = 3 per section × 15** (sourced), grow-out **75 jumbo** (ASSUMPTION). Binding check is per compartment. The sum 270 is not a single bin.

No egg cooler is listed. ASSUMPTION: one setter load (216) can sit for the week. No meat cooler is listed. Birds that do not fit the grow-out are dressed the same week; pounds the order does not take are unstored.

\(U \times \$3{,}729.96\) is a planning total. It does not authorize a purchase. Stage 1 worms remain the only spend.

Smoke, 48 paths, seed 20260926:

| Case | N0 | U | List total | What binds |
|------|----|---|------------|------------|
| $1,000 at month 2 (~89.8 lb at \(F_{prelim}=\$11.1406\)) | 268 | 4 | $14,919.84 | Grow-out, about 86% of \(U \times 75\). Unstored meat 0 |
| $2,000 every month from month 2 through 24 | 780 | 25 | $93,249.00 | Grow-out throughput. Median unstored dressed meat about 13,012 lb, because the kit has no cooler. Median eggs above the weekly store: 0. Many eggs are still unset |

## Evidence tiers

- **Trusted:** Fed H.15; Grit/Hatching Time product pages with explicit numbers; peer-reviewed hatchability/slaughter ranges.
- **Candidate (quarantine):** blog retail $/lb guides; grow-out headcount derate; mortality; replacement fractions.

Do **not** invent “Source: Admin analytics” labels.

---

## Run

```bash
cd research/quail   # or /workspace/quail-revenue-model
python run_example.py --y 5 --z 15 --U 1 --c-bar 2 --weeks 40
python bird_mc.py   # sex-specific dressed weight, $1000 and $2000 cases, egg and survival plots
```
