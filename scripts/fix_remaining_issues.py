#!/usr/bin/env python3
"""
Fix remaining data quality issues:
1. Remove duplicate tickers (keep first occurrence)
2. Apply stricter market cap filtering (per-company max)
3. Regenerate aggregated data

Usage:
    python scripts/fix_remaining_issues.py
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CLEANED_SOURCE_DIR = PROJECT_ROOT / "data" / "cleaned" / "source"

# Stricter thresholds
MAX_COMPANY_MARKET_CAP = 500e9  # $500B per company (higher than any space/energy company)
MAX_DAILY_PRICE = 10000  # $10k per share (allows BRK-A style but catches extreme errors)

SECTORS = ["space", "bio", "energy"]


def fix_sector(sector: str):
    """Fix remaining issues for a sector."""
    market_path = CLEANED_SOURCE_DIR / f"market-data-{sector}.json"

    print(f"\n{'='*60}")
    print(f"Fixing {sector.upper()} sector")
    print(f"{'='*60}")

    with open(market_path, 'r') as f:
        companies = json.load(f)

    # Step 1: Deduplicate by ticker
    seen_tickers = set()
    deduped_companies = []
    duplicates_removed = 0

    for company in companies:
        ticker = company.get('ticker')
        if ticker and ticker in seen_tickers:
            print(f"  Removing duplicate ticker {ticker}: {company['company_name']}")
            duplicates_removed += 1
            continue
        if ticker:
            seen_tickers.add(ticker)
        deduped_companies.append(company)

    print(f"  Removed {duplicates_removed} duplicate tickers")

    # Step 2: Apply stricter market cap filtering
    records_filtered = 0
    companies_affected = 0

    for company in deduped_companies:
        if company.get('status') != 'success' or not company.get('market_data'):
            continue

        original_count = len(company['market_data'])
        filtered_data = []

        for record in company['market_data']:
            close_price = record.get('close', 0)
            market_cap = record.get('market_cap', 0)

            # Apply stricter thresholds
            if close_price > MAX_DAILY_PRICE:
                records_filtered += 1
                continue

            if market_cap and market_cap > MAX_COMPANY_MARKET_CAP:
                records_filtered += 1
                continue

            filtered_data.append(record)

        if len(filtered_data) < original_count:
            companies_affected += 1
            company['market_data'] = filtered_data
            company['data_points'] = len(filtered_data)

            additional_excluded = original_count - len(filtered_data)
            company['excluded_data_points'] = company.get('excluded_data_points', 0) + additional_excluded

            if not filtered_data:
                print(f"  WARNING: {company['company_name']} has no valid data after filtering")

    print(f"  Filtered {records_filtered} additional records from {companies_affected} companies")

    # Save fixed data
    with open(market_path, 'w') as f:
        json.dump(deduped_companies, f, indent=2)

    print(f"  Saved fixed data to {market_path}")

    return {
        "duplicates_removed": duplicates_removed,
        "records_filtered": records_filtered,
        "companies_affected": companies_affected
    }


def main():
    print("Fixing Remaining Data Quality Issues")
    print("=" * 60)
    print(f"Max company market cap: ${MAX_COMPANY_MARKET_CAP/1e9:.0f}B")
    print(f"Max daily price: ${MAX_DAILY_PRICE:,.0f}")

    for sector in SECTORS:
        fix_sector(sector)

    print("\n" + "=" * 60)
    print("DONE - Now re-run aggregate_public_clean.py and stitch_data_clean.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
