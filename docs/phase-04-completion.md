# Phase 4 Completion Report: Image Preprocessing & Quality Assessment

> **Project:** Explainable Multimodal AI for Handwritten Prescription Understanding  
> **Phase:** Phase 4 — Image Preprocessing & Quality Module  
> **Status:** PASS (FROZEN)  
> **Execution Date:** 2026-09-27  

---

## 1. Status

**PHASE 4 EXIT GATE: PASS**

The image preprocessing and quality assessment infrastructure has been implemented, validated, and frozen. All 86 backend automated tests, 123 frontend unit/integration tests, 37 live HTTP socket tests, 7/7 dataset audit checks, TypeScript compilation, production build, and 24 browser-level Puppeteer end-to-end integration tests are passing with zero regressions.

---

## 2. Implementation Summary

Phase 4 establishes an evidence-grounded, non-destructive image preprocessing and quality evaluation subsystem for clinical prescription documents. Key achievements include:

1. **Original Image Immutability Invariant:** Formally established and verified `original_image != preprocessed_image`. The original uploaded prescription bytes, file references, and SHA-256 cryptographic fingerprints remain unaltered and byte-for-byte identical. The original image is preserved at its stored path and accessible via static HTTP serving for optical verification during the application session.
2. **Ingestion Validation Subsystem:** Pre-flight validation enforcing supported MIME types/formats (JPEG, PNG, WEBP, TIFF, BMP), dimensional safety bounds (min: $150 \times 150\,\text{px}$, max: $8000 \times 8000\,\text{px}$), corruption detection, EXIF orientation transposition, and RGBA-to-RGB white-background compositing to prevent stroke transparency loss.
3. **Deterministic Image Quality Metrics:** Engineering heuristics assessing pixel resolution and effective pixel density (heuristic PPI based on assumed prescription pad dimensions — not physical EXIF DPI), optical/motion blur (Variance of Laplacian), luminance/exposure, RMS grayscale contrast, high-frequency residual noise, skew angle detection (projection profile variance sweep), spatial illumination unevenness (3×3 grid variance), and pixel clipping/saturation.
4. **Deterministic Tri-State Quality Decision:** Transitions strictly between `acceptable`, `degraded_but_usable`, and `insufficient` using configurable thresholds, triggering HTTP 422 `IMAGE_QUALITY_INSUFFICIENT` on fatally degraded inputs while permitting readable handwriting with minor imperfections.
5. **Modular 8-Stage Preprocessing Pipeline:** Produces 5 unconditional derived representations (`grayscale.png`, `normalized.png` via Gaussian background division, `denoised.png` via median stroke filtering, `enhanced.png` via percentile contrast stretching, and `thresholded.png` via Sauvola local adaptive dynamic binarization) plus 1 conditional representation (`deskewed.png` via alignment rotation, generated only when detected skew angle $|\theta| \ge 0.5°$). Total: up to 6 derived image artifacts per run.
6. **Traceable Configuration & Cryptographic Artifact Manifests:** Preprocessing configuration `p04_standard_v1` (version `1.0.0`, status `implemented`) with deterministic SHA-256 fingerprinting. Generates persistent `metadata.json`, `quality.json`, and `manifest.json` per run in `data/processed/preprocessing_runs/<prescription_id>/`.
7. **Service Layer & API Contract Integration:** Integrated `ImagePreprocessingService` into FastAPI `POST /api/v1/prescriptions/analyze` without breaking the frozen Section 6 API contract or Phase 1 UI envelope. Added research inspection endpoint `GET /api/v1/prescriptions/{id}/artifacts`.
8. **Research Visual Debugging Utility:** Created `scripts/inspect_preprocessing.py` for terminal inspection and multi-panel side-by-side visual comparisons across calibration samples.

---

## 3. Architecture Changes

