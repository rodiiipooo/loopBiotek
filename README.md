# LoopBiotek

## Open Infrastructure for Independent, Resilient, Net-Export Communities

**LoopBiotek** is an open development project for designing, modeling, building, deploying, and operating communities that can produce more of their essential resources than they consume.

The project combines:

* Earth-coupled architecture
* Food production
* Nutrient and waste recovery
* Water systems
* Renewable and resilient energy
* Climate adaptation
* Automation and robotics
* Resource optimization
* Community-scale economics
* Mathematical modeling and simulation
* Modular construction
* Long-term maintenance and operational management

The goal is not to create isolated survival compounds.

The goal is to create **productive communities that use local resources efficiently, protect their inhabitants from environmental uncertainty, and generate enough economic surplus to sustain and expand themselves.**

---

# Why this exists

Three reasons sit together behind this project: care for the Earth, care that nobody in the community goes hungry, and a livelihood that does not rest on a wage alone. Habitat, food, water, energy, waste, and economics are usually planned as separate jobs. LoopBiotek treats them as one system, because a failure in any of them changes what the others can do for people and for the land they share.

**The Earth.** The climate is warming, and the conditions a community has to plan for are less certain than they were. Design that takes that seriously protects people and the living systems around them in the same drawings: shelter coupled to the soil, food and water accounted for, energy demand kept honest.

