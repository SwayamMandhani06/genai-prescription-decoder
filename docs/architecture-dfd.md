# DawaAI Architecture & Data Flow Diagrams (DFDs)
## Level 0, Level 1, and Level 2 System Decompositions

**System:** DawaAI — Explainable Multimodal AI for Handwritten Prescription Understanding  
**Document Classification:** Architectural Specification & Data Flow Engineering  
**System Classification:** Deployment-Ready Assistive Research Prototype for Academic Demonstration  
**Version:** 1.0 (Frozen Architecture)  
**Date:** March 2026

---

## 1. System Overview & Boundaries

DawaAI is architected as an assistive clinical intelligence research prototype. It enforces a strict separation of concerns between raw image conditioning, multimodal feature extraction, medical knowledge graph grounding, uncertainty gating, and human clinician verification, designed with regulatory considerations under Section 42 of the Indian Pharmacy Act (1948) in mind.

---

## 2. Level 0 DFD: System Context Diagram

The Level 0 context diagram defines the boundary between external entities (Patients, Registered Pharmacists, External Medical Compendia) and the DawaAI system core.

```mermaid
flowchart TD
    subgraph ExternalEntities["External Entities"]
        Patient["Patient / Caregiver"]
        Pharmacist["Registered Pharmacist"]
        CDSCO_DB[("CDSCO National Formulary DB")]
        RxNorm_DB[("NLM RxNorm Compendium")]
    end

    subgraph DawaAI_Boundary["DawaAI System Boundary (Assistive Prototype)"]
        CoreEngine(("DawaAI Prescription Platform"))
    end

    Patient -->|"Uploads prescription image (JPEG/PNG)"| CoreEngine
    CoreEngine -->|"Presents vernacular posology & speech guidance (EN/HI/MR)"| Patient

    CoreEngine -->|"Queries drug candidates & trade names"| CDSCO_DB
    CDSCO_DB -->|"Returns approved molecules & fixed-dose combinations"| CoreEngine

    CoreEngine -->|"Queries active ingredients & clinical dosages"| RxNorm_DB
    RxNorm_DB -->|"Returns normalized RxCUIs & dosage forms"| CoreEngine

    CoreEngine -->|"Renders dual-pane stroke canvas, flagged alerts & LASA warnings"| Pharmacist
    Pharmacist -->|"Submits verified field confirmations/corrections"| CoreEngine
    CoreEngine -->|"Emits verified verification record & audit trail"| Pharmacist
```

---

## 3. Level 1 DFD: Macro Subsystem Decomposition

The Level 1 DFD decomposes the core engine into its primary functional processes, data stores, and inter-process data flows matching the canonical phase history.

```mermaid
flowchart TD
    RawImage[Prescription Image] --> P1["1.0 Document Ingestion & Adaptive Preprocessing (Phase 4)"]
    
    subgraph S1["Image Conditioning"]
        P1 -->|"Conditioned Enhanced / Binarized Image & Skew Angle"| P2["2.0 Multimodal Vision-Language Extraction (Phase 6)"]
    end

    subgraph S2["Feature Extraction & Parsing"]
        P2 -->|"Structured Posology Fields & Bounding Box Coordinates"| P3["3.0 Formulary Grounding & Validation (Phase 7)"]
    end

    subgraph S3["Clinical Verification"]
        DB1[("CDSCO & RxNorm Compendia")] <-->|"Fuzzy Entity Resolution & RxCUI"| P3
        P3 -->|"Validated Molecules with Dosage Invariant Preserved"| P4["4.0 LASA Conflict Screening (Phase 10)"]
        DB2[("ISMP 2024 Confusable Pairs")] -->|"Curated Confusable Set"| P4
    end

    subgraph S4["Safety & Abstention"]
        P4 -->|"Screened Entities with Tall Man Lettering"| P5["5.0 Confidence Estimation & Selective Abstention (Phases 8 & 9)"]
        P5 -->|"Ambiguous / Low Confidence (Chow's Rule)"| FlowAbstain["Abstention & Flagging Alert"]
        P5 -->|"Accepted Preview Threshold"| FlowVerified["Accepted Structured Prescription"]
    end

    subgraph S5["Output & Vernacular Delivery"]
        FlowVerified --> P6["6.0 Multilingual Posology & Speech Engine (Phase 11)"]
        P6 -->|"Structured Daily Regimen (Morning/Noon/Eve/Night)"| P7["7.0 Dual-Pane Canvas & Pharmacist Review (Phases 9 & 11)"]
        FlowAbstain --> P7
    end

    subgraph S6["Pharmacist-in-the-Loop Verification"]
        Pharmacist["Registered Pharmacist"] <-->|"Review Stroke Bounding Boxes & Submit Confirm/Correct"| P7
        P7 -->|"Persist Verification Events"| AuditLog[("Audit Trail Record")]
        P7 -->|"Assistive Posology Advice & Spoken Audio"| FinalPatient["Patient / Caregiver"]
    end
```

---

## 4. Level 2 DFDs: Detailed Subsystem Decompositions

