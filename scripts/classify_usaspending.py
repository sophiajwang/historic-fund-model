#!/usr/bin/env python3
"""
Classify USASpending awards by sector and domain.
Step 2.3 of the government spending pipeline.

Applies NAICS mappings (contracts) and CFDA mappings (assistance)
to assign sector and domain to each award.

Usage:
    python3 scripts/classify_usaspending.py --agency NASA
    python3 scripts/classify_usaspending.py --agency NASA --dry-run
    python3 scripts/classify_usaspending.py --all
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
NORMALIZED_DIR = DATA_DIR / "usaspending" / "normalized"
CLASSIFIED_DIR = DATA_DIR / "usaspending" / "classified"

# Load mapping files
def load_mappings():
    """Load NAICS and CFDA mapping files."""
    naics_path = DATA_DIR / "naics-to-domain-mapping.json"
    cfda_path = DATA_DIR / "cfda-to-domain-mapping.json"

    with open(naics_path) as f:
        naics_raw = json.load(f)

    with open(cfda_path) as f:
        cfda_mapping = json.load(f)

    # Flatten NAICS mapping: sector -> naics -> mapping becomes naics -> {sector, ...mapping}
    naics_mapping = {"mappings": {}}
    for sector in ["space", "bio", "energy"]:
        if sector in naics_raw:
            for naics_code, mapping in naics_raw[sector].items():
                confidence = mapping.get("confidence", "medium")
                # Handle excluded codes
                if confidence == "exclude":
                    naics_mapping["mappings"][naics_code] = {
                        "sector": None,
                        "domains": [],
                        "confidence": "exclude",
                        "description": mapping.get("description", ""),
                        "note": mapping.get("note", ""),
                    }
                else:
                    naics_mapping["mappings"][naics_code] = {
                        "sector": sector,
                        "domains": mapping.get("domains", []),
                        "confidence": confidence,
                        "description": mapping.get("description", ""),
                    }

    return naics_mapping, cfda_mapping


# Agency to default sector mapping
AGENCY_SECTORS = {
    "NASA": "space",
    "DoE": "energy",
    "HHS": "bio",
    "NSF": None,  # Multi-sector, relies on CFDA/NAICS
    "DoD": None,  # Multi-sector, relies on CFDA/NAICS
}


def classify_contract(record, naics_mapping, agency):
    """Classify a contract record using NAICS code."""
    naics_code = record.get("naics_code", "")

    # Check if NAICS code is in mapping
    if naics_code and naics_code in naics_mapping.get("mappings", {}):
        mapping = naics_mapping["mappings"][naics_code]

        # Handle excluded codes
        if mapping.get("confidence") == "exclude":
            return {
                "sector": None,
                "domains": [],
                "confidence": "high",
                "classification_method": "excluded",
                "classification_code": naics_code,
                "exclusion_reason": mapping.get("note", "Out of scope"),
            }

        return {
            "sector": mapping.get("sector"),
            "domains": mapping.get("domains", []),
            "confidence": mapping.get("confidence", "low"),
            "classification_method": "naics",
            "classification_code": naics_code,
        }

    # Fall back to agency default
    default_sector = AGENCY_SECTORS.get(agency)
    if default_sector:
        return {
            "sector": default_sector,
            "domains": [f"{default_sector}_general"],
            "confidence": "medium",
            "classification_method": "agency_default",
            "classification_code": naics_code,
        }

    # Needs LLM classification
    return {
        "sector": None,
        "domains": [],
        "confidence": "low",
        "classification_method": "needs_llm",
        "classification_code": naics_code,
    }


def classify_assistance(record, cfda_mapping, agency):
    """Classify an assistance record using CFDA code."""
    cfda_number = record.get("cfda_number", "")

    # Check if CFDA code is in mapping
    if cfda_number and cfda_number in cfda_mapping.get("mappings", {}):
        mapping = cfda_mapping["mappings"][cfda_number]

        # Check if excluded
        if mapping.get("sector") is None and not mapping.get("domains"):
            if "EXCLUDE" in mapping.get("notes", ""):
                return {
                    "sector": None,
                    "domains": [],
                    "confidence": "high",
                    "classification_method": "excluded",
                    "classification_code": cfda_number,
                    "exclusion_reason": mapping.get("notes", ""),
                }

        # Check if needs LLM
        if mapping.get("confidence") == "low" or "LLM" in mapping.get("notes", ""):
            return {
                "sector": mapping.get("sector"),
                "domains": mapping.get("domains", []),
                "confidence": "low",
                "classification_method": "needs_llm",
                "classification_code": cfda_number,
            }

        return {
            "sector": mapping.get("sector"),
            "domains": mapping.get("domains", []),
            "confidence": mapping.get("confidence", "medium"),
            "classification_method": "cfda",
            "classification_code": cfda_number,
        }

    # Fall back to agency default
    default_sector = AGENCY_SECTORS.get(agency)
    if default_sector:
        return {
            "sector": default_sector,
            "domains": [f"{default_sector}_general"],
            "confidence": "medium",
            "classification_method": "agency_default",
            "classification_code": cfda_number,
        }

    # Needs LLM classification
    return {
        "sector": None,
        "domains": [],
        "confidence": "low",
        "classification_method": "needs_llm",
        "classification_code": cfda_number,
    }


def classify_agency(agency, naics_mapping, cfda_mapping, dry_run=False):
    """Classify all records for an agency."""
    agency_dir = NORMALIZED_DIR / agency
    output_dir = CLASSIFIED_DIR / agency

    if not agency_dir.exists():
        print(f"ERROR: Normalized directory not found: {agency_dir}")
        return None

    print(f"\n{'='*60}")
    print(f"CLASSIFYING {agency}")
    print(f"{'='*60}")

    # Find all JSON files
    contracts_files = sorted(agency_dir.glob("*_contracts.json"))
    assistance_files = sorted(agency_dir.glob("*_assistance.json"))

    print(f"Found {len(contracts_files)} contracts files")
    print(f"Found {len(assistance_files)} assistance files")

    if dry_run:
        print("\n[DRY RUN] Would classify files above")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    # Stats tracking
    stats = {
        "contracts": defaultdict(int),
        "assistance": defaultdict(int),
    }

    # Process contracts
    print(f"\nClassifying contracts...")
    for filepath in contracts_files:
        print(f"  {filepath.name}...", end=" ", flush=True)

        with open(filepath) as f:
            data = json.load(f)

        classified_records = []
        for record in data["records"]:
            classification = classify_contract(record, naics_mapping, agency)
            record["classification"] = classification
            classified_records.append(record)

            # Track stats
            stats["contracts"][classification["classification_method"]] += 1
            if classification["sector"]:
                stats["contracts"][f"sector_{classification['sector']}"] += 1

        # Write output
        output_path = output_dir / filepath.name
        data["records"] = classified_records
        data["metadata"]["classified_at"] = datetime.now().isoformat()
        data["metadata"]["classification_stats"] = dict(stats["contracts"])

        with open(output_path, 'w') as f:
            json.dump(data, f)

        print(f"done")

    # Process assistance
    print(f"\nClassifying assistance...")
    for filepath in assistance_files:
        print(f"  {filepath.name}...", end=" ", flush=True)

        with open(filepath) as f:
            data = json.load(f)

        classified_records = []
        for record in data["records"]:
            classification = classify_assistance(record, cfda_mapping, agency)
            record["classification"] = classification
            classified_records.append(record)

            # Track stats
            stats["assistance"][classification["classification_method"]] += 1
            if classification["sector"]:
                stats["assistance"][f"sector_{classification['sector']}"] += 1

        # Write output
        output_path = output_dir / filepath.name
        data["records"] = classified_records
        data["metadata"]["classified_at"] = datetime.now().isoformat()
        data["metadata"]["classification_stats"] = dict(stats["assistance"])

        with open(output_path, 'w') as f:
            json.dump(data, f)

        print(f"done")

    # Print summary
    print(f"\n{'='*60}")
    print(f"CLASSIFICATION SUMMARY FOR {agency}")
    print(f"{'='*60}")

    print(f"\nContracts:")
    for method, count in sorted(stats["contracts"].items()):
        if not method.startswith("sector_"):
            print(f"  {method}: {count:,}")

    print(f"\n  By sector:")
    for method, count in sorted(stats["contracts"].items()):
        if method.startswith("sector_"):
            print(f"    {method.replace('sector_', '')}: {count:,}")

    print(f"\nAssistance:")
    for method, count in sorted(stats["assistance"].items()):
        if not method.startswith("sector_"):
            print(f"  {method}: {count:,}")

    print(f"\n  By sector:")
    for method, count in sorted(stats["assistance"].items()):
        if method.startswith("sector_"):
            print(f"    {method.replace('sector_', '')}: {count:,}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Classify USASpending awards")
    parser.add_argument("--agency", choices=["NASA", "DoE", "HHS", "NSF", "DoD"],
                        help="Agency to process")
    parser.add_argument("--all", action="store_true", help="Process all agencies")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without actually processing")

    args = parser.parse_args()

    if not args.agency and not args.all:
        parser.error("Either --agency or --all is required")

    print("USASpending Award Classifier")
    print("="*60)

    # Load mappings
    print("Loading NAICS and CFDA mappings...")
    naics_mapping, cfda_mapping = load_mappings()
    print(f"  NAICS mappings: {len(naics_mapping.get('mappings', {}))}")
    print(f"  CFDA mappings: {len(cfda_mapping.get('mappings', {}))}")

    agencies = ["NASA", "DoE", "HHS", "NSF", "DoD"] if args.all else [args.agency]

    all_stats = {}
    for agency in agencies:
        stats = classify_agency(agency, naics_mapping, cfda_mapping, dry_run=args.dry_run)
        if stats:
            all_stats[agency] = stats

    if all_stats:
        print(f"\n{'='*60}")
        print("OVERALL SUMMARY")
        print(f"{'='*60}")

        total_classified = 0
        total_needs_llm = 0
        total_excluded = 0

        for agency, stats in all_stats.items():
            contracts_llm = stats["contracts"].get("needs_llm", 0)
            assistance_llm = stats["assistance"].get("needs_llm", 0)
            assistance_excluded = stats["assistance"].get("excluded", 0)

            contracts_total = sum(v for k, v in stats["contracts"].items() if not k.startswith("sector_"))
            assistance_total = sum(v for k, v in stats["assistance"].items() if not k.startswith("sector_"))

            total_classified += contracts_total + assistance_total
            total_needs_llm += contracts_llm + assistance_llm
            total_excluded += assistance_excluded

            print(f"\n{agency}:")
            print(f"  Contracts: {contracts_total:,} ({contracts_llm:,} need LLM)")
            print(f"  Assistance: {assistance_total:,} ({assistance_llm:,} need LLM, {assistance_excluded:,} excluded)")

        print(f"\nTotals:")
        print(f"  Total records: {total_classified:,}")
        print(f"  Need LLM classification: {total_needs_llm:,} ({100*total_needs_llm/total_classified:.1f}%)")
        print(f"  Excluded (not R&D): {total_excluded:,}")

        print(f"\n✓ Complete. Output written to: {CLASSIFIED_DIR}")


if __name__ == "__main__":
    main()
