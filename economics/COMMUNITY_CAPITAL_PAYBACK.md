# Community capital payback

People can pool setup capital and take it back from project proceeds in proportion to what they put in. This page is the planning rule and the formulas behind `community_capital.py`. It is research math for the open repository.

It is not legal, tax, or securities advice. A live pool needs its own agreements. Every default dollar figure below is an **ASSUMPTION**: a planning input, not verified commercial performance.

**Stage 1 (worms) is the only active spend** until vermiculture revenue is at least $2k/mo, or a firm prepaid forward runway covers Stage-1 costs, and Rod clears the gate. Source of record: [`../biology/CASCADE.md`](../biology/CASCADE.md). Sizing a food stock or a shell in this model does not open crickets, isopods, land, greens, algae, quail, aquaponics, or community QoL spend.

`R_t` is surplus the caller has already computed **after** the nutrition stack, operating costs, and Module 11-style reserves (nutrition shortfall, seed floor, unserved energy, negative cash). This page does not compute those gates and does not sell a herd forward. Firm forward book stays P10 surplus only, in the external worm model.

## Rod’s rule

`n` people contribute. Person `i` contributes capital `x_i ≥ 0`.

\[
X = \sum_i x_i
\]

The opening ownership share is

\[
s_i = \frac{x_i}{X} \quad (X > 0)
\]

If \(X = 0\), shares are undefined. There is no capital claim. Any surplus follows the post-payback rule among listed residents.

Each period `t`, distributable surplus \(R_t \ge 0\) goes to **capital recovery** while any contribution in the active tranche is still unpaid. The payment is the locked share of that period’s surplus, and it stops at the unpaid balance:

\[
p_{i,t}^{\text{cap}} = \min\left(o_{i,t},\; s_i R_t\right)
\]

\(o_{i,t}\) is what `i` is still owed. With the default interest rate of 0, \(o_{i,t} = x_i - \sum_{\tau < t} p_{i,\tau}^{\text{cap}}\) (principal only).

Before anyone is capped, each dollar of contribution draws the same fraction of the surplus:

\[
\frac{p_{i,t}^{\text{cap}}}{x_i} = \frac{R_t}{X}
\]

Someone who contributes more dollars receives more of each dollar of proceeds. That is a larger absolute payment, at the same rate per dollar. Equal contributions produce equal payment streams. With a constant \(R\) and a zero interest rate, every member of the same tranche finishes in the same period, because the time to recover \(x_i\) is \(X / R\).

When a member’s balance hits zero, further capital payments to that member stop. Their unclaimed slice of \(R_t\) is **not** added to anyone else’s locked share. If that leftover cannot be paid inside the tranche without raising a share, it is recorded as unallocated for the period while any principal in the tranche remains. Unallocated is a period report: the model does not roll it into the next \(R_t\). A later period includes that cash only when the caller puts it in that period’s surplus. Capital claims do not continue after the whole pool is repaid.

### Optional interest

`interest_rate_per_period` defaults to **0**. A positive rate is an **ASSUMPTION**. At the start of the period the model accrues simple interest on outstanding principal, \(r \times\) principal, and retires that interest before principal. Repayment then stops when principal and accrued interest are both zero, so cumulative receipts can exceed \(x_i\). The rate uses the same period length as \(R_t\).

### Post-payback surplus

After **every** capital obligation is zero, leftover surplus in that same period, and every later \(R_t\), follows a resident rule. The default **ASSUMPTION** is equal per current member:

\[
p_{i,t}^{\text{post}} = \frac{R_t^{\text{left}}}{n_{\text{active}}}
\]

Optional **ASSUMPTION**: labor shares \(w_i / \sum w\) among current members (`post_payback="labor_shares"`). Weights are an input. They are not inferred from hours.

Worked switch: contributions 300 and 100, one period with \(R = 1000\). Capital payments are 300 and 100. The leftover 600 is split 300 and 300. The larger investor does not keep a 75% claim on the leftover.

## Headcount and weight to setup CapEx

Inputs are parameters. `H` is average daily resident count. `W` is average resident body weight in kilograms.

Food, kcal basis (default):

\[
\text{kg per person-day} = \frac{k_{\text{kcal/kg body/day}} \cdot W}{k_{\text{kcal/kg food}}}
\]

Food, mass basis (`basis="kg_scaled"`):

\[
\text{kg per person-day} = m_{\text{ref}} \cdot \frac{W}{W_{\text{ref}}}
\]

\[
\text{FoodStockCapEx}(H, W) = H \cdot D_{\text{days}} \cdot (\text{kg per person-day}) \cdot p_{\$/kg}
\]

Facility area can ignore weight or scale with it. \(\epsilon =\) `area_weight_elasticity`. \(\epsilon = 0\) keeps area flat. \(\epsilon = 1\) scales meters squared with \(W / W_{\text{ref}}\).

\[
A(W) = A_{\text{ref}} \left(\frac{W}{W_{\text{ref}}}\right)^{\epsilon}
\]

\[
\text{FacilityCapEx}(H, W) = H \cdot A(W) \cdot c_{\$/m^2}
\]

