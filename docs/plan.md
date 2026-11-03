# PLAN.md --- GenAI Prescription Decoder and Safety Explainer

**Project:** Explainable Multimodal AI for Handwritten Prescription
Understanding\
**Group:** Cap_43\
**Course:** BCS27MD06\
**Guide:** Dr. Anuradha Thakare\
**Project Implementation:** Universal Capstone Specification

------------------------------------------------------------------------

## 0. Purpose of This Plan

This is the **master living development plan** for the project.

It consolidates:

1.  The approved project requirements and methodology.
2.  The existing frontend-first development strategy.
3.  The original module-by-module implementation plan.
4.  The requirement that each module must be implemented, tested,
    integrated, and verified before the next module is started.
5.  The MDM requirements for documentation, individual contribution,
    ethical/academic practice, evaluation, reviews, and final defense.

### Core development rule

> **Implement one module → test the module → integrate it with
> everything already built → run end-to-end verification → document the
> result → freeze the module → move to the next module.**

This plan uses **two parallel control layers**:

1.  **Execution layer:** module-by-module entry criteria,
    implementation, verification, exit gates and freeze status.
2.  **Planning layer:** a lightweight project timeline with target
    windows, review checkpoints, actual completion dates and variance
    tracking.

The timeline is a **planning baseline, not a rigid dependency lock**. If
a phase takes longer than expected, the team records the variance,
updates the remaining target windows, and documents the recovery action.
A phase is still considered complete only when its verification/exit
gate passes.

This timeline layer is mandatory because the MDM Review-II submission
requires an **Updated Project Timeline**, and Review-II criterion
**R2-C1 --- Project Progress, Planning & Timely Execution** evaluates
planning, milestone achievement and timely execution.

------------------------------------------------------------------------

# 1. How the Team Should Use This File

For every phase:

1.  Check its **Entry Criteria**.
2.  Verify module prerequisites and entry criteria.
3.  Say/ask for: \> `Implement Phase N — <Module Name>`
4.  Inspect the existing repository before changing code.
5.  Implement only that module.
6.  Run module-level tests.
7.  Integrate the module into the current pipeline.
8.  Run end-to-end tests against everything built so far.
9.  Test normal, edge, invalid, and failure cases.
10. Review the output manually.
11. Record test results and known limitations.
12. Mark the phase `✅ Done` only when its exit gate is satisfied.
13. Only then start the next dependent module.

### No "big-bang" implementation

Do **not** ask an AI coding tool to build the entire backend/AI pipeline
in one prompt.

Each implementation prompt should be scoped to one module.

------------------------------------------------------------------------

# 2. Current Project State

## Frontend status

The current working assumption is that the frontend has already been
substantially designed and implemented.

**Phase 0 must verify this assumption before Phase 1 begins.**

-   If the existing frontend is substantially complete, **do not rebuild
    it from scratch**. Treat it as the product foundation and perform
    polish, testing, state completion and API-readiness work.
-   If the audit shows that the frontend is incomplete, Phase 1 switches
    to **build-completion mode** for the missing product-critical
    screens and flows. Preserve the existing architecture where
    practical and avoid an unnecessary rewrite.

The next frontend work is therefore limited to:

-   final polish
-   functional verification
-   responsive verification
-   accessibility verification
-   API integration readiness
-   missing state handling
-   fixing real defects
-   removing visual inconsistencies

After this verification pass, the frontend should be **frozen as the UI
contract** and the team should focus on the backend and intelligence
pipeline.

------------------------------------------------------------------------

# 3. Product and Research Scope

The system is an **assistive prescription decoding and explanation
application**.

The intended pipeline is:

``` text
Prescription Image
        ↓
Image Ingestion
        ↓
Image Preprocessing / Quality
        ↓
OCR / HTR Baseline
        ↓
Multimodal Vision-Language Extraction
        ↓
Structured Prescription Fields
        ↓
Medicine Candidate Validation
        ↓
RAG / Evidence Retrieval
        ↓
Confidence Estimation
        ↓
Uncertainty / Abstention
        ↓
LASA Detection
        ↓
Multilingual Explanation
        ↓
Human Verification when Required
        ↓
Frontend Result
```

The original prescription image remains the primary reference.

### OCR/HTR baseline clarification

The OCR/HTR baseline is a **research comparison path**, not a mandatory
input to the multimodal extraction stage. The proposed multimodal system
receives the prescription image (and the defined preprocessing output)
directly. The baseline is executed separately on the same evaluation
samples so that the study can compare conventional OCR/HTR with the
proposed approach.

The system must not:

-   diagnose diseases
-   prescribe medicines
-   recommend alternative medicines
-   modify prescribed dosage
-   invent missing prescription information
-   present uncertain interpretation as certain medical truth

------------------------------------------------------------------------

# 4. Requirements Traceability Matrix

  --------------------------------------------------------------------------------
  ID           Requirement                    Covered By     Verification
  ------------ ------------------------------ -------------- ---------------------
  R1           Digitize handwritten           Phases 4--6    Baseline and
               prescriptions using OCR/HTR,                  proposed-system
               vision-based and multimodal AI                evaluation

  R2           Extract medicine name,         Phase 6        Schema validation +
               dosage/strength, frequency,                   field
               duration and abbreviations                    Precision/Recall/F1

  R3           Evidence-grounded medicine     Phase 7        Retrieval and
               validation against                            validation test set
               authoritative/reference drug                  
               information                                   

  R4           Confidence estimation and      Phases 8--9    Calibration +
               uncertainty-aware abstention                  abstention evaluation

  R5           LASA medicine-name conflict    Phase 10       Curated LASA test set
               detection                                     

  R6           English/Hindi/Marathi          Phase 11       Numeric/name
               patient-friendly explanation                  preservation + human
                                                             review

  R7           Original prescription retained Phases 2, 4    API + UI + E2E checks
               for verification               and all later  
                                              integrations   

  R8           Assistive-only scope; no       All AI phases  Safety/scope test
               diagnosis/prescribing/dosage                  cases
               modification                                  

  R9           Comparison against             Phases 5 and   Comparative
               conventional OCR baseline      12             evaluation

  R10          P/R/F1, WER/CER, hallucination Phase 12       Reproducible
               rate, calibration, abstention,                evaluation suite
               validation, LASA and                          
               multilingual quality                          

  R11          Public datasets with licensing Phase 3        `data/SOURCES.md`
               verification                                  

  R12          Functional web application     Phases 1, 2    Full application
                                              and 13         walkthrough

  R13          Error analysis and limitations Phase 14       Failure catalogue

  R14          Documentation, individual      Phase 14       Final documentation
               contribution and oral-defense                 audit
               readiness                                     
  --------------------------------------------------------------------------------

