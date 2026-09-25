# LoopBiotek Additional CAPEX — Investment Shortlist

**Prepared:** 2026-09-25 (America/Chicago)  
**Scope:** Open and commercial equipment options for LoopBiotek / Glass Sand community CAPEX.  
**Pricing rule:** USD figures below are either (a) taken from a fetched vendor/dealer page, or (b) labeled **estimate / contact for quote**. Prefer US-available or shippable options.  
**Context:** Rod already operates **Glass Sand** (crush glass → sand) and LoopBiotek community work. **Algae = nutrient-density primary; biofuel secondary.**

**Agent caveat:** Re-fetch cited URLs or get a written quote before any PO. Do not load “contact for quote” bands into `reference/loop_params.xlsx` as firm costs.

---

## 1. Glass recycler / glass-to-sand

### Need
Convert mixed waste glass into safe, rounded sand/aggregate for construction, landscaping, abrasives, and Glass Sand product lines.

### Recommended primary
**Andela GP-Mini** (Andela Products, Richfield Springs, NY) — hand-fed compact pulverizer with integrated trommel; entry system for pilots / breweries / small municipalities.

| Spec | Value (vendor) |
|------|----------------|
| Throughput | ~1,000–1,500 lb/hr |
| Power | 5 hp pulverizer + ½ hp trommel; 230/460 V 3-phase (single-phase option listed) |
| Footprint | ~75″ L × 52″ W × 70″ H; ~2,000 lb shipping |
| Output | Rounded sand/aggregate ~3/8″ (10 mm) and smaller; trommel separates caps/labels |
| Dust | Dust port for collector or water mist |
| Source | https://andelaproducts.com/complete-systems/glass-pulverizer-systems/gp-mini-system/ |

AU distributor related specs (same product family): ~500 kg/hr; motors **3.73 kW + 0.4 kW**; 415 V 3-phase — https://wasteinitiatives.com.au/product/glass-crushers/glass-pulverisers/gp-mini-small-glass-pulveriser/

### Alternates
1. **Andela GP-MegaMini** — 1,500–2,000 lb/hr; sand vs 1/8–3/8″ gravel split — https://andelaproducts.com/complete-systems/glass-pulverizer-systems/gp-megamini-system/  
2. **Andela GP-05L** — 1–2 ton/hr municipal class — https://andelaproducts.com/complete-systems/glass-pulverizer-systems/  
3. **Pilot hammer mill:** **LGXEnzhuo Glass Bottle Crusher** — **$1,139.99** listed (Dallas TX seller); 2.5 kW / 220 V; 300–500 kg/hr; screens 3 / 6 / 10 mm — https://jumboindustrial.com/products/lgxenzhuo-glass-bottle-crusher-220v-2-5kw-with-3mm-6mm-10mm-screens/  
   - Caveat: testing-class hammer mill; edges not Andela-rounded; silica/dust controls required.

### Approx CAPEX band (USD)
| Option | Band | Confidence |
|--------|------|------------|
| LGXEnzhuo small crusher | **$1,139.99** (listed) | High |
| Andela GP-Mini / MegaMini / GP-05L+ | **Contact for quote** (Andela FAQ: prices vary; request free estimate) | No public list price |
| Larger Andela (up to GP-2HD ~20 ton/hr) | **Contact for quote** | No public list price |

Andela FAQ: https://andelaproducts.com/faqs/  

**Market revenue context (not CAPEX):** Andela materials cite end-product bands roughly $0–10/ton bulk aggregate, $20–30 specialty, $150–1,000/ton abrasives / filtration / colored landscaping — https://andelaproducts.com/wp-content/uploads/2023/12/Andela-Want-to-Start-Recycling-Glass-2022-.pdf

### Specs that matter
- **Construction sand:** fine fraction toward C33-style sieve (Andela cites No.4 / ≤5 mm sand profiles in customer PDFs).  
- **Abrasive / blast media:** finer, dried, screened (often ≤2–3 mm for fine sand per Andela FAQ) — extra drying/bagging CAPEX.  
- **Dust / silica:** OSHA crystalline-silica rules apply; budget dust collector or mist + PPE.  
- **Power / pad:** 3-phase preferred for GP-Mini; concrete pad + bins.

### Pros / cons for LoopBiotek ↔ Glass Sand
| Pros | Cons |
|------|------|
| Direct feed to Glass Sand SKUs | Andela = custom quote + lead time |
| Rounded edges safer for community handling | Small hammer mills ≠ construction-sand quality |
| Trommel separates contaminants | Dust control + permitting at commercial volume |

### Open-source / agent-editable angle
Mass-balance (lb glass in → sand / aggregate / residue) in a simple CSV or notebook. Dust/air permits are local AHJ, not EPANET.

---

## 2. “Sand blasting oven for glass production” — terminology clarified

**Likely means either or both of:**
- **(a) Sandblast / abrasive cabinet** — etch, frost, or clean glass/metal with blast media (often glass bead). **Do not use crystalline silica sand** in cabinets (silicosis risk).  
- **(b) Annealing / fusing / casting kiln** — heat-treat fused, slumped, or cast glass (Evenheat, Paragon, Skutt; industrial lehrs at much higher CAPEX).

**Also possible:** polishing lathes, sintering furnaces, tempering ovens — different equipment classes; not shortlisted as the primary reading of the phrase.

### 2a — Sandblast cabinets

#### Need
Surface finish / etch glass products and clean tooling without outdoor open blasting.

#### Recommended primary
**Econoline 101696R-A** (42×24 siphon cabinet + dust collector) — **$3,049.00** — https://www.globalindustrial.com/p/42x24-abrasive-blast-cabinet-siphon-101696r-a

#### Alternates
1. **Econoline Mini Bench 101691R-A** — **$1,119.05** — https://www.jmesales.com/econoline-mini-blast-cabinet-steel-120-psi/  
2. **Econoline 36-1** — **$2,319.07** (same JME catalog family as above)  
3. Cyclone / Eastwood cabinets appear in the ~$1,600–$2,100 retail band in search results; Eastwood page was bot-blocked at fetch — **re-check live** before buy.

#### Specs that matter
Work envelope, CFM (compressor sizing), dust collector, media type (glass bead / AlOx — not silica sand). Cabinet usually 110 V; compressor is separate CAPEX.

### 2b — Glass kilns / annealing ovens

#### Need
Fuse, slump, anneal, and kiln-cast community glass products from cullet/frit (including Glass Sand–adjacent streams).

#### Recommended primary (pilot studio)
**Paragon Fusion-14** — **$2,160.00** (sale from $2,400) — 14″×14″×~6.75″ chamber; 120 V / 15 A / 1800 W; max ~1700 °F — https://paragonkilns.com/products/fusion14-glass-fusing-kiln · https://kilnfrog.com/products/fusion-14

#### Alternate (casting / deeper work)
**Evenheat GTS 24** — **$4,752.00** (from $5,940) — 24″×24″×13.5″; ~4.2 ft³; 240 V / 32 A / 7680 W; NEMA 6-50; max 1800 °F; casting-capable — https://modernpotters.com/products/evenheat-gts-24-glass-kiln  

**Industrial lehrs / tempering:** contact for quote; typically far above studio kilns — not Phase 0–1.

