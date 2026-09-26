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
| `birds_per_lb_vs_month.png` | A shorter delivery month needs more starters per pound, and a larger N0 for a 40 lb order, until the 68-bird floor binds. |
| `delivery_split_vs_soon.png` | The same 30 lb book needs fewer starters when the flexible 15 lb waits until month 12 instead of shipping in month 3. |
| `ne_vs_sale.png` | Selling a 1:3 quail flock until Ne would fall below 50 is refused. |
| `quail_inbreeding_leakage.png` | A higher share of full-sib offspring cuts hatch, fertility, and viability on the Sato slopes. The extra reject rate is an assumption. |
| `quail_n0_for_2000.png` | About 2,872 starters hold $2,000 a month of P10 meat from month 2 through month 24. |
| `quail_feed_vs_herd.png` | Worm and plant feed follow the heavy herd. A short ration fails closed. |
| `worm_p10_sell_room.png` | Worm P10 room grows with the starting herd and with a later month. |

The ops screen shows this gallery under **Decision charts**.
