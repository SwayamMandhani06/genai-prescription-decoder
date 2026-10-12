# DawaAI REST API Specification

**Service Name:** DawaAI Prescription Understanding API  
**Version:** 1.0.0  
**Base Path:** `/api/v1`  
**API Documentation (OpenAPI/Swagger):** `GET /docs`  
**ReDoc Specification:** `GET /redoc`

---

## 1. Global Conventions & Standards

- **Encoding:** `UTF-8`
- **Request Payloads:** `multipart/form-data` for image uploads; `application/json` for structured requests.
- **Response Payloads:** `application/json`
- **Correlation ID:** Every response includes an `X-Request-ID` header for distributed tracing and diagnostic telemetry.
- **Error Format:** All client and server errors adhere to the standardized `ErrorResponse` envelope.

---

## 2. Standard Error Response Envelope

```json
{
  "error": {
    "code": "IMAGE_QUALITY_INSUFFICIENT",
    "message": "Optical blur detected; stroke sharpness below diagnostic threshold.",
    "stage": "image_quality_assessment",
    "retryable": true,
    "details": {
      "heuristic_score": 0.28,
      "recommendation": "Hold camera steady in good lighting directly above the prescription."
    }
  },
  "detail": "Optical blur detected; stroke sharpness below diagnostic threshold.",
  "prescription_id": "RX-20261012-0042",
  "original_image_url": "/uploads/rx_a1b2c3d4_scan.png"
}
```

### Standard Error Codes (`ErrorCode`)
| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `INVALID_REQUEST` | 400 | Malformed parameters, missing required fields. |
| `FILE_TOO_LARGE` | 413 | Upload exceeds maximum permitted size (15 MB). |
| `INVALID_FILE_TYPE` | 415 | Unsupported MIME type or invalid binary magic byte signature. |
| `IMAGE_QUALITY_INSUFFICIENT`| 422 | Optical blur, severe glare, or low resolution prevents legible reading. |
| `VALIDATION_FAILED` | 422 | Drug candidate could not be resolved against pharmacopeia formulary. |
| `RATE_LIMIT_EXCEEDED` | 429 | Client IP exceeded 60 requests per minute quota. |
| `INTERNAL_ERROR` | 500 | Unexpected server or inference runtime exception. |
| `MODEL_UNAVAILABLE` | 503 | Upstream vision-language inference engine unavailable. |
| `PROCESSING_FAILED` | 504 | Upstream inference or knowledge retrieval timeout. |

---

## 3. Endpoints

### 3.1 Health & Diagnostics

#### `GET /health` / `GET /api/v1/health`
Checks container readiness, model pipeline mode, and filesystem storage availability.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "pipeline_mode": "multimodal",
  "storage_accessible": true
}
```

---

### 3.2 Prescription Processing

#### `POST /api/v1/prescriptions/analyze` (Alias: `POST /api/v1/prescriptions/process`)
Uploads a raw prescription scan or specifies a curated sample ID for multimodal decoding.

**Headers:**
- `Content-Type: multipart/form-data`

**Request Parameters (Form Data):**
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `file` | `UploadFile` | Optional* | Prescription scan (JPEG, PNG, WebP, TIFF). |
| `sample_id` | `string` | Optional* | Pre-loaded academic evaluation ID (`rx-sample-1`). |
| `confidence_threshold` | `float` | No | Minimum confidence cutoff (`0.0`–`1.0`). |
| `enable_lasa_detection` | `boolean` | No | Enables Look-Alike Sound-Alike screening (default: `true`). |
| `target_language` | `string` | No | Regional vernacular target: `en`, `hi`, `mr` (default: `en`). |
| `mock_scenario` | `string` | No | Test harness scenario override (`confident`, `uncertain`, `lasa_warning`, `abstained`). |

*\*Either `file` or `sample_id` must be provided.*

**Response (200 OK):**
```json
{
  "prescription_id": "RX-20261012-781A",
  "original_image_url": "/uploads/rx_4f1c9d2a_scan.png",
  "overall_confidence": 0.92,
  "overall_status": "VERIFIED",
  "requires_human_review": false,
  "fields": {
    "medicine_name": {
      "value": "Amoxicillin",
      "confidence": 0.94,
      "status": "confident",
      "coordinates": {"x": 120, "y": 340, "w": 280, "h": 50},
      "validation_source": "CDSCO / RxNorm"
    },
    "strength": {
      "value": "500 mg",
      "confidence": 0.91,
      "status": "confident"
    },
    "dosage_form": {
      "value": "Capsule",
      "confidence": 0.96,
      "status": "confident"
    },
    "frequency": {
      "value": "TID (3 times daily)",
      "confidence": 0.88,
      "status": "confident"
    },
    "duration": {
      "value": "7 days",
      "confidence": 0.89,
      "status": "confident"
    }
  },
  "lasa_alert": {
    "detected": false,
    "primary_drug": "Amoxicillin",
    "confusable_with": null,
    "tall_man_lettering": "amoxicillin",
    "similarity_score": 0.12
  },
  "explanation": {
    "language": "en",
    "summary": "Take 1 capsule of Amoxicillin 500mg three times daily after meals for 7 days.",
    "instructions": [
      "Take after meals with water",
      "Complete the full 7-day course even if feeling better"
    ],
    "precautions": "Notify your physician if rash or severe diarrhea develops."
  }
}
```

---

### 3.3 Accession Record Retrieval

#### `GET /api/v1/prescriptions/{prescription_id}`
Retrieves a previously processed record or curated academic demonstration fixture.

**Parameters:**
- `prescription_id`: Accession identifier (e.g., `DEMO-RX-01`, `RX-SAMPLE-1`).

**Response (200 OK):**
Returns `PrescriptionAnalyzeResponse` payload.

---

### 3.4 Preprocessing Manifest & Optical Diagnostics

#### `GET /api/v1/prescriptions/{prescription_id}/artifacts`
Retrieves run manifest for image deskewing, Sauvola binarization, and optical quality scores.

---

### 3.5 Human Clinician Verification & Audit Trail

#### `POST /api/v1/verification/{prescription_id}/fields/{field_id}/confirm`
Records human clinician confirmation of an extracted posology field into the audit trail.

**Request Body:**
```json
{
  "original_value": "Metformin",
  "reason": "Confirmed against original physician signature and handwriting."
}
```

#### `POST /api/v1/verification/{prescription_id}/fields/{field_id}/correct`
Records clinician correction when model extraction was erroneous or ambiguous.

**Request Body:**
```json
{
  "corrected_value": "Metformin 500mg",
  "reason": "Dosage stroke was unclear; corrected per physician consultation."
}
```
