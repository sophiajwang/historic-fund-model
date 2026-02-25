# Returns Model Methodology
## Space vs. Bio vs. Energy — Total Value Creation & Cohort Analysis

---

## Overview

This model has three layers, built in sequence. Each layer builds on the data from the previous one.

**Layer 1: Total Value Creation Accounting (primary)**
→ "Has this sector created or destroyed value, and how much?"

**Layer 2: Vintage Cohort Analysis (primary)**
→ "If you invested in companies founded in year X, what happened?"

**Layer 3: Public Market Portfolio Simulation (supplementary)**
→ "How would a passive basket of public companies in each sector have performed?"

Each layer is built using the company universes constructed in the prior phase (~57 space, ~220-290 bio, ~120-155 energy).

---

## Layer 1: Total Value Creation Accounting

### Concept

For each sector, calculate:

```
Sector Gross Multiple = Total Value Created / Total Capital Invested
```

Where:
- **Total Value Created** = sum of all current market caps + acquisition prices received + estimated private company valuations
- **Total Capital Invested** = sum of all equity capital raised (VC rounds + IPO/SPAC proceeds + follow-on offerings) + government grants/loans deployed

This produces a single headline number per sector: "For every $1 invested in space/bio/energy, the sector is currently worth $X."

### Data Collection Template

For every company in the universe, collect:

#### Capital Invested (Input Side)

| Field | Source (Hard Data) | Source (Estimate) | Notes |
|---|---|---|---|
| total_vc_funding_raised | Crunchbase, SEC S-1 filings | Press reports | Sum of all pre-IPO equity rounds |
| ipo_spac_proceeds | SEC S-1, SPAC proxy (424B filings) | N/A | Cash raised at IPO/SPAC, not enterprise value |
| secondary_offerings | SEC prospectus filings | N/A | Follow-on equity raises post-IPO |
| government_grants_loans | DOE LPO, NASA SBIR, NIH Reporter, USASpending.gov | N/A | Include only equity-like grants and forgivable loans; exclude procurement contracts (those are revenue, not capital) |
| total_capital_invested | = sum of above | | |

**Critical distinction:** Procurement contracts (e.g., NASA paying SpaceX for launches, DoD buying satellites) are NOT capital invested. They are revenue. Government R&D grants and DOE loans ARE capital invested because they fund the company's development with risk of loss. This distinction matters a lot for space where government contracts are large.

**What counts as VC funding for acquired companies:** Total VC raised through the last private round before exit. For companies that IPO'd and were later acquired, include VC + IPO proceeds + secondary offerings.

#### Value Created (Output Side)

| Field | Source (Hard Data) | Source (Estimate) | Tier |
|---|---|---|---|
| current_market_cap | Current stock price × shares outstanding (Yahoo Finance) | N/A | Hard data (public cos) |
| acquisition_price | SEC 8-K filings, merger proxy | N/A | Hard data |
| bankruptcy_recovery | SEC bankruptcy filings, asset sale records | Press reports | Hard data where available |
| last_private_valuation | SEC filings (sometimes disclosed in late rounds), secondary market data | Press-reported round valuations | **Estimate — flagged separately** |
| estimated_current_private_value | N/A | Last round valuation adjusted for time / reported markdowns | **Estimate — flagged separately** |

### Tiering System for Data Quality

Every value figure gets tagged:

| Tier | Definition | Use in Model |
|---|---|---|
| **Tier 1: Hard** | SEC filing, public market price, confirmed acquisition price | Primary analysis |
| **Tier 2: Reported** | Press-reported funding round at specific valuation, widely corroborated by multiple outlets | Primary analysis, flagged |
| **Tier 3: Estimated** | Inferred from partial data (e.g., funding amount + estimated dilution → implied valuation), single-source reports | Supplementary analysis only |
| **Tier 4: Unknown** | No reliable data | Excluded from quantitative analysis, noted as gap |

### Presentation Format

**Primary output (hard data only — Tier 1 + Tier 2):**

| Metric | Space | Bio | Energy |
|---|---|---|---|
| Total Capital Invested ($B) | | | |
| Total Value — Public Cos (current market caps) | | | |
| Total Value — Acquisitions (at deal price) | | | |
| Total Value — Hard Data Subtotal | | | |
| Gross Multiple (Hard Data Only) | | | |
| Capital Destroyed (bankruptcies at invested capital) | | | |

**Supplementary output (includes Tier 3 estimates):**

