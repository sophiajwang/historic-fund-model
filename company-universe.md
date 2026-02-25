# Systematic Company Universe Construction Methodology
## Cross-Industry Returns Study: Space, Bio, Energy (US, 2000–2025)

---

## 1. Overview

This document defines a **repeatable, source-driven process** for constructing the company universe for each sector. The goal is to minimize researcher discretion and make inclusion/exclusion decisions auditable. The same process applies identically to all three sectors — only the input sources and classification codes differ.

The process has four stages:
1. **Seed** — pull candidate lists from defined public sources
2. **Screen** — apply uniform inclusion/exclusion filters
3. **Classify** — tag each company by sub-sector, market status, and outcome
4. **Validate** — cross-check against a second independent source to catch gaps

---

## 2. Stage 1: Seed — Generating the Candidate List

The candidate list is the raw, unfiltered set of companies that *might* belong in the universe. We generate it by combining multiple public sources to maximize coverage.

### Source A: ETF & Index Constituents (Public Companies)

Pull the full holdings list from sector-specific ETFs. These are maintained by professional index providers with their own inclusion criteria, giving us a pre-filtered starting point.

| Sector | ETF(s) | Provider | Why |
|---|---|---|---|
| Space | UFO (Procure Space ETF) | Procure | Only pure-play space ETF; S-Network Space Index |
| Space | ARKX (ARK Space Exploration) | ARK Invest | Broader definition, catches adjacencies |
| Space | ROKT (SPDR S&P Kensho Final Frontiers) | S&P/Kensho | Rules-based NLP selection |
| Bio | XBI (SPDR S&P Biotech) | S&P | Equal-weight, broadest US biotech coverage |
| Bio | IBB (iShares Biotech) | Nasdaq Biotech Index | Market-cap weighted, larger names |
| Energy | TAN (Invesco Solar) | MAC Solar Index | Solar pure-plays |
| Energy | ICLN (iShares Global Clean Energy) | S&P Global Clean Energy | Filter to US-only |
| Energy | QCLN (First Trust NASDAQ Clean Edge) | NASDAQ Clean Edge | US-focused clean energy |
| Energy | NLR (VanEck Uranium+Nuclear) | MVIS | Nuclear/uranium |
| Energy | LIT (Global X Lithium & Battery) | Solactive | Filter to US-only |
| Energy | DRIV / IDRV (EV ETFs) | Various | Filter to US-only |

**Process:**
1. Download current holdings from each ETF provider's website (all publish full holdings daily as CSV/PDF)
2. Combine into a single candidate list per sector, deduplicate by ticker
3. For space: also pull the S-Network Space Index constituent list directly (published at snetworkglobalindexes.com), as it has more rigorous methodology documentation than the ETFs themselves

**Limitation:** ETFs only capture *currently listed* companies. They miss delistings, bankruptcies, and SPACs that have since failed. This is addressed in Source C.

### Source B: Industry Classification Codes (Public Companies, Historical)

Use SIC and NAICS codes via SEC EDGAR full-text search to find companies that *were* public at any point during the study window, including those that have since delisted.

| Sector | Relevant SIC Codes | Relevant NAICS Codes |
|---|---|---|
| Space | 3761 (Guided Missiles & Space Vehicles), 3764 (Propulsion), 3769 (Space Vehicle Equipment), 4899 (Communication Services NEC), 3812 (Search/Navigation Equipment) | 336414 (Guided Missile & Space Vehicle Mfg), 336415 (Propulsion), 336419 (Other Guided Missile/Space Parts), 517410 (Satellite Telecom), 541715 (R&D, Physical/Engineering/Life Sciences) |
| Bio | 2836 (Biological Products), 2835 (In Vitro Diagnostics), 2830 (Industrial Chemicals — pharma), 3841 (Surgical/Medical Instruments — borderline) | 325414 (Biological Product Mfg), 325413 (In Vitro Diagnostics), 541711 (Biotech R&D) |
| Energy | 3674 (Semiconductors — solar cells), 3629 (Electrical Industrial Apparatus — batteries), 3699 (Electronic Components NEC) | 221114 (Solar Electric Power Gen), 221115 (Wind Electric Power Gen), 335911 (Storage Battery Mfg), 336111 (Auto Mfg — EVs) |

