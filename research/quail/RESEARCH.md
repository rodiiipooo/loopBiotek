# Research notes — jumbo Coturnix + Grit kit + comps

Fetched / searched **2026-09-26** (America/Chicago). Every number tagged.

## Cascade context

- Quail = Stage 4. Worms = Stage 1 SoR. Planning only.
- Cascade: `loopBiotek/biology/CASCADE.md`

## Species — jumbo Coturnix japonica

| Claim | Value | Tag | Source |
|-------|-------|-----|--------|
| Eggs/hen/year | 200–300 (default 280) | SOURCED range | Agroproductividad review (Fagundes et al. cited 280–300); Incubator Warehouse guide 200–300 |
| Incubation | 17–18 d | SOURCED | Same guides; standard Coturnix |
| Lay onset | 6–8 wk | SOURCED | Incubator Warehouse; hobby guides |
| Peak hen-day timing | 94% at 15 wk of age (week 9 of lay); first egg mean 38.9 d in that unimproved flock | SOURCED | Narinc, Karaman, Aksoy, Firat. 2013. Poultry Science 92:1676–1682. https://doi.org/10.3382/ps.2012-02511 |
| Peak hen-day band | about 88–98%; one cited flock about 90% | SOURCED as cited by Narinc | Narinc et al. 2013, citing Minvielle et al. 2000 and Nestor and Bacon 1982. The planning peak rate 0.90 is an ASSUMPTION midpoint. Narinc's own peak was 94%. |
| Sharp drop in lay | after 26 wk of age; second-year eggs 48.3% of the first-year total | SOURCED | Woodard and Abplanalp 1971, summarized in the UC Davis manual *Japanese Quail Husbandry in the Laboratory* (senescence section). https://yumpu.com/en/document/view/19003227/japanese-quail-husbandry-in-the-laboratory-department-of-animal-/14 |
| Planning slot | fraction ≥ 0.85, which is weeks 14–33 of age | ASSUMPTION gate on the curve above | About 6 months of lay after the week-8 end of onset. The 365-day rotation stays the useful-life assumption, not this gate. |
| Jumbo live weight | 12–14 oz (default 13) | ASSUMPTION mid | Homesteading Place; Thank Chickens / JMF jumbo notes; Pips Farm “jumbo” ≥12 oz |
| Jumbo harvest window | 8–10 wk (default 63 d) | ASSUMPTION mid | Incubator Warehouse jumbo section; homestead harvest 8–10 wk |
| Dress yield | 70–75% (default 72%) | ASSUMPTION mid | Incubator Warehouse; Agroproductividad carcass 65–75% |
| Hatchability | 62.5–92.5% band (default 75%) | ASSUMPTION mid | Romão et al. LRRD meat-type Italian quail onset study |
| Standard (non-jumbo) live | 150–200 g | SOURCED (label separately) | Agroproductividad commercial meat lines — **not** used as jumbo default |

## Grit Quail Professional Kit

URL: https://store.grit.com/products/quail-professional-kit?variant=47213766246652

| Item | Spec | Tag | Source |
|------|------|-----|--------|
| Price | $3,449.99 sale / $3,729.96 list | SOURCED | Grit page WebFetch 2026-09-26 |
| Incubator | CT120SH, ≤216 quail eggs/batch | SOURCED | Kit page “Getting Started” |
| Brooder | CB25-03-5K 5-layer, ≤150 quail | SOURCED | Hatching Time chick brooder same SKU |
| Grow-out | GL25-03-5K 5-layer H:9.5" | SOURCED model; capacity ASSUMED 75 jumbo | Kit page + HT grow-out (“capacity depends on breed”) |
| Breeding cage | BYK-03-5K, 15/layer, 75 standard; larger birds 3/section → 45 | SOURCED | Grit/HT quail cage pages |
| Footprint (breed) | 38.6 × 24 × 77.2 in | SOURCED | HT specs |
| Footprint (grow-out) | ~36.3 × 21.6 × 77.2 in | SOURCED | Gone Broody / HT family listing |
| Brood narrative | wk 0–4 brood, 4–6 grow, ≥6 breed | SOURCED | Kit page steps (notes vary by breed/temp) |

## Competing meat prices ($/lb dressed)

| Comp | $/lb | Channel | Tag | Calc / source |
|------|------|---------|-----|----------------|
| Webstaurant MF whole 4–5 oz ×24 | **13.17** | foodservice | SOURCED | $118.49 / 9 lb case (page: total case size 9 lb; $0.82/oz) https://www.webstaurantstore.com/manchester-farms-4-5-oz-fresh-whole-quail-with-feet-case/871MAN33398.html |
| Same Plus member | **10.06** | foodservice | SOURCED | $90.55 / 9 lb |
| Manchester Farms case ~4 oz 6/4 @ $84.93 | **~14.16** | producer | SOURCED | $84.93 / (24×0.25 lb) from manchesterfarms.com shop table |
| D’Artagnan semi-boneless 4×4 oz | **31.99** | specialty retail | SOURCED | dartagnan.com — excluded from default E[P_comp] |
| Blog “farm-raised $6–10” | 8 mid | blog | **candidate / quarantine** | lowfodmapeating 2026 guide — not in default mean |

