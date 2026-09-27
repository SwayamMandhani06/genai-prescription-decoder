"""
Service Coordinator for Phase 8: Confidence Estimation & Calibration.
Adheres strictly to Sections 1, 4, 5, 10, 11, 16, 17, and 19 of PLAN.md:
- Evaluates field-level confidence and multi-medicine independence
- Preserves raw signals vs calibrated confidence
- Enforces sample-size validity: flags 'insufficient_data' when statistical power is lacking
- Preserves visual vs reference conflicts
- Never implements Phase 9 abstention logic
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from backend.app.multimodal.schemas import (
    PrescriptionExtractionResult,
    ExtractedMedicine,
    ExtractedField,
)
from ai.rag.schemas import MedicineValidationResult
from .schemas import (
    RawConfidenceSignal,
    CalibratedConfidence,
    FieldConfidenceAssessment,
    MedicineIdentityConfidence,
    DosageConfidenceAssessment,
    MedicineConfidenceAssessment,
    PrescriptionConfidenceAssessment,
    CalibrationMetrics,
    CalibrationComparison,
    CalibrationStatus,
    CalibrationMethod,
)
from .config import ConfidenceConfig, get_confidence_config
from .calibrator import (
    BaseCalibrator,
    PlattScalingCalibrator,
    IsotonicCalibrator,
    CalibrationFactory,
    InsufficientDataError,
)
from .metrics import evaluate_calibration_metrics
from .signals import (
    extract_field_confidence_signal,
    extract_dosage_confidence_signal,
    extract_medicine_identity_confidence,
    detect_confidence_conflicts,
)


class ConfidenceEstimationService:
    """
    Central service for computing, calibrating, and auditing prescription confidence.
    """

    def __init__(self, config: Optional[ConfidenceConfig] = None):
        self.config = config or get_confidence_config()
        self.active_calibrator: Optional[BaseCalibrator] = None
        self.calibration_status: CalibrationStatus = "insufficient_data"
        self.calibration_model_id: Optional[str] = None
        self.active_method: Optional[CalibrationMethod] = None
        self.config_hash: str = self.config.compute_hash()

    def set_active_calibrator(self, calibrator: BaseCalibrator) -> None:
        """Sets an explicitly fitted calibration model."""
        self.active_calibrator = calibrator
        self.active_method = calibrator.method_name
        self.calibration_model_id = calibrator.model_id
        if calibrator.is_fitted:
            self.calibration_status = "calibrated"
        else:
            self.calibration_status = "insufficient_data"

    def fit_calibrator(
        self,
        scores: List[float],
        labels: List[int],
        method: CalibrationMethod = "platt_scaling",
        model_id: Optional[str] = None,
    ) -> BaseCalibrator:
        """
        Attempts to fit a calibration model on provided scores and ground truth outcomes.
        If sample count is below the minimum threshold, safely flags 'insufficient_data'
        without fabricating overfitted parameters.
        """
        calibrator = CalibrationFactory.create(
            method=method,
            model_id=model_id or f"cal_{method}_v1",
            min_samples=self.config.min_samples_for_calibration,
        )
        try:
            calibrator.fit(scores, labels)
            self.set_active_calibrator(calibrator)
        except InsufficientDataError:
            self.active_calibrator = calibrator
            self.calibration_status = "insufficient_data"
            self.active_method = method
            self.calibration_model_id = calibrator.model_id

        return calibrator

    def evaluate_field_confidence(
        self,
        field: ExtractedField,
        field_name: str,
        model_version: str = "gemini-3.8-flash",
    ) -> FieldConfidenceAssessment:
        """Evaluates confidence for an individual posology field."""
        raw_sig = extract_field_confidence_signal(
            field=field,
            field_name=field_name,
            model_version=model_version,
            config_version=self.config.config_version,
        )

        calibrated_conf = CalibratedConfidence(
            value=None,
            calibration_method=self.active_method,
            calibration_version=self.active_calibrator.version if self.active_calibrator else None,
            calibration_dataset_version=self.config.calibration_dataset_version,
            calibration_status=self.calibration_status,
        )

        if self.active_calibrator and self.active_calibrator.is_fitted and raw_sig.raw_value is not None:
            calibrated_conf = self.active_calibrator.calibrate(
                raw_sig.raw_value,
                dataset_version=self.config.calibration_dataset_version,
            )

        # Conflict description
        conflict = False
        conflict_desc = None
        if field.status == "uncertain" and raw_sig.raw_value and raw_sig.raw_value > 0.70:
            conflict = True
            conflict_desc = "High raw model confidence contradicts uncertain visual stroke flag."

        return FieldConfidenceAssessment(
            field_name=field_name,
            observed_value=field.value,
            raw_signal=raw_sig,
            calibrated=calibrated_conf,
            status=field.status,
            visual_evidence_supported=(field.presence == "present" and field.extraction_state != "missing"),
            reference_supported=None,
            conflict_detected=conflict,
            conflict_description=conflict_desc,
        )

    def evaluate_medicine_confidence(
        self,
        med: ExtractedMedicine,
        validation_res: Optional[MedicineValidationResult],
        model_version: str = "gemini-3.8-flash",
    ) -> MedicineConfidenceAssessment:
        """
        Evaluates confidence for a single prescribed medicine line item completely
        independently of any other medicines on the prescription pad.
        """
        med_name_conf = self.evaluate_field_confidence(
            med.medicine_name,
            field_name="medicine_name",
            model_version=model_version,
        )
        freq_conf = self.evaluate_field_confidence(
            med.frequency,
            field_name="frequency",
            model_version=model_version,
        )
        dur_conf = self.evaluate_field_confidence(
            med.duration,
            field_name="duration",
            model_version=model_version,
        )
        dosage_conf = extract_dosage_confidence_signal(
            med.dosage,
            validation_res=validation_res,
            model_version=model_version,
            config_version=self.config.config_version,
        )

        # Calibrate dosage if calibrator is active
        if self.active_calibrator and self.active_calibrator.is_fitted and dosage_conf.visual_extraction_confidence.raw_value is not None:
            dosage_conf.calibrated = self.active_calibrator.calibrate(
                dosage_conf.visual_extraction_confidence.raw_value,
                dataset_version=self.config.calibration_dataset_version,
            )
        else:
            dosage_conf.calibrated.calibration_status = self.calibration_status

        med_id_conf = extract_medicine_identity_confidence(
            med.medicine_name,
            validation_res=validation_res,
            model_version=model_version,
            config_version=self.config.config_version,
            conflict_delta_threshold=self.config.conflict_delta_threshold,
        )

        conflict_flags = detect_confidence_conflicts(med, validation_res)

        # Compute line-item raw composite score
        valid_raw_scores = [
            conf.raw_signal.raw_value
            for conf in (med_name_conf, freq_conf, dur_conf)
            if conf.raw_signal.raw_value is not None
        ]
        if dosage_conf.visual_extraction_confidence.raw_value is not None:
            valid_raw_scores.append(dosage_conf.visual_extraction_confidence.raw_value)

        overall_raw = sum(valid_raw_scores) / len(valid_raw_scores) if valid_raw_scores else 0.50
        overall_raw = round(overall_raw, 4)

        overall_cal = None
        if self.active_calibrator and self.active_calibrator.is_fitted:
            overall_cal = round(self.active_calibrator.predict_one(overall_raw), 4)

        return MedicineConfidenceAssessment(
            item_index=1,  # updated by caller if multi-med
            medicine_name=med_name_conf,
            dosage=dosage_conf,
            frequency=freq_conf,
            duration=dur_conf,
            abbreviations=med.abbreviations,
            medicine_identity_confidence=med_id_conf,
            overall_raw_confidence=overall_raw,
            overall_calibrated_confidence=overall_cal,
            calibration_status=self.calibration_status,
            conflict_flags=conflict_flags,
        )

    def evaluate_prescription_confidence(
        self,
        extraction_result: PrescriptionExtractionResult,
        validation_results: Optional[List[MedicineValidationResult]] = None,
    ) -> PrescriptionConfidenceAssessment:
        """
        Evaluates document-level and multi-medicine confidence for a prescription extraction.
        Maintains independent evaluations for each prescribed line item.
        """
        model_version = extraction_result.model.model_id
        medicines_assessment: List[MedicineConfidenceAssessment] = []

        val_map: Dict[str, MedicineValidationResult] = {}
        if validation_results:
            for vr in validation_results:
                val_map[vr.input_candidate.strip().lower()] = vr

        for idx, med in enumerate(extraction_result.medicines, start=1):
            med_key = (med.medicine_name.value or "").strip().lower()
            matching_val = val_map.get(med_key)
            # Fallback to index matching if candidate key mismatch
            if matching_val is None and validation_results and idx <= len(validation_results):
                matching_val = validation_results[idx - 1]

            med_assessment = self.evaluate_medicine_confidence(
                med=med,
                validation_res=matching_val,
                model_version=model_version,
            )
            med_assessment.item_index = idx
            medicines_assessment.append(med_assessment)

        # Primary field dictionary matching Section 6 contract keys
        fields_assessment: Dict[str, FieldConfidenceAssessment] = {}
        for f_name, f_obj in extraction_result.fields.items():
            fields_assessment[f_name] = self.evaluate_field_confidence(
                field=f_obj,
                field_name=f_name,
                model_version=model_version,
            )

        # Overall raw score: conservative aggregate across medicines
        if medicines_assessment:
            overall_raw = sum(m.overall_raw_confidence for m in medicines_assessment) / len(medicines_assessment)
        elif fields_assessment:
            raw_vals = [
                f.raw_signal.raw_value for f in fields_assessment.values()
                if f.raw_signal.raw_value is not None
            ]
            overall_raw = sum(raw_vals) / len(raw_vals) if raw_vals else 0.50
        else:
            overall_raw = 0.50

        overall_raw = round(overall_raw, 4)

        overall_cal = None
        if self.active_calibrator and self.active_calibrator.is_fitted:
            overall_cal = round(self.active_calibrator.predict_one(overall_raw), 4)

        return PrescriptionConfidenceAssessment(
            prescription_id=extraction_result.prescription_id,
            medicines=medicines_assessment,
            fields=fields_assessment,
            overall_raw_score=overall_raw,
            overall_calibrated_confidence=overall_cal,
            calibration_status=self.calibration_status,
            calibration_model_id=self.calibration_model_id,
            calibration_method=self.active_method,
            config_hash=self.config_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def evaluate_metrics(
        self,
        scores: List[float],
        labels: List[int],
        num_bins: Optional[int] = None,
        dataset_type: str = "empirical_evaluation",
        clinical_evidence: bool = False,
    ) -> CalibrationMetrics:
        """Computes empirical calibration metrics."""
        bins_count = num_bins or self.config.num_calibration_bins
        return evaluate_calibration_metrics(
            scores,
            labels,
            num_bins=bins_count,
            dataset_type=dataset_type,
            clinical_evidence=clinical_evidence,
        )


# Global Singleton Service instance
_GLOBAL_CONFIDENCE_SERVICE = ConfidenceEstimationService()


def get_confidence_service() -> ConfidenceEstimationService:
    """Returns the singleton active confidence estimation service."""
    return _GLOBAL_CONFIDENCE_SERVICE