**Process:**
1. Query EDGAR full-text company search (efts.sec.gov/LATEST/search-index) by SIC code
2. Export all US-domiciled filers that were active at any point 2000–2025
3. Merge with Source A list, deduplicate

**Limitation:** SIC/NAICS codes are self-reported and often inaccurate, especially for "new space" companies that may file under generic codes. This is why we need Source C.

### Source C: Industry Reports & Databases (Private + Historical Public)

These sources capture private companies, historical exits, and companies missed by ETFs and SIC codes.

| Sector | Source | What It Provides | Access |
|---|---|---|---|
| Space | Space Capital Quarterly Reports | Comprehensive list of space economy companies by category, VC deal flow | Free (spacecapital.com) |
| Space | BryceTech Annual Start-Up Space Report | All venture-funded space companies, funding data | Free summary; full report purchasable |
| Space | Satellite Industry Association Annual Report | Satellite company universe, revenue data by segment | Free (sia.org) |
| Space | NASA SBIR/STTR Award Database | Companies receiving NASA innovation funding | Free (sbir.nasa.gov) |
| Bio | Crunchbase (free tier) | Search "Biotechnology" industry tag, US, founded 2000–2025 | Free (limited to ~1000 results) |
| Bio | FDA Approved Drugs Database (Drugs@FDA) | Companies that successfully brought drugs to market | Free (fda.gov) |
| Bio | NVCA Yearbook / PitchBook-NVCA Venture Monitor | Top VC-backed biotech companies by funding | Free annual summary PDFs |
| Energy | ARPA-E Project Database | All ARPA-E funded energy companies | Free (arpa-e.energy.gov) |
| Energy | DOE Loan Programs Office (LPO) Portfolio | All DOE loan/guarantee recipients | Free (energy.gov/lpo) |
| Energy | Crunchbase (free tier) | Search "Clean Energy" / "Renewable Energy" tags, US | Free |
| Energy | NVCA Yearbook | Top VC-backed energy/cleantech companies | Free annual summary |
| All | Crunchbase "Exits" filter | Companies with IPO, acquisition, or closure recorded | Free tier |

**Process:**
1. Pull company lists from each source
2. For Space Capital: use their published quarterly "Space Investment Quarterly" which categorizes every funded space company
3. For BryceTech: use the startup list from their annual report
4. For Crunchbase: search by industry tag + US HQ + founded 2000–2025, export
5. Merge all into master candidate list per sector, deduplicate by company name (normalize for name changes, e.g., "Maxar" vs "MacDonald Dettwiler")

### Source D: SPAC & De-SPAC Tracker (Public, Historical)

Space and cleantech had significant SPAC waves. Many of these companies have since delisted or failed and won't appear in current ETF holdings.

| Source | URL | What It Provides |
|---|---|---|
| SPACResearch.com | spacresearch.com | Full database of all SPACs, filterable by industry |
| SEC EDGAR SPAC filings | Search for "blank check" or "special purpose acquisition" | All SPAC S-1 and merger proxy filings |

**Process:**
1. Pull all completed de-SPACs tagged as space, biotech, or clean energy
2. Record merger date, initial enterprise value, current status (active, delisted, bankrupt)
3. Add to candidate list

---

## 3. Stage 2: Screen — Inclusion / Exclusion Filters

Every company in the candidate list is run through the same set of binary filters. A company must pass ALL inclusion criteria and NONE of the exclusion criteria.

### Inclusion Criteria (must meet ALL)

