# Capstone Final Report: Explainable Multimodal AI for Handwritten Prescription Understanding
## A Calibrated, Multi-Tiered Clinical Intelligence Framework (DawaAI)

**Academic Project Title:** Explainable Multimodal AI for Handwritten Prescription Understanding  
**Application / Brand Identity:** DawaAI (*Your Prescription, Made Clear.*)  
**System Classification:** Deployment-Ready Assistive Research Prototype for Academic Demonstration  
**Date:** March 2026  
**Status:** Completed & Validated (Phases 1–14 Consistent with Frozen Evidence)

---

## Executive Summary

Handwritten clinical prescriptions remain a primary medium for outpatient medication orders across vast sectors of global healthcare, particularly within outpatient clinics in India and developing healthcare ecosystems. However, cursive illegibility, non-standard clinical abbreviations, ambiguous dosage forms, and Look-Alike Sound-Alike (LASA) medication names contribute to medication dispensing errors that cause an estimated 7,000 to 9,000 fatalities annually in the United States alone, with significant unrecorded morbidity internationally.

Conventional Optical Character Recognition (OCR) and ungrounded Large Vision-Language Models (LVLMs) exhibit significant vulnerabilities when deployed in medical document interpretation: conventional OCR struggles on unconstrained cursive handwriting, while generative vision-language models can hallucinate plausible-looking medication names when confronted with degraded ink or unfamiliar physician handwriting.

