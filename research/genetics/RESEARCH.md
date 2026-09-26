# Sources — reproduction math

Tags are **SOURCED** or **ASSUMPTION**. Quail is Stage 4 planning. Fish is Stage 5 planning. Neither authorizes a purchase.

## Population size

| Item | Value | Tag | Source |
|------|-------|-----|--------|
| \(N_e = 4 N_m N_f / (N_m + N_f)\) | formula | SOURCED | Wright's sex-ratio effective size. Used as the idealized random-mating case. |
| \(\Delta F = 1/(2 N_e)\) | formula | SOURCED | Falconer and Mackay, quantitative genetics; FAO broodstock manual, Tave, *Inbreeding and brood stock management*, https://www.fao.org/4/x3840e/X3840E04.htm |
| Short-term cap | \(\Delta F \le 0.01\), so \(N_e \ge 50\) | SOURCED as the FAO short-term rule | FAO, *Conservation of the Genetic Resources of Fish*, https://www.fao.org/4/AD013E/AD013E04.htm |
| Long-term \(N_e\) near 500 | not the default | SOURCED as the same note's long-term figure | Same FAO page. Not applied as the gate. |
| Quail sex ratio | 1 male : 3 females | ASSUMPTION | Same planning ratio as `research/quail`. |
| Fish sex ratio | 1:1 | ASSUMPTION | Placeholder until a stock is chosen. |

## Quail depression

Sato and colleagues compared consecutive full-sib mating with random mating in Japanese quail and reported weighted regressions per 10% of F: fertility 2.16, hatchability 5.98, viability 5.50, fitness index 7.50 percentage points. Japanese Journal of Zootechnical Science 55(5):315, https://www.jstage.jst.go.jp/article/chikusan1924/55/5/55_5_315/_pdf

They note Sittmann, Abplanalp, and Fraser, Genetics 54:371–379 (1966), found about 7 points of hatchability per 10% F. The default hatch slope here is the 5.98-point regression, not the 7-point one.

Hen-day egg rate of about 3.38 points per 10% F is from a separate incross-line study, not from the Sato regression. It is stored as its own trait so the two papers are not averaged.

Added reject rate of 0.02 per 0.10 F is an **ASSUMPTION**. Those papers do not publish a grade or condemn rate.

## Fish depression

The Ne and \(\Delta F\) formulas above are the sourced part for fish. The 3% and 5% relative losses per 0.10 F are **ASSUMPTION** placeholders so a leakage case has a slope. They are not a measurement on the aquaponics species this cascade has not chosen.

## Pedigree

Offspring \(F = a_{\mathrm{sire},\mathrm{dam}}/2\) is the standard tabular relationship. Full-sib 0.25, half-sib 0.125, and parent–offspring 0.25 are the checks in `reproduction.py`.
