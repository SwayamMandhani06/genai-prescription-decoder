# Evidence-Based Error Analysis & Failure Taxonomy
## Qualitative Risk Categories and Observed Failure Cases in Handwritten Prescription AI (DawaAI)

**System:** DawaAI — Explainable Multimodal AI for Handwritten Prescription Understanding  
**Document Classification:** Clinical Error Taxonomy & Boundary Failure Analysis  
**System Classification:** Deployment-Ready Assistive Research Prototype for Academic Demonstration  
**Version:** 1.0 (Frozen Specification)  
**Date:** March 2026

---

## 1. Introduction & Research Rationale

Prescription interpretation in outpatient healthcare operates under strict safety requirements. Ambiguous shorthand, degraded cursive handwriting, and Look-Alike Sound-Alike (LASA) drug nomenclature create risks of medication dispensing errors.

This document provides a systematic, evidence-based error analysis of the DawaAI pipeline grounded in the frozen evaluation artifacts of Phase 12 (`eval/reports/error_taxonomy.json`). Rather than asserting fabricated clinical probabilities, we categorize qualitative risk dimensions, analyze observed edge cases from our small curated development cohort ($N=7$), and document how the multi-tiered architecture (Preprocessing, RAG Formulary Grounding, ISMP Tall Man Screening, and Selective Abstention) detects, flags, or isolates failure modes for human clinician review.

---

## 2. Standardized 14-Category Clinical Error Taxonomy (Phase 12)

The standardized 14-category error taxonomy established in Phase 12 records observed frequencies and pipeline behaviors across evaluated samples (`eval/reports/error_taxonomy.json`):

| Error Category ID | Error Name | Observed Count | Pipeline Behavior & Observed Status |
|:---|:---|:---:|:---|
| `ERR-01` | Optical Quality Degraded | 2 | **Processed** by Phase 4 adaptive enhancement; optical metrics flagged degraded state; enhancement applied but residual artifacts remain |
| `ERR-02` | Severe Illegibility / Cursive Ligature | 4 | **Detected** by optical/confidence metrics and **flagged** for Phase 9 Selective Abstention |
| `ERR-03` | Omission of Dosage | 3 | **Detected** and **flagged** by Phase 6 extraction as `missing` |
| `ERR-04` | Ambiguous Decimal Stroke (`1.0` vs `10`) | 1 | **Detected** as ambiguous and **flagged** for Phase 9 Human Verification |
| `ERR-05` | Non-Standard Abbreviation | 2 | **Detected** and **processed** by Phase 7 & Phase 11 abbreviation lookup dictionaries; flagged for clinician verification if unmapped |
| `ERR-06` | Unregistered / Novel Brand Name | 2 | **Detected** and **flagged** by Phase 7 CDSCO validation as unconfirmed candidate |
| `ERR-07` | Orthographic LASA Collision | 1 | **Detected** and **flagged** by Phase 10 with Tall Man warning |
| `ERR-08` | Phonetic LASA Collision | 1 | **Detected** and **flagged** by Phase 10 Double Metaphone filter |
| `ERR-09` | Out-of-Vocabulary Formulation | 1 | **Detected** and **flagged** as formulation mismatch |
| `ERR-10` | Multilingual Lexical Mismatch | 0 | **Prevented** by constrained deterministic posology templates |
| `ERR-11` | Overconfident Calibration Anomaly | 0 | **Prevented** by `insufficient_data` sample-size safeguard |
| `ERR-12` | Crop / Bounding Box Truncation | 1 | **Detected**; spatial polygon preserved for manual visual inspection |
| `ERR-13` | Human Correction Discrepancy | 0 | **Logged** in audit trail for clinician review |
| `ERR-14` | Unsupported Hallucination | 0 | **Detected** and **blocked** by Phase 11 Fidelity Validator |

*Note:* Pipeline actions are classified strictly as detected, flagged, processed, or prevented. No error is claimed as corrected without ground-truth verification.

---

## 3. Case-by-Case Analysis of Curated Evaluation Cohort ($N=7$)

The 7 local samples constitute an engineering development/CI cohort. They are designed for deterministic pipeline integration, failure path verification, and automated regression testing.

