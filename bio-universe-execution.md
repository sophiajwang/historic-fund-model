# Bio Sector — Universe Construction Execution
## Stages 1–3: Seed, Screen, Classify

---

## Key Methodological Note: Handling Bio's Scale

The US public biotech universe contains 500–700+ companies at any given time. Space had ~57. We cannot and should not individually curate each one. Instead:

- **Public companies:** Use ETF constituent lists as the *definitive* universe (not just a seed). XBI and IBB together cover the investable public biotech universe comprehensively. We take their union as our public company set.
- **Historical exits & failures:** Systematically pull from M&A databases and FDA records rather than recall.
- **Private companies:** Apply a higher materiality threshold ($50M+ raised or $500M+ last valuation) to keep the universe tractable for analysis. The private biotech universe is thousands of companies; we need the ones that move the needle on return analysis.

This is a deliberate methodological divergence from space, where we could afford to be near-exhaustive. The divergence is justified and should be documented in the final output.

---

## Stage 1: Seed — Candidate List by Source

### Source A: ETF Constituent Pulls

**⚠️ ACTION REQUIRED:** Download current holdings CSVs from:
- XBI: ssga.com (search XBI, download holdings)
- IBB: ishares.com (search IBB, download holdings)
- ARKG: ark-funds.com/funds/arkg (daily holdings CSV)
- XLV: ssga.com (Health Care Select — use to identify large-cap pharma benchmarks to EXCLUDE)

#### XBI (SPDR S&P Biotech ETF)
*Index methodology: S&P Biotechnology Select Industry Index. Equal-weighted. Companies must be classified as "Biotechnology" under GICS. Listed on NYSE, NASDAQ, or CBOE. US-domiciled.*

This is our **primary public company source**. As of recent data, XBI holds ~130-140 companies.

**⚠️ ACTION REQUIRED:** The full XBI holdings list IS the core public biotech universe. Download it. Every company on this list automatically passes Stage 2 screening (the GICS "Biotechnology" classification and equal-weight index methodology already enforce our inclusion criteria).

**Selected current/recent XBI constituents I can confirm from training data (illustrative, NOT exhaustive — the live pull is definitive):**

**Large-cap biotech (>$20B market cap at some point)**
| Company | Ticker | Sub-sector | Notes |
|---|---|---|---|
| Amgen | AMGN | Biologics | ~$150B+, may rotate out of XBI into XLV |
| Gilead Sciences | GILD | Therapeutics (Antivirals) | HIV/HCV franchise |
| Regeneron | REGN | Biologics | Eylea, Dupixent |
| Vertex Pharmaceuticals | VRTX | Therapeutics (SM) | CF franchise, ~$100B+ |
| Moderna | MRNA | mRNA / Vaccines | Peak ~$140B (2021), declined significantly |
| BioNTech | BNTX | mRNA / Vaccines | German-founded, US-listed — ⚠️ borderline |
| Illumina | ILMN | Genomics / Tools | Sequencing platform |
| Alnylam Pharmaceuticals | ALNY | Therapeutics (RNAi) | |
| Sarepta Therapeutics | SRPT | Gene Therapy | DMD gene therapy |
| Argenx | ARGX | Biologics | Netherlands-founded, US-listed — ⚠️ borderline |
| Neurocrine Biosciences | NBIO | Therapeutics (Neuro) | |
| BioMarin Pharmaceutical | BMRN | Therapeutics (Rare Disease) | |
| Exact Sciences | EXAS | Diagnostics | Cologuard |
| Natera | NTRA | Diagnostics (Genomics) | Prenatal/oncology testing |

