#!/usr/bin/env python3
"""
Generate research findings from the unified dataset.
Outputs: data/research-findings.md
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import statistics

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MASTER_FILE = DATA_DIR / "master" / "all-sectors-unified.json"

SECTORS = ["space", "bio", "energy"]


def load_data():
    """Load the master unified dataset."""
    with open(MASTER_FILE) as f:
        data = json.load(f)

    # Filter out "_general" categories (catch-all buckets that distort analysis)
    records = [r for r in data["records"] if not r["domain"].endswith("_general")]

    print(f"  Filtered out _general categories: {len(data['records'])} -> {len(records)} records")

    return records


def aggregate_by_sector_year(records):
    """Aggregate records to sector-year level."""
    agg = defaultdict(lambda: {
        "private": 0, "govt": 0, "market_cap": 0,
        "private_count": 0, "govt_count": 0, "public_count": 0
    })

    for r in records:
        key = (r["sector"], r["year"])
        if r["private"] and r["private"]["capital_raised"]:
            agg[key]["private"] += r["private"]["capital_raised"]
            agg[key]["private_count"] += 1
        if r["government"] and r["government"]["outlayed"]:
            agg[key]["govt"] += r["government"]["outlayed"]
            agg[key]["govt_count"] += 1
        if r["public"] and r["public"]["market_cap_eoy"]:
            agg[key]["market_cap"] += r["public"]["market_cap_eoy"]
            agg[key]["public_count"] += 1

    return agg


def format_dollars(amount, billions=True):
    """Format dollar amounts."""
    if amount is None or amount == 0:
        return "-"
    if billions:
        return f"${amount/1e9:.2f}B"
    else:
        return f"${amount/1e6:.1f}M"


def calculate_cagr(start_value, end_value, years):
    """Calculate compound annual growth rate."""
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return None
    return (end_value / start_value) ** (1 / years) - 1


def generate_rq1_analysis(records, agg):
    """RQ1: Capital Flow Composition"""
    md = []
    md.append("## RQ1: Capital Flow Composition\n")
    md.append("**Question:** How has the ratio of private-to-government capital shifted over time, and when did private capital surpass government outlays?\n")

    # Annual totals by sector
    for sector in SECTORS:
        md.append(f"\n### {sector.upper()} - Annual Capital Flows\n")
        md.append("| Year | Private Raised | Govt Outlayed | Public Market Cap | Private Share | Govt Share |")
        md.append("|------|----------------|---------------|-------------------|---------------|------------|")

        crossover_year = None

        for year in range(2008, 2027):
            key = (sector, year)
            data = agg.get(key, {"private": 0, "govt": 0, "market_cap": 0})

            private = data["private"]
            govt = data["govt"]
            market_cap = data["market_cap"]
            total = private + govt

            if total > 0:
                private_share = private / total
                govt_share = govt / total

                if private_share > 0.5 and crossover_year is None and private > 0:
                    crossover_year = year

                md.append(f"| {year} | {format_dollars(private)} | {format_dollars(govt)} | {format_dollars(market_cap)} | {private_share:.1%} | {govt_share:.1%} |")
            else:
                md.append(f"| {year} | - | - | - | - | - |")

        if crossover_year:
            md.append(f"\n**Crossover Year:** {crossover_year} (first year private share > 50%)\n")
        else:
            md.append(f"\n**Crossover Year:** Not yet reached (government still dominates)\n")

    # Summary table
    md.append("\n### Cross-Sector Comparison (2008-2026 Totals)\n")
    md.append("| Sector | Total Private | Total Govt | Total Inflows | Private Share | Crossover Year |")
    md.append("|--------|---------------|------------|---------------|---------------|----------------|")

    for sector in SECTORS:
        total_private = sum(agg.get((sector, y), {}).get("private", 0) for y in range(2008, 2027))
        total_govt = sum(agg.get((sector, y), {}).get("govt", 0) for y in range(2008, 2027))
        total_inflows = total_private + total_govt
        private_share = total_private / total_inflows if total_inflows > 0 else 0

        # Find crossover
        crossover = "N/A"
        for year in range(2008, 2027):
            key = (sector, year)
            data = agg.get(key, {"private": 0, "govt": 0})
            total = data["private"] + data["govt"]
            if total > 0 and data["private"] / total > 0.5:
                crossover = str(year)
                break

        md.append(f"| {sector.capitalize()} | {format_dollars(total_private)} | {format_dollars(total_govt)} | {format_dollars(total_inflows)} | {private_share:.1%} | {crossover} |")

    return "\n".join(md)


def generate_rq2_analysis(records, agg):
    """RQ2: Growth Trajectory Comparison"""
    md = []
    md.append("## RQ2: Growth Trajectory Comparison\n")
    md.append("**Question:** Do space, bio, and energy follow similar growth curves? Where is space today compared to where bio/energy were earlier?\n")

    # Get 2008 baselines
    baselines = {}
    for sector in SECTORS:
        key = (sector, 2008)
        data = agg.get(key, {"private": 0, "govt": 0})
        baselines[sector] = {
            "private": data["private"] if data["private"] > 0 else None,
            "govt": data["govt"] if data["govt"] > 0 else None
        }

    # Indexed growth table
    md.append("\n### Indexed Private Capital Growth (2008 = 1.0)\n")
    md.append("| Year | Space | Bio | Energy |")
    md.append("|------|-------|-----|--------|")

    for year in range(2008, 2027):
        row = [str(year)]
        for sector in SECTORS:
            key = (sector, year)
            data = agg.get(key, {"private": 0})
            baseline = baselines[sector]["private"]
            if baseline and data["private"] > 0:
                indexed = data["private"] / baseline
                row.append(f"{indexed:.2f}x")
            else:
                row.append("-")
        md.append("| " + " | ".join(row) + " |")

    # Indexed govt growth
    md.append("\n### Indexed Government Outlays Growth (2008 = 1.0)\n")
    md.append("| Year | Space | Bio | Energy |")
    md.append("|------|-------|-----|--------|")

    for year in range(2008, 2027):
        row = [str(year)]
        for sector in SECTORS:
            key = (sector, year)
            data = agg.get(key, {"govt": 0})
            baseline = baselines[sector]["govt"]
            if baseline and data["govt"] > 0:
                indexed = data["govt"] / baseline
                row.append(f"{indexed:.2f}x")
            else:
                row.append("-")
        md.append("| " + " | ".join(row) + " |")

    # CAGR calculations
    md.append("\n### Compound Annual Growth Rates (CAGR)\n")
    md.append("| Sector | Private CAGR (2008-2024) | Govt CAGR (2008-2024) |")
    md.append("|--------|--------------------------|----------------------|")

    for sector in SECTORS:
        start_private = agg.get((sector, 2008), {}).get("private", 0)
        end_private = agg.get((sector, 2024), {}).get("private", 0)
        start_govt = agg.get((sector, 2008), {}).get("govt", 0)
        end_govt = agg.get((sector, 2024), {}).get("govt", 0)

        private_cagr = calculate_cagr(start_private, end_private, 16)
        govt_cagr = calculate_cagr(start_govt, end_govt, 16)

        private_str = f"{private_cagr:.1%}" if private_cagr else "-"
        govt_str = f"{govt_cagr:.1%}" if govt_cagr else "-"

        md.append(f"| {sector.capitalize()} | {private_str} | {govt_str} |")

    # Capital efficiency
    md.append("\n### Capital Efficiency (Market Cap / Cumulative Private Raised)\n")
    md.append("| Year | Space | Bio | Energy |")
    md.append("|------|-------|-----|--------|")

    cumulative = {s: 0 for s in SECTORS}
    for year in range(2008, 2027):
        row = [str(year)]
        for sector in SECTORS:
            key = (sector, year)
            data = agg.get(key, {"private": 0, "market_cap": 0})
            cumulative[sector] += data["private"]

            if cumulative[sector] > 0 and data["market_cap"] > 0:
                efficiency = data["market_cap"] / cumulative[sector]
                row.append(f"{efficiency:.1f}x")
            else:
                row.append("-")
        md.append("| " + " | ".join(row) + " |")

    # Time-lag estimation
    md.append("\n### Time-Lag Estimation\n")
    md.append("*Where is Space today compared to where Bio/Energy were earlier?*\n")

    # Get space's 2024 indexed value
    space_2024_private = agg.get(("space", 2024), {}).get("private", 0)
    space_baseline = baselines["space"]["private"]

    if space_baseline and space_2024_private:
        space_indexed = space_2024_private / space_baseline
        md.append(f"Space 2024 private capital indexed value: **{space_indexed:.1f}x** (vs 2008 baseline)\n")

        # Find when bio/energy reached this level
        for sector in ["bio", "energy"]:
            baseline = baselines[sector]["private"]
            if baseline:
                for year in range(2008, 2027):
                    data = agg.get((sector, year), {}).get("private", 0)
                    if data > 0 and data / baseline >= space_indexed:
                        md.append(f"- {sector.capitalize()} reached {space_indexed:.1f}x in **{year}** (Space lags by ~{2024 - year} years)")
                        break

    return "\n".join(md)


def generate_rq3_analysis(records):
    """RQ3: Government Spending as Leading Indicator"""
    md = []
    md.append("## RQ3: Government Spending as Leading Indicator\n")
    md.append("**Question:** Does government spending in year N predict private capital in years N+1, N+2, N+3?\n")

    # Build domain-level time series
    domain_series = defaultdict(lambda: {"govt": {}, "private": {}})

    for r in records:
        domain = r["domain"]
        year = r["year"]

        if r["government"] and r["government"]["outlayed"]:
            domain_series[domain]["govt"][year] = r["government"]["outlayed"]
        if r["private"] and r["private"]["capital_raised"]:
            domain_series[domain]["private"][year] = r["private"]["capital_raised"]

    # Calculate correlations for domains with sufficient data
    correlations = []

    for domain, series in domain_series.items():
        govt_years = set(series["govt"].keys())
        private_years = set(series["private"].keys())

        # Need at least 5 overlapping years for meaningful correlation
        for lag in [0, 1, 2, 3]:
            govt_values = []
            private_values = []

            for year in range(2008, 2024):
                if year in series["govt"] and (year + lag) in series["private"]:
                    govt_values.append(series["govt"][year])
                    private_values.append(series["private"][year + lag])

            if len(govt_values) >= 5:
                # Calculate Pearson correlation
                n = len(govt_values)
                mean_g = sum(govt_values) / n
                mean_p = sum(private_values) / n

                numerator = sum((g - mean_g) * (p - mean_p) for g, p in zip(govt_values, private_values))
                denom_g = sum((g - mean_g) ** 2 for g in govt_values) ** 0.5
                denom_p = sum((p - mean_p) ** 2 for p in private_values) ** 0.5

                if denom_g > 0 and denom_p > 0:
                    corr = numerator / (denom_g * denom_p)
                    correlations.append({
                        "domain": domain,
                        "lag": lag,
                        "correlation": corr,
                        "n": n,
                        "total_govt": sum(govt_values),
                        "total_private": sum(private_values)
                    })

    # Summary by lag
    md.append("\n### Correlation by Lag (All Domains)\n")
    md.append("| Lag (Years) | Avg Correlation | Domains with r > 0.5 | Domains with r > 0.7 |")
    md.append("|-------------|-----------------|----------------------|----------------------|")

    for lag in [0, 1, 2, 3]:
        lag_corrs = [c for c in correlations if c["lag"] == lag]
        if lag_corrs:
            avg_corr = sum(c["correlation"] for c in lag_corrs) / len(lag_corrs)
            high_corr = sum(1 for c in lag_corrs if c["correlation"] > 0.5)
            very_high = sum(1 for c in lag_corrs if c["correlation"] > 0.7)
            md.append(f"| {lag} | {avg_corr:.3f} | {high_corr} | {very_high} |")

    # Top domains by correlation (lag 1-2)
    md.append("\n### Top Domains: Government Leads Private Capital (1-2 Year Lag)\n")
    md.append("| Domain | Lag | Correlation | Govt Total | Private Total |")
    md.append("|--------|-----|-------------|------------|---------------|")

    lag_1_2 = [c for c in correlations if c["lag"] in [1, 2] and c["correlation"] > 0.3]
    lag_1_2.sort(key=lambda x: -x["correlation"])

    for c in lag_1_2[:15]:
        md.append(f"| {c['domain']} | {c['lag']} | {c['correlation']:.3f} | {format_dollars(c['total_govt'])} | {format_dollars(c['total_private'])} |")

    # Negative correlations (govt crowds out private?)
    md.append("\n### Domains with Negative Correlation (Potential Crowding Out?)\n")
    md.append("| Domain | Lag | Correlation | Govt Total | Private Total |")
    md.append("|--------|-----|-------------|------------|---------------|")

    negative = [c for c in correlations if c["correlation"] < -0.3]
    negative.sort(key=lambda x: x["correlation"])

    for c in negative[:10]:
        md.append(f"| {c['domain']} | {c['lag']} | {c['correlation']:.3f} | {format_dollars(c['total_govt'])} | {format_dollars(c['total_private'])} |")

    return "\n".join(md)


def generate_additional_stats(records, agg):
    """Additional summary statistics."""
    md = []
    md.append("## Additional Statistics\n")

    # Top domains by total capital
    md.append("### Top 10 Domains by Total Capital (Private + Government)\n")

    domain_totals = defaultdict(lambda: {"private": 0, "govt": 0, "sector": None})
    for r in records:
        domain = r["domain"]
        domain_totals[domain]["sector"] = r["sector"]
        if r["private"] and r["private"]["capital_raised"]:
            domain_totals[domain]["private"] += r["private"]["capital_raised"]
        if r["government"] and r["government"]["outlayed"]:
            domain_totals[domain]["govt"] += r["government"]["outlayed"]

    for sector in SECTORS:
        md.append(f"\n**{sector.upper()}:**\n")
        md.append("| Rank | Domain | Private | Government | Total |")
        md.append("|------|--------|---------|------------|-------|")

        sector_domains = [(d, v) for d, v in domain_totals.items() if v["sector"] == sector]
        sector_domains.sort(key=lambda x: -(x[1]["private"] + x[1]["govt"]))

        for i, (domain, vals) in enumerate(sector_domains[:10], 1):
            total = vals["private"] + vals["govt"]
            md.append(f"| {i} | {domain} | {format_dollars(vals['private'])} | {format_dollars(vals['govt'])} | {format_dollars(total)} |")

    # Data coverage
    md.append("\n### Data Coverage Summary\n")
    md.append("| Sector | Years with Private Data | Years with Public Data | Years with Govt Data |")
    md.append("|--------|------------------------|------------------------|----------------------|")

    for sector in SECTORS:
        private_years = sum(1 for y in range(2008, 2027) if agg.get((sector, y), {}).get("private", 0) > 0)
        public_years = sum(1 for y in range(2008, 2027) if agg.get((sector, y), {}).get("market_cap", 0) > 0)
        govt_years = sum(1 for y in range(2008, 2027) if agg.get((sector, y), {}).get("govt", 0) > 0)
        md.append(f"| {sector.capitalize()} | {private_years}/19 | {public_years}/19 | {govt_years}/19 |")

    # Year-over-year growth
    md.append("\n### Year-over-Year Growth Rates (Private Capital)\n")
    md.append("| Year | Space | Bio | Energy |")
    md.append("|------|-------|-----|--------|")

    for year in range(2009, 2027):
        row = [str(year)]
        for sector in SECTORS:
            curr = agg.get((sector, year), {}).get("private", 0)
            prev = agg.get((sector, year - 1), {}).get("private", 0)
            if curr > 0 and prev > 0:
                growth = (curr - prev) / prev
                row.append(f"{growth:+.0%}")
            else:
                row.append("-")
        md.append("| " + " | ".join(row) + " |")

    return "\n".join(md)


def main():
    print("Generating Research Findings...")

    # Load data
    records = load_data()
    print(f"  Loaded {len(records)} unified records")

    # Aggregate
    agg = aggregate_by_sector_year(records)

    # Generate analyses
    sections = []

    # Header
    sections.append(f"""# Research Findings: Capital Flows in Space, Bio, and Energy

