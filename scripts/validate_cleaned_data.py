#!/usr/bin/env python3
"""
Validate cleaned data and generate comparison report.

Verifies that:
1. No duplicate market caps across domains (single attribution)
2. All market caps are within reasonable ranges
3. Compares before/after totals

Usage:
    python scripts/validate_cleaned_data.py

Output:
    data/cleaned/audit/validation_report.md
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CLEANED_DIR = DATA_DIR / "cleaned"
SOURCE_DIR = DATA_DIR / "source"
AUDIT_DIR = CLEANED_DIR / "audit"

SECTORS = ["space", "bio", "energy"]

# Validation thresholds
MAX_SECTOR_MARKET_CAP = {
    "space": 500e9,   # $500B
    "bio": 5e12,      # $5T
    "energy": 500e9,  # $500B
}


def load_unified_data(path: Path) -> list:
    """Load unified JSON file."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def check_market_cap_duplicates(records: list) -> list:
    """Check for duplicate market caps in the same year (multi-counting)."""
    issues = []

    # Group by year
    by_year = defaultdict(list)
    for r in records:
        if r.get("public") and r["public"].get("market_cap_eoy"):
            by_year[r["year"]].append({
                "domain": r["domain"],
                "market_cap": r["public"]["market_cap_eoy"],
                "tickers": r["public"].get("tickers", [])
            })

    # Check for same market cap values in multiple domains
    for year, entries in by_year.items():
        market_cap_to_domains = defaultdict(list)
        for entry in entries:
            market_cap_to_domains[entry["market_cap"]].append(entry["domain"])

        for market_cap, domains in market_cap_to_domains.items():
            if len(domains) > 1:
                issues.append({
                    "year": year,
                    "market_cap": market_cap,
                    "domains": domains,
                    "issue": "Same market cap in multiple domains"
                })

    return issues


def check_market_cap_totals(records: list, sector: str) -> dict:
    """Check total market cap by year against thresholds."""
    by_year = defaultdict(float)

    for r in records:
        if r.get("public") and r["public"].get("market_cap_eoy"):
            by_year[r["year"]] += r["public"]["market_cap_eoy"]

    max_threshold = MAX_SECTOR_MARKET_CAP[sector]
    issues = []

    for year, total in sorted(by_year.items()):
        if total > max_threshold:
            issues.append({
                "year": year,
                "total": total,
                "threshold": max_threshold,
                "issue": f"Exceeds ${max_threshold/1e9:.0f}B threshold"
            })

    return {
        "by_year": dict(by_year),
        "issues": issues
    }


def compare_with_original(sector: str) -> dict:
    """Compare cleaned data with original."""
    original_path = SOURCE_DIR / f"{sector}-public.json"
    cleaned_path = CLEANED_DIR / "source" / f"{sector}-public.json"

    original_by_year = defaultdict(float)
    cleaned_by_year = defaultdict(float)

    if original_path.exists():
        with open(original_path) as f:
            for r in json.load(f):
                if r.get("total_market_cap_eoy"):
                    original_by_year[r["year"]] += r["total_market_cap_eoy"]

    if cleaned_path.exists():
        with open(cleaned_path) as f:
            for r in json.load(f):
                if r.get("total_market_cap_eoy"):
                    cleaned_by_year[r["year"]] += r["total_market_cap_eoy"]

    comparison = {}
    for year in sorted(set(original_by_year.keys()) | set(cleaned_by_year.keys())):
        orig = original_by_year.get(year, 0)
        clean = cleaned_by_year.get(year, 0)
        reduction = (orig - clean) / orig * 100 if orig > 0 else 0

        comparison[year] = {
            "original": orig,
            "cleaned": clean,
            "reduction_pct": reduction
        }

    return comparison