**Mid-cap / growth ($2B–$20B)**
| Company | Ticker | Sub-sector | Notes |
|---|---|---|---|
| CRISPR Therapeutics | CRSP | Gene Editing | First CRISPR therapy approved 2023 (Casgevy) |
| Intellia Therapeutics | NTLA | Gene Editing | In vivo gene editing |
| Editas Medicine | EDIT | Gene Editing | |
| Blueprint Medicines | BPMC | Therapeutics (Precision) | |
| Karuna Therapeutics | KRTX | Therapeutics (Neuro) | Acquired by BMS 2024, ~$14B |
| Mirati Therapeutics | MRTX | Therapeutics (Oncology) | Acquired by BMS 2024, ~$4.8B |
| Prometheus Biosciences | RXDX | Therapeutics (GI) | Acquired by Merck 2023, ~$10.8B |
| Seagen | SGEN | ADCs (Oncology) | Acquired by Pfizer 2023, ~$43B |
| Acceleron Pharma | XLRN | Biologics | Acquired by Merck 2021, ~$11.5B |
| Immunomedics | IMMU | ADCs (Oncology) | Acquired by Gilead 2020, ~$21B |
| Arena Pharmaceuticals | ARNA | Therapeutics (GI) | Acquired by Pfizer 2022, ~$6.7B |
| GW Pharmaceuticals | GWPH | Therapeutics (Neuro) | Acquired by Jazz 2021, ~$7.2B |
| MyoKardia | MYOK | Therapeutics (Cardio) | Acquired by BMS 2020, ~$13.1B |
| Turning Point Therapeutics | TPTX | Therapeutics (Oncology) | Acquired by BMS 2022, ~$4.1B |
| Recursion Pharmaceuticals | RXRX | AI Drug Discovery | |
| 10x Genomics | TXG | Genomics / Tools | Single-cell platform |
| Ginkgo Bioworks | DNA | Synthetic Biology | SPAC 2021, significant decline |
| Seres Therapeutics | MCRB | Microbiome | |
| Absci | ABSI | AI Drug Discovery | |
| Beam Therapeutics | BEAM | Gene Editing (Base) | |
| Verve Therapeutics | VERV | Gene Editing (Cardio) | |
| Prime Medicine | PRME | Gene Editing (Prime) | |

**Small-cap / early-stage (sub-$2B) — sampled, not exhaustive**
XBI holds ~80-100 companies in this range at any given time. The live pull captures all of them. These are important for return distribution analysis — many will go to zero, a few will be acquired at premiums.

#### IBB (iShares Nasdaq Biotechnology ETF)
*Index methodology: Nasdaq Biotechnology Index. Market-cap weighted. Must be listed on NASDAQ, classified as Biotech or Pharma under ICB.*

IBB overlaps ~70-80% with XBI but includes some larger names XBI doesn't (market-cap weighting pulls in large pharma-adjacent biotechs) and some NASDAQ-listed companies not in XBI.

**Key additions from IBB not in XBI:**
| Company | Ticker | Notes |
|---|---|---|
| AbbVie | ABBV | ⚠️ Large pharma — may screen out as conglomerate |
| Biogen | BIIB | Large-cap biotech, historically in both |
| Incyte | INCY | Mid-large biotech |
| Jazz Pharmaceuticals | JAZZ | Specialty pharma/biotech |
| United Therapeutics | UTHR | Biotech (pulmonary/transplant) |
| Exelixis | EXEL | Oncology |
| Halozyme | HALO | Drug delivery platform |

**⚠️ ACTION REQUIRED:** Download IBB holdings, merge with XBI, deduplicate. The union of XBI + IBB is the public biotech universe.

#### ARKG (ARK Genomic Revolution ETF)
*ARK active management. Broader definition including genomics-adjacent companies (tools, diagnostics, ag-bio).*

| Company | Ticker | Likely Screen Result | Notes |
|---|---|---|---|
| Twist Bioscience | TWST | ✅ In | Synthetic biology / tools |
| Pacific Biosciences | PACB | ✅ In | Long-read sequencing |
| Adaptive Biotechnologies | ADPT | ✅ In | Immune sequencing |
| Fate Therapeutics | FATE | ✅ In | iPSC cell therapy |
| Ginkgo Bioworks | DNA | ✅ In (overlap w/ XBI) | |
| Teladoc | TDOC | ❌ Out | Telehealth, not biotech |
| Ionis Pharmaceuticals | IONS | ✅ In (overlap) | Antisense therapeutics |
| Personalis | PSNL | ✅ In | Genomic sequencing for oncology |
| Repligen | RGEN | ✅ In | Bioprocessing tools |
| Somalogic | SLGC | ✅ In | Proteomics — acquired by Standard BioTools |
| Signify Health | SGFY | ❌ Out | Health services, not biotech |
| Butterfly Network | BFLY | ❌ Out | Medical imaging device, not biotech |

