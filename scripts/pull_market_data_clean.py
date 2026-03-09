#!/usr/bin/env python3
"""
Pull public market data with proper split-adjusted prices.

This is the cleaned version of pull_market_data.py that:
1. Explicitly ensures split-adjusted prices
2. Validates prices against reasonable ranges
3. Excludes clearly erroneous data
4. Outputs to data/cleaned/source/

Usage:
    python scripts/pull_market_data_clean.py --sector space
    python scripts/pull_market_data_clean.py --all
    python scripts/pull_market_data_clean.py --all --resume

Output:
    data/cleaned/source/market-data-{sector}.json
"""

import argparse
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("Please install yfinance: pip install yfinance")
    exit(1)

# Configuration
SEC_USER_AGENT = "HistoricFundModel/1.0 (research@example.com)"
CHECKPOINT_INTERVAL = 20
START_DATE = "2008-01-01"

# Validation thresholds
MAX_REASONABLE_PRICE = 100000  # $100k per share (allows for BRK-A style stocks)
MIN_REASONABLE_PRICE = 0.0001  # $0.0001 per share
MAX_REASONABLE_MARKET_CAP = 3.5e12  # $3.5 trillion


def load_sec_tickers() -> dict:
    """Load CIK to ticker mapping from SEC."""
    url = "https://www.sec.gov/files/company_tickers.json"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', SEC_USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        cik_to_ticker = {}
        ticker_to_cik = {}
        for entry in data.values():
            cik = str(entry['cik_str']).zfill(10)
            ticker = entry['ticker']
            cik_to_ticker[cik] = ticker
            ticker_to_cik[ticker] = cik

        return cik_to_ticker, ticker_to_cik

    except Exception as e:
        print(f"Error loading SEC tickers: {e}")
        return {}, {}


def validate_price(price: float, ticker: str) -> bool:
    """Check if price is within reasonable bounds."""
    if price is None:
        return False
    if price < MIN_REASONABLE_PRICE or price > MAX_REASONABLE_PRICE:
        return False
    return True


def get_market_data_clean(ticker: str, start_date: str = START_DATE) -> dict:
    """Pull historical market data with validation and cleaning."""
    try:
        stock = yf.Ticker(ticker)

        # Get historical data - yfinance returns split-adjusted by default
        # auto_adjust=True (default) applies split adjustments to OHLC
        hist = stock.history(start=start_date, end=datetime.now().strftime('%Y-%m-%d'), auto_adjust=True)

        if hist.empty:
            return {'error': 'No historical data found'}

        # Get info for additional details
        info = stock.info
        shares_outstanding = info.get('sharesOutstanding')

        # Convert to list of records with validation
        market_data = []
        excluded_count = 0

        for date, row in hist.iterrows():
            close_price = row['Close']

            # Validate price
            if not validate_price(close_price, ticker):
                excluded_count += 1
                continue

            # Calculate market cap using current shares outstanding
            # This is an approximation - actual historical shares varied
            market_cap = None
            if shares_outstanding:
                market_cap = int(close_price * shares_outstanding)
                # Validate market cap
                if market_cap > MAX_REASONABLE_MARKET_CAP:
                    # Market cap too high - likely bad data
                    excluded_count += 1
                    continue

            market_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2) if row['Open'] else None,
                'high': round(row['High'], 2) if row['High'] else None,
                'low': round(row['Low'], 2) if row['Low'] else None,
                'close': round(close_price, 2),
                'volume': int(row['Volume']) if row['Volume'] else 0,
                'market_cap': market_cap,
            })

        if not market_data:
            return {'error': f'All {excluded_count} data points failed validation'}

        # Get listing date (first date in history)
        listing_date = market_data[0]['date'] if market_data else None

        result = {
            'ticker': ticker,
            'company_name_yahoo': info.get('longName') or info.get('shortName'),
            'exchange': info.get('exchange'),
            'sector_yahoo': info.get('sector'),
            'industry_yahoo': info.get('industry'),
            'listing_date': listing_date,
            'current_price': info.get('currentPrice'),
            'market_cap_current': info.get('marketCap'),
            'shares_outstanding': shares_outstanding,
            'data_points': len(market_data),
            'excluded_data_points': excluded_count,
            'date_range': f"{market_data[0]['date']} to {market_data[-1]['date']}" if market_data else None,
            'market_data': market_data,
            'data_quality': {
                'adjusted_prices': True,
                'validation_applied': True,
                'max_price_threshold': MAX_REASONABLE_PRICE,
                'max_market_cap_threshold': MAX_REASONABLE_MARKET_CAP,
            }
        }

        if excluded_count > 0:
            result['data_quality']['excluded_records'] = excluded_count
            result['data_quality']['exclusion_reason'] = 'price_or_market_cap_out_of_range'

        return result

    except Exception as e:
        return {'error': str(e)}