| # | Criterion | How to Verify |
|---|---|---|
| 1 | **US-domiciled:** HQ in the US, or primary listing on a US exchange (NYSE, NASDAQ, OTC) | EDGAR filing address; Crunchbase HQ field |
| 2 | **Active during study window:** Company existed (founded or operating) at some point between Jan 1, 2000 and May 31, 2025 | Founded date from Crunchbase/EDGAR; if founded before 2000, must still have been operating after Jan 1, 2000 |
| 3 | **Primary sector revenue ≥50%:** More than half of the company's revenue (or, for pre-revenue companies, stated primary business activity) is in the target sector | Most recent 10-K segment reporting; if no segment data, use company's self-description in SEC filings ("the Company is engaged in...") |
| 4 | **Minimum materiality:** Public companies must have had a market cap ≥$50M at some point; Private companies must have raised ≥$10M in total institutional funding OR been acquired for ≥$10M OR received ≥$5M in government grants/contracts | Market cap from historical price data; funding from Crunchbase/press; acquisition price from SEC filings/press |

### Exclusion Criteria (must meet NONE)

| # | Criterion | Rationale |
|---|---|---|
| 1 | **Conglomerate:** Company has >$10B total revenue and target sector is <50% of revenue | These distort returns analysis; tracked separately for market sizing |
| 2 | **Downstream consumer only:** Company uses sector output but doesn't produce it (e.g., Garmin uses GPS but doesn't build satellites; airlines buy SAF but don't produce it) | Not part of the industry value chain |
| 3 | **Pure financial vehicle:** SPACs that never completed a merger; blank-check companies with no operating business | No operating business to evaluate |
| 4 | **Foreign-founded, US-listed only for capital access:** Company has no meaningful US operations, employees, or customers (e.g., some foreign biotechs list ADRs on NASDAQ) | US study scope |

### Edge Case Resolution Protocol

For companies that are ambiguous (borderline revenue split, multi-sector businesses, recent pivots):

1. **Check revenue split in most recent 10-K.** If segment data exists, use it. ≥50% = in, <50% = out.
2. **If no segment data (pre-revenue or private):** Read the company's "Business" section in their most recent SEC filing (10-K, S-1, or SPAC proxy). If the first paragraph describes the company as primarily operating in the target sector, include.
3. **If still ambiguous:** Flag as "borderline" and include in a separate appendix. Do not include in primary returns analysis. Document the reasoning.
4. **For companies that changed sectors (pivot):** Classify based on their primary business at time of exit/valuation event. If still active, use current primary business.

---

## 4. Stage 3: Classify

Every company that passes screening is tagged with the following fields:

| Field | Values | Source |
|---|---|---|
| sector | space / bio / energy | Assigned by screener |
| sub_sector | (see sub-sector definitions below) | Based on primary product/service |
| market_status | public_ipo / public_spac / public_spinoff / private_active / private_acquired / private_failed / public_delisted | SEC filings, Crunchbase |
| founded_year | YYYY | Crunchbase, SEC filings |
| first_funding_year | YYYY | Crunchbase (earliest round) |
| total_funding_raised_M | $M | Crunchbase, press releases |
| ipo_or_spac_year | YYYY or null | SEC filings |
| ipo_or_spac_valuation_M | $M or null | S-1/proxy filing |
| peak_market_cap_M | $M or null | Historical price data |
| current_market_cap_M | $M or null | Current price × shares outstanding |
| exit_type | ipo / spac / acquisition / bankruptcy / still_private / still_public | SEC filings, press |
| exit_valuation_M | $M or null | Acquisition price, IPO valuation, or last known private valuation |
| exit_year | YYYY or null | |
| vintage_cohort | 2000-2004 / 2005-2009 / 2010-2014 / 2015-2019 / 2020-2025 | Based on founded_year |

### Sub-sector Definitions

**Space:** Launch, Satellite Manufacturing, Earth Observation & Remote Sensing, Satellite Communications, In-Space Infrastructure & Services, Space Software & Analytics, Human Spaceflight & Exploration, National Security Space

**Bio:** Therapeutics (Small Molecule), Therapeutics (Biologics / Cell & Gene), Genomics & Sequencing, Diagnostics, Tools & Platforms, Synthetic Biology, mRNA & Vaccines, AI-Driven Drug Discovery

