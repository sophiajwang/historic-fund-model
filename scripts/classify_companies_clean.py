#!/usr/bin/env python3
"""
Classify unclassified companies and assign primary domains to multi-domain companies.

This script:
1. Classifies companies with empty domains using Claude API
2. Assigns a single primary_domain to companies with multiple domains

Usage:
    python scripts/classify_companies_clean.py --sector space --dry-run
    python scripts/classify_companies_clean.py --all
    python scripts/classify_companies_clean.py --all --limit 10

Output:
    Updates data/cleaned/source/market-data-{sector}.json with:
    - domains: original or newly assigned domains
    - primary_domain: single domain for aggregation (no multi-counting)
"""

import argparse
import json
import os
import re
import time
from pathlib import Path
from datetime import datetime

ANTHROPIC_AVAILABLE = False
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CLEANED_DIR = DATA_DIR / "cleaned" / "source"


def load_domains(sector: str) -> list:
    """Load domain definitions from CSV file."""
    csv_path = DATA_DIR / f"domains-{sector}.csv"
    domains = []
    if csv_path.exists():
        with open(csv_path) as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split(",", 2)
                if len(parts) >= 2:
                    domains.append({
                        "category_name": parts[0],
                        "label": parts[1],
                        "description": parts[2] if len(parts) > 2 else ""
                    })
    return domains


def classify_company_llm(client, company: dict, domains: list, sector: str) -> dict:
    """Classify a company with no domains using Claude API."""
    company_name = company.get("company_name", "")
    ticker = company.get("ticker", "")
    industry = company.get("industry_yahoo", "")
    sector_yahoo = company.get("sector_yahoo", "")

    # Build domain reference
    domain_ref = "\n".join([
        f"  - {d['category_name']}: {d['description'][:150]}"
        for d in domains[:30]  # Limit to avoid token overflow
    ])

    prompt = f"""You are classifying a public company for a research dataset tracking capital flows in the {sector} sector.

Company: {company_name}
Ticker: {ticker}
Yahoo Finance sector: {sector_yahoo}
Yahoo Finance industry: {industry}

This company was identified as potentially being in the {sector} sector but needs domain classification.

Available domains for {sector}:
{domain_ref}

Based on the company name and industry, classify this company:
1. Select 1-3 most relevant domains from the list above
2. Choose ONE primary domain that best represents the company's main business

Respond with JSON only:
{{"domains": ["domain1", "domain2"], "primary_domain": "domain1", "confidence": "high" | "medium" | "low", "reasoning": "one sentence"}}

If this company does NOT belong in the {sector} sector at all, respond:
{{"domains": [], "primary_domain": null, "confidence": "high", "reasoning": "Not a {sector} company - describe why"}}"""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {"domains": [], "primary_domain": None, "confidence": "low", "reasoning": "Failed to parse response"}

    except Exception as e:
        return {"domains": [], "primary_domain": None, "confidence": "low", "reasoning": f"API error: {str(e)}"}


def assign_primary_domain_llm(client, company: dict, domains_list: list, sector: str) -> dict:
    """Assign primary domain to a multi-domain company using Claude API."""
    company_name = company.get("company_name", "")
    ticker = company.get("ticker", "")
    current_domains = company.get("domains", [])
    industry = company.get("industry_yahoo", "")

    # Get descriptions for current domains
    domain_lookup = {d['category_name']: d['description'] for d in domains_list}
    domain_descriptions = "\n".join([
        f"  - {d}: {domain_lookup.get(d, 'No description')[:100]}"
        for d in current_domains
    ])

    prompt = f"""You are determining the PRIMARY business domain for a public company in the {sector} sector.

Company: {company_name}
Ticker: {ticker}
Industry: {industry}

The company has been classified into these domains:
{domain_descriptions}

Select the ONE domain that BEST represents this company's primary business focus.
This will be used to ensure the company's market cap is counted only once in aggregations.

Respond with JSON only:
{{"primary_domain": "domain_name", "confidence": "high" | "medium" | "low", "reasoning": "one sentence explaining why this is the primary domain"}}"""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            # Validate that primary_domain is in the company's domains
            primary = result.get("primary_domain")
            if primary and primary in current_domains:
                return result
            elif primary and primary not in current_domains:
                # LLM returned a domain not in the list - use first domain
                return {
                    "primary_domain": current_domains[0],
                    "confidence": "medium",
                    "reasoning": f"LLM suggested {primary} but defaulted to {current_domains[0]}"
                }
            else:
                return {
                    "primary_domain": current_domains[0] if current_domains else None,
                    "confidence": "low",
                    "reasoning": "Defaulted to first domain"
                }
        else:
            return {
                "primary_domain": current_domains[0] if current_domains else None,
                "confidence": "low",
                "reasoning": "Failed to parse response"
            }

    except Exception as e:
        return {
            "primary_domain": current_domains[0] if current_domains else None,
            "confidence": "low",
            "reasoning": f"API error: {str(e)}"
        }


