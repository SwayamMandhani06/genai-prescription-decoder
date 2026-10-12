# DawaAI Datasets, Licensing, and Knowledge Base Provenance

**Document Purpose:** Complete inventory of benchmark datasets, drug pharmacopeias, licensing rights, splits, and privacy considerations.

---

## 1. Datasets & Knowledge Bases Inventory

| Resource Name | Source / Provider | Version / Release | License / Terms of Use | Purpose in DawaAI |
| :--- | :--- | :--- | :--- | :--- |
| **CDSCO National Formulary of India** | Central Drugs Standard Control Organisation, India | 2021 Edition / Updates | Open Government Data (OGD) India | Indian brand and generic medicine validation, scheduled drug checks |
| **RxNorm Drug Nomenclature** | US National Library of Medicine (NIH NLM) | Monthly Release (2024) | Open / UMLS Terminology Services Agreement | Standardized active ingredient (RxCUI) mapping and generic grounding |
| **ISMP Look-Alike Sound-Alike (LASA) List** | Institute for Safe Medication Practices (ISMP) | 2023–2024 List | Clinical Reference / Educational Use | Confusable drug screening and TALL MAN typography mapping |
| **IAM-HistDB Handwriting Database** | University of Bern Computer Vision & AI Group | Version 3.0 | Academic Research Non-Commercial | Baseline cursive optical handwriting transcription benchmarking |
| **DawaAI Curated Prescription Suite** | Internal Capstone Academic Repository | 1.0.0 (Anonymized) | MIT License | Reproducible unit, integration, and E2E regression testing (`backend/app/fixtures`) |

---

## 2. Ethical Compliance & De-Identification

All prescription samples included in repository test fixtures and evaluation runs adhere to HIPAA Safe Harbor and Indian Digital Personal Data Protection Act (DPDP) principles:
1. **De-Identification:** All identifiable patient names, addresses, hospital accession numbers, phone numbers, and physician license stamps are synthetic, obfuscated, or replaced with anonymized placeholders (e.g., *"Patient: Anonymized Adult"*).
2. **Zero Commercial Patient Data:** No proprietary patient clinical records obtained without written patient consent are stored in this repository.

---

## 3. Train / Validation / Test Partitioning

To avoid data leakage across handwriting styles:
- **Writer-Separated Splits:** Data partitions are strictly split by physician/writer ID. No writer appearing in the training split is included in the evaluation or test splits.
- **Partition Ratio:** 70% Training / 15% Validation / 15% Test.
- **Distribution:** Balanced across legible clear scripts, moderate cursive abbreviations, and severe optical degradation.