#### Approx CAPEX band (USD)
| Item | Band | Source |
|------|------|--------|
| Mini blast cabinet | **$1,119.05** | JME Econoline Mini |
| Mid blast cabinet | **$2,319–$3,049** | JME / Global Industrial |
| Studio fuse kiln | **$2,160** | Paragon Fusion-14 |
| Studio cast kiln | **$4,752** | Evenheat GTS 24 dealer |

### Pros / cons
| Pros | Cons |
|------|------|
| Blast + kiln → finished Glass Sand craft SKUs | Cabinet media ≠ construction sand product |
| 120 V Fusion-14 fits community shop | Large casting needs 240 V / 50 A |
| Synergy with crushed-glass frit | Dust from blasting and investment molds |

### Open-source / agent-editable angle
Firing schedules as versioned CSV/JSON (ramp–hold–anneal). Keep a/b terminology in docs — this is not one “oven.”

---

## 3. Glass injection molding equipment

### Need
Repeatable community products. **True molten-glass injection molding is rare / industrial** (hot-glass press, IS bottle machines, optical glass press). Consumer “glass injection” often means **glass-filled thermoplastic injection**.

### Realistic community path (recommended sequence)
1. **Kiln-cast + refractory molds** (lowest CAPEX, best craft fit)  
2. **Glass-filled polymer injection** on benchtop / used 50–150 ton press  
3. **Hot-glass press / IS** only if volume and capital justify (Phase 2+)

### Recommended primary (Phase 0–1)
**Kiln-cast path:** Paragon/Evenheat (above) + investment mold material  
- **Glass-Cast™ 400 investment** — **$42.00** (bag; stock varies) — https://shop.sculpt.com/products/glass-cast-400-investment  
- Max casting temp guidance on product literature ~1540 °F; silica hazard — PPE required.

### Alternate A — plastic injection (glass-filled polymers)
| Class | Price band | Notes |
|-------|------------|-------|
| Manual desktop (Morgan Press class) | Used **$1,500–$8,000** (market guide) | Meadoworks |
| Automatic benchtop (**Babyplast** 6/10P class) | Used **$10,000–$35,000** (market guide) | Micro-molder common in US R&D |
| Used ~50 ton industrial | Often **~$6,000–$25,000+** depending on age | Hardened screw/barrel for glass-filled resins |
| Sources | https://www.meadoworks.com/resources/desktop-injection-molding-machine-guide · https://www.babyplast.com/ | |

**Agent caveat:** Glass-filled nylon/PP abrades screws — specify wear-resistant barrel/screw. Desktop clamp typically **<5 ton** — not for large structural parts.

### Alternate B — industrial glass press / IS
Hot-glass press / IS machines: **contact for quote**; typically six-figure+ with molds, furnace, and lehr. Not community-fab default.

### Approx CAPEX band
| Path | Band | Confidence |
|------|------|------------|
| Kiln + investment + molds | **~$2,200–$6,000** equipment + consumables | High for kiln; molds vary |
| Babyplast / auto benchtop | **$10k–$35k** used (guide) | Medium |
| Used 50–150 ton press | **estimate / contact for quote** | Low–medium |
| Hot-glass injection / IS | **contact for quote** | No list price found |

### Pros / cons for Loop
| Pros | Cons |
|------|------|
| Kiln-cast uses cullet/frit from Glass Sand | Not true “injection” throughput |
| Polymer path enables fixtures / packaging | Glass-filled resin ≠ recycled-glass body |
| Clear upgrade ladder | Full hot-glass injection unrealistic for Phase 0 |

### Open-source / agent-editable angle
Mold CAD (FreeCAD / OpenSCAD) + kiln schedule files. Prefer polymer path only after cast product-market fit.

---

## 4. Pyrolysis machine

### User link (fetched)
**GEP ECOTECH portable (skid) pyrolysis plant** — https://www.aishred.com/product/portable-pyrolysis-plant.html  

| Published | Detail |
|-----------|--------|
| Price band on page | **USD 57,100 – 285,700** |
| Feedstocks claimed | MSW, medical, ag/forestry, biomass, tires, plastics, sludge |
| Products claimed | Combustible gas, fuel oil, carbon black, ash |
| Vendor note | Custom equipment → contact for precise quote |
| Origin | Zhengzhou, China (GEP ECOTECH / aishred) |

### Alternates (published start prices)
1. **Beston batch** — starts at **$67,000**; **continuous** starts at **$688,900** — https://www.bestongroup.com/pyrolysis-plant/cost/  
   - Example batch BLJ-16: ~1 batch/day class; tire ~10–16 t/batch depending on prep.  
2. **Huayin continuous Model S** — capacity marketing; **contact for quote** — https://www.huayinenergy.com/products/continuous-pyrolysis-plant.html  

### Continuous vs batch
| | Batch | Continuous / portable skid |
|--|-------|----------------------------|
| CAPEX entry | Lower (Beston from ~$67k equipment) | Portable page $57k–$286k; continuous industrial ≫ $600k |
| Ops | Furnace/day class | Higher automation |
| US install | Shipping, foundation, scrubbers, tanks | Same + skid logistics |

### Regulatory / air-quality reality (US communities) — **critical**
- Pyrolysis / “advanced recycling” sits in a **shifting federal Clean Air Act** frame (OSWI §129 vs manufacturing §111 debates). Follow current EPA rulemaking — do not assume exemption.  
- **State air permits, zoning, solid-waste licenses, fire code, and wastewater** usually dominate timeline and cost — often **larger than machine price**.  
- Budget: emissions control (scrubber / thermal oxidizer), monitoring if required, oil storage, residual char handling, public engagement.  
- **Agent caveat:** A China skid quote ≠ a permitted US plant. Model CAPEX as **equipment + compliance + site**.

### Approx CAPEX band
| Item | Band | Confidence |
|------|------|------------|
| GEP portable (page) | **$57,100–$285,700** | Page range; still contact for config |
| Beston batch start | **from $67,000** | Vendor published start |
| Beston continuous start | **from $688,900** | Vendor published start |
| US install + permits + APC | **estimate / contact for quote** — often ≫ equipment | High uncertainty |

### Pros / cons for Loop
| Pros | Cons |
|------|------|
| Plastics/tires → oil + carbon streams | Permitting risk for community sites |
| Portable framing for distributed waste | Emissions / odor / neighbor opposition |
| Possible char co-product | Tire chars often **not** soil-grade biochar without further treatment |

### Open-source / agent-editable angle
Mass/energy balance only after vendor heat/mass data. Do **not** auto-recommend purchase without a local environmental counsel checklist.

---

## 5. Biochar machines

### User link (fetched)
**Earthly Biochar Original Biochar Kiln** — **$1,299.00** (tax included where applicable; shipping calculated; ships worldwide from UK)  
https://www.earthlybiochar.com/en-us/products/biochar-kiln-make-biochar-at-home  

| Spec | Value |
|------|-------|
| Chamber | 25 L → **7–10 L biochar per burn** |
| Temp | 600–800 °C claimed |
| Cycle | ~1 hour; quench with water |
| Fit | Backyard / gardener; dual BBQ grate |

