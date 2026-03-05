#!/usr/bin/env python3
"""
Pull Form D filing index for all companies with EDGAR CIKs.

For each company with a CIK, retrieves all Form D and D/A filings from 2008 onward.

Usage:
    python scripts/pull_form_d_index.py --sector space
    python scripts/pull_form_d_index.py --all
    python scripts/pull_form_d_index.py --all --resume

Output:
    data/source/form-d-index-{sector}.json
"""

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

# Configuration
SEC_USER_AGENT = "HistoricFundModel research@example.com"
SEC_RATE_LIMIT = 0.12  # ~8 requests/second
CHECKPOINT_INTERVAL = 50
START_DATE = "2008-01-01"
END_DATE = "2026-12-31"


def get_form_d_filings(cik: str, retries: int = 3) -> list:
    """Get all Form D and D/A filings for a CIK."""

    # Remove leading zeros for URL but keep for reference
    cik_clean = cik.lstrip('0')

    url = (
        f"https://efts.sec.gov/LATEST/search-index?"
        f"forms=D&dateRange=custom&startdt={START_DATE}&enddt={END_DATE}&ciks={cik}"
    )

    filings = []

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', SEC_USER_AGENT)

            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))

                hits = data.get('hits', {}).get('hits', [])

                for hit in hits:
                    source = hit.get('_source', {})

                    # Extract filing details
                    adsh = source.get('adsh', '')  # Accession number
                    form_type = source.get('form', '')
                    file_date = source.get('file_date', '')

                    # Build file URL
                    # Format: https://www.sec.gov/Archives/edgar/data/{cik}/{adsh_no_dashes}/
                    adsh_clean = adsh.replace('-', '')
                    file_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{adsh_clean}/"

                    filings.append({
                        'accession_number': adsh,
                        'form_type': form_type,
                        'filing_date': file_date,
                        'file_url': file_url,
                    })

                break  # Success

        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                time.sleep(2 ** attempt)
                continue
            elif attempt == retries - 1:
                print(f"  HTTP error for CIK {cik}: {e}")
        except Exception as e:
            if attempt == retries - 1:
                print(f"  Error for CIK {cik}: {e}")
            time.sleep(1)

    time.sleep(SEC_RATE_LIMIT)

    # Sort by filing date
    filings.sort(key=lambda x: x['filing_date'])

    return filings


def save_checkpoint(index: list, output_path: Path):
    """Save current index to file."""
    print(f"\n  💾 Saving checkpoint ({len(index)} companies)...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)


def process_sector(sector: str, resume: bool = False):
    """Process all companies for a sector."""

    universe_path = Path(__file__).parent.parent / 'data' / 'source' / f'universe-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'source' / f'form-d-index-{sector}.json'

    print(f"\n{'='*60}")
    print(f"Pulling Form D index for {sector} sector")
    print(f"{'='*60}")

    # Load universe
    with open(universe_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    # Filter to companies with CIKs
    companies_with_cik = [c for c in companies if c.get('cik')]
    print(f"Found {len(companies_with_cik)} companies with CIKs (out of {len(companies)} total)")

    # Load existing index if resuming
    index = []
    processed_ciks = set()
    if resume and output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        processed_ciks = {entry['cik'] for entry in index}
        print(f"Resuming: {len(index)} companies already processed")

    # Process each company
    total = len(companies_with_cik)
    new_count = 0
    total_filings = sum(len(entry.get('filings', [])) for entry in index)

    for i, company in enumerate(companies_with_cik):
        cik = company['cik']

        # Skip if already processed
        if cik in processed_ciks:
            continue

        print(f"[{i+1}/{total}] {company['company_name']}...", end=' ')

        filings = get_form_d_filings(cik)

        entry = {
            'cik': cik,
            'company_name': company['company_name'],
            'sector': sector,
            'filings': filings,
            'filing_count': len(filings),
        }

        index.append(entry)
        processed_ciks.add(cik)
        new_count += 1
        total_filings += len(filings)

        print(f"→ {len(filings)} filings")

        # Checkpoint
        if new_count > 0 and new_count % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(index, output_path)

    # Final save
    save_checkpoint(index, output_path)

    # Summary
    companies_with_filings = len([e for e in index if e['filing_count'] > 0])

    print(f"\nSummary for {sector}:")
    print(f"  Companies with CIKs: {len(index)}")
    print(f"  Companies with Form D filings: {companies_with_filings}")
    print(f"  Total Form D filings: {total_filings}")
    print(f"  Avg filings per company: {total_filings/len(index):.1f}" if index else "  No companies")


def main():
    parser = argparse.ArgumentParser(description='Pull Form D filing index')
    parser.add_argument('--sector', choices=['space', 'bio', 'energy'],
                        help='Sector to process')
    parser.add_argument('--all', action='store_true',
                        help='Process all sectors')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint')

    args = parser.parse_args()

    if not args.sector and not args.all:
        parser.print_help()
        return

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    for sector in sectors:
        process_sector(sector, resume=args.resume)


if __name__ == '__main__':
    main()
