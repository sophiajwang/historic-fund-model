#!/usr/bin/env python3
"""
Aggregate offerings into annual primary market time series.

Roll up individual offerings into annual totals by sector, domain, and year.
Multi-domain handling: capital is attributed to each domain (tracked separately
to handle double-counting).

Usage:
    python scripts/aggregate_private.py --sector space
    python scripts/aggregate_private.py --all

Output:
    data/source/{sector}-private.json
"""

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


def get_offering_year(offering: dict) -> str:
    """Extract year from offering date."""
    # Use date_of_first_sale if available, otherwise original_filing_date
    date = offering.get('date_of_first_sale') or offering.get('original_filing_date')
    if date:
        return date[:4]
    return None


def process_sector(sector: str):
    """Process offerings for a sector and aggregate into annual totals."""

    offerings_path = Path(__file__).parent.parent / 'data' / 'source' / f'offerings-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'source' / f'{sector}-private.json'

    print(f"\n{'='*60}")
    print(f"Aggregating annual private market data for {sector} sector")
    print(f"{'='*60}")

    # Load offerings
    with open(offerings_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    print(f"Loaded {len(companies)} companies")

    # Aggregate by (domain, year)
    # Structure: {(domain, year): {'amounts': [], 'companies': set()}}
    aggregates = defaultdict(lambda: {'amounts': [], 'companies': set()})

    # Also track sector-level aggregates
    sector_aggregates = defaultdict(lambda: {'amounts': [], 'companies': set()})

    total_offerings = 0
    skipped_no_year = 0
    skipped_no_domains = 0

    for company in companies:
        cik = company['cik']
        domains = company.get('domains', [])

        if not domains:
            skipped_no_domains += len(company['offerings'])
            continue

        for offering in company['offerings']:
            year = get_offering_year(offering)
            if not year:
                skipped_no_year += 1
                continue

            amount = offering.get('total_amount_sold_final') or 0
            total_offerings += 1

            # Attribute to each domain
            for domain in domains:
                key = (domain, year)
                aggregates[key]['amounts'].append(amount)
                aggregates[key]['companies'].add(cik)

            # Sector-level (deduplicated by company)
            sector_aggregates[year]['amounts'].append(amount)
            sector_aggregates[year]['companies'].add(cik)

    print(f"Processed {total_offerings} offerings")
    if skipped_no_year:
        print(f"Skipped {skipped_no_year} offerings (no date)")
    if skipped_no_domains:
        print(f"Skipped {skipped_no_domains} offerings (no domains)")

    # Convert to output format
    results = []

    for (domain, year), data in sorted(aggregates.items()):
        amounts = data['amounts']
        non_zero_amounts = [a for a in amounts if a > 0]

        record = {
            'sector': sector,
            'domain': domain,
            'year': int(year),
            'total_capital_raised': sum(amounts),
            'number_of_offerings': len(amounts),
            'offerings_with_amount': len(non_zero_amounts),
            'median_offering_size': int(statistics.median(non_zero_amounts)) if non_zero_amounts else 0,
            'mean_offering_size': int(statistics.mean(non_zero_amounts)) if non_zero_amounts else 0,
            'unique_companies_raising': len(data['companies']),
        }
        results.append(record)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved to {output_path}")

    # Summary statistics
    domains = set(r['domain'] for r in results)
    years = sorted(set(r['year'] for r in results))
    total_capital = sum(r['total_capital_raised'] for r in results)

    # Get unique totals at sector level (avoid domain double-counting)
    sector_total = sum(sum(data['amounts']) for data in sector_aggregates.values())
    unique_companies = len(set().union(*(data['companies'] for data in sector_aggregates.values())))

    print(f"\nSummary for {sector}:")
    print(f"  Domains: {len(domains)}")
    print(f"  Years: {min(years)} - {max(years)}")
    print(f"  Data points (domain-year): {len(results)}")
    print(f"  Total capital (sum by domain): ${total_capital:,}")
    print(f"  Total capital (deduplicated): ${sector_total:,}")
    print(f"  Unique companies: {unique_companies}")

    # Show top domains by capital raised
    domain_totals = defaultdict(int)
    for r in results:
        domain_totals[r['domain']] += r['total_capital_raised']

    print(f"\n  Top 5 domains by capital raised:")
    for domain, total in sorted(domain_totals.items(), key=lambda x: -x[1])[:5]:
        print(f"    {domain}: ${total:,}")

    # Show capital by year
    print(f"\n  Capital by year (deduplicated):")
    for year in sorted(sector_aggregates.keys())[-5:]:
        data = sector_aggregates[year]
        print(f"    {year}: ${sum(data['amounts']):,} ({len(data['companies'])} companies)")


def main():
    parser = argparse.ArgumentParser(description='Aggregate private market data')
    parser.add_argument('--sector', choices=['space', 'bio', 'energy'],
                        help='Sector to process')
    parser.add_argument('--all', action='store_true',
                        help='Process all sectors')

    args = parser.parse_args()

    if not args.sector and not args.all:
        parser.print_help()
        return

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    for sector in sectors:
        process_sector(sector)


if __name__ == '__main__':
    main()