### Alternates
1. **Kon-Tiki (Finger Lakes Biochar, USA)** — **$1,125** pickup only (tilt **$1,250**; Kon-teeny demo **$650**) — https://fingerlakesbiochar.com/kontiki/  
   - Claims **5+ ft³ biochar in <2 hr** depending on feedstock.  
2. **Oregon Kiln (open shop drawings)** — **~$700** materials+labor (2017 estimate) — https://www.appropedia.org/Biochar_Kiln-Oregon_Kiln  
3. **Farm / forestry mobile:** **AirBurners CharBoss® T26** — purchase price **$152,121** (USDA-ARS economic analysis, as of June 2024) — https://www.ars.usda.gov/ARSUserFiles/60100500/Worksheets/Economic_Analysis_and_Profit_Potential_of_a_Mobile_Air_Curtain_Biochar_Processor.pdf  
   - ~0.296 t biochar/hr cited via USFS/USBI LCA in that paper; needs loader/excavator.  
4. **Biochar Now / Charm Industrial:** proprietary operators — **equipment generally not sold retail**; **contact for quote / partnership**.

### Yield / feedstock / Loop soil fit
- Feedstock: dry woody chips, prunings, ag residues (avoid treated/painted wood, high-Cl plastics).  
- **Loop nutrient loop:** charge biochar with compost / diluted algae effluent / recovered nutrients after cool-down; pairs with algae nutrient-density goal.  
- Local open-burn / air rules still apply to outdoor kilns.

### Approx CAPEX band
| Option | Band | Confidence |
|--------|------|------------|
| Earthly kiln | **$1,299** | High |
| Kon-Tiki FLB | **$1,125–$1,250** (+ pickup logistics) | High |
| Oregon Kiln DIY | **~$700** (2017 fab estimate) | Medium (dated) |
| CharBoss T26 | **$152,121** (Jun 2024 cited) | High for that model/date |
| Continuous industrial | **contact for quote** | — |

### Pros / cons
| Pros | Cons |
|------|------|
| Low Phase-0 cost; soil synergy | Backyard yield ≠ farm tons |
| Open designs (Oregon Kiln) agent-editable | Smoke / neighbor / burn permits |
| CharBoss scales forestry waste | Six-figure + excavator OPEX |

### Open-source / agent-editable angle
Oregon Kiln BOM on Appropedia (CC-BY-SA). Track feedstock → biochar volume; couple to algae/compost recipes under `algae/`.

---

## 6. Algae farming materials

### User link
**AlgaeSense Instructables** — https://www.instructables.com/AlgaeSense-Grow-Algae-Automatically-As-an-Off-Grid/  
**Fetch note:** Page is JS-heavy; automated fetch returned title only, not a full BOM. **Manual browser review required** for exact parts. Theme: off-grid automated algae as protein/nutrient source with ML.

### Recommended primary (community nutrient density)
**DIY raceway / IBC + drop-in lighting**, food-safe pathway first:

**Algae Research Supply — Algae Light Drop-In PBR**  
- AL200 (1×200 W light) from **$1,390.00**  
- Scales AL200→AL1000 (5 lights / ~1000 L / IBC-class)  
- User supplies tank; includes control box, dimmer, timer, GFCI  
- https://algaeresearchsupply.com/products/algae-light-photobioreactor  

Pair with: food-grade IBC or aquaculture tank, air pump + sparger, species-matched nutrients, harvest screen later.

### Alternates
1. **Industrial Plankton PBR 100L / 1250L / 2500L Dual** (Victoria, BC; ships NA) — closed PBR with CIP; **contact for quote** — https://industrialplankton.com/algae-photobioreactors-for-sale/  
2. **Open raceway** (liner + paddlewheel) — lowest $/m²; higher contamination risk — **estimate / contact for quote**.  
3. Lab PB250-class instruments — search snippets historically ~$2.7k–$6.8k; **re-verify live listing** before budgeting.

### BOM-style starter (DIY / AlgaeSense-class — **estimate**, not from rendered Instructables body)
| Item | Role | Rough band |
|------|------|------------|
| Clear tank / IBC / tubes | Culture volume | $50–$400 |
| Air pump + tubing + stone | Mixing / CO₂ | $30–$150 |
| LED grow / Algae Light | Photosynthesis | $200–$1,390+ |
| Sensors (pH, temp, OD) | Control | $50–$500 |
| Controller (RPi / MCU) | Automation | $35–$150 |
| Nutrients + inoculum | Growth | ongoing |
| Harvest (filter/settle) | Biomass | $20–$500 |

**Food-safe pathway:** edible species where regulated (*Chlorella*, *Spirulina*, etc.), food-contact materials, potable makeup water, hygiene plan. **Fuel pathway** is secondary and usually loses to nutrient/protein value at community scale.

### QSDsan / Loop tie-in
Existing stub: `algae/README.md` — **QSDsan / PM2** for nutrient mass-balance; couple effluent to `waste/` and `water/`. Extend `algae/cell.yaml` rather than invent parallel CSVs.

### Approx CAPEX band
| Scale | Band | Confidence |
|-------|------|------------|
| Bench / AlgaeSense-class DIY | **~$300–$2,000** | Medium (BOM estimate) |
| Drop-in lighted 200–1000 L | **$1,390+** lights (tank extra) | High for lights |
| Industrial PBR 100–2500 L | **contact for quote** | — |

### Pros / cons
| Pros | Cons |
|------|------|
| Aligns with Loop nutrient-density mission | Contamination in open ponds |
| Models in QSDsan | Food regulation if sold as food |
| Uses recovered N/P | Biofuel ROI weak at small scale |

---

## 7. Water: collection → storage → filtration → distribution

### Need
Community rain catchment and pressurized distribution that agents can model in **EPANET** (`water/stub.inp` today: reservoir R1 → junctions J1/J2, LPS units, no pumps/tanks yet).

### Recommended primary (community package)
**RainFlo complete in-ground systems** (US dealer):

| SKU | Listed price | Notes |
|-----|--------------|-------|
| RainFlo **5100-IG** | **$10,899.95** | Complete ~5,100 gal harvest system |
| RainFlo **5100-PRO** | **$21,499.95** | 2 hp VFD pump, monitoring, auto backup |
| RainFlo **10,200 gal** | **$26,299.95** | Commercial complete system |
| RainFlo **10,000 gal fiberglass** | **Price varies — call** | Custom config |
| Source | https://www.rainharvest.com/complete-systems/5000-10000-gallons.asp |

### Alternates / building blocks
1. **WISY Vortex roofwasher (first-flush / pre-filter)** — **$850.00** — up to ~5,500 sq ft roof; ~70% capture / 30% reject claimed — https://rainbrothers.com/products/rms-wisy-vortex-roofwasher-filter-up-to-5-500-sq-ft-1  
2. **Pressure distribution:** **Grundfos CMBE 3** booster — **$3,298.95** (+ $125 shipping listed) — constant pressure VFD; **flooded suction required** — https://rainwaterequipment.com/grundfos-cmbe-3-booster-constant-pressure-pump-system/  
3. **Poly / concrete / ferro cisterns** à la carte — **contact for quote** by gallon (5k–50k).  
4. **Potable train:** sediment → carbon → UV / membrane (add-on; WISY alone ≠ potable).

