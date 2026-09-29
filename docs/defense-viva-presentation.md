# Viva Defense Presentation & Examiner Q&A Guide
## Explainable Multimodal AI for Handwritten Prescription Understanding (DawaAI)

**Academic Project Title:** Explainable Multimodal AI for Handwritten Prescription Understanding  
**Product / Brand Identity:** DawaAI (*Your Prescription, Made Clear.*)  
**System Classification:** Deployment-Ready Assistive Research Prototype for Academic Demonstration  
**Candidate:** Swayam Mandhani  
**Degree:** B.Tech / Capstone Defense  
**Session:** Final Examination / Viva Voce  
**Date:** March 2026

---

## Part 1: Slide-by-Slide Defense Presentation Deck

### Slide 1: Title & Introduction
- **Slide Title:** Explainable Multimodal AI for Handwritten Prescription Understanding
- **Subtitle:** A Calibrated, Multi-Tiered Clinical Intelligence Framework (DawaAI)
- **Candidate:** Swayam Mandhani
- **Visuals:** DawaAI official brand emblem (plum cross with tilted rose pill), dual-pane interface layout.
- **Speaker Notes (45 sec):**
  > *"Good morning, respected members of the evaluation committee and examiners. Today, I am presenting our capstone project: 'Explainable Multimodal AI for Handwritten Prescription Understanding', embodied in our assistive research prototype, DawaAI. In outpatient medicine, the handwritten prescription remains ubiquitous, yet cursive illegibility and confusable drug nomenclature create risks of medication dispensing errors. DawaAI investigates a multi-tiered architecture combining document preprocessing, multimodal vision-language extraction, authoritative formulary grounding against CDSCO and RxNorm compendia, ISMP Tall Man screening, selective abstention, and registered pharmacist verification."*

---

### Slide 2: Healthcare Context & Clinical Motivation
- **Key Points:**
  - Preventable medication errors cause significant morbidity globally, injuring an estimated 1.5 million people annually in the US (IOM).
  - Outpatient care in India relies heavily on handwritten paper prescriptions.
  - Cursive illegibility, cryptic Latin abbreviations (*q.d.* vs. *q.i.d.*), and Look-Alike Sound-Alike (LASA) drug pairs.
  - Statutory Reality: Section 42 of the Indian Pharmacy Act (1948) mandates that only a Registered Pharmacist may compound or dispense medicines on prescription.
- **Speaker Notes (60 sec):**
  > *"The motivation for this research stems from outpatient patient safety. Dispensing errors arising from misread dosages or confusable drug names represent a recognized clinical hazard. Furthermore, under Section 42 of the Indian Pharmacy Act (1948), dispensing medication without the supervision of a Registered Pharmacist is an offence. For this reason, DawaAI is architected strictly as an assistive research prototype designed with pharmacist-in-the-loop verification, not as an autonomous dispensing machine."*

---

### Slide 3: Research Questions & Core Objectives
- **Key Points:**
  - **RQ1:** How accurately can clinical prescription fields be extracted from doctor handwriting?
  - **RQ2:** How does multimodal vision-language extraction compare with conventional OCR?
  - **RQ3:** Does RAG improve medicine formulation validation without hallucination?
  - **RQ4:** Does confidence calibration provide meaningful reliability information?
  - **RQ5:** Does selective abstention correctly isolate unreadable or ambiguous scripts?
  - **RQ6:** How well does LASA conflict screening detect confusable drug names?
  - **RQ7:** Does vernacular explanation in Hindi and Marathi preserve factual posology?
  - **RQ8:** What does the component ablation study reveal?
- **Speaker Notes (45 sec):**
  > *"We structured our investigation around eight core research questions covering extraction accuracy, comparison with conventional OCR baselines, RAG formulary grounding, uncertainty estimation, selective abstention, LASA screening, multilingual posology delivery, and component ablation."*

---

