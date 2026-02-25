# Data Collection Patterns

## Company Data Schema

Every company in the universe follows this structure:

```
{
  "company_name": string,
  "ticker": string | null,
  "sector": "space" | "bio" | "energy",
  "sub_sector": string,
  "market_status": "public_ipo" | "public_spac" | "public_spinoff" | "private_active" | "private_acquired" | "private_failed" | "public_delisted",
  "founded_year": number,
  "vintage_cohort": string,

  // Capital Invested
  "capital_invested": {
    "total_vc_funding_M": number | null,
    "ipo_spac_proceeds_M": number | null,
    "secondary_offerings_M": number | null,
    "government_grants_loans_M": number | null,
    "total_capital_invested_M": number | null
  },

  // Value Created
  "value_created": {
    "current_market_cap_M": number | null,
    "acquisition_price_M": number | null,
    "last_private_valuation_M": number | null,
    "valuation_date": string | null
  },

  // Metadata
  "data_tier": 1 | 2 | 3 | 4,
  "sources": string[],
  "notes": string | null
}
```

## Tiering Rules

Reference: model-methodology.md:69-76

| Tier | Definition | Example |
|------|------------|---------|
| 1 | SEC filing, public market price | Rocket Lab market cap from Yahoo Finance |
| 2 | Press-reported, multiple outlets | SpaceX tender offer valuation |
| 3 | Inferred from partial data | Private company valuation from funding + dilution |
| 4 | No reliable data | Blue Origin (Bezos-funded, no formal valuation) |

## Capital vs Revenue Distinction

Reference: model-methodology.md:53-56

Critical for space sector:
- **Capital invested**: VC rounds, IPO proceeds, government grants/loans (risk of loss)
- **NOT capital**: Procurement contracts (NASA launch contracts, DoD purchases)

## Handling Outliers

Reference: model-methodology.md:101-105

Always calculate metrics both:
1. With the dominant outlier (SpaceX for space, Tesla for energy)
2. Without the dominant outlier

Bio has no single dominant outlier — this IS a finding.

## Private Company Valuation Approach

Reference: model-methodology.md:116-133

For SpaceX:
- Use most recent tender offer price as Tier 2
- Note the range (analyst estimates) as context
- Flag % of sector value SpaceX represents

For Blue Origin:
- Exclude from quantitative analysis (Tier 4)
- Include capital invested only as supplementary context
- Document as a known gap
