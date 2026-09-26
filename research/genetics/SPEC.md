# Reproduction math (planning only)

**Stage gate:** Stage 1 worms remain the only active spend. Quail numbers are Stage 4 planning. Aquaponics fish numbers are Stage 5 planning. This file does not authorize birds, tanks, or any other Stage 2–5 purchase. See [`../../biology/CASCADE.md`](../../biology/CASCADE.md).

Purpose: a sale of surplus animals must not force the next mating to be a relative, and an accidental inbred hatch must show up as worse goods and a slower flock before anyone books it as normal production.

Two modes are both implemented in `reproduction.py`.

## Shared definitions

Wright's sex-ratio effective size (idealized random mating):

\[
N_e = \frac{4 N_m N_f}{N_m + N_f}
\]

The inbreeding added in one generation (Falconer and Mackay; the same relation is the FAO broodstock rule):

\[
\Delta F \approx \frac{1}{2 N_e}
\]

Default cap \(\Delta F \le 0.01\) per generation, so \(N_e \ge 50\). That is the FAO short-term “one percent” rule for fish genetic resources. An \(N_e\) near 500 is the long-term figure in that same note and is **not** the default gate.

The numerator relationship \(a_{ij}\) is the tabular relationship. The inbreeding coefficient of an offspring is the kinship of its parents:

\[
F_{\mathrm{offspring}} = a_{\mathrm{sire},\mathrm{dam}} / 2
\]

Unrelated founders give \(F = 0\). Full sibs give \(F = 0.25\). Half sibs give \(F = 0.125\). Parent–offspring gives \(F = 0.25\).

A parent id that is named but missing from the book is treated as unrelated to everyone listed. That hides kinship. Strict mode refuses a book with that gap.

## 1. Strict: no inbreeding

Default cap \(F_{\max} = 0\). A proposed mating is allowed only when \(F_{\mathrm{offspring}} \le F_{\max}\). At the default, only unrelated pairs pass.

A cull is allowed only when all of these hold:

- Males and females left still meet \(N_e \ge 50\) at the stated sex ratio (quail planning ratio 1 male : 3 females, the same ratio as `research/quail`; fish planning ratio 1:1, an **ASSUMPTION**).
- Headcount left is at least the synergy breed floor \(\max(N0, N_{\mathrm{start}}, N_{\mathrm{safety}})\) from [`../synergy/SPEC.md`](../synergy/SPEC.md).
- Headcount left is also at least the smallest whole-animal herd that reaches \(N_e = 50\) at that sex ratio. The number that must stay is the larger of the two floors. Surplus is what sits above that combined floor.
- If a pedigree is supplied, at least one remaining pair still has \(F \le F_{\max}\), and every named pairing under consideration passes.

Selling the synergy surplus while leaving only one family is refused, even when the raw headcount is still above \(N0\).

## 2. Leakage: accidental inbreeding

If a fraction \(x\) of offspring are inbred at a known class kinship \(F_{\mathrm{class}}\) (default full-sib \(0.25\)) and the rest are unrelated:

\[
\bar F = x \, F_{\mathrm{class}}
\]

You may pass \(\bar F\) directly instead of \(x\).

Quail haircuts are percentage-point drops per \(0.10\) of \(F\), on a 0–1 trait:

\[
y(F) = \max\big(0,\ y_0 - \beta_{10} \cdot F / 0.10\big)
\]

| Trait | \(\beta_{10}\) | Tag |
|-------|---------------:|-----|
| Fertility | 0.0216 | SOURCED. Sato and colleagues, full-sib versus random mating, Japanese quail. About 2.16 points per 10% F. |
| Hatch | 0.0598 | SOURCED. Same study. Sittmann, Abplanalp, and Fraser (1966) reported about 7 points; this default uses 5.98. |
| Viability (growth stand-in) | 0.0550 | SOURCED. Same study, about 5.50 points per 10% F. |
| Egg rate | 0.0338 | SOURCED from a different incross study (about 3.38 points of hen-day rate per 10% F). Not the Sato regression. |
| Reject rate, added | 0.02 | **ASSUMPTION.** Those papers do not report a carcass-grade regression. |

Hatch baseline \(y_0 = 0.75\) matches the quail planning midpoint. At \(F = 0.10\), hatch is \(0.75 - 0.0598\).

Fish haircuts are a fraction of the baseline lost per \(0.10\) of \(F\):

\[
y(F) = y_0 \cdot \max\big(0,\ 1 - b_{10} \cdot F / 0.10\big)
\]

| Trait | \(b_{10}\) | Tag |
|-------|----------:|-----|
| Hatch | 0.05 | **ASSUMPTION.** Not a measured aquaponics stock. |
| Growth | 0.03 | **ASSUMPTION.** |
| Fecundity | 0.05 | **ASSUMPTION.** |
| Viability | 0.05 | **ASSUMPTION.** |
| Reject rate, added points | 0.03 | **ASSUMPTION.** |

Fish hatch baseline \(0.80\) is an **ASSUMPTION** so the formula has a number. Replace it with a measured hatch before operations.

Reject rate is \(\min(1,\ r_0 + \beta_{10} \cdot F / 0.10)\). Saleable fraction is \(1\) minus that rate. Goods that fail the reject rate are not booked as production.

## What this does not do

It does not open Stage 2–5 spend. It does not replace the quail cohort simulator or an aquaponics design. Fish slopes are not tilapia measurements. The Ne formula ignores selection and, unless you pass a pedigree, it cannot see a cousin mating.
