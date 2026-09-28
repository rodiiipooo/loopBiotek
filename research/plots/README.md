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
| `birds_per_lb_vs_month.png` | Upper panel: a shorter delivery month needs more starters per pound, and a larger N0 for a 40 lb order, until the 68-bird floor binds. Lower panel: locked prepaid \(F_{\mathrm{prelim}}\) at that month. |
| `delivery_split_vs_soon.png` | The same 30 lb book needs fewer starters when the flexible 15 lb waits until month 12 instead of shipping in month 3. |
| `ne_vs_sale.png` | Selling a 1:3 quail flock until Ne would fall below 50 is refused. |
| `quail_inbreeding_leakage.png` | A higher share of full-sib offspring cuts hatch, fertility, and viability on the Sato slopes. The extra reject rate is an assumption. |
| `quail_n0_for_2000.png` | About 2,872 starters hold $2,000 a month of P10 meat from month 2 through month 24. |
| `quail_feed_vs_herd.png` | Worm and plant feed follow the heavy herd. A short ration fails closed. |
| `worm_p10_sell_room.png` | Worm P10 room grows with the starting herd and with a later month. |

The ops screen shows this gallery under **Decision charts**.

### 40 lb quail order: when to book

`birds_per_lb_vs_month.png` keeps starters per pound and starting herd \(N_0\) on the upper panel. The lower panel is the same delivery month priced with the locked prepaid from [`../synergy/SPEC.md`](../synergy/SPEC.md) and [`../quail/SPEC.md`](../quail/SPEC.md):

\[
E[P(T)] = E[P_0]\,(1 + r_{\mathrm{inf}})^{T},\quad F_{\mathrm{prelim}} = 0.9 \cdot \frac{E[P(T)]}{(1 + r_{\mathrm{prime}})^{T}}
\]

\(T\) is the delivery month divided by 12. Defaults are \(r_{\mathrm{inf}} = 0.027\), \(r_{\mathrm{prime}} = 0.07\), fairness \(0.9\). \(E[P_0]\) is the quail foodservice mean already in the model (about $12.46/lb), not a new spot.

Around month 6 the P10 starter curve for 40 lb has flattened to about 2.5 birds per pound and about 100 starters, while \(F_{\mathrm{prelim}}\) is still close to the T = 0 prepaid (0.9 times spot). A very short delivery burns starters. A very long delivery only weakly improves starter efficiency — the 40 lb order is soon on the 68-bird floor — and the prepaid discounts further versus waiting. That month-6 neighborhood is the planning window for a firm forward. Stage 4 planning only. Stage 1 worms remain the only spend.
