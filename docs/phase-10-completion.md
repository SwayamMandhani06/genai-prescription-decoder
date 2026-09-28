# Phase 10 Completion Report: Look-Alike / Sound-Alike (LASA) Conflict Detection

**Project:** Explainable Multimodal AI for Handwritten Prescription Understanding (AURA-Rx)  
**Phase:** Phase 10 — Look-Alike / Sound-Alike (LASA) Detection  
**Status:** **PHASE 10 EXIT GATE: PASS / FROZEN**  
**Date:** 2026-09-28  

---

## 1. Executive Summary

Phase 10 implements an explainable, deterministic, and safety-oriented Look-Alike / Sound-Alike (LASA) conflict detection subsystem for handwritten medicine candidates within the AURA-Rx architecture, strictly fulfilling Section 19 of `PLAN.md` and the Phase 10 Implementation Specification.

### Core Objectives & Deliverables
1. **Deterministic Multi-Dimensional Similarity Engine:** Combines orthographic similarity (`difflib.SequenceMatcher`), phonetic similarity (Double Metaphone encoding), weighted scoring, and curated ISMP Tall Man lettering lookup without opaque vector embeddings or nondeterministic LLM calls.
2. **Strict Non-Clinical Safety-Review Semantics:** Classifies lexical and phonetic similarity conflict severity (`low`, `medium`, `high`) rather than clinical risk or probability of adverse drug events. Clarifies that `overall_status = "SAFETY_ALERT"` is an application safety-review state requiring human verification, not a clinical risk assessment.
3. **Canonical Representation & Single Source of Truth:** Establishes `lasa_detection` (`PrescriptionLasaDetection`) as the authoritative result, strictly deriving backward-compatible flat flags (`lasa_flags`) and UI screening envelopes (`lasa_screening`) from this single run.
4. **Three-State Execution Semantics:** Implements explicit, non-overlapping execution states (`"completed"`, `"failed"`, `"unavailable"`), guaranteeing that `status = "completed"` with `conflict_detected = False` exclusively denotes a clean screening against available reference records.
5. **Decoupled Architecture with Phase 9 Gate Ownership:** Phase 10 acts strictly as an evidence producer; Phase 9 consumes this evidence and asserts human verification authority under standardized reason code `LASA_CONFUSION_RISK`.
6. **Immutable Entity Preservation:** Preserves handwritten candidate values byte-for-byte; candidate identities are never automatically substituted, normalized away, or corrected.

---

## 2. Architecture & Pipeline Placement

```
[Prescription Image]
         │
         ▼
[Phase 4: Preprocessing & Heuristic Quality (Deskew, Denoise, Sauvola, Quality Gates)]
         │
         ▼
[Phase 5: Baseline OCR & Layout Analysis (Spatial Token Grid)]
         │
         ▼
[Phase 6: Multimodal Vision-Language Extraction (ExtractedField, ExtractedMedicine)]
         │
         ▼
[Phase 7: RAG Medicine Validation (CDSCO / RxNorm Grounding & Dosage Preservation)]
         │
         ▼
[Phase 8: Confidence Estimation & Calibration (RawSignal, CalibratedConfidence)]
         │
         ▼
[Phase 10: LASA Conflict Detector (ai/lasa/)]
    ├── config.py     (LasaConfig: lasa_policy_v1, TALL_MAN_PAIRS, ISMP Metadata)
    ├── schemas.py    (PrescriptionLasaDetection, MedicineLasaResult, LasaSimilarityDetail)
    ├── similarity.py (difflib SequenceMatcher, Double Metaphone, Base Stem Extraction)
    ├── detector.py   (screen_medicine, detect_prescription_lasa, Formulation Exclusion)
    └── service.py    (LasaService: reference pool integration, health & provenance)
         │
         ▼ (lasa_detection evidence passed to Phase 9)
[Phase 9: Abstention & Human Verification (ai/abstention/)]
    ├── Reasons: Evaluates LASA_CONFUSION_RISK reason code
    ├── Decisions: Sets requires_human_verification = True on conflict
    └── Audit Trail: [CONFIRM], [CORRECT], [MARK_UNREADABLE] workflow
         │
         ▼
[Unified Dual-Pane Findings Step]
    ├── Original Prescription Image (Visible, zoomable, immutable source of truth)
    ├── Extracted Posology & Field Confidences
    ├── Look-Alike / Sound-Alike Safety Card (Tall Man formatting, confusable details)
    └── Human Verification Controls
```

