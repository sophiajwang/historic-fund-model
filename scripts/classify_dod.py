#!/usr/bin/env python3
"""
DoD-specific classification with multi-layer filtering.
Designed to handle 40M+ records efficiently.

Usage:
    python3 scripts/classify_dod.py --analyze          # Analyze filtering effectiveness
    python3 scripts/classify_dod.py --sample 1000      # Validate with LLM sample
    python3 scripts/classify_dod.py --run              # Full run
"""

import argparse
import json
import os
import re
import time
import random
from pathlib import Path
from collections import defaultdict, Counter
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
CLASSIFIED_DIR = DATA_DIR / "usaspending" / "classified" / "DoD"
OUTPUT_DIR = DATA_DIR / "usaspending" / "classified_dod"
NOT_APPLICABLE_DIR = DATA_DIR / "usaspending" / "not_applicable" / "DoD"

# =============================================================================
# Layer 1: NAICS-based exclusion
# =============================================================================

# NAICS prefixes that are clearly NOT relevant to space/bio/energy R&D
EXCLUDED_NAICS_PREFIXES = [
    # Food and agriculture
    "311", "312", "722",  # Food manufacturing, beverage, food services
    # Construction
    "236", "237", "238",  # Building, heavy civil, specialty construction
    # Retail and wholesale
    "44", "45", "42",     # Retail trade, wholesale trade
    # Transportation (non-aerospace)
    "481", "482", "483", "484", "485", "486", "487", "488",  # Air, rail, water, truck, transit
    # Administrative and support
    "561",  # Administrative services (janitorial, security, etc.)
    # Real estate
    "531",  # Real estate
    # Finance/insurance (non-R&D)
    "522", "523", "524",
    # Arts/entertainment
    "711", "712", "713",
    # Accommodation
    "721",
    # Personal services
    "812",
]

# NAICS codes that indicate R&D (prioritize for LLM)
# Generic R&D codes removed to reduce LLM volume - these rarely match our sectors
RD_NAICS_CODES = [
    # Removed generic: "541715", "541712", "541711", "541713", "541720"
    "541714",  # R&D in Biotechnology - keep (specific to bio)
    # Space-specific manufacturing (always relevant)
    "336414",  # Guided Missile and Space Vehicle Manufacturing
    "336415",  # Guided Missile and Space Vehicle Propulsion
    "336419",  # Other Guided Missile and Space Vehicle Parts
    # Bio-specific
    "325414",  # Biological Product Manufacturing
    # Energy/Electronics overlap
    "335911",  # Storage Battery Manufacturing
    "335912",  # Primary Battery Manufacturing
]

# More generic R&D codes - only use for keyword-based classification, not LLM
GENERIC_RD_NAICS = [
    "541715",  # R&D in Physical, Engineering, and Life Sciences
    "541712",  # R&D in Physical and Engineering Sciences
    "541711",  # R&D in Biotechnology (general)
    "541713",  # R&D in Nanotechnology
    "334511",  # Search, Detection, Navigation Instruments
]


def is_excluded_by_naics(naics_code):
    """Check if NAICS code indicates non-relevant industry."""
    if not naics_code:
        return False  # No NAICS = needs further analysis
    for prefix in EXCLUDED_NAICS_PREFIXES:
        if naics_code.startswith(prefix):
            return True
    return False


def is_rd_naics(naics_code):
    """Check if NAICS code indicates sector-specific R&D (triggers LLM)."""
    if not naics_code:
        return False
    # Only sector-specific NAICS codes, not generic R&D
    return naics_code in RD_NAICS_CODES


# =============================================================================
# Layer 2: Description quality filter
# =============================================================================

# Patterns that indicate procurement codes (not R&D)
PROCUREMENT_PATTERNS = [
    r"^\d{10}!",           # Starts with 10 digits + ! (item codes)
    r"^[A-Z0-9]{8,}!",     # All caps code + !
    r"^IGF::",             # IGF codes
    r"^DEOBLIGATION",      # Financial adjustments
    r"^CLOSEOUT",          # Contract closeouts
    r"^MODIFICATION",      # Simple modifications
    r"REDUCED OPERATIONAL STATUS",
]

