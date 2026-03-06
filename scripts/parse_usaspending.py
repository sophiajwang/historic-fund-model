#!/usr/bin/env python3
"""
Parse and normalize USASpending CSV files into JSON.
Step 2.2 of the government spending pipeline.

Usage:
    python3 scripts/parse_usaspending.py --agency NASA
    python3 scripts/parse_usaspending.py --agency NASA --dry-run
    python3 scripts/parse_usaspending.py --agency NASA --year 2023
"""

import argparse
import csv
import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "usaspending"
OUTPUT_DIR = DATA_DIR / "normalized"

# Agency codes mapping
AGENCY_CODES = {
    "NASA": "080",
    "DoE": "089",
    "DoD": "097",
    "HHS": "075",
    "NSF": "049",
}

# Columns to extract from contracts
CONTRACT_COLUMNS = {
    "award_id": "contract_award_unique_key",
    "award_id_piid": "award_id_piid",
    "fiscal_year": "action_date_fiscal_year",
    "awarding_agency": "awarding_agency_name",
    "awarding_sub_agency": "awarding_sub_agency_name",
    "naics_code": "naics_code",
    "naics_description": "naics_description",
    "description": "transaction_description",
    "description_base": "prime_award_base_transaction_description",
    "recipient_name": "recipient_name",
    "recipient_uei": "recipient_uei",
    "recipient_parent_name": "recipient_parent_name",
    "obligation": "federal_action_obligation",
    "total_outlayed": "total_outlayed_amount_for_overall_award",
    "period_start": "period_of_performance_start_date",
    "period_end": "period_of_performance_current_end_date",
    "recipient_country": "recipient_country_code",
    "is_federal_recipient": "us_federal_government",
}

# Columns to extract from assistance
ASSISTANCE_COLUMNS = {
    "award_id": "assistance_award_unique_key",
    "award_id_fain": "award_id_fain",
    "fiscal_year": "action_date_fiscal_year",
    "awarding_agency": "awarding_agency_name",
    "awarding_sub_agency": "awarding_sub_agency_name",
    "cfda_number": "cfda_number",
    "cfda_title": "cfda_title",
    "description": "transaction_description",
    "description_base": "prime_award_base_transaction_description",
    "recipient_name": "recipient_name",
    "recipient_uei": "recipient_uei",
    "recipient_parent_name": "recipient_parent_name",
    "obligation": "federal_action_obligation",
    "total_outlayed": "total_outlayed_amount_for_overall_award",
    "period_start": "period_of_performance_start_date",
    "period_end": "period_of_performance_current_end_date",
    "recipient_country": "recipient_country_code",
    "assistance_type_code": "assistance_type_code",
    "assistance_type_description": "assistance_type_description",
    "business_types_code": "business_types_code",
}


def parse_amount(value):
    """Parse a dollar amount string to float."""
    if not value or value.strip() == "":
        return 0.0
    try:
        # Remove any currency symbols or commas
        cleaned = value.replace("$", "").replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def is_federal_recipient(row, award_type):
    """Check if the recipient is a federal entity (to be filtered out)."""
    if award_type == "contract":
        return row.get("us_federal_government", "").lower() == "t"
    else:
        # For assistance, check business_types_code or recipient name patterns
        # Federal recipients are rare in assistance data based on our test
        recipient = (row.get("recipient_name") or "").upper()
        federal_patterns = ["UNITED STATES OF AMERICA", "U.S. DEPARTMENT", "FEDERAL GOVERNMENT"]
        return any(p in recipient for p in federal_patterns)


def extract_contract_record(row):
    """Extract normalized record from a contracts CSV row."""
    description = row.get("transaction_description") or row.get("prime_award_base_transaction_description") or ""

    return {
        "award_id": row.get("contract_award_unique_key", ""),
        "award_id_secondary": row.get("award_id_piid", ""),
        "award_type": "contract",
        "fiscal_year": int(row.get("action_date_fiscal_year") or 0),
        "awarding_agency": row.get("awarding_agency_name", ""),
        "awarding_sub_agency": row.get("awarding_sub_agency_name", ""),
        "naics_code": row.get("naics_code", ""),
        "naics_description": row.get("naics_description", ""),
        "cfda_number": None,  # Not applicable for contracts
        "cfda_title": None,
        "description": description[:500] if description else "",  # Truncate for storage
        "recipient_name": row.get("recipient_name", ""),
        "recipient_uei": row.get("recipient_uei", ""),
        "recipient_parent_name": row.get("recipient_parent_name", ""),
        "recipient_country": row.get("recipient_country_code", ""),
        "obligation": parse_amount(row.get("federal_action_obligation")),
        "total_outlayed": parse_amount(row.get("total_outlayed_amount_for_overall_award")),
        "period_start": row.get("period_of_performance_start_date", ""),
        "period_end": row.get("period_of_performance_current_end_date", ""),
    }


