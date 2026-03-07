#!/usr/bin/env python3
"""Quick validation of NSF keyword matching accuracy."""

import json
import os
import random
import re
import time
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CLASSIFIED_DIR = DATA_DIR / "usaspending" / "classified"

# NEW tighter keywords (same as DoD)
HIGH_CONFIDENCE_KEYWORDS = {
    "space": [
        "spacecraft", "launch vehicle", "space station", "astronaut", "lunar",
        "mars mission", "asteroid", "planetary science", "orbital mechanics",
        "satellite system", "earth observation satellite", "cubesat", "smallsat",
        "deep space", "interplanetary", "astrophysics", "cosmology",
        "space situational awareness", "space-based sensor", "on-orbit",
    ],
    "bio": [
        "gene therapy", "cell therapy", "CRISPR", "mRNA", "clinical trial",
        "Phase I", "Phase II", "Phase III", "therapeutic development", "drug discovery",
        "drug development", "biopharmaceutical", "monoclonal antibody", "immunotherapy",
        "oncology research", "genomics research", "proteomics", "synthetic biology",
        "SBIR biotech", "STTR biotech", "biodefense", "pandemic preparedness",
        "pathogen research", "biological threat", "biosurveillance",
        "medical countermeasure", "biomanufacturing", "dna sequencing research"
    ],
    "energy": [
        "photovoltaic", "fuel cell technology", "energy storage system", "carbon capture",
        "nuclear fusion", "nuclear fission", "advanced reactor", "offshore wind farm",
        "solar farm", "battery technology research", "grid modernization", "smart grid",
        "renewable energy research", "clean energy research", "hydrogen production",
        "geothermal energy", "wave energy", "tidal energy", "advanced battery research",
    ]
}

CONTEXT_KEYWORDS = {
    "space": ["satellite", "rocket", "GPS navigation", "GNSS", "remote sensing satellite",
              "space telescope", "space radar"],
    "bio": ["genomic sequencing", "protein synthesis", "antibody", "pathogen detection",
            "virus research", "therapeutic agent"],
    "energy": ["solar panel", "solar cell", "wind turbine", "wind farm",
               "nuclear reactor", "battery cell", "power grid", "grid storage",
               "hydrogen fuel", "renewable generation"],
}

RD_INDICATORS = [
    "research", "development", "r&d", "prototype", "demonstration", "sbir", "sttr",
    "innovative", "advanced", "novel", "experimental", "proof of concept", "feasibility",
    "technology development", "engineering development", "science and technology"
]

NEGATIVE_KEYWORDS = [
    "supply", "purchase order", "tablet", "capsule", "mg ", "ml ", "gram",
    "charger", "repair", "maintenance", "janitorial", "food service",
    "construction of", "renovation of", "building modification"
]


def is_potentially_relevant(record):
    """Check if record matches our keywords."""
    description = (record.get("description") or "").lower()
    naics_desc = (record.get("naics_description") or "").lower()
    cfda_title = (record.get("cfda_title") or "").lower()
    text = f"{description} {naics_desc} {cfda_title}"

    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw in text:
            return False, None

    for sector, keywords in HIGH_CONFIDENCE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return True, sector

    has_rd_indicator = any(ind in text for ind in RD_INDICATORS)
    if has_rd_indicator:
        for sector, keywords in CONTEXT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return True, sector

    return False, None


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Load NSF needs_llm records
    agency_dir = CLASSIFIED_DIR / "NSF"
    needs_llm_records = []

    print("Loading NSF records...")
    for filepath in sorted(agency_dir.glob("*.json")):
        with open(filepath) as f:
            data = json.load(f)
        for record in data["records"]:
            if record.get("classification", {}).get("classification_method") == "needs_llm":
                needs_llm_records.append(record)

    print(f"Total needs_llm records: {len(needs_llm_records):,}")

    # Apply NEW keyword filter
    keyword_matched = []
    for record in needs_llm_records:
        is_relevant, hint_sector = is_potentially_relevant(record)
        if is_relevant:
            record["_hint_sector"] = hint_sector
            keyword_matched.append(record)

    print(f"NEW keyword matched: {len(keyword_matched):,}")

    # Sample 40 for validation
    sample_size = min(40, len(keyword_matched))
    sample = random.sample(keyword_matched, sample_size)

    print(f"\nValidating {sample_size} records with LLM...")
    print("="*60)

    correct = 0
    incorrect = 0
    results = []

    for i, record in enumerate(sample):
        description = record.get("description", "")[:400]
        cfda_title = record.get("cfda_title", "")
        hint = record.get("_hint_sector")

        prompt = f"""You are validating whether a government award belongs to space, biotechnology, or energy sectors.

Award description: {description}
CFDA program: {cfda_title}
Keyword-suggested sector: {hint}

Question: Does this award genuinely belong to the {hint} sector for technology R&D purposes?

Respond with JSON only:
{{"valid": true/false, "actual_sector": "space" | "bio" | "energy" | null, "reasoning": "one sentence"}}"""

        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                is_valid = result.get("valid", False)
                actual = result.get("actual_sector")
                reasoning = result.get("reasoning", "")

                if is_valid:
                    correct += 1
                    status = "CORRECT"
                else:
                    incorrect += 1
                    status = "INCORRECT"

                results.append({
                    "hint": hint,
                    "valid": is_valid,
                    "actual": actual,
                    "reasoning": reasoning
                })

                if (i + 1) % 10 == 0:
                    print(f"  Processed {i+1}/{sample_size}...")

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(0.05)

    # Print results
    print(f"\n{'='*60}")
    print("VALIDATION RESULTS")
    print(f"{'='*60}")
    accuracy = (correct / (correct + incorrect) * 100) if (correct + incorrect) > 0 else 0
    print(f"Correct: {correct}/{correct + incorrect} ({accuracy:.1f}%)")
    print(f"\nBreakdown by sector:")

    by_sector = {}
    for r in results:
        h = r["hint"]
        if h not in by_sector:
            by_sector[h] = {"correct": 0, "incorrect": 0}
        if r["valid"]:
            by_sector[h]["correct"] += 1
        else:
            by_sector[h]["incorrect"] += 1

    for sector, counts in sorted(by_sector.items()):
        total = counts["correct"] + counts["incorrect"]
        pct = counts["correct"] / total * 100 if total > 0 else 0
        print(f"  {sector}: {counts['correct']}/{total} ({pct:.0f}%)")

    print(f"\nIncorrect examples:")
    for r in results:
        if not r["valid"]:
            print(f"  - Keyword said '{r['hint']}' but: {r['reasoning'][:80]}")


if __name__ == "__main__":
    main()
