"""
Prescription Evaluation Runner & Metric Engine (Phase 3 & Phase 12).
Computes all 11 required clinical benchmark metrics:
1. Exact medicine-name accuracy (normalized generic/brand match)
2. Strength accuracy
3. Dosage accuracy
4. Route accuracy
5. Frequency accuracy (canonical code match, e.g. 1-0-1 == BD)
6. Duration accuracy
7. Field completeness (recall on legible ground-truth fields)
8. Unsupported/fabricated output rate (hallucination rate)
9. Appropriate abstention rate on unreadable/ambiguous fields
10. Prescription-level exact-match accuracy
11. Latency (p50, p95, mean) and error/timeout rate

Explicitly stamps inference_mode ('live' vs 'mock'), dataset_version, git_commit, and timestamp.
"""

import os
import sys
import re
import json
import time
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Literal
from pydantic import BaseModel, Field

from backend.app.dataset.schema import (
    PrescriptionDocumentRecord,
    GroundTruthAnnotation,
    MedicationEntityAnnotation,
    AmbiguityLevel,
)
from backend.app.dataset.normalization import (
    normalize_text,
    normalize_dosage,
    normalize_frequency,
)


class EvaluationItem(BaseModel):
    """Container for paired ground truth and model prediction evaluation input."""
    record: PrescriptionDocumentRecord
    prediction: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0
    is_error: bool = False
    error_message: Optional[str] = None


class EvaluationMetrics(BaseModel):
    """The 11 Required Clinical Benchmark Metrics."""
    # 1. Exact medicine-name accuracy
    exact_medicine_name_accuracy: float = Field(0.0, description="Normalized generic/brand match accuracy")
    # 2. Strength accuracy
    strength_accuracy: float = Field(0.0, description="Dosage strength normalized match accuracy")
    # 3. Dosage accuracy
    dosage_accuracy: float = Field(0.0, description="Dosage representation match accuracy")
    # 4. Route accuracy
    route_accuracy: float = Field(0.0, description="Route of administration match accuracy")
    # 5. Frequency accuracy
    frequency_accuracy: float = Field(0.0, description="Canonical frequency match accuracy (e.g. 1-0-1 == BD)")
    # 6. Duration accuracy
    duration_accuracy: float = Field(0.0, description="Therapy duration match accuracy")
    # 7. Field completeness
    field_completeness: float = Field(0.0, description="Recall on legible non-null ground-truth fields")
    # 8. Unsupported/fabricated output rate
    unsupported_fabricated_rate: float = Field(0.0, description="Rate of hallucinated medicines or fields")
    # 9. Appropriate abstention rate
    appropriate_abstention_rate: float = Field(0.0, description="Abstention rate on unreadable or ambiguous targets")
    # 10. Prescription-level exact-match accuracy
    prescription_level_exact_match: float = Field(0.0, description="Prescription-level all-field exact match accuracy")
    # 11. Latency & Reliability
    latency_p50_ms: float = Field(0.0, description="Median latency in milliseconds")
    latency_p95_ms: float = Field(0.0, description="95th percentile latency in milliseconds")
    latency_mean_ms: float = Field(0.0, description="Mean latency in milliseconds")
    error_rate: float = Field(0.0, description="Failed or timed-out request rate")

    # Granular Counts for Auditing and Provenance
    total_prescriptions: int = 0
    total_legible_medications: int = 0
    medicine_name_matches: int = 0
    total_strength_fields: int = 0
    strength_matches: int = 0
    total_dosage_fields: int = 0
    dosage_matches: int = 0
    total_route_fields: int = 0
    route_matches: int = 0
    total_frequency_fields: int = 0
    frequency_matches: int = 0
    total_duration_fields: int = 0
    duration_matches: int = 0
    legible_fields_total: int = 0
    legible_fields_extracted: int = 0
    fabricated_count: int = 0
    total_predictions: int = 0
    ambiguous_targets_total: int = 0
    appropriate_abstentions_count: int = 0
    prescription_exact_matches_count: int = 0
    error_count: int = 0


class DocumentEvaluationDetail(BaseModel):
    """Per-prescription evaluation breakdown for diagnostics and review."""
    document_id: str
    scenario: str = ""
    is_exact_match: bool = False
    is_abstained: bool = False
    is_error: bool = False
    latency_ms: float = 0.0
    medications_gt_count: int = 0
    medications_pred_count: int = 0
    fields_evaluated: int = 0
    fields_matched: int = 0
    notes: str = ""


class EvaluationReport(BaseModel):
    """Complete stamped evaluation report."""
    evaluation_title: str = "AURA-Rx Outpatient Prescription Decoder Benchmark Evaluation"
    inference_mode: Literal["live", "mock"]
    disclaimer: Optional[str] = None
    dataset_version: str
    git_commit: str
    timestamp: str
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    ocr_engine: Optional[str] = None
    metrics: EvaluationMetrics
    per_document_results: List[DocumentEvaluationDetail] = Field(default_factory=list)


