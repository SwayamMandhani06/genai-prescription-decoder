"""
Deterministic Mock Fixtures for AURA-Rx Backend
Implements the 7 required evaluation scenarios specified in PLAN.md Section 11:
1. All Confident (Augmentin 625 Duo - Acute Bronchitis)
2. Partially Uncertain (Pan 40 - Abbreviation/Timing loop ambiguity)
3. Selective Abstain / Flagged (Omnacortil - Decimal ligature ambiguity)
4. LASA Conflict Warning (Metformin vs Metronidazole collision)
5. Full Document Abstention (Severe ink bleed / non-decipherable script)
"""

from typing import Dict, Any
from ..schemas.prescription import (
    PrescriptionAnalyzeResponse,
    FieldExtractionItem,
    LasaFlagItem,
    ValidationItem,
    MultilingualSummary,
    BoundingBox,
    ExtractedEntity,
    AlternativeCandidate,
    ValidationEvidence,
    LasaScreening,
    PosologyTimingSlot,
    PosologyLanguagePack,
    MultilingualPosology,
    DocumentTelemetry,
    PrescriptionMetadata,
    PatientInfo,
    PrescriberInfo,
    PrescriptionData,
)


def get_confident_fixture(prescription_id: str = "DEMO-RX-01", image_url: str = "/uploads/samples/sample-standard.svg") -> PrescriptionAnalyzeResponse:
    """Fixture 1: Fully Confident Extraction (Standard Antibiotic)"""
    return PrescriptionAnalyzeResponse(
        prescription_id=prescription_id,
        original_image_url=image_url,
        fields={
            "medicine_name": FieldExtractionItem(
                value="Augmentin 625 Duo",
                confidence=0.96,
                status="confident",
                candidates=["Augmentin 625 Duo", "Amoxiclav 625"],
                explanation="Cursive stroke matches canonical Amoxicillin/Clavulanate template with high geometric fidelity.",
            ),
            "dosage": FieldExtractionItem(
                value="625 mg",
                confidence=0.95,
                status="confident",
                candidates=["625 mg"],
                explanation="Numerals 6-2-5 explicitly separated with high ink-density contrast.",
            ),
            "frequency": FieldExtractionItem(
                value="1-0-1 (BD / Twice daily)",
                confidence=0.92,
                status="confident",
                candidates=["1-0-1", "BD"],
                explanation="Standard twice-daily posology glyph matching morning and bedtime timing slots.",
            ),
            "duration": FieldExtractionItem(
                value="5 days",
                confidence=0.94,
                status="confident",
                candidates=["5 days"],
                explanation="Numeral '5' and cursive 'days' ligature identified without spatial ambiguity.",
            ),
            "abbreviation": FieldExtractionItem(
                value="PC (Post Cibo / After meals)",
                confidence=0.91,
                status="confident",
                candidates=["PC"],
                explanation="Medical abbreviation 'p.c.' conforms to standard post-prandial administration guideline.",
            ),
        },
        lasa_flags=[],
        validation={
            "medicine_name": ValidationItem(
                found_in_db=True,
                source="CDSCO Drug Control Administration & US NLM RxNorm",
                matched_entity_name="Augmentin 625 Duo Tablet",
                generic_salt="Amoxicillin (500mg) + Clavulanic Acid (125mg)",
                rxnorm_cui="226829",
                cdsco_schedule="Schedule H (Prescription Drug)",
            )
        },
        explanation=MultilingualSummary(
            en="Take Augmentin 625mg twice daily after meals for 5 days. Complete the full antibiotic course.",
            hi="ऑगमेंटिन 625mg भोजन के बाद दिन में दो बार 5 दिनों के लिए लें। पूरा कोर्स समाप्त करें।",
            mr="ऑगमेंटिन ६२५ मिग्रॅ जेवणानंतर दिवसातून दोनदा ५ दिवस घ्या. डॉक्टरांनी सांगितलेला पूर्ण कोर्स संपवा.",
        ),
        requires_human_review=False,
        status="success",
        meta=PrescriptionMetadata(
            request_id="req-aura-20260927-001",
            timestamp="2026-09-27T12:00:00Z",
            processing_time_ms=640,
            model_version="aura-mock-v1.0-simulated",
            pipeline_stages_completed=7,
        ),
        document_telemetry=DocumentTelemetry(
            estimated_dpi=300,
            contrast_ratio=4.85,
            skew_angle_deg=0.4,
            illegibility_score=0.04,
            orientation="Portrait",
        ),
        data=PrescriptionData(
            accession_id=prescription_id,
            script_sample_key="rx-sample-1",
            scenario_title="Standard Antibiotic & Gastroprotective Script",
            scenario_subtitle="Illustrative demonstration scenario with clear cursive handwriting",
            difficulty_tag="Clear Handwriting",
            overall_status="VERIFIED",
            document_confidence=0.95,
            patient_info=PatientInfo(name="Demo Patient", age_gender="Adult / 42Y"),
            prescriber_info=PrescriberInfo(
                name="Example Prescriber, M.D. (Internal Medicine)",
                qualifications="Consulting Physician (Illustrative Demo)",
                registration_no="Demo Reg. No. 00000",
                clinic_name="Example Clinical Practice",
                clinic_address="Sample Clinic Address (Evaluation Demo)",
            ),
            extracted_entities=[
                ExtractedEntity(
                    field_key="medicine_name",
                    field_label="Medicine Name",
                    raw_value="Augmentin 625 Duo",
                    normalized_value="Augmentin 625 Duo",
                    confidence=0.96,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #1",
                    bounding_box=BoundingBox(x=12, y=30, width=78, height=12),
                    explanation="Cursive stroke matches canonical Amoxicillin/Clavulanate template with high geometric fidelity.",
                ),
                ExtractedEntity(
                    field_key="dosage",
                    field_label="Dosage / Strength",
                    raw_value="625 mg",
                    normalized_value="625 mg",
                    confidence=0.95,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #2",
                    bounding_box=BoundingBox(x=55, y=30, width=18, height=12),
                    explanation="Numerals 6-2-5 explicitly separated with high ink-density contrast.",
                ),
                ExtractedEntity(
                    field_key="frequency",
                    field_label="Frequency",
                    raw_value="1-0-1",
                    normalized_value="1-0-1 (BD / Twice daily)",
                    confidence=0.92,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #3",
                    bounding_box=BoundingBox(x=74, y=30, width=16, height=12),
                    explanation="Standard twice-daily posology glyph matching morning and bedtime timing slots.",
                ),
                ExtractedEntity(
                    field_key="duration",
                    field_label="Duration",
                    raw_value="5 days",
                    normalized_value="5 days",
                    confidence=0.94,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #4",
                    bounding_box=BoundingBox(x=82, y=30, width=12, height=12),
                    explanation="Numeral '5' and cursive 'days' ligature identified without spatial ambiguity.",
                ),
                ExtractedEntity(
                    field_key="abbreviation",
                    field_label="Medical Abbreviations",
                    raw_value="PC",
                    normalized_value="PC (Post Cibo / After meals)",
                    confidence=0.91,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #5",
                    bounding_box=BoundingBox(x=88, y=30, width=8, height=12),
                    explanation="Medical abbreviation 'p.c.' conforms to standard post-prandial administration guideline.",
                ),
            ],
            validation_evidence=ValidationEvidence(
                candidate_name="Augmentin 625 Duo Tablet",
                matched_entity_name="Augmentin 625 Duo Tablet",
                generic_salt="Amoxicillin (500mg) + Clavulanic Acid (125mg)",
                validation_status="cdsco_approved",
                status_badge_text="CDSCO Approved · Formulary Grounded",
                cdsco_schedule="Schedule H (Prescription Drug)",
                rxnorm_cui="226829",
                atc_code="J01CR02",
                therapeutic_class="Beta-lactam Antibacterial / Penicillin Combination",
                indications="Acute bacterial sinusitis, community-acquired pneumonia, acute exacerbation of chronic bronchitis",
                evidence_source="CDSCO Drug Control Administration & US NLM RxNorm",
                alternatives=[
                    AlternativeCandidate(name="Moxclav 625 (Sun Pharma)", generic="Amoxicillin + Clavulanic Acid", similarity_score=0.98, notes="Bioequivalent Indian branded generic."),
                    AlternativeCandidate(name="Clavam 625 (Alkem Labs)", generic="Amoxicillin + Clavulanic Acid", similarity_score=0.97, notes="Bioequivalent Indian branded generic."),
                ],
            ),
            lasa_screening=LasaScreening(
                has_warning=False,
                prescribed_candidate="Augmentin",
                confusable_counterpart="None",
                tall_man_prescribed="AUGMENTIN",
                tall_man_confused="NONE",
                similarity_score=12.0,
                similarity_type="Orthographic",
                metaphone_match=False,
                clinical_risk_summary="No significant Look-Alike Sound-Alike collision detected in CDSCO high-alert database.",
                mandated_action="Routine clinical verification by dispensing pharmacist.",
            ),
            posology_explanation=MultilingualPosology(
                en=PosologyLanguagePack(
                    summary="Take Augmentin 625mg twice daily after breakfast and dinner for 5 days.",
                    patient_instructions="Take 1 tablet in the morning after breakfast and 1 tablet at night after dinner. Swallow whole with a glass of water. Complete the full 5-day course even if you feel better.",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="Morning ☀️", icon_key="Sun", dosage_label="1 Tablet (625mg)", food_instruction="After breakfast"),
                        PosologyTimingSlot(time_slot="Afternoon 🌤️", icon_key="CloudSun", dosage_label="0 (Skip)", food_instruction="No dose"),
                        PosologyTimingSlot(time_slot="Evening 🌇", icon_key="Sunset", dosage_label="0 (Skip)", food_instruction="No dose"),
                        PosologyTimingSlot(time_slot="Night 🌙", icon_key="Moon", dosage_label="1 Tablet (625mg)", food_instruction="After dinner"),
                    ],
                    precautions=["Do not skip doses.", "Take with food to avoid gastric irritation.", "Notify doctor if severe rash or diarrhoea occurs."],
                ),
                hi=PosologyLanguagePack(
                    summary="नाश्ते और रात के खाने के बाद 5 दिनों के लिए दिन में दो बार ऑगमेंटिन 625mg लें।",
                    patient_instructions="सुबह नाश्ते के बाद 1 गोली और रात के खाने के बाद 1 गोली लें। पानी के साथ पूरी गोली निगलें। बेहतर महसूस होने पर भी 5 दिन का पूरा कोर्स खत्म करें।",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="सुबह ☀️", icon_key="Sun", dosage_label="1 गोली (625mg)", food_instruction="नाश्ते के बाद"),
                        PosologyTimingSlot(time_slot="दोपहर 🌤️", icon_key="CloudSun", dosage_label="0 (छोड़ें)", food_instruction="कोई खुराक नहीं"),
                        PosologyTimingSlot(time_slot="शाम 🌇", icon_key="Sunset", dosage_label="0 (छोड़ें)", food_instruction="कोई खुराक नहीं"),
                        PosologyTimingSlot(time_slot="रात 🌙", icon_key="Moon", dosage_label="1 गोली (625mg)", food_instruction="रात के खाने के बाद"),
                    ],
                    precautions=["दवा का समय न छोड़ें।", "पेट की खराबी से बचने के लिए भोजन के बाद लें।", "एलर्जी या दस्त होने पर तुरंत डॉक्टर से संपर्क करें।"],
                ),
                mr=PosologyLanguagePack(
                    summary="सकाळच्या नाश्त्यानंतर आणि रात्रीच्या जेवणानंतर ५ दिवस ऑगमेंटिन ६२५ मिग्रॅ दिवसातून दोनदा घ्या.",
                    patient_instructions="सकाळी नाश्त्यानंतर १ गोळी आणि रात्री जेवणानंतर १ गोळी घ्या. भरपूर पाण्यासोबत संपूर्ण गोळी गिळा. बरे वाटले तरी ५ दिवसांचा पूर्ण कोर्स संपवा.",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="सकाळी ☀️", icon_key="Sun", dosage_label="१ गोळी (६२५ मिग्रॅ)", food_instruction="नाश्त्यानंतर"),
                        PosologyTimingSlot(time_slot="दुपारी 🌤️", icon_key="CloudSun", dosage_label="० (नाही)", food_instruction="डोस नाही"),
                        PosologyTimingSlot(time_slot="संध्याकाळी 🌇", icon_key="Sunset", dosage_label="० (नाही)", food_instruction="डोस नाही"),
                        PosologyTimingSlot(time_slot="रात्री 🌙", icon_key="Moon", dosage_label="१ गोळी (६२५ मिग्रॅ)", food_instruction="जेवणानंतर"),
                    ],
                    precautions=["वेळेवर औषध घ्या.", "पोटाचा त्रास टाळण्यासाठी जेवणानंतरच गोळी घ्या.", "अंगावर पुरळ किंवा जुलाब झाल्यास डॉक्टरांशी संपर्क साधा."],
                ),
            ),
        ),
    )


