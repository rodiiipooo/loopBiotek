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

## 4. Unified prepaid (all sellable goods)

Same identity as `research/quail` (`fair_prepaid_forward_per_lb`), for every species good \(s\):

\[
E[P_s(T)] = E[P_{s0}]\,(1 + r_{\mathrm{inf}})^{T}
\]

\[
F_{\mathrm{prelim},s} = 0.9 \cdot \frac{E[P_s(T)]}{(1 + r_{\mathrm{prime}})^{T}}
\]

\[
F_{\mathrm{final},s} = F_{\mathrm{prelim},s} + c_{\mathrm{transport}}(\mathrm{location})
\]

Defaults: \(r_{\mathrm{inf}} = 0.027\) (BLS CPI-U Food, August 2026), \(r_{\mathrm{prime}} = 0.07\) (Fed H.15, 2026-09-24). Transport defaults to 0. Firm quantity is the reliability-quantile surplus (section 3), priced at \(F_{\mathrm{prelim}}\) or at \(F_{\mathrm{final}}\) when a location transport rate is set.

**Legacy:** the external `worm_forward_book` flat 33% discount is not used for new planning and is not ported here. Migration is a note only. New documents use \(F_{\mathrm{prelim}}\).

## 5. Gate

Stage 1 worms only. Synergy math does not open the next stage.

## 6. Cascade sale

Given the present herd and its sex counts, selling \(n\) units of species \(S\) at month \(t\) returns an impact report. Code: `cascade_impact.py`. The ops screen posts the same report to `/api/cascade-impact`.

Quail sales are split in the current sex ratio:

\[
n_m = n \frac{N_m}{N_m+N_f}, \quad n_f = n \frac{N_f}{N_m+N_f}
\]

The sale is refused when the remaining males or females fall under the Ne floor (17 and 51 at 1 male : 3 females), when Ne would fall below 50, or when \(n\) is larger than the P10 headroom at month \(t\). P10 headroom is the largest harvest that still leaves the breed floor standing in 90% of the ops-screen futures. Room left is that headroom after the sale is on the book.

Feed knock-on, per remaining bird, is the quail planning intake (ASSUMPTION, same as `quail_income.py`):

\[
\text{worm kg/month} = N \times 22\,\text{g/day} \times 0.30 \times (365.25/12) / 1000
\]

Plant kilograms use the 0.70 share. Worm offtake stops at the worm breed floor. A ration that would cross that floor fails closed. Breeders are not raided.

Worm surplus from a quail sale:

\[
Y(t) = \text{P10 worms with the sale} - \text{P10 worms if the birds stay}
\]

in pounds (1,000 worms per pound). Sold birds leave at the start of month \(t\), so they do not eat that month. The uneaten worms stay in the bin and keep the 13-week doubling stand-in until quail growth eats both paths back to the floor, or until the recommended schedule takes \(Y(t)\) as product.

If no product offtake is taken, two Stage 5 stubs apply. Both are labeled ASSUMPTION. Neither is a measured ration or a yield.

- Density: a P10 worm stock above 85% of the carrying cap is a warning. The cap is 16 times the larger of the present herd and the floor.
- Fish: a named fish count can be offered the excess worms. Intake stub is 12 g/fish/day, 20% worms and 80% plant. Growth index is \(\min(1.25,\ 1 + 0.15 \times \min(Y, \text{base})/\text{base})\). Extra plant demand is the base plant ration times that index minus one. If that extra demand makes the plant gap worse than holding the birds, the sale is refused.
- Plants: monthly production is set equal to the opening herd's heavy plant demand. The cushion starts at \(B_s = 2\) weeks of that production. Quail growth outruns this stub on both paths. The long-term lever, not modeled, is aquaponic water composition, nutrient distribution, and nutrient mix.

The recommended schedule puts the quail sale in month \(t\) only, names the further P10 monthly bird room after that sale, and lists the freed worm pounds as product offtake so they are not silently eaten later.

Sample, 200 paths, seed 20260926. Present herd 24 males and 72 females, 250,000 worms, floor 16,500. Sell 16 birds at month 4 (4 males and 12 females).

| | |
| --- | --- |
| Status | warn (plant stub cannot track quail growth; the sale shrinks that gap) |
| Remaining | 20 males + 60 females, Ne = 60 |
| P10 room at month 4 | 67.35 birds before the sale, 51.35 after |
| Worm excess at month 4 | 7.453 lb |
| Worm excess peak | 104.837 lb in month 9, then the P10 bins are back at the 16,500 floor by month 11 |
| Feed change in month 4 | −3.12 kg worms, −7.30 kg plant |
| Plant gap, hold vs sale | 499.31 kg vs 404.0 kg short of the stub cushion |
| Stage 5 fish = 40 | growth index 1.15 at month 4, +1.753 kg plant that month; gap 416.27 kg, still better than holding the birds |

Selling 40 birds from the same flock is refused (remaining sex counts fall under 17 and 51). A 320-bird flock on 16,500 worms is refused because worm feed would take the breeding floor. Chart: [`../plots/cascade_sale_vs_hold.png`](../plots/cascade_sale_vs_hold.png).
