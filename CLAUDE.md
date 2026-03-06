# Historic Fund Model

## Overview

Research infrastructure for analyzing capital flows across space, biotechnology, and energy sectors (2008-present). Combines three data sources—private fundraising (SEC EDGAR), public markets (stock APIs), and federal spending (USASpending.gov)—into a unified annual dataset for cross-sector analysis.

**Research Questions:**
1. Capital flow composition: When did private capital surpass government spending?
2. Growth trajectories: Do sectors follow similar patterns with time lag?
3. Leading indicators: Does federal spending predict private investment 1-3 years later?

## Tech Stack

- **Python 3.10+** — Pipeline automation
- **APIs:** SEC EDGAR (Form D), USASpending.gov, Yahoo Finance/Alpha Vantage
- **Claude API (Haiku)** — LLM classification for ambiguous cases
- **Data:** JSON output, PostgreSQL/DuckDB for intermediate storage
- **Libraries:** requests, lxml, pandas, yfinance

## Project Structure

```
/
├── CLAUDE.md                         # This file
├── data/
│   ├── data-collection.md            # Complete pipeline specification (40KB)
│   ├── domains-space.csv             # 51 space sector domains
│   ├── domains-bio.csv               # 51 bio sector domains
│   ├── domains-energy.csv            # 50 energy sector domains
│   ├── naics-to-domain-mapping.json  # NAICS → domain classification (contracts)
│   ├── cfda-to-domain-mapping.json   # CFDA → domain classification (assistance)
│   ├── cfda-inventory.json           # Inventory of all CFDA codes in data
│   ├── taxonomy-validation-notes.md  # Phase 0 completion audit
│   └── usaspending/                  # Raw USASpending CSV downloads
│       ├── NASA/                     # FY2008-FY2026 contracts & assistance
│       ├── DoE/                      # FY2008-FY2026 contracts & assistance
│       ├── DoD/                      # FY2008-FY2026 (contracts in subfolders)
│       ├── HHS/                      # FY2008-FY2026 contracts & assistance
│       └── NSF/                      # FY2008-FY2026 contracts & assistance
├── scripts/
│   ├── classify_companies.py         # Crunchbase → domain classification
│   ├── test_usaspending_parse.py     # USASpending CSV structure tests
│   └── test_cfda_inventory.py        # CFDA code inventory scanner
└── .claude/
    ├── settings.local.json           # Permission configuration
    └── docs/                         # Additional documentation
        └── architectural_patterns.md # Design patterns & conventions
```

## Key Files

| File | Purpose |
|------|---------|
| `data/data-collection.md` | Complete methodology spec — read this first |
| `data/domains-*.csv` | **Single source of truth** for all classification |
| `data/naics-to-domain-mapping.json` | 90 NAICS codes → domains (for contracts) |
| `data/cfda-to-domain-mapping.json` | 93 CFDA codes → domains (for assistance/grants) |

## Current Status

- **Phase 0 (Taxonomy):** Complete
- **Pipeline 1 (Private/Public Markets):** Complete (Steps 1.1-1.11)
- **Pipeline 2 (Government Spending):** Step 2.2 in progress (bulk data downloaded, parsing next)
- **Pipeline 3 (Stitching):** Not started

Progress tracked in `data/data-collection.md:14-42`

## IMPORTANT: Keep Documentation Updated

**Always update `data/data-collection.md` as work progresses:**
- Update the Progress Tracker table when steps change status
- Document any methodology changes discovered during implementation
- Note data quality issues or coverage gaps

## Commands

**Classification script:**
```bash
# Set API key first
export ANTHROPIC_API_KEY="your-key-here"

# Dry run (test parser, no API calls)
python3 scripts/classify_companies.py --sector space --dry-run

# Process single sector
python3 scripts/classify_companies.py --sector space

# Process all sectors
python3 scripts/classify_companies.py --all

# Test with limit
python3 scripts/classify_companies.py --sector space --limit 10
```

**API rate limits:**

```bash
# API rate limits
# SEC EDGAR: 10 req/sec, requires User-Agent header
# USASpending: 10 req/sec unauthenticated
# Claude API: ~1000 req/min for Haiku

# Recommended execution order
# 1. Start with space sector (smallest: ~300-500 companies)
# 2. Pipeline 1 and 2 can run in parallel
# 3. Pipeline 3 runs after both complete
```

## Classification System

**All companies and awards are classified into domains from the CSV files.**

**Private market (Pipeline 1):**
1. Crunchbase tags → search filter only (not classification)
2. Claude API → classifies companies into domains from CSV

**Government spending (Pipeline 2):**
1. Contracts → NAICS codes for high-confidence domain assignment
2. Assistance/Grants → CFDA codes for sector/domain assignment
3. Claude API → classifies ambiguous cases (DoD/NSF cross-cutting research)

See `data/data-collection.md:153-250` for full classification methodology.

## Version Control Practices

**General principles:**
- All changes tracked through Git with clear, descriptive commit messages
- Version history serves as institutional memory documenting principle evolution
- Before pushing, ensure remote changes are pulled and reconciled
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `docs:`

**Git authorship (CRITICAL):**
- Commits must be authored by the human decision-maker
- Do NOT include "Claude" or AI assistant references in commit messages or co-authorship
- Human accountability requires clear human authorship in version control

**When committing changes:**
1. Read the file first to understand current state
2. Make targeted, purposeful edits
3. Write commit messages explaining the "why" not just the "what"
4. Ensure commit messages reflect institutional decision-making

## Additional Documentation

When working on specific topics, check these files:

| Topic | File |
|-------|------|
| Architectural patterns & conventions | `.claude/docs/architectural_patterns.md` |
| Full pipeline methodology | `data/data-collection.md` |
| Domain definitions | `data/domains-{sector}.csv` |
| NAICS classification (contracts) | `data/naics-to-domain-mapping.json` |
| CFDA classification (assistance) | `data/cfda-to-domain-mapping.json` |
| CFDA inventory from data | `data/cfda-inventory.json` |
| Validation checklist | `data/taxonomy-validation-notes.md` |
