# Decision plots

Pictures for the choices a person applying the planning models has to make. Quail and worm growth curves are **ASSUMPTION**. Wright's Ne and the Sato inbreeding slopes are formulas and measurements, and each chart says which is which. The default tail is **P10**. Stage 1 worms remain the only spend. Quail charts are Stage 4 planning. Nothing here buys birds, feed, or kits.

Regenerate (matplotlib is used only for these pictures; the ops screen does not import it):

```bash
python3 -m pip install matplotlib
cd research
python3 decision_plots.py
```

| Plot | What it teaches |
|------|-----------------|
| `birds_per_lb_vs_month.png` | Flock on hand today for a 40 lb surplus-only delivery. Week 4 needs 1,184 birds. Week 26 needs 204 (51 males and 153 females at 1:3). Later weeks need more because of pipeline mortality. Lower panel: \(F_{\mathrm{prelim}}\) at the 4.01% 3-month bill. |
| `delivery_split_vs_soon.png` | The same 30 lb book needs fewer starters when the flexible 15 lb waits until month 12 instead of shipping in month 3. |
| `ne_vs_sale.png` | Selling a 1:3 quail flock until Ne would fall below 50 is refused. |
| `quail_inbreeding_leakage.png` | A higher share of full-sib offspring cuts hatch, fertility, and viability on the Sato slopes. The extra reject rate is an assumption. |
| `quail_n0_for_2000.png` | About 2,813 starters hold $2,000 a month of P10 meat from month 2 through month 24. |
| `quail_feed_vs_herd.png` | Worm and plant feed follow the heavy herd. A short ration fails closed. |
| `worm_p10_sell_room.png` | Worm P10 room grows with the starting herd and with a later month. |

The ops screen shows this gallery under **Decision charts**.

### 40 lb quail order: flock on hand today

`birds_per_lb_vs_month.png` answers a present-flock question. If a buyer at week \(n\) purchases \(x\) pounds of dressed quail (default \(x = 40\)), what population must already be here so the sale comes from surplus only and a self-sustaining flock is still growing. The filename is unchanged so the ops gallery URL stays put.

The upper panel stacks males and females and draws total \(N_{\mathrm{today}}\). Sex is the jumbo Coturnix practice already in the quail SPEC: **1 male : 3 females**. That ratio puts as many hens on eggs as the mating practice allows. Breeders are not sold to fill the order. `min_breeders_for_demand` is not the sizer: that kit inverse can cull above a cage cap.

\(N_{\mathrm{today}}\) is the larger of two counts, then snapped up to an exact 1:3 flock:

- the P10 herd for \(x \times 1.15 / 0.9\) pounds at the delivery month that contains week \(n\) (firm fraction \(\alpha = 0.9\), cull governor \(s = 1.15\));
- the Ne nucleus (17 males and 51 females) grossed up for weekly mortality, plus `birds_now_for_demand` for the dressed headcount over the lead weeks.

`safe_sell_limit` must still allow the headcount above the genetics floor. A plan that would raid breeders fails closed.

The lower panel is the locked prepaid from [`../synergy/SPEC.md`](../synergy/SPEC.md) and [`../quail/SPEC.md`](../quail/SPEC.md), with \(T = n/52\):

\[
E[P(T)] = E[P_0]\,(1 + r_{\mathrm{inf}})^{T},\quad F_{\mathrm{prelim}} = 0.9 \cdot \frac{E[P(T)]}{(1 + r_{\mathrm{tbill}})^{T}}
\]

Defaults are \(r_{\mathrm{inf}} = 0.027\), \(r_{\mathrm{tbill}} = 0.0401\) (FRED DTB3, 3-month secondary-market bill, 2026-09-22), fairness \(0.9\). The H.15 3-month constant maturity of 4.24% (2026-09-25) is a different quote and is not this rate. \(E[P_0]\) is the quail foodservice mean already in the model (about $12.46/lb).

For \(x = 40\) lb, week 4 needs 1,184 birds (P10 binds). Week 26, about six months, is the knee: **204 birds, 51 males and 153 females**, and \(F_{\mathrm{prelim}}\) is still about $11.15/lb, close to 0.9 times spot. A shorter lead needs a much larger flock. A longer lead raises today's pipeline because of mortality and discounts the prepaid further. Stage 4 planning only. Stage 1 worms remain the only spend.
