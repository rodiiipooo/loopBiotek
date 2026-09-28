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

Default run: 2,000 paths, seed `20260926` in Python’s `random.Random`, so the screen does not jump on refresh. No extra numerical library is required. Worm weekly \(\sigma = 0.015\). Quail stub weekly \(\sigma = 0.01\). Both are **ASSUMPTION** values chosen so a year with no sales still keeps the breed floor in at least 90% of scenarios, which leaves a surplus that can be tested.

## Sell limit

The default planning quantile is **P10** (\(x = 0.10\)). P10 is the amount you can still deliver in the harsh futures: only 10% of scenarios are this low or lower. You plan as if outcomes are bad. P90 of the same pound distribution is the good-growth case and is not a default for sell room or delivery planning. The screen refuses a percentile above 0.50.

P10 is the 10th percentile of finished headroom, which is the largest \(H\) that at least 90% of futures can still clear. It is not the median herd, and it is not the deterministic \(0.9 \times N\) haircut in `circular_buffers.firm_surplus`.

For a delivery in month \(T\), after draft and promised rows already on the book:

\[
H^{\star} = Q_{P10}\big(\text{headroom at month } T\big)
\]

\(H\) is added on top of those existing deliveries. Remaining room is \(H^{\star}\) in the sale unit (pounds). Already promised is the sum of draft and promised quantities. Delivered and cancelled rows stay on the list and do not take room.

A new draft or promised row is rejected when the book including that row misses the P10 bar. The UI shows that as a hard stop.

## Reverse tool

Inputs: target dollars, month \(t\), harsh-case percentile \(x\) (default 0.10), species, \(N0\) (and optional floor inputs).

Steady monthly cap: the same quantity \(q\) at each month-end from 1 through \(t\), largest \(q\) that is still the P10 of that path.

Cumulative quantity is \(q\) times the number of month-ends. Income prices each month on its own:

\[
E[P(T)] = E[P_0]\,(1 + r_{\mathrm{inf}})^{T},\quad T = m/12
\]

\[
F_{\mathrm{prelim}}(m) = 0.9 \cdot \frac{E[P(T)]}{(1 + r_{\mathrm{tbill}})^{T}}
\]

\[
\mathrm{Income}(q) = \sum_{m=1}^{t} q\, F_{\mathrm{prelim}}(m)
\]

Defaults match `research/synergy`: \(r_{\mathrm{inf}} = 0.027\), \(r_{\mathrm{tbill}} = 0.0401\) (FRED DTB3, 3-month bill, 2026-09-22), fairness \(0.9\).

The steady monthly target is feasible when \(\mathrm{Income}(q^{\star}) \ge\) target. If it is not, the tool searches a larger \(N0\) (floor inputs scale with it, up to 256×) and the earliest later month through month 36.

A separate one-delivery figure is the largest single removal at month \(t\), priced at \(F_{\mathrm{prelim}}(t)\). That can cover a target even when a sale every month cannot. The monthly cull stays blocked at \(q^{\star}\) either way.

## Prices and counts

| Species | Spot \(E[P_0]\) | Count | Tag |
|---------|----------------:|-------|-----|
| Worms | $42/lb | 1,000 per lb | Spot is the Ozark Worm Farms 10 lb bulk shelf price ($420). Not a farm-gate contract. Count is a planning 1,000 (vendors often say 800–1,000). |
| Quail | foodservice mean from `research/quail` (~$12.4633/lb) | ~1.709 birds per dressed lb (0.585 lb/bird) | Price source is the quail package. The path is an ASSUMPTION stub. |

## Delivery structure (quail)

A shorter time until delivery leaves less growth above the breeding flock, so each promised pound needs more starters. The growth curve is the quail ASSUMPTION in this package (doubling about 26 weeks, bin cap 8 times the starters). It is not the cohort simulator. The floor that cannot be sold is the strict genetics floor from [`../genetics/SPEC.md`](../genetics/SPEC.md): \(N_e \ge 50\), \(F_{\max} = 0\), quail ratio 1 male : 3 females, which is 68 birds.

Let \(Q_{\mathrm{P10}}(N, T)\) be the P10 dressed pounds at month \(T\): the amount you can still deliver in the harsh futures, with the starting herd kept. Only 10% of scenarios are this low or lower. Because the bin cap scales with \(N\),

