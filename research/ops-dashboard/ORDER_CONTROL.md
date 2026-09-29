# Order control

Stage 4 planning. This does not sell anything and it does not authorize a purchase. **Stage 1 worms remain the only spend** until vermiculture revenue is at least $2k/mo, or a firm prepaid runway covers Stage-1 costs, and Rod clears that gate. See `biology/CASCADE.md`.

The question this answers: how many birds (or pounds) can go out the door this week, or by a later week, without eating the breeding nucleus or giving up a growth rate you named.

## Weekly growth

`g` is a fraction **per week**, same clock as `M_WEEKLY` (1% mortality per week in the synergy helper).

| `g` | Meaning |
|----:|---------|
| 0 | The herd at week `t` is at least as large as it is today |
| 0.01 | About 1% more birds each week |
| 0.02 | About 2% more birds each week |

Quail in the ops-dashboard stub double in 26 weeks. That is an **ASSUMPTION**. The weekly multiplier is `rho = 2 ** (1/26)`, about 1.027, so about 2.7% per week. A target faster than that cannot be met by selling anything. The allowed sale goes to 0.

`t` is a whole number of weeks.

## What you can sell

Heads you can take **today** and still be on the growth path at week `t`:

```
S <= N * (1 - (1+g)^t / rho^t)
```

That number is then cut by the helpers that already exist:

- `safe_sell_limit` — firm surplus is 0.9 times the heads above the floor. If a forward breeder need is set, survivors at weekly mortality must still cover that need times 1.15.
- `keep_floor` / `cull_plan` — Coturnix at the default Ne keep **17 males and 51 females**. Surplus only. Breeders are not the product. The standing flock practice is 1 male : 3 females.
- `birds_now_for_demand` — inverted, so a delivery at week `t` has a pipeline on hand today.
- `flock_today` — for quail, the week-`t` delivery also has to fit the flock that helper says you need today. If `flock_today` grows a `sustain_peak` argument (peak-cull branch), it is passed as true.

Missing counts, a missing doubling time, or a helper that cannot answer: **allowed = 0**.

`safe_sell_limit` keeps the forward floor alive with weekly mortality and no births. If that proxy will not release a single animal over the lead, the week-`t` delivery is 0 as well. A doubling time that says the herd would have grown does not override it. Worms sitting only a little above a large floor will show 0 for a long lead for this reason.

`n0` is the breed-floor anchor (founders and the safety stock), not today's headcount. If you set `n0` equal to `n_now`, surplus is zero.

## Five gates on one order

`accept_order` says yes only when all five hold.

1. **Population.** After this order and every open reservation, males stay at or above 17 and females at or above 51 (or the species' own `keep_floor`). The sale comes out of surplus. It does not take a breeder.
2. **Growth.** The schedule, including this order, still leaves `N * (1+g)^t` at the horizon.
3. **Cascade.** Coupled feed math is used when `research/cascade_growth` is on the branch (`firm_take`). It is not on this branch. **STUB:** each species is checked on its own floor. Set `feed_reserve_heads` if some of the surplus has to stay as feed for the next species. This sale does not lower another species' floor. Do not raid breeders to fill a neighbor's ration.
4. **Income.** For the next `H` months (default 3), the thinnest week's firm surplus, scaled by 52/12, is still at least `M_min`. Default `M_min` is **$3,000/mo**. **ASSUMPTION**, optional target, from `economics/MARGIN_3K_BACKSOLVE.md`. It is not a measured bill. A flock that cannot throw that off refuses every order. `capacity_plan` sizes the hold that can.
5. **ROI.** Revenue is `F_prelim` from `fair_prepaid` (inflation 2.7%, 3-month bill 4.01%, fairness 0.9, spot from the ops-dashboard engine), unless you pass a `price_fn`. Variable cost for quail is **$1.85/bird**. **ASSUMPTION** (`$3.169/lb × ~0.585 lb` on the margin page; the source file is not in this checkout). Worm opex is **17.8% of prepaid revenue**. **ASSUMPTION** (path C margin ratio 0.822). Other species have no cost here, so their ROI fails closed.

Opportunity cost is only the growth you give up, not the heads this order already pays for:

```
opp_heads = H * ((1+g)^t - 1)
opp_cost  = opp_heads * max(0, revenue_per_head - var_per_head)
contribution = revenue - var_cost - opp_cost
ROI = contribution / capital_tied
```

Capital tied defaults to variable cost. The hurdle defaults to 0. The order passes the ROI gate when ROI is at least the hurdle, or contribution is at least 0. Unknown price or unknown cost fails closed.

The runway prices capacity at fair prepaid. It does not charge opportunity cost a second time. A low quote fails the ROI gate even when the flock's capacity still clears `M_min`.

## Reservations

`OrderBook` keeps open orders in memory. Pass a path and it also writes JSON under a file you choose (`research/ops-dashboard/results/` is the usual place). `reserve` / `release` add and drop a row. `available_firm(species, week, state, g, t)` subtracts every open reservation for that species from the firm cap, so the same surplus is not promised twice.

`accept_order` does not write the book unless `policy["commit"]` is true. On a yes, call `book.reserve` yourself, or set `commit`.

## Call it

From `research/ops-dashboard`:

```python
import order_control as oc

state = oc.quail_planning_state(1000, 3000)  # males, females; floor defaults to 17/51
print(oc.sellable_for_growth("quail", state, g=0.01, t=26)["allowed"])

order = {"species": "quail", "qty": 20, "unit": "lb", "week": 8}
print(oc.order_roi(order, state, oc.default_price_fn, hurdle=0.0))

book = oc.OrderBook()
decision = oc.accept_order(
    order,
    book,
    {"quail": state},
    {"g": 0.01, "t_weeks": 26, "H_months": 3, "M_min": 0},
)
print(decision.accept, decision.reasons)

plan = oc.capacity_plan(0.0, 3000, 26, species="quail")
print(plan["hold_heads"], plan["min_monthly"], plan["feasible"])
```

`sellable_for_growth` returns heads in `allowed` (sell now, over the horizon) and `allowed_by_t` (deliver at week `t` if you sell nothing before that). Quail pounds are `allowed_lb`. A schedule in the fifth argument returns `feasible` and `residual`.

`M_min=0` in the snippet turns the income target off so a 4,000-bird example can be read on its own. The default target is $3,000/mo. Use `capacity_plan` before you treat that default as something this flock can promise.

## Smoke

```bash
python3 research/ops-dashboard/test_order_control.py
```

That checks: sellable heads fall as `g` rises; an order bigger than surplus is refused; a sale that would cut the 17/51 nucleus is refused; a reservation lowers `available_firm`; a 20¢/lb stub fails ROI. It prints the week-26 quail table and one accept / one reject.

## What this will not do

- Open Stage 2–5 spend, buy kits, or name a vendor to pay.
- Sell the median herd. Firm room stays the 0.9 surplus stand-in for P10.
- Treat worms, crickets, greens, or fish margins as locked. Only quail and worms have a cost tag here, and both tags are assumptions.
- Replace `research/synergy/circular_buffers.py` or `research/ops-dashboard/delivery.py`. This module calls them.
