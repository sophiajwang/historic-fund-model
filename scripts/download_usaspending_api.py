#!/usr/bin/env python3
"""
Download USASpending data via API instead of web portal.

Benefits over manual download:
- Scriptable and resumable
- Can run overnight/in background
- Better rate limit handling (auto-retry with backoff)
- Can filter by specific criteria

USASpending API rate limits:
- Unauthenticated: ~10 requests/second
- We'll be conservative: 2-3 requests/second with backoff

Usage:
    # Download NASA contracts for FY2020
    python scripts/download_usaspending_api.py --agency NASA --fy 2020 --type contracts

    # Download all NASA data FY2008-2025
    python scripts/download_usaspending_api.py --agency NASA --fy-range 2008 2025

    # Resume interrupted download
    python scripts/download_usaspending_api.py --agency NASA --fy 2020 --resume
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "usaspending_api"

# API endpoints
BASE_URL = "https://api.usaspending.gov/api/v2"
SPENDING_BY_AWARD_URL = f"{BASE_URL}/search/spending_by_award/"

# Agency names (as they appear in USASpending)
AGENCY_NAMES = {
    "NASA": "National Aeronautics and Space Administration",
    "DOE": "Department of Energy",
    "NIH": "Department of Health and Human Services",
    "DOD": "Department of Defense",
    "NSF": "National Science Foundation",
    "NOAA": "Department of Commerce",
    "EPA": "Environmental Protection Agency",
}

# Rate limiting
REQUEST_DELAY = 0.5  # seconds between requests
MAX_RETRIES = 5
RETRY_BACKOFF = 2.0  # exponential backoff multiplier


def fiscal_year_to_dates(fy: int) -> tuple:
    """Convert fiscal year to start/end dates (Oct 1 - Sep 30)."""
    start = f"{fy - 1}-10-01"
    end = f"{fy}-09-30"
    return start, end


def make_request(url: str, json_data: dict = None, retries: int = MAX_RETRIES) -> dict:
    """Make API request with retry logic using urllib."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "HistoricFundModel/1.0 (research project)"
    }

    for attempt in range(retries):
        try:
            if json_data:
                data = json.dumps(json_data).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            else:
                req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode('utf-8'))

        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Rate limited
                wait_time = REQUEST_DELAY * (RETRY_BACKOFF ** attempt)
                print(f"  Rate limited. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            elif e.code >= 500:
                # Server error
                wait_time = REQUEST_DELAY * (RETRY_BACKOFF ** attempt)
                print(f"  Server error {e.code}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"  HTTP Error {e.code}: {e.reason}")
                return None

        except urllib.error.URLError as e:
            print(f"  URL Error: {e.reason}")
            wait_time = REQUEST_DELAY * (RETRY_BACKOFF ** attempt)
            time.sleep(wait_time)
            continue

        except Exception as e:
            print(f"  Error: {e}")
            wait_time = REQUEST_DELAY * (RETRY_BACKOFF ** attempt)
            time.sleep(wait_time)
            continue

    print(f"  Failed after {retries} retries")
    return None


def download_via_pagination(agency_name: str, fiscal_year: int, award_type: str,
                            output_file: Path, page_limit: int = None) -> int:
    """
    Download awards using pagination through the search API.
    """
    start_date, end_date = fiscal_year_to_dates(fiscal_year)

    # Map award type to codes
    if award_type == "contracts":
        award_type_codes = ["A", "B", "C", "D"]
    elif award_type == "assistance":
        award_type_codes = ["02", "03", "04", "05", "06", "07", "08", "09", "10", "11"]
    else:
        award_type_codes = ["A", "B", "C", "D", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"]

    payload = {
        "filters": {
            "agencies": [{
                "type": "awarding",
                "tier": "toptier",
                "name": agency_name
            }],
            "time_period": [{
                "start_date": start_date,
                "end_date": end_date
            }],
            "award_type_codes": award_type_codes
        },
        "fields": [
            "Award ID", "Recipient Name", "Start Date", "End Date",
            "Award Amount", "Total Outlays", "Awarding Agency", "Awarding Sub Agency",
            "Award Type", "Funding Agency", "NAICS Code", "NAICS Description",
            "Description", "Recipient UEI", "Recipient State Code", "Recipient Country Code",
            "Period of Performance Start Date", "Period of Performance Current End Date"
        ],
        "page": 1,
        "limit": 100,  # Max per page
        "sort": "Award Amount",
        "order": "desc"
    }

    all_results = []
    page = 1
    total_count = None

    print(f"Downloading: {agency_name} FY{fiscal_year} {award_type}")

    while True:
        payload["page"] = page

        result = make_request(SPENDING_BY_AWARD_URL, json_data=payload)

        if not result:
            print(f"  Failed at page {page}")
            break

        results = result.get("results", [])
        if not results:
            print(f"  No more results at page {page}")
            break

        all_results.extend(results)

        # Get total count on first page
        if total_count is None and "page_metadata" in result:
            total_count = result["page_metadata"].get("total", 0)
            total_pages = (total_count // 100) + 1
            print(f"  Total awards: {total_count:,} (~{total_pages} pages)")

        print(f"  Page {page}: +{len(results)} awards (total: {len(all_results):,})")

        # Check limits
        if page_limit and page >= page_limit:
            print(f"  Reached page limit ({page_limit})")
            break

        if not result.get("page_metadata", {}).get("hasNext", False):
            print(f"  Reached last page")
            break

        page += 1
        time.sleep(REQUEST_DELAY)  # Rate limiting

    # Save results
    if all_results:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({
                "agency": agency_name,
                "fiscal_year": fiscal_year,
                "award_type": award_type,
                "downloaded_at": datetime.now().isoformat(),
                "total_awards": len(all_results),
                "awards": all_results
            }, f, indent=2)
        print(f"  Saved {len(all_results):,} awards to {output_file.name}")

    return len(all_results)


def main():
    parser = argparse.ArgumentParser(description="Download USASpending data via API")
    parser.add_argument("--agency", required=True,
                       choices=list(AGENCY_NAMES.keys()),
                       help="Agency to download")
    parser.add_argument("--fy", type=int, help="Single fiscal year")
    parser.add_argument("--fy-range", type=int, nargs=2,
                       metavar=("START", "END"),
                       help="Fiscal year range (inclusive)")
    parser.add_argument("--type", choices=["contracts", "assistance", "all"],
                       default="all", help="Award type")
    parser.add_argument("--page-limit", type=int,
                       help="Limit pages per download (for testing)")
    parser.add_argument("--resume", action="store_true",
                       help="Skip existing files")
    args = parser.parse_args()

    # Determine fiscal years
    if args.fy:
        fiscal_years = [args.fy]
    elif args.fy_range:
        fiscal_years = list(range(args.fy_range[0], args.fy_range[1] + 1))
    else:
        print("Error: Must specify --fy or --fy-range")
        return 1

    # Determine award types
    if args.type == "all":
        award_types = ["contracts", "assistance"]
    else:
        award_types = [args.type]

    agency_name = AGENCY_NAMES[args.agency]

    print("=" * 60)
    print("USASpending API Downloader")
    print("=" * 60)
    print(f"Agency: {args.agency} ({agency_name})")
    print(f"Fiscal years: {fiscal_years[0]} - {fiscal_years[-1]}")
    print(f"Award types: {award_types}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_downloaded = 0

    for fy in fiscal_years:
        for award_type in award_types:
            output_file = OUTPUT_DIR / f"{args.agency}_FY{fy}_{award_type}.json"

            # Skip if exists and resume mode
            if args.resume and output_file.exists():
                print(f"Skipping {output_file.name} (exists)")
                continue

            count = download_via_pagination(
                agency_name,
                fy,
                award_type,
                output_file,
                page_limit=args.page_limit
            )
            total_downloaded += count
            print()

    print("=" * 60)
    print(f"Download complete. Total awards: {total_downloaded:,}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
