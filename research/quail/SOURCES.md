# Sources

Each planning input is tagged **SOURCED** (a page or in-repo workbook states it) or **ASSUMED** (used so the screen is runnable, not a measured LoopBiotek result).

Checked 2026-09-26 unless noted.

## Biology

| Input | Value in model | Tag | Source |
|-------|----------------|-----|--------|
| Species | Jumbo *Coturnix japonica* | SOURCED as the bird class; "jumbo" is a commercial size class, not a separate species | Model target |
| Incubation, biological | 17 days | SOURCED | Mississippi State University Extension, [Hatchery Management Guide](https://extension.msstate.edu/agriculture/livestock/poultry/hatchery-management-guide-for-game-bird-and-small-poultry-flock-owners), Table 2: Coturnix quail incubation period 17 days. Same figure in Utah State University Extension, [Hatching and Caring for Chicks](https://extension.usu.edu/utah4h/research/hatching-and-caring-for-chicks). |
| Sexual maturity | 6 weeks in the literature; model finish age is 8 weeks for meat | SOURCED for 6 weeks; ASSUMED for the 56-day meat clock | Oregon State thesis citing Wilson, Abbott, and Abplanalp (1961): coturnix sexually mature at 6 weeks ([PDF](https://ir.library.oregonstate.edu/downloads/2514nq19d)). Grit moves birds to breeder cages after 6 weeks of life. |
| Founder ratio y:z | 5 males : 15 females, fertility 0.90 when at least 1 male per 5 females | SOURCED benchmark; the linear drop below 1:5 is ASSUMED | Padgett and Ivey (1959), as cited in that OSU thesis: 5 males to 15 females gave about 90% fertility. |
| Eggs per hen | 6 / week | ASSUMED | Inside a high Coturnix lay rate (most days). Not a LoopBiotek measurement. |
| Hatch rate | 0.80 | ASSUMED | Planning midpoint. Not measured here. |
| Survival to process | 0.95 | ASSUMED | Planning factor. Not measured here. |
| Live weight | 16 oz (1.00 lb) | ASSUMED | Upper end of jumbo Coturnix advertisements. Not a weigh-in. |
| Ready-to-cook yield | 0.77 of live weight → 0.77 lb dressed | ASSUMED | Optimistic yield. Chosen so 37.5 birds/week × 0.77 lb = 28.875 lb/week, which rounds to the worked example 28.9. |

## Grit Quail Professional Kit

Product: [Quail Professional Kit, variant 47213766246652](https://store.grit.com/products/quail-professional-kit?variant=47213766246652). Page read 2026-09-26. Cimuka model QUAIL-PROKIT.

| Input | Value | Tag | What the page actually says |
|-------|------:|-----|-----------------------------|
| Sale price | $3,449.99 | SOURCED | "Regular price $3,449.99 USD" (compare-at $3,729.96). `reference/loop_params.xlsx` still carries the older $3,729.96 figure; this screen uses the live sale price. |
| Incubator | CT120SH, 216 eggs/batch | SOURCED | "Set / hatch up to 216 quail eggs per batch." |
| Brooder time | First 4 weeks | SOURCED | "For the first 4 weeks, the brooder supplies the necessary heat." |
| Grow-out time | Weeks 4–6 | SOURCED | "Let you quail feather out in our grow out pens." |
| Breeder move | After 6 weeks of life | SOURCED | "After week 6, move your quail to the breeding cages." |
| Brooder standing cap | 150 birds | ASSUMED | Not printed on the page. Used as 5-layer × 30. |
| Grow-out, jumbo | 75 birds | ASSUMED | Not printed. 5-layer pen × 15 jumbo birds, half a standard-coturnix stocking guess. |
| Breeder standing cap | 45 birds | ASSUMED | Not printed. 5-layer × 9. |
| Operational incubation cycle | 21 days → 72 eggs/week | SOURCED in-repo, not from Grit | `climate/thermal-model/PARAMS_FROM_XLSX.md` extracts `reference/loop_params.xlsx`: 216 eggs, 21-day cycle, 72 eggs/week/kit. |

The page disclaimer says those week-bands vary by breed and room temperature.

## Prime

| Input | Value | Tag | Source |
|-------|------:|-----|--------|
| Bank prime loan | 7.00% | SOURCED | Federal Reserve H.15, [Selected Interest Rates (Daily)](https://www.federalreserve.gov/releases/h15/), release date 2026-09-25. Column **2026 Sep 24**: Bank prime loan **7.00**. Footnote 7: rate posted by a majority of the top 25 insured U.S.-chartered banks. |

Prepaid term \(T = 0.5\) year is a worked-example choice (**ASSUMED** horizon), not a quote.

## Meat comps

### Screening anchor (used for F0)

| Input | Value | Tag |
|-------|------:|-----|
| \(\mathbb{E}[P_{\mathrm{comp}}]\) | 12.4633 USD/lb | **ASSUMED** worked-example composite |

\[
F_0 = 12.4633 / (1.07)^{0.5} \approx 12.0488
\]

Distributor case prices below are **not** averaged into 12.4633. They are higher specialty-foodservice prints. Use them as a ceiling check. Replace the anchor with a local buyer book before any prepaid contract.

### SOURCED quotes (not the anchor)

| Quote | Case math | USD/lb | Source |
|-------|-----------|-------:|--------|
| Manchester Farms 63777, whole natural, 4 oz avg, 24 birds, $84.93 | 24 × 4/16 = 6 lb | 14.16 | [Manchester Farms shop](https://manchesterfarms.com/shop-for-quail/), item 63777, read 2026-09-26 |
| Manchester Farms 5 oz avg whole or breast-cut, $84.93, 24 birds | 24 × 5/16 = 7.5 lb | 11.32 | Same page, items 53093 / 93039 |
| WebstaurantStore Manchester Farms 4 oz fresh whole, $108.99 / case | 6 lb case | 18.17 | [WebstaurantStore](https://www.webstaurantstore.com/manchester-farms-fresh-whole-quail-4-oz-case/871MF33366A.html) |
| 123 Farmers, skinless jumbo meat | listed per lb | 19 frozen / 25 fresh | [123farmers.com](https://123farmers.com/Jumbo-Coturnix-Quail.html) |

## In-repo cross-checks

- Capital order: `biology/CASCADE.md` (Stage 1 worms only).
- Kit cycle already extracted from the workbook: `climate/thermal-model/PARAMS_FROM_XLSX.md`.
