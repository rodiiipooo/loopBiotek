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

## Prime rate

| Item | Value | Tag | Source |
|------|-------|-----|--------|
| Bank prime loan | **7.00%** | SOURCED | Fed H.15 daily; 2026-09-18…24 all 7.00; release date 2026-09-25 https://www.federalreserve.gov/releases/h15/ |
| As-of used in model | 2026-09-24 | SOURCED | H.15 observation column |
| Context | Raised from 6.75% after Sep 16, 2026 FOMC | SOURCED | Reuters / U.S. Bank IR 2026-09-16 |

## Food inflation (competing-goods drift)

| Item | Value | Tag | Source |
|------|-------|-----|--------|
| CPI-U Food, 12-month % change | **2.7%** | SOURCED | BLS CPI news release, August 2026, archived 2026-09-11. https://www.bls.gov/news.release/archives/cpi_09112026.htm |
| Same window, all items | 3.4% | SOURCED | Same release. Not the default. |
| Same window, meats, poultry, fish, and eggs | 1.1% | SOURCED | Same release. Not the default. |

Default \(r_{\mathrm{inf}}\) for this meat forward is **Food 2.7%** (`INFLATION_RATE`). Override with `r_inf` or `drift_per_year`, including 0 for a flat curve.

## Booking window (40 lb, P10)

The chart [`../plots/birds_per_lb_vs_month.png`](../plots/birds_per_lb_vs_month.png) (`research/decision_plots.py`) draws starters per pound and \(N_0\) on the upper panel and \(F_{\mathrm{prelim}}\) on a lower panel. The price uses the locked formula and this file’s foodservice spot. \(T\) in the formula is the delivery month divided by 12. Defaults: \(r_{\mathrm{inf}} = 0.027\), \(r_{\mathrm{prime}} = 0.07\), fairness \(0.9\).

Around month 6, starters per pound have flattened to about 2.5 and a 40 lb P10 order needs about 100 birds, while \(F_{\mathrm{prelim}}\) is still close to the spot NPV after fairness (0.9 times $12.4633/lb). That neighborhood is the window for a firm forward. A very short \(T\) burns starters (month 1 is on the order of 20 birds per pound). A very long \(T\) only weakly improves starter efficiency — \(N_0\) is soon the 68-bird Ne floor — and the prepaid is discounted further versus waiting. This is Stage 4 planning. It does not open quail spend. Stage 1 worms remain the source of record.

## Model limitations (honest)

- Deterministic weekly cohorts; no stochastic disease / fertility shock.
- Grow-out jumbo headcount is an **assumption**.
- Continuous incubator utilization approximates batch setter/hatcher cycling.
- Replacement fractions and mortality are placeholders until farm data.
- No live trading / Kalshi.