### Slide 4: Limitations of Existing Approaches
- **Comparison Points:**
  - *Conventional OCR (Tesseract 5.4):* High Character Error Rates on unconstrained cursive handwriting without domain-specific medical lexicon constraints.
  - *1D Deep HTR (CRNN):* Limited on two-dimensional prescription layouts containing tabular schedules, stamps, and marginalia.
  - *Ungrounded Vision-Language LLMs:* Vulnerable to generating plausible-sounding hallucinations on ambiguous handwriting when not constrained by formal medical compendia.
- **Speaker Notes (45 sec):**
  > *"Existing approaches face complementary limitations: conventional OCR degrades on continuous cursive handwriting, while ungrounded generative vision-language models risk hallucinating high-frequency drug names when confronted with degraded ink. DawaAI addresses this by grounding extracted tokens against official pharmacopeias and enforcing an uncertainty-aware selective abstention policy."*

---

### Slide 5: System Architecture Overview
- **Pipeline Stages:**
  1. *Stage 1:* Adaptive Document Conditioning & Quality Validation (Phase 4).
  2. *Stage 2:* Multimodal Vision-Language Extraction via Pluggable Adapters & Deterministic Parser (Phase 6).
  3. *Stage 3:* Formulary Grounding against CDSCO & RxNorm with Strict Dosage Preservation (Phase 7).
  4. *Stage 4:* ISMP 2024 Tall Man LASA Collision Screening (Phase 10).
  5. *Stage 5:* Confidence Estimation with Sample-Size Safeguards & Selective Abstention (Phases 8 & 9).
  6. *Stage 6:* Vernacular Posology Delivery (EN/HI/MR) & Pharmacist Verification Workflows (Phases 9 & 11).
- **Speaker Notes (60 sec):**
  > *"Here is the multi-tiered architecture of DawaAI. Incoming captures are validated for optical quality, binarized with Sauvola thresholding, and deskewed. Multimodal vision-language adapters extract structured entities, which are parsed deterministically into four states. Entities are grounded against CDSCO and RxNorm compendia, screened for LASA conflicts, evaluated under our uncertainty policy, and presented in an explainable dual-pane workspace for pharmacist verification."*

---

### Slide 6: Adaptive Document Preprocessing (Phase 4)
- **Technical Implementation:**
  - Heuristic optical quality metrics: brightness, contrast variance, and blur assessment.
  - Sauvola adaptive local binarization dynamically adjusts threshold $T(x,y)$ over local windows.
  - Radon transform baseline estimation corrects skew within $[-45^\circ, +45^\circ]$ when $|\theta| \ge 0.5^\circ$.
  - Contrast stretching and normalization across dynamic ranges.
- **Speaker Notes (45 sec):**
  > *"Real-world prescriptions often suffer from uneven illumination and paper artifacts. In Phase 4, we implemented an adaptive preprocessing pipeline combining Sauvola local thresholding and Radon deskewing. On our evaluation cohort, contrast enhancement reduced Tesseract CER from 3.10 to 0.81 compared to unenhanced raw captures."*

---

### Slide 7: Multimodal Extraction Architecture (Phase 6)
- **Key Concepts:**
  - Pluggable adapter architecture: supports concrete cloud APIs (Google Gemini Flash) and deterministic offline mock adapters for automated testing.
  - Deterministic clinical parser: assigns four explicit states: `confident`, `uncertain`, `missing`, `flagged`.
  - Spatial reference coordinates: retains bounding box coordinates referencing extracted fields to the document canvas.
  - Model audit trail: logs execution timestamp, model identifier, and prompt hash.
- **Speaker Notes (45 sec):**
  > *"In Phase 6, we implemented a decoupled multimodal adapter architecture. Rather than relying on ungrounded generation, raw model outputs are parsed deterministically into structured posology fields with explicit status classifications. This provides a transparent pipeline where every entity's extraction state is fully auditable."*

---

