#!/usr/bin/env python3
"""
Aggregate public market data into annual secondary market time series.

Roll up daily market data into annual totals by sector, domain, and year.
Uses end-of-year market cap as the point-in-time value.

Usage:
    python scripts/aggregate_public.py --sector space
    python scripts/aggregate_public.py --all

Output:
    data/source/{sector}-public.json
"""

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


def get_year_end_data(market_data: list, year: int) -> dict:
    """Get the last trading day data for a given year."""
    year_data = [d for d in market_data if d['date'].startswith(str(year))]
    if year_data:
        return year_data[-1]  # Last trading day
    return None


def calculate_ytd_return(market_data: list, year: int) -> float:
    """Calculate year-to-date return for a given year."""
    year_data = [d for d in market_data if d['date'].startswith(str(year))]
    if len(year_data) >= 2:
        start_price = year_data[0]['close']
        end_price = year_data[-1]['close']
        if start_price and start_price > 0:
            return round((end_price - start_price) / start_price, 4)
    return None


def process_sector(sector: str):
    """Process market data for a sector and aggregate into annual totals."""

    market_path = Path(__file__).parent.parent / 'data' / 'source' / f'market-data-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'source' / f'{sector}-public.json'

    print(f"\n{'='*60}")
    print(f"Aggregating annual public market data for {sector} sector")
    print(f"{'='*60}")

    # Load market data
    with open(market_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    # Filter to companies with successful data
    companies_with_data = [c for c in companies if c.get('status') == 'success' and c.get('market_data')]
    print(f"Loaded {len(companies_with_data)} companies with market data")

    # Determine year range
    all_years = set()
    for company in companies_with_data:
        for d in company['market_data']:
            all_years.add(int(d['date'][:4]))

    if not all_years:
        print("No market data found")
        return

    years = sorted(all_years)
    print(f"Year range: {min(years)} - {max(years)}")

    # Aggregate by (domain, year)
    # Structure: {(domain, year): {'market_caps': [], 'returns': [], 'companies': set()}}
    aggregates = defaultdict(lambda: {'market_caps': [], 'returns': [], 'companies': set(), 'listed_this_year': 0})

    # Also track sector-level aggregates
    sector_aggregates = defaultdict(lambda: {'market_caps': [], 'returns': [], 'companies': set(), 'listed_this_year': 0})

    for company in companies_with_data:
        cik = company['cik']
        domains = company.get('domains', [])
        market_data = company['market_data']

        if not market_data:
            continue

        # Get the year the company was listed
        listing_year = int(market_data[0]['date'][:4])

        for year in years:
            # Get end-of-year data
            eoy_data = get_year_end_data(market_data, year)
            if not eoy_data:
                continue

            # Calculate YTD return
            ytd_return = calculate_ytd_return(market_data, year)

            # Get market cap (from end of year data or calculate)
            market_cap = eoy_data.get('market_cap')
            if not market_cap and company.get('shares_outstanding'):
                market_cap = int(eoy_data['close'] * company['shares_outstanding'])

            # Track if listed this year
            listed_this_year = 1 if year == listing_year else 0

            # Attribute to each domain
            if domains:
                for domain in domains:
                    key = (domain, year)
                    if market_cap:
                        aggregates[key]['market_caps'].append(market_cap)
                    if ytd_return is not None:
                        aggregates[key]['returns'].append(ytd_return)
                    aggregates[key]['companies'].add(cik)
                    aggregates[key]['listed_this_year'] += listed_this_year

            # Sector-level (deduplicated)
            if market_cap:
                sector_aggregates[year]['market_caps'].append(market_cap)
            if ytd_return is not None:
                sector_aggregates[year]['returns'].append(ytd_return)
            sector_aggregates[year]['companies'].add(cik)
            sector_aggregates[year]['listed_this_year'] += listed_this_year

    # Convert to output format
    results = []

    for (domain, year), data in sorted(aggregates.items()):
        market_caps = data['market_caps']
        returns = data['returns']

        record = {
            'sector': sector,
            'domain': domain,
            'year': year,
            'companies_listed_this_year': data['listed_this_year'],
            'total_listed_companies_eoy': len(data['companies']),
            'total_market_cap_eoy': sum(market_caps) if market_caps else None,
            'median_market_cap_eoy': int(statistics.median(market_caps)) if market_caps else None,
            'mean_market_cap_eoy': int(statistics.mean(market_caps)) if market_caps else None,
            'sector_return_ytd': round(statistics.mean(returns), 4) if returns else None,
        }
        results.append(record)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved to {output_path}")

    # Summary statistics
    domains = set(r['domain'] for r in results)
    total_market_cap = sum(r['total_market_cap_eoy'] or 0 for r in results if r['year'] == max(years))

    # Get unique totals at sector level
    latest_year = max(sector_aggregates.keys())
    sector_data = sector_aggregates[latest_year]
    sector_market_cap = sum(sector_data['market_caps'])
    unique_companies = len(sector_data['companies'])

    print(f"\nSummary for {sector}:")
    print(f"  Domains: {len(domains)}")
    print(f"  Years: {min(years)} - {max(years)}")
    print(f"  Data points (domain-year): {len(results)}")
    print(f"  Companies with market data: {len(companies_with_data)}")
    print(f"  Total market cap ({latest_year}, deduplicated): ${sector_market_cap:,}")

    # Show capital by recent years
    print(f"\n  Market cap by year (deduplicated):")
    for year in sorted(sector_aggregates.keys())[-5:]:
        data = sector_aggregates[year]
        cap = sum(data['market_caps'])
        companies = len(data['companies'])
        print(f"    {year}: ${cap:,} ({companies} companies)")


def main():
    parser = argparse.ArgumentParser(description='Aggregate public market data')
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
