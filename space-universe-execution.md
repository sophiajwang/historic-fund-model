# Space Sector — Universe Construction Execution
## Stages 1–3: Seed, Screen, Classify

---

## Stage 1: Seed — Candidate List by Source

### Source A: ETF Constituent Pulls

**⚠️ ACTION REQUIRED:** Download current holdings CSVs from:
- UFO: procureetfs.com/ufo (S-Network Space Index)
- ARKX: ark-funds.com/funds/arkx (daily holdings CSV)
- ROKT: ssga.com (search ROKT, download holdings)

**Below is the candidate list based on known holdings as of my last training data. The live pull will catch any additions/removals since then.**

#### UFO ETF (Procure Space ETF) — S-Network Space Index
*Index methodology: companies must derive ≥50% revenue from space-related activities, or be identified as a "non-pure play" with significant space exposure (capped at 40% of index weight).*

| Company | Ticker | Sub-category (per index) | Notes |
|---|---|---|---|
| Rocket Lab USA | RKLB | Pure-play | |
| Planet Labs | PL | Pure-play | |
| Spire Global | SPIR | Pure-play | |
| BlackSky Technology | BKSY | Pure-play | |
| Iridium Communications | IRDM | Pure-play | |
| Globalstar | GSAT | Pure-play | |
| EchoStar / DISH | SATS / DISH | Pure-play (comms) | Merged 2024 |
| Viasat | VSAT | Pure-play (comms) | |
| AST SpaceMobile | ASTS | Pure-play | |
| Redwire | RDW | Pure-play | |
| Intuitive Machines | LUNR | Pure-play | |
| Terran Orbital | LLAP | Pure-play | Acquired by LMT 2024 |
| Momentus | MNTS | Pure-play | Delisted 2024 |
| Virgin Orbit | VORB | Pure-play | Bankrupt 2023 |
| Astra Space | ASTR | Pure-play | Delisted/near-failure |
| Satellogic | SATL | Pure-play | Argentina-founded, US-listed |
| Maxar Technologies | MAXR | Pure-play | Acquired by Advent 2023 |
| Lockheed Martin | LMT | Non-pure-play | Will screen out (conglomerate) |
| Northrop Grumman | NOC | Non-pure-play | Will screen out (conglomerate) |
| Boeing | BA | Non-pure-play | Will screen out (conglomerate) |
| L3Harris | LHX | Non-pure-play | Will screen out (conglomerate) |
| RTX (Raytheon) | RTX | Non-pure-play | Will screen out (conglomerate) |
| Garmin | GRMN | Non-pure-play | Will screen out (downstream consumer) |
| Trimble | TRMB | Non-pure-play | Will screen out (downstream consumer) |

#### ARKX (ARK Space Exploration & Innovation ETF)
*ARK uses active management, broader definition of "space" including enablers. Many holdings are NOT space companies — they're adjacent tech.*

| Company | Ticker | Likely Screen Result | Notes |
|---|---|---|---|
| Rocket Lab USA | RKLB | ✅ In | Overlap with UFO |
| Iridium | IRDM | ✅ In | Overlap |
| Trimble | TRMB | ❌ Out | GPS consumer, not space |
| Kratos Defense | KTOS | ⚠️ Borderline | Satellite comms, drone, defense — needs revenue check |
| L3Harris | LHX | ❌ Out | Conglomerate |
| AeroVironment | AVAV | ❌ Out | Primarily drones, not space |
| Blade Air Mobility | BLDE | ❌ Out | Urban air mobility, not space |
| 3D Systems | DDD | ❌ Out | 3D printing, not space |
| Komatsu | KMTAY | ❌ Out | Construction equipment |
| Deere & Co | DE | ❌ Out | Agriculture (precision ag uses GPS — downstream) |
| Unity Software | U | ❌ Out | Simulation — space-adjacent at best |

*ARKX has a very loose definition of "space." Most of its unique holdings will screen out. Its primary value in our process is confirming the pure-plays that overlap with UFO.*

#### ROKT (SPDR S&P Kensho Final Frontiers)
*Kensho uses NLP to scan filings for space/deep-sea keywords. Broader net, noisier results.*

| Company | Ticker | Likely Screen Result | Notes |
|---|---|---|---|
| Rocket Lab | RKLB | ✅ In | Overlap |
| Planet Labs | PL | ✅ In | Overlap |
| Parsons Corp | PSN | ⚠️ Borderline | Defense/infra, some space contracts |
| HEICO | HEI | ❌ Out | Aerospace components, space is minor |
| Mercury Systems | MRCY | ⚠️ Borderline | Defense electronics, some space |
| BWX Technologies | BWXT | ⚠️ Borderline | Nuclear propulsion for space, but primarily naval reactors |

