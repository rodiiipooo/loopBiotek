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
| `birds_per_lb_vs_month.png` | A 40 lb order needs about 172 starters at month 2 and about 84 once offspring can be dressed. Pounds are sex- and age-specific. |
| `delivery_split_vs_soon.png` | All 30 lb in month 3 needs about 156 starters. 15 lb locked in month 3 plus 15 lb that can wait needs about 128. |
| `quail_egg_rate_vs_age.png` | Eggs per hen are zero before maturity, peak at week 12 (ASSUMPTION), then decline. |
| `quail_survival_vs_age.png` | ASSUMPTION survival, plus male and female dressed pounds by age. |
| `ne_vs_sale.png` | Selling a 1:3 quail flock until Ne would fall below 50 is refused. |
| `quail_inbreeding_leakage.png` | A higher share of full-sib offspring cuts hatch, fertility, and viability on the Sato slopes. The extra reject rate is an assumption. |
| `quail_n0_for_2000.png` | About 780 starters and 25 kits hold $2,000 a month from month 2. About 268 starters and 4 kits cover $1,000 at month 2. The old 2,872 figure used a flat 0.585 lb bird. |
| `quail_feed_vs_herd.png` | Worm and plant feed follow the heavy herd. A short ration fails closed. |
| `worm_p10_sell_room.png` | Worm P10 room grows with the starting herd and with a later month. |

The ops screen shows this gallery under **Decision charts**.
