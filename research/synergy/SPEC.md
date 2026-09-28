# Cascade synergy buffers (planning only)

**Stage gate:** Stage 1 worms remain the only active spend. This file is planning math for every cascade species. It does not authorize crickets, isopods, land, greens, algae, quail, aquaponics, or community QoL purchases. See [`../../biology/CASCADE.md`](../../biology/CASCADE.md).

Purpose: keep a sufficient breeding population on every link of the nutrient spine so a growth or consumption shock in one species cannot be met by raiding the breeders of another.

Sell and cull only surplus above the breed floor. Firm forwards sell only the reliability-quantile slice of that surplus.

---

## 1. Breed floor

For species \(s\) in week \(w\):

\[
N_{\mathrm{floor}}(s,w) = \max\big(N0_s,\ N_{\mathrm{start}}(s,w),\ N_{\mathrm{safety},s}\big)
\]

\(N0_s\) is the founding breeder count. \(N_{\mathrm{start}}\) is this week’s planned start (it can fall after a bad hatch). \(N_{\mathrm{safety}}\) is the reserve that does not follow a bad week down. Surplus is \(\max(0,\ N - N_{\mathrm{floor}})\). Revenue, meat orders, and another species’ feed ration stop at that line.

For quail and aquaponics fish, the count that must stay is the larger of this floor and the effective-population floor in [`../genetics/SPEC.md`](../genetics/SPEC.md). A sale that clears \(N_{\mathrm{floor}}\) but leaves too few unrelated males and females is still refused. That package is planning only.

## 2. Culling governor

From the Loop report (Module 1b; \(\alpha_Q = 0.01\) in the worked example, horizon \(L\) in weeks):

\[
H_s = \max\Big\{ H : \Pr\big(N_{\mathrm{breed}}(s, w+\tau) < N_{\mathrm{req}}(s, w+\tau)\big) \le \epsilon \Big\}
\]

Default \(\epsilon = 0.01\). \(\tau\) is a parameter in weeks. The actual offtake is the minimum of demand, \(H_s\), and surplus above the floor.

`cull_cap_deterministic` is a **proxy**, not that probability. It has no draws. It requires the point projection to clear \(N_{\mathrm{req}} / (1-\epsilon)\) after a per-week growth factor compounds for \(\tau\) weeks, then clips \(H\) to the breed-floor surplus. Replace it with the report’s Monte Carlo before any harvest rule is treated as measured.

## 3. Circular-shock guards

Nutrient spine: waste → worms/isopods; insects and greens → quail and fish; water → greens; castings → plants.

**Safety stocks.** Each species holds \(B_s\) weeks of incoming feed and \(B_s\) weeks of outgoing product. Default \(B_s = 2\) is an **ASSUMPTION**, chosen so a documented 2-week feed delay is visible in the smoke test. It is not a measured coverage.

**Waste ceilings** (diet fraction \(\phi\)). Above the ceiling, growth is at or below maintenance in the Loop Module 2 curves (`reference/complete_model.ipynb`):

| Species | \(\phi\) ceiling | Tag |
|---------|-----------------:|-----|
| Quail | 0.41 | SOURCED (break-even in that notebook is ~0.405; planning ceiling 0.41) |
| BSFL | 0.71 | SOURCED (break-even ~0.705; planning ceiling 0.71) |
| Crickets, isopods, fish, worms | none | **ASSUMPTION / placeholder.** No number until a source exists. |

**Rate of change.** A proposed weekly offtake may use only the firm room \(\max(0,\ \alpha N - N_{\mathrm{floor}})\), with default \(\alpha = 0.9\). That \(\alpha\) is the planning stand-in for the worm firm book (P10 surplus, not the median). If the proposal exceeds the room, export is halted and breeders are not cut to make up the difference.

**Shocks that must fail closed** (halt export before shrinking breeders):