def get_uncertain_fixture(prescription_id: str = "DEMO-RX-02", image_url: str = "/uploads/samples/sample-standard.svg") -> PrescriptionAnalyzeResponse:
    """Fixture 2: Partially Uncertain Extraction (Timing/Frequency Ligature Ambiguity)"""
    res = get_confident_fixture(prescription_id, image_url)
    res.status = "success"
    res.data.accession_id = prescription_id
    res.data.overall_status = "NEEDS_VERIFICATION"
    res.data.document_confidence = 0.82
    res.data.scenario_title = "Gastro-Protective & Analgesic Script (Ambiguity Demo)"
    res.data.scenario_subtitle = "Illustrative demonstration scenario with cursive abbreviation ambiguity"
    res.data.difficulty_tag = "Moderate Cursive"
    res.requires_human_review = True

    # Mark frequency as uncertain
    res.fields["frequency"] = FieldExtractionItem(
        value="1-0-1 (SOS) [Needs Verification]",
        confidence=0.62,
        status="uncertain",
        candidates=["1-0-1 (SOS)", "1-0-0 (Morning)", "PRN"],
        explanation="Cursive ligature between numeric tokens exhibits partial stroke truncation.",
        uncertainty_reason="Timing glyph ambiguous between once-daily (OD) and twice-daily (BD).",
        verification_instruction="Verify intended dosage interval against physician handwriting and clinical notes.",
    )

    for entity in res.data.extracted_entities:
        if entity.field_key == "frequency":
            entity.status = "uncertain"
            entity.confidence = 0.62
            entity.normalized_value = "1-0-1 (SOS) [Needs Verification]"
            entity.uncertainty_reason = "Trailing loop ambiguous between OD and BD."
            entity.verification_instruction = "Pharmacist audit required against physical prescription slip."

    return res


