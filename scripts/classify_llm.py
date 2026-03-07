#!/usr/bin/env python3
"""
LLM classification for ambiguous USASpending awards.
Step 2.3b - classifies records that couldn't be classified by NAICS/CFDA rules.

Records that don't fit space/bio/energy are saved to not_applicable/ for review.

Usage:
    python3 scripts/classify_llm.py --agency NSF --dry-run
    python3 scripts/classify_llm.py --agency NSF --limit 100
    python3 scripts/classify_llm.py --agency DoD --sample 1000
"""

import argparse
import json
import os
import re
import time
from pathlib import Path
from collections import defaultdict
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
CLASSIFIED_DIR = DATA_DIR / "usaspending" / "classified"
NOT_APPLICABLE_DIR = DATA_DIR / "usaspending" / "not_applicable"

# Load domain CSVs for reference
def load_domains():
    """Load domain definitions from CSV files."""
    domains = {}
    for sector in ["space", "bio", "energy"]:
        csv_path = DATA_DIR / f"domains-{sector}.csv"
        if csv_path.exists():
            domains[sector] = []
            with open(csv_path) as f:
                next(f)  # Skip header
                for line in f:
                    parts = line.strip().split(",", 2)
                    if len(parts) >= 2:
                        domains[sector].append({
                            "category_name": parts[0],
                            "label": parts[1],
                            "description": parts[2] if len(parts) > 2 else ""
                        })
    return domains


# High-confidence keywords - specific enough to indicate sector relevance
HIGH_CONFIDENCE_KEYWORDS = {
    "space": [
        "spacecraft", "launch vehicle", "space station", "astronaut", "lunar",
        "mars mission", "asteroid", "planetary science", "orbital", "propulsion system",
        "space force", "space command", "earth observation satellite", "cubesat",
        "smallsat", "deep space", "interplanetary", "astrophysics", "cosmology"
    ],
    "bio": [
        "gene therapy", "cell therapy", "CRISPR", "mRNA", "clinical trial",
        "Phase I", "Phase II", "Phase III", "therapeutic development", "drug discovery",
        "drug development", "biopharmaceutical", "monoclonal antibody", "immunotherapy",
        "oncology research", "genomics research", "proteomics", "synthetic biology",
        "SBIR biotech", "STTR biotech", "biodefense", "pandemic preparedness"
    ],
    "energy": [
        "photovoltaic", "fuel cell", "energy storage system", "carbon capture",
        "nuclear fusion", "nuclear fission", "advanced reactor", "offshore wind",
        "solar farm", "battery technology", "grid modernization", "smart grid",
        "renewable energy research", "clean energy", "ARPA-E", "hydrogen production",
        "geothermal energy", "wave energy", "tidal energy"
    ]
}

# Context-dependent keywords - need R&D indicators to be relevant
CONTEXT_KEYWORDS = {
    "space": ["satellite", "rocket", "GPS", "GNSS", "remote sensing", "telescope", "NASA"],
    "bio": ["vaccine", "genomic", "protein", "antibody", "diagnostic", "pathogen", "virus",
            "cancer", "tumor", "pharmaceutical", "biotech"],
    "energy": ["solar", "wind", "nuclear", "battery", "grid", "turbine", "hydrogen",
               "renewable", "electricity", "transmission"]
}

# R&D indicators that validate context-dependent keywords
RD_INDICATORS = [
    "research", "development", "r&d", "prototype", "demonstration", "sbir", "sttr",
    "innovative", "advanced", "novel", "experimental", "proof of concept", "feasibility",
    "technology development", "engineering development", "science and technology"
]

# Negative keywords that indicate non-R&D procurement
NEGATIVE_KEYWORDS = [
    "supply", "purchase order", "tablet", "capsule", "mg ", "ml ", "gram",  # medication
    "charger", "repair", "maintenance", "janitorial", "food service",  # services
    "construction of", "renovation of", "building modification"  # construction
]