**Energy:** Solar, Wind, Energy Storage & Batteries, Electric Vehicles, Hydrogen & Fuel Cells, Advanced Nuclear, Grid & Energy Software, Biofuels & Sustainable Fuels, Carbon Capture

---

## 5. Stage 4: Validate — Cross-Check for Completeness

After constructing the universe from Sources A–D and applying screens, validate against an independent source to catch gaps.

### Validation method

| Check | Process | Action if Gap Found |
|---|---|---|
| **Expert list cross-check** | Compare final universe against 2–3 published "top companies in [sector]" lists from industry analysts (e.g., CB Insights, Deloitte Tech Fast 500, CNBC Disruptor 50) | If a company appears on multiple expert lists but not in our universe, investigate why. If it passes the screen, add it. If it doesn't, document the exclusion reason. |
| **Revenue coverage check** | Sum the revenue of all companies in the universe and compare to published total industry revenue figures (SIA for space, EvaluatePharma for bio, BNEF for energy) | If our universe accounts for <70% of published industry revenue, investigate what's missing. Likely conglomerates — document the gap. |
| **Exit coverage check** | Compare our exits list against published M&A databases (Crunchbase exits, press roundups like "biggest biotech deals of 202X") | If a >$1B exit is missing, investigate and add if it passes the screen. |
| **Peer review** | Have at least one other team member review the final list and flag any companies they expected to see but don't | Investigate each flag, document disposition |

---

## 6. Data Collection Plan

Once the universe is finalized, collect the following data using free/public sources:

| Data Point | Public Companies Source | Private Companies Source |
|---|---|---|
| Market cap history (monthly) | Yahoo Finance historical prices × shares outstanding (from 10-K) | N/A |
| Revenue history (annual) | SEC EDGAR 10-K filings | Not reliably available |
| Valuation at funding rounds | N/A | Crunchbase (free tier shows some), press releases, SEC filings (for late-stage rounds sometimes disclosed) |
| Exit price | SEC filings (merger proxy, 8-K) | SEC filings (if acquirer is public), press |
| Founded date | EDGAR, Crunchbase | Crunchbase |
| Funding raised | N/A | Crunchbase, press |
| Industry-level market size | SIA, BryceTech, EvaluatePharma, BNEF, IEA | Same sources |
| Government spend | USASpending.gov, NASA budget docs, NIH Reporter, DOE budget | Same sources |
| VC deal flow (aggregate) | Space Capital Quarterly, NVCA Yearbook, PitchBook-NVCA free summaries | Same sources |

---

## 7. Repeatability Notes

This methodology is designed to be re-run annually or applied to new sectors by:

1. Substituting new sector-specific ETFs in Source A
2. Substituting new SIC/NAICS codes in Source B
3. Substituting new industry report sources in Source C
4. Keeping Stages 2–5 identical

The inclusion criteria (US-domiciled, ≥50% sector revenue, materiality threshold) and classification schema are sector-agnostic by design.

---

## 8. Known Limitations

- **Survivorship bias in ETF holdings:** Current ETF constituents exclude failed/delisted companies. Sources C and D partially correct for this, but coverage of pre-2015 private company failures is likely incomplete.
- **Self-reported SIC codes:** Many companies file under generic codes (e.g., 3812 "Search & Navigation Equipment" captures both space and non-space companies). Manual review is required after the SIC pull.
- **Private company valuation opacity:** Without PitchBook, private company valuations rely on press-reported funding rounds and secondary market data. These are point-in-time and may not reflect current fair value. This limitation applies equally across all three sectors.
- **Revenue split data:** Many companies don't break out segment revenue cleanly. The "first paragraph" fallback in the edge case protocol introduces some subjectivity — document all borderline calls.
- **Bio universe size:** Biotech has 500+ public companies vs. ~30 for space. Direct numerical comparison of "number of successful outcomes" is misleading without normalizing for universe size. All cross-sector comparisons should use rates (% of universe that achieved X outcome) rather than counts.
