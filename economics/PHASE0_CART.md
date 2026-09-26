# LoopBiotek Phase 0 — Buy-ready cart

**Date:** 2026-09-25  
**Rule:** Re-check live prices before PO. Do not treat this as a purchase order.  
**Full research:** [INVESTMENT_SHORTLIST.md](./INVESTMENT_SHORTLIST.md)

Buy in this order (dependencies + learning curve). Hold pyrolysis, Andela full system, and Tormach until Phase 1.

## Cart (recommended buy now)

| # | Item | Why now | Approx USD | Buy link |
|---|------|---------|------------:|----------|
| 1 | **Earthly Biochar Kiln** | Soil loop + charge with algae/compost; ships worldwide | **1,299** | https://www.earthlybiochar.com/en-us/products/biochar-kiln-make-biochar-at-home |
| 1b | *Alt (US pickup):* Kon-Tiki | Same role, Finger Lakes Biochar | **1,125** pickup | https://fingerlakesbiochar.com/kontiki/ |
| 2 | **Bambu Lab H2D** (+ AMS if offered) | Variable firmness/texture plastics; also prints metal-filament green parts | **~1,550–2,250** | https://us.store.bambulab.com/products/h2d |
| 3 | **TVF 316L Print & Sinter Kit** *or* Ultrafuse 316L 3 kg | Metal parts without six-figure printer | **515** / **465** | https://shop.thevirtualfoundry.com/products/stainless-steel-316l-filamet-print-and-sinter-kit · https://www.raise3d.com/products/ultrafuse-316l/ |
| 4 | **PMC 5 kg propane + Petrobond set** | Recycle Al scrap; patterns from H2D | **~475** | https://pmcsupplies.com/products/5-kg-propane-furnace-sand-casting-set-with-5-lbs-of-petrobond-mold-frame-safety-gloves-crucible-tongs |
| 5 | **Paragon Fusion-14** kiln | Glass fuse/slump/anneal; Glass Sand craft SKUs | **2,160** | https://paragonkilns.com/products/fusion14-glass-fusing-kiln |
| 6 | **Econoline Mini blast cabinet** | Etch/finish glass (use glass bead — not silica sand) | **1,119** | https://www.jmesales.com/econoline-mini-blast-cabinet-steel-120-psi/ |
| 7 | **Glass-Cast 400** (1–2 bags) | Kiln-cast molds for glass products | **42**/bag | https://shop.sculpt.com/products/glass-cast-400-investment |
| 8 | **LGXEnzhuo glass bottle crusher** | Pilot glass→sand until Andela quote | **1,140** | https://jumboindustrial.com/products/lgxenzhuo-glass-bottle-crusher-220v-2-5kw-with-3mm-6mm-10mm-screens/ |
| 9 | **Algae Light Drop-In AL200** | Nutrient-density PBR light; buy food-grade tank separately | **1,390**+ | https://algaeresearchsupply.com/products/algae-light-photobioreactor |
| 10 | **WISY Vortex roofwasher** | First-flush / pre-filter for community rain | **850** | https://rainbrothers.com/products/rms-wisy-vortex-roofwasher-filter-up-to-5-500-sq-ft-1 |

### Food-grade tank (algae) — buy with #9
Any food-grade IBC / clear aquaculture tank (~$50–$400 retail). Not locked to one SKU.

### Optional same-week (if roof + cistern ready)
| Item | Approx | Link |
|------|--------:|------|
| RainFlo **5100-IG** complete ~5.1k gal | **10,900** | https://www.rainharvest.com/complete-systems/5000-10000-gallons.asp |

Skip RainFlo until pad/roof design is locked; WISY alone is fine to stage.

## Hold (Phase 1 — do not buy yet)
| Item | Why wait | Next step |
|------|----------|-----------|
| Andela GP-Mini | Custom quote; overkill until pilot crush data | Request estimate: https://andelaproducts.com/complete-systems/glass-pulverizer-systems/gp-mini-system/ |
| Tormach 1100M / MR-1 | Needs shop power, pad, tooling budget | After H2D + casting prove repair-part demand |
| GEP / Beston pyrolysis | Air permits ≫ machine | Local AHJ consult first |
| Babyplast / Form 4 / TVF kiln | After product-market signal | — |

## Money check
| Bundle | Sum of listed Phase-0 cart (#1–10, Earthly not Kon-Tiki, TVF kit not Ultrafuse, no RainFlo) |
|--------|-------------:|
| **Core Phase 0** | ~**$10,000–$12,000** before tax/shipping/compressor for blast cabinet |
| **+ RainFlo 5100-IG** | ~**$21,000–$23,000** |
| Confidence | Medium–high on list prices; **re-verify** Bambu H2D combo SKU live |

## Shop readiness (same week as deliveries)
- 120 V circuits for kiln + printers; propane outdoors for casting (CO / fire code)
- Compressor for blast cabinet (often separate ~$300–$800)
- PPE: respirator (silica / investment), leather foundry gear, kiln gloves
- Dust plan for glass crush (OSHA silica)

## Agent follow-ups after buy
1. Log serials + invoices under `economics/purchases/` (create when first PO lands)
2. Extend `algae/cell.yaml` with tank volume once IBC chosen
3. Keep IFC/STL for printed fixtures in `buildings/models/` and a new `fab/` folder when CNC arrives