### Mapping to `water/stub.inp`
| Real asset | EPANET object to add |
|------------|----------------------|
| Cistern | `[TANKS]` with diameter/height or volume curve |
| Booster (CMBE / RainFlo VFD) | `[PUMPS]` + `[CURVES]` (head–flow) |
| First-flush / roof | Pattern / time-series inflow (WNTR) |
| Demand nodes | Expand `[JUNCTIONS]` beyond J1/J2 |
| UV/filter skid | Minor loss / quality (advanced) |

Agents: edit with **WNTR** in `/workspace/loopBiotek/.venv`; keep Units LPS consistent with stub.

### Approx CAPEX band (5k–50k gal class)
| Package | Band | Confidence |
|---------|------|------------|
| 5.1k gal complete IG | **$10,899.95** | High |
| 5.1k PRO | **$21,499.95** | High |
| 10.2k complete | **$26,299.95** | High |
| 50k gal community | **estimate / contact for quote** | Low |
| WISY pre-filter | **$850** | High |
| CMBE 3 pump | **$3,298.95** | High |

### Pros / cons
| Pros | Cons |
|------|------|
| Listed US packages | Potable compliance is jurisdiction-specific |
| EPANET/WNTR agent-friendly | Underground install ≠ DIY |
| Pairs with algae makeup water | Prefer clean metal roof for food-adjacent use |

### Open-source / agent-editable angle
**EPANET + WNTR + QGISRed** — primary digital twin. Store pump curves and tank geometry next to `stub.inp`.

---

## 8. Metal 3D printing

### Need
Community-fab metal parts for LoopBiotek repair hardware, Glass Sand tooling, algae fixtures, and water-fitting prototypes — without jumping straight to industrial powder-bed fusion (PBF).

### Technology ladder (community-realistic)
| Path | What it is | Fit |
|------|------------|-----|
| **Bound metal filament (FFF) + sinter** | Metal powder in polymer binder printed on (modified) FDM; debind + sinter to near-full density | **Phase 0–1 primary** |
| **Bound Metal Deposition / ADAM (Desktop Metal Studio, Markforged Metal X)** | Proprietary BMD/ADAM extrusion + wash/furnace stack | **Phase 1–2** if in-house sinter justified |
| **Binder jetting (e.g. Desktop Metal Shop)** | Powder + binder jet; industrial sinter train | Phase 2+ |
| **True powder-bed fusion (EOS, SLM, One Click Metal LPBF)** | Laser melts loose metal powder; inert gas, powder handling, facility | **Phase 2+ industrial only** |

### Recommended primary (Phase 0–1)
**BASF Forward AM Ultrafuse® 316L on an existing/open FDM + outsourced catalytic debind/sinter** (MatterHackers / DSH Technologies processing tickets).

| Spec | Value (vendor) |
|------|----------------|
| Material | ~80% 316L stainless in polymer binder; 1.75 or 2.85 mm; **3 kg** spool |
| Print | Hardened/abrasion-resistant nozzle; bed ~100–120 °C; extrusion ~230–250 °C; no part cooling |
| Shrinkage (design) | Scale ~**120% X/Y**, ~**126% Z** before print (MatterHackers guidance) |
| Post | Mail “green” parts + processing ticket → DSH Technologies debind/sinter → solid 316L returned |
| Filament list price | **$464.99** (Raise3D US store Ultrafuse 316L 3 kg) — https://www.raise3d.com/products/ultrafuse-316l/ |
| Processing | 1 ticket included with spool at MatterHackers; additional tickets historically ~**$50**/≤1 kg green (MakerBot LABS note citing MatterHackers); ticket catalog page may show stock gaps — **re-verify / contact** |
| Sources | https://www.matterhackers.com/store/l/basf-ultrafuse-316l-metal-composite-3d-printing-filament-175mm/sk/ME1E85HM · https://www.matterhackers.com/store/c/basf-ultrafuse-316l-processing-tickets |

**Near-equivalent / in-house sinter option:** **The Virtual Foundry Filamet™ 316L** (US, Stoughton WI) — print on open FDM + Filawarmer; sinter in programmable kiln.

| Item | Listed price | Source |
|------|--------------|--------|
| 316L Filamet 0.5 kg | **$210.99** | https://shop.thevirtualfoundry.com/products/stainless-steel-316l-filamet |
| 316L Filamet 1 kg | **$363.99** | same |
| Print & Sinter Kit (0.5 kg + Filawarmer + crucible + media) | **$514.95** | https://shop.thevirtualfoundry.com/products/stainless-steel-316l-filamet-print-and-sinter-kit |
| Print & Sinter Kit 1 kg | **$667.95** | same |
| TVF Sintering Kiln (7.5″ cube; 1288 °C; 120 V / 12 A) | **$4,499.99** | https://shop.thevirtualfoundry.com/products/the-virtual-foundry-sintering-kiln |
| FireX Max kiln (larger; 240 V) | **$5,199.99** | https://shop.thevirtualfoundry.com/products/firex-max-sintering-kiln |
| Claimed sintered density | ~**90–95%** with TVF process (vendor FAQ) | TVF product page |

### Alternates — desktop BMD / ADAM stacks
1. **Markforged Metal X (ADAM)** — printer SRP historically **~$99,500** (third-party capability PDFs / Metal AM reporting); full stack (Metal X + Wash-1 + Sinter-1/2 + install) customer cases **~$150k–$175k** (Markforged ROI blog: Shukla **$150k–$175k** all-in). **Contact for current quote.** Build ~250×220×200 mm class. https://markforged.com/resources/blog/roi-for-metal-3d-printers  
2. **Desktop Metal Studio System 2 (BMD)** — secondary catalogs historically cite complete system ~**$110,000**; other dealers show higher “estimated new” bands — **contact for quote**; verify current corporate/channel status before PO. https://facfox.com/docs/kb/how-much-does-a-metal-3d-printer-cost  
3. **Raise3D MetalFuse** (Forge1 + D200-E debind + S200-C sinter, Ultrafuse path) — dealer list **$149,999.00** — https://www.congeriem.com/raise3d-metalfuse.html  

### Phase 2+ — powder-bed fusion (note only)
| System | Notes | Price posture |
|--------|-------|---------------|
| **One Click Metal MPRINT** (entry LPBF) | Small-part / prototype LPBF; US store shows product but **“contact regional partner”** for price | **Contact for quote** — https://store.oneclickmetal.com/us-boldseries/mprint_805_2142/ · industry press cites ~€120k-class 500 W machines (not a PO price) |
| **EOS M 100 / SLM Solutions** | Industrial LPBF; powder handling, argon, EHS | Secondary indexes often **~$250k–$350k+** equipment — **contact for quote**; facility ≫ machine |

### Approx CAPEX band (USD)
| Option | Band | Confidence |
|--------|------|------------|
| Ultrafuse 3 kg + use existing FDM | **~$465** + tickets | High (Raise3D list) |
| TVF Filamet kit + existing FDM | **$515–$668** kits | High |
| TVF kiln (in-house sinter) | **$4,500–$5,200** | High |
| Raise3D MetalFuse stack | **$149,999** (dealer) | Medium (dealer list; confirm) |
| Markforged Metal X full system | **~$150k–$175k** case / **contact for quote** | Medium |
| Desktop Metal Studio 2 | **~$110k** secondary / **contact for quote** | Low–medium |
| One Click / EOS / SLM PBF | **contact for quote** (typically mid-six-figure+) | Low |