def save_checkpoint(results: list, output_path: Path):
    """Save current results to file."""
    print(f"\n  Saving checkpoint ({len(results)} companies)...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def process_sector(sector: str, cik_to_ticker: dict, resume: bool = False):
    """Process all public companies for a sector."""

    universe_path = Path(__file__).parent.parent / 'data' / 'source' / f'universe-{sector}.json'
    output_path = Path(__file__).parent.parent / 'data' / 'cleaned' / 'source' / f'market-data-{sector}.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Pulling CLEAN market data for {sector} sector")
    print(f"{'='*60}")

    # Load universe
    with open(universe_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    # Filter to public companies
    public_companies = [c for c in companies if c.get('has_s1_s4') and c.get('cik')]
    print(f"Found {len(public_companies)} public companies with CIKs")

    # Load existing data if resuming
    results = []
    processed_ciks = set()
    if resume and output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        processed_ciks = {r['cik'] for r in results}
        print(f"Resuming: {len(results)} companies already processed")

    # Process each company
    new_count = 0
    found_count = 0
    no_ticker = 0
    errors = 0
    excluded_records_total = 0

    for i, company in enumerate(public_companies):
        cik = company['cik']

        if cik in processed_ciks:
            continue

        # Look up ticker
        ticker = cik_to_ticker.get(cik)
        if not ticker:
            # Company not found in SEC tickers (might be delisted or foreign)
            results.append({
                'cik': cik,
                'company_name': company['company_name'],
                'sector': sector,
                'domains': company.get('domains', []),
                'ticker': None,
                'status': 'no_ticker_found',
            })
            no_ticker += 1
            new_count += 1
            continue

        print(f"[{i+1}/{len(public_companies)}] {company['company_name']} ({ticker})...", end=' ', flush=True)

        # Get market data with validation
        data = get_market_data_clean(ticker)

        if 'error' in data:
            print(f"Error: {data['error']}")
            results.append({
                'cik': cik,
                'company_name': company['company_name'],
                'sector': sector,
                'domains': company.get('domains', []),
                'ticker': ticker,
                'status': 'error',
                'error': data['error'],
            })
            errors += 1
        else:
            excluded = data.get('excluded_data_points', 0)
            excluded_records_total += excluded
            status_msg = f"OK ({data['data_points']} points"
            if excluded > 0:
                status_msg += f", {excluded} excluded"
            status_msg += ")"
            print(status_msg)

            results.append({
                'cik': cik,
                'company_name': company['company_name'],
                'sector': sector,
                'domains': company.get('domains', []),
                'ticker': ticker,
                'status': 'success',
                **data,
            })
            found_count += 1

        new_count += 1

        # Rate limiting
        time.sleep(0.5)

        # Checkpoint
        if new_count > 0 and new_count % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(results, output_path)

    # Final save
    save_checkpoint(results, output_path)

    # Summary
    print(f"\nSummary for {sector}:")
    print(f"  Public companies: {len(public_companies)}")
    print(f"  Successfully retrieved: {found_count}")
    print(f"  No ticker found: {no_ticker}")
    print(f"  Errors: {errors}")
    print(f"  Total excluded records (bad data): {excluded_records_total}")


def main():
    parser = argparse.ArgumentParser(description='Pull clean public market data')
    parser.add_argument('--sector', choices=['space', 'bio', 'energy'],
                        help='Sector to process')
    parser.add_argument('--all', action='store_true',
                        help='Process all sectors')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint')

    args = parser.parse_args()

    if not args.sector and not args.all:
        parser.print_help()
        return

    # Load SEC tickers
    print("Loading SEC ticker data...")
    cik_to_ticker, _ = load_sec_tickers()
    print(f"Loaded {len(cik_to_ticker)} ticker mappings")

    sectors = ['space', 'bio', 'energy'] if args.all else [args.sector]

    for sector in sectors:
        process_sector(sector, cik_to_ticker, resume=args.resume)


if __name__ == '__main__':
    main()
