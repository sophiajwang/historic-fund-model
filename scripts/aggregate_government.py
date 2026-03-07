#!/usr/bin/env python3
"""
Step 2.5 — Aggregate annual government time series.

Rolls up all classified awards into annual totals by sector, domain, year, and award type.
Outputs: data/source/{sector}-government.json
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CLASSIFIED_DIR = DATA_DIR / "usaspending" / "classified"
SOURCE_DIR = DATA_DIR / "source"

AGENCIES = ["NASA", "DoE", "HHS", "NSF", "DoD"]
SECTORS = ["space", "bio", "energy"]

# Map award_type to category
def get_award_category(award_type):
    """Map award type to aggregation category."""
    if award_type in ["contract", "contracts"]:
        return "contracts"
    elif award_type in ["assistance", "grant", "grants"]:
        return "grants"
    elif award_type in ["loan", "loans"]:
        return "loans"
    elif award_type in ["direct_payment", "direct_payments"]:
        return "direct_payments"
    else:
        return "other"


def load_all_classified_records():
    """Load all classified records from all agencies."""
    all_records = []

    for agency in AGENCIES:
        agency_dir = CLASSIFIED_DIR / agency
        if not agency_dir.exists():
            print(f"  Skipping {agency} - directory not found")
            continue

        for filepath in sorted(agency_dir.glob("*.json")):
            try:
                with open(filepath) as f:
                    data = json.load(f)

                for record in data.get("records", []):
                    # Only include records with valid sector classification
                    classification = record.get("classification", {})
                    sector = classification.get("sector")

                    if sector in SECTORS:
                        all_records.append({
                            "agency": agency,
                            "fiscal_year": record.get("fiscal_year"),
                            "sector": sector,
                            "domains": classification.get("domains", []),
                            "award_type": record.get("award_type"),
                            "obligation": record.get("obligation", 0) or 0,
                            "outlayed": record.get("total_outlayed", 0) or 0,
                        })
            except Exception as e:
                print(f"  Error reading {filepath}: {e}")

    return all_records


def aggregate_by_sector_domain_year(records):
    """Aggregate records into annual totals by sector, domain, year."""

    # Structure: {sector: {domain: {year: {award_type: {obligated, outlayed, count}}}}}
    aggregates = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: {"obligated": 0, "outlayed": 0, "count": 0}
                )
            )
        )
    )

    for record in records:
        sector = record["sector"]
        year = record["fiscal_year"]
        domains = record["domains"]
        award_category = get_award_category(record["award_type"])
        obligation = record["obligation"]
        outlayed = record["outlayed"]

        # If no domains, use sector_general
        if not domains:
            domains = [f"{sector}_general"]

        # Award contributes to each domain it's classified under
        for domain in domains:
            aggregates[sector][domain][year][award_category]["obligated"] += obligation
            aggregates[sector][domain][year][award_category]["outlayed"] += outlayed
            aggregates[sector][domain][year][award_category]["count"] += 1

    return aggregates


def format_output(aggregates):
    """Format aggregates into output structure per spec."""
    output = {}

    for sector in SECTORS:
        sector_data = []

        for domain, years in sorted(aggregates[sector].items()):
            for year, award_types in sorted(years.items()):
                # Calculate totals
                total_obligated = sum(at["obligated"] for at in award_types.values())
                total_outlayed = sum(at["outlayed"] for at in award_types.values())

                record = {
                    "sector": sector,
                    "domain": domain,
                    "year": year,
                    "total_obligated": round(total_obligated, 2),
                    "total_outlayed": round(total_outlayed, 2),
                    "by_award_type": {
                        "contracts": {
                            "obligated": round(award_types["contracts"]["obligated"], 2),
                            "outlayed": round(award_types["contracts"]["outlayed"], 2),
                            "count": award_types["contracts"]["count"]
                        },
                        "grants": {
                            "obligated": round(award_types["grants"]["obligated"], 2),
                            "outlayed": round(award_types["grants"]["outlayed"], 2),
                            "count": award_types["grants"]["count"]
                        },
                        "loans": {
                            "obligated": round(award_types["loans"]["obligated"], 2),
                            "outlayed": round(award_types["loans"]["outlayed"], 2),
                            "count": award_types["loans"]["count"]
                        },
                        "direct_payments": {
                            "obligated": round(award_types["direct_payments"]["obligated"], 2),
                            "outlayed": round(award_types["direct_payments"]["outlayed"], 2),
                            "count": award_types["direct_payments"]["count"]
                        }
                    }
                }
                sector_data.append(record)

        output[sector] = sector_data

    return output


def main():
    print("Step 2.5: Aggregate Annual Government Data")
    print("=" * 60)

    # Load all records
    print("\nLoading classified records from all agencies...")
    records = load_all_classified_records()
    print(f"  Total records with sector classification: {len(records):,}")

    # Count by sector
    sector_counts = defaultdict(int)
    for r in records:
        sector_counts[r["sector"]] += 1

    print("\n  By sector:")
    for sector, count in sorted(sector_counts.items()):
        print(f"    {sector}: {count:,}")

    # Aggregate
    print("\nAggregating by (sector, domain, year)...")
    aggregates = aggregate_by_sector_domain_year(records)

    # Format output
    output = format_output(aggregates)

    # Create source directory
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    # Save per-sector files
    print("\nSaving output files...")
    for sector in SECTORS:
        output_path = SOURCE_DIR / f"{sector}-government.json"
        with open(output_path, 'w') as f:
            json.dump(output[sector], f, indent=2)

        # Calculate summary stats
        total_obligated = sum(r["total_obligated"] for r in output[sector])
        total_records = len(output[sector])
        year_range = sorted(set(r["year"] for r in output[sector]))
        domains = sorted(set(r["domain"] for r in output[sector]))

        print(f"\n  {sector}-government.json:")
        print(f"    Records: {total_records:,} (domain-year combinations)")
        print(f"    Domains: {len(domains)}")
        print(f"    Years: {min(year_range) if year_range else 'N/A'} - {max(year_range) if year_range else 'N/A'}")
        print(f"    Total obligated: ${total_obligated:,.0f}")

    print("\n" + "=" * 60)
    print("Step 2.5 Complete")
    print(f"Output files saved to: {SOURCE_DIR}")


if __name__ == "__main__":
    main()
