#!/usr/bin/env python3
"""
Resolve EDGAR identities for companies in the universe files.

Matches each company to their SEC CIK number using:
1. SEC EFTS API search
2. Algorithmic scoring (name similarity, location, founding year)
3. Claude API for ambiguous cases

Usage:
    python scripts/resolve_edgar.py --sector space
    python scripts/resolve_edgar.py --sector bio
    python scripts/resolve_edgar.py --sector energy
    python scripts/resolve_edgar.py --all
    python scripts/resolve_edgar.py --all --resume

Output:
    Updates data/source/universe-{sector}.json with EDGAR fields
"""

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    exit(1)

# Configuration
SEC_USER_AGENT = "HistoricFundModel research@example.com"
SEC_RATE_LIMIT = 0.12  # ~8 requests/second (conservative)
CHECKPOINT_INTERVAL = 50

# US State abbreviations for location matching
US_STATES = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
    'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
}


def extract_state(location: str) -> str:
    """Extract US state abbreviation from location string."""
    if not location:
        return None

    location_lower = location.lower()

    # Check for state abbreviations
    for state_name, abbrev in US_STATES.items():
        if state_name in location_lower or f", {abbrev.lower()}" in location_lower or f" {abbrev.lower()} " in location_lower:
            return abbrev

    # Check for abbreviation at end
    parts = location.split(',')
    if len(parts) >= 2:
        state_part = parts[-2].strip() if 'united states' in parts[-1].lower() else parts[-1].strip()
        if len(state_part) == 2 and state_part.upper() in US_STATES.values():
            return state_part.upper()

    return None


def normalize_company_name(name: str) -> str:
    """Normalize company name for comparison."""
    if not name:
        return ""

    normalized = name.lower().strip()

    # Remove CIK references like "(CIK 0001181412)" or "(ASTS, ASTSW)"
    normalized = re.sub(r'\s*\([^)]*cik[^)]*\)', '', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\s*\([A-Z]{2,5}(?:,\s*[A-Z]{2,5})*\)', '', normalized, flags=re.IGNORECASE)

    # Remove common entity suffixes (only at end of string)
    suffixes = [
        r',?\s*inc\.?$', r',?\s*llc\.?$', r',?\s*corp\.?$',
        r',?\s*corporation$', r',?\s*incorporated$', r',?\s*ltd\.?$',
        r',?\s*limited$', r',?\s*co\.?$', r',?\s*company$',
        r',?\s*l\.?p\.?$', r',?\s*plc\.?$', r',?\s*pbc\.?$',
    ]

    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)

    # Remove punctuation but keep spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two company names."""
    n1 = normalize_company_name(name1)
    n2 = normalize_company_name(name2)
    return SequenceMatcher(None, n1, n2).ratio()


def search_sec_efts(company_name: str, retries: int = 3) -> list:
    """Search SEC EFTS API for company matches."""

    # Try different name variations
    base_name = normalize_company_name(company_name)
    name_variations = [
        company_name,                           # Original name
        base_name,                              # Normalized
        f"{base_name} inc",                     # Add Inc
        f"{base_name} usa",                     # Add USA
        f"{base_name} corp",                    # Add Corp
        f"{base_name} technologies",            # Add Technologies
        ' '.join(company_name.split()[:2]),     # First two words
        ' '.join(company_name.split()[:3]),     # First three words
    ]
    # Dedupe while preserving order
    seen = set()
    name_variations = [x for x in name_variations if x and x not in seen and not seen.add(x)]

    all_results = []
    seen_ciks = set()

    for name_var in name_variations:
        if not name_var or len(name_var) < 2:
            continue

        encoded_name = urllib.parse.quote(name_var)
        url = f"https://efts.sec.gov/LATEST/search-index?q=%22{encoded_name}%22&forms=D,S-1,S-4"

        for attempt in range(retries):
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', SEC_USER_AGENT)

                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))

                    hits = data.get('hits', {}).get('hits', [])

                    for hit in hits:
                        source = hit.get('_source', {})
                        cik = source.get('ciks', [None])[0]

                        if cik and cik not in seen_ciks:
                            seen_ciks.add(cik)
                            inc_states = source.get('inc_states', [])
                            all_results.append({
                                'cik': cik,
                                'company_name': source.get('display_names', [name_var])[0],
                                'forms': source.get('root_forms', []),
                                'file_date': source.get('file_date'),
                                'state': inc_states[0] if inc_states else None,
                            })

                    break  # Success, exit retry loop

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limited
                    time.sleep(2 ** attempt)
                    continue
                elif attempt == retries - 1:
                    print(f"  HTTP error searching for {company_name}: {e}")
            except Exception as e:
                if attempt == retries - 1:
                    print(f"  Error searching for {company_name}: {e}")
                time.sleep(1)

        time.sleep(SEC_RATE_LIMIT)

    return all_results


