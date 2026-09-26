# Ops forward dashboard (planning assist)

**Stage gate:** Stage 1 worms remain the only active spend. This screen tracks promises and sell room. It does not authorize crickets, isopods, land, greens, algae, quail, aquaponics, or community purchases. See [`../../biology/CASCADE.md`](../../biology/CASCADE.md).

The external `worm_growth_mc` / `worm_forward_book` tree is not in this repository and is not copied here. Scenarios below are a seeded stand-in so the dashboard runs on its own. Quail paths are a thinner stub (**ASSUMPTION**), not `research/quail/quail_model.py`.

## Breed floor

Same rule as [`../synergy/SPEC.md`](../synergy/SPEC.md):

\[
N_{\mathrm{floor}} = \max(N0,\ N_{\mathrm{start}},\ N_{\mathrm{safety}})
\]

Blank planned-start and safety-reserve fields use \(N0\). Sales and culls stop at the floor.

## Scenarios

Week index \(w\). Median doubling time \(D\) weeks (worms: 13, about 90 days, **ASSUMPTION**). Weekly noise \(\sigma\) (**ASSUMPTION**). Bin cap \(K = m \times \max(N0, N_{\mathrm{floor}})\) with \(m = 16\) for worms and \(m = 8\) for the quail stub.

\[
f_w \sim \mathrm{LogNormal}\big(\log(2^{1/D}),\ \sigma\big)
\]

\[
N_{w+1} = N_w + N_w\,(f_w - 1)\,\max\big(0,\ 1 - N_w/K\big) - H_w
\]

\(H_w\) is headcount removed that week (a delivery, or one month of a steady cull). A scenario fails if any week ends below \(N_{\mathrm{floor}}\).

Default run: 2,000 paths, seed `20260926`, so the screen does not jump on refresh. Worm weekly \(\sigma = 0.015\). Quail stub weekly \(\sigma = 0.01\). Both are **ASSUMPTION** values chosen so a year with no sales still keeps the breed floor in at least 90% of scenarios, which leaves a surplus that can be tested.

## Sell limit

Reliability \(x\) defaults to 0.90. That is “Safe to sell (P90)”: the breeding herd is still there in at least 90% of scenarios. At \(x = 0.90\) the allowed quantity is the low tail, in the same spirit as the firm book’s P10 rule. It is not the median herd, and it is not the deterministic \(0.9 \times N\) haircut in `circular_buffers.firm_surplus`.

For a delivery in month \(T\), after draft and promised rows already on the book:

\[
H^{\star} = \max\Big\{ H : \Pr\big(N_w \ge N_{\mathrm{floor}}\ \text{for all}\ w \le w_T\big) \ge x \Big\}
\]

\(H\) is added on top of those existing deliveries. Remaining room is \(H^{\star}\) in the sale unit (pounds). Already promised is the sum of draft and promised quantities. Delivered and cancelled rows stay on the list and do not take room.

A new draft or promised row is rejected when the book including that row fails the probability test. The UI shows that as a hard stop.

## Reverse tool

Inputs: target dollars, month \(t\), reliability \(x\), species, \(N0\) (and optional floor inputs).

Steady monthly cap: the same quantity \(q\) at each month-end from 1 through \(t\), largest \(q\) with probability at least \(x\).

Cumulative quantity is \(q\) times the number of month-ends. Income prices each month on its own:

\[
E[P(T)] = E[P_0]\,(1 + r_{\mathrm{inf}})^{T},\quad T = m/12
\]

\[
F_{\mathrm{prelim}}(m) = 0.9 \cdot \frac{E[P(T)]}{(1 + r_{\mathrm{prime}})^{T}}
\]

\[
\mathrm{Income}(q) = \sum_{m=1}^{t} q\, F_{\mathrm{prelim}}(m)
\]

Defaults match `research/synergy`: \(r_{\mathrm{inf}} = 0.027\), \(r_{\mathrm{prime}} = 0.07\), fairness \(0.9\).

The steady monthly target is feasible when \(\mathrm{Income}(q^{\star}) \ge\) target. If it is not, the tool searches a larger \(N0\) (floor inputs scale with it, up to 256×) and the earliest later month through month 36.

A separate one-delivery figure is the largest single removal at month \(t\), priced at \(F_{\mathrm{prelim}}(t)\). That can cover a target even when a sale every month cannot. The monthly cull stays blocked at \(q^{\star}\) either way.

## Prices and counts

| Species | Spot \(E[P_0]\) | Count | Tag |
|---------|----------------:|-------|-----|
| Worms | $42/lb | 1,000 per lb | Spot is the Ozark Worm Farms 10 lb bulk shelf price ($420). Not a farm-gate contract. Count is a planning 1,000 (vendors often say 800–1,000). |
| Quail | foodservice mean from `research/quail` (~$12.4633/lb) | ~1.709 birds per dressed lb (0.585 lb/bird) | Price source is the quail package. The path is an ASSUMPTION stub. |
