# Research / quail (Stage 4 planning)

**Stage gate:** Quail is later in the cascade. **Stage 1 = worms** is still source of record for live spend. Do not open quail capex until Stage-1 gate in `biology/CASCADE.md`.

| File | Role |
|------|------|
| `SPEC.md` | Parameters, formulas, sustain rule, fair prepaid |
| `RESEARCH.md` | Sourced vs assumed numbers + URLs |
| `quail_model.py` | Jumbo Coturnix + Grit kit `U`; `production_rate`, `t_ready`, fair forward |
| `run_example.py` | CLI sample |
| `results/` | Sample run outputs |

```bash
python run_example.py --y 5 --z 15 --U 1 --c-bar 2 --weeks 40
```

Primary API: production rate vs average consumption \(\bar{c}\). Secondary: fair prepaid $/lb and `kits_needed`.

The flock-today chart and the $2,000 flock chart use this prepaid and are in [`../plots/README.md`](../plots/README.md). They are planning pictures, not a purchase.

Fair prepaid inflates the foodservice spot at BLS CPI-U Food **2.7%** (August 2026), discounts the deposit at the **3-month T-bill 4.01%** (FRED DTB3, 2026-09-22), then applies fairness **0.9**. Transport is added after that and defaults to $0/lb. Pass `r_inf=0` for the pre-inflation prelim. The same identity for every cascade good, plus breed floors and shock guards, is in [`../synergy/SPEC.md`](../synergy/SPEC.md).

On the flock-today chart, that \(F_{\mathrm{prelim}}\) is the lower panel and \(T = n/52\). For 40 lb at week 26 the flock on hand is 204 birds (51 males and 153 females at 1:3) and the prepaid is still close to 0.9 times the foodservice spot. A shorter week needs a much larger flock. A later week adds pipeline mortality and discounts the deposit. That 204-bird count assumes the hens stay in peak lay. They do not.

## Peak-lay cull

A jumbo Coturnix hen is in a peak slot from about week 14 through week 33 of age. Onset at 6–8 weeks and the week-15 peak are sourced. The straight-line decline, and the 0.85 slot gate, are assumptions. See [`SPEC.md`](SPEC.md) and [`RESEARCH.md`](RESEARCH.md).

Out-of-peak hens are culled to meat. The cull never takes the flock under the Ne floor, 17 males and 51 females, and the breeders stay 1 male : 3 females. `flock_today` adds the pullet pipeline that keeps those 51 hen slots in peak. `cascade_growth_today()` is the $10,000 / 1-year comparison: \(N_{\mathrm{today}}\) with that pipeline, and without it. Spent hens are not booked as the delivery. The chart is [`../plots/peak_cull_layers.png`](../plots/peak_cull_layers.png).

```bash
python3 research/quail/test_peak_cull.py
python3 research/ops-dashboard/delivery.py
cd research && python3 decision_plots.py
```

Notes: [`RESEARCH.md`](RESEARCH.md). Stage 4 planning. Not a purchase. Stage 1 worms remain the only spend.