def score_match(company: dict, sec_result: dict) -> dict:
    """Score how well a SEC result matches our company."""

    score = 0.0
    reasons = []

    # Name similarity (0-50 points)
    name_sim = name_similarity(company['company_name'], sec_result['company_name'])
    name_score = name_sim * 50
    score += name_score
    reasons.append(f"name_sim={name_sim:.2f}")

    # Location match (0-20 points)
    company_state = extract_state(company.get('location', ''))
    sec_state = sec_result.get('state')
    if company_state and sec_state:
        if company_state == sec_state:
            score += 20
            reasons.append("state_match")
        else:
            reasons.append(f"state_mismatch({company_state}!={sec_state})")

    # Has Form D filings (0-20 points)
    forms = sec_result.get('forms', [])
    has_form_d = any('D' in str(f) for f in forms)
    if has_form_d:
        score += 20
        reasons.append("has_form_d")

    # Has S-1/S-4 filings (0-10 points bonus)
    has_s1 = any('S-1' in str(f) or 'S-4' in str(f) for f in forms)
    if has_s1:
        score += 10
        reasons.append("has_s1_s4")

    return {
        'score': score,
        'reasons': reasons,
        'name_similarity': name_sim
    }


def determine_confidence(matches: list, top_match: dict) -> str:
    """Determine confidence level based on matches."""

    if not matches:
        return 'not_found'

    # Single match with high score - auto accept
    if len(matches) == 1:
        if top_match['score'] >= 70:
            return 'high'
        elif top_match['score'] >= 50:
            return 'medium'
        else:
            return 'low'

    # Multiple matches - always use Claude to pick the right one
    return 'needs_claude'


def get_legal_name_from_claude(client: anthropic.Anthropic, company: dict) -> str:
    """Ask Claude for the legal entity name of a company."""

    prompt = f"""What is the legal corporate entity name for this company? This will be used to search SEC EDGAR for Form D or S-1 filings.

Company: {company['company_name']}
Industry/Sector: {company.get('industries', 'Unknown')}
Description: {company.get('description', 'No description')[:300]}
Location: {company.get('location', 'Unknown')}

Examples of what to return:
- SpaceX → Space Exploration Technologies Corp
- Rocket Lab → Rocket Lab USA, Inc.
- Planet (satellite company) → Planet Labs PBC

Return ONLY the legal entity name. If you're unsure or the company is too small/new, return "UNKNOWN"."""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        legal_name = response.content[0].text.strip()

        # Clean up common issues
        legal_name = legal_name.strip('"\'')
        if legal_name.upper() == "UNKNOWN" or len(legal_name) < 3:
            return None

        return legal_name

    except Exception as e:
        print(f"  Claude name lookup error: {e}")
        return None