def extract_assistance_record(row):
    """Extract normalized record from an assistance CSV row."""
    description = row.get("transaction_description") or row.get("prime_award_base_transaction_description") or ""

    return {
        "award_id": row.get("assistance_award_unique_key", ""),
        "award_id_secondary": row.get("award_id_fain", ""),
        "award_type": "assistance",
        "fiscal_year": int(row.get("action_date_fiscal_year") or 0),
        "awarding_agency": row.get("awarding_agency_name", ""),
        "awarding_sub_agency": row.get("awarding_sub_agency_name", ""),
        "naics_code": None,  # Not applicable for assistance
        "naics_description": None,
        "cfda_number": row.get("cfda_number", ""),
        "cfda_title": row.get("cfda_title", ""),
        "description": description[:500] if description else "",
        "recipient_name": row.get("recipient_name", ""),
        "recipient_uei": row.get("recipient_uei", ""),
        "recipient_parent_name": row.get("recipient_parent_name", ""),
        "recipient_country": row.get("recipient_country_code", ""),
        "obligation": parse_amount(row.get("federal_action_obligation")),
        "total_outlayed": parse_amount(row.get("total_outlayed_amount_for_overall_award")),
        "period_start": row.get("period_of_performance_start_date", ""),
        "period_end": row.get("period_of_performance_current_end_date", ""),
        "assistance_type_code": row.get("assistance_type_code", ""),
        "assistance_type_description": row.get("assistance_type_description", ""),
    }


def parse_csv_file(filepath, award_type):
    """Parse a single CSV file and return normalized records."""
    records = []
    stats = {
        "total_rows": 0,
        "federal_filtered": 0,
        "zero_obligation": 0,
        "kept": 0,
    }

    extract_func = extract_contract_record if award_type == "contract" else extract_assistance_record

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["total_rows"] += 1

            # Filter out federal recipients
            if is_federal_recipient(row, award_type):
                stats["federal_filtered"] += 1
                continue

            record = extract_func(row)

            # Skip records with zero or missing obligation
            if record["obligation"] == 0.0:
                stats["zero_obligation"] += 1
                continue

            records.append(record)
            stats["kept"] += 1

    return records, stats


def find_csv_files(agency_dir, year=None, award_type=None):
    """Find CSV files for an agency, optionally filtered by year and type."""
    files = {"contracts": [], "assistance": []}

    # Handle regular CSV files
    for filepath in agency_dir.glob("*.csv"):
        if filepath.name.startswith("."):
            continue

        filename = filepath.name

        # Parse year from filename (e.g., FY2023_080_Contracts_Full_...)
        if filename.startswith("FY"):
            file_year = int(filename[2:6])
            if year and file_year != year:
                continue

        if "Contracts" in filename:
            if award_type is None or award_type == "contracts":
                files["contracts"].append(filepath)
        elif "Assistance" in filename:
            if award_type is None or award_type == "assistance":
                files["assistance"].append(filepath)

    # Handle subdirectories (for DoD split files)
    for subdir in agency_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("."):
            # Check if this is a contracts folder (e.g., FY2023_097_Contracts_Full_...)
            if "Contracts" in subdir.name:
                if award_type is None or award_type == "contracts":
                    # Parse year
                    if subdir.name.startswith("FY"):
                        file_year = int(subdir.name[2:6])
                        if year and file_year != year:
                            continue

                    # Add all CSV files in the subdirectory
                    for csv_file in subdir.glob("*.csv"):
                        files["contracts"].append(csv_file)

    # Sort by filename
    files["contracts"].sort(key=lambda x: x.name)
    files["assistance"].sort(key=lambda x: x.name)

    return files


