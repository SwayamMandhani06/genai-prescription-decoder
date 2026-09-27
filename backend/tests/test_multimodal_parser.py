"""
Unit Tests for Phase 6 Multimodal Response Parser
"""

import json
import pytest
from backend.app.multimodal.parser import (
    strip_json_code_fences,
    parse_multimodal_response,
    MultimodalParseError,
    parse_raw_field,
)


def test_strip_json_code_fences():
    """Verifies that markdown code fence wrappers are stripped safely."""
    raw = "```json\n{\"medicines\": []}\n```"
    assert strip_json_code_fences(raw) == '{"medicines": []}'

    raw2 = "```\n{\"medicines\": []}\n```"
    assert strip_json_code_fences(raw2) == '{"medicines": []}'

    raw3 = '{"medicines": []}'
    assert strip_json_code_fences(raw3) == '{"medicines": []}'


def test_parse_raw_field_structured_and_unstructured():
    """Verifies parsing of structured dicts and scalar string/null inputs."""
    # Null field -> absence handled with status 'uncertain', presence 'absent', extraction_state 'missing'
    f_null = parse_raw_field(None, "dosage")
    assert f_null.value is None
    assert f_null.status == "uncertain"
    assert f_null.presence == "absent"
    assert f_null.extraction_state == "missing"
    assert f_null.evidence.evidence_type == "image_level"

    # Plain string -> confident, present, extracted
    f_str = parse_raw_field("500 mg", "dosage")
    assert f_str.value == "500 mg"
    assert f_str.status == "confident"
    assert f_str.presence == "present"
    assert f_str.extraction_state == "extracted"

    # Full structured dictionary
    f_dict = parse_raw_field(
        {
            "value": "Amoxicillin",
            "status": "uncertain",
            "candidates": ["Amoxicillin", "Ampicillin"],
            "explanation": "Cursive terminal loop ambiguous",
            "bounding_box": {"x": 10.0, "y": 20.0, "width": 30.0, "height": 8.0},
        },
        "medicine_name",
    )
    assert f_dict.value == "Amoxicillin"
    assert f_dict.status == "uncertain"
    assert f_dict.presence == "present"
    assert f_dict.extraction_state == "ambiguous"
    assert "Ampicillin" in f_dict.candidates
    assert f_dict.evidence.evidence_type == "visual_region"
    assert f_dict.evidence.region.x == 10.0


def test_parse_multimodal_response_valid_multiple_medicines():
    """Verifies parsing of multi-medicine response with code fence stripping."""
    payload = """```json
    {
      "medicines": [
        {
          "medicine_name": {"value": "Paracetamol", "status": "confident"},
          "dosage": {"value": "650 mg", "status": "confident"},
          "frequency": {"value": "1-1-1", "status": "confident"},
          "duration": {"value": "3 days", "status": "confident"},
          "abbreviations": ["TDS"]
        },
        {
          "medicine_name": {"value": "Cetirizine", "status": "confident"},
          "dosage": {"value": "10 mg", "status": "confident"},
          "frequency": {"value": "0-0-1", "status": "confident"},
          "duration": {"value": "5 days", "status": "confident"},
          "abbreviations": ["HS"]
        }
      ],
      "requires_human_review": false
    }
    ```"""

    res = parse_multimodal_response(payload)
    assert len(res["medicines"]) == 2
    assert res["requires_human_review"] is False
    assert res["medicines"][0].medicine_name.value == "Paracetamol"
    assert res["medicines"][1].medicine_name.value == "Cetirizine"
    assert res["medicines"][0].abbreviations == ["TDS"]
    assert res["medicines"][1].abbreviations == ["HS"]


def test_parse_multimodal_response_malformed_json_raises():
    """Verifies that non-JSON output raises MultimodalParseError."""
    with pytest.raises(MultimodalParseError):
        parse_multimodal_response("NOT A VALID JSON STREAM <<>>")

    with pytest.raises(MultimodalParseError):
        parse_multimodal_response("")


def test_parse_multimodal_response_empty_medicines():
    """Verifies that an empty extraction result is parsed without error."""
    raw = json.dumps({"medicines": [], "requires_human_review": True})
    res = parse_multimodal_response(raw)
    assert len(res["medicines"]) == 0
    assert res["requires_human_review"] is True