def resolve_with_claude(client: anthropic.Anthropic, company: dict, matches: list) -> dict:
    """Use Claude to resolve ambiguous matches."""

    matches_text = "\n".join([
        f"{i+1}. CIK {m['cik']} - {m['company_name']} ({m.get('state', 'Unknown state')}) - Forms: {m.get('forms', [])}"
        for i, m in enumerate(matches[:5])  # Limit to top 5
    ])

    prompt = f"""You are matching a company to its SEC filing identity.

Company from our database:
- Name: {company['company_name']}
- Location: {company.get('location', 'Unknown')}
- Founded: {company.get('founded', 'Unknown')}
- Description: {company.get('description', 'No description')[:300]}
- Industries: {company.get('industries', 'Unknown')}

SEC EDGAR returned these possible matches:
{matches_text}

Which CIK is the correct match for this company? Consider:
1. Name similarity (accounting for Inc/Corp/LLC variations)
2. State/location match
3. Industry relevance based on description

IMPORTANT: Do NOT match to investment funds, SPVs, or venture vehicles that invested IN the company. Examples to REJECT:
- "Gaingels Axiom Space LLC" - this is a fund that invested in Axiom, NOT Axiom itself
- "MW LSVC Axiom Space" - this is an investment vehicle, NOT the company
- "AVSF - Axiom Space 2022" - this is a fund, NOT the company
- Any entity with prefixes like "Gaingels", "MW LSVC", "AVSF", "AVGSF", "PML SPV"

Only match to the actual operating company (e.g., "Axiom Space, Inc." or "Axiom Space Inc.")

Respond with JSON only:
{{"selected_cik": "0001234567" or null if none match, "confidence": "high" or "medium" or "low", "reasoning": "One sentence explanation"}}

If none of the options are the actual operating company, return selected_cik as null."""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Handle markdown code blocks
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        result = json.loads(response_text)
        return result

    except Exception as e:
        print(f"  Claude error: {e}")
        return {"selected_cik": None, "confidence": "low", "reasoning": f"API error: {str(e)}"}


def resolve_company(company: dict, client: anthropic.Anthropic = None) -> dict:
    """Resolve EDGAR identity for a single company."""

    # Step 1: Ask Claude for the legal entity name
    legal_name = None
    if client:
        legal_name = get_legal_name_from_claude(client, company)

    # Step 2: Search SEC with legal name (if we have it) or original name
    search_name = legal_name if legal_name else company['company_name']
    sec_results = search_sec_efts(search_name)

    # If no results with legal name, try original name as fallback
    if not sec_results and legal_name and legal_name != company['company_name']:
        sec_results = search_sec_efts(company['company_name'])
        legal_name = None  # Reset so we score against original name

    # Create a modified company dict for scoring that includes the legal name
    scoring_company = company.copy()
    if legal_name:
        scoring_company['company_name'] = legal_name

    if not sec_results:
        return {
            'cik': None,
            'edgar_name': None,
            'edgar_state': None,
            'has_form_d': False,
            'has_s1_s4': False,
            'match_confidence': 'not_found',
            'match_reasoning': 'No SEC results found',
            'sec_candidates': 0
        }

    # Score all matches (using legal name if available)
    scored_matches = []
    for result in sec_results:
        match_score = score_match(scoring_company, result)
        scored_matches.append({
            **result,
            'match_score': match_score
        })

    # Sort by score
    scored_matches.sort(key=lambda x: x['match_score']['score'], reverse=True)
    top_match = scored_matches[0]

    # Determine confidence
    confidence = determine_confidence(scored_matches, top_match['match_score'])

    # If multiple matches (needs_claude) or low confidence, ask Claude to pick
    if confidence in ('needs_claude', 'low') and client:
        claude_result = resolve_with_claude(client, company, scored_matches)

        if claude_result.get('selected_cik'):
            # Find the match Claude selected
            selected = next(
                (m for m in scored_matches if m['cik'] == claude_result['selected_cik']),
                top_match
            )
            return {
                'cik': selected['cik'],
                'edgar_name': selected['company_name'],
                'edgar_state': selected.get('state'),
                'has_form_d': any('D' in str(f) for f in selected.get('forms', [])),
                'has_s1_s4': any('S-1' in str(f) or 'S-4' in str(f) for f in selected.get('forms', [])),
                'match_confidence': claude_result.get('confidence', 'medium'),
                'match_reasoning': f"Claude: {claude_result.get('reasoning', '')}",
                'sec_candidates': len(scored_matches)
            }
        else:
            return {
                'cik': None,
                'edgar_name': None,
                'edgar_state': None,
                'has_form_d': False,
                'has_s1_s4': False,
                'match_confidence': 'not_found',
                'match_reasoning': f"Claude: {claude_result.get('reasoning', 'No match')}",
                'sec_candidates': len(scored_matches)
            }

    # Use top match
    forms = top_match.get('forms', [])
    return {
        'cik': top_match['cik'],
        'edgar_name': top_match['company_name'],
        'edgar_state': top_match.get('state'),
        'has_form_d': any('D' in str(f) for f in forms),
        'has_s1_s4': any('S-1' in str(f) or 'S-4' in str(f) for f in forms),
        'match_confidence': confidence,
        'match_reasoning': ', '.join(top_match['match_score']['reasons']),
        'sec_candidates': len(scored_matches)
    }