| Sample ID | Regimen / Context | Visual Observation | Baseline OCR Finding (Phase 5) | DawaAI Pipeline Behavior | Observed Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **DOC-RX-001** | Acute Bronchitis (Amox-Clav, Paracetamol, Cetirizine) | Standard ballpoint, moderate slant | Tesseract `enhanced` CER: 0.7808, WER: 1.0000 | Multi-field extraction parsed posology; CDSCO grounded generic entities | **ACCEPTED (PREVIEW)** |
| **DOC-RX-002** | Type 2 Diabetes (Metformin, Glimepiride) | Rapid cursive ligature, trailing doctor script | Cursive character confusion on medication name lines | Extracted posology fields; flagged ambiguous frequency for clinician review | **ACCEPTED (FLAGGED FIELD)** |
| **DOC-RX-003** | LASA Challenge Case (Prednisone) | Cursive script with potential confusion | Misclassified individual characters without lexicon check | ISMP screening detected confusable pair; rendered **predniSONE** Tall Man lettering | **SAFETY ALERT (FLAGGED)** |
| **DOC-RX-004** | Pediatric Regimen (Pencil Script) | Low-contrast pencil writing | Tesseract failed to segment faint strokes on raw input | Sauvola binarization recovered stroke contours; structured fields extracted | **ACCEPTED (PREVIEW)** |
| **DOC-RX-005** | Degraded Ink Bleed-Through & Crumpled Paper | Severe background noise, ink bleeding | High character insertion rate; severe OCR degradation | Confidence signal low; selective abstention policy triggered; automated preview halted | **ABSTAINED (ESCALATED)** |
| **DOC-RX-006** | Multi-Medication Regimen | Dense horizontal line spacing | Concatenated adjacent text lines in conventional OCR | Multimodal line grouping separated entries; flagged low-contrast line | **ACCEPTED (1 FIELD FLAGGED)** |
| **DOC-RX-007** | Low-Resolution Document Scan | Low contrast, thermal paper fading | Character detachment and broken strokes | Contrast stretching normalized dynamic range; entities extracted | **ACCEPTED (PREVIEW)** |

---

## 4. Deep Dive: Observed Stress Case (Sample DOC-RX-005)

Sample DOC-RX-005 represents a curated physical stress case: a handwritten document exhibiting liquid staining, paper crumpling, and ink bleed-through from the reverse side.

### 4.1 Observed Behavior Under Conventional & Ungrounded Processing
- When evaluated with Tesseract OCR, the high level of background stroke noise resulted in numerous spurious character insertions (CER > 1.0), outputting fragmented strings.
- In ungrounded generative vision-language models, ambiguous cursive strokes are vulnerable to language-model prior bias, wherein the model risks predicting high-frequency drug names based on surrounding clinical context rather than legible physical ink.

### 4.2 Observed DawaAI Pipeline Handling
1. **Quality Assessment:** Phase 4 preprocessing flagged elevated background noise and low contrast variance.
2. **Confidence Signal:** The raw extraction signal fell below the operational acceptance threshold.
3. **Sample Size Safeguard:** In compliance with Section 20 of `PLAN.md`, empirical calibration correctly reported `calibration_status = "insufficient_data"`.
4. **Selective Abstention:** Under Chow's rule of selective classification (`abstention_policy_v1`), the low confidence score triggered full-document abstention:
   - Automated preview was halted.
   - The sample was flagged with an explicit unreadable/ambiguous diagnostic.
   - The case was routed to the human verification interface (`/api/v1/verification/DOC-RX-005`).

*Evaluation Observation:* On this curated evaluation case, DawaAI abstains rather than producing an unsupported medication prediction. This demonstrates how the selective abstention policy isolates ambiguous inputs, but should not be interpreted as a mathematical guarantee of zero clinical error across diverse patient populations.

---

## 5. Qualitative Risk Categorization & Architectural Mitigations

| Identified Clinical Risk | Qualitative Severity | Primary Vulnerability | Architectural Mitigation in DawaAI | Human-in-the-Loop Role |
| :--- | :---: | :--- | :--- | :--- |
| **Look-Alike Sound-Alike (LASA) Confusions** | High | Orthographic or phonetic similarity between distinct drugs | Phase 10 orthographic (`SequenceMatcher`) and phonetic (`Double Metaphone`) screening + ISMP Tall Man lettering | Pharmacist must review confusable pair warning |
| **Dosage Decimal Errors (e.g., `1.0` vs `10`)** | High | Faded decimal points or pen slips | Phase 7 strict dosage observation preservation (no automated mutation) + `ERR-04` flagging | Pharmacist inspects physical document ink |
| **Cursive Ligature Misreading** | Moderate | Continuous handwriting strokes blending characters | Phase 6 deterministic parser + Phase 9 selective abstention gating | Pharmacist confirms or corrects flagged tokens |
| **Unregistered / Novel Formulations** | Moderate | Formulations not present in national drug compendia | Phase 7 CDSCO validation flags candidate as unconfirmed | Pharmacist manually enters active salt |
| **Patient Posology Misunderstanding** | High | Cryptic Latin posology abbreviations (*q.d.*, *b.i.d.*) | Phase 11 patient-friendly schedules in English, Hindi, and Marathi + audio preview | Patient reviews vernacular posology card |
| **Autonomous Dispensing Risk** | Critical | Automated dispensing without clinical oversight | System designed as an assistive research prototype under Section 42 Pharmacy Act principles | Registered Pharmacist performs statutory review |

---

## 6. Scope Limitations & Research Conclusions

1. **Non-Generalizability:** The evaluation is based on the curated $N=7$ cohort. These findings represent engineering observations under controlled conditions and do not establish clinical efficacy.
2. **Input Limitations:** Physically destroyed documents (torn vital fields, completely washed-out ink) cannot be reliably interpreted by automated vision algorithms and must be escalated to direct clinician contact.
3. **Assistive Scope:** DawaAI is designed to assist clinicians in prescription review by highlighting uncertainty, not to replace the registered pharmacist.