*ARKG adds some tools/diagnostics/genomics companies that may sit outside XBI/IBB's classification. Useful supplement.*

---

### Source B: SIC/NAICS Code Pull from EDGAR

**⚠️ ACTION REQUIRED:** Run the following queries on EDGAR:
- SIC 2836 (Biological Products, No Diagnostic Substances)
- SIC 2835 (In Vitro & In Vivo Diagnostic Substances)
- SIC 2833 (Pharmaceutical Preparations — filter for biotech)
- SIC 2834 (Pharmaceutical Preparations)
- SIC 3841 (Surgical & Medical Instruments) — filter carefully
- NAICS 325414 (Biological Product Manufacturing)
- NAICS 541711 (Research & Development in Biotechnology)

**Primary value of this pull:** Catching companies that were public during 2000–2025 but have since delisted (acquired, bankrupt, or gone dark). ETF holdings only show current constituents.

**Expected additions from EDGAR historical pull (major ones):**

| Company | SIC | Status | Notes |
|---|---|---|---|
| Genentech | 2836 | Acquired by Roche 2009, ~$46.8B | Largest biotech acquisition at the time |
| MedImmune | 2836 | Acquired by AstraZeneca 2007, ~$15.6B | |
| Millennium Pharmaceuticals | 2836 | Acquired by Takeda 2008, ~$8.8B | |
| ImClone Systems | 2836 | Acquired by Eli Lilly 2008, ~$6.5B | After insider trading scandal |
| OSI Pharmaceuticals | 2834 | Acquired by Astellas 2010, ~$4B | Tarceva |
| Pharmos | 2836 | Failed / delisted | |
| Human Genome Sciences | 2836 | Acquired by GSK 2012, ~$3.6B | |
| Dendreon | 2836 | Bankruptcy 2014 | Provenge — notable failure |
| Medivation | 2836 | Acquired by Pfizer 2016, ~$14.3B | Xtandi |
| Pharmacyclics | 2836 | Acquired by AbbVie 2015, ~$21B | Imbruvica |
| Alexion Pharmaceuticals | 2836 | Acquired by AstraZeneca 2021, ~$39B | Soliris/Ultomiris |
| Celgene | 2834 | Acquired by BMS 2019, ~$74B | Revlimid — largest biotech M&A ever |
| Kite Pharma | 2836 | Acquired by Gilead 2017, ~$11.9B | CAR-T |
| Juno Therapeutics | 2836 | Acquired by Celgene 2018, ~$9B | CAR-T |
| Loxo Oncology | 2836 | Acquired by Eli Lilly 2019, ~$8B | Precision oncology |
| Array BioPharma | 2836 | Acquired by Pfizer 2019, ~$11.4B | |
| The Medicines Company | 2836 | Acquired by Novartis 2020, ~$9.7B | Inclisiran |
| Grail | 2835 | Acquired by Illumina 2021, ~$7.1B | Liquid biopsy |
| Trophos / other small biotechs | Various | Various failures | Hundreds of small-cap biotechs have delisted over 25 years |

**This historical M&A list is one of the most valuable parts of the bio analysis.** Unlike space (where exits are rare), bio has a deep, rich history of acquisitions at known prices. This IS the return data.

---

### Source C: Industry Report Pulls

