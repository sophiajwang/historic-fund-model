#!/usr/bin/env python3
"""
Parse Form D XML filings and extract offering data.

Downloads each Form D filing and parses the structured XML.
All post-2008 filings are machine-readable XML with well-defined fields.

Usage:
    python scripts/parse_form_d.py --sector space
    python scripts/parse_form_d.py --all
    python scripts/parse_form_d.py --all --resume

Output:
    data/source/form-d-parsed-{sector}.json
"""

import argparse
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

# Configuration
SEC_USER_AGENT = "HistoricFundModel/1.0 (research@example.com)"
SEC_RATE_LIMIT = 0.12  # ~8 requests/second
CHECKPOINT_INTERVAL = 100


def get_text(element, path: str, default: str = None) -> str:
    """Get text from XML element at path."""
    el = element.find(path)
    return el.text.strip() if el is not None and el.text else default


def get_bool(element, path: str, default: bool = False) -> bool:
    """Get boolean from XML element at path."""
    text = get_text(element, path, '')
    if text.lower() in ('true', 'yes', '1'):
        return True
    elif text.lower() in ('false', 'no', '0'):
        return False
    return default


def get_int(element, path: str, default: int = None) -> int:
    """Get integer from XML element at path."""
    text = get_text(element, path, '')
    try:
        return int(text)
    except (ValueError, TypeError):
        return default


def fetch_form_d_xml(file_url: str, retries: int = 3) -> str:
    """Fetch Form D XML content from SEC."""

    # Construct XML URL
    # The file_url is like: https://www.sec.gov/Archives/edgar/data/1181412/000118141222000003/
    # We need to add primary_doc.xml
    xml_url = file_url.rstrip('/') + '/primary_doc.xml'

    for attempt in range(retries):
        try:
            req = urllib.request.Request(xml_url)
            req.add_header('User-Agent', SEC_USER_AGENT)

            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode('utf-8')

        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Try alternate filename
                xml_url_alt = file_url.rstrip('/') + '/formd.xml'
                try:
                    req = urllib.request.Request(xml_url_alt)
                    req.add_header('User-Agent', SEC_USER_AGENT)
                    with urllib.request.urlopen(req, timeout=15) as response:
                        return response.read().decode('utf-8')
                except:
                    pass
                return None
            elif e.code == 429:  # Rate limited
                time.sleep(2 ** attempt)
                continue
            elif attempt == retries - 1:
                print(f"  HTTP error: {e}")
                return None
        except Exception as e:
            if attempt == retries - 1:
                print(f"  Error: {e}")
                return None
            time.sleep(1)

    return None


def parse_form_d_xml(xml_content: str, filing_info: dict) -> dict:
    """Parse Form D XML and extract offering data."""

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return {'error': f'XML parse error: {e}'}

    # Get submission type
    submission_type = get_text(root, 'submissionType', 'D')
    is_amendment = submission_type == 'D/A' or get_bool(root, './/isAmendment', False)

    # Get issuer info
    issuer = root.find('primaryIssuer')
    if issuer is not None:
        entity_name = get_text(issuer, 'entityName')
        cik = get_text(issuer, 'cik')
        jurisdiction = get_text(issuer, 'jurisdictionOfInc')
        entity_type = get_text(issuer, 'entityType')
    else:
        entity_name = None
        cik = None
        jurisdiction = None
        entity_type = None

    # Get offering data
    offering = root.find('offeringData')
    if offering is None:
        return {'error': 'No offering data found'}

    # Industry
    industry_group = get_text(offering, './/industryGroupType')

    # Federal exemptions
    exemptions = []
    for item in offering.findall('.//federalExemptionsExclusions/item'):
        if item.text:
            exemptions.append(item.text.strip())

    # Type of securities
    is_equity = get_bool(offering, './/isEquityType', False)
    is_debt = get_bool(offering, './/isDebtType', False)
    is_pooled = get_bool(offering, './/isPooledInvestmentFundType', False)
    is_option = get_bool(offering, './/isOptionToAcquireType', False)
    is_other = get_bool(offering, './/isOtherType', False)

    # Offering amounts
    total_offering_amount = get_int(offering, './/totalOfferingAmount')
    total_amount_sold = get_int(offering, './/totalAmountSold')
    total_remaining = get_int(offering, './/totalRemaining')

    # Check for indefinite offering
    indefinite = get_bool(offering, './/indefiniteSecuritiesAmount', False)

    # Investors
    total_investors = get_int(offering, './/totalNumberAlreadyInvested', 0)
    has_non_accredited = get_bool(offering, './/hasNonAccreditedInvestors', False)
    num_non_accredited = get_int(offering, './/numberNonAccreditedInvestors', 0)

    # Calculate accredited investors
    num_accredited = total_investors - num_non_accredited if total_investors else None

    # Date of first sale
    date_of_first_sale = get_text(offering, './/dateOfFirstSale/value')
    yet_to_occur = get_bool(offering, './/dateOfFirstSale/yetToOccur', False)
    if yet_to_occur:
        date_of_first_sale = None

    # Duration
    more_than_one_year = get_bool(offering, './/moreThanOneYear', False)

    # Minimum investment
    min_investment = get_int(offering, './/minimumInvestmentAccepted', 0)

    return {
        'accession_number': filing_info.get('accession_number'),
        'filing_date': filing_info.get('filing_date'),
        'form_type': filing_info.get('form_type'),
        'is_amendment': is_amendment,
        'entity_name': entity_name,
        'cik': cik,
        'jurisdiction': jurisdiction,
        'entity_type': entity_type,
        'offering': {
            'industry_group': industry_group,
            'federal_exemptions': exemptions,
            'is_equity': is_equity,
            'is_debt': is_debt,
            'is_pooled': is_pooled,
            'is_option': is_option,
            'is_other': is_other,
            'total_offering_amount': total_offering_amount,
            'total_amount_sold': total_amount_sold,
            'total_remaining': total_remaining,
            'indefinite_offering': indefinite,
            'number_of_investors': total_investors,
            'number_accredited': num_accredited,
            'number_non_accredited': num_non_accredited,
            'date_of_first_sale': date_of_first_sale,
            'more_than_one_year': more_than_one_year,
            'minimum_investment': min_investment,
        }
    }