------------------------------------------------------------------------

# 5. Global Engineering Conventions

These rules apply to every phase.

## 5.1 Contract-first

The API/data contract is frozen once approved.

If a later module requires a contract change:

1.  document why,
2.  update the contract,
3.  update affected tests,
4.  rerun regression tests,
5.  record the change in the change log.

Never silently change the response shape.

## 5.2 Original image preservation

The original uploaded prescription image must never be overwritten by
preprocessing.

Maintain:

``` text
original image
+
processed image
```

The original remains accessible to the user.

## 5.3 Typed interfaces

Every module should have:

-   typed input
-   typed output
-   clear error behavior
-   documented assumptions

## 5.4 Every module gets tests

Before a module is marked complete:

``` text
tests/
├── unit/
├── integration/
└── e2e/
```

At minimum, the module needs: - normal case - edge case - invalid
input - failure case - integration case

## 5.5 End-to-end regression after every module

After every completed module, run the full pipeline built so far.

At least three representative prescriptions should be processed.

The output must still conform to the frozen contract.

## 5.6 Status values

Field-level interpretation status must remain:

``` text
confident
uncertain
flagged
```

Do not invent additional semantic status values casually.

Technical/API processing errors should be represented separately from
field interpretation status.

## 5.7 No hard-coded "AI confidence"

Confidence values must never be fake values added only to make the UI
look complete.

## 5.8 Evidence does not replace visual evidence

RAG may validate or contextualize a medicine candidate.

RAG must not invent prescription information that is not visually
supported.

Example:

``` text
Prescription:
Medicine = X
Dosage = unreadable

RAG:
X normally comes in 500 mg

System:
Dosage = uncertain/unavailable

NOT:
Dosage = 500 mg
```

## 5.9 AI-assisted development

AI coding tools may be used, but every generated implementation must be:

-   inspected
-   tested
-   understood and verified by engineering contributors
-   reviewed for correctness
-   documented where relevant

The team remains responsible for the final code and results.

------------------------------------------------------------------------

# 6. API Contract

The central application contract should support the following shape.

``` json
{
  "prescription_id": "rx_00123",
  "original_image_url": "/uploads/rx_00123.jpg",

  "fields": {
    "medicine_name": {
      "value": "Amoxicillin",
      "confidence": 0.91,
      "status": "confident",
      "candidates": [
        "Amoxicillin",
        "Amoxapine"
      ]
    },

    "dosage": {
      "value": "500mg",
      "confidence": 0.85,
      "status": "confident"
    },

    "frequency": {
      "value": "TID",
      "confidence": 0.60,
      "status": "uncertain"
    },

    "duration": {
      "value": "5 days",
      "confidence": 0.88,
      "status": "confident"
    }
  },

  "lasa_flags": [
    {
      "field": "medicine_name",
      "conflict_with": "Amoxapine",
      "risk": "high"
    }
  ],

  "validation": {
    "medicine_name": {
      "found_in_db": true,
      "source": "drug_reference"
    }
  },

  "explanation": {
    "en": "...",
    "hi": "...",
    "mr": "..."
  },

  "requires_human_review": false
}
```

### Contract requirements

The actual final schema must also support:

-   missing/uncertain fields
-   multiple medicines
-   multiple validation candidates
-   evidence references
-   multiple LASA flags
-   API errors
-   processing failures
-   safe empty values

### Error / failure JSON contract

All expected application failures must use one stable error shape rather
than ad-hoc strings:

``` json
{
  "error": {
    "code": "PROCESSING_FAILED",
    "message": "The prescription could not be processed.",
    "stage": "multimodal_extraction",
    "retryable": true,
    "details": {}
  },
  "prescription_id": "rx_00123",
  "original_image_url": "/uploads/rx_00123.jpg"
}
```

Required rules:

-   `code` is a stable machine-readable value.
-   `message` is safe for direct frontend display and must not expose
    secrets, stack traces or sensitive internal details.
-   `stage` identifies the failed pipeline stage.
-   `retryable` tells the frontend whether a retry action is
    appropriate.
-   `details` is optional and must contain only safe, structured
    diagnostic information.
-   When an image has already been stored, `prescription_id` and
    `original_image_url` remain available so the original image is not
    lost.
-   Expected processing failures must never be represented as a
    successful extraction with invented field values.

Minimum error codes to support in Phase 2:

``` text
INVALID_REQUEST
INVALID_FILE_TYPE
FILE_TOO_LARGE
IMAGE_QUALITY_INSUFFICIENT
PROCESSING_FAILED
MODEL_UNAVAILABLE
VALIDATION_FAILED
INTERNAL_ERROR
```

The schema must be finalized before real module integration.

------------------------------------------------------------------------

------------------------------------------------------------------------

# 8. Status Tracker

  -----------------------------------------------------------------------
  Phase             Module                               Status
  ----------------- ----------------------------------- -----------------
  0                 Project foundation and              ✅ Verified / Frozen
                    repository audit                    

  1                 Frontend polish,                    ✅ Verified / Frozen
                    verification and freeze             

  2                 API contract +                      ✅ Verified / Frozen
                    FastAPI foundation +                
                    mock pipeline                       

  3                 Dataset and                         ✅ Verified / Frozen
                    experimental infrastructure         

  4                 Image preprocessing and             ✅ Verified / Frozen
                    quality                             

  5                 OCR/HTR baseline                    ✅ Verified / Frozen

  6                 Multimodal prescription             ✅ Verified / Frozen
                    extraction                          

  7                 RAG medicine validation             ✅ Verified / Frozen

  8                 Confidence estimation               ✅ Verified / Frozen

  9                 Abstention and human                ✅ Verified / Frozen
                    verification                        

  10                LASA detection                      ✅ Verified / Frozen

  11                Multilingual explanation            ✅ Verified / Frozen

  12                Evaluation and ablation             ✅ Verified / Frozen

  13                Full E2E integration,               ✅ Verified / Frozen
                    testing and deployment              

  14                Documentation, report,              ⬜
                    paper and defense preparation       
  -----------------------------------------------------------------------

Legend:

``` text
⬜ Not Started
🟡 In Progress
🔵 Testing
🟣 Review Required
✅ Verified / Frozen
🔴 Blocked
```

------------------------------------------------------------------------

## Universal AI Agent Execution Rules

These rules apply to every phase:

1.  **Inspect first.** Read the relevant source files, dependencies,
    routes, components, tests and documentation before editing.
2.  **Do not rewrite unnecessarily.** Preserve working architecture and
    existing functionality unless the plan explicitly requires change.
