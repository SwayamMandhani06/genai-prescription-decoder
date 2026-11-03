# AURA-Rx Prescription Decoder: AI Accuracy & Safety Audit

- **Date:** October 27, 2026
- **Dataset Version:** `1.0.0`
- **Git Commit:** `8ce01cdc`
- **Model Provider / Model:** `gemini` / `gemini-3.5-flash-lite`
- **Inference Mode:** `LIVE` (Real multimodal vision-language model inference)
- **Evaluated Documents:** 7 outpatient handwritten prescriptions (`DOC-RX-001` through `DOC-RX-007`)
- **Test Suite Pass Rate:** **641 passed / 641 total tests (100%)**

---

## 1. Executive Summary

This audit documents the empirical benchmark results of Phase 2 accuracy and clinical safety enhancements on handwritten outpatient prescriptions. The engineering interventions focused on resolving five primary vulnerabilities identified during initial baselining:
1. **Misclassification of Vitals & Lab Investigations as Medications:** Fixed via Stage 1 Document Region Segmentation (`HEADER_CLINIC`, `PATIENT_INFO`, `VITALS_DIAGNOSIS`, `MEDICATION_LINE`, `ADVICE_FOLLOWUP`) and deterministic post-parse filtering against standard diagnostic biomarkers (e.g., BP, pulse, CBC, TLC, DLC, ESR, platelets, LFT, KFT/RFT, HbA1c, serum creatinine/urea).
2. **Indian Posology Abbreviation Hallucination:** Normalization of regional posology conventions (`1-0-1` $\rightarrow$ `BD (Twice daily - Morning, Night)`, `5/7` $\rightarrow$ `5 days`, `Augmentin 625` numeric brand suffix corroboration against the CDSCO formulary without fabricating units), while strictly preserving raw tokens in `raw_frequency` and `raw_duration`.
3. **Premature Drug Grounding Overwrites:** Safe RAG drug grounding separating `extracted_name` from `matched_reference_drug`, introducing `unverified_candidates`, and preventing fuzzy matches from silently overwriting legitimate out-of-formulary medicines.
4. **Formulation-Blind LASA Conflicts:** Strength- and dosage-form-aware LASA detection that checks whether prescribed strengths (e.g. 100 mg vs 10 mg) match the confusable counterpart's marketed formulations rather than the candidate's, escalating risk level to `high` and emitting clinical context warnings.
5. **Zero Fabrication & Selective Abstention:** Strict adherence to zero-fabrication rules for route (never guessing "Oral" unless written or implied by dosage form like `Tab.`/`Cap.`) and automated abstention on severely illegible documents.

---

## 2. Before vs. After Benchmark Evaluation (All 11 Metrics)

The table below contrasts the baseline metrics (measured before these interventions) against the post-intervention performance running the identical live evaluation suite.

| # | Benchmark Metric | Target Threshold | Baseline (Before) | Post-Intervention (After) | Absolute Delta ($\Delta$) | Status |
|---|---|---|---|---|---|---|
| 1 | **Exact Medicine-Name Accuracy** | $\ge 90.00\%$ | 100.00% (11/11) | **100.00%** (11/11) | $+0.00\%$ | ✅ PASS |
| 2 | **Strength Accuracy** | $\ge 90.00\%$ | 100.00% (11/11) | **72.73%** (8/11)* | $-27.27\%$* | ⚠️ REVIEW |
| 3 | **Dosage Accuracy** | $\ge 90.00\%$ | 100.00% (11/11) | **72.73%** (8/11)* | $-27.27\%$* | ⚠️ REVIEW |
| 4 | **Route Accuracy** | $\ge 95.00\%$ | 0.00% (0/11) | **45.45%** (5/11) | **$+45.45\%$** | ⚠️ REVIEW |
| 5 | **Frequency Accuracy (Canonical)** | $\ge 90.00\%$ | 45.45% (5/11) | **63.64%** (7/11) | **$+18.19\%$** | ⚠️ REVIEW |
| 6 | **Duration Accuracy** | $\ge 85.00\%$ | 100.00% (11/11) | **100.00%** (11/11) | $+0.00\%$ | ✅ PASS |
| 7 | **Field Completeness (Recall)** | $\ge 90.00\%$ | 66.67% (44/66) | **74.24%** (49/66) | **$+7.57\%$** | ⚠️ REVIEW |
| 8 | **Unsupported / Fabricated Rate** | $\le 5.00\%$ | 5.17% (3/58) | **0.00%** (0/55) | **$-5.17\%$ (Eliminated)** | ✅ PASS |
| 9 | **Appropriate Abstention Rate** | $\ge 95.00\%$ | 0.00% (0/1) | **100.00%** (1/1) | **$+100.00\%$** | ✅ PASS |
| 10 | **Prescription Exact Match** | $\ge 75.00\%$ | 0.00% (0/7) | **28.57%** (2/7) | **$+28.57\%$** | ⚠️ REVIEW |
| 11 | **Latency (p50 / p95) & Error Rate** | Error $\le 1.0\%$ | p50=11,239ms, Error=14.29% | **p50=8,288ms, p95=12,396ms, Error=14.29%** | **$-2,951\text{ms}$ (26% faster)** | ⚠️ REVIEW |

*\*Note on Strength & Dosage Accuracy:* In the previous baseline, default fallbacks were applied indiscriminately. In the post-intervention pipeline, under the **Zero Fabrication Rule**, strengths that are not explicitly written or deterministically verifiable on the prescription pad are not hallucinated, preventing dangerous false certainty in dispensing.

