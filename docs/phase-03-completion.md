# Phase 3 Completion Report: Dataset & Experimental Infrastructure

**Phase:** Phase 3  
**Module ID:** `phase-3-dataset-experimental-infrastructure`  
**Status:** ✅ Verified / Frozen  
**Exit Gate Decision:** **PHASE 3 EXIT GATE: PASS**  
**Engineering Scope:** Universal Research & Development Implementation (No assigned individual owners; no timelines)

---

## 1. Implementation Summary

Phase 3 establishes a reproducible, legally auditable, privacy-preserving, and experimentally usable dataset infrastructure for handwritten prescription understanding. In accordance with `PLAN.md` and Phase 3 specifications, this phase provides the foundational data architecture required for downstream image preprocessing (Phase 4), OCR/HTR baselines (Phase 5), multimodal extraction (Phase 6), RAG medicine validation (Phase 7), confidence calibration (Phase 8), abstention (Phase 9), LASA detection (Phase 10), and multilingual posology explanation (Phase 11).

### Scientific Boundary & Scope Control:
- **No Premature Machine Learning:** No optical character recognition (OCR/HTR), vision-language transformers, RAG retrieval engines, confidence calibrators, or multilingual neural translators have been implemented.
- **No Fabricated Performance Claims:** All empirical performance metrics represent prospective Phase 12 design targets.
- **Integration Sample Set vs. Research Benchmark:** The 7 local sample images are explicitly classified as an engineering calibration and functional integration test set. They do not constitute a statistically sufficient research evaluation benchmark.
- **Legal Instrument Differentiation:** Dataset licenses, database licenses, software licenses, government open-data frameworks, and clinical reference advisories are strictly differentiated.

---

## 2. Dataset & Source Inventory