### Pros / cons for Loop
| Pros | Cons |
|------|------|
| Phase 0 metal without six-figure furnace | Shrinkage design discipline; sinter distortion risk |
| 316L fits water / outdoor hardware prototypes | Ultrafuse path depends on sinter-service schedule |
| Patterns for casting (lost-PLA / investment) | PBF powder + inert gas = facility project |
| Synergy with CNC finish-machining | BMD stacks are CAPEX-heavy vs filament+service |

### Open-source / agent-editable angle
Scale factors and sinter schedules as versioned JSON/CSV; green-part BOM mass for ticket sizing. Prefer Ultrafuse/TVF until repair-part volume justifies Metal X / MetalFuse / PBF.

---

## 9. Computer-controlled high-precision CNC

### Need
Primary **metal-cutting** CNC for community fab (brackets, shafts, molds, Glass Sand tooling), plus optional **wood/composite router** for fixtures and soft goods — clarifying that “high precision” means a machining center or rigid mill, **not** a hobby foam/wood router alone.

### Terminology
| Class | Examples | Typical use |
|-------|----------|-------------|
| **Metal machining center / CNC mill** | Tormach 1100M/770M, Haas Mini Mill, Langmuir MR-1 | Steel, stainless, Al, plastics |
| **Desktop / 5-axis proto mill** | Pocket NC V2-10, Carbide 3D Nomad 4 | Small Al/brass/plastic; limited steel |
| **CNC router** | ShopBot Desktop | Wood, plastic, soft Al engraving — **not** primary steel mill |

### Recommended primary (community metal CNC)
**Tormach 1100M** (Madison WI) — PathPilot; single-phase; steel-capable community workhorse.

| Spec | Value (vendor) |
|------|----------------|
| Starting price | **$14,995** |
| Travels | X **18″** / Y **11″** / Z **16.25″** |
| Spindle | **2 hp**, max **7,500 RPM**, R8 |
| Table | 34″ × 9.5″; max load 500 lb |
| Power | Single-phase **208–240 Vac**, 20 A, NEMA 6-20 |
| Enclosure | Open by default; ATC / RapidTurn optional |
| Assembly add-on | **$2,995** |
| Source | https://tormach.com/machines/mills/1100m.html |

### Alternates
1. **Tormach 770M** — **$11,995** start; travels 14″ × 7.5″ × 13.25″; **1.5 hp** / **10,000 RPM**; **115 Vac** 15 A — https://tormach.com/machines/mills/770m.html  
2. **Langmuir Systems MR-1** (Conroe TX) — gantry mill marketed for Al **and steel**; start **$5,195**; travels X **23.0″** / Y **21.8″** / Z **6.1″** (+2″ bonus); spindle **0–8,000 RPM**, ER-20; straightness claim **<0.00015″/in**; positional repeatability **<0.0005″**; machine ~750–900 lb; spindle often wants **240 Vac** — https://www.langmuirsystems.com/pages/mr1  
3. **Haas Mini Mill** — new industrial compact VMC; **contact Haas Build & Price** (secondary indexes cite new ~**$48k** class; used market often **~$12k–$25k+** by age/hours — **estimate / verify live listings**). Specs class: ~16″×12″×10″ travels historically; 10 hp-class spindle on current Mini Mill pages. https://www.haascnc.com/machines/vertical-mills/mini-mills/models/minimill.html  
4. **Carbide 3D Nomad 4** — **$5,400**; enclosed desktop; travels **10″×8″×3.5″**; **1.2 kW** VFD / **8,000–24,000 RPM** ER-16; Al/brass/plastic (not heavy steel) — https://shop.carbide3d.com/products/nomad-4  
5. **Penta Machine Pocket NC V2-10** — from **$7,499**; 5-axis desktop; travels X **4.55″** / Y **5.0″** / Z **3.55″**; soft steel/Al/Delrin — https://www.pentamachine.com/all-products/p/pocket-nc-v2-10  
6. **Precision Matthews PM-940M** — manual bed mill **$3,499–$5,499** (CNC conversion DIY/third-party) — https://www.precisionmatthews.com/products/pm-940m  
7. **Optional wood/soft router:** **ShopBot Desktop** — from **$9,972** (1 hp spindle + Al T-slot); XYZ move 25″×20″×5″; **120 Vac** — https://shopbottools.com/products/desktop/

### Approx CAPEX band (USD)
| Option | Band | Confidence |
|--------|------|------------|
| Langmuir MR-1 | **$5,195** (+ options/enclosure) | High |
| Nomad 4 | **$5,400** | High |
| Pocket NC V2-10 | **from $7,499** | High |
| Tormach 770M | **$11,995** (+$2,995 assembly) | High |
| Tormach 1100M | **$14,995** (+$2,995 assembly) | High |
| ShopBot Desktop (router) | **from $9,972** | High |
| PM-940M (manual) | **$3,499–$5,499** | High |
| Haas Mini Mill | New **contact for quote**; used **estimate ~$12k–$25k+** | Medium |

### Pros / cons for Loop
| Pros | Cons |
|------|------|
| CNC finishes castings & sinter prints | Coolant, chips, and training required |
| MR-1 / Tormach cut real steel brackets | Router ≠ steel production mill |
| Single-phase Tormach fits many shops | Haas used market condition risk |
| Patterns/molds for Glass Sand & casting | Enclosure / dust / noise budget |

### Open-source / agent-editable angle
Fusion 360 / FreeCAD → PathPilot or CutControl posts; keep tool library and workholding recipes in repo. Prefer **one metal mill first**; add ShopBot only if wood/composite fixture volume is high.

---

## 10. Metal casting + materials to recycle metals

### Need
Melt and pour recycled aluminum (primary), copper/brass (secondary), with patterns from CNC / plastic 3D print (lost-PLA) and optional glass-investment crossover for Glass Sand craft.

### Recommended primary (Phase 0 foundry kit)
**Propane melt furnace kit + Petrobond (oil-bonded) sand** — US retail, low CAPEX.

| Item | Listed price | Source |
|------|--------------|--------|
| **USA Cast Masters / Cast Master Elite 10 kg propane deluxe kit** (furnace + graphite crucible + tongs; tank not included) | Retail commonly listed **$199.99** (CastMasterEliteShop / Amazon ASIN family B08FF3HCLZ) — **re-verify live stock/price** | https://castmastereliteshop.com/products/10kg-propane-furnace-kit · https://www.amazon.com/Masters-CAPACITY-Crucible-Smelting-KILOGRAM/dp/B08FF3HCLZ |
| **PMC Supplies 5 kg propane furnace + Petrobond casting set** | **$474.95** (5 lb Petrobond) / **$479.95** (10 lb) | https://pmcsupplies.com/products/5-kg-propane-furnace-sand-casting-set-with-5-lbs-of-petrobond-mold-frame-safety-gloves-crucible-tongs |
| Petrobond 25 lb | **$69.95** | https://pmcsupplies.com/collections/petrobond |
| Petrobond 50 lb | **$132.95** | same |
| Quick Cast Master Kit (Petrobond, no furnace) | **$373.95** | same collection |

