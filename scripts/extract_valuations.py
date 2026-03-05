#!/usr/bin/env python3
"""
Extract valuation data from S-1/S-4 filings using Claude API.

Downloads registration statements and extracts funding round history
from Dilution, Capitalization, and Description of Capital Stock sections.

Usage:
    python scripts/extract_valuations.py --sector space
    python scripts/extract_valuations.py --all
    python scripts/extract_valuations.py --all --resume

Output:
    data/source/{sector}-valuations.json
"""

import argparse
import json
import os
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

# Configuration
SEC_USER_AGENT = "HistoricFundModel/1.0 (research@example.com)"
CHECKPOINT_INTERVAL = 10
MAX_SECTION_LENGTH = 80000  # ~20K tokens for Claude


class HTMLStripper(HTMLParser):
    """Strip HTML tags and extract text."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = False
        if tag in ('p', 'div', 'br', 'tr', 'li'):
            self.text.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)

    def get_text(self):
        return ''.join(self.text)


def strip_html(html: str) -> str:
    """Strip HTML and return plain text."""
    stripper = HTMLStripper()
    try:
        stripper.feed(html)
        text = stripper.get_text()
    except:
        # Fallback: regex strip
        text = re.sub(r'<[^>]+>', ' ', html)

    # Clean up whitespace
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'&\w+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    return text.strip()


def get_s1_filings(cik: str) -> list:
    """Get S-1, S-4, F-1 filings for a CIK."""
    cik_clean = cik.lstrip('0')

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', SEC_USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        filings = data.get('filings', {}).get('recent', {})
        forms = filings.get('form', [])
        accessions = filings.get('accessionNumber', [])
        dates = filings.get('filingDate', [])
        docs = filings.get('primaryDocument', [])

        results = []
        target_forms = ['S-1', 'S-4', 'F-1', '424B4']

        for i, form in enumerate(forms):
            base_form = form.replace('/A', '')
            if base_form in target_forms:
                acc_clean = accessions[i].replace('-', '')
                results.append({
                    'form': form,
                    'date': dates[i],
                    'accession': accessions[i],
                    'document': docs[i],
                    'url': f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_clean}/{docs[i]}"
                })

        return results

    except Exception as e:
        print(f"  Error getting filings: {e}")
        return []


def download_filing(url: str) -> str:
    """Download a filing document."""
    req = urllib.request.Request(url)
    req.add_header('User-Agent', SEC_USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error downloading: {e}")
        return None


def extract_sections(text: str) -> str:
    """Extract relevant sections for valuation analysis."""
    text_upper = text.upper()

    # Define section markers
    section_starts = [
        'DILUTION',
        'CAPITALIZATION',
        'DESCRIPTION OF CAPITAL STOCK',
        'DESCRIPTION OF SECURITIES',
        'SHARES ELIGIBLE FOR FUTURE SALE',
        'FUNDING HISTORY',
        'EQUITY FINANCING',
    ]

    section_ends = [
        'MANAGEMENT',
        'EXECUTIVE COMPENSATION',
        'PRINCIPAL STOCKHOLDERS',
        'CERTAIN RELATIONSHIPS',
        'MATERIAL U.S. FEDERAL',
        'UNDERWRITING',
        'LEGAL MATTERS',
        'EXPERTS',
        'WHERE YOU CAN FIND',
    ]

    extracted = []

    for start_marker in section_starts:
        start_pos = text_upper.find(start_marker)
        if start_pos < 0:
            continue

        # Find the next section end
        end_pos = len(text)
        for end_marker in section_ends:
            pos = text_upper.find(end_marker, start_pos + len(start_marker))
            if pos > 0 and pos < end_pos:
                end_pos = pos

        # Also check for next major section start
        for other_start in section_starts:
            if other_start != start_marker:
                pos = text_upper.find(other_start, start_pos + len(start_marker))
                if pos > 0 and pos < end_pos:
                    end_pos = pos

        section_text = text[start_pos:end_pos]

        # Skip if too short (probably not the real section)
        if len(section_text) > 500:
            extracted.append(f"=== {start_marker} ===\n{section_text[:40000]}")

    if not extracted:
        # Fallback: get first 50K chars if no sections found
        return text[:50000]

    combined = '\n\n'.join(extracted)
    return combined[:MAX_SECTION_LENGTH]


def extract_with_claude(sections: str, company_name: str, filing_type: str) -> dict:
    """Use Claude API to extract structured funding data."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return {'error': 'No API key found'}

    prompt = f"""Analyze this SEC registration statement extract for {company_name} ({filing_type} filing).

Extract ALL funding rounds and equity issuances mentioned in the document. For each round, extract:
- round_label: The name (e.g., "Series A", "Series B", "Seed", "Convertible Note")
- date: When the round occurred (YYYY-MM-DD format if possible, or YYYY-MM, or just YYYY)
- shares_issued: Number of shares issued in this round (if available)
- price_per_share: Price per share in USD (if available)
- amount_raised: Total amount raised in USD (if available)
- total_shares_after: Total shares outstanding after this round (if available)
- lead_investor: Lead investor name (if mentioned)
- source_section: Which section this data came from
- notes: Any important context

Also look for:
- Total shares authorized
- Common vs preferred stock breakdown
- Any conversion ratios

Return valid JSON only, no markdown formatting:
{{
  "company_name": "{company_name}",
  "filing_type": "{filing_type}",
  "funding_rounds": [
    {{
      "round_label": "...",
      "date": "...",
      "shares_issued": null or number,
      "price_per_share": null or number,
      "amount_raised": null or number,
      "total_shares_after": null or number,
      "lead_investor": null or "...",
      "source_section": "...",
      "notes": "..."
    }}
  ],
  "capitalization_summary": {{
    "total_shares_authorized": null or number,
    "common_shares_outstanding": null or number,
    "preferred_shares_outstanding": null or number,
    "shares_reserved_options": null or number
  }},
  "extraction_notes": "Any additional observations"
}}

Document sections:
{sections}"""

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }

    data = json.dumps({
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 4000,
        'messages': [{'role': 'user', 'content': prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=data,
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))

        content = result['content'][0]['text']

        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            return json.loads(content)
        except json.JSONDecodeError as e:
            return {'error': f'JSON parse error: {e}', 'raw_response': content[:1000]}

    except Exception as e:
        return {'error': str(e)}


def calculate_valuations(funding_rounds: list) -> list:
    """Calculate implied valuations from funding round data."""
    for round_data in funding_rounds:
        price = round_data.get('price_per_share')
        shares_after = round_data.get('total_shares_after')
        amount = round_data.get('amount_raised')

        if price and shares_after:
            post_money = price * shares_after
            round_data['implied_post_money_valuation'] = int(post_money)
            if amount:
                round_data['implied_pre_money_valuation'] = int(post_money - amount)
            round_data['valuation_confidence'] = 'high'
        elif price and amount:
            # Estimate shares issued
            shares_issued = round_data.get('shares_issued')
            if shares_issued:
                round_data['valuation_confidence'] = 'medium'
        else:
            round_data['valuation_confidence'] = 'low'

    return funding_rounds


def save_checkpoint(results: list, output_path: Path):
    """Save current results to file."""
    print(f"\n  Saving checkpoint ({len(results)} companies)...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def process_sector(sector: str, resume: bool = False):
    """Process all companies for a sector."""

    universe_path = Path(__file__).parent.parent / 'data' / 'source' / f'universe-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'source' / f'{sector}-valuations.json'

    print(f"\n{'='*60}")
    print(f"Extracting valuations for {sector} sector")
    print(f"{'='*60}")

    # Load universe
    with open(universe_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    # Filter to companies with S-1/S-4
    target_companies = [c for c in companies if c.get('has_s1_s4') and c.get('cik')]
    print(f"Found {len(target_companies)} companies with S-1/S-4 filings")

    # Load existing data if resuming
    results = []
    processed_ciks = set()
    if resume and output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        processed_ciks = {r['cik'] for r in results}
        print(f"Resuming: {len(results)} companies already processed")

    # Process each company
    new_count = 0
    success_count = 0
    error_count = 0

    for i, company in enumerate(target_companies):
        cik = company['cik']

        if cik in processed_ciks:
            continue

        print(f"[{i+1}/{len(target_companies)}] {company['company_name']}...", flush=True)

        # Get S-1/S-4 filings
        filings = get_s1_filings(cik)

        if not filings:
            print("  No filings found")
            results.append({
                'cik': cik,
                'company_name': company['company_name'],
                'sector': sector,
                'domains': company.get('domains', []),
                'status': 'no_filings',
            })
            new_count += 1
            continue

        # Use the most recent non-amendment filing
        filing = None
        for f in filings:
            if '/A' not in f['form']:
                filing = f
                break
        if not filing:
            filing = filings[0]

        print(f"  Downloading {filing['form']} ({filing['date']})...")

        # Download filing
        html = download_filing(filing['url'])

        if not html:
            print("  Failed to download")
            results.append({
                'cik': cik,
                'company_name': company['company_name'],
                'sector': sector,
                'domains': company.get('domains', []),
                'status': 'download_failed',
            })
            error_count += 1
            new_count += 1
            continue

        # Strip HTML and extract sections
        print(f"  Processing {len(html):,} chars...")
        text = strip_html(html)
        sections = extract_sections(text)

        print(f"  Extracted {len(sections):,} chars of relevant sections")

        # Extract with Claude
        print("  Calling Claude API...")
        extracted = extract_with_claude(sections, company['company_name'], filing['form'])

        if 'error' in extracted:
            print(f"  Error: {extracted['error']}")
            results.append({
                'cik': cik,
                'company_name': company['company_name'],
                'sector': sector,
                'domains': company.get('domains', []),
                'filing_type': filing['form'],
                'filing_date': filing['date'],
                'status': 'extraction_error',
                'error': extracted['error'],
            })
            error_count += 1
        else:
            # Calculate valuations
            if 'funding_rounds' in extracted:
                extracted['funding_rounds'] = calculate_valuations(extracted['funding_rounds'])

            round_count = len(extracted.get('funding_rounds', []))
            print(f"  Extracted {round_count} funding rounds")

            results.append({
                'cik': cik,
                'company_name': company['company_name'],
                'sector': sector,
                'domains': company.get('domains', []),
                'filing_type': filing['form'],
                'filing_date': filing['date'],
                'filing_url': filing['url'],
                'status': 'success',
                **extracted,
            })
            success_count += 1

        new_count += 1

        # Rate limiting
        time.sleep(1)

        # Checkpoint
        if new_count > 0 and new_count % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(results, output_path)

    # Final save
    save_checkpoint(results, output_path)

    # Summary
    print(f"\nSummary for {sector}:")
    print(f"  Companies processed: {new_count}")
    print(f"  Successful extractions: {success_count}")
    print(f"  Errors: {error_count}")

    # Count total funding rounds
    total_rounds = sum(len(r.get('funding_rounds', [])) for r in results if r.get('status') == 'success')
    print(f"  Total funding rounds extracted: {total_rounds}")


def main():
    parser = argparse.ArgumentParser(description='Extract valuations from S-1/S-4 filings')
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

    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please add your API key to .env file")
        return

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    for sector in sectors:
        process_sector(sector, resume=args.resume)


if __name__ == '__main__':
    main()