\[
b(T) = \frac{N_{\mathrm{probe}}}{Q_{\mathrm{P10}}(N_{\mathrm{probe}}, T)}
\]

does not depend on the order size. \(b(T)\) falls as \(T\) rises. Starters for an order of \(Q\) pounds are

\[
N_0(Q, T) = \max\big(N_{\mathrm{keep}},\ Q \cdot b(T)\big)
\]

with \(N_{\mathrm{keep}} = 68\). A 10 lb order is smaller than what 68 birds can safely finish even by month 3, so \(N_0\) stays 68 and the inverse relationship shows up in \(b(T)\) and in the room left after the promise. A larger order (the smoke uses 40 lb) raises \(N_0\) when delivery is soon.

Given several sales, each with a month window, the screen tries the earliest month in every window, the latest month, a single month when every sale can use it, and an even split. It keeps the plan with the smallest \(N_0\). Ties go to the plan with more safe pounds left. If none of the windows can be filled without the breeding flock, the promise is refused.

Ops uses this to choose a delivery month from realized sales: push pounds later, or split a sale that must go out early from one that can wait, instead of lumping everything into the soonest month.

## $2,000 a month from month 2

Planning question: how many quail `N0` must be on hand at purchase so that, on the P10 tail, meat sales can bring in about $2,000 every month starting in month 2 and continuing through month 24. Month 1 is growth only. This is Stage 4 planning. It does not buy birds or feed, and Stage 1 worms remain the only spend.

Growth is the quail ASSUMPTION stub in this folder (doubling about 26 weeks, bin cap 8 times the starters, weekly noise 0.01). It is not the cohort simulator. The birds that cannot be sold are `keep = max(N0, 68)`, where 68 is the strict genetics floor (Ne ≥ 50, F_max = 0, 1 male : 3 females). The purchased flock stays. The meat is growth above that floor.

Pounds in month `m` are `$2,000 / F_prelim(m)`, using the quail prepaid already in this package. At month 2 that price is about $11.19/lb, so the order is about 179 lb. By month 24 the prepaid is a little lower, so the same dollars are a few more pounds.

`research/ops-dashboard/quail_income.py` searches the smallest such `N0`. The smoke writes `results/quail_income_smoke.json` and two plots: starters against monthly dollars, and worm plus plant feed against the herd.

Feed is an ASSUMPTION, not a measured ration: 22 g as-fed per bird per day, split 30% live worms and 70% plant. The 0.41 waste ceiling in the synergy spec is a different limit. It is not this split. The standing count used for feed is the heavy herd (only 10% of futures are larger). On top of that month's ration, the synergy buffer keeps 2 weeks of feed on hand. If the supply is only enough for the light herd and has no buffer, the meat sale fails closed. The breeding floor is not cut to stretch the feed.

Smoke (`python3 quail_income.py`, 2,000 paths, seed `20260926`): **N0 = 2,813**. Month 2 sells 178.68 lb at \(F_{\mathrm{prelim}} = \$11.1933\). Month 24 sells 182.88 lb at \$10.9362. Both months are \$2,000. At month 24 the heavy herd needs about 1,167 kg of worms and 2,723 kg of plant feed (1.17 t and 2.72 t), plus the 2-week buffer of that same ration.

## Decision charts

`research/decision_plots.py` writes the PNG gallery in [`../plots/`](../plots/README.md). The ops screen serves that folder. Each file is labeled assumption versus measurement. P10 is the default tail.

| Chart | Decision |
|-------|----------|
| `birds_per_lb_vs_month.png` | Flock on hand today for a 40 lb surplus-only delivery. Week 4 needs 1,184 birds. Week 26 needs 204 (51 males and 153 females at 1:3). Later weeks need more because of pipeline mortality. The lower panel is \(F_{\mathrm{prelim}}\) at the 4.01% 3-month bill. |
| `delivery_split_vs_soon.png` | 15 lb locked in month 3 plus 15 lb that can wait needs about 87 starters. All 30 lb in month 3 needs about 173. |
| `quail_n0_for_2000.png` and `quail_feed_vs_herd.png` | The $2,000 case above, and the feed that heavy herd eats. |
| `worm_p10_sell_room.png` | At 16,500 worms, P10 room is about 13 lb in month 3 and about 113 lb in month 12. |
