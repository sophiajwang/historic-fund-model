#!/usr/bin/env python3
"""
Scan all Assistance files across all agencies to inventory actual CFDA codes.
This will inform the CFDA-to-domain mapping we need to build.
"""

import csv
import os
from pathlib import Path
from collections import defaultdict
import json

DATA_DIR = Path(__file__).parent.parent / "data" / "usaspending"

def scan_assistance_file(filepath):
    """Extract CFDA codes and titles from an assistance CSV."""
    cfda_data = defaultdict(lambda: {"title": "", "count": 0, "total_obligated": 0.0})

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cfda_num = row.get('cfda_number', '').strip()
            cfda_title = row.get('cfda_title', '').strip()

            if cfda_num:
                cfda_data[cfda_num]["count"] += 1
                cfda_data[cfda_num]["title"] = cfda_title  # Keep latest title

                # Try to parse obligation amount
                try:
                    amount = float(row.get('federal_action_obligation', '0') or '0')
                    cfda_data[cfda_num]["total_obligated"] += amount
                except (ValueError, TypeError):
                    pass

    return dict(cfda_data)


def scan_all_agencies():
    """Scan all agencies and compile CFDA inventory."""

    # Results by agency
    results = {}

    # Find all agency directories
    agencies = [d for d in DATA_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]

    print(f"Found {len(agencies)} agencies: {[a.name for a in agencies]}\n")

    for agency_dir in sorted(agencies):
        agency_name = agency_dir.name
        print(f"Scanning {agency_name}...")

        # Find all assistance files
        assistance_files = list(agency_dir.glob("*Assistance*.csv"))
        print(f"  Found {len(assistance_files)} assistance files")

        agency_cfda = defaultdict(lambda: {"title": "", "count": 0, "total_obligated": 0.0})

        for filepath in sorted(assistance_files):
            print(f"    Processing {filepath.name}...")
            file_cfda = scan_assistance_file(filepath)

            for cfda_num, data in file_cfda.items():
                agency_cfda[cfda_num]["count"] += data["count"]
                agency_cfda[cfda_num]["total_obligated"] += data["total_obligated"]
                if data["title"]:
                    agency_cfda[cfda_num]["title"] = data["title"]

        results[agency_name] = dict(agency_cfda)
        print(f"  Found {len(agency_cfda)} unique CFDA codes\n")

    return results


def print_summary(results):
    """Print summary of CFDA codes by agency."""

    print("\n" + "="*80)
    print("CFDA CODE INVENTORY BY AGENCY")
    print("="*80)

    # Aggregate across all agencies
    all_cfda = defaultdict(lambda: {"title": "", "count": 0, "total_obligated": 0.0, "agencies": set()})

    for agency, cfda_data in results.items():
        print(f"\n### {agency} ###")
        print(f"{'CFDA':<12} {'Count':>10} {'Obligated ($M)':>15}  Title")
        print("-" * 80)

        # Sort by count descending
        sorted_cfda = sorted(cfda_data.items(), key=lambda x: x[1]['count'], reverse=True)

        for cfda_num, data in sorted_cfda[:20]:  # Top 20 per agency
            obligated_m = data['total_obligated'] / 1_000_000
            print(f"{cfda_num:<12} {data['count']:>10,} {obligated_m:>15,.1f}  {data['title'][:40]}")

            # Add to aggregate
            all_cfda[cfda_num]["count"] += data["count"]
            all_cfda[cfda_num]["total_obligated"] += data["total_obligated"]
            all_cfda[cfda_num]["title"] = data["title"]
            all_cfda[cfda_num]["agencies"].add(agency)

        if len(sorted_cfda) > 20:
            print(f"  ... and {len(sorted_cfda) - 20} more CFDA codes")

    # Overall summary
    print("\n" + "="*80)
    print("TOP 30 CFDA CODES ACROSS ALL AGENCIES")
    print("="*80)
    print(f"{'CFDA':<12} {'Count':>10} {'Obligated ($B)':>15}  {'Agencies':<20} Title")
    print("-" * 100)

    sorted_all = sorted(all_cfda.items(), key=lambda x: x[1]['total_obligated'], reverse=True)

    for cfda_num, data in sorted_all[:30]:
        obligated_b = data['total_obligated'] / 1_000_000_000
        agencies_str = ','.join(sorted(data['agencies']))
        print(f"{cfda_num:<12} {data['count']:>10,} {obligated_b:>15,.2f}  {agencies_str:<20} {data['title'][:35]}")

    # Convert to serializable format and save
    output = {}
    for cfda_num, data in sorted_all:
        output[cfda_num] = {
            "title": data["title"],
            "count": data["count"],
            "total_obligated": round(data["total_obligated"], 2),
            "agencies": sorted(data["agencies"])
        }

    output_path = DATA_DIR.parent / "cfda-inventory.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n\nSaved full inventory to {output_path}")

    # Summary stats
    print(f"\n### SUMMARY ###")
    print(f"Total unique CFDA codes: {len(all_cfda)}")
    print(f"Total awards: {sum(d['count'] for d in all_cfda.values()):,}")
    print(f"Total obligated: ${sum(d['total_obligated'] for d in all_cfda.values()) / 1e9:.1f}B")

    # Coverage analysis
    sorted_by_count = sorted(all_cfda.items(), key=lambda x: x[1]['count'], reverse=True)
    cumulative = 0
    total_count = sum(d['count'] for d in all_cfda.values())

    print(f"\n### COVERAGE ANALYSIS ###")
    print("How many CFDA codes needed to cover X% of awards:")
    thresholds = [0.5, 0.8, 0.9, 0.95, 0.99]
    threshold_idx = 0

    for i, (cfda_num, data) in enumerate(sorted_by_count):
        cumulative += data['count']
        coverage = cumulative / total_count

        while threshold_idx < len(thresholds) and coverage >= thresholds[threshold_idx]:
            print(f"  {thresholds[threshold_idx]*100:.0f}% coverage: {i+1} CFDA codes")
            threshold_idx += 1

    return output


def main():
    print("CFDA Code Inventory Scanner")
    print("="*80)
    print("Scanning all Assistance files to inventory actual CFDA codes...\n")

    results = scan_all_agencies()
    inventory = print_summary(results)

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Review cfda-inventory.json for the full list
2. Focus on top CFDA codes by $ volume for manual domain mapping
3. Group CFDA codes by agency to determine sector assignment:
   - NASA CFDAs → space sector
   - HHS/NIH CFDAs → bio sector
   - DoE CFDAs → energy sector
   - DoD/NSF → ambiguous, need LLM or description-based classification
    """)


if __name__ == "__main__":
    main()
