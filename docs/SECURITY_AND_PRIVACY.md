# DawaAI Security, Privacy, and Clinical Governance Policy

**Project:** DawaAI (*Your Prescription, Made Clear.*)  
**Classification:** Academic Engineering Capstone / Assistive Healthcare AI  
**Scope:** Frontend (Vercel), Backend (FastAPI), Vision-Language Ingestion, and Formulary Knowledge Base

---

## 1. Core Safety & Ethical Principles

DawaAI adheres to the following foundational clinical and ethical mandates:

1. **The Original Prescription Is The Ground Truth:**  
   The application never destructively alters, silently replaces, or overwrites the physician's original handwritten prescription scan. All extracted entities remain tethered to their source coordinates.
2. **Never Convert Uncertainty Into False Confidence:**  
   When handwriting strokes are ambiguous, smudged, or illegible, the system does not hallucinate plausible medication names. It explicitly flags the entity as uncertain, marks candidates with confidence scores, or selectively abstains from autonomous interpretation.
3. **Assistive Guidance, Not Autonomous Prescription:**  
   DawaAI does not diagnose conditions, prescribe therapeutic regimens, calculate clinical dosages, recommend drug substitutions, or authorize medication administration. Unverified interpretations must be reviewed by a registered pharmacist or prescribing clinician.

---

## 2. Privacy & Data Handling Policy

### 2.1 Ephemeral Image Retention & Zero Persistent PHI
Prescription scans frequently contain patient names, ages, diagnoses, and physician credentials. To safeguard Protected Health Information (PHI):

- **No Permanent Database:** DawaAI does not operate a persistent relational or document database storing identifiable patient records.
- **Ephemeral Storage with Automatic Purge:** Uploaded prescription scans are stored temporarily in a restricted directory with unique cryptographically random filenames (`rx_<uuid12>_<sanitized_name>`).
- **Time-to-Live (TTL):** Files older than **2 hours** are automatically purged by the backend `cleanup_ephemeral_uploads` lifecycle task to prevent storage exhaustion and unauthorized data retention.
- **Zero Log Leakage:** Application loggers explicitly filter raw image bytes, extracted patient identifiers, and private API keys.

### 2.2 Privacy Notice for Users
A prominent notice in the application interface informs users:
> *"Prescription scans uploaded to DawaAI are processed ephemerally in volatile memory for transcription and posology extraction. Scans are retained only for your active session and are purged automatically. Do not upload records if prohibited by your local institutional policies."*

---

## 3. Application Security & Defense-in-Depth

### 3.1 Input Validation & Binary Magic Byte Verification
To defend against malicious payloads, polyglots, and file extension spoofing:
- **MIME & Extension Whitelist:** Only `image/jpeg`, `image/png`, `image/webp`, `image/tiff`, `image/bmp`, and `image/svg+xml` are accepted.
- **Binary Magic Bytes Signature Verification:** In addition to file extensions, `StorageService.validate_file_signature` verifies the first 4–12 bytes of uploaded streams against recognized image signatures (`\x89PNG`, `\xff\xd8\xff`, `RIFF...WEBP`, `II*`, `BM`, `<svg`). Spoofed Windows executables (PE `MZ` headers) or shell scripts are rejected immediately with HTTP 415.
- **Strict Size Limits:** File uploads are capped at **15 MB** (`MAX_UPLOAD_SIZE_BYTES`), returning HTTP 413 `FILE_TOO_LARGE` if exceeded.

### 3.2 Abuse Resistance & Rate Limiting
To prevent denial of service (DoS), GPU resource exhaustion, and model inference quota depletion:
- **Sliding-Window Rate Limiting:** An in-memory sliding-window rate limiter monitors client IPs on `/api/v1/prescriptions/analyze` and `/process`.
- **Threshold:** Capped at **60 requests per minute** per client IP.
- **Enforcement:** Exceeding quota immediately returns HTTP 429 `RATE_LIMIT_EXCEEDED` with a standard `Retry-After` response header.

### 3.3 HTTP Security Headers
All backend responses are enriched via FastAPI middleware with enterprise security headers:
- `X-Content-Type-Options: nosniff` (Prevents MIME-sniffing attacks)
- `X-Frame-Options: DENY` (Mitigates clickjacking)
- `Referrer-Policy: strict-origin-when-cross-origin` (Protects referrer data)
- `Permissions-Policy: camera=(), microphone=(), geolocation=()` (Restricts browser features)
- `X-Request-ID: <uuid>` (Unique correlation identifier for audit tracing)

### 3.4 Cross-Origin Resource Sharing (CORS)
- Backend restricts inbound CORS origins to explicitly approved URLs:
  - Local development: `http://localhost:5173`, `http://127.0.0.1:5173`
  - Vercel deployments: Regex pattern `https://.*\.vercel\.app` matching preview branches and production deployments.
- Rejects wildcards (`*`) when credentials are required.

### 3.5 DevSecOps & Container Hardening
- **Non-Root Execution:** The production `Dockerfile` provisions an unprivileged system user (`appuser`, UID 10001, GID 10001) with restricted `/sbin/nologin` shell.
- **Minimal Base Image:** Uses `python:3.11-slim` with only essential runtime libraries (`tesseract-ocr`, `curl`).
- **Secrets Isolation:** `.env` and sensitive credentials are excluded from the Docker build context via `.dockerignore`.
- **Automated CI Scanning:** GitHub Actions CI executes automated type checks, linters, and regression test suites on every pull request.

---

## 4. Clinical & Regulatory Notice

> [!WARNING]
> **Academic Evaluation Only:**  
> DawaAI is developed as an academic capstone engineering project. It has not undergone formal clinical trials, medical device certification (e.g., US FDA 510(k), EU MDR, or CDSCO Medical Device Rules 2017), and is not certified for autonomous clinical diagnostic or prescriptive use.
