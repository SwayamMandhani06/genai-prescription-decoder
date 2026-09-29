"""
EXP-06: Selective Abstention Evaluator (Section 21, 22, 23).
Evaluates Phase 9 uncertainty-aware selective abstention and human verification routing.
Computes abstention precision, recall, F1, coverage, selective accuracy, and threshold sweeps.
Generates eval/tables/05_abstention.csv.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.abstention.policy import evaluate_field_abstention
from ai.abstention.config import AbstentionPolicyConfig, get_default_abstention_config
from backend.app.multimodal.schemas import ExtractedField
from ai.confidence.schemas import FieldConfidenceAssessment, RawConfidenceSignal, CalibratedConfidence
from ai.rag.schemas import MedicineValidationResult, RetrievalCandidate, ValidationDecisionProvenance
from ai.rag.sources import get_source_provenance, CDSCO_SOURCE_ID
from backend.app.fixtures.abstention_fixtures import list_abstention_fixtures


class AbstentionEvaluator:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = root_dir

    def _eval_single(self, f: Dict[str, Any], cfg: AbstentionPolicyConfig):
        f_in = f.get("input_field", {})
        c_in = f.get("confidence_metadata", {})
        v_in = f.get("validation_evidence", {})
        l_in = f.get("lasa_metadata")

        ef = ExtractedField(
            value=f_in.get("value"),
            status=f_in.get("status", "confident"),
            presence=f_in.get("presence", "present"),
            extraction_state=f_in.get("extraction_state", "extracted"),
            confidence=f_in.get("confidence", 0.95),
            candidates=f_in.get("candidates", []),
            uncertainty_reason=f_in.get("uncertainty_reason")
        )

        conf = None
        if c_in:
            conf = FieldConfidenceAssessment(
                field_name=f_in.get("field_name", "medicine_name"),
                observed_value=f_in.get("value"),
                raw_signal=RawConfidenceSignal(
                    source="multimodal",
                    raw_value=c_in.get("raw_value"),
                    signal_type="model_score"
                ),
                calibrated=CalibratedConfidence(
                    value=c_in.get("calibrated_value"),
                    calibration_status=c_in.get("calibration_status", "calibrated"),
                    calibration_method=c_in.get("calibration_method")
                ),
                status=f_in.get("status", "confident")
            )

        val_res = None
        if v_in:
            prov = get_source_provenance(CDSCO_SOURCE_ID)
            ref = RetrievalCandidate(
                reference_id="ref-eval",
                source=CDSCO_SOURCE_ID,
                medicine_name=v_in.get("matched_name", "Test Med"),
                match_method="exact_normalized_name",
                score=v_in.get("score", 1.0),
                rank=1,
                evidence="eval grounding",
                provenance=prov
            ) if v_in.get("found_in_db") else None

            val_res = MedicineValidationResult(
                input_candidate=f_in.get("value", ""),
                normalized_candidate=(f_in.get("value") or "").lower(),
                validation_status=v_in.get("validation_status", "not_validated"),
                medicine_identity_status=v_in.get("validation_status", "not_validated"),
                selected_reference=ref,
                evidence="eval evidence",
                requires_human_review=(v_in.get("validation_status") != "validated"),
                formulation_consistency=v_in.get("formulation_consistency", "consistent"),
                provenance=ValidationDecisionProvenance(
                    retrieval_method="exact",
                    query_raw="eval",
                    query_normalized="eval",
                    normalization_version="1",
                    index_version="1",
                    config_hash="eval-hash",
                    matched_count=1,
                    timestamp="2026-09-28T00:00:00Z",
                    validation_rule="rule",
                    source_authorities=[CDSCO_SOURCE_ID]
                )
            )

        return evaluate_field_abstention(
            field_name=f_in.get("field_name", "medicine_name"),
            extracted_field=ef,
            confidence_assessment=conf,
            validation_result=val_res,
            config=cfg,
            lasa_result=l_in
        )

    def evaluate(self, candidate_thresholds: Optional[List[float]] = None) -> Dict[str, Any]:
        if candidate_thresholds is None:
            candidate_thresholds = [0.60, 0.70, 0.80, 0.90]

        all_fixtures = list_abstention_fixtures()
        # Focus quantitative field-level selective accuracy on field evaluation scenarios (Scenarios 1-10)
        fixtures = [f for f in all_fixtures if "input_field" in f and "expected_decision" in f]
        total_fixtures = len(fixtures)

        # Baseline evaluation with default frozen config (threshold = 0.80)
        default_config = get_default_abstention_config()
        
        tp = 0  # correctly abstained unsafe/ambiguous case
        fp = 0  # falsely abstained clean confident case
        fn = 0  # falsely accepted unsafe/ambiguous case
        tn = 0  # correctly accepted clean confident case

        accepted_count = 0
        correct_accepted = 0
        abstained_count = 0
        truly_unsafe_in_abstained = 0

        per_fixture_records: List[Dict[str, Any]] = []

        for f in fixtures:
            fix_id = f.get("fixture_id")
            expected_dec = f.get("expected_decision", {}).get("decision")

            eval_res = self._eval_single(f, default_config)

            actual_dec = eval_res.decision
            is_abstained = actual_dec == "abstained"
            should_abstain = expected_dec == "abstained"

            if is_abstained and should_abstain:
                tp += 1
                abstained_count += 1
                truly_unsafe_in_abstained += 1
            elif is_abstained and not should_abstain:
                fp += 1
                abstained_count += 1
            elif not is_abstained and should_abstain:
                fn += 1
                accepted_count += 1
            else:
                tn += 1
                accepted_count += 1
                correct_accepted += 1

            per_fixture_records.append({
                "fixture_id": fix_id,
                "expected": expected_dec,
                "actual": actual_dec,
                "reason_codes": eval_res.reason_codes,
                "requires_verification": eval_res.requires_human_verification
            })

        abst_prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        abst_rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        abst_f1 = (2 * abst_prec * abst_rec) / (abst_prec + abst_rec) if (abst_prec + abst_rec) > 0 else 0.0

        coverage = accepted_count / total_fixtures if total_fixtures > 0 else 0.0
        selective_accuracy = correct_accepted / accepted_count if accepted_count > 0 else 1.0
        error_rate_accepted = 1.0 - selective_accuracy
        error_rate_abstained = 1.0 - (truly_unsafe_in_abstained / abstained_count) if abstained_count > 0 else 0.0

        # Threshold analysis sweep across [0.60, 0.70, 0.80, 0.90]
        threshold_sweep = []
        for thresh in candidate_thresholds:
            cfg = AbstentionPolicyConfig(min_calibrated_confidence=thresh)
            t_accepted = 0
            t_correct_acc = 0
            for f in fixtures:
                expected_dec = f.get("expected_decision", {}).get("decision")
                e_res = self._eval_single(f, cfg)
                if e_res.decision == "accepted":
                    t_accepted += 1
                    if expected_dec == "accepted":
                        t_correct_acc += 1

            t_cov = t_accepted / total_fixtures if total_fixtures > 0 else 0.0
            t_sel_acc = t_correct_acc / t_accepted if t_accepted > 0 else 1.0
            threshold_sweep.append({
                "threshold": thresh,
                "coverage": round(t_cov, 4),
                "selective_accuracy": round(t_sel_acc, 4),
                "accepted_count": t_accepted
            })

        return {
            "experiment_id": "EXP-06",
            "name": "Selective Abstention & Review Safety Analysis",
            "total_evaluated": total_fixtures,
            "policy_version": "abstention_policy_v1",
            "default_threshold": 0.80,
            "metrics": {
                "abstention_precision": round(abst_prec, 4),
                "abstention_recall": round(abst_rec, 4),
                "abstention_f1": round(abst_f1, 4),
                "coverage": round(coverage, 4),
                "selective_accuracy": round(selective_accuracy, 4),
                "error_rate_accepted": round(error_rate_accepted, 4),
                "error_rate_abstained": round(error_rate_abstained, 4)
            },
            "threshold_sweep": threshold_sweep,
            "per_fixture": per_fixture_records
        }

    def generate_csv_table(self, output_dir: Path) -> Path:
        results = self.evaluate()
        output_dir.mkdir(parents=True, exist_ok=True)
        table_path = output_dir / "05_abstention.csv"

        headers = ["Policy / Threshold", "Coverage", "Selective Accuracy", "Error Rate (Accepted)", "Abstention F1", "Total Evaluated"]
        rows = []
        for sw in results["threshold_sweep"]:
            is_def = " (FROZEN DEFAULT)" if sw["threshold"] == results["default_threshold"] else ""
            rows.append([
                f"Confidence Threshold >= {sw['threshold']:.2f}{is_def}",
                f"{sw['coverage']:.4f}",
                f"{sw['selective_accuracy']:.4f}",
                f"{1.0 - sw['selective_accuracy']:.4f}",
                f"{results['metrics']['abstention_f1']:.4f}",
                str(results["total_evaluated"])
            ])

        with open(table_path, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")

        return table_path