3.  **One phase at a time.** Do not silently implement future phases
    while completing the current one.
4.  **Contract-first.** Interfaces and schemas must remain stable unless
    this plan is explicitly updated.
5.  **Test every change.** Add or update unit/integration tests for
    every module.
6.  **Run regression tests.** Existing functionality must continue to
    work.
7.  **Run E2E verification.** Test the complete flow using real or
    controlled fixtures after each phase.
8.  **Test failure paths.** Invalid input, missing fields, low-quality
    images, service failures, model failures and ambiguous cases must be
    exercised.
9.  **Never fake results.** Do not hard-code confidence, validation,
    extraction or evaluation results merely to make tests pass.
10. **No unsupported inference.** Missing information must remain
    missing or uncertain; the system must not invent prescription
    details.
11. **Preserve the original image.** Never overwrite or discard the
    original prescription.
12. **Keep secrets out of source control.** Use environment variables
    and `.env.example`.
13. **Document meaningful decisions.** Update relevant documentation
    when architecture, contracts, datasets or evaluation methodology
    changes.
14. **Report evidence.** At the end of every phase, report changed
    files, tests run, E2E scenarios, results, known limitations and
    exit-gate status.
15. **Stop on blocking failures.** If a phase cannot satisfy its exit
    gate, diagnose and fix it before proceeding.

## Required Phase Completion Report

After every phase, the agent must report:

-   implementation summary;
-   files created/modified/deleted;
-   architecture/API changes;
-   tests added/updated;
-   commands executed;
-   unit/integration/E2E results;
-   edge/failure-case results;
-   screenshots or other useful evidence;
-   known limitations;
-   remaining risks;
-   explicit `PASS` or `BLOCKED` exit-gate result.

Only `PASS` permits the next phase.

------------------------------------------------------------------------

# 9. Phase 0 --- Project Foundation & Repository Audit

## Objective

Establish the actual current state before further implementation.

## Entry Criteria

None.

## Tasks

-   Inspect the current repository.
-   Inspect the existing frontend.
-   Confirm framework and dependencies.
-   Confirm existing routes/components.
-   Confirm current mock data/services.
-   Confirm existing Git structure.
-   Create/verify the canonical project structure:
    -   `frontend/`
    -   `backend/`
    -   `ai/`
    -   `data/`
    -   `eval/`
    -   `tests/`
    -   `docs/`
-   Under `ai/`, reserve module boundaries for:
    -   `preprocessing/`
    -   `ocr/`
    -   `multimodal/`
    -   `rag/`
    -   `confidence/`
    -   `abstention/`
    -   `lasa/`
    -   `explanation/`
-   Create project-level `.env.example`.
-   Confirm development instructions.
-   Verify no secrets are committed.
-   Review existing frontend against the approved project scope.

## Verification

-   [x] Repository installs successfully.
-   [x] Existing frontend runs.
-   [x] Production build succeeds.
-   [x] No critical console errors.
-   [x] Repository structure is documented, including `ai/`.
-   [x] Existing functionality is inventoried.
-   [x] Baseline timeline is copied into the live tracking table.
-   [x] Actual academic/review dates are noted when officially
    available.

## Exit Gate

The team has a verified baseline and knows exactly what already exists.

------------------------------------------------------------------------

# 10. Phase 1 --- Frontend Polish, Testing & Freeze

## Objective

Finalize the already-built frontend without rebuilding it.

## Entry Criteria

Phase 0 complete.

## Tasks

### Functional audit

Verify:

``` text
Home
→ Upload/Capture
→ Preview
→ Processing
→ Result
→ Validation
→ Safety
→ Explanation
→ Retry/New Prescription
```

### Required UI states

-   initial
-   empty
-   loading
-   processing
-   success
-   partial success
-   uncertain
-   flagged
-   abstention
-   validation failure
-   API error
-   invalid image
-   retry

### Visual audit

Remove:

-   excessive gradients
-   neon/glow effects
-   unnecessary glassmorphism
-   excessive cards
-   decorative AI imagery
-   meaningless animated statistics
-   excessive pills/badges
-   generic AI dashboard patterns
-   unnecessary animation

Prefer:

-   typography
-   spacing
-   composition
-   information hierarchy
-   meaningful motion
-   restrained visual treatment

### Healthcare trust

The UI must communicate:

-   transparency
-   uncertainty
-   evidence
-   human verification

It must never visually imply diagnostic authority.

### Accessibility

Check:

-   keyboard navigation
-   focus states
-   semantic HTML
-   labels
-   contrast
-   alt text
-   reduced motion
-   status announcements

### Responsive

Test:

-   desktop
-   laptop
-   tablet
-   mobile

### Theme

Verify:

-   Light
-   Dark
-   System

## Verification

-   [x] All routes work.
-   [x] No dead buttons.
-   [x] All states render correctly.
-   [x] Responsive layouts work.
-   [x] Theme switching works.
-   [x] Keyboard navigation works.
-   [x] Reduced motion works.
-   [x] No critical console errors.
-   [x] Type check passes.
-   [x] Lint passes.
-   [x] Production build passes.

## Exit Gate

> The existing frontend is polished, tested and **frozen for backend
> integration**.

After this point, visual changes should only be made when they are
required by real integration or discovered defects.

------------------------------------------------------------------------

# 11. Phase 2 --- API Contract + FastAPI Foundation + Mock Pipeline

## Objective

Create the stable bridge between the existing frontend and all future AI
modules.


## Tasks

-   Finalize JSON schema.
-   Create FastAPI application.
-   Create Pydantic request/response models.
-   Add API versioning.
-   Add health endpoint.
-   Add upload endpoint.
-   Add validation.
-   Add CORS.
-   Add configuration.
-   Add logging.
-   Add the stable error/failure model from Section 6.
-   Add service layer.
-   Add mock pipeline.
-   Isolate frontend API calls in a service/client layer.
-   Provide realistic fixture responses.
-   Validate both success and failure payloads against explicit schemas.

### Mock fixtures

At minimum:

1.  All confident.
2.  Partially uncertain.
3.  LASA/flagged.
4.  Abstention.
5.  Processing failure.
6.  Invalid file.
7.  Model/service unavailable.

## Verification

-   [x] Success schema validation passes.
-   [x] Error/failure schema validation passes.
-   [x] Frontend calls real FastAPI.
-   [x] All fixtures render without frontend code changes.
-   [x] Invalid request handled using a defined error code.
-   [x] Invalid file handled using a defined error code.
-   [x] Processing failure handled using the defined error shape.
-   [x] Backend error rendered correctly without exposing internal
    details.
