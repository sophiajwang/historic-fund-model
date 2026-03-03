#!/usr/bin/env python3
"""
Parse Crunchbase raw markdown files and classify companies into domains via Claude API.

Usage:
    python scripts/classify_companies.py --sector space
    python scripts/classify_companies.py --sector bio
    python scripts/classify_companies.py --sector energy
    python scripts/classify_companies.py --all

Output:
    data/source/universe-{sector}.json
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    exit(1)


def parse_crunchbase_markdown(filepath: str) -> list[dict]:
    """Parse the Crunchbase raw markdown format into company records."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')
    companies = []
    i = 0

    # Skip header lines (first ~10 lines with metadata)
    while i < len(lines) and not lines[i].endswith(' Logo'):
        i += 1

    # Parse companies in groups of ~8 lines each
    while i < len(lines):
        # Skip empty lines
        if not lines[i].strip():
            i += 1
            continue

        # Look for "Company Logo" pattern
        if lines[i].endswith(' Logo'):
            try:
                company = {}

                # Line 0: "Company Logo" - extract name
                logo_line = lines[i]
                company['name'] = logo_line.replace(' Logo', '').strip()
                i += 1

                # Line 1: Company name (duplicate, skip if same)
                if i < len(lines) and lines[i].strip() == company['name']:
                    i += 1

                # Line 2: Location
                if i < len(lines):
                    company['location'] = lines[i].strip()
                    i += 1

                # Line 3: Founded date
                if i < len(lines):
                    company['founded'] = lines[i].strip()
                    i += 1

                # Line 4: Industries
                if i < len(lines):
                    company['industries'] = lines[i].strip()
                    i += 1

                # Line 5: Description
                if i < len(lines):
                    company['description'] = lines[i].strip()
                    i += 1

                # Line 6: CB Rank (Organization)
                if i < len(lines) and lines[i].strip().isdigit():
                    company['cb_rank_org'] = int(lines[i].strip())
                    i += 1

                # Line 7: CB Rank (Company)
                if i < len(lines) and lines[i].strip().isdigit():
                    company['cb_rank_company'] = int(lines[i].strip())
                    i += 1

                # Validate we have minimum required fields
                if company.get('name') and company.get('description'):
                    companies.append(company)

            except Exception as e:
                print(f"Warning: Error parsing company at line {i}: {e}")
                i += 1
        else:
            i += 1

    return companies


def load_domains(sector: str) -> list[dict]:
    """Load domain definitions from CSV."""
    csv_path = Path(__file__).parent.parent / 'data' / f'domains-{sector}.csv'

    domains = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Skip header
        for line in lines[1:]:
            parts = line.strip().split(',', 2)
            if len(parts) >= 3:
                domains.append({
                    'category_name': parts[0],
                    'label': parts[1],
                    'description': parts[2].strip('"')
                })

    return domains


def classify_company(client: anthropic.Anthropic, company: dict, sector: str, domains: list[dict]) -> dict:
    """Classify a single company into domains via Claude API."""

    # Build domain list for prompt
    domain_list = "\n".join([
        f"- {d['category_name']}: {d['description']}"
        for d in domains
        if d['category_name'] not in ['all_space', 'all_bio', 'all_energy']
    ])

    prompt = f"""You are classifying a company into domains for a research dataset.

Company: {company['name']}
Description: {company['description']}
Industries: {company.get('industries', 'N/A')}

Classify into one or more domains. Return ONLY category_name values from this list:

{domain_list}

A company may belong to multiple domains if its business spans multiple areas.

Respond with JSON only, no other text:
{{"domains": ["category_name_1", "category_name_2"], "confidence": "high" | "medium" | "low", "reasoning": "One sentence explanation"}}

If out of scope for {sector}, return: {{"domains": [], "confidence": "high", "reasoning": "why"}}"""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        response_text = response.content[0].text.strip()

        # Handle potential markdown code blocks
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON for {company['name']}: {e}")
        return {"domains": [], "confidence": "low", "reasoning": "Failed to parse API response"}
    except Exception as e:
        print(f"Warning: API error for {company['name']}: {e}")
        return {"domains": [], "confidence": "low", "reasoning": f"API error: {str(e)}"}


def process_sector(sector: str, dry_run: bool = False, limit: int = None):
    """Process all companies for a sector."""

    # Paths
    input_path = Path(__file__).parent.parent / 'data' / 'source' / f'crunchbase-raw-{sector}.md'
    output_path = Path(__file__).parent.parent / 'data' / 'source' / f'universe-{sector}.json'

    print(f"\n{'='*60}")
    print(f"Processing {sector} sector")
    print(f"{'='*60}")

    # Parse companies
    print(f"Parsing {input_path}...")
    companies = parse_crunchbase_markdown(input_path)
    print(f"Found {len(companies)} companies")

    if limit:
        companies = companies[:limit]
        print(f"Limited to {limit} companies")

    # Load domains
    domains = load_domains(sector)
    print(f"Loaded {len(domains)} domains")

    if dry_run:
        print("\nDry run - showing first 3 companies:")
        for c in companies[:3]:
            print(f"  - {c['name']}: {c['description'][:80]}...")
        return

    # Initialize API client
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    # Classify each company
    results = []
    total = len(companies)

    for i, company in enumerate(companies):
        print(f"[{i+1}/{total}] Classifying {company['name']}...", end=' ')

        classification = classify_company(client, company, sector, domains)

        result = {
            "company_name": company['name'],
            "description": company['description'],
            "location": company.get('location'),
            "founded": company.get('founded'),
            "industries": company.get('industries'),
            "cb_rank": company.get('cb_rank_company'),
            "sector": sector,
            "domains": classification.get('domains', []),
            "classification_confidence": classification.get('confidence', 'low'),
            "classification_reasoning": classification.get('reasoning', ''),
        }

        results.append(result)
        print(f"→ {result['domains']}")

        # Rate limiting - be conservative
        time.sleep(0.1)

    # Save results
    print(f"\nSaving {len(results)} companies to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Summary stats
    total_domains = sum(len(r['domains']) for r in results)
    empty_domains = sum(1 for r in results if not r['domains'])

    print(f"\nSummary:")
    print(f"  Total companies: {len(results)}")
    print(f"  Total domain assignments: {total_domains}")
    print(f"  Avg domains per company: {total_domains/len(results):.2f}")
    print(f"  Companies with no domains: {empty_domains}")


def main():
    parser = argparse.ArgumentParser(description='Classify Crunchbase companies into domains')
    parser.add_argument('--sector', choices=['space', 'bio', 'energy'],
                        help='Sector to process')
    parser.add_argument('--all', action='store_true',
                        help='Process all sectors')
    parser.add_argument('--dry-run', action='store_true',
                        help='Parse files without calling API')
    parser.add_argument('--limit', type=int,
                        help='Limit number of companies to process (for testing)')

    args = parser.parse_args()

    if not args.sector and not args.all:
        parser.print_help()
        return

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    for sector in sectors:
        process_sector(sector, dry_run=args.dry_run, limit=args.limit)


if __name__ == '__main__':
    main()
