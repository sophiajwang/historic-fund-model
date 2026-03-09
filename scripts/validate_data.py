#!/usr/bin/env python3
"""
Validate public market data and detect data quality issues.

Audits market data files to identify:
1. Extreme outliers (market cap > $3.5T per company)
2. Suspicious YoY volatility (>500% change)
3. Multi-domain companies (potential multi-counting)
4. Companies with missing domain assignments

Usage:
    python scripts/validate_data.py --sector space
    python scripts/validate_data.py --all
    python scripts/validate_data.py --all --output-dir data/cleaned/audit

Output:
    audit_report.md - Human-readable findings
    flagged_records.json - Machine-readable issues list
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# Validation thresholds
MAX_SINGLE_COMPANY_MARKET_CAP = 3.5e12  # $3.5 trillion
MAX_YOY_CHANGE = 5.0  # 500%
MIN_REASONABLE_PRICE = 0.001  # $0.001 per share
MAX_REASONABLE_PRICE = 1e6  # $1M per share (catches unadjusted splits)


def load_market_data(sector: str) -> list:
    """Load raw market data for a sector."""
    path = Path(__file__).parent.parent / 'data' / 'source' / f'market-data-{sector}.json'
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_price_outliers(company: dict) -> list:
    """Detect unreasonable stock prices (likely unadjusted splits)."""
    issues = []
    market_data = company.get('market_data', [])

    for record in market_data:
        close = record.get('close', 0)
        if close > MAX_REASONABLE_PRICE:
            issues.append({
                'type': 'price_outlier',
                'severity': 'critical',
                'company': company.get('company_name'),
                'ticker': company.get('ticker'),
                'cik': company.get('cik'),
                'date': record.get('date'),
                'close_price': close,
                'market_cap': record.get('market_cap'),
                'reason': f'Close price ${close:,.2f} exceeds ${MAX_REASONABLE_PRICE:,.0f} - likely unadjusted split data'
            })

    return issues


def detect_market_cap_outliers(company: dict) -> list:
    """Detect market caps exceeding reasonable thresholds."""
    issues = []
    market_data = company.get('market_data', [])

    for record in market_data:
        market_cap = record.get('market_cap', 0)
        if market_cap and market_cap > MAX_SINGLE_COMPANY_MARKET_CAP:
            issues.append({
                'type': 'market_cap_outlier',
                'severity': 'critical',
                'company': company.get('company_name'),
                'ticker': company.get('ticker'),
                'cik': company.get('cik'),
                'date': record.get('date'),
                'market_cap': market_cap,
                'threshold': MAX_SINGLE_COMPANY_MARKET_CAP,
                'reason': f'Market cap ${market_cap/1e12:.2f}T exceeds ${MAX_SINGLE_COMPANY_MARKET_CAP/1e12:.1f}T threshold'
            })

    return issues


def detect_yoy_volatility(company: dict) -> list:
    """Detect suspicious year-over-year market cap changes."""
    issues = []
    market_data = company.get('market_data', [])

    if not market_data:
        return issues

    # Group by year and get EOY values
    yearly_caps = {}
    for record in market_data:
        year = int(record['date'][:4])
        market_cap = record.get('market_cap')
        if market_cap:
            yearly_caps[year] = market_cap  # Last value for each year

    # Check YoY changes
    years = sorted(yearly_caps.keys())
    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]

        prev_cap = yearly_caps[prev_year]
        curr_cap = yearly_caps[curr_year]

        if prev_cap > 0:
            change = (curr_cap - prev_cap) / prev_cap
            if abs(change) > MAX_YOY_CHANGE:
                issues.append({
                    'type': 'yoy_volatility',
                    'severity': 'warning',
                    'company': company.get('company_name'),
                    'ticker': company.get('ticker'),
                    'cik': company.get('cik'),
                    'year': curr_year,
                    'prev_year_cap': prev_cap,
                    'curr_year_cap': curr_cap,
                    'change_pct': round(change * 100, 1),
                    'reason': f'{change*100:+.0f}% YoY change ({prev_year}->{curr_year}) exceeds {MAX_YOY_CHANGE*100:.0f}% threshold'
                })

    return issues


def detect_multi_domain_companies(companies: list) -> list:
    """Identify companies with multiple domains (multi-counting risk)."""
    issues = []

    for company in companies:
        domains = company.get('domains', [])
        if len(domains) > 1 and company.get('status') == 'success':
            issues.append({
                'type': 'multi_domain',
                'severity': 'info',
                'company': company.get('company_name'),
                'ticker': company.get('ticker'),
                'cik': company.get('cik'),
                'domains': domains,
                'domain_count': len(domains),
                'reason': f'Company has {len(domains)} domains - market cap counted {len(domains)}x in aggregation'
            })

    return issues


def detect_missing_domains(companies: list) -> list:
    """Identify companies with no domain assignment."""
    issues = []

    for company in companies:
        domains = company.get('domains', [])
        if len(domains) == 0 and company.get('status') == 'success':
            issues.append({
                'type': 'missing_domain',
                'severity': 'warning',
                'company': company.get('company_name'),
                'ticker': company.get('ticker'),
                'cik': company.get('cik'),
                'reason': 'Company has no domain assignment - excluded from domain-level analysis'
            })

    return issues


def validate_sector(sector: str) -> dict:
    """Run all validation checks on a sector's market data."""
    print(f"\nValidating {sector} sector...")

    companies = load_market_data(sector)
    successful = [c for c in companies if c.get('status') == 'success']

    all_issues = []

    # Run each validation check
    for company in successful:
        all_issues.extend(detect_price_outliers(company))
        all_issues.extend(detect_market_cap_outliers(company))
        all_issues.extend(detect_yoy_volatility(company))

    # Sector-level checks
    all_issues.extend(detect_multi_domain_companies(companies))
    all_issues.extend(detect_missing_domains(companies))

    # Summarize
    summary = {
        'sector': sector,
        'total_companies': len(companies),
        'successful_companies': len(successful),
        'issues_by_type': defaultdict(int),
        'issues_by_severity': defaultdict(int),
        'issues': all_issues
    }

    for issue in all_issues:
        summary['issues_by_type'][issue['type']] += 1
        summary['issues_by_severity'][issue['severity']] += 1

    # Convert defaultdicts to regular dicts for JSON serialization
    summary['issues_by_type'] = dict(summary['issues_by_type'])
    summary['issues_by_severity'] = dict(summary['issues_by_severity'])

    print(f"  Found {len(all_issues)} issues:")
    for issue_type, count in summary['issues_by_type'].items():
        print(f"    {issue_type}: {count}")

    return summary


