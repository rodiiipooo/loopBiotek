# Community ops forward dashboard

Local screen for the person watching the herd. It keeps a book of prepaid promises, shows how much is still safe to sell, and checks whether a dollar target can be met without using breeding animals.

Stage 1 worms are the only active spend. This app does not approve Stage 2–5 purchases. Quail on the screen is a planning stand-in.

## Run

From this directory:

```bash
python3 app.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Stop with Ctrl-C.

The book is a SQLite file at `research/ops-dashboard/data/forwards.sqlite` (created on first save). Override the folder with `OPS_DATA_DIR`.

On a Minisforum or other box, bind the tailnet only if you want other devices to reach it:

```bash
OPS_HOST=0.0.0.0 OPS_PORT=8765 python3 app.py
```

Then use the machine’s Tailscale address and port 8765. There is no login in v1. Do not expose the port on the public internet.

Install, if the box does not already have the libraries:

```bash
python3 -m pip install -r requirements.txt
```

## What “Safe to sell (P90)” means

The screen runs 2,000 seeded futures of herd growth. **Safe to sell (P90)** is the amount you can promise for the delivery month and still have the breeding herd in at least 90 of those 100 futures. It is the cautious tail, not the middle outcome. Draft and promised rows are already subtracted. If a new promise would miss that bar, the save is refused and the screen says the sale is blocked.

Food inflation **2.7%** (BLS CPI-U Food, August 2026), prime **7%**, and fairness **0.9** are the prepaid defaults. The formula is on the screen and in `SPEC.md`.

Worm growth here is a planning stand-in. The Stage-1 Monte Carlo stays outside this repo at `/workspace/worm-revenue-model/` and is not replaced by this app.

## Check the sample

```bash
python3 smoke.py
```

That writes `results/reverse_smoke.json` for 16,500 worms, $2,000 by month 12, 90% reliability, and checks that a saved promise changes the remaining room and that an oversized promise is blocked.