| Source | What It Provides | Access |
|---|---|---|
| FDA Drugs@FDA Database (fda.gov) | Every approved drug + sponsor company | Free — use to identify companies that achieved commercialization |
| FDA Novel Drug Approvals annual lists | Annual list of NMEs/BLAs by company | Free — good for tracking which companies produced value |
| EvaluatePharma (evaluate.com) | Industry-level market size, M&A data, pipeline analytics | Free summary reports; paid for full data |
| BioCentury | Biotech deal flow, IPO tracker | Paid, but annual reports sometimes free |
| NVCA Yearbook / PitchBook-NVCA Monitor | VC deal flow in Life Sciences sector | Free annual summary PDFs |
| Crunchbase (free tier) | Private biotech companies, funding, exits | Free — search "Biotechnology" + US + founded 2000-2025 |
| BIO (Biotechnology Innovation Organization) | Annual industry reports, policy data | Some reports free |
| EndPoints News / FierceBiotech | Track IPOs, M&A, bankruptcies in real-time | Free (news) — useful for filling gaps |

**⚠️ ACTION REQUIRED:**
1. Download FDA Novel Drug Approvals lists for each year 2000–2025 — identifies which companies successfully brought drugs to market (the ultimate biotech value creation event)
2. Download latest EvaluatePharma free summary — industry market size data
3. Pull NVCA Life Sciences deal flow data from yearbooks
4. Search Crunchbase for Biotechnology + US + raised >$50M — private company universe

#### Private Biotech Companies (Major — applying higher $50M raised / $500M+ valuation threshold)

| Company | Sub-sector | Last Known Valuation / Funding | Founded | Status | Notes |
|---|---|---|---|---|---|
| Genentech (pre-Roche) | Biologics | Was public, then acquired 2009 | 1976 | Acquired | Tracked from 2000 as public |
| 23andMe | Genomics / DTC | IPO via SPAC 2021, ~$3.5B initial | 2006 | Public → bankruptcy 2024 | Notable failure |
| Tempus AI | AI Drug Discovery / Diagnostics | IPO 2024, ~$6B+ | 2015 | Active (public) | |
| Grail (pre-Illumina) | Diagnostics (Liquid Biopsy) | ~$8B+ pre-acquisition valuation | 2016 | Acquired by Illumina 2021, then divested | |
| Altos Labs | Reprogramming / Longevity | ~$3B raised (2022) | 2021 | Private | Backed by Milner, Bezos |
| EQRx | Low-cost Therapeutics | ~$2B+ raised | 2019 | Acquired by Revolution Medicines 2024 | Below original valuation |
| Roivant Sciences | Platform / Multi-subsidiary | IPO via SPAC 2021, ~$7B | 2014 | Public | Vivek Ramaswamy-founded |
| Insitro | AI Drug Discovery | ~$2.4B valuation (2021) | 2018 | Private | Daphne Koller |
| Generate Biomedicines | Generative AI for Proteins | ~$1.5B+ (est.) | 2018 | Private | Flagship-founded |
| Eikon Therapeutics | AI Drug Discovery | ~$3.3B valuation (2022) | 2019 | Private | |
| Resilience | Biomanufacturing | ~$800M+ raised | 2020 | Private | CDMO / manufacturing platform |
| Vir Biotechnology | Therapeutics (Infectious Disease) | IPO 2019 | 2016 | Public | COVID-era boost, since declined |
| Lyell Immunology | Cell Therapy | IPO 2021 | 2018 | Public | Rick Klausner-founded |
| Arsenal Biosciences | Cell Therapy | ~$1B+ (est.) | 2019 | Private | |
| Mammoth Biosciences | Gene Editing (Cas14/CRISPR) | ~$1B+ (est.) | 2017 | Private | |
| Arbor Biotechnologies | Gene Editing | ~$700M+ (est.) | 2016 | Private | Feng Zhang |
| Color Health | Genomics / Population Health | ~$500M+ (est.) | 2015 | Private | |
| Devoted Health | ⚠️ Health insurance, not biotech | ~$12B (2021) | 2017 | Screens out | |
| Century Therapeutics | Cell Therapy (iPSC) | IPO 2021 | 2018 | Public | |
| Nuvation Bio | Oncology | SPAC 2021 | 2018 | Public | David Hung (Medivation founder) |
| Notable Labs | Predictive Oncology | Small-cap public | 2014 | Public | May fail materiality |
| Xencor | Biologics (Antibody Engineering) | IPO 2013 | 2004 | Public | |
| Relay Therapeutics | AI-Driven Drug Design | IPO 2020 | 2016 | Public | |
| Schrodinger | Comp. Chemistry / Drug Discovery | IPO 2020 | 1990 | Public | Software + drug discovery |

