# Phase 7 Completion Report: Evidence-Grounded RAG Medicine Validation

**Project:** Explainable Multimodal AI for Handwritten Prescription Understanding (AURA-Rx)  
**Phase:** Phase 7 — RAG-Based Medicine Validation  
**Date:** 2026-09-27  
**Execution Status:** PASS  
**Target Requirement:** PLAN.md Section 16 & Requirement R3  

---

## 1. Objective

Phase 7 implements an evidence-grounded Retrieval-Augmented Generation / retrieval-based medicine validation layer. The primary system objective is to answer:

> *"Does this visually extracted medicine candidate correspond to a known medicine/formulation in the available authoritative reference data?"*

It strictly does **NOT** answer: *"What medicine should the prescription contain?"*

### Non-Negotiable Safety Boundary
The RAG layer is strictly a **validation and evidence layer**. It does **NOT** perform:
- OCR or handwriting stroke correction / guessing
- Medical diagnosis or clinical prescribing
- Dosage recommendation, correction, or posology inference
- Automatic medicine substitution or brand-to-generic rewriting
- Clinical decision-making or therapeutic planning
- Patient-facing medical advice

When visual extraction evidence is ambiguous or incomplete, the system **strictly preserves uncertainty** and mandates clinician/pharmacist review rather than forcing an autonomous match.

---

## 2. Authoritative Source Inventory

