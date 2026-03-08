# Historic Fund Model

## Overview

Research infrastructure for analyzing capital flows across space, biotechnology, and energy sectors (2008-present). Combines three data sources—private fundraising (SEC EDGAR), public markets (stock APIs), and federal spending (USASpending.gov)—into a unified annual dataset for cross-sector analysis.

**Research Questions:**
1. Capital flow composition: When did private capital surpass government spending?
2. Growth trajectories: Do sectors follow similar patterns with time lag?
3. Leading indicators: Does federal spending predict private investment 1-3 years later?

## Tech Stack

- **Python 3.10+** — Pipeline automation
- **APIs:** SEC EDGAR (Form D), USASpending.gov, Yahoo Finance
- **Claude API (Haiku)** — LLM classification for ambiguous cases
- **Data:** JSON intermediate/output, CSV for taxonomy and bulk downloads
- **Libraries:** requests, lxml, anthropic, yfinance

## Project Structure

```
/
├── scripts/                    # Pipeline automation (21 scripts)
│   ├── aggregate_*.py          # Roll up to sector/domain/year level
│   ├── classify_*.py           # Domain classification (rule + LLM)
│   ├── parse_*.py              # Raw data parsing
│   ├── pull_*.py               # Data fetching from APIs
│   └── stitch_data.py          # Pipeline 3: join all sources
├── data/
│   ├── domains-{sector}.csv    # Canonical taxonomy (source of truth)
│   ├── *-to-domain-mapping.json # NAICS/CFDA classification rules
│   ├── source/                 # Normalized per-source data
│   ├── unified/                # Joined data (Pipeline 3 output)
│   ├── master/                 # Final combined output
│   └── usaspending/            # Raw government CSVs
└── venv/                       # Python virtual environment
```

## Key Files

| File | Purpose |
|------|---------|
| `data/data-collection.md` | Complete methodology spec — read this first |
| `data/domains-*.csv` | **Single source of truth** for all classification |
| `data/unified/{sector}-unified.json` | Final joined output per sector |
| `data/research-findings.md` | Analysis results and key statistics |

## Current Status

**All pipelines complete.** Final output in `data/unified/` and `data/master/`.

Progress tracked in `data/data-collection.md:14-47`

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Common script patterns
python3 scripts/{script}.py --sector space    # Single sector
python3 scripts/{script}.py --all             # All sectors
python3 scripts/{script}.py --agency NSF      # By agency
python3 scripts/{script}.py --dry-run         # Test without side effects
python3 scripts/{script}.py --limit 100       # Process subset
```

**API requirements:**
```bash
export ANTHROPIC_API_KEY="your-key"  # For LLM classification
# SEC EDGAR: 10 req/sec, requires User-Agent header
# USASpending: 10 req/sec unauthenticated
```

## Classification System

All companies and awards classified into domains from CSV files:

1. **Private market:** Crunchbase tags → filter; Claude API → domain assignment
2. **Government:** NAICS/CFDA codes → high-confidence; Claude API → ambiguous cases

Classification output includes audit trail: `{domains, confidence, method, reasoning}`

See `data/data-collection.md:153-250` for full methodology.

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

| Topic | File |
|-------|------|
| Architectural patterns & conventions | `.claude/docs/architectural_patterns.md` |
| Full pipeline methodology | `data/data-collection.md` |
| Domain definitions | `data/domains-{sector}.csv` |
| NAICS classification (contracts) | `data/naics-to-domain-mapping.json` |
| CFDA classification (assistance) | `data/cfda-to-domain-mapping.json` |
| Research findings & statistics | `data/research-findings.md` |
