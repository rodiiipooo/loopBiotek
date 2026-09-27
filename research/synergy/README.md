# Synergy buffers (planning only)

Breed floors, waste ceilings, offtake caps, and one prepaid formula for every cascade species. Stage 1 worms stay the spend source of record. This package does not open Stage 2–5 spend.

| File | Role |
|------|------|
| `SPEC.md` | Floor, culling governor, shock guards, unified \(F_{\mathrm{prelim}}\) |
| `RESEARCH.md` | SOURCED vs ASSUMPTION |
| `circular_buffers.py` | Pure helpers and a smoke run |
| `cascade_impact.py` | Sale of one species: herd, Ne, P10 room, feed, worm excess |
| `results/` | `circular_buffers_smoke.json`, `cascade_impact_smoke.json` |

```bash
cd research/synergy
python circular_buffers.py
python cascade_impact.py
```

Quail’s own rate model stays in [`../quail/`](../quail/README.md). The prepaid identity is the same one.

The quail feed chart [`../plots/quail_feed_vs_herd.png`](../plots/quail_feed_vs_herd.png) uses the 2-week feed buffer from this spec. A ration that misses the heavy herd plus that buffer fails closed. The intake grams are an assumption, not a measured diet.

[`cascade_impact.py`](cascade_impact.py) is the cross-species sale. Selling 16 quail at month 4 from a 24/72 flock on 250,000 worms leaves about 7.5 lb of extra worms that month and about 105 lb by month 9, on the P10 tail. The picture is [`../plots/cascade_sale_vs_hold.png`](../plots/cascade_sale_vs_hold.png). Fish and plants in that report are Stage 5 stubs.