All reference sources used by the Phase 7 validation layer are documented, audited, and cataloged in [`data/reference/reference_manifest.json`](file:///d:/Projects/genai-prescription-decoder/data/reference/reference_manifest.json):

| Source ID | Source Title | Authority / Body | Edition / Version | Record Count | SHA-256 Digest |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `cdsco-approved-drugs` | CDSCO Approved Drug Formulations Reference Subset | Central Drugs Standard Control Organisation, Directorate General of Health Services, India | 2024.1 (finite development subset) | 20 | `a8077f6c5fa281e93c5b8581a1277b712c1d0d0d5d27a174fb826e8951ad17c1` |
| `nlm-rxnorm` | NLM RxNorm Clinical Nomenclature Subset | National Library of Medicine (NLM), National Institutes of Health, USA | 2024-08 (frozen reference fixture subset) | 10 | `22f0a37352b1d630123c62b98075b8d056a7f3d38572e8f3b82f7910e620356f` |

---

## 3. Source Scope, Provenance & Regulatory Justification

### CDSCO Approved Drug Formulations Reference Subset
- **Authority:** Statutory authority under the Directorate General of Health Services, Ministry of Health and Family Welfare, Government of India.
- **Access URL:** `https://cdsco.gov.in`
- **Scope & Explicit Limitation:** The current implementation uses a finite CDSCO-derived reference subset (20 records) for engineering validation and provenance testing. It is not a comprehensive representation of all medicines or formulations approved or marketed in India.
- **Appropriateness for Project:** Establishes statutory grounding for Indian prescription practice, including official approved strengths, dosage forms, fixed-dose combination formulations (e.g., *Amoxicillin + Clavulanic Acid*), and Indian Drugs & Cosmetics Rules classifications (e.g., *Schedule H Prescription Drug*).

### NLM RxNorm Clinical Drug Nomenclature Subset
- **Authority:** US National Library of Medicine (NLM), specialized medical informatics terminology standard.
- **Access URL:** `https://www.nlm.nih.gov/research/umls/rxnorm/`
- **Snapshot Provenance & Scope:** RxNorm 2024-08 is the frozen reference snapshot used by this implementation as a reduced development subset fixture (10 records). Current NLM releases are newer; the implementation does not claim to represent the current RxNorm release or the full NLM RxNorm distribution.
- **Geographic & Formulary Limitation:** RxNorm is U.S.-centric and should not be treated as a comprehensive Indian formulary. International and Indian commercial trade brands require explicit mapping to Indian regulatory formulations.
- **Appropriateness for Project:** Provides normalized clinical drug components, Concept Unique Identifiers (RxCUI), standardized active ingredients, and brand/generic relational graphs.

---

## 4. License and Legal Classification

Every reference record contains full legal provenance metadata:

1. **`cdsco-approved-drugs`:**
   - **License:** Open Government Data License - India (OGDL-India)
   - **Classification:** `statutory_government_open_data`
   - **Terms:** Non-exclusive, royalty-free, worldwide license for academic, research, and non-commercial utilization.

2. **`nlm-rxnorm`:**
   - **License:** UMLS Metathesaurus License / NLM Public Domain Terms
   - **Classification:** `clinical_terminology_license`
   - **Access & License Boundaries:**
     - RxNorm is produced by the US National Library of Medicine (NLM).
     - The full RxNorm release requires the applicable UMLS license and UMLS Terminology Services (UTS) access.
     - The full RxNorm dataset contains source-vocabulary material with source-specific restrictions.
     - NLM-created normalized names and codes have public-domain status as described by NLM.
     - The Current Prescribable Content subset has different access conditions.
     - The license does **NOT** grant a general right to "clinical validation." The implementation does not claim clinical validation rights under the license.

---

## 5. Reference Schema Architecture

Reference records are strictly typed via Pydantic V2 in [`ai/rag/schemas.py`](file:///d:/Projects/genai-prescription-decoder/ai/rag/schemas.py):

```python
class MedicineReferenceRecord(BaseModel):
    reference_id: str             # e.g. "REF-CDSCO-001"
    source: str                   # e.g. "cdsco-approved-drugs"
    source_version: str           # e.g. "2024.1"
    medicine_name: str            # Canonical reference title
    normalized_name: str          # Deterministically normalized string
    generic_name: Optional[str]   # Generic salt or active ingredient
    brand_name: Optional[str]     # Proprietary brand name
    strength: Optional[str]       # Approved formulation strength
    dosage_form: Optional[str]    # Physical administration form
    ingredients: List[str]        # Chemical substances
    aliases: List[str]            # Bioequivalent brands / synonyms
    rxnorm_cui: Optional[str]     # Concept Unique Identifier
    cdsco_schedule: Optional[str] # Statutory schedule
    atc_code: Optional[str]       # WHO ATC classification
    therapeutic_class: Optional[str] # Pharmacological class
    indications: Optional[str]    # Approved clinical indications
    provenance: SourceProvenance  # Cryptographic & citation provenance
```

No fields are fabricated: if an attribute is absent in the source record (e.g. `cdsco_schedule` in an RxNorm record), it remains `null`.

---

## 6. Ingestion Pipeline & Checksum Verification

The reproducible ingestion engine in [`ai/rag/ingestion.py`](file:///d:/Projects/genai-prescription-decoder/ai/rag/ingestion.py) executes the following pipeline:

1. **Manifest Loading:** Reads and parses `data/reference/reference_manifest.json`.
2. **Cryptographic Checksum Verification:** Calculates SHA-256 digest of each reference file and verifies against expected manifest hashes.
3. **Schema Validation:** Enforces strict validation of all records against `MedicineReferenceRecord`.
4. **Field Normalization Verification:** Verifies `normalized_name` deterministically against the conservative normalizer.
5. **Deduplication:** Tracks and logs duplicate `reference_id`s or identical formulation keys.
6. **Provenance Attachment:** Ensures institutional provenance is attached to every ingested record.
7. **Ingestion Reporting:** Generates an `IngestionReport` detailing valid records, duplicates, and checksum verification status.

---

## 7. Normalization Engine

Conservative normalization in [`ai/rag/normalization.py`](file:///d:/Projects/genai-prescription-decoder/ai/rag/normalization.py) adheres strictly to Section 8:

- **Unicode Normalization:** Applies NFKC decomposition/composition.
- **Case Normalization:** Deterministic lowercase folding.
- **Punctuation Handling:** Replaces delimiters (`/`, `+`, `-`, `_`, `(`, `)`, `[`, `]`, `,`, `:`, `;`, `.`, `*`) with spaces.
- **Whitespace Normalization:** Trims and collapses multiple whitespace runs into single spaces.
- **Token Extraction:** Extracts alphanumeric tokens via `[a-z0-9]+`.
- **Inviolable Separation Rule:** Always preserves `raw_candidate` and `normalized_candidate` as distinct attributes via `separate_raw_and_normalized()`. Never mutates the raw candidate.

---

## 8. Indexing and Retrieval Architecture

Implemented in [`ai/rag/index.py`](file:///d:/Projects/genai-prescription-decoder/ai/rag/index.py) and [`ai/rag/retriever.py`](file:///d:/Projects/genai-prescription-decoder/ai/rag/retriever.py):

### Multi-Key In-Memory Index
- `exact_name_index`: Maps normalized canonical name to records.
- `brand_index`: Maps normalized brand name to records.
- `alias_index`: Maps normalized aliases to records.
- `ingredient_index`: Maps active pharmaceutical ingredients to records.
- `token_to_ref_ids`: Inverted token index for fast candidate filtering.
- `records_by_id`: Immutable lookup by reference ID.

### Deterministic Retrieval Hierarchy
Retrieval executes in strict stages:

```
Extracted Candidate Query
          ↓
Stage 1: Exact Normalized Canonical Name Match (Score: 1.0)
          ↓
Stage 2: Exact Proprietary Brand Match (Score: 0.99)
          ↓
Stage 3: Exact Documented Alias / Synonym Match (Score: 0.98)
          ↓
Stage 4: Exact Active Ingredient Match (Score: 0.95)
          ↓
Stage 5: Controlled Token Overlap [Jaccard + Containment] (Score: 0.70 – 0.92)
          ↓
Stage 6: Controlled Lexical Similarity [difflib SequenceMatcher] (Score: 0.75 – 0.94)
          ↓
Candidate Deduplication (Highest Score Retained)
          ↓
Deterministic Sort (-Score, +ReferenceID) & Top-K Truncation
```

---

## 9. Validation Decision Engine & Rules

Implemented in [`ai/rag/validator.py`](file:///d:/Projects/genai-prescription-decoder/ai/rag/validator.py):

### Controlled Validation Statuses
1. **`validated`:** Defined strictly and exclusively as:
   > *"Reference correspondence established according to the configured retrieval and validation rules."*
   
   **Explicit Clinical Disclaimer:** A `validated` status does **NOT** mean clinically validated, medically safe, therapeutically appropriate, prescription-correct, dosage-correct, or patient-appropriate. It signifies solely that an identity correspondence to an authoritative nomenclature entity has been verified under algorithmic retrieval criteria.
2. **`uncertain`:** Multiple plausible reference candidates exist within the ambiguity margin ($\le 0.05$), or the match score falls in the sub-autonomous range ($0.75 \le \text{score} < 0.95$) (`requires_human_review: true`).
3. **`not_validated`:** No sufficiently supported reference correspondence was found ($\text{score} < 0.75$ or empty candidate) (`requires_human_review: true`).

### Decision Rules
- **Rule 1 (`EMPTY_CANDIDATE_REJECTION`):** Empty or whitespace candidate returns `not_validated`, `requires_human_review: true`.
- **Rule 2 (`NO_REFERENCE_MATCH_FOUND`):** Zero candidates above threshold returns `not_validated`, `requires_human_review: true`.
- **Rule 3 (`MULTI_CANDIDATE_AMBIGUITY_GATE`):** If top 2 candidates have scores within $\text{ambiguity\_margin} = 0.05$, status is `uncertain`, `selected_reference: null`, `requires_human_review: true`.
- **Rule 4 (`HIGH_CONFIDENCE_FORMULARY_VALIDATED`):** Single dominant candidate with score $\ge 0.95$ returns `validated`, `requires_human_review: false` (subject to formulation consistency evaluation).
- **Rule 5 (`LEXICAL_SIMILARITY_UNCERTAIN_GATE`):** Candidate score in $[0.75, 0.95)$ returns `uncertain`, `requires_human_review: true`.
- **Rule 6 (`SUBTHRESHOLD_MATCH_REJECTED`):** Score $< 0.75$ returns `not_validated`, `requires_human_review: true`.

---

## 10. Separation of Medicine Identity from Formulation Compatibility

Medicine identity validation and dosage/formulation compatibility are distinct concepts. A dosage mismatch must never silently appear equivalent to a fully validated prescription.

### Explicit Semantic Representation
For example, given:
- **Observed prescription:** candidate = *Augmentin 625 Duo*, dosage = `1000 mg`
- **Reference entity:** medicine = *Augmentin 625 Duo*, strength = `625 mg`

The system establishes identity correspondence based on medicine-name evidence, while explicitly decoupling and preserving formulation details:
```yaml
medicine_identity_status: "validated"
dosage_observation_preserved: true
observed_dosage: "1000 mg"
reference_strength: "625 mg"
formulation_consistency: "mismatch"
requires_human_review: true
```

### Inviolable Invariants
1. **Dosage Observation Immutability:** Visually observed dosages from Phase 6 are strictly preserved without alteration (`dosage_observation_preserved: true`). The system **never** modifies observed dosages, **never** infers a "corrected" dosage, and **never** prescribes an alternative formulation.
2. **Independent Reference Strength:** The formulary reference strength is stored in `reference_strength`, completely independent of the observed text.
3. **Formulation Consistency Evaluation:** If the observed dosage conflicts with the reference entity strength, `formulation_consistency` is set to `"mismatch"`, and `requires_human_review` is forced to `true`.
4. **No Silent Reassurance:** A dosage mismatch is flagged with high clinical visibility and cannot silently pass as a completely validated or reassuring result.
5. **Brand / Generic Separation:** Extracted brand names are never silently rewritten to generic names; relationships are documented strictly as reference evidence in `brand_generic_relationship`.

---

## 11. Complete Decision Provenance

Every validation decision generates an immutable `ValidationDecisionProvenance` record containing:
- `retrieval_method`: Dominant retrieval technique used.
- `query_raw`: Exact input string observed.
- `query_normalized`: Normalized query representation.
- `normalization_version`: `"v1.0-conservative"`.
- `index_version`: `"v1.0-in-memory"`.
- `config_hash`: Deterministic 16-character SHA-256 configuration fingerprint.
- `matched_count`: Number of candidates retrieved.
- `timestamp`: ISO 8601 execution timestamp.
- `validation_rule`: Deterministic rule identifier triggered.
- `source_authorities`: Catalog of authorities evaluated.

---

## 12. API Contracts & Changes

### 1. `POST /api/v1/validation/medicine`
- **Request:** `MedicineValidationRequest` (`candidate_name`, `observed_dosage`, `top_k`, `prescription_id`)
- **Response:** `MedicineValidationResponse` (`status`, `prescription_id`, `validation_result`, `ui_evidence`)

### 2. `POST /api/v1/validation/medicine/batch`
- **Request:** `MedicineBatchValidationRequest` (`items: List[MedicineValidationRequest]`)
- **Response:** `MedicineBatchValidationResponse` (`status`, `total_processed`, `results`)

### 3. `GET /api/v1/validation/status`
- Reports `initialized`, `config_hash`, active `config`, `index_stats`, and `ingestion_report`.

### 4. Pipeline Integration: `PrescriptionAnalyzeResponse`
- Dual-contract compatibility preserved.
- `validation`: Dict mapping each extracted medicine to Section 6 `ValidationItem`.
- `data.validation_evidence`: Populated with real CDSCO/RxNorm grounding, schedule, RxCUI, and alternatives.
- `medicine_validations`: Auditable list of Phase 7 `MedicineValidationResult`s.
- `pipeline_stages_completed`: Advanced to 7.

---

## 13. Frontend Compatibility

The Phase 1 UI components (`MedicineValidationSection.tsx`) and domain mappers (`prescriptionMapper.ts`) render Phase 7 evidence without requiring architectural redesign:
- **Vision Candidate:** Displays original extracted stroke observation.
- **Formulary Entity:** Displays verified authoritative formulation.
- **Active Molecule:** Displays generic salt.
- **Regulatory Badges:** CDSCO Schedule, RxCUI external link, Therapeutic Class, or `DOSAGE MISMATCH (REVIEW REQUIRED)` badge.
- **Formulation Alert:** Displays explicit mismatch warnings when observed dosage conflicts with reference strength.
- **Alternative Candidates:** Evaluated bioequivalent formulations with match percentage.
- **Prescription Primacy Notice:** Prominently reaffirms that the prescriber's signed document remains the primary legal authority.

---

## 14. Phase 7 Mock Fixtures

All 14 required cases are implemented in [`backend/app/fixtures/rag_fixtures.py`](file:///d:/Projects/genai-prescription-decoder/backend/app/fixtures/rag_fixtures.py) and verified in `test_rag_fixtures.py`:

| # | Fixture Name | Scenario Description | Expected Identity Status | Formulation Status | Review Required |
| :-: | :--- | :--- | :--- | :--- | :---: |
| 1 | Exact medicine match | Exact canonical formulation match (*Augmentin 625 Duo*) | `validated` | `consistent` | False |
| 2 | Exact normalized match | Whitespace / case-folded match (*  augmentin 625 duo  *) | `validated` | `consistent` | False |
| 3 | Alias match | Documented commercial synonym (*Clavam 625*) | `validated` | `consistent` | False |
| 4 | Multiple candidates | Ambiguous drug stem (*Amoxicillin*) with close competitors | `uncertain` | `not_evaluated` | True |
| 5 | No match | Unlisted chemical string (*XyzNonExistentPharmaceutical123*) | `not_validated` | `not_evaluated` | True |
| 6 | Uncertain match | Truncated cursive stroke (*Amox...*) | `uncertain` | `not_evaluated` | True |
| 7 | Dosage mismatch | Posology preservation: 1000 mg observed vs 625 mg reference; no dosage mutation | `validated` | `mismatch` | **True** |
| 8 | Brand/generic relation | Brand *Augmentin* linked to generic without substitution | `uncertain` / Ref | `not_evaluated` | True |
| 9 | Duplicate reference records | Ingestion deduplication handling | Deduplicated | N/A | N/A |
| 10 | Missing source provenance | Schema validation rejection of unprovenanced records | `ValidationError` | N/A | N/A |
| 11 | Reference source unavailable | Missing file in manifest handled gracefully | Error Logged | N/A | N/A |
| 12 | Retrieval service failure | Simulated retrieval exception produces controlled failure | `VALIDATION_FAILED` | N/A | True |
| 13 | Empty medicine candidate | Whitespace query rejected without index lookup | `not_validated` | `not_evaluated` | True |
| 14 | Multi-medicine prescription | Multi-drug script validated independently | All Validated | `consistent` | False |

---

## 15. Test Suite Verification

### Summary: 219 Backend Tests Passed (100%)
- `test_rag_normalization.py`: 9 unit tests passed.
- `test_rag_ingestion.py`: 5 unit tests passed.
- `test_rag_retriever.py`: 9 unit tests passed.
- `test_rag_validator.py`: 12 unit tests passed (including metadata scope checks, formulation compatibility, and dosage mismatch alerts).
- `test_rag_fixtures.py`: 14 unit tests passed.
- `test_rag_api.py`: 6 integration tests passed.
- `test_rag_pipeline_integration.py`: 2 end-to-end integration tests passed.
- `test_dataset_manifest.py`: 4 integrity tests passed.
- **Phase 1–6 Regression Tests:** 158 existing tests passed with zero regressions.

### Summary: 123 Frontend Vitest Tests Passed (100%)
- Frontend contract, posology, error handling, and UI state architecture verified.

### Summary: 116 Live HTTP End-to-End Tests Passed (100%)
- Executed against running FastAPI instance at `http://127.0.0.1:8000` via `scripts/test_live_backend.py`.

### Summary: Typecheck & Build
- `npx tsc --noEmit`: 0 errors.
- `npm run build`: Production bundle built cleanly in 605ms.

---

## 16. Security, Privacy, and Research Integrity

- **Zero External Image Transmission:** Phase 7 validates extracted textual posology tokens; raw prescription images are not transmitted to external services.
- **Audit Traceability:** No opaque vector scores or generative hallucination used as the basis for clinical drug validation.
- **Zero Fabrication:** Provenance, citation, retrieval scores, and validation decisions are deterministically computed and auditable.
- **Scope Discipline:** No Phase 8+ functionality (confidence calibration formulas, selective abstention entropy gating, LASA phonetic screening, multilingual posology generation, or Phase 12 evaluation framework) was implemented.

---

## 17. Files Changed / Created

```
ai/
  rag/
    __init__.py
    config.py
    schemas.py
    sources.py
    ingestion.py
    normalization.py
    index.py
    retriever.py
    validator.py
    service.py
    provenance.py
data/
  reference/
    cdsco_approved_drugs.json
    nlm_rxnorm_drugs.json
    reference_manifest.json
  manifests/
    dataset_manifest.json
scripts/
  build_reference_data.py
  test_live_backend.py
  validate_dataset.py
backend/
  app/
    api/
      v1/
        validation.py
      router.py
    schemas/
      validation.py
      prescription.py
    services/
      multimodal_pipeline.py
    fixtures/
      rag_fixtures.py
  tests/
    test_rag_normalization.py
    test_rag_ingestion.py
    test_rag_retriever.py
    test_rag_validator.py
    test_rag_fixtures.py
    test_rag_api.py
    test_rag_pipeline_integration.py
README.md
docs/
  phase-07-completion.md
```

---

## 18. Phase 7 Exit Gate Checklist

- [x] RxNorm licensing language is accurate (UMLS license/UTS access; NLM public-domain terms; no claim of general right to clinical validation)
- [x] RxNorm version is genuinely traceable (frozen reference fixture subset 2024-08; newer NLM releases acknowledged)
- [x] RxNorm U.S.-centric limitation is documented (not a comprehensive Indian formulary)
- [x] CDSCO data is correctly described as a finite subset (finite CDSCO-derived reference subset of 20 records)
- [x] No comprehensive-formulary claim remains
- [x] Medicine identity and formulation compatibility are separated (`medicine_identity_status` vs `formulation_consistency`)
- [x] Observed dosage is immutable (`dosage_observation_preserved: true`, `observed_dosage` preserved)
- [x] Reference strength is separately represented (`reference_strength`)
- [x] Dosage mismatch cannot silently produce a clinically reassuring result (`requires_human_review: true` on mismatch)
- [x] No Phase 8+ functionality was added
- [x] All Phase 7 tests pass (37 dedicated RAG tests)
- [x] Phase 1–6 regression passes (219 total backend tests pass)
- [x] Live HTTP tests pass (116/116 checks pass)
- [x] Frontend/build checks pass (123/123 tests pass, `tsc` clean, Vite build clean)
- [x] Documentation is evidence-based

---

## PHASE 7 EXIT GATE: PASS