| Metric | Space | Bio | Energy |
|---|---|---|---|
| Total Value — Private Cos (estimated) | | | |
| Total Value — All-In Estimate | | | |
| Gross Multiple (All-In Estimate) | | | |

**Key analytical cuts:**

1. **With and without the dominant outlier:**
   - Space: show multiple with and without SpaceX
   - Energy: show multiple with and without Tesla
   - Bio: no single outlier to remove (this IS the finding — bio's returns are distributed)

2. **By market status:**
   - Value in currently public companies
   - Value captured via acquisitions
   - Value estimated in private companies
   - Value destroyed (bankruptcies + write-downs)

3. **By sub-sector:** Roll up the same calculation for each sub-sector (launch, EO, comms for space; therapeutics, genomics, tools for bio; solar, EV, storage, nuclear for energy)

### Handling SpaceX

SpaceX is the elephant in the room. It's ~$350B of estimated value, which likely exceeds the rest of the space universe combined. Two approaches:

**Approach A (conservative):** Use the most recent secondary market transaction price as Tier 2 data. SpaceX conducts regular tender offers to employees at set prices, and these are widely reported. The December 2024 tender at ~$350B is well-documented. This is closer to "hard data" than most private valuations because there are actual transactions.

**Approach B (bracket):** Present a range. Low end: last confirmed tender price. High end: analyst estimates (Morgan Stanley has published $350-400B+). Show the model output at both endpoints.

**Recommendation:** Use Approach A as primary (Tier 2), note the range as context. Be transparent that SpaceX represents X% of total space sector value creation and that the story changes dramatically without it.

### Handling Blue Origin

Blue Origin is uniquely difficult. It's primarily funded by Jeff Bezos' personal wealth, not by traditional VC rounds. There's no confirmed valuation. Options:

1. **Exclude from quantitative analysis.** Note it as a gap. Rational because there's no real data.
2. **Include at a rough estimate** based on comparable (e.g., value relative to SpaceX based on launch cadence, backlog, etc.). This is Tier 3 at best.
3. **Include capital invested only** (Bezos has reportedly invested $1B+/year → ~$10-15B+ total). Show it as value destruction vs. invested capital since there's no confirmed value created.

**Recommendation:** Option 1 for primary analysis, Option 3 as supplementary context. Be transparent.

---

## Layer 2: Vintage Cohort Analysis

### Concept

Group every company by **vintage cohort** (5-year founded windows) and track outcomes. This answers the VC-native question: "What's the hit rate and return distribution for companies started in each era?"

### Cohort Definitions

| Cohort | Founded | Era Context |
|---|---|---|
| Cohort 1 | Pre-2000 (tracked from 2000) | Legacy / pre-boom |
| Cohort 2 | 2000–2004 | Early technology (SpaceX, early cleantech, post-genome bio) |
| Cohort 3 | 2005–2009 | Cleantech 1.0 boom, biotech growth, space still dormant |
| Cohort 4 | 2010–2014 | Post-bust recovery, new space begins, biotech IPO boom |
| Cohort 5 | 2015–2019 | Main new space wave, CRISPR era, cleantech 2.0, fusion |
| Cohort 6 | 2020–2025 | SPAC era, IRA era, AI-bio, most recent vintage |

### Data Collection Per Cohort

For each cohort in each sector, calculate:

| Metric | How to Calculate |
|---|---|
| **N (universe size)** | Count of companies in cohort |
| **Total capital raised** | Sum of total_capital_invested for all companies in cohort |
| **Outcomes distribution** | Count and % in each bucket: still_private, public_active, acquired, bankrupt/failed |
| **Acquisitions — count and total value** | Count of acquired companies, sum of acquisition prices |
| **Acquisitions — median and mean multiple** | acquisition_price / total_capital_invested for each acquired company, then median and mean |
| **Public — current aggregate market cap** | Sum of current market caps for companies still public |
| **Public — aggregate return vs. invested capital** | current_aggregate_market_cap / total_ipo_spac_proceeds |
| **Failures — count and total capital lost** | Count of bankrupt/failed, sum of their total_capital_invested |
| **Failure rate** | failures / N |
| **Hit rate (>1x return)** | Companies where current_value > total_capital_invested / N |
| **Big hit rate (>10x)** | Companies where current_value > 10 × total_capital_invested / N |

### Presentation Format

**Table per sector (Space example):**

| Metric | Pre-2000 | 2000–04 | 2005–09 | 2010–14 | 2015–19 | 2020–25 |
|---|---|---|---|---|---|---|
| Companies (N) | | | | | | |
| Total Capital In ($M) | | | | | | |
| Still Private (%) | | | | | | |
| Public Active (%) | | | | | | |
| Acquired (%) | | | | | | |
| Failed (%) | | | | | | |
| Total Value Out ($M) | | | | | | |
| Cohort Gross Multiple | | | | | | |
| Median Company Multiple | | | | | | |
| Big Hits (>10x) | | | | | | |

**Cross-sector comparison chart:**

For the LP deck, the most powerful visual is a side-by-side of failure rates and hit rates by cohort across all three sectors. This shows:
- Whether space's failure rate is higher, lower, or comparable to bio/energy at the same maturity stage
- Whether the "winners win bigger" narrative holds (do space big hits return more than bio/energy big hits?)
- How the distribution shape differs (bio: many moderate exits; energy: bimodal with lots of failures + Tesla; space: TBD but likely dominated by SpaceX)

### Maturity Adjustment

A critical issue: space's cohorts are younger than bio's. A company founded in 2018 in bio has had time to reach Phase 3 and get acquired. A space company founded in 2018 may still be pre-revenue. To make cohorts comparable:

**Option 1: Time-to-outcome normalization.** For each sector, calculate the median time from founding to exit (IPO, acquisition, or failure). Use this to set expectations for which cohorts are "mature" vs. "still cooking."

Expected medians (to be confirmed with data):
- Bio: ~8-12 years from founding to acquisition; ~7-10 years to IPO
- Energy: ~6-10 years to IPO; acquisitions vary widely
- Space: ~8-12 years to IPO (the SPAC cohort was ~5-7 years but that was unusual)

**Option 2: Only compare "mature" cohorts.** Restrict the cross-sector comparison to cohorts with ≥10 years of seasoning (Pre-2000 through 2010-2014). Flag 2015+ cohorts as "immature — outcomes pending."

**Recommendation:** Do both. Show all cohorts in the full table, but highlight the mature cohort comparison separately. Note that space's most recent cohorts (2015+) are where most of the activity is, and these are too young to evaluate on outcomes yet — which is itself a finding about sector maturity.

---

## Layer 3: Public Market Portfolio Simulation (Supplementary)

### Concept

Construct a hypothetical equal-weight portfolio of all public pure-play companies in each sector, rebalanced annually, and calculate cumulative total return vs. benchmarks.

This is the most verifiable analysis (anyone can replicate it) and useful as a supplementary "sanity check" on the other layers.

### Construction Rules

1. **Universe:** All companies tagged as public_ipo or public_spac in the sector universe that were listed for ≥1 full calendar year
2. **Entry date:** First full calendar year after IPO/SPAC listing
3. **Exit date:** Delisting date, acquisition completion date, or end of study period
4. **Weighting:** Equal-weight, rebalanced annually on January 1
5. **Handling failures:** If a company goes to $0 (bankruptcy), the position goes to $0 in the portfolio. This is critical — do not drop failures, as that creates survivorship bias.
6. **Dividends:** Include (total return, not price return)

### Benchmarks
- S&P 500 Total Return (SPY)
- NASDAQ Composite Total Return (QQQ)
- Russell 2000 Total Return (IWM) — relevant because many space/bio/energy companies are small-cap

### Data Collection

**⚠️ ACTION REQUIRED:** For each public company in the universe:
1. Download monthly adjusted close prices from Yahoo Finance (accounts for splits and dividends)
2. Record listing date and delisting date (if applicable)
3. For acquired companies, use the acquisition price as the final portfolio value for that position

This is the most data-intensive step but the most mechanical. Can be done in a spreadsheet.

### Time Windows

| Window | Start | End | Notes |
|---|---|---|---|
| Full period | Jan 2000 | Present | Very few space pure-plays before 2021; bio and energy have full coverage |
| Post-GFC | Jan 2010 | Present | Tesla IPO era, new space begins |
| New Space era | Jan 2018 | Present | When multiple space companies became public/near-public |
| Post-SPAC | Jan 2021 | Present | Most apples-to-apples window for all three sectors |

### Presentation Format

**Line chart:** Cumulative $100 invested in each sector portfolio vs. benchmarks over each time window.

**Table:**

| Metric | Space | Bio (XBI proxy) | Energy | S&P 500 | NASDAQ |
|---|---|---|---|---|---|
| Cumulative Return (full period) | | | | | |
| Annualized Return | | | | | |
| Max Drawdown | | | | | |
| % of Companies that Outperformed S&P | | | | | |
| Best Performer (total return) | | | | | |
| Worst Performer (total return) | | | | | |

**Important caveat for the LP deck:** This layer inherently disadvantages space because (a) most space companies only went public in 2021 at peak valuations, and (b) SpaceX is excluded (private). Acknowledge this explicitly. The public market simulation tells you about the *accessible* investment universe, not the *full* sector opportunity.

---

## Execution Sequence

### Phase 1: Data Collection (estimated 4-6 hours)

| Step | Task | Time Est. | Output |
|---|---|---|---|
| 1a | Finalize company universes (live ETF pulls, EDGAR checks, cross-references per verification checklists) | 2-3 hrs | Final company lists for all 3 sectors |
| 1b | Collect capital invested data for each company (VC raised, IPO proceeds, gov grants) | 1-2 hrs | Capital invested column populated |
| 1c | Collect value data for each company (current market cap, acquisition price, last private valuation) | 1-2 hrs | Value created column populated |
| 1d | Download monthly stock prices for all public companies | 1 hr | Price history for Layer 3 |

### Phase 2: Layer 1 Model Build (estimated 2-3 hours)

| Step | Task | Time Est. | Output |
|---|---|---|---|
| 2a | Sum capital invested and value created per sector | 30 min | Headline gross multiples |
| 2b | Calculate with/without outlier variants | 30 min | SpaceX-adjusted, Tesla-adjusted figures |
| 2c | Break down by sub-sector | 1 hr | Sub-sector level multiples |
| 2d | Break down by data tier (hard vs. estimated) | 30 min | Primary vs. supplementary presentation |
| 2e | Build sensitivity analysis (what if SpaceX is worth $200B? $500B?) | 30 min | Range of outcomes |

### Phase 3: Layer 2 Model Build (estimated 2-3 hours)

| Step | Task | Time Est. | Output |
|---|---|---|---|
| 3a | Assign vintage cohorts to all companies | 30 min | Cohort tags |
| 3b | Calculate cohort-level metrics per sector | 1 hr | Cohort tables |
| 3c | Calculate cross-sector comparison metrics | 30 min | Side-by-side comparison |
| 3d | Maturity adjustment analysis | 30 min | Time-to-outcome medians, mature cohort callout |

### Phase 4: Layer 3 Model Build (estimated 2-3 hours)

| Step | Task | Time Est. | Output |
|---|---|---|---|
| 4a | Construct portfolio time series per sector | 1 hr | Monthly portfolio values |
| 4b | Calculate returns vs. benchmarks | 30 min | Return metrics |
| 4c | Generate charts | 30 min | Cumulative return line charts |
| 4d | Note limitations and caveats | 30 min | Written methodology notes |

### Phase 5: Synthesis & LP Deck Outputs (estimated 2-3 hours)

| Step | Task | Output |
|---|---|---|
| 5a | Write headline findings | 1-page summary of what the data shows |
| 5b | Build 5-8 key charts/tables for LP deck | Visual outputs |
| 5c | Write methodology appendix | Defensibility document for LP diligence |
| 5d | Document all data gaps and limitations | Transparency document |

---

## What Claude Can Do vs. What Requires Manual Work

| Task | Claude Can Do | Requires Manual Pull |
|---|---|---|
| Company universe (we've done this) | ✅ ~85% complete | Live ETF holdings, EDGAR queries, spot-checks |
| Capital invested — VC funding | ✅ Major companies from training data | Crunchbase for smaller companies |
| Capital invested — IPO proceeds | ✅ Major IPOs from training data | SEC S-1 filings for precise numbers |
| Capital invested — Gov grants | Partial (DOE loans for energy) | DOE LPO portfolio, NASA SBIR database, NIH Reporter |
| Value — Current market caps | ❌ Need live data | Yahoo Finance (5 min per sector) |
| Value — Acquisition prices | ✅ Major deals from training data | SEC 8-K filings for precision |
| Value — Private valuations | ✅ Widely-reported ones | Press cross-referencing |
| Monthly stock prices | ❌ Need live data | Yahoo Finance historical download |
| Layer 1 calculations | ✅ Once data is collected | |
| Layer 2 cohort analysis | ✅ Once data is collected | |
| Layer 3 portfolio simulation | ❌ Needs live price data | Spreadsheet model |
| Charts and visualizations | ✅ Can build in artifact | |
| Written analysis and narrative | ✅ | |
