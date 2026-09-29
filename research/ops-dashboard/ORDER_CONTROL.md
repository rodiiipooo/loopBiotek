# Order control

Stage 4 planning. This does not sell anything and it does not authorize a purchase. **Stage 1 worms remain the only spend** until vermiculture revenue is at least $2k/mo, or a firm prepaid runway covers Stage-1 costs, and Rod clears that gate. See `biology/CASCADE.md`.

The knob is **R_min**: average monthly **revenue** over a rolling window of **H** months. Default **R_min is $3,000/month** and default **H is 3**. The $3,000 figure is the planning target in `economics/MARGIN_3K_BACKSOLVE.md`. It is an **ASSUMPTION** planning floor, not a measured bill, and not permission to buy stock.

The dollar test on an order is prepaid **revenue** (`F_prelim`). Contribution margin is a second check. It runs when this module has a variable-cost **ASSUMPTION** for that species. If that cost is missing, the revenue floor still applies and the contribution check stays quiet. If the cost is present and contribution per head is below zero, the order is refused.

## What the operator does not set first

A weekly growth rate `g` is not the policy. After a sale, every cascade feed edge still has to clear and every Ne floor still has to hold. From that retained stock the module reports an implied `g_s`:

- `g_s = 0` when the herd left on hand is still at least the breed floor plus the feed buffer. Do not shrink that stock.
- `g_s` is missing when the sale would cut the floor or the buffer. The order is refused.

Biological doubling sits beside that number. It is the ops-dashboard stand-in (`rho = 2 ** (1 / doubling_weeks)`), not a target. Quail 26 weeks and worms 13 weeks are **ASSUMPTION** doubling times.

Pass `g` in the policy only when you want an extra whole-herd path on top of the revenue floor. `sellable_for_growth` is that helper. `g` there is a fraction **per week**, same clock as `M_WEEKLY` (1% mortality per week in the synergy helper). `t` is a whole number of weeks.

| `g` | Meaning, only when you pass it |
|----:|---------|
| 0 | The herd at week `t` is at least as large as it is today |
| 0.01 | About 1% more birds each week |
| 0.02 | About 2% more birds each week |

A target faster than `rho - 1` cannot be met by selling anything. The allowed sale goes to 0.

## Cascade feed

Species feed each other. This graph is the order-control check. It does not change the spend order in `biology/CASCADE.md`. Stage 1 worms remain the only spend.

```
algae (enriched nutrient water) → aquaponic vegetables / fruits / plants
plant product and waste         → worms, crickets, and quail (edible plants)
worms                           → fish and quail
crickets                        → fish and quail
```

`greens`, `vegetables`, and `fruit` in a herd book are the plant node.

An edge is checked only when both ends are in the herd book. The stock that must stay on the upstream side is:

```
rate per week × downstream breed floor × BUFFER_WEEKS
```

`BUFFER_WEEKS` is 2, from `research/synergy/circular_buffers.py`.

Default rates are **ASSUMPTION** placeholders, upstream units per downstream head per week. They are not a measured diet. Override them with `policy["feed_rates"]` using a `("worms", "quail")` key or a `"worms->quail"` string.

| Edge | ASSUMPTION units / head / week |
|------|-------------------------------:|
| worms → quail | 20 |
| worms → fish | 20 |
| crickets → quail | 10 |
| crickets → fish | 10 |
| algae → plants | no default |
| plants → worms, crickets, or quail | no default |

An edge with both ends in the book and no rate fails closed, unless the upstream herd already carries `feed_reserve_heads`. That explicit buffer covers the unrated edges out of that species.

## Cascade scale law

To scale production of species `i` by a factor `lambda_i`, every upstream species `j` has to cover the extra ration from the stock it already has. **ASSUMPTION**:

```
lambda_j = (lambda_i * (1 + g_i) * c_{i←j} * N_i) / max(eps, (g_j - loss_j) * N_j)
```

