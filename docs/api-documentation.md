# DawaAI REST API Specification & Reference Manual
## Endpoints, Schemas, and Verification Contracts for Prescription Decoding

**System:** DawaAI — Explainable Multimodal AI for Handwritten Prescription Understanding  
**API Version:** v1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**System Classification:** Deployment-Ready Assistive Research Prototype for Academic Demonstration  
**Date:** March 2026

---

## 1. Architecture & Protocol Overview

The DawaAI backend exposes an asynchronous RESTful API built on FastAPI. It processes prescription images, performs multimodal handwriting extraction, executes formulary grounding and LASA screening, applies uncertainty safeguards, and supports human clinician verification under Section 42 of the Indian Pharmacy Act (1948).

### Standard Request Headers
```http
Accept: application/json
Content-Type: application/json (or multipart/form-data for uploads)
X-Client-Platform: web-dawaai-1.0
```

### Prototype Storage & Access Limitations
Original prescription images are preserved and referenced by the application. Prototype storage and access-control limitations are documented; production-grade private cloud storage and institutional RBAC are not implemented.

---

## 2. API Endpoints Reference

### 2.1 Health & Readiness Probe
Check server operational status, environment configuration, and pipeline availability.

- **Method:** `GET`
- **Route:** `/api/v1/health`
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "project_name": "DawaAI Backend - Explainable Multimodal AI for Handwritten Prescription Understanding",
  "version": "1.0.0",
  "mock_mode": true
}
```

---

### 2.2 Upload Prescription Image (Multipart Intake)
Uploads a raw prescription document (JPEG, PNG, TIFF, or WebP) for preprocessing and reference preservation.

- **Method:** `POST`
- **Route:** `/api/v1/prescriptions/upload`
- **Content-Type:** `multipart/form-data`
- **Form Parameters:**
  - `file`: Binary image file (Maximum: 15 MB).
- **Response (201 Created):**
```json
{
  "prescription_id": "rx-883a-491b-871d-e029f6d4821a",
  "original_image_url": "/backend/uploads/rx-883a-491b-871d-e029f6d4821a.png",
  "file_size_bytes": 1420850,
  "status": "PENDING_ANALYSIS"
}
```

---

### 2.3 Process & Analyze Prescription
Executes the multimodal extraction, formulary grounding, and uncertainty pipeline.

- **Method:** `POST`
- **Route:** `/api/v1/prescriptions/process` (with canonical alias `/api/v1/prescriptions/analyze`)
- **Request Body:**
```json
{
  "prescription_id": "rx-883a-491b-871d-e029f6d4821a",
  "mock_scenario": "confident"
}
```
*Supported `mock_scenario` values for evaluation:* `"confident"`, `"uncertain"`, `"lasa"`, `"flagged"`, `"abstained"`.

- **Response (200 OK - Confident Scenario):**
```json
{
  "status": "success",
  "data": {
    "id": "rx-883a-491b-871d-e029f6d4821a",
    "overall_status": "VERIFIED",
    "document_confidence": 0.942,
    "is_abstained": false,
    "original_image_url": "/backend/uploads/sample-1-bronchitis.png",
    "extracted_entities": [
      {
        "entity_id": "ent-01",
        "raw_text": "Amox-Clav 625",
        "normalized_name": "Amoxicillin and Clavulanate Potassium",
        "tall_man_name": "amoxicillin and Clavulanate",
        "dosage": "625 mg",
        "frequency": "b.i.d. (Twice Daily)",
        "duration": "5 days",
        "raw_confidence": 0.961,
        "calibrated_confidence": null,
        "calibration_status": "insufficient_data",
        "is_uncertain": false,
        "rxcui": "1046775",
        "cdsco_status": "APPROVED",
        "bounding_box": {
          "x": 0.124,
          "y": 0.281,
          "width": 0.542,
          "height": 0.068
        },
        "posology": {
          "en": {
            "schedule": "1 tablet twice daily after food for 5 days",
            "slots": { "morning": true, "afternoon": false, "evening": true, "night": false }
          },
          "hi": {
            "schedule": "खाना खाने के बाद 1 गोली दिन में दो बार 5 दिनों तक लें",
            "slots": { "morning": true, "afternoon": false, "evening": true, "night": false }
          },
          "mr": {
            "schedule": "जेवणानंतर 1 गोळी दिवसातून दोनदा 5 दिवस घ्या",
            "slots": { "morning": true, "afternoon": false, "evening": true, "night": false }
          }
        }
      }
    ],
    "lasa_screening": {
      "has_warning": false,
      "conflicting_pair": null,
      "similarity_score": 0.0
    }
  }
}
```

- **Response (200 OK - Abstained Scenario):**
```json
{
  "status": "success",
  "data": {
    "id": "rx-552a-991c-441d-e019f6d4899c",
    "overall_status": "ABSTAINED",
    "document_confidence": 0.324,
    "is_abstained": true,
    "abstention_reason": "Severe ink bleed-through and stroke ambiguity in Line 3. Automated transcription halted under Chow's rule to prevent medication hallucination.",
    "action_required": "Physical inspection by Registered Pharmacist mandatory under Section 42 of the Pharmacy Act.",
    "extracted_entities": []
  }
}
```

---

### 2.4 Human Clinician Verification Endpoints (Phase 9)

#### A. Retrieve Verification State & Audit Trail
- **Method:** `GET`
- **Route:** `/api/v1/verification/{prescription_id}`
- **Response (200 OK):**
```json
{
  "prescription_id": "rx-883a-491b-871d-e029f6d4821a",
  "status": "IN_REVIEW",
  "verified_fields": {},
  "audit_trail": []
}
```

#### B. Confirm Field Verification
- **Method:** `POST`
- **Route:** `/api/v1/verification/{prescription_id}/fields/{field_id}/confirm`
- **Request Body:**
```json
{
  "field_name": "medicine_name",
  "clinician_id": "PHARM-MH-2024",
  "notes": "Verified against physical paper"
}
```
- **Response (200 OK):**
```json
{
  "status": "CONFIRMED",
  "field_id": "ent-01",
  "timestamp": "2026-03-29T10:30:00Z"
}
```

#### C. Correct Field Value
- **Method:** `POST`
- **Route:** `/api/v1/verification/{prescription_id}/fields/{field_id}/correct`
- **Request Body:**
```json
{
  "field_name": "dosage",
  "corrected_value": "625 mg",
  "clinician_id": "PHARM-MH-2024",
  "reason": "Corrected dosage unit"
}
```
- **Response (200 OK):**
```json
{
  "status": "CORRECTED",
  "field_id": "ent-01",
  "original_value": "620 mg",
  "corrected_value": "625 mg",
  "timestamp": "2026-03-29T10:30:05Z"
}
```

#### D. Mark Field as Unreadable
- **Method:** `POST`
- **Route:** `/api/v1/verification/{prescription_id}/fields/{field_id}/unreadable`
- **Request Body:**
```json
{
  "field_name": "frequency",
  "clinician_id": "PHARM-MH-2024",
  "reason": "Ink illegible"
}
```
- **Response (200 OK):**
```json
{
  "status": "MARKED_UNREADABLE",
  "field_id": "ent-01",
  "timestamp": "2026-03-29T10:30:10Z"
}
```

---

## 3. Error Handling & Standard Status Codes

| HTTP Status | Error Code | Description |
| :---: | :--- | :--- |
| **400** | `BAD_REQUEST` | Malformed JSON payload or missing parameters. |
| **422** | `UNPROCESSABLE_ENTITY` | Input validation error or unreadable image upload. |
| **500** | `INTERNAL_SERVER_ERROR` | Internal server or unhandled pipeline error. |
| **504** | `GATEWAY_TIMEOUT` | Vision inference timeout exceeded. |

---

## 4. Client Integration Examples

### TypeScript / Fetch API Integration
```typescript
import { PrescriptionDTO } from './types/prescription.types';

export async function analyzePrescription(
  prescriptionId: string, 
  scenario: string = 'confident'
): Promise<PrescriptionDTO> {
  const response = await fetch('http://localhost:8000/api/v1/prescriptions/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prescription_id: prescriptionId, mock_scenario: scenario }),
  });

  if (!response.ok) {
    const errorBody = await response.json();
    throw new Error(`DawaAI Analysis Failed (${response.status}): ${errorBody.error?.message}`);
  }

  const result = await response.json();
  return result.data;
}
```