```text
backend/app/
├── preprocessing/                 # [NEW] Phase 4 Preprocessing & Quality Package
│   ├── __init__.py                # Package facade exports
│   ├── config.py                  # PreprocessingConfig & QualityThresholds schemas
│   ├── metadata.py                # ImageMetadata extraction & EXIF sanitization
│   ├── validator.py               # Ingestion validator & dimensional boundary enforcement
│   ├── quality.py                 # Optical quality assessor & tri-state decision engine
│   ├── pipeline.py                # 8-stage image transformation pipeline
│   ├── artifacts.py               # Artifact persistence & immutability verification manager
│   └── service.py                 # High-level orchestration facade service
├── schemas/
│   └── prescription.py            # Extended with processed_image_url, quality_report, preprocessing_manifest
├── services/
│   └── mock_pipeline.py           # Connected ImagePreprocessingService to live analysis pipeline
└── api/v1/
    └── prescriptions.py           # Added GET /{prescription_id}/artifacts route

data/processed/
└── preprocessing_runs/            # [NEW] Dedicated storage for derived research artifacts
    └── <prescription_id>/         # Run directory with derived PNGs, metadata, quality, and manifest

scripts/
├── inspect_preprocessing.py       # [NEW] CLI inspection and multi-panel visual comparison tool
├── test_live_backend.py           # Extended with Phase 4 processed image and artifacts tests
└── browser-e2e-audit.ts           # Updated with real prescription image upload verification
```

---

## 4. Image Quality Metrics

All metrics are documented as **engineering heuristics** tailored for prescription documents and are not claimed as universal clinical constants:

| Metric | Formulation / Algorithm | Nominal Range | Degraded Cutoff | Fatal Cutoff (`insufficient`) |
| :--- | :--- | :---: | :---: | :---: |
| **Pixel Resolution** | Pixel dimensions ($W \times H$) and heuristic effective PPI (estimated from assumed standard prescription pad width; **not** physical EXIF DPI) | $\ge 300\,\text{PPI}$ (heuristic) | $150 - 300\,\text{PPI}$ | $< 150\,\text{PPI}$ or $< 150 \times 150\,\text{px}$ |
| **Blur / Sharpness** | Variance of 2D Laplacian $\sigma^2(\nabla^2 I)$ | $> 75.0$ | $25.0 - 75.0$ | $< 25.0$ |
| **Brightness / Exposure**| Grayscale mean intensity $\mu \in [0, 255]$ | $70 - 240$ | $40 - 70$ | $< 40.0$ or $> 253.0$ |
| **Grayscale Contrast** | RMS contrast (pixel standard deviation $\sigma_I$) | $> 20.0$ | $7.0 - 20.0$ | $< 7.0$ |
| **Sensor Noise** | Median filter residual ratio $\frac{1}{255}\text{mean}(\|I - \text{med}(I)\|)$ | $< 0.04$ | $0.04 - 0.08$ | $> 0.08$ (Degraded warning) |
| **Document Skew** | Projection profile variance angle sweep | $\pm 0.0 - 5.0°$ | $5.0 - 15.0°$ | $> 15.0°$ |
| **Illumination** | Spatial 3×3 block luminance variation $\frac{\sigma(\mu_{\text{block}})}{\bar{\mu}}$ | $< 0.15$ | $0.15 - 0.25$ | $> 0.25$ (Shadow warning) |
| **Pixel Clipping** | Black fraction ($I < 5$) & White fraction ($I > 250$) | Black $< 5\%$ | Black $5 - 25\%$ | Black $> 25\%$ (Crushed signal) |

### Heuristic Quality Index Semantics
The `heuristic_quality_score` $[0.0 - 1.0]$ is a weighted composite index:
$$\text{Score} = 0.35 \cdot S_{\text{blur}} + 0.20 \cdot S_{\text{contrast}} + 0.15 \cdot S_{\text{brightness}} + 0.10 \cdot S_{\text{noise}} + 0.10 \cdot S_{\text{skew}} + 0.10 \cdot S_{\text{illum}}$$
- `insufficient` images are clamped to $\le 0.39$.
- `degraded_but_usable` images fall in $[0.40, 0.79]$.
- `acceptable` images fall in $[0.80, 1.0]$.
- The three ranges cover the complete $[0.0, 1.0]$ interval with no undefined gaps.
- **Critical Notice:** The score is an engineering index of optical capture quality. It does NOT represent machine learning model inference confidence or pharmacological safety.

---