**Green sand** (clay–water bonded) is cheaper for bulk teaching molds; **Petrobond** gives finer detail and is reusable with care. **Lost-PLA / investment:** print PLA pattern → invest (e.g. Glass-Cast / plaster-silica systems already in §3) → burnout in kiln → pour. Pair CNC for match plates and permanent molds.

### Scrap recycling realism
| Metal | Reality for community fab |
|-------|---------------------------|
| **Aluminum cans / clean Al scrap** | Most realistic; melts ~660 °C; flux + skim dross; expect oxide losses |
| **Copper / brass** | Doable at higher temp; zinc fumes from brass — **ventilation critical** |
| **Steel / iron** | Much harder in small propane pots (temp, oxidation); prefer buy bar/drop or use sinter/CNC path |

### Safety (non-negotiable)
- PPE: face shield, leather apron, foundry gloves, closed-toe leather boots  
- Outdoor or **high-CFM ventilation**; never enclosed room without designed exhaust  
- **CO monitor** near combustion; propane leak check; keep extinguisher rated for surrounding combustibles  
- No wet tools into melt (steam explosion); dry scrap thoroughly  
- Silica hazard if using silica-rich investments — respirator + wet cleanup  

### Approx CAPEX band (USD)
| Path | Band | Confidence |
|------|------|------------|
| Cast Masters–class 10 kg kit alone | **~$200** listed retail | Medium (stock/price churn) |
| PMC 5 kg furnace + Petrobond set | **$475–$655** | High |
| Petrobond bulk 25–100 lb | **$70–$245** | High |
| Electric tabletop (QuikMelt-class bundles on PMC) | **~$635–$670** sets | High |
| Scaled foundry (lift-out furnace, pyrometer, dedicated hood) | **estimate / contact for quote** | Low |

### Pros / cons for Loop
| Pros | Cons |
|------|------|
| Turns Al scrap into brackets / tooling | Burn risk; zoning/fire code |
| CNC + print → patterns → cast multiples | Dimensional control weaker than CNC |
| Synergy with metal FFF patterns | Steel recycling not Phase 0 realistic |
| Glass Sand investment skills transfer | Fume / CO / silica controls |

### Open-source / agent-editable angle
Pour logs (alloy, charge mass, yield, scrap source) as CSV; pattern STL library shared with §8/§11. Checklist for PPE + CO monitor as a gate before any melt SOP.

---

## 11. Plastic 3D printer — varying firmness, textures, materials

### Need
**One primary FDM system** that can print plastics across firmness/texture (rigid PLA/PETG ↔ flexible TPU 85A–95A, multi-material soft+hard) for algae fixtures, water-fitting prototypes, Glass Sand jigs, and soft-touch interfaces — plus a **resin alternate** for Shore-tuned detail.

### Recommended primary (variable-property FDM)
**Bambu Lab H2D (dual-nozzle) + AMS 2 Pro** — true dual-nozzle soft+hard / support without single-nozzle purge waste; heated chamber for engineering plastics; TPU via direct extruder path.

| Spec | Value (vendor / US store) |
|------|---------------------------|
| Dual-nozzle volume | Dual ~**300×320×325 mm**; total two-nozzle envelope up to ~**350×320×325 mm** |
| Temp | Nozzle to **350 °C**; active chamber **65 °C** |
| Flexible | Direct-drive / servo extruder; TPU supported (follow wiki path; often external spool for softest grades) |
| AMS | AMS 2 Pro multi-material; up to many slots with adapters |
| US list (promo varies by SKU) | H2D seen **~$1,749–$1,949** on us.store.bambulab.com (typical higher); dealer West3D lists H2D from **$1,549** — **re-verify live combo SKU** |
| Sources | https://us.store.bambulab.com/products/h2d · https://west3d.com/products/bambu-lab-h2d-and-h2d-ams-combo-3d-printer |

**Why not only X1-Carbon AMS:** excellent multi-color rigid prints, but **single nozzle** → purge waste and weaker soft+hard simultaneous strategy vs H2D dual nozzles. X1C Combo still a budget alternate (Formlabs compare cites Combo **$1,449** historically — **re-check** Bambu store).

### Strong alternate (toolchanger)
**Original Prusa XL+ five-toolhead** — **$3,610.18** (assembled 5-head, US/EU store page at fetch); build **360×360×360 mm**; true toolchanger = rigid + TPU + soluble with near-zero purge — https://www.prusa3d.com/product/original-prusa-xl-5-toolhead-3d-printer/  
Enclosure / heater add-ons extra (**contact / list on Prusa site**).

### Other FDM mentions
- **UltiMaker S-line (S7/S8 class)** — professional dual extrusion; typically **~$6k–$8k+** dealer band — **contact for quote** / verify current S8 pricing.  
- **Snapmaker Artisan** — CNC/laser/print combo; less ideal as dedicated multi-firmness FDM primary.

### Recommended resin alternate (texture / Shore via chemistry)
**Formlabs Form 4 Basic Package** — **$2,625** (printer + tank + mixer + platform + finish kit); Complete Package **$5,749** (adds wash/cure automation) — https://formlabs.com/store/form-4/  
Flexible / Elastic / Soft resins map to Shore hardness ranges for seals, soft fixtures, and high-detail textures; IPA/wash + UV cure required. **Not** a substitute for large TPU lattice panels (use FDM).

### Approx CAPEX band (USD)
| Option | Band | Confidence |
|--------|------|------------|
| Bambu H2D (+ AMS) | **~$1,550–$2,250** depending on combo/promo | Medium–high (SKU churn) |
| Bambu X1C Combo | **~$1,200–$1,450** class | Medium (re-verify) |
| Prusa XL+ 5-head | **$3,610.18** | High (page price) |
| Form 4 Basic | **$2,625** | High |
| Form 4 Complete | **$5,749** | High |
| UltiMaker S-line | **estimate / contact for quote** | Medium |

### Pros / cons for Loop
| Pros | Cons |
|------|------|
| Soft gaskets + hard frames in one FDM job | Softest TPU still needs tuning |
| Resin for fine texture / Shore-specific parts | Resin OPEX + IPA/VOC handling |
| Fixtures for algae & water prototypes | Enclosure/filtration for ABS/ASA |
| Pairs with casting patterns (§10) | Large elastomeric panels → FDM not Form 4 |

### Open-source / agent-editable angle
Material profiles (Shore, modulus) as YAML next to STL; dual-extruder assignment conventions documented for agents. Prefer **H2D (or XL+)** as the “variable property” workhorse; Form 4 when surface/Shore chemistry matters more than size.

---

## Phased buy list