def generate_audit_report(results: list, output_dir: Path) -> None:
    """Generate markdown audit report."""

    report_lines = [
        "# Data Quality Audit Report",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Summary\n",
    ]

    # Overall summary table
    total_issues = sum(len(r['issues']) for r in results)
    critical_issues = sum(r['issues_by_severity'].get('critical', 0) for r in results)
    warning_issues = sum(r['issues_by_severity'].get('warning', 0) for r in results)
    info_issues = sum(r['issues_by_severity'].get('info', 0) for r in results)

    report_lines.append("| Sector | Companies | Critical | Warning | Info | Total |")
    report_lines.append("|--------|-----------|----------|---------|------|-------|")

    for r in results:
        report_lines.append(
            f"| {r['sector']} | {r['successful_companies']} | "
            f"{r['issues_by_severity'].get('critical', 0)} | "
            f"{r['issues_by_severity'].get('warning', 0)} | "
            f"{r['issues_by_severity'].get('info', 0)} | "
            f"{len(r['issues'])} |"
        )

    report_lines.append(f"| **Total** | - | **{critical_issues}** | **{warning_issues}** | **{info_issues}** | **{total_issues}** |")

    # Critical issues detail
    report_lines.append("\n## Critical Issues\n")
    report_lines.append("These require immediate attention - data is incorrect.\n")

    for r in results:
        critical = [i for i in r['issues'] if i['severity'] == 'critical']
        if critical:
            report_lines.append(f"\n### {r['sector'].upper()}\n")
            for issue in critical[:10]:  # Limit to first 10
                report_lines.append(f"- **{issue['company']}** ({issue.get('ticker', 'N/A')}): {issue['reason']}")
            if len(critical) > 10:
                report_lines.append(f"- ... and {len(critical) - 10} more")

    # Multi-domain summary
    report_lines.append("\n## Multi-Domain Companies (Multi-Counting Risk)\n")
    report_lines.append("These companies have market cap counted multiple times in domain aggregations.\n")

    for r in results:
        multi = [i for i in r['issues'] if i['type'] == 'multi_domain']
        if multi:
            report_lines.append(f"\n### {r['sector'].upper()} ({len(multi)} companies)\n")
            report_lines.append("| Company | Ticker | Domains |")
            report_lines.append("|---------|--------|---------|")
            for issue in sorted(multi, key=lambda x: -x['domain_count'])[:15]:
                domains_str = ', '.join(issue['domains'][:3])
                if len(issue['domains']) > 3:
                    domains_str += f" (+{len(issue['domains'])-3} more)"
                report_lines.append(f"| {issue['company']} | {issue.get('ticker', 'N/A')} | {domains_str} |")

    # Missing domains
    report_lines.append("\n## Companies Missing Domain Assignment\n")

    for r in results:
        missing = [i for i in r['issues'] if i['type'] == 'missing_domain']
        if missing:
            report_lines.append(f"\n### {r['sector'].upper()} ({len(missing)} companies)\n")
            for issue in missing:
                report_lines.append(f"- {issue['company']} ({issue.get('ticker', 'N/A')})")

    # Write report
    report_path = output_dir / 'audit_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\nAudit report saved to {report_path}")


def generate_flagged_records(results: list, output_dir: Path) -> None:
    """Generate JSON file of all flagged records."""

    all_issues = []
    for r in results:
        for issue in r['issues']:
            issue['sector'] = r['sector']
            all_issues.append(issue)

    output_path = output_dir / 'flagged_records.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_issues, f, indent=2)

    print(f"Flagged records saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Validate public market data')
    parser.add_argument('--sector', choices=['space', 'bio', 'energy'],
                        help='Sector to validate')
    parser.add_argument('--all', action='store_true',
                        help='Validate all sectors')
    parser.add_argument('--output-dir', type=str, default='data/cleaned/audit',
                        help='Output directory for audit reports')

    args = parser.parse_args()

    if not args.sector and not args.all:
        parser.print_help()
        return

    output_dir = Path(__file__).parent.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    results = []
    for sector in sectors:
        results.append(validate_sector(sector))

    # Generate reports
    generate_audit_report(results, output_dir)
    generate_flagged_records(results, output_dir)

    print("\n" + "="*60)
    print("Validation complete!")


if __name__ == '__main__':
    main()