def generate_validation_report():
    """Generate comprehensive validation report."""
    print("Validating cleaned data...")

    report_lines = [
        "# Data Cleaning Validation Report",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Summary\n",
    ]

    all_passed = True
    sector_results = {}

    for sector in SECTORS:
        print(f"\nValidating {sector}...")
        unified_path = CLEANED_DIR / "unified" / f"{sector}-unified.json"
        records = load_unified_data(unified_path)

        # Check for duplicates
        duplicates = check_market_cap_duplicates(records)

        # Check totals
        totals = check_market_cap_totals(records, sector)

        # Compare with original
        comparison = compare_with_original(sector)

        sector_results[sector] = {
            "duplicates": duplicates,
            "totals": totals,
            "comparison": comparison
        }

        if duplicates or totals["issues"]:
            all_passed = False

        print(f"  Duplicates: {len(duplicates)}")
        print(f"  Threshold violations: {len(totals['issues'])}")

    # Summary table
    report_lines.append("| Sector | Duplicates | Threshold Violations | Status |")
    report_lines.append("|--------|------------|---------------------|--------|")

    for sector in SECTORS:
        results = sector_results[sector]
        dup_count = len(results["duplicates"])
        violation_count = len(results["totals"]["issues"])
        status = "PASS" if dup_count == 0 and violation_count == 0 else "ISSUES"
        report_lines.append(f"| {sector} | {dup_count} | {violation_count} | {status} |")

    # Detailed results per sector
    for sector in SECTORS:
        results = sector_results[sector]
        report_lines.append(f"\n## {sector.upper()}\n")

        # Duplicates
        if results["duplicates"]:
            report_lines.append("### Duplicate Market Caps (Multi-counting detected!)\n")
            for dup in results["duplicates"]:
                report_lines.append(f"- Year {dup['year']}: ${dup['market_cap']:,.0f} in domains: {', '.join(dup['domains'])}")
        else:
            report_lines.append("### Duplicate Market Caps: NONE (Good!)\n")

        # Threshold violations
        if results["totals"]["issues"]:
            report_lines.append("\n### Threshold Violations\n")
            for issue in results["totals"]["issues"]:
                report_lines.append(f"- Year {issue['year']}: ${issue['total']/1e9:.1f}B exceeds ${issue['threshold']/1e9:.0f}B threshold")
        else:
            report_lines.append("\n### Threshold Violations: NONE (Good!)\n")

        # Before/After comparison
        report_lines.append("\n### Before/After Comparison (Total Public Market Cap)\n")
        report_lines.append("| Year | Original (Multi-counted) | Cleaned (Single) | Change |")
        report_lines.append("|------|--------------------------|------------------|--------|")

        comparison = results["comparison"]
        for year in sorted(comparison.keys())[-10:]:  # Last 10 years
            data = comparison[year]
            orig_str = f"${data['original']/1e9:.1f}B" if data['original'] else "N/A"
            clean_str = f"${data['cleaned']/1e9:.1f}B" if data['cleaned'] else "N/A"

            if data['reduction_pct'] > 0:
                change_str = f"-{data['reduction_pct']:.1f}%"
            elif data['reduction_pct'] < 0:
                change_str = f"+{abs(data['reduction_pct']):.1f}%"
            else:
                change_str = "0%"

            report_lines.append(f"| {year} | {orig_str} | {clean_str} | {change_str} |")

        # Market cap by year
        report_lines.append("\n### Market Cap by Year (Cleaned)\n")
        report_lines.append("| Year | Total Market Cap | Companies |")
        report_lines.append("|------|------------------|-----------|")

        unified_path = CLEANED_DIR / "unified" / f"{sector}-unified.json"
        records = load_unified_data(unified_path)

        by_year = defaultdict(lambda: {"cap": 0, "companies": 0})
        for r in records:
            if r.get("public") and r["public"].get("market_cap_eoy"):
                by_year[r["year"]]["cap"] += r["public"]["market_cap_eoy"]
                by_year[r["year"]]["companies"] += r["public"].get("listed_companies_eoy", 0)

        for year in sorted(by_year.keys())[-10:]:
            data = by_year[year]
            report_lines.append(f"| {year} | ${data['cap']/1e9:.1f}B | {data['companies']} |")

    # Final status
    report_lines.append("\n## Validation Status\n")
    if all_passed:
        report_lines.append("**ALL CHECKS PASSED**")
        report_lines.append("\nThe cleaned data has:")
        report_lines.append("- No duplicate market caps across domains")
        report_lines.append("- All totals within reasonable thresholds")
        report_lines.append("- Single attribution (primary_domain_only)")
    else:
        report_lines.append("**ISSUES DETECTED** - See details above")

    # Save report
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = AUDIT_DIR / "validation_report.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"\nValidation report saved to {report_path}")

    return all_passed


def main():
    print("=" * 60)
    print("CLEANED DATA VALIDATION")
    print("=" * 60)

    passed = generate_validation_report()

    print("\n" + "=" * 60)
    if passed:
        print("VALIDATION PASSED - Data is clean!")
    else:
        print("VALIDATION ISSUES DETECTED - Review report")
    print("=" * 60)


if __name__ == "__main__":
    main()