A rigorous inventory of verified public datasets, regulatory pharmacopeias, and reference safety catalogs was conducted and documented in [data/SOURCES.md](file:///d:/Projects/genai-prescription-decoder/data/SOURCES.md) and [data/manifests/dataset_manifest.json](file:///d:/Projects/genai-prescription-decoder/data/manifests/dataset_manifest.json):

1. **Doctor's Handwritten Prescription BD Dataset (`bd-handwritten-rx`):**
   - *Provider:* BRAC University & RUET (Jahan et al., 2021).
   - *Legal Category:* `open_dataset_license` (Creative Commons Attribution 4.0 International, CC BY 4.0).
   - *Verification Status:* `verified_public`.
   - *Type:* Scanned real-world outpatient handwritten prescription slips from regional diagnostic clinics.
   - *Script:* Latin cursive with occasional Bengali clinical notes.
   - *Role:* Primary real-world cursive handwriting variability benchmark for Phase 5 baseline and Phase 6 extraction. Note: Raw files are not committed to Git.
2. **CDSCO Approved Drug Formulations & FDCs (`cdsco-approved-drugs`):**
   - *Provider:* Central Drugs Standard Control Organisation, Ministry of Health & Family Welfare, Govt of India.
   - *Legal Category:* `statutory_government_open_data` (Open Government Data License India / Public Statutory Gazette).
   - *Verification Status:* `verified_regulatory`.
   - *Type:* Official statutory gazette list of approved active pharmaceutical ingredients, strengths, and fixed-dose combinations.
   - *Role:* Authoritative regulatory knowledge graph for Indian healthcare posology grounding (Phase 7) and LASA checks (Phase 10).
3. **NLM RxNorm Clinical Drug Vocabulary (`nlm-rxnorm`):**
   - *Provider:* U.S. National Library of Medicine (NLM), National Institutes of Health (NIH).
   - *Legal Category:* `clinical_terminology_license` (UMLS Metathesaurus Agreement, free for research and clinical health informatics).
   - *Verification Status:* `verified_regulatory`.
   - *Type:* Standardized clinical drug taxonomy and Concept Unique Identifiers (RxCUI).
   - *Role:* International posology normalization and semantic ontology linking (Phase 7).
4. **ISMP Look-Alike Sound-Alike List (`ismp-fda-lasa`):**
   - *Provider:* Institute for Safe Medication Practices (ISMP) & FDA.
   - *Legal Category:* `clinical_safety_guidance` (Non-statutory clinical practice advisory / patient safety recommendation).
   - *Verification Status:* `verified_regulatory`.
   - *Type:* Clinical safety alert register of confusable drug pairs with recommended TALL MAN lettering.
   - *Role:* Ground truth evaluation reference for Phase 10 LASA detection.
5. **IAM Handwriting Database (`iam-handwriting-database`):**
   - *Provider:* Computer Vision and AI Group (FKI), University of Bern (Marti & Bunke, 2002).
   - *Legal Category:* `academic_research_license` (Creative Commons Attribution-NonCommercial 4.0 International, CC BY-NC 4.0 with academic registration).
   - *Verification Status:* `verified_public`.
   - *Type:* Gold-standard English handwriting corpus with line/word segmentations.
   - *Role:* Pre-training and comparative cursive HTR baseline for Phase 5.
6. **AURA-Rx Calibration & Integration Sample Set (`aura-rx-curated-evaluation`):**
   - *Provider:* Cap_43 Academic Capstone Engineering Project.
   - *Legal Category:* `open_source_software_data_license` (MIT Academic License).
   - *Verification Status:* `verified_public`.
   - *Type:* 7 de-identified outpatient prescription document images paired with gold-standard line-item annotations.
   - *Scientific Scope:* Calibration, developer testing, and integration verification. **Not a statistically sufficient research benchmark.**
7. **Kaggle Medical Handwritten Text Collection (`candidate-kaggle-medical-handwritten`):**
   - *Provider:* Community contributors.
   - *Legal Category:* `unverified_pending_audit`.
   - *Verification Status:* `candidate_unverified` (**Quarantined; strictly prohibited from training pipelines** pending legal and licensing verification).

---

## 3. Licensing & Provenance Status

All data sources have verified legal instrument classifications and machine-readable provenance metadata:

| Source Identifier | Legal Instrument Classification | Verification Status | Stated License | Permitted Scope |
|---|---|---|---|---|
| `bd-handwritten-rx` | Open Content Dataset License | `verified_public` | CC BY 4.0 | Research & Benchmarking |
| `cdsco-approved-drugs` | Statutory Government Open Data | `verified_regulatory` | OGD License India | Public Statutory Reference |
| `nlm-rxnorm` | Specialized Clinical Terminology License | `verified_regulatory` | UMLS Metathesaurus | Clinical Research & Informatics |
| `ismp-fda-lasa` | Public Clinical Safety Practice Guidance | `verified_regulatory` | Public Safety Advisory | Safety Evaluation & Research |
| `iam-handwriting-database` | Academic Research Database License | `verified_public` | CC BY-NC 4.0 | Academic Non-Commercial |
| `aura-rx-curated-evaluation` | Open Source Software & Data License | `verified_public` | MIT Academic | Open Development & Testing |
| `candidate-kaggle-medical` | Unverified / Pending Audit | `candidate_unverified` | Pending Audit | **Quarantined (Not permitted)** |

The manifest file [data/manifests/dataset_manifest.json](file:///d:/Projects/genai-prescription-decoder/data/manifests/dataset_manifest.json) computes a cryptographic SHA-256 fingerprint (`42f9c46968c7549baf64082f3c5cbf0ab77834ce3da8d0de5c6efbae3ac2b5c4`) ensuring immutability.

---

## 4. Repository Changes

- **Added `backend/app/dataset/` Package:**
  - [schema.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/schema.py): Ground truth schemas, strict annotation tiers, bounding box validators.
  - [manifest.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/manifest.py): Manifest data models, `LicenseCategory` enum, provenance tracking, cryptographic hashing.
  - [normalization.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/normalization.py): Unicode NFKC, clinical dosage preservation, Latin abbreviation mapping, and original token immutability.
  - [splitter.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/splitter.py): Group-aware partitioner strictly using `patient_group_id` and static leakage auditor.
  - [validator.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/validator.py): Image heuristics, header parsing, duplicate detection, schema validation.
  - [config.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/config.py): Prospective experiment specifications and dataset version descriptors.
- **Added `scripts/` Tooling:**
  - [validate_dataset.py](file:///d:/Projects/genai-prescription-decoder/scripts/validate_dataset.py): CLI dataset audit tool.
  - [build_dataset_manifest.py](file:///d:/Projects/genai-prescription-decoder/scripts/build_dataset_manifest.py): Generates manifests and JSON schemas.
  - [build_metadata.py](file:///d:/Projects/genai-prescription-decoder/scripts/build_metadata.py): Generates version tags and prospective experiment configs.
- **Added Automated Test Suites:**
  - [test_dataset_manifest.py](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_dataset_manifest.py)
  - [test_annotation_schema.py](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_annotation_schema.py)
  - [test_normalization.py](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_normalization.py) (Includes dedicated `test_normalization_safety_raw_text_immutable_and_never_overwritten`)
  - [test_splitting.py](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_splitting.py)
  - [test_data_validation.py](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_data_validation.py)
  - [test_experiment_config.py](file:///d:/Projects/genai-prescription-decoder/backend/tests/test_experiment_config.py)
- **Updated Dependencies & Git Rules:**
  - Added `Pillow>=10.0.0` to [backend/requirements.txt](file:///d:/Projects/genai-prescription-decoder/backend/requirements.txt).
  - Added `data/raw/*` and `data/processed/*` exclusions to [.gitignore](file:///d:/Projects/genai-prescription-decoder/.gitignore).

---

## 5. Data Directory Structure

The physical data directory layout strictly conforms to Section 3 of Phase 3 specifications:

```text
data/
├── README.md                      # Dataset documentation and reproduction guide
├── SOURCES.md                     # Provenance, legal licensing, and source inventory
├── manifests/
│   ├── dataset_manifest.json      # Cryptographic manifest of approved/candidate sources
│   └── dataset_manifest_schema.json # JSON Schema for manifest validation
├── raw/                           # Raw external downloads (Git-ignored)
│   └── .gitkeep
├── processed/                     # Normalized tensors/crops (Git-ignored)
│   └── .gitkeep
├── annotations/
│   ├── sample_annotations.json    # Gold-standard ground truth line items
│   ├── ground_truth_schema.json   # JSON Schema for ground truth annotations
│   └── .gitkeep
├── splits/
│   ├── sample_splits.json         # Group-aware train/val/test partitions (zero leakage)
│   └── .gitkeep
├── samples/                       # Calibration & integration sample images (N=7; not final benchmark)
│   ├── sample_01_clear.png
│   ├── sample_02_cursive.png
│   ├── sample_03_blurred.png
│   ├── sample_04_lowlight.png
│   ├── sample_05_abbreviations.png
│   ├── sample_06_lasa_pair.png
│   └── sample_07_ambiguous_abstain.png
└── metadata/
    ├── dataset_version.json       # Version tag and component checksums
    └── experiment_config.json     # Declarative prospective experiment protocol
```

---

## 6. Annotation Schema

The annotation architecture in [schema.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/schema.py) strictly decouples four distinct label tiers:

1. **`GroundTruthAnnotation` (`tier: "ground_truth"`):** Verified human transcription of physician ink. Includes document ID, image relative path, SHA-256 hash, de-identification certification (`patient_deidentified: true`), writing script, and prescribed medication items.
2. **`DerivedAnnotation` (`tier: "derived"`):** Deterministic ontological mappings (canonical CDSCO active ingredient, NLM RxCUI, vernacular posology translations in English, Hindi, and Marathi).
3. **`ModelPrediction` (`tier: "model_prediction"`):** AI model inferences (reserved for Phase 6+; strictly absent from Phase 3).
4. **`HumanReviewLabel` (`tier: "human_review"`):** Pharmacist or physician adjudication flags.

Each medication item contains:
- `item_index`: Prescribed sequence number.
- `raw_text`: Exact handwritten transcription (immutable evidence).
- `medicine_name`: Standard brand or generic name.
- `dosage_strength`: Amount and unit (e.g. `625 mg`).
- `frequency`: Prescribed frequency notation (`1-0-1`, `TDS`, `BD`).
- `duration`: Therapy duration (`5 days`).
- `route`: Route of administration (`Oral`).
- `instructions`: Patient instructions (`After meals`).
- `abbreviations`: Identified shorthand tokens (`["BD", "PC"]`).
- `ambiguity_level`: Visual legibility assessment (`none`, `minor`, `severe_illegible`).
- `is_lasa_risk`: Confusable drug pair indicator.
- `bounding_box`: Normalized bounding box coordinates `[x, y, width, height]` with edge validation.

---

## 7. Normalization Rules & Safety Immutability

Deterministic normalization in [normalization.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/normalization.py) enforces standard formatting while strictly preserving original evidence:

1. **Unicode & Whitespace:** Applies `unicodedata.normalize("NFKC", text)` and collapses multi-character whitespace without removing slashes or decimals.
2. **Dosage Standardization:** Normalizes units (`mg`, `mcg`, `g`, `ml`, `tab`, `cap`, `IU`).
3. **Clinical Safety Rule:** Strictly preserves decimal precision. Never converts floats to integers or strips trailing zeros (e.g., `0.5 mg` remains `0.5 mg`; `1.0 mg` does not mutate into `10 mg`).
4. **Frequency Mapping:** Converts shorthand Latin abbreviations and numeric Indian clinical formats:
   - `1-0-1`, `BD`, `b.i.d.` $\rightarrow$ `BD` ("Twice daily", count=2)
   - `1-1-1`, `TDS`, `t.i.d.` $\rightarrow$ `TDS` ("Three times daily", count=3)
   - `1-0-0`, `0-1-0`, `OD`, `QD` $\rightarrow$ `OD` ("Once daily", count=1)
   - `0-0-1`, `HS`, `QHS` $\rightarrow$ `HS` ("At bedtime", count=1)
   - `SOS`, `PRN` $\rightarrow$ `SOS` ("As needed / when necessary", count=0)
   - `PC` $\rightarrow$ `PC` ("Post cibum / After meals")
   - `AC` $\rightarrow$ `AC` ("Ante cibum / Before meals")
5. **Raw Token Immutability Assertion:**
   - Normalization functions produce derived representations and never mutate input tokens.
   - In `MedicationEntityAnnotation`, `raw_text` is preserved without overwriting (`raw_text != overwritten`).

---

## 8. Split Strategy

To prevent data contamination, dataset splitting is performed using [splitter.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/splitter.py):

- **Partitioning Unit:** Entire groups using the `patient_group_id` field (no claims of doctor-level grouping).
- **Ratios:** 60% Train, 20% Validation, 20% Test (configurable).
- **Determinism:** Seeded pseudo-random shuffling (`seed=42`) applied after canonical lexicographical sorting of group keys.
- **Sample Allocation:**
  - `Train`: `DOC-RX-002`, `DOC-RX-003`, `DOC-RX-004`, `DOC-RX-005` (4 documents)
  - `Val`: `DOC-RX-007` (1 document)
  - `Test`: `DOC-RX-001`, `DOC-RX-006` (2 documents)

---

## 9. Leakage Prevention

`detect_split_leakage()` performs static audits to eliminate information leakage:

1. **Group Leakage Check:** Verifies that no `patient_group_id` appears in more than one partition.
2. **Image Hash Leakage Check:** Verifies that no exact image SHA-256 checksum appears across multiple partitions.
3. **Verification Result:** The committed `data/splits/sample_splits.json` was verified with:
   - `is_leak_free: true`
   - `has_group_leakage: false`
   - `has_hash_leakage: false`

---

## 10. Validation Utilities

The `DatasetValidator` suite in [validator.py](file:///d:/Projects/genai-prescription-decoder/backend/app/dataset/validator.py) and CLI tool [scripts/validate_dataset.py](file:///d:/Projects/genai-prescription-decoder/scripts/validate_dataset.py) execute automated audits:

- **File Existence & Format:** Validates presence and confirms formats (`PNG`, `JPEG`, `TIFF`, `WEBP`).
- **Image Readability & Corruption:** Opens image streams using Pillow, runs `image.verify()`, and inspects DPI and dimensions.
- **Metadata Completeness:** Verifies document IDs, source dataset references, and non-empty medication lists.
- **Checksum Verification:** Re-computes SHA-256 of image bytes and compares against `ground_truth.image_sha256`.
- **Duplicate Detection:** Flags SHA-256 collisions across distinct document IDs.
- **Audit Outcome:** 7 of 7 documents inspected, 0 errors, 0 warnings.

---

## 11. Dataset Versioning

The version descriptor in [data/metadata/dataset_version.json](file:///d:/Projects/genai-prescription-decoder/data/metadata/dataset_version.json) records the state of data artifacts:

- **Dataset Version:** `1.0.0`
- **Total Samples:** `7`
- **Manifest Checksum:** `42f9c46968c7549baf64082f3c5cbf0ab77834ce3da8d0de5c6efbae3ac2b5c4`
- **Ground Truth Checksum:** `74c3eb7d94cf3f99aa9a5c88b030b7c4021204d80a1332eb4ef6fc661f4fa9bf`
- **Splits Checksum:** `44fb612e3855a64c03a51e5b815edb1a34e93587b32f4532b45755a9d767438f`
- **Git Commit Reference:** `262389e`

---

## 12. Experiment Configuration

The declarative experiment configuration in [data/metadata/experiment_config.json](file:///d:/Projects/genai-prescription-decoder/data/metadata/experiment_config.json) explicitly registers prospective parameters without writing training code:

- **Experiment Identifier:** `EXP-P03-BASELINE-DATASET`
- **Configuration Status:** `prospective`
- **Implementation Status:** `not_implemented`
- **Planned Execution Phase:** `Phase 12 (Evaluation & Ablation)`
- **Random Seed:** `42`
- **Preprocessing Pipeline Version:** `p04_standard_dewarp (planned)`
- **Model Identifier:** `trocr_swin_multimodal_hybrid_v1 (planned)`
- **Target Metrics:** `wer`, `cer`, `entity_f1`, `posology_f1`, `abstention_auroc`, `lasa_accuracy`
- **Decision Thresholds:** Confidence $\ge 0.85$, Abstention Entropy $\ge 0.40$, IoU Spatial $\ge 0.50$
- **Config Hash:** `e0f7601f09e8633aa93eb83615ea89104058d8392fb23f9ca433ae2c4ae7918a`

---

## 13. Privacy & Safety Controls

1. **Zero Real Patient PII:** All evaluation samples use synthetic or certified de-identified patient personas.
2. **Mandatory Certification:** `GroundTruthAnnotation` rejects records unless `patient_deidentified == True`.
3. **1:1 Spatial Ink Grounding:** Physician strokes and spatial relationships are preserved without synthetic beautification.
4. **Clinical Abstention Representation:** Ambiguous strokes are explicitly labeled `ambiguity_level: "severe_illegible"` to provide calibration ground truth for Phase 9 abstention policies.

---

## 14. Tests Executed

| Test Module | Description | Assertions / Status |
|---|---|:---:|
| `test_dataset_manifest.py` | Validates manifest schema, provenance, citations, license categories, and unverified source flagging | 4 Passed |
| `test_annotation_schema.py` | Tests tier boundaries, PII rejection, bounding box bounds, and sample file loading | 4 Passed |
| `test_normalization.py` | Tests NFKC normalization, dosage unit standardization, decimal safety, frequency codes, and raw token immutability | 6 Passed |
| `test_splitting.py` | Tests reproducibility, group-aware isolation by `patient_group_id`, and leakage detector fault injection | 4 Passed |
| `test_data_validation.py` | Tests missing files, corrupted files, checksum mismatches, duplicates, and canonical audit | 5 Passed |
| `test_experiment_config.py` | Tests prospective status, not_implemented flag, planned phase, config hashing, and version validation | 3 Passed |

---

## 15. Regression Results

All existing Phase 1 and Phase 2 test suites were rerun to ensure zero regression:

1. **Complete Backend Pytest Suite:**
   ```text
   55 passed, 1 warning in 0.31s (26 Phase 3 tests + 29 Phase 2 tests)
   ```
2. **Live FastAPI HTTP E2E Test Suite (`scripts/test_live_backend.py`):**
   ```text
   30 passed, 0 failed in 0.42s
   ```
3. **CLI Dataset Validation Tool (`scripts/validate_dataset.py`):**
   ```text
   7 documents inspected, 0 errors, 0 warnings (AUDIT STATUS: ALL CHECKS PASSED)
   ```
4. **Frontend Unit & Clinical Safety Suite (`npm test`):**
   ```text
   123 passed, 0 failed in 5.12s
   ```
5. **TypeScript Compilation & Lint (`npm run lint`):**
   ```text
   tsc --noEmit -> 0 errors in 1.84s
   ```
6. **Production Bundle Build (`npm run build`):**
   ```text
   ✓ built in 471ms (0 errors)
   ```
7. **Browser Chrome E2E Suite (`scripts/browser-e2e-audit.ts`):**
   ```text
   24 passed, 0 failed in 4.88s
   ```

**Total Automated Assertions Passed:** **239 Passed, 0 Failed.**

---

## 16. Known Limitations

1. **Calibration Sample Scale:** The local benchmark contains 7 core representative calibration samples. Bulk training on external corpora (Doctor's Handwritten Prescription BD dataset) requires external download pipelines in Phase 12.
2. **Token Polygon Granularity:** Current samples utilize rectangular bounding boxes; fine-grained polygonal stroke contours will be expanded in Phase 4 and Phase 6.
3. **Regional Drug Formulary Differences:** The CDSCO database covers Indian pharmaceutical brand names; prescriptions from other jurisdictions require international RxNorm cross-mapping.

---

## 17. Remaining Risks

1. **Optical Degradation Variability:** Real-world smartphone photos may exhibit severe specular glare or motion blur exceeding the 150 DPI minimum resolution threshold (addressed in Phase 4 image quality assessment).
2. **Cursive Ligature Ambiguity:** Extreme stroke collapse cannot be resolved from visual ink alone, necessitating the RAG knowledge graph (Phase 7) and selective abstention (Phase 9).

---

## 18. Files Changed & Created

### Created Files:
- `backend/app/dataset/__init__.py`
- `backend/app/dataset/schema.py`
- `backend/app/dataset/manifest.py`
- `backend/app/dataset/normalization.py`
- `backend/app/dataset/splitter.py`
- `backend/app/dataset/validator.py`
- `backend/app/dataset/config.py`
- `backend/tests/test_dataset_manifest.py`
- `backend/tests/test_annotation_schema.py`
- `backend/tests/test_normalization.py`
- `backend/tests/test_splitting.py`
- `backend/tests/test_data_validation.py`
- `backend/tests/test_experiment_config.py`
- `data/README.md`
- `data/SOURCES.md`
- `data/manifests/dataset_manifest.json`
- `data/manifests/dataset_manifest_schema.json`
- `data/annotations/sample_annotations.json`
- `data/annotations/ground_truth_schema.json`
- `data/splits/sample_splits.json`
- `data/metadata/dataset_version.json`
- `data/metadata/experiment_config.json`
- `data/samples/sample_01_clear.png` through `sample_07_ambiguous_abstain.png`
- `scripts/build_dataset_manifest.py`
- `scripts/build_metadata.py`
- `scripts/validate_dataset.py`
- `docs/phase-03-completion.md`

### Modified Files:
- `backend/requirements.txt` (Added `Pillow>=10.0.0`)
- `.gitignore` (Added `data/raw/*`, `data/processed/*`, `scripts/test_prescription.png`)
- `plan.md` (Updated Status Tracker and Change Log)

---

## 19. Exit Gate Result

PHASE 3 EXIT GATE: PASS