### Phase 0 — Pilot (validate loops, low regret)
| Priority | Item | Approx |
|----------|------|--------|
| 1 | Biochar: Earthly **$1,299** or Kon-Tiki **$1,125** | ~$1.1–1.3k |
| 2 | Glass: LGXEnzhuo crusher **$1,140** *or* quote Andela GP-Mini | ~$1.1k / quote |
| 3 | Glass finish: Paragon Fusion-14 **$2,160** + Econoline Mini blast **$1,119** | ~$3.3k |
| 4 | Algae: DIY + Algae Light AL200 **$1,390** | ~$1.5–2.5k |
| 5 | Water: WISY **$850** + poly cistern (quote) + basic filter | ~$1–5k+ |
| 6 | Cast molds: Glass-Cast investment **$42**/bag + kiln furniture | hundreds |
| 7 | **Fab-lab plastic:** Bambu **H2D** (+ AMS) **~$1.55k–$2.25k** | ~$1.6–2.3k |
| 8 | **Metal FFF entry:** Ultrafuse 316L **$465** *or* TVF Print & Sinter Kit **$515** (use H2D/FDM) | ~$0.5k |
| 9 | **Casting starter:** PMC 5 kg propane + Petrobond set **$475** *or* Cast Masters–class kit **~$200** + Petrobond | ~$0.2–0.5k |

**Rough Phase 0 total (sum of listed items only):** ~**$10,000–$18,000** excluding Andela, cistern earthwork, permits, and fab-lab CNC.  
**Fab-lab-only Phase 0 incremental (items 7–9):** ~**$2,300–$3,300** (H2D + metal filament kit + casting kit).  
**Confidence:** Medium–high on listed SKUs; low on site work.

### Phase 1 — Community fab
| Priority | Item | Approx |
|----------|------|--------|
| 1 | **Andela GP-Mini or MegaMini** | **contact for quote** |
| 2 | Evenheat GTS 24 **$4,752** + blast mid cabinet **$3,049** | ~$7.8k |
| 3 | RainFlo 5100-IG or 10,200 | **$10.9k–$26.3k** |
| 4 | Grundfos CMBE if not in package | **~$3.3k** |
| 5 | Algae scale-up (multi-IBC / Industrial Plankton 100L) | quote |
| 6 | Babyplast / used benchtop injection *if* polymer products proven | **$10k–$35k** used guide |
| 7 | Farm biochar (multiple Kon-Tiki or Oregon Kilns) | ~$1–5k |
| 8 | **Primary metal CNC:** Tormach **1100M $14,995** (or **770M $11,995** / **MR-1 $5,195**) | ~$5k–$18k |
| 9 | **In-house metal sinter (optional):** TVF kiln **$4,500–$5,200** *or* keep Ultrafuse service tickets | ~$0–5.2k |
| 10 | **Resin alternate:** Form 4 Basic **$2,625** (or Complete **$5,749**) | ~$2.6–5.7k |
| 11 | **Optional wood router:** ShopBot Desktop from **$9,972** | if fixture volume warrants |
| 12 | Casting scale-up: more Petrobond, flasks, pyrometer, dedicated hood | hundreds–low thousands |

**Rough Phase 1 incremental (listed only):** ~**$35,000–$90,000+** plus Andela quote + injection if pursued.  
**Fab-lab-only Phase 1 incremental (CNC + optional kiln + Form 4, assuming Phase 0 plastic/metal-FFF/cast done):** ~**$13,000–$28,000** (MR-1 or Tormach-centric; exclude ShopBot unless needed).  
**Confidence:** Medium (Andela unknown; CNC choice drives band).

### Phase 2 — Industrial / multi-community
| Priority | Item | Approx |
|----------|------|--------|
| 1 | Andela GP-05L → GP-1HD / GP-2HD | **contact for quote** |
| 2 | Pyrolysis only with **air permit path** (GEP portable page **$57.1k–$285.7k** or Beston batch from **$67k** + US compliance) | equipment + **much larger** compliance |
| 3 | CharBoss T26 **$152,121** (+ excavator) *or* continuous biochar partner | ~$150k+ |
| 4 | Industrial Plankton 1250–2500 L | **contact for quote** |
| 5 | 50k gal water + potable treatment + full EPANET model | **estimate / contact for quote** |
| 6 | Hot-glass press / IS — only with offtake contracts | **contact for quote** |
| 7 | **Bound-metal stack:** Markforged Metal X system **~$150k–$175k** case / Raise3D MetalFuse **$149,999** / Desktop Metal Studio **contact** | ~$110k–$180k |
| 8 | **PBF metal:** One Click Metal / EOS / SLM | **contact for quote** (typically mid-six-figure+ + facility) |
| 9 | **Haas-class VMC** (new Mini Mill or used production mill) | new **contact**; used **estimate** |

**Rough Phase 2:** **$250,000–$1,200,000+** depending on pyrolysis/compliance and whether metal PBF/BMD is pursued.  
**Confidence:** Low (dominated by quotes and permits).

---

## Rough total CAPEX bands (per phase)

| Phase | Sum of **quoted/listed** items in this doc | Dominant unknowns | Confidence |
|-------|--------------------------------------------|-------------------|------------|
| **0 Pilot** | ~**$10,000–$18,000** (incl. fab-lab plastic/metal-FFF/cast starters) | Cistern size, electrical, dust controls | **Medium–high** |
| **0 Fab-lab only (incremental)** | ~**$2,300–$3,300** | Exact H2D combo SKU, furnace kit stock | **Medium–high** |
| **1 Community** | ~**$35,000–$90,000** + Andela | Andela, CNC tier (MR-1 vs Tormach), injection | **Medium** |
| **1 Fab-lab only (incremental)** | ~**$13,000–$28,000** | CNC primary choice; Form 4 vs defer; TVF kiln | **Medium** |
| **2 Industrial** | **$250,000–$1,200,000+** | Permits, pyrolysis APC, metal PBF/BMD, large Andela | **Low** |

Label in finance sheets as: `source=INVESTMENT_SHORTLIST.md; date=2026-09-25; verify_before_PO=true`.

---

## Synergy notes

| Loop | Synergy |
|------|---------|
| **Glass sand ↔ Glass Sand business** | Andela/GP-Mini output is the core SKU; kiln + blast turns fines/frit into craft goods; abrasive-grade fines are a premium bagged line (Andela marketing cites $150–$1,000/ton — revenue context, not a purchase price). |
| **Pyrolysis / biochar ↔ soil / energy** | Prefer **biochar-first** (Earthly/Kon-Tiki → CharBoss) for soil carbon + nutrient charging with algae/compost. Treat tire/plastic pyrolysis as a **separate industrial track** with oil offtake and air permits — do not assume char is soil-grade. |
| **Algae ↔ Loop nutrients** | Primary value is **protein / nutrient density** and N/P recovery (QSDsan). Biofuel is secondary only. Soft FDM fixtures + resin seals (§11) hold tubing and sensors. |
| **Water ↔ EPANET** | Buy RainFlo/WISY/Grundfos with **modelable** tanks and pump curves; extend `water/stub.inp` in lockstep with install so agents can stress-test drought and peak demand. Prototype fittings on H2D / CNC before committing SKUs. |
| **Fab lab: CNC + casting + metal print + plastic print** | **Plastic print** → soft/hard fixtures & lost-PLA patterns → **cast** Al repair parts → **CNC** finish critical faces/threads → **metal FFF/sinter** for stainless one-offs that casting cannot hit. Glass Sand tooling (screens, chutes, blast nozzles) and algae PBR brackets are shared CAD across all four. |

---

## Top recommended SKU / product per category

