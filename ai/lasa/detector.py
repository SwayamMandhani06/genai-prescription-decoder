"""
Phase 10: LASA (Look-Alike / Sound-Alike) Conflict Detector.
Evaluates extracted medicine names against the full reference pool and known ISMP pairs
to identify potential name-confusion risks.

Design principles:
- Safety-oriented: flags conflicts, does NOT resolve, diagnose, or prescribe
- Deterministic: all outputs reproducible given same inputs and configuration
- Decoupled: consumes Phase 6 extraction and Phase 7 RAG index; does NOT modify them
- Medicine identity only: dosage/strength/formulation similarity is OUT OF SCOPE
- Traceable: every flag includes provenance and machine-readable reason
"""

from datetime import datetime, timezone
from typing import List, Optional

from ai.rag.schemas import MedicineReferenceRecord
from ai.rag.normalization import normalize_medicine_name
from ai.rag.index import MedicineReferenceIndex
from ai.lasa.config import LasaConfig, get_default_lasa_config, TALL_MAN_PAIRS
from ai.lasa.schemas import (
    LasaSimilarityDetail,
    MedicineLasaResult,
    PrescriptionLasaDetection,
    LasaDetectionProvenance,
    LasaRiskLevel,
)
from ai.lasa.similarity import (
    combined_similarity,
    lookup_tall_man_pair,
    extract_base_stem,
)


def _classify_risk(combined_score: float, config: LasaConfig) -> LasaRiskLevel:
    """
    Deterministic similarity conflict severity classification based on configured thresholds.
    NOTE: Represents lexical/phonetic similarity proximity, NOT clinical risk.
    """
    if combined_score >= config.high_risk_threshold:
        return "high"
    elif combined_score >= config.medium_risk_threshold:
        return "medium"
    else:
        return "low"


def _determine_similarity_type(
    ortho_score: float,
    phonetic_score: float,
    is_known_pair: bool,
    config: LasaConfig,
) -> str:
    """Determines the dominant similarity mechanism."""
    if is_known_pair:
        return "known_pair"
    ortho_above = ortho_score >= config.orthographic_threshold
    phon_above = phonetic_score >= config.phonetic_threshold
    if ortho_above and phon_above:
        return "combined"
    elif phon_above:
        return "phonetic"
    else:
        return "orthographic"


def _max_risk(a: LasaRiskLevel, b: LasaRiskLevel) -> LasaRiskLevel:
    """Returns the higher of two risk levels."""
    order = {"low": 0, "medium": 1, "high": 2}
    return a if order.get(a, 0) >= order.get(b, 0) else b