def is_potentially_relevant(record):
    """Check if a record might be relevant to our sectors based on keywords."""
    description = (record.get("description") or "").lower()
    naics_desc = (record.get("naics_description") or "").lower()
    text = f"{description} {naics_desc}"

    # Check for negative keywords first (likely non-R&D)
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw in text:
            return False, None

    # Check high-confidence keywords (no R&D context needed)
    for sector, keywords in HIGH_CONFIDENCE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return True, sector

    # Check context-dependent keywords (need R&D indicator)
    has_rd_indicator = any(ind in text for ind in RD_INDICATORS)
    if has_rd_indicator:
        for sector, keywords in CONTEXT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return True, sector

    return False, None


def classify_with_llm(client, record, domains):
    """Classify a single record using Claude API."""
    description = record.get("description") or ""
    naics_code = record.get("naics_code") or ""
    naics_desc = record.get("naics_description") or ""
    cfda_number = record.get("cfda_number") or ""
    cfda_title = record.get("cfda_title") or ""

    # Build domain reference
    domain_ref = ""
    for sector, sector_domains in domains.items():
        domain_ref += f"\n{sector.upper()} domains:\n"
        for d in sector_domains[:15]:  # Limit to avoid token overflow
            domain_ref += f"  - {d['category_name']}: {d['description'][:100]}\n"

    prompt = f"""You are classifying government awards for a research dataset tracking capital flows in space, biotechnology, and energy sectors.

Award description: {description[:500]}
NAICS code: {naics_code} - {naics_desc}
CFDA: {cfda_number} - {cfda_title}

Available domains for each sector:
{domain_ref}

Classify this award:
1. If it relates to SPACE (satellites, launch, spacecraft, astronomy, etc.) → sector: "space"
2. If it relates to BIOTECHNOLOGY (therapeutics, genomics, medical research, etc.) → sector: "bio"
3. If it relates to ENERGY (solar, wind, nuclear, grid, batteries, etc.) → sector: "energy"
4. If it does NOT fit any of these sectors → sector: null

Respond with JSON only:
{{"sector": "space" | "bio" | "energy" | null, "domains": ["domain1"], "confidence": "high" | "medium" | "low", "reasoning": "one sentence"}}"""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        text = response.content[0].text.strip()
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {"sector": None, "domains": [], "confidence": "low", "reasoning": "Failed to parse response"}

    except Exception as e:
        return {"sector": None, "domains": [], "confidence": "low", "reasoning": f"API error: {str(e)}"}


