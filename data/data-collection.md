# Data Collection Methodology — Space, Bio, Energy VC Fund

## Overview

This document describes the full data collection pipeline for tracking capital flows across the space, bio, and energy industries from 2008 to present. The pipeline produces a unified annual dataset covering three capital sources: private fundraising (SEC EDGAR Form D), public market performance (stock market data), and federal government spending (USASpending.gov).

The output is a set of JSON files keyed on `(sector, subsector, year)` that can be stitched together for cross-source analysis.

This document is intended to be used as a specification in Claude Code for building the automated portions of the pipeline. Manual steps are clearly marked with `[MANUAL]` tags.

---

## Research Questions

This pipeline exists to answer three specific questions.

### RQ1: Capital Flow Composition

For each sector (space, bio, energy) and each year from 2008 to present, what is the total annual capital inflow broken down by source (private fundraising, government outlays) and what is the total public market capitalization? How has the ratio of private-to-government capital shifted over time, and at what year (if any) did private capital inflows surpass government outlays?

Metrics: total Reg D capital raised per year, total federal outlays to non-federal entities per year, total end-of-year public market cap, private share of total inflows (private / (private + government)), crossover year (first year private share > 0.5).

### RQ2: Growth Trajectory Comparison

When we normalize each sector's private capital inflows and government spending to their 2008 baseline, do space, bio, and energy follow similar growth curves with a time lag? Does space in 2024 resemble bio or energy at some earlier year? What is the estimated time lag, and what does it imply about space's trajectory over the next 5-10 years?

Metrics: indexed growth (2008 = 1.0) for private inflows, government outlays, and public market cap per sector; CAGR over rolling 5-year windows; capital efficiency ratio (public market cap / cumulative private capital raised); time-lag estimation (at what year did bio/energy reach the indexed level space is at today).

### RQ3: Government Spending as a Leading Indicator

At the subsector level, is there a statistically significant positive correlation between government outlays in year N and private capital raised in years N+1, N+2, or N+3? When the federal government increases spending in a subsector, does a measurable increase in private venture fundraising follow 1-3 years later?

Metrics: year-over-year change in government outlays per subsector, year-over-year change in private capital raised per subsector lagged by 1-3 years, Pearson correlation and Granger causality test, optimal lag per subsector, effect size (dollars of private capital per dollar of government spending increase).

---

## Scope & Assumptions

### Time range
2008 to present. Form D filings shifted to structured XML in 2008, giving us machine-readable data. Pre-2008 filings are unstructured HTML and are excluded.

### Geographic scope
US-incorporated companies and foreign companies that filed with the SEC (for private/public market data). Federal spending only (for government data). Non-US companies without SEC filings are invisible to this pipeline.

### What "private market data" means here
We can only track private capital that flowed into companies that (a) appear in Crunchbase under our sector classifications AND (b) filed Form D with the SEC. This is a subset of total private investment. Estimated Form D capture rate is 60-70% of Reg D offerings. Not all private fundraising uses Reg D. Our dataset represents "SEC-visible private capital in Crunchbase-classified companies."

### Valuation data is survivorship-biased
Full private valuation histories can only be reconstructed for companies that reached a public exit (IPO or SPAC) via S-1/S-4 filings. Companies that failed or stayed private have money-raised data from Form D but no valuations.

### Government data limitations
Excludes classified/black budget spending (significant for space/defense). Excludes tax incentives and credits (significant for energy). Excludes intra-governmental transfers. Excludes state and local government spending. Excludes sub-awards (money flowing from prime recipients to sub-contractors).

### Fiscal year alignment
Federal fiscal years run Oct 1 – Sep 30. Market and EDGAR data use calendar years. We map FY to CY by assigning FY2023 (Oct 2022 – Sep 2023) to CY2023.

---

## Phase 0: Taxonomy Construction

The taxonomy is the foundation that makes stitching possible. It must be built before any data collection begins. This is a hybrid process: Claude can draft mappings and flag ambiguities, but a human must review and finalize every mapping decision.

Phase 0 produces three outputs:
1. **`taxonomy.json`** — The canonical sector/subsector definitions
2. **`crunchbase-mapping.json`** — Rules for mapping Crunchbase categories/tags to canonical subsectors
3. **`government-classification-rules.json`** — Rules for mapping NAICS codes, agency names, and keywords to canonical subsectors

Changes to any of these files after data collection has started require reprocessing all downstream data.

### Step 0.1 — Define canonical taxonomy `[MANUAL + CLAUDE]`

Use Claude to draft an initial taxonomy based on domain knowledge of each industry. Then manually review, adjust, and finalize.

Key decisions to make during this step:
- Are the subsectors mutually exclusive, or can a company/award belong to multiple? (Recommendation: assign one primary subsector only, to avoid double-counting in aggregates.)
- Is the granularity right? Too few subsectors and you lose analytical power for RQ3 (leading indicator analysis). Too many and some subsectors will have too few data points to be meaningful.
- Does each subsector have enough expected data volume across all three sources (private, public, government) to be useful? A subsector that has heavy government spending but zero private companies is still valid — that's an interesting finding — but a subsector with almost no data in any source should probably be merged into a neighboring one.