## 5. Preprocessing Pipeline

The pipeline operates in 8 sequential stages, prioritizing non-destructive transformations:

1. **Ingestion & Validation:** Decodes image bytes, validates header integrity, converts color modes (compositing RGBA over solid white background), and transposes EXIF orientation.
2. **Grayscale Conversion:** Generates standard 8-bit single-channel luminance representation (`grayscale.png`).
3. **Illumination Normalization:** Estimates background luminance using Gaussian low-pass filtering ($\sigma = 35.0$) and applies division normalization: $I_{\text{norm}} = \frac{I}{\text{background}} \times 220.0$. Brightens dark shadows while retaining dark ink strokes (`normalized.png`).
4. **Stroke-Preserving Denoising:** Applies $3 \times 3$ median filtering to suppress salt-and-pepper sensor noise and paper dust without blurring thin cursive pen strokes (`denoised.png`).
5. **Contrast Enhancement:** Computes 1st and 99th percentiles of luminance and applies linear contrast stretching to span $[0, 255]$ (`enhanced.png`).
6. **Text Alignment Deskew (Conditional):** If detected skew angle $|\theta| \ge 0.5°$, rotates image by $-\theta$ with bilinear interpolation and white background fill (`deskewed.png`). If skew is below the correction threshold, this stage is skipped and no `deskewed.png` artifact is produced.
7. **Adaptive Dynamic Binarization:** Applies local Sauvola thresholding: $T(x,y) = m(x,y) \cdot [1 + k \cdot (\frac{s(x,y)}{R} - 1)]$ with window $25 \times 25$, $k=0.2$, $R=128$. Produces a crisp binary representation (`thresholded.png`) for downstream topological line/word segmentation.
8. **Artifact Serialization:** Persists derived PNGs and JSON manifests to disk, leaving the source image 100% untouched.

---

## 6. Configuration

Configuration is centralized in `backend/app/preprocessing/config.py`:

```json
{
  "preprocessing_config": {
    "id": "p04_standard_v1",
    "version": "1.0.0",
    "status": "implemented",
    "enable_orientation_correction": true,
    "enable_grayscale": true,
    "enable_illumination_correction": true,
    "enable_denoising": true,
    "enable_contrast_enhancement": true,
    "enable_deskew": true,
    "enable_adaptive_threshold": true,
    "max_processing_dimension": 2400,
    "illumination_sigma": 35.0,
    "denoise_kernel_size": 3,
    "contrast_percentile_low": 1.0,
    "contrast_percentile_high": 99.0,
    "deskew_search_max_angle": 10.0,
    "deskew_search_step": 0.5,
    "deskew_min_correction_angle": 0.5,
    "sauvola_window_size": 25,
    "sauvola_k": 0.2,
    "sauvola_r": 128.0
  }
}
```

- **Traceability:** `PreprocessingConfig.compute_config_hash()` generates a deterministic SHA-256 fingerprint embedded into every run manifest.
- **Phase Boundary:** This configuration is distinct from Phase 3's `experiment_config.json`, which remains locked with `status="prospective"`.

---

## 7. Artifact Handling

Derived artifacts are isolated in `data/processed/preprocessing_runs/<prescription_id>/`:

```text
data/processed/preprocessing_runs/RX-SAMPLE-01/
├── metadata.json       # Structural properties & original image SHA-256
├── quality.json        # Detailed metrics, score, issues, and recommendations
├── manifest.json       # Cryptographic manifest linking derived artifact hashes
├── grayscale.png       # 8-bit luminance representation
├── normalized.png      # Illumination-normalized representation
├── denoised.png        # Median-denoised representation
├── enhanced.png        # Contrast-stretched representation (primary for OCR)
├── deskewed.png        # Alignment-corrected representation (conditional: only when |skew| ≥ 0.5°)
└── thresholded.png     # Sauvola binarized representation
```

- Total derived image artifacts per run: 5 unconditional + 1 conditional (`deskewed.png`) = up to 6.
- Public access is mirrored to `backend/uploads/preprocessed/<prescription_id>/` for HTTP static serving.
- Original files in `backend/uploads/rx_*` and `data/samples/` are verified byte-for-byte identical before and after preprocessing.