def process_agency(agency, client, domains, dry_run=False, limit=None, sample=None, keyword_only=False, no_filter=False, batch_size=500):
    """Process all needs_llm records for an agency."""
    agency_dir = CLASSIFIED_DIR / agency
    output_dir = NOT_APPLICABLE_DIR / agency

    if not agency_dir.exists():
        print(f"ERROR: Classified directory not found: {agency_dir}")
        return None

    print(f"\n{'='*60}")
    print(f"LLM CLASSIFICATION FOR {agency}")
    print(f"{'='*60}")

    # Collect all needs_llm records
    needs_llm_records = []
    file_sources = {}  # Track which file each record came from

    for filepath in sorted(agency_dir.glob("*.json")):
        with open(filepath) as f:
            data = json.load(f)

        for record in data["records"]:
            if record.get("classification", {}).get("classification_method") == "needs_llm":
                needs_llm_records.append(record)
                file_sources[record["award_id"]] = filepath.name

    print(f"Total records needing LLM: {len(needs_llm_records):,}")

    # Pre-filter by keywords (unless --no-filter is set)
    if no_filter:
        print(f"[NO FILTER MODE] Sending all records to LLM")
        potentially_relevant = needs_llm_records
        definitely_not_applicable = []
        # Still add hint_sector for records that match keywords
        for record in potentially_relevant:
            is_relevant, hint_sector = is_potentially_relevant(record)
            if is_relevant:
                record["_hint_sector"] = hint_sector
    else:
        potentially_relevant = []
        definitely_not_applicable = []

        for record in needs_llm_records:
            is_relevant, hint_sector = is_potentially_relevant(record)
            if is_relevant:
                record["_hint_sector"] = hint_sector
                potentially_relevant.append(record)
            else:
                definitely_not_applicable.append(record)

        print(f"Potentially relevant (keywords): {len(potentially_relevant):,}")
        print(f"Definitely not applicable: {len(definitely_not_applicable):,}")

    if dry_run:
        print(f"\n[DRY RUN] Would process {len(potentially_relevant):,} records with LLM")
        print(f"[DRY RUN] Would save {len(definitely_not_applicable):,} to not_applicable/")

        # Show sample of each
        print(f"\nSample potentially relevant:")
        for r in potentially_relevant[:3]:
            print(f"  - {r.get('description', '')[:80]}...")

        print(f"\nSample not applicable:")
        for r in definitely_not_applicable[:3]:
            print(f"  - {r.get('description', '')[:80]}...")

        return None

    # Keyword-only mode: classify by keywords without LLM
    if keyword_only:
        print(f"\n[KEYWORD-ONLY MODE] Classifying {len(potentially_relevant):,} records by keywords...")
        output_dir.mkdir(parents=True, exist_ok=True)

        classified = defaultdict(list)  # sector -> records

        for record in potentially_relevant:
            hint_sector = record.get("_hint_sector")
            if hint_sector:
                record["classification"] = {
                    "sector": hint_sector,
                    "domains": [f"{hint_sector}_general"],
                    "confidence": "low",
                    "classification_method": "keyword",
                    "reasoning": "Classified by keyword match (no LLM verification)",
                }
                classified[hint_sector].append(record)

        # Save not_applicable records
        not_applicable_path = output_dir / f"{agency}_not_applicable.json"
        with open(not_applicable_path, 'w') as f:
            json.dump({
                "metadata": {
                    "agency": agency,
                    "generated_at": datetime.now().isoformat(),
                    "total_records": len(definitely_not_applicable),
                    "keyword_filtered": len(definitely_not_applicable),
                    "llm_filtered": 0,
                    "mode": "keyword_only",
                },
                "records": definitely_not_applicable
            }, f, indent=2)

        print(f"\nSaved {len(definitely_not_applicable):,} not_applicable records to {not_applicable_path}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY FOR {agency} (KEYWORD-ONLY MODE)")
        print(f"{'='*60}")
        print(f"Classified by keyword:")
        for sector, records in classified.items():
            print(f"  {sector}: {len(records):,}")
        print(f"Not applicable: {len(definitely_not_applicable):,}")

        return {
            "classified": dict(classified),
            "not_applicable": len(definitely_not_applicable),
            "mode": "keyword_only",
        }

    # Apply limit/sample
    if sample and len(potentially_relevant) > sample:
        import random
        potentially_relevant = random.sample(potentially_relevant, sample)
        print(f"Sampling {sample} records for LLM classification")

    if limit:
        potentially_relevant = potentially_relevant[:limit]
        print(f"Limiting to {limit} records")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for checkpoint to resume from
    checkpoint_path = output_dir / f"{agency}_checkpoint.json"
    start_index = 0
    classified = defaultdict(list)  # sector -> records
    not_applicable_llm = []

    if checkpoint_path.exists():
        print(f"\nFound checkpoint, resuming...")
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
        start_index = checkpoint.get("processed_count", 0)
        classified = defaultdict(list, {k: v for k, v in checkpoint.get("classified", {}).items()})
        not_applicable_llm = checkpoint.get("not_applicable_llm", [])
        print(f"  Resuming from record {start_index:,}")

    # Process with LLM
    print(f"\nProcessing {len(potentially_relevant):,} records with LLM...", flush=True)
    print(f"Checkpoint will save every {batch_size:,} records", flush=True)

    for i, record in enumerate(potentially_relevant):
        # Skip already processed records
        if i < start_index:
            continue

        if i > 0 and i % 100 == 0:
            print(f"  Processed {i:,}/{len(potentially_relevant):,}", flush=True)

        result = classify_with_llm(client, record, domains)

        record["classification"] = {
            "sector": result.get("sector"),
            "domains": result.get("domains", []),
            "confidence": result.get("confidence", "low"),
            "classification_method": "llm",
            "reasoning": result.get("reasoning", ""),
        }

        sector = result.get("sector")
        # Handle both JSON null and string "null"
        if sector and sector != "null":
            classified[sector].append(record)
        else:
            not_applicable_llm.append(record)

        # Save checkpoint every batch_size records
        if (i + 1) % batch_size == 0:
            with open(checkpoint_path, 'w') as f:
                json.dump({
                    "processed_count": i + 1,
                    "classified": dict(classified),
                    "not_applicable_llm": not_applicable_llm,
                    "saved_at": datetime.now().isoformat(),
                }, f)
            print(f"  [Checkpoint saved at {i + 1:,}]", flush=True)

        # Rate limiting
        time.sleep(0.05)  # ~20 req/sec

    # Remove checkpoint after successful completion
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    # Combine all not_applicable
    all_not_applicable = definitely_not_applicable + not_applicable_llm

    # Save not_applicable records
    not_applicable_path = output_dir / f"{agency}_not_applicable.json"
    with open(not_applicable_path, 'w') as f:
        json.dump({
            "metadata": {
                "agency": agency,
                "generated_at": datetime.now().isoformat(),
                "total_records": len(all_not_applicable),
                "keyword_filtered": len(definitely_not_applicable),
                "llm_filtered": len(not_applicable_llm),
            },
            "records": all_not_applicable
        }, f, indent=2)

    print(f"\nSaved {len(all_not_applicable):,} not_applicable records to {not_applicable_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY FOR {agency}")
    print(f"{'='*60}")
    print(f"Records processed with LLM: {len(potentially_relevant):,}")
    print(f"Classified to sector:")
    for sector, records in classified.items():
        print(f"  {sector}: {len(records):,}")
    print(f"Not applicable (LLM): {len(not_applicable_llm):,}")
    print(f"Not applicable (keyword filter): {len(definitely_not_applicable):,}")
    print(f"Total not applicable: {len(all_not_applicable):,}")

    return {
        "classified": dict(classified),
        "not_applicable": len(all_not_applicable),
    }


