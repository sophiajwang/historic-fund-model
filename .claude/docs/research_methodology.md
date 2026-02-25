# Research Methodology Patterns

## Universe Construction Process

Reference: company-universe.md

Four-stage process applied identically to all sectors:

1. **Seed**: Pull candidate lists from ETFs, EDGAR SIC codes, industry reports, SPAC databases
2. **Screen**: Apply inclusion/exclusion filters
3. **Classify**: Tag by sub-sector, market status, vintage cohort
4. **Validate**: Cross-check against independent sources

## Inclusion Criteria

Reference: company-universe.md:110-118

ALL must be met:
- US-domiciled (HQ in US or primary US exchange listing)
- Active during study window (2000-2025)
- Primary sector revenue ≥50%
- Minimum materiality: Public ≥$50M market cap; Private ≥$10M raised OR ≥$10M acquisition

## Exclusion Criteria

Reference: company-universe.md:119-127

NONE can be met:
- Conglomerate (>$10B revenue, target sector <50%)
- Downstream consumer only (uses output, doesn't produce)
- Pure financial vehicle (SPACs without merger)
- Foreign-founded, US-listed only for capital access

## Sector-Specific Decisions

### Space
Reference: space-universe-execution.md:299-317

- Conglomerates (LMT, NOC, BA) tracked in appendix only
- Borderline defense (Anduril, Kratos) require revenue verification
- eVTOL companies (Joby, Archer) excluded — not space

### Bio
Reference: bio-universe-execution.md:250-258

- XBI + IBB union IS the public universe (too large to curate individually)
- Large pharma (Pfizer, Merck) excluded — tracked as acquirers
- Non-US founded (BioNTech, Argenx) excluded from primary, noted in appendix
- Tools companies (Illumina, 10x) included if >50% biotech end market

### Energy
Reference: energy-universe-execution.md:7-21

- Definition: Energy Technology & Clean Energy (not fossil incumbents)
- Semiconductor enablers (ON Semi, Wolfspeed) excluded
- Renewable utilities (NextEra) included as "renewable utility" sub-sector
- Software-only excluded unless directly controls energy assets

## Edge Case Protocol

Reference: company-universe.md:130-136

1. Check revenue split in 10-K segment data
2. If no segment data, read "Business" section first paragraph
3. If still ambiguous, flag as "borderline" in appendix
4. For pivoted companies, classify by business at exit/valuation event

## Cross-Sector Comparison Caveats

1. **Scale difference**: Bio ~250 companies vs Space ~57 — use rates, not counts
2. **Maturity difference**: Bio cohorts are older; space 2015+ cohorts "still cooking"
3. **Exit patterns differ**: Bio has rich M&A; space has few exits; energy has two bust cycles
4. **Outlier concentration**: SpaceX/Tesla dominate; Bio is distributed