def parse_agency(agency, year=None, dry_run=False):
    """Parse all files for an agency."""
    agency_dir = DATA_DIR / agency

    if not agency_dir.exists():
        print(f"ERROR: Agency directory not found: {agency_dir}")
        return None

    print(f"\n{'='*60}")
    print(f"PARSING {agency}")
    print(f"{'='*60}")

    # Find files
    files = find_csv_files(agency_dir, year=year)

    print(f"Found {len(files['contracts'])} contracts files")
    print(f"Found {len(files['assistance'])} assistance files")

    if dry_run:
        print("\n[DRY RUN] Would process:")
        for f in files['contracts'][:5]:
            print(f"  - {f.name}")
        if len(files['contracts']) > 5:
            print(f"  ... and {len(files['contracts']) - 5} more")
        for f in files['assistance'][:5]:
            print(f"  - {f.name}")
        if len(files['assistance']) > 5:
            print(f"  ... and {len(files['assistance']) - 5} more")
        return None

    # Create output directory
    output_dir = OUTPUT_DIR / agency
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process by fiscal year
    results_by_year = defaultdict(lambda: {"contracts": [], "assistance": []})
    total_stats = {
        "contracts": {"total_rows": 0, "federal_filtered": 0, "zero_obligation": 0, "kept": 0},
        "assistance": {"total_rows": 0, "federal_filtered": 0, "zero_obligation": 0, "kept": 0},
    }

    # Process contracts
    print(f"\nProcessing contracts...")
    for filepath in files["contracts"]:
        print(f"  {filepath.name}...", end=" ", flush=True)
        records, stats = parse_csv_file(filepath, "contract")

        # Group by fiscal year
        for record in records:
            fy = record["fiscal_year"]
            results_by_year[fy]["contracts"].append(record)

        # Aggregate stats
        for key in total_stats["contracts"]:
            total_stats["contracts"][key] += stats[key]

        print(f"kept {stats['kept']:,} / {stats['total_rows']:,}")

    # Process assistance
    print(f"\nProcessing assistance...")
    for filepath in files["assistance"]:
        print(f"  {filepath.name}...", end=" ", flush=True)
        records, stats = parse_csv_file(filepath, "assistance")

        # Group by fiscal year
        for record in records:
            fy = record["fiscal_year"]
            results_by_year[fy]["assistance"].append(record)

        # Aggregate stats
        for key in total_stats["assistance"]:
            total_stats["assistance"][key] += stats[key]

        print(f"kept {stats['kept']:,} / {stats['total_rows']:,}")

    # Write output files by fiscal year
    print(f"\nWriting output files...")
    for fy, data in sorted(results_by_year.items()):
        if fy == 0:
            continue  # Skip records with missing fiscal year

        # Write contracts
        if data["contracts"]:
            output_path = output_dir / f"FY{fy}_contracts.json"
            with open(output_path, 'w') as f:
                json.dump({
                    "metadata": {
                        "agency": agency,
                        "fiscal_year": fy,
                        "award_type": "contracts",
                        "record_count": len(data["contracts"]),
                        "total_obligation": sum(r["obligation"] for r in data["contracts"]),
                        "generated_at": datetime.now().isoformat(),
                    },
                    "records": data["contracts"],
                }, f, indent=2)
            print(f"  {output_path.name}: {len(data['contracts']):,} records")

        # Write assistance
        if data["assistance"]:
            output_path = output_dir / f"FY{fy}_assistance.json"
            with open(output_path, 'w') as f:
                json.dump({
                    "metadata": {
                        "agency": agency,
                        "fiscal_year": fy,
                        "award_type": "assistance",
                        "record_count": len(data["assistance"]),
                        "total_obligation": sum(r["obligation"] for r in data["assistance"]),
                        "generated_at": datetime.now().isoformat(),
                    },
                    "records": data["assistance"],
                }, f, indent=2)
            print(f"  {output_path.name}: {len(data['assistance']):,} records")

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY FOR {agency}")
    print(f"{'='*60}")

    print(f"\nContracts:")
    print(f"  Total rows processed: {total_stats['contracts']['total_rows']:,}")
    print(f"  Federal recipients filtered: {total_stats['contracts']['federal_filtered']:,}")
    print(f"  Zero obligation filtered: {total_stats['contracts']['zero_obligation']:,}")
    print(f"  Records kept: {total_stats['contracts']['kept']:,}")

    print(f"\nAssistance:")
    print(f"  Total rows processed: {total_stats['assistance']['total_rows']:,}")
    print(f"  Federal recipients filtered: {total_stats['assistance']['federal_filtered']:,}")
    print(f"  Zero obligation filtered: {total_stats['assistance']['zero_obligation']:,}")
    print(f"  Records kept: {total_stats['assistance']['kept']:,}")

    total_obligation = sum(
        sum(r["obligation"] for r in data["contracts"]) +
        sum(r["obligation"] for r in data["assistance"])
        for data in results_by_year.values()
    )
    print(f"\nTotal obligation (kept records): ${total_obligation:,.2f}")

    return {
        "agency": agency,
        "fiscal_years": sorted([fy for fy in results_by_year.keys() if fy != 0]),
        "stats": total_stats,
        "total_obligation": total_obligation,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse USASpending CSV files")
    parser.add_argument("--agency", required=True, choices=list(AGENCY_CODES.keys()),
                        help="Agency to process")
    parser.add_argument("--year", type=int, help="Specific fiscal year to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without actually processing")

    args = parser.parse_args()

    print("USASpending CSV Parser")
    print(f"Agency: {args.agency}")
    if args.year:
        print(f"Year: FY{args.year}")
    if args.dry_run:
        print("[DRY RUN MODE]")

    result = parse_agency(args.agency, year=args.year, dry_run=args.dry_run)

    if result:
        print(f"\n✓ Complete. Output written to: {OUTPUT_DIR / args.agency}")


if __name__ == "__main__":
    main()