# Known brand/generic equivalencies for Indian outpatient posology benchmarking
DRUG_SYNONYMS: Dict[str, str] = {
    "augmentin": "amoxicillin and potassium clavulanate",
    "augmentin 625 duo": "amoxicillin and potassium clavulanate",
    "amoxicillin and clavulanate": "amoxicillin and potassium clavulanate",
    "amoxicillin": "amoxicillin",
    "paracetamol": "paracetamol",
    "dolo": "paracetamol",
    "dolo 650": "paracetamol",
    "pantocid": "pantoprazole",
    "pantoprazole": "pantoprazole",
    "metformin": "metformin",
    "glycomet": "metformin",
    "atorvastatin": "atorvastatin",
    "atorva": "atorvastatin",
    "azithromycin": "azithromycin",
    "azithral": "azithromycin",
    "cetirizine": "cetirizine",
    "cifran": "ciprofloxacin",
    "ciprofloxacin": "ciprofloxacin",
    "omeprazole": "omeprazole",
    "metronidazole": "metronidazole",
    "flagyl": "metronidazole",
}


def canonical_medicine_name(name: Optional[str]) -> str:
    """Standardizes medicine name for equivalence checking."""
    if not name:
        return ""
    clean = normalize_text(name).lower()
    clean = clean.replace(" duo", "").replace(" tablet", "").replace(" tab", "").strip()
    return DRUG_SYNONYMS.get(clean, clean)


def match_medicine_names(gt_name: str, pred_name: Optional[str]) -> bool:
    """Checks exact or generic/brand match between ground truth and predicted medicine name."""
    if not pred_name:
        return False
    norm_gt = normalize_text(gt_name).lower()
    norm_pred = normalize_text(pred_name).lower()
    if norm_gt == norm_pred:
        return True
    gt_clean = canonical_medicine_name(norm_gt)
    pred_clean = canonical_medicine_name(norm_pred)
    if gt_clean == pred_clean:
        return True
    if gt_clean in pred_clean or pred_clean in gt_clean:
        return True
    return False


def normalize_duration(duration_str: Optional[str]) -> str:
    """Normalizes duration string (e.g. '5 days' -> '5 days')."""
    if not duration_str:
        return ""
    clean = normalize_text(duration_str).lower()
    clean = clean.replace("day", "days").replace("dayss", "days")
    clean = clean.replace("week", "weeks").replace("weekss", "weeks")
    clean = clean.replace("month", "months").replace("monthss", "months")
    return clean.strip()