| Shock | Guard |
|-------|--------|
| Quail offtake +50% | Refuse the jump. Sell at most the firm room. |
| Worm hatch −30% | Floor stays at \(\max(N0, N_{\mathrm{safety}}, N_{\mathrm{start,new}})\). Do not sell down to the shocked start. |
| Feed delay 2 weeks | Breeder ration keeps the feed buffer. Export feed is refused. No cull to stretch feed. |
| Insect die-off | Mortality is charged to surplus first (control priority, not a claim about which animals die). Feed orders above the remaining surplus are halted. |

`circular_buffers.py` smoke covers these four. `fail_closed` means export halted and breeders were not taken under the floor.

### Safe-sell control law

Helpers in `circular_buffers.py` (`safe_sell_limit`, `birds_now_for_demand`, `margin_backsolve`). Planning only. Defaults: \(\alpha = 0.9\), weekly mortality \(m = 0.01\), safety fraction \(s = 1.15\). \(s\) is an **ASSUMPTION**. \(m\) matches the quail planning default.

\[
H_{\max} = \max(0,\ N_{\mathrm{now}} - N_{\mathrm{floor}})
\]

\[
D_{\mathrm{firm}} \le \alpha \cdot H_{\max}
\]

\[
N_{\mathrm{pipeline}} \ge \frac{D_{\mathrm{firm}}}{(1-m)^{w}} \cdot \frac{s}{\alpha}
\]

Fail closed means cut offtake first. Do not sell the breed floor to fill an order.

`firm_max` on this helper is \(\alpha\) times surplus above the floor. The older `firm_surplus` helper is different: it is surplus of the countable stock \(\alpha N\) above the floor, and `cap_offtake_change` still uses that view.

When a forward breeder need \(N_{\mathrm{req}}\) is passed, `safe_sell_limit` also applies `cull_cap_deterministic`: survivors of the headcount you keep, compounded at \((1-m)\) per week for the lead, must cover \(N_{\mathrm{req}} \times s\). That call uses \(\epsilon = 0\) so \(s\) is not stacked on the report’s \(\epsilon = 0.01\). The Monte Carlo governor is still TBD. This proxy fails closed.

`birds_now_for_demand` inverts the pipeline line. Default lead is 10 weeks. `margin_backsolve` divides a target dollar margin by the margin per unit. The $3k page that calls it is [`../../economics/MARGIN_3K_BACKSOLVE.md`](../../economics/MARGIN_3K_BACKSOLVE.md).

## 4. Unified prepaid (all sellable goods)

Same identity as `research/quail` (`fair_prepaid_forward_per_lb`), for every species good \(s\):

\[
E[P_s(T)] = E[P_{s0}]\,(1 + r_{\mathrm{inf}})^{T}
\]

\[
F_{\mathrm{prelim},s} = 0.9 \cdot \frac{E[P_s(T)]}{(1 + r_{\mathrm{tbill}})^{T}}
\]

\[
F_{\mathrm{final},s} = F_{\mathrm{prelim},s} + c_{\mathrm{transport}}(\mathrm{location})
\]

Defaults: \(r_{\mathrm{inf}} = 0.027\) (BLS CPI-U Food, August 2026), \(r_{\mathrm{tbill}} = 0.0401\) (3-month Treasury bill, FRED series DTB3, secondary-market discount basis, observation 2026-09-22). https://fred.stlouisfed.org/series/DTB3 Rod locked this quote for the prepaid discount. The H.15 3-month constant maturity the same week is 4.24% (2026-09-25) and is not \(r_{\mathrm{tbill}}\). Transport defaults to 0. Firm quantity is the reliability-quantile surplus (section 3), priced at \(F_{\mathrm{prelim}}\) or at \(F_{\mathrm{final}}\) when a location transport rate is set.

**Legacy:** the external `worm_forward_book` flat 33% discount is not used for new planning and is not ported here. Migration is a note only. New documents use \(F_{\mathrm{prelim}}\).

## 5. Gate

Stage 1 worms only. Synergy math does not open the next stage.