**One another.** Conscientious design starts by measuring needs, and nutrition is the first need. Surplus is what remains after the community, the breeding stock, the animals, the seed, and the safety floors have been served. A product can be sold when mouths are already fed. Community food is never traded away for profit while that need is still unmet. The weekly order that enforces this is in [Nobody goes hungry](#nobody-goes-hungry).

**A livelihood.** Demand for white-collar work is shrinking as AI takes on more of it. That raises the risk of widespread unemployment and economic stress, in the United States and elsewhere. Over a long stretch of time, the cost of living has tended to rise faster than many incomes keep up. Living costs do not scale with pay, so what a wage can buy erodes even when the job remains. LoopBiotek exists so people can build a real system — food, water, energy, shelter, and a productive surplus — that gives households and communities a buffer against that squeeze. The work is on site: running the loop, maintaining it, and selling only what the nutrition stack has already released. That surplus is also local employment, a buffer for when remote desk jobs thin out. It is a capability to build and measure. It is not a claim that the project ends unemployment, and the dollar figures in this repository remain planning values until a site measures them. See [Current Status](#current-status).

The aim is a productive place: people housed and fed, ecosystems kept in the accounting, and a real surplus that can sustain the community and, when it is safe, let it grow.

---

# Nobody goes hungry

The food model enforces that promise with a fixed weekly order. Modules 8 and 10 of [the reference notebook](reference/complete_model.ipynb) allocate every week in this order:

1. **Community human nutrition.** The cell owes its people a nutrient target `N_H = H × n_H`: the number of people `H` times each person's need vector. The reference run uses `H = 20`. The community egg allowance in that model is 12 eggs per person per week (`12H`). This claim is filled before anything is exported.
2. **Breeders and replacements.** The flock, and the other breeding stock, have to be fed so next season's food still exists. Harvest is limited by what future reproduction still needs (Module 1b).
3. **Animal feed.** Crickets, quail, fish, and the rest receive the feed their production requires after people and breeders.
4. **Seed and propagation reserves.** Seed bins and vegetative planting stock are refilled so the next planting can happen. Seed on hand, `B`, stays at or above its reserve floor.
5. **Working stock and safety floors.** Food inventory, seed, and emergency inventory sit above a floor. Module 10 requires the balance to hold in every week.
6. **Exportable surplus, last.** Only what remains after those five claims can be sold. Any product allocator runs inside this last step. Export does not draw down breeder stock, the seed reserve, or the safety floors.

**Establishment weeks look different, on purpose.** While the quail flock is still below its hen capacity, the model incubates first (about 70% of eggs in the reference code) so the future flock exists. The community eats from what remains, and eggs are still not sold out of that shortfall. The notebook treats the early food-shortfall index as a feature of building the flock. In the integrated 156-week run with `H = 20`, that index is zero from about week 28, once the flock can cover both incubation and the table. In steady state the order flips back: community eggs first (up to `12H`), then incubation of what is left, then sale of anything still above the incubator cap.

**Expansion waits on the same promise.** Module 11 refuses a growth step unless failure probabilities stay under their thresholds: the chance of a nutrition shortfall, the chance the seed bin breaks its floor, the chance an energy deficit goes unserved, and the chance cash goes negative. If any threshold fails, expansion holds. See [Model-Gated Expansion](#model-gated-expansion).

Every number in that notebook is a **planning value from the model**, not verified commercial performance. The same caution is in [Current Status](#current-status).

---

# How the Loop model works

The specification is [reference/complete_model.ipynb](reference/complete_model.ipynb): eleven modules, one weekly state vector, a 156-week coupled run, and a Monte Carlo check. The formulas live there. This section says what each piece is for, what its variables change, and when a reader should care. Later sections — [The First Reference System: The Loop](#the-first-reference-system-the-loop), [Mathematical Modeling](#mathematical-modeling), [Resource Accounting](#resource-accounting) — sit on top of the same model.

Time moves in weeks, `t = 0, 1, …`. Each week the community chooses controls `u_t` (what to cull, allocate, and harvest). Noise `ω_t` is everything biological and weather-related that does not obey the plan: hatch rates, survival, yields. Next week's state is this week's state, those choices, and that noise.

The circle the modules close: plants feed crickets, quail, fish, and black soldier fly larvae (BSFL); their wastes go to BSFL; larvae come back as feed and frass comes back to soil and plants. Cash is produced by exporting surplus, and export is last.

### Module 0 — State vector

**Purpose:** Remember everything the community has this week so every other module reads and writes the same picture.

**Key variables (plain English):**

- `X_t` — the whole community this week. It bundles the stocks below. Every later module reads this vector and writes back into it.
- `Q_t` — quail, split into females `F_a` and males `M_a` by age. This is the egg and meat engine. A missing age class shows up later as fewer eggs.
- `K_t` — crickets, by life stage. They turn plant residue into a harvest on a roughly six-week clock.
- `F_t` — fish cohorts. A cohort stocked this week is not food yet; harvest waits on weight-at-age.
- `B_t` — seed on hand. If this hits the floor, sprouting and planting shrink in later weeks.
- `S_t` — starch-crop cohorts on their own cycle. They are calories in the ground, not calories on the shelf, until harvest.
- `I_t` — product inventories (eggs, meat, and other outputs waiting to be eaten or, last, sold).
- `W_t` — water in store. Demand from animals, sprouts, crops, and people has to fit inside what is available.
- `E_t` — energy on hand (generation plus anything drawn from the grid or a generator). A deficit is paid for in cash.
- `cash_t` — money. It rises when surplus is sold and falls when feed, energy shortfalls, and the run's other operating costs are paid. A sale that skips the nutrition stack is not booked as income.

**What a reader should watch:** If seed, breeding birds, or the safety inventories fall while cash rises, the model is being read backwards — those stocks are supposed to be protected before cash is allowed to grow.

### Module 1 — Quail demographic engine

**Purpose:** Grow an age-and-sex flock that can feed the community and still replace itself.

**Key variables (plain English):**

- `F_a`, `M_a` — hens and males at age `a`. The reference code compresses juveniles into a six-week ring, then adult sexes. Total birds `N_Q` is the sum. A hole in one age class shows up weeks later as fewer eggs.
- `E_t` — eggs this week. The notebook draws them from each hen's age-specific laying chance `r_a` over seven days. Hens past the productive age `a_e` become harvest candidates.
- `E_inc` — eggs set in the incubator, capped by `C_inc` (incubator capacity). During establishment this is the flock's future. In the reference build, capacity is 400 hens, starting from 20, and the incubator cap is what stops the flock from being set faster than the hardware allows.
- `E_comm` — eggs kept for people, at most `12H` per week. This is the community claim on the flock.
- Hatch fraction `h`, female fraction `p_F`, and survival `s` — the share of incubated eggs that become chicks, the share of chicks that are female, and the share that live to the next age. A bad week here shrinks the flock that will be laying after the juvenile delay.
- `μ_Q` — hens per required male. The example is 5: one breeding male per five hens. Extra adult males are the default cull.

**What a reader should watch:** While hen count is below capacity, most eggs go to incubation and the community egg line can lag. That lag is the build-up described in [Nobody goes hungry](#nobody-goes-hungry), and it is not an export.

### Module 1b — Probabilistic culling governor

**Purpose:** Decide how many birds can be harvested this week without betting the future flock.

**Key variables (plain English):**

- `C` — birds harvested now. `C_demand` is how many the kitchen or a buyer would take. The governor may allow fewer.
- `C_max` — the largest harvest whose chance of missing future breeder targets stays within the limit. The actual harvest is the smaller of demand and this ceiling.
- `L` — how many weeks ahead the check looks. The notebook's worked example uses eight weeks. A short horizon hides a hole that is still in the juvenile ring.
- `α_Q` — the highest acceptable chance of falling short of required hens or males inside that horizon. The example uses 1%. A tighter `α_Q` means a smaller harvest today.
- `F_req`, `M_req` — how many females and males the flock must still have in each future week. If a proposed cull drives the projected flock under those lines too often, the cull is cut back.

**What a reader should watch:** A week with strong buyer demand and a small `C_max` means the flock cannot spare the birds. Selling them anyway would show up later as a nutrition shortfall, which is exactly what the gate is there to prevent.

### Module 2 — Waste-modulated growth

**Purpose:** Let diet quality, including how much waste is in the ration, change how fast each organism grows.

**Key variables (plain English):**

- `μ_j` — weekly growth rate of organism `j`. It starts from a biological maximum `μ_j^max` and is scaled by multipliers the notebook writes as `f_E`, `f_P`, `f_W`, `f_T`, and `f_ρ`. When growth falls to the maintenance rate `m`, the organism is only staying alive.
- `φ` — the fraction of the diet that is waste. For quail, more waste pulls growth down. The break-even fraction `φ*` is where growth only matches maintenance. Past `φ*`, growth is below maintenance and the stock declines.
- `φ_opt` — for a detritivore such as BSFL, the waste fraction where growth is highest. Some waste helps; too much still hurts. The notebook plots both.
- `d_j` — how digestible that ration is. Poor digestibility means more feed in for the same gain, and more waste out next week.

**What a reader should watch:** Raising the waste share in a quail ration to "use up leftovers" can cut eggs and meat before it saves any cash. The same waste may belong in the BSFL bin, where a moderate `φ` is useful.

### Module 3 — Crickets

**Purpose:** Turn residue feed into a cricket harvest on a short, staged life cycle, and send the frass onward.

**Key variables (plain English):**

- Stage bins — egg (about 1 week), nymph (about 4 weeks), adult harvest (about 2 weeks). The notebook's demo sets 200 eggs a week and promotes each bin with about 95% survival. A missed egg set shows up as a missed harvest about six weeks later.
- `I_K` — cricket feed in. The demo uses 170 lb of residue feed per week.
- `FCR_K` — feed conversion: pounds of feed per pound of live harvest. The demo uses 1.7, so harvest `P_K = I_K / FCR_K`. A worse conversion means less food from the same plants.
- Harvest fraction — the demo takes about 60% of adults each week and leaves the rest in the bin, while the egg bin is reset to 200.
- `W_K` — frass, about 0.40 lb per pound of feed, which Module 7 receives.
- Dry yield — about 0.55 lb dry product per pound live, then split across frozen retail, wholesale, and powder, each with a demand cap. Caps matter: unsold crickets are not automatic revenue.

**What a reader should watch:** Cricket harvest cannot rise just because the price is good. It rises when residue feed, survival through the nymph weeks, and the adult bin all allow it — and only after the nutrition stack has taken its share.

### Module 4 — Tilapia

**Purpose:** Hold fish as cohorts, grow them to a harvest weight, and keep from stripping the tank.

**Key variables (plain English):**

- `w_F(a)` — weight at age. The notebook uses a von Bertalanffy curve with an upper weight near 1.1 kg and a harvest window around 0.35 kg. Harvesting far below that window wastes the weeks already fed.
- `B_F` — standing biomass in the tank. The demo starts near 900 lb. Weekly harvest is limited to a quarter of standing biomass, so a tank cannot be emptied to make a sales week.
- `I_F` — fish feed. The demo feeds about 210 lb in a week at a conversion of 1.4.
- `y_F` — edible yield of what is harvested. The demo uses 0.87, gutted weight divided by live weight. Kitchens and sales see the gutted figure.
- `Y_F` — this week's edible harvest. In the coupled run, fish production starts at week 26, after quail (week 0) and crickets (week 13).

**What a reader should watch:** Until week 26, fish are not in production yet; that gap in the shortfall index is the phase schedule. After week 26, harvest still cannot exceed what biomass and the weekly cap allow.

### Module 5 — Sprouts and seed

**Purpose:** Convert seed into sprouts for the table, and keep enough seed that the conversion can continue.

**Key variables (plain English):**

- `P_sp` — sprout output. Sprouts are a conversion, not a field crop: yield times seed viability times the seed that was set a short time earlier.
- `q_t` — seed viability this week. It decays. Old seed produces fewer sprouts from the same pounds set.
- `η_sp` — an honesty check on energy. Sprouting adds water and micronutrients. The calories still come from the seed that went in.
- `B_t` — seed inventory. It gains harvested seed and loses seed used for sprouts, seed planted, other draws, and losses. It must stay at or above the reserve `B_reserve`.
- `M_eff` — seed harvested divided by seed planted. The loop only stays open if this stays above 1: more seed back than seed put in the ground.
- The notebook's illustration — 200 lb on hand, 20 lb used each week, 250 lb returned every 12 weeks, floor at 60 lb — is a worked example of that closure, not a field measurement.

**What a reader should watch:** If the seed line approaches the floor, next week's sprouts and plantings shrink first. Hunger risk shows up there before it shows up in cash.

### Module 6 — Starch and propagation reserve

**Purpose:** Grow the calorie crops on a twelve-week cycle, and hold back the planting material the next cycle needs.

**Key variables (plain English):**

- `S_c` — one planting cohort. Cohorts are tracked separately, so a harvest from one planting leaves the next planting's state intact.
- Harvest split — each harvest is divided into food and feed, seed, and a reserve. For seed crops the notebook's effective multiplication `M_eff` is about eight times after emergence and losses. That factor is what makes the next planting possible; spending it all as food ends the crop.
- `V_prop` — the propagation reserve for crops grown from cuttings or tubers rather than seed. It has a minimum `V_prop,min`. It plays the same role as the seed floor: it is not surplus.

**What a reader should watch:** A large starch harvest with a thin propagation reserve is a one-time meal. The reserve is what makes week 12 of the next cycle exist.

### Module 7 — BSFL waste processor

**Purpose:** Take the waste streams the other modules produce and turn them into larvae (feed) and frass (soil), which is what makes the system circular.

**Key variables (plain English):**

- `I_B` — waste in, the sum of streams `w_j` (the demo adds cricket frass, quail manure, and fish sludge).
- `n_larvae` — larvae out. Waste is scaled by digestibility and a conversion factor. The demo returns larvae as about 45% of the waste mass in that example, and the integrated results describe the BSFL node returning about 45% of waste mass as a feed offset.
- `n_frass` — what remains for soil. The demo uses about 40% of incoming waste. Frass is the path back to plants.
- Feed offset — the notebook applies larvae against purchased fish feed (about 30% of that feed in the module note; the coupled run cuts the purchased fish-feed term after larvae are credited). Less purchased feed is less cash out, and only after the larvae actually exist.

**What a reader should watch:** If quail, cricket, or fish production drops, waste into this module drops with it, and the feed offset shrinks the following weeks. BSFL cannot be scaled independently of the animals that feed it.

### Module 8 — Feed and nutrition allocation

**Purpose:** Enforce the hunger rule. Every edible and feed flow is claimed in the priority order in [Nobody goes hungry](#nobody-goes-hungry), and export is whatever is still unclaimed.

**Key variables (plain English):**

- `H` — people the cell is sized to feed. The reference notebook and the parameter workbook use 20, and the workbook also sketches 10, 40, and 77. Larger `H` raises the community claim every week and leaves less, later, for export.
- `n_H` — one person's nutrient need vector. `N_H = H × n_H` is the community's weekly claim. It is step 1. It is filled before breeders' feed, animal feed, seed, working stock, or sales.
- Steps 2 through 5 — breeder and replacement nutrition, animal feed requirements, seed and propagation reserves, then processing and working stock. Each is a hard claim on what the week produced.
- Step 6 — exportable surplus. This is the only step in which a sale is allowed. The notebook is explicit that a separate product-allocation optimizer, if used, operates inside this step and not above it.

**What a reader should watch:** Any proposed sale that reduces `N_H`, the breeder ration, or the seed floor is outside the model. The correct response in the accounting is to cut the sale, even when the price is attractive.

### Module 9 — Water and energy balances

**Purpose:** Check that water and power demanded by the living system fit inside what the site can supply, and price the energy gap honestly.

**Key variables (plain English):**

- `D_W` — water demand, the sum of quail, crickets, fish, sprouts, starch, and household uses. It has to sit within `W_avail`. The notebook's own limitations note treats water as this capacity check, not yet as a fully coupled tank-by-tank balance.
- `D_E` — energy demand. It has to sit within on-site generation `E_gen` plus grid or generator supply.
- The 2-cell load audit — about **41 kWh/day**. Incubator and brooder dominate, about 19 kWh/day. An earth-sheltered structure is credited with saving about 5 kWh/day (about 12%). These are the report's planning figures, the same grounding used elsewhere in this README.
- The phased supply in the notebook — about 5 kW of photovoltaics (about 157 kWh/week), a 20 kWh lithium-iron-phosphate battery, and a tri-fuel generator bridging a residual deficit of about 130 kWh/week. The coupled run bills that unmet kilowatt-hour as a cash cost.

**What a reader should watch:** An energy deficit is billed as generator fuel or grid purchases, and it can push cash down in a week when food targets are already met. See [Climate envelope](#climate-envelope) for how the building itself changes that load.

### Module 10 — Nutrient closure and net export

**Purpose:** Declare a week sustainable only when production covers use and reserves, and compute export after that declaration.

**Key variables (plain English):**

- `X_p` — surplus of product `p` this week: production minus what was consumed minus what was reserved. The model requires `X_p` to be at least zero in every week. The notebook is explicit that a positive average across the season is not the test.
- The mass balance — wastes plus products have to be accounted for as feed plus nutrients brought in from outside. Anything "missing" is an input the community is quietly depending on.
- Export — computed last, and kept from drawing down breeder stock, the seed reserve, or the safety floors. [Resource Accounting](#resource-accounting) names those floors as community food, seed, and emergency inventory. This is the same rule as Module 8, stated as a closure condition.

**What a reader should watch:** A month that "made money" while `X_p` went negative for food or seed is a month that spent the future. The model does not count that as net export.

### Module 11 — Stochastic control and expansion gates

**Purpose:** Admit that hatch, survival, sex ratio, yields, and weather are distributions, and refuse to grow the community when the odds of failure are too high.

**Key variables (plain English):**

- `ω` — one draw of the noise: a hatch rate, a survival rate, a yield, a weather week. Each Monte Carlo replicate is one full future under its own draws.
- Failure probabilities — the share of futures with a nutrition shortfall, a seed bin under its floor, an energy deficit that goes unserved, or cash below zero. The notebook's 40-replicate check on the reference run reports no steady-state shortfall and no seed-floor breach, and a cash break-even around week 83. That is a result inside this model, for `H = 20` on a 2-cell farm.
- `α` — the threshold for each of those probabilities. Expansion is allowed only when every one of them stays under its `α`. There is no growth step that "makes it up later."

**What a reader should watch:** A plan that expands because the average case is profitable, while a fat tail still breaks the seed floor or the nutrition target, fails this module. Hold is a successful output of the model.

### Climate envelope

**Purpose:** Keep the habitat livable with less energy as outdoor extremes grow, by coupling the room to the soil.

The food modules assume a building people can actually live in. A first thermal simulation of one earth-sheltered cell is in [`climate/thermal-model/`](climate/thermal-model/). Its job is to keep the room livable while leaning on the soil, so extreme outdoor weather costs less energy. It is a planning model of the envelope, not a finished HVAC design. The broader module this project still intends to grow is described under [Climate Envelope Model](#climate-envelope-model).

**Key variables (plain English):**

- Submersion — how much of the cell sits in the earth. The design minimum is at least 50%; the simulation baseline is 70%. More submersion lowers peak room temperature and the HVAC-proxy energy on the sensitivity chart, because more heat can be rejected into the soil.
- Outdoor temperature — the weather the shell has to face. The default run is a North Texas summer day swinging from about 26 °C to about 40 °C.
- Room temperature `T_r` — what the habitat feels like. The HVAC-proxy counts energy only while the room is above a 28 °C setpoint. It is a stand-in for cooling demand, not a full air-conditioner model.
- Soil temperature — the default deep soil is 18 °C, the sink the roof-water loop dumps heat into. If the loop cannot reach that sink (low submersion), the room runs hotter.

**What a reader should watch:** A design that saves food-system energy on paper and then spends it back on cooling has not helped the community. Submersion, room temperature, and the HVAC-proxy are how this repository currently checks that trade. The 41 kWh/day and ~5 kWh/day earth-shelter figures above remain the food-system load grounding; they are not a measurement from the thermal plots.

---

The notebook records its own limits in plain language: ages are compressed, noise is aggregate rather than a full demographic draw, prices and yields are illustrative, and there is no disease module, no genetics, and no moving market prices. Read the charts as a test of the rules — nutrition first, reserves held, export last, expansion gated — and treat the dollar figures as planning values.

---

# OSS tech spine

The editable technical tree sits next to this overview. Start here:

* [AGENTS.md](AGENTS.md) — how agents edit the tree (formats, IFC as source of record, sims)
* [biology/CASCADE.md](biology/CASCADE.md) — locked capital cascade; Stage 1 worms are the only active spend
* [economics/PHASE0_CART.md](economics/PHASE0_CART.md) — Phase 0 cart
* [docs/OSS_TECH_SPINE.md](docs/OSS_TECH_SPINE.md) — layout, climate regen, and the buildings prove path
* [docs/MICRO_FOR_COMMUNITIES.md](docs/MICRO_FOR_COMMUNITIES.md) — which microeconomics ideas support a healthy community business (Varian chapter map; no textbook text)

Directories in the tree: `site/`, `land/`, `biology/`, `water/`, `waste/`, `power/`, `buildings/` (including `buildings/models/*.ifc`), `algae/`, `economics/`, `architecture/`, `climate/`, `reference/`, `docs/`.

---

# The LoopBiotek Concept

Modern communities generally separate housing, agriculture, energy, water, waste, manufacturing, and commerce into independent systems.

LoopBiotek takes the opposite approach.

We treat the community as an interconnected system in which the output of one subsystem becomes the input of another.

```text
                    SUN
                     │
                     ▼
              ┌─────────────┐
              │   ENERGY    │
              └──────┬──────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   ┌───────┐     ┌───────┐     ┌───────┐
   │ WATER │     │ FOOD  │     │HABITAT│
   └───┬───┘     └───┬───┘     └───┬───┘
       │             │             │
       └─────────────┼─────────────┘
                     ▼
              ┌─────────────┐
              │   PEOPLE    │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │    WASTE    │
              └──────┬──────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ NUTRIENT RECOVERY   │
          └──────────┬──────────┘
                     │
                     ▼
                 FOOD / SOIL
                     │
                     └──────────► LOOP
```

The system is designed so that resources circulate internally for as long as practical while valuable products and services are exported.

---

# What Is a Net-Export Community?

LoopBiotek does not define sustainability as complete isolation from the outside world.

A community may still purchase specialized equipment, medicines, electronics, construction components, or other resources.

Instead, we measure whether the community can produce a **net surplus** in important resource categories.

Examples include:

### Food

```text
food produced - food consumed/imported > 0
```

### Energy

```text
energy generated - energy consumed/imported > 0
```

### Water

```text
usable water recovered/generated - water consumed/imported > 0
```

### Materials

```text
useful materials produced/recovered - materials consumed/imported > 0
```

### Economics

```text
community revenue - operating expenditure > 0
```

A surplus in these accounts is also a livelihood: people operating the system, and goods sold only after the community's own needs are met. That is local work and a buffer when a household's income depends on a remote desk job that may thin out. The motivation is in [Why this exists](#why-this-exists). The hunger rule still comes first.

A community can therefore become progressively more independent without requiring complete technological isolation.

---

# Earth-Coupled Architecture

A defining LoopBiotek design principle is the use of the earth itself as part of the environmental control system.

## Minimum Earth Integration Standard

LoopBiotek's current architectural concept requires occupied buildings to have:

> **At least 50% of their total vertical height below finished grade.**

If:

$$
H = \text{total building height}
$$

then:

$$
H_{underground} \geq 0.5H
$$

This is a **minimum design constraint**, not necessarily the optimal depth for every site.

The actual design may use greater earth integration when supported by:

* climate conditions
* geology
* soil characteristics
* groundwater conditions
* flood risk
* construction economics
* thermal modeling
* structural requirements
* community requirements

The objective is to use the surrounding earth as a thermal and protective envelope rather than relying entirely on mechanical systems to maintain suitable interior conditions.

---

# Climate Canopy

Above the earth-coupled structure, LoopBiotek may use a **climate canopy** or greenhouse-like structure.

This may include:

* greenhouse structures
* glass
* polycarbonate
* ETFE
* transparent or translucent roofing
* solar collection
* agricultural space
* protected circulation
* thermal-buffer zones

The canopy is not assumed to automatically reduce energy consumption.

Instead, its performance will be modeled.

Potential functions include:

* solar gain
* thermal buffering
* agricultural production
* wind protection
* daylighting
* rain collection
* protected activity space
* solar-thermal collection
* environmental transition between exterior and occupied space

The design objective is:

> **Use earth coupling, thermal mass, passive environmental control, and controlled solar gain to minimize the energy required to maintain acceptable environmental conditions.**

---

# Climate-Resilience Principle

LoopBiotek systems are intended to remain functional during environmental disturbances.

Design scenarios may include:

* extreme heat
* extreme cold
* drought
* heavy rainfall
* prolonged cloud cover
* grid outages
* water-system interruptions
* crop failures
* livestock losses
* equipment failures
* supply-chain disruptions
* severe storms
* wildfire smoke and other environmental hazards

The system should not depend on a single point of failure.

Instead:

```text
PASSIVE PROTECTION
        ↓
THERMAL MASS
        ↓
EARTH COUPLING
        ↓
PASSIVE VENTILATION
        ↓
SOLAR / RENEWABLE SYSTEMS
        ↓
STORAGE
        ↓
ACTIVE HVAC / CONTROL
        ↓
BACKUP SYSTEMS
```

The exact configuration will be determined by site-specific modeling.

---

# The First Reference System: The Loop

The first major LoopBiotek system is **The Loop**, a circular food-production system. Each organism below is a module in [How the Loop model works](#how-the-loop-model-works).

The current design connects:

* plants
* sprouts and greens
* crickets
* quail
* fish
* black soldier fly larvae
* soil
* compost/fertilizer
* water
* energy

The objective is to recover nutrients and biological outputs rather than treating them as waste.

The existing model routes plant production into animal and insect production, recovers animal waste through BSFL systems, returns frass to soil, and produces multiple saleable outputs.

Current modeled outputs include:

* eggs
* quail meat
* fish
* BSFL protein
* crickets
* sprouts and greens
* compost

---

# The Production Loop

```text
                    PLANTS
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     CRICKETS        QUAIL           FISH
        │              │              │
        │              └──────┬───────┘
        │                     │
        └─────────────────────▼
                         BSFL
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
              FEED              FRASS
                 │                 │
                 ▼                 ▼
              ANIMALS             SOIL
                                   │
                                   ▼
                                 PLANTS
```

The model also incorporates production ceilings and safety constraints rather than assuming unlimited recycling.

For example, the existing model explicitly accounts for waste-derived diet limits and uses these constraints when determining production levels.

---

# Community Resource Loop

The food system is only one component.

The long-term LoopBiotek architecture expands the loop:

```text
                    SOLAR
                      │
                      ▼
                   ENERGY
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    HABITAT          WATER          FOOD
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                   PEOPLE
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
        WASTE                  LABOR
          │                       │
          ▼                       ▼
   RESOURCE RECOVERY          PRODUCTION
          │                       │
          └───────────┬───────────┘
                      ▼
                   SURPLUS
                      │
                      ▼
                   EXPORT
```

The long-term objective is to turn the community into a productive economic system rather than merely a consumption center.

---

# Modular Community Architecture

LoopBiotek systems are intended to be modular.

A community can begin with a small deployment and expand as resources become available.

```text
             LOOP CELL
                 │
                 ▼
          MULTIPLE CELLS
                 │
                 ▼
          SMALL COMMUNITY
                 │
                 ▼
          LARGER COMMUNITY
                 │
                 ▼
        REGIONAL NETWORK
```

A "cell" can represent a modular combination of:

* habitation
* food production
* water
* energy
* storage
* utilities
* workspace
* biological processing

The exact cell architecture is an active area of development.

When many communities run that pattern, the next question is how the cells behave together. That is [Network of communities](#network-of-communities).

---

# Network of communities

When many communities adopt the model, each site is a **node** in a network. The cell rules do not change: the nutrition stack, the safety floors, and the Module 11 failure gates still belong to that site. What changes is the set of problems a single community has to plan for because other nodes exist.

The microeconomic vocabulary for these problems — network externalities, public goods, games, asymmetric information — is mapped, by chapter title only, in [docs/MICRO_FOR_COMMUNITIES.md](docs/MICRO_FOR_COMMUNITIES.md).

### What each community plans for

1. **Standards and complements.** Shared IFC models, schemas, and other open formats become more useful as more sites use them. Keep them versioned and open. A vendor format the cell cannot leave, or a tool that only one supplier can read, is lock-in. Complements (a standard plus the software that speaks it) are welcome. Captivity is not.

2. **Trade and specialization, held against resilience.** A site may specialize in what it is good at, and sell it, only on exportable surplus. The nutrition stack and the safety floors stay on site. A neighbor's cheap eggs are not a reason to stop keeping the local egg claim and the seed reserve.

3. **Landscape commons.** Watersheds, the electric grid, and local market demand are shared. One node's withdrawal or export changes the others. Publish withdrawals and exports. Respect caps. A full local market for one product is a commons that can be overfilled; flooding it with identical surplus hurts every seller, including the one who needed that cash.

4. **Contagion.** Failures travel. Biological (disease, pests), financial (a shared buyer or a shared debt), reputational (one site's false claim stains the badge), and procedural (copying another site's expansion settings when your own α gates would have said hold). The responses are quarantine, and certification that checks the stack, as distinct from a brand that only looks trustworthy.

5. **Free riding on the open layer.** Standards, playbooks, and ops data are cheap to copy and costly to produce. Contribution norms belong next to something real: sites that publish ops data can be eligible for certification and for mutual aid. Sites that only consume the open layer stay free to operate. They do not automatically draw on the mutual-aid pool.

6. **Coordination on shared hubs.** Incubators, cold storage, wells, and lanes that several cells use are repeated games. Dues and metered use keep the hub alive. A one-time handshake does not. The site that restrains itself has to be able to see, and respond, when another site does not.

7. **Two-sided matching.** Communities, maintainers, and buyers have to find each other. Matching is useful. Hold-up is the failure mode: one side sinks cost (a custom install, a standing crop, a trained crew) and the other renegotiates. Contracts and staged payment exist so that investment is not trapped.

8. **Incentive distortion.** Collective bounties and matches are easy to aim at the wrong target: more of one crop, faster expansion, a prettier weekly number. A bounty is admissible only when it is gated by the same stack as a sale: hunger rules, safety floors, and failure probabilities. A prize that pays a site to skip α, or to sell food its own people still need, is a bug.

### Governance stance

**Yes to a steward of protocols. No to a central planner of production.**

Someone has to version the standards, say what "nutrition-stack compliance" means in a checkable way, and keep mutual-aid playbooks current. Nobody gets to decide what every cell grows, how much it expands, or where its surplus must go.

| Layer | What it may do | What it does not do |
| --- | --- | --- |
| Cell | Run the nutrition stack, hold safety floors, apply Module 11 gates, sell only released surplus | Hand its floors to a neighbor, a buyer, or a bounty |
| Federation / standards body | Version standards, certify nutrition-stack compliance, publish mutual-aid playbooks | Seize assets, or force every site into the same crops and the same scale |
| Optional incentive desk | Offer bounties or matches for a complementary network shortfall, and only after verified stack compliance; cap any one product so the network does not become a monoculture | Pay for expansion that failed α, or for output taken from local floors |
| Markets | Price true surplus | Price the community's own nutrition claim or its safety floors |

> Autonomy inside the cell’s survival constraints; interoperability across cells; incentives only for verified surplus that fills a network gap.

Soft coordination is a shortfall board (what the network is actually missing), pull matching (a site offers surplus; a shortfall asks), and dues for shared public goods such as the standard and the playbooks. Push quotas that raid local floors are out. A federation that assigns production targets has become a planner. That is the line this project does not cross.

These are design rules for a network that does not exist yet at scale. They are not a claim that a steward, a certificate, or a bounty has been shown to work in the field. Measured performance still has to be earned site by site. See [Current Status](#current-status).

---

# Mathematical Modeling

A plain-language walkthrough of each module, its variables, and the hunger rule is in [How the Loop model works](#how-the-loop-model-works). The equations and the 156-week run are in [reference/complete_model.ipynb](reference/complete_model.ipynb).

A major component of LoopBiotek is quantitative modeling.

The objective is to model the community before constructing it.

Current modeling work includes:

* demographics
* livestock populations
* crop production
* feed requirements
* nutrient flows
* waste recovery
* energy
* water
* economics
* inventory
* safety stock
* stochastic events
* production constraints
* expansion decisions

The existing model uses stochastic simulation to evaluate uncertainty and applies constraints before allowing expansion.

The repository will continue moving these models toward reproducible simulations that can be adapted to different community sizes and locations.

---

# Climate Envelope Model

A first cell-scale simulation already lives in [`climate/thermal-model/`](climate/thermal-model/) and is summarized in [Climate envelope](#climate-envelope). The broader module below is still the planned expansion.

A planned expansion of the model is the **Climate Envelope Module**.

The module will evaluate relationships between:

* outside temperature
* soil temperature
* building depth
* thermal mass
* insulation
* glazing
* greenhouse volume
* solar radiation
* ventilation
* shading
* humidity
* internal heat generation
* livestock heat
* equipment heat
* HVAC demand
* energy storage

A simplified thermal model may be represented as:

$$
T_{inside,t+1}
=
f(
T_{inside,t},
T_{soil,t},
T_{outside,t},
Q_{solar},
Q_{internal},
Q_{ventilation},
Q_{envelope}
)
$$

The objective is to determine configurations that minimize lifecycle energy consumption while maintaining required environmental conditions.

---

# Resource Accounting

How those floors sit in the weekly priority stack is in [Nobody goes hungry](#nobody-goes-hungry).

LoopBiotek will use explicit resource accounting rather than broad claims of "sustainability."

For each resource:

$$
Net\ Balance =
Production + Recovery - Consumption - Losses
$$

Examples:

```text
Food balance
Energy balance
Water balance
Nutrient balance
Material balance
Financial balance
```

Safety reserves are accounted for before surplus is exported.

The existing Loop model already uses safety floors for community food, seed, and emergency inventories.

---

# Model-Gated Expansion

The food model's version of this gate is Module 11, described in [How the Loop model works](#how-the-loop-model-works).

Growth should not occur simply because additional capacity appears profitable.

Expansion is permitted only when defined constraints remain satisfied.

Examples:

```text
Nutrient balance       ✓
Water reserve          ✓
Energy reserve         ✓
Food reserve           ✓
Seed reserve           ✓
Breeding population    ✓
Cash reserve            ✓
Failure probability    ✓
```

If a critical condition fails:

```text
EXPANSION = HOLD
```

The existing Loop model already uses this principle: expansion is gated by nutrient balance, cash, safety stock, and modeled failure probabilities.

---

# Bio Capital Cascade

Material loops above describe how nutrients move. **Capital deployment follows one locked track.** The source of record is [`biology/CASCADE.md`](biology/CASCADE.md).

1. Worms
2. Crickets + isopods (rollie pollies)
3. Land + semi-underground vertical greens + algae
4. Quail
5. Aquaponics
6. Community quality of life, funded from surplus only

**Stage 1 (worms) is the only active spend** until vermiculture revenue is at least $2,000 per month, or a firm prepaid forward runway covers Stage-1 costs. Agents must not open Stage 2+ spend without Rod clearing that gate.

Worm growth and forward-book models live outside this repository at `/workspace/worm-revenue-model/`. Site config records `active_stage: 1` in [`site/site.yaml`](site/site.yaml); land stage tags are in [`land/allocation.yaml`](land/allocation.yaml).

---

# Open Development

The GitHub repository is intended to contain reusable resources for people who want to:

1. Study the system
2. Model their own site
3. Build independently
4. Adapt components
5. Experiment with alternative designs
6. Contribute improvements
7. Contract LoopBiotek for implementation

The open repository may eventually contain:

* mathematical models
* simulation notebooks
* engineering calculations
* system diagrams
* bills of materials
* equipment specifications
* site-assessment tools
* construction concepts
* energy models
* water models
* food-production models
* economic models
* optimization tools
* operating procedures
* monitoring tools
* maintenance documentation

---

# LoopBiotek Commercial Model

The open repository is the technical foundation.

LoopBiotek's commercial business is the **design, supply, installation, integration, commissioning, and ongoing support of these systems.**

That work is part of the livelihood described in [Why this exists](#why-this-exists). Design, construction, operation, and maintenance are jobs attached to infrastructure a community can meter: food produced, energy used, water recovered, cash after the safety floors. People can build from the open materials, or hire LoopBiotek to do the same work under contract. Either path is a system to measure. A contract is not a guarantee that a modeled surplus will show up on a given site.

Customers may choose to:

### Build Independently

Use the public resources to develop their own implementation.

### Hire LoopBiotek for Design

LoopBiotek develops a site-specific system architecture and implementation plan.

### Hire LoopBiotek to Build

LoopBiotek supplies and installs the system.

### Hire LoopBiotek to Operate and Maintain

LoopBiotek provides:

* monitoring
* maintenance
* repairs
* optimization
* training
* replacement components
* system upgrades

This creates a path from open knowledge to commercial deployment.

---

# Planned Service Categories

## 1. Site Assessment

Analysis of:

* land
* climate
* soil
* water
* solar resource
* energy availability
* construction constraints
* agricultural potential

## 2. System Design

Integrated design of:

* habitat
* food
* water
* energy
* waste recovery
* automation
* storage
* economic systems

## 3. Installation

Physical deployment and integration of system components.

## 4. Commissioning

Testing the completed system against its design requirements.

## 5. Monitoring

Continuous measurement of:

* energy
* water
* food production
* environmental conditions
* biological production
* equipment status
* inventory
* financial performance

## 6. Maintenance and Repair

Ongoing maintenance, repair, replacement, and system optimization.

## 7. Training

Training community members to operate and maintain their own systems.

---

# Development Philosophy

LoopBiotek follows several principles.

### 1. Measure Before Building

Model the system before committing major capital.

### 2. Build Small First

Start with an instrumented, reversible deployment.

### 3. Measure Everything

Collect operational data continuously.

### 4. Let the Model Learn

Replace assumptions with measured performance.

### 5. Design for Failure

Every critical subsystem should have defined failure modes and mitigation strategies.

### 6. Preserve Safety Stocks

Do not export resources required for continued operation.

### 7. Expand Only When Ready

Growth is conditional on measurable system performance.

### 8. Prefer Passive Systems

Use earth, thermal mass, solar geometry, water, vegetation, and other passive mechanisms before adding active energy consumption.

### 9. Make Systems Repairable

Favor understandable, modular, maintainable systems over unnecessary complexity.

### 10. Document Everything

The objective is to make the system transferable rather than dependent on one person.

---

# Current Status

LoopBiotek is in the **pre-construction research and development stage**.

The current Loop research has produced:

* a practical research report
* a mathematical model
* stochastic simulation
* resource-flow modeling
* production modeling
* economic modeling
* energy modeling
* expansion constraints

The current report explicitly identifies the design as pre-construction and recommends a small, instrumented, reversible first implementation so that real-world measurements can improve the model.

Active capital spend is **Stage 1 worms only**, under the gate in [`biology/CASCADE.md`](biology/CASCADE.md).

The current modeled two-cell food-production system estimates approximately:

* **$13,000** initial investment for a grid-powered configuration
* **$37,000** for the modeled off-grid configuration
* approximately **$4,300/month** steady-state revenue
* approximately **$885/month** steady operating cost

These are **planning/model values rather than verified commercial performance**, and the report identifies local quotes and buyer commitments as necessary validation steps.

---

# Repository Structure

```text
loopBiotek/
│
├── AGENTS.md                # Stage 2+ spend stays closed until Rod clears Stage 1
├── biology/                 # capital cascade SoR — Stage 1 worms active
│   ├── CASCADE.md
│   └── README.md
├── site/
│   └── site.yaml            # active_stage: 1
├── land/
│   └── allocation.yaml      # cascade stage tags
│
├── architecture/
│   ├── habitat/
│   ├── earth-sheltering/
│   ├── climate-canopy/
│   └── community-cells/
│
├── climate/
│   ├── thermal-model/
│   ├── weather/
│   ├── ventilation/
│   └── resilience/
│
├── energy/
│   ├── solar/
│   ├── storage/
│   ├── thermal/
│   └── modeling/
│
├── water/
│   ├── collection/
│   ├── treatment/
│   ├── recycling/
│   └── modeling/
│
├── food/
│   ├── plants/
│   ├── sprouts/
│   ├── starch/
│   ├── insects/
│   ├── quail/
│   ├── fish/
│   └── bsfl/
│
├── waste/
│   ├── nutrient-recovery/
│   ├── compost/
│   └── resource-flows/
│
├── economics/
│   ├── capex/
│   ├── opex/
│   ├── cashflow/
│   └── export-model/
│
├── simulation/
│   ├── mathematical-model/
│   ├── monte-carlo/
│   ├── optimization/
│   └── scenarios/
│
├── construction/
│   ├── earthworks/
│   ├── structures/
│   ├── greenhouses/
│   └── utilities/
│
├── automation/
│   ├── robotics/
│   ├── sensors/
│   ├── monitoring/
│   └── control/
│
├── deployment/
│   ├── site-assessment/
│   ├── installation/
│   ├── commissioning/
│   └── maintenance/
│
├── business/
│   ├── pricing/
│   ├── services/
│   ├── installation/
│   └── operations/
│
└── docs/
    ├── research/
    ├── specifications/
    ├── guides/
    └── decisions/
```

---

# Roadmap

## Phase 1 — Foundation

* [ ] Establish repository architecture
* [ ] Publish existing Loop mathematical model
* [ ] Publish current research report
* [ ] Document assumptions
* [ ] Establish data standards
* [ ] Establish model validation framework

## Phase 2 — Climate Architecture

* [ ] Develop earth-coupled thermal model
* [ ] Model 50% underground design constraint
* [ ] Model different soil depths
* [ ] Model thermal mass
* [ ] Model greenhouse/climate canopy
* [ ] Model ventilation
* [ ] Model shading
* [ ] Model extreme-weather scenarios
* [ ] Compare alternative building configurations

## Phase 3 — Integrated Community Model

* [ ] Integrate energy
* [ ] Integrate water
* [ ] Integrate food
* [ ] Integrate waste recovery
* [ ] Integrate habitat
* [ ] Integrate economics
* [ ] Integrate population
* [ ] Integrate resilience metrics

## Phase 4 — Reference Community

* [ ] Define Loop Cell
* [ ] Define minimum viable community
* [ ] Develop site-selection methodology
* [ ] Develop construction specifications
* [ ] Build prototype
* [ ] Instrument prototype
* [ ] Collect operational data
* [ ] Compare measured results against simulation

## Phase 5 — Commercial Deployment

* [ ] Develop standardized system packages
* [ ] Develop installation procedures
* [ ] Develop maintenance procedures
* [ ] Develop pricing
* [ ] Develop monitoring platform
* [ ] Develop training materials
* [ ] Deploy first customer systems

---

# Contributing

Contributions are welcome.

Potential contribution areas include:

* engineering
* agriculture
* biology
* aquaculture
* entomology
* architecture
* construction
* renewable energy
* water systems
* robotics
* software
* mathematics
* optimization
* economics
* manufacturing
* documentation

When contributing models or engineering calculations:

1. Document assumptions.
2. Identify data sources.
3. Make units explicit.
4. Include uncertainty where appropriate.
5. Provide reproducible calculations.
6. Distinguish measured data from assumptions.
7. Explain limitations.

---

# Design Status

LoopBiotek is an active research and development project.

Nothing in this repository should be interpreted as a guarantee that a proposed system will perform as modeled under every site or climate condition.

Construction, structural, electrical, mechanical, environmental, agricultural, and other regulated work must be reviewed and performed as required by applicable professionals, authorities, codes, and regulations.

The objective of the project is to progressively replace assumptions with measurements.

```text
IDEA
  ↓
MODEL
  ↓
SIMULATION
  ↓
PROTOTYPE
  ↓
MEASUREMENT
  ↓
VALIDATION
  ↓
DEPLOYMENT
  ↓
DATA
  ↓
IMPROVED MODEL
  ↓
NEXT GENERATION
```

---

# The Long-Term Vision

LoopBiotek is developing a framework for communities that can progressively increase their ability to provide their own:

**food + water + energy + shelter + employment + economic output**

while reducing unnecessary resource consumption and vulnerability to external disruptions.

Employment belongs in that list for a specific reason. As AI takes on more white-collar tasks, desk work can become a thinner share of how households earn a living, while living costs do not shrink to match. A community that produces its essentials and an exportable surplus has work and a buffer that can stand beside a wage, and carry more of the load if that wage thins out. The buffer counts only where the model is checked against measurements. The hunger rule is unchanged: surplus is what remains after people are fed.

The long-term objective is a network of modular, productive, resilient communities whose systems can be studied, reproduced, improved, and adapted to local conditions. How those nodes coordinate — a steward of protocols, and not a central planner of production — is in [Network of communities](#network-of-communities). The chapter map behind that stance is [docs/MICRO_FOR_COMMUNITIES.md](docs/MICRO_FOR_COMMUNITIES.md).

**Build the loop. Measure the loop. Improve the loop.**

**LoopBiotek**