# Minimum description length for R&D consideration
MIN_DESCRIPTION_LENGTH = 50


def is_procurement_description(description):
    """Check if description looks like a procurement code rather than R&D."""
    if not description:
        return True

    desc = description.strip()

    # Too short
    if len(desc) < MIN_DESCRIPTION_LENGTH:
        return True

    # Matches procurement patterns
    for pattern in PROCUREMENT_PATTERNS:
        if re.match(pattern, desc, re.IGNORECASE):
            return True

    # All caps with lots of numbers (product codes)
    if desc.isupper() and sum(c.isdigit() for c in desc) > len(desc) * 0.3:
        return True

    return False


# =============================================================================
# Layer 3: Keyword classification
# =============================================================================

# High-confidence keywords (specific to R&D in our sectors)
# DoD-specific: much stricter for bio since most "medical" is healthcare, not R&D
HIGH_CONFIDENCE_KEYWORDS = {
    "space": [
        # Core space technology
        "spacecraft", "launch vehicle", "space station", "astronaut", "lunar",
        "mars mission", "asteroid", "planetary science", "orbital mechanics",
        "satellite system", "earth observation satellite", "cubesat", "smallsat",
        "deep space", "interplanetary", "astrophysics", "cosmology",
        # Space-specific defense (not general military ops)
        "space situational awareness", "space-based sensor", "on-orbit",
        "space-based interceptor", "missile tracking satellite", "space sensor",
        "exoatmospheric", "midcourse defense", "space surveillance",
        # Note: General "missile defense" excluded (matches operations)
    ],
    "bio": [
        # DoD-specific bio R&D (not general healthcare)
        "biodefense", "pandemic preparedness", "pathogen research", "cbr", "cbrn",
        "chemical biological", "biological warfare", "biological threat",
        "darpa bio", "dtra bio", "synthetic biology defense", "biosurveillance",
        "medical countermeasure", "biomanufacturing", "dna sequencing research"
        # Removed general terms like "vaccine", "therapeutic", "clinical trial" which
        # match healthcare services in DoD context
    ],
    "energy": [
        "photovoltaic", "fuel cell technology", "energy storage system", "carbon capture",
        "nuclear fusion", "nuclear fission", "advanced reactor", "offshore wind farm",
        "solar farm", "battery technology research", "grid modernization", "smart grid",
        "renewable energy research", "clean energy research", "hydrogen production",
        "geothermal energy", "wave energy", "tidal energy", "advanced battery research",
        "operational energy", "tactical energy", "microgrid"
    ]
}

# Context-dependent keywords (need R&D indicator)
# Tightened to avoid false positives in DoD context
CONTEXT_KEYWORDS = {
    "space": ["satellite", "rocket", "GPS navigation", "GNSS", "remote sensing satellite",
              "space telescope", "space radar"],
    # Removed: "antenna" (too broad), "aerospace" (matches business research)
    "bio": ["genomic sequencing", "protein synthesis", "antibody", "pathogen detection",
            "virus research", "therapeutic agent"],
    # Removed: "diagnostic" (matches machine diagnostics), "medical" (too broad),
    # "vaccine" (matches healthcare), "pharmaceutical" (matches procurement)
    "energy": ["solar panel", "solar cell", "wind turbine", "wind farm",
               "nuclear reactor", "battery cell", "power grid", "grid storage",
               "hydrogen fuel", "renewable generation"],
    # Removed: "power" (matches lasers, electronics), "electric" (too broad),
    # "turbine" alone (matches jet turbines)
}

# R&D indicators
RD_INDICATORS = [
    "research", "development", "r&d", "prototype", "demonstration", "sbir", "sttr",
    "innovative", "advanced", "novel", "experimental", "proof of concept",
    "feasibility", "technology development", "engineering development",
    "science and technology", "darpa", "arpa", "laboratory", "testing"
]