**⚠️ Borderline companies flagged for Stage 2 revenue-split review:** Kratos (KTOS), Parsons (PSN), Mercury Systems (MRCY), BWX Technologies (BWXT)

---

### Source B: SIC/NAICS Code Pull from EDGAR

**⚠️ ACTION REQUIRED:** Run the following queries on EDGAR full-text search (efts.sec.gov/LATEST/search-index):
- SIC 3761 (Guided Missiles & Space Vehicles)
- SIC 3764 (Space Propulsion Units & Parts)
- SIC 3769 (Space Vehicle Equipment NEC)
- SIC 4899 (Communications Services NEC) — filter manually for satellite
- SIC 3812 (Search, Detection, Navigation Equipment) — filter manually for space

**Companies I expect this to surface that are NOT already in Source A:**

| Company | SIC | Status | Notes |
|---|---|---|---|
| Orbital Sciences | 3761 | Acquired by Northrop 2015 | Historical — important exit |
| SpaceDev | 3761 | Acquired by Sierra Nevada 2008 | Historical |
| GenCorp / Aerojet Rocketdyne | 3764 | Acquired by L3Harris 2023 | ~$4.7B — significant space propulsion exit |
| Raytheon (pre-merger) | 3812 | Merged into RTX 2020 | Conglomerate — screen out |

*SIC codes will also surface many non-space defense companies (SIC 3812 is very broad). Expect ~60-70% of results from 3812 to screen out. The high-value codes are 3761, 3764, 3769 which are space-specific.*

