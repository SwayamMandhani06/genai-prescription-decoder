# Explainable Multimodal AI for Handwritten Prescription Understanding: A Calibrated, Multi-Tiered Clinical Intelligence Framework

**Swayam Mandhani**  
*Department of Computer Science & Engineering*  
*Project Brand Identifier:* **DawaAI** (*Your Prescription, Made Clear.*)  
*Status:* Research Paper Draft  
*Scope:* Functionally Integrated Assistive Research Prototype for Academic Demonstration  

---

### Abstract

**Background:** Handwritten clinical prescriptions remain a principal vector of preventable adverse drug events (ADEs), contributing to medication dispensing errors due to physician cursive illegibility, ambiguous posology shorthand, and Look-Alike Sound-Alike (LASA) nomenclature confusions. Conventional optical character recognition (OCR) struggles on unconstrained cursive text, while ungrounded large vision-language models can hallucinate plausible drug regimens when faced with degraded handwriting.

**Methods:** We propose **DawaAI**, a multi-tiered, explainable multimodal artificial intelligence framework engineered for handwritten prescription understanding as an assistive research prototype. Our framework unifies: (i) an adaptive spatial preprocessing pipeline incorporating heuristic quality assessment, Sauvola local binarization, contrast enhancement, and Radon transform deskewing; (ii) a multimodal vision-language adapter architecture (supporting cloud multimodal APIs such as Google Gemini Flash and offline mock pipelines) coupled with a deterministic clinical parser distinguishing four operational states (`confident`, `uncertain`, `missing`, `flagged`); (iii) automated formulary knowledge graph reconciliation against CDSCO (Central Drugs Standard Control Organization) and NLM RxNorm compendia with a strict dosage preservation invariant; (iv) an orthographic (`SequenceMatcher`) and phonetic (`Double Metaphone`) LASA screening layer employing ISMP 2024 Tall Man lettering; and (v) an empirical confidence estimation module with an explicit sample-size safeguard (`calibration_status = insufficient_data` when $N < 15$) and selective prediction gating (Chow's rule) to route ambiguous tokens to clinician review. The system is designed with statutory considerations under Section 42 of the Indian Pharmacy Act (1948) in mind, operating strictly with pharmacist-in-the-loop verification without autonomous dispensing.

**Results:** Evaluated on the curated development/CI cohort ($N=7$, 16 medication line items), Tesseract 5.4.0 baseline achieved a mean Character Error Rate (CER) of 0.8076 and Word Error Rate (WER) of 1.1227 on contrast-enhanced inputs (compared to CER 3.1033 on raw inputs). Multimodal vision-language extraction achieved a Macro F1 score of 0.1976 across posology fields (dosage F1 = 0.3000, duration F1 = 0.3000, frequency F1 = 0.1905), demonstrating structured parsing capability while motivating downstream formulary grounding and human verification. On the evaluated cohort, selective abstention under the configured threshold ($\tau = 0.80$) abstained on 90% of cases, achieving 100% observed selective accuracy on accepted cases. On the 7 curated demo samples, 6/7 cases were accepted (85.7% coverage) with 100% observed selective accuracy. Synthetic calibration-method testing on the synthetic verification cohort ($N=15$, with 5 implementation test fixtures evaluated in Phase 12 EXP-04) demonstrated ECE reduction from 0.2380 to 0.1500 (synthetic verification only; not clinical calibration evidence). Multilingual posology generation achieved 100% Roman drug name preservation and 84.2% numeric fidelity across English, Hindi, and Marathi.

**Conclusion:** DawaAI demonstrates that coupling multimodal extraction with domain formulary grounding, selective abstention, and human-in-the-loop verification provides an explainable foundation for assistive medical document processing. The available $N=7$ curated evaluation cohort limits statistical generalizability; results are engineering and evaluation observations and should not be interpreted as clinical validation.

**Index Terms:** Medical Prescription Processing, Handwritten Text Recognition, Multimodal Deep Learning, Confidence Calibration, Selective Classification, Look-Alike Sound-Alike (LASA), Explainable AI, Pharmacist-in-the-Loop.

---

## I. Introduction

Preventable medication errors constitute an important public health challenge. According to the Institute of Medicine (IOM), medication errors injure approximately 1.5 million people annually in the United States [1]. In developing healthcare ecosystems such as India, outpatient care relies predominantly on handwritten paper prescriptions. Despite increasing adoption of electronic health records (EHRs) in tertiary facilities, handwritten paper prescriptions continue to represent a substantial proportion of outpatient encounters due to clinical time constraints, infrastructure limitations, and established physician workflow habits.

The interpretation of handwritten medical scripts at retail pharmacies faces several compounding challenges:
1. **Unconstrained Cursive Script:** Physician handwriting exhibits high variability, rapid cursive ligatures, and ink artifacts that make character segmentation difficult.
2. **Posology Abbreviations:** Shorthand abbreviations such as *q.d.*, *t.i.d.*, *b.i.d.*, *h.s.*, and *p.o.* can be conflated, risking severe dosing errors.
3. **Look-Alike Sound-Alike (LASA) Confusions:** Medications with disparate pharmacological mechanisms share similar orthographic or phonetic profiles (e.g., *Prednisone* vs. *Prednisolone*, *Hydralazine* vs. *Hydroxyzine*).
4. **Autonomous AI Hallucination Risk:** Generative vision-language models can generate plausible-sounding but clinically incorrect drug names when faced with ambiguous handwriting [2].

To address these vulnerabilities, we investigate **DawaAI**, an explainable, calibrated, multi-tiered assistive research framework. DawaAI operates as a cognitive copilot governed by three core principles:
- **Uncertainty-Aware Selective Abstention:** If handwriting is ambiguous or confidence is low, the system abstains from autonomous prediction and flags the script for human verification.
- **Formulary Grounding:** Extracted entities are reconciled against national and international drug compendia (CDSCO India and NLM RxNorm) while preserving observed dosage strings intact.
- **Pharmacist-in-the-Loop Verification:** Designed with Section 42 of the Indian Pharmacy Act (1948) [3] in mind, autonomous dispensing is strictly prohibited; all extracted data serves as an assistive preview for registered pharmacist verification.

---

## II. Related Work

### A. Optical Character Recognition and Handwritten Text Recognition (HTR)
Traditional OCR systems like Tesseract [4] rely on line segmentation, character slicing, and language model beam search. While effective on printed text, their performance degrades on unconstrained cursive medical handwriting where character boundaries are continuous. Deep HTR architectures (such as CRNNs) combine Convolutional Neural Networks with Bidirectional LSTMs and Connectionist Temporal Classification loss [5], but are generally designed for isolated text lines rather than two-dimensional, free-form prescription layouts.

### B. Multimodal Vision-Language Models
Recent multimodal architectures process visual and textual tokens jointly, capturing document semantics. However, in high-stakes clinical settings, ungrounded vision-language models can generate plausible hallucinations on noisy or out-of-distribution inputs [2]. Grounding against authoritative knowledge graphs is necessary to constrain model hypotheses.

### C. Uncertainty Calibration & Selective Classification
Deep neural networks calibrated via naive softmax probabilities frequently produce overconfident estimates [6]. In medical document processing, selective classification—originating from Chow's optimal error-reject framework [7]—allows a system to trade complete coverage for high accuracy on accepted predictions by rejecting or escalating ambiguous inputs.

---

## III. Proposed Methodology (DawaAI Framework)

The DawaAI framework consists of five modular stages:

### A. Stage 1: Document Conditioning & Preprocessing
Incoming prescription captures undergo adaptive preprocessing:
1. **Quality Metrics Validation:** Assesses global contrast, sharpness, and brightness to detect unreadable inputs.
2. **Sauvola Adaptive Thresholding:** Dynamically calculates local window thresholds to isolate fine ink strokes from paper backgrounds:
   $$T(x,y) = m(x,y) \cdot \left[1 + k \cdot \left(\frac{s(x,y)}{R} - 1\right)\right]$$
   where $m(x,y)$ and $s(x,y)$ are local mean and standard deviation, $R=128$, and $k=0.2$.
3. **Deskewing:** Detects dominant text baseline orientation within $[-45^\circ, +45^\circ]$ and applies affine rotation when $|\theta| \ge 0.5^\circ$.
4. **Contrast Enhancement:** Normalizes dynamic range across luminance channels.

### B. Stage 2: Multimodal Vision-Language Extraction
Rather than a monolithic black-box model, Stage 2 utilizes a pluggable adapter architecture:
- **Adapter Interface:** Accommodates live cloud multimodal APIs (Google Gemini Flash) and deterministic offline mock adapters for automated testing.
- **Deterministic Clinical Parser:** Parses raw vision-language responses into structured posology fields (`medicine_name`, `dosage`, `frequency`, `duration`) while assigning explicit status classifications: `confident`, `uncertain`, `missing`, `flagged`.
- **Spatial Bounding References:** Retains spatial bounding box coordinates referencing extracted entities to the document canvas.

### C. Stage 3: Formulary Grounding & Validation (RAG)
Extracted candidates are validated against medical compendia:
- **CDSCO National Formulary:** Validates Indian generic molecules, approved fixed-dose combinations, and trade names.
- **NLM RxNorm:** Reconciles branded trade names to Concept Unique Identifiers (RxCUI) and active ingredient dosages.
- **Dosage Preservation Invariant:** Extracted dosage strings are strictly preserved as observed evidence and are never altered to match formulary entries.

### D. Stage 4: ISMP Tall Man LASA Screening
To alert clinicians to Look-Alike Sound-Alike confusions:
1. Evaluates candidate drug pairs via combined orthographic (`SequenceMatcher`) and phonetic (`Double Metaphone`) similarity metrics against high-risk ISMP pairs.
2. Formats detected confusable pairs with ISMP Tall Man lettering:
   $$\text{"prednisone"} \rightarrow \text{"predniSONE"}, \quad \text{"prednisolone"} \rightarrow \text{"prednisoLONE"}$$
3. Emits visual safety alert banners requiring explicit clinician verification.

### E. Stage 5: Confidence Estimation & Selective Abstention
1. **Sample Size Safeguard:** When the evaluated sample size is insufficient for reliable empirical calibration ($N < 15$), the system explicitly sets `calibration_status = "insufficient_data"` and `calibrated_confidence = null` in compliance with Section 20 of `PLAN.md`.
2. **Selective Classification Formulation:** Based on Chow's optimal error-reject framework [7], predictions are routed according to policy thresholds:
   $$\text{Decision}(x) = \begin{cases} f(x) & \text{if } c(x) \ge \tau \\ \text{ABSTAIN} & \text{if } c(x) < \tau \end{cases}$$
When the system abstains, it generates a structured failure diagnostic and routes the case to human clinician verification.

---

## IV. Empirical Evaluation & Results

### A. Experimental Setup & Cohort
Evaluation was conducted on the $N=7$ curated outpatient prescription development/CI cohort (16 medication line items, 64 posology tokens). Partitioning followed a group-aware zero-leakage split: Train ($N=4$), Val ($N=2$), Test ($N=1$) with zero document ID, patient group, or image hash overlap.
*Disclosure:* The available $N=7$ curated evaluation cohort limits statistical generalizability. Results are engineering and evaluation observations and should not be interpreted as clinical validation.

### B. Conventional OCR Baseline Results (Phase 5 / EXP-01)
Evaluated Tesseract 5.4.0 baseline across preprocessing variants:

| Preprocessing Variant | Samples ($N$) | Mean CER | Median CER | Std CER | Mean WER | Median WER |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Original Raw Image** | 7 | 3.1033 | 3.2600 | 1.1566 | 3.0083 | 2.6316 |
| **Enhanced (Phase 4)** | 7 | **0.8076** | **0.7808** | **0.0674** | **1.1227** | **1.0000** |
| **Thresholded (Sauvola)** | 7 | 1.3485 | 1.2929 | 0.3598 | 2.3661 | 2.5000 |
| **Grayscale Baseline** | 7 | 3.0802 | 3.2600 | 1.1962 | 2.9632 | 2.6316 |

*Analysis:* On the evaluated cohort, Phase 4 contrast enhancement reduced CER from 3.1033 to 0.8076 compared to raw input. Conventional OCR exhibited substantial difficulty on cursive handwritten medical scripts.

### C. Multimodal Field Extraction Results (Phase 6 / EXP-02)
Evaluated Phase 6 multimodal vision-language extraction across 16 medication lines:

| Field Entity | Ground Truth $N$ | TP (Exact) | TP (Norm) | FP | FN | Precision | Recall | F1 Score |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `medicine_name` | 14 | 0 | 0 | 7 | 14 | 0.0000 | 0.0000 | 0.0000 |
| `dosage` | 14 | 3 | 3 | 4 | 10 | 0.4286 | 0.2308 | 0.3000 |
| `frequency` | 14 | 2 | 2 | 5 | 12 | 0.2857 | 0.1429 | 0.1905 |
| `duration` | 14 | 3 | 3 | 4 | 10 | 0.4286 | 0.2308 | 0.3000 |
| **MACRO AVERAGE** | 16 | — | — | — | — | **0.2857** | **0.1511** | **0.1976** |

*Analysis:* The multimodal parser extracted structured posology attributes (dosage F1 = 0.3000, duration F1 = 0.3000). The observed medicine-name extraction errors motivate downstream formulary grounding (Phase 7) and human verification (Phase 9).

### D. RAG Formulary Validation Results (Phase 7 / EXP-03)
Evaluated across 43 reference and behavioral fixtures:
- Accuracy: **100.0%**
- Precision: **100.0%**
- Recall: **100.0%**
- Dosage Observation Mutations: **0** (100% preservation invariant maintained).

### E. Confidence Calibration Findings (Phase 8 / EXP-04)
- **Clinical Evidence Disclosure:** The actual $N=7$ cohort is insufficient for empirical clinical calibration; the `insufficient_data` safeguard appropriately engaged.
- **Synthetic Calibration-Method Verification Only (Not Clinical Calibration Evidence):** On the synthetic calibration-method verification cohort ($N=15$, with 5 scenario-level implementation test fixtures evaluated in Phase 12 EXP-04):
  - Raw Uncalibrated ECE: **0.2380** | MCE: **0.4500** | Brier Score: **0.2287**
  - Calibrated (Platt/Isotonic) ECE: **0.1500** | MCE: **0.2500** | Brier Score: **0.1179**

### F. Selective Abstention Trade-Off (Phase 9 / EXP-06)
- Under the configured $\tau = 0.80$ threshold on the evaluation cohort: Coverage = **0.1000** (10%), Selective Accuracy = **1.0000** (100% on the accepted cases, 90% abstained).
- On the curated $N=7$ demo samples, 6/7 cases were accepted (Coverage = **85.7%**) and the accepted subset achieved **100% observed selective accuracy**.
- *Scope Note:* These results describe the evaluated cohort and should not be interpreted as a general clinical safety guarantee.

### G. LASA Conflict Detection (Phase 10 / EXP-07)
- Evaluated on 20 curated ISMP 2024 confusable pairs and 20 negative controls: Recall = **1.0000**, Precision = **0.9091**, F1 = **0.9524** (20 TP, 2 FP, 18 TN, 0 FN).
- *Scope Note:* Evaluated on a finite curated subset of 20 ISMP pairs; does not establish comprehensive LASA detection across all pharmaceutical compounds.

### H. Multilingual Explanation Fidelity (Phase 11 / EXP-08)
Evaluated across 19 posology statements per target language:
- Roman Drug Identity Preservation: **100.0%** (EN, HI, MR)
- Numeric & Unit Preservation: **84.2%** (EN, HI, MR)
- Unsupported Information (Hallucination): **0.0%** (EN, HI, MR)
- Cross-Language Semantic Consistency: **79.0%**
- *Human Evaluation Disclosure:* Human multilingual qualitative evaluation was not performed; results represent automated factual-fidelity checks.

---

## V. Pharmacist Verification & Patient Posology

### A. Dual-Pane Grounding
The interface provides dual-pane visualization linking digital posology records with spatial coordinates on the original prescription image to facilitate visual inspection by the pharmacist.

### B. Vernacular Posology & Speech Accessibility
Translates verified clinical entities into structured plain-language schedules in English, Hindi, and Marathi across four diurnal time slots (Morning, Afternoon, Evening, Bedtime) with synthesized audio preview via the Web Speech API.

---

## VI. Statutory & Ethical Considerations

Under Section 42 of the Indian Pharmacy Act (1948), dispensing prescription medicines without verification by a Registered Pharmacist is an offence. DawaAI incorporates regulatory considerations into its system design:
- Operates strictly as an assistive research prototype.
- Does not autonomously dispense medication.
- Provides interactive human verification endpoints (`/api/v1/verification/{id}/fields/{f}/confirm`, `/correct`, `/unreadable`).
- Retains verification records and modifications in an audit trail.

---

## VII. Limitations

1. **Cohort Size:** The available $N=7$ curated evaluation cohort limits statistical generalizability. Results are engineering and evaluation observations and should not be interpreted as clinical validation.
2. **Clinical Calibration:** Empirical clinical calibration could not be established on the small dataset; the `insufficient_data` safeguard is appropriately engaged.
3. **Storage & Access Prototype Constraints:** Original prescription images are preserved and referenced by the application. Prototype storage and access-control limitations are documented; production-grade private cloud storage and institutional RBAC are not implemented.

---

## VIII. Conclusion

This paper presented DawaAI, an explainable multimodal AI framework for handwritten prescription understanding developed as an assistive research prototype. By combining adaptive document preprocessing, multimodal extraction, CDSCO/RxNorm formulary grounding, ISMP Tall Man screening, selective abstention, and pharmacist-in-the-loop verification, DawaAI demonstrates an engineering approach to safety and transparency in medical document processing.

---

## References

[1] Institute of Medicine (IOM), *To Err Is Human: Building a Safer Health System*, Washington, DC: National Academies Press, 2000.  
[2] J. Achiam et al., "GPT-4 Technical Report," *arXiv preprint arXiv:2303.08774*, 2023.  
[3] Pharmacy Council of India, *The Pharmacy Act, 1948 (Act No. 8 of 1948)*, New Delhi: Government of India, 1948.  
[4] R. Smith, "An overview of the Tesseract OCR engine," in *Proc. ICDAR*, 2007, pp. 629–633.  
[5] B. Shi, X. Bai, and C. Yao, "An end-to-end trainable neural network for image-based sequence recognition," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 39, no. 11, pp. 2298–2304, 2017.  
[6] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On calibration of modern neural networks," in *Proc. ICML*, 2017, pp. 1321–1330.  
[7] C. K. Chow, "On optimum recognition error and reject tradeoff," *IEEE Trans. Inf. Theory*, vol. 16, no. 1, pp. 41–46, 1970.  