def save_checkpoint(companies: list, output_path: Path, sector: str):
    """Save current results to file."""
    print(f"\n  💾 Saving checkpoint...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2)


def process_sector(sector: str, resume: bool = False):
    """Process all companies for a sector."""

    input_path = Path(__file__).parent.parent / 'data' / 'source' / f'universe-{sector}.json'
    output_path = input_path  # Update in place

    print(f"\n{'='*60}")
    print(f"Resolving EDGAR identities for {sector} sector")
    print(f"{'='*60}")

    # Load companies
    with open(input_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    print(f"Loaded {len(companies)} companies")

    # Initialize Claude client for ambiguous cases
    client = anthropic.Anthropic()

    # Track stats
    stats = {'high': 0, 'medium': 0, 'low': 0, 'not_found': 0, 'claude_calls': 0}

    for i, company in enumerate(companies):
        # Skip if already resolved and resuming
        if resume and company.get('cik') is not None:
            print(f"[{i+1}/{len(companies)}] Skipping {company['company_name']} (already resolved)")
            stats[company.get('match_confidence', 'high')] += 1
            continue

        # Skip if already marked not_found and resuming
        if resume and company.get('match_confidence') == 'not_found':
            print(f"[{i+1}/{len(companies)}] Skipping {company['company_name']} (marked not_found)")
            stats['not_found'] += 1
            continue

        print(f"[{i+1}/{len(companies)}] Resolving {company['company_name']}...", end=' ')

        edgar_info = resolve_company(company, client)

        # Check if Claude was used
        if 'Claude:' in edgar_info.get('match_reasoning', ''):
            stats['claude_calls'] += 1

        # Update company record
        company.update(edgar_info)

        confidence = edgar_info['match_confidence']
        stats[confidence] += 1

        if edgar_info['cik']:
            print(f"→ CIK {edgar_info['cik']} ({confidence})")
        else:
            print(f"→ Not found ({edgar_info['match_reasoning'][:50]})")

        # Checkpoint
        if (i + 1) % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(companies, output_path, sector)

    # Final save
    save_checkpoint(companies, output_path, sector)

    # Summary
    print(f"\nSummary for {sector}:")
    print(f"  High confidence: {stats['high']}")
    print(f"  Medium confidence: {stats['medium']}")
    print(f"  Low confidence: {stats['low']}")
    print(f"  Not found: {stats['not_found']}")
    print(f"  Claude API calls: {stats['claude_calls']}")

    matched = stats['high'] + stats['medium'] + stats['low']
    total = len(companies)
    print(f"  Match rate: {matched}/{total} ({100*matched/total:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description='Resolve EDGAR identities for universe companies')
    parser.add_argument('--sector', choices=['space', 'bio', 'energy'],
                        help='Sector to process')
    parser.add_argument('--all', action='store_true',
                        help='Process all sectors')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint (skip already resolved)')

    args = parser.parse_args()

    if not args.sector and not args.all:
        parser.print_help()
        return

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    for sector in sectors:
        process_sector(sector, resume=args.resume)


if __name__ == '__main__':
    main()