def screen_medicine(
    candidate_name: str,
    item_index: int,
    reference_records: Optional[List[MedicineReferenceRecord]],
    config: Optional[LasaConfig] = None,
) -> MedicineLasaResult:
    """
    Screens a single extracted medicine name against the reference pool
    for look-alike / sound-alike conflicts.

    Args:
        candidate_name: Extracted medicine name from Phase 6
        item_index: 1-based medication line item index
        reference_records: All reference medicine records from the RAG index
        config: LASA detection configuration (uses default if None)

    Returns:
        MedicineLasaResult with all detected confusable counterparts
    """
    cfg = config or get_default_lasa_config()
    norm_candidate = normalize_medicine_name(candidate_name)

    if reference_records is None:
        return MedicineLasaResult(
            item_index=item_index,
            prescribed_candidate=candidate_name or "",
            normalized_candidate=norm_candidate or "",
            status="unavailable",
            has_lasa_conflict=None,
            highest_risk="low",
            confusable_count=0,
            confusables=[],
            error_message="Reference vocabulary unavailable for LASA screening",
        )

    if not norm_candidate:
        return MedicineLasaResult(
            item_index=item_index,
            prescribed_candidate=candidate_name or "",
            normalized_candidate="",
            status="completed",
            has_lasa_conflict=False,
            highest_risk="low",
            confusable_count=0,
            confusables=[],
        )

    confusables: List[LasaSimilarityDetail] = []

    # Build a set of already-compared normalized names to avoid duplicates
    compared_names: set = set()
    stem_candidate = extract_base_stem(norm_candidate)

    # ------------------------------------------------------------------
    # Pass 1: Screen against all reference records in the RAG index
    # ------------------------------------------------------------------
    for ref in reference_records:
        # Check if candidate belongs to this reference record (same drug entity)
        ref_names = [ref.medicine_name]
        if ref.brand_name:
            ref_names.append(ref.brand_name)
        ref_names.extend(ref.aliases)

        is_same_drug = False
        for rn in ref_names:
            rn_norm = normalize_medicine_name(rn)
            rn_stem = extract_base_stem(rn_norm)
            if rn_norm == norm_candidate or (stem_candidate and rn_stem == stem_candidate):
                is_same_drug = True
                break

        if is_same_drug:
            continue

        # Gather all name variants from the reference record
        name_variants = [ref.medicine_name]
        if ref.brand_name:
            name_variants.append(ref.brand_name)
        for alias in ref.aliases:
            name_variants.append(alias)

        for variant_name in name_variants:
            norm_variant = normalize_medicine_name(variant_name)
            stem_variant = extract_base_stem(norm_variant)

            # Skip self-matches and already-compared names
            if not norm_variant or norm_variant == norm_candidate:
                continue
            # Skip formulation / dosage variants of the same molecule
            if stem_candidate and stem_variant and stem_candidate == stem_variant:
                continue
            if norm_variant in compared_names:
                continue
            compared_names.add(norm_variant)

            # Compute all similarity dimensions
            ortho, phon, combo, meta_match = combined_similarity(
                candidate_name, variant_name,
                ortho_weight=cfg.orthographic_weight,
                phonetic_weight=cfg.phonetic_weight,
            )

            # Check if this is a known Tall Man pair
            tall_man = lookup_tall_man_pair(candidate_name, variant_name)
            is_known = tall_man is not None

            # Determine if this meets the threshold for flagging
            meets_threshold = combo >= cfg.combined_threshold
            if not meets_threshold and not is_known:
                continue

            # Classify risk (similarity conflict severity)
            risk = _classify_risk(combo, cfg)
            if is_known:
                risk = _max_risk(risk, cfg.known_pair_risk_override)  # type: ignore

            sim_type = _determine_similarity_type(ortho, phon, is_known, cfg)

            # Build clinical context rationale
            context_parts = []
            if is_known:
                context_parts.append(
                    f"ISMP high-risk Tall Man pair: {tall_man[2]} / {tall_man[3]}."
                )
            context_parts.append(
                f"Orthographic similarity {ortho:.2f}, phonetic similarity {phon:.2f}, "
                f"combined {combo:.2f}."
            )
            if meta_match:
                context_parts.append("Primary phonetic codes are identical (metaphone match).")
            context_parts.append(
                "Potential medicine-name similarity conflict flagged for verification. "
                "This is an application safety-review state indicating that a potential medicine-name "
                "conflict requires attention/verification. It does NOT indicate a confirmed error, "
                "wrong medicine, clinical danger, medical risk probability, diagnosis, or prescribing recommendation."
            )

            confusables.append(LasaSimilarityDetail(
                confusable_name=variant_name,
                confusable_reference_id=ref.reference_id,
                confusable_generic_name=ref.generic_name,
                orthographic_score=round(ortho, 4),
                phonetic_score=round(phon, 4),
                combined_score=round(combo, 4),
                metaphone_match=meta_match,
                similarity_type=sim_type,  # type: ignore
                risk_level=risk,
                is_known_pair=is_known,
                tall_man_prescribed=tall_man[2] if tall_man else None,
                tall_man_confused=tall_man[3] if tall_man else None,
                clinical_context=" ".join(context_parts),
            ))

    # ------------------------------------------------------------------
    # Pass 2: Check against known ISMP pairs not in reference index
    # ------------------------------------------------------------------
    for pair in TALL_MAN_PAIRS:
        # pair = (drug_a_lower, drug_b_lower, tall_man_a, tall_man_b)
        counterpart_name = None
        tall_man_prescribed = None
        tall_man_confused = None

        if norm_candidate == pair[0] or stem_candidate == pair[0]:
            counterpart_name = pair[1]
            tall_man_prescribed = pair[2]
            tall_man_confused = pair[3]
        elif norm_candidate == pair[1] or stem_candidate == pair[1]:
            counterpart_name = pair[0]
            tall_man_prescribed = pair[3]
            tall_man_confused = pair[2]

        if counterpart_name and counterpart_name not in compared_names:
            norm_counterpart = normalize_medicine_name(counterpart_name)
            stem_counterpart = extract_base_stem(norm_counterpart)
            if stem_candidate and stem_counterpart and stem_candidate == stem_counterpart:
                continue
            compared_names.add(counterpart_name)
            ortho, phon, combo, meta_match = combined_similarity(
                candidate_name, counterpart_name,
                ortho_weight=cfg.orthographic_weight,
                phonetic_weight=cfg.phonetic_weight,
            )
            risk = _max_risk(
                _classify_risk(combo, cfg),
                cfg.known_pair_risk_override,  # type: ignore
            )

            confusables.append(LasaSimilarityDetail(
                confusable_name=counterpart_name.title(),
                confusable_reference_id=None,
                confusable_generic_name=None,
                orthographic_score=round(ortho, 4),
                phonetic_score=round(phon, 4),
                combined_score=round(combo, 4),
                metaphone_match=meta_match,
                similarity_type="known_pair",
                risk_level=risk,
                is_known_pair=True,
                tall_man_prescribed=tall_man_prescribed,
                tall_man_confused=tall_man_confused,
                clinical_context=(
                    f"ISMP high-risk Tall Man pair: {tall_man_prescribed} / {tall_man_confused}. "
                    f"Orthographic similarity {ortho:.2f}, phonetic similarity {phon:.2f}, "
                    f"combined {combo:.2f}. "
                    "Potential medicine-name similarity conflict flagged for verification. "
                    "This is an application safety-review state indicating that a potential medicine-name "
                    "conflict requires attention/verification. It does NOT indicate a confirmed error, "
                    "wrong medicine, clinical danger, medical risk probability, diagnosis, or prescribing recommendation."
                ),
            ))

    # Sort descending by combined_score, then by name for determinism
    confusables.sort(key=lambda c: (-c.combined_score, c.confusable_name))

    # Trim to configured maximum
    confusables = confusables[:cfg.max_confusable_candidates]

    has_conflict = len(confusables) > 0
    highest_risk: LasaRiskLevel = "low"
    for c in confusables:
        highest_risk = _max_risk(highest_risk, c.risk_level)

    return MedicineLasaResult(
        item_index=item_index,
        prescribed_candidate=candidate_name,
        normalized_candidate=norm_candidate,
        status="completed",
        has_lasa_conflict=has_conflict,
        highest_risk=highest_risk,
        confusable_count=len(confusables),
        confusables=confusables,
        top_confusable_name=confusables[0].confusable_name if confusables else None,
        top_confusable_score=confusables[0].combined_score if confusables else None,
    )