# Negative keywords (exclude even if other keywords match)
NEGATIVE_KEYWORDS = [
    # Medication purchases
    "tablet", "capsule", " mg ", " ml ", " gram ", "dosage",
    # Equipment purchases (not R&D)
    "charger", "repair service", "maintenance service", "janitorial",
    # Construction
    "construction of", "renovation of", "building modification", "roof repair",
    # Food
    "fresh,", "frozen,", "canned,", "meat,", "poultry,",
    # Office supplies
    "office supplies", "furniture", "copier", "printer cartridge"
]


def classify_by_keywords(description, naics_desc="", naics_code=""):
    """
    Classify record using keyword matching.
    Returns: (classification, confidence)
        - classification: "space", "bio", "energy", "not_applicable", or "needs_llm"
        - confidence: "high", "medium", or "low"
    """
    if not description:
        return "not_applicable", "high"

    text = f"{description} {naics_desc}".lower()

    # Check negative keywords first
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw.lower() in text:
            return "not_applicable", "high"

    # Check high-confidence keywords
    for sector, keywords in HIGH_CONFIDENCE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return sector, "high"

    # Check context-dependent keywords (need R&D indicator)
    has_rd = any(ind.lower() in text for ind in RD_INDICATORS)
    if has_rd:
        for sector, keywords in CONTEXT_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    return sector, "medium"

    # ONLY send to LLM if:
    # 1. Has R&D NAICS code (541715, etc.) AND
    # 2. Has R&D indicators in description
    # Otherwise, mark as not_applicable
    if has_rd and is_rd_naics(naics_code):
        return "needs_llm", "low"

    # No sector keywords and not R&D NAICS = not applicable
    return "not_applicable", "medium"


# =============================================================================
# Layer 4: LLM classification
# =============================================================================

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


def classify_with_llm(client, record, domains):
    """Classify a single record using Claude API."""
    description = record.get("description") or ""
    naics_code = record.get("naics_code") or ""
    naics_desc = record.get("naics_description") or ""

    # Build domain reference
    domain_ref = ""
    for sector, sector_domains in domains.items():
        domain_ref += f"\n{sector.upper()} domains:\n"
        for d in sector_domains[:10]:
            domain_ref += f"  - {d['category_name']}: {d['description'][:80]}\n"

    prompt = f"""You are classifying DoD contracts for a research dataset tracking R&D capital flows in space, biotechnology, and energy sectors.

Contract description: {description[:500]}
NAICS code: {naics_code} - {naics_desc}

Classify this contract:
1. If it relates to SPACE R&D (satellites, launch, spacecraft, astronomy, etc.) → sector: "space"
2. If it relates to BIOTECHNOLOGY R&D (therapeutics, genomics, medical research, biodefense, etc.) → sector: "bio"
3. If it relates to ENERGY R&D (solar, wind, nuclear, grid, batteries, etc.) → sector: "energy"
4. If it is general procurement, services, or does NOT fit these sectors → sector: null

Respond with JSON only:
{{"sector": "space" | "bio" | "energy" | null, "domains": ["domain1"], "confidence": "high" | "medium" | "low", "reasoning": "brief explanation"}}"""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {"sector": None, "confidence": "low", "reasoning": "Failed to parse"}
    except Exception as e:
        return {"sector": None, "confidence": "low", "reasoning": f"API error: {str(e)}"}


# =============================================================================
# Main processing
# =============================================================================