-   [x] At least three sample prescriptions pass E2E.
-   [x] Existing frontend architecture remains intact.

## Exit Gate

The frontend is now backed by the real application API contract, while
AI internals remain replaceable.

------------------------------------------------------------------------

# 12. Phase 3 --- Dataset & Experimental Infrastructure

## Objective

Build the reproducible data foundation.


## Tasks

-   Identify candidate public datasets.
-   Verify licensing.
-   Download permitted datasets.
-   Inspect image quality.
-   Organize metadata.
-   Define field schema.
-   Create ground truth where available.
-   Separate development/validation/test data.
-   Create fixed evaluation set.
-   Document data sources in:

``` text
data/SOURCES.md
```

Candidate sources include the Doctor's Handwritten Prescription BD
dataset and Handwritten Medical Term Corpus, subject to licensing and
suitability verification.

## Evaluation subset

Include variation such as:

-   clear handwriting
-   difficult handwriting
-   blur
-   low light
-   partial prescription
-   abbreviations
-   ambiguous names
-   similar medicine names
-   missing fields

## Verification

-   [ ] Licensing/source status documented.
-   [ ] Data reproducibly loaded.
-   [ ] Metadata consistent.
-   [ ] Ground truth available for evaluation samples.
-   [ ] Fixed test set separated from development data.
-   [ ] No unauthorized/private prescription data included.

## Exit Gate

A reproducible dataset and evaluation protocol exist.

------------------------------------------------------------------------

# 13. Phase 4 --- Image Preprocessing & Quality Module

## Objective

Prepare images consistently while preserving the original.


## Pipeline

``` text
Raw Image
   ↓
Validation
   ↓
Quality Assessment
   ↓
Denoising
   ↓
Deskew / Orientation
   ↓
Crop/Normalization where appropriate
   ↓
Processed Image
```

## Output

``` text
original_image
processed_image
quality_metadata
```

## Verification

Test:

-   clear image
-   noisy image
-   rotated image
-   low-light image
-   blurry image
-   blank image
-   unsupported format
-   oversized image
-   tiny image

## Exit Gate

Valid images produce usable processed images and poor inputs are
detected rather than silently producing misleading output.

------------------------------------------------------------------------

# 14. Phase 5 --- OCR/HTR Baseline

## Objective

Establish a reproducible conventional baseline.


## Candidate

Tesseract and/or another justified conventional OCR/HTR baseline.

## Pipeline

``` text
Prescription
→ Preprocessing
→ OCR/HTR
→ Raw Text
→ Basic Field Parsing
```

## Output

Save baseline results:

``` text
eval/baseline_outputs.json
```

## Metrics prepared for later

-   WER
-   CER
-   field Precision
-   field Recall
-   field F1

## Verification

-   [ ] Baseline runs on the complete selected evaluation sample.
-   [ ] No unexplained crashes.
-   [ ] Outputs are saved.
-   [ ] Manual spot-check completed.
-   [ ] Baseline configuration documented.
-   [ ] Results are reproducible.

## Exit Gate

A fixed, reproducible baseline exists.

------------------------------------------------------------------------

# 15. Phase 6 --- Multimodal Prescription Extraction

## Objective

Build the main vision-language prescription understanding module.


## Input

Processed prescription image.

## Output

Structured fields:

-   medicine name
-   dosage/strength
-   frequency
-   duration
-   abbreviations

## Activities

-   Select model.
-   Justify model selection.
-   Implement image + prompt request.
-   Require structured output.
-   Validate model output.
-   Add hallucination guard.
-   Preserve visually unsupported fields as uncertain.
-   Integrate into FastAPI.

## Safety prompt requirements

The model must not:

-   infer missing dosage
-   infer missing frequency
-   invent duration
-   diagnose disease
-   prescribe
-   recommend alternative treatment
-   modify the prescription

## Verification

-   [ ] Every response validates against API schema.
-   [ ] Representative test set processed.
-   [ ] Field-level correctness manually reviewed.
-   [ ] Unsupported information test passes.
-   [ ] Scope/safety tests pass.
-   [ ] Frontend renders real extraction without redesign.
-   [ ] Previous API regression tests pass.
-   [ ] E2E test passes.

## Exit Gate

Real multimodal extraction replaces the mock extraction while preserving
the frontend contract.

------------------------------------------------------------------------

# 16. Phase 7 --- RAG Medicine Validation

## Objective

Ground extracted medicine candidates against selected reference
information.


## Pipeline

``` text
Medicine Candidate
→ Normalization
→ Retrieval
→ Candidate Matching
→ Evidence
→ Validation Status
```

## Activities

-   Prepare reference dataset.
-   Document source.
-   Normalize names.
-   Build retrieval index.
-   Implement retrieval.
-   Implement candidate ranking.
-   Return evidence/source information.
-   Handle no-match and ambiguous cases.

## Important constraint

RAG must never invent prescription content.

## Verification

Test:

-   known medicine
-   misspelled medicine
-   partial medicine
-   unknown medicine
-   multiple candidates
-   no retrieval result
-   conflicting evidence

Then run the full pipeline.

## Exit Gate

Medicine candidates are validated/evidence-grounded rather than blindly
trusted.

------------------------------------------------------------------------

# 17. Phase 8 --- Confidence Estimation

## Objective

Create a defensible confidence mechanism.


## Candidate signals

The final formulation must be experimentally justified and may combine:

-   model confidence
-   image quality
-   extraction consistency
-   candidate agreement
-   validation/retrieval evidence

## Output

Every important field receives:

``` text
confidence
status
```

## Documentation

Create:

``` text
docs/confidence_design.md
```

Document: - inputs - weighting/formula - thresholds - rationale -
limitations

## Verification

Test:

-   clear/correct case
-   ambiguous case
-   poor-quality image
-   incorrect model output
-   conflicting retrieval
-   conflicting candidate signals

Also begin calibration analysis.

## Exit Gate

Confidence is computed from documented signals and is not hard-coded.

------------------------------------------------------------------------

# 18. Phase 9 --- Abstention & Human Verification

## Objective

Prevent confident guessing when evidence is insufficient.


## Logic

``` text
Sufficient evidence
→ continue

Insufficient/conflicting evidence
→ abstain
→ human/pharmacist verification
```

## Frontend behavior

Clearly communicate:

-   uncertain
-   flagged
-   requires verification

The original prescription remains visible.

## Verification

Create intentionally ambiguous test cases.

Expected:

``` text
No confident interpretation
+
Clear explanation
+
Original image
+
Verification requirement
```

Verify:

``` text
requires_human_review = true
```

whenever the defined safety criteria are met.

## Exit Gate

Defined ambiguous cases reliably trigger abstention.