def process_sector(sector: str, client, dry_run: bool = False, limit: int = None):
    """Process a sector's market data to classify and assign primary domains."""
    input_path = CLEANED_DIR / f"market-data-{sector}.json"
    output_path = CLEANED_DIR / f"market-data-{sector}.json"  # Same file, we'll update in place

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print(f"Run pull_market_data_clean.py first to generate cleaned market data.")
        return None

    print(f"\n{'='*60}")
    print(f"CLASSIFYING COMPANIES FOR {sector.upper()}")
    print(f"{'='*60}")

    # Load market data
    with open(input_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    # Load domain definitions
    domains = load_domains(sector)
    print(f"Loaded {len(domains)} domain definitions")

    # Filter to successful companies only
    successful = [c for c in companies if c.get('status') == 'success']
    print(f"Total successful companies: {len(successful)}")

    # Identify companies needing work
    no_domain = [c for c in successful if len(c.get('domains', [])) == 0]
    multi_domain = [c for c in successful if len(c.get('domains', [])) > 1]
    single_domain = [c for c in successful if len(c.get('domains', [])) == 1]

    print(f"  - No domain (need classification): {len(no_domain)}")
    print(f"  - Multi-domain (need primary): {len(multi_domain)}")
    print(f"  - Single domain (already good): {len(single_domain)}")

    if dry_run:
        print(f"\n[DRY RUN] Would classify {len(no_domain)} companies")
        print(f"[DRY RUN] Would assign primary domains to {len(multi_domain)} companies")

        if no_domain:
            print(f"\nCompanies needing classification:")
            for c in no_domain[:5]:
                print(f"  - {c['company_name']} ({c.get('ticker', 'N/A')})")

        if multi_domain:
            print(f"\nCompanies needing primary domain:")
            for c in multi_domain[:5]:
                print(f"  - {c['company_name']}: {c.get('domains', [])}")

        return {"no_domain": len(no_domain), "multi_domain": len(multi_domain)}

    # Apply limit if specified
    if limit:
        no_domain = no_domain[:limit]
        multi_domain = multi_domain[:limit]

    # Track results
    classified_count = 0
    primary_assigned_count = 0
    errors = []

    # Step 1: Classify companies with no domains
    if no_domain:
        print(f"\nClassifying {len(no_domain)} companies with no domain...")
        for i, company in enumerate(no_domain):
            print(f"  [{i+1}/{len(no_domain)}] {company['company_name']}...", end=' ', flush=True)

            result = classify_company_llm(client, company, domains, sector)

            # Update company record
            company['domains'] = result.get('domains', [])
            company['primary_domain'] = result.get('primary_domain')
            company['classification'] = {
                'method': 'llm_clean',
                'confidence': result.get('confidence', 'low'),
                'reasoning': result.get('reasoning', ''),
                'classified_at': datetime.now().isoformat()
            }

            if result.get('domains'):
                print(f"-> {result['primary_domain']} ({result.get('confidence', 'low')})")
                classified_count += 1
            else:
                print(f"-> NOT IN SECTOR ({result.get('reasoning', '')[:50]})")

            time.sleep(0.1)  # Rate limiting

    # Step 2: Assign primary domains to multi-domain companies
    if multi_domain:
        print(f"\nAssigning primary domains to {len(multi_domain)} multi-domain companies...")
        for i, company in enumerate(multi_domain):
            print(f"  [{i+1}/{len(multi_domain)}] {company['company_name']}...", end=' ', flush=True)

            result = assign_primary_domain_llm(client, company, domains, sector)

            # Update company record
            company['primary_domain'] = result.get('primary_domain')
            company['primary_domain_assignment'] = {
                'method': 'llm_clean',
                'confidence': result.get('confidence', 'low'),
                'reasoning': result.get('reasoning', ''),
                'assigned_at': datetime.now().isoformat()
            }

            print(f"-> {result.get('primary_domain')} (from {len(company.get('domains', []))} domains)")
            primary_assigned_count += 1

            time.sleep(0.1)  # Rate limiting

    # Step 3: Set primary_domain for single-domain companies (trivial)
    for company in single_domain:
        domains_list = company.get('domains', [])
        if domains_list:
            company['primary_domain'] = domains_list[0]

    # Save updated data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2)

    print(f"\nSaved updated data to {output_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY FOR {sector.upper()}")
    print(f"{'='*60}")
    print(f"Companies classified: {classified_count}")
    print(f"Primary domains assigned: {primary_assigned_count}")
    print(f"Single-domain companies: {len(single_domain)}")

    return {
        "classified": classified_count,
        "primary_assigned": primary_assigned_count,
        "single_domain": len(single_domain)
    }


def main():
    parser = argparse.ArgumentParser(description="Classify companies and assign primary domains")
    parser.add_argument("--sector", choices=["space", "bio", "energy"],
                        help="Sector to process")
    parser.add_argument("--all", action="store_true",
                        help="Process all sectors")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without calling LLM")
    parser.add_argument("--limit", type=int,
                        help="Limit number of companies to process per category")

    args = parser.parse_args()

    if not args.sector and not args.all:
        parser.print_help()
        return

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not args.dry_run:
        if not ANTHROPIC_AVAILABLE:
            print("ERROR: anthropic package not installed.")
            print("Install with: pip3 install anthropic")
            return
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY environment variable not set")
            return

    print("Company Classification Script (Cleaned Data)")
    print("="*60)

    # Initialize client
    client = None
    if not args.dry_run:
        client = anthropic.Anthropic(api_key=api_key)

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    for sector in sectors:
        process_sector(sector, client, dry_run=args.dry_run, limit=args.limit)

    print("\nDone!")


if __name__ == "__main__":
    main()
