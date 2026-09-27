# $3,000/mo contribution margin — backsolve

**PLANNING only.** Every figure below is tagged. This page does not authorize Stage 2–5 CapEx, does not place a forward sale, and does not harvest a breed floor. Stage 1 worms remain the only active spend until the gate in [`../biology/CASCADE.md`](../biology/CASCADE.md) is cleared.

Helpers: `safe_sell_limit`, `birds_now_for_demand`, `margin_backsolve` in [`../research/synergy/circular_buffers.py`](../research/synergy/circular_buffers.py). Control law: [`../research/synergy/SPEC.md`](../research/synergy/SPEC.md).

\[
H_{\max}=\mathrm{Surplus},\quad D_{\mathrm{firm}}\le\alpha\cdot H_{\max},\quad N_{\mathrm{pipeline}}\ge\frac{D_{\mathrm{firm}}}{(1-m)^{w}}\cdot\frac{s}{\alpha}
\]

Fail closed = cut offtake first. \(\alpha=0.9\), \(m=0.01\), \(s=1.15\), \(\epsilon=0.01\) (Monte Carlo governor still TBD).

## Unit margins

| Stream | Price | Variable cost | Contribution | Tag |
|--------|------:|-------------:|-------------:|-----|
| Quail, fair \(F_{\mathrm{prelim}}\) | **$10.99/lb** | **$3.169/lb** | **$7.82/lb** (~**$4.57/bird** at dress 0.585 lb) | Price DERIVED; cost PLANNING |
| Quail, Rod compete | **$3.60/bird** | $3.169/lb → ~$1.85/bird | **~$1.75/bird** (~38% of fair) | PLANNING, aggressive |
| Worms | **$0.03/worm** | opex in the margin ratio below | see path C | PLANNING |
| Insects, greens, algae, fish | — | — | **not locked** | do not size CapEx |

Quail price: fair prepaid at \(T=0.5\) yr is $10.9893/lb in `research/synergy` smoke and `research/quail` (`F_prelim`). This page rounds that to $10.99/lb. Dress weight 0.585 lb/bird is the quail model default.

Quail variable cost $3.169/lb is a **PLANNING** lock named from `research/quail/results/margin_2k_starter_impact.json`. That file is not in this checkout, so the lock is recorded here and is not re-derived. Contribution: \(10.99-3.169=7.821\) → **$7.82/lb**. Per bird: \(7.82\times 0.585=4.57\).

Compete case uses the same variable cost: \(3.60-3.169\times 0.585=1.75\) per bird, \(1.75/4.57\approx 38\%\) of the fair bird margin. Prefer fair \(F_{\mathrm{prelim}}\) for capacity math.

`margin_backsolve(3000, 7.82, "lb")` → **383.6 lb/mo**, reported below as **~384 lb/mo**. `margin_backsolve(3000, 4.57, "bird")` → **~656 birds/mo**.

## Paths

### A — quail only, fair \(F_{\mathrm{prelim}}\)

| Item | Planning figure |
|------|----------------:|
| Contribution | $3,000/mo |
| Dressed meat | ~384 lb/mo |
| Birds sold | ~656 birds/mo |
| Kits | ~6 Grit Quail Professional Kits |
| Breeders | ~90♀ / ~30♂ |
| Pipeline | ≥ **1.41×** the next firm delivery over ~70 days |

**ASSUMPTION scale, not a purchase.** Six kits × 45 jumbo breeder slots = 270 heads, so a 120-bird set at the model’s 1♂:3♀ ratio fits. A one-kit quail sample is often brooder or grow-out bound after ramp; ~384 lb/mo (~88 lb/week) is a few kits, and **6** is the envelope used here. Kit price in `research/quail/SPEC.md` is not spend authority.

Pipeline: `birds_now_for_demand` at the defaults (\(w=10\) weeks ≈ 70 days) returns `pipeline_multiple` ≈ **1.413** (smoke key `birds_now_for_demand`). For 656 firm birds that is ~930 birds on hand before that delivery. Use the helper when a round ~1.35× sketch and this compound disagree.

### B — quail only, $3.60/bird

`margin_backsolve(3000, 1.75, "bird")` → **~1,714 birds/mo**, about **16 kits** if path A’s 6 kits scale with bird count (\(1714/656\times 6\approx 16\)).

**Discourage this path for capacity math.** The price is aggressive (~38% of fair contribution). Size buildings and flocks on path A. This row does not authorize kits.

### C — worms only

**PLANNING**, mirrored from the external worm ROI pattern (`/workspace/worm-revenue-model/`, not vendored; pointer in [`README.md`](./README.md)). This checkout does not contain that model.

| Step | Figure |
|------|-------:|
| Unit price | $0.03/worm |
| At ~$2,000/mo revenue | ~$1,644 cash margin after opex |
| Margin ratio | \(1644/2000=0.822\) |
| Revenue for $3,000 margin | \(3000/0.822\approx\$3{,}650\) |
| Sellable surplus | \(3650/0.03\approx 122{,}000\) worms/mo |
| Herd floor | **~690,000** |

Never harvest until the herd is above the floor. Monthly firm offtake is at most \(\alpha\) times surplus above ~690k (α = 0.9 stands in for the P10 firm book). Do not sell the median herd.

### D — mix (fair quail / worms)

Splits of the **$3,000 contribution**. Quail birds use $4.57/bird. Worm surplus and herd scale in proportion to path C (122k surplus and 690k floor at $3,000).

| Quail / worms | Quail margin | lb/mo | birds/mo | Worm margin | Worm revenue | Surplus / mo | Herd floor |
|---------------|-------------:|------:|---------:|------------:|-------------:|-------------:|-----------:|
| 70 / 30 | $2,100 | ~269 | ~459 | $900 | ~$1,095 | ~36.5k | ~207k |
| 50 / 50 | $1,500 | ~192 | ~328 | $1,500 | ~$1,825 | ~60.8k | ~345k |
| 30 / 70 | $900 | ~115 | ~197 | $2,100 | ~$2,555 | ~85.2k | ~483k |

Insects, greens, algae, and fish stay out of this table. Their margins are not locked.

## Self-sustain

Operating rules for every path. Math lives in [`../research/synergy/SPEC.md`](../research/synergy/SPEC.md); this page does not replace it.

- Breed floor \(N_{\mathrm{floor}}=\max(N0,N_{\mathrm{start}},N_{\mathrm{safety}})\). Sell surplus only.
- Firm book: \(D_{\mathrm{firm}}\le\alpha\cdot H_{\max}\) with \(\alpha=0.9\). That is the deterministic stand-in for P10 surplus, not the median.
- Cull governor target \(\epsilon=0.01\). `safe_sell_limit` applies \(s=1.15\) through the deterministic cull-cap shape when a forward breeder need is passed. The draw-based governor is TBD.
- Feed buffer ≥ 2 weeks (synergy default \(B_s=2\), an **ASSUMPTION**). Product buffer ≥ 1 week of firm delivery.
- Quail waste ceiling \(\phi\le 0.41\). Other species have no numeric ceiling until a source exists.
- Fail closed: cut offtake first. Do not raid breeders, and do not raid another species’ breeders, to fill an order.

## Stage gate

**Stage 1 worms are the only active spend.** Quail kit counts above are capacity arithmetic for a later stage. Quail CapEx stays closed until vermiculture revenue is at least $2k/mo, or a firm prepaid runway covers Stage-1 costs, and Rod clears the gate. No live trading, no P50 forward sale, no Stage 2–5 purchase follows from this page.
