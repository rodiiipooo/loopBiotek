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
| `P_meat(t)`, `fair_prepaid_forward_per_lb(T)` | competing forward + T-bill-discounted prepaid |

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
| Ne floor at 1:3 | 17♂ / 51♀ | DERIVED (Ne ≥ 50) |

### Egg-layer peak window

Hens are not kept at the blended 280 eggs/year rate forever. That 280 is a year-long average. Peak lay is a shorter slot. A hen occupies a peak slot while her productive fraction stays at or above **0.85** (ASSUMPTION). On the planning curve that is **weeks 14 through 33 of age**.

| Anchor | Value | Tag |
|--------|-------|-----|
| Onset | 6–8 wk (planning midpoint 49 d, already above) | SOURCED |
| Full peak hen-day | week 15 of age, 94% in Narinc et al. 2013 | SOURCED |
| Sharp drop | after 26 wk of age (Woodard & Abplanalp 1971) | SOURCED |
| Slot gate | fraction ≥ 0.85 | ASSUMPTION |
| In-peak ages | weeks 14–33 | DERIVED from the gate |
| Peak hen-day used for eggs | 0.90 | ASSUMPTION midpoint of the 88–98% band |
| Fraction shape | straight lines between the anchors | ASSUMPTION |
| Week-52 fraction | 0.50 | ASSUMPTION. Second-year lay was 48.3% of the first-year total, which is not this weekly point |
| Useful-life rotation | 365 d | ASSUMPTION already in the kit sim. Not the peak gate |
| Decline band named in planning | after ~6–12 months of lay | The 6-month edge is the slot gate (~26 wk of lay after week 8). The 12-month edge is the 365 d rotation |

Productive fraction \(f(a)\) at age \(a\) weeks, 1.0 on the plateau:

\[
f(a)=\begin{cases}
0 & a<6\\
(a-6)/9 & 6\le a<15\\
1 & 15\le a\le 26\\
1-0.5\,(a-26)/26 & 26<a\le 52\\
0.5\,(1-(a-52)/52) & 52<a<104\\
0 & a\ge 104
\end{cases}
\]

In peak when \(f(a)\ge 0.85\).

**Cull.** Out-of-peak hens are marked for meat, oldest first. The cull stops if the birds left would fall under 17 males or 51 females. In-peak hens are not culled to make the flock smaller. Males above 1:3 of the hens that remain, and above 17, are surplus meat. Replacements are the in-peak hens still short of the target. The target snaps up to an exact 1:3 flock that also covers 17/51.

**Steady replacement** for \(F\) peak hen slots ( \(F\) already snapped to 1:3 ):

\[
r=\frac{F}{\sum_{a\in\mathrm{peak}}(1-m)^{a}}
\]

\[
\text{hens into the cage per week}=r\,(1-m)^{a_{\min}}
\]

Pipeline females are ages \(0\) through \(a_{\min}-1\). Pipeline males are the 1:1 brothers through the meat slaughter week (63 d). Adult breeders stay \(F\) hens and \(F/3\) males. They are already in the standing flock, so `flock_today` adds only the pipeline.

`simulate_population(..., params=BiologyParams(use_peak_lay=True))` lays at \(0.90\times 7\) eggs/week from in-peak hens only, and culls hens past the slot to meat. The default kit ramp still uses the blended 280/year rate so the published meat ramp does not move. The Ne floor is enforced in `peak_cull_policy` and `flock_today`, not in a 5-male starter sim.

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

Buyer prepay at \(t=0\) is a loan to Loop until delivery \(T\). **Most-fair prepaid** inflates competing goods first, then discounts at the 3-month Treasury bill yield, then applies fairness 0.9 (Rod 2026-09-26; discount lock updated from bank prime to the T-bill):

\[
E[P_{\mathrm{comp}}(T)] = E[P_{\mathrm{comp}}(0)]\,(1 + r_{\mathrm{inf}})^{T}
\]

\[
\mathrm{NPV}_{\mathrm{comp}}(T) = \frac{E[P_{\mathrm{comp}}(T)]}{(1 + r_{\mathrm{tbill}})^{T}}
\]

\[
F_{\mathrm{prelim}} = 0.9 \cdot \mathrm{NPV}_{\mathrm{comp}}(T)
= 0.9 \cdot E[P_{\mathrm{comp}}(0)] \left(\frac{1 + r_{\mathrm{inf}}}{1 + r_{\mathrm{tbill}}}\right)^{T}
\]

Continuous flag (`continuous=True`):

\[
E[P_{\mathrm{comp}}(T)] = E[P_{\mathrm{comp}}(0)]\, e^{r_{\mathrm{inf}} T},\quad
\mathrm{NPV}_{\mathrm{comp}}(T) = E[P_{\mathrm{comp}}(T)]\, e^{-r_{\mathrm{tbill}} T},\quad
F_{\mathrm{prelim}} = 0.9 \cdot \mathrm{NPV}_{\mathrm{comp}}(T)
\]

The factor \(0.9\) is a **10% discount on the NPV** of competing goods. The deposit is discounted at \(r_{\mathrm{tbill}}\).

**Default \(r_{\mathrm{inf}} = 2.7\%\)** — BLS CPI-U **Food**, 12-month percent change, **August 2026** (release 2026-09-11). https://www.bls.gov/news.release/archives/cpi_09112026.htm Overridable via `r_inf` or `drift_per_year` (pass 0 for a flat goods curve, or another rate). Same window, not used as the default: all-items CPI **3.4%**; meats, poultry, fish, and eggs **1.1%**. This meat forward uses **Food 2.7%**.

**Sophisticated (network):** average transport cost by delivery location sits on top and does not change the goods-NPV fairness core:

$$
F_{\mathrm{final}} = F_{\mathrm{prelim}} + c_{\mathrm{transport}}(\mathrm{location})
$$

That layer enables richer strategies for the network (hub placement, route pooling).

**Bill rate used:** \(r_{\mathrm{tbill}} = 4.01\%\), tenor **3-month**. FRED series **DTB3** (secondary-market discount basis), observation **2026-09-22**. https://fred.stlouisfed.org/series/DTB3 Rod locked this quote for the prepaid discount. The H.15 3-month constant maturity on 2026-09-25 is 4.24% and is not \(r_{\mathrm{tbill}}\).

Cash flows: deposit \(F_{\mathrm{final}}\) per lb at 0; deliver 1 lb at \(T\); no further cash if fully prepaid.

**Pitch:** \(F_{\mathrm{prelim}}\) is the most-fair goods price (food inflation, the 3-month T-bill yield on the deposit, then 10% NPV discount). Add transparent transport only when using the location model. Margin vs \(F_{\mathrm{prelim}}\) is Loop surplus/subsidy on the goods; transport should track cost, not hidden margin.

This is the same identity implemented by `fair_prepaid_forward_per_lb` in `quail_model.py` and, for every sellable cascade good, by `fair_prepaid` in [`../synergy/circular_buffers.py`](../synergy/circular_buffers.py).

## Cascade buffers

Quail rate, kit caps, and this prepaid stay in this file. Multi-species breed floors, waste ceilings, offtake shocks, and the rule that a shock halts export before breeders are cut are in [`../synergy/SPEC.md`](../synergy/SPEC.md). Pedigree and inbreeding haircuts for this flock are in [`../genetics/SPEC.md`](../genetics/SPEC.md). Both are planning only. They do not open Stage 2–5 spend. Stage 1 worms remain the source of record.

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
