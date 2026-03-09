# Data Quality Audit Report

Generated: 2026-03-09 11:52:55

## Summary

| Sector | Companies | Critical | Warning | Info | Total |
|--------|-----------|----------|---------|------|-------|
| space | 26 | 8865 | 23 | 6 | 8894 |
| bio | 117 | 920 | 6 | 106 | 1032 |
| energy | 26 | 0 | 7 | 15 | 22 |
| **Total** | - | **9785** | **36** | **127** | **9948** |

## Critical Issues

These require immediate attention - data is incorrect.


### SPACE

- **XTI Aerospace** (XTIA): Close price $1,275,749,990,400.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $1,275,749,990,400.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $455,625,015,296.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $455,625,015,296.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $1,366,875,045,888.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $1,366,875,045,888.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $1,366,875,045,888.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $455,625,015,296.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $455,625,015,296.00 exceeds $1,000,000 - likely unadjusted split data
- **XTI Aerospace** (XTIA): Close price $1,549,125,025,792.00 exceeds $1,000,000 - likely unadjusted split data
- ... and 8855 more

### BIO

- **Transcode Therapeutics** (RNAZ): Close price $2,956,800.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $3,910,368.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $4,767,840.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $3,370,752.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $2,831,136.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $2,616,768.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $2,380,224.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $2,188,032.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $2,136,288.00 exceeds $1,000,000 - likely unadjusted split data
- **Transcode Therapeutics** (RNAZ): Close price $2,446,752.00 exceeds $1,000,000 - likely unadjusted split data
- ... and 910 more

## Multi-Domain Companies (Multi-Counting Risk)

These companies have market cap counted multiple times in domain aggregations.


### SPACE (6 companies)

| Company | Ticker | Domains |
|---------|--------|---------|
| Rocket Propulsion Systems | RKLB | inspace_manufacturing, launch_vehicles, product_assurance (+1 more) |
| Exo-Space | SIDU | satellite_communications, spacecraft_communications, space_ai (+1 more) |
| Voyager Technologies | VOYG | space_general, launch_vehicles, ground_operations |
| Sidus Space | SIDU | earth_data_analytics, satellite_constellations, small_satellite_engineering |
| Advanced Remote Sensing | UAVS | earth_observation, satellite_communications, satellite_constellations |
| Dynamic Map Platform North America | MNTN | earth_data_analytics, positioning_navigation_timing, satellite_communications |

### BIO (106 companies)

| Company | Ticker | Domains |
|---------|--------|---------|
| Twist Bioscience | TWST | bioprocessing, biosensors, crispr_gene_editing (+8 more) |
| Alltrna | GENB | bioinformatics, biomarker_discovery, cell_therapy (+5 more) |
| Moderna | MRNA | mrna_therapeutics, vaccines, drug_discovery (+3 more) |
| Vera Therapeutics | VERA | biomarker_discovery, cell_therapy, clinical_trials (+3 more) |
| BillionToOne | BLLN | biomarker_discovery, diagnostic_imaging, genomics (+2 more) |
| BostonGene | CAI | bioinformatics, biomarker_discovery, health_ai (+2 more) |
| Cellarity | RXRX | bioprocessing, cell_therapy, drug_discovery (+2 more) |
| iSpecimen | ISPC | biomarker_discovery, clinical_trials, health_ai (+2 more) |
| BridgeBio | BBIO | drug_discovery, gene_therapy, oncology (+2 more) |
| Innovative Genomics Institute | CRBU | crispr_gene_editing, crop_science, food_biotech (+2 more) |
| Gain Therapeutics | GANX | rare_disease, drug_discovery, metabolic_engineering (+2 more) |
| AbbVie | ABBV | immunology, oncology, neurology (+1 more) |
| Erasca | ERAS | oncology, drug_discovery, biomarker_discovery (+1 more) |
| Encoded Therapeutics | STOK | crispr_gene_editing, gene_therapy, genomics (+1 more) |
| Flare Therapeutics | BOLD | oncology, drug_discovery, precision_medicine (+1 more) |

### ENERGY (15 companies)

| Company | Ticker | Domains |
|---------|--------|---------|
| Hyliion | HYLN | distributed_energy, energy_storage_systems, grid_modernization (+1 more) |
| Solidion Technology | STI | battery_chemistry, battery_manufacturing, energy_storage_systems |
| 374Water | SCWO | bioenergy, carbon_utilization, energy_general |
| HNO International | HNOI | hydrogen_production, fuel_cells, carbon_utilization |
| NANO Nuclear Energy | NNE | small_modular_reactors, advanced_nuclear |
| Centuri Group | CTRI | energy_general, energy_industrial_base |
| Vistra | VST | energy_general, power_markets |
| EXPION360 INC. | XPON | battery_chemistry, battery_manufacturing |
| Powin Energy | IPWR | battery_manufacturing, energy_storage_systems |
| Glimpse | VRAR | battery_manufacturing, electric_vehicles |
| Fluence | FLNC | energy_storage_systems, battery_manufacturing |
| magniX | SRFM | electric_vehicles, battery_manufacturing |
| WEC Energy Group | WEC | energy_general, electric_vehicles |
| Chilean Cobalt | COBA | mining_critical_minerals, energy_general |
| Flux Power | FLUX | battery_manufacturing, energy_storage_systems |

## Companies Missing Domain Assignment


### SPACE (18 companies)

- Beta Technologies (BETA)
- SkyWater Technology (SKYT)
- Starlab Space (VOYG)
- Intuitive Machines (LUNR)
- Firefly Aerospace (FLY)
- Unusual Machines (UMAC)
- Arrive AI (ARAI)
- XTI Aerospace (XTIA)
- Karman Space & Defense (KRMN)
- Safe Pro Group (SPAI)
- Air Space Intelligence (ASTS)
- AIRO (The AIRO Group) (AIRO)
- RTX (RTX)
- Heliospace (HLEO)
- Loar Group (LOAR)
- magniX (SRFM)
- ASKA (JETMF)
- Valqari (UAVS)

### BIO (3 companies)

- Evommune (EVMN)
- Absci (ABSI)
- Enavate Sciences (SION)

### ENERGY (3 companies)

- Landbridge (LB)
- Ojjo (MWH)
- Talos Energy (TALO)