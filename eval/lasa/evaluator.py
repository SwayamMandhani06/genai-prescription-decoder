"""
EXP-07: LASA Conflict Detection Evaluator (Section 24 & 25).
Evaluates Phase 10 orthographic and phonetic similarity screening against curated ISMP pairs
and negative control non-confusable formulations.
Generates eval/tables/06_lasa.csv and confusion matrix.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from ai.lasa.detector import screen_medicine
from ai.lasa.config import get_default_lasa_config, TALL_MAN_PAIRS
from ai.rag.schemas import MedicineReferenceRecord, SourceProvenance


class LASAEvaluator:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = root_dir

        self.config = get_default_lasa_config()

    def _make_ref(self, name: str) -> MedicineReferenceRecord:
        return MedicineReferenceRecord(
            reference_id=f"ref-{name.lower().replace(' ', '-')}",
            source="eval-vocab",
            source_version="v1.0",
            medicine_name=name,
            normalized_name=name.lower().strip(),
            generic_name=name,
            brand_name=name,
            aliases=[],
            ingredients=[],
            provenance=SourceProvenance(
                source_id="eval-vocab",
                source_name="Evaluation Formulary Subset",
                source_version="v1.0",
                license="Academic Evaluation",
                license_category="statutory_government_open_data",
                retrieval_date="2026-09-28T00:00:00Z",
                citation="ISMP and CDSCO evaluation vocabulary subset"
            )
        )

    def evaluate(self) -> Dict[str, Any]:
        # Positive pairs from curated ISMP 2024 list
        pos_pairs = [(p[0], p[1]) for p in TALL_MAN_PAIRS]

        # Negative control pairs: clearly distinct drug names that must not trigger LASA
        neg_pairs = [
            ("paracetamol", "amoxicillin"),
            ("pantocid", "metformin"),
            ("cetirizine", "azithromycin"),
            ("ibuprofen", "omeprazole"),
            ("aspirin", "ciprofloxacin"),
            ("atorvastatin", "metformin"),
            ("losartan", "amoxicillin"),
            ("metoprolol", "paracetamol"),
            ("amoxicillin", "pantoprazole"),
            ("prednisolone", "azithromycin"),
            ("augmentin", "pantocid"),
            ("paracetamol", "dopamine"),
            ("glipizide", "paracetamol"),
            ("insulin", "pantoprazole"),
            ("morphine", "azithromycin"),
            ("furosemide", "aspirin"),
            ("ranitidine", "amoxicillin"),
            ("tramadol", "pantoprazole"),
            ("clarithromycin", "paracetamol"),
            ("doxycycline", "metformin")
        ]

        # Build vocabulary from all drugs
        all_drugs = set()
        for a, b in pos_pairs:
            all_drugs.add(a)
            all_drugs.add(b)
        for a, b in neg_pairs:
            all_drugs.add(a)
            all_drugs.add(b)

        ref_vocab = [self._make_ref(d) for d in all_drugs]

        tp = 0
        fn = 0
        fp = 0
        tn = 0

        pos_eval_records = []
        for a, b in pos_pairs:
            # Screen drug a in presence of b
            target_vocab = [self._make_ref(b)]
            scr = screen_medicine(
                candidate_name=a,
                item_index=1,
                reference_records=target_vocab,
                config=self.config
            )
            detected = (scr.has_lasa_conflict is True)
            if detected:
                tp += 1
            else:
                fn += 1
            top_detail = scr.confusables[0] if scr.confusables else None
            pos_eval_records.append({
                "candidate": a,
                "partner": b,
                "ground_truth_lasa": True,
                "conflict_detected": detected,
                "score": scr.top_confusable_score or (top_detail.combined_score if top_detail else 0.0),
                "tall_man_candidate": top_detail.tall_man_prescribed if top_detail else None,
                "tall_man_partner": top_detail.tall_man_confused if top_detail else None
            })

        neg_eval_records = []
        for a, b in neg_pairs:
            target_vocab = [self._make_ref(b)]
            scr = screen_medicine(
                candidate_name=a,
                item_index=1,
                reference_records=target_vocab,
                config=self.config
            )
            detected = (scr.has_lasa_conflict is True)
            if detected:
                fp += 1
            else:
                tn += 1
            top_detail = scr.confusables[0] if scr.confusables else None
            neg_eval_records.append({
                "candidate": a,
                "partner": b,
                "ground_truth_lasa": False,
                "conflict_detected": detected,
                "score": scr.top_confusable_score or (top_detail.combined_score if top_detail else 0.0)
            })

        total_tested = len(pos_pairs) + len(neg_pairs)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        acc = (tp + tn) / total_tested if total_tested > 0 else 0.0

        return {
            "experiment_id": "EXP-07",
            "name": "Look-Alike / Sound-Alike (LASA) Conflict Detection Evaluation",
            "curated_pair_source": "ISMP 2024 List of Look-Alike Drug Name Sets (N=20 pairs)",
            "negative_control_count": len(neg_pairs),
            "total_pairs_evaluated": total_tested,
            "threshold": self.config.combined_threshold,
            "orthographic_weight": self.config.orthographic_weight,
            "phonetic_weight": self.config.phonetic_weight,
            "limitation_statement": (
                "The evaluated set consists of the 20 documented high-frequency ISMP confusion pairs "
                "and 20 negative controls. It does not represent all possible global drug confusions."
            ),
            "confusion_matrix": {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "matrix": [[tn, fp], [fn, tp]]
            },
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
                "false_positive_rate": round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0,
                "false_negative_rate": round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0
            },
            "per_pair": pos_eval_records + neg_eval_records
        }

    def generate_csv_table(self, output_dir: Path) -> Path:
        results = self.evaluate()
        output_dir.mkdir(parents=True, exist_ok=True)
        table_path = output_dir / "06_lasa.csv"

        headers = ["Cohort", "Pairs (N)", "TP", "FP", "FN", "TN", "Precision", "Recall", "F1", "Accuracy"]
        m = results["metrics"]
        cm = results["confusion_matrix"]

        rows = [
            [
                "Curated ISMP 2024 High-Risk Pairs",
                "20",
                str(cm["tp"]), "-", str(cm["fn"]), "-", "-", f"{results['metrics']['recall']:.4f}", "-", "-"
            ],
            [
                "Negative Control Pairs",
                str(results["negative_control_count"]),
                "-", str(cm["fp"]), "-", str(cm["tn"]), "-", "-", "-", "-"
            ],
            [
                "COMBINED EVALUATION",
                str(results["total_pairs_evaluated"]),
                str(cm["tp"]), str(cm["fp"]), str(cm["fn"]), str(cm["tn"]),
                f"{m['precision']:.4f}",
                f"{m['recall']:.4f}",
                f"{m['f1']:.4f}",
                f"{m['accuracy']:.4f}"
            ]
        ]

        with open(table_path, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")

        return table_path