def get_lasa_fixture(prescription_id: str = "DEMO-RX-04", image_url: str = "/uploads/samples/sample-standard.svg") -> PrescriptionAnalyzeResponse:
    """Fixture 3: Look-Alike Sound-Alike Conflict (Metformin vs Metronidazole)"""
    return PrescriptionAnalyzeResponse(
        prescription_id=prescription_id,
        original_image_url=image_url,
        fields={
            "medicine_name": FieldExtractionItem(
                value="Glyciphage 500 / Metformin",
                confidence=0.84,
                status="confident",
                candidates=["Metformin 500", "Metronidazole 400"],
                explanation="Cursive stroke decoded to Metformin, but triggers orthographic/phonetic screening alert with Metronidazole.",
            ),
            "dosage": FieldExtractionItem(
                value="500 mg",
                confidence=0.92,
                status="confident",
                candidates=["500 mg"],
                explanation="Numerical strength 500 mg clear and standard for initial oral hypoglycaemic therapy.",
            ),
            "frequency": FieldExtractionItem(
                value="1-0-1 (Twice daily with major meals)",
                confidence=0.91,
                status="confident",
                candidates=["1-0-1"],
                explanation="Twice daily posology matching standard clinical glycemic protocol.",
            ),
            "duration": FieldExtractionItem(
                value="Continuous (Monthly refill x 30 days)",
                confidence=0.90,
                status="confident",
                candidates=["30 days"],
                explanation="Chronic diabetes maintenance duration verified.",
            ),
            "abbreviation": FieldExtractionItem(
                value="CC (Cum Cibo / With major meals)",
                confidence=0.89,
                status="confident",
                candidates=["CC"],
                explanation="Administration with meals recommended to minimize gastrointestinal discomfort.",
            ),
        },
        lasa_flags=[
            LasaFlagItem(
                field="medicine_name",
                conflict_with="Metronidazole",
                risk="high",
                similarity_score=82.0,
                tall_man_prescribed="metFORMIN",
                tall_man_confused="metRONIDAZOLE",
                details="High orthographic and phonetic similarity. Metformin is an oral biguanide antihyperglycemic for diabetes; Metronidazole is an antimicrobial nitroimidazole. Confusion could cause severe hypoglycemia or untreated infection.",
            )
        ],
        validation={
            "medicine_name": ValidationItem(
                found_in_db=True,
                source="CDSCO Drug Control Administration & US NLM RxNorm",
                matched_entity_name="Glyciphage 500 / Metformin 500mg",
                generic_salt="Metformin Hydrochloride (500mg)",
                rxnorm_cui="6809",
                cdsco_schedule="Schedule H (Prescription Drug)",
            )
        },
        explanation=MultilingualSummary(
            en="Take Metformin 500mg twice daily with major meals for diabetes. Ensure pharmacist dispenses Metformin, not Metronidazole.",
            hi="मधुमेह के लिए भोजन के साथ दिन में दो बार मेटफॉर्मिन 500mg लें। सुनिश्चित करें कि फार्मासिस्ट मेटफॉर्मिन दे, मेट्रोनिडाजोल नहीं।",
            mr="मधुमेहासाठी जेवणासोबत दिवसातून दोनदा मेटफॉर्मिन ५०० मिग्रॅ घ्या. फार्मासिस्टकडून मेटफॉर्मिनच असल्याची खात्री करा.",
        ),
        requires_human_review=True,
        status="abstain",
        meta=PrescriptionMetadata(
            request_id="req-aura-20260927-004",
            timestamp="2026-09-27T12:00:00Z",
            processing_time_ms=910,
            model_version="aura-mock-v1.0-simulated",
            pipeline_stages_completed=7,
        ),
        document_telemetry=DocumentTelemetry(
            estimated_dpi=260,
            contrast_ratio=4.12,
            skew_angle_deg=0.8,
            illegibility_score=0.12,
            orientation="Portrait",
        ),
        data=PrescriptionData(
            accession_id=prescription_id,
            script_sample_key="rx-sample-2",
            scenario_title="Demo Case 04 (Look-Alike Sound-Alike Similarity Example)",
            scenario_subtitle="Illustrative orthographic & phonetic similarity flag between Metformin and Metronidazole",
            difficulty_tag="LASA Similarity",
            overall_status="SAFETY_ALERT",
            document_confidence=0.85,
            patient_info=PatientInfo(name="Demo Patient", age_gender="Adult / 56Y"),
            prescriber_info=PrescriberInfo(
                name="Example Prescriber, M.D.",
                qualifications="Consulting Physician (Illustrative Demo)",
                registration_no="Demo Reg. No. 00000",
                clinic_name="Example Clinical Practice",
                clinic_address="Demo Medical Center · Illustrative Record",
            ),
            extracted_entities=[
                ExtractedEntity(
                    field_key="medicine_name",
                    field_label="Medicine Name",
                    raw_value="Metformin 500",
                    normalized_value="Glyciphage 500 / Metformin",
                    confidence=0.84,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #1",
                    bounding_box=BoundingBox(x=12, y=32, width=80, height=16),
                    explanation="Cursive stroke decoded to Metformin, but triggers orthographic/phonetic screening alert with Metronidazole.",
                ),
                ExtractedEntity(
                    field_key="dosage",
                    field_label="Dosage / Strength",
                    raw_value="500 mg",
                    normalized_value="500 mg",
                    confidence=0.92,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #2",
                    bounding_box=BoundingBox(x=55, y=32, width=18, height=14),
                    explanation="Numerical strength 500 mg clear and standard for initial oral hypoglycaemic therapy.",
                ),
                ExtractedEntity(
                    field_key="frequency",
                    field_label="Frequency",
                    raw_value="1-0-1",
                    normalized_value="1-0-1 (Twice daily with major meals)",
                    confidence=0.91,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #3",
                    bounding_box=BoundingBox(x=74, y=32, width=16, height=14),
                    explanation="Twice daily posology matching standard clinical glycemic protocol.",
                ),
                ExtractedEntity(
                    field_key="duration",
                    field_label="Duration",
                    raw_value="Continuous (30d refill)",
                    normalized_value="Continuous (Monthly refill x 30 days)",
                    confidence=0.90,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #4",
                    bounding_box=BoundingBox(x=80, y=32, width=12, height=14),
                    explanation="Chronic diabetes maintenance duration verified.",
                ),
                ExtractedEntity(
                    field_key="abbreviation",
                    field_label="Medical Abbreviations",
                    raw_value="CC",
                    normalized_value="CC (Cum Cibo / With major meals)",
                    confidence=0.89,
                    status="confident",
                    stroke_source="Prescription Line 01 · Pen Stroke #5",
                    bounding_box=BoundingBox(x=88, y=32, width=8, height=14),
                    explanation="Administration with meals recommended to minimize gastrointestinal discomfort.",
                ),
            ],
            validation_evidence=ValidationEvidence(
                candidate_name="Metformin Hydrochloride 500mg Tablet",
                matched_entity_name="Glyciphage 500 / Metformin 500mg",
                generic_salt="Metformin Hydrochloride (500mg)",
                validation_status="cdsco_approved",
                status_badge_text="CDSCO Approved · Formulary Grounded",
                cdsco_schedule="Schedule H (Prescription Drug)",
                rxnorm_cui="6809",
                atc_code="A10BA02",
                therapeutic_class="Biguanide Antihyperglycemic / Type 2 Diabetes Care",
                indications="Type 2 diabetes mellitus glycemic management in adults",
                evidence_source="CDSCO Drug Control Administration & US NLM RxNorm",
                alternatives=[
                    AlternativeCandidate(name="Glycomet 500 (USV)", generic="Metformin 500mg", similarity_score=0.96, notes="Standard bioequivalent biguanide."),
                    AlternativeCandidate(name="Metrogyl 400 (J.B. Chemicals)", generic="Metronidazole 400mg (CRITICAL LASA COLLISION)", similarity_score=0.82, notes="Antimicrobial agent. Clinician must verify patient has diabetes, NOT amoebic dysentery."),
                ],
            ),
            lasa_screening=LasaScreening(
                has_warning=True,
                prescribed_candidate="Metformin",
                confusable_counterpart="Metronidazole",
                tall_man_prescribed="metFORMIN",
                tall_man_confused="metRONIDAZOLE",
                similarity_score=82.0,
                similarity_type="Orthographic & Phonetic",
                metaphone_match=True,
                clinical_risk_summary="High phonetic and cursive visual ligature similarity. Metformin is an oral biguanide antihyperglycemic for diabetes; Metronidazole is an antimicrobial nitroimidazole for amoebic infections. Confusion could cause severe hypoglycemia or untreated infection.",
                mandated_action="The system detected possible similarity. It has NOT determined the correct medicine. Clinician and dispensing pharmacist confirmation required before dispensing.",
            ),
            posology_explanation=MultilingualPosology(
                en=PosologyLanguagePack(
                    summary="Take Metformin 500mg twice daily with major meals for diabetes.",
                    patient_instructions="Take 1 tablet with breakfast and 1 tablet with dinner. Always take with or immediately after food to minimize stomach upset. Confirm with pharmacist that this is Metformin (for blood sugar) and NOT Metronidazole.",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="Morning ☀️", icon_key="Sun", dosage_label="1 Tablet (500mg)", food_instruction="With breakfast"),
                        PosologyTimingSlot(time_slot="Afternoon 🌤️", icon_key="CloudSun", dosage_label="0 (Skip)", food_instruction="No dose"),
                        PosologyTimingSlot(time_slot="Evening 🌇", icon_key="Sunset", dosage_label="0 (Skip)", food_instruction="No dose"),
                        PosologyTimingSlot(time_slot="Night 🌙", icon_key="Moon", dosage_label="1 Tablet (500mg)", food_instruction="With dinner"),
                    ],
                    precautions=["Ensure pharmacist dispenses Metformin for blood sugar, not Metronidazole.", "Do not take on an empty stomach.", "Carry glucose tablets in case of hypoglycemia."],
                ),
                hi=PosologyLanguagePack(
                    summary="मधुमेह के लिए भोजन के साथ दिन में दो बार मेटफॉर्मिन 500mg लें।",
                    patient_instructions="नाश्ते के साथ 1 गोली और रात के खाने के साथ 1 गोली लें। पेट की परेशानी कम करने के लिए हमेशा भोजन के साथ लें। फार्मासिस्ट से पुष्टि करें कि यह मेटफॉर्मिन है, मेट्रोनिडाजोल नहीं।",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="सुबह ☀️", icon_key="Sun", dosage_label="1 गोली (500mg)", food_instruction="नाश्ते के साथ"),
                        PosologyTimingSlot(time_slot="दोपहर 🌤️", icon_key="CloudSun", dosage_label="0 (छोड़ें)", food_instruction="कोई खुराक नहीं"),
                        PosologyTimingSlot(time_slot="शाम 🌇", icon_key="Sunset", dosage_label="0 (छोड़ें)", food_instruction="कोई खुराक नहीं"),
                        PosologyTimingSlot(time_slot="रात 🌙", icon_key="Moon", dosage_label="1 गोली (500mg)", food_instruction="रात के खाने के साथ"),
                    ],
                    precautions=["फार्मासिस्ट से पुष्टि करें कि यह मेटफॉर्मिन है।", "खाली पेट न लें।", "कम ब्लड शुगर के लक्षणों पर ध्यान दें।"],
                ),
                mr=PosologyLanguagePack(
                    summary="मधुमेहासाठी जेवणासोबत दिवसातून दोनदा मेटफॉर्मिन ५०० मिग्रॅ घ्या.",
                    patient_instructions="सकाळी नाश्त्यासोबत १ गोळी आणि रात्री जेवणासोबत १ गोळी घ्या. पोटाचा त्रास टाळण्यासाठी नेहमी जेवणानंतर लगेच घ्या. फार्मासिस्टकडून मेटफॉर्मिनच असल्याची खात्री करा.",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="सकाळी ☀️", icon_key="Sun", dosage_label="१ गोळी (५०० मिग्रॅ)", food_instruction="नाश्त्यासोबत"),
                        PosologyTimingSlot(time_slot="दुपारी 🌤️", icon_key="CloudSun", dosage_label="० (नाही)", food_instruction="डोस नाही"),
                        PosologyTimingSlot(time_slot="संध्याकाळी 🌇", icon_key="Sunset", dosage_label="० (नाही)", food_instruction="डोस नाही"),
                        PosologyTimingSlot(time_slot="रात्री 🌙", icon_key="Moon", dosage_label="१ गोळी (५०० मिग्रॅ)", food_instruction="जेवणासोबत"),
                    ],
                    precautions=["फार्मासिस्टकडून मेटफॉर्मिनच असल्याची खात्री करा.", "उपाशी पोटी घेऊ नका.", "रक्तातील साखर कमी झाल्यास ग्लुकोज जवळ ठेवा."],
                ),
            ),
        ),
    )