def detect_prescription_lasa(
    prescription_id: str,
    medicine_names: List[str],
    reference_records: Optional[List[MedicineReferenceRecord]],
    config: Optional[LasaConfig] = None,
) -> PrescriptionLasaDetection:
    """
    Runs LASA detection across all medicines in a prescription.

    Args:
        prescription_id: Unique prescription identifier
        medicine_names: List of extracted medicine names from Phase 6
        reference_records: All reference records from the RAG index
        config: LASA configuration (uses default if None)

    Returns:
        PrescriptionLasaDetection with all medicine-level and aggregate results
    """
    cfg = config or get_default_lasa_config()
    now_iso = datetime.now(timezone.utc).isoformat()

    provenance = LasaDetectionProvenance(
        policy_version=cfg.policy_version,
        config_hash=cfg.config_hash(),
        orthographic_threshold=cfg.orthographic_threshold,
        phonetic_threshold=cfg.phonetic_threshold,
        combined_threshold=cfg.combined_threshold,
        reference_pool_size=len(reference_records) if reference_records is not None else 0,
        known_pairs_count=len(TALL_MAN_PAIRS),
        timestamp=now_iso,
    )

    if reference_records is None:
        return PrescriptionLasaDetection(
            prescription_id=prescription_id,
            status="unavailable",
            conflict_detected=None,
            has_any_lasa_conflict=None,
            highest_risk="low",
            total_medicines_screened=0,
            medicines_with_conflicts=0,
            medicines=[],
            summary="LASA screening unavailable: reference medicine vocabulary not provided or inaccessible.",
            provenance=provenance,
            error_message="Reference vocabulary unavailable for LASA screening",
        )

    try:
        medicines: List[MedicineLasaResult] = []
        has_any = False
        highest_risk: LasaRiskLevel = "low"
        conflict_count = 0

        for idx, med_name in enumerate(medicine_names, start=1):
            result = screen_medicine(
                candidate_name=med_name,
                item_index=idx,
                reference_records=reference_records,
                config=cfg,
            )
            medicines.append(result)
            if result.has_lasa_conflict:
                has_any = True
                conflict_count += 1
                highest_risk = _max_risk(highest_risk, result.highest_risk)

        # Build summary
        if not has_any:
            summary = (
                f"LASA screening completed for {len(medicine_names)} medicine(s). "
                "No potential medicine-name similarity conflicts detected against reference formularies."
            )
        else:
            flagged_names = [m.prescribed_candidate for m in medicines if m.has_lasa_conflict]
            summary = (
                f"LASA screening completed for {len(medicine_names)} medicine(s). "
                f"{conflict_count} medicine(s) flagged with potential look-alike/sound-alike similarity conflicts: "
                f"{', '.join(flagged_names)}. "
                f"Highest conflict severity: {highest_risk}. "
                "Conflicts are application safety-review flags indicating that a potential medicine-name conflict "
                "requires attention/verification — not clinical danger, adverse drug event, wrong medicine, "
                "medical risk probability, diagnosis, or prescribing recommendation."
            )

        return PrescriptionLasaDetection(
            prescription_id=prescription_id,
            status="completed",
            conflict_detected=has_any,
            has_any_lasa_conflict=has_any,
            highest_risk=highest_risk,
            total_medicines_screened=len(medicine_names),
            medicines_with_conflicts=conflict_count,
            medicines=medicines,
            summary=summary,
            provenance=provenance,
        )
    except Exception as exc:
        return PrescriptionLasaDetection(
            prescription_id=prescription_id,
            status="failed",
            conflict_detected=None,
            has_any_lasa_conflict=None,
            highest_risk="low",
            total_medicines_screened=0,
            medicines_with_conflicts=0,
            medicines=[],
            summary=f"LASA screening failed due to an internal detector error: {str(exc)}",
            provenance=provenance,
            error_message=str(exc),
        )