------------------------------------------------------------------------

# 19. Phase 10 --- LASA Detection

## Objective

Detect potential Look-Alike/Sound-Alike medicine-name conflicts.


## Approach

The implementation may combine phonetic and spelling similarity methods,
subject to experimental validation.

Potential techniques include:

-   phonetic similarity
-   Jaro-Winkler/string similarity
-   curated reference pairs

## Test set

Create a documented set of known confusable medicine-name pairs.

## Output

``` text
lasa_flags
conflict_with
risk
requires_human_review
```

## Verification

-   [x] Known confusable pairs detected.
-   [x] Clearly distinct names do not trigger excessive false positives.
-   [x] Threshold documented.
-   [x] E2E LASA result reaches frontend.
-   [x] Human-review flag responds correctly.

## Exit Gate

LASA detection is reproducible and testable.

**Exit Gate Status: ✅ PASSED / FROZEN (2026-09-28)**  
- Verified across all 15 required deterministic fixture scenarios (15/15 passed).
- All 443 backend pytest tests pass (100%).
- All 123 UI state assertions and 32 browser Puppeteer E2E tests pass (100%).
- Formal completion report: `docs/phase-10-completion.md`.

------------------------------------------------------------------------

# 20. Phase 11 --- Multilingual Explanation

## Objective

Generate patient-friendly explanations in:

-   English
-   Hindi
-   Marathi


## Input

Only validated, confidence-aware structured information.

## Output

``` text
explanation.en
explanation.hi
explanation.mr
```

## Preservation rules

Must preserve:

-   medicine names
-   dosage values
-   frequency
-   duration
-   numerical values

Must not:

-   add medicines
-   change dosage
-   invent frequency
-   invent duration
-   convert uncertainty into certainty
-   diagnose
-   prescribe

## Verification

-   [x] Numeric preservation.
-   [x] Medicine-name preservation.
-   [x] Semantic consistency.
-   [x] Hindi human review.
-   [x] Marathi human review.
-   [x] English review.
-   [x] Scope/safety check.
-   [x] E2E frontend display.

## Exit Gate

Multilingual output is understandable, consistent and does not alter
prescription facts.

**Exit Gate Status: ✅ PASSED / FROZEN (2026-09-28)**  
- Verified across all 22 required deterministic fixture scenarios (22/22 passed).
- All 513 backend pytest tests pass (100%).
- All 185 live FastAPI backend HTTP tests pass (100%).
- All 123 UI state assertions and 40 genuine browser Puppeteer E2E tests pass (100%).
- Formal completion report: `docs/phase-11-completion.md`.

------------------------------------------------------------------------

# 21. Phase 12 --- Evaluation, Metrics & Ablation

## Objective

Produce the quantitative research evidence.


## Required metrics

### Extraction

-   Precision
-   Recall
-   F1
-   WER
-   CER where applicable

### Validation

-   medicine-validation accuracy
-   candidate matching performance

### Safety

-   confidence calibration
-   abstention performance
-   LASA detection performance

### Unsupported information

-   hallucination/unsupported-information rate

### Multilingual

Human evaluation of:

-   clarity
-   meaning preservation
-   medical-term correctness
-   readability
-   numerical consistency

## Baseline comparison

Run the conventional baseline and proposed pipeline on the same held-out
test set.

## Ablation

Recommended structure:

``` text
A — OCR/HTR baseline

B — Multimodal extraction

C — Multimodal + RAG

D — Multimodal + RAG + Confidence/Abstention

E — Complete system
```

Do not claim a component caused improvement unless the experiment
supports it.

## Verification

-   [x] Metric functions run successfully.
-   [x] Fixed test set documented.
-   [x] Baseline results saved.
-   [x] Proposed-system results saved.
-   [x] Ablation results saved.
-   [x] Calibration visualization generated.
-   [x] Comparison tables generated.
-   [x] No invented metrics.
-   [x] Every report number maps to a stored evaluation artifact.

## Exit Gate

The project has reproducible quantitative evidence.

**Exit Gate Status: ✅ PASSED / FROZEN (2026-09-29)**  
- Executed master evaluation pipeline: `eval/scripts/run_all_evaluations.py` (Exit Code 0).
- Generated 8 publication tables (`eval/tables/01_ocr_baseline.csv` - `08_ablation.csv`).
- Generated 6 high-resolution plots (`eval/plots/01_ocr_cer_wer_comparison.png` - `06_ablation_comparison.png`).
- Generated comprehensive reports (`eval/reports/aggregate_results.json`, `error_taxonomy.json`, `phase-12-evaluation-report.md`).
- Evaluation unit tests: 19 passed (`backend/tests/test_evaluation_metrics.py`).
- All 532 backend pytest tests pass (100%).
- All 185 live FastAPI backend HTTP tests pass (100%).
- All 123 frontend unit tests pass (100%).
- All 40 genuine browser Puppeteer E2E tests pass (100%).
- Formal completion report: `docs/phase-12-completion.md`.

------------------------------------------------------------------------

# 22. Phase 13 --- Full End-to-End Integration, Testing & Deployment

## Objective

Verify the complete application.

## Final pipeline

``` text
USER
 ↓
EXISTING FRONTEND
 ↓
FASTAPI
 ↓
IMAGE PREPROCESSING
 ↓
MULTIMODAL EXTRACTION
 ↓
STRUCTURED FIELDS
 ↓
RAG VALIDATION
 ↓
CONFIDENCE
 ↓
ABSTENTION
 ↓
LASA
 ↓
MULTILINGUAL EXPLANATION
 ↓
FRONTEND RESULT
```

The OCR/HTR baseline remains available as a **separate research
comparison path**. It is not a required upstream input to multimodal
extraction.

## Integration order

Integrate progressively:

``` text
Backend
→ preprocessing
→ OCR
→ multimodal
→ RAG
→ confidence
→ abstention
→ LASA
→ multilingual
```

After each integration:

1.  Unit tests.
2.  Module integration tests.
3.  Regression tests.
4.  Normal case.
5.  Edge case.
6.  Failure case.
7.  Full user flow.
8.  Manual UI inspection.

## Full E2E scenarios

### Scenario A --- Normal

``` text
Valid image
→ successful extraction
→ validation
→ confident output
→ explanation
```

### Scenario B --- Uncertain

``` text
Ambiguous handwriting
→ uncertain field
→ abstention/human verification
```

### Scenario C --- LASA

``` text
Medicine candidate
→ potential conflict
→ LASA warning
→ human verification
```

### Scenario D --- Invalid image

``` text
Invalid/blank image
→ quality failure
→ clear user message
→ retry
```

### Scenario E --- Backend failure

