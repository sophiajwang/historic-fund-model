#!/usr/bin/env python3
"""
Deduplicate and chain Form D amendments.

Form D/A amendments update a prior Form D filing for the same offering.
This script chains amendments to their original filing so each offering
resolves to its final state.

Key insight: filings with the same date_of_first_sale belong to the same offering.

Usage:
    python scripts/chain_amendments.py --sector space
    python scripts/chain_amendments.py --all

Output:
    data/source/offerings-{sector}.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def determine_offering_type(offering: dict) -> str:
    """Determine the type of offering based on securities flags."""
    types = []
    if offering.get('is_equity'):
        types.append('equity')
    if offering.get('is_debt'):
        types.append('debt')
    if offering.get('is_pooled'):
        types.append('pooled')
    if offering.get('is_option'):
        types.append('option')
    if offering.get('is_other'):
        types.append('other')
    return '+'.join(types) if types else 'unknown'


def chain_filings_for_company(filings: list) -> list:
    """
    Chain filings into distinct offerings for a single company.

    Filings with the same date_of_first_sale belong to the same offering.
    The final state (latest filing) provides the authoritative amounts.
    """
    if not filings:
        return []

    # Group by date_of_first_sale
    by_first_sale = defaultdict(list)
    no_first_sale = []

    for f in filings:
        first_sale = f['offering'].get('date_of_first_sale')
        if first_sale:
            by_first_sale[first_sale].append(f)
        else:
            # Filings without a first sale date - treat each as separate offering
            no_first_sale.append(f)

    offerings = []
    offering_counter = 1

    # Process filings grouped by date_of_first_sale
    for first_sale_date, grouped_filings in sorted(by_first_sale.items()):
        # Sort by filing date
        grouped_filings.sort(key=lambda x: x['filing_date'])

        # First filing is the original
        original = grouped_filings[0]
        # Last filing has the final state
        latest = grouped_filings[-1]

        offering = {
            'offering_id': f'offering_{offering_counter:03d}',
            'original_filing_date': original['filing_date'],
            'latest_amendment_date': latest['filing_date'] if len(grouped_filings) > 1 else None,
            'date_of_first_sale': first_sale_date,
            'type': determine_offering_type(latest['offering']),
            'federal_exemptions': latest['offering'].get('federal_exemptions', []),
            'total_offering_amount': latest['offering'].get('total_offering_amount'),
            'total_amount_sold_final': latest['offering'].get('total_amount_sold'),
            'total_remaining': latest['offering'].get('total_remaining'),
            'investor_count_final': latest['offering'].get('number_of_investors', 0),
            'accredited_investors': latest['offering'].get('number_accredited'),
            'non_accredited_investors': latest['offering'].get('number_non_accredited', 0),
            'minimum_investment': latest['offering'].get('minimum_investment'),
            'indefinite_offering': latest['offering'].get('indefinite_offering', False),
            'more_than_one_year': latest['offering'].get('more_than_one_year', False),
            'filing_chain': [f['accession_number'] for f in grouped_filings],
            'amendment_count': len(grouped_filings) - 1,
        }
        offerings.append(offering)
        offering_counter += 1

    # Handle filings without first sale date (each is a separate offering)
    for f in no_first_sale:
        offering = {
            'offering_id': f'offering_{offering_counter:03d}',
            'original_filing_date': f['filing_date'],
            'latest_amendment_date': None,
            'date_of_first_sale': None,
            'type': determine_offering_type(f['offering']),
            'federal_exemptions': f['offering'].get('federal_exemptions', []),
            'total_offering_amount': f['offering'].get('total_offering_amount'),
            'total_amount_sold_final': f['offering'].get('total_amount_sold'),
            'total_remaining': f['offering'].get('total_remaining'),
            'investor_count_final': f['offering'].get('number_of_investors', 0),
            'accredited_investors': f['offering'].get('number_accredited'),
            'non_accredited_investors': f['offering'].get('number_non_accredited', 0),
            'minimum_investment': f['offering'].get('minimum_investment'),
            'indefinite_offering': f['offering'].get('indefinite_offering', False),
            'more_than_one_year': f['offering'].get('more_than_one_year', False),
            'filing_chain': [f['accession_number']],
            'amendment_count': 0,
        }
        offerings.append(offering)
        offering_counter += 1

    # Sort offerings by first sale date or original filing date
    offerings.sort(key=lambda x: x['date_of_first_sale'] or x['original_filing_date'])

    return offerings


def process_sector(sector: str):
    """Process all Form D filings for a sector and chain amendments."""

    parsed_path = Path(__file__).parent.parent / 'data' / 'source' / f'form-d-parsed-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'source' / f'offerings-{sector}.json'

    print(f"\n{'='*60}")
    print(f"Chaining Form D amendments for {sector} sector")
    print(f"{'='*60}")

    # Load parsed filings
    with open(parsed_path, 'r', encoding='utf-8') as f:
        filings = json.load(f)

    print(f"Loaded {len(filings)} parsed filings")

    # Group by CIK
    by_cik = defaultdict(list)
    for f in filings:
        by_cik[f['cik']].append(f)

    print(f"Found {len(by_cik)} companies")

    # Process each company
    results = []
    total_offerings = 0
    total_amendments = 0
    total_amount_raised = 0

    for cik, company_filings in sorted(by_cik.items()):
        # Get company info from first filing
        first_filing = company_filings[0]

        # Chain filings into offerings
        offerings = chain_filings_for_company(company_filings)

        if not offerings:
            continue

        company_result = {
            'cik': cik,
            'company_name': first_filing['company_name'],
            'entity_name': first_filing.get('entity_name'),
            'sector': sector,
            'domains': first_filing.get('domains', []),
            'jurisdiction': first_filing.get('jurisdiction'),
            'entity_type': first_filing.get('entity_type'),
            'offerings': offerings,
            'total_offerings': len(offerings),
            'total_filings': len(company_filings),
        }

        results.append(company_result)
        total_offerings += len(offerings)
        total_amendments += sum(o['amendment_count'] for o in offerings)
        total_amount_raised += sum(o['total_amount_sold_final'] or 0 for o in offerings)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved to {output_path}")

    # Summary statistics
    filings_with_amendments = sum(1 for r in results if any(o['amendment_count'] > 0 for o in r['offerings']))
    offerings_with_amendments = sum(1 for r in results for o in r['offerings'] if o['amendment_count'] > 0)

    print(f"\nSummary for {sector}:")
    print(f"  Companies: {len(results)}")
    print(f"  Total filings: {len(filings)}")
    print(f"  Distinct offerings: {total_offerings}")
    print(f"  Offerings with amendments: {offerings_with_amendments}")
    print(f"  Total amendments: {total_amendments}")
    print(f"  Total capital raised: ${total_amount_raised:,}")
    print(f"  Deduplication rate: {100 * (1 - total_offerings / len(filings)):.1f}%")


def main():
    parser = argparse.ArgumentParser(description='Chain Form D amendments')
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