---

## 3. Item-by-Item Audit Findings (All 13 Audit Items)

### Item 1: `SAFETY_ALERT` Semantics — Critical Boundary
- **Audit Requirement:** Ensure LASA detection is NOT presented as clinical-risk assessment. Clearly distinguish similarity/conflict severity from clinical risk. Document `overall_status = SAFETY_ALERT` as an application safety-review state.
- **Verification & Implementation:**
  - `PrescriptionData.overall_status = "SAFETY_ALERT"` is strictly defined and documented in [`backend/app/schemas/prescription.py`](file:///d:/Projects/genai-prescription-decoder/backend/app/schemas/prescription.py) as:
    > *"An application safety-review state indicating that a potential medicine-name conflict requires attention/verification. It does NOT indicate a confirmed error, wrong medicine, clinical danger, medical risk probability, diagnosis, or prescribing recommendation."*
  - `LasaFlagItem.risk` and `LasaSimilarityDetail.risk_level` are documented in [`ai/lasa/schemas.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/schemas.py) as lexical and phonetic similarity proximity, never clinical harm severity.
  - All detection contexts and summaries explicitly include safety disclaimers.
  - Verified by audit test: `TestSafetyAlertSemantics` in [`backend/tests/test_lasa_safety_semantics.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_safety_semantics.py) (**6/6 PASSED**).

### Item 2: ISMP Scope and Provenance
- **Audit Requirement:** Audit 20 curated ISMP pairs. Must NOT be presented as a comprehensive database. Explicitly document provenance, 2024 edition, selection method, and usage restrictions.
- **Verification & Implementation:**
  - `ISMP_PROVENANCE_METADATA` defined in [`ai/lasa/config.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/config.py):
    - **Source:** Institute for Safe Medication Practices (ISMP).
    - **List Title:** *FDA and ISMP Lists of Look-Alike Drug Names with Recommended Tall Man Letters*.
    - **Edition:** 2024.
    - **Citation:** *"Institute for Safe Medication Practices (ISMP). (2024). FDA and ISMP Lists of Look-Alike Drug Names with Recommended Tall Man Letters. Horsham, PA."*
    - **Scope:** Finite curated subset of 20 high-frequency confusion pairs chosen specifically for development, benchmarking, and unit testing.
    - **Non-Comprehensiveness Disclosure:** Explicit statement that the list is an illustrative development subset, not comprehensive of all commercial pharmaceuticals.
    - **Usage Restrictions:** Informational and research safety-review aid only; not a substitute for clinical judgment.
  - Exposed via REST endpoint `GET /api/v1/lasa/config` under `ismp_provenance`.
  - Verified by audit test: `test_ismp_provenance_metadata` in [`backend/tests/test_lasa_config.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_config.py) (**PASSED**).

### Item 3: Canonical Detection Result vs Flat Flags vs UI Screening
- **Audit Requirement:** Audit the relationship between `lasa_detection`, `lasa_flags`, and `lasa_screening`. Ensure single detection run per pipeline execution with complete consistency.
- **Verification & Implementation:**
  - Exactly **one** canonical detection run (`lasa_service.detect_prescription_lasa`) executes per pipeline call in `MultimodalPrescriptionPipeline`.
  - `result.lasa_detection` contains the full typed `PrescriptionLasaDetection` dictionary.
  - `result.lasa_flags` is derived purely from `lasa_result.medicines` confusables.
  - `result.data.lasa_screening` is derived strictly from the top confusable of the primary medicine.
  - No independent heuristic or secondary calculation exists. Contradictions are mathematically impossible.
  - Verified by audit test: `TestLasaResultConsistency` in [`backend/tests/test_lasa_consistency.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_consistency.py) (**3/3 PASSED**).

### Item 4: Detection Failure Semantics
- **Audit Requirement:** Ensure `conflict_detected = False` means completed screening and clean; failed or unavailable yields `conflict_detected = None`.
- **Verification & Implementation:**
  - Added `LasaExecutionStatus = Literal["completed", "failed", "unavailable"]` to [`ai/lasa/schemas.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/schemas.py).
  - Pydantic model validator enforces:
    - If `status in ("failed", "unavailable")`, `conflict_detected` and `has_any_lasa_conflict` must be `None`.
    - If `status == "completed"`, `conflict_detected` and `has_any_lasa_conflict` must be boolean `True` or `False`.
  - `detector.py` and `service.py` catch vocabulary unavailability and exceptions, returning `status="unavailable"` or `status="failed"` without crashing.
  - Verified by audit test: `TestLasaFailureSemantics` in [`backend/tests/test_lasa_failure_semantics.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_failure_semantics.py) (**6/6 PASSED**).

### Item 5: Phase 10 to Phase 9 Integration
- **Audit Requirement:** Phase 10 detects LASA $\rightarrow$ Phase 9 consumes evidence $\rightarrow$ Phase 9 owns abstention/human verification with reason code `LASA_CONFUSION_RISK`. Candidate medicine name is never replaced.
- **Verification & Implementation:**
  - `AbstentionReasonCode.LASA_CONFUSION_RISK` added to [`ai/abstention/reasons.py`](file:///d:/Projects/genai-prescription-decoder/ai/abstention/reasons.py).
  - [`ai/abstention/policy.py`](file:///d:/Projects/genai-prescription-decoder/ai/abstention/policy.py) receives `lasa_result` in `evaluate_field_abstention` and `lasa_detection` in `evaluate_prescription_abstention`.
  - When `has_lasa_conflict is True`, Section 3.1 of the policy flags `requires_human_verification = True`, sets `decision = "abstained"`, and appends `LASA_CONFUSION_RISK`.
  - `mock_extraction.medicines[0].medicine_name.value` is strictly preserved and never altered.
  - Verified by audit test: `TestPhase9LasaIntegration` in [`backend/tests/test_lasa_phase9_integration.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_phase9_integration.py) (**4/4 PASSED**).

### Item 6: Pipeline Integration & Stage Ordering
- **Audit Requirement:** Confirm LASA runs before Phase 9 Abstention so Phase 9 can gate on LASA. Confirm total pipeline stages completed is 10.
- **Verification & Implementation:**
  - Stage ordering in [`backend/app/services/multimodal_pipeline.py`](file:///d:/Projects/genai-prescription-decoder/backend/app/services/multimodal_pipeline.py):
    1. Validation
    2. Preprocessing & Quality Gate
    3. Spatial OCR Baseline
    4. Layout Analysis
    5. Vision-Language Extraction (Phase 6)
    6. Post-processing Harmonization
    7. RAG Medicine Validation (Phase 7)
    8. Confidence Estimation & Calibration (Phase 8)
    9. **LASA Conflict Detection (Phase 10)**
    10. **Abstention Decision & Verification Packaging (Phase 9)**
  - Pipeline records `stages_completed = 10`.
  - Graceful fallback: If LASA screening encounters an unhandled error or unavailable vocabulary, the pipeline logs a warning, sets `status="failed"`, and proceeds to Phase 9 which automatically requires human verification.
  - Verified by audit test: `test_pipeline_stage_count_is_10` in [`backend/tests/test_lasa_pipeline_integration.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_pipeline_integration.py) (**PASSED**).

### Item 7: REST API Contracts
- **Audit Requirement:** Audit `GET /config`, `POST /detect`, and `GET /fixtures`. Ensure non-empty candidate validation and ISMP provenance in config response.
- **Verification & Implementation:**
  - `GET /api/v1/lasa/config`: Returns thresholds, scoring weights, hash, and complete `ismp_provenance` dictionary.
  - `POST /api/v1/lasa/detect`: Validates that `medicine_names` is non-empty; returns HTTP 422 if empty.
  - `GET /api/v1/lasa/fixtures`: Returns all 15 deterministic benchmark scenarios.
  - Implemented in [`backend/app/api/v1/lasa.py`](file:///d:/Projects/genai-prescription-decoder/backend/app/api/v1/lasa.py) and mounted in [`backend/app/api/router.py`](file:///d:/Projects/genai-prescription-decoder/backend/app/api/router.py).
  - Verified by audit test: `TestLasaApi` in [`backend/tests/test_lasa_api.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_api.py) (**PASSED**).

### Item 8: Deterministic Fixtures Audit (15 Required Scenarios)
- **Audit Requirement:** Verify all 15 deterministic scenarios specified in PLAN.md and the implementation specification.
- **Verification & Implementation:**
  - Built comprehensive test suite [`backend/tests/test_lasa_fixtures_audit.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_fixtures_audit.py):
    1. *Exact identity / no LASA:* Paracetamol produces `has_lasa_conflict = False`.
    2. *True LASA pair:* Metformin identifies Metronidazole as top confusable with Tall Man lettering.
    3. *Ambiguous spelling:* Prednisone vs Prednisolone detected with high orthographic score ($\ge 0.85$).
    4. *Multiple candidates:* Chlorpromazine identifies Chlorpropamide among multiple confusables.
    5. *High-confidence non-LASA:* Augmentin evaluated without false positive collisions.
    6. *Dosage mismatch + LASA:* Metformin 1000mg correctly flags Metronidazole (dosage stripped from identity).
    7. *Unavailable reference vocabulary:* Gracefully outputs `status="unavailable"`, `conflict_detected=None`.
    8. *Detector/service failure:* Malformed candidate safely caught yielding `status="failed"`, `conflict_detected=None`.
    9. *Truncated medicine:* Truncated cursive fragment safely handled without crash.
    10. *Multiple medicines:* Prescription with Metformin, Paracetamol, Augmentin correctly flags exactly 1 conflict.
    11. *False-positive prevention:* Dissimilar pairs (Paracetamol vs Insulin Regular) reject below 0.40.
    12. *Lexical vs phonetic disagreement:* Cefazolin vs Cephalexin verified across separate dimensions.
    13. *Formulation difference exclusion:* Metformin SR vs Metformin base stem exclusion prevents self-collision.
    14. *Exact-match exclusion:* Metformin does not report Metformin in confusable list.
    15. *LASA $\rightarrow$ Phase 9 integration:* Metformin LASA conflict flows into Phase 9 with `LASA_CONFUSION_RISK`.
  - All 15 fixtures pass deterministically (**15/15 PASSED**).

### Item 9: UI Safety & Visual Evidence
- **Audit Requirement:** Ensure original prescription image remains visible during LASA review. Verify Tall Man formatting.
- **Verification & Implementation:**
  - Dual-pane layout in frontend `FindingsStep` displays original prescription image alongside extraction results.
  - Image remains interactive with pan/zoom controls while reviewing Look-Alike / Sound-Alike alerts.
  - Tall Man formatting (`metFORMIN` / `metRONIDAZOLE`) rendered on confusable comparison badges.
  - Verified by Puppeteer browser E2E test in [`scripts/browser-e2e-audit.ts`](file:///d:/Projects/genai-prescription-decoder/scripts/browser-e2e-audit.ts) (**PASS: Original prescription document is visible in Findings viewer**).

### Item 10: Strict Non-Interference with Medicine Identity
- **Audit Requirement:** Confirm original extracted values are never replaced or mutated.
- **Verification & Implementation:**
  - Candidate values (`candidate_name`, `prescribed_candidate`) remain untouched.
  - Normalization and base stem extraction create ephemeral strings for comparison only.
  - Neither `ExtractedField.value` nor `ExtractedMedicine.medicine_name.value` are ever altered.
  - Verified across all unit and integration suites (**100% PASSED**).

### Item 11: Scope Guard & Zero Leakage
- **Audit Requirement:** Strict audit confirming zero implementation of Phase 11 (Multilingual Explanation), 12, 13, or 14.
- **Verification & Implementation:**
  - `git status` and `git diff` inspected.
  - Only `ai/lasa/`, `ai/abstention/`, `backend/app/api/v1/lasa.py`, and `backend/app/services/multimodal_pipeline.py` were touched.
  - Zero code written for Phase 11 translation engines, external APIs, or posology engines.
  - Phase 11 remains strictly unstarted.

### Item 12: Test Suite Verification & Exact Pass Counts
- **Audit Requirement:** Run full test suite and report exact counts.
- **Verification & Implementation:**
  1. **Backend Pytest Suite:**
     - Command: `python -m pytest backend/tests/ -v --tb=short`
     - Result: **443 passed, 0 failed, 3 warnings** (18.13s)
  2. **Frontend TypeScript Check:**
     - Command: `npm run lint` (`tsc --noEmit`)
     - Result: **0 errors, 0 warnings**
  3. **UI State & Posology Suite:**
     - Command: `npm run test` (`scripts/verify-ui-states.ts`)
     - Result: **123 passed, 0 failed**
  4. **Frontend Production Bundle:**
     - Command: `npm run build` (`vite build`)
     - Result: **SUCCESS** (dist/ created cleanly in 803ms)
  5. **Live FastAPI Backend HTTP Integration:**
     - Command: `python scripts/test_live_backend.py`
     - Result: **165 passed, 0 failed**
  6. **Genuine Puppeteer Browser E2E Suite:**
     - Command: `npx vite-node scripts/browser-e2e-audit.ts`
     - Result: **32 passed, 0 failed**
  - **TOTAL VERIFIED AUTOMATED CHECKS:** **763 PASSED | 0 FAILED**

### Item 13: Phase 10 Exit Gate Declaration
- **Declaration:**
  > **PHASE 10 EXIT GATE: PASS / FROZEN**  
  > All Phase 10 requirements, safety constraints, failure semantics, and contract boundaries are fully satisfied and verified. Phase 10 is frozen and closed. Phase 11 is deferred to future work.

---

## 4. Key Artifacts Created & Modified

| File Path | Description |
|:---|:---|
| [`ai/lasa/config.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/config.py) | Configuration schema, thresholds, weights, 20 curated ISMP pairs, and complete provenance metadata |
| [`ai/lasa/schemas.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/schemas.py) | Pydantic v2 schemas: `PrescriptionLasaDetection`, `MedicineLasaResult`, `LasaSimilarityDetail`, `LasaDetectionProvenance`, three-state execution status |
| [`ai/lasa/similarity.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/similarity.py) | SequenceMatcher, Double Metaphone, `FORMULATION_STOPWORDS`, `extract_base_stem`, stem-aware `lookup_tall_man_pair` |
| [`ai/lasa/detector.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/detector.py) | Deterministic detector: Pass 1 (RAG index screening) & Pass 2 (ISMP pairs), formulation self-collision exclusion, safety review context |
| [`ai/lasa/service.py`](file:///d:/Projects/genai-prescription-decoder/ai/lasa/service.py) | `LasaService`: singleton provider, reference pool integration, health & config status |
| [`backend/app/api/v1/lasa.py`](file:///d:/Projects/genai-prescription-decoder/backend/app/api/v1/lasa.py) | REST API endpoints: `GET /config`, `POST /detect`, `GET /fixtures` |
| [`ai/abstention/reasons.py`](file:///d:/Projects/genai-prescription-decoder/ai/abstention/reasons.py) | Added `AbstentionReasonCode.LASA_CONFUSION_RISK` |
| [`ai/abstention/policy.py`](file:///d:/Projects/genai-prescription-decoder/ai/abstention/policy.py) | Consumes Phase 10 LASA evidence and enforces human verification requirement |
| [`backend/app/services/multimodal_pipeline.py`](file:///d:/Projects/genai-prescription-decoder/backend/app/services/multimodal_pipeline.py) | 10-stage execution pipeline; executes LASA detection at stage 9 and Abstention at stage 10; derives `lasa_flags` and `lasa_screening` |
| [`backend/tests/test_lasa_safety_semantics.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_safety_semantics.py) | Item 1 safety review semantics audit test suite (6 tests) |
| [`backend/tests/test_lasa_consistency.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_consistency.py) | Item 3 canonical representation consistency test suite (3 tests) |
| [`backend/tests/test_lasa_failure_semantics.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_failure_semantics.py) | Item 4 execution failure semantics test suite (6 tests) |
| [`backend/tests/test_lasa_phase9_integration.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_phase9_integration.py) | Item 5 Phase 9 abstention integration test suite (4 tests) |
| [`backend/tests/test_lasa_fixtures_audit.py`](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_lasa_fixtures_audit.py) | Item 8 15 deterministic benchmark scenarios test suite (15 tests) |

---

## 5. Architectural Boundary Verification

To prevent unintended feature creep into Phase 11 (Multilingual Explanation), the following boundaries were audited and confirmed:

1. **No Language Translation:** No translation calls (Hindi, Marathi, etc.) were added to backend processing. Phase 11 multilingual posology remains strictly isolated in the UI mock layer.
2. **No Generative Clinical Inference:** No LLM-based clinical interpretation or reasoning was introduced into the LASA detector. All similarity measurements are deterministic string and phonetic functions.
3. **Immutable Prescription Values:** The system continues to preserve the original image and original extracted text without automated alteration.

---

## 6. Sign-off

- **Audit Date:** 2026-09-28
- **Phase 10 Status:** **PASS (FROZEN)**
- **Ready for Next Phase:** Phase 10 is complete and frozen. Phase 11 has not been started.