def analyze_filtering(limit=None):
    """Analyze how each filter layer affects the data."""
    print("Analyzing DoD filtering effectiveness...")
    print("=" * 60)

    stats = {
        "total": 0,
        "layer1_excluded": 0,  # NAICS exclusion
        "layer2_excluded": 0,  # Description quality
        "layer3_high_conf": 0, # High-confidence keyword
        "layer3_medium_conf": 0,  # Context keyword
        "layer3_not_applicable": 0,
        "layer4_needs_llm": 0,  # Ambiguous, needs LLM
    }

    sector_counts = Counter()
    sample_needs_llm = []

    files = sorted(CLASSIFIED_DIR.glob("*.json"))
    if limit:
        files = files[:3]  # Just first 3 files for quick analysis

    for filepath in files:
        print(f"  Processing {filepath.name}...", flush=True)
        with open(filepath) as f:
            data = json.load(f)

        for record in data["records"]:
            if record.get("classification", {}).get("classification_method") != "needs_llm":
                continue  # Already classified

            stats["total"] += 1
            if limit and stats["total"] > limit:
                break

            naics = record.get("naics_code", "")
            desc = record.get("description", "")
            naics_desc = record.get("naics_description", "")

            # Layer 1: NAICS exclusion
            if is_excluded_by_naics(naics):
                stats["layer1_excluded"] += 1
                continue

            # Layer 2: Description quality
            if is_procurement_description(desc):
                stats["layer2_excluded"] += 1
                continue

            # Layer 3: Keyword classification
            classification, confidence = classify_by_keywords(desc, naics_desc, naics)

            if classification in ["space", "bio", "energy"]:
                if confidence == "high":
                    stats["layer3_high_conf"] += 1
                else:
                    stats["layer3_medium_conf"] += 1
                sector_counts[classification] += 1
            elif classification == "not_applicable":
                stats["layer3_not_applicable"] += 1
            else:  # needs_llm
                stats["layer4_needs_llm"] += 1
                if len(sample_needs_llm) < 20:
                    sample_needs_llm.append(record)

        if limit and stats["total"] >= limit:
            break

    # Print results
    print(f"\n{'=' * 60}")
    print("FILTERING ANALYSIS RESULTS")
    print(f"{'=' * 60}")
    print(f"\nTotal records analyzed: {stats['total']:,}")
    print(f"\nLayer 1 - NAICS Exclusion: {stats['layer1_excluded']:,} ({100*stats['layer1_excluded']/max(1,stats['total']):.1f}%)")
    print(f"Layer 2 - Description Quality: {stats['layer2_excluded']:,} ({100*stats['layer2_excluded']/max(1,stats['total']):.1f}%)")
    print(f"Layer 3 - High-confidence keywords: {stats['layer3_high_conf']:,}")
    print(f"Layer 3 - Medium-confidence keywords: {stats['layer3_medium_conf']:,}")
    print(f"Layer 3 - Not applicable: {stats['layer3_not_applicable']:,}")
    print(f"Layer 4 - Needs LLM: {stats['layer4_needs_llm']:,} ({100*stats['layer4_needs_llm']/max(1,stats['total']):.1f}%)")

    print(f"\nSector breakdown (keyword classified):")
    for sector, count in sector_counts.most_common():
        print(f"  {sector}: {count:,}")

    print(f"\nSample records needing LLM:")
    for r in sample_needs_llm[:5]:
        print(f"  - {(r.get('description') or '')[:80]}...")

    # Extrapolate to full dataset
    if stats["total"] > 0:
        total_dod = 40_000_000  # Approximate
        llm_rate = stats["layer4_needs_llm"] / stats["total"]
        estimated_llm = int(total_dod * llm_rate)
        hours = estimated_llm / 3600
        print(f"\n{'=' * 60}")
        print("EXTRAPOLATION TO FULL DATASET")
        print(f"{'=' * 60}")
        print(f"Estimated records needing LLM: {estimated_llm:,}")
        print(f"Estimated runtime at 1 req/sec: {hours:.1f} hours")
        print(f"Estimated cost at $0.0002/req: ${estimated_llm * 0.0002:.2f}")

    return stats


