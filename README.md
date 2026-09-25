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

# OSS tech spine

The editable technical tree sits next to this overview. Start here:

* [AGENTS.md](AGENTS.md) — how agents edit the tree (formats, IFC as source of record, sims)
* [economics/PHASE0_CART.md](economics/PHASE0_CART.md) — Phase 0 cart
* [docs/OSS_TECH_SPINE.md](docs/OSS_TECH_SPINE.md) — layout, climate regen, and the buildings prove path

Directories in the tree: `site/`, `land/`, `water/`, `waste/`, `power/`, `buildings/` (including `buildings/models/*.ifc`), `algae/`, `economics/`, `architecture/`, `climate/`, `reference/`.

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

The first major LoopBiotek system is **The Loop**, a circular food-production system.

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

---

# Mathematical Modeling

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

The long-term objective is a network of modular, productive, resilient communities whose systems can be studied, reproduced, improved, and adapted to local conditions.

**Build the loop. Measure the loop. Improve the loop.**

**LoopBiotek**
