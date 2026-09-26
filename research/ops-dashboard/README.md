# Community ops forward dashboard

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

Open http://127.0.0.1:8765 in a browser. The first page already has a sample herd (16,500 worms, 90% reliability, month 12) and a draft promise named “Demo buyer — delete me”.

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

- **Starting herd, planned start, safety reserve, how sure (percent), delivery month.** Edit the herd card, then click **Update the safe amount**. “How sure” at 90 means Safe to sell (P90): the breeding herd is still there in at least 90 of 100 simulated futures.
- **Promises.** Add a buyer, quantity, and delivery month. Leave price blank to use the fair prepaid price. Save. A promise that would cut into the breeding herd is refused.
- **Target income.** Set dollars and “by month”, then click **Check the target**. The answer is the safe monthly cap, whether that cap reaches the dollars, and what larger herd or later month would.
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

## What “Safe to sell (P90)” means

The screen runs 2,000 seeded futures of herd growth. **Safe to sell (P90)** is the amount you can promise for the delivery month and still have the breeding herd in at least 90 of those 100 futures. It is the cautious tail, not the middle outcome. Draft and promised rows are already subtracted. If a new promise would miss that bar, the save is refused and the screen says the sale is blocked.

Food inflation **2.7%** (BLS CPI-U Food, August 2026), prime **7%**, and fairness **0.9** are the prepaid defaults. The formula is on the screen and in `SPEC.md`.

Worm growth here is a planning stand-in that ships with this folder. It does not replace whatever Stage-1 records you keep outside this screen. Quail numbers are marked **ASSUMPTION**.

## Check the sample from the terminal

```bash
python3 smoke.py
```

```powershell
py -3 smoke.py
```

That writes `results/reverse_smoke.json` for 16,500 worms, $2,000 by month 12, 90% reliability, and checks that a saved promise changes the remaining room and that an oversized promise is blocked. It uses a temporary database, not `data/forwards.sqlite`.