---

### Source D: SPAC & Historical Failures

#### Biotech SPACs (selected — fewer than space, bio prefers traditional IPOs)
| Company | SPAC Partner | Merger Date | Initial EV | Current Status | Notes |
|---|---|---|---|---|---|
| 23andMe | VG Acquisition | Jun 2021 | ~$3,500M | Bankruptcy 2024 | Major failure |
| Ginkgo Bioworks | Soaring Eagle | Sep 2021 | ~$17,500M | Active, massive decline | Was most valuable synbio co |
| Roivant Sciences | Montes Archimedes | Sep 2021 | ~$7,300M | Active | |
| Nuvation Bio | Paysign (reverse) | Feb 2021 | ~$1,300M | Active | |
| Humacyte | Alpha Healthcare | Aug 2021 | ~$1,100M | Active | Bioengineered blood vessels |
| Celularity | GX Acquisition | Jul 2021 | ~$1,700M | Active, significant decline | Placental cell therapy |
| SOC Telemed | Healthcare Merger | Oct 2020 | ~$700M | Acquired by Patient Square 2022 | ⚠️ Not biotech — telehealth |
| Standard BioTools (prev. Fluidigm + Somalogic) | N/A (merger of two publics) | N/A | N/A | Active | Somalogic was SPAC (CM Life Sciences) |

#### Major Biotech Failures / Bankruptcies (2000–2025)
| Company | Sub-sector | Year | Details |
|---|---|---|---|
| ImClone Systems | Oncology | 2001 scandal, acquired 2008 | Martha Stewart insider trading; Lilly acquired |
| Dendreon | Cancer Vaccine | 2014 bankruptcy | Provenge couldn't commercialize despite approval |
| MiMedx | Regenerative Medicine | 2018 (accounting fraud) | Eventually restructured |
| Aravive | Oncology | 2023 | Clinical failure, dissolved |
| Clovis Oncology | Oncology | 2022 bankruptcy | Rubraca couldn't compete |
| Puma Biotechnology | Oncology | Significant decline, near-failure | Nerlynx underperformed |
| Intercept Pharmaceuticals | Liver Disease | Major decline after FDA rejection | OCA saga |
| Zymergen | Synthetic Biology | IPO 2021, acquired by Ginkgo 2022 ~$300M | IPO at ~$3B, 90%+ value destruction |
| Theranos | Diagnostics | 2018 (fraud) | Never public, but ~$9B private valuation |
| Sorrento Therapeutics | Multi-target | 2023 bankruptcy | COVID-era hype, unsustainable |
| Novavax | Vaccines | Massive decline from peak | Peak ~$15B, declined >90% |
| Athersys | Cell Therapy | 2023 bankruptcy | MultiStem failed trials |
| Abiomed | Cardiac | Acquired by J&J 2022, ~$16.6B | Success, not failure |
| Northwest Biotherapeutics | Cancer Vaccine | Persistent near-penny-stock | Long-running failure |
| Inovio | DNA Vaccines | Significant decline | COVID vaccine never delivered |

---

## Stage 2: Screen Results

### Screening Notes Specific to Bio

1. **Conglomerate exclusions:** AbbVie, Amgen (borderline — historically pure biotech, now diversifying), Biogen, and other large-cap names that straddle pharma/biotech. Decision rule: if the company is classified as "Biotech" by GICS and originated as a biotech (not a pharma spin-off), INCLUDE regardless of current size. This means Amgen, Gilead, Regeneron, Vertex, Biogen stay in. AbbVie is excluded (pharma origin via AbbVie/Abbott split). J&J, Pfizer, Merck, Lilly — all excluded as conglomerates (they are tracked as acquirers in the exit data).

2. **Non-US-founded, US-listed:** BioNTech (Germany), Argenx (Netherlands), Beigene (China) — these are significant companies with US listings. Decision: EXCLUDE from primary universe per methodology (US-domiciled only), but flag in appendix. BioNTech in particular is important context for the mRNA story.