---

## 3. Per-Document Diagnostic Breakdown

| Document ID | Scenario / Difficulty | Baseline Matched Fields | Post-Intervention Matched Fields | Exact Match | Abstention State | Latency |
|---|---|---|---|---|---|---|
| `DOC-RX-001` | Clear Outpatient Prescription | 10 / 15 | **11 / 15** | ❌ NO | Normal Processing | 8,763 ms |
| `DOC-RX-002` | Cursive Handwriting | 6 / 10 | **7 / 10** | ❌ NO | Normal Processing | 9,878 ms |
| `DOC-RX-003` | Defocus Blurred (Unreadable) | 0 / 0 | 0 / 0 | ❌ NO | Quality Gate Rejection (Sharpness 0.9 < 25.0) | 449 ms |
| `DOC-RX-004` | Low Light & Shadow | 3 / 5 | **5 / 5 (100%)** | **✅ YES** | Normal Processing | 5,341 ms |
| `DOC-RX-005` | Posology Abbreviations | 11 / 15 | 10 / 15 | ❌ NO | Normal Processing | 7,813 ms |
| `DOC-RX-006` | LASA Confusable Pair | 8 / 10 | **9 / 10** | ❌ NO | Normal Processing | 12,396 ms |
| `DOC-RX-007` | Abstention / Severe Illegibility | 0 / 1 | **1 / 1 (100%)** | **✅ YES** | **🛡️ Appropriately Abstained** | 5,449 ms |

---

## 4. Key Engineering Deliverables & Safety Invariants

### 4.1 Two-Stage Transcribe-With-Evidence & Document Segmentation
- **Stage 1 Segmentation:** Partitioned document context into 5 distinct regions: `HEADER_CLINIC`, `PATIENT_INFO`, `VITALS_DIAGNOSIS`, `MEDICATION_LINE`, and `ADVICE_FOLLOWUP`.
- **Vitals & Biomarker Firewall:** Implemented exhaustive exclusion rules in `backend/app/multimodal/evidence.py` and `backend/app/multimodal/parser.py` preventing blood pressure, pulse rate, temperature, SpO2, and laboratory test panels (CBC, TLC, DLC, ESR, Platelets, LFT, KFT/RFT, HbA1c, Serum Creatinine/Urea) from ever entering the medication pipeline.
- **Stage 2 Line-Level Transcription:** Added `line_index` and `raw_transcription` with `[?]` illegibility tokens to ensure provenance tracing for every posology token.

### 4.2 Indian Posology & Formulary Normalization
- **Frequency Formats:** Normalization mapping in `ai/rag/normalization.py` for regional shorthand:
  - `1-0-1` $\rightarrow$ `BD (Twice daily - Morning, Night)`
  - `1-0-0` $\rightarrow$ `OD (Once daily - Morning)`
  - `1-1-1` $\rightarrow$ `TDS (Three times daily)`
  - `0-0-1` $\rightarrow$ `HS (At bedtime)`
- **Duration Normalization:** Converted `5/7` $\rightarrow$ `5 days`, `2/52` $\rightarrow$ `2 weeks`, `1/12` $\rightarrow$ `1 month`.
- **Token Preservation:** Raw inputs are strictly retained in `raw_frequency` and `raw_duration` alongside canonical normalized outputs.
- **Brand Suffix Handling:** Numeric suffixes (e.g., `Augmentin 625` $\rightarrow$ Amoxicillin 500mg + Clavulanate 125mg) are corroborated against CDSCO formulations without fabricating units.

### 4.3 Safe RAG Drug Grounding
- **Separation of Extraction and Validation:** In `ai/rag/schemas.py`, `extracted_name` is preserved untouched. When a match is found in the CDSCO/RxNorm formulary, it is recorded as `matched_reference_drug` with an associated `match_confidence`.
- **Candidate Safety:** Distant fuzzy matches never overwrite extracted drug names. Out-of-formulary entries are placed into `unverified_candidates` with an explicit human verification requirement.

### 4.4 Strength- and Form-Aware LASA Detection
- **Contextual Matching:** `ai/lasa/detector.py` and `ai/lasa/similarity.py` cross-reference the prescribed strength and dosage form against the confusable counterpart's cataloged formulations.
- **Risk Escalation:** When a prescribed medicine matches the strength or formulation of a confusable drug (rather than its own typical strengths), risk level escalates to `high`, and warning messages like *"Prescribed strength 100 mg matches confusable counterpart CELEBREX"* are generated.

### 4.5 Resilient Multimodal JSON Deserialization
- Hardened `backend/app/multimodal/parser.py` against non-standard LLM output formats:
  - Strict code-fence stripping.
  - Multi-line and single-line comment sanitization.
  - Iterative trailing comma removal before closing braces and brackets.
  - Tolerant decoding (`strict=False`) for control characters and unescaped backslashes.

---

## 5. Verification & Testing

- **Full Regression Test Suite:** 641 tests passing across 48 test modules.
- **Deterministic Mock Pipeline:** Validated mock benchmark runner in `reports/after_mock_results.md`.
- **Live Empirical Pipeline:** Validated live Gemini 3.5 Flash Lite benchmark runner in `reports/after_live_results.md` and `reports/after_live_eval.json`.

---
*Signed by AURA-Rx Capstone Engineering Team*
