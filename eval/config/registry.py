"""
Experiment Registry (Section 8).
Defines metadata, hypotheses, inputs, configurations, metrics, and limitations for EXP-01 to EXP-09.
"""

from typing import Any, Dict, List

EXPERIMENT_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "EXP-01",
        "name": "Conventional OCR Baseline Evaluation",
        "hypothesis": "Conventional Tesseract OCR fails on unconstrained cursive medical handwriting with high CER and WER (>50%), but contrast enhancement and Sauvola adaptive binarization yield measurable relative error reductions.",
        "inputs": "Raw and preprocessed prescription sample images (N=7; 5 variants: original, grayscale, enhanced, thresholded, deskewed)",
        "configuration": "ocr_tesseract_baseline_v1 (Tesseract 5.4.0, PSM 6, OEM 1, language: eng)",
        "dataset": "AURA-Rx Curated Calibration Set (data/samples/, N=7)",
        "metrics": ["mean_cer", "median_cer", "mean_wer", "median_wer", "character_accuracy", "word_accuracy"],
        "output": "eval/tables/01_ocr_baseline.csv",
        "limitations": "Evaluated on the N=7 calibration set; serves as a functional baseline, not a broad epidemiological study."
    },
    {
        "id": "EXP-02",
        "name": "Multimodal Vision-Language Field Extraction",
        "hypothesis": "Multimodal Vision-Language architecture extracts clinical entities (medicine name, dosage, frequency, duration) with higher precision and recall than conventional OCR, while explicitly isolating ambiguous cursive tokens as UNCERTAIN.",
        "inputs": "Prescription images with gold-standard token-level posology annotations",
        "configuration": "multimodal_extraction_v1 (gemini-3.8-flash adapter and offline deterministic benchmark adapter)",
        "dataset": "data/annotations/sample_annotations.json (N=7 prescriptions, 16 distinct medication lines)",
        "metrics": ["precision", "recall", "f1", "macro_f1", "micro_f1", "missing_rate", "uncertain_rate", "exact_match_rate"],
        "output": "eval/tables/02_extraction_metrics.csv",
        "limitations": "Covers outpatient prescription patterns in development sample set."
    },
    {
        "id": "EXP-03",
        "name": "RAG-Based Medicine Formulation Validation",
        "hypothesis": "Retrieval-Augmented Grounding against CDSCO Approved Formulations and US NLM RxNorm nomenclature achieves >90% precision on true drug names while preserving visually observed dosages without silent mutation.",
        "inputs": "Extracted candidate drug strings paired with visual dosage observations",
        "configuration": "rag_validation_v1 (hierarchical retriever: exact, brand, alias, ingredient, controlled lexical threshold 0.75)",
        "dataset": "Curated CDSCO (20 records) and RxNorm (10 records) authoritative subset (30 reference formulations)",
        "metrics": ["validation_accuracy", "validation_precision", "validation_recall", "unresolved_rate", "dosage_preservation_rate", "formulation_mismatch_rate"],
        "output": "eval/tables/03_rag_validation.csv",
        "limitations": "Evaluated on finite 30-record reference subset fixture; does not represent all marketed Indian drugs."
    },
    {
        "id": "EXP-04",
        "name": "Confidence Estimation & Empirical Calibration",
        "hypothesis": "Raw model confidence exhibits overconfidence on ambiguous cursive strokes, whereas calibrated probabilities allow empirical error quantification. When calibration data is below minimum threshold (N < 15), the system safely abstains via 'insufficient_data'.",
        "inputs": "Raw multimodal confidence signals paired with empirical correctness labels",
        "configuration": "confidence_calibration_v1 (Platt scaling, Isotonic regression, temperature scaling; min_samples = 15)",
        "dataset": "Calibration cohort (N=7 development samples; 14 deterministic calibration benchmark fixtures)",
        "metrics": ["expected_calibration_error", "maximum_calibration_error", "brier_score", "negative_log_likelihood", "reliability_bins"],
        "output": "eval/tables/04_calibration.csv",
        "limitations": "Sample size (N=7) is below the 15-sample threshold for fitting robust calibration parameters; reported results reflect safe fallback and controlled fixture benchmarks."
    },
    {
        "id": "EXP-05",
        "name": "Complete Pipeline End-to-End Evaluation",
        "hypothesis": "The unified 11-stage multimodal pipeline executes end-to-end without clinical state corruption, preserving the original handwritten image at every stage while enforcing downstream safety invariants.",
        "inputs": "Raw scanned outpatient prescription images",
        "configuration": "full_multimodal_pipeline_v1 (Phases 1 through 11 fully integrated)",
        "dataset": "AURA-Rx Calibration & Integration Sample Set (N=7)",
        "metrics": ["pipeline_completion_rate", "field_extraction_rate", "safety_alert_rate", "abstention_rate", "end_to_end_latency_ms"],
        "output": "eval/reports/per_sample_results.jsonl",
        "limitations": "Evaluates end-to-end integration across development fixtures."
    },
    {
        "id": "EXP-06",
        "name": "Selective Abstention & Review Safety Analysis",
        "hypothesis": "Uncertainty-aware selective abstention selectively halts autonomous interpretation on degraded handwriting and decimal ambiguities (1.0 vs 10 mg), achieving high selective accuracy on accepted cases while maintaining appropriate human verification routing.",
        "inputs": "Structured prescription fields with confidence and validation evidence",
        "configuration": "abstention_policy_v1 (min_calibrated_confidence = 0.80, strict dosage mode enabled)",
        "dataset": "15 deterministic Phase 9 abstention fixtures + 7 sample prescriptions",
        "metrics": ["abstention_precision", "abstention_recall", "abstention_f1", "coverage", "selective_accuracy", "error_rate_accepted", "error_rate_abstained"],
        "output": "eval/tables/05_abstention.csv",
        "limitations": "Threshold sweeps conducted on calibration fixtures; not tuned against final test labels."
    },
    {
        "id": "EXP-07",
        "name": "Look-Alike / Sound-Alike (LASA) Conflict Detection",
        "hypothesis": "Dual-dimensional orthographic SequenceMatcher and Double Metaphone phonetic similarity screening identifies confusable drug names with high recall on high-risk pairs while avoiding false-positive self-collisions.",
        "inputs": "Drug candidate pairs and baseline non-confusable formulations",
        "configuration": "lasa_detection_v1 (orthographic_weight = 0.50, phonetic_weight = 0.50, threshold = 0.70, ISMP 2024 Tall Man lexicon)",
        "dataset": "15 deterministic Phase 10 benchmark fixtures + 20 curated ISMP high-frequency confusion pairs",
        "metrics": ["lasa_precision", "lasa_recall", "lasa_f1", "true_positives", "false_positives", "false_negatives", "true_negatives"],
        "output": "eval/tables/06_lasa.csv",
        "limitations": "Evaluates documented ISMP pairs; does not claim universal coverage of all world pharmacopeias."
    },
    {
        "id": "EXP-08",
        "name": "Multilingual Explanation & Factual Fidelity",
        "hypothesis": "Deterministic parameterized posology templates in English, Hindi, and Marathi preserve exact Roman-script drug identities and numerical dosages without factual drift or unsupported clinical claims.",
        "inputs": "Canonical structured prescription posology facts",
        "configuration": "explanation_policy_v1 / explanation_template_v1 / explanation_terminology_v1",
        "dataset": "22 deterministic Phase 11 explanation fixtures across English, Hindi, and Marathi",
        "metrics": ["medicine_name_preservation_rate", "numeric_preservation_rate", "dosage_preservation_rate", "frequency_preservation_rate", "duration_preservation_rate", "unsupported_fact_rate", "cross_language_consistency_rate"],
        "output": "eval/tables/07_multilingual.csv",
        "limitations": "Evaluates factual and numerical preservation; subjective clinical elegance is not scored by automated scripts."
    },
    {
        "id": "EXP-09",
        "name": "Component Ablation Study",
        "hypothesis": "Progressive ablation from (A) OCR baseline -> (B) Multimodal -> (C) +RAG -> (D) +Confidence/Abstention -> (E) Complete System demonstrates clear, quantifiable trade-offs: multimodal improves extraction F1, RAG ensures formulary grounding, abstention trades raw coverage for high selective accuracy, and LASA/Explanation completes patient safety.",
        "inputs": "Uniform held-out test evaluation samples",
        "configuration": "Configurations A through E evaluated under identical input conditions",
        "dataset": "AURA-Rx Evaluation Set (N=7 prescriptions, 16 medication entities, 64 field tokens)",
        "metrics": ["extraction_f1", "validation_accuracy", "cer", "wer", "coverage", "selective_accuracy", "unsupported_info_rate"],
        "output": "eval/tables/08_ablation.csv",
        "limitations": "Ablation is evaluated under deterministic conditions; empirical variance is bounded by sample size."
    }
]

def get_experiment(exp_id: str) -> Dict[str, Any]:
    for exp in EXPERIMENT_REGISTRY:
        if exp["id"] == exp_id:
            return exp
    raise ValueError(f"Unknown experiment ID: {exp_id}")