Save as `data/taxonomy.json`:

```json
{
  "taxonomy_version": "1.0",
  "sectors": {
    "space": {
      "subsectors": {
        "launch": "Launch vehicles & propulsion systems",
        "satellite_mfg": "Satellite manufacturing & operations",
        "earth_observation": "Earth observation & remote sensing",
        "space_science": "Space science & exploration",
        "ground_systems": "Ground systems & infrastructure",
        "in_space_services": "In-space services, logistics & debris"
      }
    },
    "bio": {
      "subsectors": {
        "therapeutics": "Therapeutics & drug development",
        "diagnostics": "Diagnostics & medical devices",
        "ag_biotech": "Agricultural biotech",
        "synbio": "Synthetic biology & biomanufacturing",
        "biodefense": "Biodefense & pandemic preparedness",
        "genomics": "Genomics & bioinformatics"
      }
    },
    "energy": {
      "subsectors": {
        "solar": "Solar generation & technology",
        "wind": "Wind generation & technology",
        "nuclear": "Nuclear fission & fusion",
        "storage": "Battery & energy storage",
        "hydrogen": "Hydrogen & fuel cells",
        "carbon_capture": "Carbon capture & sequestration",
        "grid": "Grid infrastructure & modernization"
      }
    }
  }
}
```

### Step 0.2 — Build Crunchbase mapping table `[MANUAL + CLAUDE]`

Export the list of Crunchbase category tags and industry groups that appear in your target sectors. Use Claude to draft a mapping from each Crunchbase tag to one canonical subsector. Then manually review.

This is necessary because Crunchbase uses its own tag system (e.g., "Satellite Communication," "Space Travel," "Aerospace") which doesn't map 1:1 to your subsectors.

Save as `data/crunchbase-mapping.json`:

```json
{
  "mapping_version": "1.0",
  "note": "Maps Crunchbase category tags to canonical subsectors. One tag may map to one subsector. Tags not listed here are excluded.",
  "mappings": [
    {
      "crunchbase_tag": "Space Travel",
      "sector": "space",
      "subsector": "launch",
      "confidence": "high",
      "notes": null
    },
    {
      "crunchbase_tag": "Satellite Communication",
      "sector": "space",
      "subsector": "satellite_mfg",
      "confidence": "high",
      "notes": "Includes both satellite manufacturers and satellite-based service providers"
    },
    {
      "crunchbase_tag": "Aerospace",
      "sector": "space",
      "subsector": null,
      "confidence": "low",
      "notes": "Ambiguous — includes aviation companies. Requires manual review per company."
    },
    {
      "crunchbase_tag": "Biotechnology",
      "sector": "bio",
      "subsector": null,
      "confidence": "low",
      "notes": "Too broad — maps to multiple bio subsectors. Requires manual review per company."
    },
    {
      "crunchbase_tag": "Solar",
      "sector": "energy",
      "subsector": "solar",
      "confidence": "high",
      "notes": null
    }
  ]
}
```

`[MANUAL]` For tags that map with "low" confidence or map to `null` subsector, you will need to classify individual companies manually during Step 1.1.

### Step 0.3 — Build government classification ruleset `[MANUAL + CLAUDE]`

Define the rules for classifying USASpending awards into canonical subsectors. This is the most complex mapping because it has three layers: agency assignment, NAICS code mapping, and keyword matching.

Use Claude to draft the initial ruleset. Then manually review, especially the keyword lists (too broad and you get false positives; too narrow and you miss relevant awards).

Save as `data/government-classification-rules.json`:

```json
{
  "rules_version": "1.0",

  "agency_rules": {
    "note": "Awards from these agencies are assigned to a sector by default. Subsector is then determined by NAICS or keyword.",
    "rules": [
      { "agency": "NASA", "default_sector": "space" },
      { "agency": "NIH", "default_sector": "bio" },
      { "agency": "DOE", "default_sector": "energy" }
    ]
  },

  "naics_to_subsector": {
    "note": "Direct NAICS code to subsector mapping. These are high-confidence assignments.",
    "mappings": [
      { "naics": "336414", "description": "Guided Missile and Space Vehicle Manufacturing", "sector": "space", "subsector": "satellite_mfg", "confidence": "high" },
      { "naics": "336415", "description": "Propulsion Unit Manufacturing", "sector": "space", "subsector": "launch", "confidence": "high" },
      { "naics": "336419", "description": "Other Parts Manufacturing", "sector": "space", "subsector": "satellite_mfg", "confidence": "medium" },
      { "naics": "517410", "description": "Satellite Telecommunications", "sector": "space", "subsector": "satellite_mfg", "confidence": "high" },
      { "naics": "325411", "description": "Medicinal and Botanical Manufacturing", "sector": "bio", "subsector": "therapeutics", "confidence": "high" },
      { "naics": "325414", "description": "Biological Product Manufacturing", "sector": "bio", "subsector": "therapeutics", "confidence": "high" },
      { "naics": "541711", "description": "R&D in Biotechnology", "sector": "bio", "subsector": null, "confidence": "medium", "note": "Subsector determined by keyword" },
      { "naics": "221114", "description": "Solar Electric Power Generation", "sector": "energy", "subsector": "solar", "confidence": "high" },
      { "naics": "221115", "description": "Wind Electric Power Generation", "sector": "energy", "subsector": "wind", "confidence": "high" },
      { "naics": "221116", "description": "Geothermal Electric Power Generation", "sector": "energy", "subsector": "grid", "confidence": "medium" },
      { "naics": "335911", "description": "Storage Battery Manufacturing", "sector": "energy", "subsector": "storage", "confidence": "high" },
      { "naics": "541715", "description": "R&D in Physical/Engineering/Life Sciences", "sector": null, "subsector": null, "confidence": "low", "note": "Ambiguous — covers all three sectors. Must be classified by keyword on award description." }
    ]
  },

  "keyword_rules": {
    "note": "Used for cross-agency classification and for resolving ambiguous NAICS codes. Keywords are matched against the award description field. Order matters: first match wins.",
    "space": {
      "launch":            ["launch vehicle", "space launch", "rocket propulsion", "launch services", "propulsion system"],
      "satellite_mfg":     ["satellite", "spacecraft", "space vehicle", "on-orbit"],
      "earth_observation": ["remote sensing", "earth observation", "earth science", "land imaging"],
      "space_science":     ["lunar", "cislunar", "Mars", "planetary", "deep space", "space exploration", "heliophysics"],
      "ground_systems":    ["ground station", "ground segment", "tracking station", "mission control"],
      "in_space_services": ["orbital debris", "space debris", "space situational awareness", "on-orbit servicing", "space logistics"]
    },
    "bio": {
      "therapeutics":  ["drug discovery", "clinical trial", "therapeutic", "pharmaceutical", "mRNA", "gene therapy", "cell therapy", "biologic", "biosimilar"],
      "diagnostics":   ["diagnostic", "medical device", "point-of-care", "assay", "biomarker detection"],
      "ag_biotech":    ["agricultural biotech", "crop", "plant genomics", "soil microbiome", "agricultural biology"],
      "synbio":        ["synthetic biology", "biomanufacturing", "fermentation", "metabolic engineering", "enzyme engineering"],
      "biodefense":    ["biodefense", "pandemic preparedness", "medical countermeasure", "biological threat", "biosurveillance"],
      "genomics":      ["genomics", "genome sequencing", "bioinformatics", "CRISPR", "gene editing", "proteomics"]
    },
    "energy": {
      "solar":          ["solar", "photovoltaic", "PV module", "concentrated solar"],
      "wind":           ["wind energy", "wind turbine", "offshore wind", "wind farm"],
      "nuclear":        ["nuclear fusion", "nuclear fission", "advanced nuclear", "small modular reactor", "SMR", "tokamak", "nuclear energy"],
      "storage":        ["battery storage", "energy storage", "lithium-ion", "solid state battery", "grid-scale storage"],
      "hydrogen":       ["hydrogen fuel", "fuel cell", "green hydrogen", "electrolyzer", "hydrogen production"],
      "carbon_capture": ["carbon capture", "CCS", "CCUS", "direct air capture", "carbon sequestration", "carbon removal"],
      "grid":           ["grid modernization", "smart grid", "EV charging", "electrification", "transmission", "distribution grid", "grid resilience"]
    }
  },

  "classification_priority": {
    "note": "When multiple classification methods apply, use this priority order.",
    "order": [
      "1. Agency default (NASA → space, NIH → bio, DOE → energy) sets the sector.",
      "2. NAICS code sets the subsector if a high-confidence mapping exists.",
      "3. Keyword matching on award description sets or overrides subsector if NAICS is ambiguous or missing.",
      "4. Awards that cannot be classified to a subsector after all three layers are flagged for manual review."
    ]
  }
}
```

`[MANUAL]` Review the full ruleset. Test it against a sample of actual USASpending awards to check for false positives and false negatives. Iterate on keyword lists. Pay particular attention to:
- Keywords that are too generic and would match non-relevant awards (e.g., "solar" might match "solar panel for a military building" which is a facilities contract, not an energy industry award)
- NAICS codes marked "medium" or "low" confidence
- The catch-all NAICS 541715 (R&D in Physical/Engineering/Life Sciences), which spans all three sectors and must be resolved by keyword

### Step 0.4 — Validate taxonomy completeness `[MANUAL + CLAUDE]`