\[
\text{SetupCapEx} = \text{FoodStockCapEx} + \text{FacilityCapEx} + C_{\text{other}}
\]

\[
X_{\min} = \text{SetupCapEx}
\]

\(C_{\text{other}}\) defaults to 0. It is the hook for a **cited** Stage-1 setup cost (worm bins and climate hardware live in the cascade and the external worm model). The default does not insert quail-kit, cricket, land, algae, or aquaponics prices.

Coverage of a contribution list:

\[
\text{shortfall} = \max(0,\; X_{\min} - X), \qquad \text{covers} \iff X \ge X_{\min}
\]

If `n` people split \(X_{\min}\) evenly, each contributes \(X_{\min} / n\).

### Default parameters (ASSUMPTION)

| Parameter | Default | Role |
| --- | ---: | --- |
| `food_days` | 90 | days of food stock |
| `kcal_per_kg_body_per_day` | 30 | planning energy factor per kilogram of body weight; not a diet prescription |
| `kcal_per_kg_food` | 3600 | planning energy density of a dry staple stock |
| `usd_per_kg_food` | 2.50 | planning food-stock price |
| `m2_per_person` | 12 | planning floor area at the reference weight |
| `usd_per_m2` | 800 | planning shell cost |
| `ref_weight_kg` | 70 | reference body weight for area and for the kg-scaled food basis |
| `area_weight_elasticity` | 0 | facility area independent of `W` until a caller sets otherwise |
| `other_capex` | 0 | cited extra setup hook |
| `interest_rate_per_period` | 0 | principal-only recovery |

At \(H = 20\), \(W = 70\) kg and those defaults:

\[
\text{kg per person-day} = 30 \times 70 / 3600 = 7/12
\]

\[
\text{FoodStockCapEx} = 20 \times 90 \times (7/12) \times 2.50 = 2625
\]

\[
\text{FacilityCapEx} = 20 \times 12 \times 800 = 192000
\]

\[
X_{\min} = 194625, \quad X_{\min}/5 = 38925
\]

Recompute with `python community_capital.py` if the defaults change. Doubling `H` doubles both food stock and facility cost. Doubling `W` doubles food stock on the kcal basis. Facility cost changes with `W` when `area_weight_elasticity` is not 0.

## Edge-case policy stubs

These are planning policies encoded in the module so a run has an explicit result. They are not legal advice and they are not a claim about what a contract should say.

| Case | What the model does |
| --- | --- |
| Late joiner | Senior shares stay locked. The new contribution opens a **junior tranche**, repaid only after earlier tranches are clear. People who join in the same period share that new tranche in proportion to what they add. In the period a senior tranche clears, leftover cash of that period is the junior tranche’s \(R\). |
| Exit before repaid | The unpaid principal stays a claim at the locked share. The person is removed from the post-payback resident split. |
| Explicit forfeit | The unpaid balance is written off and that share becomes 0. Other locked shares stay put. While any principal remains in the tranche, the freed slice is **unallocated**, not a raise for the people who stayed. |
| \(X < X_{\min}\) | `pool_coverage` reports the shortfall. Payback runs on capital that was actually contributed. The model does not treat the setup as funded. |
| \(R_t = 0\) | Capital payments are 0 and principal is unchanged, so repayment stretches. With the optional interest rate above 0, the unpaid obligation still grows. |
| \(X = 0\) | Shares are undefined (`pool_empty`). Surplus uses the post-payback rule if residents are listed. |

Within one period, exits and forfeits are applied first, then late joins.

## Run

From this directory:

```bash
python community_capital.py
python community_capital.py --H 20 --W 70
python -m unittest test_community_capital.py
```

The example prints three scenarios:

1. **Equal 5 × 20%** of \(X_{\min}(H, W)\). Same payment each period; the period after clearance is labeled `post_payback`.
2. **One 50% and four 12.5%** of the same \(X_{\min}\). The 50% member receives four times the dollars of a 12.5% member, at the same rate per dollar, until principal is back. The following period is an equal resident split.
3. **Unequal contributions** (80k + 40k + 20k + 10k + 5k) against that \(X_{\min}\), including the shortfall, a leading \(R_t = 0\) period, and an H, W grid (flat area, and one row with area elasticity 1).

`cum_capital` in the tables is principal recovered. It does not increase on a post-payback row.

## What stays outside this file

- Nutrition order, Module 11 thresholds, and export-last rules: root [README](../README.md) and [`../reference/complete_model.ipynb`](../reference/complete_model.ipynb).
- Which biological stage may be spent: [`../biology/CASCADE.md`](../biology/CASCADE.md).
- Worm population and forward book: `/workspace/worm-revenue-model/` (do not copy that code here).
- Quail kit counts and fair prepaid meat: [`../research/quail/`](../research/quail/). Stage 4 planning. Pass a quail price as `other_capex` only after Rod has cleared that stage; the default hook stays 0.
- Microeconomic map (present value, public goods, hold-up), chapter titles only: [`../docs/MICRO_FOR_COMMUNITIES.md`](../docs/MICRO_FOR_COMMUNITIES.md).