def save_checkpoint(parsed: list, output_path: Path):
    """Save current results to file."""
    print(f"\n  💾 Saving checkpoint ({len(parsed)} filings)...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed, f, indent=2)


def process_sector(sector: str, resume: bool = False):
    """Process all Form D filings for a sector."""

    index_path = Path(__file__).parent.parent / 'data' / 'source' / f'form-d-index-{sector}.json'
    universe_path = Path(__file__).parent.parent / 'data' / 'source' / f'universe-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'source' / f'form-d-parsed-{sector}.json'

    print(f"\n{'='*60}")
    print(f"Parsing Form D filings for {sector} sector")
    print(f"{'='*60}")

    # Load index
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    # Load universe for domain info
    with open(universe_path, 'r', encoding='utf-8') as f:
        universe = json.load(f)

    # Create CIK to company info lookup
    cik_to_company = {c['cik']: c for c in universe if c.get('cik')}

    # Count total filings
    total_filings = sum(len(entry['filings']) for entry in index)
    print(f"Found {total_filings} filings across {len(index)} companies")

    # Load existing parsed data if resuming
    parsed = []
    processed_accessions = set()
    if resume and output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            parsed = json.load(f)
        processed_accessions = {p['accession_number'] for p in parsed if 'accession_number' in p}
        print(f"Resuming: {len(parsed)} filings already parsed")

    # Process each company's filings
    filing_num = 0
    new_count = 0
    errors = 0
    total_amount_raised = 0

    for entry in index:
        company_info = cik_to_company.get(entry['cik'], {})

        for filing in entry['filings']:
            filing_num += 1
            accession = filing['accession_number']

            # Skip if already processed
            if accession in processed_accessions:
                continue

            print(f"[{filing_num}/{total_filings}] {entry['company_name'][:30]} - {filing['filing_date']}...", end=' ')

            # Fetch XML
            xml_content = fetch_form_d_xml(filing['file_url'])

            if not xml_content:
                print("→ Failed to fetch")
                errors += 1
                continue

            # Parse XML
            parsed_filing = parse_form_d_xml(xml_content, filing)

            if 'error' in parsed_filing:
                print(f"→ {parsed_filing['error']}")
                errors += 1
                continue

            # Add company info from universe
            parsed_filing['company_name'] = entry['company_name']
            parsed_filing['sector'] = sector
            parsed_filing['domains'] = company_info.get('domains', [])

            parsed.append(parsed_filing)
            processed_accessions.add(accession)
            new_count += 1

            amount = parsed_filing['offering'].get('total_amount_sold') or 0
            total_amount_raised += amount

            print(f"→ ${amount:,}" if amount else "→ (no amount)")

            # Rate limiting
            time.sleep(SEC_RATE_LIMIT)

            # Checkpoint
            if new_count > 0 and new_count % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(parsed, output_path)

    # Final save
    save_checkpoint(parsed, output_path)

    # Summary
    filings_with_amount = len([p for p in parsed if p['offering'].get('total_amount_sold')])

    print(f"\nSummary for {sector}:")
    print(f"  Total filings parsed: {len(parsed)}")
    print(f"  Filings with amount: {filings_with_amount}")
    print(f"  Total amount raised: ${total_amount_raised:,}")
    print(f"  Errors: {errors}")


def main():
    parser = argparse.ArgumentParser(description='Parse Form D XML filings')
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