Before proceeding to data collection, do a quick sanity check:
- Does every Crunchbase tag in your export map to a subsector (or get flagged for manual review)?
- Do the top 20 NAICS codes by award volume in USASpending for each primary agency map to a subsector?
- Are there obvious gaps in the keyword lists that would cause significant awards to be missed?

Use Claude to identify potential gaps by reviewing the taxonomy against known companies and programs in each sector.

Save a summary of this validation as `data/taxonomy-validation-notes.md` for audit trail purposes.

---

## Pipeline 1: Primary Market + Secondary Market (Interlinked)

These are built together because the company universe is shared and secondary market tracking is a direct extension of the primary market work (we track companies that went public).

### Step 1.1 — Export Crunchbase universe `[MANUAL]`

Export all companies from Crunchbase tagged under space, bio, and energy verticals. For each company, capture: company name, Crunchbase slug, sector, subsector, founded year, HQ country, status (active/closed/IPO), and Crunchbase UUID.

`[MANUAL]` Assign each company a subsector from the shared taxonomy using `crunchbase-mapping.json` (produced in Phase 0). For Crunchbase tags that mapped with high confidence, this is a direct lookup. For tags flagged as "low" confidence or `null` subsector in the mapping file, classify the company manually based on its description and business model.

Save as `data/source/universe.json`. Each record:

```json
{
  "company_name": "Rocket Lab USA, Inc.",
  "crunchbase_slug": "rocket-lab",
  "sector": "space",
  "subsector": "launch",
  "founded_year": 2006,
  "hq_country": "US",
  "status": "public",
  "crunchbase_uuid": "a1b2c3d4-..."
}
```

### Step 1.2 — Resolve EDGAR identities `[AUTOMATED]`

For each company in the universe, search EDGAR's EFTS API to find the matching legal entity and CIK number.

Endpoint: `https://efts.sec.gov/LATEST/search-index?q="{company_name}"&forms=D,S-1`

Rate limit: 10 requests/second. Include `User-Agent` header with contact email.

For each company, record: CIK (or null if not found), legal names on file, whether Form D filings exist post-2008, whether S-1/S-4 filings exist, and match confidence.

