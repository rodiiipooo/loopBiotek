# Jumbo Coturnix production-rate screen (Stage 4 planning)

This file is a planning screen for cascade **Stage 4 (quail)**. It does not authorize equipment, bird, or feed purchases.

**Stage 1 worms remain the source of record for spend.** `biology/CASCADE.md` is the capital-order SoR. Quail spend stays closed until vermiculture revenue is at least $2k/month, or a firm prepaid forward runway covers Stage-1 costs, and Rod clears the gate.

## Decision variables

| Symbol | Sample | Meaning |
|--------|--------|---------|
| `y` | 5 | Founder males |
| `z` | 15 | Founder females (point-of-lay) |
| `U` | 1 | Quail Professional Kits |
| `c_bar` | 2 lb/week | Average dressed-meat consumption to sustain |
| `t` | days from first egg set | Clock |

The 5:15 male:female founder pen is the Padgett & Ivey (1959) fertility trial ratio (about 90% fertility). It is not a license to stock only that pen and ignore kit caps.

## Pipeline clock

Biological incubation for *Coturnix japonica* is **17 days** (Mississippi State University Extension). This screen uses the **21-day** operational setter/hatcher cycle already in `reference/loop_params.xlsx` (216 eggs over 21 days = 72 eggs/week per kit).

Jumbo table age is **56 days** (8 weeks), an assumption. Grit's own card moves birds to breeder cages after 6 weeks.

\[
\tau = 21 + 56 = 77 \text{ days} = 11 \text{ weeks}
\]

\[
t_{\mathrm{ready}}(c_{\bar}, y, z, U) =
\begin{cases}
\tau & \text{if } r_{\mathrm{prod}}(\tau, y, z, U) \ge c_{\bar} \\
\text{undefined} & \text{otherwise}
\end{cases}
\]

Sample: \(t_{\mathrm{ready}}(2, 5, 15, 1) = 77\).

## Production rate

Let weekly eggs from founders be \(z \times 6\) (6 eggs/hen/week, assumed, inside a high Coturnix lay rate). Fertility \(f(y,z) = 0.90\) when \(y/z \ge 1/5\), and scales down linearly below that. Hatch rate 0.80 and survival to process 0.95 are planning factors (assumed inside published ranges).

Incubator throughput per kit:

\[
\frac{216}{21/7} = 72 \text{ eggs/week}
\]

Housing throughput. These standing caps are **assumed** (the product page states 216 eggs/batch and the week-bands, not bird counts):

| Stage | Standing cap (assumed) | Published time in stage | Birds/week |
|-------|-----------------------:|-------------------------|----------:|
| Brooder | 150 | 4 weeks (Grit: first 4 weeks) | 37.5 |
| Grow-out, jumbo | 75 (= 5 layers × 15) | 2 weeks (Grit: weeks 4–6) | 37.5 |
| Breeders | 45 | held | egg supply, not meat throughput |

The two housing stages bind together at 37.5 birds/week/kit. Chick placement cannot exceed that.

\[
n(y,z,U) = \min\Big(
  \min(z \cdot 6,\ 72 U) \cdot f(y,z) \cdot 0.80 \cdot 0.95,\ 
  37.5\, U
\Big)
\]

Dressed weight is **assumed**: 16 oz live (top of advertised jumbo claims) times 0.77 ready-to-cook yield.

\[
r_{\mathrm{prod}}(t, y, z, U) =
\begin{cases}
0 & t < \tau \\
n(y,z,U) \times 0.77 & t \ge \tau
\end{cases}
\quad \text{lb/week}
\]

Sample: \(n(5,15,1) = 37.5\), so

\[
r_{\mathrm{prod}}(77, 5, 15, 1) = 37.5 \times 0.77 = 28.875 \approx 28.9 \text{ lb/week}
\]

Egg supply from 15 hens (90 eggs/week) is above the 72-egg incubator cap, and chicks after fertility, hatch, and survival are above 37.5, so **housing binds**. Extra hens do not raise the rate until another kit is added.

### Housing caveat (do not skip)

An 8-week finish at 37.5 birds/week needs about \(37.5 \times 8 = 300\) standing meat-bird spaces. Brooder 150 + grow-out 75 = 225. The kit as assumed **cannot** hold that full 8-week pipeline at 37.5 birds/week. Little's law on 225 spaces and an 8-week age is about 28 birds/week, not 37.5.

This screen still reports the Grit window rate (4-week brooder and 2-week grow-out, both 37.5 birds/week) because that is the figure that matches the worked example. Treat 28.9 lb/week as a **screening ceiling**, not a build quantity. Reconcile residence and finish age before any purchase.

## Sustain inventory

Average consumption is \(c_{\bar}\) lb/week. Required production to meet it, with no extra loss term:

\[
r_{\mathrm{required}}(c_{\bar}) = c_{\bar}
\]

Pounds that must already be in the freezer at day \(t\):

\[
I_{\mathrm{sustain}}(c_{\bar}, t, y, z, U) =
\begin{cases}
\infty & \text{if } r_{\mathrm{prod}}(\tau) < c_{\bar} \\
0 & \text{if } t \ge t_{\mathrm{ready}} \\
c_{\bar} \cdot (\tau - t) / 7 & \text{if } t < \tau
\end{cases}
\]

`can_sustain` is true only when \(t \ge t_{\mathrm{ready}}\) and the steady rate covers \(c_{\bar}\). At the sample ready day the buffer is 0 lb because 28.875 ≥ 2. Seven days earlier the buffer is 2 lb.

## Kits

\[
\text{kits\_needed}(c_{\bar}, y, z) = \left\lceil \frac{c_{\bar}}{r_{\mathrm{prod}}(\tau, y, z, 1)} \right\rceil
\]

One kit covers the sample 2 lb/week. List price used for the count is the Grit sale price **$3,449.99** (variant `47213766246652`).

## Fair prepaid price

Comparable expected meat price used by the worked example:

\[
\mathbb{E}[P_{\mathrm{comp}}] = 12.4633 \text{ USD/lb}
\]

This anchor is **assumed**. Distributor quotes in `SOURCES.md` are higher and are not averaged into it. Prime is the Fed H.15 bank prime loan, **7.00%** on **2026-09-24**.

The fair forward price per lb is the expected comparable itself (delivery-date expectation). The fair prepaid contract discounts it for \(T\) years:

\[
F_0 = \frac{\mathbb{E}[P_{\mathrm{comp}}]}{(1 + r_{\mathrm{prime}})^{T}}
\]

Sample: \(r_{\mathrm{prime}} = 0.07\), \(T = 0.5\),

\[
F_0 = \frac{12.4633}{\sqrt{1.07}} \approx 12.0488 \text{ USD/lb}
\]

## What this screen is not

- Not a Monte Carlo and not a cash-flow model
- Not permission to buy the kit, chicks, or feed
- Not a change to Stage 1 worm accounting
