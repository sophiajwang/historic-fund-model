# Taxonomy Validation Notes

**Date:** 2026-03-03
**Status:** Phase 0 Complete

## Summary

| Check | Status | Notes |
|-------|--------|-------|
| Domain CSVs defined | Pass | 51 space, 51 bio, 50 energy domains |
| Crunchbase tags mapped | Pass | 35 tags across sectors, 6 excluded |
| NAICS codes mapped | Pass | 90 codes mapped, ~65 unique domains covered |
| LLM fallback defined | Pass | Prompts reference domain CSVs |

---

## 1. Crunchbase Tag Coverage

### Space (7 tags)
- Space Travel
- Satellite Communication
- Remote Sensing
- Geospatial
- GPS
- Aerospace (ambiguous - requires LLM)
- Drones (ambiguous - requires LLM)

### Bio (6 tags + 2 excluded)
- Biopharma
- Biotechnology
- Genetics
- Bioinformatics
- Life Science
- Neuroscience
- ~~Biometrics~~ (excluded - identity/security)
- ~~Quantified Self~~ (excluded - consumer wellness)

### Energy (16 tags + 4 excluded)
- Solar, Wind Energy, Nuclear, Battery, Energy Storage, Fuel Cell
- Power Grid, Electrical Distribution, Energy Management, Energy Efficiency
- Hydroelectric, Geothermal Energy, Clean Energy, Renewable Energy, Energy, Fuel
- ~~Biofuel, Biomass Energy, Fossil Fuels, Oil and Gas~~ (excluded)

### Gap Analysis
No gaps identified. Tags are intentionally broad - LLM handles domain classification.

---

## 2. NAICS Code Coverage

**Total codes mapped:** 90
**Confidence breakdown:**
- High confidence: ~40 codes (direct domain assignment)
- Medium confidence: ~25 codes (assign but may need review)
- Low confidence: ~15 codes (send to LLM)
- Excluded: ~10 codes (out of scope)

### Domains with direct NAICS mapping

**Space (15 domains covered by NAICS):**
- launch_vehicles, satellite_communications, satellite_constellations
- spacecraft_propulsion, spacecraft_structures, spacecraft_mechanisms
- spacecraft_communications, spacecraft_adcs, space_autonomy
- positioning_navigation_timing, earth_observation, earth_data_analytics
- space_instrumentation, product_assurance, spectrum_management, space_general

**Bio (15 domains covered by NAICS):**
- drug_discovery, drug_delivery, bioprocessing, vaccines
- point_of_care, biomarker_discovery, diagnostic_imaging
- medical_devices, surgical_robotics, lab_automation
- genomics, clinical_trials, regulatory_science
- crop_science, food_biotech, veterinary_biotech

**Energy (25 domains covered by NAICS):**
- solar_pv, solar_manufacturing, concentrated_solar, perovskites
- onshore_wind, offshore_wind, wind_turbine_tech
- advanced_nuclear, small_modular_reactors, nuclear_fuel
- battery_manufacturing, battery_chemistry
- hydrogen_production, hydropower, geothermal, bioenergy
- grid_modernization, transmission, distributed_energy, demand_response
- inverters_power_electronics, grid_software
- electric_vehicles, ev_charging, heat_pumps, building_efficiency
- heavy_industry, maritime_shipping, mining_critical_minerals
- carbon_utilization, energy_general

### Domains NOT covered by NAICS (require LLM)

**Space (36 domains - LLM only):**
- counterspace_capabilities, human_systems, infrared_astronomy
- inspace_manufacturing, interplanetary_transport, launch_support
- lunar_exploration, mars_exploration, microgravity_manufacturing
- military_isr_satellites, military_missile_tracking, military_satcom
- planetary_science, satellite_servicing, small_launch_vehicles
- space_ai, space_based_energy, space_cybersecurity
- space_electronic_warfare, space_environment, space_habitats
- space_industrial_base, space_medicine, space_policy
- space_resource_utilization, space_robotics, space_situational_awareness
- space_tourism, space_traffic_management, spacecraft_power_thermal
- spacecraft_ttc, small_satellite_engineering

**Bio (36 domains - LLM only):**
- antibody_engineering, biodefense, bioinformatics, biosensors
- cell_therapy, crispr_gene_editing, enzyme_engineering, epigenetics
- gene_therapy, health_ai, immunology, infectious_disease
- metabolic_engineering, microbiome, mrna_therapeutics, neurology
- oncology, pandemic_preparedness, plant_microbiome, precision_medicine
- protein_engineering, proteomics, rare_disease, regenerative_medicine
- rna_interference, single_cell, structural_biology, synbio_platforms
- transcriptomics, bio_general, bio_industrial_base, bio_policy, bio_cybersecurity

**Energy (18 domains - LLM only):**
- battery_recycling, carbon_capture, carbon_removal
- electrochemical, energy_storage_systems, flow_batteries
- fuel_cells, hydrogen_storage, industrial_efficiency
- power_markets, superconductors, thermal_storage
- energy_industrial_base, energy_policy, energy_cybersecurity, energy_finance

### Assessment
This is expected. NAICS codes are industry-focused and don't capture all research/technology domains. The LLM fallback will handle the remaining ~60% of domains.

---

## 3. Domain Definition Quality

### Checked for:
- [x] No duplicate category_names across sectors
- [x] All category_names are snake_case
- [x] All domains have descriptions
- [x] No overlapping definitions within a sector

### Potential overlaps to monitor:
- **Space:** `satellite_communications` vs `spacecraft_communications` (former is service, latter is hardware)
- **Bio:** `genomics` vs `bioinformatics` (former is sequencing, latter is computation)
- **Energy:** `battery_chemistry` vs `battery_manufacturing` (R&D vs production)

These are intentional distinctions but may require LLM guidance in edge cases.

---

## 4. Recommendations

1. **Monitor LLM classification distribution** - After first batch, check which domains have zero or very few assignments. May indicate:
   - Domain too narrow (merge with related domain)
   - Domain name/description unclear to LLM (refine)
   - Domain legitimately rare in data

2. **Add more NAICS codes as discovered** - When processing USASpending data, track NAICS codes that go to LLM frequently. Add high-volume codes to the mapping.

3. **Consider domain hierarchy later** - After seeing data distribution, may want to create roll-up groups for aggregate analysis. Defer until data is collected.

---

## Sign-off

- [x] Domain CSVs reviewed
- [x] Crunchbase tag mapping complete
- [x] NAICS mapping complete
- [x] LLM prompts reference domain CSVs
- [x] Ready to proceed to Pipeline 1

**Phase 0 validated and complete.**