### 4.1 Process 1.0: Document Preprocessing Pipeline (Phase 4)
```mermaid
flowchart TD
    InputRaw["Raw Image Input (RGB)"] --> P1_1["1.1 Heuristic Quality & Geometry Validation"]
    P1_1 -->|"Valid Canvas"| P1_2["1.2 Sauvola Local Adaptive Thresholding"]
    P1_1 -->|"Grayscale Channel"| P1_3["1.3 Contrast Stretching & Normalization"]
    P1_3 -->|"Enhanced Image"| P1_4["1.4 Radon Transform Deskew Estimator"]
    P1_4 --> OutputP1["Normalized Preprocessed Artifacts"]
```

### 4.2 Process 2.0: Multimodal Extraction (Phase 6)
```mermaid
flowchart TD
    PreprocImage["Preprocessed Image"] --> P2_1["2.1 Pluggable Multimodal Adapter (Gemini Flash / Mock)"]
    P2_1 -->|"Raw Vision-Language Output"| P2_2["2.2 Deterministic Clinical Parser"]
    P2_2 --> P2_3["2.3 4-State Status Assignment (confident / uncertain / missing / flagged)"]
    P2_3 --> OutputP2["Structured Extraction Payload with Model Audit Trail"]
```

### 4.3 Process 3.0 & 4.0: Formulary Grounding & LASA Screening (Phases 7 & 10)
```mermaid
flowchart TD
    InTokens["Extracted Posology Fields"] --> P3_1["3.1 CDSCO National Formulary Matcher"]
    InTokens --> P3_2["3.2 RxNorm Active Ingredient & RxCUI Matcher"]
    P3_1 --> P3_3["3.3 Strict Dosage Observation Preservation Invariant"]
    P3_2 --> P3_3
    P3_3 -->|"Validated Drug Candidate"| P4_1["4.1 SequenceMatcher Orthographic Similarity"]
    P3_3 -->|"Phonetic Contours"| P4_2["4.2 Double Metaphone Phonetic Similarity"]
    ISMP_Pairs[("Curated ISMP 2024 Pairs")] --> P4_1
    ISMP_Pairs --> P4_2
    P4_1 --> P4_3["4.3 ISMP Tall Man Lettering Formatting"]
    P4_2 --> P4_3
    P4_3 --> OutputP4["Formulary-Grounded & Screened Entities"]
```

### 4.4 Process 5.0: Confidence Estimation & Selective Abstention (Phases 8 & 9)
```mermaid
flowchart TD
    CandidateIn["Clinical Entities"] --> P5_1{"5.1 Sample Size Check (N < 15?)"}
    P5_1 -->|"Yes (N < 15, e.g. N=7 cohort)"| P5_2["5.2 Enforce calibration_status = insufficient_data"]
    P5_1 -->|"No (N >= 15)"| P5_3["5.3 Platt / Isotonic Calibration Computation"]
    P5_2 --> P5_4{"5.4 Chow's Rule Selective Policy (abstention_policy_v1)"}
    P5_3 --> P5_4
    P5_4 -->|"Ambiguous / Below Threshold"| AbstainBranch["Mark: ABSTAINED / Flagged for Verification"]
    P5_4 -->|"Meets Threshold"| AcceptBranch["Mark: ACCEPTED (Assistive Preview)"]
    AbstainBranch --> OutputP5["Prescription Verification Payload"]
    AcceptBranch --> OutputP5
```

### 4.5 Process 7.0: Dual-Pane Grounding & Human Verification (Phase 9)
```mermaid
flowchart TD
    VerifiedPayload["Prescription Payload + Bounding Boxes"] --> P7_1["7.1 Interactive SVG Coordinate Mapper"]
    OriginalImage["Preserved Original Prescription Canvas"] --> P7_1
    P7_1 --> P7_2["7.2 Synchronized Dual-Pane Viewer"]
    
    Pharmacist["Registered Pharmacist"] <-->|"Inspect stroke bounding box"| P7_2
    Pharmacist -->|"POST /verification/{id}/fields/{f}/confirm"| P7_3["7.3 Confirm Action Handler"]
    Pharmacist -->|"POST /verification/{id}/fields/{f}/correct"| P7_4["7.4 Correct Action Handler (Preserves Original)"]
    Pharmacist -->|"POST /verification/{id}/fields/{f}/unreadable"| P7_5["7.5 Mark Unreadable Handler"]
    
    P7_3 --> AuditLogDB[("Verification State & Audit Trail")]
    P7_4 --> AuditLogDB
    P7_5 --> AuditLogDB
```

---

## 5. Prototype Storage, Security & Regulatory Boundaries

1. **Storage & Access Prototype Constraints:** Original prescription images are preserved and referenced by the application. Prototype storage and access-control limitations are documented; production-grade private cloud storage and institutional RBAC are not implemented.
2. **Statutory Non-Dispensing Boundary:** In alignment with Section 42 of the Indian Pharmacy Act (1948), the system operates strictly as an assistive research prototype. It does not autonomously dispense medication or serve as a clinical diagnostic authority.
3. **Audit Trail Logging:** Human verification actions (`confirm`, `correct`, `unreadable`) are recorded in an audit trail ledger alongside timestamps and field-level modification details.