| # | Category | Top pick | Why |
|---|----------|----------|-----|
| 1 | Glass-to-sand | **Andela GP-Mini** (quote) | US-built, rounded sand, pilot-scale; DIY crusher only for experiments |
| 2 | “Sand blast oven” | **Paragon Fusion-14** + **Econoline 101696R-A** | Clarified as kiln + cabinet; both have live USD prices |
| 3 | Glass “injection” | **Kiln-cast + Glass-Cast 400** first | Realistic fab path before Babyplast / hot-glass |
| 4 | Pyrolysis | **GEP portable ($57.1k–$285.7k page)** only after US permit feasibility; else **defer** | Price exists; compliance dominates |
| 5 | Biochar | **Earthly Biochar Kiln $1,299** (or **Kon-Tiki $1,125** if pickup OK) | Immediate soil-loop pilot |
| 6 | Algae | **Algae Light Drop-In from $1,390** + food-grade tank | Nutrient-density; Instructables BOM needs manual scrape |
| 7 | Water | **RainFlo 5100-IG $10,899.95** (+ **WISY $850** if roof pre-filter separate) | EPANET-mappable community package |
| 8 | Metal 3D print | **Ultrafuse 316L (~$465) + sinter service** (or **TVF kit $515** + optional kiln **$4,500**) | Phase 0 metal without six-figure BMD/PBF |
| 9 | High-precision CNC | **Tormach 1100M $14,995** (budget: **MR-1 $5,195**) | Real metal mill for community fab; router optional later |
| 10 | Metal casting / recycle | **PMC 5 kg propane + Petrobond set $474.95** | Listed US kit; Al-can melting realistic with PPE/ventilation |
| 11 | Variable-property plastic print | **Bambu Lab H2D (+ AMS)**; resin: **Form 4 Basic $2,625** | Dual-nozzle soft+hard; Form 4 for Shore/texture detail |

---

## Key cited URLs (index)

- Andela GP-Mini: https://andelaproducts.com/complete-systems/glass-pulverizer-systems/gp-mini-system/  
- Andela systems overview: https://andelaproducts.com/complete-systems/glass-pulverizer-systems/  
- Andela FAQ: https://andelaproducts.com/faqs/  
- LGXEnzhuo crusher: https://jumboindustrial.com/products/lgxenzhuo-glass-bottle-crusher-220v-2-5kw-with-3mm-6mm-10mm-screens/  
- Econoline Mini: https://www.jmesales.com/econoline-mini-blast-cabinet-steel-120-psi/  
- Econoline 101696R-A: https://www.globalindustrial.com/p/42x24-abrasive-blast-cabinet-siphon-101696r-a  
- Paragon Fusion-14: https://paragonkilns.com/products/fusion14-glass-fusing-kiln  
- Evenheat GTS 24: https://modernpotters.com/products/evenheat-gts-24-glass-kiln  
- Meadoworks desktop IMM guide: https://www.meadoworks.com/resources/desktop-injection-molding-machine-guide  
- Babyplast: https://www.babyplast.com/  
- Glass-Cast 400: https://shop.sculpt.com/products/glass-cast-400-investment  
- GEP portable pyrolysis: https://www.aishred.com/product/portable-pyrolysis-plant.html  
- Beston pyrolysis cost: https://www.bestongroup.com/pyrolysis-plant/cost/  
- Earthly Biochar kiln: https://www.earthlybiochar.com/en-us/products/biochar-kiln-make-biochar-at-home  
- Kon-Tiki FLB: https://fingerlakesbiochar.com/kontiki/  
- Oregon Kiln: https://www.appropedia.org/Biochar_Kiln-Oregon_Kiln  
- CharBoss economics (USDA): https://www.ars.usda.gov/ARSUserFiles/60100500/Worksheets/Economic_Analysis_and_Profit_Potential_of_a_Mobile_Air_Curtain_Biochar_Processor.pdf  
- AlgaeSense: https://www.instructables.com/AlgaeSense-Grow-Algae-Automatically-As-an-Off-Grid/  
- Algae Light PBR: https://algaeresearchsupply.com/products/algae-light-photobioreactor  
- Industrial Plankton: https://industrialplankton.com/algae-photobioreactors-for-sale/  
- RainFlo 5–10k: https://www.rainharvest.com/complete-systems/5000-10000-gallons.asp  
- WISY Vortex: https://rainbrothers.com/products/rms-wisy-vortex-roofwasher-filter-up-to-5-500-sq-ft-1  
- Grundfos CMBE 3: https://rainwaterequipment.com/grundfos-cmbe-3-booster-constant-pressure-pump-system/  
- Raise3D Ultrafuse 316L: https://www.raise3d.com/products/ultrafuse-316l/  
- MatterHackers Ultrafuse 316L: https://www.matterhackers.com/store/l/basf-ultrafuse-316l-metal-composite-3d-printing-filament-175mm/sk/ME1E85HM  
- Ultrafuse processing tickets: https://www.matterhackers.com/store/c/basf-ultrafuse-316l-processing-tickets  
- Virtual Foundry 316L Filamet: https://shop.thevirtualfoundry.com/products/stainless-steel-316l-filamet  
- Virtual Foundry Print & Sinter Kit: https://shop.thevirtualfoundry.com/products/stainless-steel-316l-filamet-print-and-sinter-kit  
- Virtual Foundry Sintering Kiln: https://shop.thevirtualfoundry.com/products/the-virtual-foundry-sintering-kiln  
- Raise3D MetalFuse (dealer): https://www.congeriem.com/raise3d-metalfuse.html  
- Markforged Metal X ROI: https://markforged.com/resources/blog/roi-for-metal-3d-printers  
- One Click Metal MPRINT store: https://store.oneclickmetal.com/us-boldseries/mprint_805_2142/  
- Tormach 1100M: https://tormach.com/machines/mills/1100m.html  
- Tormach 770M: https://tormach.com/machines/mills/770m.html  
- Langmuir MR-1: https://www.langmuirsystems.com/pages/mr1  
- Carbide 3D Nomad 4: https://shop.carbide3d.com/products/nomad-4  
- Pocket NC V2-10: https://www.pentamachine.com/all-products/p/pocket-nc-v2-10  
- ShopBot Desktop: https://shopbottools.com/products/desktop/  
- Precision Matthews PM-940M: https://www.precisionmatthews.com/products/pm-940m  
- Haas Mini Mill: https://www.haascnc.com/machines/vertical-mills/mini-mills/models/minimill.html  
- PMC Petrobond / casting kits: https://pmcsupplies.com/collections/petrobond  
- PMC 5 kg furnace casting set: https://pmcsupplies.com/products/5-kg-propane-furnace-sand-casting-set-with-5-lbs-of-petrobond-mold-frame-safety-gloves-crucible-tongs  
- Cast Master Elite 10 kg kit: https://castmastereliteshop.com/products/10kg-propane-furnace-kit  
- Bambu Lab H2D (US): https://us.store.bambulab.com/products/h2d  
- Prusa XL+ 5-head: https://www.prusa3d.com/product/original-prusa-xl-5-toolhead-3d-printer/  
- Formlabs Form 4 store: https://formlabs.com/store/form-4/  

---

*End of shortlist. Re-verify all prices on the cited pages before purchase orders.*
