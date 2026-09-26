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

Primary API: production rate vs average consumption \(\bar{c}\). Secondary: fair forward $/lb (prime-discounted prepaid) and `kits_needed`.
