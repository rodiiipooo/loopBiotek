# Community ops forward dashboard

This screen is the operations forward book (promises, safe-to-sell, and the income check). It is not the CAD tile viewer.

A local screen for tracking prepaid promises and how much of the herd is still safe to sell. It runs on a laptop with Python only. Nothing here is a cloud service, and nothing here approves spending beyond Stage 1 worms. Quail on the screen is a planning stand-in.

## Laptop setup (5 min)

You need Git and Python 3.10 or newer. No other install.

**macOS or Linux (bash)**

```bash
git clone https://github.com/rodiiipooo/loopBiotek.git
cd loopBiotek/research/ops-dashboard
python3 --version
./run.sh
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/rodiiipooo/loopBiotek.git
cd loopBiotek\research\ops-dashboard
py -3 --version
.\run.bat
```

Open http://127.0.0.1:8765 in a browser. The first page already has a sample herd (16,500 worms, P10 harsh case, month 12) and a draft promise named “Demo buyer — delete me”.

Stop the program with Ctrl-C in that same terminal.

The book is created on first run at `research/ops-dashboard/data/forwards.sqlite` (next to this README). That file is not part of git.

If `python3` is not the command on your machine, use `python` instead. `./run.sh` and `run.bat` try `python3`, then `python`. On Windows, `py -3` is tried first.

### Optional isolated environment

You do not need this. `requirements.txt` lists no third-party packages, so the install step is a no-op. Use it only if you want a private Python environment.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Leave the venv with `deactivate`.

### Reach other devices on your network

The default listen address is this machine only (`127.0.0.1`). To also accept connections from your LAN, set `OPS_HOST`:

```bash
OPS_HOST=0.0.0.0 python3 app.py
```

```powershell
$env:OPS_HOST = "0.0.0.0"
python app.py
```

From another device, open `http://<this-computer-ip>:8765`. There is no login. Do not forward this port to the public internet.

Change the port with `OPS_PORT` (default `8765`).

### Use the screen

- **Starting herd, planned start, safety reserve, harsh-case percentile, delivery month.** Edit the herd card, then click **Update the safe amount**. The percentile defaults to **10**. That is Safe to sell (P10): the amount you can still deliver in the harsh futures. Only 10% of scenarios are this low or lower. P90 is not used.
- **Promises.** Add a buyer, quantity, and delivery month. Leave price blank to use the fair prepaid price. Save. A promise that would cut into the breeding herd is refused.
- **Target income.** Set dollars and “by month”, then click **Check the target**. The answer is the safe monthly cap, whether that cap reaches the dollars, and what larger herd or later month would.
- **Delivery structure.** For quail, enter pounds and candidate months (for example `3, 6, 12`), then click **Plan the deliveries**. The plan uses the same P10 harsh case as Safe to sell. Birds per pound fall as the month gets later. The starting herd never drops below the 68-bird breeding floor. A sooner lump is recommended only when a later month cannot take the order. This is planning, not a purchase.
- **$2,000 a month from month 2.** `python3 quail_income.py` prints the starting flock that can hold that prepaid income on the P10 tail through month 24, plus the worm and plant feed that heavy herd needs. The plots land in `results/`. Planning only. It does not buy birds or feed.
- **Decision charts.** The screen shows the P10 pictures: starters versus month, split versus all-soon, the $2,000 flock and its feed, the Ne refuse line, quail leakage, worm sell room, and the cascade sale (hold versus sell). Files and the regenerate command are in [`../plots/README.md`](../plots/README.md).
- **Cascade sale.** The card reads `POST /api/cascade-impact`: remaining herd, Ne, P10 room, feed change, and worm excess after selling birds or worms. Fish and plants on that card are Stage 5 stubs.
- **Quail.** The species menu switches to a labeled planning stub. It does not approve buying birds or kits.

### Reset the forward book

Stop the program (Ctrl-C). Delete the database file, then start again. The sample herd and demo promise come back.

macOS or Linux:

```bash
rm -f data/forwards.sqlite
./run.sh
```

Windows PowerShell:

```powershell
Remove-Item -Force data\forwards.sqlite
.\run.bat
```

To keep your herd numbers and only remove promises, delete the rows in the table on the screen instead.

## What “Safe to sell (P10)” means

The screen runs 2,000 seeded futures of herd growth. **Safe to sell (P10)** is the amount you can still deliver in the harsh futures. Only 10% of scenarios are this low or lower. You plan as if outcomes are bad. P90, the good-growth case, is not the default and the screen will not take a percentile above 50. Draft and promised rows are already subtracted. If a new promise would miss the P10 bar, the save is refused and the screen says the sale is blocked.

Food inflation **2.7%** (BLS CPI-U Food, August 2026), prime **7%**, and fairness **0.9** are the prepaid defaults. The formula is on the screen and in `SPEC.md`.

Worm growth here is a planning stand-in that ships with this folder. It does not replace whatever Stage-1 records you keep outside this screen. Quail numbers are marked **ASSUMPTION**.

## Check the sample from the terminal

```bash
python3 smoke.py
```

```powershell
py -3 smoke.py
```

That writes `results/reverse_smoke.json` for 16,500 worms, $2,000 by month 12, P10, and checks that a saved promise changes the remaining room and that an oversized promise is blocked. It uses a temporary database, not `data/forwards.sqlite`.
