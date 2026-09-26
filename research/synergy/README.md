# Synergy buffers (planning only)

Breed floors, waste ceilings, offtake caps, and one prepaid formula for every cascade species. Stage 1 worms stay the spend source of record. This package does not open Stage 2–5 spend.

| File | Role |
|------|------|
| `SPEC.md` | Floor, culling governor, shock guards, unified \(F_{\mathrm{prelim}}\) |
| `RESEARCH.md` | SOURCED vs ASSUMPTION |
| `circular_buffers.py` | Pure helpers and a smoke run |
| `results/` | `circular_buffers_smoke.json` |

```bash
cd research/synergy
python circular_buffers.py
```

Quail’s own rate model stays in [`../quail/`](../quail/README.md). The prepaid identity is the same one.

The quail feed chart [`../plots/quail_feed_vs_herd.png`](../plots/quail_feed_vs_herd.png) uses the 2-week feed buffer from this spec. A ration that misses the heavy herd plus that buffer fails closed. The intake grams are an assumption, not a measured diet.