def run_sample_validation(sample_size=1000):
    """Run LLM on a sample to validate keyword classification accuracy."""
    print(f"Running LLM validation on {sample_size} samples...")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not ANTHROPIC_AVAILABLE or not api_key:
        print("ERROR: Anthropic API not available")
        return

    client = anthropic.Anthropic(api_key=api_key)
    domains = load_domains()

    # Collect records that passed filters and were keyword-classified
    keyword_classified = []

    for filepath in sorted(CLASSIFIED_DIR.glob("*.json"))[:5]:
        print(f"  Scanning {filepath.name}...")
        with open(filepath) as f:
            data = json.load(f)

        for record in data["records"]:
            if record.get("classification", {}).get("classification_method") != "needs_llm":
                continue

            naics = record.get("naics_code", "")
            desc = record.get("description", "")
            naics_desc = record.get("naics_description", "")

            # Apply filters
            if is_excluded_by_naics(naics):
                continue
            if is_procurement_description(desc):
                continue

            classification, confidence = classify_by_keywords(desc, naics_desc)
            if classification in ["space", "bio", "energy"]:
                keyword_classified.append({
                    "record": record,
                    "keyword_sector": classification,
                    "keyword_confidence": confidence
                })

        if len(keyword_classified) >= sample_size * 2:
            break

    # Sample
    if len(keyword_classified) > sample_size:
        samples = random.sample(keyword_classified, sample_size)
    else:
        samples = keyword_classified

    print(f"\nValidating {len(samples)} keyword-classified records with LLM...")

    correct = 0
    incorrect = 0
    results = []

    for i, item in enumerate(samples):
        if i > 0 and i % 50 == 0:
            print(f"  Processed {i}/{len(samples)} - Accuracy so far: {100*correct/i:.1f}%", flush=True)

        record = item["record"]
        keyword_sector = item["keyword_sector"]

        llm_result = classify_with_llm(client, record, domains)
        llm_sector = llm_result.get("sector")

        if llm_sector == keyword_sector:
            correct += 1
        elif llm_sector and keyword_sector:
            incorrect += 1

        results.append({
            "keyword": keyword_sector,
            "llm": llm_sector,
            "match": llm_sector == keyword_sector
        })

        time.sleep(0.05)

    # Print results
    print(f"\n{'=' * 60}")
    print("VALIDATION RESULTS")
    print(f"{'=' * 60}")
    print(f"Total validated: {len(samples)}")
    print(f"Keyword matched LLM: {correct} ({100*correct/len(samples):.1f}%)")
    print(f"Keyword disagreed with LLM: {incorrect} ({100*incorrect/len(samples):.1f}%)")

    # Confusion matrix
    print(f"\nConfusion matrix:")
    confusion = defaultdict(Counter)
    for r in results:
        confusion[r["keyword"]][r["llm"] or "null"] += 1

    for kw_sector in ["space", "bio", "energy"]:
        print(f"  Keyword={kw_sector}:")
        for llm_sector, count in confusion[kw_sector].most_common():
            print(f"    LLM={llm_sector}: {count}")


