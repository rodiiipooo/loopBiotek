# Sources — synergy buffers

Planning notes. Tags are **SOURCED** or **ASSUMPTION**. No cricket, isopod, fish, or worm waste ceiling is invented.

## Breed floor and firm book

| Item | Value | Tag | Note |
|------|-------|-----|------|
| Floor | \(\max(N0, N_{\mathrm{start}}, N_{\mathrm{safety}})\) | planning rule | Generalizes the worm rule: do not sell the breeding herd. Cascade anti-pattern: do not sell median (P50) stock forward. |
| Firm-book \(\alpha\) | 0.9 | ASSUMPTION stand-in | Matches the worm reliability / P10 pattern cited in `biology/CASCADE.md` until that Monte Carlo is ported. Not a new fit. |
| Culling \(\epsilon\) | 0.01 | SOURCED as the Loop example | `README.md` Module 1b uses \(\alpha_Q = 1\%\). The code proxy is not that probability. |
| Horizon \(\tau\) | caller parameter (weeks) | — | The notebook example uses 8 weeks. |

## Waste ceilings

Computed from the deterministic Module 2 curves in `reference/complete_model.ipynb` (quail maintenance 0.018, BSFL maintenance 0.050):

| Species | Notebook break-even | Planning ceiling used here | Tag |
|---------|---------------------:|---------------------------:|-----|
| Quail | ~0.405 | 0.41 | SOURCED from that curve; ceiling is the rounded guard |
| BSFL | ~0.705 | 0.71 | SOURCED from that curve; ceiling is the rounded guard |
| Crickets | — | none | ASSUMPTION placeholder |
| Isopods | — | none | ASSUMPTION placeholder |
| Fish | — | none | ASSUMPTION placeholder |
| Worms | — | none | ASSUMPTION placeholder |

## Prices

| Item | Value | Tag | Source |
|------|-------|-----|--------|
| \(r_{\mathrm{inf}}\) | 2.7% | SOURCED | BLS CPI-U Food, 12-month change, August 2026, release 2026-09-11. https://www.bls.gov/news.release/archives/cpi_09112026.htm |
| Same window, all items | 3.4% | SOURCED | Same release. Not the default. |
| Same window, meats, poultry, fish, and eggs | 1.1% | SOURCED | Same release. Not the default. |
| \(r_{\mathrm{prime}}\) | 7.00% | SOURCED | Fed H.15 bank prime loan, 2026-09-24. https://www.federalreserve.gov/releases/h15/ |
| Fairness | 0.9 | planning rule | 10% discount on the NPV of competing goods. Same as `research/quail`. |
| Worm flat 33% discount | legacy | LEGACY | External `/workspace/worm-revenue-model/` forward book. Not vendored. Not used by `fair_prepaid`. |

## Buffers

Default \(B_s = 2\) weeks of feed and of product is an **ASSUMPTION** so the 2-week feed-delay shock has a number. Replace it with measured cover before operations.

## Migration

Do not copy `worm_growth_mc` or `worm_forward_book` into this tree. When that book is ported, firm quantity stays the P10 (reliability) surplus and the price becomes \(F_{\mathrm{prelim}}\), not the flat 33% legacy discount.
