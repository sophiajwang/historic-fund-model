# Historic Fund Model

## Overview

Research project comparing returns across three deep-tech sectors: **Space**, **Bio**, and **Energy**. The goal is to build a rigorous, data-driven model for LP presentations that answers: "How does space as an investment sector compare to biotech and clean energy?"

## Project Structure

```
historic-fund-model/
├── model-methodology.md      # 3-layer model specification (source of truth)
├── company-universe.md       # Repeatable methodology for universe construction
├── space-universe-execution.md   # ~57 space companies
├── bio-universe-execution.md     # ~220-290 bio companies
├── energy-universe-execution.md  # ~120-155 energy companies
├── data/                     # Structured data files (JSON/CSV)
└── .claude/docs/             # Additional documentation
```

## Data Model Layers

| Layer | Purpose | Key Output |
|-------|---------|------------|
| Layer 1 | Total Value Creation Accounting | Sector Gross Multiple |
| Layer 2 | Vintage Cohort Analysis | Hit rates by founding year |
| Layer 3 | Public Market Portfolio Simulation | Returns vs benchmarks |

## Key Concepts

- **Data Tiers**: Tier 1 (SEC filing), Tier 2 (press-reported), Tier 3 (estimated), Tier 4 (unknown)
- **Vintage Cohorts**: Pre-2000, 2000-04, 2005-09, 2010-14, 2015-19, 2020-25
- **Materiality Threshold**: Public ≥$50M market cap; Private ≥$10M raised

## Data Sources (for manual verification)

| Source | Sectors | What It Provides |
|--------|---------|------------------|
| ETF Holdings (UFO, XBI, TAN, etc.) | All | Current public company universes |
| SEC EDGAR | All | Historical filers, 10-K segment data |
| Crunchbase | All | Private company funding |
| DOE LPO Portfolio | Energy | Loan recipients and outcomes |
| Space Capital Quarterly | Space | Private space company valuations |
| FDA Drugs@FDA | Bio | Drug approvals by company |

## Essential Commands

This is a data/research project, not a code project. Key operations:

```bash
# Validate JSON data structure
python -m json.tool data/sector_universe.json

# (Future) Run model calculations
python scripts/calculate_multiples.py
```

## Data Quality Standards

When adding or updating data:
1. Always include `data_tier` (1-4) for every value estimate
2. Always include `source` citation
3. Flag missing data as `null`, never guess
4. Private valuations require `valuation_date`

## Additional Documentation

Check these files for specialized context:

| File | When to Check |
|------|---------------|
| [.claude/docs/data_collection_patterns.md](.claude/docs/data_collection_patterns.md) | Adding new companies or updating valuations |
| [.claude/docs/research_methodology.md](.claude/docs/research_methodology.md) | Understanding inclusion/exclusion decisions |
| [model-methodology.md](model-methodology.md) | Layer calculations and presentation formats |

## Key Analytical Notes

- **SpaceX dominance**: ~$350B of ~$400B total space value — always show with/without
- **Tesla dominance**: Similar pattern in energy
- **Bio is distributed**: No single outlier; rich M&A exit dataset
- **Two bust cycles in energy**: Cleantech 1.0 (2011) and SPAC (2022-23)
- **Space SPAC cohort**: Most went public 2021 at peak valuations
