# Reproduction math (planning only)

Quail (Stage 4) and aquaponics fish (Stage 5). Strict mode refuses inbred matings. Leakage mode haircuts hatch, growth, fecundity, and reject rate when some offspring are inbred anyway. Surplus sales have to leave both the synergy breed floor and an effective population of at least 50.

This does not approve buying birds or fish. Stage 1 worms remain the only active spend.

| File | Role |
|------|------|
| `SPEC.md` | Formulas, defaults, source tags |
| `RESEARCH.md` | Citations |
| `reproduction.py` | Helpers and a smoke run |
| `results/` | `reproduction_smoke.json` |

```bash
cd research/genetics
python3 reproduction.py
```

Ops forwards stay in [`../ops-dashboard/README.md`](../ops-dashboard/README.md). That screen is not this math, and it is not the CAD tile viewer.

Two charts in [`../plots/`](../plots/README.md): `ne_vs_sale.png` shows the sale that drops Ne below 50, and `quail_inbreeding_leakage.png` shows the Sato haircut as more offspring are full sibs. Regenerate with `python3 decision_plots.py` from `research/`.
