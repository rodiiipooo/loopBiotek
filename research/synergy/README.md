# Synergy buffers (planning only)

Breed floors, waste ceilings, offtake caps, and one prepaid formula for every cascade species. Stage 1 worms stay the spend source of record. This package does not open Stage 2–5 spend.

| File | Role |
|------|------|
| `SPEC.md` | Floor, culling governor, safe-sell control law, shock guards, unified \(F_{\mathrm{prelim}}\) |
| `RESEARCH.md` | SOURCED vs ASSUMPTION |
| `circular_buffers.py` | Pure helpers (`safe_sell_limit`, `birds_now_for_demand`, `margin_backsolve`) and a smoke run |
| `results/` | `circular_buffers_smoke.json` |

```bash
cd research/synergy
python circular_buffers.py
```

Quail’s own rate model stays in [`../quail/`](../quail/README.md). The prepaid identity is the same one.

Sell limit, in order: surplus above the breed floor, then firm offtake at most \(\alpha\) times that surplus, then a pipeline gross-up \(N_{\mathrm{pipeline}} \ge D_{\mathrm{firm}}/(1-m)^{w}\cdot s/\alpha\). If those disagree with an order, cut the offtake. The $3,000/mo sketch that calls `margin_backsolve` is [`../../economics/MARGIN_3K_BACKSOLVE.md`](../../economics/MARGIN_3K_BACKSOLVE.md). It does not open Stage 2–5 spend.

The quail feed chart [`../plots/quail_feed_vs_herd.png`](../plots/quail_feed_vs_herd.png) uses the 2-week feed buffer from this spec. A ration that misses the heavy herd plus that buffer fails closed. The intake grams are an assumption, not a measured diet.