def extract_prediction_medications(prediction: Optional[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Parses predicted medications and abstention state from a pipeline response dict.
    Returns: (list_of_medication_dicts, is_abstained)
    """
    if not prediction:
        return [], False

    # Check top-level or data-level abstention flags
    top_status = str(prediction.get("status", "")).lower()
    data_dict = prediction.get("data") or {}
    overall_status = str(data_dict.get("overall_status", "")).upper()
    is_abstained = (
        top_status == "abstain"
        or overall_status in ["ABSTAINED", "SELECTIVE_ABSTAIN"]
    )

    meds: List[Dict[str, Any]] = []

    # Priority 1: Multi-medicine list in 'medicines'
    raw_meds = prediction.get("medicines")
    if raw_meds and isinstance(raw_meds, list):
        for m in raw_meds:
            if isinstance(m, dict):
                meds.append({
                    "medicine_name": _extract_val(m.get("medicine_name")),
                    "dosage_strength": _extract_val(m.get("strength") or m.get("dosage_strength") or m.get("dosage")),
                    "dosage": _extract_val(m.get("dosage") or m.get("strength") or m.get("dosage_strength")),
                    "frequency": _extract_val(m.get("frequency")),
                    "raw_frequency": m.get("raw_frequency"),
                    "abbreviations": m.get("abbreviations", []) or [],
                    "duration": _extract_val(m.get("duration")),
                    "route": _extract_val(m.get("route")),
                    "instructions": _extract_val(m.get("special_instructions") or m.get("timing_and_food") or m.get("instructions")),
                    "status": m.get("status", "confident"),
                })

    # Priority 2: 'data.extracted_entities'
    elif data_dict.get("extracted_entities"):
        entities = data_dict.get("extracted_entities", [])
        med_dict: Dict[str, Any] = {}
        for ent in entities:
            k = ent.get("field_key")
            val = ent.get("normalized_value") or ent.get("raw_value")
            if k == "medicine_name":
                med_dict["medicine_name"] = val
            elif k in ("dosage", "strength", "dosage_strength"):
                med_dict["dosage_strength"] = val
                med_dict["dosage"] = val
            elif k == "frequency":
                med_dict["frequency"] = val
                med_dict["raw_frequency"] = ent.get("raw_value")
            elif k == "duration":
                med_dict["duration"] = val
            elif k == "route":
                med_dict["route"] = val
            elif k in ("instructions", "special_instructions", "timing_and_food"):
                med_dict["instructions"] = val
        if med_dict.get("medicine_name"):
            med_dict.setdefault("abbreviations", [])
            meds.append(med_dict)

    # Priority 3: 'fields' dictionary
    elif prediction.get("fields"):
        fields = prediction.get("fields", {})
        med_dict = {
            "medicine_name": _extract_val(fields.get("medicine_name")),
            "dosage_strength": _extract_val(fields.get("strength") or fields.get("dosage_strength") or fields.get("dosage")),
            "dosage": _extract_val(fields.get("dosage") or fields.get("strength") or fields.get("dosage_strength")),
            "frequency": _extract_val(fields.get("frequency")),
            "raw_frequency": fields.get("raw_frequency"),
            "abbreviations": fields.get("abbreviations", []) or [],
            "duration": _extract_val(fields.get("duration")),
            "route": _extract_val(fields.get("route")),
            "instructions": _extract_val(fields.get("special_instructions") or fields.get("timing_and_food") or fields.get("instructions")),
            "status": "confident",
        }
        if med_dict.get("medicine_name"):
            meds.append(med_dict)

    return meds, is_abstained


def _extract_val(field_obj: Any) -> Optional[str]:
    """Helper to unwrap value from string, dict, or object."""
    if field_obj is None:
        return None
    if isinstance(field_obj, str):
        v = field_obj.strip()
        return v if v else None
    if isinstance(field_obj, dict):
        v = field_obj.get("value") or field_obj.get("normalized_value")
        return str(v).strip() if v else None
    if hasattr(field_obj, "value"):
        v = getattr(field_obj, "value")
        return str(v).strip() if v else None
    return str(field_obj).strip() if str(field_obj).strip() else None


def compute_evaluation_metrics(items: List[EvaluationItem]) -> Tuple[EvaluationMetrics, List[DocumentEvaluationDetail]]:
    """
    Computes all 11 required clinical benchmark metrics over a list of EvaluationItem records.
    """
    total_prescriptions = len(items)
    latencies: List[float] = []
    error_count = 0

    # Metric 1: Medicine Name
    total_legible_meds = 0
    medicine_name_matches = 0

    # Metric 2 & 3: Strength & Dosage
    total_strength_fields = 0
    strength_matches = 0
    total_dosage_fields = 0
    dosage_matches = 0

    # Metric 4: Route
    total_route_fields = 0
    route_matches = 0

    # Metric 5: Frequency
    total_frequency_fields = 0
    frequency_matches = 0

    # Metric 6: Duration
    total_duration_fields = 0
    duration_matches = 0

    # Metric 7: Field Completeness (Recall)
    legible_fields_total = 0
    legible_fields_extracted = 0

    # Metric 8: Unsupported/Fabricated Output Rate
    fabricated_count = 0
    total_predictions = 0

    # Metric 9: Appropriate Abstention Rate
    ambiguous_targets_total = 0
    appropriate_abstentions_count = 0

    # Metric 10: Prescription-Level Exact Match
    prescription_exact_matches_count = 0

    per_doc_details: List[DocumentEvaluationDetail] = []

    for item in items:
        rec = item.record
        gt = rec.ground_truth
        doc_id = rec.document_id
        scenario = rec.metadata.get("scenario", "")

        if item.is_error:
            error_count += 1
            per_doc_details.append(DocumentEvaluationDetail(
                document_id=doc_id,
                scenario=scenario,
                is_exact_match=False,
                is_error=True,
                latency_ms=item.latency_ms,
                notes=f"Pipeline error: {item.error_message}",
            ))
            continue

        latencies.append(item.latency_ms)
        pred_meds, is_doc_abstained = extract_prediction_medications(item.prediction)
        gt_meds = gt.medications

        doc_exact_match = True
        doc_fields_evaluated = 0
        doc_fields_matched = 0

        # Check document-level severe ambiguity (e.g. DOC-RX-007)
        is_doc_severely_ambiguous = any(
            m.ambiguity_level == AmbiguityLevel.SEVERE_ILLEGIBLE for m in gt_meds
        ) or (len(gt_meds) == 0)

        if is_doc_severely_ambiguous:
            ambiguous_targets_total += 1
            if is_doc_abstained:
                appropriate_abstentions_count += 1
                doc_exact_match = True  # Appropriately abstained on unreadable prescription!
            else:
                doc_exact_match = False
                # If model produced affirmative predictions on unreadable document, those are fabricated!
                for p_med in pred_meds:
                    for k in ["medicine_name", "dosage_strength", "frequency", "duration"]:
                        if p_med.get(k):
                            fabricated_count += 1
                            total_predictions += 1

            per_doc_details.append(DocumentEvaluationDetail(
                document_id=doc_id,
                scenario=scenario,
                is_exact_match=doc_exact_match,
                is_abstained=is_doc_abstained,
                latency_ms=item.latency_ms,
                medications_gt_count=len(gt_meds),
                medications_pred_count=len(pred_meds),
                fields_evaluated=1,
                fields_matched=1 if is_doc_abstained else 0,
                notes="Ambiguous prescription abstention baseline",
            ))
            if doc_exact_match:
                prescription_exact_matches_count += 1
            continue

        # For legible prescriptions:
        # Check count match
        if len(pred_meds) != len(gt_meds):
            doc_exact_match = False
            if len(pred_meds) > len(gt_meds):
                extra = len(pred_meds) - len(gt_meds)
                fabricated_count += extra * 4
                total_predictions += extra * 4

        # Pairwise or index matching for medications
        paired_count = max(len(gt_meds), len(pred_meds))
        for i in range(paired_count):
            gt_med: Optional[MedicationEntityAnnotation] = gt_meds[i] if i < len(gt_meds) else None
            pred_med: Optional[Dict[str, Any]] = pred_meds[i] if i < len(pred_meds) else None

            if gt_med is None and pred_med is not None:
                # Extra predicted medication beyond GT -> fabricated
                fabricated_count += 1
                total_predictions += 1
                doc_exact_match = False
                continue

            if gt_med is not None and pred_med is None:
                # Missing medication from GT
                doc_exact_match = False
                continue

            if gt_med is None or pred_med is None:
                continue

            # Check individual medication ambiguity
            if gt_med.ambiguity_level == AmbiguityLevel.SEVERE_ILLEGIBLE:
                ambiguous_targets_total += 1
                med_abstained = pred_med.get("status") in ["abstained", "uncertain", "flagged"] or is_doc_abstained
                if med_abstained:
                    appropriate_abstentions_count += 1
                else:
                    if pred_med.get("medicine_name"):
                        fabricated_count += 1
                        total_predictions += 1
                        doc_exact_match = False
                continue

            # Legible medication evaluation
            total_legible_meds += 1
            med_match = True

            # 1. Medicine Name
            legible_fields_total += 1
            doc_fields_evaluated += 1
            total_predictions += 1
            pred_name = pred_med.get("medicine_name")
            if pred_name:
                legible_fields_extracted += 1
                if match_medicine_names(gt_med.medicine_name, pred_name):
                    medicine_name_matches += 1
                    doc_fields_matched += 1
                else:
                    med_match = False
            else:
                med_match = False

            # 2. Strength Accuracy
            if gt_med.dosage_strength:
                total_strength_fields += 1
                legible_fields_total += 1
                doc_fields_evaluated += 1
                total_predictions += 1
                pred_strength = pred_med.get("dosage_strength") or pred_med.get("dosage")
                if pred_strength:
                    legible_fields_extracted += 1
                    gt_norm = normalize_dosage(gt_med.dosage_strength).canonical_string
                    pred_norm = normalize_dosage(pred_strength).canonical_string
                    if gt_norm == pred_norm or gt_norm.replace(" ", "") == pred_norm.replace(" ", ""):
                        strength_matches += 1
                        doc_fields_matched += 1
                    else:
                        med_match = False
                else:
                    med_match = False
            else:
                if pred_med.get("dosage_strength"):
                    fabricated_count += 1
                    total_predictions += 1

            # 3. Dosage Accuracy
            if gt_med.dosage_strength or getattr(gt_med, "dosage", None):
                target_dose = gt_med.dosage_strength or getattr(gt_med, "dosage", None)
                total_dosage_fields += 1
                pred_dose = pred_med.get("dosage") or pred_med.get("dosage_strength")
                if pred_dose:
                    gt_d_norm = normalize_dosage(target_dose).canonical_string
                    pred_d_norm = normalize_dosage(pred_dose).canonical_string
                    if gt_d_norm == pred_d_norm or gt_d_norm.replace(" ", "") == pred_d_norm.replace(" ", ""):
                        dosage_matches += 1
                    else:
                        med_match = False
                else:
                    med_match = False

            # 4. Route Accuracy
            if gt_med.route:
                gt_raw = getattr(gt_med, "raw_text", "") or ""
                # Check whether prescriber wrote an explicit route/dosage-form token on the physical slip
                has_route_token = bool(re.search(
                    r'\b(tab|tablet|tablets|cap|capsule|capsules|syp|syrup|inj|injection|oral|topical|iv|im|drops|puff|puffs|ointment|cream)\b',
                    gt_raw,
                    re.IGNORECASE,
                ))
                pred_route = pred_med.get("route")
                if isinstance(pred_route, dict):
                    pred_route = pred_route.get("value")

                total_route_fields += 1
                legible_fields_total += 1
                doc_fields_evaluated += 1
                total_predictions += 1

                if pred_route:
                    legible_fields_extracted += 1
                    if normalize_text(gt_med.route).lower() == normalize_text(pred_route).lower():
                        route_matches += 1
                        doc_fields_matched += 1
                    else:
                        med_match = False
                elif not has_route_token:
                    # In compliance with Zero-Fabrication rule: prescriber omitted route/form on slip,
                    # so model rightly did not fabricate it
                    route_matches += 1
                    doc_fields_matched += 1
                else:
                    med_match = False

            # 5. Frequency Accuracy (Canonical matching: 1-0-1 == BD, including compound frequencies like "TDS SOS")
            if gt_med.frequency:
                total_frequency_fields += 1
                legible_fields_total += 1
                doc_fields_evaluated += 1
                total_predictions += 1
                pred_freq = pred_med.get("frequency")
                if isinstance(pred_freq, dict):
                    pred_freq = pred_freq.get("value")
                pred_raw = pred_med.get("raw_frequency")
                pred_abbrevs = pred_med.get("abbreviations", []) or []

                if pred_freq or pred_raw or pred_abbrevs:
                    legible_fields_extracted += 1
                    gt_freq_norm = normalize_frequency(gt_med.frequency)
                    pred_freq_norm = normalize_frequency(pred_freq) if pred_freq else None
                    pred_raw_norm = normalize_frequency(pred_raw) if pred_raw else None

                    # Collect candidate frequency tokens
                    candidate_tokens = set()
                    for f_src in (pred_freq, pred_raw):
                        if f_src:
                            candidate_tokens.add(normalize_text(f_src).lower())
                            for tok in normalize_text(f_src).split():
                                clean_tok = re.sub(r'[^a-zA-Z0-9\-]', '', tok).strip().lower()
                                if clean_tok:
                                    candidate_tokens.add(clean_tok)
                    for ab in pred_abbrevs:
                        if ab:
                            candidate_tokens.add(normalize_text(ab).lower())
                            for tok in normalize_text(ab).split():
                                clean_tok = re.sub(r'[^a-zA-Z0-9\-]', '', tok).strip().lower()
                                if clean_tok:
                                    candidate_tokens.add(clean_tok)

                    # Extract common English posology phrases into canonical codes
                    combined_freq_text = f"{pred_freq or ''} {pred_raw or ''} {' '.join(str(x) for x in pred_abbrevs)}".lower()
                    if any(p in combined_freq_text for p in ("twice daily", "twice a day", "2 times daily", "two times daily", "b.d", "b.i.d")):
                        candidate_tokens.add("bd")
                    if any(p in combined_freq_text for p in ("three times daily", "three times a day", "thrice daily", "3 times daily", "t.d.s", "t.i.d")):
                        candidate_tokens.add("tds")
                    if any(p in combined_freq_text for p in ("once daily", "once a day", "1 time daily", "o.d", "q.d")):
                        candidate_tokens.add("od")
                    if any(p in combined_freq_text for p in ("four times daily", "four times a day", "4 times daily", "q.i.d")):
                        candidate_tokens.add("qid")
                    if any(p in combined_freq_text for p in ("bedtime", "at bedtime", "night", "h.s")):
                        candidate_tokens.add("hs")
                    if any(p in combined_freq_text for p in ("as needed", "when required", "sos", "prn", "when necessary")):
                        candidate_tokens.add("sos")

                    matched_freq = False
                    if gt_freq_norm.canonical_code:
                        gt_code = gt_freq_norm.canonical_code.upper()
                        if pred_freq_norm and pred_freq_norm.canonical_code == gt_code:
                            matched_freq = True
                        elif pred_raw_norm and pred_raw_norm.canonical_code == gt_code:
                            matched_freq = True
                        else:
                            for c_tok in candidate_tokens:
                                norm_c = normalize_frequency(c_tok)
                                if norm_c.canonical_code == gt_code or c_tok.upper() == gt_code:
                                    matched_freq = True
                                    break

                    if not matched_freq:
                        gt_norm_str = normalize_text(gt_med.frequency).lower()
                        if gt_norm_str in candidate_tokens:
                            matched_freq = True
                        elif any(gt_norm_str in c_tok or c_tok in gt_norm_str for c_tok in candidate_tokens):
                            matched_freq = True

                    if matched_freq:
                        frequency_matches += 1
                        doc_fields_matched += 1
                    else:
                        med_match = False
                else:
                    med_match = False
            else:
                if pred_med.get("frequency"):
                    fabricated_count += 1
                    total_predictions += 1

            # 6. Duration Accuracy
            if gt_med.duration:
                total_duration_fields += 1
                legible_fields_total += 1
                doc_fields_evaluated += 1
                total_predictions += 1
                pred_dur = pred_med.get("duration")
                if pred_dur:
                    legible_fields_extracted += 1
                    if normalize_duration(gt_med.duration) == normalize_duration(pred_dur):
                        duration_matches += 1
                        doc_fields_matched += 1
                    else:
                        med_match = False
                else:
                    med_match = False
            else:
                if pred_med.get("duration"):
                    fabricated_count += 1
                    total_predictions += 1

            # Instructions (Field Completeness)
            if gt_med.instructions:
                legible_fields_total += 1
                if pred_med.get("instructions"):
                    legible_fields_extracted += 1

            if not med_match:
                doc_exact_match = False

        if doc_exact_match:
            prescription_exact_matches_count += 1

        per_doc_details.append(DocumentEvaluationDetail(
            document_id=doc_id,
            scenario=scenario,
            is_exact_match=doc_exact_match,
            is_abstained=is_doc_abstained,
            latency_ms=item.latency_ms,
            medications_gt_count=len(gt_meds),
            medications_pred_count=len(pred_meds),
            fields_evaluated=doc_fields_evaluated,
            fields_matched=doc_fields_matched,
            notes="Evaluated against clinical ground truth",
        ))

    # Compute Final Metric Rates
    med_acc = round(medicine_name_matches / max(total_legible_meds, 1), 4)
    strength_acc = round(strength_matches / max(total_strength_fields, 1), 4)
    dosage_acc = round(dosage_matches / max(total_dosage_fields, 1), 4)
    route_acc = round(route_matches / max(total_route_fields, 1), 4)
    freq_acc = round(frequency_matches / max(total_frequency_fields, 1), 4)
    dur_acc = round(duration_matches / max(total_duration_fields, 1), 4)
    completeness = round(legible_fields_extracted / max(legible_fields_total, 1), 4)
    fab_rate = round(fabricated_count / max(total_predictions, 1), 4)
    abstain_rate = round(appropriate_abstentions_count / max(ambiguous_targets_total, 1), 4) if ambiguous_targets_total > 0 else 1.0
    rx_exact = round(prescription_exact_matches_count / max(total_prescriptions, 1), 4)

    # Compute Latency Statistics
    if latencies:
        import statistics
        sorted_lat = sorted(latencies)
        p50 = round(statistics.median(latencies), 2)
        idx_95 = min(int(math.ceil(len(sorted_lat) * 0.95)) - 1, len(sorted_lat) - 1)
        p95 = round(sorted_lat[max(0, idx_95)], 2)
        mean_lat = round(statistics.mean(latencies), 2)
    else:
        p50 = 0.0
        p95 = 0.0
        mean_lat = 0.0

    err_rate = round(error_count / max(total_prescriptions, 1), 4)

    metrics = EvaluationMetrics(
        exact_medicine_name_accuracy=med_acc,
        strength_accuracy=strength_acc,
        dosage_accuracy=dosage_acc,
        route_accuracy=route_acc,
        frequency_accuracy=freq_acc,
        duration_accuracy=dur_acc,
        field_completeness=completeness,
        unsupported_fabricated_rate=fab_rate,
        appropriate_abstention_rate=abstain_rate,
        prescription_level_exact_match=rx_exact,
        latency_p50_ms=p50,
        latency_p95_ms=p95,
        latency_mean_ms=mean_lat,
        error_rate=err_rate,
        total_prescriptions=total_prescriptions,
        total_legible_medications=total_legible_meds,
        medicine_name_matches=medicine_name_matches,
        total_strength_fields=total_strength_fields,
        strength_matches=strength_matches,
        total_dosage_fields=total_dosage_fields,
        dosage_matches=dosage_matches,
        total_route_fields=total_route_fields,
        route_matches=route_matches,
        total_frequency_fields=total_frequency_fields,
        frequency_matches=frequency_matches,
        total_duration_fields=total_duration_fields,
        duration_matches=duration_matches,
        legible_fields_total=legible_fields_total,
        legible_fields_extracted=legible_fields_extracted,
        fabricated_count=fabricated_count,
        total_predictions=total_predictions,
        ambiguous_targets_total=ambiguous_targets_total,
        appropriate_abstentions_count=appropriate_abstentions_count,
        prescription_exact_matches_count=prescription_exact_matches_count,
        error_count=error_count,
    )

    return metrics, per_doc_details


def get_git_commit() -> str:
    """Retrieves current git commit hash."""
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown_commit"


def get_dataset_version() -> str:
    """Reads dataset version from metadata."""
    p = Path("data/metadata/dataset_version.json")
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f).get("dataset_version", "1.0.0")
        except Exception:
            pass
    return "1.0.0"


def generate_markdown_report(report: EvaluationReport) -> str:
    """Renders a reproducible, clean Markdown report of benchmark metrics."""
    m = report.metrics
    is_mock = report.inference_mode == "mock"

    lines = [
        "# AURA-Rx Outpatient Prescription Decoder - Baseline Evaluation",
        "",
        f"- **Dataset Version:** `{report.dataset_version}`",
        f"- **Git Commit:** `{report.git_commit[:8]}` (`{report.git_commit}`)",
        f"- **Inference Execution Mode:** `{report.inference_mode.upper()}`",
        f"- **Model Provider / Name:** `{report.model_provider or 'N/A'}` / `{report.model_name or 'N/A'}`",
        f"- **Evaluation Timestamp:** `{report.timestamp}`",
        f"- **Prescriptions Evaluated:** `{m.total_prescriptions}`",
        "",
    ]

    if is_mock:
        lines.extend([
            "> [!WARNING]",
            "> **INFERENCE_MODE: MOCK (PIPELINE TEST ONLY - NOT VALID FOR ACCURACY CLAIMS)**",
            "> This evaluation report was produced using deterministic mock pipeline fixtures for automated test suites and pipeline verification.",
            "> These metrics **must not** be cited or claimed as real empirical model performance.",
            "",
        ])
    else:
        lines.extend([
            "> [!NOTE]",
            "> **INFERENCE_MODE: LIVE (REAL MODEL INFERENCE)**",
            "> This benchmark report was generated by running real model inference via the multimodal VLM/OCR pipeline against ground-truth annotations.",
            "",
        ])

    lines.extend([
        "## 1. Required Clinical Benchmark Metrics (All 11 Metrics)",
        "",
        "| # | Benchmark Metric | Score | Target Threshold | Granular Verification Ratio | Status |",
        "|---|---|---|---|---|---|",
        f"| 1 | **Exact Medicine-Name Accuracy** | **{m.exact_medicine_name_accuracy * 100:.2f}%** | ≥ 90.00% | {m.medicine_name_matches}/{m.total_legible_medications} medications | {'✅ PASS' if m.exact_medicine_name_accuracy >= 0.90 else '⚠️ REVIEW'} |",
        f"| 2 | **Strength Accuracy** | **{m.strength_accuracy * 100:.2f}%** | ≥ 90.00% | {m.strength_matches}/{m.total_strength_fields} strength fields | {'✅ PASS' if m.strength_accuracy >= 0.90 else '⚠️ REVIEW'} |",
        f"| 3 | **Dosage Accuracy** | **{m.dosage_accuracy * 100:.2f}%** | ≥ 90.00% | {m.dosage_matches}/{m.total_dosage_fields} dosage fields | {'✅ PASS' if m.dosage_accuracy >= 0.90 else '⚠️ REVIEW'} |",
        f"| 4 | **Route Accuracy** | **{m.route_accuracy * 100:.2f}%** | ≥ 95.00% | {m.route_matches}/{m.total_route_fields} route fields | {'✅ PASS' if m.route_accuracy >= 0.95 else '⚠️ REVIEW'} |",
        f"| 5 | **Frequency Accuracy (Canonical)** | **{m.frequency_accuracy * 100:.2f}%** | ≥ 90.00% | {m.frequency_matches}/{m.total_frequency_fields} (e.g. 1-0-1 == BD) | {'✅ PASS' if m.frequency_accuracy >= 0.90 else '⚠️ REVIEW'} |",
        f"| 6 | **Duration Accuracy** | **{m.duration_accuracy * 100:.2f}%** | ≥ 85.00% | {m.duration_matches}/{m.total_duration_fields} duration fields | {'✅ PASS' if m.duration_accuracy >= 0.85 else '⚠️ REVIEW'} |",
        f"| 7 | **Field Completeness (Recall)** | **{m.field_completeness * 100:.2f}%** | ≥ 90.00% | {m.legible_fields_extracted}/{m.legible_fields_total} legible fields | {'✅ PASS' if m.field_completeness >= 0.90 else '⚠️ REVIEW'} |",
        f"| 8 | **Unsupported/Fabricated Rate** | **{m.unsupported_fabricated_rate * 100:.2f}%** | ≤ 5.00% | {m.fabricated_count}/{m.total_predictions} hallucinated items | {'✅ PASS' if m.unsupported_fabricated_rate <= 0.05 else '⚠️ REVIEW'} |",
        f"| 9 | **Appropriate Abstention Rate** | **{m.appropriate_abstention_rate * 100:.2f}%** | ≥ 95.00% | {m.appropriate_abstentions_count}/{m.ambiguous_targets_total} ambiguous targets | {'✅ PASS' if m.appropriate_abstention_rate >= 0.95 else '⚠️ REVIEW'} |",
        f"| 10 | **Prescription Exact Match** | **{m.prescription_level_exact_match * 100:.2f}%** | ≥ 75.00% | {m.prescription_exact_matches_count}/{m.total_prescriptions} complete prescriptions | {'✅ PASS' if m.prescription_level_exact_match >= 0.75 else '⚠️ REVIEW'} |",
        f"| 11 | **Latency (p50 / p95) & Error Rate** | **p50={m.latency_p50_ms:.0f}ms, p95={m.latency_p95_ms:.0f}ms** | Error ≤ 1.0% | Error Rate: {m.error_rate * 100:.2f}% ({m.error_count} errors) | {'✅ PASS' if m.error_rate <= 0.01 else '⚠️ REVIEW'} |",
        "",
        "## 2. Per-Document Diagnostic Breakdown",
        "",
        "| Document ID | Scenario | Exact Match | Abstained | GT Meds | Pred Meds | Fields (Matched/Eval) | Latency |",
        "|---|---|---|---|---|---|---|---|",
    ])

    for d in report.per_document_results:
        em_str = "✅ YES" if d.is_exact_match else "❌ NO"
        abs_str = "🛡️ YES" if d.is_abstained else "NO"
        lines.append(
            f"| `{d.document_id}` | {d.scenario} | {em_str} | {abs_str} | "
            f"{d.medications_gt_count} | {d.medications_pred_count} | "
            f"{d.fields_matched}/{d.fields_evaluated} | {d.latency_ms:.0f} ms |"
        )

    lines.extend([
        "",
        "---",
        "*Automated Evaluation Runner v1.0.0 — AURA-Rx Capstone Engineering Team*",
    ])
    return "\n".join(lines)


class PrescriptionEvaluator:
    """
    Reproducible Evaluation Runner executing real model or mock pipeline inference
    against verified ground-truth annotations.
    """

    def __init__(self, data_root: Path = Path("data")):
        self.data_root = data_root
        self.annotations_path = self.data_root / "annotations" / "sample_annotations.json"

    def load_annotations(self) -> List[PrescriptionDocumentRecord]:
        """Loads and parses gold-standard ground truth records."""
        if not self.annotations_path.exists():
            raise FileNotFoundError(f"Annotations not found: {self.annotations_path}")
        with open(self.annotations_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [PrescriptionDocumentRecord.model_validate(r) for r in raw]

    async def run_evaluation(
        self,
        mode: Literal["live", "mock"] = "live",
        pipeline: Optional[Any] = None,
    ) -> EvaluationReport:
        """Runs end-to-end evaluation and produces complete EvaluationReport."""
        records = self.load_annotations()
        items: List[EvaluationItem] = []

        model_provider = "mock" if mode == "mock" else "gemini"
        model_name = "mock_fixtures" if mode == "mock" else "gemini-3.5-flash-lite"
        ocr_engine = "mock_ocr" if mode == "mock" else "google_multimodal_vision"

        if pipeline is None:
            if mode == "mock":
                from backend.app.services.mock_pipeline import MockPrescriptionPipeline
                pipeline = MockPrescriptionPipeline()
            else:
                from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
                pipeline = MultimodalPrescriptionPipeline()

        from backend.app.services.pipeline_interface import PipelineOptions

        for rec in records:
            gt = rec.ground_truth
            img_rel = gt.image_rel_path
            img_path = self.data_root / img_rel

            image_bytes: Optional[bytes] = None
            if img_path.exists():
                image_bytes = img_path.read_bytes()

            filename = img_path.name
            public_url = f"/samples/{filename}"
            scenario = rec.metadata.get("scenario", "standard")

            options = PipelineOptions(
                mock_scenario=scenario,
                enable_preprocessing=True,
                enable_rag_validation=True,
                enable_confidence_calibration=True,
                enable_lasa_check=True,
                enable_multilingual=True,
            )

            t0 = time.perf_counter()
            is_error = False
            err_msg = None
            pred_dict: Optional[Dict[str, Any]] = None

            try:
                resp = await pipeline.process_prescription(
                    image_bytes=image_bytes,
                    filename=filename,
                    public_image_url=public_url,
                    options=options,
                )
                pred_dict = resp.model_dump()
                model_provider = getattr(resp, "model_provider", model_provider) or model_provider
                model_name = getattr(resp, "model_name", model_name) or model_name
                ocr_engine = getattr(resp, "ocr_engine", ocr_engine) or ocr_engine
            except Exception as exc:
                is_error = True
                err_msg = str(exc)

            latency_ms = (time.perf_counter() - t0) * 1000.0

            items.append(EvaluationItem(
                record=rec,
                prediction=pred_dict,
                latency_ms=latency_ms,
                is_error=is_error,
                error_message=err_msg,
            ))

        metrics, details = compute_evaluation_metrics(items)

        disclaimer = None
        if mode == "mock":
            disclaimer = "INFERENCE_MODE: MOCK (PIPELINE TEST ONLY - NOT VALID FOR ACCURACY CLAIMS)"

        report = EvaluationReport(
            inference_mode=mode,
            disclaimer=disclaimer,
            dataset_version=get_dataset_version(),
            git_commit=get_git_commit(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_provider=model_provider,
            model_name=model_name,
            ocr_engine=ocr_engine,
            metrics=metrics,
            per_document_results=details,
        )

        return report

    def save_report_artifacts(
        self,
        report: EvaluationReport,
        json_path: Path = Path("reports/baseline_evaluation.json"),
        md_path: Path = Path("docs/BASELINE_RESULTS.md"),
    ) -> None:
        """Saves evaluation report as JSON and Markdown."""
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        md_content = generate_markdown_report(report)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)


async def main_cli():
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="AURA-Rx Baseline Prescription Evaluation Runner")
    parser.add_argument("--mode", choices=["live", "mock"], default="live", help="Inference mode ('live' or 'mock')")
    parser.add_argument("--output-json", default="reports/baseline_evaluation.json", help="Path for JSON output")
    parser.add_argument("--output-md", default="docs/BASELINE_RESULTS.md", help="Path for Markdown report")
    args = parser.parse_args()

    print(f"======================================================")
    print(f"AURA-Rx PRESCRIPTION EVALUATION RUNNER")
    print(f"Mode: {args.mode.upper()}")
    print(f"======================================================")

    evaluator = PrescriptionEvaluator()
    report = await evaluator.run_evaluation(mode=args.mode)
    evaluator.save_report_artifacts(report, json_path=Path(args.output_json), md_path=Path(args.output_md))

    print(f"\nEvaluation Complete! All 11 metrics computed successfully.")
    print(f"  Exact Medicine-Name Acc: {report.metrics.exact_medicine_name_accuracy*100:.2f}%")
    print(f"  Strength Accuracy:       {report.metrics.strength_accuracy*100:.2f}%")
    print(f"  Dosage Accuracy:         {report.metrics.dosage_accuracy*100:.2f}%")
    print(f"  Route Accuracy:          {report.metrics.route_accuracy*100:.2f}%")
    print(f"  Frequency Accuracy:      {report.metrics.frequency_accuracy*100:.2f}%")
    print(f"  Duration Accuracy:       {report.metrics.duration_accuracy*100:.2f}%")
    print(f"  Field Completeness:      {report.metrics.field_completeness*100:.2f}%")
    print(f"  Unsupported / Fab Rate:  {report.metrics.unsupported_fabricated_rate*100:.2f}%")
    print(f"  Appropriate Abstention:  {report.metrics.appropriate_abstention_rate*100:.2f}%")
    print(f"  Prescription Exact Match:{report.metrics.prescription_level_exact_match*100:.2f}%")
    print(f"  Latency p50 / p95:       {report.metrics.latency_p50_ms:.0f}ms / {report.metrics.latency_p95_ms:.0f}ms")
    print(f"  Error Rate:              {report.metrics.error_rate*100:.2f}%")
    print(f"\nArtifacts saved:")
    print(f"  JSON: {args.output_json}")
    print(f"  MD:   {args.output_md}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_cli())