---

## 8. API Changes

All changes maintain complete backwards compatibility with Phase 1 and Phase 2 contracts:

1. **`POST /api/v1/prescriptions/analyze`:**
   - Evaluates input image quality during ingestion.
   - Rejects fatally degraded images with HTTP 422 `IMAGE_QUALITY_INSUFFICIENT` containing diagnostic issues, recommendations, and optical metrics.
   - If acceptable or degraded-but-usable, processes image and attaches:
     - `processed_image_url`: Accessible URL to derived enhanced image (`/uploads/preprocessed/{id}/enhanced.png`).
     - `quality_report`: Optical metrics breakdown and tri-state decision.
     - `preprocessing_manifest`: Run manifest with SHA-256 hashes of all derived artifacts.
     - `document_telemetry`: Populated with heuristic effective pixel density (mapped to the frozen `estimated_dpi` API field), contrast ratio, skew angle, and illegibility fraction.
2. **`GET /api/v1/prescriptions/{prescription_id}/artifacts` (New Endpoint):**
   - Retrieves run manifest, quality report, and accessible URLs for all generated derived representations (5 unconditional + 1 conditional) for visual debugging and downstream module consumption.

---

## 9. Frontend Changes

1. **Contract Compatibility:** Extended `src/types/api.types.ts` and `PrescriptionAnalyzeResponseDto` with optional Phase 4 fields (`processed_image_url`, `quality_report`, `preprocessing_manifest`). Zero breaking changes to existing UI models.
2. **Error State Verification:** Verified that HTTP 422 `IMAGE_QUALITY_INSUFFICIENT` renders the existing diagnostic error banner with retry flow and back-to-review navigation.
3. **Preservation of Original Evidence:** The original prescription image remains the primary visual reference in `ReviewStep`, `AnalyzeStep`, and `FindingsStep`. Preprocessing does not replace or occlude the physician's signed document.

---

## 10. Dataset / Test Samples Used

Evaluation utilized the 7 canonical calibration samples from Phase 3 (`data/samples/`):

| Sample Filename | Script Condition | Phase 4 Quality Status | Heuristic Score | Preprocessing Action Taken |
| :--- | :--- | :---: | :---: | :--- |
| `sample_01_clear.png` | Clean outpatient handwriting | `acceptable` | $\ge 0.80$ | Full pipeline executed |
| `sample_02_cursive.png` | High-speed cursive ligatures | `degraded_but_usable` | $[0.40, 0.79]$ | Contrast stretched, denoised |
| `sample_03_blurred.png` | Defocus optical blur | `insufficient` | $\le 0.39$ | Rejected with HTTP 422 notice |
| `sample_04_lowlight.png` | Low-light shadowed capture | `degraded_but_usable` | $[0.40, 0.79]$ | Background division + deskewed |
| `sample_05_abbreviations.png`| Clinical posology shorthand | `acceptable` | $\ge 0.80$ | Full pipeline executed |
| `sample_06_lasa_pair.png` | Confusable drug pair script | `degraded_but_usable` | $[0.40, 0.79]$ | Contrast stretched, denoised |
| `sample_07_ambiguous_abstain.png`| Severe stroke collapse | `degraded_but_usable` | $[0.40, 0.79]$ | Full pipeline executed |

---

## 11. Tests Executed

| Suite / Test Target | Command | Total | Passed | Failed |
| :--- | :--- | :---: | :---: | :---: |
| **Image Ingestion Validation** | `pytest backend/tests/test_image_validation.py` | 9 | 9 | 0 |
| **Image Quality Assessment** | `pytest backend/tests/test_image_quality.py` | 9 | 9 | 0 |
| **Preprocessing Pipeline** | `pytest backend/tests/test_preprocessing_pipeline.py` | 5 | 5 | 0 |
| **Safety & Immutability** | `pytest backend/tests/test_immutability_and_safety.py` | 3 | 3 | 0 |
| **Preprocessing API Integration** | `pytest backend/tests/test_preprocessing_api.py` | 5 | 5 | 0 |
| **Complete Backend Pytest Suite** | `python -m pytest backend/tests -v` | 86 | 86 | 0 |
| **Live FastAPI HTTP Suite** | `python scripts/test_live_backend.py` | 37 | 37 | 0 |
| **Frontend Vitest Suite** | `npm test` | 123 | 123 | 0 |
| **TypeScript Typecheck** | `npm run lint` (`tsc --noEmit`) | 1 | 1 | 0 |
| **Production Bundle Build** | `npm run build` | 1 | 1 | 0 |
| **Chrome Puppeteer Browser E2E** | `npx vite-node scripts/browser-e2e-audit.ts` | 24 | 24 | 0 |
| **Dataset Infrastructure Audit** | `python scripts/validate_dataset.py` | 7 | 7 | 0 |

