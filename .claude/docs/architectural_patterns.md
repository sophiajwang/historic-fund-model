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
- `data/data-collection.md:153-180` — Classification flow diagram

---

## Two-Layer Classification

**Pattern:** Broad filter → precise classification via LLM.

**Implementation:**
1. **Filter layer:** Crunchbase tags or NAICS codes identify relevant records
2. **Classification layer:** Claude API assigns specific domains from CSV

**Rationale:** Crunchbase tags (e.g., "Biotechnology") and NAICS codes are too broad. LLM provides precision without manual classification of thousands of records.

**References:**
- `data/data-collection.md:153-180` — Crunchbase flow
- `data/data-collection.md:313-380` — Government classification

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
- `data/taxonomy-validation-notes.md:40-80` — Coverage analysis

---

## Multi-Domain Assignment

**Pattern:** Records can belong to multiple domains.

**Implementation:**
- LLM output: `{"domains": ["launch_vehicles", "spacecraft_propulsion"]}`
- Output schema uses array, not single value

**Rationale:** Companies often span domains (e.g., Rocket Lab builds rockets AND propulsion systems). Single assignment loses information.

**References:**
- `data/data-collection.md:238-250` — Output schema

---

## Composite Key Stitching

**Pattern:** All data joined on `(sector, subsector, year)`.

**Implementation:**
- Pipeline 1 output: `{sector}-private.json`, `{sector}-public.json`
- Pipeline 2 output: `{sector}-government.json`
- Pipeline 3: Full outer join on composite key

**Rationale:** Enables time-series analysis and cross-source comparison at subsector granularity.

**References:**
- `data/data-collection.md:725-810` — Stitching steps

---

## Separation of Raw → Normalized → Aggregated

**Pattern:** Data flows through explicit transformation stages.

**Implementation:**
```
data/raw/           → Unprocessed downloads (USASpending CSVs)
data/source/        → Normalized, classified records
data/unified/       → Joined across sources
data/master/        → Final output with derived metrics
```

**Rationale:** Each stage is auditable. Errors can be traced to specific transformation.

**References:**
- `data/data-collection.md:812-845` — Expected file structure

---

## Audit Trail Convention

**Pattern:** Classification records include method, confidence, and reasoning.

**Implementation:**
```json
{
  "domains": ["solar_pv"],
  "classification_confidence": "high",
  "classification_reasoning": "...",
  "classification_method": "llm",
  "classification_model": "claude-3-haiku"
}
```

**Rationale:** Enables debugging, manual review of edge cases, and quality assessment.

**References:**
- `data/data-collection.md:238-250` — Output schema

---

## Naming Conventions

**Pattern:** Consistent naming across all files.

| Type | Convention | Example |
|------|------------|---------|
| Domain names | `snake_case` | `launch_vehicles`, `battery_manufacturing` |
| Sector names | lowercase | `space`, `bio`, `energy` |
| Output files | `{sector}-{source}.json` | `space-private.json` |
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
- `data/data-collection.md:54-56` — FY alignment note