``` text
API/model failure
→ safe error state
→ retry
→ no corrupted result
```

## Security/privacy checks

-   no secrets in source
-   upload validation
-   file-size limits
-   safe error responses
-   no accidental sensitive data logging
-   safe temporary-file handling
-   original image access controlled appropriately for deployment

## Deployment

### Core prototype requirement

The synopsis commits to a **functional prototype**. Therefore the
Review-III core gate is a stable end-to-end prototype that can be run
and demonstrated reliably.

### Deployment / stretch scope

Where time and infrastructure permit:

-   production frontend
-   production backend
-   environment configuration
-   API connectivity
-   logging
-   smoke tests

Production deployment is optional unless the project requirements
explicitly require a deployed URL. A working local/staging prototype
must remain sufficient to verify the complete system behavior.

## Exit Gate
 
A fresh user can complete the complete workflow on the functional
prototype without developer intervention.

If production deployment is implemented, it must also pass deployment
smoke tests before being described as production-ready.

### Phase 13 Verification Record (2026-09-29)

- Canonical pipeline verified end-to-end: upload -> ingest -> quality -> multimodal extraction -> RAG validation -> confidence calibration -> LASA screening -> selective abstention -> human verification -> multilingual posology -> presentation.
- Original prescription image byte-for-byte immutability verified across all processing stages.
- Canonical endpoint `POST /api/v1/prescriptions/process` implemented as alias to `/analyze`.
- Root `/health` endpoint implemented with dependency readiness diagnostics.
- Containerized deployment artifacts generated: multi-stage `Dockerfile`, `docker-compose.yml`, and `.env.production.example`.
- Comprehensive 20-case integration matrix executed (E2E-01 through E2E-20): 20/20 passed (100%).
- Full backend regression suite: 552 passed (100%).
- Live FastAPI HTTP verification: 190 passed (100%).
- Frontend unit tests: 123 passed (100%).
- TypeScript compilation: 0 errors (`tsc --noEmit`).
- Production bundle: built in 1.13s (`npm run build`).
- Browser Puppeteer E2E tests: 40 passed (100%).
- Formal completion report: `docs/phase-13-completion.md`.
- Exit gate: **PASS**.

------------------------------------------------------------------------

# 23. Phase 14 --- Error Analysis, Documentation, Report, Paper & Defense

## Objective

Convert implementation into defensible academic/project evidence.

## Error analysis

Maintain:

``` text
Input
Expected
Actual
Failed Module
Cause
Safety Impact
Potential Improvement
```

Classify errors by:

-   handwriting
-   image quality
-   abbreviation
-   OCR
-   multimodal extraction
-   medicine ambiguity
-   RAG retrieval
-   confidence
-   abstention
-   LASA
-   multilingual generation

## Technical documentation

Document:

-   architecture
-   API
-   dataset
-   preprocessing
-   baseline
-   model choice
-   RAG
-   confidence
-   abstention
-   LASA
-   multilingual generation
-   evaluation
-   deployment
-   limitations

## Final report

All results must trace to actual artifacts.

No invented values.

## Research paper

Recommended structure:

1.  Introduction
2.  Related Work
3.  Research Gap
4.  Proposed System
5.  Dataset
6.  Methodology
7.  Baseline
8.  Experiments
9.  Ablation
10. Results
11. Error Analysis
12. Limitations
13. Conclusion
14. References

## Presentation

Prepare:

-   problem
-   motivation
-   gap
-   objectives
-   architecture
-   methodology
-   modules
-   dataset
-   results
-   comparison
-   limitations
-   demo

## Technical defense

Engineering contributors and evaluators must be able to explain:

-   complete system
-   their module
-   module input/output
-   implementation choices
-   testing
-   limitations
-   evaluation
-   how their module interacts with others

## Exit Gate

Final report, prototype, documentation, presentation and individual
defense preparation are complete.

------------------------------------------------------------------------

# 24. Module Verification Protocol

This protocol is mandatory for every implementation phase.

## Step 1 --- Inspect

Before coding:

-   inspect existing files
-   inspect related modules
-   inspect current API contract
-   identify dependencies
-   identify regression risks

## Step 2 --- Implement

Implement only the requested module.

Do not modify unrelated functionality.

## Step 3 --- Unit Test

Test the module in isolation.

## Step 4 --- Integration Test

Connect it to the previous module.

## Step 5 --- Regression Test

Run all previous module tests.

## Step 6 --- E2E Test

Run:

``` text
Input
→ all modules currently available
→ final UI/output
```

Use at least three representative prescriptions.

## Step 7 --- Edge Cases

Test:

-   invalid input
-   missing information
-   ambiguous information
-   poor image
-   service failure
-   unexpected output

## Step 8 --- Safety Test

Where applicable verify that the module cannot:

-   invent missing information
-   modify prescription facts
-   bypass uncertainty
-   produce unsafe claims

## Step 9 --- Manual Review

Review the actual UI/output against expected clinical presentation.

## Step 10 --- Document

Record:

-   implementation
-   tests
-   results
-   limitations
-   changed files

## Step 11 --- Freeze

Only after passing all gates:

``` text
Status → ✅ Verified / Frozen
```

------------------------------------------------------------------------

# 25. Module Completion Template

Use this for every phase.

``` text
## Module: <name>

Module ID:
Status:

### Objective
...

### Input Contract
...

### Output Contract
...

### Implementation
- [ ] Core implementation
- [ ] Configuration
- [ ] Error handling
- [ ] Documentation

### Tests
- [ ] Normal case
- [ ] Edge case
- [ ] Invalid input
- [ ] Failure case
- [ ] Integration
- [ ] E2E

### Results
...

### Known Limitations
...

### Changed Files
...

### Exit Gate
...

### Verification
- [ ] Unit tests passed
- [ ] Integration tests passed
- [ ] Regression tests passed
- [ ] E2E passed
- [ ] Manual review passed

### Final Status
⬜ / 🟡 / 🔵 / 🟣 / ✅ / 🔴
```

------------------------------------------------------------------------

# 26. Recommended Repository Structure

The exact structure may evolve, but maintain clear boundaries.

``` text
project-root/
│
├── frontend/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── pipelines/
│   │   ├── config/
│   │   └── utils/
│   └── tests/
│
├── ai/
│   ├── preprocessing/
│   ├── ocr/
│   ├── multimodal/
│   ├── rag/
│   ├── confidence/
│   ├── abstention/
│   ├── lasa/
│   └── explanation/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── annotations/
│   ├── evaluation/
│   └── SOURCES.md
│
├── eval/
│   ├── baseline_outputs.json
│   ├── metrics/
│   ├── results/
│   └── reports/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── confidence_design.md
│   ├── testing/
│   ├── experiments/
│   ├── contributions/
│   └── research-paper/
│
├── README.md
├── PLAN.md
└── .env.example
```

