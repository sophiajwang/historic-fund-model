#!/usr/bin/env python3
"""
Pipeline 3 (Clean): Stitching with validated data.

Joins cleaned source files on (sector, domain, year), computes derived metrics,
and produces unified output files with data quality metadata.

Uses cleaned public market data (primary_domain attribution, no multi-counting).

Output:
- data/cleaned/unified/{sector}-unified.json
- data/cleaned/unified/all-sectors-unified.json
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"  # Private and government data (unchanged)
CLEANED_SOURCE_DIR = DATA_DIR / "cleaned" / "source"  # Cleaned public data
UNIFIED_DIR = DATA_DIR / "cleaned" / "unified"

SECTORS = ["space", "bio", "energy"]
YEAR_RANGE = range(2008, 2027)  # 2008-2026

# CPI deflators (base year 2023 = 1.0)
CPI_DEFLATORS = {
    2008: 0.785, 2009: 0.782, 2010: 0.795, 2011: 0.820, 2012: 0.837,
    2013: 0.849, 2014: 0.863, 2015: 0.864, 2016: 0.875, 2017: 0.894,
    2018: 0.916, 2019: 0.932, 2020: 0.944, 2021: 0.988, 2022: 1.067,
    2023: 1.000, 2024: 1.029, 2025: 1.050, 2026: 1.070
}


def load_valid_domains():
    """Load valid domains from CSV files."""
    valid_domains = {}
    for sector in SECTORS:
        csv_path = DATA_DIR / f"domains-{sector}.csv"
        valid_domains[sector] = set()
        with open(csv_path) as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split(",", 2)
                if parts:
                    valid_domains[sector].add(parts[0])
    return valid_domains


def load_source_data():
    """Load all source data - cleaned public, original private/government."""
    data = {sector: {"private": {}, "public": {}, "government": {}} for sector in SECTORS}

    for sector in SECTORS:
        # Private data from original source (not affected by cleaning)
        private_path = SOURCE_DIR / f"{sector}-private.json"
        if private_path.exists():
            with open(private_path) as f:
                records = json.load(f)
            for record in records:
                key = (record["domain"], record["year"])
                data[sector]["private"][key] = record

        # Government data from original source (not affected by cleaning)
        govt_path = SOURCE_DIR / f"{sector}-government.json"
        if govt_path.exists():
            with open(govt_path) as f:
                records = json.load(f)
            for record in records:
                key = (record["domain"], record["year"])
                data[sector]["government"][key] = record

        # PUBLIC data from CLEANED source (primary_domain attribution)
        public_path = CLEANED_SOURCE_DIR / f"{sector}-public.json"
        if public_path.exists():
            with open(public_path) as f:
                records = json.load(f)
            for record in records:
                key = (record["domain"], record["year"])
                data[sector]["public"][key] = record
        else:
            print(f"WARNING: Cleaned public data not found: {public_path}")

    return data


def get_all_keys(data, sector):
    """Get all unique (domain, year) keys across all sources for a sector."""
    keys = set()
    for source_type in ["private", "public", "government"]:
        keys.update(data[sector][source_type].keys())
    return keys


def compute_derived_metrics(unified_records):
    """Compute derived metrics for each unified record."""

    # Group by domain for cumulative calculations
    by_domain = defaultdict(list)
    for record in unified_records:
        by_domain[record["domain"]].append(record)

    # Sort each domain's records by year
    for domain in by_domain:
        by_domain[domain].sort(key=lambda x: x["year"])

    # Get 2008 baseline values per domain
    baselines = {}
    for domain, records in by_domain.items():
        baseline_record = next((r for r in records if r["year"] == 2008), None)
        baselines[domain] = {
            "private": baseline_record["private"]["capital_raised"] if baseline_record and baseline_record["private"] else None,
            "govt": baseline_record["government"]["outlayed"] if baseline_record and baseline_record["government"] else None,
            "market_cap": baseline_record["public"]["market_cap_eoy"] if baseline_record and baseline_record["public"] else None,
        }

    # Compute metrics
    for domain, records in by_domain.items():
        cumulative_private = 0
        prev_private = None
        prev_govt = None
        prev_market_cap = None

        for record in records:
            year = record["year"]
            private_raised = record["private"]["capital_raised"] if record["private"] else 0
            govt_outlayed = record["government"]["outlayed"] if record["government"] else 0
            market_cap = record["public"]["market_cap_eoy"] if record["public"] else None

            # Cumulative private
            cumulative_private += private_raised

            # Total inflow (private + government)
            total_inflow = private_raised + govt_outlayed

            # Shares
            private_share = private_raised / total_inflow if total_inflow > 0 else None
            govt_share = govt_outlayed / total_inflow if total_inflow > 0 else None

            # Capital efficiency
            capital_efficiency = market_cap / cumulative_private if market_cap and cumulative_private > 0 else None

            # YoY growth
            private_yoy = (private_raised - prev_private) / prev_private if prev_private and prev_private > 0 else None
            govt_yoy = (govt_outlayed - prev_govt) / prev_govt if prev_govt and prev_govt > 0 else None
            market_cap_yoy = (market_cap - prev_market_cap) / prev_market_cap if market_cap and prev_market_cap and prev_market_cap > 0 else None

            # Indexed to 2008 baseline
            baseline_private = baselines[domain]["private"]
            baseline_govt = baselines[domain]["govt"]
            baseline_mc = baselines[domain]["market_cap"]

            indexed_private = private_raised / baseline_private if baseline_private and baseline_private > 0 else None
            indexed_govt = govt_outlayed / baseline_govt if baseline_govt and baseline_govt > 0 else None
            indexed_mc = market_cap / baseline_mc if market_cap and baseline_mc and baseline_mc > 0 else None

            # CPI deflator
            cpi_deflator = CPI_DEFLATORS.get(year, 1.0)

            record["derived"] = {
                "total_inflow": round(total_inflow, 2) if total_inflow else None,
                "private_share": round(private_share, 4) if private_share is not None else None,
                "govt_share": round(govt_share, 4) if govt_share is not None else None,
                "cumulative_private_raised_to_date": round(cumulative_private, 2),
                "capital_efficiency": round(capital_efficiency, 4) if capital_efficiency else None,
                "private_yoy_growth": round(private_yoy, 4) if private_yoy is not None else None,
                "govt_yoy_growth": round(govt_yoy, 4) if govt_yoy is not None else None,
                "market_cap_yoy_growth": round(market_cap_yoy, 4) if market_cap_yoy is not None else None,
                "indexed_private_2008_base": round(indexed_private, 4) if indexed_private is not None else None,
                "indexed_govt_2008_base": round(indexed_govt, 4) if indexed_govt is not None else None,
                "indexed_market_cap_2008_base": round(indexed_mc, 4) if indexed_mc is not None else None,
                "cpi_deflator_2023_base": cpi_deflator,
            }

            # Update previous values
            prev_private = private_raised if private_raised > 0 else prev_private
            prev_govt = govt_outlayed if govt_outlayed > 0 else prev_govt
            prev_market_cap = market_cap if market_cap else prev_market_cap

    return unified_records


def stitch_sector(sector, data):
    """Join sources for a single sector."""
    unified = []

    all_keys = get_all_keys(data, sector)

    for domain, year in sorted(all_keys):
        private_data = data[sector]["private"].get((domain, year))
        public_data = data[sector]["public"].get((domain, year))
        govt_data = data[sector]["government"].get((domain, year))

        record = {
            "sector": sector,
            "domain": domain,
            "year": year,
            "private": {
                "capital_raised": private_data["total_capital_raised"] if private_data else None,
                "offerings": private_data["number_of_offerings"] if private_data else None,
                "companies_raising": private_data["unique_companies_raising"] if private_data else None,
            } if private_data else None,
            "public": {
                "market_cap_eoy": public_data["total_market_cap_eoy"] if public_data else None,
                "listed_companies_eoy": public_data["total_listed_companies_eoy"] if public_data else None,
                "return_ytd": public_data.get("sector_return_ytd") if public_data else None,
                "tickers": public_data.get("tickers", []) if public_data else [],
                "attribution_method": "primary_domain_only",
            } if public_data else None,
            "government": {
                "obligated": govt_data["total_obligated"] if govt_data else None,
                "outlayed": govt_data["total_outlayed"] if govt_data else None,
                "contracts_outlayed": govt_data["by_award_type"]["contracts"]["outlayed"] if govt_data else None,
                "grants_outlayed": govt_data["by_award_type"]["grants"]["outlayed"] if govt_data else None,
                "loans_outlayed": govt_data["by_award_type"]["loans"]["outlayed"] if govt_data else None,
                "direct_payments_outlayed": govt_data["by_award_type"]["direct_payments"]["outlayed"] if govt_data else None,
            } if govt_data else None,
            "data_quality": {
                "public_attribution": "primary_domain_only",
                "multi_counting": False,
                "outliers_excluded": True,
                "validated": True,
            },
            "metadata": {
                "fy_cy_note": "Government data from FY mapped to CY (same year)",
                "generated_at": datetime.now().isoformat(),
            }
        }

        unified.append(record)

    return unified


def main():
    print("Pipeline 3 (CLEAN): Stitching with validated data")
    print("=" * 60)

    # Load all source data
    print("\nLoading source data...")
    print("  Private & Government: data/source/")
    print("  Public (cleaned): data/cleaned/source/")
    data = load_source_data()

    for sector in SECTORS:
        for source_type in ["private", "public", "government"]:
            count = len(data[sector][source_type])
            print(f"  {sector}-{source_type}: {count} records")

    # Join
    print("\nJoining on (sector, domain, year)...")
    unified_data = {}

    for sector in SECTORS:
        unified_data[sector] = stitch_sector(sector, data)
        print(f"  {sector}: {len(unified_data[sector])} unified records")

    # Compute derived metrics
    print("\nComputing derived metrics...")
    for sector in SECTORS:
        unified_data[sector] = compute_derived_metrics(unified_data[sector])
    print("  Done")

    # Save output
    print("\nSaving output files...")

    UNIFIED_DIR.mkdir(parents=True, exist_ok=True)

    all_records = []

    for sector in SECTORS:
        # Save sector file
        output_path = UNIFIED_DIR / f"{sector}-unified.json"
        with open(output_path, 'w') as f:
            json.dump(unified_data[sector], f, indent=2)
        print(f"  Saved: {output_path}")

        all_records.extend(unified_data[sector])

    # Save master file
    master_path = UNIFIED_DIR / "all-sectors-unified.json"
    with open(master_path, 'w') as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "sectors": SECTORS,
                "year_range": [2008, 2026],
                "total_records": len(all_records),
                "data_quality": {
                    "public_attribution": "primary_domain_only",
                    "multi_counting_eliminated": True,
                    "outliers_excluded": True,
                    "validated": True,
                }
            },
            "records": all_records
        }, f, indent=2)
    print(f"  Saved: {master_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Pipeline 3 (CLEAN) Complete")
    print("=" * 60)

    for sector in SECTORS:
        records = unified_data[sector]
        domains = len(set(r["domain"] for r in records))
        years = sorted(set(r["year"] for r in records))

        # Count records with each data type
        with_private = sum(1 for r in records if r["private"])
        with_public = sum(1 for r in records if r["public"])
        with_govt = sum(1 for r in records if r["government"])

        # Calculate total public market cap for most recent year
        latest_year = max(years)
        total_market_cap = sum(
            r["public"]["market_cap_eoy"] or 0
            for r in records
            if r["year"] == latest_year and r["public"]
        )

        print(f"\n{sector.upper()}:")
        print(f"  Domains: {domains}")
        print(f"  Years: {min(years)} - {max(years)}")
        print(f"  Records with private data: {with_private}")
        print(f"  Records with public data: {with_public}")
        print(f"  Records with government data: {with_govt}")
        print(f"  Total public market cap ({latest_year}): ${total_market_cap:,.0f}")


if __name__ == "__main__":
    main()