3. **Diagnostics vs. biotech:** Companies like Exact Sciences, Natera, Guardant Health straddle diagnostics and biotech. If they use biological/genomic technology as their core platform, INCLUDE. If they're pure medical device (hardware-primary), EXCLUDE.

4. **Tools companies:** Illumina, 10x Genomics, Pacific Biosciences, Repligen — these enable biotech but don't develop therapeutics. INCLUDE if they're classified as biotech by GICS or if >50% of revenue comes from biotech/genomics end markets. Most pass.

### PASSED — Public Companies (Active, sampled — full list comes from live ETF pull)

**Tier 1: Large-cap biotech (anchors of the universe)**
| Company | Ticker | Sub-sector | Market Status |
|---|---|---|---|
| Amgen | AMGN | Biologics | public_ipo |
| Gilead Sciences | GILD | Therapeutics (Antivirals) | public_ipo |
| Regeneron | REGN | Biologics | public_ipo |
| Vertex Pharmaceuticals | VRTX | Therapeutics (SM / Gene) | public_ipo |
| Moderna | MRNA | mRNA / Vaccines | public_ipo |
| Biogen | BIIB | Biologics (Neuro) | public_ipo |
| Illumina | ILMN | Genomics / Tools | public_ipo |
| Alnylam | ALNY | RNAi Therapeutics | public_ipo |
| Sarepta | SRPT | Gene Therapy | public_ipo |
| BioMarin | BMRN | Rare Disease | public_ipo |
| Neurocrine | NBIO | Neuro Therapeutics | public_ipo |
| Exact Sciences | EXAS | Diagnostics (Genomic) | public_ipo |
| Natera | NTRA | Diagnostics (Genomic) | public_ipo |
| Incyte | INCY | Oncology / Inflammation | public_ipo |
| Jazz Pharmaceuticals | JAZZ | Specialty (Neuro/Onc) | public_ipo |
| United Therapeutics | UTHR | Pulmonary / Transplant | public_ipo |
| Halozyme | HALO | Drug Delivery Platform | public_ipo |
| Exelixis | EXEL | Oncology | public_ipo |

**Tier 2: Mid-cap / growth (sampled — ~50-80 more from XBI/IBB)**
| Company | Ticker | Sub-sector | Market Status |
|---|---|---|---|
| CRISPR Therapeutics | CRSP | Gene Editing | public_ipo |
| Intellia Therapeutics | NTLA | Gene Editing | public_ipo |
| Editas Medicine | EDIT | Gene Editing | public_ipo |
| Beam Therapeutics | BEAM | Base Editing | public_ipo |
| Verve Therapeutics | VERV | Gene Editing (Cardio) | public_ipo |
| Blueprint Medicines | BPMC | Precision Oncology | public_ipo |
| Recursion | RXRX | AI Drug Discovery | public_ipo |
| 10x Genomics | TXG | Genomics / Tools | public_ipo |
| Relay Therapeutics | RLAY | AI Drug Design | public_ipo |
| Schrodinger | SDGR | Comp. Chemistry | public_ipo |
| Twist Bioscience | TWST | Synthetic Biology / Tools | public_ipo |
| Pacific Biosciences | PACB | Genomics / Sequencing | public_ipo |
| Adaptive Biotechnologies | ADPT | Immune Sequencing | public_ipo |
| Repligen | RGEN | Bioprocessing Tools | public_ipo |
| Tempus AI | TEM | AI / Diagnostics | public_ipo |
| Vir Biotechnology | VIR | Infectious Disease | public_ipo |
| Roivant Sciences | ROIV | Platform / Multi | public_spac |
| Ginkgo Bioworks | DNA | Synthetic Biology | public_spac |

**Tier 3: Small-cap (~80-100 additional from XBI)**
Not individually listed here. The live XBI pull captures all of them. These are critical for the return *distribution* — the base rate of biotech is that most small-cap biotechs fail, and the sector's returns are driven by the right tail (acquisitions at premium, breakout drugs).

### PASSED — Major Acquisitions (The Core Return Dataset for Bio)

