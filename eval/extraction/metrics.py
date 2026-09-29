"""
Multimodal Extraction Evaluation Metrics (Section 12, 13, 14, 15).
Computes exact and normalized Precision, Recall, and F1 per clinical field:
- medicine_name
- dosage_strength
- frequency
- duration
Distinguishes missing vs uncertain vs incorrect fields.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


def normalize_field_value(value: Optional[str], field_type: str) -> str:
    """
    Standard evaluation normalization for field comparison.
    Preserves clinical identity while standardizing notation.
    """
    if not value:
        return ""
    
    val = unicodedata.normalize("NFKC", str(value)).lower().strip()
    val = re.sub(r"[\(\)\[\]\{\},:;\"']", " ", val)
    val = re.sub(r"\s+", " ", val).strip()

    if field_type == "dosage":
        # standardise spaces before units
        val = re.sub(r"(\d+)\s*(mg|ml|mcg|g|gm)\b", r"\1 \2", val)
    elif field_type == "duration":
        # standardise day/days
        val = re.sub(r"\bday\b", "days", val)
        val = re.sub(r"\bweek\b", "weeks", val)
        val = re.sub(r"\bmonth\b", "months", val)
    elif field_type == "frequency":
        # standardise Indian shorthand 1-0-1 etc
        val = re.sub(r"\b(bd|bid)\b", "1-0-1", val)
        val = re.sub(r"\b(od|qd)\b", "1-0-0", val)
        val = re.sub(r"\b(tds|tid)\b", "1-1-1", val)
        val = re.sub(r"\b(qid)\b", "1-1-1-1", val)

    return val


def evaluate_field_list(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Dict[str, Any]],
    field_key: str,
    gt_key: str
) -> Dict[str, Any]:
    """
    Evaluates a specific field across a set of paired medication records.
    Returns: TP, FP, FN, Precision, Recall, F1, exact_matches, normalized_matches, missing, uncertain
    """
    n_gt = len(ground_truths)
    n_pred = len(predictions)

    tp_exact = 0
    tp_norm = 0
    fp = 0
    fn = 0
    missing_count = 0
    uncertain_count = 0
    incorrect_count = 0

    # Match in order or pair-wise
    paired_count = max(n_gt, n_pred)

    for i in range(paired_count):
        gt_val = ground_truths[i].get(gt_key) if i < n_gt else None
        pred_obj = predictions[i] if i < n_pred else None

        pred_val = None
        pred_status = "confident"
        pred_state = "extracted"

        if isinstance(pred_obj, dict):
            field_data = pred_obj.get(field_key)
            if isinstance(field_data, dict):
                pred_val = field_data.get("value")
                pred_status = field_data.get("status", "confident")
                pred_state = field_data.get("extraction_state", "extracted")
            elif isinstance(field_data, str):
                pred_val = field_data
        elif pred_obj is not None:
            pred_val = getattr(pred_obj, field_key, None)
            if hasattr(pred_val, "value"):
                pred_status = getattr(pred_val, "status", "confident")
                pred_state = getattr(pred_val, "extraction_state", "extracted")
                pred_val = getattr(pred_val, "value", None)

        # Check missing or uncertain
        if pred_state == "missing" or pred_val is None:
            missing_count += 1
        if pred_status == "uncertain" or pred_state == "ambiguous":
            uncertain_count += 1

        # Matching logic
        if gt_val is not None and pred_val is not None:
            raw_match = str(gt_val).strip().lower() == str(pred_val).strip().lower()
            norm_match = normalize_field_value(gt_val, field_key) == normalize_field_value(pred_val, field_key)

            if raw_match:
                tp_exact += 1
            if norm_match:
                tp_norm += 1
            else:
                incorrect_count += 1
                fp += 1
                fn += 1
        elif gt_val is not None and pred_val is None:
            fn += 1
        elif gt_val is None and pred_val is not None:
            fp += 1

    # Standard metrics based on normalized matches
    prec = tp_norm / (tp_norm + fp) if (tp_norm + fp) > 0 else 0.0
    rec = tp_norm / (tp_norm + fn) if (tp_norm + fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    return {
        "field": field_key,
        "total_gt": n_gt,
        "total_pred": n_pred,
        "tp_exact": tp_exact,
        "tp_normalized": tp_norm,
        "fp": fp,
        "fn": fn,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "exact_match_rate": round(tp_exact / n_gt, 4) if n_gt > 0 else 0.0,
        "missing_count": missing_count,
        "uncertain_count": uncertain_count,
        "incorrect_count": incorrect_count
    }
