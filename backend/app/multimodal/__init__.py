"""
Phase 6: Multimodal Vision-Language Extraction Package
Provides typed contracts, vision adapters, parsing, and orchestration services.
"""

from .config import MultimodalConfig
from .schemas import (
    BoundingBox,
    VisualEvidence,
    ExtractedField,
    ExtractedMedicine,
    ModelMetadata,
    PrescriptionExtractionResult,
    FieldStatus,
    FieldPresence,
    ExtractionState,
    EvidenceType,
    EvidenceSource,
)
from .prompts import SYSTEM_INSTRUCTION_V1, USER_INSTRUCTION_V1
from .evidence import resolve_visual_evidence
from .parser import parse_multimodal_response, MultimodalParseError
from .postprocess import (
    finalize_extraction_result,
    postprocess_extracted_medicine,
    postprocess_extracted_field,
    build_aggregate_fields,
)
from .adapter import (
    IMultimodalModelAdapter,
    GeminiMultimodalAdapter,
    MockMultimodalModelAdapter,
)
from .service import MultimodalExtractionService

__all__ = [
    "MultimodalConfig",
    "BoundingBox",
    "VisualEvidence",
    "ExtractedField",
    "ExtractedMedicine",
    "ModelMetadata",
    "PrescriptionExtractionResult",
    "FieldStatus",
    "FieldPresence",
    "ExtractionState",
    "EvidenceType",
    "EvidenceSource",
    "SYSTEM_INSTRUCTION_V1",
    "USER_INSTRUCTION_V1",
    "resolve_visual_evidence",
    "parse_multimodal_response",
    "MultimodalParseError",
    "finalize_extraction_result",
    "postprocess_extracted_medicine",
    "postprocess_extracted_field",
    "build_aggregate_fields",
    "IMultimodalModelAdapter",
    "GeminiMultimodalAdapter",
    "MockMultimodalModelAdapter",
    "MultimodalExtractionService",
]