This is the single most important table in the bio analysis. Unlike space, bio has a deep, well-documented history of exits at known prices.

| Target | Acquirer | Year | Price ($B) | Sub-sector | Notes |
|---|---|---|---|---|---|
| Celgene | Bristol-Myers Squibb | 2019 | $74.0 | Therapeutics | Largest biotech M&A |
| Genentech | Roche | 2009 | $46.8 | Biologics | Landmark deal |
| Seagen | Pfizer | 2023 | $43.0 | ADCs (Oncology) | |
| Alexion | AstraZeneca | 2021 | $39.0 | Rare Disease | |
| Pharmacyclics | AbbVie | 2015 | $21.0 | Oncology (Imbruvica) | |
| Immunomedics | Gilead | 2020 | $21.0 | ADCs (Oncology) | |
| Abiomed | Johnson & Johnson | 2022 | $16.6 | Cardiac (devices/bio) | |
| MedImmune | AstraZeneca | 2007 | $15.6 | Biologics | |
| Medivation | Pfizer | 2016 | $14.3 | Oncology (Xtandi) | |
| Karuna Therapeutics | BMS | 2024 | $14.0 | Neuro (Schizophrenia) | |
| MyoKardia | BMS | 2020 | $13.1 | Cardiovascular | |
| Kite Pharma | Gilead | 2017 | $11.9 | Cell Therapy (CAR-T) | |
| Array BioPharma | Pfizer | 2019 | $11.4 | Oncology | |
| Acceleron Pharma | Merck | 2021 | $11.5 | Biologics | |
| Prometheus Biosciences | Merck | 2023 | $10.8 | GI / Precision Medicine | |
| Medicines Company | Novartis | 2020 | $9.7 | Cardio (Inclisiran) | |
| Juno Therapeutics | Celgene | 2018 | $9.0 | Cell Therapy (CAR-T) | |
| Millennium Pharma | Takeda | 2008 | $8.8 | Oncology (Velcade) | |
| Loxo Oncology | Eli Lilly | 2019 | $8.0 | Precision Oncology | |
| GW Pharmaceuticals | Jazz Pharma | 2021 | $7.2 | Neuro (CBD/Epilepsy) | |
| Grail | Illumina | 2021 | $7.1 | Diagnostics (Liquid Biopsy) | Forced divestiture later |
| Arena Pharmaceuticals | Pfizer | 2022 | $6.7 | GI | |
| ImClone Systems | Eli Lilly | 2008 | $6.5 | Oncology | |
| Mirati Therapeutics | BMS | 2024 | $4.8 | Oncology | |
| Turning Point Therapeutics | BMS | 2022 | $4.1 | Oncology | |
| OSI Pharmaceuticals | Astellas | 2010 | $4.0 | Oncology (Tarceva) | |
| Human Genome Sciences | GSK | 2012 | $3.6 | Biologics (Benlysta) | |

**⚠️ ACTION REQUIRED:** This list is compiled from my training data. Cross-reference against:
1. FierceBiotech annual "Top Biotech M&A" lists
2. Evaluate Pharma M&A database (if accessible)
3. SEC 8-K filings for material acquisitions

This will catch deals I'm missing, especially in the $1B–$3B range where there are likely 30+ more.

### PASSED — Notable Private Companies (Active, ≥$500M est. valuation)
| Company | Sub-sector | Last Known Valuation | Market Status |
|---|---|---|---|
| Altos Labs | Reprogramming / Longevity | ~$3B raised | private_active |
| Insitro | AI Drug Discovery | ~$2.4B | private_active |
| Eikon Therapeutics | AI Drug Discovery | ~$3.3B | private_active |
| Generate Biomedicines | Generative Protein Design | ~$1.5B+ | private_active |
| Resilience | Biomanufacturing (CDMO) | ~$800M+ raised | private_active |
| Arsenal Biosciences | Cell Therapy | ~$1B+ | private_active |
| Mammoth Biosciences | Gene Editing | ~$1B+ | private_active |
| Arbor Biotechnologies | Gene Editing | ~$700M+ | private_active |