*Generated: {datetime.now().strftime('%B %d, %Y')}*

This analysis covers capital flows from 2008-2026 across three sectors, combining:
- **Private Market:** SEC Form D filings (Reg D offerings)
- **Public Market:** End-of-year market capitalizations
- **Government:** Federal contract and grant outlays (USASpending)

---
""")

    # RQ1
    print("  Generating RQ1 analysis...")
    sections.append(generate_rq1_analysis(records, agg))

    sections.append("\n---\n")

    # RQ2
    print("  Generating RQ2 analysis...")
    sections.append(generate_rq2_analysis(records, agg))

    sections.append("\n---\n")

    # RQ3
    print("  Generating RQ3 analysis...")
    sections.append(generate_rq3_analysis(records))

    sections.append("\n---\n")

    # Additional stats
    print("  Generating additional statistics...")
    sections.append(generate_additional_stats(records, agg))

    # Methodology note
    sections.append("""
---

## Methodology Notes

### Data Sources
- **Private Market:** Crunchbase company universe → SEC EDGAR Form D filings
- **Public Market:** Yahoo Finance market data for IPO'd companies
- **Government:** USASpending.gov bulk downloads (NASA, DoE, HHS, NSF, DoD)

### Limitations
- Private market data only captures SEC-registered Reg D offerings (~60-70% of private capital)
- Government data excludes classified spending (significant for space/defense)
- Government data excludes tax incentives (significant for energy)
- Public market data starts when companies IPO (survivorship bias)

### Classification
- Companies classified into domains using Claude API (LLM)
- Government awards classified using NAICS/CFDA codes + LLM for ambiguous cases
- All domains validated against canonical taxonomy (50 domains per sector)
""")

    # Write output
    output_path = DATA_DIR / "research-findings.md"
    with open(output_path, 'w') as f:
        f.write("\n".join(sections))

    print(f"\n  Saved to: {output_path}")
    print("Done!")


if __name__ == "__main__":
    main()