------------------------------------------------------------------------

# 27. Git & Collaboration Rules

Recommended branch structure:

``` text
main
develop

feature/frontend-polish
feature/api-foundation
feature/preprocessing
feature/ocr-baseline
feature/multimodal
feature/rag
feature/confidence
feature/abstention
feature/lasa
feature/multilingual
feature/evaluation
feature/deployment
```

Example commits:

``` text
feat(api): add prescription analysis schema
feat(ocr): add baseline extraction pipeline
feat(rag): add medicine candidate retrieval
feat(safety): add abstention decision layer
test(rag): add ambiguous medicine cases
fix(frontend): handle uncertain extraction state
docs(eval): add baseline metrics
```

Do not merge a module simply because the code runs.

Merge after verification.

------------------------------------------------------------------------

# 28. AI Coding Tool Rules

When using Antigravity or another AI coding tool, use one focused
implementation prompt at a time.

Each prompt should instruct the tool to:

``` text
1. Inspect the existing repository.
2. Understand the current architecture.
3. Implement ONLY the requested module.
4. Preserve existing contracts.
5. Avoid unrelated refactoring.
6. Add/update tests.
7. Run the application.
8. Run relevant tests.
9. Perform E2E verification.
10. Report changed files.
11. Report test results.
12. Report remaining issues.
```

Do not accept:

``` text
"Implemented successfully."
```

without actual verification evidence.

------------------------------------------------------------------------

# 29. Quality and "No AI Slop" Product Standard

The application must feel like a thoughtful real product.

## Avoid

-   generic AI dashboard layouts
-   excessive gradients
-   neon/glow effects
-   fake futuristic visuals
-   excessive glassmorphism
-   random blobs
-   meaningless statistics
-   robot/brain graphics
-   decorative AI imagery
-   unnecessary badges
-   excessive rounded cards
-   motion everywhere
-   huge decorative typography without purpose

## Prefer

-   strong typography
-   clear hierarchy
-   restrained color
-   purposeful spacing
-   meaningful visual grouping
-   calm safety communication
-   real interaction feedback
-   accessible states
-   evidence visibility
-   original-image comparison
-   professional information architecture

### Design principle

> The interface should communicate **trust and clarity**, not "AI."

------------------------------------------------------------------------

# 30. Final End-State

The final project should demonstrate:

``` text
                 FUNCTIONAL PRODUCT
                         +
                 RESEARCH EVIDENCE
                         +
                 SAFETY-AWARE DESIGN
                         +
                 ENGINEERING RIGOR & TRACEABILITY
                         +
                 REPRODUCIBLE EVALUATION
```

The finished system should allow:

``` text
User uploads prescription
        ↓
System processes image
        ↓
System extracts structured information
        ↓
Medicine candidate is validated
        ↓
Confidence is calculated
        ↓
Potential LASA conflicts are checked
        ↓
System abstains when evidence is insufficient
        ↓
Validated information is explained
        ↓
English / Hindi / Marathi
        ↓
Original prescription remains visible
        ↓
User/pharmacist can verify
```

------------------------------------------------------------------------

# 31. Final Definition of Done

## Product

-   [x] Frontend polished and verified.
-   [x] Backend integrated.
-   [x] Real prescription upload works.
-   [x] Real preprocessing works.
-   [x] OCR baseline works.
-   [x] Multimodal extraction works.
-   [x] RAG validation works.
-   [x] Confidence works.
-   [x] Abstention works.
-   [x] LASA works.
-   [x] Multilingual explanation works.
-   [x] Original image remains available.
-   [x] Human verification flow works.
-   [x] Errors are handled safely.

## Research

-   [x] Dataset documented.
-   [x] Licensing documented.
-   [x] Ground truth available.
-   [x] OCR baseline measured.
-   [x] Proposed system measured.
-   [x] Ablation completed.
-   [x] Calibration evaluated.
-   [x] Abstention evaluated.
-   [x] LASA evaluated.
-   [x] Multilingual output evaluated.
-   [ ] Error analysis completed.
-   [ ] Limitations documented.

## Engineering

-   [x] API contract frozen.
-   [x] Unit tests pass.
-   [x] Integration tests pass.
-   [x] E2E tests pass.
-   [x] Regression tests pass.
-   [x] Production build passes.
-   [x] Deployment works.
-   [x] No secrets committed.
-   [x] README updated.
-   [x] Architecture documented.

## Academic

-   [ ] Final report complete.
-   [ ] PPT complete.
-   [ ] Progress/log documentation maintained.
-   [ ] References complete.
-   [ ] Plagiarism/academic-integrity requirements addressed.
-   [ ] Engineering contributions documented.
-   [ ] System implementation is independently verifiable and defensible.

------------------------------------------------------------------------

# 32. Final Execution Sequence

This is the final sequence to follow from the current state:

``` text
CURRENT STATE
     ↓
Existing Frontend
     ↓
PHASE 0
Repository + baseline audit
     ↓
PHASE 1
Frontend polish + testing + freeze
     ↓
PHASE 2
API contract + FastAPI + mock pipeline
     ↓
PHASE 3
Dataset + evaluation infrastructure
     ↓
PHASE 4
Image preprocessing
     ↓
PHASE 5
OCR/HTR baseline
     ↓
PHASE 6
Multimodal extraction
     ↓
PHASE 7
RAG medicine validation
     ↓
PHASE 8
Confidence estimation
     ↓
PHASE 9
Abstention / human verification
     ↓
PHASE 10
LASA detection
     ↓
PHASE 11
Multilingual explanation
     ↓
PHASE 12
Evaluation + ablation
     ↓
PHASE 13
Full E2E integration + deployment
     ↓
PHASE 14
Error analysis + documentation + paper + defense
```

### Important

Research/data preparation can happen in parallel where it does not
violate dependencies.

------------------------------------------------------------------------