def main():
    parser = argparse.ArgumentParser(description="LLM classification for ambiguous awards")
    parser.add_argument("--agency", required=True, choices=["NASA", "DoE", "HHS", "NSF", "DoD"],
                        help="Agency to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without calling LLM")
    parser.add_argument("--limit", type=int,
                        help="Limit number of records to process")
    parser.add_argument("--sample", type=int,
                        help="Random sample of records to process")
    parser.add_argument("--keyword-only", action="store_true",
                        help="Use keyword filtering only (no LLM calls) - useful for large datasets like DoD")
    parser.add_argument("--no-filter", action="store_true",
                        help="Skip keyword filtering - send ALL needs_llm records to LLM")
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Save checkpoint every N records (default: 500)")

    args = parser.parse_args()

    # Check API key and package
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not args.dry_run and not args.keyword_only:
        if not ANTHROPIC_AVAILABLE:
            print("ERROR: anthropic package not installed.")
            print("Install with: pip3 install anthropic --user")
            print("Or use --dry-run to see what would be processed")
            print("Or use --keyword-only to classify by keywords without LLM")
            exit(1)
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY environment variable not set")
            print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
            exit(1)

    print("USASpending LLM Classifier")
    print("="*60)

    # Load domains
    print("Loading domain definitions...")
    domains = load_domains()
    for sector, domain_list in domains.items():
        print(f"  {sector}: {len(domain_list)} domains")

    # Initialize client
    client = None
    if not args.dry_run:
        client = anthropic.Anthropic(api_key=api_key)

    # Process agency
    result = process_agency(
        args.agency,
        client,
        domains,
        dry_run=args.dry_run,
        limit=args.limit,
        sample=args.sample,
        keyword_only=args.keyword_only,
        no_filter=args.no_filter,
        batch_size=args.batch_size
    )

    if result:
        print(f"\n✓ Complete")


if __name__ == "__main__":
    main()
