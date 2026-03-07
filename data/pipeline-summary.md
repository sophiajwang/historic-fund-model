# Pipeline Summary Statistics

*Generated: March 2026*

## Overview

This document summarizes the data collected across all three capital sources for the Historic Fund Model project, covering space, biotechnology, and energy sectors from 2008 to present.

---

## Pipeline 1: Private Market (SEC Form D)

| Metric | Value |
|--------|-------|
| Companies in universe (Crunchbase) | 2,998 |
| Matched to EDGAR | 1,697 (56.6%) |
| Companies with Form D filings | 1,435 |
| Total Form D filings parsed | 5,195 |
| Distinct offerings (after deduplication) | 4,293 |
| **Total capital tracked** | **$102B** |

### By Sector

| Sector | Companies | Match Rate | With Form D |
|--------|-----------|------------|-------------|
| Space | 998 | 44.5% | 397 |
| Bio | 1,000 | 70.2% | 546 |
| Energy | 1,000 | 55.1% | 492 |

---

## Pipeline 1: Public Market (Secondary)

| Metric | Value |
|--------|-------|
| Companies with S-1/S-4 filings | 262 |
| Public companies tracked | 169 |
| **Total market cap tracked** | **$1.2T** |

---

## Pipeline 2: Government Spending (USASpending)

### Raw Data Volume

| Agency | Contracts | Assistance | Total Obligation |
|--------|-----------|------------|------------------|
| NASA | 372,831 | 129,459 | $317.8B |
| DoE | 165,571 | 111,614 | $741.3B |
| HHS | 1,103,201 | 2,718,165 | $22.9T |
| NSF | 14,444 | 420,358 | $137.9B |
| DoD | 51,091,578 | 292,205 | $6.87T |
| **Total** | **52,747,625** | **3,671,801** | **$31.0T** |

### Classification Results

| Agency | Space | Bio | Energy | Not Applicable |
|--------|-------|-----|--------|----------------|
| NASA | 124 | 31 | 9 | 70 |
| DoE | 65 | 125 | 3,600 | 482 |
| HHS | 2 | 0 | 0 | 1 |
| DoD | 2,897 | 774 | 944 | 939 |
| NSF | 6,189 | 8,783 | 5,468 | 1,878 |
| **Total** | **9,277** | **9,713** | **10,021** | **3,370** |

### Filtering Efficiency

| Agency | Total Records | After Filtering | Reduction |
|--------|---------------|-----------------|-----------|
| NSF | 317,662 | 22,391 | 93.0% |
| DoD | 40,265,535 | 5,555 | 99.99% |

---

## Combined Summary

| Capital Source | Records/Entities | Capital Value |
|----------------|------------------|---------------|
| Private Market | 4,293 offerings | $102B raised |
| Public Market | 169 companies | $1.2T market cap |
| Government | 56.4M records | $31.0T obligated |

### Classification Methods

| Source | Method |
|--------|--------|
| Private (Crunchbase) | LLM classification (Claude Haiku) |
| Public | Inherited from private company classification |
| Government | NAICS/CFDA rules + LLM for ambiguous records |

---

## Next Steps

- [ ] Step 2.4: API cross-agency search (catch awards from non-primary agencies)
- [ ] Step 2.5: Aggregate annual government data
- [ ] Pipeline 3: Stitch all sources together
