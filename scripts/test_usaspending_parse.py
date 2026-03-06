#!/usr/bin/env python3
"""
Test script to explore USASpending CSV structure before building full parser.
Run this first to understand data schema, edge cases, and validate assumptions.
"""

import csv
import os
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent / "data" / "usaspending"

def sample_csv(filepath, n_rows=5):
    """Read first n rows from a CSV and return as list of dicts."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = []
        for i, row in enumerate(reader):
            if i >= n_rows:
                break
            rows.append(row)
        return reader.fieldnames, rows

def analyze_contracts(filepath, sample_size=1000):
    """Analyze contracts CSV structure and key fields."""
    print(f"\n{'='*60}")
    print(f"ANALYZING CONTRACTS: {filepath.name}")
    print(f"{'='*60}")

    fieldnames, sample_rows = sample_csv(filepath, n_rows=sample_size)

    # Key columns we need per spec
    key_cols = [
        'contract_award_unique_key',
        'award_id_piid',
        'action_date_fiscal_year',
        'awarding_agency_code',
        'awarding_agency_name',
        'awarding_sub_agency_code',
        'awarding_sub_agency_name',
        'naics_code',
        'naics_description',
        'transaction_description',
        'prime_award_base_transaction_description',
        'recipient_name',
        'recipient_uei',
        'recipient_parent_name',
        'total_dollars_obligated',
        'total_outlayed_amount_for_overall_award',
        'federal_action_obligation',
        'period_of_performance_start_date',
        'period_of_performance_current_end_date',
        'recipient_country_code',
        'business_types_code',  # For filtering federal recipients
    ]

    print(f"\nTotal columns in file: {len(fieldnames)}")

    # Check which key columns exist
    print(f"\n--- Key Column Check ---")
    missing = []
    for col in key_cols:
        if col in fieldnames:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} (MISSING)")
            missing.append(col)

    if missing:
        # Try to find similar columns
        print(f"\n--- Searching for similar columns ---")
        for m in missing:
            similar = [f for f in fieldnames if m.split('_')[0] in f.lower()]
            if similar:
                print(f"  {m} -> possible matches: {similar[:5]}")

    # Sample values for key fields
    print(f"\n--- Sample Values (first 3 rows) ---")
    for row in sample_rows[:3]:
        print(f"\n  Award: {row.get('contract_award_unique_key', 'N/A')[:50]}")
        print(f"  FY: {row.get('action_date_fiscal_year', 'N/A')}")
        print(f"  Agency: {row.get('awarding_agency_name', 'N/A')}")
        print(f"  Sub-agency: {row.get('awarding_sub_agency_name', 'N/A')}")
        print(f"  NAICS: {row.get('naics_code', 'N/A')} - {row.get('naics_description', 'N/A')[:50]}")
        print(f"  Recipient: {row.get('recipient_name', 'N/A')[:50]}")
        print(f"  Obligated: ${row.get('total_dollars_obligated', 'N/A')}")
        print(f"  Description: {row.get('transaction_description', 'N/A')[:80]}...")

    # NAICS code distribution
    print(f"\n--- NAICS Code Distribution (top 10 in sample) ---")
    naics_counts = Counter(row.get('naics_code', '') for row in sample_rows)
    for code, count in naics_counts.most_common(10):
        desc = next((r.get('naics_description', '') for r in sample_rows if r.get('naics_code') == code), '')
        print(f"  {code}: {count} awards - {desc[:50]}")

    # Check for federal recipients (to filter out)
    print(f"\n--- Recipient Types (for filtering) ---")
    # Look for columns that might indicate federal recipients
    recipient_type_cols = [f for f in fieldnames if 'business_type' in f.lower() or 'recipient_type' in f.lower()]
    print(f"  Recipient type columns found: {recipient_type_cols}")

    return fieldnames, sample_rows


def analyze_assistance(filepath, sample_size=1000):
    """Analyze assistance CSV structure and key fields."""
    print(f"\n{'='*60}")
    print(f"ANALYZING ASSISTANCE: {filepath.name}")
    print(f"{'='*60}")

    fieldnames, sample_rows = sample_csv(filepath, n_rows=sample_size)

    # Key columns we need per spec
    key_cols = [
        'assistance_award_unique_key',
        'award_id_fain',
        'action_date_fiscal_year',
        'awarding_agency_code',
        'awarding_agency_name',
        'awarding_sub_agency_code',
        'awarding_sub_agency_name',
        'cfda_number',
        'cfda_title',
        'transaction_description',
        'prime_award_base_transaction_description',
        'recipient_name',
        'recipient_uei',
        'recipient_parent_name',
        'total_obligated_amount',
        'total_outlayed_amount_for_overall_award',
        'federal_action_obligation',
        'period_of_performance_start_date',
        'period_of_performance_current_end_date',
        'recipient_country_code',
        'assistance_type_code',
        'assistance_type_description',
        'business_types_code',
    ]

    print(f"\nTotal columns in file: {len(fieldnames)}")

    # Check which key columns exist
    print(f"\n--- Key Column Check ---")
    missing = []
    for col in key_cols:
        if col in fieldnames:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} (MISSING)")
            missing.append(col)

    if missing:
        print(f"\n--- Searching for similar columns ---")
        for m in missing:
            similar = [f for f in fieldnames if m.split('_')[0] in f.lower()]
            if similar:
                print(f"  {m} -> possible matches: {similar[:5]}")

    # Sample values
    print(f"\n--- Sample Values (first 3 rows) ---")
    for row in sample_rows[:3]:
        print(f"\n  Award: {row.get('assistance_award_unique_key', 'N/A')[:50]}")
        print(f"  FY: {row.get('action_date_fiscal_year', 'N/A')}")
        print(f"  Agency: {row.get('awarding_agency_name', 'N/A')}")
        print(f"  CFDA: {row.get('cfda_number', 'N/A')} - {row.get('cfda_title', 'N/A')[:50]}")
        print(f"  Recipient: {row.get('recipient_name', 'N/A')[:50]}")
        print(f"  Obligated: ${row.get('total_obligated_amount', 'N/A')}")
        print(f"  Assistance Type: {row.get('assistance_type_description', 'N/A')}")
        print(f"  Description: {row.get('transaction_description', 'N/A')[:80]}...")

    # CFDA distribution (important for hybrid mapping approach)
    print(f"\n--- CFDA Code Distribution (top 15 in sample) ---")
    cfda_counts = Counter(row.get('cfda_number', '') for row in sample_rows)
    for code, count in cfda_counts.most_common(15):
        title = next((r.get('cfda_title', '') for r in sample_rows if r.get('cfda_number') == code), '')
        print(f"  {code}: {count} awards - {title[:50]}")

    # Assistance types
    print(f"\n--- Assistance Types ---")
    type_counts = Counter(row.get('assistance_type_description', '') for row in sample_rows)
    for t, count in type_counts.most_common(10):
        print(f"  {t}: {count}")

    return fieldnames, sample_rows


def check_data_quality(sample_rows, award_type):
    """Check for data quality issues."""
    print(f"\n--- Data Quality Check ({award_type}) ---")

    # Check for nulls in key fields
    key_field = 'naics_code' if award_type == 'contracts' else 'cfda_number'
    null_count = sum(1 for r in sample_rows if not r.get(key_field))
    print(f"  Missing {key_field}: {null_count}/{len(sample_rows)} ({100*null_count/len(sample_rows):.1f}%)")

    # Check recipient names
    null_recipients = sum(1 for r in sample_rows if not r.get('recipient_name'))
    print(f"  Missing recipient_name: {null_recipients}/{len(sample_rows)}")

    # Check for potential federal recipients to filter
    # Common patterns: "UNITED STATES", "U.S.", federal agency names
    federal_patterns = ['UNITED STATES', 'U.S. DEPARTMENT', 'FEDERAL', 'GOVERNMENT']
    potential_federal = sum(
        1 for r in sample_rows
        if any(p in (r.get('recipient_name', '') or '').upper() for p in federal_patterns)
    )
    print(f"  Potential federal recipients: {potential_federal}/{len(sample_rows)}")


def main():
    print("USASpending Data Structure Test")
    print("================================\n")

    # Find NASA files
    nasa_dir = DATA_DIR / "NASA"
    if not nasa_dir.exists():
        print(f"ERROR: NASA directory not found at {nasa_dir}")
        return

    # Get one contracts and one assistance file
    contracts_files = sorted(nasa_dir.glob("*Contracts*.csv"))
    assistance_files = sorted(nasa_dir.glob("*Assistance*.csv"))

    print(f"Found {len(contracts_files)} contracts files")
    print(f"Found {len(assistance_files)} assistance files")

    if contracts_files:
        # Analyze first contracts file (FY2008)
        fieldnames, rows = analyze_contracts(contracts_files[0], sample_size=500)
        check_data_quality(rows, 'contracts')

    if assistance_files:
        # Analyze first assistance file (FY2008)
        fieldnames, rows = analyze_assistance(assistance_files[0], sample_size=500)
        check_data_quality(rows, 'assistance')

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print("""
Next steps:
1. Verify all key columns are present (check ✗ marks above)
2. Note NAICS/CFDA distributions for mapping
3. Determine filtering logic for federal recipients
4. Check if any columns need special parsing (dates, amounts)
    """)


if __name__ == "__main__":
    main()