`c_{i←j}` is the same weekly ration as the feed table (upstream units per head of `i`). `N_i` and `N_j` are the headcounts in the book. `g_i` defaults to 0, which holds the downstream herd, and then `(1 + g_i)` is 1. Set `g` on that herd, or pass an explicit policy `g`, to raise the draw. `g_j` defaults to the doubling stand-in `rho_j - 1`. `loss_j` defaults to `M_WEEKLY` (1% per week). Override either on the upstream herd with `g`, `loss_per_week`, or `m_weekly`.

The walk follows the feed graph backward: algae, then plants, then worms and crickets, then the fish or quail being scaled. An upstream eaten by two descendants gets the sum of those draws, then one lambda.

The scale is refused when any of these is true:

- The upstream net surplus rate `(g_j - loss_j)` is <= 0. The formula does not divide by that rate.
- The herd is already under its Ne / breed floor, or the scaled draw over `BUFFER_WEEKS` is larger than firm surplus (`safe_sell_limit`, and `cascade_growth.model.firm_take` when that module is on the tree).
- `lambda_j > 1`. Today's upstream stock cannot feed the larger sale.

A missing ration fails closed the same way. `lambda_j > 1` is a headroom miss. It is not a shopping list. Stage 1 worms remain the only spend.

`accept_order` sets `lambda_i` to `(one week of firm offtake + this order) / that offtake` when the book has an upstream of the species being sold. No upstream in the book leaves the walk empty. `capacity_plan` sets `lambda_i` to the sized herd divided by the herd already in `cascade_state` (or 1 when the sized herd is the one placed in the book).

```python
factor = oc.upstream_scale_factor("quail", "worms", 1.0, book)
plan = oc.scale_cascade("quail", 1.0, book)
```

## What you can sell (`sellable_for_growth`)

This helper answers a growth question. Capacity and order acceptance do not require it.

Heads you can take **today** and still be on a named growth path at week `t`:

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

## Gates on one order

`accept_order` says yes only when all of these hold. Fail closed.

