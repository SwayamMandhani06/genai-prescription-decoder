import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.dataset.manifest import (
    DatasetManifest,
    DatasetSourceEntry,
    ProvenanceRecord,
    SourceVerificationStatus,
    LicenseCategory,
    save_manifest
)

sources = [
    DatasetSourceEntry(
        dataset_id="bd-handwritten-rx",
        name="Doctor's Handwritten Prescription BD Dataset",
        description="Real-world scanned handwritten prescriptions from outpatient healthcare facilities in Bangladesh.",
        document_type="Prescription pad document scan",
        handwriting_characteristics="Real physician cursive Latin handwriting, rapid ligatures, variable pen strokes",
        language_script="Latin with occasional Bengali clinical notes",
        available_annotations="Document-level image scans, raw clinic transcriptions",
        verification_status=SourceVerificationStatus.VERIFIED_PUBLIC,
        access_method="Mendeley Data public download / Academic DOI access",
        known_limitations=[
            "Variable scan resolution across clinics (72 to 300 DPI)",
            "No native token-level bounding polygon coordinates in raw release",
            "Occasional regional pharmaceutical trade names specific to South Asia"
        ],
        relevance="Real-world cursive variability benchmark for Phase 5 OCR baseline and Phase 6 extraction.",
        provenance=ProvenanceRecord(
            source_url="https://doi.org/10.17632/r3gmvg62cw.1",
            provider_organization="BRAC University and RUET Biomedical Informatics Team",
            retrieval_date="2026-09-27T00:00:00Z",
            license="CC-BY-4.0",
            license_category=LicenseCategory.OPEN_DATASET_LICENSE,
            permitted_usage="Academic research, public scientific evaluation, and publication",
            attribution_requirements="Cite Jahan et al. (2021) and Mendeley Data repository DOI",
            citation="Jahan, N. et al. (2021). Doctor's Handwritten Prescription BD Dataset. Mendeley Data, V1, doi: 10.17632/r3gmvg62cw.1",
            dataset_version="1.0"
        )
    ),
    DatasetSourceEntry(
        dataset_id="cdsco-approved-drugs",
        name="CDSCO Approved Drug Formulations & Fixed Dose Combinations",
        description="Official gazette list of approved active pharmaceutical ingredients, strengths, and fixed-dose combinations in India.",
        document_type="Regulatory gazette and drug formulary tables",
        handwriting_characteristics="Typeset regulatory pharmacopeia tables",
        language_script="English (Latin terminology)",
        available_annotations="Generic name, strength, dosage form, indication, approval date",
        verification_status=SourceVerificationStatus.VERIFIED_REGULATORY,
        access_method="Open Government Data (OGD) Platform India / CDSCO portal",
        known_limitations=[
            "Covers authorized marketed formulations; does not contain colloquial handwriting slurs"
        ],
        relevance="Authoritative knowledge graph ground truth for Phase 7 RAG validation and Indian posology compliance.",
        provenance=ProvenanceRecord(
            source_url="https://cdsco.gov.in",
            provider_organization="Central Drugs Standard Control Organisation, Ministry of Health and Family Welfare, Govt of India",
            retrieval_date="2026-09-27T00:00:00Z",
            license="Open Government Data License - India",
            license_category=LicenseCategory.STATUTORY_GOVERNMENT_OPEN_DATA,
            permitted_usage="Public statutory use, health informatics research, clinical reference",
            attribution_requirements="Reference Central Drugs Standard Control Organisation, Govt of India",
            citation="CDSCO (2024). List of Approved New Drugs and Fixed Dose Combinations in India. Directorate General of Health Services.",
            dataset_version="2024.1"
        )
    ),
    DatasetSourceEntry(
        dataset_id="nlm-rxnorm",
        name="NLM RxNorm Standard Clinical Drug Nomenclature",
        description="Standard clinical drug vocabulary linking active ingredients, clinical dose forms, and concept unique identifiers (RxCUI).",
        document_type="Normalized clinical drug terminology graph",
        handwriting_characteristics="Standardized clinical typeset ontology",
        language_script="English (Latin medical terminology)",
        available_annotations="Active ingredients, clinical drug components, dose forms, brand aliases",
        verification_status=SourceVerificationStatus.VERIFIED_REGULATORY,
        access_method="UMLS Terminology Services / NLM Open Data",
        known_limitations=[
            "Primarily reflects US clinical pharmacopeia; international trade brands require mapping to Indian CDSCO names"
        ],
        relevance="Standardized posology taxonomy and RxCUI concept grounding for Phase 7.",
        provenance=ProvenanceRecord(
            source_url="https://www.nlm.nih.gov/research/umls/rxnorm/",
            provider_organization="National Library of Medicine, National Institutes of Health, USA",
            retrieval_date="2026-09-27T00:00:00Z",
            license="UMLS Metathesaurus License (Free for research/clinical applications)",
            license_category=LicenseCategory.CLINICAL_TERMINOLOGY_LICENSE,
            permitted_usage="Research, academic development, and clinical decision support evaluation",
            attribution_requirements="RxNorm is provided courtesy of the U.S. National Library of Medicine",
            citation="Nelson, S. J. et al. (2011). Normalized names for clinical drugs: RxNorm at 6 years. J Am Med Inform Assoc, 18(4):441-448.",
            dataset_version="2024-08"
        )
    ),
    DatasetSourceEntry(
        dataset_id="ismp-fda-lasa",
        name="ISMP List of Look-Alike Sound-Alike (LASA) Drug Names",
        description="Authoritative safety registry of confusable medication pairs prone to dispensing errors, with recommended TALL MAN lettering.",
        document_type="Clinical safety alert pair tables",
        handwriting_characteristics="Typeset confusable drug pair tables with orthographic emphasis",
        language_script="English (Latin pharmacology)",
        available_annotations="Confusable drug pair, confusion mechanism (sound/look), recommended Tall Man lettering",
        verification_status=SourceVerificationStatus.VERIFIED_REGULATORY,
        access_method="ISMP safety guidance portal",
        known_limitations=[
            "Specific to medication pairs; does not include full prescription context"
        ],
        relevance="Gold-standard evaluation benchmark for Phase 10 LASA detection and Tall Man formatting.",
        provenance=ProvenanceRecord(
            source_url="https://www.ismp.org/recommendations/look-alike-sound-alike-list",
            provider_organization="Institute for Safe Medication Practices (ISMP)",
            retrieval_date="2026-09-27T00:00:00Z",
            license="Public Clinical Safety Guidance",
            license_category=LicenseCategory.CLINICAL_SAFETY_GUIDANCE,
            permitted_usage="Educational and research evaluation for medical error prevention",
            attribution_requirements="Acknowledge ISMP Look-Alike Sound-Alike guidelines",
            citation="ISMP (2023). ISMP's List of Look-Alike Drug Names with Recommended Tall Man Letters. Horsham, PA.",
            dataset_version="2023-R1"
        )
    ),
    DatasetSourceEntry(
        dataset_id="iam-handwriting-database",
        name="IAM Handwriting Database (Form & Line subset)",
        description="Standard research corpus of English handwritten forms and sentences with word and line bounding boxes.",
        document_type="Handwritten sentence and form sheets",
        handwriting_characteristics="Diverse English handwriting styles from over 500 individual writers",
        language_script="English (Latin script)",
        available_annotations="Word bounding boxes, transcription text, line segmentations",
        verification_status=SourceVerificationStatus.VERIFIED_PUBLIC,
        access_method="Academic registration on University of Bern FKI portal",
        known_limitations=[
            "General English prose (LOB Corpus), not specialized medical or posology notation"
        ],
        relevance="Pre-training and baseline benchmark for cursive HTR performance in Phase 5.",
        provenance=ProvenanceRecord(
            source_url="https://fki.tic.heia-fr.ch/databases/iam-handwriting-database",
            provider_organization="Research Group on Computer Vision and Artificial Intelligence (FKI), University of Bern",
            retrieval_date="2026-09-27T00:00:00Z",
            license="CC BY-NC 4.0",
            license_category=LicenseCategory.ACADEMIC_RESEARCH_LICENSE,
            permitted_usage="Non-commercial academic research and benchmarking",
            attribution_requirements="Cite Marti & Bunke (2002)",
            citation="Marti, U.-V. and Bunke, H. (2002). The IAM-database: an English sentence database for offline handwriting recognition. IEEE PAMI, 24(11):1459-1464.",
            dataset_version="3.0"
        )
    ),
    DatasetSourceEntry(
        dataset_id="aura-rx-curated-evaluation",
        name="AURA-Rx Calibration & Integration Sample Set",
        description="A focused collection of 7 synthetic and de-identified outpatient prescription images paired with gold-standard line-item annotations. Designed strictly for functional pipeline testing, deterministic unit/integration testing, UI state rendering calibration, and split leakage verification. Does not constitute a statistically sufficient evaluation benchmark for empirical ML claims (which is scheduled for Phase 12 using large-scale external corpora).",
        document_type="Prescription document images with clinical line items",
        handwriting_characteristics="Diverse Latin handwriting styles including clean, cursive, blurred, shadowed, abbreviations, and LASA pairs",
        language_script="Latin with English, Hindi, and Marathi posology ground truth",
        available_annotations="Line item text, medicine name, dosage, frequency, route, duration, instructions, bounding boxes, ambiguity flags",
        verification_status=SourceVerificationStatus.VERIFIED_PUBLIC,
        access_method="Local repository path data/samples/",
        known_limitations=[
            "Small sample size (N=7); strictly for engineering integration, calibration, and regression testing",
            "Statistically insufficient for calculating clinical sensitivity/specificity or model generalizability claims"
        ],
        relevance="End-to-end integration and calibration benchmark for Phases 3 through 13.",
        provenance=ProvenanceRecord(
            source_url="local://data/samples",
            provider_organization="Cap_43 Academic Capstone Engineering Project",
            retrieval_date="2026-09-27T00:00:00Z",
            license="MIT Academic License",
            license_category=LicenseCategory.OPEN_SOURCE_SOFTWARE_DATA_LICENSE,
            permitted_usage="Project development, test suites, evaluation benchmarking",
            attribution_requirements="AURA-Rx Capstone Repository Documentation",
            citation="AURA-Rx Engineering Team (2026). Curated De-identified Outpatient Evaluation Benchmark. Capstone Specification.",
            dataset_version="1.0.0"
        )
    ),
    DatasetSourceEntry(
        dataset_id="candidate-kaggle-medical-handwritten",
        name="Kaggle Medical Handwritten Text Collection (Candidate)",
        description="Community contributed collection of medical handwriting snippets.",
        document_type="Snippet images",
        handwriting_characteristics="Mixed illegible cursive snippets",
        language_script="English / Latin",
        available_annotations="Snippet transcription labels",
        verification_status=SourceVerificationStatus.CANDIDATE_UNVERIFIED,
        access_method="Kaggle dataset public repository",
        known_limitations=[
            "Licensing provenance unverified; writer consent and de-identification verification incomplete",
            "Pending formal review before incorporation into experimental pipelines"
        ],
        relevance="Candidate exploratory source; marked unverified per Phase 3 safety protocol.",
        provenance=ProvenanceRecord(
            source_url="https://www.kaggle.com/datasets",
            provider_organization="Kaggle Community Upload",
            retrieval_date="2026-09-27T00:00:00Z",
            license="Unverified / Pending Audit",
            license_category=LicenseCategory.UNVERIFIED_PENDING_AUDIT,
            permitted_usage="Under legal and ethical review; not permitted in training pipelines without verified license",
            attribution_requirements="Pending verification",
            citation="Kaggle Community (2023). Medical Handwritten Dataset (Unverified Candidate).",
            dataset_version="0.1-candidate"
        )
    ),
]

manifest = DatasetManifest(
    manifest_version="1.0.0",
    sources=sources,
    local_sample_count=7
)

save_manifest(manifest, Path("data/manifests/dataset_manifest.json"))

schema = DatasetManifest.model_json_schema()
with open("data/manifests/dataset_manifest_schema.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)

print("Generated dataset_manifest.json and dataset_manifest_schema.json successfully.")
print("Manifest Checksum:", manifest.checksum)
