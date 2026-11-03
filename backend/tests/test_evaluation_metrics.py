"""
Phase 12 Research Evaluation Suite Tests.
Verifies:
1. CER and WER Levenshtein edge cases and metrics correctness
2. Field-level precision, recall, and F1 calculations
3. Split leakage detection invariants
4. Confidence calibration binning, ECE, MCE, and Brier calculations
5. Selective abstention coverage and selective accuracy metrics
6. LASA confusion matrix and metric calculations
7. Multilingual fidelity validation invariants
8. Artifact existence and publication schema conformance
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import pytest

from eval.ocr.metrics import compute_cer, compute_wer, levenshtein_dp
from eval.extraction.metrics import evaluate_field_list
from eval.data.dataset_loader import EvaluationDatasetLoader
from eval.data.leakage_detector import DataLeakageDetector
from ai.confidence.metrics import compute_calibration_bins, compute_ece, compute_mce, compute_brier_score
from eval.lasa.evaluator import LASAEvaluator
from eval.abstention.evaluator import AbstentionEvaluator
from eval.explanation.evaluator import MultilingualEvaluator
from backend.app.dataset.schema import AmbiguityLevel, PrescriptionDocumentRecord


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestOCRMetrics:
    def test_cer_wer_exact_match(self):
        ref = "Augmentin 625 Duo"
        hyp = "Augmentin 625 Duo"
        cer_res = compute_cer(ref, hyp)
        wer_res = compute_wer(ref, hyp)
        assert cer_res["cer"] == 0.0
        assert wer_res["wer"] == 0.0
        assert cer_res["insertions"] == 0
        assert cer_res["deletions"] == 0
        assert cer_res["substitutions"] == 0

    def test_cer_wer_empty_hypothesis(self):
        ref = "Paracetamol 500mg"
        hyp = ""
        cer_res = compute_cer(ref, hyp)
        wer_res = compute_wer(ref, hyp)
        assert cer_res["cer"] == 1.0
        assert wer_res["wer"] == 1.0
        assert cer_res["deletions"] == len(ref)

    def test_cer_wer_empty_both(self):
        cer_res = compute_cer("", "")
        wer_res = compute_wer("", "")
        assert cer_res["cer"] == 0.0
        assert wer_res["wer"] == 0.0

    def test_cer_wer_substitutions_and_insertions(self):
        ref = "abc"
        hyp = "axc"
        # 1 substitution (b -> x)
        cer_res = compute_cer(ref, hyp)
        assert cer_res["substitutions"] == 1
        assert cer_res["deletions"] == 0
        assert cer_res["insertions"] == 0
        assert pytest.approx(cer_res["cer"], 0.01) == 1.0 / 3.0

    def test_levenshtein_distance(self):
        d, sub, dele, ins = levenshtein_dp("kitten", "sitting")
        # kitten -> sitten (sub) -> sittin (sub) -> sitting (ins) = 3 edits
        assert d == 3
        assert ins == 1
        assert sub == 2
        assert dele == 0


class TestExtractionMetrics:
    def test_precision_recall_f1_clean(self):
        gt = [
            {"name": "Paracetamol", "dosage": "500 mg"},
            {"name": "Amoxicillin", "dosage": "250 mg"},
        ]
        pred = [
            {"name": "Paracetamol", "dosage": "500 mg"},
            {"name": "Amoxicillin", "dosage": "250 mg"},
        ]
        res = evaluate_field_list(predictions=pred, ground_truths=gt, field_key="name", gt_key="name")
        assert res["precision"] == 1.0
        assert res["recall"] == 1.0
        assert res["f1"] == 1.0
        assert res["exact_match_rate"] == 1.0

    def test_precision_recall_f1_with_errors(self):
        gt = [
            {"name": "Augmentin 625 Duo"},
            {"name": "Pantoprazole 40mg"},
        ]
        pred = [
            {"name": "Augmentin 625 Duo"},
            {"name": "Metformin 500mg"},  # False positive / incorrect substitution
        ]
        res = evaluate_field_list(predictions=pred, ground_truths=gt, field_key="name", gt_key="name")
        assert res["tp_exact"] == 1
        assert res["fp"] == 1
        assert res["fn"] == 1
        assert res["precision"] == 0.5
        assert res["recall"] == 0.5
        assert res["f1"] == 0.5


class TestDataLeakageDetector:
    def test_split_leakage_audit_passes(self):
        loader = EvaluationDatasetLoader(REPO_ROOT)
        detector = DataLeakageDetector(loader)
        report = detector.audit_splits()
        assert report.passed is True
        assert len(report.doc_id_overlap) == 0
        assert len(report.group_id_overlap) == 0
        assert len(report.image_hash_overlap) == 0


class TestConfidenceCalibrationMetrics:
    def test_calibration_bins_and_ece(self):
        # 10 predictions: 5 with conf 0.9 (all correct), 5 with conf 0.1 (all incorrect)
        confs = [0.9] * 5 + [0.1] * 5
        labels = [1] * 5 + [0] * 5
        bins = compute_calibration_bins(confs, labels, num_bins=5)
        ece = compute_ece(confs, labels, num_bins=5)
        brier = compute_brier_score(confs, labels)

        assert len(bins) == 5
        # Bin 0 ([0.0, 0.2)): count=5, mean_conf=0.1, acc=0.0 -> gap=0.1
        # Bin 4 ([0.8, 1.0]): count=5, mean_conf=0.9, acc=1.0 -> gap=0.1
        assert ece == pytest.approx(0.10, abs=0.01)
        # Brier = (5*(0.9-1)^2 + 5*(0.1-0)^2)/10 = (5*0.01 + 5*0.01)/10 = 0.01
        assert brier == pytest.approx(0.01, abs=0.001)

    def test_mce_calculation(self):
        confs = [0.8, 0.2]
        labels = [0, 0]  # First is wrong (conf 0.8, acc 0.0, gap 0.8), second is right (conf 0.2, acc 0.0, gap 0.2)
        mce = compute_mce(confs, labels, num_bins=5)
        assert mce >= 0.7


class TestSelectiveAbstentionEvaluator:
    def test_abstention_evaluation_executes(self):
        evaluator = AbstentionEvaluator(REPO_ROOT)
        res = evaluator.evaluate()
        assert res["experiment_id"] == "EXP-06"
        assert "metrics" in res
        assert 0.0 <= res["metrics"]["coverage"] <= 1.0
        assert 0.0 <= res["metrics"]["selective_accuracy"] <= 1.0
        assert len(res["threshold_sweep"]) == 4

    def test_abstention_csv_generation(self, tmp_path):
        evaluator = AbstentionEvaluator(REPO_ROOT)
        p = evaluator.generate_csv_table(tmp_path)
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "FROZEN DEFAULT" in content


class TestLASAEvaluator:
    def test_lasa_evaluation_executes(self):
        evaluator = LASAEvaluator(REPO_ROOT)
        res = evaluator.evaluate()
        assert res["experiment_id"] == "EXP-07"
        assert res["confusion_matrix"]["tp"] == 20
        assert res["confusion_matrix"]["fp"] == 2
        assert res["confusion_matrix"]["tn"] == 18
        assert res["confusion_matrix"]["fn"] == 0
        assert res["metrics"]["recall"] == 1.0
        assert res["metrics"]["precision"] >= 0.90

    def test_lasa_csv_generation(self, tmp_path):
        evaluator = LASAEvaluator(REPO_ROOT)
        p = evaluator.generate_csv_table(tmp_path)
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "ISMP 2024" in content


class TestMultilingualEvaluator:
    def test_multilingual_evaluation_executes(self):
        evaluator = MultilingualEvaluator(REPO_ROOT)
        res = evaluator.evaluate()
        assert res["experiment_id"] == "EXP-08"
        assert res["cross_language_consistency"]["consistency_rate"] >= 0.75
        en_metrics = res["per_language_metrics"]["en"]
        assert en_metrics["medicine_name_preservation_rate"] == 1.0
        assert en_metrics["unsupported_fact_rate"] == 0.0


class TestEvaluationArtifactsConformance:
    def test_publication_tables_exist_and_non_empty(self):
        tables_dir = REPO_ROOT / "eval" / "tables"
        expected_tables = [
            "01_ocr_baseline.csv",
            "02_extraction_metrics.csv",
            "03_rag_validation.csv",
            "04_calibration.csv",
            "05_abstention.csv",
            "06_lasa.csv",
            "07_multilingual.csv",
            "08_ablation.csv",
        ]
        for t in expected_tables:
            f = tables_dir / t
            assert f.exists(), f"Missing publication table: {t}"
            assert f.stat().st_size > 50, f"Table file {t} is unexpectedly small or empty"

    def test_publication_plots_exist(self):
        plots_dir = REPO_ROOT / "eval" / "plots"
        expected_plots = [
            "01_ocr_cer_wer_comparison.png",
            "02_extraction_prf1.png",
            "03_calibration_reliability.png",
            "04_abstention_tradeoff.png",
            "05_lasa_confusion_matrix.png",
            "06_ablation_comparison.png",
        ]
        for p in expected_plots:
            f = plots_dir / p
            assert f.exists(), f"Missing plot: {p}"
            assert f.stat().st_size > 1000, f"Plot file {p} is too small"

    def test_evaluation_reports_exist(self):
        reports_dir = REPO_ROOT / "eval" / "reports"
        agg_json = reports_dir / "aggregate_results.json"
        agg_csv = reports_dir / "aggregate_results.csv"
        tax_json = reports_dir / "error_taxonomy.json"
        per_sample = reports_dir / "per_sample_results.jsonl"
        report_md = reports_dir / "phase-12-evaluation-report.md"

        assert agg_json.exists() and agg_json.stat().st_size > 100
        assert agg_csv.exists() and agg_csv.stat().st_size > 100
        assert tax_json.exists() and tax_json.stat().st_size > 100
        assert per_sample.exists() and per_sample.stat().st_size > 100
        assert report_md.exists() and report_md.stat().st_size > 1000

        with open(agg_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["evaluation_id"] == "aura_rx_eval_v1"
        assert "experiments" in data

        with open(tax_json, "r", encoding="utf-8") as f:
            tax = json.load(f)
        assert len(tax["categories"]) >= 14

    def test_evaluation_manifest_conformance(self):
        manifest_file = REPO_ROOT / "eval" / "config" / "evaluation_manifest.json"
        assert manifest_file.exists()
        with open(manifest_file, "r", encoding="utf-8") as f:
            man = json.load(f)
        assert man["evaluation_id"] == "aura_rx_eval_v1"
        assert man["random_seed"] == 42
        assert "annotations_sha256" in man["dataset_metadata"]
        assert "splits_sha256" in man["dataset_metadata"]


class TestBenchmark11MetricsMath:
    """
    Tests exact mathematical correctness for all 11 benchmark metrics on synthetic edge cases:
    1. Perfect match across all fields (including canonical frequency 1-0-1 == BD)
    2. Partial field mismatches (strength mismatch, frequency mismatch)
    3. Hallucinated / fabricated fields and extra medications
    4. Correct abstention on severely illegible prescription
    5. Missed abstention with hallucinated prediction on illegible prescription
    6. Field completeness / recall on missing fields
    7. Latency p50/p95 percentiles and error/timeout rate
    """

    def _create_synthetic_record(
        self,
        doc_id: str = "DOC-SYN-001",
        med_name: str = "Augmentin",
        strength: Optional[str] = "625 mg",
        freq: Optional[str] = "1-0-1",
        dur: Optional[str] = "5 days",
        route: Optional[str] = "Oral",
        instructions: Optional[str] = "After food",
        ambiguity: AmbiguityLevel = AmbiguityLevel.NONE,
    ) -> PrescriptionDocumentRecord:
        from backend.app.dataset.schema import (
            PrescriptionDocumentRecord,
            GroundTruthAnnotation,
            MedicationEntityAnnotation,
            AnnotationTier,
        )
        meds = []
        if med_name:
            meds.append(MedicationEntityAnnotation(
                item_index=1,
                raw_text=f"{med_name} {strength or ''} {freq or ''}",
                medicine_name=med_name,
                dosage_strength=strength,
                frequency=freq,
                duration=dur,
                route=route,
                instructions=instructions,
                ambiguity_level=ambiguity,
            ))
        return PrescriptionDocumentRecord(
            document_id=doc_id,
            patient_group_id=f"GRP-{doc_id}",
            ground_truth=GroundTruthAnnotation(
                tier=AnnotationTier.GROUND_TRUTH,
                document_id=doc_id,
                image_rel_path="samples/test.png",
                image_sha256="0" * 64,
                patient_deidentified=True,
                source_dataset_id="test",
                medications=meds,
            )
        )

    def test_all_11_metrics_perfect_match(self):
        from backend.app.dataset.evaluator import EvaluationItem, compute_evaluation_metrics

        rec1 = self._create_synthetic_record("DOC-1", "Augmentin", "625 mg", "1-0-1", "5 days", "Oral", "After food")
        rec2 = self._create_synthetic_record("DOC-2", "Paracetamol", "500 mg", "SOS", "3 days", "Oral", "For fever")

        pred1 = {
            "status": "success",
            "medicines": [{
                "medicine_name": "Augmentin",
                "dosage_strength": "625 mg",
                "dosage": "625 mg",
                "frequency": "BD",  # Canonical match: 1-0-1 == BD!
                "duration": "5 days",
                "route": "Oral",
                "instructions": "After food",
            }]
        }
        pred2 = {
            "status": "success",
            "medicines": [{
                "medicine_name": "Paracetamol",
                "dosage_strength": "500 mg",
                "dosage": "500 mg",
                "frequency": "SOS",
                "duration": "3 days",
                "route": "Oral",
                "instructions": "For fever",
            }]
        }

        items = [
            EvaluationItem(record=rec1, prediction=pred1, latency_ms=120.0),
            EvaluationItem(record=rec2, prediction=pred2, latency_ms=180.0),
        ]

        metrics, details = compute_evaluation_metrics(items)

        assert metrics.exact_medicine_name_accuracy == 1.0
        assert metrics.strength_accuracy == 1.0
        assert metrics.dosage_accuracy == 1.0
        assert metrics.route_accuracy == 1.0
        assert metrics.frequency_accuracy == 1.0  # 1-0-1 matched to BD
        assert metrics.duration_accuracy == 1.0
        assert metrics.field_completeness == 1.0
        assert metrics.unsupported_fabricated_rate == 0.0
        assert metrics.appropriate_abstention_rate == 1.0
        assert metrics.prescription_level_exact_match == 1.0
        assert metrics.error_rate == 0.0
        assert metrics.latency_p50_ms == 150.0
        assert len(details) == 2
        assert all(d.is_exact_match for d in details)

    def test_partial_match_and_mismatched_frequency(self):
        from backend.app.dataset.evaluator import EvaluationItem, compute_evaluation_metrics

        rec = self._create_synthetic_record("DOC-PARTIAL", "Augmentin", "625 mg", "1-0-1", "5 days", "Oral")

        # Wrong strength (500mg != 625mg) and wrong frequency (TDS != BD)
        pred = {
            "status": "success",
            "medicines": [{
                "medicine_name": "Augmentin",
                "dosage_strength": "500 mg",
                "dosage": "500 mg",
                "frequency": "TDS",
                "duration": "5 days",
                "route": "Oral",
            }]
        }

        items = [EvaluationItem(record=rec, prediction=pred, latency_ms=100.0)]
        metrics, _ = compute_evaluation_metrics(items)

        assert metrics.exact_medicine_name_accuracy == 1.0
        assert metrics.strength_accuracy == 0.0
        assert metrics.dosage_accuracy == 0.0
        assert metrics.frequency_accuracy == 0.0
        assert metrics.duration_accuracy == 1.0
        assert metrics.route_accuracy == 1.0
        assert metrics.prescription_level_exact_match == 0.0

    def test_hallucinated_fields_and_extra_medication(self):
        from backend.app.dataset.evaluator import EvaluationItem, compute_evaluation_metrics

        # GT has 1 med with NO duration and NO instructions
        rec = self._create_synthetic_record("DOC-FAB", "Metformin", "500 mg", "OD", None, "Oral", None)

        # Pred has 2 meds (1 extra) and hallucinates duration on the first med
        pred = {
            "status": "success",
            "medicines": [
                {
                    "medicine_name": "Metformin",
                    "dosage_strength": "500 mg",
                    "frequency": "OD",
                    "duration": "30 days",  # Fabricated duration (GT is None)
                    "route": "Oral",
                },
                {
                    "medicine_name": "Glimepiride",  # Fabricated extra medication
                    "dosage_strength": "2 mg",
                    "frequency": "OD",
                    "duration": "30 days",
                    "route": "Oral",
                }
            ]
        }

        items = [EvaluationItem(record=rec, prediction=pred, latency_ms=150.0)]
        metrics, _ = compute_evaluation_metrics(items)

        assert metrics.unsupported_fabricated_rate > 0.0
        assert metrics.fabricated_count >= 1
        assert metrics.prescription_level_exact_match == 0.0

    def test_correct_abstention_on_illegible_prescription(self):
        from backend.app.dataset.evaluator import EvaluationItem, compute_evaluation_metrics
        from backend.app.dataset.schema import AmbiguityLevel

        # Severely illegible stroke collapse
        rec = self._create_synthetic_record(
            "DOC-ILLEGIBLE",
            "IllegibleStroke",
            None,
            None,
            None,
            None,
            None,
            ambiguity=AmbiguityLevel.SEVERE_ILLEGIBLE
        )

        # Model correctly triggers abstention
        pred = {
            "status": "abstain",
            "data": {
                "overall_status": "ABSTAINED",
                "extracted_entities": []
            },
            "medicines": []
        }

        items = [EvaluationItem(record=rec, prediction=pred, latency_ms=200.0)]
        metrics, details = compute_evaluation_metrics(items)

        assert metrics.appropriate_abstention_rate == 1.0
        assert metrics.unsupported_fabricated_rate == 0.0
        assert metrics.prescription_level_exact_match == 1.0
        assert details[0].is_abstained is True
        assert details[0].is_exact_match is True

    def test_missed_abstention_with_hallucination_on_illegible_prescription(self):
        from backend.app.dataset.evaluator import EvaluationItem, compute_evaluation_metrics
        from backend.app.dataset.schema import AmbiguityLevel

        rec = self._create_synthetic_record(
            "DOC-MISSED-ABSTAIN",
            "IllegibleStroke",
            None,
            None,
            None,
            None,
            None,
            ambiguity=AmbiguityLevel.SEVERE_ILLEGIBLE
        )

        # Model FAILED to abstain, falsely claiming certainty on hallucinated drug
        pred = {
            "status": "success",
            "data": {
                "overall_status": "VERIFIED"
            },
            "medicines": [{
                "medicine_name": "Ciprofloxacin",
                "dosage_strength": "500 mg",
                "frequency": "BD",
                "duration": "5 days",
            }]
        }

        items = [EvaluationItem(record=rec, prediction=pred, latency_ms=220.0)]
        metrics, details = compute_evaluation_metrics(items)

        assert metrics.appropriate_abstention_rate == 0.0
        assert metrics.unsupported_fabricated_rate > 0.0
        assert metrics.prescription_level_exact_match == 0.0
        assert details[0].is_abstained is False
        assert details[0].is_exact_match is False

    def test_field_completeness_recall(self):
        from backend.app.dataset.evaluator import EvaluationItem, compute_evaluation_metrics

        # GT has 5 legible fields: name, strength, route, frequency, duration (no instructions)
        rec = self._create_synthetic_record("DOC-COMPLETENESS", "Amoxicillin", "250 mg", "TDS", "7 days", "Oral", instructions=None)

        # Pred only provides medicine_name and dosage_strength (missing frequency, duration, route)
        pred = {
            "status": "success",
            "medicines": [{
                "medicine_name": "Amoxicillin",
                "dosage_strength": "250 mg",
                "dosage": "250 mg",
                "frequency": None,
                "duration": None,
                "route": None,
            }]
        }

        items = [EvaluationItem(record=rec, prediction=pred, latency_ms=100.0)]
        metrics, _ = compute_evaluation_metrics(items)

        # 5 legible fields in GT, only 2 extracted -> 2/5 = 0.40
        assert metrics.field_completeness == pytest.approx(0.40, abs=0.01)

    def test_latency_statistics_and_error_handling(self):
        from backend.app.dataset.evaluator import EvaluationItem, compute_evaluation_metrics

        rec = self._create_synthetic_record("DOC-LAT", "Paracetamol", "500 mg", "SOS", "3 days", "Oral")
        pred = {
            "status": "success",
            "medicines": [{
                "medicine_name": "Paracetamol",
                "dosage_strength": "500 mg",
                "frequency": "SOS",
                "duration": "3 days",
                "route": "Oral",
            }]
        }

        items = [
            EvaluationItem(record=rec, prediction=pred, latency_ms=100.0),
            EvaluationItem(record=rec, prediction=pred, latency_ms=200.0),
            EvaluationItem(record=rec, prediction=pred, latency_ms=300.0),
            EvaluationItem(record=rec, prediction=pred, latency_ms=400.0),
            EvaluationItem(record=rec, prediction=None, is_error=True, error_message="Timeout after 10s"),
        ]

        metrics, details = compute_evaluation_metrics(items)

        assert metrics.total_prescriptions == 5
        assert metrics.error_count == 1
        assert metrics.error_rate == pytest.approx(0.20, abs=0.01)
        # Median of [100.0, 200.0, 300.0, 400.0] is (200 + 300) / 2 = 250.0 ms
        assert metrics.latency_p50_ms == 250.0
        assert metrics.latency_mean_ms == 250.0
        assert details[4].is_error is True