Companies not found in EDGAR are flagged but retained in the universe (they still count for universe sizing even if we can't get their funding data).

Output appended to each record in `universe.json`:

```json
{
  "company_name": "Rocket Lab USA, Inc.",
  "crunchbase_slug": "rocket-lab",
  "sector": "space",
  "subsector": "launch",
  "cik": "0001819994",
  "legal_names_on_file": ["Rocket Lab USA, Inc."],
  "edgar_match_confidence": "high",
  "has_form_d_post_2008": true,
  "has_s1_or_s4": true
}
```

For unmatched companies:

```json
{
  "company_name": "ICEYE",
  "crunchbase_slug": "iceye",
  "sector": "space",
  "subsector": "earth_observation",
  "cik": null,
  "edgar_match_confidence": "no_match",
  "has_form_d_post_2008": false,
  "has_s1_or_s4": false,
  "likely_reason": "non_us_entity"
}
```

### Step 1.3 — Review EDGAR matches `[MANUAL]`

Review all matches flagged as low confidence or ambiguous. Common issues: multiple CIKs returned for a common company name, legal name doesn't obviously match the Crunchbase name, subsidiary vs parent entity confusion.

### Step 1.4 — Report universe coverage `[AUTOMATED]`

Before proceeding, generate a coverage report showing what percentage of the Crunchbase universe has EDGAR matches.

```json
{
  "sector": "space",
  "total_crunchbase_companies": 487,
  "matched_to_edgar": 312,
  "match_rate": 0.64,
  "with_form_d_post_2008": 278,
  "with_s1_or_s4": 27,
  "unmatched_reasons": {
    "non_us_entity": 98,
    "no_sec_filings_found": 52,
    "name_ambiguity_unresolved": 25
  }
}
```

`[MANUAL]` Review this report. If match rate is below 50% for any sector, investigate whether the Crunchbase export or EDGAR search needs refinement before proceeding.

### Step 1.5 — Pull Form D filing index `[AUTOMATED]`

For every company with a CIK, retrieve all Form D and D/A (amendment) filings from 2008 onward.

Endpoint: `https://efts.sec.gov/LATEST/search-index?q=&forms=D,D/A&dateRange=custom&startdt=2008-01-01&enddt=2025-12-31&ciks={cik}`

Store the filing index (accession numbers, dates, URLs) per company.

```json
{
  "cik": "0001819994",
  "company_name": "Rocket Lab USA, Inc.",
  "filings": [
    {
      "accession_number": "0001819994-18-000001",
      "form_type": "D",
      "filing_date": "2018-11-15",
      "file_url": "https://www.sec.gov/Archives/edgar/data/1819994/..."
    },
    {
      "accession_number": "0001819994-19-000003",
      "form_type": "D/A",
      "filing_date": "2019-06-20",
      "file_url": "..."
    }
  ]
}
```

### Step 1.6 — Parse Form D XML `[AUTOMATED]`

Download each Form D filing and parse the structured XML. All post-2008 filings are machine-readable XML with well-defined fields. No LLM needed.

Extract per filing:

```json
{
  "accession_number": "0001819994-18-000001",
  "cik": "0001819994",
  "company_name": "Rocket Lab USA, Inc.",
  "sector": "space",
  "subsector": "launch",
  "filing_date": "2018-11-15",
  "is_amendment": false,
  "offering": {
    "industry_group": "Technology",
    "federal_exemptions": ["06b"],
    "is_equity": true,
    "is_debt": false,
    "is_pooled": false,
    "total_offering_amount": 140000000,
    "total_amount_sold": 140000000,
    "total_remaining": 0,
    "number_of_investors_accredited": 12,
    "number_of_investors_non_accredited": 0,
    "date_of_first_sale": "2018-11-01"
  }
}
```

### Step 1.7 — Deduplicate and chain amendments `[AUTOMATED]`

Form D/A amendments update a prior Form D filing for the same offering. Chain amendments to their original filing so each offering resolves to its final state. Deduplication logic: group by CIK, then match amendments to originals by overlapping date ranges and offering amounts.

Output per company — a clean list of distinct offerings:

```json
{
  "cik": "0001819994",
  "company_name": "Rocket Lab USA, Inc.",
  "sector": "space",
  "subsector": "launch",
  "offerings": [
    {
      "offering_id": "offering_001",
      "original_filing_date": "2018-11-15",
      "latest_amendment_date": "2019-06-20",
      "date_of_first_sale": "2018-11-01",
      "type": "equity",
      "total_amount_sold_final": 140000000,
      "investor_count_final": 15,
      "filing_chain": [
        "0001819994-18-000001",
        "0001819994-19-000003"
      ]
    }
  ]
}
```

### Step 1.8 — Aggregate into annual primary market time series `[AUTOMATED]`

Roll up individual offerings into annual totals by sector, subsector, and year. This produces the primary market source file.

Save as `data/source/{sector}-private.json`:

```json
[
  {
    "sector": "space",
    "subsector": "launch",
    "year": 2021,
    "total_capital_raised": 1840000000,
    "number_of_offerings": 14,
    "median_offering_size": 85000000,
    "unique_companies_raising": 11
  }
]
```

### Step 1.9 — Identify public companies and pull market data `[AUTOMATED]`

From the universe, filter companies where `has_s1_or_s4 == true` or `status == "public"`. For each, determine the ticker symbol and listing date.

`[MANUAL]` Verify ticker symbols and listing dates. Some SPACs change tickers post-merger; some companies delist. This needs human review.

Pull daily historical price and market cap data from a free stock API (Yahoo Finance, Financial Modeling Prep, or Alpha Vantage) from listing date to present.

```json
{
  "ticker": "RKLB",
  "company_name": "Rocket Lab USA, Inc.",
  "sector": "space",
  "subsector": "launch",
  "listing_date": "2021-08-25",
  "exit_type": "SPAC",
  "market_data": [
    {
      "date": "2021-08-25",
      "close_price": 11.58,
      "market_cap": 5490000000,
      "volume": 28500000
    }
  ]
}
```

### Step 1.10 — Aggregate into annual secondary market time series `[AUTOMATED]`

Roll up daily market data into annual totals by sector, subsector, and year. Use end-of-year market cap as the point-in-time value.

Save as `data/source/{sector}-public.json`:

```json
[
  {
    "sector": "space",
    "subsector": "launch",
    "year": 2021,
    "companies_listed_this_year": 2,
    "total_listed_companies_eoy": 4,
    "total_market_cap_eoy": 18200000000,
    "median_market_cap_eoy": 3100000000,
    "sector_return_ytd": -0.08
  }
]
```

### Step 1.11 — S-1/S-4 deep extraction for valuations `[AUTOMATED + MANUAL]`

For each company with S-1/S-4/F-1 filings, download the registration statement. Use the Claude API to extract the capitalization/funding history — specifically the sections titled "Dilution," "Capitalization," or "Description of Capital Stock" that contain share issuance history with dates, share counts, and price per share.

The Claude API prompt should request structured JSON matching a defined schema.

Extracted per company:

```json
{
  "cik": "0001819994",
  "company_name": "Rocket Lab USA, Inc.",
  "sector": "space",
  "subsector": "launch",
  "filing_type": "S-4",
  "funding_rounds": [
    {
      "round_label": "Series A",
      "date": "2014-03-15",
      "shares_issued": 5000000,
      "price_per_share": 1.20,
      "amount_raised": 6000000,
      "lead_investor": "Khosla Ventures",
      "source_section": "Description of Capital Stock, p.142",
      "extraction_confidence": "high"
    }
  ]
}
```

Calculate implied valuations from share data:
- `post_money = price_per_share × total_shares_outstanding_after_round`
- `pre_money = post_money - amount_raised`

```json
{
  "round_label": "Series B",
  "date": "2015-09-01",
  "amount_raised": 28000000,
  "price_per_share": 3.50,
  "total_shares_outstanding_post": 25000000,
  "implied_post_money_valuation": 87500000,
  "implied_pre_money_valuation": 59500000,
  "valuation_confidence": "high"
}
```

`[MANUAL]` Every company's extracted funding timeline must be reviewed by a human. Check that valuations increase monotonically (or explain down rounds), that amounts cross-check against Form D data from Step 1.7, and that share math is internally consistent.

Save as `data/source/{sector}-valuations.json`. This is a supplementary file — it does not feed into the annual stitched view directly (since it only covers companies that went public) but is critical for answering RQ2 about valuation trajectories.

---

## Pipeline 2: Government Spending

### Step 2.1 — Bulk download primary agency award data `[MANUAL]`

Download CSV files from USASpending's Award Data Archive: `https://www.usaspending.gov/download_center/award_data_archive`

Download settings per file:
- Award type: All (contracts, grants, loans, direct payments, other)
- Agency: One per download
- Fiscal year: One per download (FY2008 through FY2025)
- Sub-agency: All

Primary agencies by sector:

**Space:** NASA (all awards), DOD (will be filtered in Step 2.3), NOAA (will be filtered)
**Bio:** NIH (all awards), NSF (will be filtered), HHS/BARDA (will be filtered), USDA (will be filtered), DOD (will be filtered)
**Energy:** DOE (all awards), EPA (will be filtered), DOD (will be filtered), DOI/BOEM (will be filtered)

For agencies that are primary for a given sector (NASA for space, NIH for bio, DOE for energy), download all awards. For shared agencies (DOD, NSF, etc.), download all awards — filtering happens in Step 2.3.

Place raw CSVs in `data/raw/usaspending/`.

### Step 2.2 — Parse and normalize CSVs `[AUTOMATED]`

Read each CSV and extract the relevant columns. Filter for non-federal recipients only (exclude intra-governmental transfers).

Key columns to extract:

```json
{
  "award_id": "CONT_AWD_NNX17AB52G",
  "fiscal_year": 2023,
  "awarding_agency": "NASA",
  "awarding_sub_agency": "Goddard Space Flight Center",
  "award_type": "contract",
  "naics_code": "336414",
  "naics_description": "Guided Missile and Space Vehicle Manufacturing",
  "award_description": "Next-generation satellite bus development",
  "recipient_name": "Rocket Lab USA, Inc.",
  "recipient_uei": "ABC123DEF456",
  "recipient_type": "private_company",
  "recipient_state": "CA",
  "total_obligated_amount": 15000000,
  "total_outlayed_amount": 12500000,
  "period_of_performance_start": "2022-09-01",
  "period_of_performance_end": "2025-08-31"
}
```

Track both `total_obligated_amount` (money committed) and `total_outlayed_amount` (money actually disbursed).

### Step 2.3 — Classify awards by sector and subsector `[AUTOMATED + MANUAL]`

Apply the classification rules defined in `government-classification-rules.json` (produced in Phase 0). The rules are applied in priority order:

1. **Agency default** sets the sector (NASA → space, NIH → bio, DOE → energy).
2. **NAICS code** sets the subsector if a high-confidence mapping exists in the ruleset.
3. **Keyword matching** on the award description field sets or overrides subsector if NAICS is ambiguous or missing.
4. Awards that cannot be classified after all three layers are flagged for manual review.

For multi-sector agencies (DOD, NSF, etc.), there is no agency default — classification relies entirely on NAICS and keyword layers.

Output per award:

```json
{
  "award_id": "CONT_AWD_NNX17AB52G",
  "sector": "space",
  "subsector": "satellite_mfg",
  "classification_method": "naics_code",
  "classification_confidence": "high"
}
```

```json
{
  "award_id": "GRANT_AWD_80NSSC20K1234",
  "sector": "space",
  "subsector": "earth_observation",
  "classification_method": "keyword_match",
  "classification_confidence": "medium",
  "matched_keywords": ["remote sensing", "earth observation"]
}
```

`[MANUAL]` Review all awards classified with "medium" or "low" confidence. Review a random sample of "high" confidence classifications to validate the rules.

### Step 2.4 — API-based cross-agency search `[AUTOMATED]`

Use the USASpending Award Search API to catch relevant awards from agencies NOT in the primary list that may have been missed by the bulk downloads.

Endpoint: `https://api.usaspending.gov/api/v2/search/spending_by_award/`

Run keyword and NAICS searches across all agencies, excluding the primary agencies already downloaded. This catches things like: Space Force contracts under DOD, DARPA energy programs, intelligence community space awards (to the extent they're unclassified).

```json
{
  "filters": {
    "time_period": [
      {"start_date": "2022-10-01", "end_date": "2023-09-30"}
    ],
    "award_type_codes": ["A", "B", "C", "D", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"],
    "naics_codes": [{"identifier": "336414"}, {"identifier": "336415"}],
    "keywords": ["satellite", "spacecraft", "launch vehicle"],
    "exclude": {
      "agencies": ["NASA"]
    }
  },
  "fields": [
    "Award ID", "Recipient Name", "Award Amount", "Awarding Agency",
    "Award Type", "Description", "NAICS Code", "Period of Performance Start Date"
  ],
  "limit": 100,
  "page": 1
}
```

Paginate through all results. Deduplicate against bulk download data on `award_id`.

### Step 2.5 — Aggregate into annual government time series `[AUTOMATED]`

Roll up all classified awards into annual totals by sector, subsector, year, and award type.

Save as `data/source/{sector}-government.json`:

```json
[
  {
    "sector": "space",
    "subsector": "launch",
    "year": 2021,
    "total_obligated": 8200000000,
    "total_outlayed": 6500000000,
    "by_award_type": {
      "contracts":       { "obligated": 6800000000, "outlayed": 5400000000, "count": 342 },
      "grants":          { "obligated": 1200000000, "outlayed": 950000000,  "count": 187 },
      "loans":           { "obligated": 0,          "outlayed": 0,          "count": 0 },
      "direct_payments": { "obligated": 200000000,  "outlayed": 150000000,  "count": 45 }
    }
  }
]
```

---

## Pipeline 3: Stitching

### Step 3.1 — Validate source files `[AUTOMATED]`

Before stitching, validate that all three source files for each sector use the same subsector codes from the taxonomy. Flag any records with subsector values not in `taxonomy.json`.

Validate that year ranges are consistent across sources (all should cover 2008–present, though some subsector/year combinations may have no data, which is fine — they become null in the stitched view).

### Step 3.2 — Join on (sector, subsector, year) `[AUTOMATED]`

Perform a full outer join of `{sector}-private.json`, `{sector}-public.json`, and `{sector}-government.json` on the composite key `(sector, subsector, year)`.

Where a source has no data for a given key (e.g., no public companies in a subsector in a given year), the fields for that source are null.

### Step 3.3 — Compute derived metrics `[AUTOMATED]`

For each row in the stitched data, compute:

- `total_inflow` = private.capital_raised + government.outlayed (both are flows, so they're additive)
- `private_share` = private.capital_raised / total_inflow
- `govt_share` = government.outlayed / total_inflow
- `cumulative_private_raised_to_date` = running sum of private.capital_raised for this sector+subsector
- `capital_efficiency` = public.market_cap_eoy / cumulative_private_raised_to_date
- `private_yoy_growth` = year-over-year change in private.capital_raised
- `govt_yoy_growth` = year-over-year change in government.outlayed
- `market_cap_yoy_growth` = year-over-year change in public.market_cap_eoy
- `indexed_private_2008_base` = private.capital_raised / private.capital_raised in 2008 for this sector+subsector
- `indexed_govt_2008_base` = government.outlayed / government.outlayed in 2008 for this sector+subsector
- `cpi_deflator_2023_base` = CPI adjustment factor for converting nominal to real 2023 dollars

Save as `data/unified/{sector}-unified.json`:

```json
[
  {
    "sector": "space",
    "subsector": "launch",
    "year": 2021,

    "private": {
      "capital_raised": 1840000000,
      "offerings": 14,
      "companies_raising": 11
    },

    "public": {
      "market_cap_eoy": 18200000000,
      "listed_companies_eoy": 4,
      "return_ytd": -0.08
    },

    "government": {
      "obligated": 8200000000,
      "outlayed": 6500000000,
      "contracts_outlayed": 5400000000,
      "grants_outlayed": 950000000,
      "loans_outlayed": 0,
      "direct_payments_outlayed": 150000000
    },

    "derived": {
      "total_inflow": 8340000000,
      "private_share": 0.22,
      "govt_share": 0.78,
      "cumulative_private_raised_to_date": 4200000000,
      "capital_efficiency": 4.33,
      "private_yoy_growth": 0.42,
      "govt_yoy_growth": 0.07,
      "market_cap_yoy_growth": 2.10,
      "indexed_private_2008_base": 12.4,
      "indexed_govt_2008_base": 1.8,
      "indexed_market_cap_2008_base": null,
      "cpi_deflator_2023_base": 0.91
    },

    "metadata": {
      "fy_cy_note": "Government data from FY2021 mapped to CY2021"
    }
  }
]
```

### Step 3.4 — Produce master file `[AUTOMATED]`

Concatenate all three sector unified files into `data/master/all-sectors-unified.json`. This is the single file that downstream analysis and visualization reads from.

---

## Expected Output File Structure

```
data/
├── taxonomy.json                    # Phase 0 output: canonical sector/subsector definitions
├── crunchbase-mapping.json          # Phase 0 output: Crunchbase tags → subsectors
├── government-classification-rules.json  # Phase 0 output: NAICS + keywords + agency → subsectors
├── taxonomy-validation-notes.md     # Phase 0 output: audit trail of taxonomy decisions
├── source/
│   ├── universe.json                # All companies, all sectors, with EDGAR matches
│   ├── space-private.json           # Annual primary market aggregates
│   ├── space-public.json            # Annual secondary market aggregates
│   ├── space-government.json        # Annual government spending aggregates
│   ├── space-valuations.json        # S-1 derived valuation histories (public companies only)
│   ├── bio-private.json
│   ├── bio-public.json
│   ├── bio-government.json
│   ├── bio-valuations.json
│   ├── energy-private.json
│   ├── energy-public.json
│   ├── energy-government.json
│   └── energy-valuations.json
├── unified/
│   ├── space-unified.json
│   ├── bio-unified.json
│   └── energy-unified.json
├── master/
│   └── all-sectors-unified.json
└── raw/
    └── usaspending/                 # Raw CSV downloads from USASpending
        ├── NASA_FY2023_All_Awards.csv
        ├── DOE_FY2023_All_Awards.csv
        └── ...
```

---

## Manual vs Automated Summary

| Step | Type | Description |
|------|------|-------------|
| 0.1 | `[MANUAL + CLAUDE]` | Define canonical taxonomy |
| 0.2 | `[MANUAL + CLAUDE]` | Build Crunchbase mapping table |
| 0.3 | `[MANUAL + CLAUDE]` | Build government classification ruleset |
| 0.4 | `[MANUAL + CLAUDE]` | Validate taxonomy completeness |
| 1.1 | `[MANUAL]` | Export Crunchbase universe, assign subsectors using crunchbase-mapping.json |
| 1.2 | `[AUTOMATED]` | Resolve EDGAR identities via EFTS API |
| 1.3 | `[MANUAL]` | Review low-confidence EDGAR matches |
| 1.4 | `[AUTOMATED]` | Generate coverage report |
| 1.4 review | `[MANUAL]` | Review coverage report, decide if match rate is acceptable |
| 1.5 | `[AUTOMATED]` | Pull Form D filing index per CIK |
| 1.6 | `[AUTOMATED]` | Parse Form D XML |
| 1.7 | `[AUTOMATED]` | Deduplicate and chain amendments |
| 1.8 | `[AUTOMATED]` | Aggregate into annual primary market time series |
| 1.9 | `[AUTOMATED]` | Pull secondary market data for public companies |
| 1.9 review | `[MANUAL]` | Verify ticker symbols and listing dates |
| 1.10 | `[AUTOMATED]` | Aggregate into annual secondary market time series |
| 1.11 | `[AUTOMATED]` | S-1/S-4 extraction via Claude API |
| 1.11 review | `[MANUAL]` | Human review of every extracted valuation timeline |
| 2.1 | `[MANUAL]` | Download USASpending CSVs by agency and fiscal year |
| 2.2 | `[AUTOMATED]` | Parse and normalize CSVs, filter non-federal recipients |
| 2.3 | `[AUTOMATED]` | Classify awards by sector/subsector using NAICS + keywords |
| 2.3 review | `[MANUAL]` | Review medium/low confidence classifications |
| 2.4 | `[AUTOMATED]` | API-based cross-agency keyword search |
| 2.5 | `[AUTOMATED]` | Aggregate into annual government time series |
| 3.1 | `[AUTOMATED]` | Validate source files against taxonomy |
| 3.2 | `[AUTOMATED]` | Join source files on (sector, subsector, year) |
| 3.3 | `[AUTOMATED]` | Compute derived metrics |
| 3.4 | `[AUTOMATED]` | Produce master file |

---

## Technical Requirements

- **Language:** Python 3.10+
- **EDGAR API:** `requests` library, 10 req/sec rate limit, `User-Agent` header required with contact email
- **XML parsing:** `lxml` for Form D XML
- **CSV processing:** `pandas` for USASpending bulk files (can be hundreds of MB per file)
- **Stock data:** Free API — Yahoo Finance (`yfinance`), Financial Modeling Prep, or Alpha Vantage
- **Claude API:** Used only in Step 1.11 for S-1/S-4 extraction (~20-30 filings for space, more for bio/energy)
- **Storage:** PostgreSQL or DuckDB for intermediate data; final outputs as JSON files
- **USASpending API:** 10 req/sec unauthenticated, higher with registration

---

## Recommended Build Order

1. Start with space sector only — smallest universe (~300-500 companies, ~20-30 went public)
2. Pipeline 1 (Steps 1.1–1.10) and Pipeline 2 (Steps 2.1–2.5) can run in parallel
3. Step 1.11 (S-1 extraction) can run in parallel with Pipeline 2
4. Pipeline 3 (stitching) runs once both Pipeline 1 and 2 produce their annual aggregates
5. Once validated on space, extend to bio, then energy
6. Estimated timeline for space: 4-6 weeks total