1. **Population.** After this order and every open reservation, males stay at or above 17 and females at or above 51 (or the species' own `keep_floor`). The sale comes out of surplus. It does not take a breeder.
2. **Cascade feed.** Every live feed edge still clears. Implied `g_s` is 0 on the retained stock. A missing ration on a live edge refuses the order. The scale law also has to clear: upstream net surplus rate above 0, Ne floors intact, and `lambda_j` at or below 1 for the sales scale this order implies.
3. **Revenue.** For the next `H` months (default 3), the thinnest week's firm surplus, priced at fair prepaid and scaled by 52/12, is still at least `R_min`. A flock that cannot throw that revenue off refuses the order. `capacity_plan` sizes the hold that can. An older `M_min` key is read as the same revenue dollars.
4. **Contribution (secondary).** When a variable-cost **ASSUMPTION** exists, monthly contribution on that same harvest has to stay at or above zero. Quail cost is **$1.85/bird** (`$3.169/lb × ~0.585 lb` on the margin page; the source file is not in this checkout). Worm opex is **17.8% of prepaid revenue** (path C margin ratio 0.822). Other species have no cost here, so this check does not invent one.
5. **ROI.** Revenue on the quote is `F_prelim` from `fair_prepaid` (inflation 2.7%, 3-month bill 4.01%, fairness 0.9, spot from the ops-dashboard engine), unless you pass a `price_fn`.

If the policy sets `g`, a sixth check runs: the sales schedule, including this order, still leaves `N * (1+g)^t` at the horizon, and the order stays inside that helper's long-lead firm cap.

Opportunity cost is only the growth you give up, not the heads this order already pays for:

```
opp_heads = H * ((1+g)^t - 1)
opp_cost  = opp_heads * max(0, revenue_per_head - var_per_head)
contribution = revenue - var_cost - opp_cost
ROI = contribution / capital_tied
```

When `g` was not set, opportunity uses `g = 0`, so the growth increment is zero. Capital tied defaults to variable cost. The hurdle defaults to 0. The order passes the ROI gate when ROI is at least the hurdle, or contribution is at least 0. Unknown price or unknown cost fails closed.

The runway prices capacity at fair prepaid. It does not charge opportunity cost a second time. A low quote fails the ROI gate even when the flock's prepaid revenue still clears `R_min`.

Firm surplus at the **delivery week** (the 0.9 stand-in for P10) still has to cover the order. The 26-week mortality proxy is reserved for `sellable_for_growth` and for the extra cap that runs when `g` is set.

## Which product to sell

`rank_skus` scores each species that has a prepaid price:

```
score = revenue per head / units of the binding bottleneck per head
```

The binding bottleneck is the inbound feed edge with the fewest weeks of upstream firm surplus. A species with no upstream in the book is scored on its own head (denominator 1). A live inbound edge with no ration leaves that species unranked. The winner is the highest finite score: the most revenue toward `R_min` per unit of the tightest upstream surplus.

## Reservations

`OrderBook` keeps open orders in memory. Pass a path and it also writes JSON under a file you choose (`research/ops-dashboard/results/` is the usual place). `reserve` / `release` add and drop a row. `available_firm(species, week, state, g, t)` subtracts every open reservation for that species from the firm cap, so the same surplus is not promised twice.

`accept_order` does not write the book unless `policy["commit"]` is true. On a yes, call `book.reserve` yourself, or set `commit`.

## Call it

From `research/ops-dashboard`:

```python
import order_control as oc

state = oc.quail_planning_state(1000, 3000)  # males, females; floor defaults to 17/51

# Optional. g is per week. Capacity and accept_order do not need it.
print(oc.sellable_for_growth("quail", state, g=0.01, t=26)["allowed"])

order = {"species": "quail", "qty": 20, "unit": "lb", "week": 8}
print(oc.order_roi(order, state, oc.default_price_fn, hurdle=0.0))

book = oc.OrderBook()
decision = oc.accept_order(
    order,
    book,
    {"quail": state},
    {"R_min": 3000, "H_months": 3, "hurdle": 0.0},
)
print(decision.accept, decision.reasons)
print(decision.residuals["runway"]["min_monthly_revenue"])

plan = oc.capacity_plan(3000, H_months=3, species="quail")
print(plan["hold_heads"], plan["min_monthly_revenue"], plan["feasible"])

book_state = {
    "worms": {"n_now": 50000, "n0": 16500},
    "quail": state,
}
print(oc.rank_skus(book_state)["winner"])
```

`sellable_for_growth` returns heads in `allowed` (sell now, over the horizon) and `allowed_by_t` (deliver at week `t` if you sell nothing before that). Quail pounds are `allowed_lb`. A schedule in the fifth argument returns `feasible` and `residual`.

`capacity_plan(R_min, H_months=3, species="quail")` sizes the hold whose prepaid revenue clears `R_min` while the herd is maintained (`g` omitted, implied 0 on retained stock). Pass `g=` only to demand a faster path. `R_min=0` keeps the breed floor and an empty sell schedule.

`R_min=0` on `accept_order` turns the revenue floor off so a small example can be read on its own. The default floor is $3,000/month revenue. Use `capacity_plan` before you treat that default as something this flock can promise.

## Smoke

```bash
python3 research/ops-dashboard/test_order_control.py
```

That checks: sellable heads fall as `g` rises; an order bigger than surplus is refused; a sale that would cut the 17/51 nucleus is refused; a reservation lowers `available_firm`; a 20¢/lb stub fails ROI; a small flock misses the revenue floor; a worm sale that cuts the quail feed buffer is refused; quail ranks above worms on revenue per binding upstream unit. It prints the week-26 quail table, one accept, one reject, and the rank winner.

## What this will not do

- Open Stage 2–5 spend, buy kits, or name a vendor to pay.
- Sell the median herd. Firm room stays the 0.9 surplus stand-in for P10.
- Treat worms, crickets, greens, algae, or fish margins as locked. Only quail and worms have a cost tag here, and both tags are assumptions. Algae and plant rations have no default.
- Replace `research/synergy/circular_buffers.py`, `research/ops-dashboard/delivery.py`, or the spend order in `biology/CASCADE.md`. This module calls the first two and leaves the third alone.
