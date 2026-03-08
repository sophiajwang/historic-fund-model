# Architectural Patterns

## Single Source of Truth

**Pattern:** Domain CSV files are the canonical reference for all classification.

**Implementation:**
- `data/domains-space.csv`, `data/domains-bio.csv`, `data/domains-energy.csv`
- All other classification systems (NAICS mapping, LLM prompts) reference these files
- Output schema uses `category_name` values from CSVs—no other values are valid

**Rationale:** Prevents drift between classification systems. Changes propagate from one place.

**References:**
- `data/data-collection.md:108-125` — Domain definition section
- `scripts/classify_llm.py:37-54` — Domain loading from CSV

---

## Two-Layer Classification

**Pattern:** Broad filter → precise classification via LLM.

**Implementation:**
1. **Filter layer:** Crunchbase tags or NAICS codes identify relevant records
2. **Classification layer:** Claude API assigns specific domains from CSV

**Rationale:** Crunchbase tags (e.g., "Biotechnology") and NAICS codes are too broad. LLM provides precision without manual classification of thousands of records.

**References:**
- `data/data-collection.md:153-180` — Crunchbase flow
- `scripts/classify_llm.py:112-137` — Keyword pre-filtering

---

## Confidence-Based Routing

**Pattern:** High-confidence cases bypass LLM; ambiguous cases use LLM.

**Implementation:**
```
NAICS confidence = "high"   → Direct domain assignment
NAICS confidence = "medium" → Assign + flag for review
NAICS confidence = "low"    → Send to LLM
NAICS confidence = "exclude"→ Skip record
```

**Rationale:** Minimizes API costs while ensuring quality. ~40% of NAICS codes are high-confidence.

**References:**
- `data/naics-to-domain-mapping.json` — Confidence ratings per code
- `scripts/classify_usaspending.py` — Routing logic

---

## Multi-Domain Assignment

**Pattern:** Records can belong to multiple domains.

**Implementation:**
- LLM output: `{"domains": ["launch_vehicles", "spacecraft_propulsion"]}`
- Aggregation handles multi-domain by attributing to each (with tracking)

**Rationale:** Companies often span domains (e.g., Rocket Lab builds rockets AND propulsion systems). Single assignment loses information.

**References:**
- `scripts/aggregate_private.py:76-81` — Multi-domain attribution

---

## Composite Key Stitching

**Pattern:** All data joined on `(sector, domain, year)`.

**Implementation:**
- Pipeline 1 output: `{sector}-private.json`, `{sector}-public.json`
- Pipeline 2 output: `{sector}-government.json`
- Pipeline 3: Full outer join on composite key

**Rationale:** Enables time-series analysis and cross-source comparison at domain granularity.

**References:**
- `scripts/stitch_data.py:86-99` — Join logic

---

## Separation of Raw → Normalized → Aggregated

**Pattern:** Data flows through explicit transformation stages.

**Implementation:**
```
data/usaspending/raw/     → Unprocessed CSV downloads
data/usaspending/normalized/ → Parsed JSON records
data/usaspending/classified/ → Records with domain assignments
data/source/              → Aggregated per-source data
data/unified/             → Joined across sources
data/master/              → Final output with derived metrics
```

**Rationale:** Each stage is auditable. Errors can be traced to specific transformation.

**References:**
- `scripts/parse_usaspending.py` — Raw → Normalized
- `scripts/aggregate_government.py` — Classified → Source

---

## Audit Trail Convention

**Pattern:** Classification records include method, confidence, and reasoning.

**Implementation:**
```json
{
  "domains": ["solar_pv"],
  "classification_confidence": "high",
  "classification_reasoning": "NAICS 541715 maps to energy R&D",
  "classification_method": "naics_rule",
  "classification_model": "claude-3-haiku"
}
```

**Rationale:** Enables debugging, manual review of edge cases, and quality assessment.

**References:**
- `scripts/classify_llm.py:355-361` — Audit fields on LLM classification

---

## Naming Conventions

**Pattern:** Consistent naming across all files.

| Type | Convention | Example |
|------|------------|---------|
| Domain names | `snake_case` | `launch_vehicles`, `battery_manufacturing` |
| Sector names | lowercase | `space`, `bio`, `energy` |
| Source files | `{sector}-{source}.json` | `space-private.json` |
| Unified files | `{sector}-unified.json` | `bio-unified.json` |

**References:**
- `data/domains-*.csv` — All category_name values follow convention

---

## Fiscal Year Alignment

**Pattern:** Federal FY mapped to calendar year for consistency.

**Implementation:**
- FY2023 (Oct 2022 – Sep 2023) → CY2023
- All private/public data uses calendar year

**Rationale:** Enables joining federal data with market data on common year key.

**References:**
- `scripts/stitch_data.py:25` — Year range definition

---

## Script CLI Pattern

**Pattern:** All scripts use consistent argparse interface.

**Implementation:**
```python
parser.add_argument('--sector', choices=['space', 'bio', 'energy'])
parser.add_argument('--all', action='store_true')
parser.add_argument('--agency', choices=['NASA', 'DoE', 'HHS', 'NSF', 'DoD'])
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--limit', type=int)
```

**Rationale:** Predictable interface across 21 scripts. Easy to test with `--dry-run` and `--limit`.

**References:**
- `scripts/aggregate_private.py:152-165` — Sector-based CLI
- `scripts/classify_llm.py:425-442` — Agency-based CLI with dry-run

---

## Checkpoint/Resume Pattern

**Pattern:** Long-running operations save progress for resumption.

**Implementation:**
```python
checkpoint_path = output_dir / f"{agency}_checkpoint.json"
if checkpoint_path.exists():
    # Resume from saved state
if (i + 1) % batch_size == 0:
    # Save checkpoint
```

**Rationale:** LLM classification of 100k+ records must survive interruptions.

**References:**
- `scripts/classify_llm.py:326-386` — Checkpoint save/load logic

---

## Metadata Headers

**Pattern:** All JSON outputs include generation metadata.

**Implementation:**
```json
{
  "metadata": {
    "agency": "NASA",
    "fiscal_year": 2021,
    "generated_at": "2026-03-06T08:07:54.491740",
    "record_count": 16974
  },
  "records": [...]
}
```

**Rationale:** Enables provenance tracking and debugging stale data issues.

**References:**
- `scripts/parse_usaspending.py` — Metadata on normalized files
- `scripts/aggregate_government.py` — Metadata on aggregated files

---

## General Domain Filtering

**Pattern:** `*_general` domains are catch-all buckets excluded from analysis.

**Implementation:**
```python
records = [r for r in data if not r["domain"].endswith("_general")]
```

**Rationale:** General domains capture unclassified spending that would distort sector totals.

**References:**
- `scripts/analyze_research_questions.py:25-28` — Filter logic
- `scripts/export_viz_data.py:31-35` — Same filter for visualization
