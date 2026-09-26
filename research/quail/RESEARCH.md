# Research note — jumbo Coturnix, Stage 4 only

Planning note for cascade Stage 4. Formulas and the worked example are in [`SPEC.md`](SPEC.md). Citations and the ASSUMED / SOURCED split are in [`SOURCES.md`](SOURCES.md). Run `python -m research.quail` from the repo root.

## Why this is not a purchase

`biology/CASCADE.md` still locks spend at Stage 1 (worms) until vermiculture revenue is at least $2k/month, or a firm prepaid runway covers Stage-1 costs, and Rod clears the next gate. Quail are stage 4: eggs and meat after on-site insect and greens feed is reliable, and only if quail margin beats feed cost. This package does not clear that gate.

## What the screen says

One Grit Quail Professional Kit (sale price $3,449.99, incubator 216 eggs/batch) is the capacity unit. Brooder 150, jumbo grow-out 75, and breeders 45 are assumptions; the product page gives week-bands, not those bird counts.

Founders in the sample are 5 males and 15 females, the Padgett & Ivey ratio. With those hens the incubator fills, and brooder and grow-out both limit throughput at 37.5 birds/week. At an assumed 0.77 lb dressed, the steady rate is 28.875 lb/week, which rounds to 28.9.

The clock is 21 days of operational incubation plus 56 days to a jumbo table age: day 77, week 11. Average consumption of 2 lb/week is covered that day with no opening freezer buffer. See SPEC for the space caveat: an 8-week pipeline at 37.5 birds/week does not fit in 225 brooder-plus-grow-out spaces. Do not treat 28.9 lb/week as a build quantity.

## Price

The worked prepaid uses an assumed foodservice composite of $12.4633/lb, not the higher Manchester Farms and 123 Farmers quotes listed in SOURCES. Prime is 7.00% (Fed H.15, 2026-09-24). Half a year of discount:

\[
F_0 = 12.4633 / (1.07)^{0.5} \approx 12.0488 \text{ USD/lb}
\]

That identity is the whole pricing model. It is not a forecast of what a buyer will sign.
