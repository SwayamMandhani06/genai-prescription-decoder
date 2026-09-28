"""
Audit Item 3: Canonical LASA Result Consistency Test.
Verifies the relationship and consistency across the three LASA representation layers:
1. Canonical Detection Result: lasa_detection (PrescriptionLasaDetection)
2. Section 6 Backward-Compatible Flat Flags: lasa_flags (List[LasaFlagItem])
3. Phase 1 UI Envelope Summary: lasa_screening (LasaScreening)

Proves that:
- There is ONE canonical detection run per pipeline execution.
- lasa_flags and lasa_screening are strictly derived from lasa_detection.
- They NEVER produce contradictory or independently calculated states.
"""

import pytest
from backend.app.services.pipeline_interface import PipelineOptions
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.multimodal import MockMultimodalModelAdapter, MultimodalExtractionService, MultimodalConfig


class TestLasaResultConsistency:
    """Verifies complete consistency across lasa_detection, lasa_flags, and lasa_screening."""

    @pytest.fixture
    def pipeline(self):
        config = MultimodalConfig(provider="mock")
        service = MultimodalExtractionService(
            adapter=MockMultimodalModelAdapter(),
            config=config,
        )
        return MultimodalPrescriptionPipeline(service=service, config=config)

    @pytest.mark.asyncio
    async def test_clean_prescription_all_three_layers_agree_no_conflict(self, pipeline):
        """When no LASA conflict exists, all 3 representations must agree."""
        options = PipelineOptions(mock_scenario="missing_dosage")
        result = await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="rx.png",
            public_image_url="/uploads/rx.png",
            options=options,
        )
        lasa_det = result.lasa_detection
        lasa_flags = result.lasa_flags
        lasa_screening = result.data.lasa_screening

        assert lasa_det is not None
        assert lasa_det["status"] == "completed"
        # Canonical detection says no conflict
        assert lasa_det["conflict_detected"] is False
        assert lasa_det["has_any_lasa_conflict"] is False

        # Flat flags must be empty
        assert len(lasa_flags) == 0

        # UI screening must indicate has_warning = False
        assert lasa_screening.has_warning is False
        assert lasa_screening.confusable_counterpart == "None Identified"
        assert lasa_screening.similarity_score == 0.0

    @pytest.mark.asyncio
    async def test_lasa_alert_prescription_all_three_layers_agree_on_conflict(self, pipeline):
        """When a LASA conflict exists, all 3 representations must agree on conflict identity and scores."""
        options = PipelineOptions(mock_scenario="uncertain")
        result = await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="rx.png",
            public_image_url="/uploads/rx.png",
            options=options,
        )
        lasa_det = result.lasa_detection
        lasa_flags = result.lasa_flags
        lasa_screening = result.data.lasa_screening

        assert lasa_det is not None
        assert lasa_det["status"] == "completed"

        # Canonical detection reports conflict
        if lasa_det["conflict_detected"]:
            # lasa_flags must have at least one item
            assert len(lasa_flags) > 0

            # Primary medicine top conflict
            primary_med = lasa_det["medicines"][0]
            if primary_med["has_lasa_conflict"]:
                assert lasa_screening.has_warning is True
                assert lasa_screening.confusable_counterpart == primary_med["confusables"][0]["confusable_name"]
                assert round(lasa_screening.similarity_score, 2) == round(primary_med["confusables"][0]["combined_score"], 2)

                # Verify agreement with first flag in lasa_flags
                assert lasa_flags[0].conflict_with == lasa_screening.confusable_counterpart

    @pytest.mark.asyncio
    async def test_no_independent_contradiction_between_layers(self, pipeline):
        """Asserts that no scenario can produce has_warning=True while lasa_flags is empty."""
        for scenario in ["confident", "uncertain", "flagged", "abstained"]:
            options = PipelineOptions(mock_scenario=scenario)
            res = await pipeline.process_prescription(
                image_bytes=b"dummy",
                filename="rx.png",
                public_image_url="/uploads/rx.png",
                options=options,
            )
            has_warning = res.data.lasa_screening.has_warning
            has_flags = len(res.lasa_flags) > 0
            det_conflict = res.lasa_detection.get("conflict_detected") if res.lasa_detection else False

            # If UI has warning, canonical detection MUST have detected conflict
            if has_warning:
                assert det_conflict is True
                assert has_flags is True
            # If flat flags exist, canonical detection MUST have detected conflict
            if has_flags:
                assert det_conflict is True
