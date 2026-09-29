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
import pytest

from eval.ocr.metrics import compute_cer, compute_wer, levenshtein_dp
from eval.extraction.metrics import evaluate_field_list
from eval.data.dataset_loader import EvaluationDatasetLoader
from eval.data.leakage_detector import DataLeakageDetector
from ai.confidence.metrics import compute_calibration_bins, compute_ece, compute_mce, compute_brier_score
from eval.lasa.evaluator import LASAEvaluator
from eval.abstention.evaluator import AbstentionEvaluator
from eval.explanation.evaluator import MultilingualEvaluator


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