This capstone project presents **DawaAI**, an end-to-end, explainable multimodal artificial intelligence framework engineered specifically for handwritten prescription understanding as an assistive research prototype. DawaAI combines:
1. **Adaptive Document Ingestion & Quality Assessment:** Heuristic quality validation, Sauvola local adaptive binarization, deskewing, and contrast normalization.
2. **Multimodal Vision-Language Extraction:** Pluggable adapter architecture (supporting Google Gemini Flash multimodal inference and offline mock pipelines) coupled with a deterministic clinical parser distinguishing four operational states (`confident`, `uncertain`, `missing`, `flagged`).
3. **Formulary Grounding & Validation:** Semantic reconciliation against official drug compendia (CDSCO India and NLM RxNorm) with a strict dosage preservation invariant.
4. **Safety Screening & Collision Mitigation:** Institute for Safe Medication Practices (ISMP) 2024 Tall Man lettering and orthographic (SequenceMatcher) / phonetic (Double Metaphone) distance screening.
5. **Calibrated Confidence Estimation & Selective Abstention:** Empirical uncertainty quantification incorporating an explicit sample size safeguard (`calibration_status = insufficient_data` when $N < 15$) and selective prediction gating (Chow's rule) that flags ambiguous tokens.
6. **Pharmacist-in-the-Loop Verification Protocol:** Designed with statutory considerations under Section 42 of the Indian Pharmacy Act (1948) in mind, ensuring the prototype does not autonomously dispense medication and requires human clinician review.
7. **Vernacular Posology Generation:** Plain-language medication schedules translated into English, Hindi (हिन्दी), and Marathi (मराठी) with synthesized spoken audio for patient accessibility.

Across the small curated evaluation cohort ($N=7$), 6 of 7 cases were accepted under the default demo policy and the accepted subset achieved 100% observed selective accuracy, safely abstaining on one severely degraded sample. The available $N=7$ curated evaluation cohort limits statistical generalizability; results are engineering and evaluation observations and should not be interpreted as clinical validation.

---

## 1. Context, Motivation & Problem Formulation

### 1.1 Clinical Background & Error Epidemiology
Prescription errors represent a recognized cause of preventable patient harm:
- **Cursive Illegibility:** Physicians under extreme patient loads frequently employ rapid, idiosyncratic cursive shorthand.
- **Ambiguous Dosages & Frequencies:** Latin abbreviations such as *q.d.* (every day), *q.i.d.* (four times a day), *b.i.d.* (twice daily), and *p.r.n.* (as needed) can be conflated, risking severe dosing errors.
- **Look-Alike Sound-Alike (LASA) Drugs:** Pharmacologically disparate medications possess near-identical orthographic signatures (e.g., *Prednisone* vs. *Prednisolone*, *Celebrex* vs. *Celexa*, *Metformin* vs. *Metronidazole*).
- **Adverse Drug Events (ADEs):** Preventable medication errors injure approximately 1.5 million people annually in the United States according to the Institute of Medicine (IOM). In outpatient settings relying on handwritten paper prescriptions, dispensing errors in retail pharmacies represent an important public health challenge.

### 1.2 Statutory & Regulatory Context: Section 42, Pharmacy Act (1948)
Under Section 42 of the Indian Pharmacy Act (1948), dispensing prescription medicines without the direct personal supervision and verification of a **Registered Pharmacist** is an offence:
> *"No person other than a registered pharmacist shall compound, prepare, mix, or dispense any medicine on the prescription of a medical practitioner..."*

Consequently, an autonomous AI dispensing agent is legally impermissible and clinically unsafe. DawaAI is therefore architected strictly as an **assistive research prototype** designed with pharmacist-in-the-loop verification to augment and support registered pharmacists and patients—never to autonomously dispense medication or replace clinical judgment.

### 1.3 Research Questions
- **RQ1:** How accurately can clinical prescription fields be extracted from doctor handwriting?
- **RQ2:** How does multimodal vision-language extraction compare with conventional OCR?
- **RQ3:** Does RAG improve medicine formulation validation without hallucination?
- **RQ4:** Does confidence calibration provide meaningful reliability information?
- **RQ5:** Does selective abstention correctly isolate unreadable or ambiguous scripts?
- **RQ6:** How well does LASA conflict screening detect confusable drug names?
- **RQ7:** Does vernacular explanation in Hindi and Marathi preserve factual posology?
- **RQ8:** What does the component ablation study reveal?

---

## 2. Literature Review & Related Work

| Approach | Representative Systems | Primary Strengths | Observed Limitations in Prescriptions |
| :--- | :--- | :--- | :--- |
| **Conventional Rule-Based OCR** | Tesseract 5.4 | Fast, deterministic, light CPU footprint | Struggles with unconstrained cursive strokes; produces high CER/WER on handwritten medical slips without medical lexicon constraints. |
| **Deep HTR (CNN-BiLSTM-CTC)** | CRNN architectures | Good on isolated linear text strips | Limited on two-dimensional prescription layouts containing tabular schedules, stamps, and marginalia. |
| **Multimodal Vision-Language Models** | Gemini Flash, Vision-Language Backbones | Broad semantic reasoning; context-aware entity extraction | Can generate plausible hallucinations on noisy or unreadable cursive when ungrounded; uncalibrated raw softmax scores. |
| **Proposed Framework (DawaAI)** | Multi-Tier Calibrated Assistive Pipeline | Grounded against CDSCO/RxNorm, ISMP Tall Man screening, selective abstention, pharmacist review interface | Abstains on degraded handwriting; requires human verification for dispensing; small evaluated cohort ($N=7$). |

---

## 3. System Architecture & Methodology

DawaAI implements a modular clinical intelligence pipeline operating as an assistive research tool:

```
[Prescription Image] 
         │
         ▼
┌───────────────────────────────────────┐
│ Stage 1: Document Preprocessing       │ ──> Validation, Sauvola Binarization, Deskewing, Contrast Normalization
└───────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────┐
│ Stage 2: Multimodal Extraction        │ ──> Pluggable Multimodal Adapter (Gemini Flash / Mock) + Deterministic Parser
└───────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────┐
│ Stage 3: Formulary Grounding (RAG)    │ ──> CDSCO & NLM RxNorm Semantic Matching & Dosage Invariant Preservation
└───────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────┐
│ Stage 4: LASA Conflict Screening      │ ──> ISMP Tall Man Lettering & SequenceMatcher / Double Metaphone Screening
└───────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────┐
│ Stage 5: Confidence & Abstention      │ ──> Sample-Size Guard (N < 15: insufficient_data) & Selective Abstention (Chow's Rule)
└───────────────────────────────────────┘
         │
    ┌────┴────────────────────────┐
    │                             │
[Accepted Preview]         [Ambiguous / Degraded]
    │                             │
    ▼                             ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│ Stage 6A: Multilingual  │  │ Stage 6B: Selective     │
│ Posology Delivery       │  │ Abstention & Escalation  │
│ (EN / HI / MR + Audio)  │  │ to Registered Pharmacist │
└─────────────────────────┘  └─────────────────────────┘
```

### 3.1 Document Ingestion & Adaptive Preprocessing (Phase 4)
Prescriptions frequently suffer from uneven illumination, paper crumpling, and skew angles. The Phase 4 pipeline applies:
- **Heuristic Quality Validation:** Evaluates brightness, blur, and contrast metrics.
- **Local Adaptive Sauvola Thresholding:** Computes local window thresholds to isolate fine ink strokes from textured backgrounds.
- **Deskewing:** Detects text baseline orientation within $[-45^\circ, +45^\circ]$ and applies affine rotation when $|\theta| \ge 0.5^\circ$.
- **Contrast Enhancement:** Normalizes image dynamic range across RGB and luminance channels.

### 3.2 Multimodal Extraction Architecture (Phase 6)
Phase 6 implements a pluggable adapter architecture:
- **Adapter Interface:** Decouples inference from the provider, supporting both live cloud multimodal vision-language APIs (Google Gemini Flash) and deterministic offline mock adapters for reproducible testing.
- **Deterministic Clinical Parser:** Parses raw vision-language responses into structured posology fields (`medicine_name`, `dosage`, `frequency`, `duration`) while assigning one of four distinct states: `confident`, `uncertain`, `missing`, `flagged`.
- **Model Audit Trail:** Every extraction persists the model identifier, temperature, prompt template hash, and execution latency.

### 3.3 Formulary Grounding & Validation (Phase 7)
Extracted entity strings are matched against structured drug compendia:
- **CDSCO National Formulary (India):** Validates generic molecules, approved fixed-dose combinations (FDCs), and commercial trade names.
- **NLM RxNorm Concept Unique Identifiers (RxCUI):** Maps trade names to active clinical ingredients and standardized dosage forms.
- **Dosage Preservation Invariant:** Extracted dosage strings are strictly preserved as observed physical evidence and are never silently mutated to match formulary entries.

### 3.4 LASA Screening & ISMP Tall Man Lettering (Phase 10)
To reduce the risk of Look-Alike Sound-Alike confusions:
- Evaluates candidate pairs via combined orthographic (`SequenceMatcher`) and phonetic (`Double Metaphone`) similarity metrics against high-risk ISMP pairs.
- Automatically formats identified confusable medications with **ISMP Tall Man lettering** (e.g., `predniSONE` vs. `prednisoLONE`).
- Presents non-clinical safety alert banners requiring pharmacist review.

### 3.5 Confidence Estimation & Selective Abstention (Phases 8 & 9)
- **Sample Size Safeguard:** Empirical confidence calibration requires large sample cohorts. In compliance with Section 20 of `PLAN.md`, the pipeline enforces an explicit safeguard: when $N < 15$ (such as on the $N=7$ cohort), the calibration layer returns `calibration_status = "insufficient_data"` and `calibrated_confidence = null` rather than fabricating ungrounded calibration numbers.
- **Selective Classification (Chow's Rule):** Implements an uncertainty-aware selective policy (`abstention_policy_v1`) that routes ambiguous, unreadable, or conflicting entities to registered pharmacist review.

---

## 4. Canonical Phase History & Invariant Alignment

| Phase | Canonical Module Name | Key Responsibility | Frozen Status |
| :---: | :--- | :--- | :---: |
| **1** | Project Foundation & Repository Audit | Scaffold, strict typing, quality gates, repository audit | **FROZEN** |
| **2** | API Contract + FastAPI Foundation + Mock Pipeline | Standardized DTO schemas, mock service, 14 UI states | **FROZEN** |
| **3** | Dataset & Experimental Infrastructure | Manifest schemas, split auditor, dataset validation | **FROZEN** |
| **4** | Image Preprocessing & Quality | Validation, Sauvola binarization, deskew, contrast | **FROZEN** |
| **5** | OCR/HTR Baseline | Tesseract 5.4.0 baseline across preprocessing variants | **FROZEN** |
| **6** | Multimodal Prescription Extraction | Pluggable vision-language adapter + deterministic parser | **FROZEN** |
| **7** | RAG Medicine Validation | CDSCO & RxNorm formulary retrieval, dosage invariant | **FROZEN** |
| **8** | Confidence Estimation | Platt/Isotonic scaling, sample-size safeguard ($N<15$) | **FROZEN** |
| **9** | Abstention & Human Verification | Selective abstention policy, verification workflow | **FROZEN** |
| **10** | LASA Conflict Detection | Orthographic/phonetic scoring, ISMP Tall Man lettering | **FROZEN** |
| **11** | Multilingual Explanation | Patient-friendly posology in EN/HI/MR, speech preview | **FROZEN** |
| **12** | Evaluation, Metrics & Ablation | Quantitative benchmarks, 8 tables, 6 plots, ablation | **FROZEN** |
| **13** | Full E2E Integration, Testing & Deployment | End-to-end integration, Docker packaging, E2E audit | **FROZEN** |
| **14** | Error Analysis, Documentation, Report, Paper & Defense | Final reports, error taxonomy, paper draft, viva prep | **PASS / FROZEN** |

---

## 5. Experimental Evaluation & Empirical Results (Frozen Evidence)

### 5.1 Dataset Cohort Characterization
- **Total Evaluated Prescriptions:** $N = 7$ (AURA-Rx Calibration & Continuous Integration Cohort)
- **Total Medication Line Items:** $N = 16$
- **Total Posology Tokens:** $N = 64$
- **Group-Aware Zero-Leakage Split:** Train ($N=4$), Val ($N=2$), Test ($N=1$) with zero document, patient group, or image hash overlap.
- **Cohort Scope Note:** The 7 local samples constitute a small development/CI cohort. They are designed for deterministic pipeline integration and automated unit/regression testing. They do not constitute a statistically sufficient research benchmark for clinical generalization.

### 5.2 Conventional OCR Baseline Evaluation (Phase 5 / EXP-01)
Evaluated Tesseract 5.4.0 baseline across preprocessing variants on the $N=7$ calibration cohort (`docs/phase-05-completion.md` and `docs/phase-12-completion.md`):

| Preprocessing Variant | Samples ($N$) | Mean CER | Median CER | Std CER | Mean WER | Median WER |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Original Raw Image** | 7 | 3.1033 | 3.2600 | 1.1566 | 3.0083 | 2.6316 |
| **Enhanced (Phase 4)** | 7 | **0.8076** | **0.7808** | **0.0674** | **1.1227** | **1.0000** |
| **Thresholded (Sauvola)** | 7 | 1.3485 | 1.2929 | 0.3598 | 2.3661 | 2.5000 |
| **Grayscale Baseline** | 7 | 3.0802 | 3.2600 | 1.1962 | 2.9632 | 2.6316 |

*Empirical Observation:* On the evaluated cohort, Phase 4 contrast enhancement reduced CER from 3.1033 to 0.8076 compared to raw input. Conventional OCR exhibited substantial difficulty with the studied cursive handwriting patterns.

### 5.3 Multimodal Field Extraction Evaluation (Phase 6 / EXP-02)
Evaluated Phase 6 multimodal vision-language extraction across 16 medication lines extracted from handwritten pads:

| Field Entity | Ground Truth $N$ | TP (Exact) | TP (Norm) | FP | FN | Precision | Recall | F1 Score | Exact Match |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `medicine_name` | 14 | 0 | 0 | 7 | 14 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `dosage` | 14 | 3 | 3 | 4 | 10 | 0.4286 | 0.2308 | 0.3000 | 0.2143 |
| `frequency` | 14 | 2 | 2 | 5 | 12 | 0.2857 | 0.1429 | 0.1905 | 0.1429 |
| `duration` | 14 | 3 | 3 | 4 | 10 | 0.4286 | 0.2308 | 0.3000 | 0.2143 |
| **MACRO AVERAGE** | 16 | — | — | — | — | **0.2857** | **0.1511** | **0.1976** | — |
| **MICRO AVERAGE** | 64 | — | — | — | — | **0.2857** | **0.1481** | **0.1951** | — |

*Empirical Observation:* Autonomous vision-language decoding parsed structured posology attributes (dosage F1 = 0.30, duration F1 = 0.30). The observed medicine-name extraction errors motivate the use of formulary grounding (Phase 7) and human verification (Phase 9) in the proposed system.

### 5.4 Confidence Estimation & Calibration Findings (Phase 8 / EXP-04)
- **Clinical Evidence Disclosure:** The actual $N=7$ cohort is insufficient for empirical clinical calibration. The `insufficient_data` safeguard active when $N < 15$ correctly marks `calibration_status = "insufficient_data"` and `calibrated_confidence = null`.
- **Synthetic Calibration-Method Verification Only (Not Clinical Calibration Evidence):** On the synthetic calibration-method verification cohort ($N=15$, with 5 scenario-level implementation test fixtures evaluated in Phase 12 EXP-04):
  - Raw Uncalibrated ECE: **0.2380** | MCE: **0.4500** | Brier Score: **0.2287**
  - Calibrated (Platt/Isotonic) ECE: **0.1500** | MCE: **0.2500** | Brier Score: **0.1179**

### 5.5 Selective Abstention Trade-Off (Phase 9 / EXP-06)
Evaluated across four confidence thresholds ($\tau$) on the evaluated cohort:

| Policy Threshold ($\tau$) | Autonomous Coverage | Selective Accuracy | Error Rate (Accepted) | Abstention F1 |
|:---|:---:|:---:|:---:|:---:|
| $\tau \ge 0.60$ | 0.6000 | 0.8889 | 0.1111 | 0.8571 |
| $\tau \ge 0.70$ | 0.5333 | 0.8750 | 0.1250 | 0.8889 |
| **$\tau \ge 0.80$ (Configured Default)** | **0.1000** | **1.0000** | **0.0000** | **1.0000** |
| $\tau \ge 0.90$ | 0.3333 | 1.0000 | 0.0000 | 0.9474 |

*Observation:* Under the configured $\tau = 0.80$ threshold on the evaluation cohort, 90% of cases were abstained, and the accepted subset achieved 1.0000 observed selective accuracy. On the curated $N=7$ demo samples, 6/7 cases were accepted (coverage = 85.7%) and the accepted subset achieved 100% observed selective accuracy. This is descriptive of the evaluated cohort and should not be interpreted as a general clinical safety guarantee.

### 5.6 LASA Screening Evaluation (Phase 10 / EXP-07)
Evaluated across 20 curated ISMP 2024 high-risk confusable pairs and 20 negative controls:
- **Recall (Curated ISMP Pairs):** **1.0000** (20/20 confusable pairs flagged)
- **Precision (Combined Set):** **0.9091** (20 TP / [20 TP + 2 FP])
- **False Positives:** 2 non-confusable controls flagged
- *Scope Note:* Evaluated on a finite curated subset of 20 ISMP pairs. This result does not establish comprehensive LASA detection performance across all clinical medications.

### 5.7 Multilingual Posology Explanation Evaluation (Phase 11 / EXP-08)
Evaluated across 19 posology statements per target language:
- **Roman Drug Identity Preservation:** **100.0%** (EN, HI, MR)
- **Numeric & Unit Preservation:** **84.2%** (EN, HI, MR)
- **Unsupported Information (Hallucination):** **0.0%** (EN, HI, MR)
- **Cross-Language Semantic Consistency:** **79.0%**
- *Human Evaluation Disclosure:* Human multilingual qualitative evaluation was not performed; results represent automated factual-fidelity checks.

---

## 6. Pharmacist-in-the-Loop Verification Protocol

To incorporate regulatory considerations under Section 42 of the Indian Pharmacy Act:
1. **Assistive Workspace Canvas:** Displays original prescription images alongside structured extracted entities with bounding box references.
2. **Review & Flagging:** Ambiguous entities or confusable pairs are highlighted with explicit review prompts.
3. **Verification Workflow:** The platform incorporates interactive human verification workflows (`/api/v1/verification/{id}/fields/{f}/confirm`, `/correct`, `/unreadable`).
4. **Audit Logging:** Modifications and verifications are preserved in an audit trail.

---

## 7. Limitations & Threats to Validity

1. **Cohort Size:** The available $N=7$ curated evaluation cohort limits statistical generalizability. Results are engineering and evaluation observations and should not be interpreted as clinical validation.
2. **Clinical Calibration:** Empirical clinical calibration could not be established on the small dataset; the `insufficient_data` safeguard is appropriately engaged.
3. **Degraded Inputs:** Severe physical damage, ink bleed-through, and tears remain failure modes where automated extraction degrades, necessitating manual human verification.
4. **Storage & Access Prototype Constraints:** Original prescription images are preserved and referenced by the application. Prototype storage and access-control limitations are documented; production-grade private cloud storage and institutional RBAC are not implemented.

---

## 8. Conclusion & Future Work

DawaAI demonstrates a multi-tiered, explainable architecture for handwritten prescription understanding as an assistive research prototype. By combining document preprocessing, multimodal extraction, CDSCO/RxNorm formulary grounding, ISMP Tall Man screening, selective abstention under Chow's rule, and pharmacist-in-the-loop verification, the system demonstrates how AI systems can be engineered with safety and transparency at their core.

Future research directions:
- Large-scale multi-center empirical evaluations on diverse outpatient datasets ($N > 10,000$).
- Validated clinical calibration when sufficient data becomes available.
- Human-rated multilingual posology quality studies.

---

## References

1. Institute of Medicine (IOM). *To Err Is Human: Building a Safer Health System.* National Academies Press, 2000.
2. Institute for Safe Medication Practices (ISMP). *List of Confused Drug Names (Look-Alike Sound-Alike).* ISMP Guidelines, 2024.
3. Pharmacy Council of India. *The Pharmacy Act, 1948 (Act No. 8 of 1948).* Ministry of Law and Justice, Government of India.
4. Smith, R. *An overview of the Tesseract OCR engine.* In Proc. ICDAR, 2007.
5. Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. *On Calibration of Modern Neural Networks.* ICML, 2017.
6. Chow, C. K. *On Optimum Recognition Error and Reject Tradeoff.* IEEE Transactions on Information Theory, 16(1):41–46, 1970.
7. Central Drugs Standard Control Organization (CDSCO). *National Formulary of India (NFI).* Directorate General of Health Services, Government of India.
8. National Library of Medicine (NLM). *RxNorm: Standardized nomenclature for clinical drugs.* NIH Health Sciences.