### PASSED — Notable Failures
| Company | Sub-sector | Outcome | Notes |
|---|---|---|---|
| Theranos | Diagnostics (Fraud) | Shut down 2018 | ~$9B peak private valuation |
| Dendreon | Cancer Vaccine | Bankruptcy 2014 | Provenge — approved but couldn't commercialize |
| Zymergen | Synthetic Biology | IPO ~$3B → acquired ~$300M | 90%+ value destruction |
| 23andMe | Genomics / DTC | SPAC → bankruptcy 2024 | ~$3.5B initial, crashed |
| Clovis Oncology | Oncology | Bankruptcy 2022 | Rubraca couldn't compete |
| Sorrento Therapeutics | Multi | Bankruptcy 2023 | COVID hype cycle |

### SCREENED OUT — With Reasoning
| Company | Reason |
|---|---|
| AbbVie (ABBV) | Pharma origin (Abbott spin-off), not biotech-native |
| Pfizer (PFE) | Large pharma conglomerate — tracked as acquirer |
| Johnson & Johnson (JNJ) | Conglomerate — tracked as acquirer |
| Merck (MRK) | Conglomerate — tracked as acquirer |
| Eli Lilly (LLY) | Conglomerate — tracked as acquirer |
| Bristol-Myers Squibb (BMY) | Conglomerate — tracked as acquirer |
| BioNTech (BNTX) | Non-US (Germany HQ) — appendix |
| Argenx (ARGX) | Non-US (Netherlands HQ) — appendix |
| Beigene (BGNE) | Non-US (China HQ) — appendix |
| Devoted Health | Health insurance, not biotech |
| Teladoc (TDOC) | Telehealth, not biotech |
| SOC Telemed | Telehealth, not biotech |

---

## Stage 3: Classification Summary

### Universe Size Estimate

| Category | Estimated Count | Notes |
|---|---|---|
| Public — Active (from XBI + IBB union) | ~150–180 | Live pull required for exact number |
| Public — Historical (acquired, delisted, failed) | ~50–80 | EDGAR pull + M&A list |
| Private — Active (above threshold) | ~15–25 | Higher threshold than space due to universe size |
| Private — Failed (notable) | ~5–10 | Known cases |
| **Total Universe** | **~220–290** | ~4-5x the space universe |

### Vintage Cohort Distribution (estimate)

| Cohort | Approximate Count | Dominant Pattern |
|---|---|---|
| Pre-2000 (tracked from 2000) | ~30-40 | Legacy biotechs (Amgen, Gilead, etc.), many still active |
| 2000–2004 | ~20-30 | Post-genome-project wave, many acquired |
| 2005–2009 | ~20-30 | Pre-financial-crisis biotechs |
| 2010–2014 | ~40-50 | Biotech IPO boom (2013–2014 was a major IPO window) |
| 2015–2019 | ~50-60 | CRISPR era, CAR-T era, precision medicine |
| 2020–2025 | ~40-50 | COVID boost, AI-bio, gene editing maturation |

---

## Gaps & Verification Checklist

**Must-do before finalizing:**

- [ ] Download live XBI + IBB holdings, merge, deduplicate → this IS the public company universe (~30 min)
- [ ] Run EDGAR SIC 2836/2835 queries for historical filers → catch delistings/acquisitions (~45 min)
- [ ] Download FDA Novel Drug Approvals lists (2000–2025) → cross-reference which companies in our universe achieved drug approval (~1 hr)
- [ ] Compile complete >$1B M&A list — cross-reference FierceBiotech annual lists, BioCentury deal logs (~1 hr)
- [ ] Search Crunchbase for Biotechnology + US + raised >$50M → private company universe (~30 min)
- [ ] Pull NVCA Life Sciences VC deal flow data → aggregate investment volume by year (~30 min)
- [ ] Spot-check 10 private company valuations against recent press (~20 min)

**Key analytical difference from space:**
Bio has enough exits to do real statistical analysis on return distributions. Space does not. The bio M&A table alone has 27 deals over $3.5B — this gives us a distribution. For the cross-industry comparison, bio will serve as the "mature" benchmark against which space's thinner track record is contextualized.
