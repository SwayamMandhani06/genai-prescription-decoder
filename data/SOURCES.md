# AURA-Rx Dataset Sources, Provenance & Licensing Inventory

This document serves as the formal academic provenance and legal licensing register for all candidate, verified, and reference datasets utilized in **AURA-Rx: Explainable Multimodal AI for Handwritten Prescription Understanding**.

---

## 1. Verified Public Research Datasets

### 1.1 Doctor's Handwritten Prescription BD Dataset

- **Dataset Identifier:** `bd-handwritten-rx`
- **Official Title:** Doctor's Handwritten Prescription BD Dataset
- **Provider / Organization:** Research Group, BRAC University & Rajshahi University of Engineering & Technology (RUET), Bangladesh (Nafisa Jahan, Md. Al-Amin, et al.)
- **Source Reference / DOI:** [https://doi.org/10.17632/r3gmvg62cw.1](https://doi.org/10.17632/r3gmvg62cw.1)
- **Publication Reference:** Jahan, N., et al. (2021). *Doctor's Handwritten Prescription BD Dataset*. Mendeley Data, V1.
- **Verification Status:** `verified_public`
- **License Classification:** **Open Content Dataset License**
- **Stated License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Document / Image Type:** Scanned real-world outpatient prescription slips collected from regional diagnostic clinics and hospital departments.
- **Handwriting Characteristics:** Natural, rapid Latin cursive handwriting written with variable ballpoint and gel pens; contains authentic ligatures, trailing stroke degradation, non-standard abbreviations, and variable pen pressure.
- **Language & Script:** English / Latin medical terminology (drug names, dosages) with occasional contextual notes in Bengali.
- **Available Annotations:** Document-level image files with corresponding ground-truth clinical transcription text files.
- **Permitted Usage:** Academic research, commercial and non-commercial development, public benchmarking, adaptation, and redistribution with appropriate attribution.
- **Attribution Requirement:** Must cite original Mendeley Data DOI and publishing authors in academic papers and repository references.
- **Access / Download Method:** Public open download via Mendeley Data API / web repository.
- **Known Limitations:**
  - Variable photographic/scanning resolution across clinics (72 to 300 DPI).
  - Lacks fine-grained token-level bounding box polygon coordinates in raw form.
  - Contains regional brand names marketed primarily in South Asia (requires alignment with Indian CDSCO names).
- **Relevance to Project:** Serves as the primary real-world baseline benchmark for cursive handwriting diversity in Phase 5 (OCR/HTR baseline) and Phase 6 (multimodal extraction). Note: Raw dataset files are not committed to Git.

---

### 1.2 IAM Handwriting Database (FKI-IAM)

- **Dataset Identifier:** `iam-handwriting-database`
- **Official Title:** IAM Handwriting Database (Sentence and Form Subset)
- **Provider / Organization:** Computer Vision and Artificial Intelligence Research Group (FKI), University of Bern, Switzerland (U.-V. Marti and H. Bunke)
- **Source Reference:** [https://fki.tic.heia-fr.ch/databases/iam-handwriting-database](https://fki.tic.heia-fr.ch/databases/iam-handwriting-database)
- **Publication Reference:** Marti, U.-V., & Bunke, H. (2002). *The IAM-database: an English sentence database for offline handwriting recognition*. IEEE Transactions on Pattern Analysis and Machine Intelligence, 24(11), 1459-1464.
- **Verification Status:** `verified_public`
- **License Classification:** **Academic Research Database License**
- **Stated License:** Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) with mandatory academic registration.
- **Document / Image Type:** Scanned forms containing English sentences written on ruled and unruled sheets.
- **Handwriting Characteristics:** Natural handwritten English prose written by 657 different writers, providing broad statistical variation in stroke slant, stroke width, character spacing, and cursive loops.
- **Language & Script:** English (Latin script).
- **Available Annotations:** Full hierarchical ground truth including document-level forms, segmented line images, word bounding boxes, and ASCII transcription text.
- **Permitted Usage:** Non-commercial academic research, algorithm evaluation, and benchmarking.
- **Attribution Requirement:** Mandatory citation of Marti & Bunke (2002).
- **Access / Download Method:** Registered academic download via University of Bern FKI portal.
- **Known Limitations:** Contains general journalistic English prose (LOB Corpus), not specialized medical pharmacopeia terms or posology shorthand.
- **Relevance to Project:** Gold-standard pre-training and cursive character recognition baseline for Phase 5 (evaluating baseline HTR architectures on pure handwriting recognition before medical fine-tuning).

---

### 1.3 AURA-Rx Calibration & Integration Sample Set (N=7)

- **Dataset Identifier:** `aura-rx-curated-evaluation`
- **Official Title:** AURA-Rx Calibration & Integration Sample Set (N=7)
- **Provider / Organization:** Cap_43 Academic Capstone Engineering Project
- **Source Reference:** Local repository path `data/samples/`
- **Verification Status:** `verified_public`
- **License Classification:** **Open Source Software & Data License**
- **Stated License:** MIT Academic License
- **Document / Image Type:** High-resolution digital prescription document images representing outpatient medical visits.
- **Handwriting Characteristics:** Diverse Latin handwriting manifestations including clean print, high-speed cursive ligatures, low-contrast ink, defocus optical blur, low-light shadows, Latin posology shorthand, and confusable LASA drug pairs.
- **Language & Script:** Latin script (English medical names) with multi-lingual ground truth (English, Hindi, Marathi).
- **Available Annotations:** Token-level bounding boxes, transcribed text, standardized drug name, dosage, frequency, duration, route, instructions, ambiguity classification, and LASA flags.
- **Permitted Usage:** Open development, automated testing, continuous integration, and reproducible benchmarking.
- **Attribution Requirement:** AURA-Rx Capstone Repository Documentation.
- **Access / Download Method:** Directly accessible in repository at `data/samples/`.
- **CRITICAL SCIENTIFIC SCOPE & LIMITATION:**
  - This is a **focused engineering calibration and functional integration sample set (N=7)**.
  - It is strictly designed for unit/integration testing, UI state rendering calibration, and split leakage verification.
  - **It is NOT a statistically sufficient empirical research benchmark.** No clinical performance, sensitivity, specificity, or generalizability claims are drawn from these 7 samples. Full statistical benchmarking is scheduled for Phase 12 using large external corpora.

---

## 2. Verified Regulatory & Knowledge Base Reference Sources

### 2.1 CDSCO Approved Drug Formulations & Fixed Dose Combinations

- **Dataset Identifier:** `cdsco-approved-drugs`
- **Official Title:** CDSCO List of Approved Fixed Dose Combinations and New Drugs in India
- **Provider / Organization:** Central Drugs Standard Control Organisation (CDSCO), Directorate General of Health Services, Ministry of Health & Family Welfare, Government of India
- **Source Reference:** [https://cdsco.gov.in](https://cdsco.gov.in)
- **Publication Reference:** CDSCO (2024). *Gazette Formulary of Approved New Drugs and Fixed Dose Combinations*. New Delhi, India.
- **Verification Status:** `verified_regulatory`
- **License Classification:** **Statutory Government Open Data / Official Regulatory Gazette**
- **Stated License:** Open Government Data (OGD) License - India
- **Document / Image Type:** Structured regulatory gazette notifications, pharmacopeia drug schedules, and formulary tables.
- **Handwriting Characteristics:** Clean typeset regulatory tables (non-handwritten).
- **Language & Script:** English (standard Indian Pharmacopoeia / British Pharmacopoeia nomenclature).
- **Available Annotations:** Active pharmaceutical ingredient (API) names, permitted strength combinations, dosage forms (tablets, capsules, syrups, injectables), and therapeutic indications.
- **Permitted Usage:** Unrestricted public, academic, and clinical reference use.
- **Attribution Requirement:** Acknowledge CDSCO, Directorate General of Health Services, Govt of India.
- **Access / Download Method:** Public government gazette download via CDSCO official web portal.
- **Known Limitations:** Contains authorized regulatory formulations; does not catalog colloquial physician handwriting spelling mistakes or regional trade slang.
- **Relevance to Project:** Authoritative ground-truth knowledge graph for Phase 7 (RAG medicine candidate validation) and Phase 10 (LASA verification) within the Indian healthcare context.

---

### 2.2 NLM RxNorm Standard Clinical Drug Nomenclature

- **Dataset Identifier:** `nlm-rxnorm`
- **Official Title:** Unified Medical Language System (UMLS) RxNorm Standard Clinical Drug Vocabulary
- **Provider / Organization:** National Library of Medicine (NLM), National Institutes of Health (NIH), USA
- **Source Reference:** [https://www.nlm.nih.gov/research/umls/rxnorm/](https://www.nlm.nih.gov/research/umls/rxnorm/)
- **Publication Reference:** Nelson, S. J., et al. (2011). *Normalized names for clinical drugs: RxNorm at 6 years*. Journal of the American Medical Informatics Association (JAMIA), 18(4), 441-448.
- **Verification Status:** `verified_regulatory`
- **License Classification:** **Specialized Clinical Terminology / Medical Database License**
- **Stated License:** UMLS Metathesaurus License (Free for research and clinical informatics worldwide)
- **Document / Image Type:** Normalized clinical drug terminology relational tables and concept graphs.
- **Handwriting Characteristics:** Typeset clinical ontology (non-handwritten).
- **Language & Script:** English (standardized clinical terminology).
- **Available Annotations:** Concept Unique Identifiers (RxCUI), active ingredients, semantic clinical drug components (SCD), branded drug components (SBD), dose forms, and brand synonyms.
- **Permitted Usage:** Research, healthcare technology development, and clinical decision support evaluation.
- **Attribution Requirement:** Acknowledge U.S. National Library of Medicine as the source.
- **Access / Download Method:** UMLS Terminology Services (UTS) open download and RESTful API.
- **Known Limitations:** Built around the US National Drug Code (NDC) pharmacopeia; foreign trade names marketed in India must be cross-referenced with CDSCO.
- **Relevance to Project:** Provides normalized clinical posology concepts and standardized RxCUI codes for Phase 7 ontology linking.

---

### 2.3 ISMP List of Look-Alike Sound-Alike (LASA) Drug Names

- **Dataset Identifier:** `ismp-fda-lasa`
- **Official Title:** ISMP's List of Look-Alike and Sound-Alike Drug Names with Recommended TALL MAN Letters
- **Provider / Organization:** Institute for Safe Medication Practices (ISMP) and FDA Center for Drug Evaluation and Research (CDER)
- **Source Reference:** [https://www.ismp.org/recommendations/look-alike-sound-alike-list](https://www.ismp.org/recommendations/look-alike-sound-alike-list)
- **Publication Reference:** ISMP (2023). *Look-Alike Drug Name Sets with Recommended Tall Man Letters*. Horsham, PA.
- **Verification Status:** `verified_regulatory`
- **License Classification:** **Public Clinical Safety Practice Guidance**
- **Stated License:** Public Clinical Safety Guidance (Non-statutory advisory; educational/safety evaluation)
- **Document / Image Type:** Safety alert pair tables with phonetic and orthographic similarity classifications.
- **Handwriting Characteristics:** Typeset clinical guidance with ISMP Tall Man capitalized typography.
- **Language & Script:** English (pharmaceutical brand and generic drug nomenclature).
- **Available Annotations:** Confusable drug pairs (e.g. `metFORMIN` vs `metroNIDAZOLE`, `predniSONE` vs `prednisoLONE`), confusion mechanism, and recommended orthographic capitalizations.
- **Permitted Usage:** Educational use, patient safety research, and clinical software evaluation.
- **Attribution Requirement:** Acknowledge Institute for Safe Medication Practices (ISMP).
- **Access / Download Method:** Public download via ISMP medication safety portal.
- **Known Limitations:** Restricted to pairwise medication confusions; does not include full prescription image context.
- **Relevance to Project:** Serves as the ground truth evaluation set for Phase 10 (LASA medicine name conflict detection and Tall Man rendering).

---

## 3. Candidate / Unverified Datasets (Under Audit)

### 3.1 Kaggle Medical Handwritten Text Collection (Candidate)

- **Dataset Identifier:** `candidate-kaggle-medical-handwritten`
- **Official Title:** Kaggle Medical Handwritten Text Collection
- **Provider / Organization:** Public Kaggle Community Contributors
- **Source Reference:** [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)
- **Verification Status:** `candidate_unverified`
- **License Classification:** **Unverified / Pending Audit**
- **Stated License:** Unverified / Pending Audit
- **Document / Image Type:** Miscellaneous cropped snippets of handwritten medical text.
- **Handwriting Characteristics:** Heterogeneous cursive snippets of varying quality.
- **Language & Script:** English / Latin.
- **Available Annotations:** Snippet transcription labels.
- **Permitted Usage:** **Under legal and ethical review.** In accordance with Phase 3 safety protocols, this dataset is **NOT approved for training or evaluation pipelines** until complete provenance, patient consent, and de-identification are formally verified.
- **Attribution Requirement:** Pending audit.
- **Access / Download Method:** Not downloaded to repository.
- **Known Limitations:** High risk of containing un-anonymized clinic records or unverified copyright licenses.
- **Relevance to Project:** Flagged as an exploratory candidate source; quarantined until licensing and ethics verification is completed.

---

## 4. Provenance & Legal Classification Summary Matrix

| Dataset Identifier | Legal Instrument Classification | Verification Status | Stated License | Permitted Scope | Primary Project Role |
|---|---|---|---|---|---|
| `bd-handwritten-rx` | Open Content Dataset License | `verified_public` | CC BY 4.0 | Research & Benchmarking | Cursive Handwriting Baseline (Phases 5 & 6) |
| `iam-handwriting-database` | Academic Research Database License | `verified_public` | CC BY-NC 4.0 | Academic Non-Commercial | Cursive HTR Pretraining Baseline (Phase 5) |
| `aura-rx-curated-evaluation` | Open Source Software & Data License | `verified_public` | MIT Academic | Open Development & Testing | Calibration & Integration Sample Set (N=7) |
| `cdsco-approved-drugs` | Statutory Government Open Data | `verified_regulatory` | OGD License India | Public Government Data | Indian Pharmacopeia Grounding (Phases 7 & 10) |
| `nlm-rxnorm` | Specialized Clinical Terminology License | `verified_regulatory` | UMLS Metathesaurus | Clinical Research | Standard Posology Ontology (Phase 7) |
| `ismp-fda-lasa` | Public Clinical Safety Practice Guidance | `verified_regulatory` | Public Safety Advisory | Safety Evaluation | LASA Conflict Ground Truth (Phase 10) |
| `candidate-kaggle-medical` | Unverified / Pending Audit | `candidate_unverified` | Pending Audit | **Quarantined (Not permitted)** | Exploratory Review Only |