### Slide 8: Formulary Grounding & Validation (Phase 7)
- **Compendia Integration:**
  - **CDSCO National Formulary:** Validates Indian generic molecules, approved fixed-dose combinations, and commercial brands.
  - **NLM RxNorm:** Normalizes trade names to Concept Unique Identifiers (RxCUI) and active ingredient dosages.
  - **Dosage Preservation Invariant:** Extracted dosage strings are strictly preserved as observed evidence and are never silently altered to match formulary entries.
- **Speaker Notes (45 sec):**
  > *"To safeguard against hallucinated medications, Phase 7 grounds candidate entities against the CDSCO national formulary of India and US NLM RxNorm. A critical safety invariant in our architecture is dosage preservation: the system never mutates or normalizes an observed dosage string to match an external database entry without clinician verification."*

---

### Slide 9: ISMP Tall Man LASA Collision Screening (Phase 10)
- **Safety Mechanism:**
  - Combined orthographic (`SequenceMatcher`) and phonetic (`Double Metaphone`) similarity metrics.
  - Evaluated on curated high-risk ISMP 2024 confusable drug pairs and negative controls.
  - Transformation to ISMP Tall Man lettering (e.g., `predniSONE` vs. `prednisoLONE`).
  - Emits non-clinical safety alert banners requiring explicit clinician verification.
- **Speaker Notes (45 sec):**
  > *"Look-Alike Sound-Alike drug name confusion is a recognized clinical hazard. Phase 10 screens candidate drug pairs using dual orthographic and phonetic similarity metrics against curated ISMP confusable pairs. Detected confusable drugs are formatted with ISMP Tall Man lettering and presented with safety warning banners."*

---

### Slide 10: Confidence Estimation & Sample-Size Safeguards (Phase 8)
- **The Problem:** Raw deep learning probabilities are frequently overconfident on out-of-distribution inputs.
- **Sample-Size Safeguard:**
  - On the actual $N=7$ evaluation cohort, the sample size is insufficient for reliable empirical calibration ($N < 15$).
  - Per Section 20 of `PLAN.md`, the pipeline enforces `calibration_status = "insufficient_data"` and `calibrated_confidence = null` rather than fabricating ungrounded calibration numbers.
- **Synthetic Calibration-Method Verification Only (Not Clinical Calibration Evidence):**
  - Algorithmic verification on the synthetic verification cohort ($N=15$, with 5 scenario-level implementation test fixtures evaluated in Phase 12 EXP-04): Raw ECE **0.2380** $\rightarrow$ Calibrated ECE **0.1500**.
- **Speaker Notes (60 sec):**
  > *"In Phase 8, we implemented confidence estimation and calibration tools. A crucial research integrity feature is our sample-size safeguard: empirical calibration requires large cohorts, so for our N=7 development cohort, the pipeline explicitly marks calibration_status as 'insufficient_data'. We do not claim validated clinical calibration performance; our algorithmic calibration testing on the synthetic verification cohort demonstrated ECE reduction from 0.238 to 0.150 as a method verification only."*

---

### Slide 11: Selective Abstention Policy (Phase 9)
- **Formulation:**
  $$\text{Decision}(x) = \begin{cases} f(x) & \text{if } c(x) \ge \tau \\ \text{ABSTAIN} & \text{if } c(x) < \tau \end{cases}$$
- **Evaluated Cohort Observations:**
  - Under the configured production default $\tau = 0.80$ on the evaluated cohort: Coverage = **0.1000** (10%), Selective Accuracy = **1.0000** (100% on accepted cases, 90% abstained).
  - On the curated $N=7$ demo samples: 6/7 cases were accepted (Coverage = **85.7%**) and the accepted subset achieved **100% observed selective accuracy**.
  - *Scope Note:* These results describe the evaluated cohort and do not constitute a universal clinical safety guarantee.
- **Speaker Notes (60 sec):**
  > *"Under Chow's rule of selective classification, the system trades complete coverage for accuracy on accepted predictions by abstaining on ambiguous cases. On our curated N=7 demo samples, 6 of 7 cases were accepted with 100% observed selective accuracy on the accepted subset, while the degraded sample was safely abstained. We explicitly disclose that this is an observation on the evaluated cohort and not a universal clinical guarantee."*