**⚠️ NOTE:** Many "new space" companies file under generic SIC codes. For example:
- SpaceX files as SIC 3761 ✅ (but is private, so won't appear in public company EDGAR search for 10-Ks — look for their bond/debt filings)
- Rocket Lab filed under 3761 ✅
- Planet Labs filed under 3812 (generic)
- AST SpaceMobile filed under 4899 (generic comms)

This is why SIC codes alone are insufficient — Sources C and D are essential.

---

### Source C: Industry Report Pulls

#### Space Capital Quarterly Reports
**⚠️ ACTION REQUIRED:** Download latest Space Capital quarterly report from spacecapital.com. They categorize companies into:
- **Infrastructure:** Launch, satellites, ground systems
- **Distribution:** Satellite comms, IoT
- **Application:** EO, analytics, geospatial

**Private companies identified from Space Capital's published data and coverage:**

| Company | Sub-sector | Last Known Valuation | Founded | Source |
|---|---|---|---|---|
| SpaceX | Launch / Comms | ~$350B (Dec 2024 tender) | 2002 | Widely reported secondary pricing |
| Blue Origin | Launch / Human Spaceflight | N/A (Bezos-funded, not formally valued) | 2000 | Press |
| Sierra Space | Space Stations / Cargo | ~$5.3B (Series B, 2023) | 2021 (spun from SNC) | Press release |
| Relativity Space | Launch | ~$4.2B (Series E, 2022) | 2015 | Press release |
| Firefly Aerospace | Launch | ~$2.5B (2023 valuation) | 2014 | Press |
| Impulse Space | In-Space Transport | ~$1.2B (2024) | 2021 | Press |
| Stoke Space | Launch (reusable upper stage) | ~$1B+ (2024) | 2019 | Press |
| ABL Space Systems | Launch | ~$2.4B (2022) | 2017 | Press — subsequent difficulties |
| Hawkeye 360 | RF Analytics / EO | ~$700M+ (est.) | 2015 | Press |
| Umbra | SAR EO | ~$400M+ (est.) | 2015 | Press |
| BlackBridge / Planet (pre-IPO) | EO | N/A — went public | 2010 | Historical |
| Capella Space | SAR EO | ~$800M+ (est.) | 2016 | Press |
| HawkEye 360 | RF Geospatial | ~$700M+ (est.) | 2015 | Press |
| Muon Space | EO (Climate) | Early stage (~$100M+) | 2021 | Press |
| True Anomaly | Space Domain Awareness | ~$1B+ (est. 2024) | 2022 | Press |
| Varda Space Industries | In-Space Manufacturing | ~$1B+ (est.) | 2020 | Press |
| Apex (formerly Apex Space) | Satellite Buses | ~$350M+ (est.) | 2022 | Press |
| K2 Space | Large Satellite Buses | Early stage | 2022 | Press |
| Phantom Space | Launch (low-cost) | Early stage | 2019 | Press |
| Astranis | GEO Comms (small sats) | ~$1.4B (2023) | 2015 | Press |
| Pixxel | Hyperspectral EO | ~$300M+ (est.) | 2019 | India-founded — **may screen out as non-US** |
| Sidus Space | In-Space Mfg / EO | Small-cap public (OTC) | 2012 | May fail materiality screen |
| York Space Systems | Satellite Manufacturing | Acquired by Voyager Space 2022 | 2012 | Press |
| Voyager Space | Space Stations / Holding Co | Private | 2019 | Starlab station with Airbus |
| Anduril Industries | Defense (incl. space) | ~$14B (2024) | 2017 | ⚠️ Borderline — space is growing but minority of revenue |
| Shield AI | Autonomy (some space) | ~$5B (2024) | 2015 | ⚠️ Likely screens out — primarily drone/aircraft AI |
| Slingshot Aerospace | Space Domain Awareness / Software | ~$200M+ (est.) | 2017 | Press |
| Kayhan Space | Space Traffic Mgmt Software | Early stage | 2018 | May fail materiality threshold |
| LeoLabs | Space Domain Awareness | ~$200M+ (est.) | 2016 | Press |
| Orbit Fab | In-Space Refueling | Early stage | 2018 | May fail materiality threshold |
| Vast | Space Stations | ~$1B+ (est. 2024) | 2021 | Press |
| Axiom Space | Space Stations / Crew | ~$3.3B+ (est. 2024) | 2016 | Press |

#### BryceTech Startup Space Report
**⚠️ ACTION REQUIRED:** Download latest report from brycetech.com. Cross-reference with above list. BryceTech tracks ~250+ venture-funded space companies globally; filter to US.

**Companies likely surfaced by BryceTech but not yet listed above:**
- Multiple early-stage companies below our $10M materiality threshold
- Historical failures (see Source D below)

#### NASA SBIR/STTR Database
**⚠️ ACTION REQUIRED:** Search sbir.nasa.gov for all SBIR/STTR awards. This will surface small companies that received NASA innovation grants but may not have raised venture capital. Most will fail the materiality screen but some may have grown.

**Companies I expect this to surface that aren't above:**
- Phase Four (now Exoterra) — in-space propulsion
- Tethers Unlimited (now Amergent Techs) — in-space manufacturing
- Made In Space — acquired by Redwire 2020
- Deep Space Industries — acquired by Bradford Space 2019
- Numerous sub-threshold companies

---

### Source D: SPAC & Historical Failures

#### Completed Space SPACs (comprehensive)
| Company | SPAC Partner | Merger Date | Initial EV ($M) | Current Status | Notes |
|---|---|---|---|---|---|
| Rocket Lab | Vector Acquisition | Aug 2021 | ~$4,100 | Active (RKLB) | |
| Planet Labs | dMY Technology VI | Dec 2021 | ~$2,800 | Active (PL) | |
| Spire Global | NavSight Holdings | Aug 2021 | ~$1,600 | Active (SPIR) | |
| BlackSky Technology | Osprey Technology | Sep 2021 | ~$1,500 | Active (BKSY) | |
| AST SpaceMobile | New Providence Acq | Apr 2021 | ~$1,800 | Active (ASTS) | |
| Terran Orbital | Tailwind Two | Mar 2022 | ~$1,580 | Acquired by LMT 2024 | |
| Redwire | Genesis Park Acq | Sep 2021 | ~$615 | Active (RDW) | |
| Momentus | Stable Road Acq | Aug 2021 | ~$1,200 | Delisted 2024 | SEC fraud charges against founder |
| Virgin Orbit | NextGen Acq II | Dec 2021 | ~$3,200 | Bankrupt Apr 2023 | LauncherOne failure |
| Astra Space | Holicity | Jul 2021 | ~$2,100 | Delisted / near-failure | Multiple launch failures, pivoting |
| Satellogic | CF Acquisition VIII | Jan 2022 | ~$1,100 | Active (SATL) | Argentina-founded |
| Blade Air Mobility | Experience Investment | May 2021 | ~$825 | Active but screens out | Urban air mobility, not space |
| Archer Aviation | Atlas Crest | Sep 2021 | ~$3,800 | Active but screens out | eVTOL, not space |
| Joby Aviation | Reinvent Technology | Aug 2021 | ~$6,600 | Active but screens out | eVTOL, not space |

#### Historical Space Company Failures (pre-SPAC era)
| Company | Sub-sector | Founded | Failure Year | Notes |
|---|---|---|---|---|
| Kistler Aerospace | Launch | 1993 | 2003 (bankruptcy) | Attempted reusable launch |
| Rotary Rocket | Launch | 1996 | 2001 | Novel concept, never flew |
| Beal Aerospace | Launch | 1997 | 2000 | Shut down, cited NASA competition |
| Sea Launch | Launch | 1995 | 2009 (bankruptcy), 2014 (2nd bankruptcy) | Ocean-based launch — US/intl JV |
| Teledesic | Comms Constellation | 1994 | 2002 | Bill Gates-backed, pre-Starlink concept |
| ICO Global / Pendrell | Comms | 1995 | Multiple restructurings | |
| LightSquared / Ligado | Comms (Spectrum) | 2010 | 2012 bankruptcy, restructured | GPS interference issues |
| Loral Space & Communications | Comms / Satellites | 1996 | 2003 bankruptcy, restructured, acquired by Telesat 2012 | |
| Orbcomm | IoT / M2M Comms | 1993 | Active but went through bankruptcy 2000, re-IPO 2004 | Still active |
| GeoEye | Earth Observation | 2004 (renamed) | Acquired by DigitalGlobe 2013 | ~$900M |
| DigitalGlobe | Earth Observation | 1992 | Acquired by Maxar 2017 | ~$2.4B |
| Maxar Technologies | EO / Satellites | 2017 (formed via MDA merger) | Acquired by Advent 2023 | ~$6.4B |
| Vector Launch | Launch | 2016 | 2019 bankruptcy | |
| LeoSat | Comms Constellation | 2013 | 2019 shut down | Failed to close funding |
| OneWeb (US operations) | Comms Constellation | 2012 | 2020 bankruptcy, rescued by Bharti/UK Gov | US-founded, now UK-based — ⚠️ borderline |
| Swarm Technologies | IoT Comms | 2016 | Acquired by SpaceX 2021 | Small acquisition |
| Planet (acquired BlackBridge/RapidEye) | EO | 2010 | N/A — Planet is the acquirer | Planet acquired BlackBridge 2015, Terra Bella from Google 2017 |
| Made In Space | In-Space Mfg | 2010 | Acquired by Redwire 2020 | Part of Redwire rollup |
| Deep Space Industries | Asteroid Mining → In-Space | 2013 | Acquired by Bradford Space 2019 | Pivoted away from asteroid mining |
| Planetary Resources | Asteroid Mining | 2009 | Acquired by ConsenSys 2018 (essentially failed) | |
| Moon Express | Lunar Landing | 2010 | Inactive | Google Lunar XPRIZE competitor |
| Aerojet Rocketdyne | Propulsion | 1942 (tracked from 2000) | Acquired by L3Harris 2023 | ~$4.7B — significant space exit |
| Orbital Sciences | Launch / Satellites | 1982 (tracked from 2000) | Merged with ATK → acquired by Northrop 2015 | ~$5.4B combined |
| Ball Aerospace | Instruments / Satellites | 1956 (tracked from 2000) | Acquired by BAE Systems 2024 | ~$5.6B |
| United Launch Alliance (ULA) | Launch (JV) | 2006 | Blue Origin acquiring from Boeing/LMT (2024, pending) | ~$2.7B reported price |

---

## Stage 2: Screen Results

### PASSED — Pure-Play Public Companies (Active)
| Company | Ticker | Sub-sector | Market Status |
|---|---|---|---|
| Rocket Lab USA | RKLB | Launch / Satellites | public_spac |
| Planet Labs | PL | Earth Observation | public_spac |
| Spire Global | SPIR | EO / Data Analytics | public_spac |
| BlackSky Technology | BKSY | Earth Observation | public_spac |
| AST SpaceMobile | ASTS | Satellite Comms | public_spac |
| Redwire | RDW | In-Space Infrastructure | public_spac |
| Intuitive Machines | LUNR | Human Spaceflight / Lunar | public_spac |
| Iridium Communications | IRDM | Satellite Comms | public_ipo |
| Globalstar | GSAT | Satellite Comms | public_ipo |
| Viasat | VSAT | Satellite Comms | public_ipo |
| EchoStar | SATS | Satellite Comms | public_spinoff |
| Satellogic | SATL | Earth Observation | public_spac |
| Orbcomm | ORBC | IoT Comms | public_ipo (re-IPO) |

### PASSED — Public Companies (Exited / Delisted / Failed)
| Company | Ticker | Sub-sector | Market Status | Exit |
|---|---|---|---|---|
| Virgin Orbit | VORB | Launch | public_spac | Bankrupt 2023 |
| Astra Space | ASTR | Launch | public_spac | Delisted / near-failure |
| Momentus | MNTS | In-Space Transport | public_spac | Delisted 2024 |
| Terran Orbital | LLAP | Satellite Mfg | public_spac | Acquired by LMT 2024 |
| Maxar Technologies | MAXR | EO / Satellite Mfg | public_ipo | Acquired by Advent 2023, ~$6.4B |
| DigitalGlobe | DGI | Earth Observation | public_ipo | Acquired by Maxar 2017, ~$2.4B |
| GeoEye | GEOY | Earth Observation | public_ipo | Acquired by DigitalGlobe 2013, ~$900M |
| Orbital Sciences | ORB | Launch / Satellites | public_ipo | Merged w/ ATK → acquired by Northrop 2015, ~$5.4B |
| Aerojet Rocketdyne | AJRD | Propulsion | public_ipo | Acquired by L3Harris 2023, ~$4.7B |
| Ball Aerospace (part of BLL) | BLL | Instruments / Satellites | public (subsidiary) | Divested to BAE 2024, ~$5.6B |
| Loral Space | LORL | Comms / Satellites | public_ipo | Bankruptcy 2003, restructured, acquired 2012 |

### PASSED — Major Private Companies
| Company | Sub-sector | Last Known Valuation | Market Status |
|---|---|---|---|
| SpaceX | Launch / Comms (Starlink) | ~$350B | private_active |
| Blue Origin | Launch / Human Spaceflight | N/A (Bezos-funded) | private_active |
| Sierra Space | Space Stations / Cargo | ~$5.3B | private_active |
| Axiom Space | Space Stations / Crew | ~$3.3B | private_active |
| Relativity Space | Launch | ~$4.2B | private_active |
| Firefly Aerospace | Launch | ~$2.5B | private_active |
| ABL Space Systems | Launch | ~$2.4B | private_active |
| Stoke Space | Launch | ~$1B+ | private_active |
| Impulse Space | In-Space Transport | ~$1.2B | private_active |
| Astranis | GEO Small-Sat Comms | ~$1.4B | private_active |
| Vast | Space Stations | ~$1B+ | private_active |
| Varda Space Industries | In-Space Mfg | ~$1B+ | private_active |
| True Anomaly | Space Domain Awareness | ~$1B+ | private_active |
| Capella Space | SAR EO | ~$800M+ | private_active |
| Hawkeye 360 | RF Analytics | ~$700M+ | private_active |
| Umbra | SAR EO | ~$400M+ | private_active |
| Slingshot Aerospace | SDA / Software | ~$200M+ | private_active |
| LeoLabs | Space Domain Awareness | ~$200M+ | private_active |
| Voyager Space | Space Stations / Holding | Private | private_active |
| Apex Space | Satellite Buses | ~$350M+ | private_active |
| York Space Systems | Satellite Mfg | Private | private_acquired (by Voyager) |
| Made In Space | In-Space Mfg | Private | private_acquired (by Redwire) |
| Swarm Technologies | IoT Comms | Private | private_acquired (by SpaceX) |

### PASSED — Historical Private Failures
| Company | Sub-sector | Founded | Failure Year | Market Status |
|---|---|---|---|---|
| Vector Launch | Launch | 2016 | 2019 | private_failed |
| LeoSat | Comms | 2013 | 2019 | private_failed |
| Planetary Resources | Asteroid Mining | 2009 | 2018 | private_failed |
| Deep Space Industries | Asteroid Mining | 2013 | 2019 | private_failed |
| Kistler Aerospace | Launch | 1993 | 2003 | private_failed |
| Beal Aerospace | Launch | 1997 | 2000 | private_failed |
| Teledesic | Comms | 1994 | 2002 | private_failed |

### SCREENED OUT — With Reasoning
| Company | Reason | Disposition |
|---|---|---|
| Lockheed Martin | Conglomerate (>$10B rev, space <50%) | Tracked in conglomerate appendix |
| Northrop Grumman | Conglomerate | Conglomerate appendix |
| Boeing | Conglomerate | Conglomerate appendix |
| RTX / Raytheon | Conglomerate | Conglomerate appendix |
| L3Harris | Conglomerate | Conglomerate appendix |
| Garmin | Downstream consumer (GPS user equipment) | Excluded |
| Trimble | Downstream consumer (positioning) | Excluded |
| AeroVironment | Primary business is drones, not space | Excluded |
| Blade Air Mobility | Urban air mobility, not space | Excluded |
| Archer Aviation | eVTOL, not space | Excluded |
| Joby Aviation | eVTOL, not space | Excluded |
| 3D Systems | 3D printing, space is minor customer | Excluded |
| Anduril | Defense-first, space <50% of revenue | ⚠️ Appendix — growing space segment, revisit annually |
| Shield AI | Drone/aircraft AI, space is negligible | Excluded |
| Pixxel | Non-US (India-founded, India HQ) | Excluded |
| OneWeb | US-founded but UK-based post-bankruptcy | ⚠️ Borderline — include in appendix as context |

### BORDERLINE — Requires Revenue Split Verification
**⚠️ ACTION REQUIRED:** Pull most recent 10-K for each and check segment revenue.

| Company | Ticker | Issue | Expected Outcome |
|---|---|---|---|
| Kratos Defense | KTOS | Satellite comms + drone/defense mix | Likely out — space probably <50% |
| Parsons Corp | PSN | Some space contracts in defense segment | Likely out — space is small part |
| Mercury Systems | MRCY | Defense electronics, some space | Likely out |
| BWX Technologies | BWXT | Nuclear propulsion (space), naval reactors | Likely out — naval is majority |
| Orbcomm | ORBC | IoT/M2M — is this "space"? Operates satellites. | Likely in — operates own constellation |

---

## Stage 3: Classification (Preliminary)

### Universe Summary

| Category | Count | Notes |
|---|---|---|
| Public — Active | 13 | Mostly 2021 SPAC cohort + legacy comms |
| Public — Exited/Failed | 11 | Mix of acquisitions and failures |
| Private — Active | 23 | Includes SpaceX as massive outlier |
| Private — Acquired | 3 | Small acquisitions |
| Private — Failed | 7 | Mix of eras |
| **Total Universe** | **57** | Before borderline resolution |
| Conglomerate Appendix | 6 | For market sizing context only |
| Borderline / TBD | 5 | Awaiting 10-K review |

### Vintage Cohort Distribution

| Cohort (by founded year) | Count | Dominant Outcome Pattern |
|---|---|---|
| Pre-2000 (tracked from 2000) | ~8 | Legacy comms (Iridium, Globalstar), failures (Kistler, Beal, Teledesic) |
| 2000–2004 | ~4 | SpaceX dominates; Blue Origin; Orbital Sciences (acq.) |
| 2005–2009 | ~4 | Thin vintage — Planetary Resources, few others |
| 2010–2014 | ~10 | First wave new space — Planet, Firefly, OneWeb, Virgin Orbit |
| 2015–2019 | ~16 | Main new space wave — Relativity, Astranis, Hawkeye, ABL, Stoke, Capella |
| 2020–2025 | ~15 | Most recent — Impulse, Varda, True Anomaly, Vast, Apex, K2 |

---

## Gaps & Verification Checklist

**Must-do before finalizing (estimated time: 2-3 hours total):**

- [ ] Download live ETF holdings for UFO, ARKX, ROKT — compare to lists above, add any companies I missed (~15 min)
- [ ] Run EDGAR SIC code queries for 3761, 3764, 3769 — check for any public filers not captured above (~30 min)
- [ ] Download latest Space Capital Quarterly — cross-reference private company list (~30 min)
- [ ] Download latest BryceTech Startup Space Report — cross-reference (~30 min)
- [ ] Pull 10-Ks for 5 borderline companies — check revenue splits (~30 min)
- [ ] Spot-check 5-10 private company valuations against most recent press coverage — flag any that are stale or disputed (~20 min)
- [ ] Check SPACResearch.com for any space SPACs I missed (~15 min)

**Known data I could not verify and should be confirmed:**
- Several private company valuations marked "est." are inferred from press reporting and may be inaccurate
- Blue Origin has never disclosed a formal valuation; some analysts estimate $30-40B+ but this is speculative
- ABL Space Systems raised at $2.4B in 2022 but has had reported difficulties since — current effective valuation may be significantly lower
- Satellogic's classification as "US" is borderline (Argentina-founded, moved legal domicile to US for SPAC)