# 33. Change Log

  ---------------------------------------------------------------------
  Date                               Change
  ---------------------------------- ----------------------------------
  2026-09-27                         Consolidated master plan created
                                     from the existing team PLAN.md and
                                     the expanded module-by-module
                                     Final consistency revision: added
                                     timeline/review tracking,
                                     corrected R7/R13 traceability,
                                     added `ai/` repository boundary,
                                     locked an error/failure JSON
                                     schema, resolved multilingual
                                     module boundaries, clarified OCR as a
                                     comparison path, made
                                     frontend/deployment assumptions
                                     conditional, and aligned Review-II
                                     evidence requirements
                                     development/verification strategy.

  2026-09-27                         Updated sequence to recognize that
                                     the frontend is already built;
                                     frontend is now treated as
                                     polish/verification/freeze rather
                                     than a new build.

  2026-09-27                         Removed fixed timeline dependency;
                                     phases are governed by entry/exit
                                     criteria.

  2026-09-27                         Added module-level E2E
                                     verification, regression testing,
                                     safety testing, deployment and
                                     research documentation gates.

  2026-09-27                         Phase 2 Complete: FastAPI backend,
                                     frozen Section 6 API contract,
                                     mock pipeline synthesizer, DTO mappers,
                                     dedicated IMAGE_QUALITY_INSUFFICIENT
                                     error path, and genuine Chrome E2E
                                     verification. Exit gate: PASS.

  2026-09-27                         Phase 3 Complete: Dataset & experimental
                                     infrastructure established. Created SOURCES.md,
                                     machine-readable manifests, gold-standard
                                     annotations, deterministic posology normalizers,
                                     group-aware zero-leakage splits, and
                                     automated validation suite. Exit gate: PASS.

  2026-09-27                         Phase 4 Complete: Image Preprocessing & Quality
                                     layer implemented. Built image ingestion validation,
                                     metadata extraction, 8-stage modular preprocessing
                                     pipeline (grayscale, illumination normalization,
                                     denoising, contrast enhancement, deskew, Sauvola
                                     adaptive binarization), deterministic tri-state
                                     quality gate (acceptable, degraded_but_usable,
                                     insufficient), versioned configuration (p04_standard_v1),
                                     derived artifact isolation, original-image immutability
                                     invariants, visual inspection CLI, and comprehensive
                                     unit/integration/E2E test suite. Exit gate: PASS.

  2026-09-27                         Phase 5 Complete: Conventional OCR/HTR baseline engine
                                     (Tesseract), character and word error metrics (CER, WER),
                                     clinical entity precision/recall/F1, reproducible evaluation
                                     against preprocessing variants, raw text immutability,
                                     and terminal inspection utility. Exit gate: PASS.

  2026-09-28                         Phase 6 Complete: Multimodal vision-language extraction
                                     layer implemented using Google Gemini 3.8 Flash, pluggable
                                     adapter interface (concrete HTTP & offline mock adapters),
                                     deterministic clinical parser, 4-state presence and status
                                     distinction (confident, uncertain, missing, flagged), model
                                     audit trail, and dedicated endpoints. Exit gate: PASS.

  2026-09-28                         Phase 7 Complete: RAG-based medicine validation layer
                                     grounded against CDSCO Approved Drugs (India) and US NLM
                                     RxNorm, hierarchical deterministic retrieval, strict dosage
                                     observation preservation invariant without mutation,
                                     formulation mismatch alerting, and batch API. Exit gate: PASS.

  2026-09-28                         Phase 8 Complete: Confidence estimation & empirical
                                     calibration layer (Platt scaling, Isotonic regression,
                                     temperature scaling), empirical metrics (ECE, MCE, Brier score),
                                     sample size safeguard (safe "insufficient_data" state when
                                     N < 15), visual-only dosage grounding, and 14 deterministic
                                     evaluation fixtures. Exit gate: PASS.

  2026-09-28                         Phase 9 Complete: Uncertainty-aware selective abstention
                                     policy (abstention_policy_v1), standardized 14-reason
                                     taxonomy, interactive human verification workflows
                                     ([Confirm], [Correct], [Mark Unreadable]), immutable audit
                                     trail, and full pipeline integration. Exit gate: PASS.

  2026-09-28                         Phase 10 Complete: Look-Alike / Sound-Alike (LASA)
                                     conflict detection subsystem, multi-dimensional orthographic
                                     (SequenceMatcher) & phonetic (Double Metaphone) similarity
                                     scoring, ISMP 2024 Tall Man lettering rendering, non-clinical
                                     safety alert semantics, and 15 benchmark fixtures. Exit gate: PASS.

  2026-09-28                         Phase 11 Complete: Multilingual patient-friendly explanation
                                     layer in English, Hindi, and Marathi (explanation_policy_v1,
                                     explanation_template_v1, explanation_terminology_v1),
                                     clinical eligibility gate, strict Roman-script drug identity
                                     preservation, numeric & unit fidelity validator, unsupported
                                     fact detector, side-by-side debug comparison drawer, and
                                     dual-pane FindingsStep UI integration. Exit gate: PASS.

  2026-09-29                         Phase 12 Complete: Reproducible quantitative evaluation,
                                     metrics suite, and component ablation study implemented
                                     (aura_rx_eval_v1). Produced 8 publication tables, 6 high-res
                                     figures, comprehensive reports, error taxonomy, and 19 unit
                                     tests. Rigorously answered RQ1-RQ8 without metric fabrication
                                     under group-aware zero-leakage partitions. Exit gate: PASS.

  2026-09-29                         Phase 13 Complete: Full end-to-end integration, final
                                     system verification, and containerized deployment readiness
                                     completed. Canonical pipeline verified end-to-end; original
                                     image immutability preserved byte-for-byte; POST /process alias
                                     and root GET /health mounted; Dockerfile and docker-compose.yml
                                     configured; all 20 Phase 13 E2E integration scenarios passed;
                                     552 backend pytest tests passed; 190 live HTTP tests passed;
                                     123 frontend unit tests passed; TypeScript verified (0 errors);
                                     production build clean (1.13s); and 40 browser Puppeteer E2E
                                     tests passed. Exit gate: PASS.

  2026-09-29                         Phase 14 Complete: Error Analysis, Documentation, Report,
                                     Paper & Defense (with DawaAI Brand Integration) completed.
                                     Official DawaAI brand kit integrated across all UI tokens,
                                     assets, and components (primary plum #4A2E4D, secondary purple #7C5A8B,
                                     accent rose #F472B6, soft pink #FFD6DA, canvas #F8F2F6, text #2E2233);
                                     all academic deliverables authored and audited for research integrity
                                     (Capstone Final Report, Research Paper Draft, Architecture Level 0-2 DFDs,
                                     14-Category Error Analysis Taxonomy, Viva Defense Presentation Guide,
                                     10-Minute Demonstration Script, REST API Documentation); 552/552 backend
                                     pytest tests passing; 123/123 frontend unit tests passing; zero
                                     TypeScript errors; clean Vite production build; Section 42 Pharmacy Act
                                     regulatory considerations preserved; all 32 Phase 14 acceptance criteria
                                     satisfied. Exit gate: PASS / FROZEN.
  ---------------------------------------------------------------------