---

### Slide 12: Pharmacist Verification Workflow (Phases 9 & 13)
- **Section 42 Regulatory Considerations:**
  - Assistive research prototype disclaimers embedded across workspace views.
  - The software does not autonomously dispense medication.
  - Interactive human verification endpoints: `/api/v1/verification/{id}/fields/{f}/confirm`, `/correct`, `/unreadable`.
  - Verification actions are logged in an immutable audit trail.
- **Speaker Notes (45 sec):**
  > *"To incorporate regulatory considerations under Section 42 of the Pharmacy Act, DawaAI enforces human-in-the-loop oversight. Clinicians can confirm, correct, or mark fields as unreadable. Every verification event is timestamped and recorded in an audit trail ledger."*

---

### Slide 13: Vernacular Posology Delivery (Phase 11)
- **Multilingual Support:**
  - Plain-language translation into English, Hindi (हिन्दी), and Marathi (मराठी).
  - Four standardized diurnal posology slots: Morning, Afternoon, Evening, Bedtime.
  - Spoken audio synthesis preview via Web Speech API.
  - Automated factual fidelity on evaluated set: 100% Roman drug name preservation, 84.2% numeric fidelity, 0% unsupported claims.
- **Speaker Notes (45 sec):**
  > *"To assist patients with posology comprehension, Phase 11 translates structured clinical entities into plain-language schedules in English, Hindi, and Marathi across four daily time slots. Automated evaluation showed 100% Roman drug name preservation and 84.2% numerical fidelity across all three target languages."*

---

### Slide 14: Quantitative Evaluation Summary (Phase 12)
- **Empirical Findings Summary:**
  - Conventional OCR Baseline (Tesseract 5.4.0 on $N=7$): Enhanced CER: 0.8076, WER: 1.1227; Raw CER: 3.1033.
  - Multimodal Vision-Language Extraction (Phase 6): Macro F1: 0.1976 across posology fields (Dosage: 0.3000, Duration: 0.3000, Frequency: 0.1905).
  - RAG Validation (Phase 7): 100% accuracy on 43 reference/behavioral fixtures; 0 dosage mutations.
  - LASA Screening (Phase 10): 1.0000 recall on 20 curated ISMP pairs; 0.9091 precision on combined set.
  - Multilingual Fidelity (Phase 11): 100% Roman drug name preservation, 84.2% numerical fidelity.
- **Speaker Notes (45 sec):**
  > *"Our Phase 12 quantitative evaluation produced eight publication-ready tables and six plots across 48 automated tests. The empirical baseline confirmed that conventional OCR struggles on cursive handwriting, while multimodal extraction parsed structured posology attributes with Macro F1 of 0.1976, highlighting the vital role of downstream formulary grounding and human verification."*

---

### Slide 15: Observed Stress Case Deep Dive (Sample DOC-RX-005)
- **Stress Case Characteristics:**
  - Severe paper crumpling, liquid stain, ink bleed-through from reverse side.
  - Baseline OCR exhibited elevated character insertion rates due to background noise.
  - DawaAI Behavior: Quality metrics detected degraded background; confidence signal dropped; sample-size safeguard reported `insufficient_data`; selective abstention halted automated preview and routed the case to clinician review.
- **Speaker Notes (60 sec):**
  > *"Sample DOC-RX-005 represents a curated physical stress case featuring heavy ink bleed-through. When processed through DawaAI, the optical quality metrics and low confidence signal triggered full-document abstention. Rather than attempting an ungrounded guess, the system halted automated output and escalated the case for human review."*

---

### Slide 16: Engineering Rigor & Test Suite Integrity
- **Test Infrastructure:**
  - Backend: **552 / 552 Pytest unit & integration tests passing** (0 failures).
  - Frontend: **123 / 123 automated UI state & DTO tests passing** (0 failures).
  - TypeScript strict compilation: **0 type errors**.
  - Production Vite bundle: **Clean compilation in 617 ms**.
  - DawaAI Brand Kit: Plum/pink palette, typography, and SVG assets harmonized.