---

## 12. Regression Results

- **Phase 1 UI Contract:** 100% passing. All 14 visual states render correctly.
- **Phase 2 API Contract:** 100% passing. Dual-contract envelope, Section 6 field schema, and error handling remain intact.
- **Phase 3 Dataset Infrastructure:** 100% passing. Manifest schemas, gold-standard annotations, posology normalizers, and group-aware zero-leakage splits verified without deviation.

---

## 13. Failure-Path Results

The following failure conditions were explicitly tested and confirmed:

1. **Empty / Zero-byte file:** Returns HTTP 400 with `ErrorCode.INVALID_REQUEST`.
2. **Corrupted / truncated byte stream:** Returns HTTP 415 with `ErrorCode.INVALID_FILE_TYPE`.
3. **Unsupported file format (.exe, .pdf):** Returns HTTP 415 with `ErrorCode.INVALID_FILE_TYPE`.
4. **Oversized dimensions (>8000px):** Returns HTTP 413 with `ErrorCode.FILE_TOO_LARGE`.
5. **Tiny image (<150px):** Returns HTTP 422 with `ErrorCode.IMAGE_QUALITY_INSUFFICIENT`.
6. **Fatally blurred image (Laplacian variance < 25.0):** Returns HTTP 422 with `ErrorCode.IMAGE_QUALITY_INSUFFICIENT` and camera stabilization advice.
7. **Severe underexposure / pitch-black image:** Returns HTTP 422 with `ErrorCode.IMAGE_QUALITY_INSUFFICIENT` and lighting advice.
8. **Non-existent accession ID on artifact lookup:** Returns HTTP 404 with structured detail message.

---

## 14. Original Image Integrity Verification

- Automated test `test_original_image_bytes_and_hash_remain_immutable` proves:
  - Original file path on disk exists and retains identical byte size.
  - Original SHA-256 hash before and after preprocessing is 100% identical.
  - Derived artifact files have distinct file paths and distinct cryptographic hashes.
- Automated test `test_source_dataset_calibration_samples_never_mutated` verifies that files in `data/samples/` are strictly read-only.

---

## 15. Reproducibility Verification

- Automated test `test_determinism_and_reproducibility` proves that processing the identical image with identical configuration produces bit-for-bit identical derived PNG bytes and identical quality scores.
- `PreprocessingConfig.compute_config_hash()` generates a consistent SHA-256 digest across runs.

---

## 16. Visual Debugging Evidence

Multi-panel visual comparison sheets generated via `scripts/inspect_preprocessing.py`:
- `data/processed/preprocessing_runs/INSPECT-SAMPLE_01_CLEAR/visual_comparison.png`
- Panels: Original Input → Grayscale → Illumination Normalized → Median Denoised → Contrast Enhanced → Sauvola Binary.

---

## 17. Limitations

1. **Heuristic Thresholds:** Quality metrics use engineering thresholds rather than clinically certified diagnostic cutoffs.
2. **Heuristic Pixel Density:** The `effective_ppi` field is estimated from assumed prescription pad dimensions (approximately 6" portrait / 8.5" landscape). It is not derived from physical EXIF DPI metadata, scanner calibration, or camera sensor characteristics. The frozen API `estimated_dpi` field maps from this heuristic.
3. **Binarization Artifacts:** Sauvola thresholding is provided for structural analysis; it can cause stroke fragmentation on very faint pencil scripts and is not recommended as the sole input to multimodal VLMs.
4. **Skew Search Range:** Text skew estimation sweeps $[-10.0°, +10.0°]$; documents rotated by $\pm 90°$ or $180°$ rely on EXIF orientation or manual user rotation in the UI.
5. **Conditional Deskew:** The `deskewed.png` artifact is only generated when detected skew exceeds $0.5°$. Well-aligned documents will produce 5 derived artifacts instead of 6.