**Default \(E[P_{\mathrm{comp}}]\)** = mean(13.17, 10.06, 14.16) = **$12.4633/lb**.

Note: foodservice comps are often standard-size birds; $/lb still used as competing meat price for fair forward. Jumbo portion size differs; adjust comps when Loop SKU is quoted.

## Prepaid discount — 3-month T-bill

| Item | Value | Tag | Source |
|------|-------|-----|--------|
| \(r_{\mathrm{tbill}}\), FRED DTB3 | **4.01%** | SOURCED | 3-month Treasury bill, secondary market, discount basis, 2026-09-22. https://fred.stlouisfed.org/series/DTB3 |
| 3-month constant maturity | 4.24% | SOURCED, not used | Fed H.15, 2026-09-25. Not the prepaid discount. |
| Tenor | 3-month | planning lock | Short-horizon prepaid discount. |

## Food inflation (competing-goods drift)

| Item | Value | Tag | Source |
|------|-------|-----|--------|
| CPI-U Food, 12-month % change | **2.7%** | SOURCED | BLS CPI news release, August 2026, archived 2026-09-11. https://www.bls.gov/news.release/archives/cpi_09112026.htm |
| Same window, all items | 3.4% | SOURCED | Same release. Not the default. |
| Same window, meats, poultry, fish, and eggs | 1.1% | SOURCED | Same release. Not the default. |

Default \(r_{\mathrm{inf}}\) for this meat forward is **Food 2.7%** (`INFLATION_RATE`). Override with `r_inf` or `drift_per_year`, including 0 for a flat curve.

## Booking window (40 lb, P10)

The chart [`../plots/birds_per_lb_vs_month.png`](../plots/birds_per_lb_vs_month.png) (`research/decision_plots.py`) answers a different question from starters per pound. For an order of \(x\) pounds (default 40) delivered at week \(n\), it draws the flock that must already be on hand. The upper panel stacks males and females. The lower panel is \(F_{\mathrm{prelim}}\) with \(T = n/52\). Defaults: \(r_{\mathrm{inf}} = 0.027\), \(r_{\mathrm{tbill}} = 0.0401\), fairness \(0.9\).

The standing flock is **1 male : 3 females**, the jumbo Coturnix breeder ratio in this SPEC. That ratio is the reproductive maximum used here: more hens would leave some without a male at that practice, and more males would idle egg slots. The Ne floor at that ratio is 17 males and 51 females. Those birds are not sold.

\(N_{\mathrm{today}}\) is the larger of two fail-closed counts. One is the P10 herd that can finish \(x \times 1.15 / 0.9\) pounds, so the harsh tail still covers the order after the firm fraction and the cull-governor gross-up. The other is the Ne nucleus, grossed up for 1% weekly mortality over the lead, plus `birds_now_for_demand` for the dressed headcount. `safe_sell_limit` has to clear the sale with the floor still in place.

For 40 lb, week 4 needs 1,184 birds. Week 26 (about 6 months) needs 204 birds, 51 males and 153 females, and \(F_{\mathrm{prelim}}\) is about $11.15/lb, still near 0.9 times the $12.46 spot. A shorter lead burns starters on the P10 tail. A longer lead raises today’s pipeline because more weeks of mortality sit in front of the same order, and the prepaid is discounted further. Those 204 and 1,184 counts leave the hens in peak forever. `flock_today(..., sustain_peak=True)` adds the pullet pipeline that keeps the 17 male / 51 female nucleus inside the peak slot. The picture is [`../plots/peak_cull_layers.png`](../plots/peak_cull_layers.png). This is Stage 4 planning. It does not open quail spend. Stage 1 worms remain the source of record.

## Peak lay and the cull

The kit simulator's 280 eggs/hen/year is a blended annual rate. It is not the peak. Narinc et al. 2013 measured 94% hen-day at 15 weeks of age. Woodard and Abplanalp 1971, via the UC Davis husbandry manual, put a sharp drop after 26 weeks of age, and second-year lay at 48.3% of the first year. The planning curve draws straight lines between those anchors (ASSUMPTION) and keeps a hen in a peak slot while she is still at 85% of peak or better (ASSUMPTION). That gate is weeks 14–33 of age, about six months after the late edge of the 6–8 week onset. The old 365-day rotation is the far edge of a 6–12 month lay, not the peak.

Out-of-peak hens go to meat. The cull does not take the flock under 17 males and 51 females. Replacements are in-peak hens, and the standing breeders stay 1 male : 3 females. For a $10,000 prepaid meat order at one year (week 52), `cascade_growth_today()` prints \(N_{\mathrm{today}}\) with that pipeline and without it. Spent-hen meat is not credited against the order. Regenerate with `python3 research/quail/test_peak_cull.py` and `python3 research/decision_plots.py`.

## Model limitations (honest)

- Deterministic weekly cohorts; no stochastic disease / fertility shock.
- Grow-out jumbo headcount is an **assumption**.
- Continuous incubator utilization approximates batch setter/hatcher cycling.
- Replacement fractions and mortality are placeholders until farm data.
- No live trading / Kalshi.