- **Speaker Notes (45 sec):**
  > *"Beyond theoretical modeling, DawaAI is engineered with high software standards. Our test suites include 552 backend pytest tests and 123 automated frontend state tests validating all 14 clinical UI states. All 675 tests pass with zero failures and zero TypeScript errors."*

---

### Slide 17: Limitations & Research Validity Disclosures
- **Explicit Disclosures:**
  1. *Cohort Limitation:* The available $N=7$ curated evaluation cohort limits statistical generalizability. Results are engineering/evaluation observations and should not be interpreted as clinical validation.
  2. *Calibration Limitation:* Clinical calibration could not be established on the small dataset; the `insufficient_data` safeguard is active.
  3. *Prototype Scope:* The system is an assistive research prototype and does not autonomously dispense medication.
  4. *Storage Constraints:* Prototype storage and access-control limitations are documented; production-grade private cloud storage and institutional RBAC are not implemented.
- **Speaker Notes (45 sec):**
  > *"We explicitly disclose several research limitations: our evaluation is based on a small curated cohort of seven prescriptions, which limits statistical generalizability. Furthermore, clinical calibration could not be validated on this small sample, which is why our insufficient_data safeguard is engaged. These findings are engineering observations and not clinical population claims."*

---

### Slide 18: Conclusion & Key Contributions
- **Summary of Contributions:**
  1. Multi-tiered, explainable architecture for handwritten prescription understanding.
  2. Pluggable multimodal adapter architecture with deterministic clinical status parsing.
  3. Formulary grounding against CDSCO and RxNorm with strict dosage preservation.
  4. ISMP Tall Man LASA collision screening.
  5. Uncertainty-aware selective abstention policy with sample-size safeguards.
  6. Multilingual posology generation in English, Hindi, and Marathi with speech preview.
- **Speaker Notes (45 sec):**
  > *"In conclusion, DawaAI demonstrates an explainable, multi-tiered approach to handwritten prescription processing as an assistive research prototype. By combining multimodal extraction, domain formulary grounding, selective abstention, and human-in-the-loop verification, the project demonstrates how AI systems can be designed with safety and transparency. Thank you, and I look forward to your questions."*

---

## Part 2: Anticipated Examiner Questions & Defense Answers

### Q1: Why didn't you rely on an end-to-end commercial LLM for the entire task?
**Defense Answer:**
> *"While general multimodal LLMs offer strong visual reasoning, relying on them unconstrained in clinical document interpretation introduces significant vulnerabilities:
> 1. **Hallucination under Ambiguity:** When an ungrounded model encounters an unreadable ink smear, language-model priors risk predicting a plausible drug name rather than admitting unreadability.
> 2. **Uncalibrated Confidence:** Commercial API endpoints typically do not expose calibrated token-level probabilities or empirical calibration guarantees.
> 3. **Lack of Domain Grounding & Safety Invariants:** An end-to-end model can silently alter a dosage string to match common patterns. DawaAI enforces a strict dosage preservation invariant, grounds candidates against CDSCO/RxNorm compendia, and applies an uncertainty-aware selective abstention policy."*

### Q2: How does the selective abstention policy balance clinician workload against safety?
**Defense Answer:**
> *"The selective abstention policy is formulated under Chow's optimal error-reject framework. In our Phase 12 evaluation, varying the policy threshold $\tau$ from 0.60 to 0.90 demonstrated the expected trade-off: at the configured default $\tau = 0.80$, 90% of cases in the evaluated cohort were abstained, and the accepted subset achieved 100% observed selective accuracy. On the 7 curated demo samples, 6/7 cases were accepted with 100% observed selective accuracy. This demonstrates how the policy isolates ambiguous tokens for review, although threshold selection in clinical practice would need to be tuned on large institutional cohorts."*