def get_abstained_fixture(prescription_id: str = "DEMO-RX-05", image_url: str = "/uploads/samples/sample-standard.svg") -> PrescriptionAnalyzeResponse:
    """Fixture 4: Full Document Clinical Abstention (Severe Stroke Ambiguity)"""
    return PrescriptionAnalyzeResponse(
        prescription_id=prescription_id,
        original_image_url=image_url,
        fields={
            "medicine_name": FieldExtractionItem(
                value="UNCONFIRMED · Model Abstained",
                confidence=0.28,
                status="flagged",
                candidates=["Model Abstained"],
                explanation="Severe cursive overlapping ink and non-decipherable strokes trigger safety policy.",
                uncertainty_reason="Severe stroke overlap, non-standard cursive abbreviations, ink bleed.",
                verification_instruction="Direct pharmacist audit or contacting prescriber required. Do not dispense automatically.",
            ),
            "dosage": FieldExtractionItem(
                value="UNCONFIRMED · Model Abstained",
                confidence=0.22,
                status="flagged",
                candidates=["Model Abstained"],
                explanation="Degraded stroke contours prevent safe numerical extraction.",
                uncertainty_reason="Numerical ligature degraded beyond diagnostic threshold.",
                verification_instruction="Verify dosage strength directly against prescriber records.",
            ),
            "frequency": FieldExtractionItem(
                value="UNCONFIRMED · Model Abstained",
                confidence=0.25,
                status="flagged",
                candidates=["Model Abstained"],
                explanation="Timing loop indistinguishable between daily, bidaily, or prn.",
                uncertainty_reason="Unresolvable cursive timing loop.",
                verification_instruction="Obtain verbal or digitized confirmation of posology from prescriber.",
            ),
            "duration": FieldExtractionItem(
                value="UNCONFIRMED · Model Abstained",
                confidence=0.30,
                status="flagged",
                candidates=["Model Abstained"],
                explanation="Day count obscured by ink smear.",
                uncertainty_reason="Paper fold and ink bleed across duration field.",
                verification_instruction="Check physical prescription.",
            ),
            "abbreviation": FieldExtractionItem(
                value="UNCONFIRMED · Model Abstained",
                confidence=0.20,
                status="flagged",
                candidates=["Model Abstained"],
                explanation="Abbreviation loop non-standard.",
                uncertainty_reason="Unrecognized handwriting shorthand.",
                verification_instruction="Confirm clinical notes.",
            ),
        },
        lasa_flags=[],
        validation={
            "medicine_name": ValidationItem(
                found_in_db=False,
                source="CDSCO Formulary · Automated Matching Abstained",
                matched_entity_name="Abstained by Safety Engine",
                generic_salt="Unverified",
                rxnorm_cui="None",
                cdsco_schedule="Unverified",
            )
        },
        explanation=MultilingualSummary(
            en="SYSTEM ABSTAINED: The handwriting is too ambiguous or degraded for safe automated interpretation. Please consult your doctor or pharmacist.",
            hi="प्रणाली ने व्याख्या रोक दी है: लिखावट बहुत अस्पष्ट है। कृपया अपने डॉक्टर या फार्मासिस्ट से परामर्श लें।",
            mr="हस्ताक्षर अत्यंत अस्पष्ट असल्याने प्रणालीने अर्थ लावणे थांबवले आहे. कृपया डॉक्टरांचा किंवा फार्मासिस्टचा सल्ला घ्या.",
        ),
        requires_human_review=True,
        status="abstain",
        meta=PrescriptionMetadata(
            request_id="req-aura-20260927-005",
            timestamp="2026-09-27T12:00:00Z",
            processing_time_ms=520,
            model_version="aura-mock-v1.0-simulated",
            pipeline_stages_completed=4,
        ),
        document_telemetry=DocumentTelemetry(
            estimated_dpi=180,
            contrast_ratio=1.85,
            skew_angle_deg=-3.4,
            illegibility_score=0.78,
            orientation="Portrait",
        ),
        data=PrescriptionData(
            accession_id=prescription_id,
            script_sample_key="rx-sample-3",
            scenario_title="Severe Stroke Ambiguity & Paper Degradation",
            scenario_subtitle="Illustrative scenario of autonomous abstention on non-decipherable script",
            difficulty_tag="Severe Ambiguity",
            overall_status="ABSTAINED",
            document_confidence=0.28,
            patient_info=PatientInfo(name="Demo Patient (Evaluation)", age_gender="Demo Record"),
            prescriber_info=PrescriberInfo(
                name="Example Prescriber, M.D.",
                qualifications="Consulting Specialist (Illustrative Demo)",
                registration_no="Demo Reg. No. 00000",
                clinic_name="Clinical Practice",
                clinic_address="Medical Center Record",
            ),
            extracted_entities=[
                ExtractedEntity(
                    field_key="medicine_name",
                    field_label="Medicine Name",
                    raw_value="[ILLEGIBLE STROKE]",
                    normalized_value="UNCONFIRMED · Model Abstained",
                    confidence=0.28,
                    status="abstained",
                    stroke_source="Line 01 · Indeterminate Cursive",
                    bounding_box=BoundingBox(x=15, y=35, width=70, height=18),
                    explanation="Severe cursive overlapping ink and non-decipherable strokes trigger safety policy.",
                    uncertainty_reason="Severe stroke overlap, non-standard cursive abbreviations, ink bleed.",
                    verification_instruction="Direct pharmacist audit or contacting prescriber required. Do not dispense automatically.",
                ),
                ExtractedEntity(
                    field_key="dosage",
                    field_label="Dosage / Strength",
                    raw_value="[ILLEGIBLE NUMERAL]",
                    normalized_value="UNCONFIRMED · Model Abstained",
                    confidence=0.22,
                    status="abstained",
                    stroke_source="Line 01 · Degraded Ligature",
                    bounding_box=BoundingBox(x=55, y=35, width=20, height=18),
                    explanation="Degraded stroke contours prevent safe numerical extraction.",
                    uncertainty_reason="Numerical ligature degraded beyond diagnostic threshold.",
                    verification_instruction="Verify dosage strength directly against prescriber records.",
                ),
                ExtractedEntity(
                    field_key="frequency",
                    field_label="Frequency",
                    raw_value="[AMBIGUOUS LOOP]",
                    normalized_value="UNCONFIRMED · Model Abstained",
                    confidence=0.25,
                    status="abstained",
                    stroke_source="Line 01 · Ambiguous Loop",
                    bounding_box=BoundingBox(x=75, y=35, width=15, height=18),
                    explanation="Timing loop indistinguishable between daily, bidaily, or prn.",
                    uncertainty_reason="Unresolvable cursive timing loop.",
                    verification_instruction="Obtain verbal or digitized confirmation of posology from prescriber.",
                ),
            ],
            validation_evidence=ValidationEvidence(
                candidate_name="Indeterminate Formulation",
                matched_entity_name="Abstained by Safety Engine",
                generic_salt="Unverified",
                validation_status="unverified",
                status_badge_text="Autonomous Abstention Active · Unverified",
                cdsco_schedule="Unverified",
                rxnorm_cui="None",
                atc_code="None",
                therapeutic_class="Unclassified due to severe ambiguity",
                indications="Prescription text could not be verified against formulary standards.",
                evidence_source="CDSCO Formulary Engine (Safety Threshold Triggered)",
                alternatives=[],
            ),
            lasa_screening=LasaScreening(
                has_warning=False,
                prescribed_candidate="Uncertain",
                confusable_counterpart="None",
                tall_man_prescribed="ABSTAINED",
                tall_man_confused="NONE",
                similarity_score=0.0,
                similarity_type="Orthographic",
                metaphone_match=False,
                clinical_risk_summary="Automated decoding suspended due to high error potential.",
                mandated_action="Prescription must be referred to a human pharmacist for physical inspection or electronic reissue.",
            ),
            posology_explanation=MultilingualPosology(
                en=PosologyLanguagePack(
                    summary="Autonomous Abstention Protocol Active: The handwriting on this prescription could not be deciphered with high certainty.",
                    patient_instructions="Do not take any medication based on this automated scan. Please contact your prescribing physician or bring the physical paper to your pharmacist for verification.",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="All Times ⚠️", icon_key="AlertCircle", dosage_label="DO NOT DISPENSE", food_instruction="Manual clinical audit required"),
                    ],
                    precautions=["Do not self-medicate.", "Consult your prescribing doctor for a printed prescription slip.", "Bring physical paper to your pharmacy."],
                ),
                hi=PosologyLanguagePack(
                    summary="स्वायत्त अस्वीकृति प्रोटोकॉल सक्रिय: इस पर्चे की लिखावट को पर्याप्त निश्चितता के साथ नहीं पढ़ा जा सका।",
                    patient_instructions="इस स्वचालित स्कैन के आधार पर कोई भी दवा न लें। कृपया अपने डॉक्टर से संपर्क करें या सत्यापन के लिए फार्मासिस्ट के पास जाएं।",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="सभी समय ⚠️", icon_key="AlertCircle", dosage_label="दवा न दें", food_instruction="फार्मासिस्ट द्वारा जांच आवश्यक"),
                    ],
                    precautions=["खुद से दवा न लें।", "स्पष्ट मुद्रित पर्चे के लिए डॉक्टर से परामर्श करें।"],
                ),
                mr=PosologyLanguagePack(
                    summary="स्वायत्त नकार प्रोटोकॉल सक्रिय: या प्रिस्क्रिप्शनवरील हस्ताक्षर निश्चिततेने वाचता आले नाही.",
                    patient_instructions="या स्कॅनवर आधारित कोणतेही औषध घेऊ नका. कृपया डॉक्टरांशी संपर्क साधा किंवा मूळ कागद फार्मासिस्टकडे न्या.",
                    daily_schedule=[
                        PosologyTimingSlot(time_slot="सर्व वेळ ⚠️", icon_key="AlertCircle", dosage_label="औषध देऊ नका", food_instruction="फार्मासिस्ट तपासणी आवश्यक"),
                    ],
                    precautions=["स्वतःहून औषध घेऊ नका.", "डॉक्टरांकडून स्पष्ट प्रिस्क्रिप्शन मागवून घ्या."],
                ),
            ),
        ),
    )