---

## 18. Research Integrity Notes

- No model training or empirical OCR accuracy claims are made in Phase 4.
- Preprocessing representations are provided as derived candidates for downstream comparative evaluation in Phase 5 and Phase 12.
- The 7 calibration samples remain classified as an engineering integration set, not an empirical research benchmark.

---

## 19. Known Risks

- **Flash Glare / Specular Reflections:** Illumination normalization cannot recover information in completely clipped white regions ($I = 255$).
- **Severe Degradation:** Extremely faded carbon-copy prescriptions may fail contrast thresholds and mandate human pharmacist review.

---

## 20. Consistency Audit Corrections Applied

This report incorporates the following corrections from the Phase 4 consistency audit:

1. **Derived artifact count:** Corrected from "5 derived representations" to "5 unconditional + 1 conditional (`deskewed.png`) = up to 6 derived image artifacts." The artifact tree, API endpoint description, and pipeline documentation now reflect the conditional nature of `deskewed.png`.
2. **Quality score range gap:** Fixed the `acceptable` state clamp from `[0.80, 0.98]` to `[0.80, 1.0]`, eliminating the unreachable `[0.99, 1.0]` gap. The three ranges now fully cover the $[0.0, 1.0]$ interval.
3. **Resolution terminology:** Replaced claims of measured DPI with accurate terminology. The internal field was renamed from `estimated_dpi` to `effective_ppi` in Phase 4 modules (`ImageMetadata`, `ResolutionMetric`, `ImageQualityAssessor`). The frozen Phase 2 API field `DocumentTelemetry.estimated_dpi` retains its name for contract stability. Documentation now clarifies this is a heuristic pixel density estimate based on assumed prescription pad dimensions, not physical EXIF DPI from scanner or camera sensors.
4. **Permanent accessibility language:** Replaced "permanently accessible to clinicians and patients" with accurate wording describing application-level accessibility and original-image preservation without implying permanent-retention or legal guarantees.
5. **Sample scores:** Changed fixed point estimates in the calibration sample table to tri-state range bands, avoiding the implication that specific hardcoded scores are guaranteed for research use.

---

## 21. Files Changed

### Created:
- `backend/app/preprocessing/__init__.py`
- `backend/app/preprocessing/config.py`
- `backend/app/preprocessing/metadata.py`
- `backend/app/preprocessing/validator.py`
- `backend/app/preprocessing/quality.py`
- `backend/app/preprocessing/pipeline.py`
- `backend/app/preprocessing/artifacts.py`
- `backend/app/preprocessing/service.py`
- `backend/tests/test_image_validation.py`
- `backend/tests/test_image_quality.py`
- `backend/tests/test_preprocessing_pipeline.py`
- `backend/tests/test_immutability_and_safety.py`
- `backend/tests/test_preprocessing_api.py`
- `scripts/inspect_preprocessing.py`
- `docs/phase-04-completion.md`

### Modified:
- `backend/requirements.txt` (added `numpy>=1.26.0`, `scipy>=1.12.0`)
- `backend/app/schemas/prescription.py` (added Phase 4 response fields)
- `backend/app/services/mock_pipeline.py` (connected preprocessing service)
- `backend/app/api/v1/prescriptions.py` (added `GET /{id}/artifacts` endpoint)
- `backend/tests/conftest.py` (added valid test image and diagnostic fixtures)
- `scripts/test_live_backend.py` (added Phase 4 live verification checks)
- `scripts/browser-e2e-audit.ts` (configured valid prescription test fixture)

---

## 22. Exit Gate

**PHASE 4 EXIT GATE: PASS**

The image preprocessing and quality assessment layer meets all required criteria. Phase 4 is officially frozen for downstream OCR/HTR baseline integration in Phase 5.
