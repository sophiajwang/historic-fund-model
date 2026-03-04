#!/usr/bin/env python3
"""
Step 2.3: Classify USASpending awards by sector and domain.

Uses a multi-tier classification approach:
1. Agency default sets sector (NASA→space, NIH→bio, DOE→energy)
2. NAICS code provides domain mapping if high/medium confidence
3. Description-based keyword pre-filter for LOW confidence codes
4. LLM fallback (Claude API) for truly ambiguous cases

Usage:
    # Dry run - analyze without LLM calls
    python scripts/classify_awards.py --dry-run

    # Classify with LLM (requires ANTHROPIC_API_KEY)
    python scripts/classify_awards.py --sector space

    # Limit LLM calls for testing
    python scripts/classify_awards.py --sector space --llm-limit 100
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables directly

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MAPPING_FILE = DATA_DIR / "naics-to-domain-mapping-expanded.json"

# Agency to sector mapping
AGENCY_SECTOR_MAP = {
    "National Aeronautics and Space Administration": "space",
    "NASA": "space",
    "Department of Energy": "energy",
    "DOE": "energy",
    "National Institutes of Health": "bio",
    "NIH": "bio",
    "Department of Health and Human Services": "bio",
    "HHS": "bio",
}

# Keywords that suggest space-relevance (for pre-filtering LOW confidence codes)
SPACE_KEYWORDS = [
    # Core space terms
    r"\bsatellite\b", r"\bspacecraft\b", r"\bspace\s*(craft|ship|station|vehicle)\b",
    r"\brocket\b", r"\blaunch\b", r"\borbit\b", r"\borbital\b",
    r"\bastronaut\b", r"\biss\b", r"\bstation\b",
    # Programs and missions
    r"\bjwst\b", r"\bjames\s*webb\b", r"\bhubble\b", r"\bwebb\s*telescope\b",
    r"\borion\b", r"\bsls\b", r"\bartemi[s]?\b", r"\bcommercial\s*crew\b",
    r"\bmars\b", r"\blunar\b", r"\bmoon\b", r"\bdeep\s*space\b",
    r"\btdrss\b", r"\btracking\s*and\s*data\b",
    # Subsystems
    r"\bpropulsion\b", r"\bpropellant\b", r"\bthruster\b",
    r"\btelemetry\b", r"\battitude\s*control\b", r"\bguidance\b",
    r"\bthermal\s*control\b", r"\bsolar\s*(array|panel|cell)\b",
    r"\bspace\s*suit\b", r"\beva\b",
    # Earth observation
    r"\bremote\s*sensing\b", r"\bearth\s*observ\b", r"\blandsat\b",
    # Ground systems
    r"\bground\s*station\b", r"\bdsn\b", r"\bdeep\s*space\s*network\b",
    r"\bmission\s*(control|operations)\b",
    # Testing
    r"\bvibration\s*test\b", r"\bthermal\s*vacuum\b", r"\bspace\s*qualif\b",
    # Facilities
    r"\bjsc\b", r"\bjohnson\s*space\b", r"\bksc\b", r"\bkennedy\s*space\b",
    r"\bjpl\b", r"\bjet\s*propulsion\b", r"\bgoddard\b", r"\bgsfc\b",
    r"\bmarshall\b", r"\bmsfc\b", r"\bames\s*research\b",
]

# Keywords that suggest NON-space (facilities, admin support)
NON_SPACE_KEYWORDS = [
    r"\bjanitorial\b", r"\bcustodial\b", r"\bcleaning\s*service\b",
    r"\bsecurity\s*guard\b", r"\bsecurity\s*patrol\b", r"\bsecurity\s*service\b",
    r"\blandscaping\b", r"\bgrounds\s*maintenance\b", r"\blawn\b",
    r"\boffice\s*furniture\b", r"\boffice\s*supplies\b",
    r"\btraining\s*(seminar|workshop|course)\b", r"\bleadership\s*training\b",
    r"\bhuman\s*resources\b", r"\bhr\s*consulting\b",
    r"\baccounting\s*service\b", r"\bfinancial\s*audit\b",
    r"\blegal\s*service\b", r"\bpatent\s*application\b",
    r"\bcafeteria\b", r"\bfood\s*service\b", r"\bvending\b",
    r"\bparking\b", r"\bshuttle\s*bus\b", r"\btransportation\s*service\b",
    r"\bpest\s*control\b", r"\bexterminator\b",
    r"\bfire\s*alarm\b", r"\bsprinkler\b", r"\bfire\s*suppression\b",
    r"\bhvac\b", r"\bair\s*conditioning\b", r"\bheating\b",
    r"\bplumbing\b", r"\belectrical\s*wiring\b", r"\broofing\b",
]

# Compile regex patterns
SPACE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SPACE_KEYWORDS]
NON_SPACE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in NON_SPACE_KEYWORDS]


def load_naics_mapping():
    """Load the NAICS to domain mapping."""
    with open(MAPPING_FILE) as f:
        return json.load(f)


def load_domain_list(sector: str):
    """Load the domain list for a sector from CSV."""
    csv_path = PROJECT_ROOT.parent / "historic-fund-model" / "data" / f"domains-{sector}.csv"
    if not csv_path.exists():
        # Try local path
        csv_path = DATA_DIR / f"domains-{sector}.csv"

    domains = []
    if csv_path.exists():
        with open(csv_path) as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split(',')
                if parts:
                    domains.append({
                        "category_name": parts[0],
                        "label": parts[1] if len(parts) > 1 else "",
                        "description": parts[2] if len(parts) > 2 else ""
                    })
    return domains


def get_sector_from_agency(agency_name: str) -> str:
    """Determine sector from awarding agency."""
    if not agency_name:
        return None

    # Direct match
    if agency_name in AGENCY_SECTOR_MAP:
        return AGENCY_SECTOR_MAP[agency_name]

    # Partial match
    agency_upper = agency_name.upper()
    if "NASA" in agency_upper or "AERONAUTICS" in agency_upper:
        return "space"
    if "ENERGY" in agency_upper:
        return "energy"
    if "HEALTH" in agency_upper or "NIH" in agency_upper:
        return "bio"

    return None  # Ambiguous agency


def keyword_prefilter(description: str) -> dict:
    """
    Pre-filter using keywords before sending to LLM.
    Returns: {"is_space": True/False/None, "confidence": str, "matches": list}
    """
    if not description:
        return {"is_space": None, "confidence": "none", "matches": []}

    desc_lower = description.lower()

    # Check for space keywords
    space_matches = []
    for pattern in SPACE_PATTERNS:
        match = pattern.search(description)
        if match:
            space_matches.append(match.group())

    # Check for non-space keywords
    non_space_matches = []
    for pattern in NON_SPACE_PATTERNS:
        match = pattern.search(description)
        if match:
            non_space_matches.append(match.group())

    # Decision logic
    if non_space_matches and not space_matches:
        return {
            "is_space": False,
            "confidence": "high",
            "matches": non_space_matches,
            "reason": "Non-space keywords found, no space keywords"
        }

    if space_matches and not non_space_matches:
        return {
            "is_space": True,
            "confidence": "medium",
            "matches": space_matches,
            "reason": "Space keywords found"
        }

    if space_matches and non_space_matches:
        # Both found - ambiguous, needs LLM
        return {
            "is_space": None,
            "confidence": "low",
            "matches": space_matches + non_space_matches,
            "reason": "Mixed keywords - ambiguous"
        }

    # No keywords found - ambiguous
    return {
        "is_space": None,
        "confidence": "none",
        "matches": [],
        "reason": "No keywords found"
    }


def classify_by_naics(naics_code: str, sector: str, mapping: dict) -> dict:
    """
    Classify award by NAICS code using the mapping.
    Returns: {"method": str, "confidence": str, "domains": list or None, "needs_llm": bool}
    """
    if not naics_code:
        return {
            "method": "no_naics",
            "confidence": "none",
            "domains": None,
            "needs_llm": True
        }

    sector_mapping = mapping.get(sector, {})
    # Filter out comment keys
    sector_mapping = {k: v for k, v in sector_mapping.items() if not k.startswith('_')}

    if naics_code not in sector_mapping:
        return {
            "method": "naics_unmapped",
            "confidence": "none",
            "domains": None,
            "needs_llm": True
        }

    entry = sector_mapping[naics_code]
    confidence = entry.get("confidence", "low")
    domains = entry.get("domains")

    if confidence == "exclude":
        return {
            "method": "naics_exclude",
            "confidence": "high",
            "domains": [],
            "needs_llm": False,
            "excluded": True
        }

    if confidence == "high":
        return {
            "method": "naics_high",
            "confidence": "high",
            "domains": domains,
            "needs_llm": False
        }

    if confidence == "medium":
        return {
            "method": "naics_medium",
            "confidence": "medium",
            "domains": domains,
            "needs_llm": False  # Accept medium confidence
        }

    # Low confidence - may need LLM
    return {
        "method": "naics_low",
        "confidence": "low",
        "domains": domains,
        "needs_llm": True
    }


def classify_with_llm(award: dict, sector: str, domains: list) -> dict:
    """
    Classify award using Claude API.
    Returns: {"domains": list, "confidence": str, "reasoning": str}
    """
    try:
        import anthropic
    except ImportError:
        return {
            "domains": None,
            "confidence": "error",
            "reasoning": "anthropic package not installed"
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "domains": None,
            "confidence": "error",
            "reasoning": "ANTHROPIC_API_KEY not set"
        }

    client = anthropic.Anthropic(api_key=api_key)

    # Build domain list for prompt
    domain_list = "\n".join([
        f"- {d['category_name']}: {d['description']}"
        for d in domains
    ])

    prompt = f"""You are classifying government contract awards into domains for a research dataset.

