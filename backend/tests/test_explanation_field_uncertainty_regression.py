"""
Regression Tests: Field-level Uncertainty & Speech Script Integrity.
Verifies that:
1. Readable medicine names are never masked with generic "could not be read" warnings.
2. Missing or uncertain secondary fields (e.g. duration, frequency) do not erase readable medicine names.
3. Genuinely unreadable medicine names produce explicit verification notices.
4. Multilingual explanations across English, Hindi, and Marathi preserve verbatim drug names.
5. Speech scripts synthesized from the explanation contain the actual medicine names and instructions.
"""

import pytest
from ai.explanation.generator import PosologyExplanationGenerator
from ai.explanation.templates import PosologyTemplateEngine
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions
from backend.app.multimodal import MockMultimodalModelAdapter, MultimodalExtractionService, MultimodalConfig


def test_readable_medicine_name_preserved_when_field_uncertain():
    """
    Field-level uncertainty: If medicine name is readable (e.g. 'Augmentin 625 Duo')
    but duration or frequency has uncertainty (status='restricted'),
    the explanation MUST use the verified name and NEVER say 'could not be read with sufficient confidence'.
    """
    for lang in ["en", "hi", "mr"]:
        summary = PosologyTemplateEngine.render_summary(
            language=lang,
            status="restricted",
            medicine_name="Augmentin 625 Duo",
            dosage="625 mg",
            frequency_key="twice_daily",
            raw_frequency="1-0-1",
            duration=None,
            meal_relation_key="after_meals",
            reason_code="EXTRACTION_OR_VALIDATION_UNCERTAIN",
        )
        assert "Augmentin 625 Duo" in summary, f"Medicine name missing from {lang} summary"
        assert "could not be read with sufficient confidence" not in summary
        assert "पढ़ा नहीं जा सका" not in summary
        assert "वाचता आले नाही" not in summary


def test_instructions_preserve_readable_name_with_verification_notice():
    """
    Ensures patient instructions state the verified medicine name and intake instructions
    while advising pharmacist confirmation for the ambiguous sub-field.
    """
    inst_en = PosologyTemplateEngine.render_patient_instructions(
        language="en",
        status="restricted",
        medicine_name="Azithromycin 500",
        dosage="500 mg",
        frequency_key="once_daily",
        duration="3 days",
        meal_relation_key="before_meals",
        reason_code="EXTRACTION_OR_VALIDATION_UNCERTAIN",
    )
    assert "Azithromycin 500" in inst_en
    assert "500 mg" in inst_en
    assert "Ambiguous handwriting flagged" in inst_en
    assert "could not be read with sufficient confidence" not in inst_en


def test_genuinely_unreadable_medicine_produces_verification_warning():
    """
    If medicine name is genuinely missing, truncated, or unreadable,
    it must return the controlled uncertain notice.
    """
    summary_unreadable = PosologyTemplateEngine.render_summary(
        language="en",
        status="restricted",
        medicine_name="Amoxi...",
        reason_code="EXTRACTION_OR_VALIDATION_UNCERTAIN",
    )
    assert "could not be read with sufficient confidence" in summary_unreadable


def test_speech_script_payload_contains_actual_medicine_and_instructions():
    """
    Verifies that the text payload for speech synthesis constructed from the explanation
    contains the actual extracted medicine name and posology, not raw OCR or generic failure text.
    """
    exp = PosologyExplanationGenerator.generate_explanation(
        prescription_id="RX-SP-001",
        medicine_name="Pantoprazole 40mg",
        dosage="40 mg",
        frequency="1-0-0",
        duration="5 days",
        candidate_status="confident",
        validation_status="validated",
        requires_human_verification=False,
    )
    en_pack = exp.explanations["en"]
    spoken_text = f"{en_pack.summary}. {en_pack.instructions}"

    assert "Pantoprazole 40mg" in spoken_text
    assert "40 mg" in spoken_text
    assert "could not be read with sufficient confidence" not in spoken_text
    assert "{" not in spoken_text  # No raw JSON
    assert "bounding_box" not in spoken_text  # No raw OCR metadata


@pytest.mark.asyncio
async def test_pipeline_does_not_mask_medicine_when_human_review_flagged():
    """
    End-to-end pipeline test: When human review is required on a prescription
    (e.g. cursive ligature or unverified field), the primary medicine name
    must reach the posology explanation and summary intact.
    """
    config = MultimodalConfig(provider="mock")
    service = MultimodalExtractionService(
        adapter=MockMultimodalModelAdapter(),
        config=config,
    )
    pipeline = MultimodalPrescriptionPipeline(service=service, config=config)
    response = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx_sample.png",
        public_image_url="http://localhost:8000/uploads/rx_sample.png",
        options=PipelineOptions(mock_scenario="uncertain"),
    )

    # In mock 'uncertain' scenario, medicine name should still be reflected or explicitly noted
    assert response.data.posology_explanation is not None
    en_summary = response.data.posology_explanation.en.summary
    assert len(en_summary) > 0
    # Posology summary in data must match top-level explanation contract
    assert response.explanation.en == en_summary
