#!/usr/bin/env python3
"""
Aggregate public market data using primary_domain only (no multi-counting).

This is the cleaned version of aggregate_public.py that:
1. Uses primary_domain for attribution (each company counted once)
2. Validates data quality before aggregation
3. Includes audit trail in output

Usage:
    python scripts/aggregate_public_clean.py --sector space
    python scripts/aggregate_public_clean.py --all

Output:
    data/cleaned/source/{sector}-public.json
"""

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime
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
    """Process market data for a sector and aggregate using primary_domain only."""

    market_path = Path(__file__).parent.parent / 'data' / 'cleaned' / 'source' / f'market-data-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'cleaned' / 'source' / f'{sector}-public.json'

    print(f"\n{'='*60}")
    print(f"Aggregating CLEAN public market data for {sector} sector")
    print(f"Using PRIMARY_DOMAIN only (no multi-counting)")
    print(f"{'='*60}")

    # Load market data
    with open(market_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    # Filter to companies with successful data AND primary_domain
    companies_with_data = [
        c for c in companies
        if c.get('status') == 'success'
        and c.get('market_data')
        and c.get('primary_domain')
    ]

    companies_no_primary = [
        c for c in companies
        if c.get('status') == 'success'
        and c.get('market_data')
        and not c.get('primary_domain')
    ]

    print(f"Companies with primary_domain: {len(companies_with_data)}")
    if companies_no_primary:
        print(f"WARNING: {len(companies_no_primary)} companies have no primary_domain (excluded)")
        for c in companies_no_primary[:3]:
            print(f"  - {c['company_name']}")

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

    # Aggregate by (primary_domain, year) - SINGLE ATTRIBUTION
    # Structure: {(domain, year): {'market_caps': [], 'returns': [], 'companies': [], 'tickers': []}}
    aggregates = defaultdict(lambda: {
        'market_caps': [],
        'returns': [],
        'companies': [],
        'tickers': [],
        'listed_this_year': 0
    })

    # Also track sector-level aggregates
    sector_aggregates = defaultdict(lambda: {
        'market_caps': [],
        'returns': [],
        'companies': set(),
        'listed_this_year': 0
    })

    for company in companies_with_data:
        cik = company['cik']
        primary_domain = company['primary_domain']  # Use PRIMARY_DOMAIN only
        ticker = company.get('ticker', 'N/A')
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

            # Attribute to PRIMARY DOMAIN ONLY (no multi-counting!)
            key = (primary_domain, year)
            if market_cap:
                aggregates[key]['market_caps'].append(market_cap)
            if ytd_return is not None:
                aggregates[key]['returns'].append(ytd_return)
            aggregates[key]['companies'].append(cik)
            aggregates[key]['tickers'].append(ticker)
            aggregates[key]['listed_this_year'] += listed_this_year

            # Sector-level (deduplicated by CIK)
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
            'total_listed_companies_eoy': len(set(data['companies'])),  # Deduplicated
            'total_market_cap_eoy': sum(market_caps) if market_caps else None,
            'median_market_cap_eoy': int(statistics.median(market_caps)) if market_caps else None,
            'mean_market_cap_eoy': int(statistics.mean(market_caps)) if market_caps else None,
            'sector_return_ytd': round(statistics.mean(returns), 4) if returns else None,
            'tickers': list(set(data['tickers'])),  # Which companies are in this domain
            'attribution_method': 'primary_domain_only',
            'data_quality': {
                'validated': True,
                'multi_counting': False,
                'generated_at': datetime.now().isoformat()
            }
        }
        results.append(record)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved to {output_path}")

    # Summary statistics
    domains = set(r['domain'] for r in results)

    # Get unique totals at sector level for most recent year
    latest_year = max(sector_aggregates.keys())
    sector_data = sector_aggregates[latest_year]
    sector_market_cap = sum(sector_data['market_caps'])
    unique_companies = len(sector_data['companies'])

    print(f"\nSummary for {sector}:")
    print(f"  Domains: {len(domains)}")
    print(f"  Years: {min(years)} - {max(years)}")
    print(f"  Data points (domain-year): {len(results)}")
    print(f"  Companies with market data: {len(companies_with_data)}")
    print(f"  Total market cap ({latest_year}): ${sector_market_cap:,}")

    # Show capital by recent years
    print(f"\n  Market cap by year (no multi-counting):")
    for year in sorted(sector_aggregates.keys())[-5:]:
        data = sector_aggregates[year]
        cap = sum(data['market_caps'])
        companies = len(data['companies'])
        print(f"    {year}: ${cap:,} ({companies} companies)")

    # Sanity check - compare with original
    original_path = Path(__file__).parent.parent / 'data' / 'source' / f'{sector}-public.json'
    if original_path.exists():
        with open(original_path, 'r') as f:
            original = json.load(f)

        # Sum market caps for same year in original
        original_by_year = defaultdict(int)
        for r in original:
            if r.get('total_market_cap_eoy'):
                original_by_year[r['year']] += r['total_market_cap_eoy']

        print(f"\n  Comparison with original (multi-counted) data:")
        for year in sorted(sector_aggregates.keys())[-3:]:
            clean_cap = sum(sector_aggregates[year]['market_caps'])
            original_cap = original_by_year.get(year, 0)
            if original_cap > 0:
                reduction = (original_cap - clean_cap) / original_cap * 100
                print(f"    {year}: ${clean_cap:,} vs ${original_cap:,} ({reduction:.1f}% reduction)")


def main():
    parser = argparse.ArgumentParser(description='Aggregate clean public market data')
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

    print("\n" + "="*60)
    print("AGGREGATION COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
