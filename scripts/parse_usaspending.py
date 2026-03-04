#!/usr/bin/env python3
"""
Step 2.2: Parse and normalize USASpending CSV files.

Reads raw CSV downloads from data/raw/usaspending/ and extracts relevant columns.
Filters for non-federal recipients only.
Outputs normalized awards to data/processed/awards_normalized.json

Usage:
    python scripts/parse_usaspending.py [--limit N] [--dry-run]
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Project root (relative to scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "usaspending"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Column mappings for contracts CSVs
CONTRACTS_COLUMNS = {
    "award_id": "contract_award_unique_key",
    "fiscal_year": "action_date_fiscal_year",
    "awarding_agency_code": "awarding_agency_code",
    "awarding_agency": "awarding_agency_name",
    "awarding_sub_agency": "awarding_sub_agency_name",
    "award_type": None,  # Will be set to "contract"
    "naics_code": "naics_code",
    "naics_description": "naics_description",
    "award_description": "transaction_description",
    "recipient_name": "recipient_name",
    "recipient_uei": "recipient_uei",
    "recipient_parent_name": "recipient_parent_name",
    "recipient_state": "recipient_state_code",
    "recipient_country": "recipient_country_code",
    "total_obligated_amount": "total_dollars_obligated",
    "total_outlayed_amount": "total_outlayed_amount_for_overall_award",
    "federal_action_obligation": "federal_action_obligation",
    "action_date": "action_date",
    "period_of_performance_start": "period_of_performance_start_date",
    "period_of_performance_end": "period_of_performance_current_end_date",
    "product_service_code": "product_or_service_code",
    "product_service_description": "product_or_service_code_description",
}

# Column mappings for assistance (grants, loans, etc.) CSVs
ASSISTANCE_COLUMNS = {
    "award_id": "assistance_award_unique_key",
    "fiscal_year": "action_date_fiscal_year",
    "awarding_agency_code": "awarding_agency_code",
    "awarding_agency": "awarding_agency_name",
    "awarding_sub_agency": "awarding_sub_agency_name",
    "award_type": "assistance_type_description",
    "naics_code": None,  # Assistance uses CFDA, not NAICS
    "naics_description": None,
    "cfda_number": "cfda_number",
    "cfda_title": "cfda_title",
    "award_description": "transaction_description",
    "recipient_name": "recipient_name",
    "recipient_uei": "recipient_uei",
    "recipient_parent_name": "recipient_parent_name",
    "recipient_state": "recipient_state_code",
    "recipient_country": "recipient_country_code",
    "total_obligated_amount": "total_obligated_amount",
    "total_outlayed_amount": "total_outlayed_amount_for_overall_award",
    "federal_action_obligation": "federal_action_obligation",
    "action_date": "action_date",
    "period_of_performance_start": "period_of_performance_start_date",
    "period_of_performance_end": "period_of_performance_current_end_date",
    "business_types": "business_types_description",
}

# Agency code to name mapping for consistent naming
AGENCY_CODE_MAP = {
    "080": "NASA",
    "089": "DOE",
    "075": "NIH",  # Part of HHS
    "097": "DOD",
    "049": "NSF",
    "013": "USDA",
    "068": "EPA",
    "014": "NOAA",  # Part of DOC
}

# Federal recipient indicators (to exclude)
FEDERAL_RECIPIENT_PATTERNS = [
    r"^FEDERAL\b",
    r"^U\.?S\.?\s+(GOVERNMENT|DEPT|DEPARTMENT)",
    r"^DEPARTMENT\s+OF",
    r"^UNITED\s+STATES\b",
    r"\bFEDERAL\s+GOVERNMENT\b",
]


def detect_file_type(filepath: Path) -> str:
    """Detect if file is contracts or assistance based on filename."""
    name = filepath.name.lower()
    if "contracts" in name:
        return "contracts"
    elif "assistance" in name:
        return "assistance"
    else:
        # Check first line for column hints
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            header = f.readline().lower()
            if "contract_award_unique_key" in header:
                return "contracts"
            elif "assistance_award_unique_key" in header:
                return "assistance"
    return "unknown"


def extract_agency_from_filename(filepath: Path) -> str:
    """Extract agency code from filename like FY2008_080_Contracts..."""
    name = filepath.name
    match = re.search(r'FY\d{4}_(\d{3})_', name)
    if match:
        code = match.group(1)
        return AGENCY_CODE_MAP.get(code, code)
    return "UNKNOWN"


def extract_fiscal_year_from_filename(filepath: Path) -> int:
    """Extract fiscal year from filename."""
    name = filepath.name
    match = re.search(r'FY(\d{4})', name)
    if match:
        return int(match.group(1))
    return 0


def is_federal_recipient(recipient_name: str) -> bool:
    """Check if recipient appears to be a federal entity."""
    if not recipient_name:
        return False
    name_upper = recipient_name.upper().strip()
    for pattern in FEDERAL_RECIPIENT_PATTERNS:
        if re.search(pattern, name_upper):
            return True
    return False


def parse_amount(value: str) -> float:
    """Parse dollar amount string to float."""
    if not value or value.strip() == "":
        return 0.0
    try:
        # Remove any non-numeric characters except minus and decimal
        cleaned = re.sub(r'[^\d.\-]', '', str(value))
        return float(cleaned) if cleaned else 0.0
    except (ValueError, TypeError):
        return 0.0


def parse_csv_file(filepath: Path, file_type: str, limit: int = None) -> list:
    """Parse a single CSV file and return normalized records."""
    records = []
    column_map = CONTRACTS_COLUMNS if file_type == "contracts" else ASSISTANCE_COLUMNS

    agency_from_file = extract_agency_from_filename(filepath)
    fy_from_file = extract_fiscal_year_from_filename(filepath)

    print(f"  Parsing {filepath.name} ({file_type}, {agency_from_file} FY{fy_from_file})...")

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            row_count = 0
            skipped_federal = 0

            for row in reader:
                row_count += 1
                if limit and row_count > limit:
                    break

                # Get recipient name and filter federal recipients
                recipient_name = row.get(column_map.get("recipient_name", ""), "")
                if is_federal_recipient(recipient_name):
                    skipped_federal += 1
                    continue

                # Build normalized record
                record = {
                    "source_file": filepath.name,
                    "file_type": file_type,
                }

                # Map columns
                for our_field, csv_field in column_map.items():
                    if csv_field is None:
                        if our_field == "award_type" and file_type == "contracts":
                            record[our_field] = "contract"
                        else:
                            record[our_field] = None
                    else:
                        record[our_field] = row.get(csv_field, "")

                # Parse amounts
                for amount_field in ["total_obligated_amount", "total_outlayed_amount", "federal_action_obligation"]:
                    if amount_field in record:
                        record[amount_field] = parse_amount(record[amount_field])

                # Parse fiscal year
                if record.get("fiscal_year"):
                    try:
                        record["fiscal_year"] = int(record["fiscal_year"])
                    except ValueError:
                        record["fiscal_year"] = fy_from_file
                else:
                    record["fiscal_year"] = fy_from_file

                # Add agency info if not in record
                if not record.get("awarding_agency"):
                    record["awarding_agency"] = agency_from_file

                records.append(record)

            print(f"    Rows processed: {row_count}, Federal recipients skipped: {skipped_federal}, Records kept: {len(records)}")

    except Exception as e:
        print(f"  ERROR parsing {filepath.name}: {e}")

    return records


def get_csv_files(raw_dir: Path) -> list:
    """Get all CSV files from raw directory."""
    csv_files = []
    for f in raw_dir.iterdir():
        if f.suffix.lower() == '.csv' and not f.name.startswith('.'):
            csv_files.append(f)
    return sorted(csv_files, key=lambda x: x.name)


def generate_summary(records: list) -> dict:
    """Generate summary statistics from parsed records."""
    summary = {
        "total_records": len(records),
        "by_file_type": defaultdict(int),
        "by_agency": defaultdict(int),
        "by_fiscal_year": defaultdict(int),
        "total_obligated": 0.0,
        "total_outlayed": 0.0,
    }

    for r in records:
        summary["by_file_type"][r.get("file_type", "unknown")] += 1
        summary["by_agency"][r.get("awarding_agency", "unknown")] += 1
        summary["by_fiscal_year"][str(r.get("fiscal_year", "unknown"))] += 1
        summary["total_obligated"] += r.get("total_obligated_amount", 0) or 0
        summary["total_outlayed"] += r.get("total_outlayed_amount", 0) or 0

    # Convert defaultdicts to regular dicts for JSON serialization
    summary["by_file_type"] = dict(summary["by_file_type"])
    summary["by_agency"] = dict(summary["by_agency"])
    summary["by_fiscal_year"] = dict(summary["by_fiscal_year"])

    return summary


def main():
    parser = argparse.ArgumentParser(description="Parse USASpending CSV files")
    parser.add_argument("--limit", type=int, help="Limit rows per file (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Parse but don't write output")
    parser.add_argument("--file", type=str, help="Parse single file only")
    args = parser.parse_args()

    print("=" * 60)
    print("USASpending CSV Parser - Step 2.2")
    print("=" * 60)

    # Check raw directory exists
    if not RAW_DIR.exists():
        print(f"ERROR: Raw data directory not found: {RAW_DIR}")
        sys.exit(1)

    # Get CSV files
    if args.file:
        csv_files = [RAW_DIR / args.file]
        if not csv_files[0].exists():
            print(f"ERROR: File not found: {csv_files[0]}")
            sys.exit(1)
    else:
        csv_files = get_csv_files(RAW_DIR)

    print(f"\nFound {len(csv_files)} CSV files in {RAW_DIR}")

    if not csv_files:
        print("No CSV files found. Download data first (Step 2.1).")
        sys.exit(1)

    # Parse all files
    all_records = []
    for filepath in csv_files:
        file_type = detect_file_type(filepath)
        if file_type == "unknown":
            print(f"  Skipping {filepath.name} (unknown file type)")
            continue

        records = parse_csv_file(filepath, file_type, limit=args.limit)
        all_records.extend(records)

    print(f"\n{'=' * 60}")
    print(f"TOTAL RECORDS PARSED: {len(all_records)}")

    # Generate summary
    summary = generate_summary(all_records)
    print(f"\nSummary:")
    print(f"  By file type: {summary['by_file_type']}")
    print(f"  By agency: {summary['by_agency']}")
    print(f"  By fiscal year: {dict(sorted(summary['by_fiscal_year'].items()))}")
    print(f"  Total obligated: ${summary['total_obligated']:,.2f}")
    print(f"  Total outlayed: ${summary['total_outlayed']:,.2f}")

    # Write output
    if not args.dry_run:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        output_file = OUTPUT_DIR / "awards_normalized.json"
        print(f"\nWriting {len(all_records)} records to {output_file}...")

        with open(output_file, 'w') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "summary": summary,
                "awards": all_records,
            }, f, indent=2)

        print(f"Done! Output saved to {output_file}")
    else:
        print("\n[DRY RUN] No output written.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