Award description: {award.get('award_description', 'N/A')}
Awarding agency: {award.get('awarding_agency', 'N/A')}
NAICS code: {award.get('naics_code', 'N/A')}
NAICS description: {award.get('naics_description', 'N/A')}
Sector: {sector}

Classify this award into one or more domains for the {sector} sector:

{domain_list}

Respond with JSON only:
{{
  "domains": ["<category_name>", ...],
  "confidence": "high" | "medium" | "low",
  "reasoning": "<one sentence>"
}}

If the award does not fit any domain or is administrative/facilities support, respond:
{{
  "domains": [],
  "confidence": "high",
  "reasoning": "<why excluded>"
}}"""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        content = response.content[0].text.strip()
        # Extract JSON from response
        if content.startswith('{'):
            result = json.loads(content)
        else:
            # Try to find JSON in response
            match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {
                    "domains": None,
                    "confidence": "error",
                    "reasoning": f"Could not parse: {content[:100]}"
                }

        return result

    except Exception as e:
        return {
            "domains": None,
            "confidence": "error",
            "reasoning": str(e)
        }


def classify_award(award: dict, sector: str, mapping: dict, domains: list,
                   use_llm: bool = True, stats: dict = None) -> dict:
    """
    Full classification pipeline for a single award.
    """
    result = {
        "award_id": award.get("award_id"),
        "sector": sector,
        "classification_method": None,
        "classification_confidence": None,
        "domains": None,
        "excluded": False,
        "llm_used": False,
    }

    # Step 1: NAICS-based classification
    naics_code = award.get("naics_code") or ""
    naics_result = classify_by_naics(
        naics_code.strip() if naics_code else "",
        sector,
        mapping
    )

    if stats:
        stats["naics_" + naics_result["method"]] += 1

    # If excluded by NAICS
    if naics_result.get("excluded"):
        result["classification_method"] = "naics_exclude"
        result["classification_confidence"] = "high"
        result["domains"] = []
        result["excluded"] = True
        return result

    # If high/medium confidence NAICS
    if not naics_result["needs_llm"] and naics_result["domains"]:
        result["classification_method"] = naics_result["method"]
        result["classification_confidence"] = naics_result["confidence"]
        result["domains"] = naics_result["domains"]
        return result

    # Step 2: Keyword pre-filter for ambiguous cases
    description = award.get("award_description", "")
    keyword_result = keyword_prefilter(description)

    if stats:
        stats["keyword_" + keyword_result["confidence"]] += 1

    # If keywords clearly indicate non-space
    if keyword_result["is_space"] == False and keyword_result["confidence"] == "high":
        result["classification_method"] = "keyword_exclude"
        result["classification_confidence"] = "medium"
        result["domains"] = []
        result["excluded"] = True
        result["keyword_matches"] = keyword_result["matches"]
        return result

    # If keywords indicate space and NAICS gave domains
    if keyword_result["is_space"] == True and naics_result["domains"]:
        result["classification_method"] = "naics_keyword_confirmed"
        result["classification_confidence"] = "medium"
        result["domains"] = naics_result["domains"]
        result["keyword_matches"] = keyword_result["matches"]
        return result

    # Step 3: LLM for truly ambiguous cases
    if use_llm:
        if stats:
            stats["llm_calls"] += 1

        llm_result = classify_with_llm(award, sector, domains)
        result["classification_method"] = "llm"
        result["classification_confidence"] = llm_result.get("confidence", "low")
        result["domains"] = llm_result.get("domains")
        result["llm_reasoning"] = llm_result.get("reasoning")
        result["llm_used"] = True

        if not result["domains"]:
            result["excluded"] = True

        return result

    # No LLM - return as unclassified
    result["classification_method"] = "unclassified"
    result["classification_confidence"] = "none"
    result["domains"] = naics_result.get("domains")  # Use NAICS domains if available
    return result


def main():
    parser = argparse.ArgumentParser(description="Classify USASpending awards")
    parser.add_argument("--sector", choices=["space", "bio", "energy"],
                       help="Sector to classify (default: all from agency)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Analyze without LLM calls")
    parser.add_argument("--llm-limit", type=int, default=0,
                       help="Limit number of LLM calls (0=unlimited)")
    parser.add_argument("--input", type=str,
                       default="awards_normalized.json",
                       help="Input file in data/processed/")
    args = parser.parse_args()

    print("=" * 60)
    print("USASpending Award Classification - Step 2.3")
    print("=" * 60)

    # Load data
    input_path = PROCESSED_DIR / args.input
    print(f"\nLoading awards from {input_path}...")
    with open(input_path) as f:
        data = json.load(f)

    awards = data.get("awards", [])
    print(f"Loaded {len(awards):,} awards")

    # Load mapping
    print(f"Loading NAICS mapping from {MAPPING_FILE}...")
    mapping = load_naics_mapping()

    # Load domain lists
    domains_by_sector = {}
    for sector in ["space", "bio", "energy"]:
        domains_by_sector[sector] = load_domain_list(sector)
        print(f"  {sector}: {len(domains_by_sector[sector])} domains")

    # Initialize stats
    stats = defaultdict(int)

    # Filter by sector if specified
    if args.sector:
        target_sector = args.sector
    else:
        target_sector = None  # Determine from agency

    # Process awards
    print(f"\nClassifying awards...")
    classified = []
    llm_calls = 0

    for i, award in enumerate(awards):
        # Determine sector
        if target_sector:
            sector = target_sector
        else:
            sector = get_sector_from_agency(award.get("awarding_agency", ""))
            if not sector:
                stats["no_sector"] += 1
                continue

        # Check LLM limit
        use_llm = not args.dry_run
        if args.llm_limit > 0 and llm_calls >= args.llm_limit:
            use_llm = False

        # Classify
        result = classify_award(
            award,
            sector,
            mapping,
            domains_by_sector.get(sector, []),
            use_llm=use_llm,
            stats=stats
        )

        if result.get("llm_used"):
            llm_calls += 1

        # Merge result with original award data
        classified_award = {**award, **result}
        classified.append(classified_award)

        # Progress
        if (i + 1) % 10000 == 0:
            print(f"  Processed {i+1:,} / {len(awards):,} ({100*(i+1)/len(awards):.1f}%)")

    # Summary
    print(f"\n{'=' * 60}")
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)

    print(f"\nTotal awards processed: {len(classified):,}")
    print(f"\nBy classification method:")
    method_counts = Counter(a.get("classification_method") for a in classified)
    for method, count in method_counts.most_common():
        print(f"  {method}: {count:,} ({100*count/len(classified):.1f}%)")

    print(f"\nExcluded (not relevant): {sum(1 for a in classified if a.get('excluded')):,}")
    print(f"LLM calls made: {llm_calls:,}")

    # Domain distribution
    domain_counts = Counter()
    for award in classified:
        for domain in (award.get("domains") or []):
            domain_counts[domain] += 1

    print(f"\nTop 20 domains by award count:")
    for domain, count in domain_counts.most_common(20):
        print(f"  {domain}: {count:,}")

    # Save results
    if not args.dry_run:
        output_file = PROCESSED_DIR / "awards_classified.json"
        print(f"\nSaving to {output_file}...")

        with open(output_file, 'w') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "classification_stats": dict(stats),
                "method_counts": dict(method_counts),
                "domain_counts": dict(domain_counts),
                "awards": classified,
            }, f, indent=2)

        print(f"Done! Saved {len(classified):,} classified awards.")
    else:
        print("\n[DRY RUN] No output written.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
