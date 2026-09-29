"""
EXP-08: Multilingual Explanation & Fidelity Evaluator (Section 26, 27, 28, 29).
Evaluates Phase 11 factual fidelity across English, Hindi, and Marathi.
Measures Roman medicine name preservation, numeric preservation, unsupported information rate,
and cross-language semantic consistency.
Generates eval/tables/07_multilingual.csv.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.explanation.generator import PosologyExplanationGenerator
from ai.explanation.fixtures import EXPLANATION_FIXTURES


class MultilingualEvaluator:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = root_dir

    def evaluate(self) -> Dict[str, Any]:
        fixtures = EXPLANATION_FIXTURES
        
        # Generation fixtures (those with "input")
        gen_fixtures = {k: v for k, v in fixtures.items() if "input" in v}
        total_gen = len(gen_fixtures)
        
        per_lang_metrics: Dict[str, Dict[str, Any]] = {
            "en": {"med_preserved": 0, "num_preserved": 0, "unsupported_count": 0, "total": 0},
            "hi": {"med_preserved": 0, "num_preserved": 0, "unsupported_count": 0, "total": 0},
            "mr": {"med_preserved": 0, "num_preserved": 0, "unsupported_count": 0, "total": 0}
        }

        cross_lang_consistent_count = 0
        per_fixture_records: List[Dict[str, Any]] = []

        for k, f in gen_fixtures.items():
            facts = f["input"]
            bundle = PosologyExplanationGenerator.generate_explanation(**facts)

            # Check cross-language fact parity
            en_res = bundle.explanations.get("en")
            hi_res = bundle.explanations.get("hi")
            mr_res = bundle.explanations.get("mr")

            if not (en_res and hi_res and mr_res):
                continue

            # Check if all 3 languages rendered the same eligibility status
            same_status = (en_res.status == hi_res.status == mr_res.status)
            
            # Check Roman drug name presence across all three if eligible
            med_name = (facts.get("medicine_name") or "").lower().strip()
            roman_in_all = True
            if med_name and en_res.status in ("eligible", "restricted"):
                roman_in_all = (
                    med_name in en_res.summary.lower() and
                    med_name in hi_res.summary.lower() and
                    med_name in mr_res.summary.lower()
                )

            if same_status and roman_in_all:
                cross_lang_consistent_count += 1

            for lang_code, res in [("en", en_res), ("hi", hi_res), ("mr", mr_res)]:
                per_lang_metrics[lang_code]["total"] += 1
                if res.validation.medicine_fidelity:
                    per_lang_metrics[lang_code]["med_preserved"] += 1
                if res.validation.numeric_fidelity:
                    per_lang_metrics[lang_code]["num_preserved"] += 1
                if not res.validation.unsupported_fact_check:
                    per_lang_metrics[lang_code]["unsupported_count"] += 1

            per_fixture_records.append({
                "fixture_key": k,
                "status": str(en_res.status),
                "consistent_across_languages": same_status and roman_in_all,
                "en_summary": en_res.summary,
                "hi_summary": hi_res.summary,
                "mr_summary": mr_res.summary
            })

        # Calculate rates per language
        lang_summary = {}
        for l_code, data in per_lang_metrics.items():
            tot = data["total"]
            lang_summary[l_code] = {
                "total_evaluated": tot,
                "medicine_name_preservation_rate": round(data["med_preserved"] / tot, 4) if tot > 0 else 1.0,
                "numeric_preservation_rate": round(data["num_preserved"] / tot, 4) if tot > 0 else 1.0,
                "unsupported_fact_rate": round(data["unsupported_count"] / tot, 4) if tot > 0 else 0.0,
            }

        cross_consistency_rate = round(cross_lang_consistent_count / total_gen, 4) if total_gen > 0 else 1.0

        return {
            "experiment_id": "EXP-08",
            "name": "Multilingual Explanation & Factual Fidelity Evaluation",
            "total_fixtures_evaluated": total_gen,
            "languages": ["English (en)", "Hindi (hi)", "Marathi (mr)"],
            "policy_version": "explanation_policy_v1",
            "template_version": "explanation_template_v1",
            "human_evaluation_status": "Human multilingual evaluation was not performed.",
            "cross_language_consistency": {
                "consistent_outputs": cross_lang_consistent_count,
                "inconsistent_outputs": total_gen - cross_lang_consistent_count,
                "consistency_rate": cross_consistency_rate
            },
            "per_language_metrics": lang_summary,
            "per_fixture": per_fixture_records
        }

    def generate_csv_table(self, output_dir: Path) -> Path:
        results = self.evaluate()
        output_dir.mkdir(parents=True, exist_ok=True)
        table_path = output_dir / "07_multilingual.csv"

        headers = ["Language", "Evaluated Sentences", "Medicine Name Preservation", "Numeric Fidelity", "Unsupported Information Rate", "Cross-Language Consistency"]
        rows = []
        for l_code, m in results["per_language_metrics"].items():
            lang_name = "English (en)" if l_code == "en" else ("Hindi (hi)" if l_code == "hi" else "Marathi (mr)")
            rows.append([
                lang_name,
                str(m["total_evaluated"]),
                f"{m['medicine_name_preservation_rate']:.4f}",
                f"{m['numeric_preservation_rate']:.4f}",
                f"{m['unsupported_fact_rate']:.4f}",
                f"{results['cross_language_consistency']['consistency_rate']:.4f}"
            ])

        with open(table_path, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")

        return table_path