def run_full_classification(batch_size=500, limit=None):
    """Run full DoD classification with LLM for keyword-matched records."""
    print("DoD Full Classification Run")
    print("=" * 60)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not ANTHROPIC_AVAILABLE or not api_key:
        print("ERROR: Anthropic API not available. Set ANTHROPIC_API_KEY.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    domains = load_domains()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    NOT_APPLICABLE_DIR.mkdir(parents=True, exist_ok=True)

    # Check for checkpoint
    checkpoint_path = OUTPUT_DIR / "DoD_checkpoint.json"
    start_index = 0
    classified = defaultdict(list)
    not_applicable_llm = []
    keyword_classified = []  # Records that passed keyword filter

    if checkpoint_path.exists():
        print("Found checkpoint, loading...")
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
        start_index = checkpoint.get("processed_count", 0)
        classified = defaultdict(list, checkpoint.get("classified", {}))
        not_applicable_llm = checkpoint.get("not_applicable_llm", [])
        keyword_classified = checkpoint.get("keyword_classified", [])
        print(f"  Resuming from record {start_index:,}", flush=True)

    # If no checkpoint, collect keyword-matched records
    if not keyword_classified:
        print("\nPhase 1: Filtering records...", flush=True)
        not_applicable_filtered = []

        for filepath in sorted(CLASSIFIED_DIR.glob("*.json")):
            print(f"  Processing {filepath.name}...", flush=True)
            with open(filepath) as f:
                data = json.load(f)

            for record in data["records"]:
                if record.get("classification", {}).get("classification_method") != "needs_llm":
                    continue

                naics = record.get("naics_code", "")
                desc = record.get("description", "")
                naics_desc = record.get("naics_description", "")

                # Layer 1: NAICS exclusion
                if is_excluded_by_naics(naics):
                    not_applicable_filtered.append(record)
                    continue

                # Layer 2: Description quality
                if is_procurement_description(desc):
                    not_applicable_filtered.append(record)
                    continue

                # Layer 3: Keyword classification
                classification, confidence = classify_by_keywords(desc, naics_desc, naics)

                if classification in ["space", "bio", "energy"]:
                    record["_keyword_sector"] = classification
                    record["_keyword_confidence"] = confidence
                    keyword_classified.append(record)
                else:
                    not_applicable_filtered.append(record)

            if limit and len(keyword_classified) >= limit:
                break

        print(f"\nFiltering complete:", flush=True)
        print(f"  Keyword-matched (for LLM): {len(keyword_classified):,}", flush=True)
        print(f"  Filtered out: {len(not_applicable_filtered):,}", flush=True)

        # Save filtered records
        not_applicable_path = NOT_APPLICABLE_DIR / "DoD_not_applicable_filtered.json"
        with open(not_applicable_path, 'w') as f:
            json.dump({
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_records": len(not_applicable_filtered),
                    "filter_method": "naics_description_keyword",
                },
                "records": not_applicable_filtered[:100000]  # Limit file size
            }, f)
        print(f"  Saved filtered records to {not_applicable_path}", flush=True)

    if limit:
        keyword_classified = keyword_classified[:limit]

    # Phase 2: LLM classification
    print(f"\nPhase 2: LLM classification of {len(keyword_classified):,} records...", flush=True)
    print(f"Checkpoint will save every {batch_size:,} records", flush=True)

    for i, record in enumerate(keyword_classified):
        if i < start_index:
            continue

        if i > 0 and i % 100 == 0:
            print(f"  Processed {i:,}/{len(keyword_classified):,}", flush=True)

        result = classify_with_llm(client, record, domains)

        record["classification"] = {
            "sector": result.get("sector"),
            "domains": result.get("domains", []),
            "confidence": result.get("confidence", "low"),
            "classification_method": "llm",
            "reasoning": result.get("reasoning", ""),
            "keyword_hint": record.get("_keyword_sector"),
        }

        sector = result.get("sector")
        if sector and sector != "null":
            classified[sector].append(record)
        else:
            not_applicable_llm.append(record)

        # Save checkpoint
        if (i + 1) % batch_size == 0:
            with open(checkpoint_path, 'w') as f:
                json.dump({
                    "processed_count": i + 1,
                    "classified": {k: v for k, v in classified.items()},
                    "not_applicable_llm": not_applicable_llm,
                    "keyword_classified": keyword_classified,
                    "saved_at": datetime.now().isoformat(),
                }, f)
            print(f"  [Checkpoint saved at {i + 1:,}]", flush=True)

        time.sleep(0.05)  # Rate limiting

    # Remove checkpoint after completion
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    # Save final results
    not_applicable_path = NOT_APPLICABLE_DIR / "DoD_not_applicable.json"
    with open(not_applicable_path, 'w') as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_records": len(not_applicable_llm),
                "method": "llm",
            },
            "records": not_applicable_llm
        }, f)

    # Print summary
    print(f"\n{'=' * 60}")
    print("DOD CLASSIFICATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Records processed with LLM: {len(keyword_classified):,}")
    print(f"Classified to sector:")
    for sector, records in classified.items():
        print(f"  {sector}: {len(records):,}")
    print(f"Not applicable (LLM): {len(not_applicable_llm):,}")
    print(f"\n✓ Complete")


def main():
    parser = argparse.ArgumentParser(description="DoD multi-layer classification")
    parser.add_argument("--analyze", action="store_true",
                        help="Analyze filtering effectiveness")
    parser.add_argument("--analyze-limit", type=int, default=100000,
                        help="Limit records for analysis (default: 100K)")
    parser.add_argument("--sample", type=int,
                        help="Run LLM validation on N samples")
    parser.add_argument("--run", action="store_true",
                        help="Full classification run with LLM")
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Checkpoint every N records (default: 500)")
    parser.add_argument("--limit", type=int,
                        help="Limit total records to process")

    args = parser.parse_args()

    if args.analyze:
        analyze_filtering(limit=args.analyze_limit)
    elif args.sample:
        run_sample_validation(sample_size=args.sample)
    elif args.run:
        run_full_classification(batch_size=args.batch_size, limit=args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