### Q3: How do you justify evaluating on an $N=7$ dataset?
**Defense Answer:**
> *"The $N=7$ cohort is an engineering development and continuous integration cohort. It was designed to provide deterministic pipeline integration, cryptographic hash traceability, and verification across specific edge cases (such as cursive ligatures, low-contrast pencil, and ink bleed-through). We explicitly disclose that $N=7$ is insufficient for statistical generalization or clinical validation claims, which is why our Phase 8 calibration layer enforces an insufficient_data safeguard for sample sizes under 15."*

### Q4: Explain the confidence calibration methodology and why clinical calibration is not claimed.
**Defense Answer:**
> *"In Phase 8, we implemented Platt scaling, Isotonic regression, and temperature scaling alongside empirical calibration metrics (ECE, MCE, and Brier score). However, reliable empirical calibration requires substantial sample sizes. Per Section 20 of PLAN.md, whenever $N < 15$—as is the case with our 7-sample cohort—the system enforces calibration_status = 'insufficient_data' and leaves calibrated_confidence as null. Our documented ECE reduction from 0.2380 to 0.1500 was achieved on synthetic verification scenarios and is explicitly labeled as algorithmic method verification, not clinical calibration evidence."*

### Q5: How does DawaAI address Section 42 of the Indian Pharmacy Act?
**Defense Answer:**
> *"Section 42 of the Pharmacy Act (1948) mandates that only a Registered Pharmacist may compound or dispense prescription medicines. DawaAI incorporates this regulatory requirement into its core architecture:
> 1. The software is classified strictly as an assistive research prototype and does not autonomously dispense medication.
> 2. Workspace views prominently display assistive disclaimers stating that the physical signed prescription is the sole legal document.
> 3. Dedicated verification endpoints allow clinicians to confirm, correct, or mark fields as unreadable.
> 4. All verification actions are logged in an immutable audit trail."*

### Q6: How does the system handle medications not found in the CDSCO database?
**Defense Answer:**
> *"When an extracted entity cannot be reconciled against the CDSCO or RxNorm compendia, the Phase 7 RAG validation layer flags the candidate as an unconfirmed formulation. The entity is marked with an unverified warning, and the system avoids generating automated posology statements for ungrounded entities, routing the candidate to human clinician verification."*

### Q7: How are bounding boxes preserved through image preprocessing?
**Defense Answer:**
> *"In Phase 4, when deskewing is applied based on the detected Radon transform angle $\theta$, the affine transformation matrix is tracked. Extracted bounding box coordinates are mapped back to the original image coordinate plane using normalized coordinates $[x, y, w, h]$ between 0.0 and 1.0, ensuring responsive SVG vector overlays regardless of display resolution."*

### Q8: What does the multilingual posology evaluation show?
**Defense Answer:**
> *"In Phase 12, the multilingual posology component was evaluated across 19 posology statements in English, Hindi, and Marathi. Automated checks confirmed 100% Roman drug name preservation, 84.2% numerical and unit fidelity, and 0% unsupported claims across all three languages. We explicitly note that human qualitative evaluation was not performed, so these results represent automated factual-fidelity checks."*

### Q9: What is the dosage preservation invariant?
**Defense Answer:**
> *"The dosage preservation invariant is a core safety rule enforced in Phase 7: the system strictly preserves the observed dosage string extracted from the physical prescription image. Even if an external formulary lists a standard strength, the system is prohibited from automatically mutating the observed dosage, ensuring that potential prescribing errors are preserved for clinician review rather than silently masked."*

### Q10: What are your key engineering quality metrics?
**Defense Answer:**
> *"The project adheres to high engineering standards across all 14 phases. The backend features 552 passing pytest tests covering unit components, RAG validation, calibration safeguards, and abstention policies. The frontend features 123 automated test assertions across all 14 required UI states, zero TypeScript compilation errors under strict mode, and clean production bundle builds."*
